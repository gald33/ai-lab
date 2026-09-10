# Run 002 — rung 0a and rung 0b

**Opened:** 2026-09-10 · **Status:** open

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

*(written after the run)*
