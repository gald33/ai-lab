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
