# How wrong can a shared convention be?

**Status: designed, nothing run. No go has been given and nothing here is a
result.**

## Question

**How wrong may a convention be and still be worth holding, purely because
everyone holds it?**

Written as a quantity: sweep the error δ in an announced price vector and find
**δ\***, the error at which *wrong-but-shared* stops beating
*correct-but-private*.

```
outcome(common, δ*) = outcome(private, δ = 0)
```

- **δ\* ≈ 0** — a convention is information transport. Sharedness is
  decoration, and the claim that opened
  [`which-part-of-a-convention-works`](../which-part-of-a-convention-works/)
  dies.
- **δ\* large** — a newborn agent should adopt the incumbent convention *even
  believing it substantially wrong*, and we have a bound on "substantially".

That is "conventions matter" as an exchange rate rather than a slogan.

## Why this question and not another

Because of one property of this island that no deployed system has: **a
convention can be manufactured to a known content-quality.**
`economy.walras()` returns the island's competitive equilibrium, so the
announced price vector can be set to *exactly right*, or wrong by a measured
amount, while everything else is held byte-identical.

In Lucille, or any real system, you never know whether the incumbent convention
is actually right. "Shared" and "correct" arrive together and cannot be pulled
apart. **Here they are two independent dials**, and that capability — not the
economy, and not the agents — is what this experiment is for.

The design is [Tier 3 of
`which-part-of-a-convention-works`](../which-part-of-a-convention-works/tier3-design.md),
whose scripted half ran and whose model half never did. Three things have
changed since it was shelved; §"What changed" below.

## The design

Two axes, and one cell off them.

**Content quality δ** — the distance of the announced vector from
`walras(island).prices`. Continuous, so arms are a sweep rather than a pair.
Two perturbation directions, reported separately because they are not the same
mistake:

- **`flatten`** pulls prices toward their common mean. At δ = 1 every good is
  priced alike, which is what an agent that never heard a price believes — so
  this direction runs continuously down to *no convention*.
- **`sharpen`** widens the spread. The ranking of goods stays right; the vector
  overstates how much better the best one is, so agents specialise harder than
  the island can support.

**Distribution** — how the vector arrives:

- *common* — announced to the island, **stated as having gone to every trader**;
- *private* — handed to each trader alone, with no indication anyone else has
  one;
- *absent* — no vector.

|  | private | common |
|---|---|---|
| **δ = 0** (correct) | **CP** | **CS** |
| **δ > 0** (wrong) | **WP** | **WS** |
| **no content** | `silent` | — |

**CS and CP differ in one sentence.** The vector is byte-identical; what
changes is whether the brief says every trader received it. That is the whole
treatment, and it is what makes the claim clean.

Each gap is a named quantity, not a rung on a ladder:

| gap | what it prices |
|---|---|
| **CS − CP** | the value of common knowledge, content held fixed. The claim lives or dies here. |
| **CS − WS** | the value of content, coordination held fixed |
| **WS − silent** | whether a shared *wrong* belief beats no belief |
| **WP ≈ WS?** | the obedience control. If equal, agents were following instructions and sharedness never mattered. |

### Why this cannot be answered by scripts, and therefore why it costs money

A scripted trader has no beliefs about other agents. Announcing a vector *to
the island* and handing the same vector *privately* produce **byte-identical
behaviour**, at every δ. So the scripted tier calibrates the content axis and
the adherence axis, and **the distribution axis does not exist in it at all.**

This is worth stating before anything is spent: the paid tier is not a more
realistic version of the free one. It is the only place one of the three axes
exists.

## What changed since this was shelved

Four things, each removing a blocker the Tier 3 design named.

**1. The ruin cliff was diagnosed and is gone.** The Tier 3 calibration found
that at δ = 0 — the exactly correct convention, fully adopted, no error at all
— only **23 of 48 islands survived**. Half the damage was present before the
perturbation started, which capped the whole instrument.
[`is-ruin-the-convention-or-the-commitment`](../is-ruin-the-convention-or-the-commitment/)
then showed that was the accumulation rule, not the convention: under flow,
permanent ruin goes **14/24 → 1/24** and **18/24 → 0/24** on the two priced
arms, with 176 and 162 recoveries. The arm ordering survives, so the ladder was
never measuring accumulation.

