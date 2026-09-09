# Proposal — does instruction help a more capable agent?

**Status: a proposal.** Not scheduled, not costed against a go, and not part of
any run in flight. Raised by the owner on 2026-08-23.

## The hypothesis

Every treatment this lab has run has cost something. 005's maximal "talk more"
block: −0.207. Its minimal constancy hint: −0.269. 006's ratio block: −0.221
against a matched placebo. The reading so far has been *"the cost is in the
adding"* — that text costs more than it returns, whatever it says.

The hypothesis here is that this is **not a fact about instructions but a fact
about capacity**: that a block of text competes for the same limited attention
the task needs, so on an agent near its limit any instruction is a tax. A more
capable agent would have room for both, and would then be able to *use* what
the block says.

## What makes it a real hypothesis and not a truism

"A better model scores better" is uninteresting and almost certainly true. The
claim here is about a **slope, not a level**: that the *difference between
treated and untreated* changes sign, or at least magnitude, with capability.

So the primary is the **interaction**, and the design has to be a 2×2:

| | untreated | treated |
|---|---|---|
| **haiku-4.5** | measured (0.79–0.82 exchange) | measured (0.57) |
| **a stronger model** | ? | ? |

The quantity of interest is `(treated − untreated | strong) − (treated −
untreated | haiku)`. A positive interaction is the hypothesis. Both main
effects are reported and neither is the claim.

## What it would change if true

It would put a **scope limit on every conclusion this lab has drawn.** Runs
005-003 through 006-001 would all become findings about `claude-haiku-4-5`
under a 180-second episode, not about instructions in general — including 005's
stopping rule, which closed a line of enquiry on the strength of two negative
runs. That rule would need re-reading, not deleting: it stopped *005* from
adding text to *haiku*, and it would remain correct about that.

The `PROPOSAL-ratio-disclosure.md` line would also reopen: a hint aimed at the
trading mechanism might land on an agent that has attention left to spend on
it.

## What would have to be watched

- **The ceiling.** If the stronger model sits near the frontier untreated,
  there is no headroom for a treatment to show in and a null means nothing.
  Current headroom is real — untreated exchange is 0.79–0.82 where break-even
  is 1.0 and gains from trade should carry it above — but this must be checked
  on the untreated strong cell **before** reading the treated one.
- **Presence.** Every run so far has had attrition move with the treatment, and
  it has confounded the primary three times (005's A3, 006's A4 and A2). A
  stronger model may simply persist longer, which would raise exchange through
  presence and not through better exchanging. Presence stays co-primary.
- **The instrument.** `run_v3.MODEL` is a module constant. A `--model` flag is
  needed, which is a small instrument change and would be recorded as one.
- **Cost.** 2 models × 2 cells × 5 seeds = 20 rounds = **80 sessions**, half of
  them on a model that is not haiku. This is materially more expensive than
  anything run so far and needs a priced estimate and an explicit go before
  anything spends. A 2-seed probe first would be cheaper and would answer the
  ceiling question on its own.

## Why this is worth doing

Because it is the first hypothesis in this sequence that would explain **all**
the negative results at once, rather than explaining each one separately. Three
treatments, three different contents, three costs of similar size — a common
cause is more parsimonious than three coincidences, and capacity is a plausible
common cause.

It is also cheap to falsify: if the interaction is flat, "the cost is in the
adding" survives a much harder test than it has faced so far.
