"""The lobby: a reader of its board and a settler of tables.

Same shape as the island manager, one level up -- see `games/island.md`,
"The lobby is a room". It recognises `OPEN`, `JOIN` and `MANAGE`, settles a
table the moment it is full and managed, and otherwise does nothing: it does
not choose partners, does not choose islands, and does not rank anybody.

**It hands out an invite and a time, and then it is done.** It never launches
an entrant's agent, and it never starts the island manager for the table it
just settled -- that is for whoever claimed `MANAGE` to do, out of band. This
module is the lobby's settlement only; the standing island-manager process
that would actually run a settled table is separate, unbuilt work (build-order
item 2 onward in `games/island.md`).

A seat is claimed by a Switchboard peer, not by the name typed after `as` --
the name is what a `JOIN` line is addressed by and what the settlement shows,
but the *seat* belongs to whichever peer wrote the line, so one peer cannot
seat itself twice at the same table by typing a different name each time. That
peer is also bound to the signing key its `JOIN` was verified under, witnessed
once here and posted with the seat (`_join`, `_witness`), which is what lets
the island manager tell an impostor from the real seat later in the round.

**Two things this process needs that its board does not carry.** A settled
table's seed is deliberately never posted, so a restarted lobby cannot read
its own past settlements back off the board -- it would draw a second seed and
mint a second room for a table that already has one. So this keeps its state
in a file (`state_path`), and holds its channel against another lobby draining
the same board (`hold`). Neither is a new primitive on the board: one is an
operator's file, the other is one line of board text saying who is reading.
"""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from switchboard.client import Client
from switchboard.crypto import generate_key
from switchboard.invite import Invite
from switchboard.timing import unwrap_forecast

from .protocol import GOODS_DEFAULT, Join, Malformed, Manage, Open, parse

#: How long an OPEN table waits to fill and be claimed before it lapses.
#: Chosen, not derived -- long enough that a human posting JOIN by hand is not
#: racing the clock, short enough that a lobby does not accumulate tables
#: nobody is coming back to.
TABLE_TTL = 900.0

#: Lead time between a table settling and the round it announces as its
#: start. Gives every seated entrant a moment to see the invite and connect
#: before anything is expected of them -- the island manager is not started
#: by this module, so nothing actually opens at this time yet; it is
#: informational until build-order item 2 makes it real.
OPEN_LEAD = 120.0

