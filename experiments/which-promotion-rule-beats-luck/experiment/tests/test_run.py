"""Gates on the stream. Determinism, bookkeeping, and the two modes."""

import pytest

from promotion.rules import RULES
from promotion.run import play, _start_index
from promotion.world import Pool


POOL = Pool(quality=(0.5, 0.6, 0.9), noise=0.1)


def test_start_picks_by_rank_not_by_index():
    assert _start_index(POOL, "best") == 2
    assert _start_index(POOL, "worst") == 0
    assert _start_index(POOL, "middle") == 1


def test_unknown_start_raises():
    with pytest.raises(ValueError):
        _start_index(POOL, "sideways")


def test_the_same_seed_gives_the_same_stream():
    a = play(POOL, RULES["greedy"], "strategy", seed=7, steps=50)
    b = play(POOL, RULES["greedy"], "strategy", seed=7, steps=50)
    assert a.regret == b.regret
    assert a.promotions == b.promotions


def test_different_seeds_give_different_streams():
    a = play(POOL, RULES["greedy"], "strategy", seed=1, steps=50)
    b = play(POOL, RULES["greedy"], "strategy", seed=2, steps=50)
    assert a.regret != b.regret


def test_gated_never_promotes_but_records_what_it_would_have():
    rec = play(POOL, RULES["gated"], "strategy", seed=3, start="worst", steps=300)
    assert rec.promotions == []
    assert rec.final_leader == _start_index(POOL, "worst")
    assert rec.would_have, "the control has to show the evidence it declined"


def test_starting_on_the_best_leaves_nothing_entrenched():
    rec = play(POOL, RULES["interval"], "strategy", seed=4, start="best", steps=100)
    assert rec.entrenched_steps == 0
    assert rec.final_correct


def test_regret_is_zero_when_the_best_holds_everything_without_noise():
    quiet = Pool(quality=(0.5, 0.9), noise=0.0)
    rule = RULES["interval"].__class__("all-in", explore=0.0, n_min=30, z=2.0)
    rec = play(quiet, rule, "strategy", seed=5, start="best", steps=20)
    assert rec.regret == pytest.approx(0.0, abs=1e-9)


def test_entrenchment_and_starvation_only_count_while_the_leader_is_wrong():
    rec = play(POOL, RULES["gated"], "strategy", seed=6, start="worst", steps=80)
    assert rec.entrenched_steps == 80
    # gated allocates leader-plus-exploration, so the best sits on its share.
    assert rec.starved_share == pytest.approx(RULES["gated"].explore / 2, abs=1e-6)


def test_a_correct_promotion_stamps_the_step_it_happened():
    rec = play(POOL, RULES["greedy"], "strategy", seed=8, start="worst", steps=200)
    if rec.first_correct_step is not None:
        step, _, target = rec.promotions[
            [i for i, p in enumerate(rec.promotions) if p[2] == POOL.best][0]]
        assert rec.first_correct_step == step
        assert target == POOL.best


def test_reversals_count_returning_to_a_previous_leader():
    rec = play(POOL, RULES["greedy"], "strategy", seed=9, start="worst", steps=300)
    seen, reversals = {_start_index(POOL, "worst")}, 0
    for _, _, target in rec.promotions:
        if target in seen:
            reversals += 1
        seen.add(target)
    assert rec.reversals == reversals


def test_protocol_mode_differs_from_strategy_mode_on_the_same_seed():
    a = play(POOL, RULES["interval"], "strategy", seed=11, steps=100)
    b = play(POOL, RULES["interval"], "protocol-linear", seed=11, steps=100)
    assert a.regret != b.regret


def test_the_coupling_is_the_only_difference_between_the_modes():
    # With coupling removed, protocol mode *is* strategy mode. If this ever
    # fails, the two modes differ by something nobody designed in and the whole
    # comparison is measuring that instead.
    quiet = Pool(quality=(0.4, 0.8), noise=0.05)
    from promotion.world import MODES
    assert MODES["strategy"] == "none"
    a = play(quiet, RULES["nmin"], "strategy", seed=12, steps=60)
    b = play(quiet, RULES["nmin"], "strategy", seed=12, steps=60)
    assert (a.regret, a.promotions) == (b.regret, b.promotions)


def test_record_survives_a_round_trip_to_json():
    import json
    rec = play(POOL, RULES["nmin"], "protocol-step", seed=13, steps=40)
    payload = json.loads(json.dumps(rec.to_json()))
    assert payload["mode"] == "protocol-step"
    assert payload["quality"] == list(POOL.quality)
    assert payload["steps"] == 40
