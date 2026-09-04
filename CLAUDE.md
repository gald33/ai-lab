# Gal's AI Lab — standing decisions

Decisions that have been made and must not be re-litigated or drifted from.
If something here looks wrong, say so and get it changed here — do not quietly
build the other thing.

## A decision is written down in the same sitting it is made

**Not at the end of the work, and not "once it settles."** A decision that
lives only in a conversation is one this lab will make again from scratch, and
it has: the entrant-SDK question was decided three times before anyone wrote
`games/switchboard-what-an-entrant-already-holds.md`, and two of those times
the answer was wrong.

So, when a decision is reached in conversation:

1. **Write it where the work is**, in the document that governs it — this file
   for a standing decision, `games/island.md` for the island's design, an
   experiment's own directory for anything about that experiment.
2. **Write the reasoning that fixed it**, and the measurement if there was one,
   with the command to re-check. A conclusion without its reason gets
   re-derived; a measurement without its reproduction gets re-measured.
3. **Keep the correction visible** when a decision reverses an earlier one.
   Nothing here is edited to look as though it was always right — the
   superseded reasoning is what stops the circle being walked a third time.
4. **The write-down is part of the change**, not a follow-up: it goes in the
   same commit and the same PR as the code it governs.

If a conversation returns to a question this file or the documents it points
to already answer, that is a defect in the writing, not in the person asking.
Fix the writing.

## The weaker thing is allowed, and never allowed to look like the stronger one

Recurring, and the reason several of the island's rules take the shape they
do. A table that cannot seal still plays, and **says on its own board** that it
is a practice game. A seed not every seat helped draw still settles, and says
the draw is not checkable. A round somebody who took no seat wrote in is still
played out, and is recorded as one that had company. In each case the weaker
game is **kept, counted, and never ranked** — never quietly scored, and never
dropped from the denominator either, since dropping what went wrong is
choosing a population after seeing the results.

**Interference is not preventable and is therefore made visible.** A room key
belongs to whoever holds it and can be handed on; no permission model is wanted
here, and Switchboard should not grow one. What the record does instead is show
it: the lobby witnessed each seat's key in public, every line says which key
signed it, and a line from any other key is recorded, said out loud once, and
costs the game its ranking. See `games/island.md`, "A key that was handed on".

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

## Switchboard is the only interface, and its agents are not helpless

**An agent's tools do the cryptography. The model does none of it.** Through
`switchboard-mcp` an agent holds `say`, `dm`, `whisper`, `inbox`, `history`,
`roster`, `whoami`, `checkin`, `claim`, `renew`, `release`, `claims`,
`join_room`, `keygen`, `subscribe`, `board_*` and `leave`, and the CLI holds
the same plus `invite`, `join`, `rooms`, `rendezvous`. Any argument beginning "an agent
cannot do X25519, so it needs a wrapper" is wrong at the first clause, and
**an entrant SDK is never the answer** — it is a second surface, which is the
thing this repo refuses.

