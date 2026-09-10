# Run 002 — rung 0a and rung 0b

**Opened:** 2026-09-10 · **Status:** done

Everything above the Outcome line was written before the run started.

---

## Why this run

The two free rungs of the ladder, run together because neither costs anything
and rung 1 is blocked on both. `PREFLIGHT.md` gates 2 and 3.

- **Rung 0a (H0a)** — how far does the instrument move when nothing varies?
  NPC seats, pinned island seeds, same cell every replicate.
- **Rung 0b (H0c)** — does content error move the *primary endpoint* on *this*
  island? A δ sweep on scripted traders, at the game island's table shape and
  under its flow accumulation rule.

Neither can set the threshold rung 1 is scored against. Run 001 established why
for 0a: NPC policies are deterministic, so a between-replicate sd from NPCs is
zero by construction and contains none of the agent sampling variance that
dominates a model cell. **H0b, the paid replication, is not authorised and is
not run here.**

## Specification

| | |
|---|---|
| entry points | `experiment/noise.py` (0a), `experiment/calibrate.py` (0b, new) |
| conditions | 0a: one cell, nothing varied. 0b: δ × direction × adherence |
| units / counts | 0a: 8 replicates × 12 games, 4 traders, 5 goods, 4 episodes, 60s. 0b: 48 islands × 8 δ × 2 directions × 4 adherences |
| seeds | pinned; `--seed0 1` in both |
| models | **none** — NPC heuristics (0a), scripted traders (0b) |
| stimuli | none beyond the island's standing brief |
| cost | zero, both rungs |

Commands, as run:

    python experiments/how-wrong-can-a-shared-convention-be/experiment/noise.py \
      --replicates 8 --games 12 --traders 4 --goods 5 --episodes 4 --seconds 60 \
      --workers 8 \
      --json experiments/how-wrong-can-a-shared-convention-be/results/rung0-noise.json

    python experiments/how-wrong-can-a-shared-convention-be/experiment/noise.py \
      ... --vary-npc-seed --json .../rung0-noise-varied-policy.json

    python experiments/how-wrong-can-a-shared-convention-be/experiment/calibrate.py \
      --islands 48 --traders 4 --goods 5 --periods 4 \
      --json .../rung0b-curve.json

## Deviations, written before the run

**D1 — rung 0a runs its games concurrently, and that is part of what it
measures.** `PREFLIGHT.md` gate 2 budgets the serial wall clock at *roughly
seven hours* and says to give it an overnight slot **or run games
concurrently**. Concurrency is taken. `--workers` is added to `noise.py` and
every replicate × seed job goes into one pool, so replicates interleave rather
than each seeing its own clean machine.

That is not a neutral scheduling choice and is not treated as one. A game is a
wall clock — episodes are real seconds and NPC seats act on a timer — so
machine load can in principle shift when a seat reaches the board. If it does,
replicates stop coming back identical and the sd this rung reports is the
variance concurrency injects. **That is the honest floor for any real run,
because any real run is concurrent too**, and gate 2's "anything above zero here
is a defect to find" is what would then have been found. Both outcomes are
reported; neither is repaired into the other.

The replicate count is **not** cut. Gate 2 says the replicate count is the whole
measurement, and it is 8 × 12 as written.

**D2 — rung 0b gets a new runner in this experiment's tree rather than the flags
gate 3 names.** Gate 3's command is

    calibrate_experiment.py --traders 4 --goods 5 --flow --islands 48

and `--traders` and `--flow` do not exist on that runner: it takes `--agents`,
defaults to 12, and runs **stock** islands only. Worse, it reports **efficiency
medians**, which is the endpoint correction C1 in `README.md` already retired —
Tier 3's own calibration showed survivor efficiency flat across the whole δ
sweep, which is why the primary here is a count.

So gate 3 is run by `experiment/calibrate.py`, which imports the same `barter`
economy, the same `announce()` perturbation and `barter.run.run_island_flow`
(004's flow mode, which lives in 002's tree beside the stock one), and reports
the **zero-period share** — the scripted analogue of `zero_episode_share`, the
frozen primary. `calibrate_experiment.py` is not edited: it is a published
runner and a reproduction of a published curve, and changing what it computes
would make that curve unreproducible.

`PREFLIGHT.md` gate 3 is corrected to name the command that exists. A gate whose
command cannot run is the "absence drawn as a pass" shape from the root
`CLAUDE.md`.

**D3 — the pinned refusal keeps its verdict and gets its diagnosis split.**
A probe at 4 traders × 5 goods × 2 episodes × 45s settled **every** game and
still left `above_autarky_share` on 0.000 — NPC seats trade themselves below
their own autarky (`capture` −0.29 to −0.54), so that endpoint sits on a bound
for a reason no episode length can fix. `pinned()`'s message told the reader to
lengthen the episode.

