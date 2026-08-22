# 004 — Stock and flow · grounding

**You are working on experiment 004 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's directory is in scope.

004 exists to test a 002 finding, so its README states the inherited claim in
full. **That restatement is the source.** Do not go read 002's directory for
context — if something inherited is missing, lift it across deliberately, in
writing, with the assumptions it came under.

## What this experiment asks

002 found that a shared price reaches the Pareto frontier and ruins somebody on
half its islands. Is that a fact about the convention, or about a world where a
production commitment can never be taken back? Full question in
[`README.md`](README.md).

## Status

**Run. Results in the README.**

## The documents that bind this experiment

| document | what it settles |
|---|---|
| [`README.md`](README.md) | design, the inherited 002 claim, and the result |
| [`runs/`](runs/) | per-run specification, assumptions, hypothesis, outcome |

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and commit it **before** the run. `tools/ground.py 004` prints this bundle.

## Local decisions

- The whole experiment turns on per-period consumption being the *only*
  difference from the world 002 ran. Any run record here carries that as an
  explicit assumption, with what would show it false.
- What the result licenses is a statement about irrecoverable commitment, not
  a revision of 002's numbers. 002's records are not edited from here.
