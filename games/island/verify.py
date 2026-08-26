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
from datetime import datetime, timezone
from pathlib import Path

PRODUCE = re.compile(r"^PRODUCE\s+(.*)$", re.IGNORECASE)
RECEIPT = re.compile(r"^@(T\d+) produced (\{.*?\}); ([0-9.]+) labour unspent")
OFFER = re.compile(r"^(p\d+): (T\d+) offers (\{.*?\}) to (T\d+) for (\{.*?\})")
SETTLED = re.compile(r"^(p\d+) settled: (T\d+) and (T\d+) exchanged "
                     r"(\{.*?\}) for (\{.*?\})")
BELL = re.compile(r"^bell — episode (\d+) closed")
OPENED = re.compile(r"^episode (\d+) of (\d+) is open; the bell is at "
                    r"(\d{2}:\d{2}:\d{2})Z \((\d+)s\)")
OPENS_AT = re.compile(r"Episode 1 opens at (\d{2}:\d{2}:\d{2})Z")

#: How late a bell may be rung before it counts as a fault. The manager rings
#: on a polling loop, so a second or two of lateness is the loop and not a
#: choice; thirty seconds is not. **Early has no allowance at all** -- a bell
#: rung before the time the board announced is the one direction that takes
#: time away from a trader who read the schedule and believed it.
LATE_ALLOWED = 30.0
EARLY_ALLOWED = 1.0
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


def check_company(board: dict, reveal: dict, report: Report) -> None:
    """Did anybody who took no seat write in this room?

    Not a fault in the board — it is a fact about the game, and one a reader
    has to be told rather than left to infer from a name they do not
    recognise. A room key can be handed on: a seated trader can pass it to a
    confederate or run a second client of its own, and no permission model
    prevents that. What the record can do is show it, because the lobby
    witnessed which key took each seat in public and every line here says
    which key signed it.

    A board with company **fails**, and the failure is the point: it is what
    keeps such a game out of the rankings while keeping it in the ledger and
    in every denominator.
    """
    keys = reveal.get("seat_keys") or {}
    if not keys:
        report.skip("company: this replay carries no witnessed seat keys, so a "
                    "stranger's line cannot be told from a seat's")
        return
    strangers: dict[str, int] = {}
    for msg in board["messages"]:
        author = msg.get("author", "")
        if author in keys or author == "manager":
            continue
        strangers[author] = strangers.get(author, 0) + 1
    if not strangers:
        report.ok("company")
        return
    for who, lines in sorted(strangers.items()):
        report.bad("company", f"{lines} line(s) from {who}, which took no seat "
                              f"at this table -- this game was played through "
                              f"interference and is not rankable")


def check_production(board: dict, reveal: dict, report: Report) -> None:
    """Every receipt must equal `share × capacity`, and capacity comes from
    the seed. A manager that credited a friend cannot survive this."""
    traders = {seat: half for seat, half in (reveal.get("traders") or {}).items()
               if isinstance(half, dict) and "capacity" in half}
    if not traders:
        report.skip("production: the reveal names no capacities")
        return
    # A sealed round puts no plan on the board at all -- `ask` delivers it to
    # the manager's own channel. So sealing is recognised by what the manager
    # announced, not by counting markers: the marker was this repo's stopgap
    # and stopped existing when `ask` shipped.
    sealed = any(str(m.get("body", "")).startswith("SEALED round")
                 for m in board["messages"] if m.get("author") == "manager")
    pending: dict[str, dict[str, float]] = {}
    for msg in board["messages"]:
        body, author = msg.get("body", ""), msg.get("author", "")
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
        report.skip("production: this round was sealed, so no plan is on the "
                    "board and the arithmetic cannot be redone by anybody -- "
                    "which is what sealing is for. The receipts stay public "
                    "and everything else here is checked as usual")


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


def _at(stamp: str | None) -> float | None:
    """A board timestamp as seconds. Hub-written, which is the point: it is
    the one clock on the board that the manager did not choose."""
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _announced(clock: str, near: float) -> float:
    """An announced `HH:MM:SSZ` as seconds, on the day it must have meant.

    The board states times absolutely but without a date, so the date comes
    from the message the announcement sits beside, and a bell just after
    midnight is read as the next day rather than as twenty-four hours early.
    """
    day = datetime.fromtimestamp(near, tz=timezone.utc).date()
    hour, minute, second = (int(part) for part in clock.split(":"))
    stamped = datetime(day.year, day.month, day.day, hour, minute, second,
                       tzinfo=timezone.utc).timestamp()
    for shift in (0, 86400, -86400):
        if abs(stamped + shift - near) <= 43200:
            return stamped + shift
    return stamped


def check_clock(board: dict, report: Report) -> None:
    """Was each bell rung when the board said it would be?

    The fourth of the four conditions in `games/island.md`: *"the schedule is
    announced before the round and every message carries the hub's own
    timestamp, so a bell rung early for one trader and late for another is
    visible in the record."* This is that, checked.

    Two clocks, and the check is that they agree. The manager **announces** an
    absolute bell time when it opens an episode, and the hub **stamps** every
    message as it arrives -- including the bell. A manager that closed an
    episode early has a stamp before its own announcement, which no wording
    can cover.
    """
    announced: dict[int, tuple[float, int]] = {}
    schedule_at = opens_at = None
    for msg in board["messages"]:
        body, at = msg.get("body", ""), _at(msg.get("at"))
        opens = OPENS_AT.search(body)
        if opens and at is not None:
            schedule_at, opens_at = at, _announced(opens.group(1), at)
            continue
        head = OPENED.match(body)
        if head and at is not None:
            announced[int(head.group(1))] = (_announced(head.group(3), at),
                                             int(head.group(4)))
    if not announced:
        report.skip("the clock: this board announces no bell times -- an older "
                    "round, or one driven by something other than run_game")
        return

    if schedule_at is None:
        report.bad("clock", "no schedule was announced before the round")
    elif opens_at is not None and opens_at < schedule_at:
        report.bad("clock", "the schedule announced an opening already past "
                            "when it was posted")
    else:
        report.ok("clock")

    for msg in board["messages"]:
        bell = BELL.match(msg.get("body", ""))
        at = _at(msg.get("at"))
        if not bell or at is None:
            continue
        episode = int(bell.group(1))
        if episode not in announced:
            report.bad("clock", f"episode {episode} closed without its opening "
                                f"ever announcing a bell time")
            continue
        due, _seconds = announced[episode]
        drift = at - due
        if drift < -EARLY_ALLOWED:
            report.bad("clock", f"episode {episode}'s bell was rung "
                                f"{abs(round(drift, 1))}s EARLY -- the board "
                                f"said {stamp_of(due)}, the hub stamped it "
                                f"{stamp_of(at)}")
        elif drift > LATE_ALLOWED:
            report.bad("clock", f"episode {episode}'s bell was rung "
                                f"{round(drift, 1)}s late, past the "
                                f"{int(LATE_ALLOWED)}s a polling loop explains")
        else:
            report.ok("clock")


def stamp_of(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%SZ")


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
    check_company(board, reveal, report)
    check_production(board, reveal, report)
    check_exchange(board, report)
    check_timing(board, reveal, report)
    check_clock(board, report)
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
