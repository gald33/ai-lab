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

## Before you spend: three gates

A paid run is the worst place to discover that the harness is broken, that the
instrument reads nothing, or that the design produces no variation. Three
checks stand between a specified run and a spent one. Each answers a different
question, and passing one says nothing about the others.

**They run in order, and each is free.** If a gate cannot be run for free, that
is itself worth knowing before the go.

### 1. Smoke — does the basic flow work at all?

The cheapest end-to-end path: the entry point starts, the pieces wire together,
records come out in the shape the analysis expects. Plus the experiment's own
offline tests and any freeze check over stimuli or pre-registered hashes.

Smoke is run at absurdly small parameters — two islands, twenty steps, two
worlds — because it is about **plumbing, not values**.

> **A smoke run's numbers are not evidence of anything.** At two islands and ten
> rounds, an economy can report every agent ruined and every score unscored, and
> that is a fact about the parameters, not about the arm. The only thing a smoke
> run establishes is that it produced output at all. Never carry a smoke number
> forward, and never let one talk you out of a design.

### 2. Calibration — does the instrument read?

The gate that gets skipped, and the expensive one to skip. It asks whether the
measurement can move at all: does the metric separate two conditions that are
known in advance to differ, and does it sit off its own floor and ceiling?

An instrument pinned at its ceiling, at its floor, or flat across a
known-different pair will return a null no matter what the agents do, and that
null is unattributable — it cannot be told apart from a real one. Print the
floor and the ceiling next to every calibration number, always.

Calibration is only needed where a metric or an instrument is new or has moved.
An unchanged instrument that read fine last run does not need re-calibrating;
say so in the run record rather than leaving the gate silently unrun.

### 3. Pilot — does it run, small, for real?

The smallest run that is the *real thing*: real agents, real board, real
manager, real clock — just few of them, and short. It is the only gate that can
surface what only appears under real sessions: agents that never speak,
messages the manager will not recognise, a clock that closes the episode before
anyone has acted, sessions that fail to start.

What a pilot must report, whatever else it reports:

- **attempted / completed / failed**, printed as counts with denominators;
- **harness and timing failures classified separately from agent behaviour** —
  a silent agent has said nothing, which is not the same as a session that
  could not start, and a pilot that cannot tell those apart has not passed;
- **cost per unit**, extrapolated to the full run, so the go is given against a
  number rather than a feeling.

A pilot's *outcome* numbers are still not evidence — the point of a pilot is
that it is too small to be. It gets a run record like any other run, and its
record says so.

### What a gate result is worth

A gate result is attached to a **commit**. A pass on a commit that has since
moved is not a pass. Re-run the gates, or state in the run record which commit
each result came from and why the change since cannot have affected it.

**A failed gate is a finding, not an obstacle.** It goes in the run record —
and, when it changes what the run does, in the deviations file — before the
run proceeds. Silently fixing the harness until the gate passes, and recording
only the pass, is how a harness bug becomes a result.

### Where the gates are declared

Each experiment declares its own gates in its `PREFLIGHT.md`: the actual
commands, what each proves, roughly how long it takes, and what a failure
means for that experiment. `tools/ground.py N --preflight` prints them.

They are declared per experiment and **not shared**, for the same reason there
is no shared framework: a common gate runner would end up shaping experiments
to fit it, and would eventually be part of what is under test. `ground.py`
prints the commands; it does not run them.

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
