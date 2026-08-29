"""The known-failures gate in `render.py`, checked without a browser.

`render.py` takes about half an hour to say anything, so the one part of it a
person edits by hand -- the `KNOWN` list -- is the part with the slowest
feedback. These run in a second and hold the two rules that make the list
honest: **an unlisted failure fails the run**, and **a listed failure that
stops happening fails it too**. The second is the one that matters. A list
whose entries outlive their bugs is a list nobody reads, and by the time
somebody does it has swallowed a regression.

Checked here rather than in `render.py` because they are arithmetic on
strings, and a rule that can be checked without a browser should be.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render  # noqa: E402

#: The two lines a real run emits today, copied from one. Every case below is
#: built out of these, so the test is anchored to what the checks actually say
#: rather than to a shape assumed here.
BAND = ("island-game-001d-g1 @safari 393x660: the island fills 85% of the 202px "
        "band between the chrome and the cards; the rest is dead sky and dead sea")
LIGHT = ("island-game-001d-g1 alive: the island is no warmer with the sun down "
         "than with it up (tint 0.42 -> 0.34); the light is not on the day's clock")


def test_the_recorded_failures_match_what_a_run_actually_prints():
    """The keys are matched against real output, not against their own wording.

    This is the failure the list is most likely to have: an entry that reads
    correctly and matches nothing, so its bug is reported as fresh and the
    entry is reported as stale, both at once."""
    fresh, known, stale = render.sort_known([BAND, LIGHT])
    assert fresh == [], fresh
    assert len(known) == 2
    assert stale == []


def test_an_unlisted_failure_still_fails():
    fresh, known, stale = render.sort_known(
        [BAND, LIGHT, "island-game-002b-g1 ring: two huts overlap"])
    assert fresh == ["island-game-002b-g1 ring: two huts overlap"]
    assert len(known) == 2 and stale == []


def test_a_recorded_failure_that_stops_failing_fails_the_run():
    """The rule that stops the list rotting. Whoever fixes one of these gets a
    red check telling them to delete its line, which is the only moment anybody
    is in a position to."""
    fresh, known, stale = render.sort_known([BAND])
    assert fresh == [] and len(known) == 1
    assert len(stale) == 1
    assert "delete its entry" in stale[0]


def test_the_numbers_may_drift_without_unmatching():
    """These are thresholds on a rendered picture and the readings move with
    the machine -- the tint came back 0.34 on one run here and 0.35 on the
    next. An entry keyed on the numbers would go stale on a fast afternoon."""
    fresh, known, stale = render.sort_known([
        BAND.replace("85%", "84%").replace("202px", "198px"),
        LIGHT.replace("0.42 -> 0.34", "0.40 -> 0.29"),
    ])
    assert fresh == [] and len(known) == 2 and stale == []


def test_the_same_complaint_about_another_board_is_a_fresh_failure():
    """An entry covers the board it was recorded on and no other. The band
    check passes on `002b-g1` today; if it stops, that is news."""
    other = BAND.replace("001d-g1", "002b-g1")
    fresh, known, stale = render.sort_known([other, BAND, LIGHT])
    assert fresh == [other]
    assert len(known) == 2 and stale == []


def test_every_entry_carries_a_date_and_a_reason_worth_reading():
    """An undated entry is indistinguishable from one nobody has looked at."""
    assert render.KNOWN, "the list is not empty today; see the README"
    for where, needle, why in render.KNOWN:
        assert where and needle, "an entry with no key matches nothing"
        assert re.match(r"^\d{4}-\d{2}-\d{2}: ", why), (
            f"{where}: an entry needs the date it was recorded, first thing")
        assert len(why) > 120, (
            f"{where}: a reason this short is a label, not a reason")
