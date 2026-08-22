# Run 005 — Does any text move this environment?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Four runs have gone into why sessions stop. That was not the question. This run
returns to it, and asks the strongest version first: **does any text change what
happens on this island?**

The treatment is deliberately maximal — talk, disclosure of needs and
capabilities, asking, naming a rate rather than only goods, improving an offer
instead of taking the first, and deciding production with intended trades in
mind. It mixes protocol and hint on purpose. If a text this strong moves
nothing, the 2×2 that separates protocol from hint is not worth running, and
that is the finding. If it moves something, there is a foothold to decompose.

The clock is the one the baselines were measured on: **10 episodes × 180s, four
traders**, matching run 004. Neither existing baseline is a clean survivor —
`idle-long` scored alive 0.72 and `idle-tick` 0.60 — so persistence is a known
hazard here, not a controlled variable, and this run measures it rather than
assuming it away.

## Specification

| | |
|---|---|
| entry point | `run_v3.py` (commit recorded at the gates below) |
| conditions | **`max-bare`** — base instructions only. **`max-talk`** — base plus `stimuli/max/talk.md`. |
| units / counts | 5 seeds × 2 cells = **10 rounds**, 10 episodes × 180s, 4 traders, 4 goods |
| seeds | 1–5, **paired**: each seed drawn identically in both cells |
| models | `claude-haiku-4-5-20251001`, one long-lived session per trader |
| stimuli | `stimuli/v3/base.md` body sha256 `c1ff3e80038c66314adcfbf711f5f873d4d129fcb02a2321400b3200fdd2b342`; `stimuli/max/talk.md`, **not frozen** |
| hub | managed Switchboard hub, one run-stamped workspace per cell × seed |
| command | `python run_v3.py --arms max-bare max-talk --rounds 5 --episodes 10 --episode-seconds 180 --agents 4 --no-control --out results/005-max` |
| cost | **go given 2026-08-22.** **40 agent sessions**, ~33 min wall clock — 10 rounds fit one concurrent wave. Paid: needs an explicit go, recorded here. |

`--no-control` is passed deliberately: `max-bare` is the control and the guard
only recognises arms named `bare`/`placebo`.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | `eff_round` can move at four traders. Run 004 gave 0.514, 0.219 and 0.144 across its cells, so the round-level metric is not pinned even though `eff_episode` is. | Every round returns the same `eff_round`, or all return 0.000. |
| A2 | Five paired seeds are enough to see an effect large enough to matter. The screen's arm means spanned 0.256 across ten arms; anything smaller than that is not what this run is for. | The cells differ by less than the within-cell spread across seeds — reported as "no effect this run can resolve", not "no effect". |
| A3 | Attrition at 180s does not differ systematically between cells. If the treatment keeps sessions alive longer, more trade follows mechanically and the efficiency difference is partly a persistence difference. | Alive fraction differs between cells — measured and reported per cell for exactly this reason, and any efficiency claim is then conditional on it. |
| A4 | The treatment actually reaches the behaviour it targets: talk rises in `max-talk`. | Talk stays near zero in both cells. Then the text did not take, and a null says nothing about what the text describes. |
| A5 | A silent agent chose to stop; a session that never joined is rescued once and counted (D10); a session that could not start is a harness failure by runtime signature. | A cell shows zero activity together with a runtime error. |

## Hypothesis

- **Expect:** `max-talk` shows a higher talk rate than `max-bare` — this is the
  manipulation check — and a higher mean paired `eff_round − floor`. I would
  call a mean difference of 0.10 or more, in the same direction on at least
  4 of 5 seeds, an effect worth decomposing.
- **Would surprise me:** talk rising sharply with no change in efficiency, which
  would mean the traders do what the text says and it does not pay.
- **Would make me abandon the 2×2:** no difference in either talk or efficiency.
  A text this strong failing to move either one means the protocol/hint
  decomposition has nothing to decompose, and 005's original question cannot be
  answered in this environment as built.

## Metrics for this run

**Primary.** Paired `eff_round − floor` per seed, mean and median over 5 seeds,
with both cells' raw values printed. Denominator: 5 seeds per cell, no round
dropped.

**Manipulation check, reported beside it, never instead of it.** Talk per
trader-episode; denominator 40 agent-episodes per round, 200 per cell.

**Secondary.** `zero_agent_episodes` per trader-episode; alive fraction per cell
(A3); settled and refused counts; the ladder from `analysis/ladder.py`.

`eff_episode` is reported but **not interpreted** — run 003 showed it is pinned
at zero for four traders.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | `b25893c` | **pass** — `101 passed`, `stimuli unchanged`, `OK` |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | `b25893c` | **pass** — an agent's `switchboard-mcp` reached the hub |
| calibration | the instrument is `eff_round`, and run 004 showed it separating conditions at 0.514 / 0.219 / 0.144 on this exact clock and population. The talk counter separated 30 from 0 in the screen. Neither is new or moved. | — | not needed — instrument unchanged since run 004 |
| pilot | runs 001, 003 and 004 cover this code path, population, clock and hub | `47363d1`, `7435faf` | reused |

## Failure modes anticipated

- **Attrition differing by cell**, which would make an efficiency difference
  partly a persistence difference. Measured, not assumed (A3).
- **A session that never joins**, rescued once during the acknowledgement window
  and counted (D10).
- **The treatment not taking** — talk flat in both cells (A4). This is a
  negative result about the text, and the record must not report it as a
  negative result about protocols.
- **Message expiry**: 10 × 180s is 32 minutes, inside the hub's one-hour TTL, so
  boards stay complete; they are saved to `results/005-max/boards/` at the end.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
