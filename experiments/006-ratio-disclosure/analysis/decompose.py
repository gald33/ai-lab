"""Split a peopled round's shortfall into showing up and trading well.

Run 007 of the previous experiment established that an agent **alone** reaches
its own autarky optimum: 85 of 104 production acts at it, mean 0.972. So the
floor is a standard these agents meet, and a peopled round that lands below it
is losing the difference in one of exactly two ways:

* **presence** -- trader-episodes in which nothing was produced at all. These
  contribute zero utility and drag the whole round down however well anyone
  else did.
* **exchange** -- for the trader-episodes that *did* act, utility as a fraction
  of that trader's own autarky optimum. Trade should push this **above 1**:
  gains from trade are the entire reason to have anyone else on the island. At
  1 it broke even. Below 1 the exchange destroyed value relative to staying
  home.

Reporting one without the other is how a treatment gets credit for an attrition
swing, which is what happened twice in the previous experiment (its runs 005
and 006).
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island  # noqa: E402


def decompose(record: dict, agents: int = 4, goods: int = 4) -> dict:
    """Presence and exchange, for one round's episode log."""
    island = draw_island(agents, goods, seed=record["seed"])
    _, optima = autarky(island)
    names = tuple(f"T{i + 1}" for i in range(agents))
    absent, ratios = 0, []
    for episode in record["episode_log"]:
        for i, name in enumerate(names):
            if name in episode.get("produced", []):
                ratios.append(episode["utilities"].get(name, 0.0) / optima[i])
            else:
                absent += 1
    played = len(record["episode_log"]) * agents
    return {
        "trader_episodes": played,
        "absent": absent,
        "presence": (played - absent) / played if played else 0.0,
        "exchange_mean": statistics.mean(ratios) if ratios else 0.0,
        "exchange_median": statistics.median(ratios) if ratios else 0.0,
        "above_autarky": sum(1 for r in ratios if r > 1.0),
        "acted": len(ratios),
    }


def main(result: Path) -> None:
    data = json.load(result.open())
    rounds = [r for r in data["rounds"] if not r.get("failed")]
    failed = len(data["rounds"]) - len(rounds)
    by_arm: dict[str, list[dict]] = {}
    for record in rounds:
        d = decompose(record, agents=data["agents"], goods=data["goods"])
        by_arm.setdefault(record["arm"], []).append(d)
        print(f'{record["arm"]:10} seed {record["seed"]}  '
              f'presence {d["presence"]:.2f} ({d["absent"]}/{d["trader_episodes"]} absent)  '
              f'exchange mean {d["exchange_mean"]:.2f} median {d["exchange_median"]:.2f}  '
              f'above autarky {d["above_autarky"]}/{d["acted"]}')
    print()
    for arm, rows in sorted(by_arm.items()):
        print(f'{arm:10} n={len(rows)} rounds  '
              f'presence {statistics.mean(r["presence"] for r in rows):.2f}  '
              f'exchange {statistics.mean(r["exchange_mean"] for r in rows):.2f}  '
              f'above autarky {sum(r["above_autarky"] for r in rows)}/'
              f'{sum(r["acted"] for r in rows)}')
    if failed:
        print(f"\n{failed} round(s) failed and are excluded from the means "
              f"above; they remain in the result file.")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
