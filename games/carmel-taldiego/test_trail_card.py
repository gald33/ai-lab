"""What the card must not get wrong, and what it must not show.

    python3 -m pytest games/carmel-taldiego/test_trail_card.py -q

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

*The world panel's six were run the same way, 2026-09-12*, and the runs are
worth listing because one of them came back green and had to be replaced:
scaling the world camera by 1.4 (the panel stops being the whole world),
dropping the widening loop (a polar stop off the card), returning only turn
zero from `laid` (the seam drawn as one path), putting `leader` back to the
chrome's `rule` (leaders invisible), and dropping `top=` at `lay_out`'s call
site (labels on the world) each go red.

**Disabling the caption's flip did not**, because on every seed this file
draws she stays left of centre and the caption never has to move -- an
untaken branch asserted by a test that looked like it covered it, which is
`CLAUDE.md`'s "absence drawn as a pass" in miniature. The frame that
exercises it is built by hand in
`test_the_span_caption_flips_when_the_frame_is_against_the_edge`.
"""

import re
import sys
import xml.etree.ElementTree as ET

import pytest
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

def rects(pins, blocks, detail_y, height):
    # The card grows with the campaign (`trail_card.card_height`), so the
    # layout has to be checked against the height actually drawn. Checking
    # it against the 640 default was checking a card nobody renders.
    out = []
    for (px, _), rows, (x, y, anchor) in zip(
            pins, blocks,
            TC.lay_out(pins, blocks, height, top=int(detail_y))):
        w, h = TC._block(rows)
        out.append((x - w if anchor == "end" else x, y - 13, w, h))
    return out


def scene(seed: bytes):
    """The lower panel exactly as `card` builds it: the world's height
    decides where it starts, so a scene that assumed `TOP` would be
    checking a panel the card does not draw."""
    world, result = run(seed)
    stops = [C.LOBBY_LANDMARK] + [leg["to"] for leg in result["moves"]]
    points = [(world.places[n]["lat"], world.places[n]["lon"]) for n in stops]
    globe = TC.world_camera(points, TC.TOP)
    detail_y = TC.TOP + globe.h
    plot_h = TC.plot_height(len(stops))
    camera = TC.fit(points, 0, detail_y, TC.WIDTH, plot_h)
    pins = [camera.at(lat, lon) for lat, lon in points]
    blocks = [[(f"{i}. {name}", 17), ("“a hint of some length”", 13),
               ("something she took, at length", 13)]
              for i, name in enumerate(stops)]
    return pins, blocks, detail_y, TC.card_height(len(stops), globe.h)


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
        pins, blocks, detail_y, height = scene(seed)
        for x, y, w, h in rects(pins, blocks, detail_y, height):
            assert 0 <= x and x + w <= TC.WIDTH, seed.hex()[:4]
            assert TC.TOP <= y and y + h <= height - TC.BOTTOM


def test_no_label_lands_on_the_world():
    """The card draws the same campaign twice, at two scales. A label is
    about a pin in the lower panel, and a label that drifts onto the world
    sits beside a 2px dot that is a *different* stop -- so the writing ends
    up on the wrong drawing, which is worse than the crowding it escaped.

    It reads the drawn card rather than `lay_out`, and that is the whole
    point of it: `lay_out` honours whatever `top` it is handed, so a test
    that hands it one is asserting its own argument. What can go wrong is
    the *call*, and dropping `top=` in `card` is how this was found.

    The one thing allowed to be written on the world is the span caption,
    which is about the frame and not about a stop."""
    for seed in (CAUGHT, ESCAPED, bytes.fromhex("55" * 32),
                 bytes.fromhex("11" * 32)):
        world, result = run(seed)
        stops = [C.LOBBY_LANDMARK] + [leg["to"] for leg in result["moves"]]
        points = [(world.places[n]["lat"], world.places[n]["lon"])
                  for n in stops]
        detail_y = TC.TOP + TC.world_camera(points, TC.TOP).h
        for node in ET.fromstring(
                TC.card(result, world, seed, C.LOBBY_LANDMARK)).iter():
            if not node.tag.endswith("text"):
                continue
            y = float(node.get("y"))
            if TC.TOP <= y < detail_y:
                assert (node.text or "").endswith("KM AROUND"), (
                    f"{node.text!r} is written on the world")


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

