"""The heuristic players, offline: no hub, no processes, no clock.

Everything here is `npc.py` alone, because that is where the decisions are.
`run_npc.py` carries the lines to a board and is tested against a real hub in
`test_run_npc.py`.
"""

from __future__ import annotations

import json
import random

import pytest

from games.island import npc


def _manager_parser():
    """The island manager's own `parse`, imported the way `run_game.py` does.

    Not a copy of it and not a re-implementation: the claim under test is that
    what an NPC writes is what the manager reads, and only the manager's
    parser can settle that.
    """
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "experiments" / "005-deliberation-protocol"))
    from island.protocol import parse
    return parse


def _dealt(seat: str, player: str, cap: dict, taste: dict) -> str:
    """The dealer's own words, as `run_game.deal` posts them in the clear."""
    return (f"@{seat} ({player}) You are {seat}. Your production capacity per "
            f"unit of labour: {cap}. Your taste weights: {taste}. Nobody else "
            f"knows either.")


def _seated(player="npc-1", seat="T2", cap=None, taste=None,
            partner="T1") -> npc.Board:
    board = npc.Board(player=player)
    board.read(f"Schedule for this round. 2 traders: {partner}, {seat}. "
               f"8 episodes, 60s each. Acknowledge with a line beginning ACK, "
               f"by 12:00:00Z.")
    board.read(_dealt(seat, player,
                      cap or {"bread": 0.9, "iron": 0.2},
                      taste or {"bread": 0.3, "iron": 0.7}))
    board.read("episode 1 of 8 is open; the bell is at 12:01:00Z (60s).")
    return board


# --- the mix ---------------------------------------------------------------

def test_a_mix_is_normalised_and_a_typo_in_it_is_refused():
    assert npc.parse_mix("autarky=1,greedy=1") == {"autarky": 0.5, "greedy": 0.5}
    assert npc.parse_mix("greedy=2") == {"greedy": 1.0}
    with pytest.raises(npc.BadMix):
        npc.parse_mix("gready=1")          # not repaired into `greedy`
    with pytest.raises(npc.BadMix):
        npc.parse_mix("greedy")
    with pytest.raises(npc.BadMix):
        npc.parse_mix("greedy=0")


def test_the_marginal_distribution_over_time_is_the_mix():
    """The reason redraws are independent rather than "not the same again":
    a scheme that avoided repeats would make 0.5 mean something other than
    half the time, and nobody reading the mix would know."""
    schedule = npc.PolicySchedule(mix={"autarky": 0.25, "greedy": 0.75},
                                  seed=11, mean_seconds=5.0)
    drawn = [schedule.policy_at(t / 10) for t in range(200_00)]
    share = drawn.count("greedy") / len(drawn)
    assert 0.65 < share < 0.85


def test_a_schedule_is_reproducible_and_never_answers_twice_about_one_moment():
    a = npc.PolicySchedule(mix=dict(npc.DEFAULT_MIX), seed=4, mean_seconds=3.0)
    b = npc.PolicySchedule(mix=dict(npc.DEFAULT_MIX), seed=4, mean_seconds=3.0)
    times = [0.0, 1.5, 7.25, 40.0, 3.0, 120.0, 7.25]
    assert [a.policy_at(t) for t in times] == [b.policy_at(t) for t in times]
    # Asked out of order, and the answer for 7.25 is the same both times.
    assert a.policy_at(7.25) == b.policy_at(7.25)
    assert a.trace() == b.trace()
    assert [seg["policy"] for seg in a.trace()][0] == a.policy_at(0.0)


def test_a_dwell_time_of_zero_is_refused_rather_than_spinning():
    with pytest.raises(npc.BadMix):
        npc.PolicySchedule(mean_seconds=0.0)


# --- what it declares ------------------------------------------------------

def test_a_declaration_is_readable_off_a_board_afterwards():
    line = npc.declaration("npc-1", npc.parse_mix("autarky=1,greedy=3"))
    found = npc.npcs_on_board([{"body": line}, {"body": "PRODUCE bread=1"}])
    assert found == {"npc-1": "autarky=0.25, greedy=0.75"}


