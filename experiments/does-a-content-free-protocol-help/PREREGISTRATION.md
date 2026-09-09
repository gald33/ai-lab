# 005 — pre-registration

Frozen in the same commit as the stimuli. Nothing in this file may be revised
after the pilot runs; a revision is a new document with a new commit and the old
one stays in history.

## Frozen stimuli

| file | sha256 | words |
|---|---|---|
| `stimuli/protocol.md` | `4bf17f65050426f61f8574d4b35f76915443219181e3c22ae1008f1ba56f0b65` | 251 |
| `stimuli/placebo.md` | `f12ef1211bb80488c9df71b8d012fa15f01dc90f042b49b8b05f3ee024ec8fba` | 240 |

Matched on length (251 / 240 words; 1423 / 1400 bytes), on register (second
person, five numbered imperatives, a closing two-sentence remark), and on
apparent authorship. The placebo contains no instruction about proposing,
objecting, agreeing, converging, stopping, or anything else another agent does.

`tools/check_stimuli.py` recomputes both hashes and fails if either file has
moved. It runs in the gates, so an edit to a stimulus breaks the suite rather
than silently changing the experiment.

## Primary metric — frozen

**Coordination rate**: the fraction of worlds in which the population
*coordinates*, where a world coordinates iff, at any round `r` within the
budget, the dispersion of the agents' submitted positions falls to or below

```
D(r) = max over pairs (i, j) of  ||p_i(r) - p_j(r)|| / ||p_bar(r)||   <=   TAU
TAU = 0.10
```

`p_i(r)` is agent `i`'s submitted position at round `r`, normalised with the
numeraire pinned at 1 exactly as `barter.calibrate.normalise` does. `p_bar` is
the componentwise mean. The **maximum** pairwise distance, not the mean: one
agent acting on a different claim is the failure the protocol is meant to
prevent, and a mean would let it average out.

`TAU = 0.10` is the pre-registered threshold. **A sensitivity curve over
`TAU` in {0.02, 0.05, 0.10, 0.15, 0.20, 0.30} is reported with every
coordination rate**, and the headline is always the `0.10` row.

Coordination is *agreement*, not correctness. Correctness is metric 2.

## Secondary metrics — frozen

2. **Regret** against the computable per-episode optimum: `1 - U/U*`, where
   `U*` is the utility the world's Walrasian equilibrium delivers. A world can
   coordinate on something bad; this is where that shows.
3. **Rounds to coordination**, over coordinating worlds only, **always reported
   with its denominator**.

## Pilot acceptance band — frozen, and fully operational

The pilot runs unguided worlds only. A market configuration is **accepted** iff
all four hold. No configuration is accepted on judgement.

| # | criterion | test |
|---|---|---|
| P1 | not hopeless, not trivial | coordination rate at `TAU=0.10` lies in `[0.15, 0.60]` |
| P2 | not instantaneous | at most **40%** of *coordinating* worlds coordinate at round <= 1 |
| P3 | not pinned at the ceiling | at most **40%** of *coordinating* worlds coordinate in the final quintile of the round budget |
| P4 | genuine spread | the interquartile range of rounds-to-coordination over coordinating worlds is **>= 2 rounds**, and at least **8** worlds coordinate so the IQR means something |

P2–P4 replace the phrase "visible spread", which was a judgement call and is
now three numbers. P4's `n >= 8` floor exists because an IQR over three worlds
is not a spread.

**Reported whether or not a configuration is accepted:** the total number of
configurations evaluated, in sweep order, with all four criteria per row. The
sweep grid is fixed in `pilot_experiment.py` before the run. Searching for a
workable task is legitimate; searching until an effect appears is not, and
publishing the whole search is the only defence.

If no configuration is accepted, 005 stops at the pilot and reports that.

## Diagnostic logging — frozen

002 Tier 3 found that half its islands died before the manipulation started, and
004 found a channel that had already saturated. Both were harness facts wearing
an agent's clothes. Every world therefore records, and every failure is
classified into **exactly one** of:

| outcome | meaning |
|---|---|
| `coordinated` | `D(r) <= TAU` at some round |
| `agent_failure` | every agent submitted a well-formed position every round, the clock never ran out early, and dispersion simply never fell — the population failed to agree |
| `budget_exhausted` | dispersion was still falling at the last round (strictly decreasing over the final three) — the world ran out of rounds, not out of agreement |
| `harness_failure` | any of: a round produced no submission from some agent; a submission was malformed; a world raised; wall-clock for a round exceeded its limit |

`harness_failure` worlds are **excluded from every rate and their count is
reported separately.** A rate computed over a denominator that quietly includes
timeouts is the survivorship trap this lab has now hit twice.

Per world the record keeps: the full dispersion trajectory, per-round
submission counts, per-round wall-clock, the seed, and the configuration. Per
round it keeps enough to tell a stalled harness from a stubborn population
without re-running anything.

## Predictions — frozen

1. `method only > placebo baseline` on coordination rate at `TAU=0.10`.
   Moderate confidence. This is the claim.
2. `content only > method only`.
3. `both > content only`, by a smaller margin than (1).
4. The most likely single outcome is that **the pilot fails P1 upward** —
   unguided agents coordinate more often than 0.60 — and the sweep has to push
   toward noisier signals and narrower observation.
