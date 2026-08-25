# Proposal — don't bet the whole labour on a trade that might not happen

**Status: a proposal, with its arithmetic already done.** Raised by the owner on
2026-08-23 after run 001. Nothing has been spent on it.

## The idea

Run 001 handed traders the exact equilibrium and they produced it perfectly —
and then 22% of the named exchanges never settled, and the rounds where any
were missing collapsed. The plan asks a trader to produce a **corner bundle**:
almost all of one good, worthless on its own, valuable only once the trades
complete. It is a bet with no hedge.

The owner's suggestion: commit only part of the labour to the plan, and keep
the rest on something that pays whatever happens.

## The arithmetic, before spending anything

Blend the plan's labour shares with the trader's own solo optimum:
`s = λ·s_plan + (1−λ)·α`, and scale its trades by the same λ. λ=1 is run 001;
λ=0 is autarky. Simulated over the twelve islands, with each named trade
completing independently at the rate run 001 actually achieved:

| trade completion | full plan (λ=1) | | hedged (λ=0.8) | |
|---|---|---|---|---|
| | mean × autarky | zero-utility | mean × autarky | zero-utility |
| 1.00 | **1.733** | 0% | 1.612 | 0% |
| 0.90 | 1.411 | 16% | **1.502** | 0% |
| **0.78 — observed** | 1.067 | **32%** | **1.366** | **0%** |
| 0.60 | 0.645 | 54% | **1.166** | 0% |

The optimum over λ at the observed completion rate is interior, at **λ ≈ 0.8**,
worth **1.37×** against the full plan's **1.07×**.

**The mechanism is visible in the second column.** Hedging does not trade
better; it removes the zeros. A Cobb-Douglas trader holding none of one good
scores nothing, and the full plan puts 32% of trader-episodes in that state at
the completion rate these agents achieve. The hedge's cost when everything
works is 0.12×; its benefit when things fail is the difference between 1.07 and
1.37. Below about 95% completion it wins.

## Two versions, and they are not the same experiment

**A. Hedged production — a strategy, no rule change.** The plan handed over
names blended shares and scaled trades. Everything else is run 001. Cells:
`e-bare`, `e-plan` (λ=1, already run), `e-hedge` (λ=0.8). 12 paired seeds.
Prediction is sharp and pre-registerable: `e-hedge` beats `e-plan` on captured
gain, and its zero-utility trader-episode count falls to near nothing.

**B. Tranched production — the owner's literal proposal, and a rule change.**
Produce half, trade it, then commit the rest knowing what settled. This is
strictly better than a fixed hedge, because the second tranche is allocated
with information rather than in advance.

It cannot be done under the current rules. The manager refuses a second
`PRODUCE` in an episode — *"you have already produced this episode"*, 9
refusals in run 001 — and holdings are consumed at every bell, so tranches
cannot span episodes either. It needs the manager to accept partial labour
commitment: several `PRODUCE` lines per episode, summing to the budget.

That is a change to **what the manager will settle**, which is the kind of
change this lab is allowed to make (format and timing), but it is an instrument
change and would be pre-registered as one. It also changes the meaning of every
earlier run's production numbers, so it starts a new baseline rather than
extending the old one.

## Recommended order

**A first.** It needs no rule change, its prediction is quantitative, and it
tests the *idea* — that partial commitment beats full commitment under
imperfect completion — at the lowest cost. 12 seeds × 3 cells = 36 rounds, but
`e-plan` and `e-bare` at these seeds are already run, so in practice it is
**12 rounds and 48 sessions** against existing controls, with the caveat that
across-run comparison is weaker than within-run and would be stated.

**B if A works.** The adaptive version is the interesting one, and it is worth
a rule change only once the fixed version has shown the principle holds.

## What would falsify the whole idea

`e-hedge` failing to beat `e-plan`. That would mean the zeros are not what is
costing the rounds — that traders holding a hedged bundle simply trade less, or
that the 78% completion rate is itself a function of how aggressive the plan is
rather than a fixed property of the mechanism. The second is worth watching for
either way: a gentler plan may complete more often, which would make the hedge
look better for a reason that has nothing to do with insurance.
