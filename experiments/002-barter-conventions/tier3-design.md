# Tier 3 — the coordination premium

**Status: the calibration half is built and run; the model half is designed and
unrun.** This is the design document for the next tier of [002](README.md). The
prediction at the end is pre-registered so that it can be wrong in public, and
nothing in it has been tested — the instrument being validated is not the
hypothesis being tested.

## Why the ladder has to go

Tiers 1 and 2 rank arms. `silent`, `disclose`, `price`, `money` — each rung adds
words *and* machinery *and* a disposition at the same time, so no gap between
two rungs is attributable to any one of them. That is why the Tier 1
non-monotonicity reads as a broken hypothesis rather than a finding: `disclose`
lands below silence and `price` reaches the frontier while ruining half its
islands, and the design cannot say which ingredient did either.

It also measures the wrong thing. Efficiency was the dependent variable, so a
good convention and a good economy were the same number. The island is a
setup, not a goal — solving it well is available at any time by computing the
equilibrium and handing it over, and that would answer nothing.

So Tier 3 stops ranking conventions and starts measuring one property of them.

## The instrument property nobody else has

`economy.walras()` returns the competitive equilibrium: a price vector, the
production shares it implies for each agent's private capacities, and a
convergence certificate. That makes this island the rare setting where a
convention can be **manufactured to a known content-quality**.

In a real system — Lucille, or any deployment — you never know whether the
incumbent convention is actually right, so "shared" and "correct" arrive
together and cannot be separated. Here they are two independent dials. That
capability, not the economy, is what the harness is for.

## Design: two axes and a dial

Every arm is a point in:

**Content quality δ.** The distance of the announced price vector from
`walras(island).prices`. `δ = 0` is exactly right. `δ` is continuous, so arms
are a sweep rather than a pair.

**Distribution.** How the vector arrives:

- *common* — announced to the island, stated as having gone to every agent
- *private* — handed to each agent alone, with no indication anyone else has one
- *absent* — no vector

The cells:

|                    | private | common |
|--------------------|---------|--------|
| **δ = 0** (correct) | CP | CS |
| **δ > 0** (wrong)   | WP | WS |
| **no content**      | `silent` | — |

Each gap is a named quantity rather than a rung:

- **CS − CP** — the value of common knowledge, content held byte-identical.
  This is the number the whole "conventions matter" claim lives or dies on.
- **CS − WS** — the value of content, coordination held fixed.
- **WS − silent** — whether a shared *wrong* belief beats no belief. Tier 1
  says uncoordinated beliefs are worse than none (`disclose` < `silent`); this
  asks whether coordinated wrong ones are still better than none.
- **WP** — the control against the boring explanation. If WP ≈ WS, agents are
  following instructions and the sharedness never mattered.

`silent` carries over unchanged from Tier 2, as the no-content floor.

## The headline number

Sweep δ for the common arms and find **δ\***, the error at which wrong-but-
shared stops beating correct-but-private:

```
eff(common, δ*) = eff(private, 0)
```

δ\* is the **coordination premium**: how wrong a convention may be and still be
worth holding, purely because everyone holds it. That is "conventions are
important" as an exchange rate rather than a slogan.

- **δ\* ≈ 0** — conventions are information transport. Sharedness is
  decoration, and the claim dies.
- **δ\* large** — a newborn agent should adopt the incumbent convention *even
  believing it substantially wrong*, with a bound on "substantially".

## Conventions, protocols, strategies

The rules in an arm are tagged rather than the arm being classified. Three
columns, and every rule in every arm gets a row:

| | enforced by | violation visible as |
|---|---|---|
| **mechanism** | the manager | impossible |
| **protocol** | a verifier on the transcript | malformed, typed, countable |
| **strategy** | nothing | only in outcomes, after the fact |

Protocols are the conventions with a verifier; strategies are the conventions
with a scorer. Enforcement is **held fixed** across all of Tier 3 — the manager
is the substrate, and varying it varies the substrate. The `told`/`built` pair
already isolates the verifier column, and carries over unchanged.

This split is what makes adoption measurable at all: protocol adoption is
checkable without the answer key, strategy adoption needs it, and the two
degrade independently.

## Adoption is the mechanism metric

Commitments move through the manager, so adoption is observable from state
rather than from self-report. Agent claims stay unscored, as everywhere in 002.

