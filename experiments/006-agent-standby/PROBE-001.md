# 006 — probe 001: does a wake fire, and who held the clock?

*Written before the probe runs, per `CLAUDE.md`: what is being measured and
what each outcome would mean, fixed in advance.*

## Why a probe and not a run

`006-standby-alarm-has-never-rung` has two attempts on record, both from a
Claude Code cloud session, and both silent — 8.3h and 17.4h late. The item's
own reading is that the observation is solid and the explanation was not: a
container suspended at the end of a turn and a VM still up with nothing
running-and-idle predict the same silence, and two runs cannot separate them.

This probe cannot separate them either. What it can do, for nothing, is
establish whether **any** wake fires in this substrate at all, and — because
it arms two of them with different holders — which kind.

**It is n = 1 per arm.** It is a probe, not a finding, and the arc's question
is not settled by it either way.

## The substrate

A Claude Code **remote/cloud** session (`claude.ai/code`), ephemeral container,
this repository checked out. The same family of substrate as both recorded
attempts, which is what makes it worth one more look rather than a new one.

## The two arms, and what separates them

| arm | who holds the clock | how it is armed | what firing would show |
|---|---|---|---|
| **A — in-container** | the agent's own runtime: a process inside the container | a background shell timer that exits after ~3 minutes | the container outlives the turn *and* something inside it can still reach the agent — the standby design's actual claim |
| **B — server trigger** | the runtime, on the agent's behalf | a scheduled message due in ~3 minutes, bound to this session | only that a **server** kept the time and resumed the session; the agent held nothing |

Arm B is armed as a **control**, not as a candidate answer. The item rules out
adopting a server-side trigger and calling the question answered, and this does
not do that: B exists so that a silent A is legible. If neither fires, the
session simply ended; if B fires and A does not, the clock is the runtime's and
not the agent's, which is the arc's hypothesis stated as an observation.

## Pre-registered readings

- **A fires** → this substrate can host an agent-held alarm. Record the
  latency, then the open question becomes cost (what a quiet wake buys), not
  possibility.
- **A silent, B fires** → the agent cannot hold its own clock here, and
  availability in this substrate is lent by the runtime. One substrate, n = 1,
  and it does not generalise beyond "here".
- **Neither fires** → the probe measured nothing about clocks. It is reported
  as a failed probe, in the denominator, not dropped.
- **A fires late** → recorded with its lateness. "Fired" means the wake
  arrived, not that it arrived on time.

## Denominators

Arms armed: 2. Arms fired: to be filled in after. This file is not edited to
say something else afterwards; the outcome is appended below it.

## Outcome

*Appended 2026-08-25, after both arms resolved. The pre-registered text above
is unedited.*

**Arms armed: 2. Arms fired: 2.**

| arm | armed | due | fired | late |
|---|---|---|---|---|
| A — in-container timer | 19:42:21Z | 19:45:21Z | 19:45:21Z | 0s |
| B — server trigger | 19:43:0xZ | 19:46:00Z | 19:46:59Z | 59s |

B's lateness is its documented granularity: the scheduler polls once a minute,
so a minute is the resolution, not a delay to explain.

### What this does not show, which is most of it

The pre-registered reading for "A fires" was *this substrate can host an
agent-held alarm*. **It is not claimable from this probe**, and the reason is
in the timing rather than in the result:

- **A's wake landed in a session that was already awake.** A GitHub webhook
  and a message from the operator both arrived in the minutes around it, so
  the container was demonstrably alive and the agent mid-turn when the timer
  exited. The timer fired on time and its completion reached the agent, and
  neither of those facts required the timer to *wake* anything.
- **B did resume an idle session**, after roughly 90 seconds of dormancy. That
  is the one wake here that crossed from quiet to awake, and it is the arm
  held by a server — the arm this item rules out as an answer.
- **90 seconds is not the regime the failures are in.** The two recorded
  absences were 5 minutes and 6 hours, and the item's own reading is that a
  reclaimed container and a live VM with nothing running-and-idle predict the
  same silence. Nothing at this timescale separates them either.

So probe 001 establishes that **a wake of some kind fires in this substrate**,
which two prior attempts had not, and it establishes nothing about who can
hold the clock. That is a smaller result than the arms were designed to
produce, and it is the one the timing supports.

### What probe 002 has to change

One thing: **dormancy**. The arms are fine; they were read too early.

- Arm A must be armed and then left alone across a gap long enough that the
  container's survival is in question — the item quotes no reclamation
  duration, so the first useful ladder is something like 5, 20 and 60 minutes,
  each with **no** other traffic into the session, which is the hard part
  here: a subscribed pull request wakes it on its own.
- The discriminator to record is not "did it fire" but **"was the session
  quiet when it did"**. Probe 001 could not answer that for arm A, and any
  future probe that cannot should say so in the same place rather than
  reporting a fire.
- Arm B stays as the control, unchanged, for the same reason it was there:
  if a long-gap A is silent and a long-gap B fires, the substrate is lending
  the clock rather than the agent holding it.

Nothing here retires the mechanism and nothing here validates it. The arc's
question is where it was, with one thing removed from it: silence is no longer
the only thing this substrate has ever produced.
