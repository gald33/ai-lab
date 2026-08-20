# Reports

Session reports: what was built, what was run, what the numbers support, and —
at more length than is comfortable — where each claim is weakest.

These exist because the lab's most valuable contribution, per
[CONTRIBUTING](../CONTRIBUTING.md), is being told an experiment is wrong. A
result buried in a commit message is hard to attack. A result with its claims
numbered, its evidence graded, and its soft spots named is easy to attack, which
is the point.

**Reports are not the experiment.** Each experiment's own README remains
authoritative for its design and findings. A report says what happened in one
working session, across experiments, including the parts that did not work and
the mistakes that were caught.

## Reading one as a reviewer

Every experiment report carries a **Claims** table. Each claim has a strength:

| strength | means |
|---|---|
| `solid` | replicated, effect large against its interval, mechanism inspected |
| `supported` | the data says this, but a stated assumption carries weight |
| `weak` | directionally indicated, not established; do not build on it |
| `refuted` | tested and did not hold; recorded so it is not re-run by accident |

Then a **Review targets** section: the specific things most likely to be wrong,
ranked, with what evidence would settle each. Start there.

## Index

| report | covers |
|---|---|
| [2026-08-20 — session](2026-08-20-session.md) | cross-cutting: what changed, three near-misses, review guide |
| [2026-08-20 — 002 Tier 3 calibration](2026-08-20-002-tier3-calibration.md) | manufacturing conventions of known quality; the δ curve |
| [2026-08-20 — 003 Tier 1](2026-08-20-003-promotion-rules.md) | promotion rules over strategies and protocols |
| [2026-08-20 — 004](2026-08-20-004-stock-and-flow.md) | stock vs flow; whether ruin was ever about conventions |
