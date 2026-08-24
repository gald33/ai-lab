# Run 004 — The ladder, pass A

**Opened:** 2026-08-24 · **Status:** running

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

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
