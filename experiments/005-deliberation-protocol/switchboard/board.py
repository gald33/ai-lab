"""The board. An append-only file that anyone may read and anyone may append to.

This is the whole interface. There is no other channel, no tool API, and no
harness method an agent can call. An agent acts by writing a line here; the
manager acts by reading lines and writing its own.

Concurrency is handled the way an append-only log always handles it: each write
is a single `write()` of one newline-terminated line opened in append mode, and
POSIX guarantees that is atomic for writes under PIPE_BUF. Readers track their
own byte offset, so a reader never blocks a writer and two readers never
interfere.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Line:
    seq: int
    at: float
    author: str
    text: str

    def render(self, origin: float) -> str:
        return f"[{self.at - origin:6.1f}s] {self.author}: {self.text}"


class Board:
    """One board, one file. Shared by every agent and the manager."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def say(self, author: str, text: str) -> None:
        """Append one line. Atomic; never rewrites what is already there."""
        text = " ".join(str(text).split())
        if not text:
            return
        record = json.dumps({"at": time.time(), "author": author, "text": text},
                            ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(record + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def read(self) -> list[Line]:
        """Every line on the board, oldest first."""
        out: list[Line] = []
        if not self.path.exists():
            return out
        with open(self.path, encoding="utf-8") as fh:
            for seq, raw in enumerate(fh):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    d = json.loads(raw)
                except json.JSONDecodeError:
                    continue  # a torn write is skipped, never repaired
                out.append(Line(seq=seq, at=d["at"], author=d["author"],
                                text=d["text"]))
        return out

    def since(self, seq: int) -> list[Line]:
        return [l for l in self.read() if l.seq >= seq]