def test_quoting_somebody_elses_declaration_does_not_make_you_one():
    """It is anchored, so a trader repeating the line back -- which is exactly
    what an agent that learns by reading the room does -- does not unrank a
    game by accident, and does not name a seat that never played."""
    line = npc.declaration("npc-1", npc.DEFAULT_MIX)
    assert npc.npcs_on_board([{"body": f"I see that: {line}"}]) == {}
    assert npc.npcs_on_board([{"body": None}, {"body": 3}]) == {}


# --- reading the board -----------------------------------------------------

def test_a_practice_board_carries_everyones_half_and_only_ours_is_ours():
    """The failure this prevents is the worst one available: a trader playing
    the whole round against somebody else's tastes."""
    board = npc.Board(player="npc-1")
    board.read(_dealt("T1", "scout-v2", {"bread": 0.1}, {"bread": 1.0}))
    assert board.seat == ""          # not ours; the manager said whose it was
    board.read(_dealt("T2", "npc-1", {"bread": 0.4, "iron": 0.6},
                      {"bread": 0.25, "iron": 0.75}))
    assert board.seat == "T2"
    assert board.tastes == {"bread": 0.25, "iron": 0.75}


def test_a_sealed_half_arrives_with_no_address_and_is_ours_by_having_arrived():
    board = npc.Board(player="npc-1")
    board.read("You are T1. Your production capacity per unit of labour: "
               "{'bread': 0.4}. Your taste weights: {'bread': 1.0}. Nobody "
               "else knows either. You are seated here as npc-1.", mine=True)
    assert board.seat == "T1" and board.capacity == {"bread": 0.4}


def test_holdings_come_from_the_managers_receipts_and_the_bell_eats_them():
    board = _seated()
    board.read("@T2 produced {'bread': 0.45, 'iron': 0.14}; 0.0 labour unspent")
    assert board.held("bread") == pytest.approx(0.45)
    assert board.produced_this_episode and board.labour_left == 0.0
    board.read("p1: T1 offers {'iron': 0.2} to T2 for {'bread': 0.1} — open "
               "until the bell. T2 takes it by writing exactly: APPROVE p1")
    assert list(board.inbox) == ["p1"]
    board.read("p1 settled: T1 and T2 exchanged {'iron': 0.2} for {'bread': 0.1}")
    assert board.held("iron") == pytest.approx(0.34)
    assert board.held("bread") == pytest.approx(0.35)
    assert board.inbox == {}
    board.read("episode 2 of 8 is open; the bell is at 12:02:00Z (60s).")
    assert board.held("bread") == 0.0 and board.labour_left == 1.0


def test_a_receipt_for_another_seat_changes_nothing_here():
    board = _seated()
    board.read("@T1 produced {'bread': 9.0}; 0.0 labour unspent")
    assert board.held("bread") == 0.0 and not board.produced_this_episode


def test_a_bundle_that_is_not_one_is_ignored_rather_than_evaluated():
    """These strings arrived over a board anybody can write to."""
    board = _seated()
    board.read("@T2 produced {__import__('os').system('x')}; 0.0 labour unspent")
    assert board.held("bread") == 0.0


# --- the policies ----------------------------------------------------------

def test_autarky_spends_its_labour_in_the_proportions_of_its_tastes():
    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    assert npc.lines("autarky", board, ["T1"]) == ["PRODUCE bread=0.3 iron=0.7"]


def test_autarky_never_trades_however_good_the_offer_and_says_so_at_once():
    """It will not trade at any holdings, so there is no state of the world in
    which it would take this. Sitting on the offer would keep the maker's goods
    escrowed until the bell for nothing -- a no told by silence."""
    board = _seated()
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    board.read("p1: T1 offers {'iron': 5.0} to T2 for {'bread': 0.01} — open "
               "until the bell. T2 takes it by writing exactly: APPROVE p1")

    assert npc.lines("autarky", board, ["T1"]) == ["DECLINE p1"]
    assert not any(l.startswith("APPROVE")
                   for l in npc.lines("autarky", board, ["T1"]))


