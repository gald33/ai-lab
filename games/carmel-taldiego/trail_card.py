"""The trail she left, drawn, for the post that closes a campaign.

    python3 games/carmel-taldiego/trail_card.py --out /tmp/trail.svg

Gal, 2026-09-09: *"I wonder if we want to show the map visually"*. The
answer this file is the buildable half of is in `games/carmel-taldiego.md`,
"Three maps, and only one of them is the map" -- which says that there are
three different pictures hiding behind the word "map", that two of them are
safe and one of them decides an open question, and that this is the one
worth drawing first.

WHAT IT DRAWS, AND WHAT IT REFUSES TO. It draws the landmarks (public,
committed in `landmarks.tsv`), the path she actually walked, the hint she
posted on arrival at each stop, and what she took there. Every one of those
is already published by `close_campaign` -- the seed goes in that post, and
with the seed a reader can re-derive all of it -- so **the card is a
post-reveal artifact and nothing else**. Handed out mid-campaign it would
publish the trail to searchers who had not earned it.

**It did not draw her exits, and there are no longer exits to draw.** Gal,
2026-09-09: *"we have no routes."* The refusal below was right and is now
moot; what survives it is the reason it was a refusal rather than a flag.
`games/carmel-taldiego.md`, "Which makes the exit count a choice about how big
a game this is", leaves open whether the routes are public: routes-public
is a two-person deduction game with a 352 KB entry requirement, no-routes
is a fifty-person search game with none, and *"that is Gal's to make rather
than mine to assume"*. A picture of the routes is that decision, made by
whoever drew the picture. So the drawing stops at the trail, which is
settled, and a `--routes` flag is deliberately absent rather than defaulted
off -- an off-by-default flag is the same decision waiting to be flipped by
somebody who does not know it is a decision.

WHY THERE IS AN INSET, WHICH IS A FINDING AND NOT A DESIGN FLOURISH.
Measured over 60 campaigns while answering the question above:

    legs per campaign   median 3     (min 1, max 4)
    campaign span       median 2,914 km   (max 13,681 km)
    countries visited   median 4

A campaign happens inside a box about 2,900 km across on a map 40,000 km
around, so a whole-world drawing renders the entire chase as a smudge three
pixels wide. The card is therefore the box, at a readable scale, with the
world as an inset saying where the box is. That the chase never leaves one
corner of the map is a property the numbers in that document had not
surfaced, and it was drawing it that surfaced it. Re-check both rows with
`--survey`.

    THE PARAGRAPH ABOVE IS SUPERSEDED, 2026-09-12, AND KEPT WHERE IT STOOD
    because its measurement is the one that was quoted onward. Gal: *"I want
    a world map."* The world is the card's main panel now and the box is the
    panel below it, which is the same two pictures with their sizes swapped.

    **The smudge is not what stops a world drawing, and never was.** Over
    200 campaigns (`--survey`, which prints these two rows now precisely so
    that the next claim about a drawing is measured):

        world-scale extent   median 46.2 px   min 0.2   max 288.8
        closest two stops    median 11.7 px   min 0.0   max 110.1

    Legible, and nothing like three pixels -- the six published seeds run 14
    to 155px. What does not fit at that scale is the *writing*: a median
    campaign is a twentieth of the card wide and a stop's label is 17px
    tall on three lines, so a card that only showed the world would be a
    world with an unreadable pile in one corner of it. The long tail is
    worse and in the other direction -- nineteen legs, with two stops on the
    same pixel. **Extent was never the obstruction**, and an enlarged panel
    is what answers the thing that is.

    *Measured twice in one sitting, and it moved both times, which is the
    part to keep.* The first run said 106.8px and 2.9px, over campaigns of
    13 legs; then the hint became a riddle (#264), campaigns fell to a
    median of 2.5 legs, and the same command said 46.2px and 11.7px. Nothing
    was wrong with either. **Campaign shape is downstream of every parameter
    in `carmel.py`, so it is a thing to measure and never a thing to
    quote** -- `games/carmel-taldiego.md` has said so under "Framing it
    found the thing the numbers had not said" since the third time it
    happened, and this is the fourth.

    The old numbers are also a campaign shape the game no longer has -- 3
    legs became 15-21 when `REPUTATION_TO_WIN` was calibrated to 750 -- so
    the rows above are a 2026-09-09 game, correct when measured. Both sets
    are re-checked by `--survey`, which now prints the world-scale pixels
    too rather than leaving a claim about a drawing to be eyeballed.

THE BASEMAP WAS THE GAZETTEER, AND THAT WAS A DISCLOSURE. The first
version of this file drew the thousand landmarks as a field of faint dots
and argued they were free, since `landmarks.tsv` is public. Gal,
2026-09-09: *"don't disclose the potential landmarks"* -- and he is right
against the argument, not merely overruling it. **A public table is not a
plotted map.** The dots were the candidate set, positioned, which is the
one piece of work a searcher reading a hint actually has to do; the card
was doing it for them and calling it a background. Nothing was leaked that
could not have been derived, and the card still handed it over.

So the basemap is real geography now -- coastlines, borders and lakes from
Natural Earth, committed in `basemap.json`, **with no place names on it at
all**. That last part is what makes it safe rather than merely different:
a labelled street map would have named Fez and Bergen and Ushuaia at this
zoom, which discloses more than the dots ever did. `build_basemap.py` has
the rest of that argument, including why not Google's tiles.

The geography earns its place beyond looking real: the vocabulary a hint
is drawn from is `coastal`, `landlocked`, `far_from_the_equator`,
`no_passport_needed_next_door`. A coastline and a border are the picture of
exactly those words.

It emits static SVG with no script in it, so `CLAUDE.md`'s browser rule
("anything a page *does* is asserted in a real browser") does not apply:
the card does nothing, it only says. `test_trail_card.py` asserts on the
markup for that reason and would be the wrong test for a card that moved.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import basemap as BM  # noqa: E402
import imagery as IM  # noqa: E402
import carmel as C  # noqa: E402

#: The card, in pixels. 2:1-ish, which is what a timeline crops to.
WIDTH, HEIGHT = 1000, 640

#: How tall the card grows when a campaign has more stops than 640 can
#: label. **A longer campaign needs a taller card**, and campaigns got
#: longer on 2026-09-10 when `REPUTATION_TO_WIN` was calibrated from 140 to
#: 750 -- two legs became twelve, and the seeds this file draws run to
#: seventeen stops needing 1,020px of label in 492px of plot.
#:
#: Two columns do not save it: the widest block on that card is 460px, so
#: two fit across 1000px but stack to 984px, still short. Nothing about the
#: layout was wrong -- the card was sized for the campaign the game used to
#: have.
def plot_height(stops: int) -> int:
    """The enlarged panel: tall enough that every stop's label has somewhere
    to go."""
    return max(HEIGHT - TOP - BOTTOM, 40 + 60 * ((stops + 1) // 2))


def card_height(stops: int, world_h: float) -> int:
    """The whole card: title strip, the world, the enlarged box, footer.

    `world_h` is a campaign's, not a constant, because a stop outside the
    band widens it (`world_camera`).
    """
    return int(TOP + round(world_h) + plot_height(stops) + BOTTOM)

#: Space kept clear for the title strip and the footer.
TOP, BOTTOM = 92, 56

#: How much room to leave around the trail's bounding box, as a fraction of
#: its longer side. Below about 0.15 the end stops sit on the frame and
#: their labels have nowhere to go.
PAD = 0.28

#: The root the surveys draw their seeds from, so a number quoted in
#: `games/carmel-taldiego.md` is one the command reproduces rather than one it
#: resembles. The maps are still drawn -- 200 of them -- this only fixes
#: *which* 200, which is the difference between a measurement and an
#: anecdote. `--seed` varies it, and a number that moves much when it does
#: is a number that wanted more trials.
SURVEY_ROOT = bytes.fromhex("5e ed 00 00".replace(" ", "") * 8)

#: The world band's north and south edges, in degrees.
#:
#: **A whole-world Mercator panel is always a choice about where to stop**,
#: since the projection runs to infinity at the poles. The band is fixed
#: rather than fitted to the campaign, for two reasons: six published cards
#: are then the same map six times, which is what lets a reader compare them
#: at a glance; and a fitted band would be a statement about where the
#: thousand landmarks are, which is the one thing this card does not say.
#:
#: It widens for a stop outside it -- one landmark in the thousand sits
#: north of 75 -- and that discloses nothing her own published trail does
#: not. See `world_camera`.
NORTH, SOUTH = 75.0, -56.0

#: Room left around a stop that widened the band, in unit-square terms:
#: about 12px at `WIDTH`, so a polar pin is not welded to the frame.
POLAR_MARGIN = 0.012

INK = {
    "ground": "#14110e",     # the card's chrome: title strip and footer
    "sea": "#0d151b",        # water, and the plot area's floor
    "land": "#312c24",       # the real world, Natural Earth
    "border": "#544a3c",  # country borders, hairline
    "frontier": "#ffd9a0",   # the same, over a photograph
    "line": "#e0a34a",       # her trail
    "stop": "#f2e4cf",
    "text": "#f2e4cf",
    "dim": "#94897a",
    "theft": "#d4573f",
    "rule": "#2a241e",
    # A leader joins a label to its pin, and `rule` is not a colour that can
    # do that: it is the chrome's hairline, chosen against the title strip,
    # and over the map it is darker than the land it crosses. At three stops
    # nobody noticed; at eighteen, half the labels float free of the trail
    # and the card stops saying which room it is talking about.
    "leader": "#6d6052",
}


# --- the camera -----------------------------------------------------------

def unwrap(xs: list[float]) -> list[float]:
    """Mercator x values made continuous, so a trail across the
    antimeridian has a frame instead of one the width of the world.
    Reykjavik to Fiji is a short hop east, not a 340-degree one."""
    out = [xs[0]]
    for x in xs[1:]:
        previous = out[-1]
        out.append(min((x + turn for turn in (-1.0, 0.0, 1.0)),
                       key=lambda candidate: abs(candidate - previous)))
    return out


class Camera:
    """A viewport onto the Mercator unit square: a centre and one scale.

    Under Mercator zoom is a single number, which is what makes this a
    class with three fields instead of the per-latitude correction the
    equirectangular version needed (`basemap.py` says why).
    """

    def __init__(self, cx, cy, scale, x, y, w, h):
        self.cx, self.cy, self.scale = cx, cy, scale
        self.x, self.y, self.w, self.h = x, y, w, h

    def unit(self, point) -> tuple[float, float]:
        """A projected (x, y) in the unit square, to pixels."""
        return (self.x + self.w / 2 + (point[0] - self.cx) * self.scale,
                self.y + self.h / 2 + (point[1] - self.cy) * self.scale)

    def at(self, lat: float, lon: float) -> tuple[float, float]:
        return self.unit(BM.mercator(lat, lon))

    def box(self) -> tuple[float, float, float, float]:
        """What it can see, in unit-square coordinates."""
        return (self.cx - self.w / 2 / self.scale,
                self.cy - self.h / 2 / self.scale,
                self.cx + self.w / 2 / self.scale,
                self.cy + self.h / 2 / self.scale)


def fit(points: list[tuple[float, float]], x, y, w, h,
        pad: float = PAD) -> Camera:
    """A camera holding every (lat, lon) in `points`, with room to label."""
    projected = [BM.mercator(lat, lon) for lat, lon in points]
    xs = unwrap([px for px, _ in projected])
    ys = [py for _, py in projected]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    half_x = max((max(xs) - min(xs)) / 2, 1e-5) * (1 + pad)
    half_y = max((max(ys) - min(ys)) / 2, 1e-5) * (1 + pad)
    return Camera(cx, cy, min(w / (2 * half_x), h / (2 * half_y)),
                  x, y, w, h)


def world_camera(points: list[tuple[float, float]], y: float) -> Camera:
    """The whole world at the card's full width, `NORTH` to `SOUTH`.

    Gal, 2026-09-11: *"I want a world map."* This is the card's main panel
    and `fit` draws the panel below it, which is the same two pictures the
    card always had with their sizes swapped -- see the correction in this
    module's docstring for why the measurement that demoted the world was
    answering a question nobody had asked.

    The camera is the locator inset's, widened: scale is `WIDTH`, so one
    turn of the world is exactly the card, and the band decides the height.
    """
    top, bottom = BM.mercator(NORTH, 0.0)[1], BM.mercator(SOUTH, 0.0)[1]
    for lat, lon in points:
        py = BM.mercator(lat, lon)[1]
        top, bottom = min(top, py - POLAR_MARGIN), max(bottom,
                                                       py + POLAR_MARGIN)
    return Camera(0.5, (top + bottom) / 2, WIDTH, 0, y, WIDTH,
                  (bottom - top) * WIDTH)


def laid(camera: Camera, projected: list[tuple[float, float]]) -> list[str]:
    """A polyline as SVG paths, one per turn of the world the camera sees.

    Two jobs in one function, and the second is a bug fix. Mercator x is
    cyclic, so a line from Kamchatka to Alaska runs 0.96 -> 0.03 in the
    projection and draws, naively, all the way back across the Atlantic:
    `unwrap` makes it continuous first. Then the continuous line is emitted
    at whichever turns overlap the frame -- usually one, and two for a leg
    that crosses the seam, which a whole-world panel can show at both edges
    and the box panel never could.

    `fit` already unwrapped the *stops* to choose the frame
    (`test_a_trail_across_the_antimeridian_is_not_the_width_of_the_world`);
    nothing was doing it for the line between them.
    """
    xs = unwrap([x for x, _ in projected])
    ys = [y for _, y in projected]
    left, _, right, _ = camera.box()
    out = []
    for turn in (-1.0, 0.0, 1.0):
        if min(xs) + turn <= right and max(xs) + turn >= left:
            out.append(BM.path([(x + turn, y) for x, y in zip(xs, ys)],
                               camera.unit))
    return out


def whole_world(camera: Camera) -> list[str]:
    """The world at a glance, from the coarse layer the locator inset used.

    1,958 points against the detailed layer's 29,949. **Decimation is
    honest here in a way it was not for the flight**, whose level-of-detail
    scheme was built and deleted because every zoom closer than the crushed
    one still needs the real coastline (`games/carmel-taldiego.md`, "Two
    schemes to make the page lighter"). A still card never zooms, and at
    1000px for the whole world the fine coastline is sub-pixel anyway.

    No borders: at this width they are a grey haze over the land, and the
    panel below draws them where `no_passport_needed_next_door` can be read.
    """
    return [f'<path d="{BM.path([BM.mercator(lat, lon) for lon, lat in shape], camera.unit, close=True)}"'
            f' fill="{INK["land"]}"/>'
            for shape in BM.load()["land_coarse"]]


#: Rough width of a glyph as a fraction of the font size, for Georgia. Only
#: used to decide which side of a pin a label goes on, so it needs to be
#: about right rather than right -- but too small is the dangerous
#: direction, since it puts text off the card.
GLYPH = 0.52


def _block(rows) -> tuple[float, float]:
    """A label block's width and height in pixels, near enough to lay out."""
    width = max((len(text) * size * GLYPH for text, size in rows if text),
                default=0.0)
    height = 6 + 18 * sum(1 for text, _ in rows if text)
    return width, height


def lay_out(pins, blocks, height: int = HEIGHT, top: int = TOP
            ) -> list[tuple[float, float, str]]:
    """Where each stop's label goes: (x, y-of-first-line, text-anchor).

    `top` is the first row the labels may use. It is a parameter since the
    world panel arrived: a label that is free to go anywhere goes onto the
    world map, beside a 2px pin that is not the pin it belongs to, and the
    card then has two drawings of the same campaign with the writing on the
    wrong one.

    THIS IS NOT DECORATION AND THE FIRST TWO VERSIONS WERE WRONG IN THE SAME
    WAY. The first put a label left of its pin on the right third of the
    card -- a threshold that was right for the trail it was written against
    and ran the next one off the edge. The second measured the block and
    still overlapped Rhine Falls with Wieskirche, 170 km apart, because it
    placed every label independently.

    Neighbourhood routing is what makes that the normal case rather than
    bad luck: exits are drawn from a landmark's look-alikes, look-alikes are
    geographically clustered (measured: 3.2x enriched in the fifty nearest),
    so consecutive stops sit close together on the card *by construction*.
    A card that only reads when the trail is spread out is a card that only
    reads sometimes.

    So: candidates per pin, in preference order, first one that fits the
    card and clears every block already placed. A displaced label gets a
    leader line, which is why moving one is allowed to look like anything.
    """
    placed: list[tuple[float, float, float, float]] = []

    def clear(x, y, w, h):
        if x < 20 or x + w > WIDTH - 20 or y < top + 4 or y + h > height - BOTTOM:
            return False
        return all(not (x < ox + ow and ox < x + w
                        and y < oy + oh and oy < y + h)
                   for ox, oy, ow, oh in placed)

    out = []
    for (px, py), rows in zip(pins, blocks):
        w, h = _block(rows)
        chosen = None
        for dx, dy in ((12, -12), (12, -h - 4), (12, 8),
                       (-12, -12), (-12, -h - 4), (-12, 8),
                       (12, -h - 22), (-12, -h - 22), (12, 26), (-12, 26)):
            x = px + dx if dx > 0 else px + dx - w
            y = py + dy
            if clear(x, y, w, h):
                chosen = (x, y)
                break
        if chosen is None:
            # THE TEN CANDIDATES ABOVE ARE A TWO-STOP CARD'S WORTH. This
            # branch used to stack the block under the lowest one already
            # placed and clamp it to the card, which does not check `clear`
            # -- so the moment the clamp bit, two labels overlapped. It was
            # unreachable while `REPUTATION_TO_WIN` ended a campaign in two
            # legs, and the calibration to 750 made a campaign twelve legs
            # and reached it on the first seed tried.
            #
            # So: scan properly before giving up. Down each margin, at the
            # line spacing the blocks already use, first slot that clears.
            for x in (min(max(px + 12, 20), WIDTH - 20 - w),
                      20, WIDTH - 20 - w):
                y = top + 8
                while y + h <= height - BOTTOM:
                    if clear(x, y, w, h):
                        chosen = (x, y)
                        break
                    y += 8
                if chosen:
                    break
        if chosen is None:
            # The card is genuinely full. Overlapping is still wrong, so
            # this is the one case the test above cannot hold, and it is
            # left visible rather than papered over.
            x = min(max(px + 12, 20), WIDTH - 20 - w)
            y = min(max([oy + oh + 4 for ox, oy, ow, oh in placed]
                        or [top + 8]), height - BOTTOM - h)
            chosen = (x, y)
        placed.append((chosen[0], chosen[1], w, h))
        # the anchor sits on the edge of the block nearest its pin, so the
        # leader line has somewhere honest to end
        anchor = "start" if chosen[0] >= px else "end"
        out.append((chosen[0] + (w if anchor == "end" else 0),
                    chosen[1] + 13, anchor))
    return out


# --- the card -------------------------------------------------------------

def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def geometry(camera: Camera, over_imagery: bool = False) -> list[str]:
    """The real world inside a camera's frame, as SVG.

    Sea is the card's ground, so only land, lakes and borders are drawn.
    `basemap.near` has already cut every shape to the frame, so this is a
    few hundred points rather than the committed forty thousand.

    Over a photograph only the borders are drawn, brighter: the imagery has
    coastlines already and better ones, and a border is the single thing a
    photograph cannot show. `no_passport_needed_next_door` is a hint in this
    game's vocabulary, so it has to be visible.
    """
    cut = BM.near(camera.box(), keys=("borders",) if over_imagery
                  else ("land", "lakes", "borders"))
    out = []
    if over_imagery:
        for shape in cut["borders"]:
            out.append(f'<path d="{BM.path(shape, camera.unit)}" fill="none"'
                       f' stroke="{INK["frontier"]}" stroke-width="1"'
                       f' opacity="0.55"/>')
        return out
    for shape in cut["land"]:
        out.append(f'<path d="{BM.path(shape, camera.unit, close=True)}"'
                   f' fill="{INK["land"]}"/>')
    for shape in cut["lakes"]:
        out.append(f'<path d="{BM.path(shape, camera.unit, close=True)}"'
                   f' fill="{INK["sea"]}"/>')
    for shape in cut["borders"]:
        out.append(f'<path d="{BM.path(shape, camera.unit)}" fill="none"'
                   f' stroke="{INK["border"]}" stroke-width="0.8"'
                   f' opacity="0.7"/>')
    return out


def card(result: dict, world: C.Map, seed: bytes, start: str,
         imagery: str | None = None) -> str:
    """One finished campaign, drawn. `result` is `carmel.chase`'s.

    Two panels: the world, and the box on it that the campaign happened in,
    enlarged. `imagery` names a NASA GIBS layer to lay under both (see
    `imagery.py`); without one the basemap is the committed vectors.
    """
    legs = result["moves"]
    stops = [start] + [leg["to"] for leg in legs]
    places = [world.places[name] for name in stops]
    points = [(p["lat"], p["lon"]) for p in places]

    globe = world_camera(points, TOP)
    detail_y = TOP + globe.h
    plot_h = plot_height(len(stops))
    height = card_height(len(stops), globe.h)
    main = fit(points, 0, detail_y, WIDTH, plot_h)
    pins = [main.at(lat, lon) for lat, lon in points]
    projected = [BM.mercator(lat, lon) for lat, lon in points]

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}"'
           f' height="{height}" viewBox="0 0 {WIDTH} {height}"'
           f' font-family="Georgia, serif">',
           f'<rect width="{WIDTH}" height="{height}" fill="{INK["ground"]}"/>']

    # --- the world, and the frame the panel below enlarges ----------------
    svg += [f'<clipPath id="world"><rect y="{TOP}" width="{WIDTH}"'
            f' height="{globe.h:.0f}"/></clipPath>',
            f'<rect y="{TOP}" width="{WIDTH}" height="{globe.h:.0f}"'
            f' fill="{INK["sea"]}"/>',
            '<g clip-path="url(#world)">']
    if imagery:
        svg += IM.wrapper(WIDTH, int(globe.h), TOP,
                          IM.background(globe, imagery))
    else:
        svg += whole_world(globe)
    for a, b in zip(places, places[1:]):
        line = [BM.mercator(lat, lon) for lat, lon in
                BM.great_circle((a["lat"], a["lon"]), (b["lat"], b["lon"]))]
        for drawn in laid(globe, line):
            svg.append(f'<path d="{drawn}" fill="none"'
                       f' stroke="{INK["line"]}" stroke-width="1.4"'
                       f' stroke-linecap="round" opacity="0.9"/>')
    for px, py in (globe.unit(point) for point in projected):
        svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.2"'
                   f' fill="{INK["stop"]}"/>')

    frame = _frame(globe, projected)
    for fx, fy, fw, fh in frame:
        svg.append(f'<rect x="{fx:.1f}" y="{fy:.1f}" width="{fw:.1f}"'
                   f' height="{fh:.1f}" fill="none" stroke="{INK["dim"]}"'
                   f' stroke-width="1" stroke-dasharray="3 3"'
                   f' opacity="0.8"/>')
    svg.append('</g>')
    svg.append(_caption(frame, globe, _span(places)))

    # --- that box, enlarged -----------------------------------------------
    svg += [f'<clipPath id="plot"><rect y="{detail_y:.0f}" width="{WIDTH}"'
            f' height="{plot_h}"/></clipPath>',
            f'<rect y="{detail_y:.0f}" width="{WIDTH}" height="{plot_h}"'
            f' fill="{INK["sea"]}"/>',
            '<g clip-path="url(#plot)">']
    if imagery:
        svg += IM.wrapper(WIDTH, plot_h, int(detail_y),
                          IM.background(main, imagery))
    svg += geometry(main, over_imagery=bool(imagery))
    svg.append('</g>')

    # the trail
    emptied = kept(result)
    for index, (leg, a, b) in enumerate(zip(legs, places, places[1:])):
        line = [BM.mercator(lat, lon) for lat, lon in
                BM.great_circle((a["lat"], a["lon"]), (b["lat"], b["lon"]))]
        for drawn in laid(main, line):
            if imagery:
                svg.append(f'<path d="{drawn}" fill="none" stroke="#000"'
                           f' stroke-width="4.6" opacity="0.4"'
                           f' stroke-linecap="round"/>')
            svg.append(f'<path d="{drawn}" fill="none"'
                       f' stroke="{INK["line"]}" stroke-width="2.2"'
                       f' stroke-linecap="round"'
                       f' opacity="{0.95 if index in emptied else 0.5}"'
                       + ('' if index in emptied else ' stroke-dasharray="5 5"')
                       + '/>')

    # the stops, and what she said and took at each
    caught_at = len(legs) if result["outcome"] == "caught" else None
    blocks = []
    for i, name in enumerate(stops):
        leg = legs[i - 1] if i else None
        if not leg:
            last = ""
        elif i - 1 in emptied:
            last = world.treasure[name]["treasure"]
        elif i == caught_at:
            last = f'caught taking {world.treasure[name]["treasure"]}'
        else:
            last = "nothing taken"
        blocks.append([
            (f'{i}. ' + (name if i else f"{name}  — the lobby"), 17),
            (f'“{leg["details"][0].replace("_", " ")}”' if leg else "", 13),
            (last, 13),
        ])

    # over a photograph the ink needs its own edge; over the vector basemap
    # it would be a smudge round every letter for no reason
    halo = (' stroke="#0b0906" stroke-width="3" paint-order="stroke"'
            ' stroke-linejoin="round"') if imagery else ""
    for i, ((px, py), rows, (tx, ty, anchor)) in enumerate(
            zip(pins, blocks,
                lay_out(pins, blocks, height, top=int(detail_y)))):
        stole = i - 1 in emptied if i else False
        # a leader, when the label had to move away from its pin
        if abs(tx - px) > 26 or not (py - 22 < ty < py + 30):
            svg.append(f'<path d="M{px:.1f},{py:.1f} L{tx:.1f},'
                       f'{ty - 5:.1f}" stroke="{INK["leader"]}"'
                       f' stroke-width="1" opacity="0.8"/>')
        if i == caught_at:
            svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11"'
                       f' fill="none" stroke="{INK["theft"]}"'
                       f' stroke-width="1.6"/>')
        svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{6 if i else 5}"'
                   f' fill="{INK["theft"] if stole else INK["ground"]}"'
                   f' stroke="{INK["stop"]}" stroke-width="2"/>')
        line = 0
        for text, size in rows:
            if not text:
                continue
            final = text == rows[2][0] and rows[2][0]
            fill = (INK["stop"] if size == 17
                    else INK["theft"] if final and stole else INK["dim"])
            style = ' font-style="italic"' if final else ""
            svg.append(f'<text x="{tx:.1f}" y="{ty + line * 18:.1f}"'
                       f' fill="{fill}" font-size="{size}"'
                       f' text-anchor="{anchor}"{style}{halo}>'
                       f'{_esc(text)}</text>')
            line += 1

    # title and footer
    took = len(emptied)
    svg.append(f'<text x="34" y="46" fill="{INK["text"]}" font-size="30">'
               f'Carmel Taldiego, {_esc(result["outcome"])}</text>')
    svg.append(f'<text x="34" y="72" fill="{INK["dim"]}" font-size="15">'
               f'{len(legs)} rooms, {took} of them emptied,'
               f' {result["reputation"]} reputation,'
               f' {result["hours"]:.0f} hours</text>')
    svg.append(f'<text x="34" y="{height - 22}" fill="{INK["dim"]}"'
               f' font-size="12" font-family="monospace">'
               f'seed {seed.hex()}</text>')
    if imagery:
        svg.append(f'<text x="{WIDTH - 20}" y="{height - 22}"'
                   f' fill="{INK["rule"]}" font-size="10" text-anchor="end">'
                   f'{_esc(IM.CREDIT)}</text>')
    svg.append('</svg>')
    return "\n".join(svg)


