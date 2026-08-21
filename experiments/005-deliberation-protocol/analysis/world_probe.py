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
    floors, ceilings, gaps, widths = [], [], [], []
    for seed in seeds:
        island = draw_island(n_agents, n_goods, seed=seed)
        _, auto_utils = autarky(island)
        wal = walras(island)
        lo = efficiency(island, list(auto_utils))
        hi = efficiency(island, list(wal.utilities))
        floors.append(lo.lower)
        ceilings.append(hi.lower)
        gaps.append(hi.lower - lo.lower)
        widths.append(max(lo.upper - lo.lower, hi.upper - hi.lower))
    return {"floor": statistics.median(floors),
            "ceiling": statistics.median(ceilings),
            "gap": statistics.median(gaps),
            "gap_min": min(gaps), "gap_max": max(gaps),
            "width": max(widths)}


def coverage_pressure(n_agents: int, n_goods: int) -> float:
    """Labour per good, the structural source of the coverage coupling.

    Below 1 the population cannot cover every good at full intensity and who
    makes what has to be decided between agents; well above 1 every agent can
    cover everything alone and the coupling weakens toward nothing.
    """
    return n_agents / n_goods


def main(sizes: list[int], n_goods: int = 4, islands: int = 24) -> None:
    seeds = range(1, islands + 1)
    print(f"{n_goods} goods, {islands} islands per row. Benchmarks are "
          f"economy.efficiency\nlower bounds -- the same scale as the primary "
          f"metric W.\n")
    print(f"{'agents':>6s} {'labour/good':>11s} {'autarky':>8s} {'exchange':>9s} "
          f"{'gap':>6s} {'gap range':>14s} {'max bracket':>12s}")
    for n in sizes:
        if n < 2:
            print(f"{n:>6d}   -- refused: an exchange economy needs at least "
                  f"two agents")
            continue
        s = spread(n, n_goods, seeds)
        print(f"{n:>6d} {coverage_pressure(n, n_goods):>11.2f} "
              f"{s['floor']:>8.3f} {s['ceiling']:>9.3f} {s['gap']:>6.3f} "
              f"{s['gap_min']:>6.3f}-{s['gap_max']:<7.3f} {s['width']:>12.4f}")
    print("\ngap = exchange ceiling - autarky floor, both as efficiency lower "
          "bounds.\nIt is the whole prize on the table for dealing with anyone "
          "at all, and\ntherefore the ceiling on any treatment effect. A "
          "population size whose gap\nis near zero cannot show one however "
          "good the treatment is.\n\nmax bracket is the widest sandwich "
          "(upper - lower) seen in the row: the\nhonest error bar on every "
          "number beside it.")


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]] or [2, 4, 8, 12]
    main(args)
