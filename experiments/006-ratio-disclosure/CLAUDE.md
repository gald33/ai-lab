# 006 — Ratio disclosure · grounding

**You are working on experiment 006 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's directory is grounding here — 005 is named below
as the source of this experiment's *instrument* and of the two results that
motivate it, and that is a code and evidence dependency, not a grounding one.
Its pre-registration, its arms and its stopping rule are 005's, not this
experiment's.

## What this experiment asks

Does telling traders **what** to disclose — the two ratios that describe them —
improve coordination against a length-matched placebo?

Full question in [`README.md`](README.md), design frozen in
[`PREREGISTRATION.md`](PREREGISTRATION.md).

## What it inherits, and what it must not inherit

- **The instrument.** `run.py` drives `005-deliberation-protocol/run_v3.py`.
  That file starts sessions, runs the clock, reads the board and settles. It
  decides nothing about this experiment. Same relationship 005 has to 002's
  `barter.economy`.
- **Two results, as evidence.** 005's run 007 (an agent alone reaches its own
  autarky optimum: mean 0.972 over 104 acts) and its runs 005–006 (added text
  cost more than it returned, twice). The first is why this experiment can read
  a shortfall as a trading failure. The second is why there is a placebo cell
  and not just a treated one.
- **Not 005's stopping rule.** That rule closed *005's* line of adding text.
  This experiment exists because 005's run 007 changed what a shortfall means,
  and it carries its own stopping rule in the pre-registration.

## Local decisions

- **Three cells, always.** `r-bare`, `r-placebo`, `r-ratios`. A treated cell
  without a matched placebo cannot separate the content from the cost of being
  handed a paragraph, and that cost is measured, not hypothetical.
- **Two endpoints, always reported together.** Presence (trader-episodes with
  any production) and exchange (utility over own autarky optimum, for the
  trader-episodes that acted). Reporting one alone is how a treatment takes
  credit for an attrition swing; that happened twice in 005.
- **Exchange above 1 is the point.** Gains from trade are why anyone else is on
  the island. A treatment that leaves exchange at or below 1 has not worked,
  whatever it did to the headline.
- Stimuli are compared by **body** hash, excluding the repo-facing title and
  note. `tools/check_stimuli.py` recomputes them and checks the placebo carries
  no domain word and matches length within 5%.
- The board is the only surface. Nothing here adds a tool, a schema or a format
  for agents; the treatment says what is worth saying, never how to say it.

## Before running anything

Open a run record from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and commit it **before** the run. Gates in [`PREFLIGHT.md`](PREFLIGHT.md) need
a recorded result on the current commit. Paid cells do not run without an
explicit go, recorded in the run record with the expected spend.
