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
from v2 import round as round_mod  # noqa: E402
from v2.round import run_round  # noqa: E402
from v2.prompt import CELLS, stimulus, turn  # noqa: E402
from v2.runner import Turn  # noqa: E402
from v2.score import accumulate, round_efficiency, score  # noqa: E402
from v2.world import ActionError, MARKET, PRODUCTION, World  # noqa: E402

ISLAND = draw_island(8, 4, seed=1)


def fresh(episodes=2) -> World:
    return World(island=draw_island(8, 4, seed=1), episodes=episodes)


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

def test_conservation_holds_across_episodes():
    w = fresh(episodes=3)
    for _ in range(3):
        stock(w)
        w.open(MARKET)
        w.check_conservation()
        w.close_episode()
    assert len(w.episode_utilities) == 3


def test_the_bell_is_not_a_decline():
    w = fresh()
    stock(w)
    w.open(MARKET)
    w.offer("T1", "T2", {"bread": 0.05}, {"cloth": 0.05})
    w.close_episode()
    assert w.expired_at_bell == 1
    assert w.declined == 0


def test_holdings_are_eaten_and_labour_returns():
    w = fresh()
    stock(w)
    total = sum(sum(t.holdings) for t in w.traders.values())
    assert total > 0
    w.close_episode()
    assert sum(sum(t.holdings) for t in w.traders.values()) == pytest.approx(0.0)
    assert sum(w.consumed) == pytest.approx(total)
    assert all(not t.produced_this_episode for t in w.traders.values())


def test_a_good_nobody_makes_zeroes_everyone():
    # The coverage coupling the design rests on, at the smallest scale that
    # shows it: three goods covered perfectly, one missing, everyone at zero.
    w = fresh()
    w.open(PRODUCTION)
    for n in w.traders:
        w.produce(n, {"bread": 0.34, "cloth": 0.33, "iron": 0.33})
    utils = w.close_episode()
    assert all(u == 0.0 for u in utils)


# --- scoring ------------------------------------------------------------

def test_scoring_refuses_a_round_with_no_closed_episode():
    with pytest.raises(ValueError):
        score(ISLAND, [])


def test_the_two_efficiencies_are_bracketed_and_count_zeros():
    w = fresh(episodes=2)
    for _ in range(2):
        stock(w)
        w.close_episode()
    s = score(ISLAND, w.episode_utilities)
    assert 0.0 <= s.eff_round <= s.eff_round_upper <= 1.0
    assert len(s.eff_episode) == 2
    assert s.agent_episodes == 16
    assert s.zero_agent_episodes == 0


def test_k_identical_episodes_score_exactly_one_episode():
    """004's homogeneity argument, which the per-round metric depends on.

    Cobb-Douglas exponents sum to 1, so utility is homogeneous of degree 1 and
    k identical episodes sit against k times the one-episode frontier. If that
    is wrong, the accumulated vector is not on the frontier's scale and the
    primary metric means nothing.
    """
    from barter.economy import autarky
    _, auto = autarky(ISLAND)
    one = score(ISLAND, [list(auto)]).eff_round
    for k in (2, 3, 5, 8):
        many = score(ISLAND, [list(auto)] * k).eff_round
        assert many == pytest.approx(one, abs=1e-6), (
            f"{k} identical episodes should score exactly one episode")


def test_accumulation_sums_each_agent_across_episodes():
    assert accumulate([[1.0, 2.0], [3.0, 4.0]]) == [4.0, 6.0]


def test_one_ruined_episode_zeroes_that_episode_but_not_the_round():
    """The reason a round-level metric exists at all.

    A single agent at zero puts an episode's vector maximally far from the
    frontier -- arithmetically correct, and why per-episode efficiency is a
    coverage measure rather than a welfare one. Accumulated over the round the
    same agent is fed four times out of five, so the round survives.
    """
    from barter.economy import autarky
    _, auto = autarky(ISLAND)
    ruined = [0.0] + list(auto[1:])
    s = score(ISLAND, [list(auto)] * 4 + [ruined])
    assert s.eff_episode[-1] == 0.0, "the ruined episode is maximally far"
    assert all(e > 0.4 for e in s.eff_episode[:4])
    assert s.eff_round > 0.4, "but the round as a whole is barely dented"
    assert s.zero_agent_episodes == 1


