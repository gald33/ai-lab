# 002 — Barter conventions

**Status: running. Tier 1 is complete; Tier 2 is mid-flight and the harness is
still moving under it; [Tier 3](tier3-design.md) is designed and unrun.** The Tier 1 ladder below is a result. The Tier 2 numbers
are recorded honestly but most of them measure the harness, and the section that
says which is the point of publishing them at all.

## Question

Does a shared convention for talking about value make a group of agents better
off — and if so, which part of the convention does the work: the words, the
machinery that enforces them, or the disposition they ask for?

The answer changes what you build. If words are enough, coordination is a
prompting problem. If the machinery carries it, it is an infrastructure problem
and the prompt is decoration.

## Motivation

Switchboard ([001](../001-switchboard-coordination/)) asked whether coordination
improves because agents reason harder or because good primitives leave them less
to reason about. That experiment measured agents sharing a codebase, where
"better coordination" is hard to define independently of the task.

An economy has an answer key. Given capacities and tastes, the Pareto frontier
is computable, so "how much did they leave on the table" is a number rather than
a judgement — and it is the same number whatever the agents said to each other.

## Hypothesis

That the ladder is monotone: each rung adds to the one below it and does at
least as well. Specifically, that a shared unit of account beats free
conversation, machinery beats prose, and a medium of exchange beats a common
price because it removes the double coincidence of wants.

What would make me wrong: a rung that *lowers* welfare. That would mean the
convention is not free — that it costs something to adopt, or commits agents to
production decisions that only pay off if everyone else honours it.

## Experimental design

An island of `n` agents and `m` goods. Each agent has private Cobb-Douglas
tastes and private Ricardian capacities, and one unit of labour. It calls
`produce` to split that labour across goods, then trades. Its score is the
product of its final holdings raised to its taste exponents — so a good it holds
none of scores zero, however much of everything else it has.

Trade is two-phase and only the manager moves quantities: a buyer proposes,
which escrows the buyer's side immediately, and the named seller approves.
Nothing else can change a holding, so an island that finished above the frontier
would be a bookkeeping bug rather than a finding.

**Tier 1 — scripted, free, replicated.** Hand-coded traders, no models. Four
arms, twelve islands each, twelve agents, five goods.

| arm | what it adds |
|---|---|
| A `silent` | no communication at all |
| B `disclose` | agents publish their own valuations |
| C `price` | ...and agree one price vector |
| D `money` | ...and accept the numeraire past the point of wanting it |

**Tier 2 — models, paid, n=1.** The same island, the same scorer, the same
benchmarks, with Claude agents in place of the scripts. Seven arms, from
`silent` (no channel) to `paid` (numeraire, quote board, medians, staleness,
money clause, and a `pay` tool that prices at the board median).

Everything an agent is told is an independent switch — seventeen of them,
covering the prompt paragraphs, the tool surface and each sentence of the turn
note. The named arms are combinations, pinned by test, so a result can be
attributed to a switch rather than to a rung.

## Why this isolates the mechanism

`told` and `built` share a system prompt **byte for byte** and differ only in
whether the convention has machinery — a quote board with validation and
aggregation. That pair is the whole design: everything else on the ladder varies
words and machinery together, and only this one holds the words fixed.

The scorer is distribution-neutral by construction. Efficiency is a ray measure:
the factor θ by which every agent's utility could be scaled and still be
feasible. It says nothing about who got what, so an arm cannot score well by
concentrating gains.

## What is load-bearing

The manager. Every quantity moves through one state machine that enforces
non-negativity, conservation, and two-phase settlement, checked after every
round. Remove it and agents keep their own balances, at which point an agent can
report a trade that never happened and the frontier stops meaning anything.

## Controls

Model (`claude-haiku-4-5-20251001`), island seed, agent count, goods count,
round count, tool budgets, and the full switch vector, all recorded per run.
Tier 1 is seeded and replicated; Tier 2 is n=1 per arm and is not.

Two benchmarks bracket every island, computed from the island itself rather than
from any run: the **autarky floor** (nobody trades) and the **exchange ceiling**
(trade perfectly, but produce as if alone). An arm above the ceiling changed what
got *made*, not just who held it.

## Metrics

**Outcome.** Efficiency against the frontier; how many agents finished below
their own autarky; the median agent's multiple of its own autarky; whether
anyone was ruined outright.

Utilities are Cobb-Douglas and therefore not interpersonally comparable, so
every fairness number is a ratio to that agent's *own* counterfactual, never a
sum across agents.

**Mechanism.** Trades proposed, settled, expired, cancelled; crossed offers and
how they resolved; idle labour; messages and quotes posted.

**Harness.** Windows no agent got into, turns cut at a deadline, turns held
back, sweeps applied, and how many schedules the muster took. These exist to be
subtracted: a settle window an agent never reached is the harness losing a trade,
not a trader declining one, and they score identically without this.

Agent self-reports are never scored. One trader announced on the floor that it
had approved a trade the manager had refused; the manager's record is what
counts.

