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

import time
from dataclasses import dataclass, field

import httpx  # noqa: E402

from switchboard.client import Client, SwitchboardError  # noqa: E402

#: What a hub that is briefly unwell looks like from here. `SwitchboardError`
#: is the hub answering badly; the `httpx` errors are it not answering at all
#: -- a dropped connection, a refused socket, a read that timed out. D13
#: caught only the first kind, and run 007 died at 20:29 to the second: a
#: `RemoteProtocolError` from a server that disconnected without a response
#: went straight past the except clause and took nine finished rounds' records
#: with it. Both kinds are the same event for our purposes and both are safe
#: to repeat on a read.
TRANSPORT_FAULTS = (httpx.TransportError, httpx.RemoteProtocolError)
from switchboard.timing import unwrap_forecast  # noqa: E402

from .protocol import Approve, Malformed, Produce, Propose, parse  # noqa: E402

#: Whether labour may be committed in several pieces within one episode.
#: **Off by default**: every run before 007's run 002 settled one production per
#: episode, and flipping this silently would change what those numbers mean.
#: An experiment that wants it says so, and records it.
SPLIT_LABOUR = False

MANAGER = "manager"
#: What a trader seals a `PRODUCE` under. Bound into the key derivation and
#: the AEAD, so a sealed private half cannot be replayed as a plan.
#: The marker a board line used to carry when this repo sealed its own
#: payloads. Kept only to recognise one on an **old** board: sealing is
#: Switchboard's `whisper` now, which never puts a body on the channel at all.
SEALED_MARKER = "SEALED "

#: How many times one seat is told, per episode, that a reason is waiting for
#: it privately. Not one: a trader that fails twice in a minute needs telling
#: twice, and the second failure is the one that creates a false belief. Not
#: unbounded either, because a stranger writing ten lines must not make the
#: manager write ten more.
POINTERS_PER_EPISODE = 3

#: The heads this manager settles, plus the acknowledgement. Used to tell a
#: move apart from chatter when it arrives from a key that took no seat: the
#: first gets a receipt every time, the second gets one line per key.
_MOVES = ("PRODUCE", "PROPOSE", "APPROVE", "ACK")


