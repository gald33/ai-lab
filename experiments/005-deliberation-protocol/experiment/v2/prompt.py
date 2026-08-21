"""Assembling what one agent sees on one turn.

Two layers, kept apart so the experiment's factors cannot leak into each other
-- and, since they are separated anyway, sent down two different channels so
the invariant one can be cached.

* **The stimulus** -- base, plus the cell's treatment blocks, read from the
  frozen files in ``stimuli/v2`` rather than duplicated here. Identical on
  every turn of a run.
* **The turn** -- this agent's private state, its unread messages, its open
  offers, the action format, and **everything that has happened to it so far
  this round**. Rendered from authoritative world state.

The history block is the round's only channel between episodes. Item stocks,
labour and open offers all reset at each episode's bell; what carries is what an
agent has been told and what it has seen happen. Without it a five-episode round
is five unrelated one-episode rounds, and there is nothing for an agent to
learn. It is trimmed oldest-first when it grows past `HISTORY_CHARS`, and the
trim is announced in the prompt rather than done silently -- an agent that has
forgotten something should know that it has.

``tools/check_v2.py`` hashes the stimulus half and asserts the cells differ by
exactly their treatments, so the parity claim is a test rather than a promise.

Caching
-------
The stimulus is identical on every one of a round's 160 agent-turns, so it goes
in the **system prompt**, which the runtime caches, rather than being re-sent as
user text 160 times. What remains in the user message is ordered by how often it
changes: the round history first, because it is strictly append-only and
therefore a growing cacheable prefix, then this turn's state, inbox and open
offers, which change every turn. Trimming the history rewrites that prefix and
costs a cache miss, which is one more reason to trim rarely.
"""

from __future__ import annotations

import json
from pathlib import Path

STIM = Path(__file__).resolve().parents[2] / "stimuli" / "v2"

#: cell -> (stimulus block or None, hint or not)
CELLS = {
    "bare":     (None,       False),
    "placebo":  ("placebo",  False),
    "protocol": ("protocol", False),
    "hint":     (None,       True),
    "both":     ("protocol", True),
}

#: How much round history an agent carries. Oldest entries are dropped first
#: and the drop is stated in the prompt.
HISTORY_CHARS = 14000

ACTIONS = """\
## How to act

Reply with a single JSON object and nothing else — no prose outside it, no
explanation, no code fence. One key, `actions`, holding a list. The list may be
empty if you want to do nothing this turn.

{"actions": [ {"call": "...", ...}, ... ]}

Each entry is one of:

  {"call": "post", "text": "..."}
  {"call": "message", "to": "T3", "text": "..."}
  {"call": "offer", "to": "T3", "give": {"iron": 0.4}, "want": {"salt": 0.3}}
  {"call": "accept", "offer_id": "o7"}
  {"call": "decline", "offer_id": "o7"}
  {"call": "cancel", "offer_id": "o7"}
  {"call": "produce", "plan": {"bread": 0.5, "iron": 0.5}}

They are executed in the order you give them, and you will see the result of
each one on your next turn. A call belonging to a stage that is not open will
be refused. Nothing you write in `text` is read by the system."""


def body(text: str) -> str:
    """Drop the repo-facing title and italic note; keep from the first heading."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("## "):
            return "\n".join(lines[i:]).strip()
    raise ValueError("stimulus has no body heading")


def stimulus(cell: str, episodes: int) -> str:
    if cell not in CELLS:
        raise ValueError(f"unknown cell {cell!r}")
    block, hint = CELLS[cell]
    parts = [body((STIM / "base.md").read_text())
             .replace("{periods}", str(episodes))]
    if block:
        parts.append(body((STIM / f"{block}.md").read_text()))
    if hint:
        parts.append(body((STIM / "hint.md").read_text()))
    return "\n\n".join(parts)


def _inbox(items: list[dict]) -> str:
    if not items:
        return "Nothing new since your last turn."
    out = []
    for m in items:
        where = "on the board" if m["public"] else "to you privately"
        out.append(f"- **{m['from']}** {where}: {m['text'].strip()}")
    return "\n".join(out)


def _history(entries: list[str]) -> tuple[str, bool]:
    """Most recent last, oldest dropped first if it does not fit."""
    kept: list[str] = []
    used = 0
    for entry in reversed(entries):
        if used + len(entry) > HISTORY_CHARS:
            return "\n".join(reversed(kept)), True
        kept.append(entry)
        used += len(entry)
    return "\n".join(reversed(kept)), False


def turn(*, cell: str, state: dict, inbox: list[dict], pending: dict,
         results: list[str], episodes: int, history: list[str] | None = None) -> str:
    """The turn half of the prompt. The stimulus half travels separately.

    Ordered most-stable-first so that as much of it as possible is a cacheable
    prefix: append-only history, then the volatile per-turn blocks.
    """
    parts = []
    if history:
        text, trimmed = _history(history)
        parts += [f"## What has happened so far this round", ""]
        if trimmed:
            parts.append("*(earlier turns have been dropped to save room; "
                         "what follows is the most recent part)*\n")
        parts += [text, ""]
    parts += [f"## Episode {state['episode'] + 1} of {episodes} — "
              f"the {state['stage']} stage is open", ""]
    if results:
        parts += ["### What happened to your last actions", ""]
        parts += [f"- {r}" for r in results]
        parts.append("")
    parts += ["### Your private state", "",
              "```json", json.dumps(state, indent=1), "```", "",
              "### Messages since your last turn", "", _inbox(inbox), ""]
    if pending["you_offered"] or pending["offered_to_you"]:
        parts += ["### Open offers", "",
                  "```json", json.dumps(pending, indent=1), "```", ""]
    parts += [ACTIONS]
    return "\n".join(parts)
