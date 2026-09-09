"""What has to stay true of Carmel's policy.

She is the control: `games/hue-and-cry.md` keeps her an NPC precisely so a
searcher's score is not confounded with how well she played. A policy that
drifts is a control that has stopped controlling, so these pin the shape of
her decisions rather than any particular chase.

    python3 -m pytest games/hue-and-cry/test_carmel.py -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402

SEED = bytes.fromhex(
    "ca12e100000000000000000000000000000000000000000000000000d1e60000")
WORLD = C.Map(SEED)
START = "Stonehenge"


def test_she_is_deterministic_given_the_seed():
    """The control only controls if it is reproducible. Two runs of the same
    seed are the same chase, hop for hop."""
    a = C.itinerary(SEED, START, WORLD)
    b = C.itinerary(SEED, START, C.Map(SEED))
    assert [(x["to"], x["dwell"], x["hint"]) for x in a] \
        == [(x["to"], x["dwell"], x["hint"]) for x in b]


def test_she_only_ever_moves_along_an_exit():
    """She has five exits and no teleport. If this fails the routes have
    stopped constraining her and the hint stops meaning anything, because a
    hint is read against her REACHABLE set."""
    at = START
    for leg in C.itinerary(SEED, START, WORLD):
        assert leg["to"] in WORLD.exits(at), f"{at} -> {leg['to']}"
        at = leg["to"]


def test_every_hint_she_posts_is_true_of_where_she_went():
    """*She may lie in prose. She may not lie in a clue.* The manager
    rejects a false one, so a Carmel who posts one is a Carmel who forfeits
    her own moves."""
    for leg in C.itinerary(SEED, START, WORLD):
        assert leg["hint"] in WORLD.descriptors[leg["to"]]


def test_she_posts_the_least_informative_hint_she_holds():
    """Her whole stated strategy, and the thing the descriptor layer exists
    to make possible. Anything else is a different control."""
    at = START
    for leg in C.itinerary(SEED, START, WORLD):
        reachable = WORLD.exits(at)
        live = WORLD.live_hints(leg["to"])
        covers = {w: len([x for x in reachable if w in WORLD.descriptors[x]])
                  for w in live}
        assert covers[leg["hint"]] == max(covers.values())
        at = leg["to"]


def test_she_never_robs_the_same_room_twice():
    seen = set()
    for leg in C.itinerary(SEED, START, WORLD):
        if leg["dwell"]:
            assert leg["to"] not in seen
            seen.add(leg["to"])


def test_a_theft_always_costs_her_time():
    """The dwell is the exposure and there is no other. A free theft would
    delete the game's only trade."""
    for leg in C.itinerary(SEED, START, WORLD):
        assert (leg["dwell"] > 0) == (leg["leaves"] > leg["arrived"])


def test_the_follower_closes_only_by_what_she_steals():
    """The arithmetic the whole chase turns on, and the one this file got
    backwards at first: their travel cancels exactly, so the gap is her head
    start minus everything she has stolen. Asserted rather than reasoned,
    because reasoning about it produced the wrong answer twice.
    """
    trail = C.itinerary(SEED, START, WORLD)
    home = "Uluru"
    lag0 = C.travel_hours(WORLD.places[home], WORLD.places[START])
    clock = lag0
    stolen = 0.0
    for leg in trail[:8]:
        clock += C.travel_hours(WORLD.places[leg["from"]],
                                WORLD.places[leg["to"]])
        gap = clock - leg["arrived"]
        assert abs(gap - (lag0 - stolen)) < 1e-6, (
            f"gap {gap:.2f} is not head start {lag0:.2f} minus"
            f" {stolen:.2f} stolen")
        stolen += leg["dwell"]


def test_more_hunters_leave_her_a_smaller_budget():
    """Which is why the threshold cannot be a fixed number. Her budget is
    the NEARER searcher's head start, so adding hunters shrinks it."""
    budgets = []
    for n in (1, 5):
        r = C.chase(SEED, START, searchers=n, world=WORLD, threshold=10 ** 9)
        budgets.append(min(r["lags"]))
    assert budgets[0] >= budgets[1]


def test_the_threshold_is_interpolated_and_not_extrapolated():
    assert C.reputation_to_win(2) == C.REPUTATION_TO_WIN[2]
    assert C.reputation_to_win(4) == 70          # between 3 and 5
    assert C.reputation_to_win(50) == C.REPUTATION_TO_WIN[5]
    assert C.reputation_to_win(1) == C.REPUTATION_TO_WIN[1]
