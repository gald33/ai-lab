#!/usr/bin/env python3
"""Tier 1 runner — scripted, free, replicated.

Every rule sees the same pools and the same seeds, in every mode. Run it wide;
it costs nothing.

    python promotion_experiment.py --replications 40 --json results/tier1.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys

from promotion.report import summarise, table
from promotion.rules import RULES, RULE_NAMES
from promotion.run import play
from promotion.world import MODES, draw_pool


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--replications", type=int, default=40,
                   help="pools per (rule, mode, start); each is one seed")
    p.add_argument("--steps", type=int, default=400)
    p.add_argument("--invocations", type=int, default=20,
                   help="invocations per step, split across candidates")
    p.add_argument("--candidates", type=int, default=5)
    p.add_argument("--spread", type=float, default=0.4,
                   help="quality range; a pool with an obvious winner measures nothing")
    p.add_argument("--noise", type=float, default=0.15)
    p.add_argument("--rules", nargs="*", default=list(RULE_NAMES))
    p.add_argument("--modes", nargs="*", default=list(MODES))
    p.add_argument("--starts", nargs="*", default=["worst", "middle", "best"])
    p.add_argument("--json", type=str, default=None, help="write the whole record here")
    args = p.parse_args(argv)

    for name in args.rules:
        if name not in RULES:
            p.error(f"unknown rule {name!r}; expected one of {', '.join(RULE_NAMES)}")
    for name in args.modes:
        if name not in MODES:
            p.error(f"unknown mode {name!r}; expected one of {', '.join(MODES)}")

    # Pools are drawn once per seed and shared by every rule, mode and start, so
    # a difference between rules is never a difference between pools.
    pools = [draw_pool(random.Random(seed), size=args.candidates,
                       spread=args.spread, noise=args.noise)
             for seed in range(args.replications)]

    records, rows = [], []
    for mode in args.modes:
        for start in args.starts:
            for name in args.rules:
                rule = RULES[name]
                group = [play(pools[s], rule, mode, seed=s, start=start,
                              steps=args.steps, invocations=args.invocations)
                         for s in range(args.replications)]
                records.extend(group)
                row = summarise(group)
                row["start"] = start
                rows.append(row)

    for mode in args.modes:
        for start in args.starts:
            sel = [r for r in rows if r["mode"] == mode and r["start"] == start]
            if not sel:
                continue
            print(f"\n## {mode}, starting on the {start} candidate\n")
            print(table(sel))

    if args.json:
        payload = {
            "config": vars(args),
            "pools": [{"quality": list(pl.quality), "noise": pl.noise} for pl in pools],
            "summary": rows,
            "records": [r.to_json() for r in records],
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=1)
        print(f"\nwrote {args.json} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
