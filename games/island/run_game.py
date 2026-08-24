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

**Practice, not ranked.** Until there is a private channel (`games/island.md`,
item 2c) the private half has to be posted in the clear, so every trader can
read every other trader's capacities and tastes. That is a different game from
the one being measured, and it is marked as such on the board and in the
record: a practice game is kept, counted, and never ranked. `--ranked` is
refused with the reason rather than quietly producing a row that claims more
than it can.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from switchboard.client import Client
from switchboard.config import ClientConfig, MANAGED_HUB_TOKEN, MANAGED_HUB_URL
from switchboard.invite import Invite

from .lobby import Lobby, Table

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
    trader wrote. The signing key is per process and crosses rooms unchanged,
    which is the thing that makes a witnessed key worth witnessing.

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


def deal(mgr: Manager, dealer: Dealer, table: Table) -> None:
    """Tell each trader its own half, in the clear, and say that it is.

    The one step that is honestly wrong until item 2c lands. `PRODUCE` shares
    are public too, so a practice game hides nothing at all -- which is why it
    is announced rather than glossed, and why the record it produces is not
    ranked.
    """
    mgr.say("This is a PRACTICE game: each trader's capacities and tastes are "
            "posted below in the clear, where every other trader can read "
            "them. Nothing here is ranked.")
    seated = players(table)
    for name in mgr.names:
        mgr.say(f"@{name} ({seated.get(name, '?')}) {dealer.private_state(name)}")


def play(table: Table, invite: Invite, *, episode_seconds: int,
         ack_seconds: int, out: Path) -> dict:
    """One settled table, from its first bell to its record."""
    client = Client.from_invite(invite, agent_id=MANAGER)
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
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
    ack_deadline = started + ack_seconds
    mgr.say(schedule.schedule_text(table.episodes, mgr.names,
                                   opens_at=ack_deadline,
                                   episode_seconds=episode_seconds,
                                   ack_seconds=ack_seconds))
    deal(mgr, dealer, table)

    def until(deadline: float) -> None:
        while time.time() < deadline:
            bind_seats(mgr, table)
            mgr.drain()
            time.sleep(DRAIN_EVERY)
        bind_seats(mgr, table)
        mgr.drain()

    until(ack_deadline)
    missing = sorted(set(players(table)) - set(mgr.keys))
    if missing:
        # Said out loud rather than left to look like silence: a seat nobody
        # ever occupied is a different event from a trader that chose not to
        # speak, and the record has to be able to tell them apart.
        mgr.say(f"{', '.join(missing)} never reached this room and cannot be "
                f"settled for; the round opens without them.")
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

    board = save_board(mgr, out)
    return record(table, mgr, dealer, out, board=board,
                  seconds=round(time.time() - started, 1))


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
                 "body": m.get("body")}
                for m in rows if isinstance(m.get("body"), str)]
    path = out / f"board-{mgr.client.config.workspace}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"workspace": mgr.client.config.workspace,
                                "channel": mgr.channel,
                                "messages": messages}, indent=1) + "\n")
    return path


def record(table: Table, mgr: Manager, dealer: Dealer, out: Path, *,
           board: Path, seconds: float) -> dict:
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
        "practice": True,
        "rounds": [{
            "workspace": mgr.client.config.workspace,
            "seed": table.seed,
            "episodes": table.episodes,
            "arm": "practice",
            "game": {"id": table.id, "rounds": table.rounds},
            "trajectory": trajectory_from(dealer.island, mgr.episode_log,
                                          list(mgr.names), list(mgr.goods)),
            "episode_log": mgr.episode_log,
            "refusals": mgr.refusals,
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
    payload = _reveal.reveal(table.seed, table.traders, len(GOODS),
                             names=list(players(table)))
    payload["players"] = players(table)
    # The key that opens this game's room. Safe only because the game is done.
    payload["room_key"] = invite.key
    payload["round"] = {"seed": table.seed, "workspace": rnd["workspace"],
                        "trajectory": rnd["trajectory"]}
    path = out / f"reveal-{rnd['workspace']}.json"
    path.write_text(json.dumps(payload, indent=1) + "\n")
    return path


def watch(lobby: Lobby, *, every: float, episode_seconds: int,
          ack_seconds: int, out: Path) -> None:
    """Poll the lobby; play whatever settles. Never returns on its own."""
    played: set[str] = set()
    while True:
        lobby.drain()
        for table in list(lobby.tables.values()):
            if not table.settled or table.id in played:
                continue
            played.add(table.id)
            invite = pending_invite(lobby, table)
            if invite is None:
                print(f"{table.id}: settled but no invite on the board", flush=True)
                continue
            print(f"{table.id}: playing seed={table.seed} "
                  f"workspace={table.workspace}", flush=True)
            rec = play(table, invite, episode_seconds=episode_seconds,
                       ack_seconds=ack_seconds, out=out)
            path = out / f"{table.id}.json"
            path.write_text(json.dumps(rec, indent=1) + "\n")
            sidecar = publish(table, invite, rec, out)
            added, _ = _scores.ingest(path, players=rec["players"])
            status = added[0]["status"] if added else "already recorded"
            print(f"{table.id}: wrote {path} and {sidecar.name}; "
                  f"ledger says {status}", flush=True)
        time.sleep(every)


def pending_invite(lobby: Lobby, table: Table) -> Invite | None:
    """The invite the lobby posted for this table, read back off the board.

    Read rather than reconstructed: the lobby minted the room's key and this
    is the only place it exists. Rebuilding one here would produce a different
    key and a different, empty room.
    """
    marker = f"{table.id} invite: "
    for msg in reversed(sorted(lobby.client.history(lobby.channel, limit=500),
                               key=lambda r: r.get("seq", 0))):
        body = msg.get("body")
        if isinstance(body, str) and body.startswith(marker):
            return Invite.decode(body[len(marker):])
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
    ap.add_argument("--ranked", action="store_true",
                    help="refused: there is no private channel yet")
    args = ap.parse_args(argv)

    if args.ranked:
        raise SystemExit(
            "a ranked game needs the private half to stay private, and there "
            "is no channel to send it down yet (games/island.md, item 2c). "
            "Practice games run in plaintext and are not ranked.")

    client = Client(ClientConfig(url=args.hub, url_source="explicit", token=args.token,
                                 workspace=args.workspace, key=args.key),
                    agent_id="lobby")
    lobby = Lobby(client=client, channel=args.channel)
    print(f"watching {args.hub}/{args.workspace}#{args.channel} for settled tables")
    try:
        watch(lobby, every=args.every, episode_seconds=args.episode_seconds,
              ack_seconds=args.ack_seconds, out=args.out)
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
