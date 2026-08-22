# <experiment name>

A starting point for a new experiment.

These are **prompts for thinking, not mandatory fields.** Every section below is
here because forgetting it has cost someone an experiment, but that doesn't make
it universal. Drop what doesn't apply, add what's missing, reorder freely.

One rule worth keeping: **a heading kept with nothing under it is worse than no
heading.** An empty "Limitations and confounders" reads as a claim that there
aren't any. If a section has nothing to say, delete it.

Alongside this file, a new experiment directory gets:

- **`CLAUDE.md`** — from [`../CLAUDE.md`](CLAUDE.md) in this template: the
  grounding an agent working on *this* experiment carries, and no other.
- **`runs/`** — one record per run, from
  [`runs/RUN-TEMPLATE.md`](runs/RUN-TEMPLATE.md), written before the run.

[`experiments/GROUNDING.md`](../../experiments/GROUNDING.md) says why.

---

## Question

The specific thing being asked. Narrow enough that the answer changes what gets
built next.

## Motivation

What produced this question. Usually a real system doing something unexplained —
say which system and what it did.

## Hypothesis

What you expect, and — more usefully — what would have to be true for you to be
wrong. If no result could surprise you, this isn't an experiment.

## Experimental design

Conditions, task, agents, models, harness, run counts. Enough that someone could
rebuild it without asking you anything.

## Why this isolates the mechanism

The argument that this design tests what it claims to test. This is the section
that saves the most work when written *before* the runs.

## What is load-bearing

The part that, if removed, makes the result disappear. If nothing here is
load-bearing, you're measuring the harness.

## Controls

What is held fixed across conditions, and how you know it stayed fixed. Model
version, prompts, tool set, task instances, seeds, ordering.

## Metrics

Mechanism metrics and outcome metrics, listed separately. A mechanism can work
perfectly and move no outcome; that's a finding, but only if the two were
measured apart.

Note how agent self-reports are handled. An agent claiming it did something is a
claim; score against system state.

## Results

What happened. Numbers, with run counts and spread.

## Interpretation

What the numbers support — and, explicitly, what they don't. The gap between
those two is where most overclaiming lives.

## Negative results

Things that didn't work, and things that worked without mattering. Keep them.
They're the parts of the experiment least likely to be rediscovered by anyone
else.

## Limitations and confounders

Named, not gestured at. "Model non-determinism" is not a confounder; "stage 5
also shortens the critical path, so its gain isn't attributable to coordination
alone" is.

## Experimental artifacts

Where the code, raw records, and analysis live, and what's in each per-run
record.

## Reproduction

How to run it. Include the version pins and anything environment-specific that
will silently change the result.

## Follow-up questions

What this opened up. Often the most valuable output.
