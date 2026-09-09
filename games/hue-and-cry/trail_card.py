"""The trail she left, drawn, for the post that closes a campaign.

    python3 games/hue-and-cry/trail_card.py --out /tmp/trail.svg

Gal, 2026-09-09: *"I wonder if we want to show the map visually"*. The
answer this file is the buildable half of is in `games/hue-and-cry.md`,
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

**It does not draw her exits, and that is the point of the refusal.**
`games/hue-and-cry.md`, "Which makes the exit count a choice about how big
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

THE BASEMAP IS THE GAZETTEER. There are no coastlines here and no
shapefile: the faint dots are the thousand landmarks, and they read as
continents because that is where landmarks are. This is not a saving on a
dependency, it is the honest picture -- the world of this game *is* those
thousand places, and a searcher choosing where to wait is choosing among
dots on this field and not among countries.

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

import carmel as C  # noqa: E402

#: The card, in pixels. 2:1-ish, which is what a timeline crops to.
WIDTH, HEIGHT = 1000, 640

#: Space kept clear for the title strip and the footer.
TOP, BOTTOM = 92, 56

#: How much room to leave around the trail's bounding box, as a fraction of
#: its longer side. Below about 0.15 the end stops sit on the frame and
#: their labels have nowhere to go.
PAD = 0.28

#: The root the surveys draw their seeds from, so a number quoted in
#: `games/hue-and-cry.md` is one the command reproduces rather than one it
#: resembles. The maps are still drawn -- 200 of them -- this only fixes
#: *which* 200, which is the difference between a measurement and an
#: anecdote. `--seed` varies it, and a number that moves much when it does
#: is a number that wanted more trials.
SURVEY_ROOT = bytes.fromhex("5e ed 00 00".replace(" ", "") * 8)

#: The locator inset, bottom right.
INSET_W, INSET_H, INSET_PAD = 232, 116, 18

INK = {
    "ground": "#14110e",
    "field": "#3a332b",      # the thousand landmarks
    "near": "#6b6053",       # landmarks inside the frame
    "line": "#e0a34a",       # her trail
    "stop": "#f2e4cf",
    "text": "#f2e4cf",
    "dim": "#94897a",
    "theft": "#d4573f",
    "rule": "#2a241e",
}


# --- projection -----------------------------------------------------------

def _unwrap(lons: list[float]) -> list[float]:
    """Longitudes made continuous relative to the first, so a trail across
    the antimeridian has a bounding box instead of a box the width of the
    world. Reykjavik to Fiji is a short hop east, not a 340-degree one."""
    out = [lons[0]]
    for lon in lons[1:]:
        previous = out[-1]
        best = min((lon + turn for turn in (-360.0, 0.0, 360.0)),
                   key=lambda candidate: abs(candidate - previous))
        out.append(best)
    return out


def window(points: list[tuple[float, float]], aspect: float,
           pad: float = PAD) -> tuple[float, float, float, float]:
    """The (lat0, lon0, lat1, lon1) box to draw, padded and widened to the
    viewport's aspect so nothing is squashed.

    Longitude degrees are narrower than latitude degrees away from the
    equator, by cos(lat). Ignoring that draws Reykjavik's neighbourhood
    twice as wide as it is, which for a card whose whole job is "how far
    apart are these places" would be a lie in the direction that matters.
    """
    lats = [lat for lat, _ in points]
    lons = _unwrap([lon for _, lon in points])
    lat0, lat1 = min(lats), max(lats)
    lon0, lon1 = min(lons), max(lons)
    mid_lat, mid_lon = (lat0 + lat1) / 2, (lon0 + lon1) / 2
    squeeze = max(math.cos(math.radians(mid_lat)), 0.2)

    # in "equal-area-ish" units, where a longitude degree is cos(lat) wide
    half_y = max((lat1 - lat0) / 2, 0.25)
    half_x = max((lon1 - lon0) * squeeze / 2, 0.25)
    half_y *= 1 + pad
    half_x *= 1 + pad
    if half_x / half_y < aspect:
        half_x = half_y * aspect
    else:
        half_y = half_x / aspect
    return (mid_lat - half_y, mid_lon - half_x / squeeze,
            mid_lat + half_y, mid_lon + half_x / squeeze)


class Frame:
    """One geographic window mapped onto one rectangle of the card."""

    def __init__(self, box, x, y, w, h):
        self.lat0, self.lon0, self.lat1, self.lon1 = box
        self.x, self.y, self.w, self.h = x, y, w, h

    def at(self, lat: float, lon: float) -> tuple[float, float]:
        span = self.lon1 - self.lon0
        # bring the longitude into this window's turn of the world
        while lon < self.lon0 and lon + 360 <= self.lon1 + 1e-9:
            lon += 360
        while lon > self.lon1 and lon - 360 >= self.lon0 - 1e-9:
            lon -= 360
        px = self.x + (lon - self.lon0) / span * self.w
        py = self.y + (self.lat1 - lat) / (self.lat1 - self.lat0) * self.h
        return px, py

    def holds(self, lat: float, lon: float) -> bool:
        px, py = self.at(lat, lon)
        return (self.x - 1 <= px <= self.x + self.w + 1
                and self.y - 1 <= py <= self.y + self.h + 1)


def arc(a: dict, b: dict, steps: int = 40) -> list[tuple[float, float]]:
    """The great circle between two places, sampled.

    A straight line between two points on a flat map is not the way anybody
    travels, and here it is not the way the game charges her either:
    `carmel.travel_hours` bills her the great-circle kilometres. The line on
    the card is the line she paid for.
    """
    lat1, lon1, lat2, lon2 = map(math.radians,
                                 [a["lat"], a["lon"], b["lat"], b["lon"]])
    d = 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    if d < 1e-9:
        return [(a["lat"], a["lon"]), (b["lat"], b["lon"])]
    out = []
    for i in range(steps + 1):
        f = i / steps
        p = math.sin((1 - f) * d) / math.sin(d)
        q = math.sin(f * d) / math.sin(d)
        x = p * math.cos(lat1) * math.cos(lon1) + q * math.cos(lat2) * math.cos(lon2)
        y = p * math.cos(lat1) * math.sin(lon1) + q * math.cos(lat2) * math.sin(lon2)
        z = p * math.sin(lat1) + q * math.sin(lat2)
        out.append((math.degrees(math.atan2(z, math.hypot(x, y))),
                    math.degrees(math.atan2(y, x))))
    return out


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


def lay_out(pins, blocks) -> list[tuple[float, float, str]]:
    """Where each stop's label goes: (x, y-of-first-line, text-anchor).

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
        if x < 20 or x + w > WIDTH - 20 or y < TOP + 4 or y + h > HEIGHT - BOTTOM:
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
            # nothing fits; stack it under the lowest block on its side
            x = min(max(px + 12, 20), WIDTH - 20 - w)
            y = max([oy + oh + 4 for ox, oy, ow, oh in placed] or [TOP + 8])
            y = min(y, HEIGHT - BOTTOM - h)
            chosen = (x, y)
        placed.append((chosen[0], chosen[1], w, h))
        # the anchor sits on the edge of the block nearest its pin, so the
        # leader line has somewhere honest to end
        anchor = "start" if chosen[0] >= px else "end"
        out.append((chosen[0] + (w if anchor == "end" else 0),
                    chosen[1] + 13, anchor))
    return out


