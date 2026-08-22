# 003 — preflight gates

The checks between a specified run and a spent one. Run in order; each is free.
Record every result, with its commit, in the run record. See
[`experiments/GROUNDING.md`](../GROUNDING.md) for what each gate is for.

Paths below are relative to `experiment/`.

## 1. Smoke — does the basic flow work at all?

    python -m pytest . -q

Expect: `42 passed`. Takes well under a second — Tier 1 is fully scripted, so
there is no excuse for running anything here without a green suite.

Then the sweep end to end, at parameters too small to mean anything:

    python promotion_experiment.py --replications 2 --steps 20 --starts middle

Expect: one row per rule, with intervals and denominators. **Its numbers are not
evidence.** At two replications the intervals are meaningless and a rule can
look decisively best or worst by luck — which is, pointedly, the very thing this
experiment exists to study.

If it fails: at this size, a failure is a wiring failure. Read it as one.

## 2. Calibration — does the instrument read?

Tier 1 is its own calibration: the rules are scripted and the good and lucky
candidates differ by construction, so the sweep must separate them.

    python promotion_experiment.py --replications 40 --starts worst middle best

Expect the rules to **separate on regret**, with non-overlapping IQRs. At
defaults they do: `bandit` lands around 11.5 (IQR 10.3–12.6) while `greedy`,
`nmin`, `interval` and `gated` all sit at 31.3 (29.4–32.9), across 40/40
replications with the denominator printed on every cell.

Note what that same output shows: the four tied rules are tied *exactly*, and
`promotions` and `entrenched` are both zero. The regret axis reads; the
promotion-dynamics columns are flat at these parameters, so a run that means to
say something about entrenchment must move the parameters until they aren't —
and check that here first, not after spending.

If every rule scores the same on regret too, the promoter is not being measured
and no Tier 2 result would be attributable. Stop.

## 3. Pilot — does it run, small, for real?

**Not applicable yet.** Tier 1 is scripted end to end and costs nothing; there
is nothing to pilot. Tier 2 — the same promoter over real instincts — is neither
designed nor run, and its pilot gate gets declared here in the same commit as
its design document, before its first run record.

Say "no pilot: Tier 1 is scripted and free" in the run record rather than
leaving the gate blank.