The **exit code does not change**: a pinned endpoint is a failed gate, and
weakening a refusal so that my own run passes is precisely the "quietly fixing
the harness until it passes" this experiment's `CLAUDE.md` names. What changes
is that the runner now says which of the two faults it is, using the `dead()`
count it already had. Written here before the run that will trip it.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | at 4 × 60s NPC seats settle, so the endpoints are not pinned | `pinned()` names an endpoint and the run exits 1 |
| A2 | running games concurrently does not change what a game returns | replicates stop being identical, or the seed check reports False |
| A3 | 8 concurrent games fit on this machine without games dying | harness failures, or `dead()` rising against run 001's serial games |
| A4 | the flow island's zero-period share is off both bounds at δ = 0 | rung 0b's floor/ceiling print shows it pinned |
| A5 | zero-period share moves in δ on a 4-agent flow island | the curve is flat, and gate 3 says **stop and do not spend** |

## Hypothesis

- **Expect:** 0a returns exactly zero on every endpoint with every replicate
  identical (run 001 measured this serially at 2 × 45s; A2 says concurrency
  does not break it). `--vary-npc-seed` returns the first non-zero number this
  experiment has, and it is a policy-draw number, not an agent-variance one.
  0b returns a curve rising in δ, steeper in `sharpen` than in `flatten`.
- **Would surprise me:** 0a non-zero with `--vary-npc-seed` off. That is A2
  failing, and it makes concurrency a measured variance source rather than a
  scheduling detail.
- **Would make me abandon the design:** 0b flat in δ, or pinned at either bound.
  There is then no content axis for the distribution axis to hold constant, and
  gate 3 says stop.

## Metrics for this run

0a reports a between-replicate sd **per endpoint with its denominator** —
`zero_episode_share` (primary), `capture`, `above_autarky_share`, `eff_round` —
plus the per-game sd, attempted/played/harness failures, and games that settled
nothing. Nothing is dropped from a denominator.

0b reports, per (δ, direction, adherence) cell: realised error, **zero-period
share**, always-zero agents, recoveries, and efficiency alongside — never
summed with it. Floor and ceiling printed.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| 1 smoke | `pytest experiments/how-wrong-can-a-shared-convention-be/tests -q` | `deb95e5` | 13 passed |

Gate 1's third command — `noise.py --games 2 --episodes 2` — **failed before
this run started**, and the failure is the first finding; see Outcome.

---

## Outcome

**Status: both gates run. Gate 2 (rung 0a) produced a number; gate 3 (rung 0b)
passed and H0c is not refused. H0b remains unauthorised and unrun, so there is
still no threshold in this experiment.**

- **Records:** `results/rung0-noise.json`, `results/rung0-noise-varied-policy.json`,
  `results/rung0a-serial-control.json`, `results/rung0b-curve.json` (+`.log`),
  `results/rung0a-concurrent-probe.log`.
- **Ran:** rung 0a 96 attempted / 96 played / 0 harness failures / 0 games that
  settled nothing, twice. Rung 0b 9,216 scripted island-runs across 12 table
  shapes. Nothing spent.

### Finding 0 — the runner could not finish, and had not been able to since run 001

`noise.py::main()` raised `UnboundLocalError` **every time it was called**. It
bound a local named `identical`, which shadowed the module function of that
name, on the line that calls it. That line was added by run 001, together with
the guard it calls, *because run 001 had found a 0.0000 that meant nothing* —
so a guard written to stop a misleading number had itself never once executed.

`tests/test_noise.py` tested `identical()`, `pinned()` and `dead()` as
functions. Nothing ran `main()`, which is the only caller any of them has. This
is the root `CLAUDE.md`'s rule arriving in this experiment: *a check nobody has
seen fail is a check nobody has seen work* — and the failure it names, an
absence drawn as a pass, is the same one four of the six CI instances were.

Two tests now run `main()` end to end, and both go red when the shadow is put
back (demonstrated, not assumed).

### Finding 1 — concurrent games shared four signing sockets between them

The first attempt at rung 0a raised `no AF_UNIX signer available on this
platform` on its second game. `switchboard.signing.socket_path()` hashes the
**agent id and nothing else**, every game here seats `t1`..`t4`, and
`SigningServer.start()` unlinks whatever is at the path before binding. Eight
concurrent games, four sockets in `/tmp/switchboard`, verified by listing it.

The raised error is the loud half. **The quiet half is a seat reaching a
neighbour's signer** and writing a line from a key the lobby never witnessed —
which `games/island.md` costs a game its ranking for, arriving silently, inside
the measurement whose entire purpose is to say how far this instrument moves on
its own.