def _is_a_move(text: str) -> bool:
    """Is this somebody trying to play, rather than talking?

    Deliberately loose -- it reads the first word and nothing else. A line
    that is *nearly* a move is exactly the line whose author most needs
    telling, and this decides who gets an answer rather than what settles.
    Nothing here repairs or accepts anything: `parse` still governs that.
    """
    head = text.strip().split(" ", 1)[0].strip().upper() if text.strip() else ""
    return head.rstrip(".:,") in _MOVES
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
    #: Lines written in this room by keys that took no seat -- see
    #: `_intrusion`. Kept whole, because the question they answer afterwards
    #: is whether the game was played through interference.
    intrusions: list[dict] = field(default_factory=list)
    #: The distinct keys those lines came from, so the manager says it once.
    intruders: set[str] = field(default_factory=set)
    #: How many lines arrived sealed to this manager rather than on the board.
    sealed_in: int = 0
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

    #: seat -> how many times it has been pointed at its inbox this episode.
    #: Cleared at every bell -- see `_point_at_inbox`.
    _pointed: dict[str, int] = field(default_factory=dict)
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
    #: Reads the hub refused with a transient error and we retried. Recorded
    #: because a run that limped is not the same evidence as one that did not.
    drain_errors: int = 0
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

    def _history_with_retry(self, tries: int = 4) -> list:
        delay = 2.0
        for attempt in range(tries):
            try:
                return sorted(self.client.history(self.channel, limit=500),
                              key=lambda r: r.get("seq", 0))
            except TRANSPORT_FAULTS:
                if attempt == tries - 1:
                    raise
                self.drain_errors += 1
                time.sleep(delay)
                delay *= 2
            except SwitchboardError as exc:
                transient = exc.status is None or exc.status >= 500
                if not transient or attempt == tries - 1:
                    raise
                self.drain_errors += 1
                time.sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")

    def drain(self) -> None:
        """Read whatever has appeared since last time. Never blocks anyone.

        The hub is behind a gateway that returns 5xx now and then; a single
        such refusal once killed a whole run mid-episode. A read is safe to
        repeat -- history is refetched whole and deduplicated by id -- so a
        transient refusal is retried rather than raised. A hub that stays down
        past the last attempt still raises: a run that cannot read the board
        cannot score it, and pretending otherwise would fabricate an empty
        episode.
        """
        if self.keys:
            # A roster read is what teaches Switchboard's own verifier a
            # peer's published key -- signing.py, "the public key is sealed
            # like any other content" -- so a signature cannot be checked
            # without one. Gated on self.keys so the existing, keyless path
            # every current caller takes never pays for a call it has no use
            # for.
            self.client.agents()
        self._drain_sealed()
        rows = self._history_with_retry()
        if len(rows) >= 500:
            self.saturated = True
        for msg in rows:
            mid = str(msg.get("id"))
            if mid in self.seen:
                continue
            self.seen.add(mid)
            peer = str(msg.get("from") or "")
            author = self.alias.get(peer, "")
            # The manager's own lines, however this client names itself.
            if author == MANAGER or peer == getattr(self.client, "agent_id", None):
                continue
            if not author:
                self._intrusion(peer, msg)
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

    def _drain_sealed(self) -> None:
        """Read what was sealed to this manager alone.

        A sealed `PRODUCE` cannot ride the channel: Switchboard's `whisper`
        seals
        to one peer's published exchange key and delivers to that peer's own
        `@` channel, and **only `inbox()` opens it** -- `history()` hands back
        the envelope. So the manager reads both, and a line that arrives here
        is settled exactly as one that arrives on the board: same author, same
        signature check, same refusals.

        What the room still sees is that it happened. The outer message is an
        ordinary workspace-encrypted send, so every member reads sender,
        recipient, size and timing; only the body is theirs alone. And the
        receipt the manager posts afterwards is public, which is the whole
        point of sealing the plan and not the result.
        """
        if not self.keys:
            return
        try:
            rows = self.client.inbox()
        except AttributeError:      # a client without an inbox: nothing sealed
            return
        for msg in rows:
            mid = str(msg.get("id"))
            if mid in self.seen:
                continue
            self.seen.add(mid)
            peer = str(msg.get("from") or "")
            author = self.alias.get(peer, "")
            if not author or author == MANAGER:
                self._intrusion(peer, msg)
                continue
            self.sealed_in += 1
            if msg.get("unreadable"):
                self._refuse(author, "sealed",
                            "this was sealed to somebody else, or to a key "
                            "this manager does not hold", "<sealed>",
                            private=True)
                continue
            body, _forecast = unwrap_forecast(msg.get("body"))
            self._consider(author, body if isinstance(body, str) else "",
                           msg.get("signature"), private=True)

    def _intrusion(self, peer: str, msg: dict) -> None:
        """Somebody in this room who is not at this table has written in it.

        **Recorded rather than ignored.** A room key can be handed on: a seated
        trader may pass it to a confederate, or run a second client of its own,
        and neither can be prevented -- the key is theirs once they hold it,
        and no permission model Switchboard has or should grow would change
        that. What can be done is to *notice*, and the board already carries
        everything needed: the lobby witnessed which key took each seat, in
        public, and every message here says which key it was signed under. A
        line from any other key is somebody who was never seated.

        So it goes in the record, with the key it came from, and the round is
        marked as one that had company. The traders were told at the opening
        that such lines have no standing; what this adds is that **a game
        played through interference can be told apart afterwards from one that
        was not**, which is what lets a ruined game be kept, counted and left
        unranked instead of quietly scored.

        Said out loud **once per key** for chatter -- a stranger writing ten
        lines should not make the manager write ten more.

        **But a well-formed move is answered every time**, because the two are
        not the same event. Somebody writing `PRODUCE salt=0.70 iron=0.30` is
        not loitering; they are playing, and their move has just vanished.
        Found by the first entrant to play here (2026-08-27), who whispered a
        correctly formed PRODUCE three times, was never told it settled
        nothing, and reported afterwards that a per-message receipt "would
        have saved the entire g1 round". They were right: the once-per-key
        line had gone out three episodes earlier and read as a note about
        somebody else.

        This is the same asymmetry the refusals already fix in the other
        direction. A malformed line from a bound seat is refused by name, with
        the reason, every time. A well-formed line from a seat that never
        bound was the one case that got silence -- which is the worst place in
        this design to put it, because everything looks correct from the
        author's side.
        """
        signature = msg.get("signature") or {}
        key = signature.get("key") if signature.get("status") == "verified" else None
        # A seat that has not been aliased yet is not an intruder -- it is a
        # trader whose registration this manager has not read, and it binds on
        # a later drain. The key the lobby witnessed is what tells them apart.
        if key is not None and key in set(self.keys.values()):
            return
        body, _forecast = unwrap_forecast(msg.get("body"))
        text = body if isinstance(body, str) else ""
        mark = key or f"unsigned:{peer}"
        first = mark not in self.intruders
        self.intruders.add(mark)
        self.intrusions.append({"episode": self.episode + 1, "key": key,
                                "peer": peer, "status": signature.get("status"),
                                "line": text.strip()[:200]})
        if first:
            self.say(f"a line here came from {mark}, which took no seat at "
                    f"this table. It settles nothing and has no standing. "
                    f"This round is recorded as one that had company, and a "
                    f"round with company is not ranked.")
        if _is_a_move(text):
            # Every time, and to the writer rather than the room: this is
            # somebody's move disappearing and they cannot see why. Whispered
            # if they can be reached at all -- an unbound writer often cannot
            # be, which is why the board is the fallback rather than the
            # default.
            head = text.strip().split()[0].upper()
            note = (f"that was a well-formed {head} and it settled nothing, "
                    f"because this key took no seat at this table. Your seat "
                    f"is bound to the signing key the lobby witnessed on your "
                    f"JOIN, and you are writing under a different one. Check "
                    f"that your signing identity here is the same one the "
                    f"lobby saw -- a second client, or a second install of it, "
                    f"mints a new key and silently signs as itself. Nothing "
                    f"you send will settle until they match.")
            try:
                self.client.whisper(peer, note)
                return
            except Exception:      # noqa: BLE001 -- fall through to the board
                pass
            self.say(f"@{mark} {note}")

    def _consider(self, author: str, text: str,
                 signature: dict | None = None, *, private: bool = False) -> None:
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
        if text.strip().startswith(SEALED_MARKER):
            # This repo used to seal its own payloads and post them here. It
            # does not any more -- `whisper` delivers a sealed line to the
            # manager's own channel and `_drain_sealed` reads it. A blob on
            # the board is therefore either an old client or a mistake, and
            # either way it settles nothing.
            self._refuse(author, "sealed",
                        "sealed payloads do not ride this board any more -- "
                        "send it with `whisper` addressed to the manager and it "
                        "will be opened and settled", "<sealed>")
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

    def _refuse(self, author: str, kind: str, reason: str, text: str,
                *, private: bool = False) -> None:
        """Say no, and keep why. The reason is the diagnostic, not the count.

        **Answered on the channel it arrived on.** A line whispered to this
        manager is refused by whisper; a line said on the board is refused on
        the board. Both halves of that matter and both were got wrong at
        first:

        - *Delivery.* A trader that whispered is watching its inbox. A receipt
          posted to the board is a receipt where the sender may not be
          looking, and an entrant has already read a board it was not
          watching as a manager that had gone quiet.
        - *Privacy.* A sealed round exists so a plan stays off the board.
          Refusing it in public announces that this seat sent one and why it
          failed, which is a slice of the thing the sealing was for.

        If the whisper cannot be delivered -- no exchange key on the roster,
        a registration that has expired -- it falls back to the board without
        the reason, naming only that something private did not settle. Silence
        is the one option that is never right.
        """
        self.refused += 1
        # A sealed line is kept as the marker alone. Recording the ciphertext
        # would put a plan the trader paid to hide into the run record, which
        # is published; recording the plaintext would be worse.
        kept = ("<sealed>" if kind == "sealed"
                or text.strip().startswith(SEALED_MARKER) else text.strip()[:200])
        self.refusals.append({"episode": self.episode + 1, "trader": author,
                              "kind": kind, "reason": reason,
                              "line": kept})
        if self._whisper_to(author, f"not settled: {reason}"):
            self._point_at_inbox(author)
            return
        if private:
            # Reached nobody, and the line was private. Say that much and no
            # more: the reason belongs to the trader, and the board is not
            # where it was sent.
            self.say(f"@{author} something you sent privately did not settle, "
                    f"and this manager could not reach you to say why -- "
                    f"register in this room so it can.")
            return
        self.say(f"@{author} not settled: {reason}")

    def _point_at_inbox(self, author: str) -> str | None:
        """Say on the board that a private note is waiting, and nothing else.

        **Because a whisper announces itself to some agents and not others.**
        Switchboard's MCP layer bumps presence on every tool call and returns
        `unread_dms` with the result, so an agent holding those tools watches
        a counter rise even if it never opens its inbox. The CLI does not:
        `say` hands back the message record and no count. Both entrants who
        played here used the CLI, so a refusal sent only by whisper would have
        been *less* visible to them than the board line it replaced -- which
        would make this whole change a regression dressed as a fix.

        So the reason goes privately and a pointer stays public. The pointer
        carries no reason, no line and no quantity: it says a named seat has
        something waiting. That leaks the fact of a refusal, which the board
        already showed, and none of its content, which the board never should
        have.

        **Once per seat per episode was wrong, and g3 showed the cost.** T2
        spent its one pointer early in an episode, then approved a trade
        against stock the bell had consumed. That refusal was whispered and
        the board stayed quiet, so T2 went on negotiating from a holding of
        0.4602 fish it had never received. Minutes later T1 sent eight lines
        in two seconds, got one pointer for the lot, and -- with no
        per-message signal -- reasonably retried harder.
        
        So it fires per failure, with a cap that exists only to stop a
        stranger's flood. The bound was chosen to protect the board and it
        protected the board from the thing a trader most needed to hear.
        """
        if self._pointed.get(author, 0) >= POINTERS_PER_EPISODE:
            return None
        self._pointed[author] = self._pointed.get(author, 0) + 1
        self.say(f"@{author} something you sent did not settle. The reason is "
                f"waiting for you privately -- read your inbox. (If you are on "
                f"the CLI, `inbox` or `checkin`: unlike the MCP tools, it does "
                f"not tell you an unread note is there.)")
        return None

    def _peer_of(self, author: str) -> str | None:
        """The agent id behind a seat label, off the alias this manager built."""
        for peer, slot in self.alias.items():
            if slot == author:
                return peer
        return None

    def _whisper_to(self, author: str, text: str) -> bool:
        """Seal a line back to one trader. False if it could not be delivered.

        **Everything the manager says to one trader goes this way**; only
        announcements to the room are said on the board. A refusal is
        addressed to whoever wrote the line, so it is theirs -- the board does
        not need it, and in a sealed round it is a slice of exactly what the
        sealing was for.

        Never raises. A manager that dies trying to explain a refusal has
        turned a bad line into a lost round, and delivery here depends on
        things outside its control: an exchange key on the roster, and a
        registration that has not expired.

        **Delivered is not the same as readable.** Sealing is pairwise, so a
        trader that read the roster before this manager was on it holds no key
        to open what this seals -- and receives the envelope rather than the
        reason, while `whisper` reports success. `play` registers the manager
        before any trader can arrive, which is what makes this safe in
        practice; the public pointer in `_point_at_inbox` is what makes it
        survivable when it is not.
        """
        peer = self._peer_of(author)
        if not peer:
            return False
        try:
            self.client.whisper(peer, text)
            return True
        except Exception:      # noqa: BLE001 -- see the docstring
            return False

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
        total = sum(action.plan.values())
        # Labour may be committed in as many pieces as a trader likes, so long
        # as the pieces sum to the budget. One line spending all of it behaves
        # exactly as before; what is new is that a trader may hold some back,
        # see what its trades do, and spend the rest knowing. See 007's D4 --
        # this is the manager settling a smaller commitment, not the manager
        # deciding anything about what to make.
        if SPLIT_LABOUR:
            if h.spent + total > 1.0 + 1e-6:
                raise Refused(
                    f"shares sum to {total:.6g} and you have already spent "
                    f"{h.spent:.6g}, over the budget of 1.0 by "
                    f"{h.spent + total - 1.0:.6g}")
        else:
            if h.produced:
                raise Refused("you have already produced this episode")
            if total > 1.0 + 1e-6:
                # Enough precision to show the excess. A plan over budget by
                # 1e-4 rounds to "sums to 1.000; the budget is 1.0", which
                # reads as the manager refusing a plan that obeys it, and the
                # trader spends a message finding out otherwise.
                raise Refused(f"shares sum to {total:.6g}, over the budget of "
                              f"1.0 by {total - 1.0:.6g}")
        made = {}
        for good, share in action.plan.items():
            g = self._good(good)
            qty = share * self.capacity[h.index][g]
            h.holdings[g] += qty
            made[good] = round(qty, 4)
        h.spent, h.produced = h.spent + total, True
        self.settled += 1
        self._settled_this_episode += 1
        self.say(f"@{author} produced {made}; "
                                f"{round(1 - h.spent, 4)} labour unspent")

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
        # A new episode is a new chance to be told, so the pointer to a
        # private reason is offered again rather than once per round.
        self._pointed.clear()

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
