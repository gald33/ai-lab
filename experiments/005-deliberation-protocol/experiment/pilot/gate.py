"""The four acceptance criteria, computed rather than eyeballed.

Every number in `PREREGISTRATION.md`'s acceptance table is a constant here, and
`evaluate` returns the per-criterion verdicts whether the configuration passes
or fails. Both halves matter: the constants being in code means the band cannot
drift after the numbers are in, and the full verdict row being returned for
every configuration means the whole search gets published, not just the winner.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from .run import (AGENT_FAILURE, BUDGET_EXHAUSTED, COORDINATED,
                  HARNESS_FAILURE, TAU, TAU_CURVE, World)

#: P1 — coordination rate must land strictly inside this closed band.
BAND = (0.15, 0.60)
#: P2 — at most this fraction of coordinating worlds may agree at round <= 1.
MAX_INSTANT = 0.40
#: P3 — at most this fraction may agree in the final quintile of the budget.
MAX_LATE = 0.40
#: P4 — the interquartile range of rounds-to-coordination, in rounds.
MIN_IQR = 2.0
#: P4 — and the number of coordinating worlds the IQR is computed over. An
#: interquartile range over three worlds is not a spread.
MIN_COORDINATED = 8


def _quartiles(values: list[float]) -> tuple[float, float]:
    """Linear-interpolated Q1 and Q3.

    Spelled out rather than taken from `statistics.quantiles` so the IQR in the
    report is reproducible from this file alone, at any n, on any Python.
    """
    xs = sorted(values)
    n = len(xs)

    def q(p: float) -> float:
        if n == 1:
            return xs[0]
        pos = p * (n - 1)
        lo = int(pos)
        hi = min(lo + 1, n - 1)
        return xs[lo] + (pos - lo) * (xs[hi] - xs[lo])

    return q(0.25), q(0.75)


@dataclass
class Verdict:
    """One configuration's row in the published search."""

    key: str
    worlds: int
    harness_failures: int
    scored: int
    coordinated: int
    agent_failures: int
    budget_exhausted: int
    rate: float
    instant_share: float
    late_share: float
    iqr: float
    median_rounds: float | None
    median_error: float | None
    p1: bool
    p2: bool
    p3: bool
    p4: bool
    curve: dict[str, float]

    @property
    def accepted(self) -> bool:
        return self.p1 and self.p2 and self.p3 and self.p4

    def to_json(self) -> dict:
        out = {k: getattr(self, k) for k in
               ("key", "worlds", "harness_failures", "scored", "coordinated",
                "agent_failures", "budget_exhausted", "rate", "instant_share",
                "late_share", "iqr", "median_rounds", "median_error",
                "p1", "p2", "p3", "p4", "curve")}
        out["accepted"] = self.accepted
        return out


def evaluate(worlds: list[World], rounds: int) -> Verdict:
    if not worlds:
        raise ValueError("no worlds to evaluate")

    broken = [w for w in worlds if w.outcome == HARNESS_FAILURE]
    # Excluded from every rate, and counted. A denominator that quietly
    # includes timeouts is the survivorship trap this lab has hit twice.
    scored = [w for w in worlds if w.outcome != HARNESS_FAILURE]
    if not scored:
        raise ValueError(f"every world was a harness failure: {broken[0].note}")

    hit = [w for w in scored if w.outcome == COORDINATED]
    rounds_to = [float(w.coordinated_at) for w in hit]
    rate = len(hit) / len(scored)

    instant = sum(1 for r in rounds_to if r <= 1)
    cutoff = rounds - max(1, rounds // 5)
    late = sum(1 for r in rounds_to if r > cutoff)
    instant_share = instant / len(hit) if hit else 0.0
    late_share = late / len(hit) if hit else 0.0

    if len(rounds_to) >= 2:
        q1, q3 = _quartiles(rounds_to)
        iqr = q3 - q1
    else:
        iqr = 0.0

    errors = [w.error for w in hit if w.error is not None]
    curve = {}
    for t in TAU_CURVE:
        k = f"{t:g}"
        curve[k] = sum(
            1 for w in scored if w.coordinated_at_tau.get(k) is not None
        ) / len(scored)

    return Verdict(
        key=worlds[0].config.key,
        worlds=len(worlds),
        harness_failures=len(broken),
        scored=len(scored),
        coordinated=len(hit),
        agent_failures=sum(1 for w in scored if w.outcome == AGENT_FAILURE),
        budget_exhausted=sum(1 for w in scored if w.outcome == BUDGET_EXHAUSTED),
        rate=rate,
        instant_share=instant_share,
        late_share=late_share,
        iqr=iqr,
        median_rounds=statistics.median(rounds_to) if hit else None,
        median_error=statistics.median(errors) if errors else None,
        p1=BAND[0] <= rate <= BAND[1],
        p2=instant_share <= MAX_INSTANT,
        p3=late_share <= MAX_LATE,
        p4=iqr >= MIN_IQR and len(hit) >= MIN_COORDINATED,
        curve=curve,
    )
