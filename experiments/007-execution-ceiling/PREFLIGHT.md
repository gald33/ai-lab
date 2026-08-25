# 007 — Preflight

Nothing spends until every gate has a recorded result **on the commit being
run**, written into the run record. A failed gate is a finding.

## Smoke

    cd experiments/007-execution-ceiling
    python -m pytest tests -q
    cd ../005-deliberation-protocol && python -m pytest . -q

Expect all passing in both: this experiment's plan properties, and the
instrument's own suite, which now covers the absolute acknowledgement deadline.

## The plan itself

    python plan.py 1

Expect four blocks whose transfers agree pairwise — every "get x g from Tj"
matched by Tj's "give x g to Ti". Checked by test, printed here to be read.

## Assembly

    python tools/show_prompt.py e-plan

Expect base instructions, then `## The plan you have been given`, then the
private block ending in that trader's own numbers.

## Toolchain

    python -c "import sys; sys.path.insert(0, '../005-deliberation-protocol'); \
        import run_v3; run_v3.preflight()"

## Pilot

**Required, and not reused.** The 30-second announcement window is new and its
risk is named in D2. A 2-seed pilot at the real timing must run first and
report the acknowledged count and the production count; if traders are still
producing, the window is survivable and the full run may proceed.
