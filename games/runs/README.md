# Game runs

One record per game whose result is meant to be kept, numbered `NNN-slug.md`,
created from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and committed **before** the game is played. Specification, assumptions and
hypothesis are written before and not edited after; only the Outcome section is
filled in later.

**Separate from `experiments/005-deliberation-protocol/runs/` on purpose.**
Those records answer 005's question, which has a recorded null and is not being
revisited. A game runs on the same island and much of the same code, but it is
not an experimental cell: nothing here is pre-registered against 005's metric,
and a row on the scoreboard is not evidence about the deliberation protocol.
Numbering them in the same sequence would invite exactly that misreading.

What carries over unchanged is the process, because it is the part that stops a
result meaning less than it appears to: the record is committed first, the
preflight gates are recorded with the commit they ran on, denominators are
printed, harness failures are classified apart from agent behaviour, and a paid
run does not start without an explicit go written down here.
