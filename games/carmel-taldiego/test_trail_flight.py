"""What the flight must do, watched in a real browser.

    python3 -m pytest games/carmel-taldiego/test_trail_flight.py -q

`CLAUDE.md`: *"A page's behaviour is checked in a browser, or it is not
checked"* -- and everything this page is for is behaviour. A camera that
pulls back mid-leg, a line that draws as she flies, a caption that changes
when she lands: not one of those is visible to an assertion on markup, and
the lobby's frozen countdowns are what happens when you try.

So these drive Chromium. Where there is none they **skip**, and
`HUE_REQUIRE_BROWSER=1` turns every skip into a failure -- set in the
`pages` CI job, for the reason `render.py --require` exists: a skip and a
pass are the same green tick, and a job that quietly checked nothing is
worse than no job.

Every test here has been made to fail on purpose. The camera ones by
replacing the `sin(pi t)` pull-back with a constant scale; the disclosure
ones by putting the gazetteer back into the page; the reduced-motion one
by ignoring the media query.
"""

import json
import os
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import carmel as C  # noqa: E402
import trail_flight as F  # noqa: E402

#: One campaign she wins across three continents, and one she is caught on.
FLOWN = bytes.fromhex("55" * 32)
CAUGHT = bytes.fromhex("22" * 32)


def _span_km(result: dict, world) -> float:
    """How far apart the two most distant rooms of a campaign are."""
    stops = [world.places[leg["to"]] for leg in result["moves"]]
    return max((C.travel_hours(a, b) * C.TRAVEL_KMH
                for a in stops for b in stops), default=0.0)


def _tightest(seeds: list[bytes]) -> bytes:
    """The seed among these whose campaign covers the least ground.

    **Chosen by span rather than named**, because a seed's campaign shape
    is not stable. `CAUGHT` was the local campaign when this file was
    written; Carmel's decisions gained their randomness the same day
    (`games/carmel-taldiego.md`, "Randomness in all three of her decisions")
    and her median hop went from 653 km to 2,982, so the seed that used to
    stay in Europe now crosses the planet. The claim under test is about a
    campaign that covers little ground, so the test asks for one of those
    instead of trusting a number written down before the policy changed.
    """
    def span(sd: bytes) -> float:
        world, result = built(sd)
        return _span_km(result, world)

    # A campaign that never left one landmark is not the local case, it is
    # a degenerate one, and it would pass this test by carrying nothing.
    real = [sd for sd in seeds if span(sd) > 100] or seeds
    return min(real, key=span)


#: The local campaign, picked by span. Computed once: building a chase is
#: not free and three tests want the same one.
LOCAL: bytes | None = None


def local_seed() -> bytes:
    global LOCAL
    if LOCAL is None:
        LOCAL = _tightest([bytes.fromhex(f"{b:02x}" * 32)
                           for b in range(1, 21)])
    return LOCAL


def built(seed: bytes):
    world = C.Map(seed)
    result = C.chase(seed, C.LOBBY_LANDMARK, searchers=2, world=world)
    return world, result


#: A campaign that ends in an arrest, found rather than named. Computed
#: once; scanning costs a chase per seed.
ARRESTED: bytes | None = None


def arrested_seed() -> bytes:
    """A seed whose campaign is caught, scanned for rather than written down.

    Same reason as `_tightest` above and one more: an outcome is not stable
    across checkouts either. `absurd.tsv` is gitignored, so a checkout
    holding it builds 80 hand-written treasures and CI builds none, and the
    same seed is caught in one and escapes in the other.
    """
    global ARRESTED
    if ARRESTED is None:
        for b in range(1, 60):
            seed = bytes.fromhex(f"{b:02x}" * 32)
            if built(seed)[1]["outcome"] == "caught":
                ARRESTED = seed
                break
        else:
            pytest.fail("no seed in 59 ends in an arrest:"
                        " the catch is unreachable")
    return ARRESTED


def html(seed: bytes) -> str:
    world, result = built(seed)
    return F.page(result, world, seed, C.LOBBY_LANDMARK)


def embedded(seed: bytes) -> dict:
    """The JSON the page carries, which is everything it can possibly say."""
    source = html(seed)
    body = source.split('id="data">', 1)[1].split("</script>", 1)[0]
    return json.loads(body)


