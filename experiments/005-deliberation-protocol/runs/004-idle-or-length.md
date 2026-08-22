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
| cost | **12 agent sessions**; the 180s cells run ~32 min concurrently, the 45s cell ~10 min. Paid: needs an explicit go, recorded here. |

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
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | | |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | | |
| calibration | not applicable in the usual sense: the instrument is a count read off the board, and run 003 demonstrated it separates conditions (0.80 against 0.57). The offline gates on the tick's scope and wording stand in for it. | — | n/a |
| pilot | runs 001 and 003 cover the code path, population, hub and both clocks | `47363d1` | reused |

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

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
