"""The round-0 focal-point check: does it catch a cell that agreed too early?

Offline and synthetic. The point of the check is that it fails on a record
that looks coordinated before anyone has spoken, so what is tested here is the
failure, not the formatting.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiment"))

import focal  # noqa: E402
from agents.market import draw_world  # noqa: E402
from agents.prompt import _vector  # noqa: E402


def _episode(cell, seed, prices):
    return {"cell": cell, "seed": seed,
            "transcript": [[{"agent": i, "message": "", "prices": p}
                            for i, p in enumerate(prices)]]}


def _record(episodes):
    return {"config": {"rounds": 5}, "episodes": episodes}


def _write(tmp_path, record):
    path = tmp_path / "record.json"
    path.write_text(json.dumps(record))
    return path


def test_a_cell_that_agreed_before_anyone_spoke_fails(tmp_path, capsys):
    hint = draw_world(1, 5).hint
    everyone_copied = [list(hint) for _ in range(8)]
    path = _write(tmp_path, _record([_episode("content-only", 1, everyone_copied)]))

    assert focal.report(path) == 1
    assert "agreed before anyone spoke" in capsys.readouterr().out


def test_a_cell_that_did_not_passes(tmp_path, capsys):
    signals = draw_world(1, 5).signals
    path = _write(tmp_path, _record([_episode("baseline", 1, signals)]))

    assert focal.report(path) == 0
    assert "pass" in capsys.readouterr().out


def test_copying_is_counted_against_the_printed_hint_not_the_hint(tmp_path):
    """An agent never saw the hint, it saw a string. The string is what it
    could copy, and the unrounded hint is what it could not."""
    world = draw_world(2, 5)
    printed = [float(x) for x in _vector(world.hint).split()[1::2]]
    episode = _episode("both", 2, [printed] * 8)

    assert focal.copied_hint(episode, world.hint) == 8
    assert printed != world.hint, "the render is lossy, which is the whole point"


def test_the_recorded_v1_run_still_fails_exactly_where_the_review_said(capsys):
    """The check is calibrated against the run that motivated it: the two
    hinted cells fail, the two unhinted ones pass."""
    record = Path(__file__).resolve().parents[1] / "results" / "agents.json"
    if not record.exists():  # pragma: no cover - the record is committed
        return

    assert focal.report(record) == 1
    out = capsys.readouterr().out
    rows = {line.split()[0]: line.split()[1:] for line in out.splitlines()
            if line[:1].isalpha() and len(line.split()) == 4}
    assert rows["content-only"][1] == "11" and rows["both"][1] == "6"
    assert rows["baseline"][1] == "0" and rows["method-only"][1] == "0"