def test_greedy_takes_an_offer_that_helps_and_leaves_one_that_does_not():
    board = _seated()
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    good = npc.Offer("p1", "T1", "T2", {"iron": 0.3}, {"bread": 0.05})
    bad = npc.Offer("p2", "T1", "T2", {"iron": 0.001}, {"bread": 0.2})
    assert npc.approve("greedy", board, good)
    assert not npc.approve("greedy", board, bad)


def test_no_policy_approves_what_it_cannot_pay_for():
    """The manager refuses it with a reason, and an NPC that spends the round
    collecting refusals is noise on somebody else's board."""
    board = _seated()
    board.read("@T2 produced {'bread': 0.1, 'iron': 0.1}; 0.0 labour unspent")
    beyond = npc.Offer("p1", "T1", "T2", {"iron": 9.0}, {"bread": 5.0})
    assert not any(npc.approve(p, board, beyond) for p in npc.POLICIES)


def test_greedy_offers_what_it_has_most_of_for_what_it_wants_most():
    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    board.read("@T2 produced {'bread': 0.9, 'iron': 0.02}; 0.0 labour unspent")
    partner, give, want = npc.propose("greedy", board, ["T1"])
    assert partner == "T1" and list(give) == ["bread"] and list(want) == ["iron"]


def test_a_price_taker_with_no_market_to_read_specialises_by_capacity():
    board = _seated(cap={"bread": 0.9, "iron": 0.2})
    assert npc.lines("price-taker", board, ["T1"]) == ["PRODUCE bread=1.0"]


def test_a_price_taker_learns_only_from_exchanges_that_settled():
    board = _seated()
    board.read("p9: T1 offers {'iron': 1.0} to T3 for {'bread': 4.0} — open "
               "until the bell.")
    assert board.prices == {}                 # an offer is not a price
    board.read("p9 settled: T1 and T3 exchanged {'iron': 1.0} for {'bread': 4.0}")
    assert board.prices["bread"] < board.prices["iron"]


def test_a_price_taker_follows_the_price_into_the_good_it_is_worse_at():
    """The whole case for trading, as a policy: iron is dearer than bread by
    enough that the seat's larger bread capacity stops being worth using."""
    board = _seated(cap={"bread": 0.9, "iron": 0.2})
    board.read("p9 settled: T1 and T3 exchanged {'iron': 1.0} for {'bread': 9.0}")
    assert npc.lines("price-taker", board, ["T1"]) == ["PRODUCE iron=1.0"]


def test_a_price_taker_will_not_pay_over_its_own_prices():
    board = _seated()
    board.read("@T2 produced {'bread': 0.9, 'iron': 0.02}; 0.0 labour unspent")
    board.read("p9 settled: T1 and T3 exchanged {'iron': 1.0} for {'bread': 2.0}")
    dear = npc.Offer("p1", "T1", "T2", {"iron": 0.1}, {"bread": 0.8})
    fair = npc.Offer("p2", "T1", "T2", {"iron": 0.1}, {"bread": 0.2})
    assert not npc.approve("price-taker", board, dear)
    assert npc.approve("price-taker", board, fair)


# --- what it writes --------------------------------------------------------

def test_every_line_it_writes_is_one_the_manager_parses():
    """The point of the whole exercise: an NPC has no way to act that is not a
    line somebody could have typed, so the manager's own parser is the test."""
    parse = _manager_parser()

    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    written = []
    for policy in npc.POLICIES:
        written += npc.lines(policy, board, ["T1"])
    board.read("@T2 produced {'bread': 0.9, 'iron': 0.02}; 0.0 labour unspent")
    board.read("p1: T1 offers {'iron': 0.4} to T2 for {'bread': 0.1} — open "
               "until the bell.")
    for policy in npc.POLICIES:
        written += npc.lines(policy, board, ["T1"])
    assert written
    for line in written:
        assert parse(line) is not None, line