def missing(why: str):
    if os.environ.get("HUE_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and HUE_REQUIRE_BROWSER is set: this run "
                    f"watched no flight at all")
    pytest.skip(why)


class Flight:
    """A page open in a browser, with the clock under the test's hand."""

    def __init__(self, tab):
        self.tab = tab

    def seek(self, ms: float) -> dict:
        return self.tab.evaluate("ms => window.seekFlight(ms)", ms)

    @property
    def plan(self) -> dict:
        return self.tab.evaluate("window.flightPlan")

    @property
    def now(self) -> dict:
        return self.tab.evaluate("window.flight")

    def text(self, selector: str) -> str:
        return self.tab.inner_text(selector)


def linked(seed: bytes, fragment: str | None = None,
           plan: dict | None = None, landing: str = "",
           clipboard: bool = False):
    """A `Flight` on the *published* viewer, opened at a chase's address.

    The same browser and the same `Flight`, but the page under it is
    `F.viewer()` beside `F.basemap_js()` -- what `build_site` writes -- so
    what this drives is the artifact a link actually opens rather than a
    page assembled for the test.
    """
    import contextlib

    @contextlib.contextmanager
    def open_it():
        try:
            from playwright import sync_api as play
        except ImportError:
            missing("no playwright to drive a page with")
        chrome = next((p for p in pathlib.Path("/opt/pw-browsers")
                       .glob("chromium*") if p.is_file()), None)
        home = pathlib.Path(os.environ.get("PYTEST_TMP", "/tmp")) / "chase"
        home.mkdir(parents=True, exist_ok=True)
        (home / "index.html").write_text(F.viewer(landing),
                                         encoding="utf-8")
        (home / "basemap.js").write_text(F.basemap_js(), encoding="utf-8")
        tail = (F.link(plan or embedded(seed), "x").split("#", 1)[1]
                if fragment is None else fragment)
        with play.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(
                    executable_path=str(chrome) if chrome else None)
            except Exception as exc:                        # noqa: BLE001
                missing(f"no chromium to drive a page with: {exc!r}")
            tab = browser.new_context(
                viewport={"width": 1000, "height": 700},
                permissions=(["clipboard-read", "clipboard-write"]
                             if clipboard else [])).new_page()
            broke = []
            tab.on("pageerror", lambda e: broke.append(str(e)))
            tab.goto((home / "index.html").as_uri() + "#" + tail)
            tab.wait_for_function("() => window.flight !== undefined",
                                  timeout=10000)
            try:
                yield Flight(tab)
            finally:
                browser.close()
            assert not broke, broke

    return open_it()


def flown(seed: bytes = FLOWN, reduced: bool = False):
    """A context manager yielding a `Flight`, or a skip."""
    import contextlib

    @contextlib.contextmanager
    def open_it():
        try:
            from playwright import sync_api as play
        except ImportError:
            missing("no playwright to drive a page with")
        chrome = next((p for p in pathlib.Path("/opt/pw-browsers")
                       .glob("chromium*") if p.is_file()), None)
        page = pathlib.Path(os.environ.get("PYTEST_TMP", "/tmp")) / "flight.html"
        page.write_text(html(seed), encoding="utf-8")
        with play.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(
                    executable_path=str(chrome) if chrome else None)
            except Exception as exc:                        # noqa: BLE001
                missing(f"no chromium to drive a page with: {exc!r}")
            context = browser.new_context(
                viewport={"width": 1000, "height": 700},
                reduced_motion="reduce" if reduced else "no-preference")
            tab = context.new_page()
            broke = []
            tab.on("pageerror", lambda e: broke.append(str(e)))
            tab.goto(page.as_uri())
            tab.wait_for_function("() => window.flight !== undefined",
                                  timeout=8000)
            try:
                yield Flight(tab)
            finally:
                browser.close()
            assert not broke, broke

    return open_it()


# --- the camera, which is the whole point --------------------------------

