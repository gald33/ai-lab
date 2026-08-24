"""The manager: a reader of the board and a settler of state.

It never calls an agent, never asks an agent for anything, and never waits for
one. It reads the Switchboard channel, recognises the three formatted messages,
settles them against the island, and says its own lines back so that what it
did is visible to everyone -- a receipt is a channel message like any other.

The board here is **native Switchboard**, reached through its own client. The
agents reach the same channel through the Switchboard MCP server. There is no
intermediate script, no bespoke transport, and nothing either side can call
that Switchboard does not already provide.

It enforces exactly two things:

* **timing** -- what it will still settle, given the schedule it posted;
* **format** -- a line that is nearly a formatted message is refused, with the
  reason, and never repaired into a plausible one;

It enforces no price, no role, no partner and no plan -- and it does not
score. It records what each trader held at each bell and stops there. Utility
needs a taste, tastes belong to `dealer.py`, and scoring happens afterwards
from the seed (`score.trajectory_from`). That is the first of the four
conditions in `games/island.md` under which somebody other than the lab could
run this: a manager that holds no tastes knows nothing a spectator does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from switchboard.client import Client  # noqa: E402
from switchboard.timing import unwrap_forecast  # noqa: E402

from .protocol import Approve, Malformed, Produce, Propose, parse  # noqa: E402

MANAGER = "manager"
_EPS = 1e-9


@dataclass
class Holder:
    name: str
    index: int
    holdings: list[float]
    spent: float = 0.0
    produced: bool = False


@dataclass
class Proposal:
    pid: str
    maker: str
    taker: str
    give: dict[str, float]
    want: dict[str, float]
    episode: int
    status: str = "open"


@dataclass
class Manager:
    """Reads the channel from a cursor; settles what it recognises."""

    #: Production capacity per unit of labour, by trader index then good --
    #: `dealer.Dealer.capacity`. The manager takes this rather than an
    #: `Island` because an `Island` also carries `alpha`, and the point of
    #: the split is that this process never holds one.
    capacity: tuple[tuple[float, ...], ...]
    client: Client
    channel: str = "island"
    goods: tuple[str, ...] = ("bread", "cloth", "iron", "salt")
    names: tuple[str, ...] = ()
    episode: int = 0
    #: True between an episode opening and its bell. There are no stages
    #: inside an episode: producing, proposing and approving all settle for as
    #: long as the episode is open. The clock divides episodes from each other
    #: and nothing else.
    #:
    #: It starts **shut**, and the bell leaves it shut. Starting it open made
    #: the acknowledgement window part of episode 1: production settled before
    #: episode 1 was announced, so that episode ran longer than the others and
    #: longer for whoever produced early than for whoever waited. An episode
    #: that is not the same length as its siblings is not a repeat of them.
    episode_open: bool = False
    #: Message ids already considered. Switchboard history is append-only, so
    #: a seen-set is enough and no ordering assumption is needed.
    seen: set[str] = field(default_factory=set)
    holders: dict[str, Holder] = field(default_factory=dict)
    proposals: dict[str, Proposal] = field(default_factory=dict)
    acknowledged: set[str] = field(default_factory=set)
    #: Every trader the manager has heard from at all, acknowledgement or
    #: action. A session that exits without appearing here never reached the
    #: board, which is a different event from one that acted and then stopped.
    spoke: set[str] = field(default_factory=set)
    #: Switchboard peer id -> trader name. Filled in as agents register, so
    #: the manager scores the trader rather than the transport's identity.
    alias: dict[str, str] = field(default_factory=dict)
    #: trader name -> the signing key its seat was bound to, when `bind()`
    #: was given one. A trader with no entry here is not key-checked at all
    #: -- every existing caller of `bind()` omits it, so this is inert until
    #: something passes a key. See `games/island.md`, "Seats, and who is in
    #: one": the lobby is what witnesses this key today; nothing here draws
    #: it from anywhere but its caller.
    keys: dict[str, str] = field(default_factory=dict)
    settled: int = 0
    refused: int = 0
    talk: int = 0
    #: One record per episode, written at the bell. The screen had to be
    #: diagnosed by re-reading boards, and a board lives an hour on the hub --
    #: so by the time a result looked odd the evidence for it had expired.
    #: What the metrics cannot say on their own goes here instead: which
    #: proposals lapsed, who ended with nothing of what, and what each trader
    #: actually got.
    episode_log: list[dict] = field(default_factory=list)
    #: Every refusal, with the reason the trader was given. A count says how
    #: often the manager said no; only the reason says what the traders could
    #: not manage to express.
    refusals: list[dict] = field(default_factory=list)
    #: True if a single drain ever came back full. The manager reads the most
    #: recent rows and skips what it has seen, which is safe while it drains
    #: faster than the board fills -- and silently lossy if it ever does not.
    saturated: bool = False
    _settled_this_episode: int = 0
    _next: int = 1

    def __post_init__(self) -> None:
        if not self.names:
            self.names = tuple(f"T{i + 1}" for i in range(len(self.capacity)))
        for i, name in enumerate(self.names):
            self.holders[name] = Holder(name, i, [0.0] * len(self.goods))

    # --- reading -----------------------------------------------------------

    def say(self, text: str) -> None:
        self.client.post(self.channel, text)

    def drain(self) -> None:
        """Read whatever has appeared since last time. Never blocks anyone."""
        if self.keys:
            # A roster read is what teaches Switchboard's own verifier a
            # peer's published key -- signing.py, "the public key is sealed
            # like any other content" -- so a signature cannot be checked
            # without one. Gated on self.keys so the existing, keyless path
            # every current caller takes never pays for a call it has no use
            # for.
            self.client.agents()
        rows = sorted(self.client.history(self.channel, limit=500),
                      key=lambda r: r.get("seq", 0))
        if len(rows) >= 500:
            self.saturated = True
        for msg in rows:
            mid = str(msg.get("id"))
            if mid in self.seen:
                continue
            self.seen.add(mid)
            author = self.alias.get(str(msg.get("from") or ""), "")
            if not author or author == MANAGER:
                continue
            # A Switchboard `say` that carries a timing forecast arrives as an
            # envelope, not a string. Stringifying it turns "ACK. Ready." into
            # "{'text': 'ACK. Ready.', 'timing_forecast': {...}}" and every
            # match against it fails -- which is how two protocol-arm rounds
            # came to report 1/2 acknowledged when both traders had in fact
            # acknowledged. Unwrap with Switchboard's own inverse rather than
            # guessing at the shape.
            body, _forecast = unwrap_forecast(msg.get("body"))
            self._consider(author, body if isinstance(body, str) else "",
                           msg.get("signature"))

    def _consider(self, author: str, text: str,
                 signature: dict | None = None) -> None:
        if author not in self.holders:
            return
        self.spoke.add(author)
        bound = self.keys.get(author)
        if bound is not None:
            verdict = signature or {}
            if verdict.get("status") != "verified" or verdict.get("key") != bound:
                self._refuse(author, "imposture",
                            f"this did not come from the key {author} took "
                            f"its seat with", text)
                return
        upper = text.strip().upper()
        if upper.startswith("ACK"):
            self.acknowledged.add(author)
            return
        try:
            action = parse(text)
        except Malformed as exc:
            self._refuse(author, "malformed", str(exc), text)
            return
        if action is None:
            self.talk += 1
            return
        try:
            if isinstance(action, Produce):
                self._produce(author, action)
            elif isinstance(action, Propose):
                self._propose(author, action)
            elif isinstance(action, Approve):
                self._approve(author, action)
        except Refused as exc:
            self._refuse(author, type(action).__name__.lower(), str(exc), text)

    def _refuse(self, author: str, kind: str, reason: str, text: str) -> None:
        """Say no, and keep why. The reason is the diagnostic, not the count."""
        self.refused += 1
        self.refusals.append({"episode": self.episode + 1, "trader": author,
                              "kind": kind, "reason": reason,
                              "line": text.strip()[:200]})
        self.say(f"@{author} not settled: {reason}")

    # --- settling ----------------------------------------------------------

    def _good(self, name: str) -> int:
        if name not in self.goods:
            raise Refused(f"no such good {name!r}")
        return self.goods.index(name)

    def _free(self, name: str, good: str) -> float:
        held = self.holders[name].holdings[self._good(good)]
        for p in self.proposals.values():
            if p.status == "open" and p.maker == name:
                held -= p.give.get(good, 0.0)
        return held

    def _produce(self, author: str, action: Produce) -> None:
        if not self.episode_open:
            raise Refused("this episode has closed")
        h = self.holders[author]
        if h.produced:
            raise Refused("you have already produced this episode")
        total = sum(action.plan.values())
        if total > 1.0 + 1e-6:
            # Enough precision to show the excess. A plan over budget by 1e-4
            # rounds to "sums to 1.000; the budget is 1.0", which reads as the
            # manager refusing a plan that obeys it, and the trader spends a
            # message finding out otherwise.
            raise Refused(f"shares sum to {total:.6g}, over the budget of 1.0 "
                          f"by {total - 1.0:.6g}")
        made = {}
        for good, share in action.plan.items():
            g = self._good(good)
            qty = share * self.capacity[h.index][g]
            h.holdings[g] += qty
            made[good] = round(qty, 4)
        h.spent, h.produced = total, True
        self.settled += 1
        self._settled_this_episode += 1
        self.say(f"@{author} produced {made}; "
                                f"{round(1 - total, 4)} labour unspent")

    def _propose(self, author: str, action: Propose) -> None:
        if not self.episode_open:
            raise Refused("this episode has closed")
        if action.to not in self.holders:
            raise Refused(f"no such trader {action.to!r}")
        if action.to == author:
            raise Refused("you cannot deal with yourself")
        for good, qty in action.give.items():
            if self._free(author, good) + _EPS < qty:
                raise Refused(f"you have {self._free(author, good):.4f} {good} "
                              f"uncommitted, not {qty:.4f}")
        pid = f"p{self._next}"
        self._next += 1
        self.proposals[pid] = Proposal(pid, author, action.to, action.give,
                                       action.want, self.episode)
        self.settled += 1
        self._settled_this_episode += 1
        self.say(f"{pid}: {author} offers {action.give} to "
                                f"{action.to} for {action.want} — open until "
                                f"the bell")

    def _approve(self, author: str, action: Approve) -> None:
        if not self.episode_open:
            raise Refused("this episode has closed")
        p = self.proposals.get(action.proposal_id)
        if p is None:
            raise Refused(f"no such proposal {action.proposal_id!r}")
        if p.status != "open":
            raise Refused(f"{p.pid} is already {p.status}")
        if p.taker != author:
            raise Refused(f"{p.pid} was not addressed to you")
        for good, qty in p.want.items():
            if self._free(author, good) + _EPS < qty:
                raise Refused(f"you have {self._free(author, good):.4f} {good} "
                              f"uncommitted, not the {qty:.4f} it asks for")
        maker, taker = self.holders[p.maker], self.holders[author]
        for good, qty in p.give.items():
            g = self._good(good)
            maker.holdings[g] -= qty
            taker.holdings[g] += qty
        for good, qty in p.want.items():
            g = self._good(good)
            taker.holdings[g] -= qty
            maker.holdings[g] += qty
        p.status = "settled"
        self.settled += 1
        self._settled_this_episode += 1
        self.say(f"{p.pid} settled: {p.maker} and {author} "
                                f"exchanged {p.give} for {p.want}")

    # --- the clock ---------------------------------------------------------

    def open_episode(self) -> None:
        """Ring the episode in. Nothing settles until this has been called."""
        self.episode_open = True

    def close_episode(self) -> dict[str, dict[str, float]]:
        """The bell. Open proposals lapse, holdings are eaten, labour returns.

        Returns what each trader held when it rang, which is this manager's
        whole output: it does not compute utility and cannot, having no
        tastes. `score.trajectory_from` turns these into a trajectory
        afterwards, from the seed.
        """
        self.drain()
        lapsed = [p.pid for p in self.proposals.values() if p.status == "open"]
        for p in self.proposals.values():
            if p.status == "open":
                p.status = "lapsed"

        # Unrounded, because this is now the record rather than a diagnostic
        # beside one. At six decimals a utility rebuilt from these agrees with
        # one computed from full precision to 7.2e-07, against the ledger's
        # 1e-6 tolerance -- which passes, and is not a margin.
        held = {n: {g: self.holders[n].holdings[i]
                    for i, g in enumerate(self.goods)}
                for n in self.names}

        # What the numbers alone cannot answer later: who went without, and in
        # what. A zero episode is one trader holding none of one good, and a
        # utility vector cannot say which trader or which good -- but that is
        # exactly the question every post-mortem of this run turned out to ask.
        self.episode_log.append({
            "episode": self.episode + 1,
            "holdings": held,
            "starved": {n: [g for i, g in enumerate(self.goods)
                            if self.holders[n].holdings[i] <= _EPS]
                        for n in self.names
                        if any(self.holders[n].holdings[i] <= _EPS
                               for i in range(len(self.goods)))},
            "produced": [n for n in self.names if self.holders[n].produced],
            "lapsed": lapsed,
            "settled": self._settled_this_episode,
        })
        self._settled_this_episode = 0
        for h in self.holders.values():
            h.holdings = [0.0] * len(self.goods)
            h.spent, h.produced = 0.0, False
        self.episode += 1
        self.episode_open = False
        self.say(f"bell — episode {self.episode} closed. "
                                f"{len(lapsed)} proposal(s) lapsed. "
                                f"Everything held has been consumed; stocks and "
                                f"labour are reset.")
        return held

    def bind(self, peer_id: str, name: str, key: str | None = None) -> None:
        """Bind a Switchboard identity to a trader name, once, at launch.

        `key` is optional and unused by every caller here today -- 005 binds
        by launch order, not by a witnessed key, so imposture-checking stays
        off for it. It exists for a caller that *did* witness one, such as a
        lobby that bound this seat before the round opened: pass it and every
        further message from `name` has to verify against it or be refused.
        """
        self.alias[peer_id] = name
        if key is not None:
            self.keys[name] = key



class Refused(Exception):
    """A well-formed message the world will not settle, with a reason."""
