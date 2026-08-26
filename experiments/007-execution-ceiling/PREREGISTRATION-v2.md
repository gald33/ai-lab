# 007 — Pre-registration v2

**Frozen 2026-08-23, before run 002 ran.** v1 stands as run 001's frozen design
and is not revised.

## What run 001 established

Handed the island's equilibrium, traders produced it **214/214** and reached
+0.709 captured gain against a control, 9 of 12 seeds, unconfounded by presence
(0.90 against 0.89). But only **112 of 144** named exchanges settled, and the
rounds divided almost totally: of the six where every exchange settled, five
beat their floor; of the six where any was missing, one did.

`FINDING-where-the-plan-breaks.md` located the cause: partners and goods are
right (only 7% of settled combinations are off-plan) but **quantities drift** —
53% of flows are the planned amount, 22% under half, 12% over. Over-giving
starves a later trade, which is what produces the missing exchanges.

The plan makes a trader hold a corner bundle that is worthless until its trades
complete. A plan 80% executed can be worth nothing.

## Question

Does **committing labour gradually** — half the plan, then the rest once the
exchanges have or have not happened — beat committing it all at once?

## Cells

| cell | instructions | rule |
|---|---|---|
| `t-plan` | base + `stimuli/plan.md`, run 001's block, byte-identical | split labour **allowed** |
| `t-tranche` | base + `stimuli/tranche.md` — the same economics, plus the advice to commit in pieces | split labour **allowed** |

- `plan.md` — `c5cca53acbec2638bd5aba9acf1de59998566bf4726bc3bf8ba54f1103ecb896`, 315 words
- `tranche.md` — `6131c10dfe2b12be75f55aa0e3ee9d5b991261b774945b3e9bf106d880201dbf`, 404 words

Both cells get the same per-trader plan from `plan.py` and **both** may split
labour (D4). The treatment is the advice, not the rule. No control cell (D5).

## Units

**12 seeds × 2 cells = 24 rounds**, paired. 5 episodes × 180s, 4 traders,
window 45s with acknowledgement asked by 30s. Seeds 1–12, as run 001.

## Primary endpoint

**Captured gain**, as in v1: `(u_achieved − u_autarky) / (u_plan − u_autarky)`
per acting trader-episode, averaged within a round, paired `t-tranche − t-plan`
per seed. **Mean and median both.** Denominator 12 seeds per cell.

## Co-primary — the mechanism this is supposed to fix

**Zero-utility trader-episodes**: the share ending with none of some good. The
simulation behind `PROPOSAL-partial-commitment.md` says a hedge should drive
this to near zero while a full commitment leaves it near 32% at the observed
completion rate. If captured gain improves and this does not fall, the
improvement is not the mechanism claimed and the run says so.

## Compliance, read from settled state

1. **Split usage** — productions per trader-episode. `t-plan` should sit near 1
   and `t-tranche` above it. If `t-tranche` does not exceed `t-plan` here, the
   advice did not reach behaviour: a **manipulation failure**, not a null.
2. **First-tranche size** — the labour share in a trader's first production.
3. **Exchange completion** — named exchanges that settled, against run 001's
   112/144.

## Thresholds, fixed now

- **Tranching works** if paired `t-tranche − t-plan` on captured gain is
  **≥ +0.15** on at least **9 of 12** seeds, **and** zero-utility
  trader-episodes are lower in `t-tranche`.
- **Harmful** at ≤ −0.15 on the same counting rule.
- **Anything else is a null**, including a difference of the right size carried
  by fewer than 9 seeds.
- **Reported regardless:** the absolute captured gain in both cells, and
  whether any round reaches 1.0.

## Stopping rule

If tranching works, the next question is how little of the plan is needed — the
ladder in `CLAUDE.md`, now with a survivable way to walk it. If it does not, and
compliance was high, then the loss is not the brittleness of the commitment, and
the remaining candidate is the exchange mechanism itself: proposals that lapse,
and quantities that drift with no atomic check against a named amount.

## What is not claimed

Nothing about coordination: the plan is computed from all four traders' private
data. Nothing about other models, islands, agent counts or episode lengths.
Production counts are not comparable across D4's boundary.
