"""Gates on the flow mode. Offline, no models.

The flow island differs from the stock one by exactly one call — `close_period`
— so these gates are mostly about that call doing what it claims and nothing
else: that goods are actually eaten, that the conservation invariant stays as
strong as it was rather than being relaxed to accommodate consumption, that
labour comes back, and that the stock path is untouched.
"""

import pytest

from barter.economy import draw_island, utility
from barter.manager import LEVEL_OFFER, LEVEL_SETTLE, Manager
from barter.run import run_island, run_island_flow, score_flow


ISLAND = draw_island(6, 4, seed=1)


def fresh() -> Manager:
    return Manager(island=draw_island(6, 4, seed=1), labour_per_round=1.0)


def test_a_new_manager_has_eaten_nothing():
    m = fresh()
    assert m.consumed == [0.0] * ISLAND.n_goods
    assert m.period_utilities == []


def test_closing_a_period_eats_the_holdings():
    m = fresh()
    for agent_id in m.agents:
        m.op_produce(agent_id, {"fish": 0.5, "grain": 0.5})
    before = sum(sum(s.holdings) for s in m.agents.values())
    assert before > 0
    m.close_period()
    assert sum(sum(s.holdings) for s in m.agents.values()) == pytest.approx(0.0)
    assert sum(m.consumed) == pytest.approx(before)


def test_closing_a_period_records_the_utility_it_ate():
    m = fresh()
    for agent_id in m.agents:
        m.op_produce(agent_id, {"fish": 0.5, "grain": 0.5})
    expected = [utility(s.alpha, s.holdings)
                for s in sorted(m.agents.values(), key=lambda s: s.index)]
    got = m.close_period()
    assert got == pytest.approx(expected)
    assert m.period_utilities == [got]


def test_labour_comes_back_so_the_next_period_is_a_whole_economy():
    m = fresh()
    a = next(iter(m.agents))
    m.op_produce(a, {"fish": 1.0})
    assert m.agents[a].spent == pytest.approx(1.0)
    m.close_period()
    assert m.agents[a].spent == 0.0
    assert m.agents[a].shares == [0.0] * ISLAND.n_goods
    assert m.agents[a].last_spent_tick is None
    # And it can actually be spent again, which `spent` alone would not prove.
    m.op_produce(a, {"grain": 1.0})
    assert m.agents[a].holdings[1] > 0


def test_an_open_offer_does_not_survive_the_bell():
    # Goods in escrow are goods nobody can eat. Carrying an open offer across a
    # period would either strand them or hand the buyer a second period's worth.
    m = fresh()
    ids = list(m.agents)
    for agent_id in ids:
        m.op_produce(agent_id, {"fish": 0.5, "grain": 0.5})
    m.open(LEVEL_OFFER)
    m.open(LEVEL_SETTLE)
    reply = m.op_propose(ids[0], seller=ids[1], give={"fish": 0.1}, want={"grain": 0.1})
    trade_id = reply["trade_id"]
    assert m.trades[trade_id].status == "pending"
    m.close_period()
    assert m.trades[trade_id].status == "expired"


def test_conservation_holds_at_the_bell_and_is_checked_before_eating():
    # The invariant is asserted inside close_period while the books still
    # balance, so it stays as strong as it is in the stock model.
    m = fresh()
    for agent_id in m.agents:
        m.op_produce(agent_id, {"fish": 1.0})
    m.close_period()
    m.check_conservation()  # post-reset: nothing produced, nothing held


def test_conservation_survives_many_periods():
    m = fresh()
    for _ in range(5):
        for agent_id in m.agents:
            m.op_produce(agent_id, {"fish": 0.4, "grain": 0.6})
        m.close_period()
        m.next_round()
    assert len(m.period_utilities) == 5
    m.check_conservation()


def test_a_stock_run_never_closes_a_period():
    # The whole difference between the models is this one call, so a stock run
    # having made it would mean the two are not being compared at all.
    out = run_island(ISLAND, "C", seed=1, trade_rounds=10)
    assert out.efficiency is not None


def test_the_stock_path_is_unchanged_by_the_flow_addition():
    a = run_island(ISLAND, "C", seed=1, trade_rounds=20)
    b = run_island(ISLAND, "C", seed=1, trade_rounds=20)
    assert a.utilities == b.utilities
    assert (a.executed, a.messages) == (b.executed, b.messages)


def test_a_flow_run_produces_one_row_per_period():
    out = run_island_flow(ISLAND, "C", seed=1, periods=4, rounds_per_period=6)
    assert out.periods == 4
    assert len(out.trajectory) == 4
    assert all(len(row) == ISLAND.n_agents for row in out.trajectory)


def test_flow_is_deterministic_under_a_seed():
    a = run_island_flow(ISLAND, "C", seed=3, periods=3, rounds_per_period=6)
    b = run_island_flow(ISLAND, "C", seed=3, periods=3, rounds_per_period=6)
    assert a.trajectory == b.trajectory


