# 004 — stock and flow

**Date:** 2026-08-20 · **Status:** run, reported · **Cost:** none (no model calls)
**Records:** [`stock_and_flow.json`](../experiments/004-stock-and-flow/results/stock_and_flow.json) (well-fed discovery) ·
[`stock_and_flow_starved.json`](../experiments/004-stock-and-flow/results/stock_and_flow_starved.json) (one talking round per period)

## Origin

This experiment was **not planned**. It came from a question during review:
002's agents trade between labour instalments, but do they *consume*? They do
not. The question turned out to name the property that caps 002's whole
instrument, so it was built.

Credit where it belongs: the design change originated with the repo's author,
not with the analysis.

## Question

002 found that a shared price reaches the frontier and ruins somebody on half
its islands. Is that a fact about the convention, or about a world where a
production commitment can never be taken back?

## What was built

The flow model is a **mode inside 002**, not a fork:
`Manager.close_period()` plus `run_island_flow()`. 002's published ladder is
untouched and still reproduces, gated by test.

`close_period` is the entire difference, and a stock run never calls it. Order
matters and is not incidental:

1. Every pending proposal expires, returning escrow. Goods in escrow are goods
   nobody can eat.
2. **Conservation is asserted before anything is consumed**, while the period's
   books still balance exactly. The invariant is therefore as strong under flow
   as under stock rather than relaxed to accommodate eating — which is the
   failure mode that would let a flow island manufacture goods and beat the
   frontier.
3. Utility is read off holdings; only then are they zeroed.
4. Labour is restored. Each period is a whole economy.

**What carries across a period is only what agents have learned.** Traders are
constructed once outside the period loop and keep their price beliefs. Holdings
do not carry, labour does not, open offers do not.

That forced a rewrite the author approved in advance: 002's instalment policy
conditions on holdings (*make the valuable thing you are short of*), and with
holdings reset there is nothing to read. Under flow the convention becomes the
sole carrier of information between periods.

**Comparability.** Cobb-Douglas exponents sum to 1 on this island, so utility is
homogeneous of degree 1: `T` identical periods sum to `T ×` one period's utility
against `T ×` the one-period frontier. Dividing back out by `T` puts flow and
one-shot stock on the same axis. Trading intensity is matched — each flow period
gets the rounds the whole stock run gets.

**Configuration.** 24 islands (seeds 1–24), 12 agents, 5 goods, 6 periods, 60
trading rounds per period, arms A–D, both models on every island under the same
seed. Benchmarks: autarky floor 0.446, exchange ceiling 0.521.

## Claims

| # | claim | strength |
|---|---|---|
| 1 | Permanent ruin **nearly vanishes** under flow | solid |
| 2 | The arm **ordering survives**, so 002's ladder was not measuring accumulation | solid |
| 3 | Flow changes almost nothing on islands stock could already score; it **rescues the ones stock could not score** | solid |
| 4 | Rescued islands land near 0.75, above the exchange ceiling | supported |
| 5 | Convergence is **not detected**, in either discovery regime | refuted (H3) |
| 6 | The convention's value is in the price reached *inside* an episode, not in anything carried between them | supported |
| 7 | Recovery is **churn, not healing** | supported |

### Claim 1

| arm | stock ruined | flow permanently ruined | recoveries |
|---|---|---|---|
| A `silent` | 0/24 (0.00–0.14) | 0/24 (0.00–0.14) | 0 |
| B `disclose` | 0/24 (0.00–0.14) | 0/24 (0.00–0.14) | 0 |
| C `price` | **14/24 (0.39–0.76)** | **1/24 (0.01–0.20)** | 176 |
| D `money` | **18/24 (0.55–0.88)** | **0/24 (0.00–0.14)** | 162 |

Intervals do not overlap for either priced arm.

A and B never ruin anybody under either model and record zero recoveries — no
price, no specialisation, nothing to be caught short by. **The effect appears
exactly where commitment does**, which is what makes this a claim about
commitment rather than about the scoring change in general.

### Claim 3 — and the survivorship trap that nearly produced the opposite

The runner's own summary table invites a false reading: arm C scores 0.987 under
stock and 0.848 under flow, which looks like flow being worse. Those are
different island sets — stock's figure is a median over the **10** islands it
could score, flow's over **23**.

Paired on the same islands:

| arm | islands stock could score | stock | flow, those islands | flow, islands stock could not score |
|---|---|---|---|---|
| C | 10/24 | 0.987 | 0.981 | **0.769** (n=13) |
| D | 6/24 | 0.946 | 0.864 | **0.744** (n=18) |

The islands 002 reported as ruined were not hopeless economies. One bad first
commitment was fatal, and that is all.

### Claim 5 — the hypothesis failed twice, and the route matters

**First attempt measured a channel that had already saturated.** The per-period
zero rate is flat (arm C: .194 .181 .170 .139 .205 .188), which reads as "agents
do not learn". Before reporting that, the learning channel was inspected
directly — and it works *too well*. Tatonnement reaches the true equilibrium
**inside period 0**, to a relative error of 0.0013 and then 0.0000, with every
agent agreeing to machine precision. Nothing is left for a later period to
learn. Convergence was not absent; it was **unmeasurable**.

