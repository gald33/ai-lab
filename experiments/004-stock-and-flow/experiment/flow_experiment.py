#!/usr/bin/env python3
"""004 runner — the same island scored as stock and as flow.

**Cross-experiment import, deliberately.** This experiment is *about* 002's
harness, so it runs 002's code rather than a copy of it. A copy would drift, and
a finding about 002 produced by a fork of 002 is a finding about the fork. The
flow mode itself lives in 002 (`barter.run.run_island_flow`) as a mode beside
the stock one, so 002's published ladder is untouched and reproducible.

    python flow_experiment.py --islands 24 --json ../results/stock_and_flow.json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

_BARTER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "..", "002-barter-conventions", "experiment")
sys.path.insert(0, os.path.abspath(_BARTER))

from barter.economy import autarky, draw_island, efficiency, exchange_ceiling  # noqa: E402
from barter.run import run_island, run_island_flow  # noqa: E402

ARMS = ("A", "B", "C", "D")
NAMES = {"A": "silent", "B": "disclose", "C": "price", "D": "money"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--islands", type=int, default=24)
    p.add_argument("--seed0", type=int, default=1, help="matches 002's sweep")
    p.add_argument("--agents", type=int, default=12)
    p.add_argument("--goods", type=int, default=5)
    p.add_argument("--periods", type=int, default=6)
    # Each flow period is a whole stock run plus consumption, so trading
    # intensity is matched rather than merely similar. At a smaller number the
    # flow arm looks worse for want of trading rounds, which would be a finding
    # about the budget rather than about the model.
    p.add_argument("--rounds", type=int, default=60)
    p.add_argument("--arms", nargs="*", default=list(ARMS))
    p.add_argument("--json", type=str, default=None)
    args = p.parse_args(argv)

    seeds = [args.seed0 + i for i in range(args.islands)]
    islands = [draw_island(args.agents, args.goods, seed=s) for s in seeds]

    brackets = []
    for island in islands:
        brackets.append({
            "autarky": efficiency(island, autarky(island)[1]).lower,
            "ceiling": exchange_ceiling(island).lower,
        })

    records, rows = [], []
    for arm in args.arms:
        stock_eff, flow_eff, first_eff, last_eff = [], [], [], []
        stock_ruined = flow_permanent = 0
        zero_periods = recoveries = 0
        for i, island in enumerate(islands):
            st = run_island(island, arm, seed=seeds[i], trade_rounds=args.rounds)
            fl = run_island_flow(island, arm, seed=seeds[i], periods=args.periods,
                                 rounds_per_period=args.rounds)
            if st.efficiency.ruined:
                stock_ruined += 1
            else:
                stock_eff.append(st.efficiency.lower)
            if fl.always_zero:
                flow_permanent += 1
            if not fl.efficiency.ruined:
                flow_eff.append(fl.efficiency.lower)
            if not fl.first_efficiency.ruined:
                first_eff.append(fl.first_efficiency.lower)
            if not fl.last_efficiency.ruined:
                last_eff.append(fl.last_efficiency.lower)
            zero_periods += fl.zero_periods
            recoveries += fl.recoveries
            records.append({
                "island": seeds[i], "arm": arm,
                "stock_efficiency": (None if st.efficiency.ruined
                                     else st.efficiency.lower),
                "stock_ruined": list(st.efficiency.ruined),
                "flow": fl.to_json(),
            })

        def med(xs):
            return round(statistics.median(xs), 3) if xs else None

        rows.append({
            "arm": arm, "name": NAMES.get(arm, arm), "islands": len(islands),
            "stock_efficiency": med(stock_eff), "stock_scored": len(stock_eff),
            "stock_ruined": stock_ruined,
            "flow_efficiency": med(flow_eff), "flow_scored": len(flow_eff),
            "flow_permanent_ruin": flow_permanent,
            "flow_first": med(first_eff), "flow_last": med(last_eff),
            "zero_periods": zero_periods,
            "zero_period_rate": round(
                zero_periods / (len(islands) * args.agents * args.periods), 4),
            "recoveries": recoveries,
        })

    print(f"autarky floor {statistics.median(b['autarky'] for b in brackets):.3f}, "
          f"exchange ceiling {statistics.median(b['ceiling'] for b in brackets):.3f}, "
          f"{len(islands)} islands, {args.periods} periods x {args.rounds} rounds\n")
    print("| arm | stock eff | stock ruined | flow eff | flow permanent ruin | "
          "flow first | flow last | zero-period rate | recoveries |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        se = "—" if r["stock_efficiency"] is None else r["stock_efficiency"]
        fe = "—" if r["flow_efficiency"] is None else r["flow_efficiency"]
        print(f"| {r['arm']} {r['name']} | {se} ({r['stock_scored']}/{r['islands']}) | "
              f"{r['stock_ruined']}/{r['islands']} | {fe} ({r['flow_scored']}/{r['islands']}) | "
              f"{r['flow_permanent_ruin']}/{r['islands']} | {r['flow_first']} | "
              f"{r['flow_last']} | {r['zero_period_rate']} | {r['recoveries']} |")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"config": vars(args), "brackets": brackets,
                       "summary": rows, "records": records}, fh, indent=1)
        print(f"\nwrote {args.json} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
