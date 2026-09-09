# 007 — Pre-registration

**Frozen 2026-08-23, before any cell ran.** Never revised in place.

## Question

Handed the island's solution — what to produce, what to hold, which exchanges
to make with whom — do agents execute it, and how much of the available gain
does that collect?

## Cells

| cell | instructions |
|---|---|
| `e-bare` | base, unchanged |
| `e-plan` | base + `stimuli/plan.md`, plus that trader's own plan appended to its private block |

`plan.md` body hash `c5cca53acbec2638bd5aba9acf1de59998566bf4726bc3bf8ba54f1103ecb896`, 315 words. The
per-trader numbers are computed by `plan.py` from the island and are not part
of the hash; `tests/test_plan.py` fixes their properties instead.

## Units

**12 seeds × 2 cells = 24 rounds**, paired on seed. 10 episodes × 180s, 4
traders. Announcement window 30s, acknowledgement asked by 20s (D2). Seeds
1–12 — seeds 6–12 are islands no run has used.

Twelve rather than five because the previous experiment's binding problem was
resolution: within-run sd of paired differences is 0.175, so n=12 resolves
about 0.14 and n=5 resolved nothing.

## Primary endpoint

**Captured gain**, per trader-episode in which the trader produced:

    captured = (u_achieved − u_autarky) / (u_plan − u_autarky)

`u_plan` is that trader's equilibrium utility, `u_autarky` its solo optimum.
1.0 means it collected everything the plan offered; 0 means it did no better
than staying home; negative means worse. Averaged within a round, then paired
`e-plan − e-bare` per seed. Denominator 12 seeds per cell, no round dropped.

Scale-free by construction, because the plan is worth 1.4×–2× autarky depending
on the island and a raw difference would not be comparable across seeds.

## Co-primary

**Presence** — the share of trader-episodes with any settled production —
always reported beside the primary. A same-signed move in both is reported as
confounded, as in 006.

## Compliance, read from settled state

1. **Production match** — share of settled productions whose labour shares are
   within 0.05 of the plan's, per good.
2. **Named exchanges settled** — share of the plan's transfers that settled at
   least once in the round.
3. **Episode of first full compliance** — the first episode in which all four
   traders produced their planned shares.

Compliance is the manipulation check. If `e-plan` does not exceed `e-bare` on
(1), the plan did not reach behaviour and the primary is uninterpretable —
reported as a manipulation failure, not a null.

## Thresholds, fixed now

- **The ceiling is real** if `e-plan − e-bare` on captured gain is **≥ +0.15**
  on at least **9 of 12** seeds.
- **Handing over the answer does not help** if the difference is within ±0.15
  or splits below 9 of 12 — a far stronger negative than any so far, because
  the treatment cannot be improved upon.
- **Harmful** at ≤ −0.15 on the same counting rule.
- **Reported regardless:** the absolute level of captured gain in `e-plan`, and
  whether any round reaches **1.0**.

## Stopping rule

If compliance is high and captured gain is not, no further instruction
experiment runs in this lab. The agents would have been given the answer, been
shown to follow it, and still not collected the gain — which would locate the
problem in the mechanism, and the next work would be mechanism design.

## What is not claimed

This is not a coordination result: the plan is computed from all four traders'
private data and dissolves the information problem by construction. Nothing
about other models, islands, agent counts or episode lengths.
