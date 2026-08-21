# 005 v2 — protocol × hint, on a coupled island

**Status: designed, unrun. Nothing here has been executed and no money has been
spent on it.** This document plus the three files in `stimuli/v2/` are the
deliverable for review.

v1 is superseded and stays in history. Its
[run report](../../reports/2026-08-21-005-deliberation-protocol.md) records why:
the task was a price-guessing game whose stated objective *was* agreement, the
manipulation had five rounds to act in, and the hint cells coordinated by
transcribing a number the prompt happened to print at three decimals. v2 changes
the world, the objective, the communication surface and both treatments.

## Questions

Three, kept separate on purpose.

- **Protocol factor.** Does a shared, domain-independent way of structuring
  conversation improve collective economic outcomes?
- **Hint factor.** Does making one structural dependency salient improve agents'
  ability to reason about the task?
- **Interaction.** Does better conversational structure make the strategic
  insight more useful, or the other way round?

## Design

2×2, crossed, paired on identical seeded worlds.

| | no hint | hint |
|---|---|---|
| **no protocol** | `baseline` | `hint` |
| **protocol** | `protocol` | `both` |

Every cell receives the **same base block**: the same world, the same private
and public information, the same decisions, the same clock, the same Switchboard
calls. Treatments are appended blocks and nothing else changes.

**No treatment enforces anything.** The protocol is advice about conversation
that nothing checks. The hint names a dependency and stops. Neither contains a
decision, and the harness never overrides, completes or corrects a production
choice, a trade, or a message.

## The world, and why it is coupled

Eight traders, four goods, one unit of labour each per period, Cobb-Douglas
tastes, per-period consumption (the flow model from
[004](../004-stock-and-flow/)). Capacities and tastes are drawn per agent and
are **private**.

Three couplings make individually-good reasoning insufficient, and they are
properties of the world rather than instructions:

1. **Coverage.** Utility is a product over all four goods. A good nobody
   produces is a good nobody can eat, and everyone's utility that period is
   zero — including the traders who chose well. No amount of private
   optimisation protects an agent from this; it is a fact about what the other
   seven did.
2. **Assignment.** Who should make what depends on comparative advantage across
   the population, and every capacity is private. The information needed to
   assign well exists only in eight separate heads.
3. **Congestion.** The marginal value of a unit of a good falls as more of it
   exists. What your labour is worth depends on how many others spent theirs
   the same way — which is decided simultaneously, not observed first.

Production is committed **before** the market opens, in a separate stage on the
clock. That ordering is what turns coupling into something communication can
act on: talk before the production stage can change what gets made; talk after
it can only redistribute what exists.

**The objective given to agents is their own summed utility.** Not agreement,
not consensus, not a price. Prices, roles, conventions and counterparties are
things agents may find useful; none of them is named as a goal.

## Communication

The public board is genuinely public: `post` is visible to all eight, permanent
and attributed. `message` is targeted. `read` returns both, tagged by sender
and channel. There is no cap on volume and no artificial peer sampling — v1's
"you see two random others per round" is gone, and with it the confound that
the harness was rationing the very thing under test.

**Knowing the tools is base, not treatment.** All four cells get the full
Switchboard surface with identical mechanics. The protocol treatment is advice
about *how to converse* with tools everyone already has.

## Metrics

### Primary — pre-registered

**Realised welfare against the per-period Pareto frontier.**

For each period, `economy.efficiency` returns a certified sandwich — a lower
bound from an achieved allocation and an upper bound from a supporting price
vector — for the island's realised holdings at the bell. The primary statistic
for a world is

```
W = mean over periods of ( efficiency_lower_bound of that period )
```

reported per world, in `[0, 1]`, with the sandwich gap carried alongside as the
honest error bar. **Higher is better and the metric is continuous**, so there is
no threshold to tune and no cut point to accuse.

Comparisons are **paired by seed**, world as the unit of analysis, exact
binomial sign test on paired differences, ties reported. The 2×2 is read as two
main effects and one interaction, each on paired differences.

Benchmarks printed with every result: the **autarky floor** (nobody trades) and
the **exchange ceiling** (the Walrasian point). A cell below the autarky floor
has agents who would have done better ignoring each other entirely, which is a
result worth being able to state.

### Secondary — pre-registered, none of them primary

- **Zero-utility periods** — count and rate, per cell. This is the coverage
  failure made visible, and it is a *failure metric with its own denominator*
  rather than a hole in the welfare average.
- **Search cost** — periods until a world first exceeds the autarky floor, and
  until it first exceeds the exchange ceiling. Reported with denominators;
  worlds that never do are counted, never dropped.
- **Trajectory** — `W` by period. Whether behaviour improves across the run is
  the closest thing here to learning, and v1 could not ask it.