def test_nothing_is_written_before_the_episode_opens_or_after_the_bell():
    board = _seated()
    board.read("the round is over. Stop; nothing further will settle.")
    assert npc.lines("greedy", board, ["T1"]) == []

    unopened = npc.Board(player="npc-1")
    unopened.read(_dealt("T1", "npc-1", {"bread": 0.4}, {"bread": 1.0}))
    assert npc.lines("greedy", unopened, []) == []


def test_it_does_not_produce_twice_on_one_receipt():
    board = _seated()
    assert npc.lines("greedy", board, ["T1"])[0].startswith("PRODUCE")
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.63}; 0.0 labour unspent")
    assert not any(l.startswith("PRODUCE")
                   for l in npc.lines("greedy", board, ["T1"]))


def test_it_does_not_promise_the_same_unit_to_two_partners():
    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    board.read("@T2 produced {'bread': 0.9, 'iron': 0.02}; 0.0 labour unspent")
    first = npc.lines("greedy", board, ["T1"])
    assert first and first[0].startswith("PROPOSE")
    board.read("p4: T2 offers {'bread': 0.225} to T1 for {'iron': 0.5} — open "
               "until the bell.")
    assert npc.lines("greedy", board, ["T1"]) == []
    assert board.free("bread") == pytest.approx(0.675)


def test_a_quantity_is_never_written_in_exponent_form():
    """`PRODUCE` and `PROPOSE` both parse digits and at most one dot, so
    `1e-05` is a malformed line rather than a small one."""
    assert "e" not in npc._num(0.00001)
    assert npc._num(0.25) == "0.25" and npc._num(1.0) == "1.0"


def test_the_trace_is_json_and_says_which_policy_was_live_when():
    schedule = npc.PolicySchedule(mix=dict(npc.DEFAULT_MIX), seed=3,
                                  mean_seconds=10.0)
    schedule.policy_at(95.0)
    trace = schedule.trace()
    assert len(trace) > 3
    assert [seg["at"] for seg in trace] == sorted(seg["at"] for seg in trace)
    json.dumps(trace)


def test_a_plan_written_once_is_not_written_again_while_the_receipt_travels():
    """Labour may be committed in pieces, so the manager settles a second
    PRODUCE rather than refusing it. A seat that re-decided every poll until
    its receipt came back therefore spent its budget several times over --
    which is what the first real sealed round did, three times in one episode.
    """
    board = _seated()
    plan = npc.lines("greedy", board, ["T1"])
    assert plan and plan[0].startswith("PRODUCE")
    npc.wrote(board, plan[0])
    assert npc.lines("greedy", board, ["T1"]) == []

    # The receipt arrives late and changes nothing; the next episode re-arms.
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    assert not any(l.startswith("PRODUCE")
                   for l in npc.lines("greedy", board, ["T1"]))
    board.read("episode 2 of 8 is open; the bell is at 12:02:00Z (60s).")
    assert npc.lines("greedy", board, ["T1"])[0].startswith("PRODUCE")


def test_an_offer_written_once_is_not_written_again_either():
    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    board.read("@T2 produced {'bread': 0.9, 'iron': 0.02}; 0.0 labour unspent")
    offer = npc.lines("greedy", board, ["T1"])
    assert offer and offer[0].startswith("PROPOSE")
    npc.wrote(board, offer[0])
    assert npc.lines("greedy", board, ["T1"]) == []


def test_no_plan_any_taste_vector_produces_is_ever_over_the_budget():
    """The refusal is total -- the manager rejects the whole line, not the
    excess -- so a plan over by 1e-4 is a plan that produces nothing. One seat
    wrote exactly that every poll for a whole round: fifteen refusals, zero
    utility, while its partner's shares happened to round down and it played
    normally.
    """
    parse = _manager_parser()
    rng = random.Random(5)
    for _ in range(2000):
        raw = [rng.random() for _ in range(rng.randint(2, 7))]
        total = sum(raw)
        tastes = {g: v / total for g, v in
                  zip(("bread", "cloth", "iron", "salt", "fish", "a", "b"), raw)}
        board = npc.Board(player="npc-1", tastes=tastes,
                          capacity={g: 1.0 for g in tastes},
                          episode_open=True)
        for policy in npc.POLICIES:
            for line in npc.lines(policy, board, []):
                action = parse(line)
                assert sum(action.plan.values()) <= 1.0 + 1e-9, line