Fixed by giving each game its own `XDG_RUNTIME_DIR` for the length of the game:
the socket for an identity moves, the identity does not. Verified at 8
concurrent games — no harness failures, nothing left in the shared directory —
and then across 192 games with zero failures. Written up as a Switchboard fact
in [`games/switchboard-what-an-entrant-already-holds.md`](../../../games/switchboard-what-an-entrant-already-holds.md)
§3ee, because the next thing that runs two agents of one name at once will meet
it too.

**The 2 × 2 concurrent probe run before this fix is void** and its numbers are
not used anywhere. It is kept as `results/rung0a-concurrent-probe.log` with this
sentence attached, because deleting a contaminated run is choosing a population
after seeing it.

### Finding 2 — A2 fails, and it is not concurrency. The island is a wall clock.

**A2 said running games concurrently does not change what a game returns.** It
does not hold, and the serial control says the cause is not concurrency:

| `--workers 1`, 4 traders × 2 episodes × 45s | seed 1 | seed 2 |
|---|---|---|
| replicate 1 | `capture` −0.2796, 12 settled | −0.5423, 9 settled |
| replicate 2 | `capture` −0.2836, 10 settled | −0.5295, 11 settled |

That is the serial path, the one run 001 measured, on the identical cell with
identical seeds. NPC policies **are** deterministic given their seed; how many
of their moves land inside an episode is not, because the episode is a real
clock and the bell rings on it. Run 001 saw byte-identical replicates at **two**
seats and that stands for two seats.

So `PREFLIGHT.md` gate 2's *"expect exactly zero, and that is a pass"* is
withdrawn, with the superseded sentence left visible in the gate and in
`README.md`'s item 4 — which has now been corrected twice, both times by running
it rather than by thinking about it again. See `DEVIATIONS.md` A3.

This is better than the zero it replaces. **A floor of zero cannot be exceeded
by anything**, so it would have told the next reader nothing.

### Rung 0a — the harness floor, measured

8 replicates × 12 seeds, 4 traders, 5 goods, 4 episodes × 60s, `--workers 8`.
96 attempted, 96 played, **0 harness failures, 0 dead games, no endpoint
pinned**, every complete replicate played the same seeds. 74 minutes.

| endpoint | between-replicate sd | per-game sd | n | for scale: **agent** variance measured elsewhere |
|---|---|---|---|---|
| **`zero_episode_share`** (primary) | **0.0086** | 0.0589 | 96 | — |
| `capture` | 0.0097 | 0.1401 | 96 | 0.229 run-mean, 1.03 per round |
| share above own autarky | 0.0398 | 0.1884 | 96 | 0.085, and 0.114 on a later control |
| `eff_round` | 0.0041 | 0.0964 | 96 | 0.155 |

The right-hand column is from
`../do-they-take-a-handed-over-answer/runs/003-how-much-does-the-instrument-move.md`,
at a different table shape and with **models on the seats**. It is there for
order of magnitude and is **not** a threshold: those numbers contain agent
sampling and these do not, which is the whole reason H0b is a separate, paid
run.

**The harness contributes roughly a twentieth of the movement models did.**
That is the useful sentence this gate exists to produce, and it could not have
been produced by the zero it was expected to return.

**The primary is granular, and the jitter is under one grid step.** The
zero-episode share is a count over 4 traders × 4 episodes, so it moves in
sixteenths; the five values seen across 96 games are 0.0625 … 0.3125. Within a
single seed, across its 8 replicates, its sd has median 0.0289 — **less than
half of one trader-episode**. Averaging 12 seeds takes the run-mean movement to
0.0086.

That is the endpoint choice being vindicated by the instrument rather than by
argument: `above_autarky_share`, also a bounded share, moves within a seed with
median sd 0.1294 — four and a half times the primary's.

### Rung 0a with `--vary-npc-seed` — the policy draw

The same cell again, 96 games, 74 minutes, 0 harness failures, a fresh policy
seed per replicate and the island held fixed. This is a third quantity: not the
harness, and **not agent variance either**.

| endpoint | harness only | + policy draw | × | models, elsewhere |
|---|---|---|---|---|
| **`zero_episode_share`** | 0.0086 | **0.0588** | 6.9 | — |
| `capture` | 0.0097 | **0.1503** | 15.5 | 0.229 |
| share above own autarky | 0.0398 | **0.0859** | 2.2 | 0.085 / 0.114 |
| `eff_round` | 0.0041 | **0.0620** | 15.2 | 0.155 |

**This is what the free rung is for, and it is not zero.** Three tiers now
stand in order with two of them measured here: the harness moves 0.0086 on the
primary, drawing a different policy for the same seats moves 0.0588, and models
move more again. The right-hand column is a different table shape with models
on the seats and is order-of-magnitude only.

