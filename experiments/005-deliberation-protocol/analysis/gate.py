"""The pilot gate on the round structure, evaluated from a run record.

P1-P4 are frozen in PREREGISTRATION-v2.md; AMENDMENT-v2.md moves them onto the
round-level metric. This file only reads the record and applies them.

`eff_round` -- the accumulated utility vector against the frontier of the total
-- is the primary. `eff_episode` is reported beside it and is a coverage
measure, not welfare: one agent at zero puts an episode's vector maximally far
from the frontier however well the other seven did.

Harness failures are excluded from every rate and counted separately, and the
denominator is printed beside every number.

    python analysis/gate.py results/v2_pilot_rounds.json
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiment"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island  # noqa: E402
from v2.score import score as rescore  # noqa: E402


def iqr(xs: list[float]) -> float:
    if len(xs) < 4:
        return 0.0
    s = sorted(xs)
    mid = len(s) // 2
    lo, hi = s[:mid], (s[mid + 1:] if len(s) % 2 else s[mid:])
    return statistics.median(hi) - statistics.median(lo)


def trend(xs: list[float]) -> str:
    """Crude within-round direction: last two episodes against the first two."""
    if len(xs) < 4:
        return " "
    early = statistics.mean(xs[:2])
    late = statistics.mean(xs[-2:])
    if late > early + 0.02:
        return "up"
    if late < early - 0.02:
        return "down"
    return "flat"


def main(path: str) -> int:
    data = json.loads(open(path).read())
    rounds = data["rounds"]
    harness = [r for r in rounds if r["outcome"] == "harness_failure"]
    scored = [r for r in rounds if r["outcome"] != "harness_failure"]

    print(f"{path}\n{data['agents']} agents, {data['goods']} goods, "
          f"{data['episodes_per_round']} episodes/round, "
          f"cells {', '.join(data['cells'])}")
    print(f"{len(scored)} scored, {len(harness)} harness failures "
          f"(excluded from every rate below)\n")
    for r in harness:
        print(f"  harness failure seed {r['seed']}: {r['note'][:90]}")
    if not scored:
        print("nothing scored; the gate cannot be evaluated")
        return 1

    for r in scored:
        island = draw_island(data["agents"], data["goods"], seed=r["seed"])
        r["score"] = rescore(island, r["trajectory"]).to_json()

    eff = [r["score"]["eff_round"] for r in scored]
    floors = [r["score"]["autarky_floor"] for r in scored]
    above = [r for r in scored
             if r["score"]["eff_round"] >= 1.05 * r["score"]["autarky_floor"]]
    zeros = sum(r["score"]["zero_agent_episodes"] for r in scored)
    agent_episodes = sum(r["score"]["agent_episodes"] for r in scored)

    print(f"{'seed':>5s} {'eff_round':>10s} {'floor':>7s} {'vs':>5s} | "
          f"{'per-episode eff':<32s} {'trend':>5s} | {'gain':>5s} "
          f"{'worst':>5s} | {'zeros':>8s} {'hist kB':>8s} {'min':>5s}")
    for r in scored:
        s = r["score"]
        per = " ".join(f"{x:.2f}" for x in s["eff_episode"])
        print(f"{r['seed']:>5d} {s['eff_round']:>10.3f} "
              f"{s['autarky_floor']:>7.3f} "
              f"{s['eff_round'] / s['autarky_floor']:>5.2f} | {per:<32s} "
              f"{trend(s['eff_episode']):>5s} | {s['gain_median']:>5.2f} "
              f"{s['gain_worst']:>5.2f} | "
              f"{s['zero_agent_episodes']:>3d}/{s['agent_episodes']:<4d} "
              f"{r.get('history_chars_max', 0) / 1000:>8.1f} "
              f"{r['seconds'] / 60:>5.0f}")

    med = statistics.median(eff)
    print(f"\nmedian eff_round {med:.3f}   median floor "
          f"{statistics.median(floors):.3f}   ceiling 1.000")
    trimmed = [r["seed"] for r in scored if r.get("history_trimmed")]
    print(f"history trimmed in {len(trimmed)}/{len(scored)} rounds"
          + (f" (seeds {trimmed})" if trimmed else ""))

    checks = [
        ("P1 not trivial", med <= 0.85, f"median eff_round {med:.3f} <= 0.85"),
        ("P2 not hopeless", len(above) / len(scored) >= 0.40,
         f"{len(above)}/{len(scored)} = {len(above)/len(scored):.0%} of rounds "
         f"reach 1.05x their floor, need >= 40%"),
        ("P3 coordination bites", zeros / agent_episodes >= 0.15,
         f"{zeros}/{agent_episodes} = {zeros/agent_episodes:.0%} agent-episodes "
         f"at zero utility, need >= 15%"),
        ("P4 headroom", iqr(eff) >= 0.10 and len(scored) >= 12,
         f"IQR {iqr(eff):.3f} >= 0.10 over {len(scored)} rounds, need >= 12"),
    ]
    print()
    for name, passed, detail in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {name:24s} {detail}")

    ok = all(p for _, p, _ in checks)
    print(f"\n{'GATE PASSES' if ok else 'GATE FAILS'} — "
          f"{'the paid cells are authorised' if ok else 'do not run the paid cells'}")
    if not ok and med < statistics.median(floors):
        print("\nNote: median eff_round is *below* the autarky floor, on the "
              "metric that\nsurvives partial ruin. That is agents doing worse "
              "than not trading at all,\nand it is not a difficulty setting "
              "that needs raising.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else "results/v2_pilot_rounds.json"))
