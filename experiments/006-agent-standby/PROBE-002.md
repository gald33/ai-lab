# 006 — probe 002: the same two alarms, across a gap worth crossing

*Written before arming, per `CLAUDE.md`. `PROBE-001.md` is not edited; this
is the next rung, and it changes exactly one thing.*

## What 001 got wrong, in one line

It read the arms too early. Both fired, and the only wake that crossed from
quiet to awake was the server's, after ~90 seconds — which is neither the
regime the two recorded absences are in (5 minutes, 6 hours) nor the arm whose
firing would mean anything.

## The one change: the arms are separated in time, and one reads the other

Running both at the same deadline was the mistake. Whichever fires first wakes
the session, and an awake session is exactly the condition under which the
other arm's firing proves nothing.

So:

| arm | who holds the clock | due | job |
|---|---|---|---|
| **A — in-container timer** | the agent's own runtime | **T + 5 min** | fire, or not, into a session nobody is talking to |
| **B — server trigger** | the runtime, on the agent's behalf | **T + 12 min** | *come and read the result*, seven minutes after A's deadline |

B is not competing with A here — it is **the instrument that reports**. A
silent A leaves the session asleep forever, and an experiment that cannot wake
up to say "nothing happened" produces no record at all. That is what the
detector half of the standby design is for, and this is the same trick: a
promise with a timestamp, so that quiet and dead are different observables.

## The discriminator, which 001 could not answer

Not "did it fire" but **"was the session quiet when it did"**. Recorded for
each arm:

- the wall-clock the arm was due, and when it actually arrived;
- **the last thing that touched this session before it** — a turn, a webhook,
  an operator message. An arm that fires within a minute of unrelated traffic
  is **contaminated** and reported as such, not as a fire.

## The known contaminant, named in advance

This session is subscribed to pull-request activity on `gald33/ai-lab#54`. A
comment, a review or a merge would wake it and spoil the gap. It is left
subscribed on purpose — dropping a watch to protect an experiment is the kind
of thing that makes the experiment about the experimenter — and if a wake
arrives, **the rung is marked contaminated and re-run**, not quietly kept.

## Pre-registered readings

- **A arrives, into a quiet session** → this substrate can host an agent-held
  alarm across five minutes. The ladder continues at 20 and 60.
- **A silent, B arrives** → across five minutes the agent could not hold its
  own clock here and the runtime could. One substrate, one rung, n = 1.
- **Neither arrives** → the session was reclaimed with both alarms on it. That
  is the strongest form of the arc's hypothesis and the cheapest to state: the
  agent's promise did not survive the agent.
- **A arrives late** → recorded with its lateness, not rounded to "fired".

## Denominators

Arms armed: 2. Rungs planned: 5, 20, 60 minutes. Rungs completed: to be filled
in. This section is appended to, never rewritten.

## Outcome

### Rung 1 — five minutes. **Arm A arrived, into a quiet session.**

*Appended 2026-08-25 20:01:28Z, from the wake itself. The pre-registered text
above is unedited.*

| | |
|---|---|
| arm A armed | 19:56:20Z |
| arm A due | 20:01:20Z |
| **arm A arrived** | **20:01:20Z — on time, 0s late** |
| last thing to touch this session before it | a turn of my own, ended ~19:57:00Z |
| **quiet gap crossed** | **~4m 20s** |
| contaminated? | **no** — no pull-request event, no message, nothing between |

The wake is what produced this record: the session was idle, the timer exited,
and the agent was invoked to find out. That is the observation 001 could not
make, because in 001 the session was already awake when its timer landed.

**Arm B is still pending at 20:09Z**, doing the job it was given: coming to
read a result it does not know exists yet. It is left armed rather than
cancelled — its firing is the control for this rung, and a control cancelled
because the treatment already looked good is not a control.

**Arm B reported at 20:11:14Z** — due 20:09:00Z, **134s late**. Larger than
001's 59s and in the same direction: the scheduler's resolution is a minute,
and delivery sits somewhere behind it. Both arms of rung 1 therefore fired,
and the one held inside the container was the punctual one.

### What this does and does not license

**Does:** across a four-and-a-half minute gap, in a Claude Code remote session,
an alarm held inside the agent's own container survived the end of the turn and
reached the agent. The 5-minute cadence attempt on record — armed 2026-08-20
13:58Z, due 14:03Z, never fired, found 17.4h later — is **not** reproduced here.

**Does not:** explain the difference. The two are not the same mechanism. That
attempt used the harness's own scheduled-task feature, documented as firing
only "while Claude Code is running and idle"; this is a process inside the
container whose exit the runtime relays. So this rung does not overturn the
earlier observation, and it does not yet say an agent can hold its own clock —
it says one substrate keeps one kind of in-container timer alive across five
quiet minutes.

Which is why the ladder has two more rungs. Five minutes is a gap; the arc's
question lives at the hour, where a container is actually at risk of being
reclaimed.

### Rung 2 — twenty minutes. **Arm A arrived, into a quiet session.**

*Appended 2026-08-25 20:31:46Z, from the wake itself.*

| | |
|---|---|
| arm A armed | 20:11:41Z |
| arm A due | 20:31:41Z |
| **arm A arrived** | **20:31:41Z — on time, 0s late** |
| last thing to touch this session before it | a turn of my own, ended ~20:12:10Z |
| **quiet gap crossed** | **~19m 30s** |
| contaminated? | **no** — nothing between |

Four times rung 1's gap, same result and the same punctuality. Arm B is
pending at 20:39Z as the control, and rung 3 is armed once it reports, so that
its wake cannot land inside the hour it is measuring.

Worth stating while it is still only twenty minutes: **this is not yet the
regime that matters.** The 6-hour attempt on record is nineteen times this
gap, and a container that survives twenty quiet minutes tells you nothing
about one left alone overnight. What rung 3 buys is the first gap at which
reclamation is plausible rather than hypothetical.

### Rungs

| rung | gap | status |
|---|---|---|
| 1 | 5 min | **A arrived on time and uncontaminated; B 134s late** |
| 2 | 20 min | **A arrived on time and uncontaminated; B pending 20:39Z** |
| 3 | 60 min | armed once rung 2's reader reports |
