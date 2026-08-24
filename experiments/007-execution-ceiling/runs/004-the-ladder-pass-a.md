# Run 004 — The ladder, pass A

**Opened:** 2026-08-24 · **Status:** reported (pass A)

Everything above the Outcome line is written **before** the run starts.

---

## Why this run

Run 001's block worked and contained three separable things: numbers no trader
could derive (**the cheat**), a way of acting with others (**the protocol**),
and facts derivable from a trader's own private block (**the hint**). The cheat
is removed from all four cells. This asks how much survives, and which part
carries it.

Design frozen in [`PREREGISTRATION-v3.md`](../PREREGISTRATION-v3.md).

## Specification

| | |
|---|---|
| entry point | `run.py` |
| conditions | `l-bare` · `l-protocol` · `l-hint` · `l-both` (2×2) |
| units / counts | 12 seeds × 4 cells = **48 rounds**, paired; 5 episodes × 180s; 4 traders |
| timing | window 45s, acknowledgement by 30s |
| primary | **share of trader-episodes above own autarky** (run-mean sd 0.085) |
| co-primary | **share ruined** — zero utility (run-mean sd 0.073) |
| command | `python run.py --arms l-bare l-protocol l-hint l-both --rounds 12 --episodes 5 --episode-seconds 180 --ack-seconds 45 --ack-by-seconds 30 --agents 4 --out results/004-ladder-a` |
| cost | **192 agent sessions**, 5 waves, **~80 min** |
| go | Given by the owner on 2026-08-24 ("Go on. Run the experiment we need."), before launch. |

**This is pass A of two.** Per the pre-registration, no ordering among the
cells is believed from one pass; pass B repeats it on the same seeds and a
result requires both passes to agree in sign. Pass A may report descriptive
numbers with denominators. It may not report a finding.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | The bounded endpoints carry the run noise run 003 measured (0.085, 0.073) and not more. | Pass B's cell means move by much more than that. Then even these endpoints are unresolvable and the design is out of options at this size. |
| A2 | `l-both` is exactly `l-protocol` + `l-hint`. Guaranteed by generation and by test. | The test fails. It runs in the gates. |
| A3 | No cell carries the cheat: no `walras()` output, no counterparty, no quantity, no price, and `PRIVATE_HOOK` returns nothing for every ladder arm. | The test fails. It runs in the gates. |
| A4 | Removing the cheat leaves *something*. | All three treated cells sit on `l-bare` — which is the pre-registered stopping condition, not a failure of the run. |
| A5 | Length is a confound between cells (346, 412, 758 words) and is not controlled. | If `l-both` beats both singles by roughly what a longer block would buy, length is the parsimonious reading. Stated here rather than discovered; a length-matched placebo is the fix and costs a fifth cell. |

## Hypothesis

- **Expect:** the hint to carry more than the protocol. Run 001 showed
  production compliance was total and exchange compliance was not, and the hint
  is the block that says what to do when an exchange fails.
- **Would surprise me:** the protocol alone matching `l-both`. That would mean
  the domain content is redundant once the method is right.
- **Would not surprise me:** everything sitting on the control. Four treatments
  in 005 and 006 did exactly that, and the one that did not was the one holding
  the answer.

## Preflight

| gate | commit | result |
|---|---|---|
| smoke — this experiment and the instrument | `7df45cc` | **pass** — `10 passed`, `112 passed` |
| `both` is its two parts, unmodified | `7df45cc` | **pass** — protocol then hint, zero extra words |
| protocol names nothing about the island | `7df45cc` | **pass** — none of 35 domain words |
| no ladder cell carries the cheat | `7df45cc` | **pass** — no plan text, no prices, and `PRIVATE_HOOK` returns empty for all four arms |
| toolchain | `7df45cc` | **pass** |
| pilot | reused — runs 001a/001b for the timing, 001–003 for the instrument | `7df45cc` | reused |

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*
**Pass A of two. Descriptive only — the pre-registration forbids a finding
from one pass.**

- **Records:** `results/004-ladder-a/v3.json`, 48 rounds, stamp `0824T0454`.
  All 48 boards saved before the TTL.
- **Ran:** all 48 rounds, 5 episodes each, no failed rounds.

- **Numbers — cell means.** Denominator 12 seeds per cell.

  | cell | above own autarky | ruined | presence | `eff_round` | rounds above floor |
  |---|---|---|---|---|---|
  | `l-bare` | 0.314 | **0.298** | 0.93 | 0.352 | 1/12 |
  | `l-protocol` | 0.358 | 0.147 | 0.93 | 0.363 | 2/12 |
  | `l-hint` | 0.445 | 0.139 | 0.95 | 0.465 | 2/12 |
  | `l-both` | **0.449** | **0.075** | 0.88 | 0.306 | **4/12** |

- **Numbers — primary, paired against `l-bare`.**

  | cell | mean | median | favouring | **seeds at ≥ +0.15** |
  |---|---|---|---|---|
  | `l-protocol` | +0.044 | +0.050 | 7/12 | **5/12** |
  | `l-hint` | +0.130 | +0.186 | 8/12 | **7/12** |
  | `l-both` | +0.134 | +0.225 | 9/12 | **7/12** |

  **The pre-registered rule — "≥ +0.15 on at least 8 of 12 seeds" — is met by
  no cell.** All three are nulls by the rule as written. Seeds at ≤ −0.15:
  3, 3 and 2 respectively, so none is harmful either.

- **Numbers — co-primary, share ruined (lower is better).**

  | cell | mean | median | lower on |
  |---|---|---|---|
  | `l-protocol` | **−0.151** | −0.059 | 7/12 |
  | `l-hint` | **−0.159** | −0.125 | 8/12 |
  | `l-both` | **−0.223** | −0.100 | 7/12 |

  Every treated cell more than halves the ruin rate: 0.298 in the control
  against 0.147, 0.139 and **0.075**.

- **Assumptions that did not hold:** none. **A2** and **A3** held by test —
  `both` is exactly its two parts, and no ladder cell carries any of the cheat.
  **A4** did not fire: the treated cells do not sit on the control. **A5**
  stands as written and is untested: `l-both` is the longest block and also the
  best on both endpoints, so length is not ruled out.

- **Deviations:** none.

## What this changed

**Read the two endpoints together, because they say different things.**

On the primary, no cell clears the pre-registered bar. On the co-primary, every
cell more than halves the ruin rate, and `l-both` cuts it by three quarters —
0.298 to 0.075.

That combination is the opposite of run 001's. The full plan **raised** ruin
(23–41% against an 18% control) while raising the average: it bought a better
mean by making the outcome more violent. These blocks, with the cheat removed,
do the reverse — they take the zeros out. `l-both` is the only cell in this
experiment's history to be better than its control on *both* endpoints at once.

**And rounds above their own floor go 1, 2, 2, 4.** Small numbers, and exactly
the kind of ordering run 003 warned cannot be trusted from one pass — but it
runs the same way as everything else here.

**What pass A does not license.** Any claim about which block carries it. The
protocol's +0.044 and the hint's +0.130 differ by less than this instrument
resolves, and `l-both` is within 0.004 of `l-hint` on the primary while being
412 words longer, which is what A5 anticipated and cannot separate.

**Pass B is the run that decides.** Same command, same seeds. A cell that holds
its sign on both endpoints across both passes is a result; one that flips is
unresolved. Nothing here should be quoted until then.
