# 003 — Promotion rules

**Status: Tier 1 complete.** The scripted tier is run and reported below. Tier 2
— the same promoter over real instincts — is not designed and not run.

## Question

When candidate solutions to a task compete and the winner is promoted
automatically, under what promotion rule does the competition converge on the
*good* solution rather than the *lucky* one — and does a solution whose value
depends on being shared need a different rule from one whose value does not?

The answer changes what gets built. If one rule handles both, a promoter is a
piece of infrastructure you write once. If not, then any system that promotes
solutions automatically will quietly entrench the wrong protocol while
converging correctly on strategies, and will look like it is working.

## Motivation

Lucille — the production assistant that produced
[001](../001-switchboard-coordination/) — implements each task through an
*instinct*: a solution that can be pure code, a model call, a procedure, a
delegation, or any mix. Instincts can be proposed and competed, so that whatever
is best now becomes the current leading one.

The promotion rule was never the interesting part. It should have been.
[002](../002-barter-conventions/) is where that became visible: its Tier 2 arms
are single islands, and `bound` "wins" at 0.507 against a floor of 0.448 — a
number I refuse to rank because n=1 per arm. An automatic promoter would not
have refused. It would have promoted `bound` and moved on.

That is the whole question. A promoter is a procedure for deciding when evidence
is sufficient, running unsupervised, on exactly the noisy single-run evidence a
person would decline to act on.

## Two kinds of solution

A solution's payoff either depends on how many others use it, or it does not.

- **Strategy.** Payoff depends on the world. Being right matters; being popular
  does not. Two candidates can run side by side and be compared directly.
- **Protocol.** Payoff depends on the *fraction of the population* using it. Its
  value is entirely in being shared — an unshared protocol has no content to
  fall back on.

This is the distinction 002's Tier 3 draws between conventions with a verifier
and conventions with a scorer, and it has a consequence that is easy to state
and awkward to build around:

> A strategy under competition is fine. A **protocol** under competition is not
> shared, so during its trial it underperforms the incumbent *because* it is
> being trialled — and a promoter that scores it during that window will reject
> it however good it is.

## Hypothesis

That a single promotion rule cannot serve both, and specifically:

1. On strategies, ordinary rules converge, and the interesting failure is
   **entrenchment** — a leader that is promoted receives more traffic, so its
   estimate sharpens while challengers starve on thin samples, and a genuinely
   better challenger can no longer accumulate the evidence needed to displace
   it. Entrenchment should be a function of the rule, not of the candidates.
2. On protocols, the same rules should be **systematically unable to promote a
   better candidate**, and should get *worse* as they get more careful. A rule
   that demands more evidence before switching holds the challenger at low
   adoption for longer, which is the condition that makes it lose.

What would make this wrong: a rule that promotes better protocols without any
population-wide coordination step. That would mean the coordination payoff is
weaker than the argument assumes and protocols are simply strategies with a
slower learning curve — in which case one promoter does serve both and the
distinction has no operational content.

The second clause is the one I expect to be right and would most like to be
wrong about, because it implies protocol change cannot be delegated to a
promoter at all.

## Experimental design

The candidates are not the subject. **The promoter is.**

Solutions are manufactured with *known* quality, the same trick
[002 Tier 3](../002-barter-conventions/tier3-design.md) uses for conventions: a
solution is a draw from a distribution whose true mean is set by the harness, so
"did the promoter find the best one" is checkable rather than inferred. No real
system permits this — in Lucille you never know the true ranking, which is
precisely why an entrenched wrong leader is invisible there.

**The task stream.** A sequence of instances. On each, the promoter routes
traffic across the candidate pool according to its rule, observes a noisy score
per invocation, and may promote. Nothing else moves.

**Payoff.**

- *Strategy mode*: a candidate's expected score is its true quality, independent
  of how much traffic it holds.
- *Protocol mode*: expected score is `q_i · f(a_i)`, where `a_i` is the fraction
  of the population currently on candidate `i` and `f` is increasing. `f` is a
  design choice, not a neutral substrate, so it is a reported parameter and both
  a linear and a threshold form are run.

**Conditions — the promotion rules.** Five, from careless to conservative:

| rule | promotes when |
|---|---|
| `greedy` | observed mean of a challenger exceeds the leader's |
| `nmin` | ...and the challenger has at least `n` observations |
| `interval` | the challenger's confidence interval clears the leader's |
| `bandit` | traffic allocated by an uncertainty-aware rule; promotion is a readout |
| `gated` | never promotes automatically; records what it *would* have done |

