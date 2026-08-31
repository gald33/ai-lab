"""The hand's declaration, and the limit of what it proves.

`games/island/hand/declaration.py` is testimony. These tests check that the
line is written, read back and acted on -- and one of them checks the thing
that is *not* true, because a taxonomy whose limits are only in prose is one
the code does not have. That lesson is already on the record here: the
practice flag was written in `games/island.md` from the start and games were
ranked anyway, because nothing read it.
"""

from __future__ import annotations

import pytest

from games.island.hand.declaration import (MODES, declaration, hands_on_board)


def _board(*bodies):
    return [{"body": b} for b in bodies]


@pytest.mark.parametrize("mode", MODES)
def test_a_declaration_is_read_back_off_the_board(mode):
    """Written by the page, read by the record, with nothing passed between.

    The manager does not know who launched anybody and must not have to: a
    game replayed from its board next year has to reach the answer this does.
    """
    assert hands_on_board(_board(declaration("T1", mode))) == {"T1": mode}


def test_both_modes_are_kept_apart():
    """A seat that is sometimes one and sometimes the other measures neither
    the model nor the person, which is why there are two words and not one."""
    board = _board(declaration("T1", "advised"), declaration("T2", "assisted"))
    assert hands_on_board(board) == {"T1": "advised", "T2": "assisted"}


def test_quoting_somebody_elses_declaration_is_not_making_one():
    """Anchored, for `npc.DECLARED`'s reason.

    The board is talk as well as trade, and a trader saying "you posted HAND:
    T1 is played by a person" has declared nothing about itself.
    """
    quoted = f"I see that {declaration('T1', 'advised')}"
    assert hands_on_board(_board(quoted)) == {}


def test_a_mode_nobody_defined_is_refused_at_the_point_of_writing():
    """Rather than written and silently unread later."""
    with pytest.raises(ValueError, match="advised or assisted"):
        declaration("T1", "surrogate")


def test_the_declaration_is_talk_and_not_a_formatted_message():
    """The manager recognises PRODUCE, PROPOSE and APPROVE. This is none of
    them on purpose: a declaration settles nothing and must not look as
    though it might."""
    line = declaration("T1", "advised")
    assert not line.startswith(("PRODUCE", "PROPOSE", "APPROVE"))
    assert "is not ranked" in line


def test_an_undeclared_hand_is_not_caught_by_anything(monkeypatch):
    """**The limit, asserted rather than described.**

    Switchboard is open. A person can play a seat and say nothing, and the
    board that results is indistinguishable from a table of agents -- because
    the record only ever sees signed lines from a key, never what was driving
    the client that sent them. Nothing in this repository detects it and
    nothing here pretends to.

    This test exists so that the day somebody adds detection, it fails and
    makes them come and change the sentence in `games/island.md` that says
    there is none.
    """
    played_by_a_person = _board(
        "PRODUCE bread=3 fish=1",
        "PROPOSE 2 bread for 3 fish",
        "happy to trade if you need bread",
    )
    assert hands_on_board(played_by_a_person) == {}
