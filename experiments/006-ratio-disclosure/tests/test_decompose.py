"""Presence and exchange: does the split call the obvious cases right?"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from analysis.decompose import decompose  # noqa: E402
from barter.economy import autarky, draw_island  # noqa: E402


def _round(seed, episodes):
    return {"seed": seed, "episode_log": episodes}


def test_a_silent_round_is_all_absence_and_no_exchange():
    r = _round(1, [{"produced": [], "utilities": {}} for _ in range(10)])
    d = decompose(r)
    assert d["presence"] == 0.0
    assert d["absent"] == 40
    assert d["exchange_mean"] == 0.0
    assert d["acted"] == 0


def test_everyone_at_their_own_optimum_scores_one():
    island = draw_island(4, 4, seed=1)
    _, optima = autarky(island)
    names = ("T1", "T2", "T3", "T4")
    ep = {"produced": list(names),
          "utilities": {n: optima[i] for i, n in enumerate(names)}}
    d = decompose(_round(1, [ep]))
    assert d["presence"] == 1.0
    assert abs(d["exchange_mean"] - 1.0) < 1e-9
    assert d["above_autarky"] == 0


def test_gains_from_trade_read_above_one():
    island = draw_island(4, 4, seed=1)
    _, optima = autarky(island)
    names = ("T1", "T2", "T3", "T4")
    ep = {"produced": list(names),
          "utilities": {n: optima[i] * 1.5 for i, n in enumerate(names)}}
    d = decompose(_round(1, [ep]))
    assert abs(d["exchange_mean"] - 1.5) < 1e-9
    assert d["above_autarky"] == 4


def test_absence_does_not_dilute_the_exchange_average():
    """A trader that did not act is counted in presence, not in exchange."""
    island = draw_island(4, 4, seed=1)
    _, optima = autarky(island)
    ep = {"produced": ["T1"], "utilities": {"T1": optima[0]}}
    d = decompose(_round(1, [ep]))
    assert d["acted"] == 1
    assert abs(d["exchange_mean"] - 1.0) < 1e-9
    assert d["absent"] == 3
