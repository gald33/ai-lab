# 007 — The execution ceiling · grounding

**You are working on experiment 007 only.** The repo-root
[`CLAUDE.md`](../../CLAUDE.md) and [`experiments/GROUNDING.md`](../GROUNDING.md)
apply. 005 supplies the *instrument* and 006 supplies two results that motivate
this; neither's design documents are grounding here.

## What this experiment asks

**If the answer is handed to them, do they take it?**

Not whether agents can find a good allocation — this hands them the island's
competitive equilibrium, per trader, in their own goods and quantities. What is
measured is whether instruction converts into settled state at all, and how
much of the available gain it collects.

## Why it exists

Experiments 005 and 006 ran four treatments and none improved coordination; a
re-analysis then showed the design could not have resolved the effects it was
testing for (`006-ratio-disclosure/FINDING-run-level-variance.md`). Before
spending more on subtler treatments, establish the **bound**: the most
informative instruction possible, on many seeds.

- If the plan is followed and the gain appears, there is a ceiling to aim at
  and the earlier nulls are about the *content* of hints, not about instruction.
- If the plan is followed and the gain does not appear, the mechanism is the
  problem, not what agents know.
- If the plan is not followed, that is the finding, and no subtler hint is
  worth running.

## The program this run opens

**Start at the end, then dismantle.** The point of handing over the whole
solution is not the treatment — nobody would ship it — it is to establish that
a good outcome is *reachable at all* by these agents on this island. That is a
feasibility question and it has to be answered before any subtler treatment is
worth running.

If it is reachable, 007 becomes a debugging sequence: remove one part of the
solution at a time and find where the outcome breaks.

| rung | what the trader is given |
|---|---|
| 1 | the full plan — shares, holdings, named exchanges, counterparties *(run 001)* |
| 2 | the plan without counterparties — what to make and hold, find your own partners |
| 3 | the prices only — work out your own bundle from them |
| 4 | the method, no numbers — this is 006's ratio block, already run and null |
| 5 | nothing — the control, already run many times |

Rungs 4 and 5 have been measured and are indistinguishable. Rung 1 is this
run. **Where the line falls between 1 and 4 is the finding**, and each rung is
only worth running if the rung above it worked.

## What this is not

**Not a coordination experiment.** The plan is computed from all four traders'
private data, so it dissolves the private-information problem by construction.
It measures execution.

**Not the system deciding.** See [D1](DEVIATIONS.md). The plan is a stimulus in
the prompt. The manager settles what a trader writes on the board and refuses
what is malformed, exactly as in every other experiment. Nothing is settled on
a trader's behalf and a trader that ignores the plan is not corrected.

## Local decisions

- **Two cells only**: `e-bare` and `e-plan`. Seeds are spent on power, not on
  arms — the previous experiment's problem was resolution, not variety.
- **Report the gain as a fraction of what the plan offers.** The equilibrium is
  worth 1.4×–2× autarky depending on the island, so a raw difference is not
  comparable across seeds. `captured = (achieved − autarky) / (plan − autarky)`.
- **Compliance is read from settled state**: did the labour shares match the
  plan, did the named exchanges settle. Never from what a trader says it did.
- The board is the only surface. The plan is text in a prompt; no tool, schema
  or channel is added for it.

## Before running anything

A run record from the template, committed **before** the run. Gates in
[`PREFLIGHT.md`](PREFLIGHT.md) recorded against the commit being run. Paid
cells need an explicit go, recorded with expected spend.