def test_the_awkward_vector_from_the_first_real_round():
    """0.136 + 0.8595 + 0.0046 sums to 1 and rounds to 1.0001."""
    board = _seated(taste={"bread": 0.136, "cloth": 0.8595, "iron": 0.0046},
                    cap={"bread": 1.0, "cloth": 1.0, "iron": 1.0})
    plan = _manager_parser()(npc.lines("autarky", board, ["T1"])[0])
    assert sum(plan.plan.values()) <= 1.0


# --- DECLINE: the offer's other ending -------------------------------------

def test_a_trading_policy_waits_until_it_has_produced_before_saying_no():
    """Before production a seat holds almost nothing and would refuse offers it
    would gladly take a moment later. The cost of declining late is escrow held
    a few seconds longer; the cost of declining early is a trade that should
    have happened and now cannot."""
    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    board.read("p1: T1 offers {'bread': 0.001} to T2 for {'iron': 0.9} — open "
               "until the bell.")

    assert npc.declines("greedy", board) == [], "it has not produced yet"
    assert npc.lines("greedy", board, ["T1"])[0].startswith("PRODUCE")

    board.read("@T2 produced {'bread': 0.27, 'iron': 0.63}; 0.0 labour unspent")
    assert npc.declines("greedy", board) == ["DECLINE p1"]


def test_an_offer_worth_taking_is_approved_and_never_declined():
    board = _seated()
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    board.read("p1: T1 offers {'iron': 0.3} to T2 for {'bread': 0.05} — open "
               "until the bell.")

    assert npc.declines("greedy", board) == []
    assert npc.lines("greedy", board, ["T1"]) == ["APPROVE p1"]


def test_a_decline_is_written_once_while_the_receipt_travels():
    board = _seated()
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    board.read("p1: T1 offers {'iron': 0.001} to T2 for {'bread': 0.2} — open "
               "until the bell.")

    said = npc.lines("greedy", board, ["T1"])
    assert said == ["DECLINE p1"]
    npc.wrote(board, said[0])
    assert npc.declines("greedy", board) == []


def test_the_managers_decline_receipt_frees_this_seats_own_escrow():
    """The goods never moved, so no holding changes -- what comes back is what
    an open offer had committed. A maker that could not see that would size its
    next offer against goods it still believes are promised away."""
    board = _seated(taste={"bread": 0.3, "iron": 0.7})
    board.read("@T2 produced {'bread': 0.9, 'iron': 0.02}; 0.0 labour unspent")
    offer = npc.lines("greedy", board, ["T1"])[0]
    assert offer.startswith("PROPOSE")
    board.read("p4: T2 offers {'bread': 0.225} to T1 for {'iron': 0.5} — open "
               "until the bell.")
    assert board.free("bread") == pytest.approx(0.675), "escrowed while open"

    board.read("p4 declined: T1 will not take T2's offer; "
               "{'bread': 0.225} is free again")

    assert board.free("bread") == pytest.approx(0.9), "and free again after"
    assert board.outstanding == {}


def test_a_decline_is_a_line_the_manager_parses():
    parse = _manager_parser()
    board = _seated()
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    board.read("p7: T1 offers {'iron': 0.001} to T2 for {'bread': 0.2} — open "
               "until the bell.")

    written = npc.lines("greedy", board, ["T1"])
    assert written == ["DECLINE p7"]
    assert parse(written[0]).proposal_id == "p7"


def test_the_bell_forgets_what_was_declined():
    board = _seated()
    board.read("@T2 produced {'bread': 0.27, 'iron': 0.14}; 0.0 labour unspent")
    board.read("p1: T1 offers {'iron': 0.001} to T2 for {'bread': 0.2} — open "
               "until the bell.")
    npc.wrote(board, "DECLINE p1")
    assert board.posted_decline == {"p1"}

    board.read("episode 2 of 8 is open; the bell is at 12:02:00Z (60s).")
    assert board.posted_decline == set() and board.inbox == {}