def _frame(camera: Camera, projected: list[tuple[float, float]],
           margin: float = 12.0) -> list[tuple[float, float, float, float]]:
    """The dashed box on the world, in pixels -- one rect per turn of the
    world it is visible at, which is two when a campaign straddles the seam.

    `margin` is in pixels and the camera's scale is `WIDTH`, so the
    conversion is a division rather than a fudge factor.
    """
    xs = unwrap([x for x, _ in projected])
    ys = [y for _, y in projected]
    pad = margin / camera.scale
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    left, _, right, _ = camera.box()
    out = []
    for turn in (-1.0, 0.0, 1.0):
        if x0 + turn <= right and x1 + turn >= left:
            ax, ay = camera.unit((x0 + turn, y0))
            bx, by = camera.unit((x1 + turn, y1))
            out.append((ax, ay, bx - ax, by - ay))
    return out


def _caption(frame, camera: Camera, text: str) -> str:
    """The span, written beside the frame it describes.

    It has to be *beside* it: the whole point of the line is that the box is
    that small, and a caption in the corner of the panel is a statistic
    instead. So it goes right of the box, or left when that would run off
    the card, and above unless the box is against the top of the panel.
    """
    fx, fy, fw, fh = frame[0]
    width = len(text) * 11 * GLYPH + 1.2 * len(text)
    if fx + fw + 8 + width <= WIDTH - 20:
        x, anchor = fx + fw + 8, "start"
    elif fx - 8 - width >= 20:
        x, anchor = fx - 8, "end"
    else:
        x, anchor = 20, "start"
    y = fy - 7 if fy - 7 >= camera.y + 14 else fy + fh + 16
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{INK["dim"]}"'
            f' font-size="11" letter-spacing="1.2"'
            f' text-anchor="{anchor}">{_esc(text)}</text>')


