"""Gates on the one thing `ground.py` must never get wrong: which experiment.

`find()` had no tests while it resolved numbers, and the rename is exactly the
change that would have broken it silently -- a lookup that returns *an*
experiment rather than *the* experiment grounds an agent in another
experiment's frozen metric, which `experiments/GROUNDING.md` calls the most
expensive contamination available here. So the ambiguous cases assert an exit
rather than a choice.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import ground  # noqa: E402


def test_a_full_name_resolves_to_itself():
    assert ground.find("is-ruin-the-convention-or-the-commitment").name == (
        "is-ruin-the-convention-or-the-commitment")


def test_a_fragment_of_the_question_is_enough():
    """Nobody types the whole question, so nobody would use the tool."""
    assert ground.find("ruin").name == "is-ruin-the-convention-or-the-commitment"


def test_every_retired_number_still_reaches_a_directory_that_exists():
    """The map is only worth having if each entry resolves on disk."""
    for number, name in ground.RETIRED_NUMBERS.items():
        assert (ROOT / "experiments" / name).is_dir(), f"{number} -> {name}"


def test_a_retired_number_names_the_experiment_on_stderr(capsys):
    """The number resolves *and* teaches the name, or it just hides the rename."""
    ground.find("005")
    assert "does-a-content-free-protocol-help" in capsys.readouterr().err


def test_the_note_stays_out_of_a_paths_pipe(capsys):
    """`--paths` feeds other commands; a courtesy line on stdout would corrupt it."""
    ground.find("005")
    assert capsys.readouterr().out == ""


def test_the_number_that_was_two_experiments_refuses_to_pick_one():
    """`006` is the measured reason the number was never an identifier."""
    with pytest.raises(SystemExit) as exit_:
        ground.find("006")
    for name in ground.AMBIGUOUS_NUMBERS["006"]:
        assert name in str(exit_.value)


def test_an_ambiguous_fragment_is_an_error_not_a_first_match():
    with pytest.raises(SystemExit) as exit_:
        ground.find("does")
    assert "ambiguous" in str(exit_.value)


def test_no_match_lists_what_there_is():
    """A dead end that does not say what exists sends the reader to grep."""
    with pytest.raises(SystemExit) as exit_:
        ground.find("no-such-experiment")
    assert "does-a-content-free-protocol-help" in str(exit_.value)


def test_no_experiment_directory_is_numbered_any_more():
    """The convention, asserted where it can actually be checked."""
    numbered = [d.name for d in (ROOT / "experiments").iterdir()
                if d.is_dir() and d.name[:3].isdigit()]
    assert numbered == []
