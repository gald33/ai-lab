"""The paired reading of 005's four cells, as pre-specified in DEVIATIONS.md D2.

Twelve worlds cannot resolve a rate. What twelve *paired* worlds can resolve is
a within-world difference, and `min_r D(r)` is defined on every world including
the ones that never agreed. Every comparison here is world-by-world, exact
binomial sign test, ties dropped and reported. The unit is the world, never the
agent-round -- 004 produced a phantom drift by forgetting that.

    python analysis/paired.py results/agents.json
"""

from __future__ import annotations

import json
import math
import sys
from itertools import combinations


def sign_test(better: int, worse: int) -> float:
    """Two-sided exact binomial p at q=1/2, ties already dropped."""
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def main(path: str) -> None:
    data = json.loads(open(path).read())
    eps = data["episodes"]
    cells = ["baseline", "method-only", "content-only", "both"]
    by = {c: {e["seed"]: e for e in eps if e["cell"] == c} for c in cells}
    seeds = data["seeds"]
    hint_err = {int(s): None for s in seeds}
    for s in seeds:
        w = data["worlds"][str(s)]
        num = math.sqrt(sum((w["hint"][g] - w["truth"][g]) ** 2
                            for g in range(len(w["truth"]))))
        den = math.sqrt(sum(x * x for x in w["truth"]))
        hint_err[s] = num / den

    print(f"model {data['model']}  tau {data['tau']}  "
          f"{data['worlds_per_cell']} worlds x {len(cells)} cells  "
          f"rounds {data['config']['rounds']}\n")

    print("PRIMARY -- coordination rate at tau=0.10 (under-powered by design)")
    print(f"{'cell':13s} {'coordinated':>12s} {'rate':>6s}  95% Wilson")
    for c in cells:
        rows = list(by[c].values())
        k = sum(1 for e in rows if e["outcome"] == "coordinated")
        lo, hi = wilson(k, len(rows))
        print(f"{c:13s} {k:7d}/{len(rows):<4d} {k/len(rows):6.2f}  "
              f"({lo:.2f}-{hi:.2f})")

    print("\nOutcome classification (harness faults are excluded from rates)")
    print(f"{'cell':13s} {'coord':>6s} {'agent_fail':>11s} {'budget':>7s} "
          f"{'harness':>8s} {'retries':>8s}")
    for c in cells:
        rows = list(by[c].values())
        cnt = lambda o: sum(1 for e in rows if e["outcome"] == o)
        print(f"{c:13s} {cnt('coordinated'):6d} {cnt('agent_failure'):11d} "
              f"{cnt('budget_exhausted'):7d} {cnt('harness_failure'):8d} "
              f"{sum(e['retries'] for e in rows):8d}")

    print("\nPRE-SPECIFIED READING -- min dispersion, paired by seed")
    print("lower is better; a tie is exact equality\n")
    print(f"{'comparison':30s} {'better':>7s} {'worse':>6s} {'tie':>4s} "
          f"{'median delta':>13s} {'p':>7s}")
    for a, b in combinations(cells, 2):
        better = worse = tie = 0
        deltas = []
        for s in seeds:
            x, y = by[a][s]["min_dispersion"], by[b][s]["min_dispersion"]
            deltas.append(x - y)
            if x < y:
                better += 1
            elif x > y:
                worse += 1
            else:
                tie += 1
        p = sign_test(better, worse)
        print(f"{a + ' < ' + b:30s} {better:7d} {worse:6d} {tie:4d} "
              f"{median(deltas):13.3f} {p:7.3f}")

    print("\nAGREEMENT IS NOT CORRECTNESS -- final error vs the truth")
    print(f"{'cell':13s} {'median':>8s}   paired vs baseline (lower better)")
    base = by["baseline"]
    for c in cells:
        errs = [by[c][s]["final_error"] for s in seeds]
        line = f"{c:13s} {median(errs):8.3f}"
        if c != "baseline":
            better = sum(1 for s in seeds
                         if by[c][s]["final_error"] < base[s]["final_error"])
            worse = sum(1 for s in seeds
                        if by[c][s]["final_error"] > base[s]["final_error"])
            line += (f"   {better} better / {worse} worse, "
                     f"p = {sign_test(better, worse):.3f}")
        print(line)
    print(f"\nmedian error of the hint itself: {median(list(hint_err.values())):.3f}")
    print("A cell that copies the hint verbatim inherits exactly this error.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/agents.json")