def test_the_camera_pulls_back_in_flight_and_closes_again_on_arrival():
    """The move Gal asked for, measured rather than admired."""
    with flown() as flight:
        plan = flight.plan
        legs = [s for s in plan["segments"] if s["kind"] == "flight"]
        holds = [s for s in plan["segments"] if s["kind"] == "hold"]
        assert legs and holds

        for leg in legs:
            start = flight.seek(leg["at"] + 1)["scale"]
            middle = flight.seek(leg["at"] + leg["ms"] / 2)["scale"]
            end = flight.seek(leg["at"] + leg["ms"] - 1)["scale"]
            # a bigger scale is a closer camera
            assert middle < start * 0.95, f"never pulled back: {leg}"
            assert middle < end * 0.95, f"never closed again: {leg}"

        for hold in holds:
            at = flight.seek(hold["at"] + hold["ms"] / 2)
            assert at["phase"] == "hold"


def test_a_hold_is_the_same_kilometres_wherever_she_is():
    """Mercator's scale runs as 1/cos(lat), so a fixed number of units is a
    different number of kilometres in Bergen than in Zanzibar. Holding the
    kilometres is what makes two rooms read as the same kind of place."""
    across = []
    for lat in (-54.8, 0.0, 35.7, 60.4, 78.2):
        scale = F.close_scale(lat)
        units = F.WIDTH / scale
        import math
        across.append(units * F.EQUATOR_KM * math.cos(math.radians(lat)))
    assert max(across) - min(across) < 1.0, across
    assert abs(across[0] - F.CLOSE_KM) < 1.0


def test_it_never_zooms_in_during_a_flight():
    """A leg shorter than the hold would otherwise lurch forward and back."""
    world, result = built(FLOWN)
    plan = F.plan(result, world, C.LOBBY_LANDMARK)
    for i, leg in enumerate(plan["flights"]):
        assert leg["wide"] <= plan["stops"][i]["scale"]
        assert leg["wide"] <= plan["stops"][i + 1]["scale"]


def test_a_short_leg_still_pulls_back_enough_to_read():
    world, result = built(FLOWN)
    plan = F.plan(result, world, C.LOBBY_LANDMARK)
    for i, leg in enumerate(plan["flights"]):
        near = min(plan["stops"][i]["scale"], plan["stops"][i + 1]["scale"])
        assert near / leg["wide"] >= F.MIN_PULL - 1e-6


# --- the trail and the pins ----------------------------------------------

def test_the_trail_only_ever_grows():
    with flown() as flight:
        total = flight.plan["total"]
        lengths = [flight.seek(total * i / 20)["trail"] for i in range(21)]
        assert lengths == sorted(lengths), lengths
        assert lengths[0] < lengths[-1]


def test_a_pin_appears_for_each_room_as_she_reaches_it():
    with flown() as flight:
        holds = [s for s in flight.plan["segments"] if s["kind"] == "hold"]
        seen = [flight.seek(h["at"] + h["ms"] / 2)["pins"] for h in holds]
        assert seen == list(range(1, len(holds) + 1)), seen


def test_the_room_she_is_caught_in_is_ringed():
    """The marker nothing had ever counted.

    `paint` has always drawn a ring on the caught room, and until
    `REPUTATION_TO_WIN` moved to 750 no seed this file used was ever
    caught -- so the branch ran in no test, and the two tests above read
    `pins.childNodes.length` as "rooms reached", which it is not. Raising
    the threshold made catches ordinary and both went red at once. They
    count `[data-stop]` now, and the ring gets the assertion it never had.

    Made to fail on purpose by dropping the `st.caught` branch: `marks`
    then equals `pins` and this goes red while the two above stay green,
    which is the split that was missing.
    """
    with flown(seed=arrested_seed()) as flight:
        holds = [s for s in flight.plan["segments"] if s["kind"] == "hold"]
        at = flight.seek(holds[-1]["at"] + holds[-1]["ms"] / 2)
        assert at["pins"] == len(holds)
        assert at["marks"] == at["pins"] + 1, "no ring on the room she fell in"


def test_the_caption_says_where_she_is_and_then_that_she_is_flying():
    with flown() as flight:
        stops = embedded(FLOWN)["stops"]
        holds = [s for s in flight.plan["segments"] if s["kind"] == "hold"]
        for i, hold in enumerate(holds):
            flight.seek(hold["at"] + hold["ms"] / 2)
            assert stops[i]["name"] in flight.text("#where")
        leg = next(s for s in flight.plan["segments"] if s["kind"] == "flight")
        flight.seek(leg["at"] + leg["ms"] / 2)
        assert "in the air" in flight.text("#where")


