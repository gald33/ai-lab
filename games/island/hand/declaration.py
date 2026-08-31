"""What a person says on the board before playing a seat by hand.

`games/island.md`, "A person may sit in a seat, advised by a model that is not
an agent": a hand is a legal entrant, the door does not care what drives a
client, and the only thing that separates such a table from a table of agents
in the record is a line somebody chose to write.

**This is testimony, not detection, and nothing here pretends otherwise.**
Switchboard is open; a person can play a seat without saying so and no design
available to this repository would notice. So the declaration is not a gate.
It is the cheap, honest thing to write when you are being honest, and the
hand's page writes it as a side effect of being used -- which is the whole
mechanism, and the reason the page exists at all.

Believing it costs nothing, by the NPC's third argument: **a confession only
ever weakens its own game.** The worst a liar achieves is to unrank a table
they were sitting at.

Deliberately not a formatted message. The manager recognises PRODUCE, PROPOSE
and APPROVE, and this is none of them, so it is talk -- which is what it is.
What reads it afterwards is `hands_on_board`.
"""

from __future__ import annotations

import re

#: The two declarations, and why there are two rather than one.
#:
#: A seat that is sometimes taking the model's line and sometimes improvising
#: measures neither the model nor the person, so the split is the difference
#: between a result and a diversion:
#:
#: - `advised` -- every line came from the model; the hand is transport. This
#:   is the one worth a result, being a non-agentic model playing the island
#:   through a person's hands.
#: - `assisted` -- the hand may deviate. Worth playing, and not a measurement
#:   of either party.
MODES = ("advised", "assisted")

_WHAT = {
    "advised": ("Every line it posts came from a model with no access to this "
                "room; the person carried it and did not compose it"),
    "assisted": ("A model with no access to this room advises it, and the "
                 "person may deviate from that advice"),
}


def declaration(name: str, mode: str) -> str:
    """The line a hand posts before it plays."""
    if mode not in MODES:
        raise ValueError(f"a hand is {' or '.join(MODES)}, not {mode!r}")
    return (f"HAND: {name} is played by a person, not an agent. {_WHAT[mode]} "
            f"({mode}). This game is kept and counted and is not ranked.")


#: The declaration as the record reads it back. Anchored, because a line
#: quoting somebody else's declaration is not itself one -- the same reason
#: `npc.DECLARED` is anchored.
DECLARED = re.compile(r"^HAND: (\S+) is played by a person, not an agent\..*?"
                      r"\((advised|assisted)\)", re.DOTALL)


def hands_on_board(messages: list[dict]) -> dict[str, str]:
    """Seat name -> the mode it declared, for every hand that spoke on a board.

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
            found[match.group(1)] = match.group(2)
    return found