## Results

### Tier 1 (12 islands per arm, complete)

| arm | median efficiency | islands with someone ruined |
|---|---|---|
| A `silent` | 0.476 | 0/12 |
| B `disclose` | 0.457 | 0/12 |
| C `price` | **0.997** | **6/12** |
| D `money` | 0.872 | **10/12** |

Autarky floor 0.405, exchange ceiling 0.493 (medians).

The ladder is **not** monotone and the hypothesis is wrong in a specific way.
`silent` trades almost perfectly and still lands at the exchange ceiling,
because it never changes what it *makes* — trading skill is not the binding
constraint, knowing what to produce is. `disclose` does worse than silence:
publishing valuations without an agreed reading gives every agent a slightly
different price, so they specialise on beliefs that do not match and then cannot
trade with each other. Talking is not free.

`price` reaches the frontier exactly when it works and ruins somebody half the
time. That is the finding worth keeping: a shared price is what turns disclosure
into specialisation that pays, and specialisation is a commitment, so when
settlement then fails the loss is total rather than small. The convention does
not add safety; it adds leverage.

### Tier 2 (n=1 per arm, seed 41, 4 agents, 3 rounds)

| arm | efficiency | settled | cost |
|---|---|---|---|
| `paid` | 0.372 | 1/23 | $2.85 |
| `spend` | 0.371 | 4/20 | $2.60 |
| `bound` | **0.507** | 6/26 | $3.04 |
| `built` | 0.397 | 6/25 | $2.59 |
| `told` | 0.392 | 3/20 | $2.93 |
| `free` | 0.457 | 7/27 | $2.87 |
| `silent` | 0.374 | 0/18 | $2.21 |

Floor 0.448, ceiling 0.539. Only `bound` and `free` clear the floor; the rest
left their agents worse off than never trading.

### Tier 2 harness probes (single arm, `paid`, seed 41, 3 agents, 1 round)

Three islands isolating one harness change each, so they compare to each other
directly. Floor 0.626, ceiling 0.713.

| shape | efficiency | settled | missed | cut | held | cost |
|---|---|---|---|---|---|---|
| muster, three 60s windows | 0.540 | 1/7 | 2 | — | — | $0.74 |
| + batched tools, 60/150/150, hard deadline | 0.546 | 0/7 | 1 | 0 | 3 | $0.80 |
| unstaged, one 300s window | ruined 1 | **2/17** | 0 | 0 | 3 | $0.63 |

The mechanical numbers improve monotonically and the economic ones do not. By
the third the harness has stopped being the story: nothing missed, nothing cut,
volume up 2.4×, first settlements — and the island fails on its own terms, with
all three traders producing the same good.

### Tier 2 at minimum size (seven arms, 3 agents, 1 round)

$4.48, floor 0.626, ceiling 0.713. **Every arm finished below the floor.**
Diagnostic rather than comparative: it made the settle-window starvation
countable, and the count is the reason the shape changed.

| arm | settle turns | agents who got one | settled |
|---|---|---|---|
| `paid` | 1 | 1/3 | 0/6 |
| `built` | 1 | 1/3 | 0/8 |
| `bound` | 2 | 2/3 | 0/5 |
| `free` | 2 | 2/3 | 2/8 |
| `told` | 3 | 3/3 | 2/4 |
| `spend` | 4 | 2/3 | 2/7 |
| `silent` | 5 | 3/3 | 2/11 |

Both islands where all three agents reached the settle window settled trades;
two of the three where only one did settled nothing.

**These are not yet evidence about conventions.** Settlement is catastrophic
across every arm — one to seven trades of twenty-odd proposed — and the causes
found so far are all harness:

- Escrow is taken at propose time and held, so an agent with offers open is
  illiquid and cancels its own to get back under the wall. Fifteen of twenty-
  three went that way in one island.
- `want` names a quantity only the seller can see, so a proposal can be
  unsettleable the moment it is written.
- Windows were equal and turns are not. A production turn runs 18–33 seconds and
  a trading turn 68–169, against sixty-second windows, so every trading turn
  outlived the window it began in. `silent` spent 84% of its turns in a window
  where the only available action can be taken once. **Fixed** by the probes
  above — batched tools, unequal windows, a hard round deadline — which is why
  the seven-arm tables were not re-run against them: the fix arrived after the
  sweeps and the sweeps have not been repeated.

The first two are open. Until they are closed the ladder is measuring the
mechanism, and the seven-arm orderings above should be read as "no arm has
demonstrated it can clear the floor reliably" rather than as a ranking.

## Negative results

**The muster changed nothing.** Publishing the full schedule in absolute times
and requiring every trader to acknowledge it before anything opened worked
exactly as designed — one attempt, all acked, nobody absent — and the settlement
rate did not move. It was built to fix agents missing windows they were never
told about; the timestamps then showed nobody was missing windows for that
reason.

