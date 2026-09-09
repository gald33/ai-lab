"""What the card must not get wrong, and what it must not show.

    python3 -m pytest games/hue-and-cry/test_trail_card.py -q

Two of these guard arithmetic and the rest guard a design decision, which
is unusual for a test file and is the point of this one. `trail_card.py`
refuses to draw her exits because `games/hue-and-cry.md` leaves the
routes-public question open and a picture of the routes decides it. A
refusal that only lives in a docstring is a refusal somebody adds a flag to
on a quiet afternoon, so it is asserted here instead.

Every test below has been made to fail on purpose, per `CLAUDE.md`'s "a
check is green for the reason it names": the accounting ones by reverting
`kept` to `leg["dwell"]`, the layout ones by returning the naive
right-of-the-pin position, and the refusal ones by drawing the exits.
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import trail_card as TC  # noqa: E402

#: A seed whose campaign ends in an arrest, and one where she gets away.
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
    """The catch is walking in while she is still standing there, so the
    final room of a caught campaign is always one she was mid-theft in.
    Counting it puts the card's header at odds with `chase`'s own total."""
    world, result = run(CAUGHT)
    assert result["outcome"] == "caught"
    legs = result["moves"]
    assert legs[-1]["dwell"], "this seed no longer catches her mid-theft"
    assert len(legs) - 1 not in TC.kept(result)

    banked = sum(world.treasure[legs[i]["to"]]["reputation"]
                 for i in TC.kept(result))
    assert banked == result["reputation"]


def test_a_campaign_she_wins_banks_every_room_she_dwelt_in():
    """The other side of it, so the fix above cannot be 'never credit the
    last room'."""
    world, result = run(ESCAPED)
    assert result["outcome"] != "caught"
    legs = result["moves"]
    assert TC.kept(result) == {i for i, leg in enumerate(legs) if leg["dwell"]}
    assert sum(world.treasure[legs[i]["to"]]["reputation"]
               for i in TC.kept(result)) == result["reputation"]


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

def test_it_never_asks_the_map_for_an_exit():
    """The routes-public question is open (`games/hue-and-cry.md`, "Which
    makes the exit count a choice about how big a game this is"). Drawing
    them answers it, so the card does not have them to draw."""
    world, result = run(ESCAPED)

    def refuse(_landmark):
        raise AssertionError("the card asked for an exit")

    world.exits = refuse
    TC.card(result, world, ESCAPED, C.LOBBY_LANDMARK)


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
    frame = TC.Frame(TC.window(points, TC.WIDTH / plot_h),
                     0, TC.TOP, TC.WIDTH, plot_h)
    pins = [frame.at(lat, lon) for lat, lon in points]
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
    """Two places 3,000 km apart either side of the date line. Wrapped
    naively the box is 340 degrees wide and the card draws the Atlantic."""
    box = TC.window([(-18.0, 178.0), (-21.0, -175.0)], 2.0)
    assert box[3] - box[1] < 60


def test_the_great_circle_is_the_distance_she_was_billed_for():
    """`carmel.travel_hours` charges her great-circle kilometres, so the
    line on the card is the line she paid for."""
    a = {"lat": 51.5, "lon": -0.1}
    b = {"lat": 35.7, "lon": 139.7}
    points = TC.arc(a, b)
    assert abs(points[0][0] - a["lat"]) < 1e-6
    assert abs(points[0][1] - a["lon"]) < 1e-6
    assert abs(points[-1][0] - b["lat"]) < 1e-6
    # a great circle from London to Tokyo goes over the arctic, not through
    # the middle of the map: its highest latitude beats both endpoints
    assert max(lat for lat, _ in points) > 65
