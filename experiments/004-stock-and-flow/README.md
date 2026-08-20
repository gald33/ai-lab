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
beliefs. Arm C's tatonnement therefore continues across periods, so a later
period starts from a better price than the first did. **That is the only channel
between periods**, which is what makes "does a convention help agents converge"
a question this island can answer at all.

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
efficiency of the first and last period separately, whose gap is convergence.

**Mechanism.** Permanent ruin (agents scoring zero in *every* period — the flow
analogue of stock ruin); the zero-period rate (agent-periods scoring zero, which
is bounded rather than terminal); and **recoveries** — zero periods followed by a
positive one. Recovery is the thing the stock model structurally cannot exhibit,
so counting it is how the two models are told apart.

Stock and flow run on the same islands under the same seeds, so every comparison
is paired and the difference is the model rather than the draw.

## Results

See [results/stock_and_flow.json](results/stock_and_flow.json); the tables below
come from [analysis/trajectory.py](analysis/trajectory.py) against that record.

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
- **Trading intensity matched to the stock run is a choice.** It makes each
  period a fair stock run, but it also means a flow island receives `T ×` the
  total trading rounds. The per-period frontier is the right benchmark for that,
  and it is used — but an arm that needs many rounds to converge within a period
  is being flattered relative to one that does not.

## Experimental artifacts

```
experiment/flow_experiment.py   the runner; imports 002's package deliberately
analysis/trajectory.py          per-period tables read from the record
results/stock_and_flow.json     one record per (island, arm), both models
```

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
