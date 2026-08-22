# Run 004 — Is it the length of the episode, or the emptiness inside it?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Run 003 settled that a harness parameter ends these sessions, not the agents'
appetite for the task. Same island, same population, same instructions, the
same announced horizon of thirty episodes: at 180s the traders stopped at
episodes 3, 3, 4 and 8; at 45s they reached 19, 30, 17 and 30. Hiding the count
and giving a reason to continue both scored *below* the control, so neither the
announced horizon nor motivation is the mechanism.

That leaves the episode length itself doing the work, and two ways it could:

- **Length.** A 180s episode is simply too long a unit for a session to hold.
- **Emptiness.** A 180s episode is mostly waiting. An agent acts in the first
  half-minute and then spends the rest calling `checkin`, which caps at 25s and
  returns nothing. Its own exit language in run 002 complained about exactly
  this — "minimizing the cognitive overhead", "manage tokens efficiently".

This run holds the episode at 180s and removes only the emptiness.

## Specification

| | |
|---|---|
| entry point | `run_v3.py` (commit recorded at the gates below) |
| conditions | three cells |
| | **`idle-long`** — 180s episodes, manager silent within the episode. Run 002's conditions. |
| | **`idle-tick`** — 180s episodes, manager posts the time remaining every 30s. Same length, less empty. |
| | **`idle-short`** — 45s episodes, silent. Run 003's control conditions. |
| units / counts | 1 round per cell × 3 cells; **10 episodes**, 4 traders |
| seeds | 1, the same island as runs 002 and 003 |
| models | `claude-haiku-4-5-20251001`, one long-lived session per trader |
| stimuli | `stimuli/v3/base.md` only, body sha256 `c1ff3e80038c66314adcfbf711f5f873d4d129fcb02a2321400b3200fdd2b342`. No advice block in any cell. |
| hub | managed Switchboard hub, one run-stamped workspace per cell |
| command | `python run_v3.py --arms idle-long idle-tick --rounds 1 --episodes 10 --episode-seconds 180 --agents 4 --no-control --out results/004-idle-long` then `python run_v3.py --arms idle-short --rounds 1 --episodes 10 --episode-seconds 45 --agents 4 --no-control --out results/004-idle-short` |
| cost | **go given 2026-08-22.** **12 agent sessions**; the 180s cells run ~32 min concurrently, the 45s cell ~10 min. Paid: needs an explicit go, recorded here. |

Ten episodes, not thirty: at 180s every session in run 002 was gone by episode
8, so ten is enough to see the failure and costs a third of the clock. The two
episode lengths cannot share one invocation, so the run is two commands; both
are part of this record.

`--no-control` is passed deliberately — `idle-long` is this run's reference
condition and the guard only recognises arms named `bare`/`placebo`.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | Run 002's collapse reproduces in `idle-long`. Without that this run has no reference condition and answers nothing. | `idle-long` persists to episode 10. Then run 002's abort was not reproducible and every explanation built on it, including run 003's contrast, is unsafe. |
| A2 | A time-remaining tick every 30s materially reduces idle, because `checkin(wait=25)` returns with content rather than timing out empty. | Agents ignore ticks entirely — visible as `idle-tick` behaving exactly like `idle-long`, which is also this run's negative result. |
| A3 | A tick is a timing announcement and not a prompt: addressed to nobody, naming only the clock, telling no one to act. Gated offline. | Would be false if the tick named an agent or an action; it does neither. |
| A4 | Persistence is comparable across cells at equal **episode** counts even though wall clock differs, because the metric is the episode index reached. | Last-acted tracks wall clock rather than episode index across cells — reported both ways so this is visible. |
| A5 | A silent agent chose to stop; a session that could not start is a harness failure, separated by runtime signatures and the canary. | Zero activity together with a runtime error in a session log. |

## Hypothesis

- **Expect:** `idle-long` collapses by about episode 4, as run 002 did.
  `idle-short` persists to episode 10, as run 003 did. **`idle-tick` persists**,
  or at least clearly outlasts `idle-long`.
- **Would surprise me:** `idle-tick` collapsing exactly like `idle-long`. Then
  emptiness is not the mechanism and the length of the episode is doing the
  work by itself, which is a stranger fact and worth its own run.
- **Would make me abandon this line:** `idle-long` persisting to episode 10.
  Run 002's collapse would then be unreproduced, and the right response is to
  re-establish it before explaining it — not to explain it harder.

## Metrics for this run

**Primary.** `last_episode_acted` per trader and the alive fraction over **40
agent-episodes** per cell (4 traders × 10 episodes), read off the board.
Reported alongside the wall-clock time of each trader's last action, so length
and elapsed time can be told apart (A4).

**Secondary, descriptive only.** Settled, refused, talk; `zero_agent_episodes`.
Run 003 showed `eff_episode` is pinned at zero for four traders, so **no
efficiency number from this run means anything** and none is interpreted.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | `7435faf` | **pass** — `101 passed`, `stimuli unchanged`, `OK` |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | `7435faf` | **pass** — an agent's `switchboard-mcp` reached the hub |
| calibration | not applicable in the usual sense: the instrument is a count read off the board, and run 003 demonstrated it separates conditions (0.80 against 0.57). The offline gates on the tick's scope and wording stand in for it. | — | n/a |
| pilot | runs 001 and 003 cover the code path, population, hub and both clocks | `47363d1` | reused |

