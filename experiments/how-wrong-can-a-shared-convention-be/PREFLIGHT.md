# How wrong can a shared convention be? — preflight gates

*The checks that stand between a specified run and a spent one.
`tools/ground.py how-wrong --preflight` prints this file. Nothing runs them for
you — deliberately; see [`../GROUNDING.md`](../GROUNDING.md). The relative links
below resolve from `experiments/how-wrong-can-a-shared-convention-be/`, not from
here.*

Run in order. Each is free. Record every result, with its commit, in the run
record.

**Gates 2 and 3 are also rungs 0 and 0b of the ladder**, and their output is
not just a pass — it is the input to the thresholds in
[`PREREGISTRATION.md`](PREREGISTRATION.md). Nothing paid runs until both have
produced numbers and those thresholds are written down.

## 1. Smoke — does the basic flow work at all?

    python -m pytest experiments/how-wrong-can-a-shared-convention-be/tests -q
    python -m pytest experiments/which-part-of-a-convention-works/experiment/tests/test_calibrate.py -q
    python experiments/how-wrong-can-a-shared-convention-be/experiment/noise.py --games 2 --episodes 2 --json /tmp/smoke.json

Expect: the tests pass, and `noise.py` writes a JSON record with a
`zero_episode_share` per game and a printed denominator.

Takes: seconds.

Smoke parameters are chosen to be too small to mean anything. **The numbers a
smoke run prints are not evidence**; only that it printed them.

If it fails: usually the island import path
(`experiments/does-a-content-free-protocol-help` on `sys.path`) or a hub the
NPC runner could not reach.

## 2. Rung 0 — how far does this instrument move on its own?

    python experiments/how-wrong-can-a-shared-convention-be/experiment/noise.py \
      --replicates 8 --games 12 --traders 4 --goods 5 --episodes 4 --seconds 60 \
      --json experiments/how-wrong-can-a-shared-convention-be/results/rung0-noise.json

Same cell, same seeds, nothing varied, NPCs on every seat.

**Expect exactly zero, and that is a pass.** NPC policies are deterministic
given their seed, so replicates come back byte-identical — measured in run 001,
`capture` agreeing to sixteen digits. What this gate bounds is the *harness*:
how much the manager, clock and economy move on their own. Anything above zero
here is a defect to find, not a noise budget to spend.

**It therefore cannot set a threshold, and this gate is not H0b.** The
threshold-setting measurement replicates a *model* cell and costs money,
because agent sampling is the dominant term and no NPC run contains any of it.
Add `--vary-npc-seed` for the policy-draw component — still free, still not
agent variance, but a better lower bound than zero.

Report a between-replicate sd **per endpoint**, each with its denominator —
zero-episode share, `capture`, share above own autarky, `eff_round`.

**Budget the wall clock.** A game runs its episodes in real time — at 4 × 60s
plus the ack window that is over four minutes each, so the replication above is
**roughly seven hours serially**. Measured in run 001: 2 episodes × 45s came to
about two minutes a game. Give it an overnight slot or run games concurrently;
do not discover this at hour three and cut the replicate count, because the
replicate count is the whole measurement.

What this gate can still do is *fail the experiment* before any money moves: a
cell whose games settle nothing, or whose endpoints sit on a bound, is refused
by the runner with a non-zero exit rather than reported as precise.

For reference, the movement measured on the same manager by
`../do-they-take-a-handed-over-answer/runs/003-how-much-does-the-instrument-move.md`:
0.229 on captured gain (run-mean), 1.03 per round, 0.155 on `eff_round`, 0.085
on share-above-autarky, 0.073 on share-ruined — and a later control moved 0.114
on that last one. **Those are agent variance at a different table shape**, which
is the quantity H0b has to re-measure here. They are the right order of
magnitude to budget against and the wrong numbers to pre-register.

If it fails to run at all: the NPC seats could not be filled, or the hub was
unreachable. Both are harness, both go in the run record classified as such.

## 3. Rung 0b — does the instrument read? Does content error move it *here*?

    python experiments/how-wrong-can-a-shared-convention-be/experiment/calibrate.py \
      --islands 48 \
      --json experiments/how-wrong-can-a-shared-convention-be/results/rung0b-curve.json

The scripted δ sweep, **recalibrated at this island's table shape and
accumulation rule**. The published curve in
[`../which-part-of-a-convention-works/tier3-design.md`](../which-part-of-a-convention-works/tier3-design.md)
is a *stock* curve at 12 agents and does not transfer; see correction C2 in
[`README.md`](README.md).

*This gate used to name `calibrate_experiment.py --traders 4 --goods 5 --flow
--islands 48`, and **two of those flags do not exist**: that runner takes
`--agents`, defaults to 12 of them, has no flow mode, and reports efficiency
medians — the endpoint correction C1 retired. A gate whose command cannot run
is the root `CLAUDE.md`'s "absence drawn as a pass", arriving in the gate that
decides whether any money moves. Corrected in run 002, which also says why the
published runner was left alone rather than extended.*

**The table shape is swept, not fixed**, and that is the correction run 002
found rather than predicted. Whether the primary can read at all depends on
where in the game's allowed range (2–4 traders, 2–5 goods) the cell sits, and
where goods outnumber traders the scripted arm is at total ruin for **every** δ
including zero. Do not read that as "nothing happens there": the silent anchor
is printed beside it, and it is not ruined.

Expect: the zero-period share off both its floor and its ceiling, moving in δ,
with both perturbation directions reported separately, the silent anchor and
the efficiency bracket printed, and a verdict naming the shapes that read.

If it fails — the curve is flat in δ — **stop and do not spend.** A metric
pinned at either end returns a null that cannot be told apart from a real one,
and with no content axis there is nothing for the distribution axis to hold
constant.

## 4. Pilot — does it run, small, for real?

    <the smallest real-agent run: 2 islands, 4 seats, CS and silent only>

Expect: attempted / completed / failed with denominators; harness and timing
failures counted separately from agent behaviour; a cost per game that
extrapolates to rung 1's seed count.

If it fails: the failure modes this island actually has are in
[`games/island/what-the-first-games-found.md`](../../games/island/what-the-first-games-found.md)
— read it before diagnosing anything. The recurring shape is **the system
reporting success while doing nothing**, so a pilot that "passed" with no
settled trades has not passed.

## Known environment traps

- **`agent-switchboard` floor is 2.2.2** and a floor obliges an install rather
  than performing one. A host that has not reinstalled is an old reader and
  cannot open what this repo seals. Check with
  `pip download agent-switchboard -d /tmp/x --no-deps` and read
  `crypto.WHISPER_MARKER`.
- **A table seats 2–4 and runs exactly 1 round** (`games/island/protocol.py`).
  `episodes` is the within-round axis; there is no multi-round table.
- **`seconds` is a fixed ladder**, not any integer, and it is part of the
  scoreboard level.
- **A game that cannot seal is a practice game**, announced as one and never
  ranked. Practice games are kept and counted, never dropped from a
  denominator.
- **`ISLAND_REQUIRE_BROWSER=1`** for any page test, because a skip and a pass
  are the same green tick.