- **Communication volume** — posts, direct messages, characters, per cell and
  per period. A protocol that helps by producing *less* talk is as interesting
  as one that helps by producing more.
- **Market outcomes** — offers made, accepted, declined, cancelled, expired at
  the bell. Bell expiries are counted separately from declines; conflating them
  is the defect 004 found in its own code.
- **Idle labour** — labour never committed, which distinguishes a trader who
  chose badly from one that never acted.

### Outcome classification — every world lands in exactly one

| outcome | meaning |
|---|---|
| `scored` | every agent acted every period within its stage, the run completed |
| `agent_failure` | a well-formed run in which agents did badly — including a world where nobody made salt |
| `harness_failure` | a call raised, a stage produced no submission from some agent, a malformed action, or a wall-clock overrun |

`harness_failure` worlds are **excluded from every rate and their count is
reported separately**. Timing and harness faults are logged on their own axis so
that a slow or broken run can never be read as agent behaviour — which is the
mistake 002 Tier 3 and 004 each made once.

**Nothing is scored from what an agent says.** Every metric above is read from
manager state. Self-reports are recorded in the transcript and are not
authoritative.

## Pilot gate — before any paid 2×2

Baseline cell only, unguided agents, swept over market configurations. A
configuration is **accepted** iff all four hold:

| # | criterion | test |
|---|---|---|
| P1 | not trivial | median `W` over the sweep's worlds is **≤ 0.85** of the exchange ceiling |
| P2 | not hopeless | median `W` is **≥ 1.05 ×** the autarky floor in at least **40%** of worlds |
| P3 | genuine coordination difficulty | at least **15%** of agent-periods are zero-utility, i.e. coverage actually fails sometimes |
| P4 | headroom to move | interquartile range of `W` across worlds is **≥ 0.10**, over **≥ 12** scored worlds |

P1 and P4 are the anti-saturation criteria the brief asks for. **If baseline
saturates, difficulty is raised — more goods, more heterogeneous capacities,
shorter stages, more agents — and never by weakening the agents.** Weakening
agents would change what the treatments are being tested on.

**The number of configurations evaluated is reported in sweep order with all
four criteria per row**, accepted or not. Searching for a workable task is
legitimate; searching until an effect appears is not, and publishing the whole
search is the only defence.

If no configuration is accepted, v2 stops at the pilot and says so.

## Hygiene, carried forward from 002/003/004

- Conditions paired on identical seeded worlds; the world is the unit.
- Denominators printed everywhere; failed worlds never silently dropped.
- Failure metrics defined alongside success metrics.
- Harness state scored, self-reports never.
- Timing and harness faults logged separately from agent behaviour.
- Primary metric and thresholds pre-registered before the run.
- Sensitivity reported wherever a threshold could change a conclusion. The
  primary metric is continuous and has none; the pilot criteria do, and the
  sweep table shows every configuration against every criterion.
- Treatment texts frozen and hash-pinned before the run;
  `tools/check_v2.py` fails the suite if a stimulus moves.

## Design concerns that could make the result hard to interpret

Listed because they are unresolved, not because they are handled.

1. **There is no placebo in this 2×2.** The brief specifies a bare baseline, so
   `protocol` differs from `baseline` by 355 words of advice *and* by the fact
   that advice was given at all. A positive protocol effect will not separate
   "this convention helps" from "being handed a considered-looking document
   helps". A fifth, length-matched inert cell would separate them at 25% more
   cost. **My recommendation is to add it**; the design as specified does not,
   and this is the single largest interpretive risk here.
2. **The two treatments are not length-matched to each other** (355 vs 225
   words). A main-effect difference between them is partly a difference in how
   much text arrived. The interaction term is unaffected.
3. **The hint may be discoverable within the run.** If agents work out the
   production/coordination coupling in period 1 unaided, the hint cells only
   move the discovery earlier and the effect shrinks with run length. The
   trajectory metric will show this, but it is a real threat to the hint factor
   and the pilot should be read with it in mind.
4. **Eight agents on an open board is a lot of text.** Context pressure late in
   a run is a mechanism that could produce a protocol effect for reasons that
   have nothing to do with deliberation quality — a summarising convention
   helps simply by compressing. That would be a true finding but not the one
   the question names.
5. **`W` averages over periods and can hide shape.** A world that is terrible
   then excellent scores like one that is mediocre throughout. The trajectory
   metric is reported for exactly this reason and should be read with the
   primary, not after it.
6. **Cost.** Eight agents × four stages × periods × worlds × four cells, with
   full board context, is materially more expensive than v1's 1,920 calls. The
   pilot is the place to measure the per-world price before the 2×2 is
   authorised.
