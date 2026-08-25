# 007 — Pre-registration v3 (the ladder)

**Frozen 2026-08-24, before run 004.** v1 and v2 stand as runs 001 and 002's
frozen designs and are not revised.

## What forced a new endpoint

Run 003 replicated one cell four times, changing nothing, and measured the
instrument's own movement:

| endpoint | per-seed sd across runs | **run-mean sd** |
|---|---|---|
| captured gain (median) | 1.029 | **0.229** |
| `eff_round` | 0.359 | 0.155 |
| round beat its floor | 0.365 | 0.126 |
| **share of trader-episodes above own autarky** | 0.265 | **0.085** |
| **share of trader-episodes ruined (zero utility)** | 0.259 | **0.073** |

Captured gain is a ratio with an unbounded tail: one Cobb-Douglas zero moves a
round by units. The two **bounded share** measures carry a third of its run
noise. Every threshold this lab has set was on the noisy one.

**The primary changes accordingly**, and it is a change of instrument rather
than of question.

## Question

The block that worked in run 001 contained three separable things: numbers no
trader could have derived (**the cheat**), a way of acting with others (**the
protocol**), and facts a trader could work out from its own private block
(**the hint**). With the cheat removed, **how much of the effect survives, and
which part carries it?**

## Cells — a 2×2, cheat removed from all four

| cell | block | body sha256 (16) | words |
|---|---|---|---|
| `l-bare` | none | — | — |
| `l-protocol` | `decomposed/01-protocol.md` | `18e33d64c9e3dd07` | 346 |
| `l-hint` | `decomposed/02-hint.md` | `964f4250bfaa7c0d` | 412 |
| `l-both` | `decomposed/both.md` | `7bf764c5ad0ebbbd` | 758 |

`both.md` is **generated** as the concatenation of the other two, in order,
with no word changed, and is regenerated rather than edited. A 2×2 whose
interaction cell is a rewrite measures nothing.

**The protocol block is domain-free**, checked against a 35-word list: it names
no good, no exchange, no production, no island. **The hint block is derivable
from a trader's own private block alone.** Neither contains anything from
`walras()` or from another trader's state — see
`stimuli/decomposed/00-CHEAT-removed.md` for the audit of what came out.

## Units

**12 seeds × 4 cells = 48 rounds**, paired on seed. 5 episodes × 180s, 4
traders, window 45s with acknowledgement by 30s. Seeds 1–12.

## Primary

**Share of trader-episodes above own autarky** — of the trader-episodes in
which the trader produced, the fraction ending with more utility than that
trader's own solo optimum. Bounded in [0, 1]; run-mean sd 0.085.

Reported as paired differences per seed against `l-bare`, for each of the three
treated cells, mean and median, denominator 12 seeds per cell.

## Co-primary

**Share ruined** — trader-episodes ending with zero utility. Bounded, run-mean
sd 0.073, and the mechanism every block in this experiment is aimed at.

A cell that raises "above autarky" **and** raises "ruined" has made the outcome
more variable rather than better, which is exactly what the full plan did in
run 001 (23–41% ruined against the control's 18%). Both are always reported
together.

## Thresholds, fixed now

Set against a run-mean sd of ~0.085, not against habit:

- **A block works** if its paired difference against `l-bare` on the primary is
  **≥ +0.15** on at least **8 of 12** seeds.
- **A block is harmful** at **≤ −0.15** on the same counting rule.
- **Anything else is a null.**
- **The interaction** — whether `l-both` exceeds the better of `l-protocol` and
  `l-hint` by ≥ +0.10 — is reported but **not** claimed at this size; a
  difference of differences needs more than one pass.

## Replication is part of the design, not a follow-up

**No ordering among the cells is believed from one pass.** Run 003 showed the
same cell's run-mean moving by 0.085–0.23 depending on endpoint, and 006 showed
a paired difference reversing sign between runs. Run 004 is **pass A**; pass B
repeats it on the same seeds. A result is a result when both passes agree in
sign on the same cell; a cell that flips between passes is reported as
unresolved, not averaged into significance.

Pass A alone may report **descriptive** numbers with their denominators. It may
not report a finding.

## Stopping rule

If neither block moves the primary in either pass, then with the cheat removed
nothing survives — the effect in run 001 was the numbers, not the reasoning or
the method — and this experiment ends rather than proposing a fifth block.

## What is not claimed

Nothing about other models, islands, agent counts or episode lengths. Nothing
about captured gain, which this design no longer uses as a primary and which
run 003 showed this lab cannot resolve.