**Staging the round made things worse.** Opening produce, then offer, then
settle was meant to let traders deliberate before committing. They do not
deliberate separately: the offers *are* the negotiation, so withholding offering
withheld the negotiating. Worse, a turn spans windows, so a trader that decided
at t=150 to approve was refused because approving opened at t=210, announced on
the floor that it had approved, and never got another turn.

**Unstaging fixed the mechanics and not the island.** Everything open for one
five-minute window: volume up 2.4× and the first settlements. Then all three
traders announced they were producing grain, all three did, and one finished
holding zero of three goods — score zero. One of them had asked *"What are you
producing?"* in the same turn it committed its entire unit of labour, because
everything opens at once now. So the original instinct was right about the need
and wrong about the remedy: deliberation does have to precede commitment; what
broke things was staging the *trading*.

## Tier 3 — the coordination premium

Designed, not run: [tier3-design.md](tier3-design.md).

The ladder is retired. Tiers 1 and 2 vary words, machinery and disposition
together, so no gap between rungs is attributable to any one of them — which is
why the Tier 1 non-monotonicity above reads as a broken hypothesis rather than a
finding. Tier 3 replaces the ranking with a measurement, using the one property
this island has that a real system does not: `walras()` computes the
equilibrium, so a convention can be **manufactured to a known content-quality**
and its correctness varied independently of whether it is shared.

Two axes — content error δ from the true price vector, and distribution (common
knowledge, private, absent) — give four cells whose gaps are named quantities:
the value of sharedness with content held fixed, and the value of content with
sharedness held fixed. The headline number is δ\*, the error at which a
wrong-but-shared convention stops beating a correct-but-private one. That is the
coordination premium, and it is what "conventions are important" reduces to when
it is made falsifiable.

Efficiency stops being the goal and becomes an instrument: adoption is measured
from manager state, and welfare only says whether adoption mattered. Enforcement
is held fixed throughout — the manager is substrate, not an arm.

## Limitations and confounders

- **Tier 2 is n=1 per arm.** One island is an anecdote. The Tier 1 spread across
  twelve islands is wide enough that single Tier 2 islands cannot be ranked.
- **A turn is 174–230 seconds and a window is 300**, so each agent acts once per
  round. There is currently no revision loop at all in the unstaged shape.
- **Model is Haiku 4.5 throughout.** The Tier 1 finding is that knowing what to
  produce binds harder than trading skill; a stronger model might move exactly
  that.
- **The escrow rule is a design choice, not a neutral substrate.** One-sided
  escrow makes a proposal a commitment, which is what makes a posted price
  binding — and it is also directly responsible for the cancellation rate. The
  arms cannot currently be separated from it.
- **Cobb-Douglas zeroes hard.** An agent that never acquires some good scores
  zero, so a single failed settlement can dominate an island's number. Reported
  as `ruined` rather than averaged in, but it makes the variance large.

## Experimental artifacts

```
experiment/barter/          the economy, the manager, the flow, the arms
experiment/barter_experiment.py       Tier 1 runner (scripted, free)
experiment/barter_llm_experiment.py   Tier 2 runner (models, paid)
experiment/tests/           130 offline gates; no network, no model calls
results/                    one JSON per run, kept whole
results/README.md           what each record is, and which measure the harness
```

Each Tier 2 record carries the full switch vector, both efficiency brackets,
both benchmarks, per-agent gain ratios, the manager's summary and rejections,
every floor message, the quote board, the per-round trajectory, the harness
counters, and the whole transcript with per-turn start times and durations. An
island costs money, so anything anyone later wants should be recoverable from
the record rather than by re-running it.

## Reproduction

```bash
pip install -r experiment/requirements.txt

# Tier 1: scripted, free, seconds.
python experiment/barter_experiment.py --agents 12 --goods 5 --islands 12

# Tier 2: models, paid. Prints the bill before spending it.
python experiment/barter_llm_experiment.py --arms told built \
    --agents 4 --rounds 3 --window 60 150 150 --muster \
    --seed 41 --json results/out.json

# The gates, which drive the whole harness with a stand-in model.
python -m pytest experiment/tests -q
```

Wall clock is exact: rounds × the sum of `--window`, plus the muster lead.

## Follow-up questions

Several of these are now folded into the [Tier 3 design](tier3-design.md); the
escrow and visibility items remain prerequisites for it.

- Does deliberation-before-commitment survive if only *production* is staged and
  trading is left open throughout? That is the shape the negative results point
  at and it has not been run.
- Escrow released on a failed cover-check rather than held, and some way to see
  what a counterparty holds. Both are testable against Tier 1 for free, and
  until they are, the Tier 2 ladder is measuring the mechanism rather than the
  conventions.
- Tier 1 says knowing what to produce binds harder than trading skill. Does that
  survive a stronger model, or is it a Haiku result?
- `price` reaches the frontier and ruins half its islands. Is there a convention
  that keeps the specialisation and bounds the downside — insurance, staged
  commitment, a settlement guarantee?
