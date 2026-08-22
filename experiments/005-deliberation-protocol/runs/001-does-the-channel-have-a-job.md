# Run 001 — Does the channel have a job?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

The ten-arm screen left 005's question unanswerable. A deliberation protocol is
a manipulation of *how agents talk*, and across 50 rounds and roughly 790
settled actions the traders produced **30 free-text messages**. With two
traders and four goods a `PROPOSE` is a sufficient statistic — it names the
partner, the goods and the terms — so a sentence has nothing left to do. A
protocol-versus-hint run on that channel would return a null that cannot be
told apart from a real one, which is the failure the calibration gate exists to
prevent.

So this run does not test any advice. It asks whether the channel can be made
live at all, by giving talk a job: with four traders a trader must find *who*
holds what it needs before an offer is worth making, and that is information an
offer cannot carry cheaply. Both cells get the base instructions only, which
also buys the bare baseline the screen never had.

The screen is written up in `reports/2026-08-22-005-screen-retrospective.md` as
exploratory output, not a result. Nothing from it is carried into this run's
expectations.

## Specification

| | |
|---|---|
| entry point | `run_v3.py` (commit `f471f99`) |
| conditions | population size: **2 traders** vs **4 traders**. Nothing else differs. |
| arms | `bare` in both cells — base instructions only, no advice block, no hint |
| units / counts | 12 seeds × 2 cells = **24 rounds**; 3 episodes × 180s each |
| seeds | 1–12, paired across cells (the same seed drawn at each n) |
| models | `claude-haiku-4-5-20251001`, one long-lived session per trader |
| stimuli | `stimuli/v3/base.md`, body sha256 `c1ff3e80038c66314adcfbf711f5f873d4d129fcb02a2321400b3200fdd2b342` |
| goods | 4 |
| hub | managed Switchboard hub, one run-stamped workspace per cell × seed |
| command | `python run_v3.py --arms bare --rounds 12 --episodes 3 --episode-seconds 180 --agents 2 --out results/001-n2` and the same with `--agents 4 --out results/001-n4` |
| cost | **96 agent sessions** (24 at n=2, 72 at n=4), ~33 min wall clock per cell at 10 concurrent. Paid: needs an explicit go, recorded here before the run. |

Environment-specific and load-bearing: the CA bundle `run_v3.py` assembles at
startup, without which every agent's MCP server fails while the manager stays
healthy. See the toolchain gate.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | With 2 traders an offer carries everything a message could, so talk is redundant *by construction* rather than by disposition. | Talk at n=2 is substantial here — it was near zero in the screen, so a jump means the silence had another cause. |
| A2 | With 4 traders, partner identity is information an offer cannot carry cheaply, so talk has a job. | Talk stays near zero at n=4, or rises but never names a partner. |
| A3 | Floor and frontier are the ones `score.py` computes, and are comparable across n on the capture scale (autarky 0, frontier 1). | A capture-scaled floor is not 0 for some seed, or `efficiency` returns a sandwich too wide to read at n=4. |
| A4 | A silent agent chose silence; a session that could not start is a harness failure. The two are separated by the runtime's error signatures and by the pre-flight canary. | A round reports zero talk *and* its session log carries a runtime error. |
| A5 | Message counts scale with trader count mechanically, so only per-trader-episode rates are comparable across cells. | The unnormalised count moves while the rate does not. |
| A6 | The manager settles exactly what the boards show; no number here comes from a self-report. | A metric cannot be reproduced from `results/*/v3.json` plus the channel history. |

## Hypothesis

- **Expect:** talk per trader-episode **at least 3× higher at n=4 than at
  n=2**, and at n=4 a majority of talk messages naming another trader. Coverage
  failures (zero agent-episodes per trader-episode) *no worse* at n=4 despite
  the harder matching problem.
- **Would surprise me:** talk rises at n=4 but coverage worsens — traders
  talking instead of covering. Or n=4 clears autarky more often than n=2 with
  no rise in talk, which would mean population helps for reasons unrelated to
  the channel.
- **Would make me abandon the design:** talk per trader-episode stays near zero
  at n=4. Then this environment cannot support a communication manipulation at
  any population worth paying for, and 005's question needs a different
  environment rather than another arm. Reaching that conclusion is what this
  run is for.

## Metrics for this run

**Primary — a new commitment, not previously pre-registered.**

- `talk_rate` — non-ACK, non-action messages per trader-episode. Denominator:
  traders × episodes (72 at n=2, 144 at n=4, per 12-seed cell).
- `talk_share` — of each trader's messages, the fraction that are talk.
- `addressed_talk` — share of talk messages naming another trader, and of
  those, the share followed by a settled exchange with that trader in the same
  episode. Volume without this is chatter, not coordination.

**Secondary — already reported by `score.py`.**

- `zero_agent_episodes`, per trader-episode so the cells are comparable.
- `eff_round` and `eff_episode`, paired against each seed's own floor, on the
  capture scale.
- The ladder from `analysis/ladder.py`: never-cleared rounds censored at k+1,
  clear-rate beside every rung.

Denominators printed everywhere. No round leaves one, including rounds that
settle nothing.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | `e801240` | **pass** — `96 passed`, `stimuli unchanged`, `OK` |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | `e801240` | **pass** — an agent's `switchboard-mcp` reached the hub |
| calibration | pilot at n=4 against the screen's n=2 talk rate | | not yet run — needs the pilot |
| pilot | `python run_v3.py --arms bare --rounds 1 --episodes 2 --agents 4` | | not yet run — **paid, awaiting the go** |

**Calibration is required here and is not being skipped.** The primary metric
is new, and an instrument that cannot move returns an unattributable null —
the trap this run exists to escape. It asks whether `talk_rate` separates two
conditions known in advance to differ. The screen supplies one side for free
(n=2, ~0.02 talk per trader-episode); the pilot at n=4 supplies the other. If
the pilot is indistinguishable from the screen, the instrument has not been
shown to read and the main run does not follow.

## Failure modes anticipated

- **Every agent's tools broken while the manager is healthy.** Killed a
  50-round run four minutes in. Agents reach the hub through `switchboard-mcp`
  with an explicit env and inherit nothing. Caught by the toolchain gate.
- **Workspace reuse.** Hub messages live an hour, so a reused workspace shows
  traders a previous run's bells. Workspaces are run-stamped; a board carrying
  messages older than its own schedule voids the round.
- **A session that starts and stops.** Agent behaviour, not harness failure,
  *unless* the log carries `API Error`, `Invalid MCP`, `not found` or
  `Execution error`. Reported as separate counts.
- **The clock outrunning the traders at n=4.** Four traders may not get through
  a matching round in 180s. That is a result about the clock, not a harness
  failure, and is reported as one — with lapsed-proposal counts from the
  per-episode ledger as evidence.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
