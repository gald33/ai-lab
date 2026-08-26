"""Check a finished game against its own published record.

    python -m games.island.verify games/replays/board-<workspace>.json

`games/island.md`, "Who runs the manager", claims four things about a board
are checkable against the seed that drew the island -- production, exchange,
timing and refusal. This is that claim as a program, so that it is either true
or visibly not, rather than an argument in a document.

It reads two files, both published when the game ended: the **board** (every
line, in order, with the manager's reading of each signature) and the
**reveal** sidecar beside it (the island, the seed, the seat keys, and how the
seed was drawn). It recomputes what it can and prints denominators for
everything, because a checker that says "ok" without saying how many things it
looked at is worth nothing.

**What it cannot check, and says so rather than implying otherwise:**

- **signatures are not re-verifiable from a saved board.** The Switchboard
  client verifies at read time and hands its caller a verdict, so the bytes
  never reach the file. What the board carries is the manager's reading, and
  what this checks is that a seat's lines carry the key the *lobby* witnessed
  for that seat, in public, before the round. That catches a board attributing
  a line to the wrong seat; it does not catch a manager that forged the
  verdicts, and nothing in one party's copy could.
- **omission.** A line the manager never wrote down is invisible here. That is
  condition 3 in `island.md` -- a second, independent archive -- and it is not
  built.
- **a sealed round's production**, which is the point of sealing: the shares
  are not on the board, so the arithmetic cannot be redone. A sealed game is
  checked on everything else and this is counted, not skipped quietly.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PRODUCE = re.compile(r"^PRODUCE\s+(.*)$", re.IGNORECASE)
RECEIPT = re.compile(r"^@(T\d+) produced (\{.*?\}); ([0-9.]+) labour unspent")
OFFER = re.compile(r"^(p\d+): (T\d+) offers (\{.*?\}) to (T\d+) for (\{.*?\})")
SETTLED = re.compile(r"^(p\d+) settled: (T\d+) and (T\d+) exchanged "
                     r"(\{.*?\}) for (\{.*?\})")
BELL = re.compile(r"^bell — episode (\d+) closed")
SHARE = re.compile(r"^([a-z]+)=([0-9.]+)$")


@dataclass
class Report:
    """What was checked, what failed, and how many of each."""

    checks: dict[str, list[int]] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def ok(self, kind: str) -> None:
        row = self.checks.setdefault(kind, [0, 0])
        row[0] += 1
        row[1] += 1

    def bad(self, kind: str, why: str) -> None:
        row = self.checks.setdefault(kind, [0, 0])
        row[1] += 1
        self.failures.append(f"{kind}: {why}")

    def skip(self, why: str) -> None:
        self.skipped.append(why)

    @property
    def passed(self) -> bool:
        return not self.failures


def _vector(blob: str) -> dict[str, float]:
    """A manager's `{'bread': 0.61}` as numbers. Literal, never eval'd."""
    return {str(k): float(v) for k, v in ast.literal_eval(blob).items()}


def check_draw(reveal: dict, report: Report) -> None:
    """Was this island drawn, or chosen?

    The lobby committed to its nonce before any seat could join, every seat's
    nonce went on the lobby's board as it sat down, and the lobby's own is
    published here. So the seed is recomputable by anybody, from lines that
    existed before the draw -- which is what a manager choosing its island
    could not survive.
    """
    draw = reveal.get("draw")
    if not draw:
        report.skip("the draw: this replay predates commit-reveal, so nothing "
                    "here shows whether its seed was drawn or chosen")
        return
    if draw.get("method") != "commit-reveal":
        report.skip(f"the draw: settled as {draw.get('method')!r} -- not every "
                    f"seat brought a nonce, so the seed was the lobby's alone")
        return

    nonce, commit = draw.get("nonce", ""), draw.get("commit", "")
    if hashlib.sha256(nonce.encode()).hexdigest() != commit:
        report.bad("draw", "the published nonce does not hash to the "
                           "commitment the table opened with")
        return
    report.ok("draw")

    material = "|".join([nonce] + sorted(draw.get("seat_nonces", {}).values()))
    seed = int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big") >> 1
    if seed != reveal.get("seed"):
        report.bad("draw", f"the nonces make seed {seed}, the record says "
                           f"{reveal.get('seed')}")
    else:
        report.ok("draw")


def check_authorship(board: dict, reveal: dict, report: Report) -> None:
    """Does every seat's line carry the key the lobby witnessed for that seat?"""
    keys = reveal.get("seat_keys") or {}
    if not keys:
        report.skip("authorship: this replay carries no witnessed seat keys")
        return
    for msg in board["messages"]:
        author = msg.get("author", "")
        if author not in keys:
            continue
        block = msg.get("signature") or {}
        if not block:
            report.bad("authorship", f"seq {msg.get('seq')} by {author} has no "
                                     f"reading of its signature at all")
        elif block.get("status") != "verified":
            report.bad("authorship", f"seq {msg.get('seq')} by {author} was "
                                     f"{block.get('status')}, not verified")
        elif block.get("key") != keys[author]:
            report.bad("authorship", f"seq {msg.get('seq')} says {author} but "
                                     f"carries another seat's key")
        else:
            report.ok("authorship")


