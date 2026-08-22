# Run 002 — Does anything converge, given enough episodes?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Every round this experiment has run has been three episodes long, and three
episodes is barely enough to fail once and recover. The screen's mean
`eff_episode` climbed 0.373 → 0.509 → 0.534 and then the round ended — a curve
still rising when the clock stopped. Nothing so far can say whether that curve
plateaus, and where.

So: one round, thirty episodes, and look at the trajectory. This is the first
run where a round is long enough for the threshold ladder to have a shape
rather than three points, and long enough for the accumulated-context channel —
the reason a round has more than one episode at all — to show whether it
carries anything.

It also gives the talk question a second, cheaper look. Run 001's calibration
could not be executed at pilot size (deviation D6). Thirty episodes at four
traders is 120 trader-episodes, against 8 in the pilot: **12 expected talk
messages under the screen's n=2 rate of 0.100**. That is not a substitute for
001's paired design — one round, one seed, no n=2 arm — and no comparison
between populations is claimed from it. It is a look at whether talk ever
appears when traders have run out of new things to try.

## Specification

| | |
|---|---|
| entry point | `run_v3.py` (commit recorded at the gate below) |
| conditions | none — a single cell, no contrast. This is a trajectory probe, not a comparison. |
| arms | `bare` — base instructions only, no advice block, no hint |
| units / counts | **1 round × 30 episodes × 180s**, 4 traders, 4 goods |
| seeds | 1 (the same island the pilot drew, so the pilot's two episodes are a sanity check on the first two here) |
| models | `claude-haiku-4-5-20251001`, one long-lived session per trader |
| stimuli | `stimuli/v3/base.md`, body sha256 `c1ff3e80038c66314adcfbf711f5f873d4d129fcb02a2321400b3200fdd2b342` |
| hub | managed Switchboard hub, one run-stamped workspace |
| command | `python run_v3.py --arms bare --rounds 1 --episodes 30 --episode-seconds 180 --agents 4 --out results/002-thirty` |
| cost | **go given 2026-08-22.** **4 agent sessions**, ~92 min wall clock. Few sessions, but each is long and its context grows all round, so token cost per session is far above a 3-episode round's. Paid: needs an explicit go, recorded here. |

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | A session survives 30 episodes. The turn cap now scales with episode count (`40 × episodes`); at 400 it would have bound here and cut agents off mid-round. | An agent stops acting partway through and its log shows the cap reached. |
| A2 | The manager sees every board message. It reads the most recent 500 rows every 1.5s and skips what it has seen, which is safe only while it drains faster than the board fills. | `drain_saturated` is true in the record — then some message may never have been read, and the round's counts are lower bounds. |
| A3 | The board is **not** a complete record of this round, and does not need to be. Hub messages expire after an hour; this round runs ~92 minutes, so the first half hour will have aged out before the bell. The authoritative record is the manager's per-episode ledger. | A number here can only be reproduced from channel history, which by then is partial. |
| A4 | Context accumulated across episodes is what a long round buys, and it persists for the whole round. | Trajectory is flat and indistinguishable from 30 independent episodes. |
| A5 | A silent agent chose silence; a session that could not start is a harness failure, told apart by the runtime's error signatures and the canary. | Zero activity together with a runtime error in the session log. |

## Hypothesis

- **Expect:** `eff_episode` rises over the first several episodes and then
  plateaus, with the plateau **at or slightly above** the autarky floor
  (0.642 on this island at n=4). Coverage failures concentrate early. Talk
  stays low but non-zero — a handful of messages over 120 trader-episodes.
- **Would surprise me:** a plateau well *below* the floor that thirty episodes
  never escape — traders locking into a bad pattern and repeating it, which
  the screen's flat-round finding says is exactly what they do when a pattern
  works. Or a late collapse after a stable plateau.
- **Would make me abandon the design:** no trajectory at all — episode 30
  indistinguishable from episode 1. Then accumulated context buys nothing
  here, and a round having more than one episode is not doing the work the
  design claims for it.

## Metrics for this run

Reported, not tested — a single round with no contrast supports no comparison,
and every number here is n=1.

- `eff_episode` across all 30 episodes, and `eff_round` against the one-episode
  frontier × k.
- The threshold ladder from `analysis/ladder.py`, which for the first time has
  30 points to place a curve on; never-cleared censored at k+1 = 31.
- `zero_agent_episodes` per trader-episode, and where in the round they fall.
- Talk per trader-episode, denominator 120. Descriptive only.
- Lapsed proposals per episode, from the ledger.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | `4777f14` | **pass** — `96 passed`, `stimuli unchanged`, `OK` |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | `4777f14` | **pass** — an agent's `switchboard-mcp` reached the hub |
| calibration | not applicable — no instrument is being asked to separate conditions here; this run compares nothing. The metrics are the ones run 001 and the ladder already established. | — | n/a |
| pilot | run 001's pilot, same code path, same population, same island: 4/4 acknowledged, 28 settled, 0 harness failures | `b26628e` | **pass** — reused, and the two shared episodes are checked against it |

## Failure modes anticipated

- **The turn cap binding mid-round.** Never reached at three episodes; at
  thirty it would have. Now scaled with episodes. If an agent still stops,
  the log says whether the cap was the reason.
- **Drain saturation.** Recorded per round as `drain_saturated`. If true, the
  counts are lower bounds and the record must say so.
- **Message expiry mid-round.** Expected, not a fault: the ledger is the
  record. It does mean an agent that reads far-back history late in the round
  gets less than one that read early, which is a property of the environment
  and is reported rather than corrected.
- **A session dying late.** Distinguished from silence by the runtime error
  signatures. A round that loses an agent at episode 20 is not a 30-episode
  round and is reported with the episode it was lost at.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
