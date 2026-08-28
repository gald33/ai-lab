"""Run a settled table: the glue between the lobby and the island.

    python -m games.island.run_game --workspace island-lobby

The lobby settles a table -- seats bound to witnessed keys, a seed drawn, a
room minted, an invite posted -- and then stops, deliberately. This is what
picks that up: it opens the table's room, deals each seat its private half,
binds the manager to the keys the lobby witnessed, runs the clock, and writes
the record when the last bell rings.

**It never launches an entrant's agent.** That is the line `games/island.md`
draws around the lobby and it does not stop being the line here: entrants run
their own sessions, reach the room with the invite, and this waits for them on
a clock. Nothing here prompts anybody, and nothing here is a turn. The runner
starts nothing, drives nobody, and only reads, settles and keeps time.

**Run this or `run_lobby.py` against a workspace, never both.** This embeds a
lobby of its own, and it has to: the seed is drawn at settlement and never
posted, because posting it would hand every trader's tastes to everybody. So
whoever settles a table is the only one who knows which island it is, and
therefore the only one who can deal it. Two lobbies on one channel settle
every table twice, mint two room keys for one workspace, and produce a game
where the entrants and the manager cannot read each other -- which looks
exactly like nobody turning up. `pending_invite` refuses rather than plays
when it sees that, but the arrangement to avoid is running both at once, so
this holds the channel on the board when it starts and an older lobby reading
the same board stands down (`lobby.HOLD`). It also keeps its own state in a
file, so a restart plays on with the tables it settled rather than settling
them again under new ids.

The honest name for this is a limitation, not a design: a manager that is not
the lobby is what `games/island.md` wants, and it needs the lobby to be able
to seal the seed to it. That is the same released-primitive wait as the
private half.

**Sealed or in the clear, and it says which.** A table whose every seat offered
a key at `JOIN` plays sealed: the private half is sealed to each seat and
`PRODUCE` is sealed back, so tastes and shares never reach the board. A table
where any seat did not is not sealable -- the private half has to be posted in
the clear, every trader can read every other trader's capacities and tastes,
and that is a different game from the one being measured. It is marked as such
on the board and in the record, kept, counted, and never ranked; `--ranked`
skips it rather than producing a row that claims more than it can.

**No agent can play a sealed round with the released Switchboard.** Sealing
needs X25519, and an entrant's agent has `say`, `history`, `inbox` and `sleep`
-- so every sealed round exercised here is driven by scripted clients calling
`sealed.seal_to` directly. Switchboard has since shipped the tool that fixes
this: `whisper` seals to one recipient's published `exchange_key`, and `inbox`
opens what was sealed to you. **That release landed**, so `island/sealed.py` is
gone, this
module deals through `whisper`, and a game real agents play is a practice game
only when a seat turns up without an exchange key to seal to.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable

from switchboard.client import Client
from switchboard.config import ClientConfig, MANAGED_HUB_TOKEN, MANAGED_HUB_URL
from switchboard.invite import Invite

from .archive import INDEPENDENT, SAME_PARTY, Archivist, compare
from .live import write as write_live
from .lobby import Held, Lobby, Table
from .lobby_page import write as write_page

# The island economy this game runs, from 005's tree. A code dependency is not
# grounding -- 005's own CLAUDE.md says exactly that about its import of 002 --
# and the package is `island` while this one is `games.island`, so the two
# names do not collide.
_ISLAND = Path(__file__).resolve().parents[2] / "experiments" / "005-deliberation-protocol"
sys.path.insert(0, str(_ISLAND))

sys.path.insert(0, str(_ISLAND / "viewer"))

from island import schedule  # noqa: E402
from island.dealer import GOODS, Dealer  # noqa: E402
from island.manager import MANAGER, Manager  # noqa: E402
from island.score import trajectory_from  # noqa: E402

import reveal as _reveal  # noqa: E402
import scores as _scores  # noqa: E402

#: How often the manager looks at the channel. It is a reader, so this only
#: decides how promptly receipts appear, never when an agent may act.
DRAIN_EVERY = 1.5


def bind_seats(mgr: Manager, table: Table) -> set[str]:
    """Bind each seat slot to whoever holds the key the lobby witnessed for it.

    **By key, not by peer id.** A peer id is blinded per workspace, so the id
    the lobby saw is not the id the table's room sees for the same agent --
    they differ, and binding the lobby's would silently ignore every line the
    trader wrote. The signing key is what can cross the two rooms unchanged,
    which is the thing that makes a witnessed key worth witnessing.

    **"Can", not "does".** A key is per *client*, not per process: two bare
    `Client`s for one `agent_id` in one process publish two different
    `pubkey`s, checked against the managed hub and offline both. It crosses
    only when something holds one identity for that agent -- `signing`'s
    server on an `agent_id` socket, which every client then attaches to
    instead of minting its own, and which `switchboard-mcp` runs. An entrant
    that builds a fresh client per room is not wrong about the protocol; it
    simply is not the same entrant in the second room, and this returns
    without it. `play` says that on the board rather than leaving it to look
    like an absence.

    Idempotent, and returns the slots bound so far: an entrant cannot be found
    before it registers in the room, so this is called again on every drain
    until the table is full or the round starts without it.
    """
    want = {key: table.label(peer) for peer, key in table.keys.items()}
    for agent in mgr.client.agents():
        key = agent.get("pubkey")
        slot = want.get(key) if isinstance(key, str) else None
        if slot is not None:
            mgr.bind(agent["agent_id"], slot, key=key)
    return set(mgr.keys)


def players(table: Table) -> dict[str, str]:
    """Seat slot -> the entrant sitting in it, for the ledger.

    The gap `viewer/README.md` names -- "a player is currently whatever the
    run record called the model" -- closed by the lobby knowing who sat down.
    """
    return {table.label(peer): name for peer, name in table.seats.items()}


#: What the manager seals a private half under. Distinct from the context a
#: trader seals `PRODUCE` under, so neither can be replayed as the other.


def sealable(mgr: Manager) -> dict[str, str]:
    """Seat slot -> the agent id in *this room* to seal that seat's half to,
    but only if every seat has one. Empty means this table plays in the clear.

    **Decided here rather than in the lobby**, and that is the change
    `whisper` made. A seat used to have to carry a `box=` key on its `JOIN`; now the
    key is the entrant's own published `exchange_key`, which its client
    publishes on `register()` and the manager reads off this room's roster
    like any other. So the question "can this table be sealed?" is answered
    where the sealing happens, by looking at who actually turned up, rather
    than by what somebody wrote on a board one room earlier.
    """
    roster = {a.get("agent_id"): a for a in mgr.client.agents()}
    by_slot: dict[str, str] = {}
    for peer, slot in mgr.alias.items():
        if slot == MANAGER:
            continue
        agent = roster.get(peer) or {}
        if isinstance(agent.get("exchange_key"), str) and agent["exchange_key"]:
            by_slot[slot] = peer
    return by_slot if len(by_slot) == len(mgr.names) else {}


def deal(mgr: Manager, dealer: Dealer, table: Table) -> bool:
    """Tell each trader its own half -- sealed to it alone, or in the clear.

    Sealed when every seat published an exchange key in this room, which is
    what makes a game rankable: the tastes never reach the board, and
    `PRODUCE` sealed the other way keeps the shares off it too, which together
    close the capacity leak (capacity is a public receipt's quantity divided
    by a share).

    In the clear otherwise, and said out loud rather than glossed: a practice
    game hides nothing at all, and the record it produces is not ranked.
    """
    seated = players(table)
    by_slot = sealable(mgr)

    if not by_slot:
        mgr.say("This is a PRACTICE game: each trader's capacities and tastes "
                "are posted below in the clear, where every other trader can "
                "read them. Nothing here is ranked.")
        for name in mgr.names:
            mgr.say(f"@{name} ({seated.get(name, '?')}) "
                    f"{dealer.private_state(name)}")
        return False

    mgr.say(f"SEALED round. Your private half is on its way to you alone -- "
            f"read it with `inbox`, which opens what was sealed to you. Send "
            f"your PRODUCE back the same way, with `whisper` addressed to "
            f"{mgr.client.agent_id}: a plan posted on this board in the clear "
            f"gives your capacity away, since the receipt states the quantity. "
            f"PROPOSE and APPROVE stay public, and so does every receipt -- "
            f"what is hidden is the labour behind them, and nothing else.")
    for name in mgr.names:
        # `private_state` already opens with "You are T1." -- naming the seat
        # twice is how a briefing starts to read like a machine wrote it.
        mgr.client.whisper(by_slot[name],
                           f"{dealer.private_state(name)} "
                           f"You are seated here as {seated.get(name, '?')}.")
    return True


def _stay_present(client) -> None:
    """Keep the manager on the roster, every drain.

    **Registration lapses in about two minutes; a round runs eight.** So a
    manager that registers once at the start is absent from the roster for
    most of its own game -- and a peer that is not on the roster cannot be
    whispered to, because sealing needs its exchange key from there. Every
    sealed PRODUCE after the first couple of minutes therefore had nowhere to
    go.

    Found by the trader in g3, who reported that "one early whisper worked and
    later ones failed" and had reasonably blamed its own setup. It was this.

    Never raises: a failed heartbeat is a manager that may go unreachable, and
    a manager that dies of one is a round that certainly ends.
    """
    try:
        client.heartbeat(renew_leases=False)
    except Exception as exc:      # noqa: BLE001 -- see the docstring
        print(f"presence not refreshed: {exc!r}", flush=True)


def _show(mgr: Manager, live: Path | None) -> None:
    """Write the board where a spectator can read it, and never stop a game.

    Same rule as `_tick` and `_witness`, and for the plainest reason of the
    three: nobody watching is playing. A file that cannot be written costs a
    spectator a refresh and costs the traders nothing, so it is said out loud
    and the bells go on.
    """
    if live is None:
        return
    try:
        write_live(mgr.client, mgr.channel, live)
    except Exception as exc:      # noqa: BLE001 -- see the docstring
        print(f"live view not written: {exc!r}", flush=True)


def _witness(archivist: Archivist | None) -> None:
    """Let the second copy read the room, and never let it stop the game.

    Same rule as `_tick`, for a stronger reason: the archive exists to check
    the manager, so an archive that could halt a round would hand the manager
    a reason to want it gone. `Archivist.catch_up` swallows its own read
    failures; this is the belt for anything past them.
    """
    if archivist is None:
        return
    try:
        archivist.catch_up()
    except Exception as exc:      # noqa: BLE001 -- see the docstring
        print(f"archivist: {exc!r}", flush=True)


def _tick(tick: Callable[[], None] | None) -> None:
    """Run the lobby's drain beside the game, and never let it stop one.

    A game in progress is the thing with a clock on it. If the lobby throws --
    a hub that blinked, a line it could not read -- the table it is running
    must not die of it, so the fault is said out loud and the bells go on.
    """
    if tick is None:
        return
    try:
        tick()
    except Exception as exc:  # noqa: BLE001 - a game outranks its lobby
        print(f"lobby drain failed mid-game, continuing: {exc!r}", flush=True)


def who_is_at_this_table(table: Table) -> str:
    """Name the seats, out loud, before anybody speaks.

    **The room is not the table.** An invite is a read-write credential with
    no read-only variant, and this room's was posted on a lobby board every
    entrant there can read, so anyone who was in the lobby can walk in here
    and talk. The manager already ignores them -- a line from an unbound
    author settles nothing and is refused by name -- but *settling* is not the
    only thing a message does. A trader is a reader, and a stranger's line
    reads exactly like a rival's until somebody says otherwise.

    So the manager says otherwise, once, in the one place a trader is
    certainly looking: which seats are at this table and which keys they took
    them with, both already public on the lobby board, and that anything from
    anyone else is not part of this game. It does not silence the room, which
    is not ours to do and would need a permission model Switchboard does not
    have and should not be made to grow. It arms the reader instead.

    Sealing the invite to each seat is what would actually close the room, and
    it needs no new primitive either -- it is `whisper`, the same tool the
    private half already travels by, addressed at the invite instead of the
    tastes.
    """
    seats = ", ".join(f"{table.label(peer)} = {name} (key {table.keys.get(peer, '?')})"
                      for peer, name in table.seats.items())
    return (f"The seats at this table, witnessed in public on the lobby board "
            f"before this room existed: {seats}. This room's invite was posted "
            f"there too, so others may be here and may write. **Nothing they "
            f"write is part of this game**: a line from anyone but these seats "
            f"settles nothing, and I will refuse it by name where you can see "
            f"the refusal. Read accordingly -- what a stranger says here has "
            f"no standing, whatever it looks like.")


def ack_close(started: float, ack_seconds: float, table: Table) -> float:
    """When the ack window shuts: the later of this runner's own window and
    the time the board announced.

    The board already told the entrants when this table opens, and an entrant
    that arrives at the announced time is on time. A table settled at 19:38
    and announced for 19:40 would otherwise be free to call its seats absent
    at 19:39, for turning up exactly when they were told to.
    """
    return max(started + ack_seconds, table.opens_at or 0.0)


def play(table: Table, invite: Invite, *, episode_seconds: int,
         ack_seconds: int, out: Path, tick: Callable[[], None] | None = None,
         ranked_only: bool = False,
         archivist: Archivist | None = None,
         live: Path | None = None) -> dict | None:
    """One settled table, from its first bell to its record.

    ``tick`` is called on every drain of this room. `watch` no longer needs
    it -- it plays each table in its own thread and keeps draining the lobby
    on its own -- but a caller that plays a table in-line still does, or the
    lobby goes deaf for the length of the game: every OPEN and JOIN waits for
    the last bell, and nothing lapses on time either.
    """
    client = Client.from_invite(invite, agent_id=MANAGER)
    # **The manager registers too, and not only for the roster line.** Sealing
    # is pairwise: a seat opens what was sealed to it by deriving a secret
    # with the *sender's* exchange key, so a manager that never registered
    # publishes no such key and every half it seals arrives unreadable. It
    # cost a test to find, and it would have cost a game.
    client.register(name=MANAGER, kind="local", branch="main",
                    task=f"running {table.id}")
    # The first `table.goods` of the vocabulary. The table settled its own
    # count when it opened, and the entrants were briefed on that number -- so
    # this must follow the table rather than a default of its own.
    goods = GOODS[:table.goods]
    dealer = Dealer.draw(table.seed, table.traders, goods)
    mgr = Manager(capacity=dealer.capacity, client=client,
                  channel="island", goods=dealer.goods)

    # The seats the lobby witnessed, bound to the keys it witnessed them
    # under. This is the whole point of the lobby having done that: a line
    # from anything but the key that took the seat is refused from here on.
    #
    # Bound to the *slot* (`T1`), not to the entrant's chosen name: the
    # manager settles seats, and which player is in which seat is the
    # lobby's `T1 = scout-v2` line and the ledger's `players` mapping. The
    # entrant learns its slot from that same settlement.
    #
    # Attempted now and again on every drain: a seat can only be bound once
    # its holder has registered in this room, which it has not yet done.
    bind_seats(mgr, table)

    started = time.time()
    ack_deadline = ack_close(started, ack_seconds, table)
    mgr.say(schedule.schedule_text(table.episodes, mgr.names,
                                   opens_at=ack_deadline,
                                   episode_seconds=episode_seconds,
                                   ack_seconds=ack_seconds))
    mgr.say(who_is_at_this_table(table))

    def until(deadline: float) -> None:
        while time.time() < deadline:
            bind_seats(mgr, table)
            _stay_present(mgr.client)
            mgr.drain()
            _witness(archivist)
            _show(mgr, live)
            _tick(tick)
            time.sleep(DRAIN_EVERY)
        bind_seats(mgr, table)
        _stay_present(mgr.client)
        mgr.drain()
        _witness(archivist)
        _show(mgr, live)
        _tick(tick)

    # **Wait before asking who is here.** Whether a table can seal turns on
    # every seat having published an exchange key *in this room*, and an
    # entrant only reaches this room after reading the invite off the lobby
    # board. Asking at settlement asks an empty roster: it answered "no" every
    # time, so the manager dealt in the clear and announced a practice game
    # while the lobby had just witnessed both seats as sealable. **Sealing had
    # therefore never worked for an agent that joins at its own pace** -- only
    # for test clients that register instantly. Found by watching g3, where
    # the two lines contradicted each other one second apart.
    #
    # So the acknowledgement window comes first, and the deal after it: the
    # traders learn their half as episode 1 opens rather than two minutes
    # before, which is the cost, and it is worth paying.
    until(ack_deadline)

    if ranked_only and not sealable(mgr):
        mgr.say("Standing this table down: it was opened for a ranked game, "
                "and not every seat published an exchange key in this room, "
                "so its private half cannot be sealed. Nothing here is "
                "recorded. Open another table to play in the clear.")
        return None
    sealed = deal(mgr, dealer, table)

    missing = sorted(set(players(table)) - set(mgr.keys))
    if missing:
        # Said out loud rather than left to look like silence: a seat nobody
        # ever occupied is a different event from a trader that chose not to
        # speak, and the record has to be able to tell them apart.
        mgr.say(f"{', '.join(missing)} never reached this room and cannot be "
                f"settled for; the round opens without them. If you are here "
                f"and reading this, your seat did not bind: a seat binds by "
                f"the signing key the lobby witnessed on your JOIN, and a "
                f"client built fresh for this room mints a new one. Reach "
                f"both rooms with one signing identity -- switchboard-mcp's "
                f"signing server does this for you.")
    mgr.say(f"{len(mgr.acknowledged)}/{len(mgr.names)} acknowledged "
            f"({', '.join(sorted(mgr.acknowledged)) or 'nobody'}). "
            f"Episode 1 opens now.")

    for e in range(table.episodes):
        mgr.open_episode()
        bell = time.time() + episode_seconds
        mgr.say(f"episode {e + 1} of {table.episodes} is open; the bell is at "
                f"{schedule.stamp(bell)} ({episode_seconds}s). "
                f"PRODUCE, PROPOSE and APPROVE all settle until the bell.")
        until(bell)
        mgr.close_episode()

    mgr.say("the round is over. Stop; nothing further will settle.")
    mgr.drain()
    # One last look before it stops watching, so the archive holds the closing
    # line too -- and after the manager's own drain, so the two copies are of
    # the same room at the same moment rather than a second apart.
    _witness(archivist)
    _show(mgr, live)
    if archivist is not None:
        archivist.close()

    board = save_board(mgr, out)
    return record(table, mgr, dealer, out, board=board, sealed=sealed,
                  seconds=round(time.time() - started, 1))


def _verdict(signature: dict | None) -> dict:
    """The manager's reading of one line's signature, kept small on purpose."""
    block = signature or {}
    kept = {"status": block.get("status", "unsigned")}
    if isinstance(block.get("key"), str):
        kept["key"] = block["key"]
    return kept


def save_board(mgr: Manager, out: Path) -> Path:
    """The channel as a file, in the shape the viewer and the ledger read.

    A hub keeps a board for an hour; after that this copy is the only one, and
    the replay, the ledger's `played_at` and its board digest all come from
    here. Written from a fresh read rather than from anything the manager
    accumulated, so it is the board as it stands and not a summary of it.
    """
    rows = sorted(mgr.client.history(mgr.channel, limit=500),
                  key=lambda r: r.get("seq", 0))
    names = {peer: name for peer, name in mgr.alias.items()}
    messages = [{"seq": m.get("seq"), "at": m.get("created_at"),
                 "author": names.get(str(m.get("from") or ""),
                                     MANAGER if str(m.get("from")) == mgr.client.agent_id
                                     else str(m.get("from") or "?")),
                 "body": m.get("body"),
                 # What the manager's own client made of the signature when it
                 # read the line, and the key it verified under. **Not a
                 # signature**: the client verifies at read time and hands its
                 # caller a verdict, so the bytes never reach here and a later
                 # reader cannot re-verify -- see `verify.py`, which says so
                 # rather than implying otherwise. What it does buy is the
                 # check that matters most: a line attributed to a seat has to
                 # carry the key the lobby witnessed for that seat, in public,
                 # before the round.
                 "signature": _verdict(m.get("signature"))}
                for m in rows if isinstance(m.get("body"), str)]
    path = out / f"board-{mgr.client.config.workspace}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"workspace": mgr.client.config.workspace,
                                "channel": mgr.channel,
                                "messages": messages}, indent=1) + "\n")
    return path


def record(table: Table, mgr: Manager, dealer: Dealer, out: Path, *,
           board: Path, seconds: float, sealed: bool = False) -> dict:
    """The run record, in the shape `viewer/scores.py:ingest` already reads."""
    return {
        "experiment": "005-v3",
        "game": {"id": table.id, "rounds": table.rounds},
        "model": "entrants",
        "agents": table.traders,
        "goods": len(dealer.goods),
        "episodes_per_round": table.episodes,
        #: Seat slot -> entrant, for `scores.ingest(..., players=...)`.
        "players": players(table),
        # A practice game is kept and counted and never ranked: the private
        # half was public, so what it measures is not what the board ranks.
        "practice": not sealed,
        "rounds": [{
            "workspace": mgr.client.config.workspace,
            "seed": table.seed,
            "episodes": table.episodes,
            "arm": "sealed" if sealed else "practice",
            "sealed_lines": mgr.sealed_in,
            "game": {"id": table.id, "rounds": table.rounds},
            "trajectory": trajectory_from(dealer.island, mgr.episode_log,
                                          list(mgr.names), list(mgr.goods)),
            "episode_log": mgr.episode_log,
            "refusals": mgr.refusals,
            # Lines from keys that took no seat. A round that had company is
            # kept and counted and never ranked -- see `island/manager.py`,
            # `_intrusion`, and `viewer/scores.py`.
            "intrusions": mgr.intrusions,
            "intruders": sorted(mgr.intruders),
            "spoke": sorted(mgr.spoke),
            "acknowledged": sorted(mgr.acknowledged),
            "settled": mgr.settled, "refused": mgr.refused, "talk": mgr.talk,
            "channel": mgr.channel,
            "channel_messages": len(mgr.seen),
            "drain_saturated": mgr.saturated,
            "board": board.name,
            "seconds": seconds,
        }],
    }


def publish(table: Table, invite: Invite, record: dict, out: Path) -> Path:
    """The replay, and the key that opens the room -- only now the game is over.

    "A seed still in play is not replayable by anyone": revealing the seed's
    tastes mid-round would hand every trader its rivals' preferences, so the
    sidecar is written at the end and not before. The room key goes with it
    for the same reason it can now: the hidden half is being revealed anyway,
    and a key-holder is the only one who can check who signed what, so
    publishing it is what makes authorship checkable by anybody afterwards.
    """
    rnd = record["rounds"][0]
    payload = _reveal.reveal(table.seed, table.traders, table.goods,
                             names=list(players(table)))
    payload["players"] = players(table)
    # The key that opens this game's room. Safe only because the game is done.
    payload["room_key"] = invite.key
    payload["round"] = {"seed": table.seed, "workspace": rnd["workspace"],
                        "trajectory": rnd["trajectory"]}
    # How the island was drawn, and everything needed to check it. The lobby's
    # nonce is the one piece that was secret while the game ran; published
    # here, the seed becomes recomputable by anybody from lines that were on
    # the lobby's board before the draw -- which is what stops a manager
    # re-rolling an island until it suited somebody.
    payload["seat_keys"] = {table.label(peer): key
                            for peer, key in table.keys.items()}
    payload["draw"] = {
        "method": table.draw,
        "commit": table.commit,
        "nonce": table.nonce,
        "seat_nonces": {table.label(peer): nonce
                        for peer, nonce in table.nonces.items()},
        "recompute": ("sha256 of the lobby nonce and every seat nonce sorted, "
                      "joined by '|', first 8 bytes big-endian, >> 1"),
    }
    path = out / f"reveal-{rnd['workspace']}.json"
    path.write_text(json.dumps(payload, indent=1) + "\n")
    return path


def claim(manager: Client, lobby: Lobby, channel: str,
          claimed: set[str]) -> None:
    """Offer to run any table that is forming and has nobody to run it.

    A table settles when it is full **and** managed, and `MANAGE` is the line
    that says "I will run this one". This process is the thing that would run
    it, so this is it saying so -- on the board, in the grammar, where the
    lobby settles it like anybody else's claim.

    It comes from a second client with its own identity, because the lobby
    skips messages from its own `agent_id`: a lobby that settled its own
    claims would be choosing the manager rather than witnessing a choice, and
    would not see the line at all.
    """
    for table in lobby.tables.values():
        if table.settled or table.lapsed or table.manager or table.id in claimed:
            continue
        claimed.add(table.id)
        manager.post(channel, f"MANAGE {table.id}")
        print(f"{table.id}: offering to manage it", flush=True)


#: One game finishing writes a row; two finishing together would write two
#: into the same ledger at once. The ledger is append-only and its own reader,
#: so the write is serialised here rather than being made to cope.
_LEDGER = threading.Lock()

#: How many tables this runner will play at once. The lab pays for the manager
#: of every table that settles on its board, and `OPEN` is free to whoever
#: writes it -- so without a cap here the bill is set by strangers. Two is
#: what one operator can watch; the point is that the number exists and is
#: said out loud when it binds, not what it is.
MAX_CONCURRENT = 2


def prune(out: Path, keep: int) -> list[Path]:
    """Drop the raw output of all but the `keep` most recent games.

    **The ledger row is never touched**, so a pruned game is still counted, is
    still in every denominator, and still has its board digest on record. What
    goes is the bulk: the record, the board and the reveal it points at, which
    together are the only thing here that grows without limit.

    Oldest first, by the record's own mtime, and only games that have one --
    a board with no record beside it is a game that did not finish and is left
    alone rather than tidied away.
    """
    if keep <= 0:
        return []
    records = sorted((p for p in out.glob("g*.json") if p.is_file()),
                     key=lambda p: p.stat().st_mtime)
    dropped: list[Path] = []
    for record in records[:max(0, len(records) - keep)]:
        try:
            workspace = json.loads(record.read_text())["rounds"][0]["workspace"]
        except (OSError, ValueError, KeyError, IndexError):
            continue
        for path in (record, out / f"board-{workspace}.json",
                     out / f"reveal-{workspace}.json",
                     out / f"archive-{workspace}.json"):
            if path.exists():
                path.unlink()
                dropped.append(path)
    return dropped


#: The archivist's name in a table's room. Not `MANAGER`, and not a seat: it
#: takes no seat, settles nothing and is refused like any other stranger if it
#: ever speaks -- `Manager._intrusion` sees to that. It only reads.
ARCHIVIST = "archivist"


def archivist_for(table: Table, invite: Invite, *, lab_manages: bool
                  ) -> Archivist:
    """A second reader of one table's room, with an identity of its own.

    Its own `Client`, never the manager's: sharing one would make the archive
    a copy of the manager's opinion of the room rather than a second look at
    it. It registers so the roster shows who was watching -- a witness nobody
    can see is worth less than one they can.

    `standing` is decided here from one fact and not guessed: whether the
    party managing this table is this process. When it is not, this is the
    independent copy condition 3 asks for. When it is, it is two clients in
    one process, which is not two parties, and the archive says so.
    """
    client = Client.from_invite(invite, agent_id=ARCHIVIST)
    client.register(name=ARCHIVIST, kind="local", branch="main",
                    task=f"archiving {table.id}")
    return Archivist(client=client, channel="island",
                     writer=table.manager or "?",
                     standing=SAME_PARTY if lab_manages else INDEPENDENT)


def _play_table(table: Table, invite: Invite, *, episode_seconds: int,
                ack_seconds: int, out: Path, ledger: Path | None,
                ranked_only: bool = False, keep: int = 0,
                lab_manages: bool = True, live_dir: Path | None = None) -> None:
    """One table, start to ledger row. Runs in its own thread -- see `watch`.

    Nothing it touches is shared except the ledger: the table is its own, the
    room is its own, and the `Manager` and its `Client` are built inside
    `play`. A game that raises says so and dies alone; the lobby and every
    other table go on, because a table is not the process.
    """
    try:
        # Built before the game rather than inside it, so a room this process
        # cannot even join is a loud failure here instead of a silently
        # unwatched round.
        try:
            archivist = archivist_for(table, invite, lab_manages=lab_manages)
        except Exception as exc:      # noqa: BLE001
            print(f"{table.id}: no archivist -- {exc!r}; the game goes on "
                  f"and its board will have one copy only", flush=True)
            archivist = None
        rec = play(table, invite, episode_seconds=episode_seconds,
                   ack_seconds=ack_seconds, out=out, ranked_only=ranked_only,
                   archivist=archivist,
                   live=(live_dir / f"{table.id}.json") if live_dir else None)
        if rec is None:
            print(f"{table.id}: stood down -- opened for a ranked game and "
                  f"cannot seal", flush=True)
            return
        path = out / f"{table.id}.json"
        path.write_text(json.dumps(rec, indent=1) + "\n")
        sidecar = publish(table, invite, rec, out)
        # **Published now, with the reveal.** Holding it back protects
        # nothing: the seed is revealed at this point anyway, and every line
        # in it was public to the room when it was written. What publishing
        # buys is that the omission check can be run by anybody, which is the
        # entire point of a second copy.
        if archivist is not None:
            arc = archivist.save(out, table.workspace or table.id)
            diff = compare(json.loads(
                (out / f"board-{table.workspace}.json").read_text()),
                archivist.payload()) if table.workspace else None
            if diff and (diff["missing"] or diff["altered"]):
                print(f"{table.id}: THE TWO COPIES DISAGREE -- "
                      f"{len(diff['missing'])} line(s) witnessed and not on "
                      f"the board, {len(diff['altered'])} altered; see "
                      f"{arc.name}", flush=True)
        with _LEDGER:
            added, _ = _scores.ingest(
                path, players=rec["players"],
                **({"ledger": ledger} if ledger is not None else {}))
        status = added[0]["status"] if added else "already recorded"
        print(f"{table.id}: wrote {path} and {sidecar.name}; "
              f"ledger says {status}", flush=True)
        if keep:
            dropped = prune(out, keep)
            if dropped:
                print(f"pruned {len(dropped)} file(s) from older games; their "
                      f"ledger rows stand", flush=True)
    except Exception as exc:  # noqa: BLE001 - one table must not take the rest
        print(f"{table.id}: game failed -- {exc!r}", flush=True)


def watch(lobby: Lobby, *, every: float, episode_seconds: int,
          ack_seconds: int, out: Path, ranked_only: bool = False,
          ledger: Path | None = None, manager: Client | None = None,
          channel: str = "lobby", max_concurrent: int = MAX_CONCURRENT,
          page: Path | None = None, keep: int = 0,
          live_dir: Path | None = None) -> None:
    """Poll the lobby; claim what nobody is running; play whatever settles.

    **Each table plays in its own thread.** A game takes minutes, and two
    tables can settle a minute apart: playing them in turn means the second
    one's traders sit in a room where nothing happens, for the length of
    somebody else's game, having been told a time. The lobby keeps reading on
    this thread throughout, which is why `play` no longer needs to drain it.

    Never returns on its own.
    """
    played: set[str] = set()
    claimed: set[str] = set()
    games: list[threading.Thread] = []
    while True:
        lobby.drain()
        if page is not None:
            # This runner embeds the only lobby on its channel, so it is also
            # the only process that can render one -- `run_lobby --page` would
            # have to be a second lobby, which is the thing HOLD exists to
            # prevent. A deployment that ran the page and the games separately
            # would have one of them stand down.
            try:
                write_page(lobby, page)
            except Exception as exc:  # noqa: BLE001 - a page is not a game
                print(f"lobby page not written: {exc!r}", flush=True)
        if lobby.stood_down:
            print("another lobby holds this channel; stopping rather than "
                  "settling every table twice", flush=True)
            return
        if manager is not None:
            claim(manager, lobby, channel, claimed)
        for table in list(lobby.tables.values()):
            if not table.settled or table.id in played:
                continue
            played.add(table.id)
            if (out / f"{table.id}.json").exists():
                # A restarted runner restores the tables it settled (that is
                # the point of the state file), and a table's record on disk
                # is the evidence it already played one. Replaying it would
                # deal the same island twice and write a second row for one
                # game.
                print(f"{table.id}: already played -- {out / f'{table.id}.json'} "
                      f"is on disk", flush=True)
                continue
            try:
                invite = pending_invite(lobby, table)
            except SettledTwice as exc:
                print(f"{table.id}: refusing to play -- {exc}", flush=True)
                continue
            if invite is None:
                print(f"{table.id}: settled but no invite on the board", flush=True)
                continue
            games = [t for t in games if t.is_alive()]
            if len(games) >= max_concurrent:
                # Said on the board, not only in this process's log: a table
                # that settled and is waiting looks exactly like a table
                # nobody is running, and the difference matters to the people
                # sitting at it.
                print(f"{table.id}: waiting -- {len(games)} games already "
                      f"running (cap {max_concurrent})", flush=True)
                played.discard(table.id)
                continue
            print(f"{table.id}: playing seed={table.seed} "
                  f"workspace={table.workspace}", flush=True)
            thread = threading.Thread(
                target=_play_table, args=(table, invite),
                kwargs={"episode_seconds": episode_seconds,
                        "ack_seconds": ack_seconds, "out": out,
                        "ledger": ledger, "ranked_only": ranked_only,
                        "keep": keep, "live_dir": live_dir,
                        # Whether this process is also the party that will
                        # write this table's board. `claimed` holds the
                        # tables it offered to run, so a table managed by a
                        # stranger is one it never claimed -- and that is the
                        # case where the second copy is an independent
                        # witness rather than a second file.
                        "lab_manages": table.id in claimed},
                name=f"game-{table.id}", daemon=True)
            games.append(thread)
            thread.start()
        games = [t for t in games if t.is_alive()]
        time.sleep(every)


class SettledTwice(Exception):
    """Two lobbies settled one table, so its room has two keys and no game."""


def pending_invite(lobby: Lobby, table: Table) -> Invite | None:
    """The invite this lobby posted for the table, read back off the board.

    Read rather than reconstructed: the lobby minted the room's key and this
    is the only place it exists. Rebuilding one here would produce a different
    key and a different, empty room.

    **And refuse outright if two exist.** A second lobby draining the same
    channel settles the same table again -- a second settlement line, a second
    `generate_key()`, a second invite -- and the two rooms then share a
    workspace and nothing else. Entrants join on the first key, this manager on
    the second, and neither can read a word the other writes: the traders talk
    to themselves, the manager settles nothing, and the record comes out
    `absent` as though nobody turned up. It cost an afternoon to see, because
    every part of it works and the failure is silence.
    """
    marker = f"{table.id} invite: "
    found = [body[len(marker):]
             for msg in sorted(lobby.client.history(lobby.channel, limit=500),
                               key=lambda r: r.get("seq", 0))
             if isinstance(body := msg.get("body"), str) and body.startswith(marker)]
    if len(found) > 1:
        raise SettledTwice(
            f"{table.id} has {len(found)} invites on the board, so more than "
            f"one lobby settled it and its room has more than one key. "
            f"Whoever plays a table must be whoever settled it: the seed is "
            f"never on the board, so a second lobby draws its own and mints "
            f"its own room. Run `run_game` *or* `run_lobby` against a "
            f"workspace, not both.")
    return Invite.decode(found[0]) if found else None
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hub", default=os.environ.get("SWITCHBOARD_URL") or MANAGED_HUB_URL)
    ap.add_argument("--token", default=os.environ.get("SWITCHBOARD_TOKEN") or MANAGED_HUB_TOKEN)
    ap.add_argument("--workspace", default=os.environ.get("SWITCHBOARD_WORKSPACE", "island-lobby"))
    ap.add_argument("--key", default=os.environ.get("SWITCHBOARD_KEY"))
    ap.add_argument("--channel", default="lobby")
    ap.add_argument("--every", type=float, default=3.0, help="seconds between lobby polls")
    ap.add_argument("--episode-seconds", type=int, default=schedule.EPISODE_SECONDS)
    ap.add_argument("--ack-seconds", type=int, default=schedule.ACK_SECONDS)
    ap.add_argument("--out", type=Path, default=Path("games/results"))
    ap.add_argument("--ledger", type=Path, default=None,
                    help="where finished rounds are recorded (default: the "
                         "repo's own ledger). Point a rehearsal somewhere "
                         "else: the ledger is append-only and a row written "
                         "into it by a test does not come back out")
    ap.add_argument("--state", type=Path, default=None,
                    help="where the embedded lobby keeps what the board does "
                         "not carry -- the seeds it drew and the lines it has "
                         "already acted on -- so a restart does not settle a "
                         "table twice (default: <out>/lobby-<ws>-<ch>.json)")
    ap.add_argument("--page", type=Path, default=None,
                    help="rewrite this HTML file on every poll: the lobby as a "
                         "page a person can look at. It belongs here rather "
                         "than on run_lobby because this process embeds the "
                         "only lobby its channel may have")
    ap.add_argument("--live", type=Path, default=None,
                    help="write each running game's board into this directory "
                         "as JSON, one file per table, rewritten every drain. "
                         "It is what lets a person watch a game in progress "
                         "without being handed a room key -- the viewer reads "
                         "it with ?live=<url>. Serve it; it carries only what "
                         "is on the board, never the sealed half")
    ap.add_argument("--keep", type=int, default=0,
                    help="keep the raw output of only this many finished games, "
                         "pruning oldest first. The ledger row always survives, "
                         "so a pruned game is still counted and still in every "
                         "denominator; what goes is the board and reveal it "
                         "points at. 0 keeps everything (default)")
    ap.add_argument("--max-games", type=int, default=MAX_CONCURRENT,
                    help="how many tables to play at once. The lab pays for "
                         "the manager of every table that settles, and OPEN "
                         "costs its author nothing, so this is what stops a "
                         "stranger setting the bill (default: %(default)s)")
    ap.add_argument("--ranked", action="store_true",
                    help="refuse to play a table that is not sealable")
    ap.add_argument("--managed-by", default="lucille",
                    help="the name this runner offers to manage under, and "
                         "the one the settlement line records")
    args = ap.parse_args(argv)

    def _client(agent_id: str) -> Client:
        return Client(ClientConfig(url=args.hub, url_source="explicit",
                                   token=args.token, workspace=args.workspace,
                                   key=args.key), agent_id=agent_id)

    state = args.state or args.out / f"lobby-{args.workspace}-{args.channel}.json"
    lobby = Lobby(client=_client("lobby"), channel=args.channel, state_path=state)
    try:
        lobby.lock()
    except Held as exc:
        print(exc)
        return 1
    lobby.load()
    lobby.hold()
    # The claimant, separate from the lobby that witnesses it -- see `claim`.
    # Registered so the settlement line names it rather than a blinded id.
    manager = _client(MANAGER)
    manager.register(name=args.managed_by, kind="local", branch="main",
                     task=f"running tables in {args.workspace}")
    print(f"watching {args.hub}/{args.workspace}#{args.channel}, "
          f"offering to manage as {args.managed_by}, "
          f"holding as {lobby.holder}, state in {state}")
    try:
        watch(lobby, every=args.every, episode_seconds=args.episode_seconds,
              ack_seconds=args.ack_seconds, out=args.out,
              ranked_only=args.ranked, ledger=args.ledger,
              manager=manager, channel=args.channel,
              max_concurrent=args.max_games, page=args.page, keep=args.keep,
              live_dir=args.live)
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
