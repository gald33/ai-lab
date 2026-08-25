# 005 — the round-0 focal point is not the rounding

*Written 2026-08-25 against `results/agents.json`, offline: nothing was run and
nothing spent. This answers `005-render-precision-fix`, and it answers it by
disagreeing with the fix the item names first.*

## What the item asked for

`INSTRUMENT-REVIEW.md` established that both hinted cells were coordinated at
round 0 — before any agent had heard anybody — and read that as a **display
artifact**: every number an agent sees goes through `prompt._vector`, which
formats with `f"{p:.3f}"`, so "each agent given the hint is handed the same
string" and 99.2% of submissions sit on the 3-decimal grid. The item it opened
is *"stop the instrument handing every agent the same printed number"*, done
when the hint is either rendered at a precision that does not do that, or the
hinted cells are dropped.

The first branch does not exist. Rendering precision is not what hands every
agent the same number.

## What the record says

**The hint is one number, given to everyone by design.** `market.draw_world`
draws a single `hint` per world and `prompt.build` prints it to all eight
agents under a block that says every trader has been given this same estimate
and knows the others have. Rounding is not what makes it common; the design is.

**Round 0 in the hinted cells is copying, and it is nearly total.** Of 192
round-0 submissions across the two hinted cells, **184 are the hint exactly as
the prompt printed it** (`content-only` 94/96, `both` 90/96) and **0 are the
unrounded hint** — agents copied the string they were shown, which is the only
form of it they ever had:

```
cell           worlds  at zero  copied hint
baseline           12        0        0/96
both               12        6       90/96
content-only       12       11       94/96
method-only        12        0        0/96
```

**Rounding never collided two agents' private signals.** Across all twelve
worlds there are 336 agent pairs, and **not one pair is shown the same printed
signal vector**; of 1,344 printed components, 337 match, of which 336 are
bread, which the format pins at exactly 1.0 in every cell. The 3-decimal grid
does not merge distinct estimates into one. It never had the chance to.

So printing the hint at six decimals instead of three changes nothing that
matters: eight agents handed one number still copy one number, and still agree
before anyone has spoken. Raising the precision would let the *next* run
report that the artifact was addressed while reproducing it in full.

## What actually closes it

Two branches, and only these two. Both are pre-registration decisions, not
code, so neither is taken here:

1. **Drop the hinted cells.** `PREREGISTRATION-v2.md`'s reason for the hint —
   that `both − hint > protocol − baseline` isolates whether the protocol adds
   something structural to coordinate about — survives only if the hint cells
   measure deliberation, and on this record they measure copying. The two
   unhinted cells (`baseline` 3/12, `method-only` 4/12) are unaffected by the
   artifact and remain readable, which is what a re-run would be reading.
2. **Make the hint not a copyable common string** — draw it per agent from a
   tighter distribution than the private signal, or state it as an interval
   rather than a point. This keeps a "public, better-than-yours estimate" arm
   at the price of no longer being the common-knowledge hint the current design
   describes, so the block's text changes and the stimulus re-freezes.

## The acceptance criterion, as code

`analysis/focal.py` is the check the item asks to have named in the next
pre-registration, written so it cannot be forgotten:

    python analysis/focal.py results/agents.json

It reports, per cell, how many worlds had **zero dispersion at round 0** and
how many round-0 submissions were the printed hint, denominators beside both,
and exits non-zero if any cell agreed before anyone spoke. On the v1 record it
fails on exactly the two hinted cells, which is what calibrates it.

A run whose hinted cells still fail this check has not measured deliberation
in them, whatever it spent.
