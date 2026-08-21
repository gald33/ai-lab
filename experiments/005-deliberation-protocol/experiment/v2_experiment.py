"""Run 005 v2: one or more cells over paired seeded rounds.

    python v2_experiment.py --cells bare --rounds 6 --episodes 5 --json out.json

A round is k episodes on one island, with agent memory carried across them
and reset at the round boundary. Every cell sees the same islands under the
same seeds and the same speaking order, so the cells are paired on everything
except their treatment blocks.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island  # noqa: E402
from v2.round import HARNESS_FAILURE, run_round  # noqa: E402
from v2.prompt import CELLS  # noqa: E402
from v2.runner import MODEL  # noqa: E402
from v2.score import score  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", nargs="+", default=["bare"])
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--agents", type=int, default=8)
    ap.add_argument("--goods", type=int, default=4)
    ap.add_argument("--episodes", type=int, default=5)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    for cell in args.cells:
        if cell not in CELLS:
            raise SystemExit(f"unknown cell {cell!r}; have {', '.join(CELLS)}")

    seeds = list(range(1, args.rounds + 1))
    turns_per_round = args.agents * 4 * args.episodes
    print(f"model {MODEL}  cells {len(args.cells)}  rounds {args.rounds}  "
          f"agents {args.agents}  episodes/round {args.episodes}\n"
          f"= {len(args.cells) * args.rounds * turns_per_round} agent-turns\n")

    records = []
    with tempfile.TemporaryDirectory() as sandbox:
        for cell in args.cells:
            for seed in seeds:
                island = draw_island(args.agents, args.goods, seed=seed)
                rd = run_round(island=island, cell=cell, seed=seed,
                               episodes=args.episodes, cwd=sandbox,
                               concurrency=args.concurrency)
                row = rd.to_json()
                if rd.outcome == HARNESS_FAILURE:
                    print(f"  {cell:9s} seed {seed:3d}  HARNESS FAILURE  "
                          f"{rd.note[:70]}")
                else:
                    s = score(island, rd.trajectory)
                    row["score"] = s.to_json()
                    per_ep = " ".join(f"{x:.2f}" for x in s.eff_episode)
                    print(f"  {cell:9s} seed {seed:3d}  eff_round {s.eff_round:.3f}"
                          f"  floor {s.floor:.3f}  gain {s.gain_median:.2f}"
                          f"  per-episode [{per_ep}]  zeros "
                          f"{s.zero_agent_episodes}/{s.agent_episodes}"
                          f"  refused {rd.refused}  {rd.seconds:.0f}s")
                records.append(row)

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"experiment": "005-v2", "model": MODEL, "cells": args.cells,
             "seeds": seeds, "agents": args.agents, "goods": args.goods,
             "episodes_per_round": args.episodes, "rounds": records}, indent=1))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