def kept(result: dict) -> set[int]:
    """The indices into `moves` of the rooms she actually emptied.

    DRAWING THIS FOUND A BUG IN THE FIRST VERSION OF THIS FILE, which is the
    argument for drawing it. A leg's `dwell` is non-zero whenever she
    *started* a theft, and on a caught campaign she started the last one --
    the catch is walking in while she is still standing there, so the room
    she is caught in is always a room she is mid-theft in. Crediting her
    with it drew a card that disagreed with the scoreboard on the same page:
    `carmel.chase` returns `trail[caught_on - 1]["reputation"]`, her total
    BEFORE that room, and the header printed that number beside a map
    claiming she had emptied the room it excludes.

    So the last room of a caught campaign is a theft interrupted.
    """
    legs = result["moves"]
    interrupted = len(legs) - 1 if result["outcome"] == "caught" else -1
    return {i for i, leg in enumerate(legs)
            if leg["dwell"] and i != interrupted}


def _span(places: list[dict]) -> str:
    widest = max((C.travel_hours(a, b) * C.TRAVEL_KMH
                  for a in places for b in places), default=0.0)
    return f"{widest:,.0f} KM ACROSS, ON A WORLD 40,075 KM AROUND"


# --- the measurement the card's two panels rest on -------------------------

def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[int(q * (len(ordered) - 1))]


