# The run is a bigger effect than any treatment measured so far

**Written 2026-08-23, after run 002, from runs 001 and 002 only. Not a run
record — a re-analysis of two existing runs, adding no data.**

## What happened

`r-ratios` is one frozen block, `36cd95dc…`, run twice on the same five
islands. Paired against `r-bare` on exchange:

| seed | run 001 | run 002 |
|---|---|---|
| 1 | −0.27 | +0.15 |
| 2 | −0.18 | +0.16 |
| 3 | −0.03 | +0.38 |
| 4 | −0.19 | +0.12 |
| 5 | −0.54 | +0.55 |
| **mean** | **−0.242**, 0 of 5 | **+0.271**, 5 of 5 |

**Pooled over ten paired rounds: mean +0.015, median +0.044, 5 of 10
favouring.** Every seed flips sign between the runs. Nothing about the block
changed: same hash, same seeds, same model, same clock, same hub.

**It is not a labelling error.** Workspaces match arms in both result files,
and only `r-ratios` boards carry the block's vocabulary. Checked before writing
this.

## What it means for what has been claimed

The spread of paired differences is **sd 0.322** pooled, **sd 0.175** with each
run's mean removed. Against that:

| to detect | seeds needed within one run |
|---|---|
| 0.10 | ≈ 25 |
| 0.20 | ≈ 7 |
| 0.25 | ≈ 4 |

Every run in experiments 005 and 006 used **5 seeds** and several used 3. The
pre-registered threshold has been **0.10** throughout. **This design has never
been able to resolve the effect it was written to detect** — including run
002's null, and including the stopping rules that two of those nulls fired.

The differences that *have* been reported — −0.207, −0.269, −0.221, −0.074 —
all sit at or below one within-run standard deviation.

## What is not undermined

- **005 run 007**, the empirical floor: mean 0.972 over 104 production acts,
  85 at the optimum, zero corner bundles. That is a level, measured against a
  closed form, not a small difference between cells.
- **006 run 002a's manipulation result**: 20 of 20 cost keys against 0 of 20 in
  two untreated cells. A count that lopsided needs no power argument.
- **Presence** differences, which have been large (0.83 against 0.59) and
  consistent in direction within runs.

The pattern is that this lab's **absolute** measurements are sound and its
**between-cell difference** measurements are not.

## What to do about it, in order

1. **Establish whether the run effect is the tool grant or noise.** Re-run run
   001's exact three cells (`r-bare`, `r-placebo`, `r-ratios`) under the
   current grant, same seeds. If the reversal follows the grant, D2 changed the
   untreated cells despite their writing no keys, and that is a finding about
   capability grants. If it does not, the run effect is noise and item 2 is the
   only way forward. **15 rounds, 60 sessions.**
2. **Stop pre-registering 0.10 thresholds at n=5.** Either raise n to ~25 for a
   0.10 effect, or declare the smallest interesting effect to be 0.25 and use
   n≈5 honestly, and say which in the pre-registration.
3. **Re-read the two stopping rules.** 005's and 006's both fired on
   differences smaller than one within-run sd. They should be treated as *not
   yet tested* rather than as settled, and neither should be cited as evidence
   that instruction is useless.

## The uncomfortable reading

Three treatments were reported as harmful and one as null. Pooled properly,
what has actually been shown is that **this instrument cannot yet tell any of
these treatments apart from doing nothing** — and that a run-to-run difference
nobody controlled is larger than all of them.
