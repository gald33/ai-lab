# Run 005 — The ladder, pass B

**Opened:** 2026-08-24 · **Status:** running

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

- **Records:**
- **Ran:**
- **Numbers:**
- **Agreement with pass A:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
