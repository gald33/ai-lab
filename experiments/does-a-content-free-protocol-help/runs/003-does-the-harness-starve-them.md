# Run 003 — Is it the harness starving them, or can they not do this?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Run 002 aborted: every session ended itself early, each one reasoning about the
episodes it had been told still remained (D7, and D7a which withdraws D7's
stated cause). That leaves a question the experiment cannot proceed past —
whether a thirty-episode round is impossible *for these agents*, or impossible
*as this harness presents it*.

This run is a **manipulation check**, not a test of any advice. It asks whether
the environment can sustain a long round at all when the two obvious starvations
are removed. Its result cannot be read as evidence about deliberation
protocols, and one of its cells is a domain instruction that would be
disqualifying in that context.

## Specification

| | |
|---|---|
| entry point | `run_v3.py` (commit recorded at the gates below) |
| conditions | three cells, one factor each against the control |
| | **`persist-bare`** — control. Identical to run 002 except the clock. |
| | **`persist-nocount`** — the round's length is never stated. The manager announces five episodes at a time and says only that the round is still running. |
| | **`persist-improve`** — told to treat each episode as an attempt to beat the last. A domain instruction, and named as one. |
| units / counts | 1 round per cell × 3 cells; **30 episodes × 45s**, 4 traders |
| seeds | 1, the same island in all three cells |
| models | `claude-haiku-4-5-20251001`, one long-lived session per trader |
| stimuli | `stimuli/v3/base.md` body sha256 `c1ff3e80038c66314adcfbf711f5f873d4d129fcb02a2321400b3200fdd2b342`; `persist-improve` adds `stimuli/persist/improve.md`, which is **not frozen** |
| hub | managed Switchboard hub, one run-stamped workspace per cell |
| command | `python run_v3.py --arms persist-bare persist-nocount persist-improve --rounds 1 --episodes 30 --episode-seconds 45 --agents 4 --no-control --out results/003-persist` |
| cost | **go given 2026-08-22.** **12 agent sessions**, ~24 min wall clock; cells run concurrently. Paid: needs an explicit go, recorded here. |

`--no-control` is passed deliberately: `persist-bare` *is* this run's control,
and the guard only recognises the arms named `bare`/`placebo`. Recorded rather
than worked around silently.

**Why 45s and not run 002's 180s.** The control cell doubles as the
clock-versus-count discriminator D7a asked for. At 45s, episode 3 arrives about
two minutes in instead of seven. If `persist-bare` agents still stop around
episode 3, duration was never the mechanism; if they run to about episode 9,
it was. Holding 180s would have answered the same question at four times the
wall clock and told us nothing extra.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | Persistence is readable from settled state: the last episode in which a trader acted is when it was still alive. | A trader is alive but silent for many episodes, so "last acted" understates it. Mitigated by reading the ledger's per-episode `produced` list as well. |
| A2 | The three cells differ in exactly one thing each against the control. | The hidden-horizon cell leaks the count somewhere — tested offline; or `improve.md` implies a horizon and so moves two things at once (see the confound below). |
| A3 | Shortening the episode to 45s does not itself make the task impossible — four traders can still produce and settle an exchange inside it. | Every cell collapses at episode 1–2 with no settled exchanges, in which case the clock broke the economy and the run says nothing about persistence. |
| A4 | An agent that stops has chosen to; a session that could not start is a harness failure, separated by runtime error signatures and the canary. | A cell shows zero activity together with a runtime error in its logs. |
| A5 | One round per cell is enough to see a difference of the size run 002 showed (sessions ending at episode 3 of 30). | Cells differ by one or two episodes, which one round cannot resolve — then the answer is "no detectable difference at n=1", not "no difference". |

**Named confound.** `persist-improve` implies that more episodes are coming and
gives a reason to stay, so it carries part of `persist-nocount`'s mechanism.
The 2×2 that would separate them was dropped to save four sessions. If
`improve` sustains and `nocount` does not, that is *a* reason to continue
mattering — not evidence about which reason.

## Hypothesis

- **Expect:** `persist-bare` collapses again, around episode 3, at roughly two
  minutes — showing duration was never the mechanism. At least one of the other
  two cells runs materially longer.
- **Would surprise me:** all three collapsing at the same episode. That would
  mean neither the announced horizon nor a reason to continue is what ends a
  session, and the cause is something none of the three candidates in D7a name.
- **Would make me abandon the design:** all three running the full thirty
  episodes, including the control. Then run 002's abort was about its 180s
  clock after all, D7a's reasoning is wrong, and the trajectory probe should
  simply be re-run at 45s.

## Metrics for this run

**Primary — new, and declared as new.**

- `last_episode_acted`, per trader: the highest episode index in which that
  trader produced, proposed or approved. Denominator **120 agent-episodes**
  (4 traders × 30) per cell.
- `alive_fraction`: agent-episodes with the trader still acting, over 120.

