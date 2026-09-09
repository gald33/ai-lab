"""The real world, projected, and cut down to what one picture needs.

Shared by `trail_card.py` (a still) and `trail_flight.py` (a moving one),
because they must agree about where places are. `basemap.json` is committed
and `build_basemap.py` is what rebuilds it.

WEB MERCATOR, AND NOT BECAUSE IT IS FASHIONABLE. The flight zooms from a
hemisphere to a valley, and under Mercator that is a **single scale factor**
-- the projection is conformal, so shapes stay right at every zoom and the
camera is one number. Under the equirectangular frame the still card used
before, zooming in near the poles stretched everything sideways and the
camera needed a per-latitude correction that was wrong the moment it moved.
It is also the projection every reader has seen, which is the other half of
"the real world map".

The cost is the honest one: Mercator lies about area, badly, towards the
poles. Nothing here is scored on area, and the flight is never zoomed out
far enough for it to matter to a trail.

NOTHING IN THIS FILE KNOWS A LANDMARK. That is deliberate -- see
`build_basemap.py` for why the basemap carries no toponyms, and
`games/hue-and-cry.md`, "A real map that names places discloses more than a
field of dots did".
"""

from __future__ import annotations

import json
import math
from pathlib import Path

DATA = Path(__file__).with_name("basemap.json")

#: Web Mercator cannot represent the poles, and clamps here -- the standard
#: cut, and the one every tiled map uses.
MAX_LAT = 85.05112878

_CACHE: dict | None = None


def load() -> dict:
    """The committed world. Read once; callers must not mutate it."""
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(DATA.read_text(encoding="utf-8"))
    return _CACHE


def mercator(lat: float, lon: float) -> tuple[float, float]:
    """Longitude and latitude to the unit square, y down.

    (0,0) is 180 degrees west at the north cut, (1,1) is 180 east at the
    south. Distances in these units are comparable in x and y, which is what
    lets one scale factor serve as the whole camera.
    """
    lat = max(-MAX_LAT, min(MAX_LAT, lat))
    x = (lon + 180.0) / 360.0
    s = math.sin(math.radians(lat))
    y = 0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)
    return x, y


def unmercator(x: float, y: float) -> tuple[float, float]:
    lon = x * 360.0 - 180.0
    lat = math.degrees(2 * math.atan(math.exp((0.5 - y) * 2 * math.pi))
                       - math.pi / 2)
    return lat, lon


def great_circle(a: tuple[float, float], b: tuple[float, float],
                 steps: int = 64) -> list[tuple[float, float]]:
    """The (lat, lon) path she actually flew, sampled.

    `carmel.travel_hours` bills her great-circle kilometres, so this is the
    line she paid for. Under Mercator it is a curve, which is correct and is
    the reason the card looks like an airline map rather than a ruler.
    """
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    d = 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    if d < 1e-9:
        return [a, b]
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


def bounds(shape: list) -> tuple[float, float, float, float]:
    xs = [p[0] for p in shape]
    ys = [p[1] for p in shape]
    return min(xs), min(ys), max(xs), max(ys)


def clip_polygon(points: list, box: tuple) -> list:
    """Sutherland-Hodgman: a filled shape cut to the rectangle, still closed.

    A BOUNDING-BOX FILTER IS NOT ENOUGH AND THE FIRST VERSION OF THIS FILE
    ONLY DID THAT. Every card showing a European valley kept Eurasia --
    which intersects the frame, so the filter kept it, all 12,000 points of
    it -- and the "clipped" basemap was very nearly the whole planet. Cut
    properly, the same frame carries a few hundred points.

    Clipping a polygon rather than trimming its points is what keeps it
    *fillable*: an open run of coastline near the frame has no inside, and
    land drawn as a stroke instead of a fill is a different picture.
    """
    x0, y0, x1, y1 = box
    edges = ((0, x0), (1, x1), (2, y0), (3, y1))
    out = list(points)
    for side, value in edges:
        if not out:
            return []
        clipped, previous = [], out[-1]
        for point in out:
            inside = _inside(point, side, value)
            if inside != _inside(previous, side, value):
                clipped.append(_cross(previous, point, side, value))
            if inside:
                clipped.append(point)
            previous = point
        out = clipped
    return out


