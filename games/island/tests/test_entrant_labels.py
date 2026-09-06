"""`harness=` and `by=`: optional at the door, and never anywhere near a score.

Added 2026-09-06 for the public launch. The interesting question about a public
board is which *kinds* of agent do well -- can fifty lines of Python beat a
frontier coding agent -- and the ledger could not answer it, because a row's
only identity was a name the entrant chose and a `model` field that read
`"entrants"` for every game played through the door.

Three properties are worth holding, and each has a way of going wrong:

1. **Optional.** A required field is a new way to be refused at a door whose
   whole purpose is being easy to get through. Every existing `JOIN` shape must
   still parse and still seat.
2. **Bounded and refused, never repaired.** The lobby does not repair a
   malformed line into a plausible one, here as everywhere.
3. **Never scored.** `CLAUDE.md`: self-reports are non-authoritative, and
   metrics come from settled state. A label an entrant writes about itself must
   not move a number -- so the same round scored with and without labels has to
   produce the same score, byte for byte.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "experiments" / "005-deliberation-protocol" / "viewer"))

import scores  # noqa: E402

from games.island.protocol import Malformed, parse  # noqa: E402


# ---- 1. optional ----------------------------------------------------------

@pytest.mark.parametrize("line", [
    "JOIN g7 as scout-v2",
    "JOIN g7 as scout-v2 nonce=0123456789abcdef",
])
def test_a_join_without_labels_still_parses(line):
    """The door does not get narrower because it got more expressive."""
    joined = parse(line)
    assert joined.name == "scout-v2"
    assert joined.harness == "" and joined.by == ""


def test_both_labels_are_carried_in_any_order():
    a = parse("JOIN g7 as s nonce=0123456789abcdef harness=claude-code by=gald33")
    b = parse("JOIN g7 as s by=gald33 harness=claude-code nonce=0123456789abcdef")
    assert a == b
    assert (a.harness, a.by) == ("claude-code", "gald33")


def test_either_label_alone_is_enough():
    assert parse("JOIN g7 as s harness=bash").harness == "bash"
    assert parse("JOIN g7 as s by=gald33").by == "gald33"


# ---- 2. refused, never repaired -------------------------------------------

@pytest.mark.parametrize("line,says", [
    ("JOIN g7 as s harness=", "harness="),
    ("JOIN g7 as s by=", "by="),
    ("JOIN g7 as s harness=" + "x" * 33, "harness="),
    ("JOIN g7 as s by=gal@example.com", "email"),
    ("JOIN g7 as s harness=claude code", "one word"),
])
def test_a_malformed_label_is_refused_by_name(line, says):
    with pytest.raises(Malformed) as exc:
        parse(line)
    assert says in str(exc.value)


def test_a_label_written_twice_is_refused_rather_than_chosen_between():
    """The same rule `nonce=` has, for the same reason.

    A line carrying two answers is not a line with one, and a parser that picks
    by position is repairing a malformed message into a plausible one.
    """
    with pytest.raises(Malformed) as exc:
        parse("JOIN g7 as s harness=a harness=b")
    assert "twice" in str(exc.value)


def test_an_unknown_field_is_still_unknown():
    with pytest.raises(Malformed):
        parse("JOIN g7 as s model=gpt-5")


# ---- 3. never scored ------------------------------------------------------

def _round():
    return {"workspace": "w_test", "seed": 7,
            "trajectory": [[0.4, 0.5], [0.45, 0.52]]}


def _record():
    return {"agents": 2, "goods": 5, "episode_seconds": 60, "model": "entrants"}


def test_labels_change_no_number_on_the_row():
    """The same round, scored with and without labels, scores identically.

    This is the property that matters and the one that would be quietly lost if
    a label ever reached the arithmetic -- so it is asserted over the whole row
    rather than over the fields somebody remembered to check.
    """
    bare = scores.entry(_record(), _round(), players={"T1": "a", "T2": "b"})
    told = scores.entry(_record(), _round(), players={"T1": "a", "T2": "b"},
                        entrants={"T1": {"harness": "bash", "by": "gald33"}})
    scored = {k: v for k, v in bare.items()
              if k not in ("players", "recorded_at")}
    assert scored == {k: v for k, v in told.items()
                      if k not in ("players", "recorded_at")}


def test_a_label_lands_on_its_own_seat_and_nowhere_else():
    row = scores.entry(_record(), _round(), players={"T1": "a", "T2": "b"},
                       entrants={"T1": {"harness": "bash", "by": "gald33"}})
    one, two = row["players"]
    assert one == {"slot": "T1", "id": "a", "model": "entrants",
                   "harness": "bash", "by": "gald33"}
    # The seat that declared nothing carries nothing -- not an empty string,
    # and not "unknown". Most rows in this ledger predate the field entirely.
    assert two == {"slot": "T2", "id": "b", "model": "entrants"}
    assert "harness" not in two and "by" not in two


def test_a_seat_that_declared_only_one_carries_only_one():
    row = scores.entry(_record(), _round(), players={"T1": "a", "T2": "b"},
                       entrants={"T1": {"harness": "python"}})
    assert row["players"][0] == {"slot": "T1", "id": "a", "model": "entrants",
                                 "harness": "python"}


def test_every_existing_ledger_row_still_reads():
    """No row in the file has these fields, and none of them may start failing.

    The ledger is the record. A schema change that made 331 existing rows
    unreadable would be the reporting failure this repo keeps writing about,
    arrived at through a feature.
    """
    rows = scores.load()
    assert rows, "the ledger is empty; this test is checking nothing"
    for row in rows:
        for player in row["players"]:
            assert "slot" in player and "id" in player
            assert player.get("harness") is None or isinstance(
                player["harness"], str)
