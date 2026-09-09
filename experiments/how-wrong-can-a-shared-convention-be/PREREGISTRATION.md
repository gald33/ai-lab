# Pre-registration

**Frozen before any run. Nothing below has been measured.**

Amendments go in `DEVIATIONS.md`, dated, **before** the run they affect. A
threshold moved after seeing a number is not a threshold.

## Status of every number here

| kind | status |
|---|---|
| thresholds | **not yet nameable** — they are set by H0b, which is a paid run and has not happened |
| seed counts | **not yet nameable** — same reason |
| prediction | frozen below, and it can be wrong in public |
| endpoints | frozen below |
| stimuli | to be frozen by hash before rung 1 |

**This document deliberately does not contain a threshold yet.** The one
lesson this lab paid most for is that a threshold named before the
instrument's own movement is measured is a threshold chosen to be met. H0b
produces the movement; the thresholds are then written here, in an amendment,
before rung 1 runs. H0a is free and bounds the harness only — it cannot
substitute, and run 001 is why.

## Hypotheses, in the order they are tested

Each says what would refuse it. A hypothesis with no refusal condition is not
being tested.

### H0 — the instrument moves less than the effect we intend to claim

*Rung 0.* **Two measurements, and they are not the same quantity.** Split after
run 001 found that NPC replicates are deterministic and return a between-run sd
of exactly zero.

- **H0a, free** — replicate one NPC cell with nothing varied. This bounds the
  *harness*: how much the manager, clock and economy move on their own. Expect
  zero, and treat anything above zero as a defect in the harness rather than as
  a noise budget.
- **H0b, paid** — replicate one *model* cell with nothing varied, on the arm
  rung 1 will use. This is the number every threshold below is written against,
  because agent sampling is the dominant term and no NPC run contains it.

Report a between-replicate sd per endpoint with its denominator, for each.

**Refused if** the sd on the zero-episode share from **H0b** exceeds the
smallest CS − CP worth reporting. Then this experiment does not run in this form, and that is
the finding — the same finding
[`do-they-take-a-handed-over-answer`](../do-they-take-a-handed-over-answer/)
produced about its own instrument, arrived at before the money rather than
after.

### H0c — content error changes the outcome on *this* island

*Rung 0b.* The scripted δ sweep, recalibrated at this island's table shape and
accumulation rule (see README, correction C2).

**Refused if** the zero-episode share is flat in δ across both directions. Then
there is no content axis here to hold constant, and rungs 1–3 are unrunnable
whatever the distribution does.

### H1 — a correct, common convention beats no convention

*Rung 1.* CS at δ = 0 against `silent`, paired on identical seeded rounds.

**Refused if** CS does not beat `silent` by more than the H0b movement. Then
no distribution question is worth asking, because the content the distribution
is distributing does nothing.

### H2 — sharedness is worth something, with content held byte-identical

*Rung 2, and the reason this experiment exists.* CS against CP at δ = 0, plus
WP as the obedience control.

**The prediction: CS > CP.**

**Refused if** CS ≈ CP outside the H0b movement. That is a real result and
kills the strong form of "conventions matter": what a newborn agent needs would
be the right answer, not the same answer.

**Confounded rather than refused if** WP ≈ WS: agents were following
instructions and the sharedness never entered.

### H3 — δ\* > 0, and the common-arm curve cliffs rather than slopes

*Rung 3.* Carried over verbatim from the Tier 3 design, which pre-registered it
before its calibration ran, **and which got the variable wrong** — it predicted
the cliff in efficiency, and efficiency is exactly where the calibration found
no signal (README, correction C1). The shape claim survives; the variable is
now the zero-episode share.

Sharedness buys real tolerance for error and then punishes excess error harder
than privacy does, because agents specialise more confidently on a shared error
than on private doubt.

- **Wrong in the first clause** → conventions do not matter here.
- **Wrong in the second** → conventions are free after all, and Tier 1's "the
  convention adds leverage, not safety" was specific to that mechanism rather
  than general.

**What would make the tier uninterpretable** is adoption near zero across every
arm. That is a harness result and must be caught by H0c before any model is
paid for.

## Endpoints, frozen

**Primary.** Zero-episode share per trader — `zero_episodes` from
`viewer/scores.py`, divided by the round's episode count. Paired by island.

Chosen because it is a count, and because the hypothesis ledger's own summary
is that nine "did they do it at all" questions have clean answers here and
seven "how much did it help" questions do not.

**Secondary, reported always, never substituted for the primary.**

| endpoint | why it is secondary |
|---|---|
| `capture` | between-run sd 0.229 on the run mean, 1.03 per round |
| share of traders above own autarky | sd 0.085 |
| `eff_round` | sd 0.155 |

**Mechanism, on its own ledger.** Protocol adoption (countable per message,
needs no answer key) and strategy adoption (distance from the `walras()` split,
needs the answer key). Reported beside the outcome and **never added to it** —
`do-they-take-a-handed-over-answer` and 001's preserved negative both exist
because a well-calibrated mechanism with a flat outcome is a finding, and
reported as one number it is indistinguishable from a broken one.

## Design commitments

- **Paired on identical seeded rounds.** The round is the unit.
- **Denominators printed everywhere.** No failed run leaves a denominator.
- **Harness and timing failures classified separately** from agent behaviour.
- **Controls are replicated, not single-draw.** The lab's best-supported
  difference to date rests on four treated draws against one control draw, and
  that is why it is still only "probably".
- **Stimuli frozen by hash** before the first paid run; `tools/check_stimuli.py`
  guards them.
- **No paid run without an explicit go.**

## What is assumed, not re-tested

From the hypothesis ledger, whose rows this cites rather than re-deriving.
Each is `solid` there, and re-testing it would be spending to confirm what is
already known:

| assumed | evidence |
|---|---|
| instruction changes behaviour immediately and exactly | 214/214 settled productions matched a handed plan, control 0/215 |
| a granted capability nobody mentions is not used | 20 against 0, and 68% against 0 of 149, on two different capabilities |
| telling agents only *what* is worth saying does not work | 7 free-text messages across 200 trader-episodes |
| agents solve their own labour allocation alone | 0.972 of the closed-form optimum over 104 production acts |

**So the manipulation check in this experiment will succeed. That is not a
result and must not be reported as one.** What is under test is whether the
*distribution* of identical content changes the outcome.

## The trap this design is most likely to fall into

That the announced vector at δ = 0 is a **cheat**: it is computed from the
island's equilibrium, which is computed from every trader's private data. The
one treatment that repeatedly beat its control in this lab's history was
exactly such a cheat, and every legitimate treatment derived from it landed
inside the noise.

The defence is that this experiment is **not** claiming the announcement is
legitimate information an agent could have. δ = 0 is an instrument setting, not
a proposed intervention. The claim is about the *difference between two ways of
distributing the same vector*, and both arms carry the identical cheat, so it
cancels in the CS − CP contrast that is the point.

**Stated here so that it is not discovered in review**: any reading of a raw CS
or CP level as "how well agents can do" is invalid for that reason. Only the
contrasts are interpretable.
