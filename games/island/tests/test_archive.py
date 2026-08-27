"""Condition 3: a second copy, and what it is able to say.

The tests that matter here are the disagreement ones. An archive that only
ever agrees with the board is indistinguishable from no archive at all, so
what is checked below is that a line the manager left out is *found*, and that
the archive is honest about the places it could not have found one.
"""

from __future__ import annotations

import json

from games.island.archive import (INDEPENDENT, SAME_PARTY, WINDOW, Archivist,
                                  compare)


class _Room:
    """A channel that hands back the last `WINDOW` lines, like the hub."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.fail = False

    def history(self, channel, limit=WINDOW):
        if self.fail:
            raise RuntimeError("hub blinked")
        return self.rows[-limit:]

    def post(self, seq, body, who="T1"):
        self.rows.append({"seq": seq, "created_at": f"t{seq}",
                          "from": who, "body": body})


def _arc(room, standing=INDEPENDENT):
    return Archivist(client=room, channel="island", writer="mgr",
                     standing=standing, clock=lambda: 100.0)


def _board(rows):
    return {"messages": [{"seq": r["seq"], "body": r["body"]} for r in rows]}


def test_it_finds_a_line_the_board_does_not_carry():
    """The whole reason the file exists."""
    room = _Room()
    for seq, body in [(1, "PRODUCE"), (2, "PROPOSE"), (3, "APPROVE")]:
        room.post(seq, body)
    arc = _arc(room)
    arc.catch_up()

    # The manager writes down everything except the middle line.
    diff = compare(_board([r for r in room.rows if r["seq"] != 2]),
                   arc.payload())

    assert [m["body"] for m in diff["missing"]] == ["PROPOSE"]
    assert diff["altered"] == []


def test_it_finds_a_line_whose_text_changed():
    room = _Room()
    room.post(1, "APPROVE g1 2 wood")
    arc = _arc(room)
    arc.catch_up()

    diff = compare({"messages": [{"seq": 1, "body": "APPROVE g1 9 wood"}]},
                   arc.payload())

    assert diff["altered"] == [1]


def test_agreement_says_nothing_is_missing():
    room = _Room()
    room.post(1, "PRODUCE")
    room.post(2, "APPROVE")
    arc = _arc(room)
    arc.catch_up()

    diff = compare(_board(room.rows), arc.payload())

    assert diff["missing"] == [] and diff["altered"] == []
    assert diff["witnessed"] == 2 and diff["on_board"] == 2


def test_a_line_written_before_it_looked_is_not_called_an_invention():
    """Blindness, not evidence.

    The archivist joined at seq 5. Lines 1-4 are on the board and it never saw
    them, which says nothing about the manager -- and an archive that reported
    them as extras would cry wolf on every game it joined late.
    """
    room = _Room()
    for seq in range(1, 9):
        room.post(seq, f"line {seq}")
    arc = _arc(room)
    arc.rows = {}                      # joined late: only 5..8 are read
    arc.client = _Room(room.rows[4:])
    arc.catch_up()

    diff = compare(_board(room.rows), arc.payload())

    assert diff["extra"] == [1, 2, 3, 4]
    assert diff["unexplained_extra"] == []
    assert arc.payload()["before_first_read"] == 4


def test_it_declares_the_hole_when_the_board_outran_it():
    """A gap between two lines it did read is a line it provably missed."""
    room = _Room()
    room.post(1, "first")
    arc = _arc(room)
    arc.catch_up()
    room.post(2, "unseen")
    room.rows = [r for r in room.rows if r["seq"] != 2]   # gone before it looked
    room.post(3, "third")
    arc.catch_up()

    assert arc.gaps() == [2]
    # And a board line inside that hole is explained by it, not blamed on it.
    diff = compare(_board([{"seq": 2, "body": "unseen"}]), arc.payload())
    assert diff["unexplained_extra"] == []


def test_a_read_that_fails_is_counted_and_not_raised():
    """An archivist that can kill the game it watches costs more than it is
    worth -- and hands the manager a reason to want it gone."""
    room = _Room()
    room.post(1, "a")
    arc = _arc(room)
    room.fail = True

    assert arc.catch_up() == 0
    assert arc.failed == 1

    room.fail = False
    assert arc.catch_up() == 1


def test_a_full_window_is_recorded_as_a_warning():
    room = _Room([{"seq": i, "created_at": "t", "from": "T1", "body": str(i)}
                  for i in range(1, WINDOW + 1)])
    arc = _arc(room)
    arc.catch_up()

    assert arc.payload()["saturated_polls"] == 1


def test_the_archive_says_which_kind_of_witness_it_was():
    """An archive that let a same-party copy pass for an independent one would
    be worth less than none: it would look like a check."""
    room = _Room()
    room.post(1, "a")

    lab = _arc(room, standing=SAME_PARTY)
    lab.catch_up()
    stranger = _arc(room, standing=INDEPENDENT)
    stranger.catch_up()

    assert lab.payload()["standing"] == SAME_PARTY
    assert stranger.payload()["standing"] == INDEPENDENT
    assert compare(_board(room.rows), lab.payload())["standing"] == SAME_PARTY


def test_it_writes_a_file_named_for_the_room(tmp_path):
    room = _Room()
    room.post(1, "a")
    arc = _arc(room)
    arc.catch_up()
    arc.close()

    path = arc.save(tmp_path, "island-lobby-g1")

    assert path.name == "archive-island-lobby-g1.json"
    saved = json.loads(path.read_text())
    assert saved["closed_at"] == 100.0 and saved["lines"] == 1
    assert saved["messages"][0]["body"] == "a"
