"""How close does an agent alone get to the floor we have been scoring against?

`barter.economy.autarky` is a closed-form optimum: spend labour in proportion
to tastes, `s[g] = alpha[g]`. Every "below autarky" line in runs 003-006 is
measured against an agent that solves that perfectly. Whether these agents do
has never been measured, and this reads it off a solo run's board.

**Solo capture** is `u(what the trader produced) / u(the autarky optimum)`, per
production act. It is only interpretable when nobody could have traded: in a
peopled round a corner bundle is a reasonable opening move and scores 0 here
through Cobb-Douglas, not through incompetence.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island, utility  # noqa: E402

GOODS = ("bread", "cloth", "iron", "salt")
PRODUCED = re.compile(r"@(T\d+) produced (\{[^}]*\})")
AMOUNT = re.compile(r"'(\w+)': ([0-9.]+)")


def bundle_of(text: str) -> list[float]:
    """The produced bundle as a vector over GOODS. Absent goods are zero."""
    got = {g: float(v) for g, v in AMOUNT.findall(text)}
    return [got.get(g, 0.0) for g in GOODS]


def capture(alpha: list[float], produced: list[float], optimum: float) -> float:
    """Utility of what was made, as a fraction of the solo optimum."""
    return utility(alpha, produced) / optimum if optimum else 0.0


def board_captures(board: list[dict], seed: int, agents: int = 4,
                   goods: int = 4) -> list[tuple[str, float]]:
    """(trader, solo capture) for every production the manager settled."""
    island = draw_island(agents, goods, seed=seed)
    _, optima = autarky(island)
    out = []
    for msg in board:
        if msg.get("from") != "manager":
            continue
        hit = PRODUCED.search(str(msg.get("body")))
        if not hit:
            continue
        name, blob = hit.groups()
        i = int(name[1:]) - 1
        out.append((name, capture(island.alpha[i], bundle_of(blob), optima[i])))
    return out


def main(boards: Path) -> None:
    import statistics
    pooled: list[float] = []
    for path in sorted(boards.glob("*.json")):
        seed = int(re.search(r"seed(\d+)", path.stem).group(1))
        rows = board_captures(json.load(path.open()), seed)
        vals = [v for _, v in rows]
        pooled += vals
        if vals:
            print(f"{path.stem:28} n={len(vals):3} mean {statistics.mean(vals):.3f} "
                  f"median {statistics.median(vals):.3f} "
                  f"at-optimum {sum(1 for v in vals if v >= 0.99)}/{len(vals)}")
    if pooled:
        print(f"\npooled n={len(pooled)} mean {statistics.mean(pooled):.3f} "
              f"median {statistics.median(pooled):.3f} "
              f"at-optimum {sum(1 for v in pooled if v >= 0.99)}/{len(pooled)}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "results/007-solo/boards"))
