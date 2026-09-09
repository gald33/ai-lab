# Run 006 — Does saying what constancy *implies* change anything?

**Opened:** 2026-08-22 · **Status:** reported

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
| cost | **24 agent sessions**, ~33 min, six rounds in one wave. Expected spend at that size. |
| go | Given by the owner on 2026-08-22 ("run it"), before launch. |

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
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | `eaf8b60` | **pass** — `102 passed`, `stimuli unchanged`, `OK` |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | `eaf8b60` | **pass** — an agent's `switchboard-mcp` reached the hub |
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

- **Records:** `results/006-probe/v3.json`, six rounds, run stamp `0822T1839`.
  Boards saved under `results/006-probe/boards/`. The behavioural endpoint is
  recomputed by `analysis/repeats.py` from those boards.

- **Ran:** both cells in full. 3 seeds x 2 cells = 6 rounds, 10 episodes each,
  4 traders each. 4/4 traders acknowledged in every round and all four spoke in
  every round, so no cell lost a trader at the door. **Zero rescues** (D10 did
  not fire). No round hit the 500-message history cap. `drain_errors` 0 in all
  six -- D13's retry never fired.

  **The 18:22 attempt is not in this and is counted nowhere.** It died to a hub
  502 fifteen minutes in and wrote no round record; see D13.

- **Numbers -- primary.** Paired `eff_round`, denominator 3 seeds per cell, no
  round dropped.

  | seed | floor | `probe-bare` | `probe-constant` | paired diff |
  |---|---|---|---|---|
  | 1 | 0.642 | 0.556 | 0.357 | -0.200 |
  | 2 | 0.674 | 0.533 | 0.200 | -0.333 |
  | 3 | 0.604 | 0.274 | 0.000 | -0.274 |

  **Mean -0.269, median -0.274, 0 of 3 seeds favouring the treatment.**
  Neither cell beat autarky on any seed: `eff_round - floor` is negative in all
  six rounds, from -0.086 to -0.604.

- **Numbers -- behavioural (A3).** Repeat exchanges, read from settled state.

  | seed | `probe-bare` | `probe-constant` | diff |
  |---|---|---|---|
  | 1 | 0.88 (30/34) | 0.69 (11/16) | -0.19 |
  | 2 | 0.86 (19/22) | 0.65 (11/17) | -0.22 |
  | 3 | 0.50 (4/8) | 0.33 (2/6) | -0.17 |

  Settled exchanges fell in every seed: 34->16, 22->17, 8->6. The first repeat
  appears at episode 2 in five of six rounds and episode 1 in the sixth, in
  both cells.

- **Numbers -- comparison 1 (the fix).** `max-bare` -> `probe-bare` on the same
  three islands, across runs: 0.000 -> 0.556, 0.461 -> 0.533, 0.472 -> 0.274.
  Two up, one down; n=3 across runs, and A1's weakness applies.

- **Numbers -- secondary.** Alive fraction, the mean over ten episodes of the
  share of traders that produced that episode:

  | | alive (mean of 3) | settled | refused | talk |
  |---|---|---|---|---|
  | `probe-bare` | **0.78** (0.88 0.85 0.60) | 273 | 24 | 0 |
  | `probe-constant` | **0.59** (0.68 0.45 0.65) | 226 | 26 | 0 |

  Zero-agent episodes, denominator 30 episodes per cell: `probe-bare` 17,
  `probe-constant` 28. `eff_episode` reported, not interpreted.

- **Assumptions that did not hold:** **A4**. It said persistence should not
  differ systematically between cells and named the consequence if it did. It
  does: 0.78 against 0.59, lower in the treated cell on all three seeds.
  **The efficiency difference is therefore confounded with a persistence
  difference and this run cannot separate them** -- the same failure, in the
  same direction, that A3 produced in run 005. The repeat-exchange difference
  is a share and so less mechanically driven by volume, but fewer exchanges are
  fewer chances to repeat, and it is not independent of the attrition either.

  **A3 holds** in that the block moved settled behaviour and not talk -- but
  moved it downward, which is not the direction A3 anticipated. **A1** holds;
  the diff between the two commits carries the deadline change and the arm
  wiring only. **A2** holds: the paired difference (0.269) exceeds run 005's
  (0.207) and the 0.10 the hypothesis named. **A5** holds -- no session failed
  to join, so nothing was rescued and no log carries a runtime error.

  **The manipulation check is missing and cannot be recovered.** `talk` is 0 in
  all six rounds: no trader wrote a word of free text in either cell. Nothing on
  the board shows whether a treated trader read the block, so "ignored it" and
  "never attended to it" are not separable here.

- **Deviations:** D12, as specified, and **D13**, written before the relaunch.

## What this changed

**The stopping rule fired.** The record said, before the run: *"Would make me
stop adding text: both this and run 005 negative. Two independent additions,
one maximal and one minimal, both harmful, would say the cost is in the
adding."* Run 005's maximal treatment came in at mean −0.207 (4 of 5 seeds
against it); this minimal one at mean −0.269 (3 of 3 against it). Both
negative, both in the same direction, and both bought with the same currency:
a cell that trades less and stops sooner. **No further run in this experiment
adds instruction text to see whether it helps.**

**What the control refuted was the premise of the probe.** The question this
run opened with was whether traders fail to act on constancy across episodes.
They do not: `probe-bare` repeats 86–88% of its exchanges from episode 2 on,
in the two rounds with enough exchanges to say so, with no prompting at all.
Repetition was not the missing ingredient, and the rounds that repeat most are
still below their own autarky floor. That is a finding about the island, not
about the text.

**What cannot be concluded.** Not that the block was ignored — with `talk` at 0
in both cells there is no evidence either way about what a treated trader made
of it. And not that the block *causes* the efficiency drop, because A4 failed:
the treated cell also stopped sooner, and this design cannot separate the two.

**Next, and only if it is worth doing.** The per-bell restatement — the manager
sending each trader its own private block by `dm` at every bell — would test
recall separately from reasoning, since the private state is currently handed
over once at session start and is ten episodes back in context by the end. It
is a change to what the manager *repeats*, not to what it *instructs*, so it
does not violate the stopping rule above. It is not scheduled.
