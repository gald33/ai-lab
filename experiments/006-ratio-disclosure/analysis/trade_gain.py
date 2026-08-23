"""Did exchanging help the trader that did it? Measured without any floor.

The autarky floor answers a participation question — would this agent rather
not have traded — and 005's run 007 showed the floor is a level these agents
reach when alone. It does **not** measure how well they do at the joint
problem: a solo agent has no access to half of it, and a harder problem is not
a failure at an easier one.

This measure sidesteps that. For one trader in one episode, compare the utility
of what it ended up holding with the utility of the bundle it produced itself.
Same agent, same episode, before and after exchanging. Above 1 means trade
helped it; below 1 means trade left it worse off than keeping its own output.

**It understates trade.** A trader-episode whose own production scored zero — a
corner bundle, deliberately worthless without an exchange — has no finite
ratio and is dropped. Those are exactly the cases where a completed trade is
worth most, so they are counted separately rather than ignored.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island, utility  # noqa: E402

GOODS = ("bread", "cloth", "iron", "salt")
PRODUCED = re.compile(r"@(T\d+) produced (\{[^}]*\})")
EPISODE = re.compile(r"episode (\d+) of")
AMOUNT = re.compile(r"'(\w+)': ([0-9.]+)")


def productions(board: list[dict]) -> dict[tuple[int, str], list[float]]:
    """(episode, trader) -> the bundle the manager settled for it."""
    out, episode = {}, 0
    for msg in board:
        if msg.get("from") != "manager":
            continue
        body = str(msg.get("body"))
        if bell := EPISODE.search(body):
            episode = int(bell.group(1))
        if hit := PRODUCED.search(body):
            name, blob = hit.groups()
            got = {g: float(v) for g, v in AMOUNT.findall(blob)}
            out[(episode, name)] = [got.get(g, 0.0) for g in GOODS]
    return out


def gains(record: dict, board: list[dict], agents: int = 4, goods: int = 4):
    """(finite ratios, corner productions, corners rescued into utility)."""
    island = draw_island(agents, goods, seed=record["seed"])
    made = productions(board)
    names = tuple(f"T{i + 1}" for i in range(agents))
    ratios, corners, rescued = [], 0, 0
    for episode in record["episode_log"]:
        for i, name in enumerate(names):
            key = (episode["episode"], name)
            if key not in made:
                continue
            before = utility(island.alpha[i], made[key])
            after = episode["utilities"].get(name, 0.0)
            if before > 0:
                ratios.append(after / before)
            else:
                corners += 1
                rescued += after > 0
    return ratios, corners, rescued


def main(result: Path, boards: Path) -> None:
    data = json.load(result.open())
    by_arm: dict[str, list] = {}
    for record in data["rounds"]:
        if record.get("failed"):
            continue
        path = boards / f'{record["arm"]}-seed{record["seed"]}.json'
        rows = gains(record, json.load(path.open()),
                     agents=data["agents"], goods=data["goods"])
        acc = by_arm.setdefault(record["arm"], [[], 0, 0])
        acc[0] += rows[0]
        acc[1] += rows[1]
        acc[2] += rows[2]
    print("u(after trading) / u(own production), per trader-episode\n")
    for arm, (ratios, corners, rescued) in sorted(by_arm.items()):
        if not ratios:
            continue
        print(f"{arm:16} n={len(ratios):4} mean {statistics.mean(ratios):.2f} "
              f"median {statistics.median(ratios):.2f} "
              f"above 1 {sum(1 for r in ratios if r > 1) / len(ratios):.0%}")
        print(f"{'':16} plus {corners} corner productions worth zero alone, "
              f"{rescued} rescued by trade "
              f"({rescued / corners:.0%})" if corners else "")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
