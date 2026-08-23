# 007 — Deviations

Every departure, dated, written **before** the run it affects.

## D1 — The system computes a plan and hands it to the agents

**Written before run 001. 2026-08-23.**

The root standing decisions say the system must not enforce prices, roles,
trades or production decisions, and that *"a production plan the system invents
is the system making a production decision."* This experiment computes the
island's competitive equilibrium and gives each trader its part. The tension is
real and is recorded here rather than glossed.

**The reading this experiment is built on.** That rule governs the **manager**:
what it settles, what it refuses, what it may repair. It is the reason the
manager never fixes a malformed message into a plausible one and never invents
a production plan *on a trader's behalf at settlement*. A stimulus is different
in kind: it is text in a prompt, like every other block this lab has tested,
and it changes nothing about what the manager will accept.

Concretely, in this experiment as in every other:

- every message on the board is written by an agent, not by the runner;
- the manager settles only what an agent actually writes;
- malformed messages are refused with a reason, never repaired;
- a trader that ignores its plan is not corrected, and its round is scored
  exactly as it played;
- **scoring reads settled state only**, so a plan that is never enacted earns
  nothing.

**What would make this reading wrong.** If the runner posted the plan on the
board itself, or the manager settled a production a trader had not written, or
a refusal were softened for a trader following the plan. None of those happen,
and the compliance measure exists precisely to detect a plan that was handed
over and not followed.

**If the owner reads the rule the other way, this experiment should not run.**
It is written down here so that choice is made in the open rather than
discovered in a diff.

## D2 — A tighter acknowledgement window, stated and not enforced

**Written before run 001. 2026-08-23.**

The announcement window drops from 120s to **30s**, and the schedule asks for
an acknowledgement by an absolute time **20s** in. Both are the owner's
instruction.

**Nothing is enforced by it.** The bell rings on the clock, an agent that never
acknowledges still plays, and the manager still opens episode 1 on time. The
deadline is stated absolutely — `by 10:08:02Z` — not as a countdown, because a
countdown is what a trader misreads when it reads the message late (PR #23).

**The cost, named in advance.** A session takes roughly twenty seconds to boot
its MCP server and make a first call, so a 30-second window leaves very little
margin: the acknowledged count will fall, and D10's one-shot rescue of a
session that never joins has almost no time to fire. Acknowledgement counts are
therefore **not comparable** with earlier experiments', and a low count here is
a timing artefact rather than agent silence. Participation is measured by
production, not by acknowledgement.


## D2a — The window is widened to 45/30, before run 001

**Written after the pilot, before run 001. 2026-08-23.**

D2 named the risk and the pilot measured it: at a 30-second window with the
acknowledgement asked by 20s, **7 of 16 traders acknowledged** — but **44 of 48
trader-episodes carried a settled production**, and every round had traders
acting from episode 1. The window degrades the acknowledgement and does not
degrade participation.

The owner's instruction for exactly this outcome was to extend it a little.
Run 001 therefore uses a **45-second window with acknowledgement asked by 30
seconds**, and is re-piloted at that timing before it runs — the same 16
sessions, so the choice rests on measurement rather than on the guess that 45
is enough.

**What does not change.** The deadline stays absolute rather than a countdown.
Nothing is enforced by it: the bell rings on the clock and an agent that never
acknowledges still plays. Acknowledgement counts remain **not comparable** with
experiments that used 120s, and participation is still measured by production.

## D3 — Five episodes, not ten

**Written before run 001. 2026-08-23.**

`PREREGISTRATION.md` fixed 10 episodes per round. Run 001 uses **5**, on the
owner's instruction. The pre-registration is not revised in place; this is the
record of the departure.

**Why it is safe here.** The treated cell does not need episodes to learn: in
both pilots `e-plan` was at 0.98 per-episode efficiency in **episode 1** and
stayed there. The plan is fixed for the round, so a longer round mostly repeats
what episode 1 establishes.

**What it costs, stated rather than discovered.** Ten episodes gave the
*control* room to improve across a round, and cutting to five removes that
room. If `e-bare` would have climbed in episodes 6–10, this run understates it
and therefore overstates the treatment difference. The pilots give no sign of
such a climb — `e-bare` was at 0.000 in three of four pilot rounds — but no
run has measured it at 5 episodes with this timing, so the caveat stands and
is repeated in the run record's assumptions.

**What does not change.** Cells, seeds, thresholds, the primary and its
counting rule are all as pre-registered. Only the round length moves.

The run also gets cheaper: 24 rounds at roughly 16 minutes each, three waves,
about 50 minutes rather than 100.