def test_it_actually_moves_on_its_own():
    """The one test that does not touch `seek`. Everything above would pass
    on a page whose clock never ran."""
    with flown() as flight:
        first = flight.now
        flight.tab.wait_for_timeout(1500)
        second = flight.now
        assert second["clock"] > first["clock"] + 500, (first, second)


def test_asking_for_no_motion_gets_the_whole_trail_at_once():
    with flown(reduced=True) as flight:
        at = flight.now
        assert at.get("reduced") is True
        assert at["done"] is True
        assert at["pins"] == len(embedded(FLOWN)["stops"])
        before = at["trail"]
        flight.tab.wait_for_timeout(1200)
        assert flight.now["trail"] == before, "it moved anyway"


# --- the world at both ends ----------------------------------------------

def test_it_opens_on_the_world_and_ends_back_out_at_it():
    """Gal, 2026-09-12: *"do the flight too"*. Two shots, not one long zoom
    -- and the difference is checkable: at both ends the camera is the whole
    world, and the opening one shows the box without the trail, because the
    trail has not happened yet."""
    with flown(seed=arrested_seed()) as flight:
        shots = [s for s in flight.plan["segments"] if s["kind"] == "globe"]
        assert len(shots) == 2, "an opening shot and a closing one"

        opening = flight.seek(shots[0]["at"] + shots[0]["ms"] / 2)
        assert opening["globe"] == 1 and opening["opening"] is True
        assert opening["pins"] == 0, "the opening shot gave the trail away"
        assert "40,075" in flight.text("#scale"), "not the whole world"

        closing = flight.seek(shots[1]["at"] + shots[1]["ms"] / 2)
        assert closing["globe"] == 1 and closing["opening"] is False
        assert closing["pins"] == len(embedded(arrested_seed())["stops"])
        assert "40,075" in flight.text("#scale")
        assert "KM AROUND" in flight.text("#said"), "no span on the way out"


def test_the_flight_itself_never_sits_at_world_scale():
    """The shots are affordable because they are *cuts*: the camera never
    passes through the middle, so the page never has to carry a detailed
    world. If a hold or a leg ever widened that far, the corridor geometry
    would be a lie at that zoom and the weight test below would be next."""
    with flown() as flight:
        for s in flight.plan["segments"]:
            if s["kind"] in ("globe", "fade"):
                continue
            at = flight.seek(s["at"] + s["ms"] / 2)
            assert at["scale"] > F.WIDTH * 4, (s["kind"], at["scale"])


def test_the_world_shot_is_the_coarse_layer_and_only_that():
    """`test_the_geometry_is_cut_to_the_frame` measures the corridor and
    would not see a second copy of the planet arriving beside it. This
    measures the other layer, and pins it to the one that costs 4% of the
    map rather than the one that costs all of it."""
    coarse = F.BM.load()["land_coarse"]
    carried = embedded(FLOWN)["globe"]["coarse"]
    assert len(carried) == len(coarse)
    assert (sum(len(s) for s in carried)
            == sum(len(s) for s in coarse) == 1958)


# --- a chase as a link ----------------------------------------------------

def test_a_link_carries_the_chase_and_not_the_planet():
    """Gal, 2026-09-12: *"your agent can give you a link to a website that
    shows your chase animation"*. What makes that a link and not a build is
    that the three heavy things in a plan are all things the page can get
    for itself."""
    import gzip
    import base64

    full = embedded(FLOWN)
    small = F.packed(full)
    assert "geometry" not in small and "coarse" not in small["globe"]
    assert all("centres" not in f for f in small["flights"])
    assert all(len(f["path"]) <= F.LINK_POINTS for f in small["flights"])

    # and the chase itself survives intact: every stop, every word
    assert [x["name"] for x in small["stops"]] == [x["name"] for x in
                                                   full["stops"]]
    assert [x["took"] for x in small["stops"]] == [x["took"] for x in
                                                   full["stops"]]
    assert [f["km"] for f in small["flights"]] == [f["km"] for f in
                                                   full["flights"]]

    url = F.link(full, F.CHASE_PAGE)
    body = url.split("#", 1)[1]
    back = json.loads(gzip.decompress(base64.urlsafe_b64decode(
        body + "=" * (-len(body) % 4))))
    assert back == small, "the address is not the payload"


