# 005 — The deliberation protocol

**Status: designed, unrun.** No code, no results. This document is the
pre-registration; it is meant to be attacked before anything is built.

## Question

Agents given a coordination task deliberate badly. When we help them, we help in
two different currencies without noticing:

- **content** — a hint about *what the answer is* ("the price is around 3");
- **method** — a shared understanding of *how to deliberate*: how to put a claim
  on the table, how to object, how to tell that the group has converged, when to
  stop talking and act.

The lab's standing claim is that conventions matter most to newborn agents. 002
and its Tier 3 calibration only ever tested content: a price vector of
manufactured quality, handed over. That measures how good a hint is, and how
much error a hint can carry before it kills the island. It says nothing about
whether a group with **no hint at all** does better when it shares a method for
producing one.

**005 asks exactly that: does a content-free deliberation protocol improve
coordination, holding the hint fixed?**

## Why this is not 002 again

002's axis was *hint quality* (δ) and, in design though not in fact, *hint
sharedness*. Both are about the hint. A deliberation protocol is orthogonal by
construction: it contains no claim about the market, so it cannot smuggle the
answer in. That is the property that makes the experiment clean, and it is worth
stating as a check on the artifact rather than an intention — **a protocol
document that names a good, a price, a quantity, or a role fails review before
the run.**

## Design

A 2×2, crossed, paired on seeded worlds.

| | no hint | hint |
|---|---|---|
| **no protocol** | baseline | content only |
| **protocol** | **method only** ← the cell that answers the question | both |

The interesting comparisons, in order:

1. **method only vs baseline** — the headline. Does method alone buy anything?
2. **method only vs content only** — is method worth as much as an answer?
3. **both vs content only** — does method still add once the answer is known?
   (If it does, the protocol is doing something other than substituting for the
   hint — plausibly getting the group to *act* on the hint faster.)

### The control is a placebo, not an empty prompt

The protocol arm gives agents extra text, extra structure, and a signal that
someone thought about their situation. A bare baseline confounds all of that
with the protocol's content.

The primary control is therefore a **length-and-effort-matched placebo**: inert
process advice of the same token count, the same imperative register, and the
same apparent authorship, that carries no coordination structure — "read the
task twice before answering; be concise; check your arithmetic". The baseline
cell above is the placebo cell. A bare-prompt cell is run as a secondary
reference only, and no headline number is computed against it.

**The placebo carries the causal weight of the entire experiment.** If it is
badly written — if it accidentally contains coordination advice, or is so
obviously filler that it reads as noise — the result is uninterpretable. It
should be drafted independently of the protocol and reviewed against a checklist
before either is used.

## Adoption is not measured

We do not measure whether agents follow the protocol.

The obvious readout — read the transcripts, compare phrasing to the protocol,
score compliance — is fragile in a way that is fatal here: the scorer becomes
part of the instrument, "adoption" becomes a judgement about surface form, and
an LLM judge would put a second model between the manipulation and the number.
A typed channel (`propose` / `accept` / `object` as tool calls) would make
adoption a record rather than a reading, but it also *is* a partial enforcement
of the protocol, which the constraint below forbids for anything that matters.

So: **the manipulation is the protocol text; the outcome is coordination; the
mechanism is unmeasured.** This is a real limitation and is recorded as one. It
means a positive result establishes that the protocol document changes outcomes,
not *how*. Mechanism is a separate experiment with a different instrument.

## What the system may and may not do

Stated by the repo's author and binding on the implementation:

- The system **may** enforce timing (when a round opens and closes), submission
  format (what a well-formed action looks like), and scoring.
- The system **must not** enforce prices, roles, trades, or production
  decisions.
- **Self-reports are non-authoritative.** Nothing an agent says about what it
  did, believed, or intended enters a metric. Metrics come from manager state
  and submitted actions only.

The protocol is a *document handed to agents*, never a rule the harness checks.
An agent that ignores it entirely must be able to play the game to completion.

## Pilot gate — run before any arm

