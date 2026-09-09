"""Gates on the rung-0 runner's arithmetic and on its two refusals.

The game-playing half needs a hub and a clock and is exercised by running it;
what is tested here is everything that decides *what number comes out*, because
that number becomes this experiment's thresholds and a wrong one is not
visible downstream -- it just makes every later comparison pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "experiment"))

import noise  # noqa: E402


def game(**over):
    base = {"zero_episode_share": 0.25, "capture": 0.5,
            "above_autarky_share": 0.5, "eff_round": 0.6,
            "seed": 1, "settled": 4}
    return {**base, **over}


# --- the endpoints, off a ledger row ------------------------------------

def test_the_primary_is_a_share_of_trader_episodes_not_of_traders():
    """2 traders x 4 episodes = 8 slots; 3 zeros is 3/8, not 3/2."""
    row = {"eff_round": 0.5, "autarky_floor": 0.0,
           "zero_episodes": {"T1": 1, "T2": 2}, "ratios": {}}
    assert noise.endpoints_from(row, 4)["zero_episode_share"] == 3 / 8


def test_above_autarky_counts_only_ratios_strictly_above_one():
    row = {"eff_round": 0.5, "autarky_floor": 0.0, "zero_episodes": {},
           "ratios": {"T1": 1.4, "T2": 1.0, "T3": 0.2, "T4": None}}
    assert noise.endpoints_from(row, 4)["above_autarky_share"] == 1 / 4


def test_a_row_with_no_traders_yields_none_rather_than_dividing_by_zero():
    row = {"eff_round": None, "autarky_floor": None,
           "zero_episodes": {}, "ratios": {}}
    got = noise.endpoints_from(row, 4)
    assert got["zero_episode_share"] is None
    assert got["above_autarky_share"] is None


# --- the summary --------------------------------------------------------

def test_between_replicate_sd_is_the_sd_of_replicate_means():
    """Not the sd of every game pooled -- those are different numbers, and
    conflating them is how a threshold gets chosen against the wrong one."""
    reps = [[game(zero_episode_share=0.0), game(zero_episode_share=0.4)],
            [game(zero_episode_share=0.2), game(zero_episode_share=0.2)]]
    summary = noise.between_replicate_sd(reps)["zero_episode_share"]
    assert summary["replicate_means"] == [0.2, 0.2]
    assert summary["between_replicate_sd"] == 0.0
    # pooled, the same games do move
    assert summary["per_game_sd"] > 0
    assert summary["games"] == 4


def test_a_missing_endpoint_shrinks_its_own_denominator_only():
    reps = [[game(), game(capture=None)]]
    summary = noise.between_replicate_sd(reps)
    assert summary["capture"]["games"] == 1
    assert summary["zero_episode_share"]["games"] == 2


# --- the two refusals ---------------------------------------------------

def test_a_bounded_endpoint_on_a_bound_in_every_game_is_pinned():
    """Found by running the real thing at 15s: every game settled nothing,
    every share sat at a bound, and the reported sd was 0.0000 -- which reads
    as the most precise instrument this lab has ever had."""
    reps = [[game(zero_episode_share=1.0, above_autarky_share=0.0)],
            [game(zero_episode_share=1.0, above_autarky_share=0.0)]]
    assert noise.pinned(reps) == ["above_autarky_share", "zero_episode_share"]


def test_an_endpoint_that_moves_off_a_bound_is_not_pinned():
    reps = [[game(zero_episode_share=1.0, above_autarky_share=0.5)],
            [game(zero_episode_share=0.25, above_autarky_share=0.5)]]
    assert "zero_episode_share" not in noise.pinned(reps)


def test_an_unbounded_endpoint_is_never_called_pinned():
    """`capture` and `eff_round` have no bound to sit on, so the check must
    not be applied to them -- a constant capture is a different problem."""
    reps = [[game(capture=0.0, eff_round=0.0)]] * 2
    assert "capture" not in noise.pinned(reps)
    assert "eff_round" not in noise.pinned(reps)


def test_games_that_settled_nothing_are_counted_not_dropped():
    reps = [[game(settled=0), game(settled=3)], [game(settled=0)]]
    assert noise.dead(reps) == 2


def test_a_game_missing_its_settled_count_reads_as_dead_rather_than_alive():
    """Absent must not be optimistic: the whole class of defect this island
    keeps finding is the system reporting success while doing nothing."""
    assert noise.dead([[{"settled": None}]]) == 1


def test_replicates_that_returned_the_same_numbers_are_named_as_such():
    """The other road to a meaningless 0.0000, and the one NPCs actually take:
    heuristics are deterministic given their seed, so two replicates come back
    byte-identical and the sd is 0 because nothing varied."""
    reps = [[game()], [game()]]
    assert noise.identical(reps) is True


def test_replicates_that_differ_anywhere_are_not_identical():
    reps = [[game()], [game(eff_round=0.61)]]
    assert noise.identical(reps) is False


def test_one_replicate_cannot_be_identical_to_anything():
    assert noise.identical([[game()]]) is False
