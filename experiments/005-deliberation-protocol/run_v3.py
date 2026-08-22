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
import pathlib
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

# A SWITCHBOARD_KEY in this process's environment makes the *manager* sign and
# encrypt, whether or not the config asks for it, and the workspace becomes an
# encrypted one. Agents launched without that key can still read, so the
# failure looks partial and reads like a hub fault -- which is exactly how one
# of them diagnosed it: "read operations work... the hub's signing service is
# not responding to write requests". Nothing was wrong with the hub. Drop the
# key before any client is built, so manager and agents are on the same footing.
os.environ.pop("SWITCHBOARD_KEY", None)


# TLS trust. This session reaches the hub through an egress proxy, and the CA
# file the environment points every tool at carries the proxy's own roots but
# not the public ones -- and the hub presents a real public chain. curl happens
# to survive that; anything on Python's ssl module does not, so httpx raises
# CERTIFICATE_VERIFY_FAILED and every Switchboard call becomes "internal
# error". That is a harness fault wearing the costume of agent silence: the
# sessions start, find every tool broken, ask to have it fixed, and stop. It
# cost a run mid-flight when the bundle was rewritten one minute after launch.
#
# So build one bundle that holds both: every certificate in the system store
# and every certificate the proxy supplies. Verification stays on -- this adds
# roots, it never disables a check -- and the file is exported so that the
# agents' MCP subprocesses, which get an explicit env and would otherwise
# inherit nothing, trust exactly what the manager trusts.
def _ca_bundle() -> str:
    import glob
    import re

    out: list[str] = []
    for f in [*sorted(glob.glob("/etc/ssl/certs/*.pem")),
              os.environ.get("SSL_CERT_FILE", ""),
              "/root/.ccr/ca-bundle.crt"]:
        if not f:
            continue
        try:
            text = pathlib.Path(f).read_text()
        except OSError:
            continue
        out += re.findall(
            r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", text, re.S)
    seen: set[str] = set()
    keep = [c for c in out if not (c in seen or seen.add(c))]
    path = HERE / ".ca-bundle.pem"
    path.write_text("\n".join(keep) + "\n")
    return str(path)


CA_BUNDLE = _ca_bundle()
for _var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
    os.environ[_var] = CA_BUNDLE

# The managed hub is the default: a local `switchboard serve` is one more
# thing to keep alive, and it died between runs more than once. The managed
# one is reachable, versioned and not this experiment's to operate.
from switchboard.config import MANAGED_HUB_TOKEN, MANAGED_HUB_URL  # noqa: E402

HUB = os.environ.get("SWITCHBOARD_URL") or MANAGED_HUB_URL
TOKEN = os.environ.get("SWITCHBOARD_TOKEN") or MANAGED_HUB_TOKEN
WORKSPACE = os.environ.get("SWITCHBOARD_WORKSPACE", "island")

# One stamp per run, so every round of it gets a workspace no earlier run has
# written to. Recorded in the result: a board that cannot be found again is not
# evidence.
RUN_STAMP = time.strftime("%m%dT%H%M", time.gmtime())

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
                    "SWITCHBOARD_WORKSPACE": WORKSPACE,
                    # An MCP server gets this env and not the parent's, so the
                    # trust and proxy settings have to be named here or every
                    # tool the agent holds fails at the TLS handshake.
                    "SSL_CERT_FILE": CA_BUNDLE,
                    "REQUESTS_CA_BUNDLE": CA_BUNDLE,
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    "HTTPS_PROXY": os.environ.get("HTTPS_PROXY", ""),
                    "NO_PROXY": os.environ.get("NO_PROXY", "")},
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

#: The screen. Ten one-off advice blocks, run as ten arms on one seed, to find
#: out cheaply which kinds of advice move anything at all. These are
#: deliberately impure — a block may mix a communication convention with a
#: domain suggestion — because the point is to find a live one and only then
#: decompose it into its protocol part and its hint part and test those
#: separately. A screen is not an experiment: ten numbers on one draw have no
#: error bars, and whatever wins here is a hypothesis to be re-run, not a
#: result. Nothing under stimuli/screen/ is frozen or citable.
SCREEN = {
    "s01": "screen/s01-manager",
    "s02": "screen/s02-protocol",
    "s03": "screen/s03-coupling",
    "s04": "screen/s04-coverage",
    "s05": "screen/s05-advantage",
    "s06": "screen/s06-example",
    "s07": "screen/s07-checklist",
    "s08": "screen/s08-population",
    "s09": "screen/s09-failures",
    "s10": "screen/s10-ask",
}
ARMS.update({name: (block, False) for name, block in SCREEN.items()})