`gated` is the control. It is the person who looked at `bound` at n=1 and
declined, and it makes the cost of automation legible: every other rule is
scored against what the same evidence would have supported under a human hold.

**Tier 1 — scripted, free, replicated.** No models. Known-quality candidates,
synthetic noise, many replications per rule per mode. This is where the
promotion rules are actually compared, and it costs nothing to run wide.

**Tier 2 — real instincts, paid.** The same promoter over solutions that are
actually code, model calls, procedures and delegations. Not yet designed, and
deliberately: Tier 1 decides which rules are worth spending money on, and its
answer key does not survive the move to real solutions.

## Why this isolates the mechanism

Both modes share the promoter, the traffic accounting, the noise process, the
candidate pool and the seeds. The **only** difference is whether payoff reads
`a_i`. So a rule that converges in strategy mode and fails in protocol mode
fails because of the coordination coupling and nothing else.

Manufactured quality is what makes "lucky" separable from "good" at all. Without
it, a promoter that picks a bad candidate and a promoter that picks a good one
in a hard instance are the same observation.

## What is load-bearing

The coupling between payoff and adoption fraction. Remove it and protocol mode
*becomes* strategy mode — same code path, same rules, same convergence. If the
two modes give the same answer, the finding is that the protocol/strategy
distinction has no operational consequence for promotion, and this experiment
argued itself out of existence. That is a real possible outcome and it should be
reported as one.

## Controls

Seeds, candidate pool (count, true qualities, noise scale), task-stream length,
the `f` used in protocol mode, initial leader, and traffic accounting — all
recorded per run. Every rule sees the **same** stream under the same seed, so
differences are the rule rather than the draw.

The initial leader matters and is varied deliberately: starting on the best
candidate, the worst, and a middling one. A rule that only looks good when it
starts on a good leader has not been tested.

## Metrics

**Outcome.** Cumulative regret against always having used the best candidate.
Final-state correctness: is the promoted leader the true best. Time to first
correct promotion.

**Mechanism.** Promotion count and direction. **Entrenchment**: how long a
known-wrong leader holds after a better candidate is present. **Starvation**:
traffic share of the true best while it is not leading. **Reversal rate**:
promotions later undone, which distinguishes a rule that is unstable from one
that is stuck.

Outcome and mechanism are read separately, per the repo's standing rule. A rule
can reach the right leader and have starved it for most of the stream, which is
a correct outcome from a mechanism that would fail on a shorter run — and those
are two claims.

Nothing here rests on a self-report; a promoter's own record of why it promoted
is not evidence that the promotion was right.

## Limitations and confounders

- **The promoter and the traffic allocator are not separable.** How much a
  candidate is tried and when it is promoted are the same rule in most designs,
  and entrenchment lives exactly in that coupling. Rules are reported as
  (allocation, promotion) pairs rather than as promotion rules alone.
- **Manufactured quality is stationary.** Real instincts drift as the system and
  its inputs change, and a rule that is correct against fixed qualities may be
  wrong against moving ones. Non-stationarity is out of scope and its absence is
  a stated limit, not an oversight.
- **`f` is invented.** The shape of the coordination payoff is chosen, and the
  strength of the protocol-mode result depends on it. Both linear and threshold
  forms run; if the finding only holds for one, that is the finding.
- **Entrenchment is partly definitional.** It is measured in stream position,
  which any rule with a lower exploration rate will inflate. Reported alongside
  exploration share rather than alone.
- **Tier 1 is not a system.** It is a simulator of a promoter, with no agents in
  it. It can establish that a rule is unsound; it cannot establish that a sound
  rule works on real instincts.

## Experimental artifacts

## Results

### Tier 1 (40 pools per rule per mode per start, 400 steps, 20 invocations/step)

Regret is cumulative against the whole population having used the best
candidate for the whole stream, so lower is better and the scale is arbitrary —
only comparisons within a table mean anything. `correct` is how many of the 40
replications ended on the true best candidate.

**Strategy mode, starting on the worst candidate.**

| rule | regret (median) | IQR | correct | first correct | entrenched steps |
|---|---|---|---|---|---|
| `greedy` | **7.1** | 5.2–9.2 | 38/40 | 1 | 3 |
| `nmin` | 20.3 | 15.9–25.4 | **39/40** | 59 | 60 |
| `interval` | 22.4 | 18.3–25.5 | 31/40 | 59 | 60 |
| `bandit` | 11.2 | 10.0–12.4 | 38/40 | 6 | 7 |
| `gated` | 99.4 | 79.3–122.6 | 0/40 | — | 400 |

