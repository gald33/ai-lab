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

*(appended after the probe — empty until then)*