The `capture` column is the one to look at before spending: **0.1503 from a
policy draw alone**, against the 0.229 this lab measured with models. Most of
the movement that was attributed to agents in the earlier measurement is
available without any agents at all. Whether that is also true here is exactly
what H0b would settle, and it is a reason to run H0b rather than a substitute
for it.

**`above_autarky_share` is the odd one out**, and it is the endpoint to trust
least: it is the only one whose harness-only movement is already an appreciable
fraction of its policy-draw movement (0.0398 against 0.0859, ×2.2 where the
others are ×7 to ×15), and it is the one that pinned at zero in the shorter
cell. It stays a secondary and nothing is read off it.

### Rung 0b — H0c is not refused

48 islands × 12 table shapes × 8 δ × 2 directions, adherence 1.0, plus a silent
anchor per shape. 9,216 scripted island-runs, 27 minutes, exit 0.

**6 of 12 shapes can read the primary at all**, and the six that cannot are
exactly the six with more goods than traders. That is structural: arm C's rule
is full specialisation, so at most `traders` goods are ever produced, and
Cobb-Douglas zeroes every agent on the rest — at every δ **including zero**.
Correction C4 in `README.md`, amendment A1 in `DEVIATIONS.md`.

The widest cell, 4 traders × 3 goods:

| δ | realised error | **zero-period share**, flatten | realised error | **zero-period share**, sharpen |
|---|---|---|---|---|
| 0.0 | 0.000 | 0.227 | 0.000 | 0.227 |
| 0.05 | 0.023 | 0.272 | 0.021 | **0.525** |
| 0.1 | 0.046 | 0.302 | 0.040 | 0.626 |
| 0.2 | 0.092 | 0.332 | 0.077 | 0.646 |
| 0.3 | 0.140 | 0.396 | 0.109 | 0.694 |
| 0.5 | 0.248 | 0.521 | 0.168 | 0.784 |
| 0.75 | 0.382 | 0.651 | 0.238 | 0.872 |
| 1.0 | 0.495 | 0.720 | 0.293 | 0.905 |

Silent anchor: **0.000**. Autarky 0.668, exchange ceiling 0.719.

**A4 and A5 both hold, at this shape and not at the default one.** The share is
off both bounds at δ = 0 and moves in δ in both directions. H0c is not refused.

**C1 is confirmed inside this run's own output**, which was not expected and is
worth more than the curve. Down the `sharpen` column the primary moves 0.227 →
0.905 while survivor efficiency moves 0.931 → 0.923 → 0.907 → 0.905 → 0.902 for
the first five rungs. **The count moves by 0.4 where efficiency moves by 0.03.**
The Tier 3 design would have estimated δ\* off that second line.

`sharpen` jumps 0.227 → 0.525 at a realised error of 0.021 and then crawls: a
cliff detector, not a ladder. δ\* is estimated on `flatten` — `DEVIATIONS.md`
A2.

### Assumptions

| # | held? | |
|---|---|---|
| A1 | **yes** | nothing pinned at 4 × 60s; every game settled |
| A2 | **no** | and not because of concurrency — Finding 2 |
| A3 | **yes**, after Finding 1 | 0 harness failures in 192 games at `--workers 8` |
| A4 | **yes**, at 4 × 3 | **no** at the game's default 5 goods, and structurally so |
| A5 | **yes**, at 4 × 3 | span 0.678 `sharpen`, 0.493 `flatten` |

### Deviations

D1, D2 and D3 as written above the line. D1's stated risk is what Finding 2
turned out to be about, except that the cause was not the one D1 named — the
non-determinism is in the wall clock and is present serially. No deviation was
added after seeing a number. Three amendments went into `DEVIATIONS.md` (A1–A3);
**none of them moves a threshold**, because there is none to move.

### What this changed, and what is still blocked

- Rung 1's cell is now specific: **4 traders, 3 goods**. It was not before.
- Rung 3's δ ladder runs on `flatten`.
- The harness floor is **0.0086** on the primary and is written down, and the
  policy-draw floor above it is **0.0588**. Both are lower bounds on what H0b
  will find, which is more than a zero could ever have been.
- `PREFLIGHT.md` gate 2 and gate 3 both named things that were not true: gate 2
  expected a zero that cannot happen at four seats, gate 3 named a command with
  two flags that do not exist. Both corrected.

**Still blocked, and deliberately.** H0b is the paid replication of a *model*
cell and no NPC run substitutes for it. Rung 1 does not start until H0b has run
and the thresholds are written into `PREREGISTRATION.md` as an amendment. **No
go has been given and none is assumed.**
