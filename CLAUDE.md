# Gal's AI Lab — standing decisions

Decisions that have been made and must not be re-litigated or drifted from.
If something here looks wrong, say so and get it changed here — do not quietly
build the other thing.

## The board is the only surface

**There are no primitives other than what Switchboard provides.**

Switchboard gives agents a board. Agents write to it. That is the whole
interface, and it is the only interface.

**There is no harness for Switchboard, and no tool API for the economy.**
No `produce()`, no `offer()`, no `accept()`, no action schema dispatched by the
runner. An agent does not "call" anything.

The economy exists **only** as a **manager function** that reads the board,
recognises particular formatted messages, and settles them:

- a formatted message that declares production,
- a formatted message that proposes an exchange,
- a formatted message that approves one.

The manager is a reader of board text and a settler of state. It is not a tool
the agents hold. Anything an agent wants to do, it does by writing a message.

### What this rules out, explicitly

- A second channel for "economy actions" separate from talking. **One surface.**
- A JSON `actions` list dispatched to harness methods.
- Any call an agent makes that is not a board write.
- Describing tools to agents in their instructions as if they were an API.

### What the system may still do

Enforce **timing** (when the board is open, and for what), **format** (what a
well-formed message must look like to be recognised), and **scoring**.

It must **not** enforce prices, roles, trades, or production decisions, and it
must never repair a malformed message into a plausible one. A production plan
the system invents is the system making a production decision.

**Self-reports are non-authoritative.** Metrics come from settled state, never
from what an agent says about what it did.

## Agents run themselves. There is no scheduler.

**Every agent is its own long-lived session**, running concurrently and
continuously. An agent is not a function the runner calls.

- **No turn-taking, no rounds of play, no waves, no batching.** Never build all
  agents' prompts from one snapshot, never fire them in parallel, never block
  on all of them returning. There is no such thing as a "turn" here.
- **Each agent reads the board when it wants and writes when it wants.**
  Nobody is prompted to act.
- **Nothing waits for an agent.** An agent that says nothing has said nothing;
  the bell rings anyway and the episode closes on the clock.

**The manager is a reader, not a driver.** It watches the board, recognises
formatted messages that declare production, propose an exchange or approve one,
settles them, and keeps score. It never tells an agent to do anything and never
asks an agent for anything.

Concretely: the board is an append-only file; each agent is a long-lived
session with read and append access to it; the manager is a separate process
watching that file. The runner's whole job is to start the sessions, run the
clock, read the board, settle, and score.

### The drift to watch for

Building a loop that calls each agent in sequence or in parallel and applies
their replies **is the forbidden thing**, however natural it looks in code. It
has been built twice already. If the design starts to need a "turn", stop —
something has gone wrong.

## Timing

The schedule is **announced on the board and acknowledged before every round**,
because context resets at the round boundary: an acknowledgement carried over
from an earlier round is consent from agents who no longer remember giving it.

The manager enforces the schedule by what it will still settle after a
deadline, not by controlling when agents act.

## Vocabulary

| term | what resets at its boundary |
|---|---|
| **episode** | item stocks, labour, open proposals, episode utility |
| **round** (one seed) | agent context and history, accumulated utility |

A round is **k episodes on one island** — same tastes, same capacities, same
traders throughout. Context persists across a round's episodes and resets only
at the round boundary. That memory is the learning channel and is the reason a
round has more than one episode.

Do not call an episode a "period" or a round a "world".

**The game calls an episode a day.** Decided by Gal, 2026-08-25. It is a
presentation name and nothing else: the island's day opens, runs, and a bell
closes it, and the viewer's sun crosses the sky through it, so "day" is what a
spectator is shown. The **manager still writes "episode" on the board**, the
frozen stimulus still says episode, and `eff_episode` keeps its name — renaming
those would change what agents read and what the ledger records. So the
transcript quotes the manager's word and the metric panel names the metric;
everywhere the game speaks in its own voice it says day.

## Metrics

- **`eff_round`** — accumulated utility vector against the frontier of the
  total. **The primary.**
- **`eff_episode`** — the episode's utility vector against the one-episode
  frontier. A **coverage** measure: one agent at zero puts the vector maximally
  far from the frontier however well the others did. Never read it as welfare.

The frontier of the total is `k ×` the one-episode frontier, because Σα = 1
makes utility homogeneous of degree 1.

## Process

- Pre-register metrics and thresholds before running; freeze stimuli by hash.
- Deviations and amendments are written **before** the run they affect.
- Pair conditions on identical seeded rounds; the **round** is the unit.
- Print denominators everywhere. Never drop failed runs from a denominator.
- Classify harness/timing failures separately from agent behaviour.
- Do not spend on a paid run without an explicit go.
