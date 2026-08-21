"""Start the sessions, run the clock, read the board, settle, score.

That is the whole job. There is no scheduler here: agents are launched once and
never called again. Agents reach the hub through the **native Switchboard MCP
server** and nothing else -- there is no bespoke transport, no wrapper script,
and no tool this experiment invented. The manager reaches the same channel
through the Switchboard client, as one more participant. They read and write the board on their own initiative, at
whatever moment they choose, and this process never waits for any of them. The
clock advances on wall time whether anybody has spoken or not.

    python run_v3.py --arms bare both --rounds 1 --episodes 8 --agents 2

Per arm, per round: a fresh board, a fresh island under the round's seed, one
long-lived session per agent, and a manager reading the board behind them.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island  # noqa: E402


from switchboard.client import Client  # noqa: E402
from switchboard.config import ClientConfig  # noqa: E402

from island.manager import MANAGER, Manager  # noqa: E402

MODEL = "claude-haiku-4-5-20251001"
STIM = HERE / "stimuli" / "v3"

HUB = os.environ.get("SWITCHBOARD_URL", "http://127.0.0.1:8787")
TOKEN = os.environ.get("SWITCHBOARD_TOKEN", "sb_public_lucille")
WORKSPACE = os.environ.get("SWITCHBOARD_WORKSPACE", "island")

def client_for(agent_id: str, workspace: str) -> Client:
    """A client pinned to one workspace.

    Workspace cannot come from the environment here: the arms run in threads of
    one process and would share it. Each arm is its own workspace, so that two
    arms cannot see each other's roster, inboxes or direct messages -- a
    channel alone would not separate them, and `T1` in one arm and `T1` in the
    other are different traders who must not share an identity.
    """
    return Client(ClientConfig(url=HUB, url_source="explicit", token=TOKEN,
                               workspace=workspace, agent_id=agent_id))


#: The only tools an agent has. Everything else it might want to do, it does by
#: saying something on the channel.
TOOLS = ["mcp__switchboard__checkin", "mcp__switchboard__say",
         "mcp__switchboard__history", "mcp__switchboard__inbox",
         "mcp__switchboard__dm", "mcp__switchboard__roster",
         "mcp__switchboard__whoami", "Bash(sleep:*)"]

MCP_CONFIG = {
    "mcpServers": {
        "switchboard": {
            "command": "switchboard-mcp",
            "env": {"SWITCHBOARD_URL": HUB, "SWITCHBOARD_TOKEN": TOKEN,
                    "SWITCHBOARD_WORKSPACE": WORKSPACE},
        }
    }
}

#: arm -> (stimulus block or None, hint or not)
ARMS = {
    "bare":     (None,       False),
    "placebo":  ("placebo",  False),
    "protocol": ("protocol", False),
    "hint":     (None,       True),
    "both":     ("protocol", True),
}

#: The schedule, in seconds. Announced on the board and acknowledged before
#: every round, because context resets at the round boundary and an
#: acknowledgement carried over is consent from agents who no longer remember
#: giving it.
ACK_SECONDS = 120
PRODUCTION_SECONDS = 30
EPISODE_SECONDS = 60

#: How often the manager looks at the channel. It is a reader, so this only
#: decides how promptly receipts appear, never when an agent may act.
DRAIN_EVERY = 1.5


def body(text: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("## "):
            return "\n".join(lines[i:]).strip()
    raise ValueError("stimulus has no body heading")


def instructions(arm: str, private: str, episodes: int) -> str:
    block, hint = ARMS[arm]
    parts = [body((STIM / "base.md").read_text())]
    if block:
        parts.append(body((STIM / f"{block}.md").read_text()))
    if hint:
        parts.append(body((STIM / "hint.md").read_text()))
    parts.append(f"""## This round

{private}

This round is {episodes} episodes long, and every episode lasts
{EPISODE_SECONDS} seconds. Production is open for the first
{PRODUCTION_SECONDS} seconds of each episode; the market is open from then
until the bell. Your capacities and tastes are the same in every episode of
this round, and so is everyone else's.

An episode is short. Reading the whole channel every time will cost you more of
it than it is worth.

**Begin now.** Do not ask whether to start and do not wait to be told; there is
nobody to answer you, and the clock is already running. Your first act should be
`checkin`.