Most of the risk here is that the task is uninformative. A market where unguided
agents converge in round one has no headroom; one where they never converge has
no signal. Either way every arm reads the same and the experiment is dead.

So the first thing built is **unguided worlds only**, swept over market
configurations, with a pre-registered acceptance band:

- unguided coordination succeeds in a **strict minority but not never** — target
  a success rate in **[0.15, 0.60]** across seeded worlds;
- and time-to-coordination has visible spread rather than being pinned at the
  floor or the ceiling of the round budget.

The number of configurations tried before one lands in the band **is reported**.
Searching for a workable task is legitimate; searching until the effect appears
is not, and the only defence is publishing the search.

If no configuration lands in the band, 005 stops there and reports that. A null
pilot is a result about the harness, and 002 Tier 3 already showed that harness
facts (half the islands died at δ=0) can dominate the manipulation.

## Metrics

Primary, in order:

1. **Coordination rate** — the fraction of worlds meeting a pre-registered
   coordination threshold. The threshold is fixed before the run and reported
   with a **sensitivity curve** across neighbouring thresholds, because a single
   cut point invites exactly one accusation and the curve answers it.
2. **Regret against a computable per-episode optimum.** The market is chosen so
   the optimum is computable (as `walras()` is in 002), so regret is a lookup
   rather than a comparison against the best arm.
3. **Rounds to coordination**, over worlds that coordinate — reported with its
   denominator, always. Medians over survivors are not comparisons; 002 and 004
   both produced a false reading this way before it was caught.

Secondary: dispersion of submitted actions per round, and the count of distinct
committed positions per round. These are structural, come from manager state,
and are *not* adoption measures — they describe the group's state, not any
agent's compliance.

## Statistics

- **Paired on seeded worlds.** Every arm sees the same worlds under the same
  seeds. The unit of analysis is the world, not the agent-round: agents within a
  world are not independent, which is the mistake that produced 004's phantom
  convergence drift.
- Replication count set by a **power calculation** against the pilot's observed
  variance, done before the arms run, not after.
- Rates reported with Wilson intervals; paired comparisons by exact binomial
  sign test on worlds.

## Prediction, pre-registered

1. **method only > placebo baseline** on coordination rate. Held with moderate
   confidence — this is the claim.
2. **content only > method only.** An answer beats a way of finding one, in a
   stationary market where the answer exists.
3. **both > content only**, by a smaller margin than (1). Method's residual
   value once the answer is known is real but small.
4. The pilot is the most likely place this dies, and the most likely failure is
   that unguided agents coordinate immediately.

## What this design does not measure

Recorded so a reviewer does not have to find them.

- **Adoption / mechanism** — deliberately, see above.
- **Hint distribution** — private vs common hint is not crossed here. It was
  proposed and deferred: crossing it makes a 2×2×2 and reintroduces the
  sharedness axis, which is the thing 005 exists to hold still. It is the
  natural 006.
- **Protocol quality.** One protocol is tested. A bad protocol failing and a
  good one succeeding are not distinguished by a single arm; a δ-style quality
  sweep over protocols is possible and is not attempted.
- **Non-stationarity.** As in 004, the market does not move. A protocol's value
  plausibly rises when the answer keeps changing, and that is untested.

## Cost

Unlike 002 Tier 3, 003 and 004, **this experiment cannot be run for free.** The
manipulation is a document given to a reasoning agent; scripted traders have no
beliefs about other agents and would produce byte-identical behaviour across all
four cells — exactly the limit 002's Tier 3 hit on its sharedness axis. The pilot
is the only part that can be partly scripted, and only to check that the market
has headroom at all.

## Open questions for review

1. Is the placebo the right primary control, or does matching length and register
   already concede too much to the protocol arm?
2. Is `[0.15, 0.60]` the right acceptance band, or should the pilot target a
   specific unguided success rate rather than a range?
3. Is "coordination" the right primary outcome for a claim about deliberation,
   given that a group can coordinate on something bad? Regret is reported, but it
   is second.
4. Is leaving mechanism unmeasured acceptable, or does a positive result without
   it under-determine the conclusion to the point of not being worth the money?
