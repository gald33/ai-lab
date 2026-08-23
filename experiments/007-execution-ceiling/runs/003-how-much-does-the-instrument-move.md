# Run 003 — How much does the instrument move on its own?

**Opened:** 2026-08-23 · **Status:** running

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards.

---

## Why this run

Three times now a cell has moved between runs by more than the treatment effect
the run was built to detect:

| | | |
|---|---|---|
| 006 run 001 → 002 | `r-ratios` against its control | **−0.242 → +0.271**, sign reversed |
| 007 run 001 → 002 | the plan cell's exchange completion | **78% → 33%** |
| 007 run 001 → 002 | the plan cell's rounds above floor | **6/12 → 0/12** |

The last two are the same block on the same seeds with no mechanical
difference — run 002's `t-plan` held a permission it never used.

`FINDING-run-level-variance.md` estimated the paired-difference spread at sd
0.322 pooled against 0.175 within a run, and proposed measuring the run effect
directly. That was not done, and run 002 is what it cost: a clean manipulation
whose primary cannot be read, because its own control did not replicate.

**This run measures nothing about agents.** It repeats one cell, unchanged, and
asks how much the answer moves when nothing is varied.

## Specification

| | |
|---|---|
| entry point | `run.py`, `e-plan` only — run 001's cell, `SPLIT_LABOUR` off, exactly as run 001 |
| conditions | **one**: `e-plan`. No control, no treatment, no contrast (`--no-control`). |
| units / counts | **3 replicates × 12 seeds = 36 rounds**, 5 episodes × 180s, 4 traders |
| seeds | 1–12 in every replicate — the same twelve islands, three times |
| timing | window 45s, acknowledgement asked by 30s, as run 001 |
| command | three sequential invocations, `--out results/003-stability-a|b|c`, each `--arms e-plan --rounds 12 --episodes 5 --episode-seconds 180 --ack-seconds 45 --ack-by-seconds 30 --agents 4 --no-control` |
| cost | **144 agent sessions**, ~32 min per replicate, **~96 min** total |
| go | Given by the owner on 2026-08-23 ("Yes do it"), before launch. |

Three separate invocations rather than one, so each replicate gets its own
`RUN_STAMP` and its own workspaces — a replicate that shared a board with
another would not be an independent measurement of anything.

## What is measured

Per replicate, per seed: captured gain (mean and median), `eff_round`,
exchange completion, zero-utility trader-episodes, presence.

Then the decomposition this run exists for:

1. **Between-replicate sd** of each measure, on the same seed — how much the
   same island's answer moves when nothing changes.
2. **Between-seed sd** within a replicate — the variation a paired design
   already removes.
3. **The ratio.** If between-replicate sd is comparable to or larger than the
   effects this lab has been reporting (0.10–0.27), then no run so far has
   resolved anything, and the pre-registered thresholds have all been below the
   noise floor.

Run 001's `e-plan` becomes a fourth observation of the same cell, reported
beside the three and flagged as run under an earlier commit.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | The three replicates are independent: separate stamps, separate workspaces, separate sessions. | Two replicates share a workspace name. Checked before analysis. |
| A2 | Nothing outside the runner varies systematically across ~96 minutes — hub load, model serving, time of day. | Replicates trend monotonically rather than scattering. That would be a finding about *when* to run, not about noise. |
| A3 | 12 seeds × 3 replicates is enough to separate a between-replicate sd from a between-seed sd. | The two are within each other's uncertainty and the run says the decomposition is unresolved. |

## Hypothesis

- **Expect:** a between-replicate sd large enough to explain the 006 sign
  reversal and run 002's halving — which would mean this lab's instrument
  cannot resolve 0.10-sized effects and every threshold set so far was set
  below the noise.
- **Would surprise me:** replicates agreeing closely. That would make the two
  observed swings systematic rather than random, and the search would turn to
  what actually differed between those runs — the tool grant in 006, the
  `SPLIT_LABOUR` flag in 007 — despite neither being used.

## What this run cannot do

It cannot fix anything. It produces a number that says how much to distrust
every paired difference this lab has reported, including its own positive
result in run 001.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
