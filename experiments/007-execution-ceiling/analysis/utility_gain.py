"""How much utility did the group actually make, and who gained by being in it?

Everything scored so far answers *was it effective* -- `eff_round` puts the
utility vector against the Walrasian frontier, and captured gain puts it
between autarky and the plan. Both are ratios to a ceiling, so both are blind
to the question a coordination benchmark should also answer: **how much
utility exists at the end, and is any individual better off than working
alone?**

Two readings, both against the same denominator -- `autarky`, the closed-form
best an agent can do with nobody to trade with:

- **gain** = `u_i / u_i^autarky`, per agent per episode. Above 1.0 means this
  agent is better off in company than alone. This is the individual-rationality
  reading: a group can be far from the frontier and still be worth joining.
- **total** = `sum_i u_i / sum_i u_i^autarky`, per episode. Utility is not
  comparable across agents in general, but the sum against the same-units sum
  of solo optima says whether the island *produced more than the sum of its
  hermits*. This is the one that can be high while efficiency is low.

The geometric mean over non-zero agents is reported next to the arithmetic
mean because a ruined agent (zero utility) sends the geometric mean to zero
and the arithmetic mean merely down -- the two together say whether a cell is
lifted by everyone or by a couple of winners carrying corpses.

Usage: python analysis/utility_gain.py results/001-ceiling/v3.json [...]
       python analysis/utility_gain.py --paired results/001-ceiling/v3.json
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island  # noqa: E402


def solo_optima(seed: int, agents: int, goods: int) -> list[float]:
    """Each agent's utility at its own closed-form solo optimum."""
    _, optima = autarky(draw_island(agents, goods, seed=seed))
    return list(optima)


def round_rows(rnd: dict, agents: int, goods: int) -> tuple[list[float], list[float]]:
    """(per-agent-episode gains, per-episode totals) for one round.

    A round that failed carries no episode log and contributes nothing but is
    still visible to the caller as an empty pair -- it must stay in the
    denominator of "rounds read", never be dropped silently.
    """
    if rnd.get("failed") or not rnd.get("episode_log"):
        return [], []
    optima = solo_optima(rnd["seed"], agents, goods)
    names = [f"T{i + 1}" for i in range(agents)]
    gains: list[float] = []
    totals: list[float] = []
    for ep in rnd["episode_log"]:
        us = ep.get("utilities", {})
        for i, name in enumerate(names):
            if optima[i]:
                gains.append(us.get(name, 0.0) / optima[i])
        got = sum(us.get(n, 0.0) for n in names)
        if sum(optima):
            totals.append(got / sum(optima))
    return gains, totals


def summarise(label: str, gains: list[float], totals: list[float]) -> str:
    if not gains:
        return f"{label:24} no settled episodes"
    live = [g for g in gains if g > 0]
    geo = math.exp(statistics.fmean(math.log(g) for g in live)) if live else 0.0
    above = sum(1 for g in gains if g > 1.0) / len(gains)
    ruined = sum(1 for g in gains if g == 0) / len(gains)
    return (f"{label:24} n={len(gains):4}  gain mean {statistics.fmean(gains):.2f} "
            f"median {statistics.median(gains):.2f}  geo(live) {geo:.2f}  "
            f"above-alone {above:.0%}  ruined {ruined:.0%}  "
            f"total {statistics.fmean(totals):.2f}")


def paired(path: str) -> None:
    """Per-seed total welfare for every arm in one run, paired on the island.

    Only meaningful for a run whose arms share seeds -- the seed *is* the
    island, so pairing on it removes the draw from the comparison. A seed an
    arm failed on is printed as a gap rather than dropped: the denominator is
    seeds attempted, always.
    """
    doc = json.load(open(path))
    agents, goods = doc.get("agents", 4), doc.get("goods", 4)
    grid: dict[int, dict[str, float]] = {}
    for rnd in doc["rounds"]:
        _, totals = round_rows(rnd, agents, goods)
        if totals:
            grid.setdefault(rnd["seed"], {})[rnd["arm"]] = statistics.fmean(totals)
    arms = sorted({a for row in grid.values() for a in row})
    print("seed  " + "  ".join(f"{a:>10}" for a in arms))
    for seed in sorted(grid):
        cells = "  ".join(f"{grid[seed][a]:>10.2f}" if a in grid[seed] else f"{'--':>10}"
                          for a in arms)
        print(f"{seed:4}  {cells}")
    print(f"\nseeds {len(grid)}")
    for a in arms:
        vals = [grid[s][a] for s in grid if a in grid[s]]
        print(f"  {a:12} above 1.0 on {sum(1 for v in vals if v > 1)}/{len(vals)} seeds")
    if len(arms) == 2:
        both = [s for s in grid if all(a in grid[s] for a in arms)]
        diffs = [grid[s][arms[1]] - grid[s][arms[0]] for s in both]
        if len(diffs) > 1:
            print(f"  {arms[1]} - {arms[0]}: n={len(diffs)} "
                  f"mean {statistics.fmean(diffs):+.3f} sd {statistics.stdev(diffs):.3f} "
                  f"wins {sum(1 for d in diffs if d > 0)}/{len(diffs)}")


def main(paths: list[str]) -> None:
    for path in paths:
        doc = json.load(open(path))
        agents, goods = doc.get("agents", 4), doc.get("goods", 4)
        cells: dict[str, tuple[list[float], list[float]]] = {}
        read = failed = 0
        for rnd in doc["rounds"]:
            read += 1
            if rnd.get("failed"):
                failed += 1
            g, t = round_rows(rnd, agents, goods)
            have = cells.setdefault(rnd["arm"], ([], []))
            have[0].extend(g)
            have[1].extend(t)
        print(f"\n{Path(path).parent.name}  rounds {read} ({failed} failed)")
        for arm in sorted(cells):
            print("  " + summarise(arm, *cells[arm]))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--paired":
        for path in args[1:]:
            paired(path)
    else:
        main(args or ["results/001-ceiling/v3.json"])
