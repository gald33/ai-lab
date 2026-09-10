"""Rung 0 — how far does this instrument move when nothing is varied?

    python noise.py --replicates 8 --games 12 --traders 4 --episodes 4 --seconds 60 \
      --workers 8

Plays the same cell, on the same island seeds, with the same NPC policies,
`--replicates` times, and reports a between-replicate sd per endpoint with its
denominator. No model is called and nothing is spent.

**This is the gate that has no pass mark.** It produces the number every
threshold in `PREREGISTRATION.md` is written against. The lab's most expensive
lesson is that four treatments were run against pre-registered thresholds of
0.10-0.15 on an instrument whose own between-run movement was later measured at
0.229 on the ratio and 1.03 per round; rows 10-16 of the hypothesis ledger are
the wreckage, and the measurement that would have prevented all of it cost one
afternoon and was run last. Here it is run first.

**Nothing here is a treatment.** Every replicate is identical by construction,
and the runner asserts that the seeds it played match across replicates rather
than trusting itself -- an "identical" cell that quietly drew different islands
would report seed variance as instrument noise, which is the one way this
measurement can lie and still look sane.

## What is deliberately weaker than a real game, and said out loud

- **The seed is pinned, so the draw is `unverified` rather than
  `commit-reveal`.** A noise measurement needs the same island in every
  replicate, and a commit-reveal draw is by design not choosable. These games
  are therefore not checkable in their draw and must never be ranked -- kept
  and counted, never ranked, exactly as `games/island.md` requires of every
  weaker game.
- **The seats are heuristics, not models, and heuristics are deterministic.**
  Measured on the first live run: two replicates of the identical cell returned
  byte-identical endpoints, `capture` agreeing to sixteen digits. Same island
  seed and same policy seed means same play, so with `--vary-npc-seed` off this
  reports **zero**, and zero is the true answer to the question it is asking:
  *how much does the harness itself move when nothing varies?* Not much.

  **That is not the number a threshold is written against.** For a model cell
  the dominant term is sampling variance in the agents, which no NPC run
  contains — the previously measured 0.229 and 1.03 are agent variance, not
  harness variance. So the free rung establishes the floor and **the
  threshold-setting measurement needs models and costs money.** This module's
  docstring said the opposite when it was written; see run 001.

  `--vary-npc-seed` draws a fresh policy seed per replicate, which adds the
  policy-draw component while holding the island fixed. That is a third
  quantity again — not agent variance either, but a better lower bound than
  zero.

- **Games run concurrently, and that is not outside the measurement.** A game
  is a wall clock — episodes are real seconds and NPC seats act on a timer — so
  machine load can in principle move when a seat reaches the board. Playing
  8 × 12 games serially is about seven hours, which `PREFLIGHT.md` gate 2
  budgets and offers concurrency as the alternative to; `--workers` is that
  alternative. If concurrency does shift the play, replicates stop coming back
  identical and the sd reported here is the variance concurrency injects —
  which is the honest floor for any real run, because a real run is concurrent
  too. Both outcomes are reported and neither is repaired into the other. See
  `plan()` for why the job order is seed-major, and run 002.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import json
import socket
import statistics
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
#: The viewer's ledger scores what the manager settled. On the path rather than
#: imported through a package because that is how every other caller reaches it.
sys.path.insert(0, str(REPO / "experiments" / "does-a-content-free-protocol-help"
                       / "viewer"))

from switchboard import signing                                    # noqa: E402
from switchboard.client import Client                              # noqa: E402
from switchboard.config import ClientConfig                        # noqa: E402
from switchboard.crypto import generate_key                        # noqa: E402

from games.island import npc, run_game                             # noqa: E402
from games.island.lobby import Lobby                               # noqa: E402
from games.island.run_npc import play as play_seat                 # noqa: E402

import scores                                                      # noqa: E402

#: The endpoints, in the order `PREREGISTRATION.md` freezes them. The first is
#: the primary and is a count; the rest are reported beside it and never
#: instead of it.
ENDPOINTS = ("zero_episode_share", "capture", "above_autarky_share", "eff_round")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def hub(tmp: Path):
    """A real hub on a real port, for the length of one game.

    Not a mock, for `games/island/tests/conftest.py`'s reason: the lobby and
    every seat read through the real client, so what is measured is what runs.
    """
    import uvicorn
    from switchboard.server import create_app
    from switchboard.config import ServerConfig
    from switchboard.store import Store

    port = _free_port()
    store = Store(str(tmp / "hub.db"))
    app = create_app(ServerConfig(db_path=store.path), store=store)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(400):
        if server.started:
            break
        time.sleep(0.05)
    else:                                              # pragma: no cover
        raise RuntimeError("hub did not start")
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@dataclass
class Cell:
    """One cell of the design. Every field here is held fixed across replicates."""

    traders: int = 4
    goods: int = 5
    episodes: int = 4
    seconds: int = 60
    ack_seconds: int = 10
    mix: dict[str, float] = field(
        default_factory=lambda: dict(npc.DEFAULT_MIX))

    def open_line(self) -> str:
        return (f"OPEN traders={self.traders} episodes={self.episodes} "
                f"rounds=1 goods={self.goods} seconds={self.seconds}")


def endpoints_from(row: dict, episodes: int) -> dict[str, float | None]:
    """The four endpoints, off one ledger row.

    Read from settled state via the viewer's own ledger, never from anything a
    seat said about itself.
    """
    eff, floor = row.get("eff_round"), row.get("autarky_floor")
    zeros = row.get("zero_episodes") or {}
    ratios = row.get("ratios") or {}

    seats = len(zeros) or None
    return {
        # The primary. Bounded in [0, 1] and defined on every trader in every
        # episode, which is what `capture` is not.
        "zero_episode_share": (
            sum(zeros.values()) / (seats * episodes) if seats else None),
        "capture": scores.captured(eff, floor),
        "above_autarky_share": (
            sum(1 for r in ratios.values() if r is not None and r > 1.0)
            / len(ratios) if ratios else None),
        "eff_round": eff,
    }


def play_one(seed: int, cell: Cell, *, npc_seed: int, tmp: Path,
             log=print) -> dict:
    """One whole game on a pinned island, from an empty lobby to a scored row.

    Returns the ledger row's endpoints plus the seed actually played, so the
    caller can assert the replicates really were identical.
    """
    names = [f"npc-{i + 1}" for i in range(cell.traders)]
    agent_ids = [f"t{i + 1}" for i in range(cell.traders)]

    servers = []
    for agent_id in agent_ids:
        server = signing.SigningServer(signing.SigningIdentity.generate(), agent_id)
        if not server.start():                        # pragma: no cover
            raise RuntimeError("no AF_UNIX signer available on this platform")
        servers.append(server)

    try:
        with hub(tmp) as url:
            key = generate_key()

            def client(agent_id: str) -> Client:
                return Client(ClientConfig(url=url, url_source="explicit",
                                           workspace="w_rung0", key=key),
                              agent_id=agent_id)

            lobby = Lobby(client=client("lobby"))
            # Pinned, so every replicate plays the same island. The draw is
            # therefore `unverified` -- see this module's docstring.
            lobby.draw_seed = lambda: seed

            client("opener").post("lobby", cell.open_line())
            lobby.drain()

            seats = {}
            for name, agent_id in zip(names, agent_ids):
                entrant = client(agent_id)
                entrant.register(name=agent_id, kind="local", branch="main", task="")
                entrant.post("lobby", f"JOIN g1 as {name}")
                seats[name] = agent_id

            manager = client("m")
            manager.register(name="rung0", kind="local", branch="main", task="")
            manager.post("lobby", "MANAGE g1")
            lobby.drain()

            table = lobby.tables["g1"]
            if not table.settled or table.seed is None:
                raise RuntimeError(f"table did not settle: {len(table.seats)} seats")

            invite = run_game.pending_invite(lobby, table)
            if invite is None:
                raise RuntimeError("the lobby settled without posting an invite")

            # Each seat moves to the table's room keeping the agent id, and so
            # the signing key, it took its seat under.
            deadline = time.time() + cell.ack_seconds + cell.episodes * cell.seconds + 60
            threads = []
            for i, (name, agent_id) in enumerate(seats.items()):
                room = Client.from_invite(invite, agent_id=agent_id)
                room.register(name=name, kind="local", branch="main", task="trading")
                schedule = npc.PolicySchedule(mix=cell.mix, seed=npc_seed + i,
                                              mean_seconds=max(2.0, cell.seconds / 6))
                thread = threading.Thread(
                    target=play_seat, args=(room, "island"),
                    kwargs=dict(name=name, schedule=schedule, every=1.0,
                                deadline=deadline, log=lambda *a, **k: None),
                    daemon=True)
                thread.start()
                threads.append(thread)

            record = run_game.play(table, invite, episode_seconds=cell.seconds,
                                   ack_seconds=cell.ack_seconds, out=tmp)
            for thread in threads:
                thread.join(timeout=10)

            if record is None:
                raise RuntimeError("the game produced no record")

            result = tmp / "g1.json"
            result.write_text(json.dumps(record))
            added, _ = scores.ingest(result, ledger=tmp / "ledger.jsonl",
                                     players=record["players"])
            if not added:
                raise RuntimeError("the ledger took no row for this game")

            row = added[0]
            if row.get("status") == "unscored":
                raise RuntimeError(f"unscored: {row.get('why')}")

            out = endpoints_from(row, cell.episodes)
            out["seed"] = table.seed
            out["draw"] = table.draw
            out["settled"] = record["rounds"][0].get("settled")
            log(f"    seed {table.seed}  "
                + "  ".join(f"{k}={out[k]:.3f}" for k in ENDPOINTS
                            if out.get(k) is not None))
            return out
    finally:
        for server in servers:
            server.close()


@dataclass(frozen=True)
class Job:
    """One game to play: which replicate it belongs to, and on what."""

    replicate: int
    seed: int
    cell: Cell
    npc_seed: int


def run_job(job: Job) -> dict:
    """Play one game and return its endpoints, tagged with its replicate.

    Module level and picklable on purpose: this is what crosses into a worker
    process. Its own temporary directory, its own hub, its own port -- a game
    shares nothing with the game beside it except the machine.
    """
    with tempfile.TemporaryDirectory() as raw:
        out = play_one(job.seed, job.cell, npc_seed=job.npc_seed,
                       tmp=Path(raw), log=lambda *a, **k: None)
    out["replicate"] = job.replicate
    return out


def plan(replicates: int, seeds: list[int], cell: Cell, *,
         vary_npc_seed: bool) -> list[Job]:
    """Every game this run will play, **seed-major**.

    The order is part of the measurement rather than a detail of the loop. With
    `--workers` equal to the replicate count, seed-major puts all replicates of
    one seed in flight together, so they contend for the machine identically --
    which is the paired shape `CLAUDE.md`'s Process section asks for, applied to
    the one thing concurrency can vary here. Replicate-major would run each
    replicate under its own load profile and then compare them.
    """
    return [Job(replicate=r, seed=seed, cell=cell,
                npc_seed=1000 + seed + (10_000 * r if vary_npc_seed else 0))
            for seed in seeds for r in range(replicates)]


def play_all(jobs: list[Job], *, workers: int, run=None, pool=None,
             log=print) -> tuple[list[dict], list[dict]]:
    """Play every job, `workers` in flight, and return (results, failures).

    Results are keyed back to their job rather than kept in completion order,
    so **what this reports does not depend on which game finished first.** A
    summary that changed with the scheduler would be the `overhead` render
    check's disease -- a verdict riding on something the check does not control.

    `workers=1` is a plain in-process loop and not a pool of one, because that
    is the path run 001 measured and it must stay the same path.
    """
    # Looked up here rather than bound as a default, so a test can replace
    # `run_job` on the module. The pool path pickles the callable by reference
    # and a worker imports the real one, which is why the tests that stand in
    # for a game use `workers=1`.
    run = run or run_job
    results: list[dict] = []
    failures: list[dict] = []

    def failed(job: Job, exc: BaseException) -> None:
        # Classified as harness, counted, and never dropped from a
        # denominator -- `CLAUDE.md`, "Process".
        log(f"    replicate {job.replicate + 1} seed {job.seed}  "
            f"HARNESS FAILURE: {exc}")
        failures.append({"replicate": job.replicate, "seed": job.seed,
                         "error": str(exc)})

    if workers <= 1:
        for job in jobs:
            try:
                results.append(run(job))
                log(f"    replicate {job.replicate + 1} seed {job.seed}  done")
            except Exception as exc:                  # noqa: BLE001
                failed(job, exc)
        return results, failures

    factory = pool or concurrent.futures.ProcessPoolExecutor
    with factory(max_workers=workers) as executor:
        futures = {executor.submit(run, job): job for job in jobs}
        for done, future in enumerate(
                concurrent.futures.as_completed(futures), start=1):
            job = futures[future]
            try:
                results.append(future.result())
                log(f"    [{done}/{len(jobs)}] replicate {job.replicate + 1} "
                    f"seed {job.seed}  "
                    + "  ".join(f"{k}={results[-1][k]:.3f}" for k in ENDPOINTS
                                if results[-1].get(k) is not None))
            except Exception as exc:                  # noqa: BLE001
                failed(job, exc)
    return results, failures


def by_replicate(results: list[dict], replicates: int) -> list[list[dict]]:
    """Group finished games back into replicates, each sorted by seed."""
    out: list[list[dict]] = [[] for _ in range(replicates)]
    for game in results:
        out[game["replicate"]].append(game)
    return [sorted(games, key=lambda g: g["seed"]) for games in out]


#: A bounded share sitting on 0.0 or 1.0 in every game is not a precise
#: measurement, it is a pinned one -- and it reports sd 0.0000, which reads as
#: the most precise instrument this lab has ever had. Found by running this at
#: `--seconds 15`, where no NPC completes a round trip: every game settled
#: nothing, every endpoint pinned, and the summary licensed a threshold of
#: zero. `PREFLIGHT.md` gate 3 already says a metric pinned at floor or ceiling
#: returns a null that cannot be told apart from a real one; this is that check,
#: applied to the gate that produces the thresholds.
BOUNDED = {"zero_episode_share", "above_autarky_share"}


def pinned(replicates: list[list[dict]]) -> list[str]:
    """The bounded endpoints that never left a bound. Empty is what we want."""
    out = []
    for endpoint in BOUNDED:
        values = [g[endpoint] for games in replicates for g in games
                  if g.get(endpoint) is not None]
        if values and all(v <= 1e-12 or v >= 1.0 - 1e-12 for v in values):
            out.append(endpoint)
    return sorted(out)


def identical(replicates: list[list[dict]]) -> bool:
    """True when every replicate returned exactly the same numbers.

    Then the reported sd is 0 because nothing varied, not because the
    instrument is precise -- the same trap as `pinned`, arriving by a different
    road. NPC seats are deterministic, so this is the *expected* result with
    `--vary-npc-seed` off, and it is still worth saying out loud every time:
    a run that reports 0.0000 and does not explain why is a run somebody will
    quote as a threshold.
    """
    if len(replicates) < 2:
        return False
    shape = [tuple(sorted((g["seed"], g.get(e)) for g in games)
                   for e in ENDPOINTS) for games in replicates]
    return len(set(map(str, shape))) == 1


def dead(replicates: list[list[dict]]) -> int:
    """Games in which the manager settled nothing at all.

    Not a harness failure -- a seat that says nothing has said nothing and the
    bell rings anyway -- but a cell where *every* game is dead is measuring the
    clock, not the instrument. Counted and reported rather than dropped.
    """
    return sum(1 for games in replicates for g in games
               if not g.get("settled"))


def between_replicate_sd(replicates: list[list[dict]]) -> dict[str, dict]:
    """Per endpoint: the sd of the replicate means, with its denominator.

    The replicate mean is the unit, matching how
    `do-they-take-a-handed-over-answer` reported its own 0.229 -- a per-round
    sd and a per-run sd are different numbers and conflating them is how a
    threshold ends up chosen against the wrong one. Both are reported.
    """
    out: dict[str, dict] = {}
    for endpoint in ENDPOINTS:
        per_replicate = []
        every_game = []
        for games in replicates:
            values = [g[endpoint] for g in games if g.get(endpoint) is not None]
            every_game.extend(values)
            if values:
                per_replicate.append(statistics.fmean(values))
        out[endpoint] = {
            "replicate_means": [round(v, 6) for v in per_replicate],
            "between_replicate_sd": (round(statistics.stdev(per_replicate), 6)
                                     if len(per_replicate) > 1 else None),
            "replicates": len(per_replicate),
            "games": len(every_game),
            "per_game_sd": (round(statistics.stdev(every_game), 6)
                            if len(every_game) > 1 else None),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--replicates", type=int, default=4,
                    help="how many times to play the identical cell")
    ap.add_argument("--games", type=int, default=6,
                    help="islands per replicate; the same seeds every time")
    ap.add_argument("--traders", type=int, default=4)
    ap.add_argument("--goods", type=int, default=5)
    ap.add_argument("--episodes", type=int, default=4)
    ap.add_argument("--seconds", type=int, default=60,
                    help="episode length; part of the level, so a smoke value "
                         "measures a different cell than the run will")
    ap.add_argument("--vary-npc-seed", action="store_true",
                    help="draw a fresh policy seed per replicate, adding the "
                         "policy-draw component while holding the island "
                         "fixed. Still not agent variance.")
    ap.add_argument("--seed0", type=int, default=1,
                    help="the first island seed; games use seed0..seed0+games-1")
    ap.add_argument("--workers", type=int, default=1,
                    help="games in flight at once. A game is mostly a wall "
                         "clock, so this is not CPU-bound; 1 is the serial "
                         "path run 001 measured. See `plan()` for why the job "
                         "order is seed-major.")
    ap.add_argument("--json", type=Path, help="where to write the record")
    args = ap.parse_args(argv)

    cell = Cell(traders=args.traders, goods=args.goods,
                episodes=args.episodes, seconds=args.seconds)
    seeds = [args.seed0 + i for i in range(args.games)]

    print(f"{cell.open_line()}   {args.replicates} replicates x {args.games} games"
          f"   workers={args.workers}")
    print("nothing is varied between replicates; this is not a treatment\n")

    jobs = plan(args.replicates, seeds, cell,
                vary_npc_seed=args.vary_npc_seed)
    results, failures = play_all(jobs, workers=args.workers)
    replicates = by_replicate(results, args.replicates)

    played = sum(len(g) for g in replicates)
    attempted = args.replicates * args.games
    summary = between_replicate_sd(replicates)
    dead_games = dead(replicates)
    pinned_endpoints = pinned(replicates)
    all_identical = identical(replicates)

    print(f"\nattempted {attempted}, played {played}, harness failures "
          f"{len(failures)}, games that settled nothing {dead_games}")

    # An "identical" cell that drew different islands would report seed
    # variance as instrument movement. Checked rather than assumed.
    #
    # `same_seeds`, not `identical`: this was called `identical` and so shadowed
    # the module function of that name, which made `main()` raise
    # UnboundLocalError on the line that calls it -- every time, from the moment
    # run 001 added the guard. `tests/test_noise.py` tested `identical()` and
    # nothing ran `main()`, so a guard added *because* a run had misled somebody
    # had itself never executed. `CLAUDE.md`: a check nobody has seen fail is a
    # check nobody has seen work.
    played_seeds = [sorted(g["seed"] for g in games) for games in replicates
                    if len(games) == args.games]
    same_seeds = len(set(map(tuple, played_seeds))) <= 1
    print(f"every complete replicate played the same seeds: {same_seeds}")

    print(f"\n{'endpoint':<22} {'between-replicate sd':>21} {'per-game sd':>12} "
          f"{'n':>4}")
    for endpoint in ENDPOINTS:
        s = summary[endpoint]
        between = ("     -" if s["between_replicate_sd"] is None
                   else f"{s['between_replicate_sd']:.4f}")
        per_game = ("   -" if s["per_game_sd"] is None
                    else f"{s['per_game_sd']:.4f}")
        print(f"{endpoint:<22} {between:>21} {per_game:>12} {s['games']:>4}")

    print("\nThese numbers are the input to this experiment's thresholds and "
          "are not\nthemselves a result. NPC seats are not models: a model "
          "cell moves at\nleast this much.")

    if all_identical:
        print("\nEVERY REPLICATE RETURNED THE SAME NUMBERS.")
        print("The sd above is 0 because nothing varied, not because the "
              "instrument is\nprecise. NPC policies are deterministic given "
              "their seed, so this is the\nexpected result with --vary-npc-seed "
              "off, and what it measures is the\nharness floor: how much the "
              "manager, clock and economy move on their own.\nThe agent "
              "sampling variance that a threshold has to clear is not in this "
              "number\nand cannot be got from NPCs.")

    if pinned_endpoints:
        print("\nPINNED, AND THEREFORE UNUSABLE: "
              + ", ".join(pinned_endpoints))
        print("Every game left these endpoints on a bound, so the sd above is "
              "0 because\nthe instrument never moved -- not because it is "
              "precise. A threshold taken\nfrom this run would be a threshold "
              "of zero. Do not spend against this.")
        # Two different faults report the same 0.0000, and they have different
        # remedies. Telling them apart needs `dead()`, which this run already
        # counted, so the runner says which rather than leaving the reader to
        # guess -- the verdict is the same either way and only the diagnosis
        # changes. Added in run 002, where an NPC cell settled every game and
        # still pinned `above_autarky_share` at zero, and the message as
        # written told the reader to lengthen an episode that was already long
        # enough.
        if dead_games:
            print(f"\n{dead_games} of {played} games settled nothing. That is "
                  f"the clock:\nlengthen the episode or the ack window until "
                  f"games settle, and measure again.")
        else:
            print(f"\nEvery one of {played} games settled. So this is not the "
                  f"clock -- it is the\nseat population: these seats never "
                  f"reach the other side of this bound.\nA longer episode "
                  f"will not move it, and this endpoint cannot be calibrated "
                  f"with\nthese seats at all. Which seats are on the table is "
                  f"part of the cell.")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "cell": {"traders": cell.traders, "goods": cell.goods,
                     "episodes": cell.episodes, "seconds": cell.seconds,
                     "mix": cell.mix},
            "seeds": seeds,
            "attempted": attempted,
            "played": played,
            "harness_failures": failures,
            "workers": args.workers,
            "seeds_identical_across_replicates": same_seeds,
            "games_that_settled_nothing": dead_games,
            "pinned_endpoints": pinned_endpoints,
            "every_replicate_identical": all_identical,
            "npc_seed_varied": args.vary_npc_seed,
            "replicates": replicates,
            "summary": summary,
        }, indent=2))
        print(f"\nwrote {args.json}")

    # A pinned run is a failed gate, not a tight one. Exiting 0 here is how a
    # threshold of zero gets written down.
    if not played or pinned_endpoints:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
