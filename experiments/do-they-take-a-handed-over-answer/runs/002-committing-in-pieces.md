# Run 002 — Does committing the plan gradually beat committing it at once?

**Opened:** 2026-08-23 · **Status:** reported

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

- **Records:** `results/002-tranche/v3.json`, 24 rounds, stamp `0823T1523`; all
  24 boards saved before the TTL.
- **Ran:** all 24 rounds, 5 episodes each, no failed rounds.

- **Numbers — compliance (A1). The rule reached behaviour.**

  | productions per trader-episode | `t-plan` | `t-tranche` |
  |---|---|---|
  | one | **149 (100%)** | 55 (31%) |
  | two | 0 | **117 (66%)** |
  | three | 0 | 4 (2%) |

  Labour left unspent at a trader's last production: **mean 0.00 in both
  cells**, 0% leaving more than 0.1 unspent. Traders that split came back and
  spent the rest. **A5 held**: second tranches happened before the bell.

- **Numbers — primary (captured gain, paired `t-tranche − t-plan`).**
  On means: **mean −1.857, median −0.237, 4 of 12 favouring.** On medians:
  **mean +0.133, median −0.067, 5 of 12 favouring.** Against the pre-registered
  threshold — ≥ +0.15 on at least 9 of 12 — this is a **null**. The mean is
  dominated by two rounds with extreme ratios (`t-plan` seed 10 at +31.64),
  which is why the median was pre-registered alongside it.

- **Numbers — co-primary (zero-utility trader-episodes).** `t-plan` **38%**,
  `t-tranche` **26%**. Lower in the treated cell, in the direction the
  mechanism predicted, and by less than the simulation's near-zero.

- **Numbers — secondary.** Presence 0.78 (`t-plan`) against **0.91**
  (`t-tranche`). Named exchanges settled: **48/144 (33%)** against **63/144
  (44%)**. Mean `eff_round` 0.042 against 0.188. Rounds above their own floor:
  **0/12 in both cells**.

- **Assumptions that did not hold: A2, and it invalidates the run's level.**

  A2 said splitting should cost nothing, so `t-plan` — run 001's `e-plan`
  block, byte-identical, same seeds, same timing, same 5 episodes, with the
  split rule available and **never used** (100% one production) — should have
  reproduced run 001. It did not, by a wide margin:

  | | run 001 `e-plan` | run 002 `t-plan` |
  |---|---|---|
  | named exchanges settled | **112/144 (78%)** | **48/144 (33%)** |
  | mean `eff_round` | 0.471 | 0.042 |
  | rounds above their floor | 6/12 | **0/12** |

  No mechanical difference explains it. The cell never split, so D4's rule
  changed nothing it did; the block hash, the seeds, the episode count, the
  window and the model are identical. **The instrument moved between the two
  runs by more than the effect this run was built to detect.**

  **A1, A3, A4, A5 held.** A4 in particular: `t-plan` could split and never
  did, so the rule alone does nothing and the advice is what produced the
  splitting.

- **Deviations:** D1, D2, D2a, D3, D4, D5, all written before the run. No new
  deviation.

## What this changed

**The manipulation is the cleanest this lab has produced.** Told they could
commit labour in pieces, 68% of treated trader-episodes did, and none of them
stranded labour by forgetting the second tranche. Told nothing, the control
split **zero** times out of 149 while holding exactly the same permission. The
rule alone changes nothing; the advice is what moves behaviour.

**Every mechanism measure moved the right way, and the primary did not.**
Zero-utility trader-episodes 38% → 26%, presence 0.78 → 0.91, exchange
completion 33% → 44%. Captured gain: 4 of 12 seeds. Partial commitment did what
it was supposed to do to the failure mode and did not convert it into utility
at a size this design can resolve.

**But the run cannot carry that reading, because its control did not
replicate.** `t-plan` is run 001's `e-plan` with a permission it never used, and
its exchange completion halved — 78% to 33% — with no mechanical difference
between them. Run 001's headline result was built on that cell. **This is the
third time in this lab that a cell has moved by more than the treatment effect
between runs**, after 006's `r-ratios` reversing sign, and it is now the largest
instance.

**So the honest state is: two results, and one of them undermines the other.**
Within this run, the tranching advice is enacted and moves the mechanism.
Across runs, the instrument moved enough that neither this run's level nor run
001's can be trusted as measured.

**What should happen next is not another treatment.** `FINDING-run-level-
variance.md` proposed re-running a cell to see whether the instrument is stable;
that proposal was not acted on and this run is what it costs. The next thing
worth spending on is **the same cell, repeatedly, on the same seeds, changing
nothing** — enough times to measure how much the instrument moves on its own.
Until that number exists, every paired difference this lab reports is a
difference plus an unmeasured run effect of unknown size.
