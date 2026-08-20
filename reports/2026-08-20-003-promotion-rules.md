# 003 Tier 1 — promotion rules

**Date:** 2026-08-20 · **Status:** run, reported · **Cost:** none (no model calls)
**Record:** [`experiments/003-promotion-rules/results/tier1.json`](../experiments/003-promotion-rules/results/tier1.json)

The experiment was designed and run in the same session. Design and prediction
were committed before the run — see commit `cce3e73` (design, PR #4) preceding
`616b7e7` (results, PR #5) — so the prediction below is pre-registered in the
weak sense that it is in the history before the numbers are, and in no stronger
sense: the same author wrote both, hours apart.

## Question

When candidate solutions to a task compete and a promoter picks a winner
automatically, what rule converges on the *good* candidate rather than the
*lucky* one — and does a candidate whose value depends on being shared need a
different rule from one whose value does not?

## What was built

A simulator of a **promoter**, not of candidates. Five (allocation, promotion)
pairs run over a stream of task instances; on each step the promoter routes
traffic across a candidate pool, observes a noisy score per invocation, and may
promote.

Candidates have **manufactured true quality** — the harness sets the mean each
candidate draws from — so "did the promoter find the best one" is a lookup
rather than an inference. This is the same instrument trick 002's Tier 3 uses
for conventions, and it is the only reason "lucky" and "good" are separable at
all.

Two payoff modes, differing in exactly one term:

- **strategy** — expected score is the candidate's true quality `q_i`
- **protocol** — expected score is `q_i · f(a_i)`, where `a_i` is the fraction of
  the population currently allocated to candidate `i`

`f` is run in two forms (`linear`, `step`) because its shape is invented and the
result should not depend on the invention. Both forms agree on every
qualitative claim below.

**Configuration.** 5 candidates, qualities drawn in `[1-spread, 1]` with
`spread=0.4`, observation noise σ=0.15, 400 steps, 20 invocations per step, 40
replications per (rule × mode × starting leader), starting leaders `worst`,
`middle`, `best`. Every rule sees the same pools under the same seeds.

## Claims

| # | claim | strength |
|---|---|---|
| 1 | On strategies, ordinary rules converge and fail by **entrenchment**, ordered by how much evidence they demand | solid |
| 2 | On protocols, `greedy` / `nmin` / `interval` **never promote**, in 120 replications each | solid |
| 3 | Those three score **identically** to `gated`, which declines to promote by construction | solid |
| 4 | Conservatism does not trade speed for accuracy — `interval` is both slower *and* less often right than `nmin` | supported |
| 5 | `bandit` is the sole exception, and the mechanism is that it never runs a split population | supported |
| 6 | Therefore protocol change cannot be delegated to a try-a-bit-then-decide promoter | supported |

### Claim 1 — entrenchment, ordered by evidence demanded

Strategy mode, starting on the worst candidate, median of 40 runs, at a **fixed
exploration share of 0.10 for every rule** — so the ordering is attributable to
the promotion test rather than to sampling.

| rule | entrenched steps | regret | found best |
|---|---|---|---|
| `greedy` | 3 | 7.1 | 38/40 |
| `nmin` | 60 | 20.3 | 39/40 |
| `interval` | 60 | 22.4 | 31/40 |
| `bandit` | 7 | 11.2 | 38/40 |
| `gated` | 400 | 99.4 | 0/40 |

### Claims 2 and 3 — the protocol result

Counting only the 80 runs per rule that did **not** start on the best candidate
(the other 40 are trivially correct and would inflate every cell):

| rule | strategy: found best | strategy promotions | protocol: found best | protocol promotions |
|---|---|---|---|---|
| `greedy` | 76/80 | 367 | **0/80** | **0** |
| `nmin` | 78/80 | 179 | **0/80** | **0** |
| `interval` | 62/80 | 112 | **0/80** | **0** |
| `bandit` | 75/80 | 91 | **75/80** | 84 |
| `gated` | 0/80 | 0 | 0/80 | 0 |

Zero promotions is not "promoted late" or "promoted the wrong one". The
mechanism is arithmetic: a challenger held at the exploration share is *scored*
at the exploration share. Under `linear` coupling at 2.5% of traffic it observes
about `q·0.025 ≈ 0.02` against a leader's ≈0.5. No quantity of evidence makes
that look better, and demanding more evidence of a crushed number yields more
evidence of a crushed number.

Claim 3 is the sharper form: under a coordination payoff, **automated promotion
and no promotion are the same policy**.

### Claim 5 — why the bandit escapes, measured not assumed

The allocations, at a step where every candidate has been sampled:

```
greedy    shares [0.9, 0.025, 0.025, 0.025, 0.025]   max share 0.90
interval  shares [0.9, 0.025, 0.025, 0.025, 0.025]   max share 0.90
bandit    shares [0.0, 0.0,   0.0,   0.0,   1.0  ]   max share 1.00
```

UCB sends a whole step to one candidate, so every trial runs at `f(1) = 1` and
the coupling never bites. Its protocol-mode regret (11.5) is essentially its
strategy-mode regret (11.2).

**This is a shape requirement, not a deployable rule.** The bandit wins by
performing a population-wide cutover on every step, and switching is free in
this harness — no migration window, no agent left on the old candidate, no
cost. That is precisely the assumption a real protocol migration violates.

## Threats to validity

Ranked by how much they would change the conclusions.

1. **Free switching.** Claim 5, and therefore the practical reading of claim 6,
   rests entirely on a zero-cost population-wide switch. Untested.
2. **Promoter and allocator are inseparable.** `bandit` differs from the others
   in *allocation*, not in its promotion test, and allocation is the whole
   result. Rules are reported as (allocation, promotion) pairs and must not be
   cited as promotion rules alone.
3. **Stationary quality.** Real candidates drift. Nothing here tests a moving
   target, and a rule that converges once may be the wrong shape for a world
   that keeps changing.
4. **`f` is invented.** Two monotone forms were run and agree. A non-monotone
   coupling was not tried.
5. **Entrenchment is partly definitional.** Measured in stream position, it is
   partly a restatement of exploration share. Mitigated by holding the share
   fixed at 0.10 across every non-bandit rule; the 3 → 60 → 400 ordering is
   therefore the promotion test. It is *not* mitigated for `bandit`, whose
   allocation differs.
6. **Claim 4 is a 40-run median comparison** with no interval computed. 31/40 vs
   39/40 is suggestive, not established.
7. **Tier 1 is a simulator of a promoter with no agents in it.** It can show a
   rule unsound. It cannot show a sound rule workable on real solutions.

## What would falsify the headline

A rule that promotes better protocols with no population-wide coordination
step. That would mean protocols are strategies with a slower learning curve and
the distinction has no operational content.

## Harness fault found and fixed

**The first run produced a complete set of confident, entirely false tables.**

With 5 candidates and a 10% exploration share, each challenger is owed 0.5 of
20 invocations. Largest-remainder allocation gave every challenger an identical
remainder and broke the tie by index, so the same two low indices took the
spare invocations on **every step of every run** — and the rest of the pool was
never sampled at all, by any rule, in any mode, for the entire stream.

The tell was the best candidate's traffic share reading exactly `0.0` while the
tables reported 0/40 correct almost everywhere.

Rotating the tie-break by one position per step was **also wrong** — it walks
the full index space rather than the contested group, leaving a 240/240/160/160
split across four challengers over 400 steps. The fix rotates within the tie
group that straddles the cutoff; spread is now ≤1 invocation in 400 steps at
every pool size tried (3, 4, 5, 7 candidates).

Two gates pin it, including one asserting the **unrotated** version still
starves, so the regression cannot return silently.

## Review targets

Ranked. Start at the top.

1. **`promotion/world.py::allocate`** — the tie-group rotation. This function
   silently decided the first run's entire result. Verify the rotation is fair
   for pool sizes and exploration shares not covered by the gates.
2. **Is `bandit` a fair comparison at all?** It is the only rule whose
   allocation is not leader-plus-exploration. If the intended comparison is
   promotion tests, `bandit` may belong in a different table.
3. **The 0/80 result** — confirm it is arithmetic and not an off-by-one in
   `Rule.challenger` that prevents promotion in protocol mode for an unrelated
   reason. The claim is strong enough that a boring bug would be embarrassing.
4. **`Stats.stderr` returns `inf` below two observations.** Check no rule
   accidentally depends on that for correctness rather than for safety.
5. Claim 4's 31/40 vs 39/40, which is reported without an interval.

## Reproduction

```bash
cd experiments/003-promotion-rules/experiment
pip install -r requirements.txt
python promotion_experiment.py --replications 40 --steps 400 --json ../results/tier1.json
python -m pytest tests -q     # 42 gates, offline
```
