# 002 — preflight gates

The checks between a specified run and a spent one. Run in order; each is free.
Record every result, with its commit, in the run record. See
[`experiments/GROUNDING.md`](../GROUNDING.md) for what each gate is for.

Paths below are relative to `experiment/`.

## 1. Smoke — does the basic flow work at all?

    python -m pytest . -q

Expect: `171 passed, 1 skipped`. Takes ~30s. Tier 1 is scripted and the offline
gates drive the whole harness with a stand-in, so this covers the economy, the
flow, the calibration instrument and the LLM tool surface without a model.

Then the scripted arms end to end, at parameters too small to mean anything:

    python barter_experiment.py --islands 2 --rounds 10 --json /tmp/smoke.json

Expect: a table and a written record. **Its numbers are not evidence.** At two
islands every arm can report ruin, and that is a fact about the parameters.

If it fails: usually the dependency trap below, or Tier 2 harness movement —
the README is explicit that the Tier 2 harness is still moving, so a smoke
failure there is expected news, not a surprise.

## 2. Calibration — does the instrument read?

Tier 3 is instrument calibration by construction: efficiency as a function of a
convention's content error at known adherence. The gate is that the curve
*moves* — that δ separates.

    python calibrate_experiment.py --islands 6 --rounds 40 \
        --deltas 0.0 0.4 --directions flatten --adherences 1.0

Expect: a non-empty `scored` denominator on both δ rows, and δ=0.0 scoring
above δ=0.4. Autarky floor and the exchange ceiling printed alongside.

**A degenerate-parameter run does not calibrate anything.** At `--islands 2
--rounds 10` this prints `0/2 scored` and `2/2 ruined` on both rows — no
survivors, so no curve. That is the smoke gate's answer, not this one's; if the
scored denominator is zero, the gate has not run, whatever it printed.

If it fails: a flat or unscored curve means Tier 3 cannot answer its question at
these parameters. Stop; the design needs changing before anything is spent.

## 3. Pilot — does it run, small, for real?

    python barter_llm_experiment.py --islands 1 --rounds 5 --json /tmp/pilot.json

Expect: attempted / completed / failed with denominators; harness and timing
failures counted apart from agent behaviour; a per-island cost that extrapolates
to the full run.

Tier 2 is the paid tier and does not run without an explicit go, recorded in the
run record against the extrapolated number.

If it fails: the failure this experiment actually sees is a harness one being
scored as behaviour. The README's honest recording of harness-bound Tier 2
numbers only works if the pilot can still tell the two apart.

## Known environment traps

- `requirements.txt` pins `agent-switchboard>=0.9.0`, but the tests import
  `switchboard.server`, which needs **`fastapi`**. Without it 36 tests fail with
  `ModuleNotFoundError: No module named 'fastapi'` — a missing extra, not a
  logic failure. Install it before reading a red suite as a finding.
- Switchboard is pinned at ≥0.9 because the muster reads presence and the order
  board reads `updated_by`; neither existed earlier. An older version fails in
  ways that look like agent behaviour.
