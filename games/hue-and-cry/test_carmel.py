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
START = C.LOBBY_LANDMARK


def test_she_is_deterministic_given_the_seed():
    """The control only controls if it is reproducible. Two runs of the same
    seed are the same chase, hop for hop."""
    a = C.itinerary(SEED, START, WORLD)
    b = C.itinerary(SEED, START, C.Map(SEED))
    assert [(x["to"], x["dwell"], x["hint"]) for x in a] \
        == [(x["to"], x["dwell"], x["hint"]) for x in b]


def test_there_are_no_routes():
    """Gal, 2026-09-09: *"we have no routes."*

    Written so it can fail for the reason it is named after, which the
    absence of `Map.exits` alone cannot: reintroduce a reachable set and
    this goes red, because she would stop leaving the kinship band. It
    asserts she reaches somewhere that is NOT among the 200 nearest
    look-alikes of where she stood -- the exact pool the deleted `band()`
    drew her five exits from.
    """
    import gazetteer

    assert not hasattr(WORLD, "exits") and not hasattr(WORLD, "band")

    gaz = WORLD.descriptors
    at, escaped = START, False
    for leg in C.itinerary(SEED, START, WORLD, 6):
        band = [x for _, x in sorted((-gazetteer.kinship(at, x, gaz), x)
                                     for x in gaz if x != at)][:200]
        escaped = escaped or leg["to"] not in band
        at = leg["to"]
    assert escaped, "every hop stayed inside a look-alike band"
    # Demonstrated rather than assumed, per CLAUDE.md: on this seed 2 of her
    # first 6 hops land outside the band, so restoring a reachable set of
    # any kind turns this red.


