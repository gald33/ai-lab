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
from secret_matrix import RECIPE, room_token, salt_for  # noqa: E402

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


def test_a_reader_can_derive_a_room_from_the_notice_alone():
    """THE ONE THE NOTICE EXISTS FOR. Nothing is worth publishing a recipe
    for if the recipe cannot be followed, so this follows it: pull the salt
    out of what she posted, and derive a room with a fresh `hashlib` call
    written from the printed line rather than by importing ours.

    Switchboard's MCP surface has 27 tools and not one of them hashes, so
    the reader here is any agent with a shell -- which is why the recipe is
    a bare digest over a byte string and not an HMAC or a KDF.
    """
    import hashlib

    notice = C.open_campaign(SEED, START)
    salt_line = next(l for l in notice.splitlines() if "salt =" in l)
    salt = bytes.fromhex(salt_line.split("=")[1].strip())

    # Written from the recipe as printed, importing nothing of ours.
    derived = "w_" + hashlib.sha256(
        b"hue-and-cry/v1/landmark" + b"\x00" + salt + b"\x00"
        + "Uluru".encode("utf-8")).hexdigest()
    assert derived == room_token("Uluru", salt_for(SEED))


def test_the_notice_publishes_the_salt_and_never_the_seed():
    """*"she has to post the salt so the hash can be computed at all"* --
    and the seed is the other half of that sentence: it stays hers, because
    it is what keeps the hints and the treasures sealed until the end."""
    notice = C.open_campaign(SEED, START)
    assert salt_for(SEED).hex() in notice
    assert SEED.hex() not in notice
    assert RECIPE in notice


def test_the_closing_post_publishes_the_seed():
    """It is the only thing that makes the campaign checkable afterwards.
    Nothing enforces that she posts it -- there is no component that could
    -- but a campaign nobody can check is a campaign nobody counts."""
    trail = C.itinerary(SEED, START, WORLD, 5)
    post = C.close_campaign(SEED, "You did not find me", 200, trail)
    assert SEED.hex() in post


def test_the_notice_is_not_a_command():
    """*"we have no commands here"* -- nothing parses it, there is no verb
    to recognise and nothing to settle. If this file grows a grammar again,
    it has grown a manager to read it, which this game does not have."""
    for post in (C.open_campaign(SEED, START),
                 C.close_campaign(SEED, "caught", 0, [])):
        for line in post.splitlines():
            head = line.split()[0] if line.split() else ""
            assert not (len(head) > 2 and head.isupper() and head.isalpha()), (
                f"{head!r} reads like a command")


def test_the_lobby_is_the_same_room_every_game():
    """A lobby that moved with the game salt could not be found by anybody
    who was not already playing, which is the one thing a lobby is for."""
    assert isinstance(C.LOBBY, str) and C.LOBBY