**Second attempt starved the channel.** `discovery_rounds=1` forces the price to
be found across periods. The pooled zero rate now drifts down (C: .674 .601 .639
.528 .573 .556) and one island — seed 1 — descends 3, 4, 2, 0, 1, 0.

**The drift does not survive pairing.** Agent-periods within an island are not
independent, so the test is per-island: zero count in the first two periods
against the last two, exact binomial sign test.

| regime | arm | improved | worse | tied | p |
|---|---|---|---|---|---|
| starved (1 round) | C | 10 | 6 | 8 | 0.45 |
| starved (1 round) | D | 9 | 7 | 8 | 0.80 |
| well-fed (30 rounds) | C | 8 | 10 | 6 | 0.82 |
| well-fed (30 rounds) | D | 12 | 10 | 2 | 0.83 |

Nothing significant anywhere. The pooled drift was correlated agent-periods, and
the clean-looking island was **one of twenty-four, selected by eye after the
fact**.

### Claim 6

Starving discovery is catastrophic in *level*: arm C's permanent ruin goes from
1/24 to 12/24 and its zero-period rate from 0.18 to 0.59. So the convention's
value is entirely in the price it reaches inside an episode.

For the newborn-agent question this is the sharper reading: what matters is how
fast a convention converges within the episode an agent is actually in, not what
it carries between episodes.

## Threats to validity

1. **Six periods is too few to refuse convergence outright.** "Not detected" is
   what is claimed; "absent" is not. A slow effect would be missed.
2. **Stationarity.** Tastes and capacities never change, so a later period is
   the same problem. Convergence here would be agents getting better at a fixed
   problem, not tracking a moving one.
3. **The learning channel is narrow by construction.** Price beliefs persist and
   nothing else does. A richer memory — of counterparties, of what settled, of
   who defected — would plausibly change the convergence result. Its absence is
   a design choice, not a neutral baseline.
4. **Consumption is total.** No saving, no inventory, no buffer. That is the
   cleanest contrast with stock and also an extreme; a partial-carryover model
   sits between the two and was not run.
5. **Matched trading intensity flatters slow arms.** A flow island receives `T ×`
   the total trading rounds. The per-period frontier is the right benchmark and
   is used, but an arm needing many rounds to converge within a period is
   favoured relative to one that does not.
6. **Claim 4's 0.75 figure** is a median over rescued islands only, and those are
   selected precisely by having failed under stock. It is not a random sample of
   anything.

## Defect found in this session's own code, and fixed

`close_period` settles open offers as `expired` so their escrow returns, and
`score_flow` computed `rejected = rejected + expired`. Offers that merely had
not been taken when the bell rang were therefore **counted as rejections**,
inflating a flow run's rejection count relative to a stock run's by
construction.

No reported finding used `rejected`, so nothing above is affected — but it would
have poisoned any later comparison. `Manager.period_expiries` now counts them
separately, `FlowOutcome.expired_at_bell` reports them, and `rejected` excludes
them. Two gates added.

*This defect was found while writing this report, not while writing the code.*

## Review targets

1. **`Manager.close_period` ordering.** The claim that the conservation
   invariant is *as strong* under flow as under stock rests on asserting it
   before consumption, after escrow returns. Verify there is no path where
   goods vanish unchecked.
2. **The homogeneity argument.** `T` periods ↔ `T ×` frontier holds because
   Σα = 1. Confirm that holds for every island `draw_island` produces, not just
   the ones sampled.
3. **Duplication between `run_island` and `run_island_flow`.** The adopter
   shuffle and trader construction are copy-pasted. They can drift.
4. **`Floor(enabled=arm != "A")`** in the flow driver uses the *island's* arm, so
   the floor is enabled even when individual traders fall back to arm A under
   partial adherence. Believed harmless — arm A traders neither post nor read —
   but it is an inconsistency worth a second opinion.
5. **The cross-experiment import.** 004 imports 002's package via `sys.path`
   insertion. Deliberate, and argued in the README, but it is the first such
   dependency in a repo that avoids shared frameworks on purpose.
6. Whether claim 7 ("churn, not healing") is better explained by the trading
   order shuffle rotating who comes up short, which would make it a harness
   property rather than an economic one.

## Reproduction

```bash
cd experiments/004-stock-and-flow/experiment
pip install -r ../../002-barter-conventions/experiment/requirements.txt
python flow_experiment.py --islands 24 --periods 6 --rounds 60 \
    --json ../results/stock_and_flow.json
python flow_experiment.py --islands 24 --periods 6 --rounds 60 --discovery 1 \
    --arms C D --json ../results/stock_and_flow_starved.json
python ../analysis/trajectory.py ../results/stock_and_flow.json

# gates live with the code, in 002
cd ../../002-barter-conventions/experiment && python -m pytest tests -q
```
