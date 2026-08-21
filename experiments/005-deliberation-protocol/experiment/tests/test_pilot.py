"""Gates on the 005 pilot. Offline, no models, no network.

Three things need pinning. First, that the frozen stimuli have not moved, since
the placebo carries the experiment's causal weight. Second, that the four
acceptance criteria are computed from the numbers rather than read off a table
— the whole point of operationalising "visible spread" was to remove the
judgement call, and a gate is what stops it coming back. Third, that a harness
fault is classified as a harness fault and never enters a rate, which is the
mistake 002 and 004 each made once.
"""

import math
import re
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))

from pilot.gate import (BAND, MAX_INSTANT, MIN_COORDINATED, MIN_IQR, evaluate,
                        _quartiles)
from pilot.run import (AGENT_FAILURE, BUDGET_EXHAUSTED, COORDINATED,
                       HARNESS_FAILURE, TAU, TAU_CURVE, World, run_world)
from pilot.world import Config, dispersion, draw_agents, draw_truth, normalise
import check_stimuli


CFG = Config(8, 4, 0.30, 2, 0.15, 20)


# --- the frozen stimuli -----------------------------------------------------

def test_the_frozen_stimuli_have_not_moved():
    assert check_stimuli.check() == []


def test_the_placebo_is_length_matched_to_the_protocol():
    root = pathlib.Path(__file__).resolve().parents[2] / "stimuli"
    a = len(root.joinpath("protocol.md").read_text().split())
    b = len(root.joinpath("placebo.md").read_text().split())
    assert abs(a - b) / max(a, b) < 0.10, f"{a} vs {b} words is not matched"


def _mentions(text: str, word: str) -> bool:
    # Word boundaries, not substrings. The stimuli are frozen, so an
    # over-broad gate cannot be resolved by editing the text it guards — the
    # first version of this flagged "buys nothing" as naming a purchase.
    return re.search(rf"\b{re.escape(word)}\b", text) is not None


def test_the_placebo_contains_no_coordination_vocabulary():
    # A placebo that accidentally tells agents to agree with each other is not
    # a control, and this experiment would have no interpretable result.
    root = pathlib.Path(__file__).resolve().parents[2] / "stimuli"
    text = root.joinpath("placebo.md").read_text().lower()
    for word in ("propose", "proposal", "object", "objection", "accept",
                 "agree", "agreement", "converge", "consensus", "group",
                 "others", "everyone", "anyone else"):
        assert not _mentions(text, word), f"placebo mentions {word!r}"


def test_the_protocol_names_no_market_content():
    # A protocol that names a price or a good would smuggle the hint into the
    # method arm, which is the one thing the design must not do.
    root = pathlib.Path(__file__).resolve().parents[2] / "stimuli"
    text = root.joinpath("protocol.md").read_text().lower()
    for word in ("price", "prices", "good", "goods", "quantity", "produce",
                 "production", "trade", "buy", "sell", "market",
                 "equilibrium", "role", "seller", "buyer"):
        assert not _mentions(text, word), f"protocol names market content: {word!r}"


# --- dispersion is the metric the pre-registration says it is ---------------

def test_dispersion_is_zero_when_everyone_submits_the_same_thing():
    p = [1.0, 2.0, 0.5, 3.0]
    assert dispersion([p, p, p]) == pytest.approx(0.0)


def test_dispersion_is_the_max_not_the_mean():
    # One agent acting on a different claim is the failure being measured, so a
    # lone outlier must not be averaged away by its agreeable neighbours.
    tight = [[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]]
    outlier = [[1.0, 1.0], [1.0, 1.0], [1.0, 3.0]]
    assert dispersion(outlier) > 5 * dispersion(tight)


def test_dispersion_ignores_scale_because_positions_are_normalised():
    a, b = [1.0, 2.0, 3.0, 4.0], [2.0, 4.0, 6.0, 8.0]
    assert dispersion([normalise(a), normalise(b)]) == pytest.approx(0.0)