def test_the_command_in_the_docstring_runs():
    """Every other test in this file calls `card`, and `main` is what a
    reader is told to run. #264 renamed a leg's hint to its details and left
    `main`'s summary raising `KeyError` after the card had been written --
    green suite, broken command, for as long as nobody typed it.

    A subprocess rather than a call, because the failure was in the script
    path: argument parsing, the write, and the print after it."""
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "card.svg"
        done = subprocess.run(
            [sys.executable, str(Path(TC.__file__)),
             "--seed", ESCAPED.hex(), "--out", str(out)],
            capture_output=True, text=True, timeout=300)
        assert done.returncode == 0, done.stderr[-2000:]
        assert out.read_text().startswith("<svg")
        assert "wrote" in done.stdout


# --- the world panel ------------------------------------------------------

def test_the_world_panel_is_the_whole_world():
    """Not most of it. A world map that quietly cropped east and west would
    still look like a world map, and would be drawing a claim about where
    she can be."""
    globe = TC.world_camera([(48.0, 2.0)], TC.TOP)
    left, top, right, bottom = globe.box()
    assert right - left == pytest.approx(1.0), "one turn of the world"
    assert top == pytest.approx(BM.mercator(TC.NORTH, 0.0)[1])
    assert bottom == pytest.approx(BM.mercator(TC.SOUTH, 0.0)[1])
    assert globe.h == pytest.approx((bottom - top) * TC.WIDTH)


def test_a_stop_outside_the_band_widens_it():
    """Mercator has no poles to draw, so the band stops somewhere; one
    landmark of the thousand is north of it. A fixed frame would put her pin
    off the card, and a card that loses a stop is worse than a tall one."""
    far = 78.24                      # the northernmost landmark in the map
    globe = TC.world_camera([(48.0, 2.0), (far, 15.0)], TC.TOP)
    _, top, _, bottom = globe.box()
    assert top < BM.mercator(far, 15.0)[1] < bottom
    x, y = globe.at(far, 15.0)
    assert TC.TOP < y < TC.TOP + globe.h, "the polar stop is on the panel"


def test_a_leg_across_the_seam_is_drawn_at_both_edges():
    """Kamchatka to Alaska is a short hop east and 0.96 -> 0.03 in the
    projection. `fit` has unwrapped the *stops* since the card was written;
    nothing was unwrapping the line between them, so the leg was drawn back
    across the Atlantic -- invisible while every campaign was European.

    A whole-world panel is where that finally shows, and where the fix is
    not a single path: the leg leaves one edge of the world and arrives at
    the other, so it is two."""
    globe = TC.world_camera([(53.0, 158.0), (57.0, -153.0)], TC.TOP)
    line = [BM.mercator(lat, lon) for lat, lon in
            BM.great_circle((53.0, 158.0), (57.0, -153.0))]
    assert len(TC.laid(globe, line)) == 2

    # and the naive drawing is the thing being ruled out: unwrapped, the
    # leg spans the 49 degrees between them, not the 311 the other way
    xs = TC.unwrap([x for x, _ in line])
    assert max(xs) - min(xs) == pytest.approx(49 / 360, abs=0.01)


