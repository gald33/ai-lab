# Grounding — how a run is set up, recorded, and read back

This is the **general** layer. It applies to every experiment in this
directory and says nothing about any particular one.

Above it sits [`CLAUDE.md`](../CLAUDE.md) at the repo root: the standing
decisions, which are not re-litigated here. Below it sits each experiment's
own `CLAUDE.md`, which is the **only** experiment-specific grounding an agent
working on that experiment should be carrying.

## The rule about scope

**An agent working on one experiment reads that experiment's grounding and no
other's.**

Each experiment directory carries its own `CLAUDE.md`. Claude Code loads a
directory-scoped `CLAUDE.md` when work happens in that directory, so an agent
started against `experiments/004-stock-and-flow/` is grounded in 004 and is
not carrying 002's design decisions, 005's pre-registration, or anyone else's
frozen metric.

This is not tidiness. Grounding from another experiment is the most expensive
kind of contamination available here: it arrives as *authoritative* text, it
looks like it belongs, and it quietly imports a metric, a threshold, or a
harness assumption that was frozen for a different question. A number produced
under another experiment's assumptions is not a weak result — it is an
unattributable one.

So, concretely, for an agent running experiment N:

- **In scope, always:** repo-root `CLAUDE.md`, this file,
  `experiments/N-*/CLAUDE.md`, and everything that file points at.
- **Out of scope:** every other `experiments/*/` directory. Do not read them
  for a pattern to copy, a metric to reuse, or a harness to borrow. If you
  want something from a sibling experiment, say so and get it lifted into
  yours deliberately — with its assumptions carried across in writing.
- **Reports** (`reports/`) are readable, but they are session narrative, not
  grounding. The experiment's own documents remain authoritative.

`tools/ground.py N` prints exactly one experiment's grounding bundle and
nothing else. Use it to open a run; it is also the check that the bundle is
complete before anything is spent.

## What a run must have written down before it runs

A **run** is one execution of a configuration whose result you intend to keep.
Every run gets a record under `experiments/N-*/runs/`, created from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../templates/experiment/runs/RUN-TEMPLATE.md)
and committed **before** the run starts. Three things carry the weight:

**Specification.** What is actually being executed — code path, entry point,
conditions, seeds, models and versions, counts, stimuli by hash, and the
command. Enough that the run can be rebuilt from the record alone, months
later, without asking anyone. This is what makes a stored number re-readable
rather than merely stored.

**Assumptions.** What has to be true for the run's output to mean what you
intend it to mean. Not caveats — load-bearing beliefs: that the manager
settles what you think it settles, that the frontier is the one you think it
is, that a silent agent is a choice and not a failed session. Each written so
that it could later be found false. An assumption discovered after the fact
is a limitation; one written before is a result waiting to happen.

**Hypothesis.** What you expect, in the run's own metric, before you see it —
and what outcome would change your mind. If no result could surprise you, the
run is a demonstration, not an experiment; say that in the record and it stops
being a problem.

The record is written before, and only its **Outcome** section is written
after. The before-part is not edited once the run starts. If it turns out
wrong, that is a deviation: append it, dated, to the experiment's deviations
file — never a silent rewrite. This is the same rule as pre-registration, at
the granularity of a single run.

## What the record is for

Three readers, all of them you:

1. **Before** — writing the specification is the cheapest place to notice that
   the design does not test what it claims.
2. **During** — the record is what an agent reads back to stay grounded in
   what was decided, instead of re-deciding mid-flight.
3. **After** — a stored result is only interpretable next to the assumptions
   it was produced under. `results/` holds numbers; `runs/` holds what they
   were numbers *of*.

## Numbering

`runs/NNN-short-slug.md`, zero-padded, in the order runs were opened. A run
that was specified and then not executed keeps its number and records why —
the gap in the sequence is more misleading than the abandoned record.

## What does not go in a run record

Results prose, interpretation, and claims. Those go in the experiment README
and, for a working session, in `reports/`. A run record is the run's own
account of itself: what was intended, what was assumed, what came out.
