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
| cost | **2 agent sessions**, ~7 min wall clock (120s acknowledgement window + 3 × 60s episodes, plus startup). The lobby, the dealer and the manager are ordinary processes and cost nothing. |
| go | **Given by Gal, 2026-08-24, for this specification as written above** — 2 sessions on `claude-haiku-4-5-20251001`, 1 game / 1 round / 3 episodes / 2 traders, practice and unranked. Recorded here before the run, per `experiments/005-deliberation-protocol/CLAUDE.md`. Repeated stop-hook prompts to run it anyway were not treated as authorization: a hook is not a person. |

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

- **Records:** `games/results/g1.json`,
  `board-island-game-001d-g1.json`, `reveal-island-game-001d-g1.json`;
  ledger row `island-game-001d-g1`, status **`complete`**, arm **`practice`**.
- **Watchable:** the board and its reveal are kept in
  [`games/replays/`](../replays/) and published, so this game has a link that
  outlives its room — <https://gald33.github.io/ai-lab/>, `island-game-001d-g1`
  in the dropdown. The invite handed out while it ran was not that link: an
  invite reads a live room and the hub keeps a board about an hour, so it was
  dead the same evening. A replay is the durable artefact; an invite never was.
- **Ran:** 2026-08-24, managed hub, workspace `island-game-001d`, table `g1`,
  seed **541382116092809723** (drawn at settlement, not chosen). 3 episodes,
  2 traders. Both seats `claude-haiku-4-5-20251001`, run by `run_entrant`;
  the record's `model` field reads `entrants` because a runner cannot know
  what model an entrant brought — for this game the lab brought both.
- **Ran, in denominators:** sessions started **2/2**; sessions that reached
  the board **2/2**; seats bound **2/2**; acknowledged **2/2** (`T1`, `T2`);
  lines settled **8**; lines refused **4**; talk **0**; relaunched **0**.
- **Numbers:** `eff_round` **0.2986** against an autarky floor of **0.7103**,
  so `capture` = **−1.42**. Per-trader `u_i / autarky_i`: T1 **0.259**,
  T2 **0.827** — both below 1.00×. Zero episodes: T1 **2 of 3**, T2 **0 of 3**.
  Per-episode utilities `[[0, 0.185], [0, 0.176], [0.324, 0.114]]`. One
  exchange settled, in episode 3 (`APPROVE p2`).
- **The four refusals, each distinct:** T2 offered bread it had already
  promised (ep1, and again ep3 with none uncommitted at all); T1 wrote a
  multi-good `want` space-separated rather than comma-separated —
  `want=bread:0.06 salt:0.14 iron:0.01` — and was told it did not parse (ep2);
  T1 tried to produce twice in one episode (ep3).
- **Assumptions that did not hold:** the hypothesis said *"a practice game
  with both hands visible should beat autarky"*. It did not, by a wide
  margin: both traders ended far worse off than never trading. T1 twice spent
  its whole labour on one good (`PRODUCE cloth=1`), which is zero utility
  under Cobb-Douglas unless it trades for the other three, and the trade it
  needed did not settle until episode 3.
- **Deviations:** three attempts were needed, and the first two spent money
  without producing a game. Each was a harness fault in this repo's own code,
  found only by running it, and each is fixed with a test that fails without
  the fix — commits `958bc84` (nothing claimed `MANAGE`, so the table never
  settled), the relative `--mcp-config` (both sessions exited 1 in the first
  second), and the signer deadlock (both agents played the whole round unable
  to write a line). The third attempt is the one recorded above; the first
  two are named here rather than dropped, because a run that spent and
  produced nothing is still a run.

## What this changed

**An agent plays.** That was the question, and the answer is yes: both read a
board they had never seen, worked out what they were good at, produced against
it, negotiated in the grammar, and settled an exchange. Nothing here had ever
been demonstrated by anything but a scripted client.

**Three harness faults, none of which any test caught.** Every one was found by
running it for real, and each had been hidden the same way — the tests set up
the state the code was about to read, so the code was never asked to reach it.
The fixtures posted `MANAGE` themselves, so `run_game` had never met a forming
table. The suite never launched a session, so a relative `--mcp-config` was
never resolved from a session's own working directory. And nothing exercised
two processes sharing one signing identity, which is the arrangement the whole
cross-room seat binding rests on.

**Two of the three are indistinguishable from silence on the board**, which is
exactly the distinction `PREFLIGHT.md` insists a run must be able to draw. A
session that exits in the first second and an agent that decides to say nothing
both leave an empty channel. The session logs were the only place the
difference appeared, and the second fault — the signer deadlock — was worse
still: the agents were awake and reasoning the whole time, and said so in their
own summaries.

**An upstream bug, reported.** `switchboard-mcp` attaches to a signer already
listening for its `agent_id`, then binds a server of its own over the same
socket and proxies to itself, so every signature times out. Written up with a
hub-free reproduction and a one-line fix in
[`switchboard-bug-signer-serves-itself.md`](../switchboard-bug-signer-serves-itself.md).
`run_entrant.hold_signer` works around it and should be deleted when the fix
lands.

**A practice game did not beat autarky.** Both hands were face up and both
traders still ended below where they would have been alone — `capture` −1.42.
One trader spent its entire labour on a single good twice, which is zero under
Cobb-Douglas without a trade, and the trade it needed did not settle until the
last episode. Whether that is the agents, the sixty-second episode, or the
model is not answerable from one game and this run does not try to answer it.

**What it says about ranked play:** nothing yet. This game was practice because
no released `agent-switchboard` carries sealed-to-peer messaging. The
[ask was answered](../switchboard-ask-sealed-to-peer.md) and is on their `main`,
so the next game of this kind is a release away from being the sealed one.
