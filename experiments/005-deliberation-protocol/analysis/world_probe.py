"""What an island looks like at a given number of agents. Free, no models.

The population size is a design parameter of v2 rather than a constant, and it
moves several things at once: how far apart the autarky floor and the exchange
ceiling sit (how much there is to gain by dealing with anyone at all), how
likely it is that a good goes unproduced, and how much conversation the board
has to carry. This probe reports the first two directly from the economy, so a
population size can be chosen against numbers instead of intuition.

Nothing here runs agents. It measures the *world*: the benchmarks are computed
from the island, and the coverage figure is a property of the production
technology, not of anyone's behaviour.

    python analysis/world_probe.py 2 4 8 12
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island, efficiency, walras  # noqa: E402


def spread(n_agents: int, n_goods: int, seeds: range) -> dict:
    """Floor, ceiling and the gap between them, on the primary metric's scale.

    Both benchmarks are put through ``economy.efficiency`` -- the same
    certified sandwich the primary metric ``W`` uses -- rather than through a
    ratio of utility sums. A sum of Cobb-Douglas utilities is not comparable
    across islands and its natural denominator, the equal-weight planner point,
    is the Nash bargaining solution rather than a utilitarian ceiling, so a
    Walrasian numerator can and does exceed it. ``efficiency`` has neither
    problem: it is a distance to the frontier, in [0, 1], with the width of the
    bracket reported rather than assumed away.
    """
    floors, widths, gaps, ceil_slack = [], [], [], []
    for seed in seeds:
        island = draw_island(n_agents, n_goods, seed=seed)
        _, auto_utils = autarky(island)
        wal = walras(island)
        lo = efficiency(island, list(auto_utils))
        # The Walrasian point is on the frontier by the first welfare theorem,
        # so its efficiency is 1 by construction and is not measured here --
        # it is *checked*. What `efficiency` returns for it is a bracket whose
        # upper bound is 1 and whose lower bound is however far the
        # achievability search got, which at small n is visibly short of it.
        # Reporting that lower bound as "the ceiling" would be reporting solver
        # slack as economics, so the ceiling is 1.0 and the slack is a
        # diagnostic column instead.
        hi = efficiency(island, list(wal.utilities))
        ceil_slack.append(1.0 - hi.lower)
        assert hi.upper >= 1.0 - 1e-9, f"walras point below the frontier: {hi}"
        floors.append(lo.lower)
        widths.append(lo.upper - lo.lower)
        gaps.append(1.0 - lo.lower)
    return {"floor": statistics.median(floors),
            "floor_width": max(widths),
            "gap": statistics.median(gaps),
            "gap_min": min(gaps), "gap_max": max(gaps),
            "slack": max(ceil_slack)}


def coverage_pressure(n_agents: int, n_goods: int) -> float:
    """Labour per good, the structural source of the coverage coupling.

    Below 1 the population cannot cover every good at full intensity and who
    makes what has to be decided between agents; well above 1 every agent can
    cover everything alone and the coupling weakens toward nothing.
    """
    return n_agents / n_goods


def main(sizes: list[int], n_goods: int = 4, islands: int = 24) -> None:
    seeds = range(1, islands + 1)
    print(f"{n_goods} goods, {islands} islands per row. The autarky floor is "
          f"an\neconomy.efficiency lower bound -- the same scale as the "
          f"primary metric W.\n")
    print(f"{'agents':>6s} {'labour/good':>11s} {'autarky':>8s} {'+/-':>7s} "
          f"{'ceiling':>8s} {'gap':>6s} {'gap range':>14s} {'slack':>7s}")
    for n in sizes:
        if n < 2:
            print(f"{n:>6d}   -- refused: an exchange economy needs at least "
                  f"two agents")
            continue
        s = spread(n, n_goods, seeds)
        print(f"{n:>6d} {coverage_pressure(n, n_goods):>11.2f} "
              f"{s['floor']:>8.3f} {s['floor_width']:>7.4f} {1.0:>8.3f} "
              f"{s['gap']:>6.3f} "
              f"{s['gap_min']:>6.3f}-{s['gap_max']:<7.3f} {s['slack']:>7.4f}")
    print("""
ceiling  1.000 in every row, and not an estimate: the competitive equilibrium
         is Pareto-optimal by the first welfare theorem, and the run asserts
         that efficiency's upper bound reaches it on every island.

gap      1 - autarky floor. The whole prize on the table for dealing with
         anyone at all, and therefore the ceiling on any treatment effect. A
         population size whose gap is near zero cannot show one however good
         the treatment is.

range    the smallest and largest per-island gap in the row -- not an error
         bar. It says how much the islands differ from each other, which is
         the variance a paired test has to see through.

+/-      widest autarky-floor bracket (efficiency upper - lower) in the row.
         This one *is* an error bar.

slack    worst shortfall of efficiency's lower bound at the equilibrium, where
         the true value is 1. Pure solver convergence, reported so it is never
         mistaken for an economic result.""")


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]] or [2, 4, 8, 12]
    main(args)
