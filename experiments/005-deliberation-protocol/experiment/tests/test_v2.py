"""Gates on the 005 v2 harness. Offline, no models, no network.

The model is stubbed with a scripted responder, so these test the *world* and
the *plumbing*: that the clock is enforced, that escrow cannot be double-spent,
that conservation holds at the bell, that a bell expiry is not a decline, that
a refused call is reported rather than repaired, and that the five cells differ
by exactly their treatment blocks.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island  # noqa: E402
from v2 import episode as episode_mod  # noqa: E402
from v2.episode import run_episode  # noqa: E402
from v2.prompt import CELLS, stimulus, turn  # noqa: E402
from v2.runner import Turn  # noqa: E402
from v2.score import score  # noqa: E402
from v2.world import ActionError, MARKET, PRODUCTION, World  # noqa: E402

ISLAND = draw_island(8, 4, seed=1)


def fresh(periods=2) -> World:
    return World(island=draw_island(8, 4, seed=1), periods=periods)


def stock(w: World) -> None:
    w.open(PRODUCTION)
    for n in w.traders:
        w.produce(n, {g: 0.25 for g in w.goods})


# --- the clock ----------------------------------------------------------

def test_producing_outside_the_production_stage_is_refused():
    w = fresh()
    with pytest.raises(ActionError):
        w.produce("T1", {"bread": 1.0})


def test_offering_outside_the_market_is_refused():
    w = fresh()
    stock(w)
    with pytest.raises(ActionError):
        w.offer("T1", "T2", {"bread": 0.1}, {"cloth": 0.1})


def test_talking_is_allowed_in_every_open_stage():
    # The design's claim that talk before production differs from talk after it
    # only means anything if talking is possible in both.
    w = fresh()
    w.post("T1", "floor")
    w.open(PRODUCTION)
    w.message("T1", "T2", "production")
    w.open(MARKET)
    w.post("T1", "market")
    assert w.posts == 2 and w.directs == 1


def test_one_production_call_per_period():
    w = fresh()
    w.open(PRODUCTION)
    w.produce("T1", {"bread": 0.5})
    with pytest.raises(ActionError):
        w.produce("T1", {"cloth": 0.5})


def test_labour_budget_is_enforced():
    w = fresh()
    w.open(PRODUCTION)
    with pytest.raises(ActionError):
        w.produce("T1", {"bread": 0.7, "cloth": 0.7})


# --- the board ----------------------------------------------------------

def test_a_post_reaches_everyone_and_a_message_reaches_one():
    w = fresh()
    w.post("T1", "everyone")
    w.message("T1", "T3", "just you")
    assert len(w.read("T3")) == 2, "T3 sees the post and the direct message"
    assert [m["text"] for m in w.read("T2")] == ["everyone"], \
        "T2 sees the post and never the direct message"
    assert w.read("T2") == [], "and the cursor means it arrives only once"


def test_you_do_not_read_your_own_messages():
    w = fresh()
    w.post("T1", "mine")
    assert w.read("T1") == []


def test_the_cursor_means_each_item_arrives_once():
    w = fresh()
    w.post("T1", "one")
    assert len(w.read("T2")) == 1
    assert w.read("T2") == []
    w.post("T1", "two")
    assert len(w.read("T2")) == 1


# --- escrow and exchange ------------------------------------------------

def test_an_open_offer_commits_the_goods_it_promises():
    w = fresh()
    stock(w)
    w.open(MARKET)
    free = w.free("T1", "bread")
    w.offer("T1", "T2", {"bread": free}, {"cloth": 0.1})
    assert w.free("T1", "bread") == pytest.approx(0.0)
    with pytest.raises(ActionError):
        w.offer("T1", "T3", {"bread": free}, {"iron": 0.1})


def test_cancelling_returns_the_escrow():
    w = fresh()
    stock(w)
    w.open(MARKET)
    before = w.free("T1", "bread")
    r = w.offer("T1", "T2", {"bread": 0.05}, {"cloth": 0.05})
    w.cancel("T1", r["offer_id"])
    assert w.free("T1", "bread") == pytest.approx(before)


def test_only_the_named_taker_can_accept():
    w = fresh()
    stock(w)
    w.open(MARKET)
    r = w.offer("T1", "T2", {"bread": 0.05}, {"cloth": 0.05})
    with pytest.raises(ActionError):
        w.accept("T3", r["offer_id"])


def test_an_offer_settles_once():
    w = fresh()
    stock(w)
    w.open(MARKET)
    r = w.offer("T1", "T2", {"bread": 0.05}, {"cloth": 0.05})
    w.accept("T2", r["offer_id"])
    with pytest.raises(ActionError):
        w.accept("T2", r["offer_id"])


def test_a_trade_moves_goods_both_ways():
    w = fresh()
    stock(w)
    w.open(MARKET)
    b1, c2 = w.free("T1", "bread"), w.free("T2", "cloth")
    r = w.offer("T1", "T2", {"bread": 0.05}, {"cloth": 0.04})
    w.accept("T2", r["offer_id"])
    assert w.free("T1", "bread") == pytest.approx(b1 - 0.05)
    assert w.free("T2", "cloth") == pytest.approx(c2 - 0.04)
    assert w.free("T1", "cloth") > 0 and w.free("T2", "bread") > 0


# --- the bell -----------------------------------------------------------

def test_conservation_holds_across_periods():
    w = fresh(periods=3)
    for _ in range(3):
        stock(w)
        w.open(MARKET)
        w.check_conservation()
        w.close_period()
    assert len(w.period_utilities) == 3


def test_the_bell_is_not_a_decline():
    w = fresh()
    stock(w)
    w.open(MARKET)
    w.offer("T1", "T2", {"bread": 0.05}, {"cloth": 0.05})
    w.close_period()
    assert w.expired_at_bell == 1
    assert w.declined == 0


def test_holdings_are_eaten_and_labour_returns():
    w = fresh()
    stock(w)
    total = sum(sum(t.holdings) for t in w.traders.values())
    assert total > 0
    w.close_period()
    assert sum(sum(t.holdings) for t in w.traders.values()) == pytest.approx(0.0)
    assert sum(w.consumed) == pytest.approx(total)
    assert all(not t.produced_this_period for t in w.traders.values())


def test_a_good_nobody_makes_zeroes_everyone():
    # The coverage coupling the design rests on, at the smallest scale that
    # shows it: three goods covered perfectly, one missing, everyone at zero.
    w = fresh()
    w.open(PRODUCTION)
    for n in w.traders:
        w.produce(n, {"bread": 0.34, "cloth": 0.33, "iron": 0.33})
    utils = w.close_period()
    assert all(u == 0.0 for u in utils)


# --- scoring ------------------------------------------------------------

def test_scoring_refuses_an_episode_with_no_closed_period():
    with pytest.raises(ValueError):
        score(ISLAND, [])


def test_w_is_bracketed_and_counts_zeros():
    w = fresh(periods=2)
    for _ in range(2):
        stock(w)
        w.close_period()
    s = score(ISLAND, w.period_utilities)
    assert 0.0 <= s.w <= s.w_upper <= 1.0
    assert s.agent_periods == 16
    assert s.zero_agent_periods == 0


# --- cells --------------------------------------------------------------

def test_every_cell_is_base_plus_exactly_its_treatments():
    base = stimulus("bare", 3)
    for cell, (block, hint) in CELLS.items():
        text = stimulus(cell, 3)
        assert text.startswith(base), f"{cell} does not contain the base block"
        assert ("A shared way of talking" in text) == (block == "protocol")
        assert ("Some general advice" in text) == (block == "placebo")
        assert ("worth noticing about this island" in text) == hint


def test_the_period_count_is_substituted_everywhere():
    assert "{periods}" not in stimulus("both", 5)
    assert "5 periods" in stimulus("both", 5)


def test_a_turn_prompt_carries_state_inbox_and_format():
    w = fresh()
    w.post("T2", "hello everyone")
    p = turn(cell="bare", state=w.state("T1"), inbox=w.read("T1"),
             pending=w.pending("T1"), results=["produced {}"], periods=3)
    assert "hello everyone" in p and "capacity" in p and '"actions"' in p
    assert "What happened to your last actions" in p


# --- the loop, with the model stubbed -----------------------------------

def test_a_refused_call_is_reported_and_never_repaired(monkeypatch):
    """The harness must not invent a production plan for a bad one."""
    def stub(prompt, cwd):
        if "production stage is open" in prompt:
            return Turn(actions=[{"call": "produce",
                                  "plan": {"bread": 0.9, "cloth": 0.9}}], raw="")
        return Turn(actions=[], raw="")
    monkeypatch.setattr(episode_mod, "ask", stub)
    ep = run_episode(island=ISLAND, cell="bare", seed=1, periods=1, cwd=".",
                     concurrency=2)
    assert ep.outcome == "scored"
    assert ep.refused == 8, "every trader's over-budget plan should be refused"
    assert all(u == 0.0 for u in ep.trajectory[0]), "nobody produced anything"


def test_every_call_the_base_block_advertises_is_accepted(monkeypatch):
    """The surface described to agents and the surface implemented must match.

    The pilot spent 43 of its 154 refusals on `read` and `pending` -- calls the
    base block documents and the executor did not accept. A harness that
    refuses what its own instructions offer is measuring its own inconsistency.
    """
    import re as _re
    from v2.prompt import STIM
    advertised = set(_re.findall(r"^- `(\w+)\(", (STIM / "base.md").read_text(),
                                 _re.M))
    calls = [{"call": c} for c in sorted(advertised)]

    def stub(prompt, cwd):
        return Turn(actions=calls, raw="")
    monkeypatch.setattr(episode_mod, "ask", stub)
    ep = run_episode(island=ISLAND, cell="bare", seed=1, periods=1, cwd=".",
                     concurrency=2)
    unknown = [r for row in ep.transcript for r in row["results"]
               if "no such call" in r]
    assert not unknown, f"base.md advertises calls the executor rejects: {unknown[:3]}"


def test_the_stubbed_loop_completes_and_is_scorable(monkeypatch):
    def stub(prompt, cwd):
        if "production stage is open" in prompt:
            return Turn(actions=[{"call": "produce",
                                  "plan": {"bread": .25, "cloth": .25,
                                           "iron": .25, "salt": .25}}], raw="")
        return Turn(actions=[{"call": "post", "text": "hello"}], raw="")
    monkeypatch.setattr(episode_mod, "ask", stub)
    ep = run_episode(island=ISLAND, cell="protocol", seed=2, periods=2,
                     cwd=".", concurrency=4)
    assert ep.outcome == "scored"
    assert len(ep.trajectory) == 2
    s = score(ISLAND, ep.trajectory)
    assert s.w > 0
