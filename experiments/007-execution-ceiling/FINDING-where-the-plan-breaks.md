# Where the plan breaks

**Written 2026-08-23, from run 001's 24 saved boards. No new data; nothing
spent.** A re-analysis of a run already reported, answering the question its
outcome raised: 214 of 214 productions matched the plan, but only 112 of 144
named exchanges ever settled. Why does a trade both parties were told to make
fail to happen?

## It is not that the plan is impossible

For every one of the twelve islands, the plan's twelve transfers are
executable — and not narrowly. Starting each trader from its own planned
production and applying the transfers bilaterally:

- a workable order exists on **12 of 12** seeds;
- and **100% of 4,000 random orders** complete, on every seed.

There is no sequencing puzzle. Any order works, because the plan never asks a
trader to give more of a good than it produces.

## It is not that they act before producing

Of the 96 refusals reading *"you have N uncommitted"*, only **16 (17%)** came
from a trader that had not yet produced that episode. The other **80** came
from traders that had produced and were still short.

Since any order works from own production, being short after producing means
the goods went somewhere the plan did not send them.

## It is not that they trade with the wrong people

Of the settled (giver, taker, good) combinations, only **8 of 120 (7%)** are
combinations the plan does not contain. Partners and goods are almost entirely
right.

## It is the quantities

Actual given ÷ planned given, per trader-episode-good, n = 213:

| | share |
|---|---|
| gave less than half the plan | **22%** |
| gave under | 13% |
| **gave the planned amount** | **53%** |
| gave up to 2× | 12% |
| gave over 2× | 1% |

Median 1.00, mean 0.86. **Just over half of the flows are right and the rest
drift, in both directions.** Over-giving starves a later planned trade — 23% of
trader-episode-good rows give away more than the plan allots — and that is what
produces the 80 post-production refusals, which in turn are the missing 32
exchanges.

## Why this is the interesting result

These agents copy a production instruction **perfectly**: 214 of 214, to within
5%, seven rounds fully compliant in episode 1. The same agents, in the same
prompt, given exchange quantities in the same format, get them right barely
half the time.

The difference between the two is not the arithmetic. It is that **production
is a solo act and exchange is a joint one**. A production line is written once
and settles against nothing but a budget. An exchange has to match a
counterparty's message, arrive while both sides still hold the goods, and be
approved before the bell — and every one of those is a place for a quantity to
drift.

**And the outcome is brittle to exactly this.** From the run: of the six rounds
where every planned exchange settled, five beat their floor; of the six where
any was missing, one did. A plan executed at 90% is not worth 90% — the traders
are holding deliberate corner bundles, and a Cobb-Douglas corner that never
gets completed is worth nothing at all.

## What it points at

Not more instruction. The instruction was perfect and was followed for
production. The gap is in **executing a joint action against a live
counterparty**, and the candidates are mechanism-shaped:

1. **Make an exchange atomic against the plan** — a proposal that names a
   quantity either matches or is refused, so drift cannot silently starve a
   later trade. This is a settlement rule, not a hint.
2. **Let a proposal survive the bell**, so a trade that missed its window is not
   lost. 72 lapse notes across the run.
3. **Make a failed corner survivable** — the brittleness is what converts a
   22% shortfall into a zero round.

Each is a change to the game rather than to what agents are told, which is
where the evidence has been pointing since the 2026-08-23 report and now points
with a specific mechanism attached.