**The island this experiment runs on is already a flow island** — everything a
trader holds is consumed at each bell (`games/island/run_game.py`, and the
`episode` row of CLAUDE.md's vocabulary table). The dynamic range is back
without anything being built.

**2. The endpoint already exists and is the right shape.**
`viewer/scores.py` records `zero_episodes` per trader — a bounded per-agent
count. That is the endpoint class the hypothesis ledger says survives this
lab's noise, and it is flow-native.

**3. A private announcement is now actually private.** `whisper` shipped and
the wire is renamed as of 2.2.2, verified off the wheel. CP is a real cell
rather than a harness assertion.

**4. Half the noise measurement is free — and only half.** *This paragraph
originally read "the noise measurement is free". It was wrong, and run 001
measured it wrong within a day, so the correction is kept visible rather than
edited over.*

`games/island/npc.py` gives three heuristic policies, and heuristics are
**deterministic given their seed**: two replicates of the identical cell
returned byte-identical endpoints, `capture` agreeing to sixteen digits. So the
free run reports a between-replicate sd of exactly zero, and zero is the honest
answer to the question it asks — *how much does the harness move when nothing
varies?* Not at all.

> **Half of that is wrong too, and it is the half that says zero.** *Kept
> visible for the same reason the sentence above it is: this paragraph has now
> been corrected twice, and both corrections came from running the thing rather
> than from thinking about it again.*
>
> The policies are deterministic. The **island is a wall clock**, and how many
> moves land inside an episode is not. At **four** seats, replicates of one
> identical cell differ — including at `--workers 1`, the serial path run 001
> itself measured: `capture` −0.2796 against −0.2836 on one seed, 12 settled
> moves against 10. Run 001 measured **two** seats and stands for two seats.
>
> So the free rung does produce a number, and that is better than the zero this
> paragraph promised: a floor of zero cannot be exceeded by anything and tells
> a later reader nothing. What has not changed is the sentence below — it is a
> **harness** number, agent sampling is not in it, and H0b still has to be
> bought. See [`DEVIATIONS.md`](DEVIATIONS.md) A3.

That is a genuinely useful floor, and it is **not** the number a threshold is
written against. The 0.229 and 1.03 this lab measured before are **agent**
variance — model sampling — and no NPC run contains any. So:

| what moves | measured by | costs |
|---|---|---|
| the harness, clock and economy | NPC replicates, identical seeds | nothing |
| the NPC policy draw | NPC replicates, `--vary-npc-seed` | nothing |
| **the agents** | **model replicates of one cell** | **money** |

The third is the one rung 1's threshold needs, and it has to be bought. What
the free rungs buy is the guarantee that the harness is not adding to it.

## Corrections to the Tier 3 design

**This section was headed "Three corrections" and there are five.** C1–C3 were
written before any run, per CLAUDE.md's process rule. C4 and C5 came out of
running the two free rungs (run 002) and are kept in the same list rather than
in an errata section, because a reader deciding what to run needs all five and
does not care which were foreseen. Which were foreseen is said in each.

### C1 — The endpoint is a count. Efficiency carries no signal about δ.

The Tier 3 design defines δ\* as an efficiency comparison. **Its own
calibration then showed efficiency is exactly where the signal is not**: across
the entire sweep — every delta, both directions, 121 surviving islands —
survivor efficiency has median 0.972 and range 0.741–1.000. It is 0.978 at
δ = 0 and 0.998 at δ = 0.3 sharpen. Written as an efficiency comparison, δ\*
would be estimated from a line that does not move.

So `outcome(·)` in the δ\* definition is **the zero-episode share**, and the
primary endpoint of this experiment is a count. `capture` is reported beside
it, never as it.

### C2 — The published calibration curve is a *stock* curve and does not transfer.

This is the correction most likely to be skipped, because the curve exists and
looks usable. It was measured on 002's accumulating island, at 12 agents and
24–48 islands. **This experiment runs on the flow island at 2–4 traders.** A
model tier compared against a curve from a different accumulation rule and a
different table shape is compared against nothing.

Recalibration at the game island's table shape is free, scripted, and gates
everything below it.

### C3 — Noise is measured before any threshold is named.

The lab's most expensive lesson, and it is not re-learned here. Every threshold
pre-registered in the three previous experiments was 0.10–0.15, against an
instrument whose own between-run movement was later measured at 0.229 on the
ratio and **1.03 per round** on captured gain. Rows 10–16 of the hypothesis
ledger are the wreckage.

So the replicated NPC control runs **first**, and the numbers it produces are
what this experiment is allowed to pre-register. A threshold chosen without
that arithmetic is a threshold chosen to be met.

### C4 — The table shape decides whether the endpoint can read at all.

*Not foreseen. Measured in run 002, rung 0b.*

C2 says recalibrate at this island's table shape. What recalibration found is
that "this island's table shape" is not one shape and the choice is not free:
of the **12 cells the game allows** (2–4 traders × 2–5 goods), only **6 can
read the primary at all**, and the six that cannot are exactly the six where
**goods outnumber traders**.

The reason is structural rather than statistical. Arm C's rule is full
specialisation — a price-taker with linear technology and one unit of labour
puts all of it into the good with the highest `price × capacity` — so at most
`traders` distinct goods are ever produced, and Cobb-Douglas with a positive
exponent on a good nobody made is zero for **every** agent in **every** period,
whatever the announced vector said. The zero-period share is 1.000 at every δ
including δ = 0.

**Do not read that as "nothing happens there".** The silent anchor in the same
cells is **0.000**: with no convention at all, nobody is ruined. So more goods
than traders is where the convention is most violent and least informative —
a maximal convention effect and no content-error effect in one row.

| shape | silent | flatten span | sharpen span |
|---|---|---|---|
| 4 × 3 | 0.000 | 0.493 | **0.678** |
| 3 × 3 | 0.000 | 0.340 | 0.484 |
| 3 × 2 | 0.000 | 0.332 | 0.486 |
| 4 × 2 | 0.000 | 0.303 | 0.456 |
| 2 × 2 | 0.000 | 0.344 | 0.448 |
| 4 × 4 | 0.000 | 0.217 | 0.259 |
| any with goods > traders | 0.000 | **0.000** | **0.000** |

**So rung 1 runs at 4 traders and 3 goods**, not at the game's default of 5
goods. That is inside the allowed range and needs no change to the island.

Two things this does **not** say. It is a property of the *scripted* trader,
which fully specialises; the NPC seats on the real island do not, and at 4
traders and 5 goods they return a zero-episode share of 0.5 rather than 1.0
(run 002, rung 0a). And it explains, rather than excuses, why the published
curve reads at all: 12 agents and 5 goods is a cell where 12 > 5.

## The ladder

From [`do-they-take-a-handed-over-answer`](../do-they-take-a-handed-over-answer/):
start at the most informative rung and dismantle it, so a dead arm is found on
the first rung rather than the fifth. **A rung is run only on evidence that the
rung above it moved.**

| rung | cell | cost | what it kills | state |
|---|---|---|---|---|
| **0a** | NPC replication, nothing varied | free | nothing — it bounds the harness | **run** (002) |
| **0b** | scripted δ sweep, table shape swept | free | the tier, if the curve is flat here | **run, passed** (002) |
| **0b′** | H0b: model replication of one cell | **money** | nothing — it sets every threshold below | not authorised |
| **1** | CS at δ = 0 vs `silent`, 4 traders × 3 goods | ~25 paired games | the tier, if a correct shared convention does not beat nothing | blocked on 0b′ |
| **2** | CS vs CP at δ = 0, plus WP | ~75 games | the claim: CS ≈ CP means sharedness is decoration | blocked on 1 |
| **3** | δ sweep, common arms only → δ\* | the expensive one | — | blocked on 2 |

Rung 2 is where the paper is. Rung 3 is where the number is.

**Rung 1's cell is now specific**, which it was not when this table was
written: **4 traders, 3 goods**, and the δ ladder for rung 3 runs on
`flatten`. Both come from rung 0b — see C4 for the shape, and for the
direction: `sharpen` moves 0.227 → 0.525 between δ = 0 and δ = 0.05, at a
realised error of 0.021, and then crawls. It is a cliff detector and a terrible
ladder; `flatten` spreads 0.227 → 0.720 across the whole range. That asymmetry
is H3's prediction arriving early and in the scripted tier, where it costs
nothing and claims nothing about agents.

## Metrics

Read from settled state. Self-reports are not data.

**Primary (outcome).** Zero-episode share per trader, paired by island.
Bounded, decomposable, defined on every trader in every episode.

**Secondary (outcome).** `capture`; share of traders above their own autarky;
`eff_round`. Reported with their own between-run movement beside them, never
instead of the primary.

**Mechanism — adoption, from settled state.** Two kinds, which degrade
independently:

- **protocol adoption** — a transcript verifier: quotes denominated in the
  numeraire, conformant to the board's format, referencing the announced
  vector. Typed and countable per message. Checkable *without* the answer key.
- **strategy adoption** — the distance between the recorded `PRODUCE` split and
  the split the announced vector implies for that trader's capacities, straight
  out of `walras()`. One number per trader per episode. Needs the answer key.

**Disposition.** Adoption as a function of δ, restricted to traders whose own
capacities *contradict* the announced vector. A trader that follows a
convention its private information disputes is deferring to the group. The
defection-rate-versus-δ curve is disposition measured rather than requested.

**Every arm lands in this table, and the two ledgers are never added:**

|  | outcome moved | outcome didn't |
|---|---|---|
| **adopted** | the convention did the work | **dead convention** — worked as designed, moved nothing |
| **not adopted** | confound: something else moved it | null, correctly |

No arm of any previous experiment here can be placed in that table. That is the
sharpest statement of what has been missing.

## Confounders

- **Detection.** A trader may notice the vector is wrong because its own
  capacities contradict it. That is the disposition measurement, not a bug —
  but δ must be perturbed in partially detectable directions, and
  detectability recorded per trader as a flag. A model that detects nothing
  flattens the disposition curve into pure obedience; **that is a
  model-capability result and must be reported as one**, not as a disposition
  finding.
- **Common knowledge by assertion.** "Every trader received this" is a claim
  the trader must trust. The harness is trusted infrastructure, so this is
  acceptable — but it means CS measures *believed* common knowledge. If
  CS ≈ CP, read the transcripts for whether agents acted on the sharedness at
  all before concluding sharedness is worthless.
- **Obedience versus convention.** WP is the main control, but
  instruction-following is a specific pressure on model agents. Vary the
  framing at fixed δ — "we suggest" against "the island uses" — to size it.
- **Table size.** A public table seats 2–4. Common knowledge among two is a
  thin version of the thing being measured; the experiment runs at 4.
- **δ is not a welfare distance.** It is a distance in price space. What a
  given δ costs is what rung 0b measures rather than assumes.

## What this does not do

It does not test **enforcement**. The manager is held fixed as substrate: an
arm that varies enforcement varies the thing everything else is measured
against. Auctions and clearing rules are deliberately out.

It does not introduce a second surface. The announcement is a **frozen stimulus
block in each seat's private brief**, alongside the tastes and capacities that
already arrive there. No manager change, no new primitive, no tool.

## Why this is publishable whichever way it comes out

Every null this lab has produced so far was *unresolvable* — the noise swamped
it, and "we did not find it" is all that could be said. This design is the
first where a null is a result:

- the manipulation check is a **count**, and counts survive this instrument;
- the noise floor is measured **before** the threshold is named;
- the two arms differ in **one sentence of byte-identical content**.

So: **CS > CP** gives an exchange rate for sharedness on LLM agents, against an
answer key nobody else has. **CS ≈ CP** kills the claim that opened this line of
work, at a stated resolution. "It is not there, to within this bound" is a
different object from "we did not find it", and the noise measurement is what
converts one into the other.

## Where the material lives

- The design this inherits:
  [`../which-part-of-a-convention-works/tier3-design.md`](../which-part-of-a-convention-works/tier3-design.md)
- The manufactured convention: `which-part-of-a-convention-works/experiment/barter/calibrate.py`
- The economy and closed forms: `which-part-of-a-convention-works/experiment/barter/economy.py`
- The flow result: [`../is-ruin-the-convention-or-the-commitment/README.md`](../is-ruin-the-convention-or-the-commitment/README.md)
- The instrument, the manager, the scorer: `does-a-content-free-protocol-help/island/`, `does-a-content-free-protocol-help/viewer/scores.py`
- The island as a played game: `games/island.md`, `games/island/`
- What the noise is: `../do-they-take-a-handed-over-answer/runs/003-how-much-does-the-instrument-move.md`
- What is assumed rather than re-tested: [`reports/2026-08-24-hypothesis-ledger.md`](../../reports/2026-08-24-hypothesis-ledger.md)
