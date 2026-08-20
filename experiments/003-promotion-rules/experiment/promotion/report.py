"""Aggregation across replications. Medians and spread, never a bare mean.

Regret distributions here are skewed — a rule that entrenches on a bad leader
in one replication and converges in the next has a mean that describes neither
— so every table reports the median and the interquartile range.
"""

from __future__ import annotations

import statistics
from typing import Any, Iterable

from .run import Record


def quartiles(values: list[float]) -> tuple[float, float, float]:
    """Median, and the values a quarter of the way in from each end."""
    if not values:
        return (0.0, 0.0, 0.0)
    s = sorted(values)
    n = len(s)
    return (s[n // 4], statistics.median(s), s[min(n - 1, (3 * n) // 4)])


def summarise(records: Iterable[Record]) -> dict[str, Any]:
    """One row: how a rule did across its replications, in one mode."""
    rs = list(records)
    if not rs:
        return {}
    regrets = [r.regret for r in rs]
    lo, mid, hi = quartiles(regrets)
    correct = [r for r in rs if r.final_correct]
    firsts = [r.first_correct_step for r in rs if r.first_correct_step is not None]
    return {
        "rule": rs[0].rule,
        "mode": rs[0].mode,
        "runs": len(rs),
        "regret_median": round(mid, 3),
        "regret_iqr": [round(lo, 3), round(hi, 3)],
        "correct": len(correct),
        "correct_rate": round(len(correct) / len(rs), 3),
        "first_correct_median": statistics.median(firsts) if firsts else None,
        "promotions_median": statistics.median([len(r.promotions) for r in rs]),
        "would_have_median": statistics.median([len(r.would_have) for r in rs]),
        "entrenched_median": statistics.median([r.entrenched_steps for r in rs]),
        "starved_median": round(statistics.median([r.starved_share for r in rs]), 4),
        "reversals_median": statistics.median([r.reversals for r in rs]),
        "explore": rs[0].explore,
    }


def table(rows: list[dict[str, Any]]) -> str:
    """The comparison, as markdown. Entrenchment is printed next to exploration
    share on purpose: measured in stream position it is partly a restatement of
    how little a rule explores, and reporting it alone would overstate it."""
    head = ("| rule | regret (median) | IQR | correct | first correct | "
            "promotions | entrenched | best's share while not leading | explore |")
    sep = "|---|---|---|---|---|---|---|---|---|"
    lines = [head, sep]
    for r in rows:
        first = r["first_correct_median"]
        lines.append(
            f"| `{r['rule']}` | {r['regret_median']} | "
            f"{r['regret_iqr'][0]}–{r['regret_iqr'][1]} | "
            f"{r['correct']}/{r['runs']} | {first if first is not None else '—'} | "
            f"{r['promotions_median']:g} | {r['entrenched_median']:g} | "
            f"{r['starved_median']} | {r['explore']} |")
    return "\n".join(lines)
