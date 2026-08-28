"""Put a heuristic player in a seat, so a table one short does not lapse.

    python -m games.island.run_npc --workspace island-lobby --name npc-1
    python -m games.island.run_npc --workspace island-lobby --fill

The first form claims one seat and plays it. The second watches the lobby and,
when a table has sat unfilled for `--patience` seconds, starts one process of
the first form for each missing seat -- which is the whole point of this file:
three entrants turn up, the fourth does not, and the round is played anyway.

**An NPC is an entrant and gets nothing an entrant does not.** It holds one
signing identity across both rooms, registers, posts `JOIN`, waits for the
invite, and then reads the board and writes lines to it. `run_entrant.py` does
the same and then spends money starting a model; this does the same and then
runs `npc.lines` instead. Everything else -- the seat binding by witnessed key,
the manager refusing a malformed line, the bell -- is identical, because there
is no other path and this file does not add one.

**Every NPC is its own process, and that is a decision rather than an
accident.** One process running several seats would be cheaper and is refused
for two reasons. It is the shape of a scheduler: a loop over players, ticking
each in turn, is exactly the thing `CLAUDE.md` says has been built twice and
must not be built again -- and it is *easy* to write by accident once the
players share a process. And a process holding several seats' keys can open
every whisper addressed to any of them, so a round it plays is not the sealed
round the record would claim; a heuristic that only reads its own is a
convention and not a property. Separate processes make both true by
construction rather than by care.

**What it does not do**: seal. In a sealed round the manager whispers this
seat its private half and this reads it, but the plan goes back on the board
in the clear, which gives away this seat's capacity. That costs nothing worth
having -- a table with an NPC in it is practice and unranked already
(`npc.declaration`) -- and it keeps the loop small enough to read.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

from switchboard import signing
from switchboard.client import Client
from switchboard.config import ClientConfig, MANAGED_HUB_TOKEN, MANAGED_HUB_URL

from . import npc
from .lobby import HOLD
from .run_entrant import claim, wait_for_invite

#: How long a table forms before this offers to fill it. Deliberately shorter
#: than `lobby.TABLE_TTL` (900s) and much longer than a settling table takes:
#: an NPC that raced real entrants to the seats would be the reason a table
#: had no people in it.
PATIENCE = 300.0

#: How often the seat's loop reads the board. An episode is 60s by default and
#: a trade takes three lines to complete (offer, approval, receipt), so this is
#: fast enough to finish one and slow enough not to be a hub load test.
EVERY = 2.0


def _client(*, hub: str, token: str | None, workspace: str, key: str | None,
            agent_id: str) -> Client:
    return Client(ClientConfig(url=hub, url_source="explicit", token=token,
                               workspace=workspace, key=key),
                  agent_id=agent_id)


def play(client: Client, channel: str, *, name: str,
         schedule: npc.PolicySchedule, every: float = EVERY,
         deadline: float | None = None,
         log=print) -> npc.Board:
    """One seat, until the manager says the round is over.

    Nothing prompts this and nothing waits for it, the same as every other
    seat: it reads when it wants and writes when it wants. The loop is here
    because a heuristic has to have *some* clock of its own, and polling the
    board is the smallest one that is not a turn.
    """
    board = npc.Board(player=name)
    seen: set[str] = set()
    started = time.time()
    client.post(channel, npc.declaration(name, schedule.mix))

    while not board.over and (deadline is None or time.time() < deadline):
        for msg in sorted(client.history(channel, limit=200),
                          key=lambda r: r.get("seq", 0)):
            mid = str(msg.get("id") or msg.get("seq"))
            body = msg.get("body")
            if mid in seen or not isinstance(body, str):
                continue
            seen.add(mid)
            board.read(body)

        # **The roster first, and it is not optional.** A whisper is opened by
        # deriving a secret with the *sender's* exchange key, and a client
        # that has never called `agents()` holds none -- so the manager's deal
        # arrives `unreadable` and is marked read on the way past. This seat
        # then plays a whole sealed round knowing neither its capacities nor
        # its tastes, which is exactly what it did the first time this was run
        # end to end: two seats, both acknowledged, nothing produced, a
        # trajectory of zeros. `games/island/requirements.txt` records the
        # same failure blinding both traders in `g5`.
        try:
            client.agents()
        except Exception:  # a poll that failed is not a round that ended
            pass

        # A sealed round deals the private half to this seat alone, and an
        # envelope this seat cannot open arrives marked rather than as content.
        for msg in client.inbox(wait=0.0, limit=50):
            body = msg.get("body")
            if isinstance(body, str) and not msg.get("unreadable"):
                board.read(body, mine=True)

        if board.ack_wanted and not board.acked:
            client.post(channel, f"ACK {name} is seated and reading.")
            board.acked = True

        policy = schedule.policy_at(time.time() - started)
        for line in npc.lines(policy, board, board.partners()):
            client.post(channel, line)
            npc.wrote(board, line)
            log(f"{name}: [{policy}] {line}", flush=True)

        if board.over:
            break
        time.sleep(every)
    return board


def seat(args) -> int:
    """Claim one seat in the lobby and play it. One process, one key."""
    agent_id = args.name
    mix = npc.parse_mix(args.mix)
    policy_seed = args.policy_seed if args.policy_seed is not None else secrets.randbits(32)
    schedule = npc.PolicySchedule(mix=mix, seed=policy_seed,
                                  mean_seconds=args.switch_mean)

    server = signing.SigningServer(signing.SigningIdentity.generate(), agent_id)
    if not server.start():
        raise SystemExit(
            "could not start a signer on this platform, so this NPC cannot "
            "hold one key across both rooms and its seat would never bind")
    board = None
    try:
        lobby = _client(hub=args.hub, token=args.token, workspace=args.workspace,
                        key=args.key, agent_id=agent_id)
        lobby.register(name=args.name, kind="local", branch="main",
                       task=f"playing the island as {args.name} (heuristic)")
        print(f"{args.name}: signing as {lobby.public_key}", flush=True)

        deadline = time.time() + args.wait
        table, episodes, goods = claim(lobby, args.channel, name=args.name,
                                       table=args.table, opening=None,
                                       goods=args.goods, every=args.every,
                                       deadline=deadline,
                                       # An NPC brings its half of the seed
                                       # like any seat: filling a table must
                                       # not also cost it a checkable draw.
                                       nonce=secrets.token_hex(16))
        print(f"{args.name}: claimed a seat on {table} "
              f"({episodes} episodes, {goods} goods)", flush=True)

        invite = wait_for_invite(lobby, args.channel, table,
                                 every=args.every, deadline=deadline)
        print(f"{args.name}: {table} settled, joining {invite.workspace}",
              flush=True)

        # `from_invite` rather than four fields copied across by hand: hub,
        # workspace, token and key each fail *silently* when they do not match
        # a peer's, leaving this seat alone in a room that looks quiet. Which
        # is exactly what assembling them here did, once, for a whole game.
        room = Client.from_invite(invite, agent_id=agent_id)
        # Registering here is what publishes this seat's exchange key in the
        # table's room, which is what a sealed deal is addressed to.
        room.register(name=args.name, kind="local", branch="main",
                      task=f"trading on {table}")
        # An episode's worth of slack past the announced end, so a manager that
        # started late still finds this seat here.
        board = play(room, args.island, name=args.name, schedule=schedule,
                     every=args.every,
                     deadline=time.time() + args.wait + episodes * 300)
        print(f"{args.name}: the round is over", flush=True)
    finally:
        server.close()
        if args.trace:
            args.trace.parent.mkdir(parents=True, exist_ok=True)
            args.trace.write_text(json.dumps({
                "name": args.name,
                "mix": mix,
                "policy_seed": policy_seed,
                "switch_mean_seconds": args.switch_mean,
                "seat": board.seat if board else None,
                # The order the policies came in. The board carries the mix;
                # only this carries which was live when.
                "schedule": schedule.trace(),
            }, indent=1) + "\n")
            print(f"{args.name}: policy trace in {args.trace}", flush=True)
    return 0


def _opened_at(msg: dict, default: float) -> float:
    """When the hub says a line was written, or `default` if it does not say.

    The lobby posts no deadline on its `is forming` line, so the only clock
    this watcher has is the hub's own timestamp on the message. Falling back
    to the reader's clock makes a restarted watcher patient again rather than
    seating somebody the moment it starts, which is the safer way to be wrong.
    """
    raw = msg.get("created_at")
    if not isinstance(raw, str):
        return default
    try:
        from datetime import datetime
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return default


def missing(client: Client, channel: str, *, patience: float,
            now: float | None = None, filler: str | None = None,
            min_real: int = 1) -> dict[str, int]:
    """Tables that have sat forming too long, and how many seats each lacks.

    Read off the lobby's own board and nothing else -- this process has no
    privileged view of the lobby and is not given one. Which means it can only
    see what it can count: `is forming` says how many seats a table wants,
    `seat ... =` says one was taken, and `is full` or `lapsed` ends it.

    **A table nobody turned up to is not filled.** `min_real` is how many of
    those seats have to be held by somebody who is not this filler before it
    offers anything, and it is 1 by default: the point of an NPC is that three
    entrants and an empty chair still play, never that a drawn island plays
    itself to an audience of nobody. A round with no people in it costs a seed,
    an hour of the lobby and a row in the archive, and answers no question that
    was asked -- and because `run_game` marks any board with an NPC on it
    `practice`, it cannot even be ranked afterwards.

    Which seats are this filler's own is read the same way as everything else
    here, off the name in the lobby's own `seat ... = <name>` line: `fill`
    seats `<filler>-<table>-<n>`, so `filler` is that prefix. Pass
    `min_real=0` for the old behaviour of filling anything short.
    """
    now = time.time() if now is None else now
    wants: dict[str, int] = {}
    taken: dict[str, int] = {}
    real: dict[str, int] = {}
    opened: dict[str, float] = {}
    done: set[str] = set()
    for msg in sorted(client.history(channel, limit=500),
                      key=lambda r: r.get("seq", 0)):
        body = msg.get("body")
        if not isinstance(body, str) or body.startswith(HOLD):
            continue
        parts = body.split()
        if len(parts) > 3 and parts[1:3] == ["is", "forming:"]:
            wants[parts[0]] = int(parts[3])
            opened[parts[0]] = _opened_at(msg, now)
        elif len(parts) > 2 and parts[1] == "seat":
            taken[parts[0]] = taken.get(parts[0], 0) + 1
            # `<table> seat <label> = <name>, ...` -- the name is what tells a
            # filled seat from a real one, and nothing else on the board does.
            seated_as = parts[4].rstrip(",") if len(parts) > 4 else ""
            if filler is None or not seated_as.startswith(f"{filler}-"):
                real[parts[0]] = real.get(parts[0], 0) + 1
        elif len(parts) > 2 and parts[1:3] == ["is", "full:"]:
            done.add(parts[0])
        elif len(parts) > 1 and parts[1] == "lapsed:":
            done.add(parts[0])
    return {t: wants[t] - taken.get(t, 0) for t in wants
            if t not in done and wants[t] > taken.get(t, 0)
            and real.get(t, 0) >= min_real
            and now - opened.get(t, now) >= patience}


def fill(args) -> int:
    """Watch the lobby; seat NPCs in tables that have waited long enough.

    It starts one child process per missing seat and never more than one per
    seat, because a second NPC claiming a seat somebody has just taken is a
    refusal on somebody else's board.
    """
    client = _client(hub=args.hub, token=args.token, workspace=args.workspace,
                     key=args.key, agent_id=args.name)
    client.register(name=args.name, kind="local", branch="main",
                    task="filling unfilled tables with heuristic players")
    print(f"filling on {args.hub}/{args.workspace}#{args.channel} after "
          f"{int(args.patience)}s, mix {npc.show_mix(npc.parse_mix(args.mix))}",
          flush=True)
    children: list[subprocess.Popen] = []
    seated: dict[str, int] = {}
    try:
        while True:
            for table, short in missing(client, args.channel,
                                        patience=args.patience,
                                        filler=args.name,
                                        min_real=args.min_real).items():
                for i in range(seated.get(table, 0), short):
                    name = f"{args.name}-{table}-{i + 1}"
                    print(f"{table}: {short} seat(s) unclaimed after "
                          f"{int(args.patience)}s -- seating {name}", flush=True)
                    children.append(subprocess.Popen(
                        [sys.executable, "-m", "games.island.run_npc",
                         "--hub", args.hub, "--workspace", args.workspace,
                         "--channel", args.channel, "--table", table,
                         "--name", name, "--mix", args.mix,
                         "--switch-mean", str(args.switch_mean),
                         "--trace", str(args.workdir / f"{name}.json")]
                        + (["--token", args.token] if args.token else [])
                        + (["--key", args.key] if args.key else [])))
                seated[table] = max(seated.get(table, 0), short)
            children = [c for c in children if c.poll() is None]
            time.sleep(max(args.every, 3.0))
    except KeyboardInterrupt:
        print()
        for child in children:
            child.terminate()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="npc", help="the seat name to claim")
    ap.add_argument("--hub", default=os.environ.get("SWITCHBOARD_URL") or MANAGED_HUB_URL)
    ap.add_argument("--token", default=os.environ.get("SWITCHBOARD_TOKEN") or MANAGED_HUB_TOKEN)
    ap.add_argument("--workspace", default=os.environ.get("SWITCHBOARD_WORKSPACE", "island-lobby"))
    ap.add_argument("--key", default=os.environ.get("SWITCHBOARD_KEY"))
    ap.add_argument("--channel", default="lobby")
    ap.add_argument("--island", default="island", help="the table's channel")
    ap.add_argument("--table", default=None, help="join this table rather than waiting")
    ap.add_argument("--goods", type=int, default=5)
    ap.add_argument("--mix", default=npc.show_mix(npc.DEFAULT_MIX).replace(", ", ","),
                    help="the distribution this NPC draws its policy from, "
                         f"over {', '.join(npc.POLICIES)}")
    ap.add_argument("--policy-seed", type=int, default=None,
                    help="fixes the sequence of policies, so a round is "
                         "reproducible from the trace file alone")
    ap.add_argument("--switch-mean", type=float, default=npc.SWITCH_MEAN_SECONDS,
                    help="mean seconds on one policy before redrawing")
    ap.add_argument("--every", type=float, default=EVERY)
    ap.add_argument("--wait", type=float, default=900.0)
    ap.add_argument("--trace", type=Path, default=None,
                    help="where to write which policy was live when")
    ap.add_argument("--workdir", type=Path, default=Path("games/npcs"))
    ap.add_argument("--fill", action="store_true",
                    help="watch the lobby and seat NPCs in tables that have "
                         "waited out --patience without filling")
    ap.add_argument("--patience", type=float, default=PATIENCE,
                    help="how long a table forms before this offers to fill it")
    ap.add_argument("--min-real", type=int, default=1,
                    help="how many seats must be held by somebody who is not "
                         "this filler before it seats anybody (default 1, so "
                         "a table nobody turned up to lapses rather than "
                         "playing itself; 0 fills anything short)")
    args = ap.parse_args(argv)
    npc.parse_mix(args.mix)  # refused here rather than after a seat is taken
    args.workdir.mkdir(parents=True, exist_ok=True)
    if args.fill:
        return fill(args)
    if args.trace is None:
        args.trace = args.workdir / f"{args.name}.json"
    return seat(args)


if __name__ == "__main__":
    raise SystemExit(main())