# --- cells --------------------------------------------------------------

def test_every_cell_is_base_plus_exactly_its_treatments():
    base = stimulus("bare", 3)
    for cell, (block, hint) in CELLS.items():
        text = stimulus(cell, 3)
        assert text.startswith(base), f"{cell} does not contain the base block"
        assert ("A shared way of talking" in text) == (block == "protocol")
        assert ("Some general advice" in text) == (block == "placebo")
        assert ("worth noticing about this island" in text) == hint


def test_the_episode_count_is_substituted_everywhere():
    assert "{periods}" not in stimulus("both", 5)
    assert "5 episodes" in stimulus("both", 5)


def test_a_turn_prompt_carries_state_inbox_and_format():
    w = fresh()
    w.post("T2", "hello everyone")
    p = turn(cell="bare", state=w.state("T1"), inbox=w.read("T1"),
             pending=w.pending("T1"), results=["produced {}"], episodes=3)
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
    monkeypatch.setattr(round_mod, "ask", stub)
    ep = run_round(island=ISLAND, cell="bare", seed=1, episodes=1, cwd=".",
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
    monkeypatch.setattr(round_mod, "ask", stub)
    ep = run_round(island=ISLAND, cell="bare", seed=1, episodes=1, cwd=".",
                     concurrency=2)
    unknown = [r for row in ep.transcript for r in row["results"]
               if "no such call" in r]
    assert not unknown, f"base.md advertises calls the executor rejects: {unknown[:3]}"


def test_memory_carries_across_episodes_inside_a_round(monkeypatch):
    """The round's whole reason for having more than one episode.

    Item stocks reset at every bell; what an agent was told does not. If the
    history block did not reach a later episode's prompt, a five-episode round
    would be five unrelated one-episode rounds and there would be nothing to
    learn.
    """
    seen: list[str] = []

    def stub(prompt, cwd):
        seen.append(prompt)
        if "production stage is open" in prompt:
            return Turn(actions=[{"call": "produce",
                                  "plan": {g: .25 for g in
                                           ("bread", "cloth", "iron", "salt")}}],
                        raw="")
        return Turn(actions=[{"call": "post", "text": "MARKER-EARLY"}], raw="")

    monkeypatch.setattr(round_mod, "ask", stub)
    run_round(island=ISLAND, cell="bare", seed=9, episodes=3, cwd=".",
              concurrency=4)
    later = [p for p in seen if "Episode 3 of 3" in p]
    assert later, "the round reached its third episode"
    assert any("What has happened so far this round" in p for p in later)
    assert any("MARKER-EARLY" in p for p in later), \
        "episode 1's talk should still be visible in episode 3"


def test_history_is_trimmed_oldest_first_and_says_so():
    from v2.prompt import HISTORY_CHARS, _history
    entries = [f"entry {i} " + "x" * 500 for i in range(200)]
    text, trimmed = _history(entries)
    assert trimmed, "200 long entries must not fit"
    assert len(text) <= HISTORY_CHARS
    assert "entry 199" in text, "the newest entry is kept"
    assert "entry 0 " not in text, "the oldest is dropped"


def test_the_stubbed_loop_completes_and_is_scorable(monkeypatch):
    def stub(prompt, cwd):
        if "production stage is open" in prompt:
            return Turn(actions=[{"call": "produce",
                                  "plan": {"bread": .25, "cloth": .25,
                                           "iron": .25, "salt": .25}}], raw="")
        return Turn(actions=[{"call": "post", "text": "hello"}], raw="")
    monkeypatch.setattr(round_mod, "ask", stub)
    ep = run_round(island=ISLAND, cell="protocol", seed=2, episodes=2,
                     cwd=".", concurrency=4)
    assert ep.outcome == "scored"
    assert len(ep.trajectory) == 2
    s = score(ISLAND, ep.trajectory)
    assert s.eff_round > 0
