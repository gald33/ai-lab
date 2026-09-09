# 004 — preflight gates

The checks between a specified run and a spent one. Run in order; each is free.
Record every result, with its commit, in the run record. See
[`experiments/GROUNDING.md`](../GROUNDING.md) for what each gate is for.

Paths below are relative to `experiment/`.

## 1. Smoke — does the basic flow work at all?

    python flow_experiment.py --islands 2 --periods 2 --json /tmp/smoke4.json

Expect: the four-arm table (silent, disclose, price, money), a record written,
and the arms' denominators matching the island count. Takes ~17s.

**Its numbers are not evidence.** At two islands, `1/2 ruined` on one arm is a
coin, not a finding — and ruin is precisely the quantity this experiment is
about, which makes a smoke number here unusually tempting to read. Don't.

This experiment has no test suite of its own. That is the gap in its preflight:
the smoke run is doing the work a suite should, and it only catches failures
loud enough to stop the script.

If it fails: it imports the economy this experiment shares with 002; a failure
here is usually that import, not the flow logic.

## 2. Calibration — does the instrument read?

The instrument is efficiency and the ruin rate over periods, and the design
turns entirely on per-period consumption being the *only* difference from the
world 002 ran. The gate is that the stock and flow columns can differ at all:

    python flow_experiment.py --islands 12 --periods 6 --json /tmp/cal4.json

Takes ~3 minutes. Expect efficiency off both its floor and its 1.0 ceiling on
the silent and disclose arms, and the `zero-period rate` and `recoveries`
columns non-zero somewhere. At these parameters that reads: silent 0.476
(12/12), disclose 0.457 (12/12), price 0.997 stock / 0.809 flow, with a
zero-period rate of 0.156 and 77 recoveries.

If flow reproduces stock exactly on every arm, per-period consumption is not
reaching the mechanism and the experiment cannot answer its question. The same
run also shows the effect the experiment is *about* — price ruins 6/12 under
stock and 0/12 permanently under flow — which makes this gate unusually easy to
mistake for the result. It isn't one: twelve islands is a calibration size.

Arm C reaching ~1.0 is expected — a correct shared price is the frontier by
construction, so the ceiling there is not a pinned instrument. Read the floor
and ceiling on the other arms.

## 3. Pilot — does it run, small, for real?

**Not applicable.** Every arm here is scripted and free; there are no model
calls and nothing to spend. Say "no pilot: scripted and free" in the run record
rather than leaving the gate blank.

If a later variant puts real agents on these arms, its pilot gate gets declared
here before its first run record.
