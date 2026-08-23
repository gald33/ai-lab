# Run 001 — Does telling them what to disclose help?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

The first run of this experiment, and the first test of its whole premise.
[`PREREGISTRATION.md`](../PREREGISTRATION.md) holds the frozen design; this
record holds what was actually done.

The premise, in one line: 005's run 007 showed an agent alone reaches its own
autarky optimum (mean 0.972, 104 acts), so a peopled round below that floor is
losing value in the interaction — and the loss decomposes into **presence** and
**exchange**. Ratios are the smallest thing a trader could say that would let
someone else work out who should make what.

## Specification

| | |
|---|---|
| entry point | `run.py`, driving `005-deliberation-protocol/run_v3.py` (commit at the gates below) |
| conditions | `r-bare`, `r-placebo`, `r-ratios` — frozen by hash in the pre-registration |
| units / counts | 5 seeds × 3 cells = **15 rounds**, paired on seed; 10 episodes × 180s; 4 traders |
| seeds | 1–5, the islands 005's runs 005–007 used |
| models | `claude-haiku-4-5-20251001` |
| command | `python run.py --arms r-bare r-placebo r-ratios --rounds 5 --episodes 10 --episode-seconds 180 --agents 4 --out results/001-first` |
| cost | **60 agent sessions**, 15 rounds at 10 concurrent = 2 waves of ~32 min, so **~64 min** of wall-clock |
| go | *(not yet given — nothing runs until it is, and it is recorded here)* |

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | The placebo is inert: it changes prompt length and register, not what a trader knows about the economy. | `r-placebo` differs from `r-bare` on the primary by as much as `r-ratios` does. Then "adding a paragraph" is the effect and the content is not separable. |
| A2 | Presence and exchange move independently enough to be read apart. | Both move together in every seed; the run then reports a confound rather than an exchange effect, as the pre-registration requires. |
| A3 | Five seeds can resolve a difference of 0.10 on exchange. 005's runs saw between-seed spreads of that order on related measures. | Between-seed spread within a cell swamps the between-cell difference — reported as "no effect this design can resolve". |
| A4 | The instrument is unchanged from 005's run 007 apart from arm registration and the `--out` path. | The diff says otherwise. |
| A5 | A trader that says a ratio says it on the channel, where the manipulation check can see it. Direct messages are not counted and are not searched. | The check comes back near zero in `r-ratios` while its boards look talkative — then the measure is wrong, not the treatment. |

## Hypothesis

- **Expect:** exchange up in `r-ratios` against `r-placebo`, by more than the
  0.10 threshold, on at least 4 of 5 seeds. The reasoning: the information is
  genuinely absent from every board so far, it is cheap to state, and the
  islands carry eightfold differences in opportunity cost that nothing has ever
  exploited.
- **Would surprise me:** exchange unchanged while the manipulation check
  passes. That would mean traders can state their ratios and still not use each
  other's, which points at the exchange mechanism rather than at what is said.
- **Would not surprise me, given 005:** the whole thing coming in negative, with
  both treated cells below `r-bare`. Two runs have already found that adding
  text costs more than it returns. If that repeats **with the placebo also
  down**, the finding is about text, not about ratios — which is exactly what
  the placebo cell is for.

## Metrics

Per the pre-registration: **exchange** (primary), **presence** (co-primary,
always beside it), the manipulation check, and `eff_round` reported but not
primary. Denominator 5 seeds per cell; a failed round is reported as failed and
stays in the denominator.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python tools/check_stimuli.py`; `python -m pytest tests -q` | | |
| assembly | `python tools/show_prompt.py r-ratios` | | |
| toolchain | `run_v3.preflight()` | | |
| pilot | reused — 005's runs 005, 006 and 007 cover this instrument, clock, hub, model, population and episode length | reused | |

## Failure modes anticipated

- **A hub blip.** It killed two runs in 005. The retry now covers both a bad
  answer and a dropped connection, and a failed round no longer destroys the
  others' records — but a long enough outage still ends a round, and that round
  is reported as failed.
- **Attrition differing by cell**, which confounded 005 twice (its A3 and A4).
  Presence is co-primary here for that reason rather than a footnote.
- **The manipulation check failing**, which makes the primary uninterpretable
  and is reported as such, not as a null.
- **Boards not saved.** The runner does not save them; they are pulled off the
  hub immediately after the run, before the one-hour TTL, as in 006 and 007.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
