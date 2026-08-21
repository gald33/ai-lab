"""The text an agent sees. This file is the instrument, so it is written out
in full rather than assembled from fragments at call time.

Four blocks, in this order, and only two of them vary:

1. ``TASK``      identical in every cell. It states the game and what counts as
                 winning it. It does not say how to deliberate.
2. the stimulus  `stimuli/protocol.md` in the protocol cells,
                 `stimuli/placebo.md` in the others. Frozen, hash-pinned, and
                 read from disk rather than duplicated here so that a
                 divergence between what was frozen and what was sent is
                 impossible rather than merely unlikely.
3. the hint      present only in the ``hint`` cells.
4. the round     the agent's private signal, what it heard, and the format.

The task block deliberately contains the *objective* — agree, and be right —
because that is the game, not the manipulation. If it were only in the protocol
cells, those agents would be pursuing a goal the others had not been given, and
the experiment would be measuring instructions rather than method.
"""

from __future__ import annotations

from pathlib import Path

from .market import GOODS

STIMULI = Path(__file__).resolve().parents[2] / "stimuli"

TASK = """\
You are one of 8 independent traders on an island that trades four goods:
bread, cloth, iron and salt.

There is one true set of relative prices on this island. Nobody knows it. You
hold your own private estimate of it, which is close but noisy, and every other
trader holds their own, drawn independently. Your estimate is not better or
worse than theirs.

The game runs for a fixed number of rounds. In each round you write one short
message and submit one price vector. Your message is passed to a small number
of the other traders, and you are shown the messages and submissions of a small
number of them. You never see everyone.

At the end, every trader trades at the vector they last submitted. Two traders
who submitted different vectors will fail to trade with each other, and both
lose. Two traders who submitted the same vector trade successfully, and they do
better the closer that vector is to the island's true prices.

So you are trying to do two things at once: end up submitting the same vector
as the others, and have that vector be right. Agreeing on something wrong is
better than not agreeing, and agreeing on something right is better still.

Prices are relative. Bread is the numeraire and is always exactly 1.00."""

HINT_BLOCK = """\
## An estimate you have been given

Every trader on the island has been given this same estimate, and every trader
knows that every trader has been given it. It was produced independently of
your private estimate and is closer to the true prices than yours is, but it is
not exact.

{hint}"""

FORMAT = """\
## Your reply

Reply with a single JSON object and nothing else — no prose before or after, no
explanation. Exactly these two keys:

{{"message": "<at most 60 words, what you want the traders who hear you to read>",
 "prices": {{"bread": 1.0, "cloth": <number>, "iron": <number>, "salt": <number>}}}}

"prices" is your submission for this round. It is what you would trade at if
the game ended now, and it is the only thing that is scored. Bread must be
exactly 1.0. Say whatever you like in "message"; nobody is checking it."""


def _vector(price: list[float]) -> str:
    return "  ".join(f"{g} {p:.3f}" for g, p in zip(GOODS, price))


def read_stimulus(kind: str) -> str:
    """Load a frozen stimulus. ``kind`` is 'protocol' or 'placebo'."""
    if kind not in ("protocol", "placebo"):
        raise ValueError(f"unknown stimulus {kind!r}")
    text = (STIMULI / f"{kind}.md").read_text()
    # Drop the file's own front matter: the title line and the italic note
    # explaining what the file is for are addressed to a reader of the
    # repository, not to a participant.
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("You are one of several people"):
            start = i
            break
    return "\n".join(lines[start:]).strip()


def build(*, stimulus: str, hint: list[float] | None, signal: list[float],
          heard: list[tuple[int, str, list[float]]], round_index: int,
          rounds: int) -> str:
    """The full prompt for one agent in one round."""
    parts = [TASK, "", "## How to go about it", "", stimulus]
    if hint is not None:
        parts += ["", HINT_BLOCK.format(hint=_vector(hint))]
    parts += ["", "## Your private estimate", "", _vector(signal)]
    if round_index == 0:
        parts += ["", f"## Round 0 of {rounds}", "",
                  "Nobody has spoken yet. This is your opening submission."]
    else:
        parts += ["", f"## Round {round_index} of {rounds}", "",
                  "Since the last round you heard from these traders:"]
        for index, message, price in heard:
            parts += ["", f"**Trader {index}** submitted: {_vector(price)}",
                      f"and said: {message.strip() or '(nothing)'}"]
    parts += ["", FORMAT]
    return "\n".join(parts)
