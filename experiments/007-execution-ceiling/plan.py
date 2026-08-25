"""The exact plan, computed per island and written per trader.

`walras` solves the island: the competitive equilibrium is the allocation where
every trader can afford the bundle it wants and every good clears. This turns
one trader's part of that solution into the sentences it will read — what to
produce, what to end up holding, and the net trades that get it there.

**This is a stimulus, not an instruction the system enforces.** It is appended
to the trader's private block in the prompt. The manager settles what a trader
actually writes on the board and refuses what is malformed, exactly as in every
other cell. Nothing here is settled on a trader's behalf, and a trader that
ignores the plan is not corrected. That distinction is the whole reason this is
allowed to exist — see D1.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "002-barter-conventions" / "experiment"))

from barter.economy import Island, autarky, utility, walras  # noqa: E402

GOODS = ("bread", "cloth", "iron", "salt")
#: Four decimals is what the manager echoes when it settles a production, so
#: asking for more precision than that would be asking for a number the board
#: cannot show back.
DP = 4


def _fmt(values, goods=GOODS, *, skip_zero=True):
    parts = [f"{g}={round(v, DP)}" for g, v in zip(goods, values)
             if not (skip_zero and round(v, DP) == 0)]
    return " ".join(parts) or "nothing"


def _transfers(island: Island, point, names: tuple[str, ...]):
    """One bilateral decomposition of the equilibrium's net trades.

    An equilibrium fixes each trader's *net* position in each good, not who
    hands what to whom -- any matching of the longs against the shorts clears
    it. So pick one and give every trader the same one: for each good, walk the
    surpluses against the deficits largest-first. The point is not that this
    matching is canonical; it is that both sides of every transfer read the
    same sentence, which is what the block promises them.
    """
    out = []
    for g in range(len(GOODS)):
        net = [point.allocation[i][g] - island.capacity[i][g] * point.shares[i][g]
               for i in range(island.n_agents)]
        givers = sorted(((-v, i) for i, v in enumerate(net) if v < 0), reverse=True)
        takers = sorted(((v, i) for i, v in enumerate(net) if v > 0), reverse=True)
        gi = ti = 0
        give = list(givers)
        take = list(takers)
        while gi < len(give) and ti < len(take):
            qty = min(give[gi][0], take[ti][0])
            if round(qty, DP) > 0:
                out.append((g, give[gi][1], take[ti][1], round(qty, DP)))
            give[gi] = (give[gi][0] - qty, give[gi][1])
            take[ti] = (take[ti][0] - qty, take[ti][1])
            if give[gi][0] <= 1e-9:
                gi += 1
            if take[ti][0] <= 1e-9:
                ti += 1
    return out


def plan_for(island: Island, index: int, names: tuple[str, ...]) -> str:
    """One trader's part of the equilibrium, as text for its private block."""
    point = walras(island)
    _, floor = autarky(island)
    goods = len(GOODS)
    me = names[index]

    shares = point.shares[index]
    produce = [island.capacity[index][g] * shares[g] for g in range(goods)]
    hold = list(point.allocation[index])
    net = [hold[g] - produce[g] for g in range(goods)]

    transfers = [x for x in _transfers(island, point, names)
                 if index in (x[1], x[2])]
    lines = []
    for good, giver, taker, qty in transfers:
        if index == taker:
            lines.append(f"  - get {qty} {GOODS[good]} from {names[giver]}")
        else:
            lines.append(f"  - give {qty} {GOODS[good]} to {names[taker]}")

    gain = utility(island.alpha[index], hold) / floor[index]
    return (
        f"**Your plan.** Produce with labour shares "
        f"{_fmt(shares, skip_zero=False)} — that is "
        f"{_fmt(produce)} — every episode.\n\n"
        f"End each episode holding {_fmt(hold)}.\n\n"
        f"To get there, {me} needs to:\n" + "\n".join(lines) + "\n\n"
        f"Following this exactly is worth about {gain:.2f}x what you would get "
        f"alone. Prices that support it, per unit: "
        f"{_fmt(point.prices, skip_zero=False)}."
    )


def hook(arm: str, name: str, island: Island, index: int) -> str:
    """`run_v3.PRIVATE_HOOK`: the plan for treated cells, nothing otherwise."""
    if arm != "e-plan":
        return ""
    names = tuple(f"T{i + 1}" for i in range(island.n_agents))
    return plan_for(island, index, names)


if __name__ == "__main__":
    from barter.economy import draw_island
    isl = draw_island(4, 4, seed=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    for i in range(4):
        print(f"--- T{i + 1} " + "-" * 50)
        print(plan_for(isl, i, ("T1", "T2", "T3", "T4")))
