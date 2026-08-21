"""005 — the four cells, with models.

    baseline      placebo,  no hint
    content only  placebo,  hint
    method only   protocol, no hint     <- the cell the experiment exists for
    both          protocol, hint

Every cell sees the same seeds, and a seed fixes the truth, the private
signals, the observation schedule and the hint. The four cells are therefore
paired world by world, which is what makes twelve worlds worth running at all.

    python agent_experiment.py --worlds 12 --rounds 5 --json ../results/agents.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agents.episode import (COORDINATED, HARNESS_FAILURE, TAU, TAU_CURVE,
                            run_episode)
from agents.market import N_AGENTS, N_GOODS, SIGMA, WIDTH, draw_world
from agents.prompt import read_stimulus
from agents.runner import MODEL

CELLS = {
    "baseline":     ("placebo",  False),
    "content-only": ("placebo",  True),
    "method-only":  ("protocol", False),
    "both":         ("protocol", True),
}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", type=int, default=12)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--seed0", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=2,
                    help="episodes in flight; each uses 8 agent workers")
    ap.add_argument("--cwd", default="/tmp/005-sandbox")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    Path(args.cwd).mkdir(parents=True, exist_ok=True)
    stimuli = {k: read_stimulus(k) for k in ("protocol", "placebo")}
    seeds = list(range(args.seed0, args.seed0 + args.worlds))
    worlds = {s: draw_world(s, args.rounds) for s in seeds}

    jobs = [(cell, s) for cell in CELLS for s in seeds]
    print(f"model {MODEL}  cells {len(CELLS)}  worlds {args.worlds}  "
          f"rounds {args.rounds}  = {len(jobs) * N_AGENTS * (args.rounds + 1)} calls",
          flush=True)

    started = time.perf_counter()
    done = [0]

    def one(job):
        cell, seed = job
        kind, use_hint = CELLS[cell]
        ep = run_episode(worlds[seed], cell=cell, stimulus=stimuli[kind],
                         use_hint=use_hint, rounds=args.rounds, cwd=args.cwd)
        done[0] += 1
        print(f"  [{done[0]:3d}/{len(jobs)}] {cell:12s} seed {seed:3d}  "
              f"{ep.outcome:17s} minD "
              f"{'--' if ep.min_dispersion is None else format(ep.min_dispersion, '.3f')}  "
              f"{time.perf_counter() - started:6.0f}s"
              f"{'  ' + ep.note if ep.note else ''}", flush=True)
        return ep

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        episodes = list(pool.map(one, jobs))

    summary = []
    for cell in CELLS:
        rows = [e for e in episodes if e.cell == cell]
        scored = [e for e in rows if e.outcome != HARNESS_FAILURE]
        coord = [e for e in scored if e.outcome == COORDINATED]
        lo, hi = wilson(len(coord), len(scored))
        mins = sorted(e.min_dispersion for e in scored)
        summary.append({
            "cell": cell,
            "worlds": len(rows),
            "harness_failures": len(rows) - len(scored),
            "scored": len(scored),
            "coordinated": len(coord),
            "rate": len(coord) / len(scored) if scored else None,
            "wilson": [round(lo, 3), round(hi, 3)],
            "median_min_dispersion": mins[len(mins) // 2] if mins else None,
            "median_rounds_to_coordinate":
                sorted(e.coordinated_at for e in coord)[len(coord) // 2]
                if coord else None,
            "median_final_error":
                sorted(e.final_error for e in scored)[len(scored) // 2]
                if scored else None,
            "retries": sum(e.retries for e in rows),
            "curve": {f"{t:g}": sum(
                1 for e in scored if e.coordinated_at_tau.get(f"{t:g}") is not None
            ) / len(scored) if scored else None for t in TAU_CURVE},
        })

    print(f"\n{'cell':13s} {'rate':>16s} {'medMinD':>9s} {'rounds':>7s} "
          f"{'medErr':>8s} {'harness':>8s}")
    for row in summary:
        r = "--" if row["rate"] is None else (
            f"{row['coordinated']}/{row['scored']} "
            f"({row['wilson'][0]:.2f}-{row['wilson'][1]:.2f})")
        med = row["median_min_dispersion"]
        err = row["median_final_error"]
        print(f"{row['cell']:13s} {r:>16s} "
              f"{'--' if med is None else format(med, '.3f'):>9s} "
              f"{str(row['median_rounds_to_coordinate']):>7s} "
              f"{'--' if err is None else format(err, '.3f'):>8s} "
              f"{row['harness_failures']:8d}")

    out = {
        "experiment": "005-agents",
        "model": MODEL,
        "tau": TAU, "tau_curve": list(TAU_CURVE),
        "config": {"n_agents": N_AGENTS, "n_goods": N_GOODS, "sigma": SIGMA,
                   "width": WIDTH, "rounds": args.rounds},
        "worlds_per_cell": args.worlds,
        "seeds": seeds,
        "elapsed_seconds": round(time.perf_counter() - started, 1),
        "summary": summary,
        "worlds": {str(s): worlds[s].to_json() for s in seeds},
        "episodes": [e.to_json() for e in episodes],
    }
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