def test_normalise_pins_the_numeraire():
    assert normalise([4.0, 8.0, 2.0])[0] == 1.0


# --- outcome classification -------------------------------------------------

def test_a_world_is_deterministic_under_its_seed():
    a, b = run_world(CFG, 7), run_world(CFG, 7)
    assert a.trajectory == b.trajectory and a.outcome == b.outcome


def test_every_world_lands_in_exactly_one_outcome():
    seen = {run_world(CFG, s).outcome for s in range(1, 25)}
    assert seen <= {COORDINATED, AGENT_FAILURE, BUDGET_EXHAUSTED, HARNESS_FAILURE}


def test_a_coordinated_world_records_where_and_how_wrong_it_was():
    hit = next(w for w in (run_world(CFG, s) for s in range(1, 40))
               if w.outcome == COORDINATED)
    assert hit.coordinated_at is not None
    assert hit.trajectory[hit.coordinated_at] <= TAU
    assert hit.error is not None, "agreement is not correctness; record both"


def test_agreement_is_not_correctness():
    # A world can agree on the wrong answer. If error were always ~0 the
    # secondary metric would be decorative.
    errs = [w.error for w in (run_world(Config(8, 4, 0.6, 2, 0.05, 20), s)
                              for s in range(1, 40))
            if w.error is not None]
    assert errs and max(errs) > 0.05


def test_the_full_budget_is_always_run_so_the_tau_curve_is_not_truncated():
    # Returning early at TAU would make the tighter rows of the sensitivity
    # curve unreachable and every one of them would read low by construction.
    w = next(x for x in (run_world(CFG, s) for s in range(1, 40))
             if x.outcome == COORDINATED)
    assert len(w.trajectory) == CFG.rounds + 1
    assert set(w.coordinated_at_tau) == {f"{t:g}" for t in TAU_CURVE}


def test_the_tau_curve_is_monotone_in_tau():
    w = next(x for x in (run_world(CFG, s) for s in range(1, 40))
             if x.outcome == COORDINATED)
    hits = [w.coordinated_at_tau[f"{t:g}"] for t in sorted(TAU_CURVE)]
    seen = [h for h in hits if h is not None]
    assert seen == sorted(seen, reverse=True) or len(set(seen)) <= 1


def test_budget_exhausted_is_distinguished_from_a_population_that_will_not_agree():
    # The difference between "ran out of rounds" and "would never agree" is the
    # difference between a harness choice and a finding about agents.
    from pilot.run import _still_falling
    assert _still_falling([0.9, 0.5, 0.3])
    assert not _still_falling([0.5, 0.5, 0.5])
    assert not _still_falling([0.3, 0.4, 0.3])


def test_every_round_records_a_submission_count_and_a_wall_clock():
    w = run_world(CFG, 3)
    assert len(w.submissions) == len(w.trajectory) == len(w.seconds)
    assert all(c == CFG.n_agents for c in w.submissions)
    assert all(s >= 0 for s in w.seconds)


def test_a_raising_world_is_a_harness_failure_and_not_a_datum(monkeypatch):
    import pilot.run as run_mod

    def boom(_):
        raise RuntimeError("simulated harness fault")

    monkeypatch.setattr(run_mod, "dispersion", boom)
    w = run_mod.run_world(CFG, 1)
    assert w.outcome == HARNESS_FAILURE
    assert "simulated harness fault" in w.note


def test_harness_failures_are_excluded_from_the_rate_and_counted_separately():
    good = [run_world(CFG, s) for s in range(1, 21)]
    broken = World(config=CFG, seed=99, outcome=HARNESS_FAILURE, note="timeout")
    a = evaluate(good, CFG.rounds)
    b = evaluate(good + [broken] * 20, CFG.rounds)
    assert b.harness_failures == 20
    assert b.scored == a.scored
    assert b.rate == pytest.approx(a.rate), "a timeout must not move a rate"


def test_evaluate_refuses_a_sweep_that_was_entirely_harness_failure():
    broken = World(config=CFG, seed=1, outcome=HARNESS_FAILURE, note="timeout")
    with pytest.raises(ValueError):
        evaluate([broken], CFG.rounds)


