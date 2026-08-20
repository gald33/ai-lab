# 005 — deviations from the pre-registration

Written and committed **before the agent run**, in the same spirit as
`PREREGISTRATION.md`: a deviation declared in advance is a design choice, and a
deviation noticed afterwards is a result about the author.

Nothing in `PREREGISTRATION.md` is edited. Everything below is a departure from
it, with the reason, and with what it costs.

## D1 — the round budget is 6 submissions, not 21

The accepted pilot configuration is `n8-k4-s0.15-w2-a0.3-r20`: eight agents,
four goods, twenty talking rounds. The agent run uses **six submissions**
(`r0` before anyone has heard anything, then five rounds of talk-and-resubmit).

Reason: cost and wall-clock. Twenty rounds is `4 cells x 12 worlds x 8 agents x
21 = 8,064` model calls. Six is 2,304.

Cost: `budget_exhausted` becomes a much more likely classification, and the
pilot's calibration of "not pinned at the ceiling" (P3) does not transfer. The
classification still runs and is still reported, so a cell that ran out of
rounds is visible rather than silently recorded as disagreement.

## D2 — the primary metric is under-powered, and a paired secondary is
pre-specified here

Coordination rate at `TAU=0.10` remains **the** primary metric and is reported
first. At twelve worlds per cell its Wilson interval is roughly +/-0.27, which
cannot separate 0.40 from 0.60. It is reported anyway, with intervals, because
changing the primary metric after freezing it is the exact move this document
exists to prevent.

**Pre-specified before any cell was run:** the reading is carried by
**minimum dispersion reached**, `min_r D(r)` — continuous, defined on every
world including ones that never coordinate, and **paired by seed** across
cells. Paired on twelve worlds, with the same truth, the same private signals,
the same observation draw and the same hint in all four cells, this has real
power where a twelve-world rate has none.

Comparisons are by exact binomial sign test on paired worlds, the unit being
the world, never the agent-round.

## D3 — the model is Haiku 4.5, and this is a choice about the hypothesis

The lab's standing claim is that conventions matter **especially to newborn
agents thrown at a task**. A protocol that helps a weak deliberator and not a
strong one is a finding, not a failure, and running the cheapest capable model
puts the hypothesis where it is most likely to be visible.

Cost: the result is about Haiku 4.5 and does not transfer upward. A null on a
stronger model would be a separate experiment, and the design does not claim
otherwise.

## D4 — the hint is common, not private

`PREREGISTRATION.md` defers hint distribution to a later experiment and does not
cross it. The `hint` cells therefore have to pick one, and they announce a
single vector to every agent in the world.

The hint is `normalise(exp(log(truth) + N(0, 0.10)))` — informative, closer to
the answer than any private signal (`sigma = 0.15`), and **wrong**, so a
population that simply copies it agrees on something slightly false and pays for
it in metric 2.

Cost: a common hint is itself a coordination device, so `content only` is
expected to score very well, and `both` may ceiling. That is prediction 2 and it
is not evidence about the protocol either way.

## D5 — one retry on a malformed submission

An agent that returns unparseable output is asked once more with the same
prompt. A second failure is a `harness_failure` for that world, excluded from
every rate and counted separately, exactly as the pre-registration requires.

Reason: a JSON slip is a fact about output formatting, not about deliberation,
and the pre-registration already insists that harness faults never enter a rate.

Cost: the retry is invisible in the transcript record unless read for; the retry
count is reported per cell.