- **Protocol adoption** — a transcript verifier: quotes denominated in the
  numeraire, conformant to the board's format, referencing the announced
  vector. Typed and countable per message.
- **Strategy adoption** — the distance between the recorded `produce` split and
  the split the announced vector implies for that agent's capacities, straight
  out of `walras()`. One number per agent per island, from manager state.
- **Disposition** — adoption as a function of δ, restricted to agents whose own
  capacities contradict the announced vector. An agent that follows a
  convention its private information disputes is deferring to the group. The
  defection-rate-versus-δ curve is disposition measured rather than requested,
  which is what the `money` clause has been asking for in prose.

Every arm then lands in the quadrant the repo's own rule demands — mechanism
separately from outcome:

|                 | outcome moved | outcome didn't |
|-----------------|---------------|----------------|
| **adopted**     | the convention did the work | **dead convention** — worked as designed, moved nothing |
| **not adopted** | confound: something else moved it | null, correctly |

No Tier 2 arm can currently be placed in this table. That is the sharpest
statement of what was missing.

## What the tiers become

**Tier 1 — instrument calibration, not a parallel result.** Scripted traders
already carry a price belief (`Trader.price`) and a rule for producing against
it (`_book`, `production_plan`). Seed that belief with a perturbed `walras`
vector, skip tatonnement, and add an adherence parameter. That yields
`eff(δ | full adoption)` as a replicated curve across islands, for free. It is
the answer key for the answer key.

**Tier 2 — models.** Measures the two things scripts cannot: **adoption(δ)**,
and the gap between observed efficiency and the calibrated curve *at the
observed adoption level*. That gives the decomposition:

```
observed shortfall = calibrated loss from δ
                   + loss from partial adoption
                   + residual (harness)
```

The harness counters already recorded are the third term. Tier 2's settlement
catastrophe stops contaminating the finding and gets subtracted, per the
existing doctrine that harness counters exist to be subtracted.

**Words, machinery, disposition** finally separate into three measurements
instead of three ingredients of one rung:

| claim | measured by |
|---|---|
| words | CP vs `silent` — content moves behaviour with no coordination and no enforcement |
| machinery | the `told`/`built` pair applied to the announced vector — validation on/off, content and distribution byte-identical |
| disposition | the defection-versus-δ curve |

## The newborn claim, made literal

A newborn agent's alternative to adopting a convention is deriving one, and
derivation has a price in turns and tokens that the record already carries. So:

```
newborn value = utility(adopt blind) − utility(derive alone) − derivation cost
```

CP vs `silent` measures the derivation burden. CS − CP measures what the newborn
gets additionally from everyone *else* having been born into the same thing. If
CS − CP is the larger term, the original intuition holds in its strong form:
what a newborn needs is not the right answer but the *same* answer.

## Switches

Tier 3 adds to `llm.Telling` rather than replacing it. Existing switches keep
their meaning and their dependencies.

| switch | what it does |
|---|---|
| `announced` | a price vector is handed to the agent at the start |
| `common` | the announcement states that every agent received this vector. Requires `announced` |
| `delta` | perturbation magnitude applied to `walras` prices. Not a boolean — recorded as a float in the switch vector |
| `delta_dir` | direction of perturbation: toward specialisation, or toward autarky |

The existing dependency rule applies: `common` without `announced` is
incoherent and should raise rather than run. The arms above are combinations —
CS is `announced + common + delta=0`, WP is `announced + delta>0`.

## Confounders

- **Detection.** An agent may notice the vector is wrong, because its own
  capacities contradict it. That is not a bug — it is the disposition
  measurement — but δ must be perturbed in directions that are partially
  detectable, and detectability recorded per agent as a flag. Haiku may detect
  nothing, flattening the disposition curve into pure obedience. That is a
  model-capability result worth having, and must be reported as one rather than
  as a disposition finding.
- **Common knowledge by assertion.** "Everyone received this" is a harness
  claim the agent must trust. The harness is trusted infrastructure, so this is
  acceptable — but it means CS measures *believed* common knowledge. If
  CS ≈ CP, check the transcripts for whether agents acted on the sharedness at
  all before concluding sharedness is worthless.
- **Perturbation direction.** A δ-wrong vector still pointing toward
  specialisation is a different object from one pointing toward autarky. Both
  directions run, reported separately. A single scalar δ hides this, which is
  why `delta_dir` is its own switch.
