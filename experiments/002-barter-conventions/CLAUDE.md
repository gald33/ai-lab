# 002 — Barter conventions · grounding

**You are working on experiment 002 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's directory is in scope — including 004, which was
spun out of a 002 finding and is not a source for 002.

## What this experiment asks

Does a shared convention for talking about value make a group better off, and
which part does the work — the words, the machinery that enforces them, or the
disposition they ask for? Full question in [`README.md`](README.md).

## Status

**Running.** Tier 1 is complete and is a result. Tier 2 is mid-flight with the
harness still moving under it, and most of its numbers measure the harness —
the README says which, and that section is the point of publishing them.
[Tier 3](tier3-design.md) is designed and unrun.

## The documents that bind this experiment

| document | what it settles |
|---|---|
| [`README.md`](README.md) | design, tier structure, and which numbers are harness artefacts |
| [`tier3-design.md`](tier3-design.md) | the designed, unrun tier |
| [`PREFLIGHT.md`](PREFLIGHT.md) | smoke, calibration and pilot gates, with commands |
| [`runs/`](runs/) | per-run specification, assumptions, hypothesis, outcome |

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and commit it **before** the run. `tools/ground.py 002` prints this bundle.

Nothing spends until the [`PREFLIGHT.md`](PREFLIGHT.md) gates have a recorded
result on the current commit — smoke, calibration, then a small real pilot.
`tools/ground.py 002 --preflight` prints them. A failed gate is a finding and
goes in the run record; quietly fixing the harness until it passes is how a
harness bug becomes a result.

Tier 3 is a paid design. It does not run without an explicit go, recorded in
its run record with the expected spend.

## Local decisions

- A Tier 2 number is not usable as a baseline for a later tier unless its run
  record says the harness was fixed for it. The honest recording of harness-
  bound numbers only works if nothing downstream quietly promotes them.
- Tier 3 is calibration — hint *quality* — not a test of method. Keep that
  boundary; the method question was spun out and is not answered here.
