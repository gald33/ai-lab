"""The manager: a reader of the board and a settler of state.

It never calls an agent, never asks an agent for anything, and never waits for
one. It reads the Switchboard channel, recognises the three formatted messages,
settles them against the island, and says its own lines back so that what it
did is visible to everyone -- a receipt is a channel message like any other.

The board here is **native Switchboard**, reached through its own client. The
agents reach the same channel through the Switchboard MCP server. There is no
intermediate script, no bespoke transport, and nothing either side can call
that Switchboard does not already provide.

It enforces exactly three things:

* **timing** -- what it will still settle, given the schedule it posted;
* **format** -- a line that is nearly a formatted message is refused, with the
  reason, and never repaired into a plausible one;
* **scoring** -- read from settled state, never from what an agent said.

It enforces no price, no role, no partner and no plan.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import Island, utility  # noqa: E402

from switchboard.client import Client  # noqa: E402

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

    island: Island
    client: Client
    channel: str = "island"
    goods: tuple[str, ...] = ("bread", "cloth", "iron", "salt")
    names: tuple[str, ...] = ()
    episode: int = 0
    #: True while PRODUCE will still be settled this episode.
    production_open: bool = True
    #: True while PROPOSE and APPROVE will still be settled this episode.
    market_open: bool = False
    #: Message ids already considered. Switchboard history is append-only, so
    #: a seen-set is enough and no ordering assumption is needed.
    seen: set[str] = field(default_factory=set)
    holders: dict[str, Holder] = field(default_factory=dict)
    proposals: dict[str, Proposal] = field(default_factory=dict)
    episode_utilities: list[list[float]] = field(default_factory=list)
    acknowledged: set[str] = field(default_factory=set)
    #: Switchboard peer id -> trader name. Filled in as agents register, so
    #: the manager scores the trader rather than the transport's identity.
    alias: dict[str, str] = field(default_factory=dict)
    settled: int = 0
    refused: int = 0
    talk: int = 0
    _next: int = 1

    def __post_init__(self) -> None:
        if not self.names:
            self.names = tuple(f"T{i + 1}" for i in range(self.island.n_agents))
        for i, name in enumerate(self.names):
            self.holders[name] = Holder(name, i, [0.0] * self.island.n_goods)

    # --- reading -----------------------------------------------------------

    def say(self, text: str) -> None:
        self.client.post(self.channel, text)

    def drain(self) -> None:
        """Read whatever has appeared since last time. Never blocks anyone."""
        rows = sorted(self.client.history(self.channel, limit=500),
                      key=lambda r: r.get("seq", 0))
        for msg in rows:
            mid = str(msg.get("id"))
            if mid in self.seen:
                continue
            self.seen.add(mid)
            author = self.alias.get(str(msg.get("from") or ""), "")
            if not author or author == MANAGER:
                continue
            self._consider(author, str(msg.get("body") or ""))

    def _consider(self, author: str, text: str) -> None:
        if author not in self.holders:
            return
        upper = text.strip().upper()
        if upper.startswith("ACK"):
            self.acknowledged.add(author)
            return
        try:
            action = parse(text)
        except Malformed as exc:
            self.refused += 1
            self.say(f"@{author} not settled: {exc}")
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
            self.refused += 1
            self.say(f"@{author} not settled: {exc}")

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
        if not self.production_open:
            raise Refused("production for this episode has closed")
        h = self.holders[author]
        if h.produced:
            raise Refused("you have already produced this episode")
        total = sum(action.plan.values())
        if total > 1.0 + 1e-6:
            raise Refused(f"shares sum to {total:.3f}; the budget is 1.0")
        made = {}
        for good, share in action.plan.items():
            g = self._good(good)
            qty = share * self.island.capacity[h.index][g]
            h.holdings[g] += qty
            made[good] = round(qty, 4)
        h.spent, h.produced = total, True
        self.settled += 1
        self.say(f"@{author} produced {made}; "
                                f"{round(1 - total, 4)} labour unspent")

    def _propose(self, author: str, action: Propose) -> None:
        if not self.market_open:
            raise Refused("the market for this episode is not open")
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
        self.say(f"{pid}: {author} offers {action.give} to "
                                f"{action.to} for {action.want} — open until "
                                f"the bell")

    def _approve(self, author: str, action: Approve) -> None:
        if not self.market_open:
            raise Refused("the market for this episode is not open")
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
        self.say(f"{p.pid} settled: {p.maker} and {author} "
                                f"exchanged {p.give} for {p.want}")

    # --- the clock ---------------------------------------------------------

    def close_episode(self) -> list[float]:
        """The bell. Open proposals lapse, holdings are eaten, labour returns."""
        self.drain()
        lapsed = [p.pid for p in self.proposals.values() if p.status == "open"]
        for p in self.proposals.values():
            if p.status == "open":
                p.status = "lapsed"
        utils = []
        for name in self.names:
            h = self.holders[name]
            utils.append(utility(self.island.alpha[h.index], h.holdings))
        self.episode_utilities.append(utils)
        for h in self.holders.values():
            h.holdings = [0.0] * self.island.n_goods
            h.spent, h.produced = 0.0, False
        self.episode += 1
        self.production_open, self.market_open = True, False
        self.say(f"bell — episode {self.episode} closed. "
                                f"{len(lapsed)} proposal(s) lapsed. "
                                f"Everything held has been consumed; stocks and "
                                f"labour are reset.")
        return utils

    def bind(self, peer_id: str, name: str) -> None:
        """Bind a Switchboard identity to a trader name, once, at launch."""
        self.alias[peer_id] = name

    def private_state(self, name: str) -> str:
        h = self.holders[name]
        cap = {g: round(self.island.capacity[h.index][i], 4)
               for i, g in enumerate(self.goods)}
        taste = {g: round(self.island.alpha[h.index][i], 4)
                 for i, g in enumerate(self.goods)}
        return (f"You are {name}. Your production capacity per unit of labour: "
                f"{cap}. Your taste weights: {taste}. Nobody else knows either.")


class Refused(Exception):
    """A well-formed message the world will not settle, with a reason."""
