# 003 — Promotion rules · grounding

**You are working on experiment 003 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's directory is in scope.

## What this experiment asks

When candidate solutions compete and the winner is promoted automatically,
under what rule does the competition converge on the *good* solution rather
than the *lucky* one — and does a solution whose value depends on being shared
need a different rule from one whose value does not? Full question in
[`README.md`](README.md).

## Status

**Tier 1 complete.** The scripted tier is run and reported. Tier 2 — the same
promoter over real instincts rather than scripted ones — is neither designed
nor run.

## The documents that bind this experiment

| document | what it settles |
|---|---|
| [`README.md`](README.md) | design and the Tier 1 result |
| [`runs/`](runs/) | per-run specification, assumptions, hypothesis, outcome |

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and commit it **before** the run. `tools/ground.py 003` prints this bundle.

Tier 2 needs a design document committed before its first run record, not
assembled inside one.

## Local decisions

- Tier 1 is scripted on purpose: the promoter is under test, not the
  candidates. A Tier 2 run record must state, as an assumption, what it now
  relies on the candidates to do — that is where the tier's fragility lives.
- The two solution kinds — value-if-shared and value-regardless — are the
  contrast. A run that scores them together has measured nothing.