def test_even_the_longest_chase_is_a_link_somebody_would_send():
    """The ceiling exists because the first version was 45 KB of address for
    a seventeen-room chase, which is not a link, it is a file with a colon
    in it.

    **The campaign is searched for, not named**, and the first version of
    this test is why: it asserted the ceiling over `FLOWN`, `CAUGHT` and
    `local_seed`, and every one of those is a two-leg chase under the
    riddle, so raising `LINK_POINTS` to 9,999 left it green. That is the
    third time in this branch that a check named after a seed turned out to
    be a check named after a campaign shape -- and campaign shape is
    downstream of every parameter in `carmel.py`. Running out of long
    campaigns fails rather than passes, for the same reason.
    """
    longest, stops = None, 0
    for b in range(1, 80):
        seed = bytes.fromhex(f"{b:02x}" * 32)
        found = embedded(seed)
        if len(found["stops"]) > stops:
            longest, stops = found, len(found["stops"])
    assert stops >= 8, f"no campaign in 79 seeds is longer than {stops}"
    assert len(F.link(longest, F.CHASE_PAGE)) < 12_000, stops
    assert len(F.link(embedded(arrested_seed()), F.CHASE_PAGE)) < 4_000


def test_a_link_plays_with_no_chase_baked_into_the_page():
    """The whole claim, in a browser: a static page, a chase in the
    fragment, and a film. Nothing else on the page knows which chase it is
    -- the head, the title and every caption come out of the address."""
    with linked(arrested_seed()) as flight:
        assert flight.now.get("broken") is None, flight.now
        holds = [s for s in flight.plan["segments"] if s["kind"] == "hold"]
        at = flight.seek(holds[-1]["at"] + holds[-1]["ms"] / 2)
        assert at["phase"] == "hold"
        assert at["pins"] == len(holds)
        assert "Carmel Taldiego" in flight.tab.title()
        stops = embedded(arrested_seed())["stops"]
        assert stops[-1]["name"] in flight.text("#where")


def test_the_credit_scene_names_who_took_her():
    """Gal, 2026-09-12: the link is *"the 'credit scene' reward when the game
    is won"*. A credit scene with no credit in it is a report, so the shot
    the film ends on carries the name of whoever walked in on her.

    Only there, and only when somebody did: the opening shot is before any
    of it happened, and the published six were caught by a model with no
    name -- which is why `by` is absent from those rather than filled in
    with something plausible.
    """
    plan = embedded(arrested_seed())
    assert plan["by"] is None, "a simulated searcher was given a name"

    with linked(arrested_seed(), plan=dict(plan, by="a night porter")) as f:
        shots = [s for s in f.plan["segments"] if s["kind"] == "globe"]
        f.seek(shots[0]["at"] + shots[0]["ms"] / 2)
        assert "night porter" not in f.text("#say"), "credited before the end"
        f.seek(shots[1]["at"] + shots[1]["ms"] / 2)
        assert "taken by a night porter" in f.text("#say")


def test_a_catcher_called_something_hostile_is_still_just_a_name():
    """The name is a searcher's own roster string, minted into an address by
    her and opened by somebody else -- so it is a stranger's text arriving on
    a page a third party is reading, which is the shape every injection has.

    `textContent` is what makes it safe, and this is the check that says so:
    the markup arrives as characters on the screen and never as an element.
    """
    hostile = '<img src=x onerror="window.pwned=1">'
    plan = dict(embedded(arrested_seed()), by=hostile)
    with linked(arrested_seed(), plan=plan) as f:
        shots = [s for s in f.plan["segments"] if s["kind"] == "globe"]
        f.seek(shots[1]["at"] + shots[1]["ms"] / 2)
        assert hostile in f.text("#say"), "the name was not shown verbatim"
        assert f.tab.evaluate("window.pwned") is None
        assert f.tab.evaluate("document.querySelectorAll('#say img').length") == 0