- **Obedience versus convention.** WP is the main control, but instruction-
  following is a specific pressure on model agents. Vary the framing of one arm
  at fixed δ — "we suggest" against "the island uses" — to size it.
- **Cobb-Douglas cliffs.** Unchanged from Tier 2. Ruin is reported separately
  and never averaged in.
- **δ is not a welfare distance.** It is a distance in price space; the
  efficiency cost of a given δ is what Tier 1 calibration measures rather than
  assumes. Do not read δ as "how much worse this convention is".

## Prediction, pre-registered

**δ\* > 0, and the common-arm curve cliffs rather than slopes.** Sharedness buys
real tolerance for error, and then punishes excess error harder than privacy
does, because agents specialise more confidently on a shared error than on
private doubt.

- Wrong in the first clause → conventions do not matter here, and the claim
  that opened 002 is dead.
- Wrong in the second → conventions are free after all, and Tier 1's "the
  convention adds leverage, not safety" was specific to that mechanism rather
  than general.

Either outcome is worth the run. The one that would make the tier
uninterpretable is adoption near zero across every arm, which is a harness
result and should be caught by Tier 1 calibration before any model is paid for.

## The instrument, as built

The calibration half is implemented and runs offline:

```
experiment/barter/calibrate.py       manufacture a convention of known quality
experiment/calibrate_experiment.py   the delta x adherence sweep
experiment/tests/test_calibrate.py   21 gates on the measuring stick itself
results/tier3_calibration.json       every record from the sweep
```

`announce(island, delta, direction)` perturbs `walras()` prices and returns the
announced vector, the equilibrium it came from, the **realised** relative
distance, and the production split the vector implies for each agent — the
answer key strategy adoption is scored against once models are on the island.

Two perturbation directions, because one scalar hides the difference and they
are not the same mistake:

- **`flatten`** pulls prices toward their common mean. At `delta = 1` every good
  is priced alike, which is what an agent that never heard a price believes — so
  this direction runs the convention continuously down to *no convention*.
- **`sharpen`** widens the spread. The ranking of goods stays correct; the
  vector overstates how much better the best one is, so agents specialise harder
  than the island can support. Tier 1 already showed specialisation is a
  commitment whose downside is total, so this direction should hurt
  asymmetrically.

`delta` is a knob, not a distance — the same value means different things in the
two directions and on different islands — so every record carries the realised
distance next to it and a curve can be read against either.

**Held fixed.** An announced price makes the agent skip discovery, so
tatonnement cannot walk the vector back toward equilibrium and quietly undo the
perturbation. Everything else is arm C untouched: the specialisation rule, the
acceptance test, the proposal search, the manager. The price's provenance is the
only thing that moved.

**Adherence** hands the announcement to a seeded shuffle of the agents rather
than a prefix by index, so partial adoption is not confounded with whatever the
island's agent ordering correlates with. A non-adopter falls back to arm A — no
announced price, no floor, no specialisation — which is what "did not adopt the
convention" has to mean for the number to measure anything.

### Validation

At `delta = 0` with full adherence the instrument reaches efficiency **1.0** and
ruins **7/12**, against the published discovered-price arm C at **0.997** and
**6/12**, on the same islands (`seed0 = 1`, matching `barter_experiment.sweep`).
The gap is exact-versus-discovered prices and runs in the expected direction:
handing agents the equilibrium exactly makes them specialise harder than
tatonnement's approximation does, which buys the last 0.003 of efficiency and
costs one more ruined island. An instrument that did *not* reproduce arm C's
shape at delta 0 would be measuring something else.

### The calibration curve

48 islands per cell, full adherence, both directions, seeds 1–48. Benchmarks
for this island set: autarky floor 0.437, exchange ceiling 0.520.

