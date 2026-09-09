# 004 — Stock and flow

**Status: run. Results below.**

## Question

[002](../002-barter-conventions/) found that a shared price reaches the Pareto
frontier and ruins somebody on half its islands. Is that a fact about the
convention, or about a world where a production commitment can never be taken
back?

The answer changes what 002 means. If ruin survives per-period consumption, then
"the convention adds leverage, not safety" is a claim about conventions. If it
does not, the claim is about irrecoverable commitment, and a shared price is
merely the thing that made agents commit hard enough for irrecoverability to
bite.

## Motivation

002's island accumulates. Holdings start at zero, production adds to them, trade
moves them, nothing ever removes them, and utility is read once off the final
bundle. Cobb-Douglas utility is zero whenever any good is missing, so an agent
that failed to acquire a good has scored zero for the whole run and no later
round can fix it. There is no consumption step, and the conservation invariant
(`holdings + escrow == everything produced`) makes adding one impossible without
changing the accounting.

The [Tier 3 calibration](../002-barter-conventions/tier3-design.md) is what
forced the question. At δ = 0 — the exactly correct equilibrium price, announced
to everybody, fully adopted — only **23 of 48 islands survive**. That is not a
convention effect: there is no error in the convention. It is the accumulation
rule, and it caps the whole instrument, because the calibration curve runs from
48% survival to 0% with half the damage present before the perturbation starts.

## Hypothesis

That most of 002's ruin is the accumulation rule rather than the convention, and
specifically:

1. Permanent ruin should **largely disappear** under flow. An agent that misses
   a good in one period is not thereby denied it forever, so the terminal
   Cobb-Douglas zero becomes a bad period.
2. The *ordering* of the arms should survive. If flow reshuffles which
   convention wins, then 002's ladder was measuring accumulation and not
   conventions, which would be a much stronger result than the one expected.
3. Arms with a price should **converge** across periods, and arms without one
   should not. Under flow the only thing carried from period to period is what
   agents have learned, and a convention is the mechanism that carries it — so
   an arm with no shared price has nothing to improve on.

What would make this wrong: permanent ruin staying at stock levels. That would
mean ruin is caused within a single period — agents specialise into a
configuration that cannot cover everybody, and a fresh period reproduces the
same configuration — in which case irrecoverability was never the mechanism and
002's finding stands exactly as written.

## Design

The same island, the same manager, the same arms, the same seeds. **Two scoring
models**, and every island is run through both.

**Stock** — 002 unchanged. One unit of labour, produce, trade for `rounds`
rounds, score the final bundle once.

**Flow** — every period is a whole economy. One unit of labour, produce, trade
for `rounds` rounds, then **consume everything** and start again with nothing.
Welfare is the sum of per-period utility.

The flow model is implemented as a mode inside 002 (`barter.run.run_island_flow`,
`Manager.close_period`) rather than as a fork, so 002's published ladder is
untouched and still reproduces. This experiment imports 002's package directly
for the same reason: a finding about 002's harness produced by a copy of 002
would be a finding about the copy.

### What carries across a period

Only what agents have learned. Holdings do not, labour does not, open offers do
not — they expire at the bell and their escrow returns, because goods held in
escrow are goods nobody can eat.

Traders are constructed once, outside the period loop, and keep their price
beliefs. Arm C's tatonnement therefore continues across periods, and **that is
the only channel between periods** — which is what was supposed to make "does a
convention help agents converge" answerable here.

It did not, at 002's default of 30 talking rounds per period: the channel
saturates inside period 0, reaching the true equilibrium to a relative error of
0.001 with every agent agreeing exactly, so a later period starts from precisely
where the first one ended. `discovery_rounds` exists to starve it — see the
convergence result below, which is a finding about the measurement before it is
a finding about the island.

It also forced a rewrite. 002's instalment policy conditions on holdings — *make
the valuable thing you are short of* — and with holdings reset there is nothing
to read. Under flow an agent must learn from prices and observations instead.
That is the point rather than a cost: it makes the convention the sole carrier
of information between periods, instead of letting the stock of goods carry it.

### Why the two are comparable

Cobb-Douglas exponents sum to 1 on this island, so utility is homogeneous of
degree 1. `T` identical periods therefore sum to `T ×` one period's utility, and
the frontier of the sum is `T ×` the one-period frontier. Dividing the sum back
out by `T` puts a flow island and a one-shot stock island on the same axis
rather than on two axes that merely resemble each other.

Trading intensity is matched: each flow period gets the same number of trading
rounds as the entire stock run. At anything less the flow arm looks worse for
want of rounds, which would be a finding about the budget.