**Secondary.** `eff_episode` trajectory, `zero_agent_episodes`, settled and
refused counts, talk per trader-episode. All descriptive: a cell where everyone
stops at episode 3 has no economics worth reading, and none of these are
comparable across cells that ran for different lengths.

Denominators printed everywhere; no cell or round leaves one.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | `47363d1` | **pass** — `98 passed`, `stimuli unchanged`, `OK` |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | `47363d1` | **pass** — an agent's `switchboard-mcp` reached the hub |
| calibration | not applicable — this run compares three cells against each other on a count read from settled state; no instrument is being asked to separate conditions it has not separated before. The offline gates on the hidden horizon stand in for it. | — | n/a |
| pilot | run 001's pilot covers the code path, population and hub; the clock is new and untested at 45s, which A3 names | `b26628e` | reused, with A3 carrying the residual risk |

## Failure modes anticipated

- **The 45s clock breaking the economy** rather than testing persistence (A3).
  Read the settled counts in episode 1 before reading anything else.
- **A cell whose agents never started**, separated from silence by the canary
  and the runtime signatures, and reported as its own count.
- **The horizon leaking** in the hidden cell — gated offline, and the board is
  checked for the string after the run.
- **Message expiry**: at 45s × 30 the round is 24 minutes, inside the hub's
  one-hour TTL, so unlike run 002 the board should remain a complete record.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `results/003-persist/v3.json`.
- **Ran:** 3 cells attempted, **3 completed**, 0 aborted, 0 harness failures.
  12/12 sessions started, 12/12 acknowledged. **Every cell ran all 30
  episodes.** 25 min wall clock.

- **Numbers — primary (persistence).** Last episode in which each trader
  produced, proposed or approved, read off the board; denominator 120
  agent-episodes per cell.

  | cell | alive fraction | T1 | T2 | T3 | T4 |
  |---|---|---|---|---|---|
  | `persist-bare` | **0.80** | 19 | 30 | 17 | 30 |
  | `persist-nocount` | 0.63 | 6 | 25 | 30 | 15 |
  | `persist-improve` | 0.57 | 14 | 17 | 7 | 30 |

  The control has the highest persistence of the three. No horizon leak in
  `persist-nocount`: 0 occurrences of the count on its board.

  Against run 002 — same island, same population, same instructions, same
  announced horizon of 30, only the episode length differs:

  | | T1 | T2 | T3 | T4 |
  |---|---|---|---|---|
  | run 002, 30 × 180s | 3 | 3 | 4 | 8 |
  | run 003 `persist-bare`, 30 × 45s | 19 | 30 | 17 | 30 |

- **Numbers — secondary (economics).** `eff_episode` is **0.000 in 90 of 90
  episodes**, and `eff_round` is 0.000 in all three cells against a floor of
  0.642.

  | cell | settled | refused | starved agent-episodes | agent-episodes holding all four goods |
  |---|---|---|---|---|
  | `persist-bare` | 180 | 61 | 75 / 120 | 45 / 120 |
  | `persist-nocount` | 88 | 11 | 75 / 120 | 45 / 120 |
  | `persist-improve` | 105 | 32 | 79 / 120 | 41 / 120 |

  Episodes in which **all four** traders held all four goods: **0 of 90**.
  Traders starved per episode, pooled: 1 trader in 6 episodes, 2 in 34, 3 in
  45, 4 in 5. Missing goods are spread evenly (cloth 179, salt 177, bread 164,
  iron 140). Talk: 0 in all three cells, over 360 trader-episodes.

- **Assumptions that did not hold:** **A3**. It said a 45s episode would not
  itself make the task impossible, and named "every cell collapses at episode
  1–2 with no settled exchanges" as the falsifier. That is not what happened —
  180 exchanges settled in the control — so A3 is not false as written, but its
  intent fails: the economy ran and still scored zero everywhere, which A3 did
  not anticipate and the run cannot distinguish from a 45s clock too short to
  cover four goods. **A5** also fails in the direction it named: the cells
  differ, but with one round each and attrition varying by trader inside a
  cell, one round cannot resolve them.

- **Deviations:** D8 (both departures, as specified). No new deviation: nothing
  departed from the record during the run.

## What this changed

Two things, and the second was not what this run was for.

**The horizon is not what ended run 002.** Hiding the count did not help, and
neither did a reason to continue — both scored *below* the control on
persistence. What separates run 002 from this run is the episode length, and
neither the announced count (identical at 30) nor total elapsed time (22 min
here against 7 min there) explains it. That leaves idle time per episode as the
live candidate, which none of D7a's three named.

**At four traders the episode metric is pinned at zero.** An episode scores
non-zero only if every trader ends holding some of every good, and that
happened in 0 of 90 episodes despite 373 settled exchanges. `eff_episode`
cannot move at this population, so it cannot measure anything here — and run
001's design puts its n=4 cell on exactly this instrument. That comparison
cannot be run until the metric is fixed or the population is reduced, and it is
the calibration run 001's own gate was supposed to perform and could not.
