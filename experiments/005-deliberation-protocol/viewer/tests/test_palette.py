"""The colour gates `tokens.css` claims, actually run.

    python -m pytest viewer/tests/test_palette.py -q

The stylesheet has always carried its numbers in a comment. Nothing recomputed
them, and two of them were wrong:

* `--util` was **byte-identical** to `--good-5`. Harmless while the island had
  four goods; the moment it gained a fifth, a trader's utility bar and the bar
  of the good directly above it were the same pink.
* `--eff` sat at CVD ΔE **1.6** from `--good-1` — so the headline metric and the
  bread bar were already one colour to a red-green dichromat, at four goods,
  while the comment above them said 16.0.

Both were found by writing this file, not by looking at the page.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import palette  # noqa: E402

TOKENS = palette.tokens()
SERIES = [f"--good-{i}" for i in range(1, 8)]
#: The slots the island can actually draw today: `protocol.GOODS_MAX` is 7, and
#: a game is the first N of the vocabulary.
METRICS = ["--eff", "--util"]

#: `--above` is the same blue as `--good-1`, deliberately: it is drawn only on
#: `scores.html`, which renders no goods at all, so the two never share a
#: surface. Named here so the gate stays strict about everything else.
EXEMPT = {("--good-1", "--above")}

#: A graphical object needs 3:1 against its surface (WCAG 1.4.11).
CONTRAST_FLOOR = 3.0
#: Below about 10 two colours are one colour at chart sizes. The series is only
#: held to this on *adjacent* pairs -- the palette says so, and goods carry a
#: glyph and a fixed position precisely because it does not clear all-pairs.
SERIES_FLOOR = 9.0
#: A metric must not be mistakable for any stock, so it is held to all-pairs.
METRIC_FLOOR = 15.0


def test_no_metric_is_a_series_colour() -> None:
    # The exact-equality case, stated on its own because it is the one that
    # shipped: `--util` *was* `--good-5`.
    for metric in METRICS + ["--above", "--below"]:
        for slot in SERIES:
            if (slot, metric) in EXEMPT:
                continue
            assert TOKENS[slot] != TOKENS[metric], (
                f"{metric} is byte-identical to {slot} ({TOKENS[slot]})")


@pytest.mark.parametrize("name", SERIES[:5] + METRICS)
def test_every_encoding_colour_carries_on_the_surface(name: str) -> None:
    got = palette.contrast(TOKENS[name], TOKENS[palette.SURFACE])
    assert got >= CONTRAST_FLOOR, f"{name} is {got:.2f}:1 on {palette.SURFACE}"


@pytest.mark.parametrize("a,b", list(zip(SERIES[:4], SERIES[1:5])))
def test_adjacent_goods_are_told_apart(a: str, b: str) -> None:
    # Adjacent on the shelf is where it matters: that is the pair a reader
    # compares without moving their eye.
    got = palette.worst_cvd(TOKENS[a], TOKENS[b])
    assert got >= SERIES_FLOOR, f"{a} vs {b} is ΔE {got:.1f} at worst"


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize("slot", SERIES)
def test_a_metric_is_never_mistakable_for_a_stock(metric: str, slot: str) -> None:
    # All-pairs, not adjacent-pairs: a score has no fixed position and no glyph
    # to fall back on, so colour is all it has.
    got = palette.worst_cvd(TOKENS[metric], TOKENS[slot])
    assert got >= METRIC_FLOOR, (
        f"{metric} vs {slot} is ΔE {got:.1f} at worst — "
        "a score would read as a stock")


def test_the_metrics_are_told_apart_from_each_other() -> None:
    a, b = (TOKENS[m] for m in METRICS)
    got = palette.worst_cvd(a, b)
    assert got >= METRIC_FLOOR, f"{METRICS[0]} vs {METRICS[1]} is ΔE {got:.1f}"


def test_the_comment_is_not_describing_a_palette_that_moved() -> None:
    """The numbers written in `tokens.css` are the numbers it has.

    This is the whole reason the file exists: the old comment claimed CVD ΔE
    16.0 for metrics that were at 1.6 and 0.0.
    """
    css = palette.TOKENS.read_text()
    worst_metric = min(palette.worst_cvd(TOKENS[m], TOKENS[s])
                       for m in METRICS for s in SERIES)
    worst_adjacent = min(palette.worst_cvd(TOKENS[a], TOKENS[b])
                         for a, b in zip(SERIES[:4], SERIES[1:5]))
    assert f"ΔE {worst_metric:.1f}" in css, (
        f"tokens.css does not state the metrics' real worst ΔE ({worst_metric:.1f})")
    assert f"ΔE {worst_adjacent:.1f}" in css, (
        f"tokens.css does not state the series' real worst ΔE ({worst_adjacent:.1f})")


def test_the_simulation_is_not_the_identity() -> None:
    # Guards the gate itself: a CVD simulation that returned its input would
    # make every assertion above pass for free.
    red, green = "#d95926", "#199e70"
    assert palette.simulate(red, "deuteranopia") != red
    assert palette.worst_cvd(red, green) < palette.delta_e(red, green), (
        "dichromacy should bring these closer, not leave them alone")


def test_no_two_encoding_colours_are_identical() -> None:
    named = {n: TOKENS[n] for n in SERIES + METRICS}
    for (na, ca), (nb, cb) in itertools.combinations(named.items(), 2):
        assert ca != cb, f"{na} and {nb} are both {ca}"
