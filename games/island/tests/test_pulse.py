"""The launch counters, and the two things they must not do.

`pulse.py` answers "did the launch work" from the record rather than from a
tracker. Two properties keep it honest, and both are easy to lose:

1. **It never claims to measure what it does not.** Page views, brief copies
   and agents that were handed a brief and never arrived are all invisible to
   it, and it says so out loud. A blank in a report reads as a zero, and those
   are not zeroes.
2. **Reading it is read-only.** It reaches a live hub, so it must not register,
   announce presence, or advance a cursor -- a counter that looked like an
   entrant would change the number it exists to report. `--offline` is the
   path taken here; the hub half is exercised by the same read-only client the
   viewer uses and is not worth a live test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from games.island import pulse

ROOT = Path(__file__).resolve().parents[3]


def _row(who, played_at, partner=None, **over):
    # The partner varies per row by default. It used to be one fixed name,
    # which made every row a repeat for that name and quietly turned the
    # repeat-attempt test into a test of the fixture.
    partner = partner or f"partner-{played_at}"
    base = {"v": 2, "round_id": f"r{who}{played_at}",
            "game": {"id": f"g{who}{played_at}", "rounds": 1},
            "played_at": played_at, "played_from": "board",
            "recorded_at": played_at, "workspace": f"w-{who}-{played_at}",
            "arm": "sealed", "npcs": {}, "hands": {}, "draw": "commit-reveal",
            "island": {"seed": 5, "agents": 2, "goods": 5, "episodes": 4,
                       "seconds": 60},
            "players": [{"slot": "T1", "id": who, "model": "entrants",
                         "harness": "bash"},
                        {"slot": "T2", "id": partner, "model": "entrants"}],
            "eff_round": 0.9, "eff_round_upper": 1.0, "autarky_floor": 0.6,
            "eff_episode": [0.9] * 4, "ratios": {"T1": 1.4, "T2": 1.2},
            "utility_total": {"T1": 1.0, "T2": 1.0},
            "autarky_utility": {"T1": 0.7, "T2": 0.8},
            "zero_episodes": {"T1": 0, "T2": 0},
            "trajectory": [[0.9, 0.9]] * 4,
            "traffic": {"settled": 4, "refused": 0, "talk": 1},
            "company": 0, "intruders": [], "status": "complete",
            "attendance": "recorded", "acknowledged": [], "spoke": [],
            "source": {"result": "x.json", "board": "b.json"}}
    base.update(over)
    return base


def test_a_repeat_attempt_is_counted_and_named():
    """The number the launch is actually asking about.

    Somebody played, disliked their score, changed something and came back.
    Knowable from the ledger alone, which is the whole argument for not adding
    a tracker to answer it.
    """
    rows = [_row("shell-goblin", "2026-09-06T10:00:00+00:00"),
            _row("shell-goblin", "2026-09-06T11:00:00+00:00"),
            _row("one-shot", "2026-09-06T12:00:00+00:00")]
    out = pulse.from_the_ledger(rows)
    assert out["entrants_who_came_back"] == 1
    assert out["repeat_attempts"]["shell-goblin"] == 2
    assert "one-shot" not in out["repeat_attempts"]


def test_our_own_entrants_are_labelled_rather_than_dropped():
    """"Did anybody play" and "did a stranger play" are different questions.

    Both are answered, and nothing is removed from a denominator to answer
    either -- a board that dropped the lab's own games would be reporting on a
    population it chose.
    """
    rows = [_row("npc-g1-1", "2026-09-06T10:00:00+00:00"),
            _row("shell-goblin", "2026-09-06T11:00:00+00:00")]
    out = pulse.from_the_ledger(rows)
    assert out["games_completed"] == 2
    assert out["entrants_all"] > out["entrants_not_ours"]
    assert out["entrants_not_ours"] >= 1


def test_the_open_table_is_reported_held_or_not():
    """The one state the front door quotes, so it must be countable here."""
    out = pulse.from_the_ledger([_row("a", "2026-09-06T10:00:00+00:00")])
    assert out["games_on_the_open_table"] == 1
    assert out["open_table_held"] is True

    other = _row("a", "2026-09-06T10:00:00+00:00")
    other["island"]["seconds"] = 120
    assert pulse.from_the_ledger([other])["games_on_the_open_table"] == 0


def test_declared_harnesses_are_counted():
    out = pulse.from_the_ledger([_row("a", "2026-09-06T10:00:00+00:00")])
    assert out["harnesses_declared"] == {"bash": 1}


def test_it_says_what_it_cannot_see():
    """A blank reads as a zero. These are not zeroes."""
    text = pulse.report({"ledger": pulse.from_the_ledger([]),
                         "hub": {"reachable": False, "why": "not asked"}})
    assert "Not measured here, and not zero" in text
    for blind in pulse.BLIND:
        assert blind in text


def test_an_unreachable_hub_is_a_stated_fact_not_a_silent_zero():
    """The failure this repo keeps finding: reporting success while doing
    nothing. A hub that could not be read must not render as a quiet door."""
    text = pulse.report({"ledger": pulse.from_the_ledger([]),
                         "hub": {"reachable": False, "why": "timeout"}})
    assert "UNREACHABLE" in text
    assert "timeout" in text
    assert "lobby process" not in text


def test_it_runs_offline_without_touching_the_network():
    """`--offline` is what CI runs: no hub, no flake, and still a real answer."""
    done = subprocess.run(
        [sys.executable, "-m", "games.island.pulse", "--offline", "--json"],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr
    data = json.loads(done.stdout)
    assert data["hub"]["reachable"] is False
    assert data["ledger"]["ledger_rows"] > 0
