"""Rebuild `basemap.json` -- the real world, at the size a card can carry.

    python3 games/carmel-taldiego/build_basemap.py

Gal, 2026-09-09: *"can we overlay it on the real world map? maybe from
google maps or a free service?"* -- and, in the same breath, *"don't
disclose the potential landmarks"*. Those two pull against each other
harder than they look, which is why this file exists instead of an API key.

**A labelled street map discloses more than the dot field it replaces.**
The landmarks are famous places; Google Maps and every OSM raster style
print their names at the zoom this card sits at. Swapping a field of
anonymous dots for a map that *names* Fez, Bergen and Ushuaia would have
moved in the wrong direction while looking like the right one. So the
basemap is geography with **no toponyms at all**: coastlines, country
borders, big lakes. It says "this is the real world" and nothing about who
is in it.

WHY NOT TILES, WHICH WAS THE OTHER HALF OF THE QUESTION. Three reasons and
the third is the one that decides it:

- **Google's tiles need an API key and a billing account**, and its terms
  forbid caching them, so they cannot be committed. A stimulus this repo
  cannot freeze by hash is one it cannot re-run a campaign against.
- **OSM's tile policy forbids bulk downloading**, and a live page would
  fetch a few hundred tiles per flight across eight zoom levels.
- **Raster tiles snap between integer zooms.** The flight zooms
  continuously from a whole hemisphere to one valley; over vectors that is
  one smooth scale, and over tiles it is eight visible steps.

Natural Earth is public domain (CC0), so it is committed here in full
rather than fetched, and this script is the only thing that touches the
network -- like `build_landmarks.py`, it is not run in CI.

    land        ne_50m_land                        filled
    borders     ne_50m_admin_0_boundary_lines_land hairlines
    lakes       ne_50m_lakes                       the big ones only
    land_coarse the same land, crushed              the locator inset only

MEASURED, AND IT CHANGES WHAT THE TOLERANCE IS FOR. At 0.02 degrees the
simplifier removes **0.5%** of 1:50m's points (29,949 -> 29,808): Natural
Earth is already near that resolution, so this file's size is the source's
and not a choice anybody made. The tolerance only starts trading at 0.04
(-31%), which is 4.4 km and visibly angular at the zoom the flight reaches.
It is kept because a rebuild from 1:10m would need it, and because a number
that turns out to do nothing is worth writing down rather than deleting.

The real size lever is elsewhere: `basemap.near()` clips to the frame, so a
card carries a few hundred points of the ~43,000 committed here.

`land_coarse` is the exception, and the one place a tolerance earns its
keep: the locator inset is 232 px wide, so 1:50m detail there is thousands
of points drawn sub-pixel. Crushed to 0.5 degrees it is a recognisable
world in a fortieth of the points.

1:50m is the resolution the flight's closest zoom can stand. 1:110m is
visibly blocky at a 600 km view -- and a 600 km view is where the card
lives, since a campaign spans a couple of thousand kilometres
(`trail_card.py --survey`).
"""

from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

BASE = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
        "/master/geojson")

OUT = Path(__file__).with_name("basemap.json")

#: Douglas-Peucker tolerance in degrees. 0.02 deg is about 2 km, which is
#: half a pixel at the flight's closest zoom -- so the simplification is
#: invisible where it matters and pays for itself everywhere else.
TOLERANCE = 0.02

#: Rings smaller than this (in square degrees) are dropped. Kept low on
#: purpose: Zanzibar and Tasmania are landmarks' islands, and a basemap
#: that loses the island she is standing on is worse than a heavy one.
MIN_AREA = 0.05

#: For the locator inset: a much harder simplification, and only the shapes
#: big enough to read at 232 px across.
COARSE_TOLERANCE = 0.5
COARSE_MIN_AREA = 4.0

#: Coordinates are rounded to this many decimals. Three is ~110 m, well
#: under a pixel at any zoom this flies to.
DECIMALS = 3


def fetch(layer: str) -> dict:
    url = f"{BASE}/{layer}.geojson"
    print(f"  {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def simplify(points: list, tolerance: float) -> list:
    """Douglas-Peucker, iteratively so a 40,000-point coastline cannot
    blow the stack."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        if last <= first + 1:
            continue
        (x1, y1), (x2, y2) = points[first], points[last]
        dx, dy = x2 - x1, y2 - y1
        span = math.hypot(dx, dy)
        worst, at = -1.0, first
        for i in range(first + 1, last):
            x, y = points[i]
            if span < 1e-12:
                d = math.hypot(x - x1, y - y1)
            else:
                d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / span
            if d > worst:
                worst, at = d, i
        if worst > tolerance:
            keep[at] = True
            stack.append((first, at))
            stack.append((at, last))
    return [p for p, k in zip(points, keep) if k]


def area(ring: list) -> float:
    """Twice the signed area, absolute -- only ever compared to itself."""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def rings(geometry: dict) -> list:
    """Every ring or line in a geometry, as a flat list of point lists."""
    kind, coordinates = geometry["type"], geometry["coordinates"]
    if kind == "LineString":
        return [coordinates]
    if kind == "MultiLineString" or kind == "Polygon":
        return list(coordinates)
    if kind == "MultiPolygon":
        return [ring for polygon in coordinates for ring in polygon]
    return []


def layer(name: str, min_area: float = 0.0,
          tolerance: float | None = None, cached: dict | None = None) -> list:
    out = []
    for feature in (cached or fetch(name))["features"]:
        for ring in rings(feature["geometry"]):
            points = [(float(x), float(y)) for x, y in ring]
            if min_area and area(points) < min_area:
                continue
            points = simplify(points, TOLERANCE if tolerance is None
                              else tolerance)
            if len(points) < 2:
                continue
            out.append([[round(x, DECIMALS), round(y, DECIMALS)]
                        for x, y in points])
    return out


def main() -> None:
    print("fetching Natural Earth (public domain, CC0):")
    land = fetch("ne_50m_land")
    basemap = {
        "source": "Natural Earth 1:50m (public domain)",
        "land": layer("ne_50m_land", MIN_AREA, cached=land),
        "borders": layer("ne_50m_admin_0_boundary_lines_land"),
        "lakes": layer("ne_50m_lakes", MIN_AREA * 4),
        "land_coarse": layer("ne_50m_land", COARSE_MIN_AREA,
                             tolerance=COARSE_TOLERANCE, cached=land),
    }
    OUT.write_text(json.dumps(basemap, separators=(",", ":")),
                   encoding="utf-8")

    size = OUT.stat().st_size
    for key in ("land", "borders", "lakes", "land_coarse"):
        shapes = basemap[key]
        print(f"  {key:8} {len(shapes):5} shapes"
              f"  {sum(len(s) for s in shapes):7,} points")
    print(f"\nwrote {OUT.name}  {size:,} bytes")


if __name__ == "__main__":
    main()
