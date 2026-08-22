# 001 — preflight gates

**None are declarable yet, and that is the honest state of this experiment.**

`experiment/` is empty: the runs that produced the existing data were taken with
code that is not in this tree, so there is nothing here to smoke-test, no
instrument to calibrate, and nothing to pilot. This file exists to say that
plainly rather than leave the gates looking merely unrun.

What that means for the next run:

- **Nothing further runs here until the code is in the tree and this file has
  real commands in it.** Declaring the gates is part of the same work as
  restoring the code, not a follow-up to it.
- The existing records cannot be gated retroactively. They are reported as
  pre-preflight — alongside the pre-registration gap noted in
  [`CLAUDE.md`](CLAUDE.md) — or not reported at all.
- Cleaning the existing data is not a run and does not need these gates. It
  needs a run record saying what was cleaned and on what rule, which is a claim
  about records that already exist.

See [`experiments/GROUNDING.md`](../GROUNDING.md) for what each gate is for, and
[`templates/experiment/PREFLIGHT.md`](../../templates/experiment/PREFLIGHT.md)
for the shape to fill in.