# --- the four criteria ------------------------------------------------------

def _fake(rounds_at: list[int | None], cfg=CFG) -> list[World]:
    out = []
    for i, r in enumerate(rounds_at):
        w = World(config=cfg, seed=i,
                  outcome=COORDINATED if r is not None else AGENT_FAILURE,
                  coordinated_at=r, error=0.05 if r is not None else None)
        w.coordinated_at_tau = {f"{t:g}": r for t in TAU_CURVE}
        out.append(w)
    return out


def test_p1_rejects_a_market_nobody_can_solve_and_one_everybody_can():
    assert not evaluate(_fake([None] * 40), 20).p1
    assert not evaluate(_fake([5] * 40), 20).p1
    assert evaluate(_fake([5, 8, 11, 14, 3, 9, 12, 6, 15, 4] + [None] * 20), 20).p1


def test_p2_rejects_a_market_that_agrees_instantly():
    v = evaluate(_fake([0, 1, 0, 1, 0, 1, 0, 1, 9, 12] + [None] * 15), 20)
    assert v.instant_share > MAX_INSTANT and not v.p2


def test_p3_rejects_a_market_pinned_at_the_round_ceiling():
    v = evaluate(_fake([17, 18, 19, 20, 17, 18, 19, 20, 3, 5] + [None] * 15), 20)
    assert not v.p3, "coordination bunched in the final quintile is censoring"


def test_p4_needs_both_a_spread_and_enough_worlds_to_have_one():
    flat = evaluate(_fake([6, 6, 6, 6, 6, 6, 6, 6, 6, 6] + [None] * 20), 20)
    assert flat.iqr < MIN_IQR and not flat.p4
    thin = evaluate(_fake([2, 6, 14] + [None] * 10), 20)
    assert thin.iqr >= MIN_IQR and thin.coordinated < MIN_COORDINATED
    assert not thin.p4, "an IQR over three worlds is not a spread"


def test_acceptance_needs_all_four():
    v = evaluate(_fake([3, 5, 7, 9, 11, 13, 4, 8, 12, 6] + [None] * 20), 20)
    assert v.p1 and v.p2 and v.p3 and v.p4 and v.accepted


def test_quartiles_interpolate_the_way_the_report_says_they_do():
    assert _quartiles([1, 2, 3, 4, 5]) == (2.0, 4.0)
    assert _quartiles([1, 1]) == (1.0, 1.0)


def test_the_band_and_criteria_match_the_pre_registration():
    # The constants live in code so they cannot drift once numbers are in.
    text = (pathlib.Path(__file__).resolve().parents[2]
            / "PREREGISTRATION.md").read_text()
    assert f"[{BAND[0]}, {BAND[1]}]".replace("0.6,", "0.60,") in text or \
        "[0.15, 0.60]" in text
    assert f"{int(MAX_INSTANT * 100)}%" in text
    assert f">= {int(MIN_IQR)} rounds" in text
    assert f"least **{MIN_COORDINATED}**" in text
    assert f"TAU = {TAU:g}" in text or f"`TAU = 0.10`" in text


# --- the sweep itself -------------------------------------------------------

def test_the_grid_is_a_full_factorial_and_is_fixed_in_the_file():
    from pilot_experiment import ANCHORS, SIGMAS, WIDTHS, grid
    g = grid()
    assert len(g) == len(SIGMAS) * len(WIDTHS) * len(ANCHORS)
    assert len({c.key for c in g}) == len(g)


def test_the_grid_spans_both_extremes_rather_than_a_neighbourhood():
    # If the grid only covered configurations that pass, the published search
    # would be a formality.
    from pilot_experiment import ROUNDS, grid
    verdicts = []
    for cfg in grid()[:9]:
        worlds = [run_world(cfg, s) for s in range(1, 21)]
        verdicts.append(evaluate(worlds, ROUNDS))
    assert any(v.rate > BAND[1] for v in verdicts), "no trivially-solved corner"
