"""What the flight must do, watched in a real browser.

    python3 -m pytest games/hue-and-cry/test_trail_flight.py -q

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


def built(seed: bytes):
    world = C.Map(seed)
    result = C.chase(seed, C.LOBBY_LANDMARK, searchers=2, world=world)
    return world, result


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
    carried = sum(len(s) for v in embedded(CAUGHT)["geometry"].values()
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
    local = html(CAUGHT)
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
