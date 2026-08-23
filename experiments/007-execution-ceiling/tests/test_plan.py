"""The plan must be an equilibrium, and both halves of every trade must agree."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island, utility, walras  # noqa: E402

from plan import GOODS, _transfers, hook, plan_for  # noqa: E402

NAMES = ("T1", "T2", "T3", "T4")


def test_every_transfer_has_two_agreeing_sides():
    """T1's 'get x from T2' must be T2's 'give x to T1', or the block lies."""
    for seed in (1, 2, 3):
        island = draw_island(4, 4, seed=seed)
        texts = [plan_for(island, i, NAMES) for i in range(4)]
        for good, giver, taker, qty in _transfers(island, walras(island), NAMES):
            assert f"give {qty} {GOODS[good]} to {NAMES[taker]}" in texts[giver]
            assert f"get {qty} {GOODS[good]} from {NAMES[giver]}" in texts[taker]


def test_transfers_clear_each_good():
    """What is given of a good equals what is taken of it."""
    for seed in (1, 2, 3):
        island = draw_island(4, 4, seed=seed)
        point = walras(island)
        for g in range(4):
            moved = sum(q for good, _, _, q in _transfers(island, point, NAMES)
                        if good == g)
            short = sum(max(0.0, point.allocation[i][g]
                            - island.capacity[i][g] * point.shares[i][g])
                        for i in range(4))
            assert abs(moved - short) < 1e-3


def test_the_plan_beats_autarky_for_everyone():
    """A plan that left someone worse off alone would not be worth following."""
    for seed in (1, 2, 3, 4, 5):
        island = draw_island(4, 4, seed=seed)
        point = walras(island)
        _, floor = autarky(island)
        for i in range(4):
            assert utility(island.alpha[i], point.allocation[i]) > floor[i]


def test_labour_shares_stay_within_budget():
    for seed in (1, 2, 3):
        island = draw_island(4, 4, seed=seed)
        for row in walras(island).shares:
            assert sum(row) <= 1.0 + 1e-6


def test_the_hook_gives_nothing_to_the_control():
    island = draw_island(4, 4, seed=1)
    assert hook("e-bare", "T1", island, 0) == ""
    assert "Your plan" in hook("e-plan", "T1", island, 0)
