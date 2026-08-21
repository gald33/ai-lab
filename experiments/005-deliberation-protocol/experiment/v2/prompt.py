"""Assembling what one agent sees on one turn.

Two layers, kept apart so the experiment's factors cannot leak into each other:

* **The stimulus** -- base, plus the cell's treatment blocks, read from the
  frozen files in ``stimuli/v2`` rather than duplicated here. Identical on
  every turn of a run.
* **The turn** -- this agent's private state, its unread messages, its open
  offers, and the action format. Rendered from authoritative world state.

``tools/check_v2.py`` hashes the stimulus half and asserts the cells differ by
exactly their treatments, so the parity claim is a test rather than a promise.
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


def stimulus(cell: str, periods: int) -> str:
    if cell not in CELLS:
        raise ValueError(f"unknown cell {cell!r}")
    block, hint = CELLS[cell]
    parts = [body((STIM / "base.md").read_text()).replace("{periods}", str(periods))]
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


def turn(*, cell: str, state: dict, inbox: list[dict], pending: dict,
         results: list[str], periods: int) -> str:
    """The full prompt for one agent on one turn."""
    parts = [stimulus(cell, periods), "", "---", "",
             f"## Period {state['period'] + 1} of {periods} — "
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
