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
    "ground": "#14110e",     # the card's chrome: title strip and footer
    "sea": "#0d151b",        # water, and the plot area's floor
    "land": "#312c24",       # the real world, Natural Earth
    "border": "#544a3c",  # country borders, hairline
    "line": "#e0a34a",       # her trail
    "stop": "#f2e4cf",
    "text": "#f2e4cf",
    "dim": "#94897a",
    "theft": "#d4573f",
    "rule": "#2a241e",
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


def geometry(camera: Camera, prefix: str = "") -> list[str]:
    """The real world inside a camera's frame, as SVG.

    Sea is the card's ground, so only land, lakes and borders are drawn.
    `basemap.near` has already cut every shape to the frame, so this is a
    few hundred points rather than the committed forty thousand.
    """
    cut = BM.near(camera.box())
    out = []
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


def card(result: dict, world: C.Map, seed: bytes, start: str) -> str:
    """One finished campaign, drawn. `result` is `carmel.chase`'s."""
    legs = result["moves"]
    stops = [start] + [leg["to"] for leg in legs]
    places = [world.places[name] for name in stops]
    points = [(p["lat"], p["lon"]) for p in places]

    plot_h = HEIGHT - TOP - BOTTOM
    main = fit(points, 0, TOP, WIDTH, plot_h)
    pins = [main.at(lat, lon) for lat, lon in points]
    ix, iy = _emptiest_corner(pins)
    inset = Camera(0.5, 0.5, INSET_W, ix, iy, INSET_W, INSET_H)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}"'
           f' height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}"'
           f' font-family="Georgia, serif">',
           f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{INK["ground"]}"/>',
           f'<clipPath id="plot"><rect y="{TOP}" width="{WIDTH}"'
           f' height="{plot_h}"/></clipPath>',
           f'<rect y="{TOP}" width="{WIDTH}" height="{plot_h}"'
           f' fill="{INK["sea"]}"/>',
           f'<g clip-path="url(#plot)">']
    svg += geometry(main)
    svg.append('</g>')

    # the trail
    emptied = kept(result)
    for index, (leg, a, b) in enumerate(zip(legs, places, places[1:])):
        line = BM.great_circle((a["lat"], a["lon"]), (b["lat"], b["lon"]))
        drawn = BM.path([BM.mercator(lat, lon) for lat, lon in line],
                        main.unit)
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
            final = text == rows[2][0] and rows[2][0]
            fill = (INK["stop"] if size == 17
                    else INK["theft"] if final and stole else INK["dim"])
            style = ' font-style="italic"' if final else ""
            svg.append(f'<text x="{tx:.1f}" y="{ty + line * 18:.1f}"'
                       f' fill="{fill}" font-size="{size}"'
                       f' text-anchor="{anchor}"{style}>{_esc(text)}</text>')
            line += 1

    # the inset: where on earth that was, on the coarse world
    svg.append(f'<rect x="{inset.x}" y="{inset.y}" width="{inset.w}"'
               f' height="{inset.h}" fill="{INK["sea"]}"'
               f' stroke="{INK["rule"]}"/>')
    svg.append(f'<clipPath id="inset"><rect x="{inset.x}" y="{inset.y}"'
               f' width="{inset.w}" height="{inset.h}"/></clipPath>')
    svg.append('<g clip-path="url(#inset)">')
    for shape in BM.load()["land_coarse"]:
        drawn = BM.path([BM.mercator(lat, lon) for lon, lat in shape],
                        inset.unit, close=True)
        svg.append(f'<path d="{drawn}" fill="{INK["land"]}"/>')
    cx, cy = inset.unit((main.cx % 1.0, main.cy))
    svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="none"'
               f' stroke="{INK["line"]}" stroke-width="1.6"/>')
    svg.append('</g>')
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
    """
    legs = result["moves"]
    interrupted = len(legs) - 1 if result["outcome"] == "caught" else -1
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
