# Run 001 — If the answer is handed over, do they take it?

**Opened:** 2026-08-23 · **Status:** running

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

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
