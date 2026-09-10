"""The real world photographed, from NASA, with no names on it.

    python3 games/hue-and-cry/trail_card.py --imagery relief --out /tmp/t.svg

Gal, 2026-09-09: *"I was actually thinking about actually seeing the real
map or satelite, not a must."*

THIS CORRECTS AN ARGUMENT MADE EARLIER THE SAME DAY, and the correction is
narrow but it matters. `games/hue-and-cry.md` ruled out map tiles partly on
disclosure: *"every raster style prints their names at this zoom -- Fez,
Bergen, Ushuaia, labelled, on the map she is being chased across."* True of
a **street** map and false of a **photograph**. Satellite imagery has no
toponyms at all, so the objection that killed Google's tiles does not reach
imagery -- it was an argument about labels wearing an argument about tiles.

What survives of that paragraph is everything else: Google's tiles still
need an API key and a billing account and still forbid the caching a frozen
stimulus requires. So the imagery is NASA's.

WHY NASA GIBS. No key, no account, no rate deal to sign, and the imagery is
public domain. Three layers are wired up and the default is the middle one:

    relief   BlueMarble_ShadedRelief_Bathymetry   cloud-free, ocean depth
    marble   BlueMarble_NextGeneration            cloud-free, land only
    modis    MODIS_Terra_CorrectedReflectance     a real day, real clouds

`relief` is the default because `modis` is a photograph of one morning:
charming, and half of Europe is under cloud on any given one. The clouds are
not noise for a picture of a chase -- they are just somebody else's weather
sitting on the room she robbed.

**Resolution is sufficient rather than lucky.** The card's closest view is
about 500 km across (`trail_flight.CLOSE_KM`, floored by what the vector
basemap could honestly draw), which at 1000 px is 500 m per pixel. GIBS
serves `relief` to zoom 8 -- 610 m/px at the equator, and finer as
`1/cos(lat)` carries it: 385 m/px at 51 degrees, where the lobby is. So the
imagery is at or past the card's resolution everywhere a campaign has been
measured to go.

NO IMAGE LIBRARY, WHICH IS A DECISION AND NOT A LIMITATION. The obvious
build composites the tiles into one JPEG, and that needs Pillow -- a
dependency this repo does not have and would be installing to do a job SVG
already does. Tiles are placed as positioned `<image>` elements instead:
crisper (nothing is resampled twice), dependency-free, and it works
unchanged inside the flight's camera transform. It costs about a third more
bytes, because base64 inflates by four thirds and nothing is recompressed.

THE BORDERS STAY VECTOR, AND THAT IS THE POINT OF KEEPING BOTH. A
photograph has no borders, and `no_passport_needed_next_door` is a hint in
this game's vocabulary. So imagery draws the ground and `basemap.json`
draws the one thing a photograph cannot show. Coastlines are dropped when
imagery is on -- the photograph has those already, and better.
"""

from __future__ import annotations

import base64
import hashlib
import math
import os
import urllib.error
import urllib.request
from pathlib import Path

WMTS = ("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/default/"
        "{date}/{matrix}/{z}/{y}/{x}.{ext}")

#: name -> (layer, date, tile matrix set, extension, max zoom)
LAYERS = {
    "relief": ("BlueMarble_ShadedRelief_Bathymetry", "2004-01-01",
               "GoogleMapsCompatible_Level8", "jpeg", 8),
    "marble": ("BlueMarble_NextGeneration", "2004-01-01",
               "GoogleMapsCompatible_Level8", "jpeg", 8),
    "modis": ("MODIS_Terra_CorrectedReflectance_TrueColor", "2024-07-15",
              "GoogleMapsCompatible_Level9", "jpg", 9),
}

CREDIT = "imagery: NASA GIBS / Blue Marble — public domain"

#: Pulled down and drained a little so ink reads on top of a photograph.
#: Applied in SVG rather than to the pixels, so the tiles stay exactly the
#: bytes NASA served and anybody can check them.
DIM, SATURATION = 0.36, 0.72

#: Tiles are drawn a hair oversized. Neighbouring `<image>` elements land on
#: fractional pixels and a renderer will show a one-pixel seam between them,
#: which reads as a grid drawn over the world.
BLEED = 0.75

#: A tile is immutable -- a fixed layer, date and address -- so it is cached
#: forever and a re-render of the same card touches the network once.
CACHE = Path(os.environ.get(
    "HUE_TILE_CACHE",
    Path.home() / ".cache" / "hue-and-cry" / "tiles"))


