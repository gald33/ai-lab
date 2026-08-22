"""The solo-floor measure: does it call the optimum the optimum?"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                      / "002-barter-conventions" / "experiment"))

from analysis.solo_floor import bundle_of, board_captures  # noqa: E402
from barter.economy import autarky, draw_island  # noqa: E402


def test_bundle_reads_absent_goods_as_zero():
    assert bundle_of("{'cloth': 0.5, 'salt': 0.25}") == [0.0, 0.5, 0.0, 0.25]


def _note(name, bundle):
    return {"from": "manager", "body": f"@{name} produced {bundle}; 0.0 labour unspent"}


def test_the_autarky_split_scores_one():
    """An agent that spends labour in proportion to tastes is at the optimum."""
    island = draw_island(4, 4, seed=1)
    shares, _ = autarky(island)
    goods = ("bread", "cloth", "iron", "salt")
    # Six decimals is what the manager writes to the board, so the tolerance
    # below is that rounding and not a looseness in the measure.
    made = {g: round(island.capacity[0][i] * shares[0][i], 6)
            for i, g in enumerate(goods)}
    rows = board_captures([_note("T1", made)], seed=1)
    assert rows[0][0] == "T1"
    assert abs(rows[0][1] - 1.0) < 1e-5


def test_a_corner_bundle_scores_zero():
    """Cobb-Douglas: nothing of one good is nothing at all, untraded."""
    rows = board_captures([_note("T1", {"bread": 1.0})], seed=1)
    assert rows[0][1] == 0.0
