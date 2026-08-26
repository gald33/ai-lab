"""Freeze the stimuli by body hash, and check the placebo is what it claims.

Body only: the repo-facing title and note above the first `## ` heading are not
sent to any agent and must not move a hash, or an editorial note becomes a
deviation.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / "005-deliberation-protocol"))

from run_v3 import body  # noqa: E402  -- the same reader the agents get

#: Words that would make the placebo a domain hint rather than a placebo.
DOMAIN = ("good", "goods", "cost", "costs", "worth", "price", "prices", "trade",
          "trades", "exchange", "exchanges", "labour", "produce", "production",
          "capacity", "capacities", "taste", "tastes", "salt", "iron", "bread",
          "cloth", "ratio", "ratios", "holding", "holdings", "utility",
          "specialise", "specialize", "bundle", "offer", "propose")


def digest(path: Path) -> str:
    return hashlib.sha256(body(path.read_text()).encode()).hexdigest()


def main() -> int:
    stim = HERE / "stimuli"
    bad = 0
    print("HASHES")
    for path in sorted(stim.glob("*.md")):
        words = len(body(path.read_text()).split())
        print(f"  {path.name:14} body {digest(path)}  {words} words")

    ratios = body((stim / "ratios.md").read_text()).split()
    placebo = body((stim / "placebo.md").read_text()).split()
    delta = abs(len(ratios) - len(placebo)) / len(ratios)
    print(f"\nLENGTH MATCH\n  ratios {len(ratios)} words, placebo "
          f"{len(placebo)} words, delta {delta:.1%}")
    if delta > 0.05:
        print("  FAIL: placebo must match ratios within 5%")
        bad += 1
    else:
        print("  pass: within 5%")

    print("\nDOMAIN LEAKAGE -- the placebo must carry no task-domain word")
    text = " ".join(placebo).lower()
    hits = sorted({w for w in DOMAIN if f" {w} " in f" {text} "})
    if hits:
        print(f"  FAIL: placebo contains {', '.join(hits)}")
        bad += 1
    else:
        print(f"  pass: none of {len(DOMAIN)} domain words appear")

    print("\nOK" if not bad else f"\n{bad} check(s) failed")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
