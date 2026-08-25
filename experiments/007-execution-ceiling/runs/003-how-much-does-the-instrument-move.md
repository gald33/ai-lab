# Run 003 — How much does the instrument move on its own?

**Opened:** 2026-08-23 · **Status:** reported

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

- **Records:** `results/003-stability-a`, `-b`, `-c2`. The first C attempt
  (`-c`) is in the tree with all twelve rounds marked failed and contributes to
  nothing (D6).

- **Ran:** A **12/12**, B **10/12** (seeds 11 and 12 lost to the outage), C's
  re-run **12/12**. Run 001's `e-plan` is a fourth observation of the same cell,
  under an earlier commit. Analysis is on the **10 seeds common to all four**.

- **Numbers — the same cell, same seeds, four times, nothing varied.**
  Captured gain, median per round:

  | seed | run 001 | A | B | C | range |
  |---|---|---|---|---|---|
  | 1 | +1.00 | +1.00 | +1.00 | +0.75 | 0.25 |
  | 2 | +1.00 | −0.91 | +1.00 | +1.00 | 1.91 |
  | 3 | −1.57 | −0.49 | +1.00 | +0.26 | 2.57 |
  | 4 | +1.00 | +1.00 | −2.58 | −4.12 | **5.12** |
  | 5 | −0.46 | +1.00 | +1.00 | −0.73 | 1.73 |
  | 6 | +1.00 | +1.00 | +1.00 | +1.00 | 0.00 |
  | 7 | +0.46 | −4.44 | +1.00 | +1.00 | **5.44** |
  | 8 | −0.99 | +1.00 | −0.51 | −0.99 | 1.99 |
  | 9 | −1.29 | +0.33 | +1.00 | +0.61 | 2.29 |
  | 10 | +1.00 | +1.00 | +1.00 | +1.00 | 0.00 |

  **Between-run sd on the same seed, averaged: 1.029.**
  Mean range on the same seed: **2.131**.
  Between-seed sd inside one run: 1.399.

- **Numbers — per run, on the common seeds.**

  | | rounds above floor | mean `eff_round` | zero-utility |
  |---|---|---|---|
  | run 001 | 5/10 | 0.432 | 41% |
  | A | 4/10 | 0.390 | 34% |
  | B | **7/10** | **0.737** | 23% |
  | C | 5/10 | 0.509 | 32% |

- **Assumptions.** **A1 held** — four distinct stamps and workspace sets,
  checked. **A2 did not fail as feared**: the four runs do not trend, they
  scatter (0.432, 0.390, 0.737, 0.509 in time order), so this is noise rather
  than a drift in the hub or the hour. **A3 held**: between-run and
  between-seed sd are separable and both are large.

  **Three of ten seeds are stable at +1.00 across all four runs** (6, 10, and
  1 within 0.25). The variance is not uniform — it is concentrated in the seeds
  whose plans do not reliably complete.

- **Deviations:** D6, written between the failure and the re-run.

## What this changed

**The instrument moves by 1.03 and the effects it was built to detect are
0.10 to 0.27.** On identical inputs — same block, same seeds, same code, same
timing — the same island's answer ranges over 2.13 on average and over 5 on two
of ten seeds. Seed 7 returned +0.46, −4.44, +1.00 and +1.00.

**Every pre-registered threshold in this lab has been below its own noise
floor.** 005's 0.10, 006's 0.10, 007's 0.15: all set against a quantity that
moves by an order of magnitude more when nothing is changed. That is not a
criticism of any single run's analysis; the analyses were correct given the
numbers. The numbers were never resolvable.

**What this retires.** Every paired between-cell difference this lab has
reported, including run 001's +0.709 — which was one draw from a distribution
whose spread on the same cell is 1.03. Run 002's null, 006's null, 005's three
negatives: none of them measured what their records claim, and none should be
cited.

**What survives, unchanged.** Absolute measurements against a closed form, and
counts too lopsided for noise to explain:

- the solo floor, 0.972 of the closed-form optimum over 104 acts, 85 at it;
- production compliance under the plan, 214/214, against 0/215 untreated;
- board-key disclosure, 20/20 against 0/20 with identical tools;
- labour splitting, 68% of treated trader-episodes against 0/149 untreated.

Those are the lab's real results. They are all of the form *"did the agents do
the thing at all"*, and none of them is a difference in degree.

**What would make degrees measurable.** Not more seeds at this spread — 0.15
would need n≈370. Either an outcome measure that is not dominated by the
Cobb-Douglas zero (the variance is concentrated in exactly the seeds whose
plans fail to complete, and a single zero swings a round by units), or a
mechanism where a partial plan degrades smoothly. The second is what run 002
was reaching for and could not demonstrate, because this is the noise it was
being measured against.