def test_a_hint_leaves_the_reader_a_hundred_places_not_five():
    """The number the decision was made on, pinned so it cannot drift back.

    With no routes a hint is read against the whole map, and the hint she
    chooses is the commonest of her three live descriptors -- so the
    candidate set is large by construction and that is the point. If this
    falls to single figures somebody has quietly re-narrowed the game.
    """
    sizes = sorted(WORLD.cover[max(WORLD.live_hints(n), key=WORLD.cover.get)]
                   for n in WORLD.descriptors)
    assert sizes[len(sizes) // 2] > 100, sizes[len(sizes) // 2]


def test_every_hint_she_posts_is_true_of_where_she_went():
    """*She may lie in prose. She may not lie in a clue.* The manager
    rejects a false one, so a Carmel who posts one is a Carmel who forfeits
    her own moves."""
    for leg in C.itinerary(SEED, START, WORLD):
        assert leg["hint"] in WORLD.descriptors[leg["to"]]


def test_she_leans_hard_on_the_least_informative_hint_without_always_taking_it():
    """Her stated strategy, softened on 2026-09-09 -- Gal: *"add some
    randomness for all her decisions."*

    This used to assert `cover[hint] == max(cover)` on every single leg.
    That is now false by design: she draws among her three live
    descriptors weighted by `cover ** (1 / WHIM)`, so she usually says the
    vaguest thing she holds and sometimes says a sharper one. The
    superseded assertion is quoted here rather than deleted, because the
    thing it was protecting still needs protecting -- a Carmel who picked
    uniformly would have no strategy at all, and would pass a test that
    only checked the hint was true.

    So: over a long campaign she must take the vaguest available hint far
    more often than the sharpest. Both bounds matter. The lower one fails
    if `WHIM` is turned up until she is picking at random; the upper one
    fails if the draw is quietly reverted to `max`.
    """
    vaguest = sharpest = legs = 0
    for seed_byte in range(1, 12):
        seed = bytes.fromhex(f"{seed_byte:02x}" * 32)
        for leg in C.itinerary(seed, START, WORLD, 20):
            live = [WORLD.cover[w] for w in WORLD.live_hints(leg["to"])]
            mine = WORLD.cover[leg["hint"]]
            legs += 1
            vaguest += mine == max(live)
            sharpest += mine == min(live) and min(live) != max(live)
    assert legs > 100, legs
    assert 0.55 < vaguest / legs < 0.95, (
        f"she took the vaguest hint on {vaguest / legs:.0%} of {legs} legs")
    assert sharpest > 0, "she never once said the sharper thing"


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


def test_the_follower_closes_by_everything_she_does_standing_still():
    """The arithmetic the whole chase turns on, and the one this file has
    now got wrong twice.

    Their travel still cancels exactly. What does not cancel is anything she
    does while not travelling, and since 2026-09-09 that is two things and
    not one: the dwell she spends stealing, and **the prep she spends
    getting ready to move**, which is hers alone -- Gal: *"prep time is only
    for her, not the player."* So the gap is her head start minus everything
    she has stolen AND everything she has packed.

    Asserted rather than reasoned, because reasoning about it produced the
    wrong answer twice: once when this said travel closed the gap, and once
    when the previous version of this test named the dwell as the only term.
    """
    trail = C.itinerary(SEED, START, WORLD)
    home = "Uluru"
    lag0 = C.travel_hours(WORLD.places[home], WORLD.places[START])
    clock, standing = lag0, 0.0
    for i, leg in enumerate(trail[:8]):
        clock += leg["travel"]
        standing += leg["prep"]
        gap = clock - leg["arrived"]
        assert abs(gap - (lag0 - standing)) < 1e-6, (
            f"leg {i}: gap {gap:.2f} is not head start {lag0:.2f} minus"
            f" {standing:.2f} spent standing still")
        standing += leg["dwell"]


def test_a_far_move_costs_her_and_costs_the_searcher_nothing():
    """Gal, 2026-09-09: *"prep time is only for her, not the player."*

    The asymmetry the whole mechanic rests on. If a searcher ever pays prep,
    the far candidates stop being the beatable ones and the timestamp stops
    being worth reading.
    """
    import inspect

    a, b = WORLD.places["Eiffel Tower"], WORLD.places["Uluru"]
    near = WORLD.places["Bastille"]

    assert C.prep_hours(a, b) > C.prep_hours(a, near), "prep must grow with distance"
    assert C.prep_hours(a, b) == C.PREP * C.travel_hours(a, b)

    # And nothing in the searcher's own leg arithmetic calls it: `pursue`
    # uses prep only to rank candidates by what SHE will pay.
    body = inspect.getsource(C.pursue)
    for line in body.splitlines():
        if "clock +=" in line:
            assert "prep_hours" not in line, line


def test_she_can_be_overtaken_to_a_far_place_and_not_to_a_near_one():
    """What her pursuers can deduce, which is the half Gal was unsure of:
    not where she is, but which of the places she might be they can beat
    her to. `e <= PREP * t(here, X)` -- so it is the far ones."""
    here = WORLD.places["Eiffel Tower"]
    far, near = WORLD.places["Uluru"], WORLD.places["Bastille"]
    lag = 6.0
    assert C.prep_hours(here, far) > lag, "a far hop must be beatable"
    assert C.prep_hours(here, near) < lag, "a near hop must not be"


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


def test_her_randomness_comes_out_of_the_seed_and_not_out_of_random():
    """`close_campaign` publishes the seed so that anybody holding the
    transcript can re-derive every choice she was entitled to make. A
    Carmel who rolled real dice would be a Carmel whose campaign nobody
    can check: the commit-reveal would still verify the hints and the
    treasures and would say nothing at all about her play.

    Determinism is asserted at the top of this file. This asserts the
    mechanism, because determinism could also be got by seeding a global
    RNG -- which would then be a shared, order-dependent global that any
    other import could disturb.
    """
    import inspect

    source = inspect.getsource(C)
    assert "import random" not in source
    assert "random." not in source.replace("os.urandom", "")

    # Same seed, same leg, different decision -> different draw. If the
    # three shared a stream, softening one would shift the others.
    rolls = {kind: C._draw(SEED, 3, kind) for kind in ("where", "say", "steal")}
    assert len(set(rolls.values())) == 3, rolls
    assert C._draw(SEED, 3, "where") != C._draw(SEED, 4, "where")


def test_the_searcher_reads_nothing_that_is_sealed():
    """What a searcher can know about where she is going is one term of
    three, and that is what makes her randomness worth anything.

    Her score is `reputation x cover / (1 + prep / ASSUMED_LAG)`.
    `reputation` is sealed in `treasures.enc` and `cover` comes from the
    seed-derived live hints; only `prep` is public. So *"she prefers
    near"* is the whole of what a pursuer can model, and softening the
    argmax is exactly what makes that one term a weaker predictor.

    If `pursue` ever reads a treasure or a live hint, that argument is
    void and the model is measuring a searcher nobody could be.
    """
    import inspect

    body = inspect.getsource(C.pursue)
    for sealed in ("treasure", "live_hints", ".cover"):
        assert sealed not in body, f"pursue reads {sealed}, which is sealed"

    # And it goes red if that ever changes: a Map whose sealed fields
    # raise on access still runs a whole pursuit.
    class Sealed(dict):
        def __getitem__(self, key):
            raise AssertionError("the searcher opened a sealed table")

    world = C.Map(SEED)
    trail = C.itinerary(SEED, START, world, 6)
    world.treasure, world.cover = Sealed(), Sealed()
    C.pursue(world, START, "Uluru", trail)


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
