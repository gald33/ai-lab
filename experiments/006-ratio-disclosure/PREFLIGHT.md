# 006 — Preflight

Nothing spends until every gate below has a recorded result **on the commit
being run**, written into the run record. A failed gate is a finding.

## Smoke

    cd experiments/006-ratio-disclosure
    python tools/check_stimuli.py
    python -m pytest tests -q

Expect: `OK` from the stimulus check — both body hashes matching the
pre-registration, placebo within 5% of ratios in length, no domain word in the
placebo — and all tests passing.

## Assembly

    python tools/show_prompt.py r-ratios | head -40

Expect: base instructions followed by `## Two ratios`, and the private state
block last. Confirms the treated cell is base + its own block and nothing else.

## Toolchain

    python -c "import sys; sys.path.insert(0, '../005-deliberation-protocol'); \
        import run_v3; run_v3.preflight()"

Expect: `preflight: an agent's switchboard-mcp reached ...`. This spawns the
MCP server exactly as an agent gets it and calls one tool. It is the gate that
would have caught the TLS failure that cost a run in 005.

## Pilot

None of its own. The instrument, clock, hub, model, population and episode
length are unchanged from 005's runs 005–007, which are its pilot. **This is
recorded as a reused pilot in the run record, with the runs named.**
