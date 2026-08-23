# 006 — Deviations

Every departure from the pre-registration or from a run record, dated, and
written **before** the run it affects wherever that is possible. When it is
not — as with D1 below — the record says so plainly rather than presenting a
mid-run addition as a plan.

## D1 — A roster poller added while run 001 was in flight

**Written 2026-08-23, during run 001's second wave, before any of its numbers
were computed.**

Agents set a `task` string with Switchboard's `checkin` tool. It is
workspace-scoped and every other agent in the workspace can read it with
`roster`. It is therefore a channel between agents that the manager never reads
and that no run in this lab has ever measured: every `talk` figure ever
reported, including this experiment's, counts messages on the settled channel
only.

The owner noticed the task strings in a viewer during run 001 and asked what
they were. A read-only poller (`tools/roster_poll.py`) was started immediately.
It writes nothing to any hub, sends nothing to any agent, and appends each new
`(agent, task)` it sees.

**Coverage is uneven and that is not repairable.** It started after wave one
(`r-bare`, `r-placebo`) had finished and its agents had deregistered, so those
ten rounds have **no** roster capture. The five `r-ratios` rounds are captured
from their first minute. So the roster figure can say what the treated cell did
and **cannot** compare it against the controls. It is reported as a one-cell
observation, never as a between-cell contrast.

**What it does not change.** No stimulus, no cell, no threshold, no endpoint.
The pre-registered primary and co-primary are untouched, and the manipulation
check's channel half is symmetric across all three cells.

## D2 — The tool grant is narrower than Switchboard's surface

**Written 2026-08-23, after run 001's cells had all been launched. It describes
a standing property of the instrument, not a change to it.**

Agents reach the hub through the native `switchboard-mcp` server, which exposes
15 tools. The runner launches each session with `--allowedTools` naming 7 of
them: `checkin`, `say`, `history`, `inbox`, `dm`, `roster`, `whoami`, plus
`Bash(sleep:*)`.

The restriction binds — verified directly by asking a session to call
`board_set`, which returned *"Claude requested permissions to use
mcp__switchboard__board_set, but you haven't granted it yet."* So `board_set`,
`board_get`, `board_list`, `claim`, `release`, `claims`, `keygen` and `help`
are present in the server and unusable by any agent, in this run and in every
run of experiment 005.

**Two consequences, both recorded rather than fixed mid-run.**

1. `dm` **is** granted, and a direct message is invisible to the manager and to
   every analysis. An observer cannot read another agent's inbox, so it cannot
   be reconstructed after the fact. Every "no trader said anything" claim in
   this lab is a claim about the **channel**, and is stated that way here.
2. The keyed board — the one surface that would make a disclosure claim
   checkable without text-matching — is switched off. A cell that posts ratios
   to a named key would need the grant widened, which is an instrument change
   and would be pre-registered as one.

Nothing was changed during run 001. The grant is identical across its three
cells, so it cannot explain any difference between them.
