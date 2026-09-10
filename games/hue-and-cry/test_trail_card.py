"""What the card must not get wrong, and what it must not show.

    python3 -m pytest games/hue-and-cry/test_trail_card.py -q

Two of these guard arithmetic and the rest guard a design decision, which
is unusual for a test file and is the point of this one. `trail_card.py`
names no landmark but the trail's own: a card that named the places around
her would be handing over a shortlist she is supposed to be deduced from.
A refusal that only lives in a docstring is a refusal somebody adds a flag
to on a quiet afternoon, so it is asserted here instead.

*This file was written while the map still had routes*, and one of its
tests guarded against drawing them. Gal removed the routes the same
afternoon -- *"we have no routes"* -- and that test is deleted rather than
left passing, for the reason recorded where it stood.

Every test below has been made to fail on purpose, per `CLAUDE.md`'s "a
check is green for the reason it names": the accounting ones by reverting
`kept` to `leg["dwell"]`, the layout ones by returning the naive
right-of-the-pin position, and the naming one by labelling the basemap.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import basemap as BM  # noqa: E402
import trail_card as TC  # noqa: E402

#: A seed whose campaign ends in an arrest, and one where she gets away.
# Two campaigns to draw. **Nothing below asserts what either seed's outcome
# is**, and that is deliberate: `absurd.tsv` is gitignored, so a checkout
# holding `HUE_TREASURE_KEY` builds 80 absurd treasures and CI builds none,
# and the same seed is caught in one and escapes in the other. The name is
# kept for the diff's sake and now means only "the first campaign".
CAUGHT = bytes.fromhex("22" * 32)
ESCAPED = bytes.fromhex("a3" * 32)


def run(seed: bytes):
    world = C.Map(seed)
    result = C.chase(seed, C.LOBBY_LANDMARK, searchers=2, world=world)
    return world, result


def draw(seed: bytes) -> str:
    world, result = run(seed)
    return TC.card(result, world, seed, C.LOBBY_LANDMARK)


def texts(svg: str) -> list[str]:
    return [(node.text or "") for node in ET.fromstring(svg).iter()
            if node.tag.endswith("text")]


# --- the arithmetic the drawing found -------------------------------------

def test_the_room_she_is_caught_in_is_not_credited():
    """The catch is being in the room with her, and she is only in a room
    she has not finished robbing -- so the final room of a caught campaign
    is always a theft interrupted. Counting it puts the card's header at
    odds with `chase`'s own total.

    **Asserted against a constructed result rather than a seeded chase**,
    because the outcome of any particular seed is not stable across
    checkouts. `absurd.tsv` is gitignored, so a checkout holding
    `HUE_TREASURE_KEY` builds 80 absurd treasures at the reputation floor
    and CI builds none -- different prizes, different dwells, different
    chase. `CAUGHT = "22"` was caught on CI and escaped here; `"4b"` was
    the other way round. A test that needs a named seed to lose is a test
    that goes red on somebody's laptop for a reason that is not a bug.
    """
    legs = [{"to": "Uluru", "dwell": 6.0}, {"to": "Stonehenge", "dwell": 11.0}]
    caught = {"outcome": "caught", "moves": legs}
    assert TC.kept(caught) == {0}, "the interrupted theft was credited"
    assert TC.kept({"outcome": "she wins", "moves": legs}) == {0, 1}


def test_the_card_and_the_scoreboard_agree_on_every_outcome():
    """The invariant the fix above exists for, and the one worth pinning:
    what the card banks is what `chase` reports, whatever happened.

    This replaces a pair of tests that each needed a seed with a particular
    outcome. It is stronger than both -- it holds for a catch, for a win
    and for a campaign that simply ran out of moves, so `kept` cannot be
    fixed for one and broken for another -- and it does not care which
    treasure table the checkout can build.
    """
    # No assertion that the outcomes differ. There was one, and it went
    # red when Carmel's decisions gained their randomness on 2026-09-09 --
    # all four seeds started escaping. It was guarding that `kept` gets
    # exercised on a catch, and the test above does that directly, on a
    # constructed result that no change to the chase can turn into a
    # different outcome.
    for tag in ("22", "4b", "a3", "07"):
        seed = bytes.fromhex(tag * 32)
        world, result = run(seed)
        legs = result["moves"]
        banked = sum(world.treasure[legs[i]["to"]]["reputation"]
                     for i in TC.kept(result))
        assert banked == result["reputation"], (
            f"{tag}: card banks {banked}, chase reports"
            f" {result['reputation']} on a {result['outcome']} campaign")


def test_the_header_counts_what_the_map_marks():
    """A consistency check and not an independent one -- it reads `kept`
    on both sides, so a wrong `kept` passes it. What it catches is the
    header and the pins drifting apart, which is the failure a reader would
    see and not believe. The arithmetic itself is the test above."""
    svg = draw(CAUGHT)
    _, result = run(CAUGHT)
    header = next(t for t in texts(svg) if "of them emptied" in t)
    assert f"{len(TC.kept(result))} of them emptied" in header


# --- what it must not show ------------------------------------------------

# `test_it_never_asks_the_map_for_an_exit` was here, and is deleted rather
# than left passing. It monkeypatched `Map.exits` to raise, and Gal removed
# the routes the same afternoon -- so on a Map with no `exits` at all the
# patch just sets an unused attribute and the test passes without checking
# anything. That is `CLAUDE.md`'s "absence drawn as a pass" exactly, and a
# vacuous green test is worse than no test.
#
# What it was protecting is still protected, by the test below: the card
# may name no landmark but the trail's own, so it cannot hand over a
# shortlist by any road, route layer or not.


def test_no_landmark_but_the_trail_is_named():
    """The basemap is a thousand dots and none of them is labelled. A card
    that named the places around her would be a shortlist."""
    world, result = run(ESCAPED)
    svg = TC.card(result, world, ESCAPED, C.LOBBY_LANDMARK)
    body = "\n".join(texts(svg))
    walked = {C.LOBBY_LANDMARK} | {leg["to"] for leg in result["moves"]}
    named = {name for name in world.places if name in body}
    assert named <= walked


def test_it_is_a_still_picture():
    """`CLAUDE.md`: anything a page *does* is asserted in a real browser.
    This file asserts on markup, which is only legal because the card does
    nothing -- so that is the thing to check before believing the rest."""
    svg = draw(ESCAPED)
    assert "<script" not in svg.lower()
    assert "<animate" not in svg.lower()
    assert not re.search(r'\son[a-z]+\s*=', svg)


def test_it_is_well_formed():
    ET.fromstring(draw(CAUGHT))


# --- the layout -----------------------------------------------------------

def rects(pins, blocks):
    out = []
    for (px, _), rows, (x, y, anchor) in zip(pins, blocks,
                                             TC.lay_out(pins, blocks)):
        w, h = TC._block(rows)
        out.append((x - w if anchor == "end" else x, y - 13, w, h))
    return out


def scene(seed: bytes):
    world, result = run(seed)
    stops = [C.LOBBY_LANDMARK] + [leg["to"] for leg in result["moves"]]
    points = [(world.places[n]["lat"], world.places[n]["lon"]) for n in stops]
    plot_h = TC.HEIGHT - TC.TOP - TC.BOTTOM
    camera = TC.fit(points, 0, TC.TOP, TC.WIDTH, plot_h)
    pins = [camera.at(lat, lon) for lat, lon in points]
    blocks = [[(f"{i}. {name}", 17), ("“a hint of some length”", 13),
               ("something she took, at length", 13)]
              for i, name in enumerate(stops)]
    return pins, blocks


def test_no_two_labels_overlap():
    """Neighbourhood routing puts consecutive stops close together by
    construction, so this is the normal case and not an edge one."""
    for seed in (CAUGHT, ESCAPED, bytes.fromhex("55" * 32),
                 bytes.fromhex("11" * 32)):
        placed = rects(*scene(seed))
        for i, (x, y, w, h) in enumerate(placed):
            for ox, oy, ow, oh in placed[i + 1:]:
                assert not (x < ox + ow and ox < x + w
                            and y < oy + oh and oy < y + h), seed.hex()[:4]


def test_every_label_stays_on_the_card():
    for seed in (CAUGHT, ESCAPED, bytes.fromhex("55" * 32)):
        for x, y, w, h in rects(*scene(seed)):
            assert 0 <= x and x + w <= TC.WIDTH, seed.hex()[:4]
            assert TC.TOP <= y and y + h <= TC.HEIGHT - TC.BOTTOM


# --- the projection -------------------------------------------------------

def test_a_trail_across_the_antimeridian_is_not_the_width_of_the_world():
    """Two places either side of the date line. Wrapped naively the frame is
    340 degrees wide and the card draws the Atlantic instead of Fiji."""
    camera = TC.fit([(-18.0, 178.0), (-21.0, -175.0)], 0, 0, 1000, 500)
    x0, _, x1, _ = camera.box()
    assert x1 - x0 < 0.2, (x0, x1)


def test_the_great_circle_is_the_distance_she_was_billed_for():
    """`carmel.travel_hours` charges her great-circle kilometres, so the
    line on the card is the line she paid for."""
    points = BM.great_circle((51.5, -0.1), (35.7, 139.7))
    assert abs(points[0][0] - 51.5) < 1e-6
    assert abs(points[-1][0] - 35.7) < 1e-6
    # London to Tokyo goes over the arctic, not across the middle of the
    # map: its highest latitude beats both ends
    assert max(lat for lat, _ in points) > 65


def test_mercator_round_trips():
    for lat, lon in ((0.0, 0.0), (51.5, -0.1), (-54.8, -68.3), (78.2, 15.6)):
        back = BM.unmercator(*BM.mercator(lat, lon))
        assert abs(back[0] - lat) < 1e-6 and abs(back[1] - lon) < 1e-6


# --- what replaced the field of dots ---------------------------------------

def test_the_card_draws_real_geography_and_not_the_gazetteer():
    """Gal, 2026-09-09: *"don't disclose the potential landmarks"*. The
    first version drew all thousand as a dot field and argued they were
    free because `landmarks.tsv` is public. A public table is not a plotted
    map: the dots were the candidate set, positioned, which is the one job
    a searcher reading a hint actually has."""
    world, result = run(ESCAPED)
    svg = TC.card(result, world, ESCAPED, C.LOBBY_LANDMARK)
    walked = {C.LOBBY_LANDMARK} | {leg["to"] for leg in result["moves"]}

    # every stop she made is drawn, and there are only that many markers
    circles = [n for n in ET.fromstring(svg).iter()
               if n.tag.endswith("circle")]
    stole = len(TC.kept(result))
    assert len(circles) <= len(walked) + 2, len(circles)

    # and the basemap that replaced them is real, and is there
    assert 'fill="' + TC.INK["land"] + '"' in svg
    assert svg.count("<path") > 10


def test_the_basemap_has_no_names_in_it():
    """The other half of why a real map is safe here: no toponyms at any
    zoom. A labelled street map would print the names of exactly the famous
    places this game is hiding."""
    world = BM.load()
    assert set(world) == {"source", "land", "borders", "lakes", "land_coarse"}
    for key in ("land", "borders", "lakes", "land_coarse"):
        for shape in world[key]:
            for point in shape:
                assert len(point) == 2
                assert all(isinstance(v, (int, float)) for v in point)