**Two false starts, before any data.** Run 004 was launched twice and stopped
twice: each time a session exited inside the first minute having never posted
to the board, changing the population of one cell — `idle-long` the first time
(3 traders against 4, biasing the reference cell toward the hypothesis) and
`idle-tick` the second. Deviation **D10** records the harness change that
followed: during the acknowledgement window only, a session whose trader has
never appeared on the board is relaunched once and counted. Neither false start
contributed data; both are reported in **Ran** below.

## Failure modes anticipated

- **`idle-long` not reproducing run 002.** Named in A1 as the thing that would
  void the run rather than a nuisance.
- **The tick crossing the line into prompting.** Gated offline on wording; the
  boards are checked afterwards for any tick naming an agent or an action.
- **Ticks flooding the board** so that reading history becomes expensive, which
  would be a second change riding along with the first. Six ticks per 180s
  episode against a board that carried ~37 messages per episode at four
  traders; reported as a message count per cell so it can be judged.
- **A session dying late**, separated from choosing to stop by runtime
  signatures.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `results/004-idle-long/v3.json` (both 180s cells),
  `results/004-idle-short/v3.json`, boards saved under `results/004-boards/`
  (151, 209 and 291 messages — all complete, none near the 500-row cap).
- **Ran:** 3 cells attempted, **3 completed**, 0 harness failures. 12/12
  sessions started and acknowledged; **0 rescues triggered** (D10). Two earlier
  false starts collected no data and are described under Preflight.

- **Numbers — primary.** Alive fraction over 40 agent-episodes per cell:

  | cell | alive | T1 | T2 | T3 | T4 | settled | refused |
  |---|---|---|---|---|---|---|---|
  | `idle-long` (180s, silent) | 0.72 | 5 | 4 | 10 | 10 | 60 | 2 |
  | `idle-tick` (180s, ticked) | **0.60** | 10 | 3 | 8 | 3 | 65 | 1 |
  | `idle-short` (45s, silent) | **1.00** | 10 | 10 | 10 | 10 | 122 | 10 |

  45 ticks delivered. Board messages: 151, 209, 291.

- **Assumptions that did not hold:** **A1**, the one named as run-voiding.
  `idle-long` was to reproduce run 002's collapse and did not: 0.72 here
  against 0.15 there, with two of four traders lasting all ten episodes. The
  reference condition is not run 002's, so **this run cannot answer the
  question it was opened for.**

  **A2** returns its negative case: `idle-tick` behaved no better than
  `idle-long` — worse, at 0.60 against 0.72 — so the ticks did not buy
  persistence. Because A1 failed, that comparison is between two conditions
  neither of which collapsed, and it cannot separate "ticks do not help" from
  "there was nothing to rescue".

  **A4** is why the failure is visible: `idle-long` ran 32 minutes for its ten
  episodes and `idle-short` 7.5, so the two differ in wall clock as well as
  episode length, and the record says so rather than reporting only episodes.

- **Deviations:** D9 (the tick, as specified) and **D10**, written after the
  two false starts and before the run proper.

## What this changed

**The idle hypothesis is unsupported, and the run that was meant to test it
lost its reference condition.** Ticking a 180s episode did not improve
persistence. But `idle-long` did not collapse either, so the honest reading is
that run 004 did not reproduce the phenomenon it set out to explain.

**Why the reference probably failed.** Run 002 announced thirty 180s episodes;
run 004 announced ten. Putting every persistence cell run so far on one scale:

  | cell | announced total | alive | per-trader spread |
  |---|---|---|---|
  | run 002, 30 × 180s | 90.0m | 0.15 | 3–8 of 30 |
  | run 004 `idle-long`, 10 × 180s | 30.0m | 0.72 | 4–10 of 10 |
  | run 004 `idle-tick`, 10 × 180s | 30.0m | 0.60 | 3–10 of 10 |
  | run 003 `persist-bare`, 30 × 45s | 22.5m | 0.80 | 17–30 of 30 |
  | run 003 `persist-nocount` | 22.5m | 0.63 | 6–30 of 30 |
  | run 003 `persist-improve` | 22.5m | 0.57 | 7–30 of 30 |
  | run 004 `idle-short`, 10 × 45s | 7.5m | 1.00 | 10–10 of 10 |

  The two extremes separate cleanly. **The middle does not:** 30 minutes gives
  0.60–0.72 and 22.5 minutes gives 0.57–0.80, overlapping ranges. Episode
  length alone does not order them either — 10 × 180s (0.72) sits inside the
  range of 30 × 45s (0.57–0.80).

**The methodological finding, which is the useful one.** Every cell here is one
round, and the spread *within* a cell is as large as the differences *between*
cells: `idle-long` holds traders at 4, 5, 10 and 10. Four runs have now each
overturned the last run's mechanism — the turn cap (A1 of run 002), then 220
calls (D7, withdrawn by D7a), then the announced horizon (run 003), then idle
emptiness (here). Every one of those was inferred from a single round.

The next thing to do about persistence is not another mechanism. It is the same
cell repeated enough times to know whether 0.60 and 0.72 are different numbers
at all.