**Protocol mode (`linear`), starting on the worst candidate.**

| rule | regret (median) | IQR | correct | first correct | promotions |
|---|---|---|---|---|---|
| `greedy` | 153.0 | 135.2–177.5 | **0/40** | — | **0** |
| `nmin` | 153.0 | 135.2–177.5 | **0/40** | — | **0** |
| `interval` | 153.0 | 135.2–177.5 | **0/40** | — | **0** |
| `bandit` | **11.5** | 10.3–12.6 | 37/40 | 6 | 1 |
| `gated` | 153.0 | 135.2–177.5 | 0/40 | — | 0 |

The pattern holds under `protocol-step` (regret 124.2 for the four, 11.5 for
`bandit`) and from every starting point. Four rules produce **identical** regret
to three decimal places in protocol mode, because they all do the same thing:
nothing.

Both clauses of the prediction hold, and the second holds harder than
predicted.

**On strategies, the rules converge and fail by entrenchment, ordered by how
much evidence they demand.** Entrenched steps run 3 → 60 → 60 → 400 across
`greedy`, `nmin`, `interval`, `gated`. Conservatism buys nothing here: `interval`
carries *more* regret than `nmin` and is right less often (31/40 against 39/40),
because the runs where it never accumulates a distinguishable gap are runs where
it never promotes at all. The careful rule is not slower to be right; it is
sometimes never right.

**On protocols, three of the rules never promote — not once in 120
replications.** Not "promote the wrong one", not "promote late". A challenger
held at the exploration share is scored at the exploration share: at 2.5% of
traffic under `linear` coupling it observes about 0.02 against a leader's 0.5,
so no amount of evidence makes it look better, and demanding more evidence
changes nothing because more evidence of a crushed number is still a crushed
number. `gated`, which declines to promote by construction, scores **identically
to the three rules that were trying**. That equality is the cleanest statement of
the result: under a coordination payoff, automated promotion and no promotion at
all are the same policy.

**The exception is the one rule that never runs a split population.** `bandit`
is correct in 37–40 of 40 in every mode and carries essentially the same regret
in protocol mode as in strategy mode (11.5 against 11.2) — the coordination
coupling costs it almost nothing. The mechanism is visible in its allocation:

```
greedy    shares=[0.9, 0.025, 0.025, 0.025, 0.025]   max share 0.90
interval  shares=[0.9, 0.025, 0.025, 0.025, 0.025]   max share 0.90
bandit    shares=[0.0, 0.0, 0.0, 0.0, 1.0]           max share 1.00
```

UCB sends the whole step to one candidate, so every trial runs at full
adoption and `f(a) = f(1) = 1`. It is not that the bandit explores better. It is
that **it performs a population-wide cutover on every step and therefore never
pays the coordination cost at all.** The design predicted that promoting a
protocol would need a population-wide switch; the run produced one without being
asked, as the only strategy that works.

## Interpretation

What the numbers support: under a payoff that scales with adoption, promotion
rules of the try-a-bit-then-decide family do not merely underperform — they are
structurally unable to act, and the more evidence they require the more
completely the requirement cannot be met. The failure is not statistical
timidity. A trial at 2.5% adoption is not a small sample of the candidate's
value; it is an accurate measurement of a different quantity.

What they do not support: any claim that the *bandit* is the answer. Its
immunity comes from a harness in which switching the entire population costs
nothing and takes one step. That is exactly the assumption a real protocol
migration violates — versioning, in-flight requests, agents that have not read
the new spec. Read the bandit result as *what shape a working protocol promoter
has to be* (all-in, population-wide, reversible), not as a rule anyone can
deploy. Whether that shape survives a switching cost is untested and is the
first follow-up.

Nor do they support ranking `greedy` first for strategies. It wins on regret
by acting on a single observation, and the same haste shows up as churn: median
3 promotions against `nmin`'s 1, and 2 promotions even when it *starts* on the
best candidate — it demotes the correct leader on noise and finds its way back.
Low regret over 400 steps and a leader that moves on one sample are the same
behaviour, and a system with any switching cost would price them very
differently.

## Negative results

