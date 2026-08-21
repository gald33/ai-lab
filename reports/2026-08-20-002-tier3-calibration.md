# 002 Tier 3 — the calibration instrument, built and run

**Date:** 2026-08-20 · **Status:** calibration half run; model half designed, unrun
**Cost:** none (no model calls)
**Records:** [`tier3_calibration_wide.json`](../experiments/002-barter-conventions/results/tier3_calibration_wide.json) (48 islands, the reported run) ·
[`tier3_calibration.json`](../experiments/002-barter-conventions/results/tier3_calibration.json) (12 islands, superseded — kept because its intervals are why it was re-run wide)

## Why the tier exists

002's ladder varies words, machinery and disposition together, so no gap
between rungs is attributable to any one of them. It also made efficiency both
the goal and the measurement, so "a good convention" and "a good economy" were
the same number.

Tier 3 replaces ranking with measurement, using the one property this island has
that no real system has: `economy.walras()` computes the competitive
equilibrium, so a convention can be **manufactured to a known content quality**
with correctness and sharedness as independent dials.

## What was built

`barter/calibrate.py` perturbs the equilibrium price vector by a parameter δ in
two directions:

- **`flatten`** — pull prices toward their common mean. At δ=1 every good is
  priced alike, which is what an agent that never heard a price believes; the
  direction interpolates the convention continuously down to *no convention*.
- **`sharpen`** — widen the spread. Ranking stays correct; the vector overstates
  how much better the best good is, so agents specialise harder than the island
  supports.

Both δ and the **realised relative distance** are recorded, because the same δ
means different things in the two directions and on different islands.

`Trader` gains an optional `announced` price. With it set, discovery is skipped,
so tatonnement cannot walk the vector back toward equilibrium and undo the
perturbation under measurement. Everything else is arm C untouched — the
specialisation rule, the acceptance test, the proposal search, the manager. The
price's provenance is the only thing that moved.

`run_island` gains `adherence`, handing the announcement to a **seeded shuffle**
of the agents rather than a prefix by index, so partial adoption is not
confounded with whatever the island's agent ordering correlates with. A
non-adopter falls back to arm A — no announced price, no floor, no
specialisation.

## Instrument validation

At δ=0 with full adherence, on the same islands as the published ladder
(`seed0=1`, matching `barter_experiment.sweep`):

| | efficiency | ruined |
|---|---|---|
| this instrument, δ=0 | 1.000 | 7/12 |
| published arm C (discovered price) | 0.997 | 6/12 |

The gap is exact-versus-discovered prices and runs in the expected direction:
handing agents the equilibrium exactly makes them specialise harder than
tatonnement's approximation does, buying the last 0.003 of efficiency and
costing one more ruined island. An instrument that did not reproduce arm C's
shape at δ=0 would be measuring something else.

## Claims

| # | claim | strength |
|---|---|---|
| 1 | **Efficiency carries no signal about δ.** The entire effect of content error is on whether an island survives, and it is binary | solid |
| 2 | Survival **cliffs** rather than slopes | solid |
| 3 | `sharpen` is far the worse mistake, and the gap is at errors too small to notice | supported |
| 4 | At δ=0 — a perfect convention, fully adopted — only 23/48 islands survive, which is a property of the harness and caps the instrument | solid |
| 5 | Partial adherence is catastrophic at every δ including zero | weak |
| 6 | The **CS − CP gap is not measurable at this tier at all** | solid (by construction) |

### The curve

48 islands per cell, full adherence, seeds 1–48. Benchmarks for this island set:
autarky floor 0.437, exchange ceiling 0.520. Intervals are Wilson 95%.

| δ | realised error | flatten survived | sharpen survived |
|---|---|---|---|
| 0.0 | 0.000 | 23/48 (0.34–0.62) | 23/48 (0.34–0.62) |
| 0.05 | ~0.019 | 19/48 (0.27–0.54) | **7/48 (0.07–0.27)** |
| 0.1 | ~0.039 | 18/48 (0.25–0.52) | 6/48 (0.06–0.25) |
| 0.2 | ~0.078 | 7/48 (0.07–0.27) | 5/48 (0.05–0.22) |
| 0.3 | ~0.116 | 9/48 (0.10–0.32) | 1/48 (0.00–0.11) |
| 0.5 | ~0.19 | 3/48 (0.02–0.17) | 0/48 (0.00–0.07) |
| 0.75 | ~0.28 | 0/48 (0.00–0.07) | 0/48 |
| 1.0 | ~0.37 | 0/48 (0.00–0.07) | 0/48 |

