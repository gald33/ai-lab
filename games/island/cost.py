"""What a managed game and an NPC seat cost, measured rather than guessed.

    python -m games.island.cost

Stands a hub of its own, plays one real game on it, and reports peak memory,
CPU, hub requests and bytes for each part. `HOSTING.md`'s "What a game and an
NPC actually cost" is this script's output; rerun it there and the numbers in
that table should move only with the machine.

**It measures processes, not functions.** A profiler would tell you where the
CPU went inside one process, which is not the question a host has. The
question is how many of these can run at once on a box, and that is answered
by RSS per process, requests per second at the hub, and bytes on the wire --
so those are what this counts, from outside, the way the operating system and
the hub see them.

Four windows, in order, because each answers something the others cannot:

1. **the lobby, idle** -- `run_game` watching a board with no tables. The
   floor: what a host pays to have a door open at all.
2. **one NPC, polling** -- a seat waiting for a table. What a filler costs
   while nothing is happening.
3. **a full game** -- `run_game` managing, two NPCs seated. The realistic
   total, on a board with real traffic on it.
4. **the manager alone** -- a table settled and played to seats that never
   bound, so nothing else is on the hub. The manager's own share, measured
   rather than subtracted out of (3).

The fourth exists because subtraction was the obvious way to get it and would
have been wrong: an NPC in a game polls more than an NPC waiting for one, so
(3) minus twice (2) charges the manager for the difference.

**Window 4 shares the workspace with window 3, so its runner declines window
3's table out loud** -- `g1 has 2 invites on the board, so more than one lobby
settled it`. That is `run_game.SettledTwice` working exactly as it should: two
runners on one board would settle every table twice, and it refuses rather
than minting a second room. It opens its own table and measures that. The line
in `game2.log` is expected; a *quiet* second runner would be the bug.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

#: Every HTTP request the hub served, and the bytes in and out of it. Counted
#: by an ASGI wrapper rather than read out of a log, so a request that failed
#: or returned nothing still counts -- a poll that got a 502 cost the same
#: round trip as one that got a board.
COUNT = {"req": 0, "in": 0, "out": 0}
_LOCK = threading.Lock()

_CLK = os.sysconf("SC_CLK_TCK")
_PAGE = os.sysconf("SC_PAGE_SIZE")


def counting(app):
    """Wrap an ASGI app so every request and its bytes are counted."""
    async def wrapped(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        n_in, n_out = [0], [0]

        async def rx():
            message = await receive()
            n_in[0] += len(message.get("body", b"") or b"")
            return message

        async def tx(message):
            n_out[0] += len(message.get("body", b"") or b"")
            await send(message)

        await app(scope, rx, tx)
        with _LOCK:
            COUNT["req"] += 1
            COUNT["in"] += n_in[0]
            COUNT["out"] += n_out[0]
    return wrapped


def usage(pid: int) -> tuple[int, float] | None:
    """(resident bytes, CPU seconds) for a pid, or None once it is gone.

    CPU is cumulative from process start, including the interpreter coming up.
    That is deliberate: startup is a real cost a host pays per process, and
    counting it makes every figure here an upper bound on the steady state
    rather than a flattering one.
    """
    try:
        fields = open(f"/proc/{pid}/stat").read().rsplit(") ", 1)[1].split()
        cpu = sum(int(fields[i]) for i in (11, 12, 13, 14)) / _CLK
        rss = int(open(f"/proc/{pid}/statm").read().split()[1]) * _PAGE
        return rss, cpu
    except (FileNotFoundError, IndexError, ProcessLookupError, ValueError):
        return None


def children(pid: int) -> list[int]:
    """Direct children, so `run_npc --fill` is charged for the seats it starts."""
    found = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True,
                           text=True)
    return [int(x) for x in found.stdout.split()] if found.returncode == 0 else []


class Window:
    """One measured stretch: a process tree, and the hub over the same seconds."""

    def __init__(self, label: str, pids, every: float = 0.5):
        self.label, self.pids, self.every = label, list(pids), every
        self.peak: dict[int, int] = {}
        self.cpu: dict[int, float] = {}
        self._stop = threading.Event()

    def __enter__(self):
        with _LOCK:
            self._req0, self._in0, self._out0 = (COUNT["req"], COUNT["in"],
                                                 COUNT["out"])
        self._t0 = time.time()
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()
        return self

    def _sample(self) -> None:
        while not self._stop.wait(self.every):
            for pid in list(self.pids):
                for one in [pid] + children(pid):
                    got = usage(one)
                    if got:
                        self.peak[one] = max(self.peak.get(one, 0), got[0])
                        self.cpu[one] = got[1]

    def __exit__(self, *_) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        self.wall = time.time() - self._t0
        with _LOCK:
            self.requests = COUNT["req"] - self._req0
            self.wire = (COUNT["in"] - self._in0) + (COUNT["out"] - self._out0)

    def report(self) -> dict:
        wall = max(self.wall, 1e-9)
        return {
            "label": self.label,
            "wall_s": round(self.wall, 1),
            "processes": len(self.peak),
            "peak_rss_mb": round(sum(self.peak.values()) / 1e6, 1),
            "cpu_s": round(sum(self.cpu.values()), 2),
            "cpu_pct_of_one_core": round(100 * sum(self.cpu.values()) / wall, 1),
            "hub_requests": self.requests,
            "requests_per_s": round(self.requests / wall, 2),
            "hub_bytes": self.wire,
            "bytes_per_s": round(self.wire / wall),
            "bytes_per_request": round(self.wire / self.requests) if self.requests else 0,
        }


def _hub(db: Path):
    """A hub in this process, counting everything it serves."""
    import uvicorn
    from switchboard.server import create_app
    from switchboard.config import ServerConfig
    from switchboard.store import Store

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    store = Store(str(db))
    app = counting(create_app(ServerConfig(db_path=store.path), store=store))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(400):
        if server.started:
            break
        time.sleep(0.05)
    else:  # pragma: no cover - only on a very slow machine
        raise SystemExit("hub did not start")
    return f"http://127.0.0.1:{port}", server


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--episodes", type=int, default=4)
    ap.add_argument("--seconds", type=int, default=15,
                    help="episode length; one of protocol.EPISODE_SECONDS_ALLOWED")
    ap.add_argument("--goods", type=int, default=5)
    ap.add_argument("--idle-window", type=float, default=30.0)
    ap.add_argument("--out", type=Path, default=Path("games/results/cost"))
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parents[2]
    tmp = args.out.resolve()
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    hub, server = _hub(tmp / "hub.db")
    key = generate_key()
    workspace = "w_cost"

    env = dict(os.environ, SWITCHBOARD_URL=hub, SWITCHBOARD_WORKSPACE=workspace,
               SWITCHBOARD_KEY=key, PYTHONPATH=str(root))
    env.pop("SWITCHBOARD_TOKEN", None)

    def client(agent_id: str) -> Client:
        one = Client(ClientConfig(url=hub, url_source="explicit",
                                  workspace=workspace, key=key), agent_id=agent_id)
        one.register(name=agent_id, kind="local", branch="main", task="")
        return one

    def runner(name: str, *extra: str, log: str) -> subprocess.Popen:
        return subprocess.Popen(
            [sys.executable, "-m", f"games.island.{name}", "--hub", hub,
             "--workspace", workspace, f"--key={key}", *extra],
            env=env, cwd=str(root),
            stdout=open(tmp / log, "w"), stderr=subprocess.STDOUT)

    windows = []
    game = runner("run_game", "--out", str(tmp / "out"),
                  "--episode-seconds", str(args.seconds), "--ack-seconds", "20",
                  "--every", "1", log="game.log")
    time.sleep(6)                     # past startup, into its own loop

    with Window("lobby, idle (run_game, no tables)", [game.pid]) as w:
        time.sleep(args.idle_window)
    windows.append(w.report())

    solo = runner("run_npc", "--name", "npc-solo", "--table", "nosuch",
                  "--wait", "40", "--every", "2",
                  "--workdir", str(tmp / "npcs"), log="solo.log")
    time.sleep(5)
    with Window("one NPC, polling for a table", [solo.pid]) as w:
        time.sleep(args.idle_window * 0.8)
    windows.append(w.report())
    solo.terminate()

    opener = client("opener")
    opener.post("lobby", f"OPEN traders=2 episodes={args.episodes} "
                         f"goods={args.goods} seconds={args.seconds}")
    # `--min-real 0`: the table this opens has nobody real at it, and the
    # filler's default (a table nobody turned up to lapses rather than
    # playing itself) is right for the lobby and wrong for a measurement.
    # Without it this window waited its whole limit and measured nothing.
    filler = runner("run_npc", "--fill", "--patience", "5", "--min-real", "0",
                    "--every", "2",
                    "--workdir", str(tmp / "npcs"), log="fill.log")
    record = tmp / "out" / "g1.json"
    with Window("a full game (run_game + 2 NPC seats)",
                [game.pid, filler.pid]) as w:
        _wait_for(record)
    windows.append(w.report())
    filler.terminate()
    game.terminate()
    time.sleep(1)

    disk = {p.name: p.stat().st_size
            for p in sorted(tmp.rglob("*")) if p.is_file()
            and p.suffix in (".json",) and "hub.db" not in p.name}
    played = json.loads(record.read_text()) if record.exists() else {}

    # --- the manager's own share, on a hub with nobody else on it ----------
    game2 = runner("run_game", "--out", str(tmp / "out2"),
                   "--episode-seconds", str(args.seconds), "--ack-seconds", "20",
                   "--every", "1", log="game2.log")
    time.sleep(6)
    opener.post("lobby", f"OPEN traders=2 episodes={args.episodes} "
                         f"goods={args.goods} seconds={args.seconds}")
    time.sleep(3)
    for seat, table in (("t-one", "g2"), ("t-two", "g2")):
        client(seat).post("lobby", f"JOIN {table} as {seat}")
    with Window("the manager alone (seats that never bound)", [game2.pid]) as w:
        _wait_for(tmp / "out2" / "g2.json")
    windows.append(w.report())
    game2.terminate()
    server.should_exit = True

    print(json.dumps({
        "game": {"episodes": args.episodes, "episode_seconds": args.seconds,
                 "goods": args.goods, "traders": 2},
        "windows": windows,
        "disk_bytes": disk,
        "disk_total": sum(disk.values()),
        "settled": (played.get("rounds") or [{}])[0].get("settled"),
    }, indent=1))
    return 0


def _wait_for(path: Path, limit: int = 600) -> None:
    for _ in range(limit):
        if path.exists():
            time.sleep(2)
            return
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