def geography(sample: int = 150, root: bytes = SURVEY_ROOT) -> None:
    """How much of the map's structure a geographic drawing would show.

    The answer decides what may honestly be drawn on a world projection.
    Routes are drawn from descriptor kinship (`games/carmel-taldiego.md`,
    "Routes run between places that resemble each other"), and kinship
    leans geographic without being geographic -- so a route network on a
    map would be a false picture of what is next to what, while a trail on
    one is just where she went.
    """
    import random
    import statistics

    world = C.Map(root)
    names = list(world.places)
    random.seed(int.from_bytes(root[:8], "big"))
    picked = random.sample(names, sample)

    def km(a, b):
        return C.travel_hours(a, b) * C.TRAVEL_KMH

    # SUPERSEDED APPARATUS, KEPT FINDING. This measured her five exits
    # against geography. Gal removed the exits the same afternoon -- "we
    # have no routes" -- so the question is asked of the thing that
    # replaced them: the candidates a hint leaves, which is what a searcher
    # now walks. The claim under test is unchanged and so is its answer.
    import gazetteer

    gaz = world.descriptors
    along = []
    for n in picked:
        hint = max(world.live_hints(n), key=world.cover.get)
        along += [km(world.places[n], world.places[m])
                  for m in gaz if m != n and hint in gaz[m]]
    apart = [km(world.places[a], world.places[b])
             for a, b in (random.sample(names, 2) for _ in range(3000))]

    print(f"over {sample} landmarks, every candidate the hint allows\n")
    print(f"  median distance to a place her hint also fits  "
          f"{statistics.median(along):7,.0f} km")
    print(f"  median distance between two landmarks at random "
          f"{statistics.median(apart):7,.0f} km")
    for near in (5, 50):
        hit = 0
        for n in picked:
            hint = max(world.live_hints(n), key=world.cover.get)
            close = {m for _, m in sorted(
                (km(world.places[n], world.places[m]), m)
                for m in names if m != n)[:near]}
            kin = {m for _, m in sorted((-gazetteer.kinship(n, m, gaz), m)
                                        for m in gaz if m != n)[:near]}
            hit += len(close & kin)
        share = hit / (len(picked) * near)
        print(f"  her look-alikes among the {near:>2} geographically nearest"
              f"{'':>1}{share:6.1%}   (chance: {near / (len(names) - 1):.1%})")
    print("\nKinship leans geographic and is nothing like geographic. A\n"
          "reader who takes adjacency on a world map for adjacency in the\n"
          "game has it backwards: she moves to places that sound alike --\n"
          "and, since the prep clock, prefers the near ones among those.")