class Unavailable(RuntimeError):
    """Imagery was asked for and could not be had.

    Raised rather than quietly falling back to the vector basemap: a card
    that silently drew something else would be `CLAUDE.md`'s "a skip drawn
    as a pass" wearing a different hat, and the caller cannot see the
    difference in the output.
    """


def zoom_for(scale: float, layer: str = "relief") -> int:
    """The tile zoom whose pixels are at least as fine as the camera's.

    `scale` is pixels per Mercator unit; a zoom-z pyramid is 256 * 2^z
    pixels around. Rounded up, so the imagery is never asked to stretch,
    and clamped to what the layer actually serves.
    """
    top = LAYERS[layer][4]
    return max(0, min(top, math.ceil(math.log2(max(scale, 1.0) / 256))))


def tiles_for(box: tuple[float, float, float, float], z: int) -> list[tuple[int, int]]:
    """Which (x, y) tiles at zoom `z` a unit-square `box` touches."""
    n = 2 ** z
    x0, y0, x1, y1 = box
    out = []
    for ty in range(max(0, math.floor(y0 * n)),
                    min(n - 1, math.floor(y1 * n)) + 1):
        for tx in range(math.floor(x0 * n), math.floor(x1 * n) + 1):
            out.append((tx, ty))
    return out


def _cached(layer: str, z: int, x: int, y: int) -> Path:
    key = hashlib.sha256(f"{layer}/{z}/{x}/{y}".encode()).hexdigest()[:24]
    return CACHE / layer / f"{key}.img"


def fetch(layer: str, z: int, x: int, y: int, opener=None) -> bytes | None:
    """One tile, from the cache or the network. `None` if it is not there.

    A missing tile is not fatal on its own -- the pyramid has gaps at the
    poles and past the date line -- so this reports and `background` decides.
    """
    spot = _cached(layer, z, x, y)
    if spot.exists():
        return spot.read_bytes()

    opener = opener or urllib.request.urlopen
    name, date, matrix, ext, _ = LAYERS[layer]
    n = 2 ** z
    url = WMTS.format(layer=name, date=date, matrix=matrix,
                      z=z, y=y % n, x=x % n, ext=ext)
    try:
        with opener(url, timeout=30) as response:
            body = response.read()
    except (urllib.error.URLError, OSError, ValueError):
        return None
    if not body:
        return None
    spot.parent.mkdir(parents=True, exist_ok=True)
    spot.write_bytes(body)
    return body


def background(camera, layer: str = "relief", opener=None,
               scale: float | None = None) -> list[str]:
    """The photograph under a camera's frame, as positioned SVG `<image>`s.

    `scale` overrides which zoom is chosen, for a camera that will later be
    zoomed in on (the flight holds closer than it starts).
    """
    if layer not in LAYERS:
        raise Unavailable(f"no such imagery layer: {layer!r}. "
                          f"try one of {', '.join(sorted(LAYERS))}")
    z = zoom_for(scale if scale is not None else camera.scale, layer)
    n = 2 ** z
    wanted = tiles_for(camera.box(), z)

    out, got = [], 0
    for tx, ty in wanted:
        body = fetch(layer, z, tx, ty, opener=opener)
        if body is None:
            continue
        got += 1
        left, top = camera.unit((tx / n, ty / n))
        size = camera.scale / n
        uri = ("data:image/jpeg;base64,"
               + base64.b64encode(body).decode("ascii"))
        out.append(
            f'<image x="{left - BLEED / 2:.2f}" y="{top - BLEED / 2:.2f}"'
            f' width="{size + BLEED:.2f}" height="{size + BLEED:.2f}"'
            f' preserveAspectRatio="none" href="{uri}"/>')

    if not got:
        raise Unavailable(
            f"asked for {layer!r} imagery and got none of {len(wanted)} tiles "
            f"at zoom {z}. The card is not drawn rather than drawn wrong; "
            f"re-run without --imagery for the vector basemap.")
    return out


def wrapper(width: int, height: int, y: int, tiles: list[str]) -> list[str]:
    """The tiles, toned so ink reads on them.

    A photograph is busy and bright and the trail has to sit on top of it.
    Both adjustments are SVG, not pixels: the bytes stay NASA's.
    """
    return [
        f'<filter id="tone"><feColorMatrix type="saturate"'
        f' values="{SATURATION}"/></filter>',
        '<g filter="url(#tone)">', *tiles, '</g>',
        f'<rect y="{y}" width="{width}" height="{height}"'
        f' fill="#0b0d10" opacity="{DIM}"/>',
    ]
