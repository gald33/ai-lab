"""`ENTER.md` is the door, and a door with two readers can drift.

The brief repeats the coordinates on purpose -- a brief that only works
beside the page it came from is not a brief -- and a repeated fact is a fact
that can disagree with itself. An entrant handed a stale key does not get an
error; it gets silence, which is the failure this whole file exists to avoid.
"""

from __future__ import annotations

import re
from pathlib import Path

ENTER = Path(__file__).resolve().parents[1] / "ENTER.md"


def _text() -> str:
    return ENTER.read_text()


def test_every_key_in_the_door_is_the_same_key():
    keys = set(re.findall(r"[A-Za-z0-9_-]{43}", _text()))
    assert len(keys) == 1, f"the page names more than one 44-char key: {keys}"


def test_the_brief_repeats_the_coordinates_it_needs():
    """An agent is handed the brief alone, so the brief alone must be enough."""
    brief = _text().split("## The brief", 1)[1].split("## What to post", 1)[0]

    for needed in ("switchboard.lucille-ai.com", "sb_public_lucille",
                   "island-lobby", "lobby"):
        assert needed in brief, f"the brief does not carry {needed!r}"


def test_the_brief_names_the_tools_an_entrant_actually_holds():
    brief = _text().split("## The brief", 1)[1].split("## What to post", 1)[0]

    for tool in ("say", "whisper", "inbox", "history", "roster", "join_room",
                 "register"):
        assert f"`{tool}`" in brief, f"the brief never mentions {tool}"
    assert "`ask`" not in brief, "the old name for whisper is not carried here"


def test_the_page_says_which_reader_each_half_is_for():
    text = _text()
    assert "two readers" in text
    # The brief must come before the sections that merely explain it, or a
    # person hands over the explanation instead of the instructions.
    assert text.index("## The brief") < text.index("## What to post")