#: The persistence check (run 003). Not about advice: run 002 aborted because
#: every session ended itself while a round it had been told was thirty
#: episodes long still had twenty-seven to go. These cells ask whether that is
#: the harness starving the agents or the agents being unable to do the task.
#:
#: `persist-improve` is a domain instruction and is named as one. It is a
#: ceiling test, and nothing measured with it is evidence about protocols.
ARMS.update({
    "persist-bare":    (None, False),
    "persist-nocount": (None, False),
    "persist-improve": ("persist/improve", False),
})

#: Arms in which the round's length is never stated. The manager announces a
#: few episodes at a time and says nothing about the total, so an agent cannot
#: reason about "the remaining 27 episodes" -- which is what every session in
#: run 002 did on its way out.
HIDE_HORIZON = {"persist-nocount"}

#: How many episodes the manager names at once when the horizon is hidden.
CHUNK = 5

#: The idle check (run 004). Run 003 showed the same instructions and the same
#: announced horizon persist to episode 30 at 45s and die by episode 8 at 180s,
#: so a harness parameter is doing the work. These cells ask which one: the
#: length of the episode, or the emptiness of the wait inside it.
#:
#: `idle-tick` keeps the 180s episode and has the manager post the time
#: remaining every 30s, so a `checkin(wait=25)` returns with something instead
#: of timing out on a dead board. That is a **timing announcement** -- it is
#: addressed to nobody, tells no one to act, and asks no one for anything, which
#: is the line the standing decisions draw. It is still a departure from a
#: silent episode and is recorded as one.
ARMS.update({
    "idle-long":  (None, False),
    "idle-tick":  (None, False),
    "idle-short": (None, False),
})
TICKING = {"idle-tick"}
TICK_SECONDS = 30

#: The schedule, in seconds. Announced on the board and acknowledged before
#: every round, because context resets at the round boundary and an
#: acknowledgement carried over is consent from agents who no longer remember
#: giving it.
#:
#: Defaults, overridable per run and recorded in the result: the shape of the
#: clock is a design parameter, not a constant, and a record that does not say
#: which clock it ran on cannot be compared with one that ran on another.
ACK_SECONDS = 120
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


def _horizon(arm: str, episodes: int) -> str:
    """What the agent is told about how long the round is."""
    if arm in HIDE_HORIZON:
        return (f"Every episode lasts {EPISODE_SECONDS} seconds. The manager "
                f"says which episodes are scheduled next and will tell you when "
                f"the round is over; until it does, the round is still running.")
    return (f"This round is {episodes} episodes long, and every episode lasts "
            f"{EPISODE_SECONDS} seconds.")


