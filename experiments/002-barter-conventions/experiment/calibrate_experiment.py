#!/usr/bin/env python3
"""Tier 3 calibration runner — scripted, free, replicated.

Traces efficiency against a convention's content error, at known adherence,
with everything else held at arm C. No models, no network, no cost.

    python calibrate_experiment.py --islands 12 --json ../results/tier3_calibration.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys

from barter.calibrate import ADHERENCES, DELTAS, announce
from barter.economy import draw_island, exchange_ceiling, efficiency, autarky
from barter.run import run_island


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--islands", type=int, default=12)
    # Matches barter_experiment.sweep, so the calibration runs on the *same*
    # islands as the published Tier 1 ladder and its benchmarks are directly
    # comparable rather than merely similar.
    p.add_argument("--seed0", type=int, default=1)
    p.add_argument("--agents", type=int, default=12)
    p.add_argument("--goods", type=int, default=5)
    p.add_argument("--rounds", type=int, default=60)
    p.add_argument("--deltas", type=float, nargs="*", default=list(DELTAS))
    p.add_argument("--directions", nargs="*", default=["flatten", "sharpen"])
    p.add_argument("--adherences", type=float, nargs="*", default=list(ADHERENCES))
    p.add_argument("--json", type=str, default=None)
    args = p.parse_args(argv)

    seeds = [args.seed0 + i for i in range(args.islands)]
    islands = [draw_island(args.agents, args.goods, seed=s) for s in seeds]

    # Benchmarks come from the island, not from any run, so they are computed
    # once and are the same for every cell in the sweep.
    # `.lower` is the efficiency number throughout 002 — it is the bound
    # witnessed by an actual feasible allocation rather than by a price — and a
    # ruined island carries no efficiency at all rather than a small one.
    brackets = []
    for island in islands:
        floor_util = autarky(island)[1]
        brackets.append({
            "autarky": efficiency(island, floor_util).lower,
            "ceiling": exchange_ceiling(island).lower,
        })

    records, rows = [], []
    for direction in args.directions:
        for delta in args.deltas:
            notes = [announce(island, delta, direction) for island in islands]
            for adherence in args.adherences:
                effs, worsts, ruined = [], [], 0
                for i, island in enumerate(islands):
                    out = run_island(island, "C", seed=seeds[i], trade_rounds=args.rounds,
                                     announced=list(notes[i].price),
                                     adherence=adherence)
                    is_ruined = bool(out.efficiency.ruined)
                    if is_ruined:
                        ruined += 1
                    else:
                        effs.append(out.efficiency.lower)
                    worsts.append(out.worst_ratio)
                    records.append({
                        "island": seeds[i],
                        "delta": delta,
                        "direction": direction,
                        "adherence": adherence,
                        "error": notes[i].error,
                        "efficiency": None if is_ruined else out.efficiency.lower,
                        "bracket": out.efficiency.bracket,
                        "ruined": list(out.efficiency.ruined),
                        "exchange_efficiency": (None if out.exchange_efficiency.ruined
                                                else out.exchange_efficiency.lower),
                        "worst_ratio": out.worst_ratio,
                        "executed": out.executed,
                        "proposed": out.proposed,
                    })
                rows.append({
                    "direction": direction,
                    "delta": delta,
                    "adherence": adherence,
                    "error_median": round(statistics.median(n.error for n in notes), 3),
                    # Median over the islands that survived. A ruined island has
                    # no efficiency to average, and folding a zero in here would
                    # turn the one outcome most worth seeing into a low number.
                    "efficiency_median": (round(statistics.median(effs), 3)
                                          if effs else None),
                    "scored": len(effs),
                    "worst_median": round(statistics.median(worsts), 3),
                    "ruined": ruined,
                    "islands": len(islands),
                })

    print(f"autarky floor {statistics.median(b['autarky'] for b in brackets):.3f}, "
          f"exchange ceiling {statistics.median(b['ceiling'] for b in brackets):.3f} "
          f"(medians over {len(islands)} islands)")
    for direction in args.directions:
        for adherence in args.adherences:
            sel = [r for r in rows
                   if r["direction"] == direction and r["adherence"] == adherence]
            if not sel:
                continue
            print(f"\n## {direction}, adherence {adherence}\n")
            print("| delta | realised error | efficiency (median of survivors) | "
                  "scored | worst agent vs own autarky | ruined |")
            print("|---|---|---|---|---|---|")
            for r in sel:
                eff = "—" if r["efficiency_median"] is None else r["efficiency_median"]
                print(f"| {r['delta']} | {r['error_median']} | {eff} | "
                      f"{r['scored']}/{r['islands']} | {r['worst_median']} | "
                      f"{r['ruined']}/{r['islands']} |")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"config": vars(args), "brackets": brackets,
                       "summary": rows, "records": records}, fh, indent=1)
        print(f"\nwrote {args.json} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