def test_one_url_is_the_front_door_and_the_film():
    """Gal, 2026-09-12: *"the base url for the page is the landing page for
    the game."* Bare it is where a player starts; with a chase in its
    fragment it is the chase. Both states, in a browser, because which one
    a reader gets is behaviour and markup cannot see it."""
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import build_site as BS

    front = BS.landing()
    with linked(arrested_seed(), fragment="", landing=front) as f:
        assert f.now.get("landing") is True
        assert "Hand this to your agent" in f.text("#landing")
        assert f.tab.evaluate(
            "getComputedStyle(document.getElementById('stage')).display"
        ) == "none", "the film played with no chase in the address"

    with linked(arrested_seed(), landing=front) as f:
        assert f.now.get("landing") is None
        assert f.text("#landing").strip() == "", "the door stayed open"
        holds = [s for s in f.plan["segments"] if s["kind"] == "hold"]
        assert f.seek(holds[-1]["at"] + holds[-1]["ms"] / 2)["phase"] == "hold"


def test_the_copy_button_puts_the_prompt_on_the_clipboard():
    """Gal, 2026-09-12: *"add copy button."* `CLAUDE.md`: anything a page
    *does* is asserted in a real browser, and a control that silently does
    nothing is worse than no control -- so this clicks it and reads the
    clipboard back rather than checking that a button is present.

    What it must copy is **the block on the page**, not a second copy of the
    prompt kept beside it: `games/island/lobby_page.py` settled that shape
    and the reason, which is that a button copying something a reader cannot
    see asks them to paste an unread instruction into an agent they are
    responsible for.
    """
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import build_site as BS

    with linked(arrested_seed(), fragment="", landing=BS.landing(),
                clipboard=True) as f:
        f.tab.click("#take")
        f.tab.wait_for_selector("#take[data-took]", timeout=4000)
        assert "Copied" in f.text("#take")
        took = f.tab.evaluate("navigator.clipboard.readText()")
        assert took.strip() == f.text("#ask").strip(), (
            "the button copied something other than the block on the page")
        assert "hue and cry" in took.lower()


def test_the_copy_button_says_so_when_it_cannot_copy():
    """The other branch, and the one a reader actually meets: plain http, an
    embedded browser, a refused permission. It selects the block instead and
    says which happened.

    **Driven rather than grepped.** The first version of this asserted that
    the page contained the string `selectNodeContents`, which is a check
    that the word is present: pointing the selection at `document.body`
    instead of at the prompt left it green. So the clipboard is replaced
    with one that refuses, and what the reader is left holding -- the
    selection -- is what gets asserted.
    """
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import build_site as BS

    with linked(arrested_seed(), fragment="", landing=BS.landing()) as f:
        f.tab.evaluate("""() => Object.defineProperty(navigator, 'clipboard', {
            value: { writeText: () => Promise.reject(new Error('nope')) },
            configurable: true });""")
        f.tab.click("#take")
        f.tab.wait_for_function(
            "() => /clipboard refused/.test("
            "document.getElementById('take').textContent)", timeout=4000)
        picked = f.tab.evaluate("window.getSelection().toString()")
        assert picked.strip() == f.text("#ask").strip(), (
            "the fallback selected something other than the prompt")


def test_the_front_door_is_backed_by_the_map_the_game_is_played_on():
    """Gal: *"the background is the same world map."* The same coarse layer
    the card's world panel and the flight's two shots draw -- not a second
    drawing of the world, and not a gazetteer: the disclosure rule holds on
    a landing page exactly as it does on a card."""
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import build_site as BS
    import carmel as C2

    door = BS.backdrop()
    coarse = F.BM.load()["land_coarse"]
    assert door.count("<path") == len(coarse), "not the coarse world"
    assert F.INK["land"] in door

    world = C2.Map(bytes(32))
    named = [name for name in world.places if name in door]
    assert not named, f"the front door names landmarks: {named[:3]}"


def test_a_broken_chase_still_complains_even_with_a_front_door():
    """The front door is for an address with *nothing* in it. One that
    carries a chase which will not unpack is a broken link, and saying
    "welcome, here are the rules" to somebody holding one is a failure drawn
    as a greeting."""
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import build_site as BS

    with linked(arrested_seed(), fragment="not-a-chase",
                landing=BS.landing()) as f:
        assert "would not unpack" in (f.now.get("broken") or "")
        assert "Nothing to show" in f.text("#head")


def test_a_link_with_nothing_in_it_says_so():
    """`CLAUDE.md`: a skip drawn as a pass, in its user-facing form. An
    empty map and a page that gave up look identical from the sofa, so the
    page says which it is."""
    with linked(arrested_seed(), fragment="") as flight:
        assert "no chase" in (flight.now.get("broken") or "")
        assert "Nothing to show" in flight.text("#head")


