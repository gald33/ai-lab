#!/usr/bin/env python3
"""Read a calibration record and print the curve.

The tables in the writeup come from here rather than from a re-run, so they can
be checked against the stored record without spending the islands again.

    python analysis/curve.py results/tier3_calibration_wide.json

**Survival is the primary readout, not efficiency.** Efficiency is a median over
the islands where nobody was ruined, and in this sweep that set shrinks to
nothing well before the perturbation stops mattering — so the efficiency line
stays high while the islands are being destroyed underneath it. Reading it alone
would say a convention wrong by half costs 12% when it actually costs the
island. Every efficiency figure is printed with the count it was computed from
and is meaningless without it.
"""

from __future__ import annotations

import json
import math
import statistics
import sys


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """A binomial interval that behaves at 0/n and n/n, where the normal
    approximation returns a zero-width interval and invites overreading."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def curve(records: list[dict], direction: str, adherence: float) -> list[dict]:
    rows = []
    deltas = sorted({r["delta"] for r in records})
    for delta in deltas:
        g = [r for r in records
             if r["direction"] == direction
             and r["adherence"] == adherence
             and r["delta"] == delta]
        if not g:
            continue
        surv = [r for r in g if r["efficiency"] is not None]
        lo, hi = wilson(len(surv), len(g))
        rows.append({
            "delta": delta,
            "error": statistics.median(r["error"] for r in g),
            "survived": len(surv),
            "islands": len(g),
            "survival_lo": lo,
            "survival_hi": hi,
            "efficiency": (statistics.median(r["efficiency"] for r in surv)
                           if surv else None),
        })
    return rows


def render(rows: list[dict], title: str) -> str:
    out = [f"### {title}", "",
           "| δ | realised error | survived | 95% interval | efficiency (of survivors) |",
           "|---|---|---|---|---|"]
    for r in rows:
        eff = "—" if r["efficiency"] is None else f"{r['efficiency']:.3f}"
        out.append(
            f"| {r['delta']} | {r['error']:.3f} | {r['survived']}/{r['islands']} | "
            f"{r['survival_lo']:.2f}–{r['survival_hi']:.2f} | {eff} |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[1]) as fh:
        data = json.load(fh)
    recs = data["records"]
    brackets = data["brackets"]
    print(f"autarky floor {statistics.median(b['autarky'] for b in brackets):.3f}, "
          f"exchange ceiling {statistics.median(b['ceiling'] for b in brackets):.3f}, "
          f"{len(recs)} island-runs\n")

    for adherence in sorted({r["adherence"] for r in recs}, reverse=True):
        for direction in sorted({r["direction"] for r in recs}):
            rows = curve(recs, direction, adherence)
            if rows:
                print(render(rows, f"{direction}, adherence {adherence}"), "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
