# 003 — Promotion rules

**Status: designed, not run. Nothing below is a result.** The design and the
pre-registered prediction are here; there is no code and no data yet.

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

```
experiment/    the promoter, the two payoff modes, the rules, the runner
results/       one JSON per run, kept whole
analysis/      the comparison across rules and modes
```

Nothing here yet.

## Follow-up questions

- If protocol promotion needs a population-wide switch, what is the smallest
  rule that performs one safely — a versioned negotiation, a scheduled cutover,
  a quorum?
- Does an entrenched wrong leader ever recover without exploration being forced,
  or is forced exploration the only exit?
- 002 asks how wrong a *shared* convention can be and still be worth holding.
  This asks how a system would ever notice. The two numbers are related and it
  is not yet clear how.
