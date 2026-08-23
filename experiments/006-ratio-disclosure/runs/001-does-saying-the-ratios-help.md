# Run 001 — Does telling them what to disclose help?

**Opened:** 2026-08-22 · **Status:** reported

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
| go | Given by the owner on 2026-08-23 ("go"), before launch. Expected spend: 60 agent sessions, ~64 min. |

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
| smoke | `python tools/check_stimuli.py`; `python -m pytest tests -q` | `4d9b066` | **pass** — `OK` (both hashes match the pre-registration, placebo 4.2% shorter, no domain word), `8 passed` |
| assembly | `python tools/show_prompt.py r-ratios` | `4d9b066` | **pass** — base headings in order, then `## Two ratios` exactly once, then the private block |
| toolchain | `run_v3.preflight()` | `4d9b066` | **pass** — an agent's `switchboard-mcp` reached the hub |
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

- **Records:** `results/001-first/v3.json`, fifteen rounds, run stamp
  `0823T0336`. Boards under `results/001-first/boards/`, pulled off the hub
  before the TTL. Roster capture for the five `r-ratios` rounds only (D1).

- **Ran:** all fifteen rounds, none failed. 4/4 traders acknowledged in every
  round. **Two rescues (D10 of the instrument), both in `r-bare`** — seeds 1
  and 4, each a session that started and never joined, relaunched once;
  `r-placebo` and `r-ratios` had none.

- **Numbers — primary (exchange, `r-ratios − r-placebo`).** Utility over the
  trader's own autarky optimum, for trader-episodes that produced.

  | seed | `r-bare` | `r-placebo` | `r-ratios` | paired diff |
  |---|---|---|---|---|
  | 1 | 0.83 | 0.49 | 0.57 | **+0.08** |
  | 2 | 0.92 | 0.95 | 0.74 | −0.21 |
  | 3 | 0.69 | 0.88 | 0.65 | −0.23 |
  | 4 | 0.69 | 0.87 | 0.50 | −0.38 |
  | 5 | 0.95 | 0.78 | 0.41 | −0.36 |

  **Mean −0.221, median −0.229, 1 of 5 seeds favouring the treatment.** Against
  `r-bare`: mean −0.242, **0 of 5** favouring. Denominator 5 seeds per cell; no
  round dropped.

  This meets the pre-registered **harmful** threshold (≤ −0.10 with at least 4
  of 5 seeds in that direction).

- **Numbers — co-primary (presence).** Share of trader-episodes with any
  settled production, denominator 200 trader-episodes per cell.

  | cell | presence | exchange | above own autarky |
  |---|---|---|---|
  | `r-bare` | **0.83** | 0.82 | 61/167 |
  | `r-placebo` | **0.85** | 0.79 | 71/170 |
  | `r-ratios` | **0.73** | 0.57 | 34/146 |

  Presence falls in **4 of 5** seeds against `r-placebo`, mean −0.120.

- **Numbers — the absolute test.** No cell reached exchange above 1.0. Best
  round: `r-placebo` seed 2 at 0.95 mean, median 1.19. Across all three cells,
  **166 of 483** acting trader-episodes beat their own autarky optimum.

- **Numbers — manipulation check.** Free-text trader messages stating a ratio,
  by the crude matcher in `analysis/manipulation.py`:

  | cell | channel | roster `task` |
  |---|---|---|
  | `r-bare` | 0 of 1 free messages | not captured (D1) |
  | `r-placebo` | 0 of 0 free messages | not captured (D1) |
  | `r-ratios` | **3 of 7** free messages | **0 of 373** task strings |

  Only the treated cell stated any ratio. **The absolute volume is 7 free-text
  messages across 5 rounds and 200 trader-episodes.**

- **Assumptions that did not hold:** **A2**. It said presence and exchange
  would move independently enough to be read apart, and named the consequence
  if they did not. Both fall together in the treated cell. **Per the
  pre-registration, the exchange difference is therefore reported as confounded
  with a presence difference and is not read as an exchange effect.**

  **A1 holds, and this is the run's cleanest result.** The placebo is inert:
  `r-placebo − r-bare` on exchange is **−0.021**, with 3 of 5 seeds favouring
  the placebo. Being handed a considered-looking paragraph, by itself, did
  nothing measurable.

  **A3 holds** in the sense that matters: the difference (0.221) exceeds the
  0.10 the pre-registration named and exceeds the within-cell between-seed
  spread of the controls.

  **A4 holds** — the only difference in the instrument is the arm registration and the `--out` path.

  **A5 holds** for the channel and is **extended** by D1: ratios were not
  hiding in roster task strings either. Direct messages remain unreadable by
  anyone, including this analysis (D2).

- **Deviations:** **D1** (roster poller added mid-run, uneven coverage) and
  **D2** (the tool grant is narrower than Switchboard's surface; `dm` is
  granted and unmeasurable, the keyed board is not granted). Both written
  before any number here was computed.

## What this changed

**The treatment is harmful on the primary, and the run cannot say why.** The
paired difference clears the pre-registered harm threshold on both counting
rules. But presence falls with it in 4 of 5 seeds, and the pre-registration
fixed in advance what that means: a change in exchange accompanied by a change
in presence of the same sign is not read as an exchange effect. The treated
traders traded worse *and* showed up less, and this design cannot separate the
two. That is the third time attrition has confounded a treatment in this lab —
005's runs 005 and 006 were the first two — and it is now the single largest
obstacle to measuring anything here.

**The placebo did nothing, which retires a live hypothesis.** 005's runs 005
and 006 both found added text harmful, and the reading on offer was "the cost
is in the adding". This run had a length- and register-matched paragraph with
no domain content, and it cost **0.021** against bare with 3 of 5 seeds
favouring it. Being handed a paragraph is not what hurts. Whatever `r-ratios`
did, it did through its content.

**The manipulation check passed and is nearly empty.** Only the treated cell
stated any ratios, so the block did reach behaviour — but 3 ratio statements in
7 free-text messages across 200 trader-episodes is a manipulation of almost no
volume. This matters for what may be concluded: **the harm cannot plausibly be
caused by ratio-stating, because there was hardly any.** Something about the
block changed what traders did without getting them to say the thing it asked
for. A treatment that suppresses participation while barely producing the
behaviour it names is a different object from "a hint that does not work".

**What is not concluded.** That disclosure does not help. This run did not
achieve disclosure. The pre-registered stopping rule fires only when the
treatment is null-or-harmful **and** the manipulation check passed with the
traders having said the ratios — here they did not, so the rule does not fire
and the question stays open.

**What the run says about the island itself.** Across all three cells, 166 of
483 acting trader-episodes ended above the trader's own autarky optimum, and no
cell's mean cleared 1.0. Gains from trade are being realised about a third of
the time and lost the rest. Combined with 005's run 007 — where an agent alone
hit that optimum on 85 of 104 acts — the picture is consistent: these agents
can allocate, and lose it when they interact.

**Next.** The obstacle is attrition, not the wording of hints. A design that
cannot hold presence constant cannot measure exchange, and three runs have now
foundered on that. The candidates, in order of how much they'd tell us: hold
presence fixed by construction and measure exchange conditional on it; or
measure what a trader does in the episodes it *does* act, paired within trader
rather than within cell. Neither is scheduled, and neither adds instruction
text.
