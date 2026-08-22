# 005 — The deliberation protocol · grounding

**You are working on experiment 005 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's directory is in scope — 002 is named in the
README as the contrast this experiment is *not*, which is exactly why its
directory must not be read as grounding here.

## What this experiment asks

Does a content-free deliberation protocol — method, not content — improve
coordination, holding the hint fixed? Full question in [`README.md`](README.md).

## Status

**Run.** The pilot passed and all cells ran with agents. The headline is a
**null**: no detectable coordination gain over a matched placebo. v3 is the
native-Switchboard rebuild — no harness, no scheduler.

## The documents that bind this experiment

| document | what it settles |
|---|---|
| [`README.md`](README.md) | design and what is claimed |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | v1 frozen metric, threshold, acceptance band, stimuli hashes |
| [`PREREGISTRATION-v2.md`](PREREGISTRATION-v2.md) | v2 frozen cells, primary contrast, pilot acceptance |
| [`DESIGN-v2.md`](DESIGN-v2.md), [`AMENDMENT-v2.md`](AMENDMENT-v2.md) | v2 design and its amendment |
| [`DEVIATIONS.md`](DEVIATIONS.md) | every departure, dated, written before the run it affects |
| [`stimuli/`](stimuli/) | frozen by hash; `tools/` recomputes and fails on drift |
| [`PREFLIGHT.md`](PREFLIGHT.md) | smoke, calibration and pilot gates, with commands |
| [`runs/`](runs/) | per-run specification, assumptions, hypothesis, outcome |

A pre-registration is never revised in place. A revision is a new document at a
new version, and the old one stays in history.

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and commit it **before** the run. `tools/ground.py 005` prints this bundle.

Nothing spends until the [`PREFLIGHT.md`](PREFLIGHT.md) gates have a recorded
result on the current commit — smoke, calibration, then a small real pilot.
`tools/ground.py 005 --preflight` prints them. A failed gate is a finding and
goes in the run record; quietly fixing the harness until it passes is how a
harness bug becomes a result.

Paid cells do not run without an explicit go, recorded in the run record with
the expected spend.

## Local decisions

- v3 is native Switchboard: the board is the only surface, and the manager
  reads and settles, it never drives. Every agent is its own long-lived
  session. If v3 code starts to need a turn, a wave, or a scheduler, stop —
  that has been built twice already.
- Stimuli are compared by **body** hash, excluding the repo-facing title and
  note that are not sent to agents. Never re-freeze a hash to make a check
  pass; a moved stimulus is a deviation.
- `run_v3.py` imports `barter.economy` from 002's tree. A **code** dependency
  is not grounding: the module is used, 002's documents are not read. If that
  import needs to change, change it here and record why.
- A silent agent has said nothing. That is different from a session that could
  not start, and every run record states how the two are told apart in its
  numbers.
