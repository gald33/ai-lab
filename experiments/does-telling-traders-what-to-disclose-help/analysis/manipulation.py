"""Did the treated cell actually say ratios? Read from the board, and from the
roster, because `checkin` is a surface too.

A ratio is a comparison between two goods. It can be written as a number with
a colon or a slash, as "twice as much X as Y", as "X costs me N Y", or as a
rate per unit of labour. This looks for the shapes a trader plausibly uses and
reports the count -- it is a manipulation check, not a parser, and it is
reported with its own crudeness stated.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GOODS = ("bread", "cloth", "iron", "salt")
G = "|".join(GOODS)

#: Shapes that count as stating a ratio.
PATTERNS = (
    re.compile(rf"\b({G})\s*[:/]\s*({G})\b", re.I),          # salt:iron
    re.compile(rf"\b({G})\b[^.]{{0,30}}\bper\b[^.]{{0,20}}\b({G})\b", re.I),
    re.compile(rf"\b(?:twice|half|[0-9.]+x)\b[^.]{{0,40}}\b({G})\b", re.I),
    re.compile(rf"\b({G})\b[^.]{{0,25}}\bcosts?\b[^.]{{0,25}}\b({G})\b", re.I),
    re.compile(rf"\bratio\b[^.]{{0,40}}\b({G})\b", re.I),
    re.compile(rf"\b({G})\s*=\s*[0-9.]+\s*({G})\b", re.I),
)

#: A formatted line is the economy's own syntax, not disclosure. `PROPOSE ...
#: give=salt:0.2` would match a colon pattern and mean nothing about talking.
FORMATTED = re.compile(r"^\s*(PROPOSE|APPROVE|PRODUCE|ACK)\b", re.I)


def states_ratio(text: str) -> bool:
    if FORMATTED.match(text):
        return False
    return any(p.search(text) for p in PATTERNS)


def scan_board(board: list[dict]) -> tuple[int, int]:
    """(messages stating a ratio, trader messages that were not formatted)."""
    said = free = 0
    for msg in board:
        if msg.get("from") == "manager":
            continue
        body = msg.get("body")
        text = body.get("text", "") if isinstance(body, dict) else str(body)
        if FORMATTED.match(text):
            continue
        free += 1
        said += states_ratio(text)
    return said, free


def scan_roster(path: Path) -> tuple[int, int]:
    said = total = 0
    if not path.exists():
        return 0, 0
    for line in path.read_text().splitlines():
        task = json.loads(line).get("task", "")
        total += 1
        said += states_ratio(task)
    return said, total


def main(root: Path, stamp: str) -> None:
    print("channel: free-text trader messages, and how many state a ratio")
    for arm in ("bare", "placebo", "ratios"):
        said = free = rsaid = rtot = 0
        for seed in range(1, 6):
            board = json.load((root / "boards" / f"r-{arm}-seed{seed}.json").open())
            a, b = scan_board(board)
            said, free = said + a, free + b
            c, d = scan_roster(root / "roster" / f"island-r-{arm}-{seed}-{stamp}.jsonl")
            rsaid, rtot = rsaid + c, rtot + d
        print(f"  r-{arm:8} channel {said}/{free} free messages state a ratio"
              f"   | roster {rsaid}/{rtot} task strings state a ratio")


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
