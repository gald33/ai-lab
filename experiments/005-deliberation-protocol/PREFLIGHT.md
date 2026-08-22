# 005 — preflight gates

The checks between a specified run and a spent one. Run in order; each is free.
Record every result, with its commit, in the run record. See
[`experiments/GROUNDING.md`](../GROUNDING.md) for what each gate is for.

Paths below are relative to this directory.

## 1. Smoke — does the basic flow work at all?

    python -m pytest . -q
    python tools/check_stimuli.py
    python tools/check_v2.py

Expect: `105 passed` (~12s); `stimuli unchanged`; and `OK` from `check_v2`, which
prints the hash table, the cell parity check, the domain-leakage check over both
documents, and the protocol/placebo length match.

The freeze checks are part of smoke on purpose. A moved stimulus is a different
experiment wearing the old pre-registration, and it is silent unless checked.
**Never re-freeze a hash to make a check pass** — a moved stimulus is a
deviation, written before the run it affects.

Then the free scripted sweep end to end, too small to mean anything:

    python experiment/pilot_experiment.py --worlds 2

Expect: the sweep table, `27 configurations evaluated`, and
`harness failures across the whole sweep: 0`. **`0 accepted` at two worlds is
not a result** — the acceptance band cannot be met at that size. The only thing
this establishes is that the sweep runs and the harness-failure counter is zero.

### The agent's own toolchain

    python -c "import run_v3; run_v3.preflight()"

Expect: `preflight: an agent's switchboard-mcp reached <hub>`.

An agent reaches the hub through `switchboard-mcp` with the environment
`run_v3.py` hands it, and nothing else — the manager reaches it through the
parent environment instead. So the manager can be fine while every agent is
broken, and that is not hypothetical: a fifty-round run died four minutes in
with every session reporting every Switchboard tool as an internal error, and
nothing upstream looked wrong. The check spawns the MCP server exactly as an
agent gets it and calls one tool.

This is declared here as well as being called by `run_v3.py` at startup,
because a gate that only runs inside the thing it guards cannot be recorded
against a commit before the go.

Failure means a harness fault, never agent behaviour, and it is the one thing
the pilot below is worst at telling you: a session that starts, finds its
tools broken, and stops reads exactly like an agent that chose to stop.

## 2. Calibration — does the instrument read?

The pilot acceptance criteria in [`PREREGISTRATION-v2.md`](PREREGISTRATION-v2.md)
*are* the calibration, and they were written to be: P1 requires the realised `W`
to sit meaningfully below the exchange ceiling, P2 that it clear the autarky
floor often enough. An instrument pinned at either end returns a null that
cannot be told apart from the real one — and 005's headline is a null, which is
exactly why this gate carries the most weight here.

    python experiment/pilot_experiment.py --worlds 40

Expect: the full sweep scored against every criterion, reported whether or not
any configuration passes, with the autarky floor and the exchange ceiling
printed alongside every cell.

The exchange ceiling is asserted as 1.0 by the first welfare theorem rather than
estimated. That assertion is an assumption of every run here and belongs in the
run record as one.

## 3. Pilot — does it run, small, for real?

    python run_v3.py --arms bare --rounds 1 --episodes 2 --agents 2

The only gate that exercises the thing that actually costs money: real sessions
on the native Switchboard MCP server, a real board, the manager reading behind
them, and the clock advancing on wall time whether anybody speaks or not.

Expect: per arm, per round — sessions started / completed / failed with
denominators; the board written; the manager's settled record; and a cost that
extrapolates to the full cell.

What this gate exists to catch, and nothing else can:

- **a silent agent versus a session that could not start.** These are different
  events and the numbers must separate them. An agent that says nothing has said
  nothing; a session that failed to launch is a harness failure.
- **messages the manager will not recognise.** The manager settles formatted
  board messages and must never repair a malformed one into a plausible one, so
  a format the agents never produce shows up as an economy that never runs.
- **a clock that closes the episode before anyone has acted.** Nothing waits for
  an agent; the bell rings anyway. Two episodes is enough to see whether the
  window is survivable.

Paid cells do not run without an explicit go, recorded in the run record against
the extrapolated cost.

## Known environment traps

- `run_v3.py` imports `barter.economy` from **002's** `experiment/` directory.
  That is a declared code dependency, not grounding — 002's documents are still
  out of scope here. If the import fails, 002's tree has moved.
- The switchboard server extra (`fastapi`) is needed by the parts that stand up
  a hub. Missing it fails as `ModuleNotFoundError`, which reads like a broken
  test rather than a missing dependency.
- Per-agent working directories under `results/*/*/T*/` carry a `.mcp.json`
  with a hub token and are gitignored. The rule was once `results/v3/*/T*/`,
  which silently stopped covering a run written anywhere else. The result of a
  run is the manager's record and the hub's channel, never an agent's scratch
  dir.
