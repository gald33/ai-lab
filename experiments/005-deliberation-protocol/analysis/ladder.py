"""Episodes to first clear, across a threshold ladder.

`eff_round` is a level: how good the accumulated bundle got. It cannot say how
*fast* quality arrived, which is the thing a round of k episodes exists to
show. This is the other axis: fix a ladder of thresholds and, for each, the
episode at which a round's per-episode efficiency first reaches it.

Three things decide whether that number means anything.

**The scale is island-relative.** The autarky floor is a property of the draw --
0.523 on one island here and 0.823 on another -- so a fixed absolute threshold
measures the island as much as the agents. Everything below is on the capture
scale: autarky is 0, the frontier is 1. That makes autarky a rung at exactly 0
for every seed, by construction.

**The exchange rung is per seed and is not a line.** `exchange_ceiling` -- the
best reachable by swapping without producing differently -- lands at 0.186,
0.242, -0.023, 0.333, 0.290 on seeds 1-5. Drawing it as one number would put it
where no island has it. Seed 3's is negative because the two certified
sandwiches overlap (autarky 0.666-0.676, exchange 0.658-0.665): on that island
the rungs are not separable at the solver's precision, and this says so rather
than picking a side.

**The estimator has to keep the rounds that never cleared.** Per round,
time-to-first-clear is non-decreasing in the threshold -- anything clearing x
clears every y < x -- so the curve is monotone by construction, and
`check_monotone` asserts it. The *mean* is not, if it is taken over only the
rounds that cleared: that denominator falls from 38 to 3 across this ladder, so
each step drops the slowest rounds out of the average and the curve reads flat
or improving as performance worsens. Both estimators are reported side by side,
with the denominator on every row, so the selection cannot be read as speed.
"""
from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island, exchange_ceiling  # noqa: E402

GRID = [x / 100 for x in range(-100, 101, 5)]


@dataclass(frozen=True)
class Rung:
    """One threshold, with everything needed to read its time honestly."""

    threshold: float
    n: int                     # every round, always
    cleared: int               # how many ever reached it
    mean_censored: float       # never-cleared counted at k + 1
    mean_cleared_only: float | None   # the selected mean, for contrast

    @property
    def rate(self) -> float:
        return self.cleared / self.n


def capture(eff: float, floor: float) -> float:
    """Rescale so autarky is 0.0 and the frontier is 1.0."""
    return (eff - floor) / (1.0 - floor)


def first_clear(eff_episode: list[float], floor: float, threshold: float) -> int | None:
    """1-based episode of first clear, or None if it never cleared."""
    for i, e in enumerate(eff_episode):
        if capture(e, floor) >= threshold - 1e-12:
            return i + 1
    return None


def exchange_rungs(agents: int, goods: int, seeds: list[int],
                   floors: dict[int, float]) -> dict[int, float]:
    """The exchange ceiling per seed, on the capture scale."""
    return {s: capture(exchange_ceiling(draw_island(agents, goods, seed=s)).lower,
                       floors[s])
            for s in seeds}


def ladder(rounds: list[dict], k: int, grid: list[float] = GRID) -> list[Rung]:
    floors = {r["seed"]: r["score"]["autarky_floor"] for r in rounds}
    out = []
    for t in grid:
        hits = [first_clear(r["score"]["eff_episode"], floors[r["seed"]], t)
                for r in rounds]
        got = [h for h in hits if h is not None]
        out.append(Rung(
            threshold=round(t, 2), n=len(rounds), cleared=len(got),
            # A round that never cleared is not missing data -- it is a round
            # that took longer than the clock allowed. k + 1 is the smallest
            # value consistent with that, and keeps it in the denominator.
            mean_censored=statistics.fmean([h if h else k + 1 for h in hits]),
            mean_cleared_only=statistics.fmean(got) if got else None))
    return out


def check_monotone(rounds: list[dict], grid: list[float] = GRID) -> int:
    """Per round the curve cannot fall. Returns the number of violations."""
    floors = {r["seed"]: r["score"]["autarky_floor"] for r in rounds}
    bad = 0
    for r in rounds:
        previous = 0
        for t in grid:
            hit = first_clear(r["score"]["eff_episode"], floors[r["seed"]], t)
            here = hit if hit is not None else 10**6
            bad += here < previous
            previous = here
    return bad


def main(path: Path) -> None:
    data = json.loads(path.read_text())
    rounds, k = data["rounds"], data["episodes_per_round"]
    floors = {r["seed"]: r["score"]["autarky_floor"] for r in rounds}
    seeds = sorted(floors)

    print(f"{len(rounds)} rounds, {k} episodes each, seeds {seeds}\n")
    ex = exchange_rungs(data["agents"], data["goods"], seeds, floors)
    print("rungs on the capture scale (autarky = 0 for every seed, by construction):")
    for s in seeds:
        note = "  <- below its own autarky floor; the sandwiches overlap" if ex[s] < 0 else ""
        print(f"  seed {s}: autarky {floors[s]:.4f} raw -> 0.000   exchange {ex[s]:+.3f}{note}")
    print("\nThe exchange rung is per seed. One line at their mean would sit "
          "where no island\nhas it, which is why nothing here pools them.\n")

    violations = check_monotone(rounds)
    print(f"per-round monotonicity violations: {violations} "
          f"({'as it must be' if violations == 0 else 'THE CURVE IS BROKEN'})\n")

    print(f"{'thr':>6} {'cleared':>9} {'rate':>7} {'mean ep':>9} {'cleared-only':>13}")
    print("-" * 48)
    rungs = ladder(rounds, k)
    for r in rungs:
        only = f"{r.mean_cleared_only:13.2f}" if r.mean_cleared_only else f"{'--':>13}"
        print(f"{r.threshold:6.2f} {r.cleared:4d}/{r.n:<4d} {r.rate:7.0%} "
              f"{r.mean_censored:9.2f}{only}")

    mono = all(a.mean_censored <= b.mean_censored + 1e-9
               for a, b in zip(rungs, rungs[1:]))
    dips = sum(1 for a, b in zip(rungs, rungs[1:])
               if a.mean_cleared_only and b.mean_cleared_only
               and b.mean_cleared_only < a.mean_cleared_only - 1e-9)
    print(f"\ncensored estimator monotone: {mono}")
    print(f"cleared-only estimator falls at {dips} of {len(rungs) - 1} steps -- "
          f"that is\nthe denominator shrinking, not rounds getting faster.")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "results/screen/v3.json"
    main(Path(arg) if Path(arg).is_absolute() else HERE.parent / arg)
