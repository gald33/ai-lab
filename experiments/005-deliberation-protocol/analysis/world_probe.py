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

from barter.economy import autarky, draw_island, planner, walras  # noqa: E402


def spread(n_agents: int, n_goods: int, seeds: range) -> dict:
    """Floor, ceiling and the gap between them, over a set of islands."""
    floors, ceilings, gaps, solo = [], [], [], []
    for seed in seeds:
        island = draw_island(n_agents, n_goods, seed=seed)
        base = planner(island, [1.0 / n_agents] * n_agents)
        _, auto_utils = autarky(island)
        wal = walras(island)
        ref = sum(base.utilities)
        floors.append(sum(auto_utils) / ref)
        ceilings.append(sum(wal.utilities) / ref)
        gaps.append(ceilings[-1] - floors[-1])
        # How well one agent does alone relative to its own best case, which is
        # what makes autarky tempting or hopeless at this population size.
        solo.append(statistics.median(auto_utils))
    return {"floor": statistics.median(floors),
            "ceiling": statistics.median(ceilings),
            "gap": statistics.median(gaps),
            "gap_min": min(gaps), "gap_max": max(gaps),
            "solo": statistics.median(solo)}


def coverage_pressure(n_agents: int, n_goods: int) -> float:
    """Labour per good, the structural source of the coverage coupling.

    Below 1 the population cannot cover every good at full intensity and who
    makes what has to be decided between agents; well above 1 every agent can
    cover everything alone and the coupling weakens toward nothing.
    """
    return n_agents / n_goods


def main(sizes: list[int], n_goods: int = 4, islands: int = 24) -> None:
    seeds = range(1, islands + 1)
    print(f"{n_goods} goods, {islands} islands per row, "
          f"benchmarks as a share of the equal-weight planner point\n")
    print(f"{'agents':>6s} {'labour/good':>11s} {'autarky':>8s} {'exchange':>9s} "
          f"{'gap':>6s} {'gap range':>14s} {'solo util':>10s}")
    for n in sizes:
        if n < 2:
            print(f"{n:>6d}   -- refused: an exchange economy needs at least "
                  f"two agents")
            continue
        s = spread(n, n_goods, seeds)
        print(f"{n:>6d} {coverage_pressure(n, n_goods):>11.2f} "
              f"{s['floor']:>8.3f} {s['ceiling']:>9.3f} {s['gap']:>6.3f} "
              f"{s['gap_min']:>6.3f}-{s['gap_max']:<7.3f} {s['solo']:>10.4f}")
    print("\ngap = exchange ceiling - autarky floor. It is the whole prize on "
          "\nthe table for coordinating at all; a population size whose gap is "
          "\nnear zero cannot show a treatment effect however good the "
          "treatment is.")


if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]] or [2, 4, 8, 12]
    main(args)
