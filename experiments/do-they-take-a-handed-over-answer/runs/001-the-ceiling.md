# Run 001 — If the answer is handed over, do they take it?

**Opened:** 2026-08-23 · **Status:** reported

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards.

---

## Why this run

Rung 1 of the ladder in [`CLAUDE.md`](../CLAUDE.md). Two pilots showed a
treated round reaching 0.978 and 0.887 against floors of 0.642 and 0.674, where
the control finished at 0.000. Four rounds is not a result. This is the run
that decides whether the ceiling is real, and it is the gate on every rung
below it.

Design frozen in [`PREREGISTRATION.md`](../PREREGISTRATION.md); departures in
[`DEVIATIONS.md`](../DEVIATIONS.md).

## Specification

| | |
|---|---|
| entry point | `run.py`, driving `005-deliberation-protocol/run_v3.py` |
| conditions | `e-bare` (base, unchanged) · `e-plan` (base + `stimuli/plan.md` + that trader's own equilibrium, appended to its private block) |
| units / counts | 12 seeds × 2 cells = **24 rounds**, paired on seed; **5 episodes** × 180s (D3); 4 traders |
| seeds | 1–12; seeds 6–12 are islands no run has used |
| timing | window **45s**, acknowledgement asked by **30s** (D2, D2a) |
| command | `python run.py --arms e-bare e-plan --rounds 12 --episodes 5 --episode-seconds 180 --ack-seconds 45 --ack-by-seconds 30 --agents 4 --out results/001-ceiling` |
| cost | **96 agent sessions**, 24 rounds at 10 concurrent = 3 waves, **~50 min** |
| go | Given by the owner on 2026-08-23 ("ok", with five episodes), before launch. |

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | Five episodes do not disadvantage the control. The treated cell peaks in episode 1; the control had room to climb over ten. | `e-bare`'s per-episode trajectory is still rising at episode 5. Then the difference is overstated and the run says so (D3). |
| A2 | The plan reaches behaviour — traders produce the shares they were given. | Production match near the control's. Then the primary is uninterpretable and this is a manipulation failure, not a null. |
| A3 | Captured gain is comparable across islands, since the plan is worth 1.4×–2× autarky depending on the seed. | Its spread tracks the plan's size rather than behaviour. |
| A4 | Acknowledgement is not a treatment effect worth reading. Pilot 001b: `e-bare` 4/4 and 4/4, `e-plan` 0/4 and 2/4 at the same window, and `e-plan` seed 1 scored 0.978 with zero acknowledgements. | Nothing — it is reported and not interpreted. |
| A5 | Presence and captured gain can be read apart. | Both move together in every seed; reported as confounded, as in 006. |

## Hypothesis

- **Expect:** `e-plan − e-bare` on captured gain well past the +0.15 threshold,
  on most of the twelve seeds. The pilots were not subtle.
- **Would surprise me:** high compliance with no gain. That fires the stopping
  rule and moves the whole programme to mechanism design.
- **Would not surprise me:** a wide spread — one pilot round collapsed an
  episode inside an otherwise near-frontier round, and heavy tails are why the
  median is reported beside the mean.

## Metrics

Primary **captured gain**, `(u_achieved − u_autarky) / (u_plan − u_autarky)`,
per acting trader-episode, averaged within a round, paired per seed. **Mean and
median both**, per the measurement note in run 001a. Co-primary **presence**.
Compliance as pre-registered: production match, named exchanges settled,
episode of first full compliance. Denominator 12 seeds per cell; a failed round
is reported as failed and stays in the denominator.

## Preflight

| gate | commit | result |
|---|---|---|
| smoke — this experiment's tests and the instrument's | `c19386a` | **pass** — `5 passed`, `108 passed` |
| the plan itself — transfers agree pairwise | `c19386a` | **pass** — checked by test and printed |
| assembly — `show_prompt.py e-plan` | `c19386a` | **pass** — base, then the block, then the trader's own numbers |
| toolchain — `run_v3.preflight()` | `c19386a` | **pass** |
| pilot | — | **run 001a** (30/20) and **run 001b** (45/30), both reported |

## Failure modes anticipated

- **A hub blip**, retried on both a bad answer and a dropped connection, with a
  failed round reported as failed rather than destroying the others.
- **Boards and keys not saved** — pulled off the hub immediately after the run,
  before the one-hour TTL.
- **Heavy tails in the primary**, handled by reporting the median beside the
  mean rather than by trimming.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `results/001-ceiling/v3.json`, 24 rounds, run stamp `0823T1105`.
  All 24 boards saved under `boards/` before the TTL.

- **Ran:** all 24 rounds, 5 episodes each. No failed rounds. Presence
  **0.90** (`e-bare`) against **0.89** (`e-plan`).

- **Numbers — primary.** Captured gain, `(u_achieved − u_autarky) /
  (u_plan − u_autarky)`, per acting trader-episode, averaged within a round,
  paired per seed. Denominator 12 seeds per cell; no round dropped.

  | seed | `e-bare` mean / med | `e-plan` mean / med | diff (mean) |
  |---|---|---|---|
  | 1 | −0.26 / +0.11 | +0.88 / +1.00 | +1.14 |
  | 2 | −1.10 / −0.15 | +1.15 / +1.00 | +2.24 |
  | 3 | −0.57 / −0.32 | −1.32 / −1.57 | −0.76 |
  | 4 | −0.37 / −0.03 | +0.47 / +1.00 | +0.84 |
  | 5 | −1.04 / −0.54 | −0.98 / −0.46 | +0.06 |
  | 6 | +0.13 / +0.15 | +0.87 / +1.00 | +0.74 |
  | 7 | −1.12 / +0.05 | −0.18 / +0.46 | +0.94 |
  | 8 | −0.30 / −0.09 | −1.58 / −0.99 | −1.28 |
  | 9 | −0.22 / −0.13 | −2.17 / −1.29 | −1.95 |
  | 10 | +1.57 / −0.14 | +7.04 / +1.00 | +5.47 |
  | 11 | −0.46 / −0.40 | −0.36 / +0.52 | +0.10 |
  | 12 | −0.26 / −0.04 | +0.67 / +1.00 | +0.93 |

  **On means: mean +0.709, median +0.792, 9 of 12 seeds favouring.**
  **On medians: mean +0.349, median +0.867, 9 of 12 favouring.**

  The pre-registered threshold — ≥ +0.15 on at least 9 of 12 — is **met on both
  statistics**. Seven `e-plan` rounds have a median captured gain of exactly
  +1.00: those traders collected everything the plan offered.

- **Numbers — co-primary (presence).** 0.90 against 0.89, a gap of 0.01. **The
  primary is not confounded by attrition** — the first run in this sequence of
  which that is true.

- **Numbers — compliance, read from settled state.**

  | | `e-bare` | `e-plan` |
  |---|---|---|
  | productions matching the plan's shares | **0 / 215** | **214 / 214** |
  | rounds reaching full four-trader compliance | 0 / 12 | **7 / 12** |
  | episode of first full compliance | — | **1**, in all seven |
  | named exchanges that settled at least once | — | **112 / 144 (78%)** |

  Production compliance is total and immediate. Exchange compliance is not.

- **Numbers — where the rounds divide.** `eff_round` against each round's own
  floor, split by whether every planned exchange settled:

  | | rounds | above floor |
  |---|---|---|
  | all 12 planned exchanges settled | 1, 4, 6, 10, 11, 12 | **5 / 6** |
  | any planned exchange missing | 2, 3, 5, 7, 8, 9 | **1 / 6** |

  Mean `eff_round`: `e-bare` 0.240, `e-plan` 0.471; rounds above their floor,
  1/12 against 6/12.

- **Assumptions that did not hold:** none.

  **A1 held** — no sign that five episodes disadvantaged the control; `e-bare`
  reached full compliance never and its per-episode trajectory does not rise to
  episode 5. **A2 held emphatically** — 214/214. **A4 held** as written:
  acknowledgement is reported and not interpreted. **A5 held** — presence
  differs by 0.01 while the primary differs by 0.709.

- **Deviations:** D1, D2, D2a, D3, all written before the run. No new deviation.

## What this changed

**The ceiling is real, and it is high.** Handed the island's equilibrium,
traders reach 0.97, 0.95, 0.92, 0.82 and 0.79 of the frontier on the rounds
where the plan completes — against a control that beat its own floor once in
twelve. A good outcome is reachable by these agents on this island. Every null
in experiments 005 and 006 was measured against a task that is achievable, not
an impossible one.

**Production is not where anything breaks.** 214 of 214 settled productions
matched the plan's labour shares, to within 5%, and seven rounds had all four
traders complying **in episode 1**. Told exactly what to make, they make it,
immediately and without exception. Whatever the earlier treatments failed to
convey, it was not for want of agents willing to follow an instruction.

**It breaks in the exchange.** Only 112 of 144 named exchanges ever settled,
and the split is almost total: of the six rounds where every planned exchange
settled, five beat their floor; of the six where any was missing, one did.
There is no middle. A plan with a hole in it does not degrade gracefully — it
collapses to zero, because a Cobb-Douglas trader left holding none of one good
has no utility at all, and the plan deliberately produces corner bundles that
only trade completes.

**So the loss located in the report of 2026-08-23 is confirmed, and sharpened.**
That report said the expensive step was the specialisation bet placed before
anyone knows whether counterparties will answer. This run removes every excuse
for not answering — both sides were handed the same trade, in the same
quantities, naming each other — and 22% of those trades still never happened.

**What this licenses.** Rung 1 works, so the ladder in `CLAUDE.md` is worth
walking: rung 2 removes the counterparties from the plan, rung 3 removes
everything but the prices. But the more urgent question this run raises is not
on the ladder at all — **why does a trade both parties were told to make fail
to settle?** That is answerable from these 24 boards, without spending anything.
