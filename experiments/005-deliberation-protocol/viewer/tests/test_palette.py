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


#: The model's copy of the series, in `island3d.js`. Hex integers for three.js
#: rather than CSS, which is exactly why nothing compared the two lists.
MODEL = HERE.parent / "web" / "island3d.js"


def _model_list(name: str) -> list[str]:
    """The colours a literal list in `island3d.js` hands the island, as `#rrggbb`."""
    import re
    body = MODEL.read_text()
    block = re.search(rf"export const {name} = \[(.*?)\];", body, re.S)
    assert block, f"island3d.js no longer declares {name} as a literal list"
    return [f"#{int(h, 16):06x}" for h in re.findall(r"0x([0-9a-fA-F]{6})", block.group(1))]


def _model_series() -> list[str]:
    """The colours `GOOD_COLOURS` hands the island, as `#rrggbb`."""
    return _model_list("GOOD_COLOURS")


def test_the_island_draws_the_stylesheet_s_goods() -> None:
    """A box on the ground is the colour of the bar that counts it.

    **These had drifted, and nothing was looking.** From the fifth good on, the
    stylesheet said pink, green, purple and the model said purple, pink, cyan —
    so on any island with five goods, which is the table default since fish, a
    crate standing in a trader's yard was a different colour from its bar on
    the card and its chip in the legend. Reported by eye.

    The stylesheet is the source: its colours are the ones the gates above are
    run against, so a colour that exists only in the model has passed nothing.
    """
    model = _model_series()
    css = [TOKENS[s] for s in SERIES]
    assert len(model) == len(css), (
        f"the model draws {len(model)} goods and the stylesheet names {len(css)}")
    for i, (a, b) in enumerate(zip(css, model), start=1):
        assert a == b, (
            f"good {i} is {a} on the card and {b} on the island; a box and the "
            f"bar counting it are the same good and must be the same colour")


#: The seats, which the island has painted its huts and boats with since it was
#: modelled and which the SVG layer now draws an offer's pill in.
SEATS = [f"--seat-{i}" for i in range(1, 7)]


#: The drawing code's own copy of the named six, and the generator that takes
#: over past them. One module, imported by both layers -- the island's huts and
#: boats, and the SVG layer's pills -- so there is no third list to drift.
SEATS_JS = HERE.parent / "web" / "seats.js"


