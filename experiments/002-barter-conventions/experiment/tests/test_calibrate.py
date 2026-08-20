"""Gates on the Tier 3 calibration instrument. Offline, no models.

The perturbation is the measuring stick for the whole tier, so these are gates
on the stick rather than on any result: that delta 0 is genuinely the
equilibrium, that the two directions are different mistakes, and that an
announced price is not quietly walked back toward the truth by discovery.
"""

import math
import random

import pytest

from barter.calibrate import (ADHERENCES, DELTAS, announce, distance,
                              implied_plan, normalise, perturb)
from barter.economy import draw_island, walras
from barter.run import run_island
from barter.traders import NUMERAIRE, Floor, Trader


ISLAND = draw_island(6, 4, seed=1)


def test_normalise_pins_the_numeraire_at_one():
    out = normalise([2.0, 4.0, 1.0])
    assert out[NUMERAIRE] == pytest.approx(1.0)
    assert out[1] == pytest.approx(2.0)


def test_normalise_refuses_a_worthless_numeraire():
    with pytest.raises(ValueError):
        normalise([0.0, 1.0])


def test_delta_zero_is_the_equilibrium_untouched():
    truth = normalise(walras(ISLAND).prices)
    assert perturb(truth, 0.0, "flatten") == pytest.approx(truth)
    assert perturb(truth, 0.0, "sharpen") == pytest.approx(truth)


def test_flatten_moves_toward_one_price_for_everything():
    truth = normalise(walras(ISLAND).prices)
    flat = perturb(truth, 1.0, "flatten")
    # At delta 1 every good is priced the same, which is what an agent that
    # never heard a price believes — so this direction runs the convention all
    # the way down to no convention.
    assert max(flat) - min(flat) == pytest.approx(0.0, abs=1e-9)


def test_flatten_is_monotone_in_delta():
    truth = normalise(walras(ISLAND).prices)
    spreads = [max(p) - min(p) for p in
               (perturb(truth, d, "flatten") for d in (0.0, 0.25, 0.5, 0.75))]
    assert spreads == sorted(spreads, reverse=True)


def test_sharpen_widens_the_spread_and_keeps_the_ranking():
    truth = normalise(walras(ISLAND).prices)
    sharp = perturb(truth, 0.5, "sharpen")
    assert max(sharp) - min(sharp) > max(truth) - min(truth)
    order = sorted(range(len(truth)), key=lambda g: truth[g])
    assert sorted(range(len(sharp)), key=lambda g: sharp[g]) == order


def test_the_two_directions_are_different_mistakes():
    truth = normalise(walras(ISLAND).prices)
    assert perturb(truth, 0.4, "flatten") != pytest.approx(perturb(truth, 0.4, "sharpen"))


def test_unknown_direction_raises_rather_than_defaulting():
    with pytest.raises(ValueError):
        perturb([1.0, 2.0], 0.2, "sideways")


def test_negative_delta_raises():
    with pytest.raises(ValueError):
        perturb([1.0, 2.0], -0.1, "flatten")


def test_distance_is_zero_to_itself_and_grows_with_delta():
    truth = normalise(walras(ISLAND).prices)
    assert distance(truth, truth) == pytest.approx(0.0)
    errs = [distance(perturb(truth, d, "flatten"), truth) for d in (0.1, 0.3, 0.6)]
    assert errs == sorted(errs)


def test_distance_ignores_the_overall_level():
    # Only relative prices carry meaning, so a rescaled vector is the same
    # convention and must not register as an error.
    assert distance([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(0.0)


def test_announcement_carries_its_own_interpretation():
    note = announce(ISLAND, 0.3, "flatten")
    assert note.delta == 0.3
    assert note.direction == "flatten"
    assert note.error > 0
    assert len(note.price) == ISLAND.n_goods
    assert len(note.implied) == ISLAND.n_agents
    payload = note.to_json()
    assert payload["price"] == list(note.price)


def test_the_implied_plan_commits_each_agent_to_exactly_one_good():
    note = announce(ISLAND, 0.2, "sharpen")
    for row in note.implied:
        assert sum(row) == pytest.approx(1.0)
        assert sorted(row)[-1] == pytest.approx(1.0)


def test_the_implied_plan_follows_the_announced_price_not_the_true_one():
    # The answer key has to be keyed to what agents were told, or "did they do
    # what the convention said" silently becomes "did they do the right thing".
    truth = normalise(walras(ISLAND).prices)
    flat = perturb(truth, 1.0, "flatten")
    under_truth = implied_plan(ISLAND, truth)
    under_flat = implied_plan(ISLAND, flat)
    assert under_truth != under_flat


def test_an_announced_price_survives_discovery():
    # Tatonnement on top of an announced vector would walk it back toward
    # equilibrium and quietly undo the perturbation being measured.
    announced = [1.0, 9.0, 0.2, 3.0]
    t = Trader("a1", 0, ISLAND, "C", random.Random(0), announced=announced)
    t.goods = [f"g{i}" for i in range(ISLAND.n_goods)]
    floor = Floor(enabled=True)
    for round_no in range(5):
        t.declare(round_no, floor)
        t.observe_prices(round_no, floor)
    assert t.price == announced


def test_a_trader_without_an_announcement_still_discovers():
    t = Trader("a1", 0, ISLAND, "C", random.Random(0))
    assert t.announced is None
    assert t.price == [1.0] * ISLAND.n_goods


def test_full_adherence_gives_every_agent_the_announcement():
    note = announce(ISLAND, 0.2, "flatten")
    out = run_island(ISLAND, "C", seed=1, trade_rounds=5,
                     announced=list(note.price), adherence=1.0)
    assert out.arm == "C"


def test_partial_adherence_changes_the_island():
    note = announce(ISLAND, 0.2, "flatten")
    full = run_island(ISLAND, "C", seed=1, trade_rounds=20,
                      announced=list(note.price), adherence=1.0)
    half = run_island(ISLAND, "C", seed=1, trade_rounds=20,
                      announced=list(note.price), adherence=0.5)
    assert (full.utilities, full.executed) != (half.utilities, half.executed)


def test_zero_adherence_leaves_nobody_on_the_convention():
    note = announce(ISLAND, 0.2, "flatten")
    out = run_island(ISLAND, "C", seed=1, trade_rounds=20,
                     announced=list(note.price), adherence=0.0)
    assert out.messages == 0, "a non-adopter falls back to arm A, which has no floor"


def test_an_island_with_no_announcement_is_untouched_by_the_new_path():
    # The calibration must not have changed what the published ladder measures.
    a = run_island(ISLAND, "C", seed=1, trade_rounds=20)
    b = run_island(ISLAND, "C", seed=1, trade_rounds=20, announced=None, adherence=0.5)
    assert a.utilities == b.utilities
    assert (a.executed, a.messages) == (b.executed, b.messages)


def test_the_sweep_constants_are_ordered_and_start_at_the_truth():
    assert DELTAS[0] == 0.0
    assert list(DELTAS) == sorted(DELTAS)
    assert ADHERENCES[0] == 1.0
