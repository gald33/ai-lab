# <NNN> — preflight gates

*The checks that stand between a specified run and a spent one. Declared here,
per experiment, with the real commands. `tools/ground.py <NNN> --preflight`
prints this file. Nothing runs them for you — deliberately; see
`experiments/GROUNDING.md`. The relative links below resolve from
`experiments/<NNN>-<name>/`, not from here.*

Run in order. Each is free. Record every result, with its commit, in the run
record.

## 1. Smoke — does the basic flow work at all?

    <the offline test command>
    <the entry point at absurdly small parameters>

Expect: <what passing looks like — counts, "N passed", output written>.
Takes: <seconds>.

Smoke parameters are chosen to be too small to mean anything. **The numbers a
smoke run prints are not evidence**; only that it printed them.

If it fails: <what a failure here usually is for this experiment>.

## 2. Calibration — does the instrument read?

    <the command>

Expect: <the metric off its floor and its ceiling, and separating a
known-different pair — with the floor and ceiling printed>.

Needed when: <the metric or instrument is new or has moved>. If unchanged since
the last run that calibrated it, say so in the run record rather than leaving
this silently unrun.

If it fails: a metric pinned at floor or ceiling returns a null that cannot be
told apart from a real one. Stop; do not spend.

## 3. Pilot — does it run, small, for real?

    <the smallest real-agent run>

Expect: attempted / completed / failed with denominators, harness and timing
failures counted separately from agent behaviour, and a cost per unit that
extrapolates to the full run.

If it fails: <the failure modes this experiment actually sees>.

## Known environment traps

Things that have silently broken a run here before — a missing extra, a pin, an
env var, a service that must be up.