def survey(trials: int = 200, searchers: int = 2,
           root: bytes = SURVEY_ROOT) -> None:
    """How big a campaign is, which is what decides how to draw one."""
    import statistics

    base = C.Map(root)
    lengths, spans, countries = [], [], []
    extents, closest = [], []
    for trial in range(trials):
        seed = hashlib.sha256(root + trial.to_bytes(4, "big")).digest()
        world = C.Map(seed)
        world.descriptors, world.places, world.treasure = (
            base.descriptors, base.places, base.treasure)
        result = C.chase(seed, C.LOBBY_LANDMARK, searchers=searchers,
                         world=world)
        places = ([world.places[C.LOBBY_LANDMARK]]
                  + [world.places[leg["to"]] for leg in result["moves"]])
        lengths.append(len(result["moves"]))
        spans.append(max(C.travel_hours(a, b) * C.TRAVEL_KMH
                         for a in places for b in places))
        countries.append(len({p["country"] for p in places}))

        # What the world panel actually does with that campaign, in pixels,
        # because the sentence this card's shape used to rest on was about
        # a drawing and was never measured as one.
        drawn = [BM.mercator(p["lat"], p["lon"]) for p in places]
        xs = unwrap([x for x, _ in drawn])
        ys = [y for _, y in drawn]
        extents.append(max(max(xs) - min(xs), max(ys) - min(ys)) * WIDTH)
        pairs = [math.hypot(ax - bx, ay - by) * WIDTH
                 for i, (ax, ay) in enumerate(zip(xs, ys))
                 for bx, by in list(zip(xs, ys))[i + 1:]
                 if (ax, ay) != (bx, by)]
        closest.append(min(pairs) if pairs else 0.0)

    print(f"over {trials} campaigns, {searchers} searchers\n")
    for label, values, unit in (("legs per campaign", lengths, ""),
                                ("span", spans, " km"),
                                ("countries visited", countries, ""),
                                ("world-scale extent", extents, " px"),
                                ("closest two stops", closest, " px")):
        print(f"  {label:20} median {statistics.median(values):>9,.1f}{unit}"
              f"   min {min(values):>7,.1f}   max {max(values):>9,.1f}")
    print(f"\nThe last two rows are the card, on a {WIDTH}px world: how wide"
          "\nthe campaign draws, and how close its two nearest stops land."
          "\nBoth are why the card has two panels rather than one -- at the"
          "\nmedian a campaign is a twentieth of the width and a stop's label"
          "\nis not, and in the long tail two stops share a pixel. **Extent"
          "\nwas never why the world could not be drawn.**"
          "\n\nNeither row is a constant. Campaign shape is downstream of"
          "\nevery parameter in carmel.py, and these two moved by 2x when the"
          "\nhint became a riddle. Run this; do not quote it.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", help="hex; omitted means a fresh one")
    ap.add_argument("--out", default="trail.svg", help="where to write it")
    ap.add_argument("--searchers", type=int, default=2)
    ap.add_argument("--imagery", nargs="?", const="relief", default=None,
                    metavar="LAYER",
                    help="lay NASA GIBS imagery under it: "
                         + ", ".join(sorted(IM.LAYERS))
                         + " (default relief). Needs the network once; "
                           "tiles are cached forever after")
    ap.add_argument("--survey", action="store_true",
                    help="the measurement the card's shape rests on")
    args = ap.parse_args()

    if args.survey:
        root = bytes.fromhex(args.seed) if args.seed else SURVEY_ROOT
        geography(root=root)
        print()
        survey(searchers=args.searchers, root=root)
        return

    seed = bytes.fromhex(args.seed) if args.seed else os.urandom(32)
    world = C.Map(seed)
    result = C.chase(seed, C.LOBBY_LANDMARK, searchers=args.searchers,
                     world=world)
    Path(args.out).write_text(
        card(result, world, seed, C.LOBBY_LANDMARK, imagery=args.imagery),
        encoding="utf-8")

    print(f"{result['outcome']}: {len(result['moves'])} rooms,"
          f" {result['reputation']} reputation,"
          f" {result['hours']:.0f} hours")
    emptied = kept(result)
    for i, leg in enumerate(result["moves"]):
        took = (world.treasure[leg["to"]]["treasure"] if i in emptied
                else "caught in the act" if leg["dwell"] else "-")
        # `leg["hint"]` until #264, which made the hint three details and
        # left this line to raise `KeyError` *after* the card was written --
        # so the file's own command crashed on every run while every test in
        # `test_trail_card.py` stayed green, because they all call `card()`
        # and none of them calls `main()`. Fixed here rather than filed:
        # it is the command this module's docstring tells a reader to run.
        said = ", ".join(d.replace("_", " ") for d in leg["details"])
        print(f"  {i + 1}. {leg['to'][:34]:34} “{said}”  {took}")
    print(f"\nwrote {args.out}   seed {seed.hex()}")


if __name__ == "__main__":
    main()
