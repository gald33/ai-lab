# <NNN> — <name> · grounding

*Copy into a new experiment directory and fill in. This file is what an agent
working on this experiment carries; keep it short and make it point, rather
than restate. The relative links below resolve from
`experiments/<NNN>-<name>/`, not from here.*

**You are working on experiment <NNN> only.** The repo-root `CLAUDE.md` and
[`experiments/GROUNDING.md`](../GROUNDING.md) apply. No other experiment's
directory is in scope — see the scope rule in GROUNDING.

## What this experiment asks

One or two sentences. The full question lives in the README.

## Status

Where it actually is right now, in one line, and what the next unrun thing is.

## The documents that bind this experiment

| document | what it settles |
|---|---|
| [`README.md`](README.md) | design, and what is claimed |
| `PREREGISTRATION.md` | frozen metric, thresholds, stimuli hashes |
| `DEVIATIONS.md` | every departure, dated, written before the run it affects |
| [`PREFLIGHT.md`](PREFLIGHT.md) | smoke, calibration and pilot gates, with commands |
| [`runs/`](runs/) | per-run specification, assumptions, hypothesis, outcome |

Delete rows that do not exist yet rather than promising them.

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md),
fill in specification / assumptions / hypothesis, and commit it **before** the
run. `tools/ground.py <NNN>` prints this bundle and lists existing runs.

Nothing spends until the [`PREFLIGHT.md`](PREFLIGHT.md) gates have a recorded
result on the current commit. `tools/ground.py <NNN> --preflight` prints them.

## Local decisions

Things settled for this experiment that are not in the root CLAUDE.md and that
an agent would otherwise re-decide — naming, where records land, what counts
as a completed unit, what the harness may and may not do here.
