"""Gates on the rules. A rule sees observations and nothing else."""

import math

import pytest

from promotion.rules import RULES, RULE_NAMES, Rule, Stats


def loaded(size, means, n, noise=0.0):
    """Stats as if each candidate had been observed n times around its mean."""
    st = Stats.empty(size)
    for i in range(size):
        for k in range(n):
            st.add(i, means[i] + (noise if k % 2 else -noise))
    return st


def test_stats_track_mean_and_standard_error():
    st = loaded(2, [1.0, 2.0], 10, noise=0.5)
    assert st.mean(0) == pytest.approx(1.0)
    assert st.stderr(0) == pytest.approx(0.5 / math.sqrt(10), rel=1e-6)


def test_standard_error_is_infinite_below_two_observations():
    st = Stats.empty(2)
    st.add(0, 1.0)
    assert st.stderr(0) == math.inf
    assert st.stderr(1) == math.inf


def test_leader_holds_all_but_the_exploration_share():
    rule = Rule("t", explore=0.2)
    shares = rule.shares(1, Stats.empty(3), 0)
    assert shares[1] == pytest.approx(0.8)
    assert shares[0] == shares[2] == pytest.approx(0.1)
    assert sum(shares) == pytest.approx(1.0)


def test_greedy_promotes_on_a_single_better_observation():
    rule = RULES["greedy"]
    st = Stats.empty(2)
    st.add(0, 0.5)
    st.add(1, 0.6)
    assert rule.challenger(0, st) == 1


def test_nmin_refuses_the_same_evidence_greedy_acts_on():
    st = Stats.empty(2)
    st.add(0, 0.5)
    st.add(1, 0.6)
    assert RULES["nmin"].challenger(0, st) is None


def test_nmin_promotes_once_it_has_enough():
    st = loaded(2, [0.5, 0.6], 40)
    assert RULES["nmin"].challenger(0, st) == 1


def test_interval_refuses_a_gap_inside_the_noise():
    # Same means as the passing case, but the spread swamps the difference.
    st = loaded(2, [0.5, 0.6], 40, noise=2.0)
    assert RULES["nmin"].challenger(0, st) == 1
    assert RULES["interval"].challenger(0, st) is None


def test_interval_promotes_a_gap_it_can_distinguish():
    st = loaded(2, [0.5, 0.9], 40, noise=0.05)
    assert RULES["interval"].challenger(0, st) == 1


def test_no_rule_promotes_a_worse_challenger():
    st = loaded(3, [0.9, 0.5, 0.4], 60)
    for name in RULE_NAMES:
        assert RULES[name].challenger(0, st) is None


def test_the_widest_gap_wins_when_several_qualify():
    st = loaded(3, [0.5, 0.6, 0.8], 60)
    assert RULES["nmin"].challenger(0, st) == 2


def test_gated_still_names_a_challenger_it_will_not_take():
    # The arm is the runner declining to act, not the rule failing to see.
    st = loaded(2, [0.5, 0.9], 60, noise=0.05)
    assert RULES["gated"].gated is True
    assert RULES["gated"].challenger(0, st) == 1


def test_bandit_sends_a_whole_step_to_one_untried_candidate():
    rule = RULES["bandit"]
    shares = rule.shares(0, Stats.empty(4), 0)
    assert sum(shares) == pytest.approx(1.0)
    assert sorted(shares)[-1] == pytest.approx(0.25)  # four ties, split evenly


def test_bandit_concentrates_once_everything_has_been_tried():
    rule = RULES["bandit"]
    st = loaded(3, [0.2, 0.9, 0.3], 50)
    shares = rule.shares(0, st, 100)
    assert shares[1] == pytest.approx(1.0)
