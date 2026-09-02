"""The lobby: a reader of its board and a settler of tables.

Same shape as the island manager, one level up -- see `games/island.md`,
"The lobby is a room". It recognises `OPEN`, `JOIN` and `MANAGE`, settles a
table the moment it is full and managed, and otherwise does nothing: it does
not choose partners, does not choose islands, and does not rank anybody.

**It hands out an invite and a time, and then it is done.** It never launches
an entrant's agent, and it never starts the island manager for the table it
just settled. This module is the lobby's settlement only; the process that
picks a settled table up and actually deals it is `run_game.py`, which embeds
a lobby of its own for the reason its docstring gives -- the seed is drawn at
settlement and never posted, so whoever settles a table is the only party who
can deal it.

A seat is claimed by a Switchboard peer, not by the name typed after `as` --
the name is what a `JOIN` line is addressed by and what the settlement shows,
but the *seat* belongs to whichever peer wrote the line, so one peer cannot
seat itself twice at the same table by typing a different name each time. That
peer is also bound to the signing key its `JOIN` was verified under, witnessed
once here and posted with the seat (`_join`, `_witness`), which is what lets
the island manager tell an impostor from the real seat later in the round.

**The lobby is a public room whose key is published -- not a room without
one.** Everything on its board is meant to be readable by anybody, so the
obvious move is to run it in plaintext and hand nobody anything. That does not
work, and the reason is worth keeping: Switchboard signs a message *inside*
the seal, so that the transport cannot strip the signature without breaking
the AEAD tag. A plaintext room therefore carries **no signatures at all**, and
a seat here binds by a witnessed signing key -- so a keyless lobby refuses
every `JOIN` it receives. The key is what turns attribution on; publishing it
is what lets strangers in. It protects nothing and is not meant to.

What must stay private travels sealed to one peer (`whisper`), unaffected
either way: it seals to the recipient's exchange key, so every other holder of
the workspace key -- which here is everybody -- still cannot open it. And the
table's own room always gets a key of its own (`_settle`), which is a real
secret and is handed only to its seats.

**Two things this process needs that its board does not carry.** A settled
table's seed is deliberately never posted, so a restarted lobby cannot read
its own past settlements back off the board -- it would draw a second seed and
mint a second room for a table that already has one. So this keeps its state
in a file (`state_path`), and holds its channel against another lobby draining
the same board (`hold`). Neither is a new primitive on the board: one is an
operator's file, the other is one line of board text saying who is reading.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import secrets
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from switchboard.client import Client
from switchboard.crypto import generate_key
from switchboard.invite import Invite
from switchboard.timing import unwrap_forecast

from .protocol import (EPISODE_SECONDS_DEFAULT, GOODS_DEFAULT, Join, Malformed,
                       Manage, Open, parse)

#: How long an OPEN table waits to fill and be claimed before it lapses.
#: Chosen, not derived -- long enough that a human posting JOIN by hand is not
#: racing the clock, short enough that a lobby does not accumulate tables
#: nobody is coming back to.
TABLE_TTL = 900.0

#: Lead time between a table settling and the round it announces as its
#: start. Gives every seated entrant a moment to see the invite and connect
#: before anything is expected of them. This module still starts nothing --
#: it hands out an invite and a time -- but the time is no longer decorative:
#: it is settled onto the table as `Table.opens_at`, and `run_game` will not
#: call a seat absent before it (`play`). A board that announces a time and
#: then runs the clock from some other one is a board that lies.
OPEN_LEAD = 120.0

#: The line one lobby posts to say it is the one reading this channel. Two
#: lobbies draining one board settle every table twice -- two seeds, two room
#: keys, two invites -- and the game that follows is silence
#: (`run_game.SettledTwice`, which is where that failure was first paid for).
#: The newest holder wins and the rest stand down, so starting a second lobby
#: takes the channel over rather than corrupting it.
HOLD = "LOBBY holding this channel: "

#: How many tables one peer may have forming at once. A lobby faces strangers,
#: and OPEN costs its author nothing: without a cap, one peer can mint tables
#: until every reader is scrolling past its noise, and every one of them sits
#: for the full TTL. Two, so that opening a second table while waiting on the
#: first is ordinary and a hundred is not. It bounds only what is *forming* --
#: settling or lapsing a table frees the slot, so a busy honest opener is
#: never held back for long.
MAX_FORMING_PER_PEER = 2

#: How many tables may be **open for a seat** at once, across the whole lobby.
#: A table is open for a seat while it is neither settled nor lapsed --
#: *empty* if nobody has joined it yet, *forming* once somebody has; both are
#: a place an entrant can sit down, and that is the only difference this cap
#: cares about.
#:
#: Decided by Gal, 2026-08-29. `MAX_FORMING_PER_PEER` bounds one peer and this
#: bounds the room, which are different failures: the first is somebody
#: minting tables for the noise, the second is an honest crowd each opening
#: one and leaving a page of half-empty tables that split the entrants between
#: them and lapse together. **Two seats' worth of door is enough door**: an
#: arriving entrant should be choosing between a couple of tables, not
#: scrolling. Past that, opening is refused *and told where to sit instead* --
#: a refusal that names the tables you could join is not an obstruction.
MAX_JOINABLE = 2

#: How many tables may exist at once in any live state -- open for a seat, or
#: settled and still being played. Five, so that two forming plus a few in
#: progress is ordinary and a runaway is not. It is not the same limit as
#: `run_game --max-games`, which caps what **one host will pay to manage** at
#: once; this caps what the **board will carry**, and a lobby whose tables are
#: managed by strangers still wants one.
MAX_TABLES = 5

#: How long after its last bell a settled table still counts against
#: `MAX_TABLES`. The lobby cannot see the table's own room, so it cannot be
#: told the game ended -- what it has is the schedule it announced itself:
#: play starts at `opens_at` and runs `episodes x seconds`. This is the slack
#: after that for the bell, the record, the archive comparison and a manager
#: that started a little late.
#:
#: Deliberately an over-estimate. Holding a slot slightly too long turns one
#: extra `OPEN` away for a minute; freeing it too early lets the board fill
#: with tables whose games are still running, which is the thing being capped.
PLAY_SLACK = 180.0

#: How many messages one drain reads. The hub keeps a board for about an hour,
#: and this is the slice of it a poll takes; a board busier than this between
#: two polls loses its middle, which `Lobby._window` notices out loud rather
#: than letting it pass as quiet.
WINDOW = 500


def _stamp(ts: float) -> str:
    """An absolute UTC clock time, the same convention `run_v3.py` uses for
    every deadline it posts -- a relative "in 120s" is only true at the
    instant it was written, and nobody here is prompted to read it promptly.
    """
    return time.strftime("%H:%M:%SZ", time.gmtime(ts))


@dataclass
class Table:
    id: str
    traders: int
    episodes: int
    rounds: int
    opened_at: float
    #: The peer that opened it, so that one peer cannot mint tables without
    #: limit (`MAX_FORMING_PER_PEER`).
    opened_by: str = ""
    #: Part of the level, so it is fixed when the table opens: an entrant has to
    #: know the format before it decides to sit down, and two rounds are only
    #: comparable if they were drawn over the same number of goods.
    goods: int = GOODS_DEFAULT
    #: How long each episode runs, settled at OPEN like `goods` and for the
    #: same reason: it is part of the level, and an entrant has to know it
    #: before it decides to sit down. Until g6 this was a host-wide flag that
    #: appeared nowhere in the record -- see `protocol.EPISODE_SECONDS_ALLOWED`.
    seconds: int = EPISODE_SECONDS_DEFAULT
    #: peer id -> the name it joined under. Insertion order is seat order:
    #: the first peer to join is T1, the second T2, and so on -- the same
    #: labelling `island/manager.py` defaults to, so a settled table's seats
    #: are already the names the island manager will use.
    seats: dict[str, str] = field(default_factory=dict)
    #: peer id -> the signing key its JOIN was verified under -- witnessed
    #: once, in public, per "Seats, and who is in one". A seat with no entry
    #: here was never seated: `_join` refuses a JOIN it cannot verify rather
    #: than seating it keyless.
    keys: dict[str, str] = field(default_factory=dict)
    #: peer id -> the nonce its JOIN brought, if it brought one. A table where
    #: every seat did is drawn by commit-reveal (`Lobby._settle`) and its draw
    #: is checkable afterwards by anybody.
    nonces: dict[str, str] = field(default_factory=dict)
    #: This lobby's commitment, posted when the table opens and before any
    #: JOIN can have been read: `sha256(nonce)`.
    commit: str = ""
    #: The nonce behind that commitment. Secret until the game ends, and then
    #: published with the replay -- which is the whole mechanism: a lobby that
    #: could not see the seats' nonces when it committed cannot have chosen
    #: the island, and anybody can check the arithmetic afterwards.
    nonce: str = ""
    #: How the seed was drawn: "commit-reveal" or "unverified".
    draw: str = "unverified"
    #: peer id -> the exchange key it had published when it sat down. Read off
    #: this room's roster rather than taken from the JOIN line: a key an
    #: entrant asserts about itself is not a key anybody can seal to.
    #:
    #: **Advisory only.** What decides whether a game is sealed is whether
    #: every seat publishes one in the *table's* room, which the manager
    #: checks at deal time (`run_game.sealable`). This is here so the
    #: settlement line can tell an entrant what to expect.
    boxes: dict[str, str] = field(default_factory=dict)
    manager: str | None = None
    manager_peer: str | None = None
    #: The signing key the winning MANAGE was verified under. Witnessed for
    #: the same reason a seat's is: a name typed on a board proves nothing,
    #: and the claimant is the one party whose absence means no game happens
    #: at all.
    manager_key: str | None = None
    settled: bool = False
    lapsed: bool = False
    workspace: str | None = None
    #: When the board said this table opens -- settled once, so the line the
    #: entrants read and the clock the manager keeps come from one number.
    opens_at: float | None = None
    #: Drawn at settlement, never before -- see `Lobby._settle`. Not on the
    #: board: `barter.economy.draw_island(agents, goods, seed)` is public and
    #: deterministic, so a seed posted where entrants can read it hands them
    #: everybody's tastes before the round starts. It reaches the table's
    #: manager over `run_lobby.py`'s own log for now -- carrying it to a
    #: specific seat over the board is the sealed channel, build-order item
    #: 2c, and is not done here.
    seed: int | None = None
    #: The table's room, encoded, as handed to its seats. **Sealed to each
    #: seat, never posted** since 2026-09-02 (Gal): the room key is what makes
    #: a seat a seat, and a lobby that posted the invite on its public board
    #: handed the room to everybody who could read the lobby -- which
    #: `island.md` ("A room the strangers can talk in") had named as the one
    #: leak left. Kept here, in the private state file beside the seed, so a
    #: restarted runner can play the table it settled.
    invite: str = ""

    def verifiable(self) -> bool:
        """Whether this table's island can be shown to have been drawn rather
        than chosen: every seat brought a nonce, and the lobby committed to
        its own before it could read any of them."""
        return bool(self.seats) and bool(self.commit) and all(
            p in self.nonces for p in self.seats)

    def sealable(self) -> bool:
        """Whether every seat gave the manager something to seal to, which is
        what a ranked game needs and a practice game does without."""
        return bool(self.seats) and all(p in self.boxes for p in self.seats)

    def full(self) -> bool:
        return len(self.seats) >= self.traders

    def joinable(self) -> bool:
        """Somewhere an entrant can still sit down: **empty** if no seat has
        been claimed, **forming** once one has. Neither settled nor lapsed."""
        return not (self.settled or self.lapsed)

    def playing(self, now: float, slack: float = PLAY_SLACK) -> bool:
        """Settled, and its announced round has not plainly finished yet.

        **Estimated from the schedule this table itself announced**, because
        the lobby has no view into the table's own room and nothing tells it a
        game ended. `opens_at` is on the board, `episodes` and `seconds` were
        settled at `OPEN`, so the last bell falls at
        `opens_at + episodes x seconds` and this allows `slack` past it.

        A table settled without an announced start counts as playing: that is
        the one case where guessing short would drop a live game out of the
        count entirely.

        If a stranger's manager ever runs long enough for this to matter, the
        fix is for the manager to say so on the lobby board when it finishes
        -- a board write, in keeping with everything else here -- and for this
        to believe that in preference to its own arithmetic.
        """
        if not self.settled or self.lapsed:
            return False
        if self.opens_at is None:
            return True
        return now < self.opens_at + self.episodes * self.seconds + slack

    def ready(self) -> bool:
        return self.full() and self.manager is not None and not self.settled

    def label(self, peer: str) -> str:
        return f"T{list(self.seats).index(peer) + 1}"


@dataclass
class Lobby:
    """Reads the lobby channel from a cursor; settles the tables it recognises."""

    client: Client
    channel: str = "lobby"
    table_ttl: float = TABLE_TTL
    open_lead: float = OPEN_LEAD
    #: Injectable so a test can settle a table's lapse without sleeping 900s.
    clock: Callable[[], float] = time.time
    #: Injectable so a test can pin the seed a settlement draws rather than
    #: asserting against whatever `secrets` happened to produce.
    draw_seed: Callable[[], int] = lambda: secrets.randbits(63)
    #: Injectable for the same reason `draw_seed` is: a test pins the lobby's
    #: half of a commit-reveal rather than asserting against `secrets`.
    draw_nonce: Callable[[], str] = lambda: secrets.token_hex(16)
    #: Where this lobby's own state is kept across restarts. Optional: a test
    #: and a one-shot drain need none, a standing process does.
    state_path: Path | None = None
    #: The open handle carrying this process's flock on the state file.
    _lock: object | None = None
    #: This process's holder token, once `hold()` has claimed the channel.
    holder: str | None = None
    #: Set when a newer lobby took the channel over. A stood-down lobby reads
    #: nothing and settles nothing; it does not compete for the board.
    stood_down: bool = False
    #: The highest `seq` this lobby has read. Kept to notice a board that
    #: outran the window rather than to order anything -- see `_window`.
    last_seq: int = 0
    #: How many times that has happened. In the state file, so a restart does
    #: not report a clean board it never had.
    missed: int = 0
    seen: set[str] = field(default_factory=set)
    tables: dict[str, Table] = field(default_factory=dict)
    settled: int = 0
    refused: int = 0
    talk: int = 0
    refusals: list[dict] = field(default_factory=list)
    _names: dict[str, str] = field(default_factory=dict)
    _exchange: dict[str, str] = field(default_factory=dict)
    _next: int = 1

    # --- holding the channel ---------------------------------------------

    def hold(self) -> str:
        """Say on the board that this process is the lobby reading it.

        Not a lock and not a lease -- a lobby that dies holds nothing, and the
        next one to start says so and takes over. It exists because the
        alternative is two lobbies settling the same table into two rooms,
        which is invisible until a game plays to nobody. See `HOLD`.
        """
        self.holder = secrets.token_hex(4)
        self.present()
        self.say(f"{HOLD}{self.holder}")
        return self.holder

    def present(self) -> None:
        """Put this lobby on the roster, with the exchange key a seat needs to
        open what it is whispered.

        A whisper is sealed pairwise, and the recipient opens it with the
        *sender's* published exchange key -- read off the roster, so a sender
        that never registered is a sender whose envelopes nobody can open. A
        long TTL, renewed by the runner's heartbeat, so the row does not lapse
        two minutes after a lobby that will settle tables for days."""
        try:
            self.client.register(name="lobby", kind="local", branch="main",
                                 task=f"reading {self.channel}",
                                 ttl=3600.0, back_in=300.0)
        except Exception as exc:      # noqa: BLE001 -- a roster row is not a game
            print(f"lobby not on the roster: {exc!r}", flush=True)

    def _stand_down(self, rows: list[dict]) -> bool:
        """Whether a newer lobby now holds this channel. Said once, out loud:
        a process that has gone quiet should say why it went quiet."""
        if self.holder is None:
            return False
        holders = [body[len(HOLD):].strip()
                   for msg in rows
                   if isinstance(body := msg.get("body"), str)
                   and body.startswith(HOLD)]
        if not holders or holders[-1] == self.holder:
            return False
        if not self.stood_down:
            self.stood_down = True
            self.say(f"lobby {self.holder} stands down: {holders[-1]} holds "
                    f"this channel now. Two lobbies settle every table twice, "
                    f"so this one stops reading.")
        return True

    # --- state across restarts --------------------------------------------

    def lock(self) -> None:
        """Take an exclusive lock on the state file, for this process's life.

        `hold()` keeps two lobbies off one board; this keeps two off one file.
        They are different failures: the board is where the second lobby is
        visible, and the state file is where it is not -- two writers simply
        interleave, and the loser's seeds are gone with no line anywhere
        saying so.

        Advisory and process-scoped, which is what `flock` gives and all that
        is wanted: a lock file left behind by a killed process is not a lock,
        so a restart is never blocked by its own corpse.
        """
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        path = self.state_path.with_suffix(self.state_path.suffix + ".lock")
        handle = path.open("w")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise Held(
                f"another lobby already holds {path} -- two processes writing "
                f"one state file interleave their seeds, and the one that "
                f"loses says nothing. Point this one at its own --state, or "
                f"stop the other.") from None
        handle.write(f"{os.getpid()}\n")
        handle.flush()
        self._lock = handle

    def save(self) -> None:
        """Write what the board does not carry: the seeds, and which messages
        have already been acted on.

        The board is still the record of what happened. This is only what a
        *reader* of it needs to not act twice -- a settled table's seed is
        never posted (see `Table.seed`), so a lobby that forgot it would draw
        another one and mint a second room for a table that already has one.
        """
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"next": self._next, "seen": sorted(self.seen),
                   "last_seq": self.last_seq, "missed": self.missed,
                   "tables": {tid: asdict(t) for tid, t in self.tables.items()}}
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=1) + "\n")
        tmp.replace(self.state_path)

    def load(self) -> None:
        """Restore a previous process's state, if there is any. A missing file
        is the ordinary first run, not an error."""
        if self.state_path is None or not self.state_path.exists():
            return
        payload = json.loads(self.state_path.read_text())
        self._next = payload.get("next", self._next)
        self.last_seq = payload.get("last_seq", 0)
        self.missed = payload.get("missed", 0)
        self.seen = set(payload.get("seen", ()))
        self.tables = {tid: Table(**row)
                       for tid, row in payload.get("tables", {}).items()}

    # --- reading -------------------------------------------------------

    def say(self, text: str) -> None:
        self.client.post(self.channel, text)

    def _display(self, peer: str) -> str:
        """The peer's registered name, or the peer id itself when there is
        none yet -- an honest fallback rather than inventing one."""
        return self._names.get(peer, peer)

    def drain(self) -> None:
        """Read whatever has appeared since last time, then check lapses.

        Never blocks anyone: this is a poll, not a wait, the same contract
        `island/manager.py`'s `drain()` keeps.
        """
        # The roster first, and not only for the names: fetching it is how the
        # client learns the keys it verifies signatures against, so a history
        # read before it would witness nothing and refuse every JOIN.
        roster = self.client.agents()
        self._names = {a["agent_id"]: a["name"] for a in roster if a.get("name")}
        # What a seat can be sealed to, if it has published one. Read here
        # rather than trusted from a JOIN line -- see `Table.boxes`.
        self._exchange = {a["agent_id"]: a["exchange_key"] for a in roster
                          if isinstance(a.get("exchange_key"), str)
                          and a.get("exchange_key")}
        rows = sorted(self.client.history(self.channel, limit=WINDOW),
                      key=lambda r: r.get("seq", 0))
        if self._stand_down(rows):
            return
        self._window(rows)
        for msg in rows:
            mid = str(msg.get("id"))
            if mid in self.seen:
                continue
            self.seen.add(mid)
            peer = str(msg.get("from") or "")
            if not peer or peer == self.client.agent_id:
                continue
            body, _forecast = unwrap_forecast(msg.get("body"))
            self._consider(peer, body if isinstance(body, str) else "",
                           msg.get("signature"))
        self._forget(rows)
        self._sweep()
        self.save()

    def _window(self, rows: list[dict]) -> None:
        """Say so when the board outran the window between two drains.

        The lobby reads the last `WINDOW` messages each time. If more than
        that arrive in one interval, the oldest of them fall out before they
        are ever read -- an `OPEN` nobody answered, a `JOIN` that was never
        seated, and no sign anywhere that anything was dropped.

        `seq` is a hub-wide autoincrement, so a gap between consecutive rows
        is ordinary and proves nothing. What does prove it is the *window no
        longer reaching back to where this lobby got to*: if the oldest row
        now sits above the highest seq already read, everything between the
        two is gone. Said out loud on the board, because a lobby that missed
        somebody should not look like a lobby nobody wrote to.
        """
        if not rows:
            return
        seqs = [int(r.get("seq", 0)) for r in rows]
        oldest, newest = seqs[0], seqs[-1]
        if self.last_seq and oldest > self.last_seq + 1:
            self.missed += 1
            self.say(f"lines were posted here that this lobby never read: the "
                    f"board moved from seq {self.last_seq} to {oldest} between "
                    f"reads, past a {WINDOW}-message window. Anything asked in "
                    f"between went unanswered -- please post it again.")
        self.last_seq = max(self.last_seq, newest)

    def _forget(self, rows: list[dict]) -> None:
        """Drop message ids that have fallen out of the window we read.

        A message older than the last `WINDOW` on this channel is never delivered
        here again, so remembering it forever is only a file that grows. Skip
        a window that came back empty rather than treating it as evidence.
        """
        if not rows:
            return
        self.seen &= {str(msg.get("id")) for msg in rows}

    def _consider(self, peer: str, text: str, signature: dict | None = None) -> None:
        try:
            action = parse(text)
        except Malformed as exc:
            self._refuse(peer, "malformed", str(exc), text)
            return
        if action is None:
            self.talk += 1
            return
        try:
            if isinstance(action, Open):
                self._open(peer, action)
            elif isinstance(action, Join):
                self._join(peer, action, signature)
            elif isinstance(action, Manage):
                self._manage(peer, action, signature)
        except Refused as exc:
            self._refuse(peer, type(action).__name__.lower(), str(exc), text)

    def _refuse(self, peer: str, kind: str, reason: str, text: str) -> None:
        self.refused += 1
        self.refusals.append({"peer": peer, "kind": kind, "reason": reason,
                              "line": text.strip()[:200]})
        self.say(f"@{self._display(peer)} not settled: {reason}")

    # --- settling --------------------------------------------------------

    def _open(self, peer: str, action: Open) -> None:
        now = self.clock()
        forming = [t for t in self.tables.values()
                   if t.opened_by == peer and t.joinable()]
        if len(forming) >= MAX_FORMING_PER_PEER:
            raise Refused(
                f"you already have {len(forming)} tables forming "
                f"({', '.join(t.id for t in forming)}) -- fill one, or wait "
                f"for it to lapse, before opening another")

        # **The room's cap, not the peer's**, and the reason it names the
        # tables: somebody posting OPEN wants a game, and a lobby with two
        # tables already waiting for seats has one to offer them. Turning them
        # away without saying where to sit would make the cap read as the
        # lobby being closed.
        joinable = sorted((t.id for t in self.tables.values() if t.joinable()))
        if len(joinable) >= MAX_JOINABLE:
            raise Refused(
                f"{len(joinable)} tables are already open for a seat "
                f"({', '.join(joinable)}) -- JOIN one of those rather than "
                f"opening a third. A table opens again as soon as one of them "
                f"fills or lapses")

        live = joinable + sorted(t.id for t in self.tables.values()
                                 if t.playing(now))
        if len(live) >= MAX_TABLES:
            raise Refused(
                f"this lobby is at its limit of {MAX_TABLES} tables "
                f"({', '.join(live)}) -- some are still being played. Wait "
                f"for one to finish, or JOIN one that is open for a seat")
        table = Table(id=f"g{self._next}", traders=action.traders,
                     episodes=action.episodes, rounds=action.rounds,
                     goods=action.goods, seconds=action.seconds,
                     opened_at=self.clock(), opened_by=peer)
        # Committed here, before a single JOIN exists, which is the only
        # moment at which committing means anything: a lobby that has not
        # seen the seats' nonces cannot pick a seed to suit anybody.
        table.nonce = self.draw_nonce()
        table.commit = hashlib.sha256(table.nonce.encode()).hexdigest()
        self._next += 1
        self.tables[table.id] = table
        self.settled += 1
        # The goods are announced with the rest of the format. An entrant reads
        # this to know what island it is sitting down at -- the rules it hands
        # its agent count the goods by name, so a table that kept the number to
        # itself would have every trader briefed on the wrong island.
        self.say(f"{table.id} commits {table.commit} -- bring "
                f"nonce=<16-64 hex digits> on your JOIN and this table's "
                f"island is drawn from all of them together")
        self.say(f"{table.id} is forming: {table.traders} traders, "
                f"{table.goods} goods, "
                f"{table.episodes} episodes of {table.seconds}s, "
                f"{table.rounds} round"
                f"{'s' if table.rounds != 1 else ''} -- JOIN {table.id} as "
                f"<name>, or MANAGE {table.id}")

    def _table(self, table_id: str) -> Table:
        table = self.tables.get(table_id)
        if table is None:
            raise Refused(f"no such table {table_id!r}")
        if table.lapsed:
            raise Refused(f"{table_id} lapsed -- OPEN a new one")
        if table.settled:
            raise Refused(f"{table_id} is already settled")
        return table

    def _join(self, peer: str, action: Join, signature: dict | None) -> None:
        """A name typed on a board proves nothing -- see `games/island.md`,
        "Seats, and who is in one". So a `JOIN` is refused unless Switchboard
        itself already verified it against a key this peer announced; a seat
        is bound to that key, witnessed once here, in public, before the
        table can ever be full.
        """
        table = self._table(action.table)
        if peer in table.seats:
            raise Refused(f"you already hold seat "
                          f"{table.label(peer)} at {action.table}")
        if action.name in table.seats.values():
            raise Refused(f"{action.name!r} is already seated at {action.table}")
        if table.full():
            raise Refused(f"{action.table} is full")
        key = self._witness(signature, "JOIN")
        table.seats[peer] = action.name
        table.keys[peer] = key
        exchange = self._exchange.get(peer)
        if exchange:
            table.boxes[peer] = exchange
        if action.nonce:
            table.nonces[peer] = action.nonce.lower()
        self.settled += 1
        self.say(f"{action.table} seat {table.label(peer)} = {action.name}, "
                f"key {key}"
                f"{', sealed' if exchange else ', in the clear'}"
                f"{', nonce ' + action.nonce.lower() if action.nonce else ''} "
                f"({len(table.seats)}/{table.traders})")
        if table.ready():
            self._settle(table)

    @staticmethod
    def _witness(signature: dict | None, kind: str = "JOIN") -> str:
        """The key a message was verified under, or a refusal naming why not.

        Distinct reasons for distinct causes, the same discipline the rest of
        this module keeps: unsigned is not the same fact as unknown, and
        unknown is not the same fact as forged, however alike all three look
        from "the seat did not get bound".
        """
        status = (signature or {}).get("status")
        if status is None or status == "unsigned":
            raise Refused(f"{kind} must be signed -- this message carried no "
                          f"signature to witness")
        if status == "unknown":
            raise Refused(f"no signing key known for you yet -- register on "
                          f"this room before {kind}")
        if status != "verified":
            raise Refused(f"the signature on this {kind} does not match any "
                          f"key you have announced")
        return signature["key"]

    def _manage(self, peer: str, action: Manage,
                signature: dict | None = None) -> None:
        """Claim the manager's chair -- witnessed, exactly like a seat.

        A seat that cannot be verified is refused, and the claimant is the
        one party whose absence means the game does not happen at all: it
        draws nothing and deals nothing, but a table it has claimed is a
        table nobody else will offer to run. So the same rule applies to it,
        for the same reason.
        """
        table = self._table(action.table)
        if table.manager is not None:
            raise Refused(f"{action.table} is already managed by "
                          f"{table.manager}")
        key = self._witness(signature, "MANAGE")
        table.manager, table.manager_peer, table.manager_key = (
            self._display(peer), peer, key)
        self.settled += 1
        self.say(f"{action.table} will be managed by {table.manager}, "
                f"key {key}")
        if table.ready():
            self._settle(table)

    def _settle(self, table: Table) -> None:
        """A table with every seat filled and a manager claimed: draw its
        island, mint the game's own room, and hand out the invite. This is
        the whole of the lobby's job -- see the module docstring for what it
        deliberately does not do next.

        The seed is drawn here and nowhere earlier -- "never before the
        table forms" (`games/island.md`, "The island is drawn, not chosen")
        -- so nothing about who ended up seated, or who claimed to manage,
        could have been chosen knowing it in advance.
        """
        table.settled = True
        self.settled += 1
        if table.verifiable():
            table.seed, table.draw = self._commit_reveal(table), "commit-reveal"
        else:
            table.seed, table.draw = self.draw_seed(), "unverified"
        table.workspace = f"{self.client.config.workspace}-{table.id}"
        # **Always minted, whatever the lobby is.** The lobby is meant to be a
        # public room -- no key to hand out is the simplest answer to "how
        # does a stranger get in" -- but a table is not: its room key is what
        # makes a seat a seat, and deriving it from the lobby's own state
        # meant a public lobby silently dealt every game in a room anybody
        # holding the hub token could walk into.
        key = generate_key()
        invite = Invite(url=self.client.config.url, workspace=table.workspace,
                        token=self.client.config.token, key=key,
                        note=f"{table.id}: {table.traders} traders, "
                             f"{table.episodes} episodes")
        table.opens_at = self.clock() + self.open_lead
        roster = ", ".join(f"{label} = {name}"
                           for label, name in zip(
                               (table.label(p) for p in table.seats),
                               table.seats.values()))
        drawn = ("drawn from every nonce at this table, this lobby's included "
                 f"(committed {table.commit})" if table.verifiable()
                 else "drawn by this lobby alone -- not every seat brought a "
                      "nonce, so the draw is not checkable afterwards")
        note = "" if table.sealable() else (
            "; PRACTICE as things stand -- not every seat had an exchange key "
            "published when it sat down, so the private half would be public "
            "and the game not ranked. Register with a client that publishes "
            "one and the manager will seal to it")
        self.say(f"{table.id} is full: {roster}; managed by "
                f"{table.manager}; opens {_stamp(table.opens_at)}{note}")
        self.say(f"{table.id}: the island is {drawn}")
        self._hand_out(table, invite)

    def _hand_out(self, table: Table, invite: Invite) -> None:
        """The room, to its seats and its manager, and to nobody else.

        **Whispered, not posted.** Decided by Gal, 2026-09-02. The invite is
        a read-write credential for the table's room, and until now it went on
        this public board in the clear, one line after the settlement -- so
        the room "held only its seats" in name, and anybody reading the lobby
        held its key. `whisper` seals to one peer's published exchange key,
        which is what a sealed seat is (`Table.boxes`), so every table that
        can be sealed at all can be handed its room the same way.

        A table that cannot -- a seat with no exchange key -- gets the
        invite in the clear, as before, and the settlement line has already
        said it plays as practice. The weaker thing is kept and says so; it
        is not dressed as the stronger one.

        One public line either way, naming who was given the room: the
        runner counts those lines to refuse a table two lobbies settled
        (`run_game.pending_invite`), and a reader of the board can see the
        room was handed out without being handed it.
        """
        table.invite = invite.encode()
        peers = list(table.seats)
        if table.manager_peer and table.manager_peer not in peers:
            peers.append(table.manager_peer)
        if not all(p in self._exchange for p in peers):
            self.say(f"{table.id} invite: {table.invite}")
            return
        self.present()
        body = f"{table.id} invite: {table.invite}"
        for peer in peers:
            self.client.whisper(peer, body)
        who = ", ".join(table.label(p) for p in table.seats)
        self.say(f"{table.id} invite: sealed to {who} and the manager -- "
                 f"read your inbox (roster first); it is not on this board")

    @staticmethod
    def _commit_reveal(table: Table) -> int:
        """The seed as the hash of every nonce at this table, the lobby's own
        included.

        Sorted, so that the order seats happened to arrive in cannot change
        the island; 63 bits, because that is what `random.Random` is seeded
        with everywhere else here. The lobby's nonce stays secret until the
        replay, so nobody can compute the seed while the game is on -- and
        once it is published, anybody can, from lines that were on the board
        before the draw.
        """
        material = "|".join([table.nonce] + sorted(table.nonces.values()))
        digest = hashlib.sha256(material.encode()).digest()
        return int.from_bytes(digest[:8], "big") >> 1

    def _sweep(self) -> None:
        """Lapse whatever has sat past its deadline unfilled or unmanaged.

        Timing is the one thing the lobby enforces on its own clock rather
        than in response to a line -- a table nobody is coming back to has
        to expire without anybody having to say so.
        """
        now = self.clock()
        for table in self.tables.values():
            if table.settled or table.lapsed:
                continue
            if now - table.opened_at < self.table_ttl:
                continue
            table.lapsed = True
            reason = ("not full" if not table.full()
                      else "not managed")
            self.say(f"{table.id} lapsed: {reason} within "
                    f"{int(self.table_ttl)}s "
                    f"({len(table.seats)}/{table.traders} seated"
                    f"{', managed by ' + table.manager if table.manager else ''})")


class Refused(Exception):
    """A well-formed line the lobby will not settle, with a reason."""


class Held(Exception):
    """Another process holds this lobby's state file."""
