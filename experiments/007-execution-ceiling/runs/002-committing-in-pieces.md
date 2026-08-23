# Run 002 — Does committing the plan gradually beat committing it at once?

**Opened:** 2026-08-23 · **Status:** running

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards.

---

## Why this run

Run 001 showed the plan is followed on the production side and 22% short on the
exchange side, and that the shortfall is not proportional: a plan with a hole in
it collapses to zero, because the trader is holding a corner bundle that only
trade completes. Committing all the labour before knowing whether the exchanges
happen is what makes that fatal.

Design frozen in [`PREREGISTRATION-v2.md`](../PREREGISTRATION-v2.md); the rule
change in [D4](../DEVIATIONS.md), the missing control in D5.

## Specification

| | |
|---|---|
| entry point | `run.py`, driving `005-deliberation-protocol/run_v3.py` |
| conditions | `t-plan` (run 001's block) · `t-tranche` (same economics + commit in pieces). Both may split labour. |
| units / counts | 12 seeds × 2 cells = **24 rounds**, paired; 5 episodes × 180s; 4 traders |
| timing | window 45s, acknowledgement asked by 30s |
| command | `python run.py --arms t-plan t-tranche --rounds 12 --episodes 5 --episode-seconds 180 --ack-seconds 45 --ack-by-seconds 30 --agents 4 --no-control --out results/002-tranche` |
| cost | **96 agent sessions**, 3 waves, **~50 min** |
| go | Given by the owner on 2026-08-23 ("Go"), before launch, with delivery confirmed as prompt-delivered per D1. Expected spend: 96 agent sessions, ~50 min. |

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | The rule reaches behaviour — traders in `t-tranche` actually send more than one `PRODUCE` per episode. | Productions per trader-episode near 1 in both cells. Manipulation failure, not a null. |
| A2 | Splitting does not itself cost anything: a trader that splits and completes all its trades ends where run 001's did. | `t-plan` rounds with full exchange completion score below run 001's equivalents. |
| A3 | Zero-utility trader-episodes are the mechanism. | Captured gain improves while zeros do not fall — then something else did the work and the run says so. |
| A4 | Both cells are equally able to split, so the treatment is the advice. Guaranteed by construction (D4), and checked: `t-plan` traders may split and are simply not told to. | `t-plan` splits as often as `t-tranche`, which would mean the rule alone suffices — itself a finding. |
| A5 | 5 episodes is enough for a tranche strategy, which needs within-episode time rather than across-episode learning. | First tranches appear but second tranches do not, with the bell arriving first. |

## Hypothesis

- **Expect:** `t-tranche` above `t-plan` past the +0.15 threshold, with
  zero-utility trader-episodes markedly lower. The simulation puts the gain at
  1.37× against 1.07× at run 001's observed completion rate.
- **Would surprise me:** tranching used and captured gain unchanged. That would
  say the zeros are not what costs the rounds, and would point at the exchange
  mechanism rather than at the commitment.
- **Would not surprise me:** traders splitting once and then forgetting the
  second tranche, so labour goes unspent and the round is worse than a full
  commitment. That is A5, and unspent labour is measured.

## Metrics

Primary **captured gain**, paired, mean and median. Co-primary **zero-utility
trader-episodes**. Compliance: productions per trader-episode, first-tranche
size, exchange completion against run 001's 112/144. Also **unspent labour at
the bell**, which the manager already reports and which is the cost of a
tranche strategy that stalls.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke — this experiment and the instrument | `pytest tests -q` in both | `8a60984` | **pass** — `7 passed`, `112 passed` |
| the rule — split labour on, off by default | `pytest tests/test_v3.py -k split` | `8a60984` | **pass** — pieces summing to the budget settle, the piece that overruns is refused naming the excess, the default stays off, the bell returns the whole budget |
| assembly | `python tools/show_prompt.py t-tranche` | `8a60984` | **pass** — the plan's economics verbatim, then the tranching advice, then the trader's own numbers |
| toolchain | `run_v3.preflight()` | `8a60984` | **pass** |
| pilot | reused — run 001a/001b for the timing, run 001 for the instrument. **The split-labour rule has no live pilot**; it is covered by three unit tests and by the first round's boards being read before the wave completes. | `8a60984` | recorded as a **gap**: no live pilot of D4 |

## Failure modes anticipated

- **The rule not reaching the prompt**, which the assembly gate checks.
- **Unspent labour** — a tranche strategy that stalls is worse than no strategy.
- **A hub blip**, retried; a failed round reported as failed.
- **Boards not saved** — pulled off the hub before the TTL.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
