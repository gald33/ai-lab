# 001 — Switchboard coordination · grounding

**You are working on experiment 001 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's directory is in scope.

## What this experiment asks

When several agents work the same shared resources, does coordination improve
because the agents reason harder about each other, or because good coordination
primitives leave them less to reason about? Full question in
[`README.md`](README.md).

## Status

**Run, not published.** The data is uncleaned, the analysis unwritten, and
nothing in the README is a result. Treat every number here as provisional until
a run record says otherwise.

## The documents that bind this experiment

| document | what it settles |
|---|---|
| [`README.md`](README.md) | design; explicitly claims no outcome yet |
| [`PREFLIGHT.md`](PREFLIGHT.md) | the gates before a run — none declarable yet, and why |
| [`runs/`](runs/) | per-run specification, assumptions, hypothesis, outcome |

There is no pre-registration for the runs already taken. That is the first
thing a next run must fix: anything further here is pre-registered in its run
record before it executes, and the existing data is reported as
pre-pre-registration or not at all.

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and commit it **before** the run. `tools/ground.py 001` prints this bundle.

Nothing spends until the [`PREFLIGHT.md`](PREFLIGHT.md) gates have a recorded
result on the current commit — smoke, calibration, then a small real pilot.
`tools/ground.py 001 --preflight` prints them. A failed gate is a finding and
goes in the run record; quietly fixing the harness until it passes is how a
harness bug becomes a result.

## Local decisions

- The switchboard is the shared surface, per the root standing decisions. If a
  design here starts needing a second channel, stop.
- Cleaning the existing data is a separate piece of work from running more of
  it. Do not fold the two into one commit — the first is a claim about records
  that already exist, the second produces new ones.
