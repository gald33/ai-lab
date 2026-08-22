"""Gates on the board, the message protocol and the manager. Offline, no models.

These test the three things the design says the system may do -- timing, format
and scoring -- and one thing it must never do: repair a malformed message into
a plausible one.
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island  # noqa: E402
from island.manager import MANAGER, Manager  # noqa: E402
from island.protocol import (Approve, Malformed, Produce,  # noqa: E402
                             Propose, parse)
from island.score import score  # noqa: E402


class FakeHub:
    """A stand-in for the Switchboard client, so the gates stay offline.

    It implements exactly the two calls the manager makes -- ``post`` and
    ``history`` -- and returns rows shaped like the hub's. Testing the manager
    against the real hub would be testing Switchboard, which is not this
    experiment's code and has its own tests.
    """

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def post(self, channel: str, body: str) -> None:
        self.rows.append({"id": f"msg-{len(self.rows)}", "seq": len(self.rows),
                          "channel": channel, "from": MANAGER, "body": body})

    def envelope(self, who: str, text: str) -> None:
        """A `say` that carried a timing forecast: the body is an envelope."""
        self.rows.append({"id": f"msg-{len(self.rows)}", "seq": len(self.rows),
                          "channel": "c", "from": who,
                          "body": {"text": text,
                                   "timing_forecast": {"p50": "2026-01-01T00:00:00Z"}}})

    def as_(self, who: str, body: str) -> None:
        self.rows.append({"id": f"msg-{len(self.rows)}", "seq": len(self.rows),
                          "channel": "c", "from": who, "body": body})

    def history(self, channel: str, *, limit: int = 50, **kw) -> list[dict]:
        return list(self.rows)

ISLAND = draw_island(2, 4, seed=1)
GOODS = ("bread", "cloth", "iron", "salt")
EVEN = "PRODUCE bread=0.25 cloth=0.25 iron=0.25 salt=0.25"


def fresh() -> Manager:
    hub = FakeHub()
    m = Manager(island=draw_island(2, 4, seed=1), client=hub, channel="c")
    for n in m.names:
        m.bind(n, n)
    m.hub = hub  # type: ignore[attr-defined]
    # An episode starts shut, so the acknowledgement window cannot become part
    # of episode 1. Every test below acts inside an open episode; the ones
    # about the bell shut it themselves.
    m.open_episode()
    return m


# --- format -------------------------------------------------------------

def test_talk_is_not_an_action():
    assert parse("shall we each take two goods?") is None
    assert parse("") is None


def test_the_three_shapes_parse():
    assert parse("PRODUCE bread=0.5 iron=0.5") == Produce({"bread": .5, "iron": .5})
    assert parse("PROPOSE to=T2 give=iron:0.4 want=salt:0.3") == Propose(
        "T2", {"iron": 0.4}, {"salt": 0.3})
    assert parse("APPROVE p3") == Approve("p3")


@pytest.mark.parametrize("bad", [
    "PRODUCE bread", "PRODUCE", "PRODUCE bread=", "PRODUCE bread=-0.5",
    "PROPOSE to=T2 give=iron:0.4",
    "PROPOSE to=T2 give=bread:0.02 cloth:0.15 want=salt:0.4", "PROPOSE give=iron:0.4 want=salt:0.3",
    "PROPOSE to=T2 give=iron want=salt:0.3",
    "PROPOSE to=T2 give=iron:0 want=salt:0.3",
    "APPROVE", "APPROVE p1 p2",
])
def test_a_near_miss_is_malformed_and_never_guessed(bad):
    with pytest.raises(Malformed):
        parse(bad)


def test_the_manager_says_why_rather_than_repairing():
    m = fresh()
    m.hub.as_("T1", "PRODUCE bread")
    m.drain()
    assert m.refused == 1 and m.settled == 0
    assert not m.holders["T1"].produced, "nothing was invented on the agent's behalf"
    assert any(r["from"] == MANAGER and "not settled" in r["body"]
               for r in m.hub.history("c"))


# --- timing -------------------------------------------------------------

def test_nothing_from_a_closed_episode_settles():
    m = fresh()
    m.episode_open = False
    m.hub.as_("T1", EVEN)
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.1 want=salt:0.1")
    m.drain()
    assert m.refused == 2 and not m.holders["T1"].produced


def test_an_episode_has_no_stages_inside_it():
    """Producing and dealing settle in the same window, in either order.

    The clock divides episodes from each other and nothing else. An earlier
    version split each episode into a production window and a market window,
    and agents in every arm spent their first offers being refused for
    proposing "too early" -- a rule they had been told and still read as the
    episode simply having begun.
    """
    m = fresh()
    for n in m.names:
        m.hub.as_(n, EVEN)
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.05 want=salt:0.05")
    m.hub.as_("T2", "APPROVE p1")
    m.drain()
    assert m.refused == 0
    assert m.settled == 4
    assert m.proposals["p1"].status == "settled"


def test_producing_twice_in_one_episode_is_refused():
    m = fresh()
    m.hub.as_("T1", EVEN)
    m.hub.as_("T1", "PRODUCE bread=1.0")
    m.drain()
    assert m.settled == 1 and m.refused == 1


def test_the_labour_budget_is_enforced():
    m = fresh()
    m.hub.as_("T1", "PRODUCE bread=0.7 iron=0.7")
    m.drain()
    assert m.refused == 1


# --- exchange -----------------------------------------------------------

def stocked() -> Manager:
    m = fresh()
    for n in m.names:
        m.hub.as_(n, EVEN)
    m.drain()
    return m


def test_an_open_proposal_commits_the_goods_it_offers():
    m = stocked()
    free = m._free("T1", "bread")
    m.hub.as_("T1", f"PROPOSE to=T2 give=bread:{free:.4f} want=salt:0.1")
    m.drain()
    m.hub.as_("T1", f"PROPOSE to=T2 give=bread:{free:.4f} want=iron:0.1")
    m.drain()
    assert m.refused == 1, "the same goods cannot back two open proposals"


def test_a_trader_cannot_approve_its_own_proposal():
    """The mistake that cost two arms a whole round.

    T1 offered to T2 and then approved its own offer, twice, in different
    episodes, while T2's genuine offers sat open and lapsed at the bell. Making
    an offer and taking it yourself is not a trade, and the refusal has to say
    so rather than quietly doing nothing.
    """
    m = stocked()
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.05 want=salt:0.05")
    m.drain()
    m.hub.as_("T1", "APPROVE p1")
    m.drain()
    assert m.refused == 1
    assert m.proposals["p1"].status == "open", "and it stays takeable by T2"
    m.hub.as_("T2", "APPROVE p1")
    m.drain()
    assert m.proposals["p1"].status == "settled"


def test_your_own_open_proposal_can_leave_you_short_to_approve():
    """The other half of that round: escrow blindness.

    T1 tried to approve an offer it could not pay for, because its own open
    proposal was holding the goods. The refusal names the shortfall, which is
    the only way an agent can tell this apart from having produced too little.
    """
    m = stocked()
    free = m._free("T1", "bread")
    m.hub.as_("T1", f"PROPOSE to=T2 give=bread:{free:.4f} want=cloth:0.01")
    m.drain()
    m.hub.as_("T2", "PROPOSE to=T1 give=cloth:0.02 want=bread:0.02")
    m.drain()
    m.hub.as_("T1", "APPROVE p2")
    m.drain()
    assert m.refused == 1
    said = [r["body"] for r in m.hub.history("c") if "uncommitted" in r["body"]]
    assert said, "the refusal must name the shortfall"


def test_only_the_addressee_can_approve():
    m = stocked()
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.05 want=salt:0.05")
    m.drain()
    m.hub.as_("T1", "APPROVE p1")
    m.drain()
    assert m.refused == 1
    assert m.proposals["p1"].status == "open"


def test_approving_moves_goods_both_ways_and_settles_once():
    m = stocked()
    b1 = m._free("T1", "bread")
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.05 want=salt:0.04")
    m.drain()
    m.hub.as_("T2", "APPROVE p1")
    m.drain()
    assert m.proposals["p1"].status == "settled"
    assert m._free("T1", "bread") == pytest.approx(b1 - 0.05)
    assert m._free("T1", "salt") > 0
    m.hub.as_("T2", "APPROVE p1")
    m.drain()
    assert m.refused == 1


# --- the bell -----------------------------------------------------------

def test_open_proposals_lapse_at_the_bell_and_holdings_are_eaten():
    m = stocked()
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.05 want=salt:0.05")
    m.drain()
    m.close_episode()
    assert m.proposals["p1"].status == "lapsed"
    assert all(sum(h.holdings) == 0 for h in m.holders.values())
    assert all(not h.produced for h in m.holders.values())
    assert len(m.episode_utilities) == 1


def test_a_good_nobody_makes_zeroes_everyone():
    m = fresh()
    for n in m.names:
        m.hub.as_(n, "PRODUCE bread=0.34 cloth=0.33 iron=0.33")
    m.drain()
    assert all(u == 0.0 for u in m.close_episode())


def test_a_message_carrying_a_timing_forecast_is_still_read():
    """Switchboard wraps a `say` that carries a forecast; the text is inside.

    Two rounds reported 1/2 acknowledged because a trader's ACK arrived as an
    envelope and the manager stringified the whole dict. Every match against it
    failed silently -- an action that never settled and never refused.
    """
    m = fresh()
    m.hub.envelope("T1", "ACK ready")
    m.hub.envelope("T2", EVEN)
    m.drain()
    assert m.acknowledged == {"T1"}
    assert m.holders["T2"].produced, "a wrapped PRODUCE must settle like a bare one"
    assert m.refused == 0


def test_an_acknowledgement_is_just_a_board_line():
    m = fresh()
    m.hub.as_("T1", "ACK — schedule understood")
    m.drain()
    assert m.acknowledged == {"T1"}
    assert m.settled == 0, "acknowledging is not an economic action"


# --- scoring ------------------------------------------------------------

def test_scoring_reads_settled_state_not_what_anyone_claimed():
    m = fresh()
    m.hub.as_("T1", EVEN)
    m.hub.as_("T2", "I produced a huge amount of everything")
    m.drain()
    utils = m.close_episode()
    assert utils[0] > 0 and utils[1] == 0.0
    s = score(ISLAND, [utils])
    assert s.eff_episode == [0.0], "a self-report earns nothing"


def test_k_identical_episodes_score_exactly_one_episode():
    from barter.economy import autarky
    _, auto = autarky(ISLAND)
    one = score(ISLAND, [list(auto)]).eff_round
    for k in (2, 3, 5, 8):
        assert score(ISLAND, [list(auto)] * k).eff_round == pytest.approx(
            one, abs=1e-6)


# --- what the record has to be able to answer later ----------------------

def test_nothing_settles_before_the_episode_is_rung_in() -> None:
    """The acknowledgement window is not part of episode 1.

    It was, for the whole ten-arm screen: production settled while the manager
    was still waiting for ACKs, so episode 1 ran longer than episodes 2 and 3,
    and longer for a trader who produced early than for one who waited. An
    episode that is not the same length as its siblings is not a repeat of it.
    """
    m = fresh()
    m.episode_open = False
    m.hub.as_("T1", "PRODUCE bread=1.0")
    m.drain()
    assert m.settled == 0
    assert any("closed" in str(r["body"]) for r in m.hub.rows
               if r["from"] == MANAGER)


def test_the_bell_leaves_the_next_episode_shut() -> None:
    m = fresh()
    m.close_episode()
    assert m.episode_open is False
    m.hub.as_("T1", "PRODUCE bread=1.0")
    m.drain()
    assert m.settled == 0


def test_a_refusal_keeps_the_reason_it_gave() -> None:
    """A count says how often the manager said no; only the reason says what
    the traders could not manage to express."""
    m = fresh()
    m.hub.as_("T1", "PRODUCE bread")
    m.drain()
    assert m.refused == 1
    (r,) = m.refusals
    assert r["trader"] == "T1"
    assert r["kind"] == "malformed"
    assert r["line"] == "PRODUCE bread"
    assert r["reason"]


def test_the_bell_records_who_went_without_and_in_what() -> None:
    """A zero episode is one trader holding none of one good, and the utility
    vector cannot say which trader or which good. That is the question every
    post-mortem of the screen turned out to ask, and boards expire in an hour.
    """
    m = fresh()
    m.hub.as_("T1", "PRODUCE bread=1.0")
    m.drain()
    m.close_episode()
    (log,) = m.episode_log
    assert log["episode"] == 1
    assert log["produced"] == ["T1"]
    assert set(log["starved"]["T1"]) == {"cloth", "iron", "salt"}
    assert set(log["starved"]["T2"]) == {"bread", "cloth", "iron", "salt"}
    assert log["utilities"]["T1"] == 0.0
    assert log["holdings"]["T1"]["bread"] > 0


def test_the_bell_records_which_proposals_lapsed() -> None:
    m = fresh()
    m.hub.as_("T1", "PRODUCE bread=1.0")
    m.drain()
    m.hub.as_("T1", "PROPOSE to=T2 give=bread:0.1 want=salt:0.1")
    m.drain()
    m.close_episode()
    (log,) = m.episode_log
    assert log["lapsed"] == ["p1"]
    assert log["settled"] == 2
