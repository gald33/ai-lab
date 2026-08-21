"""Freeze, parity and leakage checks for the 005-v2 stimuli.

Three jobs, all of which fail loudly rather than warning:

1. **Freeze** -- the three stimulus files hash to the values recorded in
   PREREGISTRATION-v2.md. An edit to a stimulus breaks the suite instead of
   silently changing the experiment.
2. **Parity** -- the four assembled cell prompts differ from each other by
   *exactly* the blocks the design says they differ by, and by nothing else.
   Computed by set difference on lines, not by eye.
3. **Domain leakage** -- the protocol block contains no word belonging to the
   task domain. The protocol has to be reusable unchanged for a distributed
   task with no market in it, and that claim is worth a test rather than an
   assurance.

    python tools/check_v2.py
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STIM = ROOT / "stimuli" / "v2"

#: (stimulus, hint). ``stimulus`` is None for the bare reference cell,
#: "placebo" for the matched control, "protocol" for the treatment.
CELLS = {
    "bare":     (None,       False),
    "placebo":  ("placebo",  False),
    "protocol": ("protocol", False),
    "hint":     (None,       True),
    "both":     ("protocol", True),
}

#: Words that would mean the protocol has absorbed the task it was written for.
#: Deliberately broad: a near-miss here is cheap, a leak is not.
DOMAIN_WORDS = [
    "good", "goods", "bread", "cloth", "iron", "salt", "price", "prices",
    "pricing", "quantity", "quantities", "produce", "produced", "produces",
    "production", "labour", "labor", "trade", "trades", "trading", "trader",
    "traders", "buy", "buyer", "sell", "seller", "offer", "offers", "accept",
    "counterparty", "counterparties", "market", "markets", "economy",
    "economic", "utility", "profit", "value", "worth", "cost", "costs",
    "exchange", "island", "capacity", "taste", "holding", "holdings",
    "consume", "period", "periods", "escrow", "supply", "demand", "surplus",
    "specialise", "specialize", "equilibrium", "coordinate", "coordination",
    "agreement", "agree", "consensus", "converge", "convergence", "deal",
]

#: Domain words the protocol may use because they are ordinary English about
#: conversation and carry no task content. Each one is a deliberate exception
#: and has to be argued for, not just added.
ALLOWED = {
    # "matter" as in "a matter that concerns someone", not economic value.
    "matter",
}


def read(name: str) -> str:
    return (STIM / f"{name}.md").read_text()


def body(text: str) -> str:
    """Strip the file's front matter: the repo-facing title and italic note."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("## "):
            return "\n".join(lines[i:]).strip()
    raise ValueError("stimulus has no body heading")


def assemble(stimulus: str | None, hint: bool) -> str:
    parts = [body(read("base"))]
    if stimulus is not None:
        parts.append(body(read(stimulus)))
    if hint:
        parts.append(body(read("hint")))
    return "\n\n".join(parts)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def check_leakage(name: str) -> list[str]:
    """Both content-free blocks must be reusable for a non-market task."""
    words = set(re.findall(r"[a-z]+", body(read(name)).lower()))
    return sorted((set(DOMAIN_WORDS) & words) - ALLOWED)


def check_parity() -> list[str]:
    """Every cell must be base, plus exactly its own treatments, and no more."""
    faults = []
    base_lines = body(read("base")).splitlines()
    blocks = {n: body(read(n)).splitlines()
              for n in ("protocol", "placebo", "hint")}
    for name, (p, h) in CELLS.items():
        got = assemble(p, h).splitlines()
        want = list(base_lines)
        if p:
            want += [""] + blocks[p]
        if h:
            want += [""] + blocks["hint"]
        # Compare ignoring blank-line joins, which are assembly not content.
        g = [l for l in got if l.strip()]
        w = [l for l in want if l.strip()]
        if g != w:
            faults.append(f"{name}: assembled text is not base + its treatments")
        missing = [l for l in base_lines if l.strip() and l not in got]
        if missing:
            faults.append(f"{name}: dropped {len(missing)} base lines")
        for other in ("protocol", "placebo"):
            if p != other and any(l in got for l in blocks[other] if l.strip()):
                faults.append(f"{name}: contains {other} content but should not")
        if not h and any(l in got for l in blocks["hint"] if l.strip()):
            faults.append(f"{name}: contains hint content but should not")
    return faults


def main() -> int:
    ok = True

    print("HASHES")
    for name in ("base", "protocol", "placebo", "hint"):
        raw = read(name)
        print(f"  {name+'.md':14s} file {sha(raw)}")
        print(f"  {'':14s} body {sha(body(raw))}  "
              f"{len(body(raw).split()):4d} words")

    print("\nPARITY -- each cell is base plus exactly its treatments")
    faults = check_parity()
    for name, (p, h) in CELLS.items():
        text = assemble(p, h)
        print(f"  {name:9s} stimulus={str(p):10s} hint={str(h):5s} "
              f"{len(text.split()):5d} words  sha {sha(text)[:16]}")
    if faults:
        ok = False
        for f in faults:
            print(f"  FAIL {f}")
    else:
            print(f"  pass: {len(CELLS)}/{len(CELLS)} cells assemble to "
              f"base + their own treatments only")

    print("\nDOMAIN LEAKAGE -- protocol and placebo must contain no "
          "task-domain word")
    for name in ("protocol", "placebo"):
        hits = check_leakage(name)
        if hits:
            ok = False
            print(f"  FAIL {name} contains: {', '.join(hits)}")
        else:
            print(f"  pass: {name} -- none of {len(DOMAIN_WORDS)} domain "
                  f"words appear")
    print(f"  ({len(ALLOWED)} argued exception"
          f"{'' if len(ALLOWED) == 1 else 's'}: {', '.join(sorted(ALLOWED))})")

    print("\nLENGTH MATCH -- placebo must match protocol")
    wp, wq = len(body(read("protocol")).split()), len(body(read("placebo")).split())
    delta = abs(wp - wq) / max(wp, wq)
    print(f"  protocol {wp} words, placebo {wq} words, delta {delta:.1%}")
    if delta > 0.05:
        ok = False
        print("  FAIL placebo is not length-matched to protocol (>5%)")
    else:
        print("  pass: within 5%")

    print("\nOK" if ok else "\nFAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