def _emptiest_corner(pins) -> tuple[float, float]:
    """Where to put the locator so it does not sit on the trail.

    Fixed at bottom-right until a trail ran through it. Four candidates,
    take the one whose nearest pin is farthest away.
    """
    candidates = [
        (INSET_PAD, TOP + INSET_PAD),
        (WIDTH - INSET_W - INSET_PAD, TOP + INSET_PAD),
        (INSET_PAD, HEIGHT - BOTTOM - INSET_H - INSET_PAD),
        (WIDTH - INSET_W - INSET_PAD, HEIGHT - BOTTOM - INSET_H - INSET_PAD),
    ]
    def clearance(corner):
        cx, cy = corner[0] + INSET_W / 2, corner[1] + INSET_H / 2
        return min(math.hypot(px - cx, py - cy) for px, py in pins)
    return max(candidates, key=clearance)


# --- the card -------------------------------------------------------------

def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _path(frame: Frame, points) -> str:
    """A polyline, broken where it would wrap the frame rather than drawn
    straight across it. A trail that leaves the right edge and re-enters at
    the left is two strokes, not one stroke through the middle."""
    out, previous = [], None
    for lat, lon in points:
        px, py = frame.at(lat, lon)
        if previous is not None and abs(px - previous) > frame.w * 0.5:
            out.append(f"M{px:.1f},{py:.1f}")
        else:
            out.append(("M" if previous is None else "L")
                       + f"{px:.1f},{py:.1f}")
        previous = px
    return " ".join(out)


