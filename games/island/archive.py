"""A second copy of a board, kept by somebody other than the party writing it.

**This is condition 3** (`games/island.md`), the one of the four that cannot
be built by a manager alone. `verify.py` recomputes everything a board *says*
and can say nothing about what a board *omits*: a manager that never wrote a
line down leaves no arithmetic behind for anyone to check. The only thing that
catches omission is a second party who was in the room at the time.

**Live, and published after the round.** The hub keeps a board about an hour,
so an archivist that fetches afterwards is reading the same surviving copy as
everybody else and adds no independence at all -- by then the only witness to
a suppressed line is the party that suppressed it. So this reads the room
while the game runs. It publishes when the round ends, which costs nothing:
the seed is revealed then anyway and every line on the board was public to the
room from the moment it was written.

**Independence is a property of who manages, not of this code.** The lobby
runner holds every table's room key -- it minted it -- so it can archive any
table it dealt without asking. When a *stranger* manages, the archivist is
genuinely a different party from the writer and the copy carries weight. When
the lab's own process manages, the archivist is a second client in the same
process: two clients are not two parties, and the copy proves nothing it did
not already assert. Both are kept, and **each archive says on its face which
it is** -- an archive that let the second kind pass for the first would be
worth less than none, because it would look like a check.

**It records its own blindness.** An archive whose whole value is catching
what somebody else left out has to say where its own eyes were shut: lines it
never saw because it joined after they were written, and gaps where the board
outran its read window between two polls. Otherwise it inherits exactly the
blindness it exists to fix, and quietly.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

#: How many rows a poll asks for. The same window the lobby reads under, and
#: for the same reason: ask for more than the hub will return and a quiet gap
#: looks like a quiet board.
WINDOW = 500

#: What this archivist is to the party that wrote the board.
INDEPENDENT = "independent"
SAME_PARTY = "same-party"


@dataclass
class Archivist:
    """One room, read live, written down afterwards.

    `client` is its own -- its own signing identity, its own reads -- and is
    never the manager's. Sharing one would make the archive a copy of the
    manager's opinion of the room rather than a second look at it.
    """

    client: object
    channel: str
    #: Who wrote this board: the display name of the party managing the table.
    writer: str
    #: `INDEPENDENT` when that party is somebody else, `SAME_PARTY` when it is
    #: this process. Not inferred here -- the caller knows, and a guess would
    #: be the one field nobody should guess.
    standing: str
    clock: object = time.time

    #: seq -> the row as it was read. Keyed by seq so a line seen twice is
    #: stored once and a line seen never is visibly absent.
    rows: dict[int, dict] = field(default_factory=dict)
    polls: int = 0
    #: Polls that came back full. A full window is not proof of loss, but it
    #: is the only warning available that the board may have outrun the read.
    saturated: int = 0
    failed: int = 0
    opened_at: float | None = None
    closed_at: float | None = None

    def catch_up(self) -> int:
        """One read. Returns how many lines were new to this archive.

        Never raises: an archivist that kills the game it is watching has cost
        more than it can ever be worth, so a failed read is counted and the
        next poll tries again.
        """
        self.polls += 1
        if self.opened_at is None:
            self.opened_at = self.clock()
        try:
            rows = self.client.history(self.channel, limit=WINDOW)
        except Exception:      # noqa: BLE001 -- see the docstring
            self.failed += 1
            return 0
        if len(rows) >= WINDOW:
            self.saturated += 1
        fresh = 0
        for row in rows:
            seq = row.get("seq")
            if not isinstance(seq, int) or seq in self.rows:
                continue
            self.rows[seq] = row
            fresh += 1
        return fresh

    def close(self) -> None:
        """The round is over; nothing more will be witnessed."""
        self.closed_at = self.clock()

    # -- what it did not see ------------------------------------------------

    def gaps(self) -> list[int]:
        """Seq numbers missing from the middle of what this archive holds.

        Only the middle: a hole between two lines it did read is a line it
        provably missed. What came before its first read is a different kind
        of blindness and is reported as `before`, because an archivist cannot
        know how much of that there was.
        """
        if not self.rows:
            return []
        seen = set(self.rows)
        return [s for s in range(min(seen), max(seen) + 1) if s not in seen]

    def before(self) -> int:
        """Lines written to this room before this archive's first read.

        Read at join rather than witnessed live. They are kept -- a board
        missing its opening is worse than one whose opening is second-hand --
        but they are not evidence of the same weight, and saying so is the
        point of this field.
        """
        return max(0, (min(self.rows) - 1)) if self.rows else 0

    def payload(self) -> dict:
        return {
            "channel": self.channel,
            "writer": self.writer,
            "standing": self.standing,
            "archivist": getattr(getattr(self.client, "config", None),
                                 "agent_id", None)
                         or getattr(self.client, "agent_id", "?"),
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "polls": self.polls,
            "lines": len(self.rows),
            # Everything below is what this copy cannot vouch for.
            "before_first_read": self.before(),
            "gaps": self.gaps(),
            "saturated_polls": self.saturated,
            "failed_polls": self.failed,
            "messages": [{"seq": s, "at": self.rows[s].get("created_at"),
                          "from": str(self.rows[s].get("from") or "?"),
                          "body": self.rows[s].get("body")}
                         for s in sorted(self.rows)],
        }

    def save(self, out: Path, workspace: str) -> Path:
        path = out / f"archive-{workspace}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.payload(), indent=1) + "\n")
        return path


def compare(board: dict, archive: dict) -> dict:
    """What the writer's board and an independent copy disagree about.

    **`missing` is the whole reason this file exists**: lines the archivist
    witnessed in the room and the board does not carry. Every other field is
    context for reading it.

    `extra` is the other direction -- on the board, never seen by the
    archivist -- and is usually blindness rather than invention: anything
    written before the archivist's first read, or inside a gap it declares.
    It is reported without a verdict, and `unexplained` narrows it to the
    lines its own blind spots do not account for, which is the half worth
    a person's attention.
    """
    seen = {m["seq"]: m for m in archive.get("messages", [])
            if isinstance(m.get("seq"), int)}
    wrote = {m["seq"]: m for m in board.get("messages", [])
             if isinstance(m.get("seq"), int)}
    blind = set(archive.get("gaps") or [])
    first = min(seen) if seen else None
    missing = sorted(set(seen) - set(wrote))
    extra = sorted(set(wrote) - set(seen))
    unexplained = [s for s in extra
                   if s not in blind and (first is None or s >= first)]
    return {
        "standing": archive.get("standing"),
        "witnessed": len(seen),
        "on_board": len(wrote),
        "missing": [seen[s] for s in missing],
        "extra": extra,
        "unexplained_extra": unexplained,
        # A line both hold, whose text differs, is the loudest thing here.
        "altered": [s for s in sorted(set(seen) & set(wrote))
                    if seen[s].get("body") != wrote[s].get("body")],
    }
