# Run 007 — Is the autarky floor a floor these agents can reach?

**Opened:** 2026-08-22 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Every efficiency number this experiment has reported is measured against
`autarky()`, and `autarky()` is a **closed-form optimum**: maximising
`Σ_g α_g log(capacity_g · s_g)` subject to `Σ_g s_g = 1` gives `s_g = α_g`.
It assumes an agent that solves its own labour allocation perfectly, alone.

Nobody has shown these agents can. So "below the autarky floor", written into
runs 003–006, may be reporting a trading failure, or may be reporting that the
benchmark is a standard the agents never meet even with nobody to negotiate
with. Those are different findings and the runs so far cannot tell them apart.

**The peopled boards cannot settle it.** Computing `u(produced) / u(autarky
optimum)` over run 006's 164 production acts gives a pooled mean of 0.361 with
9 acts at the optimum — but a trader who produces two of four goods intending
to trade into the rest scores 0 there through Cobb-Douglas, not through
incompetence. The measure only means what it says when trade is impossible.
Hence a solo run.

**This does not reopen the stopping rule** fixed in run 006. It adds no
instruction text and tests no instruction. It measures the yardstick.

## Specification

| | |
|---|---|
| entry point | `run_v3.py --solo` (commit recorded at the gates below) |
| conditions | **`solo`** — base instructions, one trader on its own board, no counterparties. No second cell: the comparison is against a computed optimum, not against another arm. |
| units / counts | 3 seeds × 4 traders = **12 solo rounds**, 10 episodes × 180s |
| seeds | 1–3, the islands runs 005 and 006 used. Islands are still drawn at 4 agents, so each trader keeps the capacities and tastes — and therefore the autarky optimum — it had there. |
| models | `claude-haiku-4-5-20251001` |
| stimuli | `stimuli/v3/base.md`, unchanged and unmodified for solo. See D14. |
| command | `python run_v3.py --arms solo --rounds 3 --episodes 10 --episode-seconds 180 --agents 4 --solo --no-control --out results/007-solo` |
| cost | **12 agent sessions**, ~33 min, twelve rounds in two waves. |
| go | Given by the owner on 2026-08-22 ("go"), before launch. |

## Metrics for this run

**Primary — solo capture.** `u(produced) / u(autarky optimum)` per production
act, computed by `analysis/solo_floor.py` from the manager's own settlement
notes. Reported as: mean and median over all acts, the share within 1% of the
optimum, and the same broken down by trader and by episode index.
Denominator = production acts settled; episodes with no production are counted
separately and never silently dropped.

**Secondary.** Production acts per trader-episode (denominator 120
trader-episodes); episodes in which a solo trader produced nothing; alive
fraction; talk. `eff_round` is written by the scorer and is **meaningless here**
— three of four agents have no session — and is neither reported nor
interpreted.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | A trader alone has no reason to produce a corner bundle, so solo capture measures allocation skill rather than a trading intention. | Corner bundles appear anyway at rates like the peopled runs' — then the measure is picking up something other than skill and the run is inconclusive as designed. |
| A2 | Drawing the island at 4 agents and launching one leaves that trader's capacities, tastes and autarky optimum exactly as in runs 005–006. | A recomputed optimum differs from the one those runs used. |
| A3 | Absent counterparties do not stop a trader from producing at all. The base text speaks of other traders and the roster will show none. | Traders spend episodes waiting and produce little — reported as the D14 impurity biting, not as incompetence. |
| A4 | Production is settled the same way it is in a peopled round: same parser, same budget rule, same refusals. | Refusal counts or reasons differ in kind from run 006's. |

## Hypothesis

- **Expect:** solo capture well below 1 — I would guess a mean in 0.5–0.8 with
  few acts at the optimum. The closed form is a calculation, not an obvious
  move, and nothing in the instructions names it.
- **Would surprise me:** a mean above 0.95. That would make the autarky floor a
  fair benchmark and would mean every deficit in runs 003–006 is a trading
  failure, cleanly.
- **What either result changes:** if capture is well below 1, runs 003–006 keep
  their numbers but their *"below autarky"* line is restated — the floor is an
  optimum the agents do not reach alone, so the deficit is not attributable to
  trading. That is an amendment to those records, not a rewrite of them.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python -m pytest . -q`; `python tools/check_stimuli.py`; `python tools/check_v2.py` | (below) | |
| toolchain | `python -c "import run_v3; run_v3.preflight()"` | (below) | |
| calibration | not needed — solo capture is read from settled state against a closed form, not estimated. `tests/test_solo_floor.py` checks the measure calls the autarky split 1.0 and a corner bundle 0.0. | — | |
| pilot | runs 001, 003–006 cover this code path, clock, hub and model. The solo path is new and is covered by the smoke gate and by the first round's board being read before the wave completes. | reused | |

## Failure modes anticipated

- **The solo trader waits for counterparties who do not exist** (A3, D14).
- **A corner bundle produced out of habit rather than intent** (A1), which
  would make the measure inconclusive rather than wrong.
- **A session that never joins**, rescued once and counted (D10).
- **Twelve rounds in two waves**, so the wave boundary is a clock difference
  between rounds — it is not a treatment and no cell depends on it.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