#: The line one lobby posts to say it is the one reading this channel. Two
#: lobbies draining one board settle every table twice -- two seeds, two room
#: keys, two invites -- and the game that follows is silence
#: (`run_game.SettledTwice`, which is where that failure was first paid for).
#: The newest holder wins and the rest stand down, so starting a second lobby
#: takes the channel over rather than corrupting it.
HOLD = "LOBBY holding this channel: "


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
    #: Part of the level, so it is fixed when the table opens: an entrant has to
    #: know the format before it decides to sit down, and two rounds are only
    #: comparable if they were drawn over the same number of goods.
    goods: int = GOODS_DEFAULT
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
    #: peer id -> the X25519 key its JOIN offered for sealing, if it offered
    #: one. A seat without one can only play a practice game: there is nothing
    #: to seal its private half to.
    boxes: dict[str, str] = field(default_factory=dict)
    manager: str | None = None
    manager_peer: str | None = None
    settled: bool = False
    lapsed: bool = False
    workspace: str | None = None
    #: Drawn at settlement, never before -- see `Lobby._settle`. Not on the
    #: board: `barter.economy.draw_island(agents, goods, seed)` is public and
    #: deterministic, so a seed posted where entrants can read it hands them
    #: everybody's tastes before the round starts. It reaches the table's
    #: manager over `run_lobby.py`'s own log for now -- carrying it to a
    #: specific seat over the board is the sealed channel, build-order item
    #: 2c, and is not done here.
    seed: int | None = None

    def sealable(self) -> bool:
        """Whether every seat gave the manager something to seal to, which is
        what a ranked game needs and a practice game does without."""
        return bool(self.seats) and all(p in self.boxes for p in self.seats)

    def full(self) -> bool:
        return len(self.seats) >= self.traders

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
    #: Where this lobby's own state is kept across restarts. Optional: a test
    #: and a one-shot drain need none, a standing process does.
    state_path: Path | None = None
    #: This process's holder token, once `hold()` has claimed the channel.
    holder: str | None = None
    #: Set when a newer lobby took the channel over. A stood-down lobby reads
    #: nothing and settles nothing; it does not compete for the board.
    stood_down: bool = False
    seen: set[str] = field(default_factory=set)
    tables: dict[str, Table] = field(default_factory=dict)
    settled: int = 0
    refused: int = 0
    talk: int = 0
    refusals: list[dict] = field(default_factory=list)
    _names: dict[str, str] = field(default_factory=dict)
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
        self.say(f"{HOLD}{self.holder}")
        return self.holder

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
        self._names = {a["agent_id"]: a["name"] for a in self.client.agents()
                       if a.get("name")}
        rows = sorted(self.client.history(self.channel, limit=500),
                      key=lambda r: r.get("seq", 0))
        if self._stand_down(rows):
            return
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

    def _forget(self, rows: list[dict]) -> None:
        """Drop message ids that have fallen out of the window we read.

        A message older than the last 500 on this channel is never delivered
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
                self._manage(peer, action)
        except Refused as exc:
            self._refuse(peer, type(action).__name__.lower(), str(exc), text)

    def _refuse(self, peer: str, kind: str, reason: str, text: str) -> None:
        self.refused += 1
        self.refusals.append({"peer": peer, "kind": kind, "reason": reason,
                              "line": text.strip()[:200]})
        self.say(f"@{self._display(peer)} not settled: {reason}")

    # --- settling --------------------------------------------------------

    def _open(self, peer: str, action: Open) -> None:
        table = Table(id=f"g{self._next}", traders=action.traders,
                     episodes=action.episodes, rounds=action.rounds,
                     goods=action.goods, opened_at=self.clock())
        self._next += 1
        self.tables[table.id] = table
        self.settled += 1
        # The goods are announced with the rest of the format. An entrant reads
        # this to know what island it is sitting down at -- the rules it hands
        # its agent count the goods by name, so a table that kept the number to
        # itself would have every trader briefed on the wrong island.
        self.say(f"{table.id} is forming: {table.traders} traders, "
                f"{table.goods} goods, "
                f"{table.episodes} episodes, {table.rounds} round"
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
        key = self._witness(signature)
        table.seats[peer] = action.name
        table.keys[peer] = key
        if action.box:
            table.boxes[peer] = action.box
        self.settled += 1
        self.say(f"{action.table} seat {table.label(peer)} = {action.name}, "
                f"key {key}"
                f"{', sealed' if action.box else ', in the clear'} "
                f"({len(table.seats)}/{table.traders})")
        if table.ready():
            self._settle(table)

    @staticmethod
    def _witness(signature: dict | None) -> str:
        """The key a message was verified under, or a refusal naming why not.

        Distinct reasons for distinct causes, the same discipline the rest of
        this module keeps: unsigned is not the same fact as unknown, and
        unknown is not the same fact as forged, however alike all three look
        from "the seat did not get bound".
        """
        status = (signature or {}).get("status")
        if status is None or status == "unsigned":
            raise Refused("JOIN must be signed -- this message carried no "
                          "signature to witness")
        if status == "unknown":
            raise Refused("no signing key known for you yet -- register on "
                          "this room before JOIN")
        if status != "verified":
            raise Refused("the signature on this JOIN does not match any "
                          "key you have announced")
        return signature["key"]

    def _manage(self, peer: str, action: Manage) -> None:
        table = self._table(action.table)
        if table.manager is not None:
            raise Refused(f"{action.table} is already managed by "
                          f"{table.manager}")
        table.manager, table.manager_peer = self._display(peer), peer
        self.settled += 1
        self.say(f"{action.table} will be managed by {table.manager}")
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
        table.seed = self.draw_seed()
        table.workspace = f"{self.client.config.workspace}-{table.id}"
        key = generate_key() if self.client.encrypted else None
        invite = Invite(url=self.client.config.url, workspace=table.workspace,
                        token=self.client.config.token, key=key,
                        note=f"{table.id}: {table.traders} traders, "
                             f"{table.episodes} episodes")
        opens_at = _stamp(self.clock() + self.open_lead)
        roster = ", ".join(f"{label} = {name}"
                           for label, name in zip(
                               (table.label(p) for p in table.seats),
                               table.seats.values()))
        note = "" if table.sealable() else (
            "; PRACTICE -- not every seat offered a key to seal to, so the "
            "private half is public and this game is not ranked")
        self.say(f"{table.id} is full: {roster}; managed by "
                f"{table.manager}; opens {opens_at}{note}")
        self.say(f"{table.id} invite: {invite.encode()}")

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
