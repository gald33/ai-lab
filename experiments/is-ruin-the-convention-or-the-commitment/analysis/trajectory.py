#!/usr/bin/env python3
"""Read a stock-and-flow record and print the comparison.

    python analysis/trajectory.py results/stock_and_flow.json

Two things this prints that the runner's own table does not:

* **The per-period trajectory**, arm by arm. Welfare is the sum down a column
  and convergence is the shape of one, and a single mean hides the second
  completely — an arm that starts badly and fixes itself and an arm that is
  mediocre throughout have the same mean.
* **The paired stock/flow comparison on the same islands.** Both models ran on
  every island under the same seed, so the difference is the model rather than
  the draw, and the islands the stock model scored as ruined are exactly the
  ones worth looking at under flow.
"""

from __future__ import annotations

import json
import math
import statistics
import sys


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def per_period(records: list[dict], arm: str) -> list[dict]:
    """Efficiency-shaped view of each period: how many agents scored zero, and
    the median utility among those that did not."""
    rows = []
    runs = [r for r in records if r["arm"] == arm]
    if not runs:
        return rows
    periods = len(runs[0]["flow"]["trajectory"])
    for k in range(periods):
        alive, zeros, total = [], 0, 0
        for r in runs:
            for u in r["flow"]["trajectory"][k]:
                total += 1
                if u <= 1e-12:
                    zeros += 1
                else:
                    alive.append(u)
        rows.append({
            "period": k,
            "zero_agents": zeros,
            "agents": total,
            "zero_rate": zeros / total if total else 0.0,
            "median_utility": statistics.median(alive) if alive else None,
        })
    return rows


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1]) as fh:
        data = json.load(fh)
    recs, rows = data["records"], data["summary"]
    islands = rows[0]["islands"] if rows else 0

    print("## Paired, same islands, same seeds\n")
    print("| arm | stock ruined | flow permanently ruined | recovered |")
    print("|---|---|---|---|")
    for r in rows:
        slo, shi = wilson(r["stock_ruined"], r["islands"])
        flo, fhi = wilson(r["flow_permanent_ruin"], r["islands"])
        print(f"| {r['arm']} {r['name']} | {r['stock_ruined']}/{r['islands']} "
              f"({slo:.2f}–{shi:.2f}) | {r['flow_permanent_ruin']}/{r['islands']} "
              f"({flo:.2f}–{fhi:.2f}) | {r['recoveries']} |")

    for r in rows:
        arm = r["arm"]
        print(f"\n## {arm} {r['name']} — per period\n")
        print("| period | agents scoring zero | rate | median utility of the rest |")
        print("|---|---|---|---|")
        for row in per_period(recs, arm):
            med = "—" if row["median_utility"] is None else f"{row['median_utility']:.3f}"
            print(f"| {row['period']} | {row['zero_agents']}/{row['agents']} | "
                  f"{row['zero_rate']:.3f} | {med} |")

    # The islands the stock model could not score at all. Under flow they have
    # numbers, and whether those numbers are any good is the finding.
    print("\n## Islands the stock model scored as ruined\n")
    print("| arm | island | flow efficiency | flow permanent ruin | recoveries |")
    print("|---|---|---|---|---|")
    shown = 0
    for r in recs:
        if r["stock_efficiency"] is None:
            fl = r["flow"]
            eff = "—" if fl["efficiency"] is None else f"{fl['efficiency']:.3f}"
            print(f"| {r['arm']} | {r['island']} | {eff} | {fl['always_zero']} | "
                  f"{fl['recoveries']} |")
            shown += 1
            if shown >= 25:
                print("| … | | | | |")
                break
    if shown == 0:
        print("| — | none | | | |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
