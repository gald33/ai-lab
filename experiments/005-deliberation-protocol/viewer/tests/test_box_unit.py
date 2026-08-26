"""What one box on the island is worth, checked against the draw it came from.

**A box used to be a sixth of the round's own biggest pile.** That reads well
in a replay and is wrong twice over: a denominator taken from how the round
*ended* is not known while it is running, so a live board had no scale at all
and every non-zero holding was a single box; and even in a replay it made a box
mean a different quantity on every board, so two rounds side by side could not
be compared by looking at them.

The scale comes from the distribution instead, which the design fixes and which
is therefore known before a single message is posted. `barter.economy`'s
`draw_island` gives every trader a capacity per good of ``exp(spread * N(0,1))``
with ``spread = 0.8``, so six boxes is the **ninetieth percentile** of that --
a pile at the top of what one trader can make of one thing -- and a box is a
sixth of it.

This is the thing that keeps that number honest. `island-stock.js` cannot
import a Python module and `render.py` writes the number a third time, so all
three are literals; what stops them going stale is that this re-derives the
quantile from `draw_island` itself and fails when any of them disagrees. A
change to `spread`, or to the shape of the draw, fails here rather than
silently rescaling every yard on the island.
"""

from __future__ import annotations

import inspect
import math
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent
sys.path.insert(0, str(VIEWER.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import draw_island  # noqa: E402

#: The quantile six boxes stands for. The ninetieth and not the median, because
#: a median-sized cap saturates: the biggest pile settled on any board on disk
#: is 5.91 and the median round's biggest is 0.75, so six boxes pinned at the
#: median would show the same full yard for both.
QUANTILE = 0.90
#: The most boxes one good's pile ever shows -- `island-stock.js:MOST`.
MOST = 6


def _capacity_quantile() -> float:
    """The capacity draw's ninetieth percentile, closed form.

    ``exp(spread * N(0, 1))`` is lognormal with log-scale ``spread``, so its
    q-th quantile is ``exp(spread * z_q)``. `spread` is read off `draw_island`'s
    own signature rather than written here, which is what makes a change to it
    fail this.
    """
    spread = inspect.signature(draw_island).parameters["spread"].default
    z = statistics.NormalDist().inv_cdf(QUANTILE)
    return math.exp(spread * z)


def test_the_draw_is_still_the_lognormal_this_assumes() -> None:
    """The closed form matches capacities `draw_island` actually hands out.

    Without this the quantile above is arithmetic about a distribution nothing
    checks anybody still draws from: `draw_island` could switch to a uniform or
    a truncated draw and the closed form would keep returning 2.79.
    """
    drawn = sorted(
        c
        for seed in range(600)
        for row in draw_island(2, 5, seed=seed).capacity
        for c in row
    )
    at = drawn[int(QUANTILE * (len(drawn) - 1))]
    want = _capacity_quantile()
    assert abs(at - want) < 0.12 * want, (
        f"the capacity draw's {QUANTILE:.0%} point is {at:.3f}, and the "
        f"lognormal this assumes says {want:.3f}; the draw has changed shape"
    )


def _literal(path: Path, pattern: str) -> float:
    found = re.search(pattern, path.read_text(), re.M)
    assert found, f"{path.name} no longer declares the box unit ({pattern})"
    return eval(found.group(1))  # noqa: S307 - a numeric literal from our own tree


def test_the_island_draws_the_unit_the_draw_implies() -> None:
    want = _capacity_quantile() / MOST
    unit = _literal(VIEWER / "web" / "island-stock.js",
                    r"export const UNIT = ([0-9.]+) / MOST;") / MOST
    assert abs(unit - want) < 0.005, (
        f"a box on the island is worth {unit:.4f}, and the capacity draw's "
        f"{QUANTILE:.0%} point over {MOST} boxes is {want:.4f}"
    )


def test_the_checks_measure_against_the_same_unit() -> None:
    """`render.py` states the quantity a third time; it has to be the same one."""
    want = _capacity_quantile() / MOST
    box = _literal(HERE / "render.py", r"^BOX = ([0-9.]+ / [0-9]+)$")
    assert abs(box - want) < 0.005, (
        f"render.py measures boxes against {box:.4f} and the island draws them "
        f"at {want:.4f}; the checks and the page disagree about what a box is"
    )


def test_the_ceiling_is_six_boxes_everywhere() -> None:
    """`MOST` here, in the page, and the box counts the checks expect."""
    most = _literal(VIEWER / "web" / "island-stock.js", r"^const MOST = ([0-9]+);")
    assert most == MOST, f"the island shows at most {most} boxes, not {MOST}"
