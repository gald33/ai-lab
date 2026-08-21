"""Run 005 v2: one or more cells over paired seeded worlds.

    python v2_experiment.py --cells bare --worlds 6 --periods 3 --json out.json

Every cell sees the same islands under the same seeds, and the within-stage
speaking order is drawn from the world seed, so the cells are paired on
everything except their treatment blocks.
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
from v2.episode import HARNESS_FAILURE, run_episode  # noqa: E402
from v2.prompt import CELLS  # noqa: E402
from v2.runner import MODEL  # noqa: E402
from v2.score import score  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", nargs="+", default=["bare"])
    ap.add_argument("--worlds", type=int, default=6)
    ap.add_argument("--agents", type=int, default=8)
    ap.add_argument("--goods", type=int, default=4)
    ap.add_argument("--periods", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    for cell in args.cells:
        if cell not in CELLS:
            raise SystemExit(f"unknown cell {cell!r}; have {', '.join(CELLS)}")

    seeds = list(range(1, args.worlds + 1))
    turns_per_world = args.agents * 4 * args.periods
    print(f"model {MODEL}  cells {len(args.cells)}  worlds {args.worlds}  "
          f"agents {args.agents}  periods {args.periods}\n"
          f"= {len(args.cells) * args.worlds * turns_per_world} agent-turns\n")

    records = []
    with tempfile.TemporaryDirectory() as sandbox:
        for cell in args.cells:
            for seed in seeds:
                island = draw_island(args.agents, args.goods, seed=seed)
                ep = run_episode(island=island, cell=cell, seed=seed,
                                 periods=args.periods, cwd=sandbox,
                                 concurrency=args.concurrency)
                row = ep.to_json()
                if ep.outcome == HARNESS_FAILURE:
                    print(f"  {cell:9s} seed {seed:3d}  HARNESS FAILURE  "
                          f"{ep.note[:70]}")
                else:
                    s = score(island, ep.trajectory)
                    row["score"] = s.to_json()
                    print(f"  {cell:9s} seed {seed:3d}  W {s.w:.3f}  "
                          f"floor {s.floor:.3f}  zeros "
                          f"{s.zero_agent_periods}/{s.agent_periods}  "
                          f"refused {ep.refused}  {ep.seconds:.0f}s")
                records.append(row)

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"experiment": "005-v2", "model": MODEL, "cells": args.cells,
             "seeds": seeds, "agents": args.agents, "goods": args.goods,
             "periods": args.periods, "episodes": records}, indent=1))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
