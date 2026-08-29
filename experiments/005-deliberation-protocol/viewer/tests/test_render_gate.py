"""The gate that lets `render.py` be a required check.

`render.py` needs a browser and a minute, so it is not imported for its
checks here -- only for `verdict`, which is pure and is the part that decides
whether a run is a pass. That decision is the whole reason CI can run the
suite at all, so it gets tests of its own: a list of known failures nobody
verifies is a list that quietly swallows a real regression.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _render():
    spec = importlib.util.spec_from_file_location("render", HERE / "render.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render = _render()
KEYS = list(render.KNOWN_FAILURES)


def test_every_known_failure_carries_a_date_and_a_reason():
    """An entry with no reason is an entry nobody can ever retire."""
    assert KEYS, "the gate is pointless with nothing in it; delete it instead"
    for key, entry in render.KNOWN_FAILURES.items():
        since, why = entry
        assert len(since) == 10 and since[4] == since[7] == "-", (
            f"{key} is dated {since!r}, which is not a date")
        assert len(why) > 40, f"{key} has no reason worth reading: {why!r}"


def test_exactly_the_known_failures_is_a_pass():
    code, out = render.verdict([f"{k}: some measured number" for k in KEYS])
    assert code == 0
    # And it says so out loud, so a reader of the log knows what was tolerated
    # rather than finding a silent green.
    assert any(line.startswith("KNOWN") for line in out)


def test_anything_unlisted_fails_the_run():
    """The property the whole mechanism exists to keep."""
    code, out = render.verdict(
        [f"{KEYS[0]}: measured", "some-board cards: two cards overlap"])
    assert code == 1
    assert any(line == "FAIL some-board cards: two cards overlap" for line in out)


def test_a_known_failure_that_stops_failing_also_fails_the_run():
    """Otherwise the list rots: entries outlive the bugs and nobody notices."""
    code, out = render.verdict([f"{KEYS[0]}: measured"])
    assert code == 1
    assert any(KEYS[1] in line and "no longer failing" in line for line in out)


def test_a_clean_run_against_a_stale_list_is_not_a_pass():
    code, out = render.verdict([])
    assert code == 1
    assert sum(1 for line in out if line.startswith("FAIL")) == len(KEYS)


def test_a_known_key_matches_on_the_stable_half_only():
    """The half after the colon carries measured numbers that move each run."""
    a, _ = render.verdict([f"{KEYS[0]}: tint 0.41 -> 0.35", f"{KEYS[1]}: x"])
    b, _ = render.verdict([f"{KEYS[0]}: tint 0.42 -> 0.34", f"{KEYS[1]}: y"])
    assert a == b == 0
    # But a different board with the same check is not the same failure.
    code, _ = render.verdict(
        [f"other-board {KEYS[0].split(' ', 1)[1]}: x"] + [f"{k}: x" for k in KEYS])
    assert code == 1