def check_production(board: dict, reveal: dict, report: Report) -> None:
    """Every receipt must equal `share × capacity`, and capacity comes from
    the seed. A manager that credited a friend cannot survive this."""
    traders = {seat: half for seat, half in (reveal.get("traders") or {}).items()
               if isinstance(half, dict) and "capacity" in half}
    if not traders:
        report.skip("production: the reveal names no capacities")
        return
    pending: dict[str, dict[str, float]] = {}
    sealed = 0
    for msg in board["messages"]:
        body, author = msg.get("body", ""), msg.get("author", "")
        if body.startswith("SEALED") and author in traders:
            sealed += 1
            continue
        plan = PRODUCE.match(body)
        if plan and author in traders:
            shares = {}
            for part in plan.group(1).split():
                bit = SHARE.match(part)
                if bit:
                    shares[bit.group(1)] = float(bit.group(2))
            pending[author] = shares
            continue
        receipt = RECEIPT.match(body)
        if not receipt:
            continue
        seat, got, unspent = receipt.group(1), _vector(receipt.group(2)), float(receipt.group(3))
        shares = pending.pop(seat, None)
        if shares is None:
            if sealed:
                continue
            report.bad("production", f"a receipt for {seat} with no PRODUCE "
                                     f"before it (seq {msg.get('seq')})")
            continue
        capacity = traders[seat]["capacity"]
        for good, quantity in got.items():
            want = shares.get(good, 0.0) * capacity[good]
            if abs(want - quantity) > 5e-4:
                report.bad("production",
                           f"{seat} {good}: receipt says {quantity}, "
                           f"share × capacity is {round(want, 6)}")
            else:
                report.ok("production")
        left = round(1.0 - sum(shares.values()), 4)
        if abs(left - unspent) > 1e-3:
            report.bad("production", f"{seat} labour unspent {unspent}, "
                                     f"shares leave {left}")
        else:
            report.ok("production")
    if sealed:
        report.skip(f"production: {sealed} sealed PRODUCE line(s) -- the shares "
                    f"are not on the board, which is what sealing is for, so "
                    f"that arithmetic cannot be redone by anybody")


def check_exchange(board: dict, report: Report) -> None:
    """A settlement must move exactly what its offer named, both ways."""
    offers: dict[str, tuple[str, dict, str, dict]] = {}
    for msg in board["messages"]:
        body = msg.get("body", "")
        offer = OFFER.match(body)
        if offer:
            offers[offer.group(1)] = (offer.group(2), _vector(offer.group(3)),
                                      offer.group(4), _vector(offer.group(5)))
            continue
        done = SETTLED.match(body)
        if not done:
            continue
        pid, a, b = done.group(1), done.group(2), done.group(3)
        gave, got = _vector(done.group(4)), _vector(done.group(5))
        if pid not in offers:
            report.bad("exchange", f"{pid} settled with no offer before it")
            continue
        from_, want_give, to_, want_get = offers.pop(pid)
        if (a, b) != (from_, to_):
            report.bad("exchange", f"{pid} was {from_}->{to_}, settled {a}->{b}")
        elif gave != want_give or got != want_get:
            report.bad("exchange", f"{pid} offered {want_give} for {want_get}, "
                                   f"settled {gave} for {got}")
        else:
            report.ok("exchange")


def check_timing(board: dict, reveal: dict, report: Report) -> None:
    """Bells in order, one per episode, each after the last."""
    bells = [(int(BELL.match(m["body"]).group(1)), m.get("at"))
             for m in board["messages"] if BELL.match(m.get("body", ""))]
    if not bells:
        report.skip("timing: no bells on this board")
        return
    for (n, at), (m, later) in zip(bells, bells[1:]):
        if m != n + 1:
            report.bad("timing", f"episode {m} closed after episode {n}")
        elif at and later and later < at:
            report.bad("timing", f"episode {m}'s bell is stamped before {n}'s")
        else:
            report.ok("timing")
    trajectory = (reveal.get("round") or {}).get("trajectory") or []
    episodes = len(trajectory) or None
    if episodes and len(bells) != episodes:
        report.bad("timing", f"{len(bells)} bells for {episodes} episodes")
    else:
        report.ok("timing")


def verify(board_path: Path, reveal_path: Path | None = None) -> Report:
    board = json.loads(board_path.read_text())
    if reveal_path is None:
        reveal_path = board_path.parent / f"reveal-{board['workspace']}.json"
    report = Report()
    if not reveal_path.exists():
        report.bad("reveal", f"no reveal sidecar at {reveal_path} -- a game "
                             f"publishes one when it ends, and without it the "
                             f"island is unknown and nothing can be recomputed")
        return report
    reveal = json.loads(reveal_path.read_text())
    check_draw(reveal, report)
    check_authorship(board, reveal, report)
    check_production(board, reveal, report)
    check_exchange(board, report)
    check_timing(board, reveal, report)
    return report


def main(argv: list[str]) -> int:
    if not 2 <= len(argv) <= 3:
        print(__doc__)
        return 2
    report = verify(Path(argv[1]), Path(argv[2]) if len(argv) == 3 else None)
    print(f"{argv[1]}\n")
    for kind, (good, total) in sorted(report.checks.items()):
        print(f"  {kind:12} {good}/{total}")
    for why in report.skipped:
        print(f"  not checked -- {why}")
    for why in report.failures:
        print(f"  FAILED {why}")
    print()
    print("this board holds together" if report.passed
          else f"{len(report.failures)} check(s) failed")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
