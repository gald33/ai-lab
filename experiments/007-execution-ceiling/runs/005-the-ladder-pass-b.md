# Run 005 — The ladder, pass B

**Opened:** 2026-08-24 · **Status:** reported

Everything above the Outcome line is written **before** the run starts.

---

## Why this run

Pass A's numbers exist and are not a finding: `PREREGISTRATION-v3.md` requires
two passes agreeing in sign on the same cell before anything is claimed. This
is the second pass. Nothing about the design changes — same cells, same seeds,
same commit, same command.

## Specification

Identical to run 004 in every respect except the output directory.

| | |
|---|---|
| entry point | `run.py`, unchanged since run 004's gates |
| conditions | `l-bare` · `l-protocol` · `l-hint` · `l-both` |
| units / counts | 12 seeds × 4 cells = **48 rounds**, 5 episodes × 180s, 4 traders |
| timing | window 45s, acknowledgement by 30s |
| command | `python run.py --arms l-bare l-protocol l-hint l-both --rounds 12 --episodes 5 --episode-seconds 180 --ack-seconds 45 --ack-by-seconds 30 --agents 4 --out results/005-ladder-b` |
| cost | **192 agent sessions**, 5 waves, **~80 min** |
| go | Given by the owner on 2026-08-24 ("go"), before launch. |

## What pass A said, recorded here before pass B can be read against it

| cell | primary (mean) | seeds ≥ +0.15 | ruined |
|---|---|---|---|
| `l-bare` | — | — | 0.298 |
| `l-protocol` | +0.044 | 5/12 | 0.147 |
| `l-hint` | +0.130 | 7/12 | 0.139 |
| `l-both` | +0.134 | 7/12 | 0.075 |

No cell met the pre-registered rule on the primary. Every cell more than halved
the ruin rate.

## How the two passes are combined

Fixed now, before pass B's numbers exist:

- **A cell is a result** if it holds the **same sign** on **both** endpoints in
  **both** passes, and meets the pre-registered rule — ≥ +0.15 on at least 8 of
  12 seeds for the primary — in at least one, with the other not contradicting
  it in sign.
- **A cell is unresolved** if it flips sign on either endpoint between passes.
  Unresolved is reported as unresolved; the two passes are **not** pooled to
  manufacture a count.
- **Pooling is allowed for one thing only**: the ruin rate, which is a bounded
  share with the lowest measured run noise (0.073). Its pooled 24-seed estimate
  per cell is reported alongside the per-pass values, and is descriptive.
- **The instrument's own movement is measured again**, for free: `l-bare`
  appears in both passes on the same seeds, so pass B gives a fifth and sixth
  observation of a control cell's stability, on the new endpoints.

## Assumptions

Carried unchanged from run 004: A1–A5. **A1** is the one this run tests
hardest — whether the bounded endpoints really carry run-noise of 0.085 and
0.073 rather than more.

## Hypothesis

- **Expect:** the ruin-rate ordering to hold — every treated cell below the
  control, `l-both` lowest. It is the largest and most consistent signal pass A
  produced, on the endpoint with the least run noise.
- **Would surprise me:** the primary clearing 8/12 for any cell in pass B when
  it cleared 7/12 at best in pass A. That would be the threshold being met by
  the noise rather than by the treatment.
- **Would not surprise me:** the primary flipping between passes on
  `l-protocol`, whose pass-A difference (+0.044) is well inside the noise.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `results/005-ladder-b/v3.json`, 48 rounds, stamp `0824T0631`;
  48 boards saved. Pass A is `results/004-ladder-a/`, stamp `0824T0454`.
- **Ran:** all 48 rounds, no failed rounds, in both passes.

- **Numbers — cell means, both passes.** Denominator 12 seeds per cell per pass.

  | cell | above A | above B | ruined A | ruined B | floor A | floor B |
  |---|---|---|---|---|---|---|
  | `l-bare` | 0.314 | 0.387 | 0.298 | 0.184 | 1/12 | 2/12 |
  | `l-protocol` | 0.358 | 0.261 | 0.147 | 0.118 | 2/12 | 2/12 |
  | `l-hint` | 0.445 | 0.402 | 0.139 | 0.106 | 2/12 | 1/12 |
  | `l-both` | 0.449 | 0.431 | **0.075** | **0.085** | 4/12 | 2/12 |

