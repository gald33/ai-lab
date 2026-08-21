"""The pilot gate, P1-P4, on both metrics, evaluated from a run record.

P1-P4 are frozen in PREREGISTRATION-v2.md and AMENDMENT-v2.md. This file only
reads the record and applies them; it does not get to decide what they are.

Both metrics are reported whatever they say. ``W`` is the frozen primary and is
printed first even though the amendment establishes that it is near-binary --
dropping it because it gave an unwelcome answer is the move the freeze exists
to prevent. ``G`` is the declared companion, and the paid cells need the gate to
pass on it.

    python analysis/gate.py results/v2_pilot.json

Harness failures are excluded from every rate and counted separately, and the
denominator is printed beside every number -- the survivorship trap this lab
has now walked into twice.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiment"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island, walras  # noqa: E402
from v2.score import score as rescore  # noqa: E402


def _walras_gain(island) -> float:
    """Median gains over autarky at the competitive equilibrium.

    G has no natural ceiling of 1 the way W does, so P1 needs a reference for
    "trivially good". This is it: what the price mechanism itself achieves on
    this island.
    """
    from barter.economy import gains
    return gains(island, list(walras(island).utilities)).median


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

    # Re-score from the stored trajectories so G is available for records
    # written before the amendment. The islands are a pure function of the
    # recorded seed, agents and goods, so this reproduces rather than reruns.
    for e in scored:
        island = draw_island(data["agents"], data["goods"], seed=e["seed"])
        e["score"] = rescore(island, e["trajectory"]).to_json()
        e["_walras_g"] = _walras_gain(island)

    w = [e["score"]["W"] for e in scored]
    g = [e["score"]["G"] for e in scored]
    floors = [e["score"]["autarky_floor"] for e in scored]
    above = [e for e in scored
             if e["score"]["W"] >= 1.05 * e["score"]["autarky_floor"]]
    zeros = sum(e["score"]["zero_agent_periods"] for e in scored)
    agent_periods = sum(e["score"]["agent_periods"] for e in scored)

    print(f"{'seed':>5s} {'W':>7s} {'floor':>7s} | {'G':>6s} {'worst':>6s} "
          f"{'below':>6s} | {'zeros':>9s} {'refused':>8s} {'retries':>9s}")
    for e in scored:
        s = e["score"]
        print(f"{e['seed']:>5d} {s['W']:>7.3f} {s['autarky_floor']:>7.3f} | "
              f"{s['G']:>6.3f} {s['worst_gain']:>6.3f} "
              f"{s['below_autarky']:>3d}/{s['agent_periods']:<2d} | "
              f"{s['zero_agent_periods']:>4d}/{s['agent_periods']:<4d} "
              f"{e['refused']:>8d} "
              f"{e['retries']}+{e.get('transport_retries', 0):<7}")

    med = statistics.median(w)
    med_g = statistics.median(g)
    ref_g = statistics.median([e["_walras_g"] for e in scored])
    print(f"\nmedian W {med:.3f}   median floor {statistics.median(floors):.3f}"
          f"   ceiling 1.000 (first welfare theorem)")
    print(f"median G {med_g:.3f}   autarky is 1.000 by definition"
          f"   walras reaches {ref_g:.3f}")

    above_g = [x for x in g if x >= 1.05]
    on_w = [
        ("P1 not trivial", med <= 0.85, f"median W {med:.3f} <= 0.85"),
        ("P2 not hopeless", len(above) / len(scored) >= 0.40,
         f"{len(above)}/{len(scored)} = {len(above)/len(scored):.0%} of worlds "
         f"reach 1.05x their floor, need >= 40%"),
        ("P3 coordination bites", zeros / agent_periods >= 0.15,
         f"{zeros}/{agent_periods} = {zeros/agent_periods:.0%} agent-periods "
         f"at zero utility, need >= 15%"),
        ("P4 headroom", iqr(w) >= 0.10 and len(scored) >= 12,
         f"IQR(W) {iqr(w):.3f} >= 0.10 over {len(scored)} worlds, need >= 12"),
    ]
    on_g = [
        ("P1 not trivial", med_g <= 0.85 * ref_g,
         f"median G {med_g:.3f} <= 0.85 x walras {ref_g:.3f} = "
         f"{0.85 * ref_g:.3f}"),
        ("P2 not hopeless", len(above_g) / len(scored) >= 0.40,
         f"{len(above_g)}/{len(scored)} = {len(above_g)/len(scored):.0%} of "
         f"worlds beat autarky by 5%, need >= 40%"),
        ("P3 coordination bites", zeros / agent_periods >= 0.15,
         f"same criterion — it was always about coverage"),
        ("P4 headroom", iqr(g) >= 0.10 and len(scored) >= 12,
         f"IQR(G) {iqr(g):.3f} >= 0.10 over {len(scored)} worlds, need >= 12"),
    ]

    verdicts = {}
    for label, checks in (("W (frozen primary)", on_w), ("G (companion)", on_g)):
        print(f"\n  on {label}")
        for name, passed, detail in checks:
            print(f"    {'PASS' if passed else 'FAIL'}  {name:24s} {detail}")
        verdicts[label] = all(p for _, p, _ in checks)

    ok = verdicts["G (companion)"]
    print(f"\nW: {'passes' if verdicts['W (frozen primary)'] else 'FAILS'}    "
          f"G: {'passes' if ok else 'FAILS'}")
    print(f"{'GATE PASSES' if ok else 'GATE FAILS'} — "
          f"{'the paid cells are authorised' if ok else 'do not run the paid cells'}"
          f"\n(the paid cells require a pass on G; a pass on W alone would be a "
          f"pass on a\nmetric the amendment establishes is near-binary)")
    if not ok and med < statistics.median(floors):
        print("\nNote: median W is *below* the autarky floor. That is not a "
              "difficulty\nsetting that needs raising -- it is agents doing "
              "worse than not trading\nat all, and it needs diagnosing before "
              "any treatment is applied on top.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "results/v2_pilot.json"))