def test_a_leader_is_visible_against_the_map_it_crosses():
    """`CLAUDE.md`: a check is green for the reason it names. The leaders
    were drawn in `rule`, which is the chrome's hairline and darker than
    both the land and the sea it has to cross -- so every test about label
    placement passed while the labels had, on screen, nothing joining them
    to their pins."""
    def luminance(colour: str) -> float:
        r, g, b = (int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    leader = luminance(TC.INK["leader"])
    for under in ("land", "sea", "ground"):
        assert leader > luminance(TC.INK[under]) + 0.06, under

    # A leader is only drawn when a label had to move, so the other half of
    # this check needs a card that moved one -- and campaign shape is
    # downstream of every parameter in `carmel.py`, which is why the seed is
    # **found and not named**. It was named once: the hint became a riddle
    # (#264), campaigns fell from eighteen legs to two, and a check that had
    # been about ink went quietly green about nothing. Running out of seeds
    # is a failure here rather than a skip, for the same reason.
    for n in range(0x10, 0x40):
        drawn = draw(bytes([n]) * 32)
        if f'stroke="{TC.INK["leader"]}"' in drawn:
            break
    else:
        raise AssertionError("no campaign in 48 seeds displaced a label; "
                             "this half of the check is asserting nothing")


def test_the_span_caption_stays_on_the_card():
    """It is written beside the frame it describes rather than in a corner,
    which means it moves -- and a caption that runs off the edge is the
    failure mode that costs the panel its whole point."""
    for seed in (CAUGHT, ESCAPED, bytes.fromhex("55" * 32)):
        world, result = run(seed)
        svg = TC.card(result, world, seed, C.LOBBY_LANDMARK)
        caption = [n for n in ET.fromstring(svg).iter()
                   if n.tag.endswith("text")
                   and (n.text or "").endswith("KM AROUND")]
        assert len(caption) == 1
        x = float(caption[0].get("x"))
        width = len(caption[0].text) * 11 * TC.GLYPH
        assert 20 <= x <= TC.WIDTH - 20
        if caption[0].get("text-anchor") == "start":
            assert x + width <= TC.WIDTH
        else:
            assert x - width >= 0


def test_the_span_caption_flips_when_the_frame_is_against_the_edge():
    """The loop above is not enough on its own and saying why is the point:
    on every seed it draws, the campaign sits left of centre and the caption
    never has to move, so disabling the flip leaves it green. A campaign in
    the far east of the map is the case that exercises it, and the frame is
    built here rather than hunted for in a seed."""
    globe = TC.world_camera([(35.0, 139.0)], TC.TOP)
    text = "18,000 KM ACROSS, ON A WORLD 40,075 KM AROUND"
    against_the_edge = [(TC.WIDTH - 60.0, 300.0, 40.0, 30.0)]
    drawn = TC._caption(against_the_edge, globe, text)
    x = float(re.search(r'x="([-\d.]+)"', drawn).group(1))
    assert 'text-anchor="end"' in drawn, "it stayed on the right of the frame"
    assert x - len(text) * 11 * TC.GLYPH >= 0, "and ran off the card"


def test_the_card_draws_real_geography_and_not_the_gazetteer():
    """Gal, 2026-09-09: *"don't disclose the potential landmarks"*. The
    first version drew all thousand as a dot field and argued they were
    free because `landmarks.tsv` is public. A public table is not a plotted
    map: the dots were the candidate set, positioned, which is the one job
    a searcher reading a hint actually has."""
    world, result = run(ESCAPED)
    svg = TC.card(result, world, ESCAPED, C.LOBBY_LANDMARK)
    stops = [C.LOBBY_LANDMARK] + [leg["to"] for leg in result["moves"]]

    # Every stop she made is drawn, and nothing else is, so the count is
    # stated exactly rather than as a ceiling. It used to read
    # `<= len(walked) + 2` against the *set* of rooms, and the slack was
    # doing two jobs it never named: the inset's locator, and a ring on the
    # room she is caught in. Both turned up at once when
    # `REPUTATION_TO_WIN` moved to 750 -- longer campaigns revisit a room
    # she did not empty, which shrinks the set below the trail, and catches
    # stopped being rare. A ceiling that is met by a coincidence is
    # `CLAUDE.md`'s third shape; this counts what is drawn.
    #
    # *Recounted 2026-09-12*, when the world became the card's main panel:
    # every stop is now drawn twice, once on each panel, and the locator's
    # single circle is gone with the inset it marked. The count is still
    # stated exactly, and it is still the whole of what the card plots.
    extras = 1 if result["outcome"] == "caught" else 0
    circles = [n for n in ET.fromstring(svg).iter()
               if n.tag.endswith("circle")]
    assert len(circles) == 2 * len(stops) + extras, (
        f"{len(circles)} circles for {len(stops)} stops"
        f" on a {result['outcome']} campaign")

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
