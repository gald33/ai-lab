"""Gates on the world. No network, no models, no randomness that isn't seeded."""

import random

import pytest

from promotion.world import (MODES, Pool, allocate, best_payoff, coupling,
                             draw_pool, observe)


def test_pool_knows_its_best_and_ranks():
    pool = Pool(quality=(0.6, 0.9, 0.7))
    assert pool.best == 1
    assert pool.rank(1) == 0
    assert pool.rank(0) == 2


def test_pool_rejects_a_competition_of_one():
    with pytest.raises(ValueError):
        Pool(quality=(0.5,))


def test_drawn_pool_stays_inside_its_spread():
    pool = draw_pool(random.Random(3), size=6, spread=0.4)
    assert pool.size == 6
    assert all(0.6 <= q <= 1.0 for q in pool.quality)


def test_strategy_coupling_ignores_the_population():
    assert coupling("none", 0.01) == coupling("none", 1.0) == 1.0


def test_linear_coupling_is_worthless_alone():
    # The pure case: a protocol nobody else uses has no content to fall back on.
    assert coupling("linear", 0.0) == 0.0
    assert coupling("linear", 0.5) == 0.5


def test_step_coupling_pays_a_floor_below_its_threshold():
    assert coupling("step", 0.49, threshold=0.5, floor=0.2) == 0.2
    assert coupling("step", 0.5, threshold=0.5, floor=0.2) == 1.0


def test_unknown_coupling_raises_rather_than_defaulting():
    with pytest.raises(ValueError):
        coupling("sideways", 0.5)


def test_every_mode_names_a_real_coupling():
    for kind in MODES.values():
        coupling(kind, 0.5)


def test_best_payoff_is_the_whole_population_on_the_best():
    pool = Pool(quality=(0.5, 0.8))
    assert best_payoff(pool, "none") == pytest.approx(0.8)
    assert best_payoff(pool, "linear") == pytest.approx(0.8)
    assert best_payoff(pool, "step") == pytest.approx(0.8)


def test_observation_is_centred_on_quality_times_coupling():
    pool = Pool(quality=(0.5, 0.8), noise=0.1)
    rng = random.Random(1)
    draws = [observe(rng, pool, 1, 0.5, "linear") for _ in range(4000)]
    assert sum(draws) / len(draws) == pytest.approx(0.4, abs=0.01)


def test_noise_free_observation_is_exact():
    pool = Pool(quality=(0.5, 0.8), noise=0.0)
    assert observe(random.Random(0), pool, 0, 0.25, "linear") == pytest.approx(0.125)


def test_allocation_is_exact_and_favours_the_largest_remainder():
    counts = allocate([0.9, 0.05, 0.05], 20)
    assert sum(counts) == 20
    assert counts[0] == 18


def test_allocation_stays_exact_on_awkward_splits():
    for n in (7, 13, 20, 99):
        counts = allocate([1 / 3, 1 / 3, 1 / 3], n)
        assert sum(counts) == n


def test_allocation_refuses_an_empty_split():
    with pytest.raises(ValueError):
        allocate([0.0, 0.0], 10)


def test_rotation_reaches_every_candidate_over_a_stream():
    # Regression. With a fixed tie-break and an exploration share thinner than
    # one invocation, every challenger has the same remainder and the spare
    # invocations go to the same low indices forever — so part of the pool is
    # never sampled at all, by any rule, and the harness picks the winner. The
    # first run of this experiment did exactly that.
    shares = [0.9] + [0.025] * 4
    totals = [0] * 5
    for step in range(400):
        counts = allocate(shares, 20, offset=step)
        totals = [a + b for a, b in zip(totals, counts)]
    assert all(t > 0 for t in totals), totals
    challengers = totals[1:]
    assert max(challengers) - min(challengers) <= 0.25 * max(challengers)


def test_a_fixed_offset_still_starves_and_is_why_offset_exists():
    shares = [0.9] + [0.025] * 4
    totals = [0] * 5
    for _ in range(400):
        counts = allocate(shares, 20, offset=0)
        totals = [a + b for a, b in zip(totals, counts)]
    assert min(totals) == 0
