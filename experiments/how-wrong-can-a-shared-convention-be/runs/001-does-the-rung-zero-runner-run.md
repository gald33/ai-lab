# Run 001 — does the rung-zero runner run?

**Opened:** 2026-09-09 · **Status:** done

Everything above the Outcome line was written before the run started.

---

## Why this run

The rung-0 noise runner is the gate every threshold in this experiment is
written against, so it is the one piece of code here whose failure would be
invisible downstream — a wrong number does not break anything, it just makes
every later comparison pass. This run establishes only that
`experiment/noise.py` plays a whole game end to end against a real hub and
gets a scored row back.

**This is a smoke run. Its numbers are not evidence**, only that it produced
them. No threshold may cite this record.

## Specification

| | |
|---|---|
| entry point | `experiment/noise.py` |
| conditions | one cell, NPC seats, nothing varied between replicates |
| units / counts | 2 traders, 5 goods, 2 episodes, 1 round |
| seeds | pinned, `--seed0 1` |
| models | **none** — `games/island/npc.py` heuristics only, nothing spent |
| stimuli | none beyond the island's standing brief |
| command | `python experiment/noise.py --replicates R --games G --traders 2 --episodes 2 --seconds S` |
| cost | zero |

Episode length `--seconds` was varied deliberately across this run, which is
the one thing that makes it more than a smoke test; see Outcome.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | a pinned seed still settles a table | the lobby never settles, or `table.seed` is None |
| A2 | NPC seats reach the board in time to settle moves | `settled == 0` |
| A3 | the viewer's ledger scores a game the runner played | `status == "unscored"`, or no row added |
| A4 | replicates play the same island | the runner's own seed check reports False |

## Hypothesis

- **Expect:** the runner completes a game and returns four endpoints.
- **Would surprise me:** the ledger refusing the row.
- **Would make me abandon the design:** nothing here — this run cannot reach
  the design.

## Metrics for this run

None pre-registered. The four endpoints are printed to show they compute; they
are not reported as measurements of anything.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `pytest experiments/how-wrong-can-a-shared-convention-be/tests -q` | working tree | 10 passed |

Gates 2–4 are the ladder's own rungs and are not attempted here.

---

## Outcome

- **Records:** none kept; this run produced no result worth a results file.
- **Ran:** 7 games attempted, 7 played, 0 harness failures.

**A1–A4 all held.** The lobby settled on a pinned seed, the ledger scored every
game, and the runner's seed check reported that replicates played the same
island.

**The finding is A2, and it is why this record exists.**

| `--seconds` | settled moves | `zero_episode_share` | `eff_round` |
|---|---|---|---|
| 15 | **0** | 1.000 | 0.000 |
| 45 | 6 | 0.500 | 0.289 |

At 15s no NPC completes a round trip. Every game settled nothing, every trader
scored zero in every episode, and both bounded endpoints sat on a bound — so
the between-replicate sd came out **0.0000 on every endpoint**, which reads as
the most precise instrument this lab has ever had. It is the opposite: the
instrument never moved.

That is the calibration failure `PREFLIGHT.md` gate 3 already names — *a metric
pinned at floor or ceiling returns a null that cannot be told apart from a real
one* — arriving in the gate that **produces the thresholds**, where it would
have licensed a threshold of zero and made every later cell significant.

**Two guards were added in response**, before this record was closed:

- `pinned()` — a bounded endpoint that never leaves a bound in any game is
  named, and the run exits non-zero. A pinned run is a failed gate, not a
  tight one.
- `dead()` — games that settled nothing are counted and reported. A seat that
  says nothing has said nothing and the bell rings anyway, so a dead game is an
  outcome, not a harness failure; a cell where *every* game is dead is
  measuring the clock.

Both are tested (`tests/test_noise.py`), and the 15s cell now exits 1 with the
endpoints named.

**The second finding, and it changes the design rather than the runner.**

Two replicates of the identical cell at 45s returned **byte-identical**
endpoints — `zero_episode_share` 0.5, `eff_round` 0.289165, `capture`
-0.5501765343440532 — agreeing to sixteen digits.

NPC policies are deterministic given their seed. Same island seed and same
policy seed means the same play, so a between-replicate sd from NPCs is
**exactly zero by construction**, and the runner reported 0.0000 on every
endpoint without any of the pinning that produced the first finding.

That is the honest answer to the question that run asks — *how much does the
harness move when nothing varies?* — and it is a useful floor: the manager, the
clock and the economy contribute no variance of their own. **It is not a
threshold.** The 0.229 and 1.03 this lab measured before are *agent* variance,
model sampling, and no NPC run contains any of it.

So the design's claim that "the noise measurement is free" was wrong, and is
corrected in `README.md` with the original sentence kept visible. Rung 0 splits:

| | measures | costs |
|---|---|---|
| **H0a** | the harness, clock and economy | nothing |
| H0a `--vary-npc-seed` | the NPC policy draw as well | nothing |
| **H0b** | **the agents** — the number rung 1's threshold needs | **money** |

A third guard was added with the second: `identical()` names the case where
every replicate returned the same numbers, so a 0.0000 is never printed without
saying which of the two reasons produced it.

- **Assumptions that did not hold:** none, but A2 holds only above some episode
  length, which was not known before this run and is now a stated trap.
- **Deviations:** none. Nothing pre-registered was changed.

## What this changed

Rung 0 proper cannot be run at an episode length where NPCs do not settle, and
the pinned check now enforces that rather than leaving it to whoever reads the
output. The real rung-0 run must additionally record **how long a game actually
takes**: at 2 episodes × 45s one game is roughly two minutes wall-clock, so the
8 × 12 replication in `PREFLIGHT.md` is several hours and wants concurrency or
an overnight slot. That is a scheduling fact the preflight does not yet carry.

**Nothing here licenses a threshold**, and after the second finding that is a
stronger statement than it was: the free rung *cannot* license one, however many
replicates it is given. H0b is a paid run and has not been authorised.

`experiment/noise.py` now carries three refusals rather than none — pinned
endpoints, dead games, and identical replicates — and all three were written
because running the thing produced them. None was predicted.