### Claim 1, which invalidates the design's own readout

Across the entire sweep — every δ, both directions, **121 surviving islands** —
survivor efficiency has median **0.972** and range **0.741–1.000**. It is 0.978
at δ=0 and 0.998 at δ=0.3 sharpen, where a single island survived.

Survivors are always near the frontier, because an island that manages to give
every agent every good was coordinated enough to trade well whatever the price
said.

**Consequence for the design:** `eff(·)` in the δ\* definition has to be read as
*survival*, not efficiency. Written as an efficiency comparison, δ\* would have
been estimated from a line that does not move. The pre-registered "cliff, not
slope" prediction is correct — in a different variable than the design named.

### Claim 4 — what the baseline says about the harness

At δ=0 the convention has no error in it, and half the islands still die. That
is not a convention effect. It is 002's accumulation rule: holdings accumulate
for the whole run and are scored once, so a production bet that misses is
permanent and Cobb-Douglas zeroes on it.

The whole curve runs from 48% survival to 0% with **half the damage present
before the perturbation starts**. This directly motivated
[004](2026-08-20-004-stock-and-flow.md), which confirms the diagnosis.

### Claim 6 — the tier's hard limit

A scripted trader has no beliefs about other agents. Announcing a vector *to the
island* and handing the same vector *privately* therefore produce byte-identical
behaviour, at every δ.

So the CS − CP gap — the value of common knowledge with content held fixed,
which is the entire claim about sharedness and the reason the tier exists — is
not measurable by scripts. **The paid tier is not a more realistic version of
the free one; it is the only place one of the three axes exists.** This is a
sharper division of labour than the design assumed, and it is worth knowing
before money is spent.

## Threats to validity

1. **Claim 5 is weak and should not be cited.** Partial-adherence cells come
   from the 12-island run only, whose survival intervals span ~0.19–0.68. The
   ordering among partial levels (0.75 appearing worse than 0.5 and 0.25) is not
   resolvable at that sample size and is *not* claimed.
2. **δ is not a welfare distance.** It is a distance in price space; the
   efficiency cost of a given δ is what the calibration measures rather than
   assumes. Do not read δ as "how much worse this convention is".
3. **Both perturbation directions are monotone in the spread.** A non-monotone
   or rank-scrambling perturbation was not tried, and would be a different
   mistake again.
4. **Escrow is one-sided and unchanged**, so the arms cannot be separated from
   it here any more than in the published ladder.
5. **Claim 3's asymmetry is read off non-overlapping-ish intervals** at matched
   realised error (19/48 vs 7/48 at ~0.019). It is a large effect but a single
   sweep.

## Corrections filed against existing work

**002's Tier 1 benchmark line was stale.** It read "autarky floor 0.405,
exchange ceiling 0.493". Current code prints **0.403 / 0.484** on the same
islands (seeds 1–12, 12 agents, 5 goods) while reproducing every arm number in
the published table exactly — 0.476, 0.457, 0.997 with 6/12 ruined, 0.872 with
10/12. The README was corrected to match the code.

*A reviewer should check this specifically.* A published number was changed; the
arm numbers reproduce and the benchmark numbers did not, which is consistent
with the benchmark row having been written from a different run, but that is an
inference rather than something established.

**36 test failures on a clean checkout were a missing `fastapi`**, not broken
code. With it installed, the suite passes.

## Review targets

1. **`calibrate.py::perturb`** — is `flatten` at δ=1 genuinely "no convention",
   and does `sharpen` really preserve rank at all δ? Both are asserted by gates,
   but the gates were written by the same author as the function.
2. **The δ=0 validation.** Efficiency 1.000 vs published 0.997 and 7/12 vs 6/12
   is explained as exact-vs-discovered prices. That explanation is plausible and
   untested; an alternative is that the announced path differs from arm C in
   some way not intended.
3. **The stale-benchmark correction** — see above.
4. **`run_island`'s adopter shuffle** — confirm partial adherence is not
   confounded with agent index in some residual way.
5. Whether survival is the right primary readout, or whether some
   all-island-defined welfare measure would carry more than a binary.

## Reproduction

```bash
cd experiments/002-barter-conventions/experiment
pip install -r requirements.txt
python calibrate_experiment.py --islands 48 --agents 12 --goods 5 \
    --adherences 1.0 --json ../results/tier3_calibration_wide.json
python -m pytest tests -q
python ../analysis/curve.py ../results/tier3_calibration_wide.json
```