# --- what it must not disclose -------------------------------------------

def test_the_page_names_no_landmark_but_the_ones_she_visited():
    """The disclosure guard, at the source rather than on screen: whatever
    the camera does, the page cannot show what it does not carry."""
    for seed in (FLOWN, CAUGHT):
        data = embedded(seed)
        world, result = built(seed)
        walked = {C.LOBBY_LANDMARK} | {leg["to"] for leg in result["moves"]}

        strings = []
        def walk(node):
            if isinstance(node, str):
                strings.append(node)
            elif isinstance(node, dict):
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)
        walk(data)
        body = "\n".join(strings)
        named = {name for name in world.places if name in body}
        assert named <= walked, named - walked


def test_the_basemap_carries_no_place_names_at_all():
    """The reason a real map is safe here and Google's would not have been:
    at this zoom a labelled map prints the names of exactly the famous
    places this game hides."""
    import basemap as BM
    world = BM.load()
    for key in ("land", "borders", "lakes", "land_coarse"):
        for shape in world[key]:
            for point in shape:
                assert len(point) == 2
                assert all(isinstance(v, (int, float)) for v in point)
    assert set(world) == {"source", "land", "borders", "lakes", "land_coarse"}


def test_it_never_asks_the_map_for_an_exit():
    """The routes-public question is still open, and a moving picture can
    leak it as easily as a still one."""
    world, result = built(FLOWN)

    def refuse(_landmark):
        raise AssertionError("the flight asked for an exit")

    world.exits = refuse
    F.page(result, world, FLOWN, C.LOBBY_LANDMARK)


def test_the_geometry_is_cut_to_the_frame():
    """A page carrying the whole planet would be 700 KB of coastline on
    every campaign, and would hand a reader the shape of everywhere she was
    not.

    Measured on a campaign that stays in Europe, which is the common case:
    a campaign's median span is a couple of thousand kilometres
    (`trail_card.py --survey`).
    """
    whole = sum(len(s) for k, v in F.BM.load().items() if k != "source"
                for s in v)
    carried = sum(len(s) for v in embedded(local_seed())["geometry"].values()
                  for s in v)
    assert carried < whole * 0.1, (carried, whole)


def test_a_flight_across_continents_is_heavy_and_that_is_not_a_bug():
    """The other end of the same population, pinned so it cannot get worse
    unnoticed and cannot be mistaken for a defect.

    Brussels to Himeji by way of Rome and the Deccan carries about half the
    basemap, because when the camera pulls back to fit a 6,300 km leg it is
    *looking at* half the basemap. Two schemes to avoid that were built and
    deleted -- `basemap.near` has the numbers. The ceiling is what stops the
    page quietly doubling; it is not a claim that the weight is wrong.
    """
    source = html(FLOWN)
    assert len(source) < 600_000, len(source)
    local = html(local_seed())
    assert len(local) < 120_000, len(local)


def test_the_page_stands_alone():
    """No CDN, no tiles, no key: it opens from a file, on a plane."""
    source = html(FLOWN)
    assert "http://" not in source.replace("http://www.w3.org", "")
    assert not re.search(r'src\s*=\s*"https?:', source)
    assert "googleapis" not in source and "tile" not in source.lower()


def test_the_require_flag_turns_a_skip_into_a_failure(monkeypatch):
    """The guard on the guard.

    Every test above skips where there is no browser, and `CLAUDE.md` has a
    whole section on why that is dangerous: a skip and a pass are the same
    green tick. `HUE_REQUIRE_BROWSER` is what makes the CI job honest, so
    it is checked rather than assumed -- the six instances in that section
    are all things somebody assumed.
    """
    monkeypatch.setenv("HUE_REQUIRE_BROWSER", "1")
    with pytest.raises(BaseException) as caught:
        missing("no browser here")
    assert "watched no flight at all" in str(caught.value)

    monkeypatch.delenv("HUE_REQUIRE_BROWSER")
    with pytest.raises(BaseException) as skipped:
        missing("no browser here")
    assert "Skipped" in type(skipped.value).__name__ or skipped.value.msg