def _inside(point, side: int, value: float) -> bool:
    return (point[0] >= value if side == 0 else
            point[0] <= value if side == 1 else
            point[1] >= value if side == 2 else point[1] <= value)


def _cross(a, b, side: int, value: float):
    axis = 0 if side < 2 else 1
    span = b[axis] - a[axis]
    t = 0.0 if abs(span) < 1e-15 else (value - a[axis]) / span
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def clip_line(points: list, box: tuple) -> list:
    """An open line cut to the rectangle, as the runs that survive.

    Borders and coastlines are strokes, so they may be broken; a run that
    leaves the frame and comes back is two lines, which draws identically
    and carries none of the points in between.
    """
    x0, y0, x1, y1 = box
    runs, run = [], []
    for point in points:
        if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
            run.append(point)
        else:
            # keep one point past the edge so the stroke reaches it
            if run:
                run.append(point)
                runs.append(run)
                run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) > 1]


def near(box: tuple[float, float, float, float], margin: float = 0.02,
         keys: tuple = ("land", "lakes", "borders")) -> dict:
    """The world, cut to what a `box` of unit-square coordinates can show.
    `box` is (x0, y0, x1, y1).

    THIS IS WHY THE COMMITTED FILE MAY BE 700 KB. Every card would otherwise
    carry the whole planet to draw one valley. Land and lakes are clipped as
    polygons so they still fill; borders as lines, so they may break.

    TWO CLEVERER SCHEMES WERE BUILT HERE AND DELETED FOR NOT PAYING, which
    is worth a paragraph because both look obviously right. A flight across
    Eurasia carries 21,212 of the basemap's 45,548 points, and:

    - **Level of detail** -- a crushed world at wide zoom, the real one when
      close -- saved 30% and introduced a visible pop. At any zoom where the
      crushed layer is honest (its 55 km error under ~3 px) the detailed
      layer is still needed for everything closer, and "everything closer"
      is the whole corridor. Crude enough to save, crude enough to see.
    - **Corridor filtering** -- one frame per keyframe instead of their
      bounding box, keeping only shapes some frame actually holds -- saved
      **1%** (21,428 -> 21,212).

    The reason both fail is the same and it is not a bug: when the camera
    pulls back to fit a 6,300 km leg it *is looking at* most of that
    rectangle. A page showing a lot of world carries a lot of world. What
    clipping to the frame does buy is real and is the common case -- a
    European campaign carries 1,892 points, 4% of the map -- and that is
    where this function earns its place.
    """
    x0, y0, x1, y1 = box
    box = (x0 - margin, y0 - margin, x1 + margin, y1 + margin)
    world = load()
    out: dict[str, list] = {key: [] for key in keys}
    for key in keys:
        for shape in world[key]:
            projected = [mercator(lat, lon) for lon, lat in shape]
            # A frame straddling the antimeridian has a box outside [0,1],
            # where no shape lives; the world repeats, so try its copies.
            for turn in _turns(bounds(projected), box):
                moved = [(x + turn, y) for x, y in projected]
                if key.endswith("borders"):
                    out[key].extend(clip_line(moved, box))
                else:
                    cut = clip_polygon(moved, box)
                    if len(cut) > 2:
                        out[key].append(cut)
    return out


def _turns(shape_box: tuple, box: tuple) -> list[float]:
    """Which copies of the world, at -1, 0 and +1 turns, the frame sees."""
    sx0, sy0, sx1, sy1 = shape_box
    if sy1 < box[1] or sy0 > box[3]:
        return []
    return [turn for turn in (-1.0, 0.0, 1.0)
            if not (sx1 + turn < box[0] or sx0 + turn > box[2])]


def path(points: list[tuple[float, float]], place, close: bool = False) -> str:
    """An SVG path through projected points, `place` mapping one to pixels.

    A polyline is broken where consecutive points jump more than half the
    world in x, so a shape crossing the antimeridian is two strokes rather
    than one stroke back across the whole map. Natural Earth splits its own
    geometry at the date line, but a great circle does not.
    """
    out, previous = [], None
    for point in points:
        px, py = place(point)
        if previous is not None and abs(point[0] - previous) > 0.5:
            out.append(f"M{px:.1f},{py:.1f}")
        else:
            out.append(("M" if previous is None else "L") + f"{px:.1f},{py:.1f}")
        previous = point[0]
    return " ".join(out) + (" Z" if close else "")
