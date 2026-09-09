"""What the manager recognises when it reads the board.

Four formats, and nothing else on the board means anything to the economy. A
line that does not parse is talk, which is a legitimate and expected thing for
a line to be -- most lines will be talk.

    PRODUCE bread=0.5 iron=0.5
    PROPOSE to=T2 give=iron:0.4 want=salt:0.3
    APPROVE p3
    DECLINE p3

The manager enforces **format**: a line that is nearly one of these is not
repaired into one. It also enforces **timing**: a well-formed line that arrives
outside its window is refused with a reason. It enforces nothing else -- no
price, no role, no plan, no partner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PRODUCE, PROPOSE, APPROVE = "PRODUCE", "PROPOSE", "APPROVE"
#: The fourth (2026-08-29). An offer escrows the maker's goods for as long as
#: it is open, and the maker cannot free them -- committing is the whole point.
#: The trader it was addressed to is the only one who can say the deal is not
#: happening, so `DECLINE` is what hands those goods back before the bell.
DECLINE = "DECLINE"

_BUNDLE = re.compile(r"^([a-z]+):([0-9]*\.?[0-9]+)$")
_SHARE = re.compile(r"^([a-z]+)=([0-9]*\.?[0-9]+)$")


class Malformed(Exception):
    """Close to a formatted message, but not one. Never repaired."""


@dataclass(frozen=True)
class Produce:
    plan: dict[str, float]


@dataclass(frozen=True)
class Propose:
    to: str
    give: dict[str, float]
    want: dict[str, float]


@dataclass(frozen=True)
class Approve:
    proposal_id: str


@dataclass(frozen=True)
class Decline:
    proposal_id: str


def _bundle(raw: str, label: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        m = _BUNDLE.match(part)
        if not m:
            raise Malformed(f"{label} wants good:qty pairs, got {part!r}")
        qty = float(m.group(2))
        if qty <= 0:
            raise Malformed(f"{label} quantities must be positive, got {part!r}")
        out[m.group(1)] = out.get(m.group(1), 0.0) + qty
    if not out:
        raise Malformed(f"{label} is empty")
    return out


def parse(text: str):
    """Return a Produce/Propose/Approve/Decline, or None if this line is talk.

    Raises ``Malformed`` when a line opens with a keyword but does not parse --
    the agent tried to act and got the format wrong, which it should be told.
    """
    stripped = text.strip()
    head = stripped.split(None, 1)[0].upper() if stripped else ""
    if head not in (PRODUCE, PROPOSE, APPROVE, DECLINE):
        return None
    rest = stripped[len(head):].strip()

    if head == PRODUCE:
        plan: dict[str, float] = {}
        for part in rest.split():
            m = _SHARE.match(part)
            if not m:
                raise Malformed(f"PRODUCE wants good=share pairs, got {part!r}")
            share = float(m.group(2))
            if share < 0:
                raise Malformed("shares cannot be negative")
            plan[m.group(1)] = plan.get(m.group(1), 0.0) + share
        if not plan:
            raise Malformed("PRODUCE needs at least one good=share")
        return Produce(plan=plan)

    if head == PROPOSE:
        fields: dict[str, str] = {}
        for part in rest.split():
            if "=" not in part:
                raise Malformed(f"PROPOSE wants key=value, got {part!r}")
            key, value = part.split("=", 1)
            fields[key.lower()] = value
        missing = [k for k in ("to", "give", "want") if k not in fields]
        if missing:
            raise Malformed(f"PROPOSE is missing {', '.join(missing)}")
        return Propose(to=fields["to"], give=_bundle(fields["give"], "give"),
                       want=_bundle(fields["want"], "want"))

    if not rest or len(rest.split()) != 1:
        raise Malformed(f"{head} wants exactly one proposal id")
    pid = rest.split()[0]
    return Approve(proposal_id=pid) if head == APPROVE else Decline(proposal_id=pid)