- **Numbers — primary, paired against `l-bare`.**

  | cell | A mean | A ≥+0.15 | B mean | B ≥+0.15 | sign |
  |---|---|---|---|---|---|
  | `l-protocol` | +0.044 | 5/12 | **−0.126** | 1/12 | **flips** |
  | `l-hint` | +0.130 | 7/12 | +0.015 | 5/12 | agrees |
  | `l-both` | +0.134 | 7/12 | +0.043 | 4/12 | agrees |

  **No cell met the pre-registered rule in either pass** (≥ +0.15 on at least
  8 of 12 seeds; best was 7/12). `l-protocol` **flips sign** between passes and
  is therefore **unresolved**, not null. `l-hint` and `l-both` hold sign but
  shrink to +0.015 and +0.043 — inside the noise.

- **Numbers — co-primary, share ruined. All three agree in sign.**

  | cell | A | B | pooled (24 seeds) |
  |---|---|---|---|
  | `l-protocol` | −0.151 | −0.066 | **−0.108** |
  | `l-hint` | −0.159 | −0.077 | **−0.118** |
  | `l-both` | −0.223 | −0.099 | **−0.161** |

  Pooling is permitted here and nowhere else, per the rule fixed before this
  run. Every treated cell lowers ruin in both passes; `l-both` lowers it most
  in both.

- **The instrument check (A1).** `l-bare`, same seeds, two passes:
  **above** 0.314 → 0.387, |diff| **0.073**; **ruined** 0.298 → 0.184, |diff|
  **0.114**. The bounded endpoints move by roughly what run 003 predicted
  (0.085, 0.073) — the ruin endpoint moved somewhat more than predicted.
  **A1 broadly holds**, and the movement is of the same order as every
  treatment difference on the primary.

- **Agreement with pass A:** ruin ordering reproduces exactly —
  `l-both` < `l-hint` < `l-protocol` < `l-bare` in both passes. The primary
  reproduces in sign for two cells and flips for one, and clears its threshold
  in neither.

- **Assumptions that did not hold:** none outright; **A5** remains untested and
  now matters more — `l-both` is the longest block and the best on ruin in both
  passes.

- **Deviations:** none.

## What this changed

**By the rule fixed before the numbers existed, the ladder has one result and
one non-result.**

**The result: every block lowers ruin, and the two together lower it most.**
Pooled over 24 seeds, `l-protocol` −0.108, `l-hint` −0.118, `l-both` −0.161,
with the same ordering in both passes independently. The control ruins 30% and
18% of acting trader-episodes in the two passes; `l-both` ruins 7.5% and 8.5%.
This is the endpoint with the least run noise, it reproduced, and it is the
mechanism every block was aimed at.

**The non-result: nothing raises the share above autarky.** No cell met the
threshold in either pass, `l-hint` and `l-both` shrank to +0.015 and +0.043 in
pass B, and `l-protocol` reversed sign. Whatever these blocks do, **they do not
move traders above their own solo optimum more often** — they stop them ending
with nothing.

**Which is a coherent finding rather than a mixed one.** Removing zeros and
creating gains are different things. The cheat in run 001 did the second: it
told traders exactly which exchange would pay, and they got above autarky far
more often, at the cost of ruining more rounds. The decomposed blocks do the
first: they teach caution — commit in pieces, watch the clock, never hold none
of a good — and caution removes disasters without manufacturing surpluses.

**`l-protocol` flipping sign is the honest headline for the primary.** +0.044
then −0.126, same block, same seeds, twelve pairs each time. Anyone reading
only pass A would have reported a small positive protocol effect. That is what
two passes are for, and it is the third time in this lab that a single pass
would have produced a false direction.

**What is now known about the instrument.** Its control cell moved 0.073 on the
primary and 0.114 on ruin between two identical passes. Effects smaller than
about 0.15 on these endpoints are not measurable here at 12 seeds, which is
exactly where `l-hint` and `l-both` landed. The ruin effect is measurable
because it is 0.11–0.16 — at the edge, and it reproduced.

**What this experiment should not do next.** Add a fifth block. The stopping
rule in v3 said this experiment ends rather than proposing another one if
nothing moves the primary, and nothing did. The ruin result is worth keeping;
the search for a block that manufactures surplus is over.