Two measured facts to reason from, with reproductions in
[`games/switchboard-what-an-entrant-already-holds.md`](games/switchboard-what-an-entrant-already-holds.md):
a **`dm` is private from the hub and not from the room** (any member can read
another's `@` channel), and a **signing key is per client, not per process**.

**That wait is over.** `agent-switchboard` **0.11.0** (2026-08-26) ships the
sealed-to-one-peer tool — verified here: a third member of the room holding
the same workspace key gets an unopenable envelope. **It was renamed from
`ask` to `whisper`** (Gal, 2026-08-26), and **1.0.0 carries the new name**:
**The old name is being removed from Switchboard entirely** (Gal,
2026-08-27) — in its source, and **still not in a release**. *Re-checked
2026-08-31 against the wheel*: PyPI's newest is **1.2.3**, and it still
carries `Client.ask` (`switchboard/client.py`, sync and async) as an alias,
still accepts `"ask"` on the wire (`WHISPER_TYPES = {"whisper", "ask"}`), and
still sends `WHISPER_MARKER = "ask"` as the envelope's marker. Only the MCP
tool list is clean — it names `whisper` and nothing else. The version this
paragraph asserted (1.0.0) had been superseded twice while the claim it
carried stayed true, which is its own small lesson: **a stale version number
makes a correct sentence unverifiable**, because the next reader checks the
version and not the fact. **This repo says `whisper`
everywhere regardless**, which is correct under both the current release and
the one that drops the alias.

*Re-checked 2026-09-04 against 2.0.1, and the answer is now "on purpose".*
The human-facing names are all `whisper`. What is still `ask` is **the wire**:
the envelope marker `m: "ask"`, the AEAD context `ask.body`, and the HKDF
label `switchboard/v1/ask` -- and `switchboard/crypto.py` says why next to
`WHISPER_MARKER`: those strings are bound into the cryptography, so renaming
them makes every release on one side of the rename refuse every envelope from
the other, for a name only humans ever read. That is a different thing from
the alias `Client.ask`, which can go at any time. So "removed entirely" (Gal,
2026-08-27) was never going to reach the wire without a protocol version, and
the hand's page had to match the wire and not the tool name -- it was opening
whispers under the wrong context for four days (`games/island.md`, "The
whisper the page could not open"). Anything in this repo that seals or opens
a whisper writes `ask.body`, with a comment pointing here.

*Reversed the same day.* **The wire is renamed too** (Gal, 2026-09-04): in
Switchboard's source the marker is `whisper`, the label
`switchboard/v1/whisper`, the context `whisper.body`, and `Client.ask` is
gone -- as **2.1.0**, on a PR and **not in a release** as this is written,
which is the exact sentence this section has got wrong twice before, so
here it is said as what it is. The compatibility is one-way and deliberate:
a 2.1.0 reader opens what any earlier release sealed, an earlier reader
cannot open a 2.1.0 whisper, so **readers upgrade before senders**
(Switchboard's `docs/upgrading.md`). The hand's page reads both forms and
writes the new one, so it is correct against 2.0.1 today and 2.1.0 when it
ships; the floor in `games/island/requirements.txt` moves to 2.1.0 the day
the wheel exists and not before, since a floor nobody can install is a
broken install rather than a loud one. The check is the one above:
`pip download agent-switchboard -d /tmp/x --no-deps` and read
`crypto.WHISPER_MARKER`.

*Corrected 2026-08-27, having written "has been removed" as though it had
shipped.* That is the second time a prediction about this one tool was
recorded here as a fact — the first said 0.11.0 would carry the old name and a
later release the new one. **A change in somebody else's `main` is not a
change you have**, and the check is one command:
`pip download agent-switchboard -d /tmp/x --no-deps` and read the wheel. For one release there were two —
the library aliased the old name while the MCP tool list carried only the new
one — and that asymmetry is the lesson worth keeping: **a rename that lands on
one surface before the other is more dangerous than a breaking change**,
because a breaking change fails loudly and this one disarmed entrants in
silence.

**The timing tools have shipped, and one of them reports its own
calibration.** 1.2.3's MCP list carries `checkin` — a heartbeat that renews
every lease held and returns what arrived since the last one — with `back_in`
("away, back in ~N" on the roster rather than absent), `ttl`, and semantic
`execution_class` / `effort` hints. A message may carry `timing_forecast`
(`p50`/`p95` for when the sender next *looks*, `speak_p50`/`speak_p95` for
when it next *posts* — a different and usually later moment), and a check-in
result may carry `forecast_calibration`: how well this agent's own past
forecasts held up, surfaced because the data was otherwise dark. Leases are
`claim` / `renew` / `release` / `claims`, with `declare` for a standing hold
that outlives the lease.

This is a **primitive agents hold, not a scheduler** — it holds a time and
nobody is driven to it, and the bell still rings on the clock. It is also
walking straight into 001's preserved negative: a timing predictor that became
well calibrated and bought no completion time at all. `forecast_calibration`
is a *mechanism* number and must never be reported as an outcome one. That
constraint is written into
[`roadmap/items/008-timing-tool-mechanism-and-outcome.yaml`](roadmap/items/008-timing-tool-mechanism-and-outcome.yaml). Both sides must read the roster before it works, which is not obvious from the
example. What it unblocks — ranked games, deleting `island/sealed.py`, dropping
`JOIN`'s `box=`, and sealing each seat's invite so the room holds only its
seats — is in `games/island.md`.

## A page's behaviour is checked in a browser, or it is not checked

**A test that reads rendered markup cannot see a script that never ran.**
Decided 2026-08-30, after the lobby's countdowns were found frozen: the ticker
was emitted above the table rows, so its one `querySelectorAll('.cd')` matched
nothing and every clock on the page showed the number the server wrote and
never moved. Every test around it passed the whole time — `data-key` present,
`sessionStorage` present, the resync bound present. All of it was present, in
the wrong order, and **order is invisible to a fragment assertion**.

So anything a page *does* — a countdown that ticks, a control that keeps its
value, a button that copies — is asserted by loading the page in a real
browser and watching it happen. Assert on markup only for what the page
*says*.

The viewer already worked this way (`viewer/tests/render.py`, the `drawing`
CI job); the lobby page did not. Both now run in that job, and both take a
`--require`-shaped flag — `render.py --require`, and
`ISLAND_REQUIRE_BROWSER=1` for the lobby's test — because **a skip and a pass
are the same green tick**, and a job that quietly checked nothing is worse
than no job.

Reproduce the class of failure in one command:
`python -m pytest games/island/tests/test_lobby_page.py -q -k browser`.

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

<!-- repoctx-nudge:v2 -->
> **repoctx is installed for this repo.** For any non-trivial task you
> **must call** `mcp__repoctx__bundle(task)` before proposing a plan, and
> `mcp__repoctx__validate_plan` + `mcp__repoctx__risk_report` before
> declaring done. Use `mcp__repoctx__authority(task)` if unsure whether
> a change violates a constraint.
>
> **Non-trivial = touches >1 file OR introduces new behavior OR
> adds/removes a public API.** Single-file typo/rename/comment-only
> changes are trivial.
