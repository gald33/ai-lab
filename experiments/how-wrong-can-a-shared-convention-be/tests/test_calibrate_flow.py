"""Gates on rung 0b: the endpoint, the shortcut, and the refusal.

The refusal is the point. `PREFLIGHT.md` gate 3 says a curve flat in δ means
**stop and do not spend**, so the one thing this runner must never do is exit 0
on a flat curve. It is asserted here by handing `verdict()` a flat one, because
a refusal nobody has watched fire is a refusal nobody has watched work.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "experiment"))

import calibrate  # noqa: E402

from barter.calibrate import announce  # noqa: E402
from barter.economy import draw_island  # noqa: E402


def args(**over):
    base = dict(traders=[4], goods=[3], directions=["flatten", "sharpen"],
                adherences=[1.0], deltas=[0.0, 0.5], islands=2, seed0=1,
                periods=4, rounds=8)
    return argparse.Namespace(**{**base, **over})


def row(delta, share, *, traders=4, goods=3, direction="flatten",
        adherence=1.0):
    return {"traders": traders, "goods": goods, "direction": direction,
            "delta": delta, "adherence": adherence, "islands": 2,
            "zero_period_share": share, "error_median": 0.0,
            "always_zero": 0, "agents_total": 8, "recoveries": 0,
            "efficiency_median": 0.9, "scored": 2,
            "autarky": 0.5, "ceiling": 0.7}


# --- the shortcut is the same arithmetic, not merely similar -------------

def test_the_cached_announcement_equals_the_published_one():
    """`announcements()` solves `walras` once and perturbs many times, where
    `announce()` re-solves per δ. That is the whole cost of this sweep, so it
    is worth doing — and worth proving it changed no number."""
    island = draw_island(4, 3, seed=7)
    cached = calibrate.announcements(island, [0.0, 0.3, 1.0], ["flatten",
                                                              "sharpen"])
    for direction in ("flatten", "sharpen"):
        for delta in (0.0, 0.3, 1.0):
            want = announce(island, delta, direction)
            got = cached[(direction, delta)]
            assert got.price == want.price
            assert got.truth == want.truth
            assert got.error == want.error
            assert got.implied == want.implied


# --- the endpoint --------------------------------------------------------

def test_the_share_is_over_agent_periods_like_the_frozen_primary():
    """Same denominator as `zero_episode_share`, which is what makes the two
    comparable at all."""
    class Out:
        zero_periods = 3
    assert calibrate.zero_period_share(Out(), agents=4, periods=4) == 3 / 16


def test_more_goods_than_traders_carries_its_structural_note():
    assert calibrate.shape_note(4, 5)
    assert calibrate.shape_note(4, 4) is None
    assert calibrate.shape_note(4, 3) is None


# --- the refusal ---------------------------------------------------------

def test_a_flat_curve_is_refused_in_every_direction():
    rows = [row(d, 0.4, direction=x) for x in ("flatten", "sharpen")
            for d in (0.0, 0.5)]
    out = calibrate.verdict(rows, args())
    assert out["readable"] == 0
    assert out["widest"] is None


def test_a_curve_pinned_at_the_ceiling_is_refused_even_though_it_is_extreme():
    """1.000 at every δ is the `goods > traders` cell. It is the most dramatic
    number in the sweep and it says nothing about δ."""
    rows = [row(d, 1.0, direction=x) for x in ("flatten", "sharpen")
            for d in (0.0, 0.5)]
    assert calibrate.verdict(rows, args())["readable"] == 0


def test_one_direction_moving_is_enough_to_read():
    """H0c is refused only if the share is flat across **both** directions."""
    rows = ([row(0.0, 0.4), row(0.5, 0.4)]
            + [row(0.0, 0.1, direction="sharpen"),
               row(0.5, 0.8, direction="sharpen")])
    out = calibrate.verdict(rows, args())
    assert out["readable"] == 1
    assert out["widest"]["spans"]["sharpen"] == 0.7


def test_the_verdict_carries_the_silent_anchor_so_no_is_not_read_as_nothing():
    """Where goods outnumber traders the convention arm is ruined at every δ
    and the silent arm is not. A shape that cannot read δ is not a shape where
    nothing happened."""
    rows = [row(d, 1.0, direction=x) for x in ("flatten", "sharpen")
            for d in (0.0, 0.5)]
    rows.append({**row(None, 0.0), "direction": "silent", "adherence": None})
    shape = calibrate.verdict(rows, args())["shapes"][0]
    assert shape["reads"] is False
    assert shape["silent"] == 0.0


def test_main_refuses_with_a_non_zero_exit_on_a_shape_that_cannot_read(capsys):
    """End to end on the real economy, at the cell the smoke run showed pinned.
    Small and slow-free: 2 islands, 2 δ, 8 rounds."""
    code = calibrate.main(["--islands", "2", "--traders", "4", "--goods", "5",
                           "--deltas", "0.0", "0.5", "--rounds", "8"])
    printed = capsys.readouterr().out
    assert code == 1
    assert "FLAT IN δ EVERYWHERE" in printed
    assert "full specialisation cannot cover the goods" in printed


def test_main_passes_where_the_primary_reads(capsys):
    code = calibrate.main(["--islands", "2", "--traders", "4", "--goods", "3",
                           "--deltas", "0.0", "0.5", "--rounds", "8"])
    assert code == 0
    assert "1/1 shapes can read the primary" in capsys.readouterr().out