**The `gated` control is not a safety story.** It was included as the person who
looked at 002's `bound` at n=1 and declined, and the expectation was that it
would trade regret for correctness. In strategy mode it is the worst arm by a
factor of five and never right — declining to act is not conservative, it is
just wrong more slowly. Its only good showing is starting on the best candidate,
where doing nothing is optimal by construction and tells you nothing.

**Conservatism is not a dial between speed and accuracy.** The expectation was
that `interval` would be slower than `nmin` and more often correct. It is slower
and *less* often correct (31/40 against 39/40). There is no rung of the ladder
where demanding more evidence bought correctness, in either mode.

## Limitations and confounders

- **The promoter and the traffic allocator are not separable**, and this run
  shows why that matters more than expected: `bandit` differs from the others in
  allocation, not in its promotion test, and allocation is the whole result.
  Rules are reported as (allocation, promotion) pairs and should not be cited as
  promotion rules alone.
- **A population-wide switch is free here.** No switching cost, no migration
  window, no agent left on the old protocol. This is the assumption the bandit
  result rests on entirely, and it is the least realistic thing in the harness.
- **Manufactured quality is stationary.** Real instincts drift; nothing here
  tests a rule against a moving target, and a rule that converges once may be
  the wrong shape for a world that keeps changing.
- **`f` is invented.** Both a linear and a step form were run and they agree on
  every qualitative claim, which is weak evidence that the shape is not carrying
  the result — but both are monotone in adoption and a non-monotone coupling
  was not tried.
- **Entrenchment is measured in stream position**, so it is partly a restatement
  of exploration share. It is reported next to `explore` for that reason, and
  the exploration share is identical (0.1) across every non-bandit rule, which
  is what makes the 3 → 60 → 400 ordering attributable to the promotion test.
- **Tier 1 is a simulator of a promoter**, with no agents in it. It can show a
  rule unsound. It cannot show a sound rule workable on real instincts.

## Harness faults found and fixed

Kept because the first run of this experiment produced a full set of confident,
entirely false numbers.

**Exploration never reached most of the pool.** With five candidates and a 10%
exploration share, each challenger is owed 0.5 of the 20 invocations in a step.
Largest-remainder allocation gave every challenger an identical remainder and
broke the tie by index, so the same two low indices took the spare invocations
on every step of every run, and the rest of the pool was **never sampled at
all** — by any rule, in any mode, for the whole stream. The first tables read
0/40 correct almost everywhere with the best candidate's traffic share at
exactly 0.0, which is the tell. The tie-break now rotates within the contested
group, and two gates pin it: one asserting every candidate is reached and the
spread across challengers stays within 25%, one asserting the *unrotated*
version still starves, so the regression cannot come back silently.

Rotating by one position per step was not enough either — it walks the full
index space rather than the tie group and left a 240/240/160/160 split across
four challengers. Rotating within the contested group brings the spread to ≤1
invocation in 400 steps at every pool size tried.

## Experimental artifacts

```
experiment/promotion/world.py    pool, coupling, observation, allocation
experiment/promotion/rules.py    the five (allocation, promotion) pairs
experiment/promotion/run.py      one stream, and the record it leaves
experiment/promotion/report.py   medians and IQRs across replications
experiment/promotion_experiment.py   Tier 1 runner
experiment/tests/                42 offline gates; no network, no models
results/tier1.json               every record from the reported run
```

Each record carries the rule, mode, seed, start, the pool's true qualities, the
full promotion sequence with steps, and every mechanism counter.

## Reproduction

```bash
pip install -r experiment/requirements.txt

# The reported run. Seconds, no network, no model calls.
cd experiment
python promotion_experiment.py --replications 40 --steps 400 --json ../results/tier1.json

# The gates.
python -m pytest tests -q
```

## Follow-up questions

- **The bandit result is the whole follow-up.** Add a switching cost — a fixed
  charge per cutover, or a window where part of the population is still on the
  old candidate — and see whether the all-in shape survives it. If it does not,
  nothing here promotes protocols and the answer is that protocol change cannot
  be delegated to a promoter at all.
- What is the smallest safe population-wide switch: a versioned negotiation, a
  scheduled cutover, a quorum? The run says the shape is necessary; it says
  nothing about which one.
- Entrenchment ordered cleanly with evidence demanded (3 → 60 → 400 steps) at a
  fixed exploration share. Does that ordering survive varying the share, or do
  the rules converge once exploration is generous enough to make the demand
  cheap?
- 002 asks how wrong a *shared* convention can be and still be worth holding.
  This asks how a system would ever notice. The two numbers are related and it
  is not yet clear how.
