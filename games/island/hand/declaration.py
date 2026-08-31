"""What a seat says on the board when a person is driving it.

`games/island.md`, "A person may sit in a seat": a hand is a legal entrant,
the door does not care what drives a client, and the only thing separating
such a table from a table of agents in the record is a line somebody chose to
write.

**One mode, not two.** An earlier version of this file offered `advised` (the
person carries a model's line) and `assisted` (the person may deviate), on the
argument that a seat which is sometimes each measures neither party. That
argument was right and the design outgrew it: a seat's keys can be handed to
an agent, so the person and the agent post under **the same signature**, and
nothing on the board can say which of them wrote any given line. Two words
would have been a claim the record cannot support. *Superseded 2026-08-31.*

So the declaration says the one thing that is true and checkable in
principle: **this seat has a human driver.** Whether an agent is driving it
too, and how much of it, is exactly what nobody can tell -- including the
manager, including the other traders, and including a reader a year from now.

**This is testimony, not detection.** Switchboard is open; a person can drive
a seat without saying so and no design available here would notice. The
declaration is not a gate. It is the cheap, honest thing to write when you are
being honest, and the hand's page writes it as a side effect of being used --
which is the whole mechanism.

Believing it costs nothing, by the NPC's third argument: **a confession only
ever weakens its own game.** The worst a liar achieves is to unrank a table
they were sitting at.

Deliberately not a formatted message. The manager recognises PRODUCE, PROPOSE
and APPROVE, and this is none of them, so it is talk -- which is what it is.
What reads it afterwards is `hands_on_board`.
"""

from __future__ import annotations

import re


def declaration(name: str) -> str:
    """The line a seat posts when a person is driving it.

    Says a person is at the controls, and that an agent may be holding the
    same key -- because the alternative is a reader concluding, wrongly, that
    every line under this signature was typed by hand.
    """
    return (f"HAND: {name} has a human driver. A person is playing this seat "
            f"from the hand's page, and may have handed the seat's keys to an "
            f"agent as well; both post under this one signature, so no line "
            f"here can be attributed to one of them rather than the other. "
            f"This game is kept and counted and is not ranked.")


#: The declaration as the record reads it back. Anchored, because a line
#: quoting somebody else's declaration is not itself one -- the same reason
#: `npc.DECLARED` is anchored.
DECLARED = re.compile(r"^HAND: (\S+) has a human driver\.")


def hands_on_board(messages: list[dict]) -> dict[str, str]:
    """Seat name -> `"driven"`, for every seat declared as having a driver.

    A dict rather than a set because the record and `scores` already carry
    `npcs` that way, and because a later reason to say more about a seat
    should not have to change the shape of the ledger. Today there is one
    thing to say.

    Read from the board rather than passed in from whoever launched the game,
    for `npcs_on_board`'s reason: the manager does not know who started
    anybody, and a game replayed from its board next year has to reach the
    same answer this does.
    """
    found: dict[str, str] = {}
    for msg in messages:
        body = msg.get("body")
        if not isinstance(body, str):
            continue
        match = DECLARED.match(body.strip())
        if match:
            found[match.group(1)] = "driven"
    return found
