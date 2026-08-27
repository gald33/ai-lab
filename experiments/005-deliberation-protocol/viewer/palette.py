"""The colour gates `tokens.css` describes, as something that can be run.

The file has always carried its numbers in a comment -- "worst CVD ΔE 8.4,
worst normal-vision ΔE 19.8, all ≥3:1 on the surface". Those were computed once
and then only claimed. That was survivable while nothing moved; it stopped being
survivable when the island gained a fifth good, because `--good-5` was *byte
identical* to `--util` and `--good-7` to `--eff`. The metric colours had been
taken from the series slots, and "distinct from the four goods" was true only
for as long as there were four.

So the gates live here and are checked. Nothing in this module is used by the
page at runtime; it exists so the comment cannot drift from the palette again.

CVD simulation is Viénot, Brettel & Mollon (1999) -- the standard linear
approximation used for exactly this, applied in linear light. ΔE is CIEDE2000.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

TOKENS = Path(__file__).resolve().parent / "web" / "tokens.css"

#: The surface every gate is measured against: the panel a chart sits on.
SURFACE = "--panel"

#: Dichromacy matrices in linear sRGB. Tritanopia is included for completeness
#: though it is rare; a palette that clears all three is not relying on luck.
CVD = {
    "protanopia": ((0.11238, 0.88762, 0.0), (0.11238, 0.88762, 0.0), (0.004, -0.004, 1.0)),
    "deuteranopia": ((0.29275, 0.70725, 0.0), (0.29275, 0.70725, 0.0), (-0.02234, 0.02234, 1.0)),
    "tritanopia": ((1.0, 0.15236, -0.15236), (0.0, 0.86717, 0.13283), (0.0, 0.86717, 0.13283)),
}


def tokens(path: Path = TOKENS) -> dict[str, str]:
    """Every `--name: #rrggbb` in the stylesheet."""
    return {f"--{n}": c.lower()
            for n, c in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\b", path.read_text())}


def rgb(hex_colour: str) -> tuple[float, float, float]:
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    r, g, b = (_linear(c) for c in rgb(hex_colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio. 3:1 is the floor for a graphical object."""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _lab(hex_colour: str) -> tuple[float, float, float]:
    r, g, b = (_linear(c) for c in rgb(hex_colour))
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 1.00000
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29  # noqa: E731
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a: str, b: str) -> float:
    """CIEDE2000. Two colours below ~10 are hard to tell apart at chart sizes."""
    l1, a1, b1 = _lab(a)
    l2, a2, b2 = _lab(b)
    avg_l = (l1 + l2) / 2
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    avg_c = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(avg_c ** 7 / (avg_c ** 7 + 25 ** 7))) if avg_c else 0.0
    a1p, a2p = a1 * (1 + g), a2 * (1 + g)
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    avg_cp = (c1p + c2p) / 2
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dlp = l2 - l1
    dcp = c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    else:
        dhp = h2p - h1p - 360 if h2p > h1p else h2p - h1p + 360
    dhp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dhp) / 2)
    if c1p * c2p == 0:
        avg_hp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        avg_hp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        avg_hp = (h1p + h2p + 360) / 2
    else:
        avg_hp = (h1p + h2p - 360) / 2
    t = (1 - 0.17 * math.cos(math.radians(avg_hp - 30))
         + 0.24 * math.cos(math.radians(2 * avg_hp))
         + 0.32 * math.cos(math.radians(3 * avg_hp + 6))
         - 0.20 * math.cos(math.radians(4 * avg_hp - 63)))
    sl = 1 + (0.015 * (avg_l - 50) ** 2) / math.sqrt(20 + (avg_l - 50) ** 2)
    sc = 1 + 0.045 * avg_cp
    sh = 1 + 0.015 * avg_cp * t
    rt = (-2 * math.sqrt(avg_cp ** 7 / (avg_cp ** 7 + 25 ** 7))
          * math.sin(math.radians(60 * math.exp(-(((avg_hp - 275) / 25) ** 2)))))
    return math.sqrt((dlp / sl) ** 2 + (dcp / sc) ** 2 + (dhp / sh) ** 2
                     + rt * (dcp / sc) * (dhp / sh))


def simulate(hex_colour: str, kind: str) -> str:
    """The colour as a dichromat sees it."""
    m = CVD[kind]
    lin = [_linear(c) for c in rgb(hex_colour)]
    out = []
    for row in m:
        v = sum(row[i] * lin[i] for i in range(3))
        v = max(0.0, min(1.0, v))
        out.append(12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055)
    return "#" + "".join(f"{round(c * 255):02x}" for c in out)


def worst_cvd(a: str, b: str) -> float:
    """The smallest ΔE between two colours across normal vision and all three
    dichromacies -- which is the number that decides whether they are one
    colour to somebody."""
    return min([delta_e(a, b)] + [delta_e(simulate(a, k), simulate(b, k)) for k in CVD])


def seat_ring(n: int) -> list[str]:
    """What `web/seats.js` paints a table of `n`, asked of the module itself.

    **Not a second implementation.** The ring is generated in the browser, and a
    Python copy of the generator is the drift this repo keeps paying for -- the
    goods, then the seats. This shells out to the one implementation so that
    everything measured here is measured on what the page actually draws.
    """
    import json
    import subprocess
    src = ("import { seatRing } from './seats.js';"
           f"process.stdout.write(JSON.stringify(seatRing({int(n)})));")
    out = subprocess.run(["node", "--input-type=module", "-e", src],
                         cwd=TOKENS.parent, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"seats.js would not run: {out.stderr.strip()}")
    return [c.lower() for c in json.loads(out.stdout)]


def _seats_report(counts: list[int]) -> None:
    """The numbers the seat ring's comments claim, printed.

        python3 viewer/palette.py seats 6 7 8 10 12 16
    """
    import itertools
    surface = tokens()[SURFACE]
    for n in counts:
        ring = seat_ring(n)
        pairs = list(itertools.combinations(ring, 2))
        worst = min((worst_cvd(a, b) for a, b in pairs), default=float("inf"))
        normal = min((delta_e(a, b) for a, b in pairs), default=float("inf"))
        floor = min(contrast(c, surface) for c in ring)
        print(f"{n:3d} seats  worst CVD ΔE {worst:5.1f}  worst ΔE {normal:5.1f}  "
              f"contrast {floor:4.2f}:1  distinct {len(set(ring)) == n}")
        print(f"          {' '.join(ring)}")


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["seats"]:
        _seats_report([int(a) for a in sys.argv[2:]] or [6, 7, 8, 10, 12, 16])
    else:
        raise SystemExit("usage: palette.py seats [n ...]")