def card(result: dict, world: C.Map, seed: bytes, start: str) -> str:
    """One finished campaign, drawn. `result` is `carmel.chase`'s."""
    legs = result["moves"]
    stops = [start] + [leg["to"] for leg in legs]
    places = [world.places[name] for name in stops]
    points = [(p["lat"], p["lon"]) for p in places]

    plot_h = HEIGHT - TOP - BOTTOM
    main = Frame(window(points, WIDTH / plot_h), 0, TOP, WIDTH, plot_h)
    pins = [main.at(lat, lon) for lat, lon in points]
    inset = Frame((-90.0, -180.0, 90.0, 180.0),
                  *_emptiest_corner(pins), INSET_W, INSET_H)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}"'
           f' height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}"'
           f' font-family="Georgia, serif">',
           f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{INK["ground"]}"/>']

    # the basemap: every landmark, brighter where the frame holds it
    far, near = [], []
    for place in world.places.values():
        target = near if main.holds(place["lat"], place["lon"]) else far
        target.append(main.at(place["lat"], place["lon"]))
    for dots, colour, r, opacity in ((far, INK["field"], 1.1, 0.55),
                                     (near, INK["near"], 1.9, 0.9)):
        body = " ".join(f'M{x:.1f},{y:.1f}m-{r},0a{r},{r} 0 1,0 {2*r},0'
                        f'a{r},{r} 0 1,0 -{2*r},0' for x, y in dots)
        svg.append(f'<path d="{body}" fill="{colour}"'
                   f' opacity="{opacity}"/>')
    svg.append(f'<rect y="0" width="{WIDTH}" height="{TOP}"'
               f' fill="{INK["ground"]}"/>')
    svg.append(f'<rect y="{HEIGHT - BOTTOM}" width="{WIDTH}"'
               f' height="{BOTTOM}" fill="{INK["ground"]}"/>')

    # the trail
    emptied = kept(result)
    for index, (leg, a, b) in enumerate(zip(legs, places, places[1:])):
        svg.append(f'<path d="{_path(main, arc(a, b))}" fill="none"'
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
            (f'“{leg["hint"].replace("_", " ")}”' if leg else "", 13),
            (last, 13),
        ])

    for i, ((px, py), rows, (tx, ty, anchor)) in enumerate(
            zip(pins, blocks, lay_out(pins, blocks))):
        stole = i - 1 in emptied if i else False
        # a leader, when the label had to move away from its pin
        if abs(tx - px) > 26 or not (py - 22 < ty < py + 30):
            svg.append(f'<path d="M{px:.1f},{py:.1f} L{tx:.1f},'
                       f'{ty - 5:.1f}" stroke="{INK["rule"]}"'
                       f' stroke-width="1"/>')
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
            last = text == rows[2][0] and rows[2][0]
            fill = (INK["stop"] if size == 17
                    else INK["theft"] if last and stole else INK["dim"])
            style = ' font-style="italic"' if last else ""
            svg.append(f'<text x="{tx:.1f}" y="{ty + line * 18:.1f}"'
                       f' fill="{fill}" font-size="{size}"'
                       f' text-anchor="{anchor}"{style}>{_esc(text)}</text>')
            line += 1

    # the inset: where on earth that was
    svg.append(f'<rect x="{inset.x}" y="{inset.y}" width="{inset.w}"'
               f' height="{inset.h}" fill="{INK["ground"]}"'
               f' stroke="{INK["rule"]}"/>')
    dots = " ".join('M{:.1f},{:.1f}m-.7,0a.7,.7 0 1,0 1.4,0a.7,.7 0 1,0 -1.4,0'
                    .format(*inset.at(p["lat"], p["lon"]))
                    for p in world.places.values())
    svg.append(f'<path d="{dots}" fill="{INK["field"]}"/>')
    corners = [(main.lat0, main.lon0), (main.lat0, main.lon1),
               (main.lat1, main.lon1), (main.lat1, main.lon0)]
    cx = sum(inset.at(lat, lon)[0] for lat, lon in corners) / 4
    cy = sum(inset.at(lat, lon)[1] for lat, lon in corners) / 4
    svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="none"'
               f' stroke="{INK["line"]}" stroke-width="1.6"/>')
    # the caption is wider than the inset, so it hangs towards the middle of
    # the card rather than off whichever edge the inset was moved to
    left = inset.x < WIDTH / 2
    svg.append(f'<text x="{inset.x if left else inset.x + inset.w}"'
               f' y="{inset.y - 8}" fill="{INK["dim"]}" font-size="11"'
               f' letter-spacing="1.2"'
               f' text-anchor="{"start" if left else "end"}">'
               f'{_esc(_span(places))}</text>')

    # title and footer
    took = len(emptied)
    svg.append(f'<text x="34" y="46" fill="{INK["text"]}" font-size="30">'
               f'Carmel Taldiego, {_esc(result["outcome"])}</text>')
    svg.append(f'<text x="34" y="72" fill="{INK["dim"]}" font-size="15">'
               f'{len(legs)} rooms, {took} of them emptied,'
               f' {result["reputation"]} reputation,'
               f' {result["hours"]:.0f} hours</text>')
    svg.append(f'<text x="34" y="{HEIGHT - 22}" fill="{INK["dim"]}"'
               f' font-size="12" font-family="monospace">'
               f'seed {seed.hex()}</text>')
    svg.append('</svg>')
    return "\n".join(svg)


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

    THE RULE ITSELF NOW LIVES IN `carmel.interrupted_theft`, which is where
    the argument for why it may take the last leg without searching for it
    is written. It moved there when `close_campaign` was fixed to agree
    with this file (`games/hue-and-cry.md`, "The room she was caught in is
    counted apart and named"): the card and the closing post must count the
    same rooms, and two copies of one rule is how they drift apart again.
    This function is the shape the card wants -- indices, from a whole
    result -- over that predicate, and nothing more.
    """
    legs = result["moves"]
    interrupted = C.interrupted_theft(result["outcome"], legs)
    return {i for i, leg in enumerate(legs)
            if leg["dwell"] and i != interrupted}


def _span(places: list[dict]) -> str:
    widest = max((C.travel_hours(a, b) * C.TRAVEL_KMH
                  for a in places for b in places), default=0.0)
    return f"{widest:,.0f} KM ACROSS, ON A WORLD 40,075 KM AROUND"


# --- the measurement the inset exists because of --------------------------

def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[int(q * (len(ordered) - 1))]


def geography(sample: int = 150, root: bytes = SURVEY_ROOT) -> None:
    """How much of the map's structure a geographic drawing would show.

    The answer decides what may honestly be drawn on a world projection.
    Routes are drawn from descriptor kinship (`games/hue-and-cry.md`,
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

    along = [km(world.places[n], world.places[e])
             for n in picked for e in world.exits(n)]
    apart = [km(world.places[a], world.places[b])
             for a, b in (random.sample(names, 2) for _ in range(3000))]

    print(f"over {sample} landmarks, every exit\n")
    print(f"  median distance along one of her exits          "
          f"{statistics.median(along):7,.0f} km")
    print(f"  median distance between two landmarks at random "
          f"{statistics.median(apart):7,.0f} km")
    for near in (5, 50):
        hit = 0
        for n in picked:
            close = {m for _, m in sorted(
                (km(world.places[n], world.places[m]), m)
                for m in names if m != n)[:near]}
            hit += len(close & set(world.exits(n)))
        share = hit / (len(picked) * C.EXITS)
        print(f"  her exits among the {near:>2} geographically nearest "
              f"{'':>7}{share:6.1%}   (chance: {near / (len(names) - 1):.1%})")
    print("\nKinship leans geographic and is nothing like geographic. A\n"
          "reader who takes adjacency on a world map for adjacency in the\n"
          "game has it backwards: she moves to places that sound alike.")


def survey(trials: int = 200, searchers: int = 2,
           root: bytes = SURVEY_ROOT) -> None:
    """How big a campaign is, which is what decides how to draw one."""
    import statistics

    base = C.Map(root)
    lengths, spans, countries = [], [], []
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

    print(f"over {trials} campaigns, {searchers} searchers\n")
    for label, values, unit in (("legs per campaign", lengths, ""),
                                ("span", spans, " km"),
                                ("countries visited", countries, "")):
        print(f"  {label:20} median {statistics.median(values):>9,.0f}{unit}"
              f"   min {min(values):>7,.0f}   max {max(values):>9,.0f}")
    print("\nA campaign happens inside a box a few thousand kilometres\n"
          "across, on a map 40,075 km around. That is why the card is the\n"
          "box with the world as an inset, and not the world.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", help="hex; omitted means a fresh one")
    ap.add_argument("--out", default="trail.svg", help="where to write it")
    ap.add_argument("--searchers", type=int, default=2)
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
    Path(args.out).write_text(card(result, world, seed, C.LOBBY_LANDMARK),
                              encoding="utf-8")

    print(f"{result['outcome']}: {len(result['moves'])} rooms,"
          f" {result['reputation']} reputation,"
          f" {result['hours']:.0f} hours")
    emptied = kept(result)
    for i, leg in enumerate(result["moves"]):
        took = (world.treasure[leg["to"]]["treasure"] if i in emptied
                else "caught in the act" if leg["dwell"] else "-")
        print(f"  {i + 1}. {leg['to'][:34]:34} “{leg['hint']}”  {took}")
    print(f"\nwrote {args.out}   seed {seed.hex()}")


if __name__ == "__main__":
    main()