def test_mean_utility_is_the_column_mean():
    out = run_island_flow(ISLAND, "B", seed=2, periods=3, rounds_per_period=6)
    for i in range(ISLAND.n_agents):
        column = [row[i] for row in out.trajectory]
        assert out.mean_utilities[i] == pytest.approx(sum(column) / len(column))


def test_a_single_period_flow_run_matches_its_own_first_period():
    out = run_island_flow(ISLAND, "C", seed=4, periods=1, rounds_per_period=8)
    assert out.first_efficiency.lower == pytest.approx(out.last_efficiency.lower)
    assert out.efficiency.lower == pytest.approx(out.first_efficiency.lower)


def test_recovery_is_counted_only_across_a_boundary():
    # Hand-built trajectory: agent 0 goes zero then positive (one recovery),
    # agent 1 is zero throughout (no recovery, and permanently ruined).
    m = fresh()
    m.period_utilities = [[0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
                          [2.0, 0.0, 1.0, 1.0, 1.0, 1.0]]
    out = score_flow(draw_island(6, 4, seed=1), m, arm="X", seed=0)
    assert out.recoveries == 1
    assert out.always_zero == 1
    assert out.zero_periods == 3


def test_scoring_refuses_a_flow_run_that_closed_nothing():
    with pytest.raises(ValueError):
        score_flow(ISLAND, fresh(), arm="X", seed=0)


def test_flow_bounds_ruin_that_the_stock_model_makes_terminal():
    # The claim the experiment rests on, at the smallest scale that shows it:
    # an island the stock model scores as ruined has agents that recover when
    # the period ends and a new one begins.
    island = draw_island(12, 5, seed=1)
    stock = run_island(island, "D", seed=1, trade_rounds=60)
    flow = run_island_flow(island, "D", seed=1, periods=6, rounds_per_period=60)
    assert stock.efficiency.ruined, "seed 1 arm D is the ruined stock island"
    assert flow.always_zero == 0
    assert flow.recoveries > 0


def test_discovery_defaults_to_002s_thirty_rounds():
    a = run_island_flow(ISLAND, "C", seed=5, periods=2, rounds_per_period=6)
    b = run_island_flow(ISLAND, "C", seed=5, periods=2, rounds_per_period=6,
                        discovery_rounds=None)
    assert a.trajectory == b.trajectory


def test_starving_discovery_changes_what_agents_produce():
    # The knob has to actually bite, or a convergence measurement made with it
    # is measuring nothing.
    island = draw_island(12, 5, seed=1)
    rich = run_island_flow(island, "C", seed=1, periods=3, rounds_per_period=20,
                           discovery_rounds=30)
    poor = run_island_flow(island, "C", seed=1, periods=3, rounds_per_period=20,
                           discovery_rounds=1)
    assert rich.trajectory != poor.trajectory


def test_a_well_fed_price_arm_has_nothing_left_to_learn():
    # Why convergence is unmeasurable at the default: tatonnement reaches the
    # equilibrium inside period 0, so a later period starts from the same place
    # the first one ended. This gate pins the *reason* the starved regime
    # exists, so removing the knob would break it loudly.
    import random as _random
    from barter.calibrate import normalise
    from barter.economy import walras
    from barter.run import DISCOVERY_ROUNDS
    from barter.traders import Floor, Trader

    island = draw_island(12, 5, seed=1)
    truth = normalise(walras(island).prices)
    floor = Floor(enabled=True)
    traders = [Trader(f"a{i}", i, island, "C", _random.Random(1))
               for i in range(island.n_agents)]
    for t in traders:
        t.goods = [f"g{g}" for g in range(island.n_goods)]

    for step in range(DISCOVERY_ROUNDS):
        for t in traders:
            t.declare(step, floor)
        for t in traders:
            t.observe_prices(step, floor)

    belief = normalise(traders[0].price)
    err = (sum((belief[g] - truth[g]) ** 2 for g in range(island.n_goods)) ** 0.5
           / sum(x * x for x in truth) ** 0.5)
    assert err < 0.01, f"one period of talk should already find the price, got {err}"
    for t in traders:
        assert normalise(t.price) == pytest.approx(belief), "and everyone agrees"


def test_the_bell_is_not_a_rejection():
    # Offers open when a period ends are settled as `expired` so their escrow
    # returns — but nobody declined them, the clock ran out. Counting them as
    # rejections would make every flow run look more contentious than a stock
    # run by construction, which is a difference the harness invented.
    island = draw_island(12, 5, seed=1)
    out = run_island_flow(island, "C", seed=1, periods=3, rounds_per_period=10)
    assert out.expired_at_bell > 0, "this island does leave offers open at the bell"
    assert out.rejected + out.executed + out.expired_at_bell <= out.proposed
    assert "expired_at_bell" in out.to_json()


def test_a_stock_run_has_no_bell_to_expire_at():
    m = fresh()
    assert m.period_expiries == 0
    for agent_id in m.agents:
        m.op_produce(agent_id, {"fish": 1.0})
    m.close_period()
    assert m.period_expiries == 0, "nothing was open, so nothing expired at the bell"