Nobody will prompt you, ever. Nothing will wake you up. There is no turn that
comes round to you, and if you stop acting you have left the island for good --
the clock keeps running, the other traders keep dealing, and the bell rings on
an episode you did nothing in.

So keep yourself awake. `checkin` is the loop tool: it says you are still here
and returns anything addressed to you since last time, and with `wait` it
blocks for up to 25 seconds until something arrives. Call it, act on whatever
came back, call it again. That is how you schedule your own next moment.

Thinking is not free here. Time spent composing a plan you never say is time
the episode spent without you. If you have worked something out, say it or act
on it, then check in again.

Never finish a reply without having called `checkin` or `say`. If you have
nothing to do, call `checkin` with `wait` set to 25 and see what arrives. Keep
going until the manager says the round is over. Only then stop.""")
    return "\n\n".join(parts)


def launch(name: str, arm: str, private: str, episodes: int,
           workdir: Path, workspace: str) -> subprocess.Popen:
    """One agent, one long-lived session. Started once and never called again."""
    home = workdir / name
    home.mkdir(parents=True, exist_ok=True)
    config = json.loads(json.dumps(MCP_CONFIG))
    config["mcpServers"]["switchboard"]["env"]["SWITCHBOARD_AGENT_ID"] = name
    config["mcpServers"]["switchboard"]["env"]["SWITCHBOARD_WORKSPACE"] = workspace
    (home / ".mcp.json").write_text(json.dumps(config, indent=1))
    env = dict(os.environ)
    env.update({"SWITCHBOARD_URL": HUB, "SWITCHBOARD_TOKEN": TOKEN,
                "SWITCHBOARD_WORKSPACE": workspace,
                "SWITCHBOARD_AGENT_ID": name})
    return subprocess.Popen(
        ["claude", "-p", instructions(arm, private, episodes),
         "--model", MODEL, "--max-turns", "400",
         "--mcp-config", str(home / ".mcp.json"),
         "--allowedTools", *TOOLS],
        cwd=home, env=env,
        stdout=open(home / "session.log", "w"), stderr=subprocess.STDOUT)


def schedule_text(episodes: int, names: tuple[str, ...]) -> str:
    return (f"Schedule for this round. {len(names)} traders: "
            f"{', '.join(names)}. {episodes} episodes, {EPISODE_SECONDS}s each. "
            f"In every episode PRODUCE is settled only in the first "
            f"{PRODUCTION_SECONDS}s; PROPOSE and APPROVE are settled from then "
            f"until the bell. At the bell open proposals lapse and everything "
            f"held is consumed. Acknowledge with a line beginning ACK. "
            f"Episode 1 opens in {ACK_SECONDS}s whether or not everyone has.")


def run_round(*, arm: str, seed: int, episodes: int, agents: int, goods: int,
              outdir: Path) -> dict:
    island = draw_island(agents, goods, seed=seed)
    workdir = outdir / f"{arm}-seed{seed}"
    workdir.mkdir(parents=True, exist_ok=True)
    workspace = f"{WORKSPACE}-{arm}-{seed}"
    channel = "island"
    client = client_for(MANAGER, workspace)
    mgr = Manager(island=island, client=client, channel=channel)
    for n in mgr.names:
        mgr.bind(client_for(n, workspace).peer_id(n), n)
    started = time.time()

    mgr.say(schedule_text(episodes, mgr.names))
    procs = [launch(n, arm, mgr.private_state(n), episodes, workdir, workspace)
             for n in mgr.names]


    # A session that cannot start -- unreachable API, bad MCP config -- is a
    # harness fault, and spending ten minutes of clock on it would record an
    # empty round as though the agents had chosen silence. But a session that
    # starts and then stops has made a choice, and that is a datum, not a
    # fault. The two are told apart by what the runtime said, not by the fact
    # of exiting.
    time.sleep(20)
    broken = {}
    for name, proc in zip(mgr.names, procs):
        if proc.poll() is None:
            continue
        log = (workdir / name / "session.log").read_text()
        if any(sig in log for sig in ("API Error", "Invalid MCP",
                                      "not found", "Execution error")):
            broken[name] = log[:200]
    if broken:
        mgr.say(f"harness fault: {', '.join(sorted(broken))} could not start")
        raise RuntimeError("agent sessions failed to start: "
                           + "; ".join(f"{n}: {w.strip()}" for n, w in broken.items()))
    def wait_until(deadline: float) -> None:
        while time.time() < deadline:
            mgr.drain()
            time.sleep(DRAIN_EVERY)
        mgr.drain()

    wait_until(started + ACK_SECONDS)
    mgr.say(f"{len(mgr.acknowledged)}/{len(mgr.names)} acknowledged "
                       f"({', '.join(sorted(mgr.acknowledged)) or 'nobody'}). "
                       f"Episode 1 opens now.")

    for e in range(episodes):
        mgr.production_open, mgr.market_open = True, False
        t0 = time.time()
        mgr.say(f"episode {e + 1} of {episodes} is open. PRODUCE is "
                           f"settled for the next {PRODUCTION_SECONDS}s.")
        wait_until(t0 + PRODUCTION_SECONDS)
        mgr.production_open, mgr.market_open = False, True
        mgr.say("production is closed. PROPOSE and APPROVE are "
                           "settled until the bell.")
        wait_until(t0 + EPISODE_SECONDS)
        mgr.close_episode()

    mgr.say("the round is over. Stop; nothing further will settle.")
    time.sleep(3)
    for p in procs:
        p.terminate()
    for p in procs:
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            p.kill()

    return {"arm": arm, "seed": seed, "episodes": episodes,
            "trajectory": mgr.episode_utilities,
            "settled": mgr.settled, "refused": mgr.refused, "talk": mgr.talk,
            "acknowledged": sorted(mgr.acknowledged),
            "workspace": workspace, "channel": channel,
            "channel_messages": len(client.history(channel, limit=500)),
            "seconds": round(time.time() - started, 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["bare", "both"])
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--episodes", type=int, default=8)
    ap.add_argument("--agents", type=int, default=2)
    ap.add_argument("--goods", type=int, default=4)
    ap.add_argument("--out", default="results/v3")
    args = ap.parse_args()

    for arm in args.arms:
        if arm not in ARMS:
            raise SystemExit(f"unknown arm {arm!r}; have {', '.join(ARMS)}")

    outdir = HERE / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    wall = (ACK_SECONDS + args.episodes * EPISODE_SECONDS) / 60
    print(f"model {MODEL}  arms {args.arms}  rounds {args.rounds}  "
          f"episodes {args.episodes}  agents {args.agents}")
    print(f"clock-bound: {wall:.1f} min, and the arms run at the same time on "
          f"separate channels, so the wall-clock is {wall:.1f} min however "
          f"many arms there are.\n")

    from island.score import score  # noqa: PLC0415

    jobs = [(arm, seed) for arm in args.arms
            for seed in range(1, args.rounds + 1)]
    lock = threading.Lock()

    def one(job):
        arm, seed = job
        rec = run_round(arm=arm, seed=seed, episodes=args.episodes,
                        agents=args.agents, goods=args.goods, outdir=outdir)
        s = score(draw_island(args.agents, args.goods, seed=seed),
                  rec["trajectory"])
        rec["score"] = s.to_json()
        per = " ".join(f"{x:.2f}" for x in s.eff_episode)
        with lock:
            print(f"  {arm:9s} seed {seed}  eff_round {s.eff_round:.3f}  "
                  f"floor {s.floor:.3f}  per-episode [{per}]  "
                  f"settled {rec['settled']}  refused {rec['refused']}  "
                  f"talk {rec['talk']}  ack {len(rec['acknowledged'])}/"
                  f"{args.agents}  {rec['seconds'] / 60:.0f}m", flush=True)
        return rec

    # Arms are independent worlds on independent channels. Running them at the
    # same time is not a shortcut: nothing crosses between them, and the clock
    # each one runs on is its own.
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        records = list(pool.map(one, jobs))

    path = outdir / "v3.json"
    path.write_text(json.dumps(
        {"experiment": "005-v3", "model": MODEL, "arms": args.arms,
         "agents": args.agents, "goods": args.goods,
         "episodes_per_round": args.episodes,
         "schedule": {"ack_seconds": ACK_SECONDS,
                      "production_seconds": PRODUCTION_SECONDS,
                      "episode_seconds": EPISODE_SECONDS},
         "rounds": records}, indent=1))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
