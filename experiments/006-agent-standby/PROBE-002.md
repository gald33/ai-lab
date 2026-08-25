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

*(appended after the probe — empty until then)*
