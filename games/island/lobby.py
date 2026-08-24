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
seat itself twice at the same table by typing a different name each time.
Binding that peer to the name with a witnessed signing key, so an impostor can
be told apart from the real seat later in the round, is build-order item 2 and
is not done here -- this only prevents one peer from occupying two seats at
the *lobby* stage.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Callable

from switchboard.client import Client
from switchboard.crypto import generate_key
from switchboard.invite import Invite
from switchboard.timing import unwrap_forecast

from .protocol import Join, Malformed, Manage, Open, parse

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
    #: peer id -> the name it joined under. Insertion order is seat order:
    #: the first peer to join is T1, the second T2, and so on -- the same
    #: labelling `island/manager.py` defaults to, so a settled table's seats
    #: are already the names the island manager will use.
    seats: dict[str, str] = field(default_factory=dict)
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
    seen: set[str] = field(default_factory=set)
    tables: dict[str, Table] = field(default_factory=dict)
    settled: int = 0
    refused: int = 0
    talk: int = 0
    refusals: list[dict] = field(default_factory=list)
    _names: dict[str, str] = field(default_factory=dict)
    _next: int = 1

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
        self._names = {a["agent_id"]: a["name"] for a in self.client.agents()
                       if a.get("name")}
        rows = sorted(self.client.history(self.channel, limit=500),
                      key=lambda r: r.get("seq", 0))
        for msg in rows:
            mid = str(msg.get("id"))
            if mid in self.seen:
                continue
            self.seen.add(mid)
            peer = str(msg.get("from") or "")
            if not peer or peer == self.client.agent_id:
                continue
            body, _forecast = unwrap_forecast(msg.get("body"))
            self._consider(peer, body if isinstance(body, str) else "")
        self._sweep()

    def _consider(self, peer: str, text: str) -> None:
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
                self._join(peer, action)
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
                     opened_at=self.clock())
        self._next += 1
        self.tables[table.id] = table
        self.settled += 1
        self.say(f"{table.id} is forming: {table.traders} traders, "
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

    def _join(self, peer: str, action: Join) -> None:
        table = self._table(action.table)
        if peer in table.seats:
            raise Refused(f"you already hold seat "
                          f"{table.label(peer)} at {action.table}")
        if action.name in table.seats.values():
            raise Refused(f"{action.name!r} is already seated at {action.table}")
        if table.full():
            raise Refused(f"{action.table} is full")
        table.seats[peer] = action.name
        self.settled += 1
        self.say(f"{action.table} seat {table.label(peer)} = {action.name} "
                f"({len(table.seats)}/{table.traders})")
        if table.ready():
            self._settle(table)

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
        self.say(f"{table.id} is full: {roster}; managed by "
                f"{table.manager}; opens {opens_at}")
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