| δ | realised error | flatten survived | sharpen survived |
|---|---|---|---|
| 0.0 | 0.000 | 23/48 (0.34–0.62) | 23/48 (0.34–0.62) |
| 0.05 | ~0.019 | 19/48 (0.27–0.54) | **7/48 (0.07–0.27)** |
| 0.1 | ~0.039 | 18/48 (0.25–0.52) | 6/48 (0.06–0.25) |
| 0.2 | ~0.078 | 7/48 (0.07–0.27) | 5/48 (0.05–0.22) |
| 0.3 | ~0.116 | 9/48 (0.10–0.32) | 1/48 (0.00–0.11) |
| 0.5 | ~0.19 | 3/48 (0.02–0.17) | 0/48 (0.00–0.07) |
| 0.75 | ~0.28 | 0/48 (0.00–0.07) | 0/48 |
| 1.0 | ~0.37 | 0/48 (0.00–0.07) | 0/48 |

Survival is islands where nobody was ruined; intervals are Wilson at 95%.

Three things, and the first invalidates the readout the design originally
asked for.

**Efficiency carries no signal about δ.** Across the entire sweep — every
delta, both directions, 121 surviving islands — survivor efficiency has median
0.972 and range 0.741–1.000. It is 0.978 at δ=0 and 0.998 at δ=0.3 sharpen,
where a single island survived. Survivors are always near the frontier,
because an island that manages to give every agent every good was coordinated
enough to trade well whatever the price said. **The whole effect of content
error is on whether an island survives at all**, and it is binary.

So `eff(·)` in the δ\* definition above has to be read as survival, not as
efficiency. Written as an efficiency comparison, δ\* would be estimated from a
line that does not move.

**The failure is a cliff, not a slope — the pre-registered shape, in the wrong
variable.** The prediction was that the common-arm curve would cliff rather
than slope. It does: survival goes 23 → 19 → 18 → 7 and then to zero, with
non-overlapping intervals across the drop. But the prediction expected that
cliff in efficiency, and efficiency is exactly where it is not.

**The two directions are not the same mistake, and the gap is at small
errors.** At a matched realised error of 0.019, flattening leaves 19/48 alive
and sharpening 7/48, intervals barely touching. By an error of 0.078 both are
near-dead and the distinction is gone. So overstating how much better the best
good is destroys islands at a perturbation an agent would struggle to notice,
while understating the spread degrades them gracefully over an order of
magnitude more error. That is Tier 1's "the convention adds leverage, not
safety" on a continuous dial: leverage is asymmetric, and it is the
specialise-harder direction that carries it.

### What the baseline says about the harness

At δ=0 — the exactly correct convention, fully adopted — only **23 of 48
islands survive**. Half the islands are ruined by a convention with no error in
it at all.

That is not a δ effect and it caps what this instrument can measure: the whole
curve runs from 48% survival to 0%, and half the damage is present before the
perturbation starts. The cause is structural. Holdings accumulate for the whole
run and are scored once at the end, so a production bet that misses is
permanent — a good an agent never made in the first instalment is still missing
at the last, and Cobb-Douglas zeroes on it. There is no consumption step and no
recovery.

A repeated-flow version of the island — goods consumed each period, utility
summed across periods — would bound that: a bad period would cost one period's
utility instead of the run, ruin would stop being terminal, and the outcome
measure would regain the dynamic range this one lost. It would also make a
convention's value measurable as a *rate* — how fast a population converges on
good decisions — rather than only as a level. That is a different experiment
and it would not inherit these numbers; the stock/flow difference would itself
be a finding about whether irrecoverable commitment was doing the work all
along.

### What this tier cannot measure

A scripted trader has no beliefs about other agents. Announcing a vector *to the
island* and handing the same vector *privately* therefore produce byte-identical
behaviour, at every delta.

So the CS − CP gap — the value of common knowledge with content held fixed,
which is the entire claim about sharedness and the reason the tier exists — is
**not measurable by scripts at all**. Tier 1 calibrates the content axis and the
adherence axis. The distribution axis is irreducibly a model-tier question, and
no amount of scripted replication substitutes for it. That is a sharper division
of labour between the tiers than the design above assumed, and it is worth
stating before any money is spent: the paid tier is not a more realistic version
of the free one, it is the only place one of the three axes exists.

## What this does not do

It does not test enforcement. Auctions, clearing rules, and anything else that
removes a decision from the agent are deliberately out: the manager is held
fixed as substrate, and an arm that varies enforcement varies the thing
everything else is measured against.

It does not fix the Tier 2 settlement problem, which is still open and still
harness. The [open questions](README.md#follow-up-questions) about escrow
release and counterparty visibility are prerequisites for the Tier 2 half of
this design; the Tier 1 calibration half is free and runnable now.
