# 006 — Ratio disclosure

**Does telling traders what to disclose improve coordination?**

## Why this experiment exists

Experiment 005 asked whether a content-free deliberation *protocol* helps, and
found a null. Two of its later runs found worse than a null: adding text at all
— a maximal "talk more" treatment, and a minimal one-paragraph hint — both cost
efficiency relative to their controls.

Then 005's run 007 removed the other agents and measured what a trader does
alone. It reaches its own autarky optimum almost exactly: **mean 0.972 across
104 production acts, 85 of them at the optimum, and not one corner bundle.**

That changes what a shortfall means. The floor these experiments score against
is not a theoretical ceiling the agents can't reach — they reach it when left
alone. So a peopled round finishing below it is losing value **through the
interaction**, and the loss splits cleanly in two:

| | what it is | run 006 of 005, `probe-bare` |
|---|---|---|
| **presence** | trader-episodes with any production | 0.78 |
| **exchange** | utility ÷ own autarky optimum, for those that acted | 0.90 |

Exchange should be **above 1** — gains from trade are the whole reason to have
counterparties. It is 0.90, with 34 of 93 acting trader-episodes above their
own optimum. Trade is close to break-even and highly variable, and a fifth of
trader-episodes are simply empty.

## The hypothesis

Traders cannot see each other's capacities or tastes, and nothing tells them
what would be useful to say. The information that would actually settle who
should make what is two **ratios** — what a good costs you in another good, and
what it is worth to you now — and both are scale-free, so they can be compared
across traders without a shared unit or a numéraire.

At an agent's own optimum these two ratios are equal, which is why an untraded
agent has one number to state rather than two, and why the gap between them is
exactly where an exchange is worth making.

**This is a domain hint and is called one.** It tells agents what to say about
the economy. It is not a protocol and no claim about protocols may be built on
it.

## Design

Three cells on paired seeds: `r-bare` (base instructions), `r-placebo` (base
plus a length- and register-matched paragraph carrying no domain content), and
`r-ratios` (base plus the disclosure block). The placebo is not optional: 005
established that being handed a considered-looking paragraph has a cost, so
without it a difference cannot be attributed to the content.

Frozen specification in [`PREREGISTRATION.md`](PREREGISTRATION.md).