def _ring(n: int) -> list[str] | None:
    """What `seats.js` paints a table of `n`, or None with no node to ask."""
    import json
    import subprocess
    src = ("import { seatRing } from './seats.js';"
           f"process.stdout.write(JSON.stringify(seatRing({n})));")
    try:
        out = subprocess.run(["node", "--input-type=module", "-e", src],
                             cwd=SEATS_JS.parent, capture_output=True, text=True,
                             timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        raise AssertionError(f"seats.js would not run: {out.stderr.strip()}")
    return [c.lower() for c in json.loads(out.stdout)]


def _need_ring(n: int) -> list[str]:
    ring = _ring(n)
    if ring is None:
        pytest.skip("no node to run seats.js with")
    return ring


#: How many seats the ring is measured out to. Not a cap the game has -- there
#: is none -- but past this a table is a different problem than a palette.
RING_MAX = 16

#: The counts every gate below is run at: the named six, and rings either side
#: of the sizes a table plausibly reaches.
RINGS = (6, 7, 8, 10, 12, RING_MAX)


def test_the_island_draws_the_stylesheet_s_seats() -> None:
    """A pill is the colour of the hut that made the offer on it.

    The same failure the goods had, one list along: the seats were hex integers
    for three.js in `island3d.js` and `--seat-1..6` in CSS, and until an offer's
    pill wore a seat colour nothing needed both. The drawing code is one module
    now -- `seats.js`, imported by the island and by the SVG layer -- and the
    stylesheet is still the source: its colours are the ones the gates above are
    run against, so a colour that exists only in the drawing code has passed
    nothing.
    """
    named = _need_ring(len(SEATS))
    css = [TOKENS[s] for s in SEATS]
    assert len(named) == len(css), (
        f"seats.js names {len(named)} seats and the stylesheet names {len(css)}")
    for i, (a, b) in enumerate(zip(css, named), start=1):
        assert a == b, (
            f"seat {i} is {a} in the stylesheet and {b} on the island; an offer "
            f"and the trader who made it must be the same colour")


def test_no_table_seats_two_traders_in_one_colour() -> None:
    """The defect this replaces: `SEAT_COLOURS[i % 6]` at seven seats.

    The seventh trader wore the first trader's colour -- on the hut, on the boat
    and on every offer either of them made -- and nothing caps a table at six.
    A repeated colour is not a quiet failure; it is a wrong answer to the one
    question a colour on this island is asked.
    """
    for n in range(1, RING_MAX + 1):
        ring = _need_ring(n)
        assert len(ring) == n, f"a table of {n} got {len(ring)} colours"
        assert len(set(ring)) == n, (
            f"a table of {n} paints two seats one colour: "
            f"{sorted(c for c in set(ring) if ring.count(c) > 1)}")


def test_every_seat_is_visible_on_the_surface_it_is_drawn_on() -> None:
    """A graphical object needs 3:1 against its surface (WCAG 1.4.11).

    A generated colour has not been looked at by anybody, which is the whole
    risk of generating one. The ring holds lightness fixed in OKLab precisely so
    that this holds at every hue; this is the assertion that it does.
    """
    for n in RINGS:
        for i, colour in enumerate(_need_ring(n), start=1):
            ratio = palette.contrast(colour, TOKENS[palette.SURFACE])
            assert ratio >= CONTRAST_FLOOR, (
                f"seat {i} of {n} ({colour}) is {ratio:.2f}:1 on {palette.SURFACE}")


def test_no_seat_is_a_good_or_a_metric() -> None:
    """A seat's colour must not read as a good or a score.

    **Byte-distinctness, not the series' contrast floors, and the difference is
    the point.** A seat is never the only thing saying whose an offer is -- the
    pill carries `maker→taker` in text, and the hut stands where it stands -- so
    it is not asked to be tellable apart at a glance the way two bars on one
    shelf are. Nor could it be: past six seats the ring fills the hue wheel, the
    goods are on that wheel too, and promising every seat is distinguishable
    from every good at twelve seats is a promise no palette can keep. What it
    must not be is the *same colour* as something that already means a good or a
    metric on the same frame.
    """
    for n in RINGS:
        for i, colour in enumerate(_need_ring(n), start=1):
            for other in SERIES + METRICS:
                assert colour != TOKENS[other], (
                    f"seat {i} of {n} is byte-identical to {other} ({colour})")


#: What a seat's colour is actually held to under dichromacy, and it is a long
#: way under the series' 9.0.
#:
#: **Two colours at ΔE 2 are one colour to somebody, and this floor admits
#: that.** It is not a standard anybody would design to; it is a regression
#: gate at the level the palette measures today, so that a repaint or a change
#: to the ring cannot quietly make things worse. The reason it can be this low
#: is the reason the goods carry glyphs: colour is what makes a seat findable,
#: and the name in text beside it is what identifies it.
#:
#: The measurement, and where each number comes from:
#:
#:     python3 viewer/palette.py seats 6 7 8 10 12 16
#:
#: The hand-picked six measure 2.1 -- `--seat-1` and `--seat-6` are ΔE 5.3
#: apart at worst and `--seat-2` and `--seat-5` are the 2.1 -- so the six do
#: *not* clear the series' adjacent floor, and never did. The generated rings
#: measure 5.1 at seven seats, 3.2 at eight, 2.8 at ten and 3.8 at twelve: past
#: six, a viewer is given something better than the six, not worse.
SEAT_FLOOR = 2.0

#: The largest table the floor above is claimed at. Past twelve it stops being
#: true and is not asserted: at sixteen the closest pair measures 1.1 and at
#: twenty-four 0.0 -- two seats one colour to a dichromat, distinct only in
#: bytes. Said out loud here rather than left for somebody to find on a big
#: table: that is a property of the eye and the gamut, not of the generator,
#: and no palette fixes it. What still holds at any size is what the two tests
#: below assert -- no two seats the same colour, and every seat legible.
TELLABLE_MAX = 12


def test_seats_are_as_far_apart_as_the_palette_has_measured() -> None:
    """No repaint may quietly make two seats harder to tell apart.

    The floor is the measurement, not an aspiration -- see `SEAT_FLOOR`. What
    this catches is a change that moves it: a repainted `--seat-n`, a different
    span of lightness in the ring, a chroma the gamut eats.
    """
    for n in [n for n in RINGS if n <= TELLABLE_MAX]:
        ring = _need_ring(n)
        for a, b in itertools.combinations(range(n), 2):
            worst = palette.worst_cvd(ring[a], ring[b])
            assert worst >= SEAT_FLOOR, (
                f"seats {a + 1} and {b + 1} of {n} ({ring[a]}, {ring[b]}) are "
                f"ΔE {worst:.1f} apart at worst, under the measured {SEAT_FLOOR}")


def test_a_generated_ring_beats_the_hand_picked_six() -> None:
    """Past six, nobody is handed something worse than a smaller table gets.

    Stated as a test because it is the argument for generating at all rather
    than, say, repeating the six with a pattern or a border. If a repaint ever
    makes the six better than the ring, this fails and the ring is what needs
    looking at.
    """
    named = min(palette.worst_cvd(a, b)
                for a, b in itertools.combinations(_need_ring(len(SEATS)), 2))
    for n in (7, 8, 10, 12):
        ring = _need_ring(n)
        worst = min(palette.worst_cvd(a, b) for a, b in itertools.combinations(ring, 2))
        assert worst >= named, (
            f"a table of {n} separates its seats by ΔE {worst:.1f}, worse than "
            f"the hand-picked six at {named:.1f}")