def instructions(arm: str, private: str, episodes: int) -> str:
    block, hint = ARMS[arm]
    parts = [body((STIM / "base.md").read_text())]
    if block:
        # A block naming a directory ("screen/s01-terse") is resolved against
        # the stimuli root, so the screen's un-frozen blocks never sit in the
        # frozen v3 directory.
        path = (STIM.parent / f"{block}.md") if "/" in block else (STIM / f"{block}.md")
        parts.append(body(path.read_text()))
    if hint:
        parts.append(body((STIM / "hint.md").read_text()))
    parts.append(f"""## This round

{private}

{_horizon(arm, episodes)} There are no stages inside an episode: from the
moment it opens until the bell, producing, proposing and approving all settle.
Your capacities and tastes are the same in every episode of this round, and so
is everyone else's.

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
           workdir: Path, workspace: str, *, max_turns: int) -> subprocess.Popen:
    """One agent, one long-lived session. Started once and never called again."""
    home = workdir / name
    home.mkdir(parents=True, exist_ok=True)
    config = json.loads(json.dumps(MCP_CONFIG))
    config["mcpServers"]["switchboard"]["env"]["SWITCHBOARD_AGENT_ID"] = name
    config["mcpServers"]["switchboard"]["env"]["SWITCHBOARD_WORKSPACE"] = workspace
    (home / ".mcp.json").write_text(json.dumps(config, indent=1))
    env = dict(os.environ)
    env.update({"SSL_CERT_FILE": CA_BUNDLE, "REQUESTS_CA_BUNDLE": CA_BUNDLE,
                "SWITCHBOARD_URL": HUB, "SWITCHBOARD_TOKEN": TOKEN,
                "SWITCHBOARD_WORKSPACE": workspace,
                "SWITCHBOARD_AGENT_ID": name})
    return subprocess.Popen(
        ["claude", "-p", instructions(arm, private, episodes),
         "--model", MODEL, "--max-turns", str(max_turns),
         "--mcp-config", str(home / ".mcp.json"),
         "--allowedTools", *TOOLS],
        cwd=home, env=env,
        stdout=open(home / "session.log", "w"), stderr=subprocess.STDOUT)


def preflight() -> None:
    """Prove an agent's own toolchain works before spending a run on it.

    The screen's first attempt died four minutes in: every session started,
    found every Switchboard tool returning "internal error", asked to have the
    connection fixed, and stopped. The manager was fine -- it had the parent
    environment -- so nothing upstream looked wrong, and the guard below reads
    a session that starts and stops as a choice, which is what it usually is.

    An agent reaches the hub through `switchboard-mcp` with the env this file
    hands it, and nothing else. So check that exact path: spawn the server the
    way an agent gets it and call one tool. Ten seconds here against fifty
    rounds of silence is not a close trade.
    """
    import shutil  # noqa: PLC0415

    if not shutil.which("switchboard-mcp"):
        raise SystemExit("preflight: switchboard-mcp is not on PATH")
    env = dict(MCP_CONFIG["mcpServers"]["switchboard"]["env"])
    env["SWITCHBOARD_AGENT_ID"] = "preflight"
    calls = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "preflight", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "whoami", "arguments": {}}},
    ]
    try:
        done = subprocess.run(  # noqa: S603
            ["switchboard-mcp"], input="\n".join(json.dumps(c) for c in calls),
            env=env, capture_output=True, text=True, timeout=45, check=False)
    except subprocess.TimeoutExpired:
        raise SystemExit("preflight: switchboard-mcp did not answer in 45s") from None
    out = done.stdout + done.stderr
    if '"isError": true' in out or '"id": 2' not in out:
        raise SystemExit(
            "preflight: an agent's own MCP server could not reach the hub, so "
            "every agent would start, find its tools broken and stop. This is "
            "a harness fault, not agent behaviour.\n"
            f"  hub {HUB}\n  last output: {out[-400:].strip()}")
    print(f"preflight: an agent's switchboard-mcp reached {HUB}")


def schedule_text(episodes: int, names: tuple[str, ...], *, hide: bool = False) -> str:
    span = (f"Episodes are {EPISODE_SECONDS}s each; the next few are announced "
            f"as they come." if hide
            else f"{episodes} episodes, {EPISODE_SECONDS}s each.")
    return (f"Schedule for this round. {len(names)} traders: "
            f"{', '.join(names)}. {span} "
            f"Within an episode there are no stages: PRODUCE, PROPOSE and "
            f"APPROVE all settle for as long as the episode is open. At the "
            f"bell open proposals lapse and everything held is consumed. "
            f"Acknowledge with a line beginning ACK. "
            f"Episode 1 opens in {ACK_SECONDS}s whether or not everyone has.")


def run_round(*, arm: str, seed: int, episodes: int, agents: int, goods: int,
              outdir: Path) -> dict:
    island = draw_island(agents, goods, seed=seed)
    workdir = outdir / f"{arm}-seed{seed}"
    workdir.mkdir(parents=True, exist_ok=True)
    # The stamp is what keeps one run's board out of the next one's. Messages
    # live an hour on the hub, so a workspace named only for its arm and seed
    # still holds the last run's schedule, bells and episode openings -- and a
    # trader calling history reads a bell that belongs to a round that no
    # longer exists. That is contamination of the stimulus, not untidiness.
    workspace = f"{WORKSPACE}-{arm}-{seed}-{RUN_STAMP}"
    channel = "island"
    client = client_for(MANAGER, workspace)
    mgr = Manager(island=island, client=client, channel=channel)
    for n in mgr.names:
        mgr.bind(client_for(n, workspace).peer_id(n), n)
    started = time.time()

    hide = arm in HIDE_HORIZON
    mgr.say(schedule_text(episodes, mgr.names, hide=hide))
    # A turn cap that never bound at three episodes will bind at thirty, and an
    # agent cut off mid-round goes silent in a way that reads exactly like
    # choosing to stop. Scale it with the work, with headroom.
    procs = [launch(n, arm, mgr.private_state(n), episodes, workdir, workspace,
                    max_turns=max(400, 40 * episodes))
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
    ticks = arm in TICKING

    def wait_until(deadline: float, *, tick: bool = False) -> None:
        next_tick = time.time() + TICK_SECONDS
        while time.time() < deadline:
            mgr.drain()
            if tick and time.time() >= next_tick and deadline - time.time() > 5:
                mgr.say(f"{round(deadline - time.time())}s remain in this episode.")
                next_tick = time.time() + TICK_SECONDS
            time.sleep(DRAIN_EVERY)
        mgr.drain()

    wait_until(started + ACK_SECONDS)
    mgr.say(f"{len(mgr.acknowledged)}/{len(mgr.names)} acknowledged "
                       f"({', '.join(sorted(mgr.acknowledged)) or 'nobody'}). "
                       f"Episode 1 opens now.")

    for e in range(episodes):
        mgr.open_episode()
        t0 = time.time()
        if hide:
            # A few at a time, and never a total. An agent that cannot count
            # the episodes left cannot decide to delegate them.
            if e % CHUNK == 0:
                last = min(e + CHUNK, episodes)
                mgr.say(f"episodes {e + 1} to {last} are scheduled next, "
                        f"{EPISODE_SECONDS}s each.")
            mgr.say(f"episode {e + 1} is open for {EPISODE_SECONDS}s. "
                    f"PRODUCE, PROPOSE and APPROVE all settle until the bell.")
        else:
            mgr.say(f"episode {e + 1} of {episodes} is open for {EPISODE_SECONDS}s. "
                    f"PRODUCE, PROPOSE and APPROVE all settle until the bell.")
        wait_until(t0 + EPISODE_SECONDS, tick=ticks)
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
            # The screen had to be diagnosed by re-reading boards that expire
            # in an hour. What the metrics cannot say goes in the record.
            "episode_log": mgr.episode_log, "refusals": mgr.refusals,
            "settled": mgr.settled, "refused": mgr.refused, "talk": mgr.talk,
            "acknowledged": sorted(mgr.acknowledged),
            "workspace": workspace, "channel": channel, "run_stamp": RUN_STAMP,
            # Counted by the manager as it drained, not by a final history
            # call: that call caps at 500 rows, and hub messages expire after
            # an hour, so on a round longer than that the board is no longer a
            # complete record of itself. The per-episode ledger is.
            "channel_messages": len(mgr.seen),
            "drain_saturated": mgr.saturated,
            "seconds": round(time.time() - started, 1)}


def main() -> None:
    global ACK_SECONDS, EPISODE_SECONDS
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["bare", "both"])
    ap.add_argument("--rounds", type=int, default=1)
    ap.add_argument("--episodes", type=int, default=8)
    ap.add_argument("--agents", type=int, default=2)
    ap.add_argument("--goods", type=int, default=4)
    ap.add_argument("--out", default="results/v3")
    ap.add_argument("--episode-seconds", type=int, default=60)
    ap.add_argument("--ack-seconds", type=int, default=120)
    # Rounds are independent worlds and could all run at once, but the box and
    # the hub are not independent of each other. A cap trades wall-clock for
    # headroom; it changes nothing any agent sees, since each round's clock
    # starts when that round starts.
    ap.add_argument("--max-concurrent", type=int, default=10)
    ap.add_argument("--no-control", action="store_true",
                    help="run without a control arm, and record that choice")
    args = ap.parse_args()

    for arm in args.arms:
        if arm not in ARMS:
            raise SystemExit(f"unknown arm {arm!r}; have {', '.join(ARMS)}")

    ACK_SECONDS = args.ack_seconds
    EPISODE_SECONDS = args.episode_seconds

    # A run without a control measures its arms against the autarky floor and
    # nothing else, so it cannot say whether any block beat saying nothing.
    # The ten-arm screen had no control and could not answer that -- and a
    # baseline cannot be borrowed from an earlier run, whose code, clock and
    # trust settings all differed. Refuse by default; allow it to be waived
    # out loud, in the command that runs it and in the record.
    CONTROLS = ("bare", "placebo")
    if not any(a in CONTROLS for a in args.arms) and not args.no_control:
        raise SystemExit(
            f"no control arm: none of {', '.join(CONTROLS)} is in {args.arms}. "
            "Without one, 'no arm beat the floor' cannot be told from 'no arm "
            "beat saying nothing'. Add a control, or pass --no-control if the "
            "run genuinely does not need one.")

    outdir = HERE / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    wall = (ACK_SECONDS + args.episodes * EPISODE_SECONDS) / 60
    print(f"model {MODEL}  arms {args.arms}  rounds {args.rounds}  "
          f"episodes {args.episodes}  agents {args.agents}")
    n_jobs = len(args.arms) * args.rounds
    waves = -(-n_jobs // min(args.max_concurrent, n_jobs))
    print(f"clock-bound: {wall:.1f} min per round; {n_jobs} rounds at "
          f"{args.max_concurrent} at a time is {waves} wave(s), so about "
          f"{waves * wall:.0f} min of wall-clock and {n_jobs * args.agents} "
          f"agent sessions.\n")

    preflight()

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
    workers = min(args.max_concurrent, len(jobs))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(one, jobs))

    path = outdir / "v3.json"
    path.write_text(json.dumps(
        {"experiment": "005-v3", "model": MODEL, "arms": args.arms,
         "no_control": bool(args.no_control),
         "agents": args.agents, "goods": args.goods,
         "episodes_per_round": args.episodes,
         "schedule": {"ack_seconds": ACK_SECONDS,
                      "episode_seconds": EPISODE_SECONDS},
         "rounds": records}, indent=1))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
