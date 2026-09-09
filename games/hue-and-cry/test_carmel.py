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
from secret_matrix import token_for  # noqa: E402

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


def test_what_she_needs_to_win_does_not_read_the_size_of_the_field():
    """The correction that reshaped the game. This was a table keyed by how
    many were hunting, which nobody at the table can evaluate: she never
    learns who came, and the field is not closed when she opens the
    campaign -- whoever wants to join, joins, whenever they like.

    So the threshold is one number, and a chase against ten is meant to be
    harder than a chase against one.
    """
    assert isinstance(C.REPUTATION_TO_WIN, int)
    a = C.chase(SEED, START, searchers=1, world=WORLD)
    b = C.chase(SEED, START, searchers=9, world=WORLD)
    assert a["outcome"] != "caught" or b["outcome"] == "caught"


def test_nothing_she_decides_can_see_the_searchers():
    """She is the control, and a control that reacts to the field is not
    one. Her three decisions take the world, where she is and what she has
    taken -- and no argument that could carry a searcher."""
    import inspect

    for method in (C.Carmel.choose_destination, C.Carmel.choose_hint,
                   C.Carmel.will_steal, C.Carmel.best_cover):
        args = set(inspect.signature(method).parameters) - {"self"}
        assert not (args & {"searchers", "hunters", "field", "turnout"}), (
            f"{method.__name__} can see the field")


def test_the_lobby_notice_carries_the_opening_room_and_nothing_else():
    """The notice is how a campaign becomes findable at all: with a thousand
    rooms and nothing broadcast, a searcher with no lead never finds her. It
    must not say more than where to start."""
    notice = C.open_campaign(SEED, START)
    verb, address = notice.split()
    assert verb == "OPEN"
    assert address == token_for(SEED, START)
    assert START not in notice, "the notice names the landmark in clear"
    for other in ("Uluru", "Eiffel Tower"):
        assert token_for(SEED, other) not in notice


def test_the_lobby_is_the_same_room_every_game():
    """A lobby that moved with the game salt could not be found by anybody
    who was not already playing, which is the one thing a lobby is for."""
    assert isinstance(C.LOBBY, str) and C.LOBBY
