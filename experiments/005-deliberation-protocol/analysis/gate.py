"""The pre-registered pilot gate, P1-P4, evaluated from a run record.

Frozen in PREREGISTRATION-v2.md before the pilot ran. This file only reads the
record and applies them; it does not get to decide what they are.

    python analysis/gate.py results/v2_pilot.json

Harness failures are excluded from every rate and counted separately, and the
denominator is printed beside every number -- the survivorship trap this lab
has now walked into twice.
"""

from __future__ import annotations

import json
import statistics
import sys


def iqr(xs: list[float]) -> float:
    if len(xs) < 4:
        return 0.0
    s = sorted(xs)
    mid = len(s) // 2
    lo = s[:mid]
    hi = s[mid + 1:] if len(s) % 2 else s[mid:]
    return statistics.median(hi) - statistics.median(lo)


def main(path: str) -> int:
    data = json.loads(open(path).read())
    eps = data["episodes"]
    harness = [e for e in eps if e["outcome"] == "harness_failure"]
    scored = [e for e in eps if e["outcome"] != "harness_failure"]

    print(f"{path}\n{data['agents']} agents, {data['goods']} goods, "
          f"{data['periods']} periods, cells {', '.join(data['cells'])}")
    print(f"{len(scored)} scored, {len(harness)} harness failures "
          f"(excluded from every rate below)\n")
    for e in harness:
        print(f"  harness failure seed {e['seed']}: {e['note'][:90]}")
    if not scored:
        print("nothing scored; the gate cannot be evaluated")
        return 1

    w = [e["score"]["W"] for e in scored]
    floors = [e["score"]["autarky_floor"] for e in scored]
    above = [e for e in scored
             if e["score"]["W"] >= 1.05 * e["score"]["autarky_floor"]]
    zeros = sum(e["score"]["zero_agent_periods"] for e in scored)
    agent_periods = sum(e["score"]["agent_periods"] for e in scored)

    print(f"{'seed':>5s} {'W':>7s} {'floor':>7s} {'W/floor':>8s} "
          f"{'zeros':>9s} {'refused':>8s} {'retries':>8s}")
    for e in scored:
        s = e["score"]
        print(f"{e['seed']:>5d} {s['W']:>7.3f} {s['autarky_floor']:>7.3f} "
              f"{s['W'] / s['autarky_floor']:>8.2f} "
              f"{s['zero_agent_periods']:>4d}/{s['agent_periods']:<4d} "
              f"{e['refused']:>8d} "
              f"{e['retries']}+{e.get('transport_retries', 0):<6}")

    med = statistics.median(w)
    print(f"\nmedian W {med:.3f}   median floor {statistics.median(floors):.3f}   "
          f"ceiling 1.000 (first welfare theorem)")

    checks = [
        ("P1 not trivial", med <= 0.85,
         f"median W {med:.3f} <= 0.85"),
        ("P2 not hopeless", len(above) / len(scored) >= 0.40,
         f"{len(above)}/{len(scored)} = {len(above)/len(scored):.0%} of worlds "
         f"reach 1.05x their floor, need >= 40%"),
        ("P3 coordination bites", zeros / agent_periods >= 0.15,
         f"{zeros}/{agent_periods} = {zeros/agent_periods:.0%} agent-periods "
         f"at zero utility, need >= 15%"),
        ("P4 headroom", iqr(w) >= 0.10 and len(scored) >= 12,
         f"IQR(W) {iqr(w):.3f} >= 0.10 over {len(scored)} worlds, need >= 12"),
    ]
    print()
    for name, passed, detail in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {name:24s} {detail}")

    ok = all(p for _, p, _ in checks)
    print(f"\n{'GATE PASSES' if ok else 'GATE FAILS'} — "
          f"{'the paid cells are authorised' if ok else 'do not run the paid cells'}")
    if not ok and med < statistics.median(floors):
        print("\nNote: median W is *below* the autarky floor. That is not a "
              "difficulty\nsetting that needs raising -- it is agents doing "
              "worse than not trading\nat all, and it needs diagnosing before "
              "any treatment is applied on top.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "results/v2_pilot.json"))
