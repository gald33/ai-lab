# Run 006 — Does saying what constancy *implies* change anything?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Watching run 005's boards, the traders behave as though each episode were a
fresh island: they rediscover who makes what, and the last episodes look like
the first. The obvious remedy is to tell them capacities do not change — except
**the instructions already say so**, in the per-round block: *"Your capacities
and tastes are the same in every episode of this round, and so is everyone
else's."*

So this probe does not add a fact. It adds the **implication**: that what you
learn about a trader keeps its value, that early episodes are for finding out
and later ones for repeating what worked, and that a bad rate was not bad luck
because the costs behind it do not move. Whether stating a consequence changes
behaviour when the premise was already stated is the question.

**Two changes are in flight at once, and this run separates them.** PR #23
replaced relative countdowns with absolute UTC deadlines, after a trader
acknowledged "Episode 1 in 120s" when episode 1 was thirty seconds away. Both
cells here carry that fix, so it is held constant between them; and
`probe-bare` re-measures run 005's control *under* the fix, which is the only
way to see what the fix alone did. Conflating the two was the thing to avoid.

## Specification

| | |
|---|---|
| entry point | `run_v3.py` (commit recorded at the gates below), carrying PR #23 |
| conditions | **`probe-bare`** — base instructions only. **`probe-constant`** — base plus `stimuli/probe/constant.md`. |
| units / counts | 3 seeds × 2 cells = **6 rounds**, 10 episodes × 180s, 4 traders |
| seeds | 1–3, **paired** across cells, and the same islands run 005 used |
| models | `claude-haiku-4-5-20251001` |
| stimuli | `stimuli/v3/base.md` body sha256 `c1ff3e80038c66314adcfbf711f5f873d4d129fcb02a2321400b3200fdd2b342`; `stimuli/probe/constant.md`, **not frozen** |
| command | `python run_v3.py --arms probe-bare probe-constant --rounds 3 --episodes 10 --episode-seconds 180 --agents 4 --no-control --out results/006-probe` |
| cost | **24 agent sessions**, ~33 min, six rounds in one wave. Paid: needs an explicit go, recorded here. |

## The two comparisons

1. **The fix.** `probe-bare` against run 005's `max-bare` on seeds 1–3 — same
   clock, population, island and instructions, differing only in absolute
   versus relative deadlines. Across runs, so it is a weaker comparison than
   the second, and is reported as such.
2. **The instruction.** `probe-constant` against `probe-bare`, paired within
   this run.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | Everything except the deadline format is unchanged between run 005 and this run — same code path, hub, model, clock, population and seeds. | Any other difference surfaces in the diff between the two commits. |
| A2 | Three seeds can show an effect the size run 005 produced (−0.207). Anything smaller is not what this probe is for. | Cells differ by less than the spread across seeds — reported as "no effect this probe can resolve". |
| A3 | The constancy block changes behaviour that is visible in settled state: repeated exchanges between the same pair, later episodes cheaper in discovery. Talk is not the target and is not the endpoint. | Neither repetition nor efficiency moves, and only talk does. |
| A4 | Persistence does not differ systematically between cells. Run 005's treatment cost a third of it, so this is measured, not assumed. | Alive fractions differ; any efficiency claim is then conditional on them. |
| A5 | A silent agent chose to stop; a session that never joined is rescued once and counted (D10). | Zero activity with a runtime error in a log. |

## Hypothesis

- **Expect:** a small positive paired difference for `probe-constant`, driven by
  later episodes rather than earlier ones. I would call **+0.10 or more, in the
  same direction on at least 2 of 3 seeds**, worth following up.
- **Would surprise me:** the block making things worse, as run 005's treatment
  did. That would suggest any added text costs more than it returns here,
  whatever it says — a different and more troubling finding than "this
  particular text does not help".
- **Would make me stop adding text:** both this and run 005 negative. Two
  independent additions, one maximal and one minimal, both harmful, would say
  the cost is in the adding.

## Metrics for this run

**Primary.** Paired `eff_round − floor` per seed, mean and median over 3 seeds,
both cells' raw values printed. Denominator 3 seeds per cell; no round dropped.

**Behavioural, for A3.** Repeat exchanges — the share of settled exchanges whose
(maker, taker, goods) pair has settled before in the same round — and the
episode index at which each round's first repeat appears. This is the behaviour
the block targets and it is read from settled state.

**Secondary.** Alive fraction (A4); talk per trader-episode; settled and
refused; `zero_agent_episodes`. `eff_episode` reported, not interpreted.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | | |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | | |
| calibration | not needed — `eff_round` separated cells at −0.207 in run 005 on this exact clock and population, and the repeat-exchange measure is read from settled state rather than estimated. | — | instrument unchanged since run 005 |
| pilot | runs 001, 003, 004 and 005 cover this code path, clock, population and hub | reused | |

## Failure modes anticipated

- **Conflating the fix with the instruction** — the reason both cells carry the
  fix and `probe-bare` re-measures the old control.
- **Attrition differing by cell** (A4), which would make an efficiency
  difference partly a persistence difference, as it did in run 005.
- **A session that never joins**, rescued once and counted (D10).
- **Three seeds being too few**, named in A2 rather than discovered after.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
