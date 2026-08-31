"""The driver's declaration and brief, and the limits of both.

`games/island/hand/declaration.py` is testimony; `hand/brief.py` is what a
driver hands an agent. These tests check that the line is written, read back
and acted on, that the brief withholds what it is supposed to withhold -- and
one of them checks the thing that is *not* true, because a taxonomy whose
limits live only in prose is one the code does not have. That lesson is
already on the record here: the practice flag was written in `games/island.md`
from the start and games were ranked anyway, because nothing read it.
"""

from __future__ import annotations

import pytest

from games.island.hand.brief import brief
from games.island.hand.declaration import declaration, hands_on_board


def _board(*bodies):
    return [{"body": b} for b in bodies]


def _flat(text: str) -> str:
    """The brief as a reader takes it, with the line wrapping collapsed.

    It is prose: where a sentence breaks is cosmetic, and an assertion that
    depended on it would fail the next time a word was added. What is being
    checked is what the brief says, not how it is folded.
    """
    return " ".join(text.split())


def _brief(**over):
    args = dict(seat="T1", workspace="island-g7", room_key="k" * 43,
                channel="island", agent_id="t1",
                signing_key="s" * 43, exchange_key="x" * 43,
                episodes=8, seconds=90.0)
    args.update(over)
    return brief(**args)


# --- the declaration -------------------------------------------------------

def test_a_declaration_is_read_back_off_the_board():
    """Written by the page, read by the record, with nothing passed between.

    The manager does not know who launched anybody and must not have to: a
    game replayed from its board next year has to reach the answer this does.
    """
    assert hands_on_board(_board(declaration("T1"))) == {"T1": "driven"}


def test_the_declaration_claims_a_driver_and_never_how_much_they_drove():
    """**One reason, because two would be a claim the record cannot support.**

    A driver may hand the seat's keys to an agent, and then both post under
    one signature. Nothing on the board separates them -- not the manager, not
    the other traders, not a reader a year from now -- so the line says a
    person is at the controls and stops there. It used to say `advised` or
    `assisted`; that distinction died with the shared key.
    """
    line = declaration("T1")

    assert "has a human driver" in line
    assert "may have handed the seat's keys to an agent" in line
    assert "no line here can be attributed to one of them" in line
    assert "advised" not in line and "assisted" not in line


def test_quoting_somebody_elses_declaration_is_not_making_one():
    """Anchored, for `npc.DECLARED`'s reason.

    The board is talk as well as trade, and a trader saying "you posted HAND:
    T1 has a human driver" has declared nothing about itself.
    """
    quoted = f"I see that {declaration('T1')}"
    assert hands_on_board(_board(quoted)) == {}


def test_the_declaration_is_talk_and_not_a_formatted_message():
    """The manager recognises PRODUCE, PROPOSE and APPROVE. This is none of
    them on purpose: a declaration settles nothing and must not look as
    though it might."""
    line = declaration("T1")
    assert not line.startswith(("PRODUCE", "PROPOSE", "APPROVE"))
    assert "is not ranked" in line


def test_an_undeclared_driver_is_not_caught_by_anything():
    """**The limit, asserted rather than described.**

    Switchboard is open. A person can drive a seat and say nothing, and the
    board that results is indistinguishable from a table of agents -- because
    the record only ever sees signed lines from a key, never who was at the
    keyboard behind it. Nothing in this repository detects that and nothing
    here pretends to.

    This test exists so that the day somebody adds detection, it fails and
    makes them come and change the sentence in `games/island.md` that says
    there is none.
    """
    driven_in_silence = _board(
        "PRODUCE bread=3 fish=1",
        "PROPOSE 2 bread for 3 fish",
        "happy to trade if you need bread",
    )
    assert hands_on_board(driven_in_silence) == {}


# --- the brief -------------------------------------------------------------

def test_the_brief_withholds_the_lobby_so_the_agent_cannot_leave_one_room():
    """**A property, not an instruction.**

    The person opens and joins by hand; the agent is handed one room and never
    the lobby's coordinates. So it is not that the agent is asked not to open
    a table -- it is that an `OPEN` or a `JOIN` it wrote would land in no room
    anybody reads. That matters beyond tidiness: `OPEN` is the one verb that
    spends the lab's budget, which is why the lobby caps it, and a second
    `JOIN` would take another seat in the driver's name.
    """
    flat = _flat(_brief())

    assert "island-lobby" not in flat, "the lobby's workspace is not in here"
    # Its published key is in `ENTER.md` and in the page; it is not in this.
    assert "Z822U5v1WFyeOEJUeLchMgLED-VgI_0chD4OjmRxej0" not in flat
    assert "You have not" in flat and "lobby's coordinates" in flat
    assert "nothing for you to open and nothing for you to join" in flat


def test_the_brief_warns_that_the_agent_will_see_its_own_signature():
    """The one thing an agent cannot work out from the room.

    Lines arrive attributed to its seat, signed with its own key, that it did
    not write -- and a key that did not match a seat is exactly what the
    manager's own machinery calls an impostor. Unwarned, the sensible reading
    of a driver is "somebody is forging me".
    """
    flat = _flat(_brief())

    assert "that you did not write" in flat
    assert "not an impostor" in flat
    assert "they are your driver" in flat


def test_the_brief_carries_the_seat_key_because_there_is_no_alternative():
    """The lobby witnesses one key per seat and the manager refuses any line
    that does not match it, so a driver and their agent post under the same
    signature or the agent does not play. That is why the hand's identity is
    extractable where nothing else here would be."""
    flat = _flat(_brief(signing_key="SIGN-ME", exchange_key="SEAL-ME"))

    assert "SIGN-ME" in flat and "SEAL-ME" in flat
    assert "refused by the manager" in flat


def test_the_brief_names_the_clock_that_will_not_wait():
    """A driver-and-agent seat is slower than an agent, and the bell does not
    move for it (`games/island.md`, "The clock does not move")."""
    flat = _flat(_brief(episodes=3, seconds=45.0))

    assert "3 episodes" in flat
    assert "45 seconds" in flat and "the bell does not wait" in flat


def test_the_brief_gives_the_three_forms_and_says_nothing_else_is_a_move():
    """The manager never repairs a malformed line into a plausible one, so an
    agent that half-remembers the grammar simply does not play."""
    flat = _flat(_brief())

    for form in ("PRODUCE", "PROPOSE", "APPROVE"):
        assert form in flat
    assert "Nothing else is a move" in flat
    assert "never repairs a malformed line" in flat
