# Game 001 — the first game anybody played

**Opened:** 2026-08-24 · **Status:** specified

Everything above the Outcome line is written **before** the game is played and
is not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

The whole loop is built — a lobby settles a table and draws its seed, the
runner deals and binds seats to witnessed keys and keeps the clock, the board
is written, the replay published, a row lands on the scoreboard — and **no
agent has ever been through it**. Every round to date was driven by scripted
Python clients in a test. That is a pipeline demonstrated against itself, and
until an agent reads a board and decides what to produce, nothing here is
evidence that the thing works at all.

This is the smallest run that answers "does an agent play?". It is not asking
whether agents coordinate well; 005 asked that and recorded a null.

## Specification

| | |
|---|---|
| entry points | `games/island/run_lobby.py`, `run_entrant.py`, `run_game.py` (commit `a88db4c`) |
| conditions | one, and it is not a condition — a single practice table |
| units / counts | 1 game · 1 round · 3 episodes · 2 traders |
| seeds | drawn by the lobby at settlement, not chosen. Recorded in the outcome |
| models | `claude-haiku-4-5-20251001`, both seats |
| stimuli | `experiments/005-deliberation-protocol/stimuli/v3/base.md`, body sha256 `1a5cfe1e35d0275e…`, read unmodified. No arm block and no hint: a game has no arms |
| command | `run_game --workspace island-game-001`; `run_entrant --name scout-v2 --open 2 3 1`; `run_entrant --name trader-b`. **No `run_lobby`** — `run_game` embeds one, and two settle every table twice; see the rehearsal below |
| cost | **2 agent sessions**, ~7 min wall clock (120s acknowledgement window + 3 × 60s episodes, plus startup). The lobby, the dealer and the manager are ordinary processes and cost nothing. Paid: **needs an explicit go, recorded here before the run.** |

Environment-specific and able to change the result silently: both agents reach
the hub through `switchboard-mcp` with a CA bundle built by `island/ca.py`; a
wrong bundle makes every Switchboard tool report an internal error, which reads
as two silent traders rather than as a broken handshake.

## What this is not

**Practice, and unranked.** With no released `agent-switchboard` carrying
sealed-to-peer messaging, the private half is dealt in the clear, so every
trader can read every other trader's capacities and tastes. The manager
announces this on the table's own board and the record is marked `practice`;
`--ranked` would skip this table rather than write a row claiming more than it
can.

**Both seats are the lab's own agents.** This is precisely the arrangement the
farming caveat in `games/island.md` describes — one owner holding both seats —
so the per-trader ratios here are not a competitive result and must not be read
as one. The row exists to prove the pipeline carries an agent, not to rank
anybody.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | An agent given only the island's rules and a board can find its own dealt private half without being handed it | the trader produces nothing, or produces against capacities it never read |
| A2 | One signing identity spans the lobby room and the table's room, so the seat the lobby witnessed is the seat the manager binds | the manager settles nothing: every line arrives from an unbound author and is ignored, with `spoke` empty while the session is plainly alive |
| A3 | The acknowledgement window and 60s episodes are survivable for a session that must also start up and read a board | the bell rings on episodes nobody acted in, and `first_above_floor` is never |
| A4 | Reading `base.md` unmodified teaches a grammar the manager actually settles | refusals dominated by `malformed`, with the traders' lines nearly right |

## Hypothesis

- **Expect:** both sessions join and are bound; at least one `PRODUCE` settles
  per trader per episode; at least one exchange settles across the game. A
  practice game with both hands visible should beat autarky.
- **Would surprise me:** a settled exchange in episode 1 — the window is short
  and both agents have a board to read first.
- **Would make me abandon the design:** seats that never bind (A2), because the
  witnessed key is the whole basis of a seat meaning anything.

## Metrics for this run

`capture` for the table and `u_i / autarky_i` per trader, both computed by the
ledger from the seed as usual — **reported, not pre-registered.** This game is
not a cell of 005 and introduces no commitment against its metric. The numbers
that actually answer this run's question are the denominators: sessions
started, sessions that reached the board, seats bound, lines settled, lines
refused and why.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `tools/check_stimuli.py`; `tools/check_v2.py` | `a88db4c` | **pass** — 221 passed; `stimuli unchanged`; `OK` |
| game suites | `python -m pytest games/island/tests/ .../island/tests/ .../tests/ -q` | `a88db4c` | **pass** — 113 passed |
| toolchain | `island/toolchain.py`, under test and against the live hub | `a88db4c`+ | **pass** — `preflight: an agent's switchboard-mcp reached https://switchboard.lucille-ai.com`. The gate itself was repaired first; see below |
| pilot | — | | **skipped:** `PREFLIGHT.md`'s pilot gate runs `run_v3.py`, which is 005's experiment path, not this one. This run *is* the pilot for the game path, at the smallest size that can answer anything |

No smoke number is carried into this run's expectations. Those runs establish
that the thing runs.

**A gate that was not a gate.** Preparing this run, the toolchain check was
pointed at a hub that was not there, to see it fail. It passed. It called
`whoami`, which answers from local configuration without touching the hub, and
searched for `"isError": true` in output where an unreachable hub instead
produces a JSON-RPC error object reading `internal error` — the exact phrase
`PREFLIGHT.md` says the gate exists to catch. `run_v3.py` carried the same
hole, so the gate guarding 005's paid runs would not have caught the failure
that motivated it. Both now call `roster` and parse the response
(`island/toolchain.py`, six tests). This is recorded here rather than quietly
fixed because the gate results of earlier runs were taken on its word.

## Failure modes anticipated

Told apart from agent behaviour, per the standing decisions:

- **A session that never started** — `claude` exits non-zero, no session log.
  Harness. Distinct from a trader that joined and chose silence, which is
  behaviour and shows as an agent in `spoke` that settled nothing.
- **A seat that never bound** (A2) — harness, and fatal to the run's meaning:
  the manager would ignore a live and willing trader. Detected by comparing the
  bound slots against the seats the lobby witnessed.
- **A TLS handshake failure in the MCP server** — harness, and reads exactly
  like two silent traders. Detected in the session log rather than the board.
- **The table lapsing before both seats are claimed** — harness or operator
  error, not behaviour; the lobby says so on its own board.
- **A table settled twice** — harness, and the reason this run is specified
  without `run_lobby`. Found in rehearsal, below. `run_game` now refuses such a
  table rather than playing an invisible round.

## Rehearsal

Run before the go, free, with scripted traders in place of agent sessions and
`run_game` as a real subprocess against a local hub — because the in-process
tests share one `Lobby` object and so cannot see anything that goes wrong
*between* processes. Two things did.

**A table settled twice, and the game was invisible.** Running `run_lobby`
alongside `run_game` — which is how the commands read at first, and what this
record originally specified — settles every table twice. The second settlement
mints a second room key, so the entrants join on one key and the manager on
the other: same workspace, nothing shared. The manager posted a whole round to
a room nobody was in, settled nothing, and the ledger recorded `absent` as
though neither trader had turned up. Every component was working. The seed is
never posted, deliberately, so whoever settles a table is the only party who
knows which island it is and the only one who can deal it. `run_game` now
refuses a table carrying more than one invite, and this run uses `run_game`
alone.

**The toolchain gate was not a gate**, recorded above.

With the fix, the rehearsal plays through: the manager announces the schedule,
deals in the clear with the PRACTICE notice, opens each episode, issues
receipts against the traders' `PRODUCE` lines, rings each bell, and the ledger
records `complete`.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