## What is load-bearing

`Manager.close_period`. It is the only difference between the two models — a
stock run never calls it. Remove it and a flow island *is* a stock island, on
the same code path.

Conservation is asserted **inside** it, before anything is consumed, while the
period's books still balance exactly. The invariant is therefore as strong under
flow as under stock rather than being relaxed to accommodate eating, which is
the failure mode that would let a flow island quietly manufacture goods and beat
the frontier.

## Metrics

**Outcome.** Efficiency of the mean period against the one-period frontier;
efficiency of the first and last period separately.

Both first/last efficiency figures have a **moving denominator** — they are
medians over the islands scoreable in *that* period — so their difference is not
a convergence measurement. Convergence is tested on the zero rate instead, which
is defined on every island in every period, and tested *paired by island*,
because agent-periods within an island are not independent.

**Mechanism.** Permanent ruin (agents scoring zero in *every* period — the flow
analogue of stock ruin); the zero-period rate (agent-periods scoring zero, which
is bounded rather than terminal); and **recoveries** — zero periods followed by a
positive one. Recovery is the thing the stock model structurally cannot exhibit,
so counting it is how the two models are told apart.

Stock and flow run on the same islands under the same seeds, so every comparison
is paired and the difference is the model rather than the draw.

## Results

24 islands, 12 agents, 5 goods, 6 periods, 60 trading rounds per period. Both
models ran on every island under the same seed, so every comparison is paired.
Benchmarks: autarky floor 0.446, exchange ceiling 0.521. Intervals are Wilson at
95%.

### Permanent ruin nearly vanishes

| arm | stock ruined | flow permanently ruined | recoveries |
|---|---|---|---|
| A `silent` | 0/24 (0.00–0.14) | 0/24 (0.00–0.14) | 0 |
| B `disclose` | 0/24 (0.00–0.14) | 0/24 (0.00–0.14) | 0 |
| C `price` | **14/24 (0.39–0.76)** | **1/24 (0.01–0.20)** | 176 |
| D `money` | **18/24 (0.55–0.88)** | **0/24 (0.00–0.14)** | 162 |

Hypothesis 1 holds, and it is most of 002's ruin. The intervals do not overlap
for either priced arm.

A and B never ruin anybody under either model and record no recoveries — they
have no price, so they never specialise, so there is nothing to recover from.
That is the control working: the effect appears exactly where commitment does.

### The efficiency columns are a survivorship trap

The naive comparison — stock 0.987 against flow 0.848 for arm C — is not a
comparison. Stock's figure is the median over the **10** islands it could score;
flow's is over **23**. Paired on the same islands:

| arm | islands stock could score | stock | flow, those islands | flow, the islands stock could not score |
|---|---|---|---|---|
| C | 10/24 | 0.987 | 0.981 | **0.769** (n=13) |
| D | 6/24 | 0.946 | 0.864 | **0.744** (n=18) |

Flow changes almost nothing where the stock model already had a number. What it
does is **give a number to the islands that had none**, and those land near
0.75 — above the exchange ceiling of 0.521 and well above the autarky floor of
0.446.

That is the finding worth keeping. The islands 002 reported as ruined were not
hopeless economies. They were economies where one bad first commitment was
fatal, and they are worth about 0.75 the moment the commitment stops being
permanent.

### The arm ordering survives

Under flow the ordering is C > D > A > B, the same as under stock. 002's ladder
was not measuring the accumulation rule: `disclose` really is worse than
silence, and a shared price really is what reaches the frontier. Hypothesis 2
holds, and the weaker, more interesting alternative — that flow would reshuffle
the arms — is refused.

### Convergence: not detected, in either regime

Hypothesis 3 fails, and the route to that conclusion is the part worth reading.

**First attempt: unmeasurable, not absent.** The per-period zero rate is flat
(arm C: .194 .181 .170 .139 .205 .188), which reads as "agents do not learn".
Before reporting that, the learning channel was checked directly — and it works
*too well*. Tatonnement reaches the true equilibrium **inside period 0**, to a
relative error of 0.0013 and then 0.0000, with every agent agreeing to machine
precision. Nothing is left for a later period to learn. Convergence was not
absent; it was unmeasurable, because the channel had no work to do.

**Second attempt: starve the channel.** `discovery_rounds=1` gives one talking
round per period, so the price must be found *across* periods. The pooled zero
rate now drifts downward — arm C .674 .601 .639 .528 .573 .556 — and one island
(seed 1) shows a clean descent of 3, 4, 2, 0, 1, 0.

