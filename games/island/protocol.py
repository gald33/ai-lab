"""What the lobby recognises when it reads its board.

Three formats, mirroring the island manager's own three -- same shape, one
level up:

    OPEN traders=2 episodes=8 rounds=1
    JOIN g7 as scout-v2
    MANAGE g7

The lobby enforces **format**: a line that is nearly one of these is not
repaired into one. It enforces nothing else here -- no partner, no island, no
manager choice. See ``lobby.py`` for what it does with a line once parsed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

OPEN, JOIN, MANAGE = "OPEN", "JOIN", "MANAGE"

_KV = re.compile(r"^([a-z]+)=(-?[0-9]+)$")


class Malformed(Exception):
    """Close to a formatted message, but not one. Never repaired."""


@dataclass(frozen=True)
class Open:
    traders: int
    episodes: int
    rounds: int = 1


@dataclass(frozen=True)
class Join:
    table: str
    name: str


@dataclass(frozen=True)
class Manage:
    table: str


def parse(text: str):
    """Return an Open/Join/Manage, or None if this line is just talk.

    Raises ``Malformed`` when a line opens with a keyword but does not parse
    -- somebody tried to act and got the format wrong, which they should be
    told, the same distinction ``island/protocol.py`` draws.
    """
    stripped = text.strip()
    head = stripped.split(None, 1)[0].upper() if stripped else ""
    if head not in (OPEN, JOIN, MANAGE):
        return None
    rest = stripped[len(head):].strip()

    if head == OPEN:
        fields: dict[str, int] = {}
        for part in rest.split():
            m = _KV.match(part)
            if not m:
                raise Malformed(f"OPEN wants key=integer pairs, got {part!r}")
            fields[m.group(1)] = int(m.group(2))
        missing = [k for k in ("traders", "episodes") if k not in fields]
        if missing:
            raise Malformed(f"OPEN is missing {', '.join(missing)}")
        extra = set(fields) - {"traders", "episodes", "rounds"}
        if extra:
            raise Malformed(f"OPEN does not understand {', '.join(sorted(extra))}")
        if fields["traders"] < 2:
            raise Malformed("a table needs at least 2 traders")
        if fields["episodes"] < 1:
            raise Malformed("a table needs at least 1 episode")
        rounds = fields.get("rounds", 1)
        if rounds < 1:
            raise Malformed("a table needs at least 1 round")
        return Open(traders=fields["traders"], episodes=fields["episodes"], rounds=rounds)

    if head == JOIN:
        parts = rest.split()
        if len(parts) != 3 or parts[1].lower() != "as":
            raise Malformed("JOIN wants '<table> as <name>'")
        table, _, name = parts
        return Join(table=table, name=name)

    if head == MANAGE:
        parts = rest.split()
        if len(parts) != 1:
            raise Malformed("MANAGE wants exactly one table id")
        return Manage(table=parts[0])
