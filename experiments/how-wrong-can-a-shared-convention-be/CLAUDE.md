# How wrong can a shared convention be? · grounding

*The relative links below resolve from
`experiments/how-wrong-can-a-shared-convention-be/`, not from here.*

**You are working on this experiment only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. No other experiment's design documents are grounding here.

## What this experiment asks

**How wrong may a convention be and still be worth holding, purely because
everyone holds it?**

Concretely: does a *wrong but shared* price vector beat a *correct but private*
one, and at what error does that stop being true. The headline quantity is
δ\*; the claim it tests is CS − CP, the value of common knowledge with the
content held byte-identical.

[`README.md`](README.md) is the design. [`PREREGISTRATION.md`](PREREGISTRATION.md)
is what is frozen, and [`DEVIATIONS.md`](DEVIATIONS.md) is every departure from
it, dated and written before the run it affects. Read all three before proposing
anything.

## Where this came from, and what that means for scope

The design is **Tier 3 of `which-part-of-a-convention-works`**, whose scripted
half ran and whose model half never did. That document is a **code and design
dependency, not grounding**: read
[`../which-part-of-a-convention-works/tier3-design.md`](../which-part-of-a-convention-works/tier3-design.md)
for the design this inherits, and take nothing else from that directory as
authoritative here. Its Tier 1 and Tier 2 thresholds, arms and metrics were
frozen for a different question and a different accumulation rule.

Three corrections to that design are already written down in
[`README.md`](README.md) and are not to be re-litigated:

1. **The endpoint is a count, not efficiency.** Tier 3's own calibration showed
   survivor efficiency is flat across the entire δ sweep.
2. **The published calibration curve is a *stock* curve** at 12 agents and does
   not transfer to this island. Recalibrate before using it.
3. **Noise is measured before any threshold is named.**

## The three things most likely to go wrong here

**Reporting the manipulation check as a result.** Instruction reliably changes
behaviour in this lab — 214/214, 20 against 0, 68% against 0%. The agents *will*
adopt the announced vector. That is assumed, is cited by row in
`PREREGISTRATION.md`, and is not a finding.

**Adding the mechanism ledger to the outcome ledger.** Adoption and outcome are
reported side by side and never summed, including when they point in opposite
directions. A convention that is adopted perfectly and moves nothing is a
*dead convention*, which is a result;
[`../is-coordination-less-to-reason-about/`](../is-coordination-less-to-reason-about/)
preserved exactly that shape — a timing predictor that became well calibrated
and bought no completion time at all — ahead of its own numbers, because it is
the result most likely to be dropped.

**Reading a raw CS or CP level as a capability claim.** The announced vector at
δ = 0 is computed from every trader's private data. Both arms carry that cheat
identically, so it cancels in the contrast and only the contrast is
interpretable.

## Substrate rules that bind this experiment

From the root standing decisions, restated because this design touches each:

- **The board is the only surface.** The announcement is a frozen stimulus
  block in a seat's private brief, where tastes and capacities already arrive.
  It is not a tool, not a manager change, and not a second channel.
- **The manager is held fixed as substrate.** An arm that varies enforcement
  varies the thing everything else is measured against. Enforcement is out.
- **No scheduler.** Each seat is its own long-lived session; the bell rings on
  the clock whether or not anyone acted.
- **Self-reports are non-authoritative.** Every metric comes from settled
  state.

## The gates

[`PREFLIGHT.md`](PREFLIGHT.md) declares them, and
`tools/ground.py how-wrong --preflight` prints them. They are free and they run
in order. Rung 0 and rung 0b of the ladder are gates in this sense: **nothing
paid runs until both have produced numbers**, and the thresholds in
`PREREGISTRATION.md` are written from rung 0's output before rung 1 starts.

Open a run record from the template before anything runs, and commit it first:

    tools/ground.py how-wrong --new-run "<name>"
