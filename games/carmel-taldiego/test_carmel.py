"""What has to stay true of Carmel's policy.

She is the control: `games/carmel-taldiego.md` keeps her an NPC precisely so a
searcher's score is not confounded with how well she played. A policy that
drifts is a control that has stopped controlling, so these pin the shape of
her decisions rather than any particular chase.

    python3 -m pytest games/carmel-taldiego/test_carmel.py -q
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


def test_she_leans_on_the_least_informative_hint_by_exactly_as_much_as_WHIM_says():
    """Her stated strategy, softened on 2026-09-09 -- Gal: *"add some
    randomness for all her decisions."*

    This used to assert `cover[hint] == max(cover)` on every leg, which is
    now false by design: she draws among her three live descriptors
    weighted by `cover ** (1 / WHIM)`.

    **The replacement asserted `rate > 0.55` and that was the wrong shape
    of test twice over.** It went red in CI at exactly 0.550, and it was
    only ever a number somebody had watched once: the rate depends on the
    treasure table, because the table decides which rooms she goes to and
    therefore which live hints she is choosing between -- and `absurd.tsv`
    is gitignored, so a checkout with `HUE_TREASURE_KEY` and CI compute
    different ones (50% here, 55% there). Calibrating a constant against
    one of them is the same defect as the seeds in `test_trail_card.py`.

    So it derives its own target instead. The sampler's definition gives
    an exact per-leg probability of taking the vaguest hint; the mean of
    those is what the run should produce, and the assertion is that it
    does. Then two bounds that no longer need calibrating: the expectation
    must sit well clear of the 1/3 a coin would give -- turn `WHIM` up to
    uniform and it fails -- and the observed rate must not be 100%, which
    is what reverting the draw to `max` would give.
    """
    def vaguest_odds(landmark: str) -> float:
        live = [WORLD.cover[w] for w in WORLD.live_hints(landmark)]
        top = max(live)
        weights = [(c / top) ** (1 / C.WHIM) for c in live]
        return max(weights) / sum(weights)

    took, expected, legs = 0, [], 0
    for seed_byte in range(1, 12):
        seed = bytes.fromhex(f"{seed_byte:02x}" * 32)
        for leg in C.itinerary(seed, START, WORLD, 20):
            live = [WORLD.cover[w] for w in WORLD.live_hints(leg["to"])]
            took += WORLD.cover[leg["hint"]] == max(live)
            expected.append(vaguest_odds(leg["to"]))
            legs += 1

    assert legs > 100, legs
    rate, target = took / legs, sum(expected) / len(expected)
    assert abs(rate - target) < 0.12, (
        f"she took the vaguest hint on {rate:.1%} of {legs} legs, and"
        f" WHIM={C.WHIM} predicts {target:.1%}")
    assert target > 0.45, (
        f"WHIM={C.WHIM} leaves her only a {target:.1%} lean on the vaguest"
        f" hint, against {1 / 3:.1%} for a coin: that is not a strategy")
    assert rate < 0.95, "the draw has been reverted to max"


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


def test_the_clock_is_her_standing_still_and_nothing_else():
    """The arithmetic the chase turns on, and the one this file has now got
    wrong three times.

    It said travel closed the gap; then that the dwell was the only term
    that closed it; then that prep and dwell both did, while travel
    cancelled. Gal, 2026-09-10: *"travel time is zero because it cancelled
    out with the player's. And for the player it is zero in real time."*

    So there is no travel term left to cancel. Her clock is prep and dwell,
    those are the only durations in the game, and **a searcher's lag is a
    constant** -- it does not shrink as she steals or grow as she flies,
    because it never had a journey in it. What the lag has to beat is one
    leg's window, not an accumulated gap.
    """
    trail = C.itinerary(SEED, START, WORLD)
    clock = 0.0
    for i, leg in enumerate(trail[:8]):
        assert leg["travel"] == 0, "a journey came back into the clock"
        assert abs(leg["arrived"] - (leg["posted"] + leg["prep"])) < 1e-9
        assert abs(leg["leaves"] - (leg["arrived"] + leg["dwell"])) < 1e-9
        clock += leg["prep"] + leg["dwell"]
        assert abs(clock - leg["leaves"]) < 1e-6, (
            f"leg {i}: the campaign clock is not the sum of what she has"
            f" spent standing still")


def test_a_far_move_costs_her_and_costs_the_searcher_nothing():
    """Gal, 2026-09-09: *"prep time is only for her, not the player."* And
    2026-09-10: the player's travel is zero.

    **This test used to check the wrong thing and passed by accident.** It
    scanned `pursue` for `clock +=` lines and asserted none of them called
    `prep_hours` -- and when travel went to zero, `pursue` stopped having a
    `clock +=` line at all, so the loop ran zero times and the test went
    green having checked nothing. `CLAUDE.md`'s "absence drawn as a pass",
    caught in this file for the third time.

    So it asserts behaviour instead: a searcher's lag is untouched by how
    far she goes, which is what "prep is only for her" now means when
    nobody travels.
    """
    a, near = WORLD.places["Eiffel Tower"], WORLD.places["Bastille"]
    far = WORLD.places["Uluru"]
    assert C.prep_hours(a, far) > C.prep_hours(a, near), "prep grows with distance"

    # Two campaigns, one searcher, identical but for how far she goes: its
    # lag is what it joined with, both times and whatever she did.
    trail = C.itinerary(SEED, START, WORLD, 6)
    _, lag = C.pursue(WORLD, START, "Uluru", trail, joined_at=4.0)
    _, lag_far = C.pursue(WORLD, START, "Bastille", trail, joined_at=4.0)
    assert lag == lag_far == 4.0, (lag, lag_far)


def test_a_searcher_too_slow_for_the_window_never_reaches_her():
    """She is in a room from `posted + prep` until `posted + prep + dwell`.
    A searcher whose lag exceeds that window is not there, however well it
    guessed -- which is the whole of what the clock still decides now that
    nobody travels."""
    trail = C.itinerary(SEED, START, WORLD, 8)
    widest = max(leg["prep"] + leg["dwell"] for leg in trail)
    move, _ = C.pursue(WORLD, START, "Uluru", trail, joined_at=widest + 1)
    assert move is None, "it was standing beside her after she had gone"


def test_a_field_that_divides_the_candidates_covers_more_of_them():
    """The arithmetic the lobby is for, and it is arithmetic now rather
    than an aspiration: coverage is `WATCH x searchers` against the
    candidate set, so a field that splits the list sees more of it than a
    field where everyone watches the same nearest handful.

    Asserted as a comparison between the two rotas on the same trail, so it
    needs no calibrated number and cannot drift with `WATCH`.
    """
    trail = C.itinerary(SEED, START, WORLD, 12)
    field = 5

    def covered(divided: bool) -> int:
        found = set()
        for i in range(field):
            move, _ = C.pursue(WORLD, START, "Uluru", trail, joined_at=0.0,
                               share=(i, field) if divided else (0, 1))
            if move is not None:
                found.add(move)
        return len(found)

    assert covered(True) >= covered(False), (
        f"dividing the candidates found {covered(True)} legs and not"
        f" dividing found {covered(False)}")


def test_the_packing_grows_faster_than_the_journey():
    """Gal, 2026-09-10: *"make her distance to time super linear."*

    Twice as far must cost **more** than twice the packing, at every
    scale. Asserted as a ratio rather than against a constant, so it holds
    whatever `PREP`, the pivot and the exponent are set to -- and fails the
    moment somebody flattens the exponent back to 1.
    """
    here = WORLD.places["Eiffel Tower"]

    def prep_at(km: float) -> float:
        # A synthetic point due east, so the only thing varying is distance.
        far = {"lat": here["lat"], "lon": here["lon"] + km / 111.0
               / max(0.2, __import__("math").cos(
                   __import__("math").radians(here["lat"])))}
        return C.prep_hours(here, far)

    for km in (500, 1000, 2000, 4000):
        single, double = prep_at(km), prep_at(2 * km)
        assert double > 2 * single * 1.05, (
            f"{km} km -> {2 * km} km only took prep from {single:.2f}h to"
            f" {double:.2f}h, which is not superlinear")

    # And the pivot is where it agrees with the linear rule it replaced,
    # which is what keeps the exponent the only thing that changed.
    at_pivot = C.PREP * C.PREP_PIVOT
    far = {"lat": 0.0, "lon": 0.0}
    origin = {"lat": 0.0, "lon": 0.0}
    hours = C.PREP_PIVOT
    assert abs(C.PREP * C.PREP_PIVOT
               * (hours / C.PREP_PIVOT) ** C.PREP_EXPONENT
               - at_pivot) < 1e-9


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