**That drift does not survive pairing.** Agent-periods within an island are not
independent, so the honest test is per-island: zero count in the first two
periods against the last two, sign-tested.

| regime | arm | improved | worse | tied | p |
|---|---|---|---|---|---|
| starved (1 round) | C | 10 | 6 | 8 | 0.45 |
| starved (1 round) | D | 9 | 7 | 8 | 0.80 |
| well-fed (30 rounds) | C | 8 | 10 | 6 | 0.82 |
| well-fed (30 rounds) | D | 12 | 10 | 2 | 0.83 |

Nothing significant anywhere. The pooled drift was correlated agent-periods, and
the seed-1 island that looked like clean convergence was one island out of
twenty-four, selected by eye after the fact.

**What the starved regime does show is a level effect, and a large one.**
Starving discovery is catastrophic: arm C's permanent ruin goes from 1/24 to
12/24 and its zero-period rate from 0.18 to 0.59.

So the convention's value here is entirely in **how good a price it reaches
inside an episode**, and none of it is in anything accumulated across episodes.
For the newborn-agent question that is the sharper reading: what matters is how
fast a convention converges within the episode an agent is actually in, not what
it carries between them.

## Negative results

**Convergence was measured before it was checked whether it could be.** The
first convergence number was produced from a channel that had already saturated,
and it would have been published as "agents do not learn from a shared price".
The reason it was caught is that the channel was inspected directly rather than
inferred from the outcome — the same discipline that caught the allocation
starvation in [003](../003-promotion-rules/). A mechanism has to be shown live
before its silence means anything.

**A single island looked like the result.** Seed 1 arm C under starved discovery
descends 3, 4, 2, 0, 1, 0, which is exactly what convergence should look like.
Across 24 islands the effect is absent. Kept because the temptation to report it
was real and the paired test is the only reason it was not.

**Recovery is churn, not healing.** 176 recoveries in arm C sit alongside a
zero-period rate that never falls. The flow economy reaches a *churning steady
state*: 15–20% of agent-periods score zero throughout, but it is a different
agent each time. Nobody is permanently ruined and nobody is permanently safe.

## Limitations and confounders

- **Stationarity.** Tastes and capacities never change, so a later period is the
  same problem as an earlier one. Convergence here is agents getting better at a
  fixed problem, not tracking a moving one, and a convention that helps with the
  first may be useless for the second.
- **Six periods is short.** Convergence measured over six periods says little
  about an asymptote, and an arm still improving at the last period has not
  been shown to stop.
- **The learning channel is narrow by construction.** Price beliefs persist and
  nothing else does. A richer memory — of counterparties, of what settled, of
  who defected — would plausibly change the convergence result, and its absence
  is a design choice rather than a neutral baseline.
- **Consumption is total.** Agents eat everything every period; there is no
  saving, no inventory, no buffer against a bad period. That is the cleanest
  contrast with the stock model but it is also an extreme, and a model with
  partial carryover sits between the two and was not run.
- **Six periods is too few to refuse convergence outright.** The paired test
  finds nothing, but it is a test over six periods on 24 islands and it would
  miss a slow effect. "Not detected" is what is claimed, not "absent".
- **Trading intensity matched to the stock run is a choice.** It makes each
  period a fair stock run, but it also means a flow island receives `T ×` the
  total trading rounds. The per-period frontier is the right benchmark for that,
  and it is used — but an arm that needs many rounds to converge within a period
  is being flattered relative to one that does not.

## Experimental artifacts

```
experiment/flow_experiment.py   the runner; imports 002's package deliberately
analysis/trajectory.py          per-period tables read from the record
results/stock_and_flow.json          one record per (island, arm), both models
results/stock_and_flow_starved.json  the same, at one discovery round per period
```

Tables above come from `analysis/trajectory.py` against those records.

The flow mode itself lives in 002:
[`barter/run.py`](../002-barter-conventions/experiment/barter/run.py)
(`run_island_flow`, `FlowOutcome`, `score_flow`) and
[`barter/manager.py`](../002-barter-conventions/experiment/barter/manager.py)
(`close_period`), gated by
[`tests/test_flow.py`](../002-barter-conventions/experiment/tests/test_flow.py).

## Reproduction

```bash
pip install -r ../002-barter-conventions/experiment/requirements.txt

cd experiment
python flow_experiment.py --islands 24 --periods 6 --rounds 60 \
    --json ../results/stock_and_flow.json

# The gates for the flow mode live with the code, in 002.
cd ../../002-barter-conventions/experiment && python -m pytest tests -q
```
