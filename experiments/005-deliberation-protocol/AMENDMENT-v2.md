# 005 v2 — amendment 1: the primary metric is near-binary

**Written after the pilot, before any treatment cell has been run.** No cell
other than `bare` has been executed at the time of writing, so nothing here is
chosen with knowledge of a treatment effect. `PREREGISTRATION-v2.md` is not
edited; this document sits beside it.

## What the pilot showed

Six unguided worlds, and every one scored **below the autarky floor**:

| seed | W | autarky floor | zero agent-periods |
|---|---|---|---|
| 1 | 0.194 | 0.459 | 4/24 |
| 2 | 0.387 | 0.503 | 3/24 |
| 3 | 0.167 | 0.459 | 3/24 |
| 4 | 0.395 | 0.508 | 1/24 |
| 5 | **0.000** | 0.453 | 3/24 |

Seed 5 is the tell. `W = 0.000` with only 3 of 24 agent-periods at zero is not
a possible reading for a welfare measure. Tested directly, on seed 5's island:

```
autarky                      lower 0.4530  upper 0.4532
autarky, 1 agent at zero     lower 0.0000  upper 0.0000
1.5x autarky, one at zero    lower 0.0000  upper 0.0000
```

**One agent at zero utility zeroes the whole world's efficiency**, even when
every other agent is half again better off than it would have been alone.

That is not a bug in `economy.efficiency`. It is correct: with Cobb-Douglas
preferences a ruined agent's utility really is zero, and no set of welfare
weights puts a zero on the frontier, so the distance to the frontier really is
maximal. The mistake is mine, in choosing it as the primary metric for a world
where partial ruin is common.

## What that means for the pre-registration

`W` is **not** the continuous welfare measure `DESIGN-v2.md` claims. It is a
coverage indicator: near-binary in whether anybody was ruined, and almost
insensitive to how well everyone else did. The design's argument that "the
metric is continuous, so there is no threshold to tune and no cut point to
accuse" is false, and the pilot's below-floor results are mostly this artefact
rather than a fact about the task.

This is [002 Tier 3](../../reports/2026-08-20-002-tier3-calibration.md)'s claim 1
recurring — *"efficiency carries no signal; the entire effect is on whether an
island survives, and it is binary"* — from the other direction. That report is
in this repository, written by the same author, and the design walked into the
same wall anyway.

## The amendment

`W` **stays the pre-registered primary and will be reported first, always.**
Swapping a frozen metric because it gave an inconvenient answer is the move
this repository's whole apparatus exists to prevent.

Added beside it, pre-specified here before any treatment runs:

**Companion primary — `G`, median gains over autarky.** Using
`economy.gains`, each agent's period utility as a multiple of what it would
have had alone; the **median across agents**, then the **mean across periods**.
A single ruined agent moves the median by one rank instead of destroying the
statistic. `G = 1.0` is "no better than not trading"; `G > 1` is a real gain.

Reported with it, and never folded into it:

- **`worst`** — the minimum gains ratio. Ruin is visible here, as a number
  about ruin, rather than smuggled into a welfare average.
- **`below`** — how many agents finished under their own autarky, per period.
- **zero rate** — unchanged, still the coverage metric it always was.

`G` is a median and therefore has its own failure mode: it says nothing about
the tails, which is exactly why `worst` and `below` are mandatory alongside it
rather than optional.

## Revised pilot gate

P1–P4 are evaluated on **both** metrics and both verdicts are reported. The
paid cells require the gate to pass on `G`; a pass on `W` alone would be a pass
on a metric now known to be near-binary.

| # | on `W` (as frozen) | on `G` |
|---|---|---|
| P1 not trivial | median `W` ≤ 0.85 | median `G` ≤ 0.85 × the `G` the Walrasian point achieves |
| P2 not hopeless | `W` ≥ 1.05 × floor in ≥ 40% of worlds | `G` ≥ 1.05 in ≥ 40% of worlds |
| P3 coordination bites | ≥ 15% of agent-periods at zero | unchanged — this criterion was always about coverage |
| P4 headroom | IQR(`W`) ≥ 0.10 over ≥ 12 worlds | IQR(`G`) ≥ 0.10 over ≥ 12 worlds |

Both are reported whatever they say.

## What this does not fix

The pilot ran **6 worlds, not the 12 P4 requires**, so P4 cannot pass on either
metric without more worlds. That was a sizing decision made before the metric
problem was known, and it is a second reason the paid cells are not authorised
yet.

---

# Amendment 2: rounds, episodes, and memory between them

**Written before any run under the new structure.** The pilot reported above
was run under the old one and is superseded as a baseline: three episodes with
no memory is not five episodes with memory, and the two are not comparable.

## The structure, corrected

| term | what resets at its boundary |
|---|---|
| **episode** | item stocks, labour, open offers, episode utility |
| **round** (one seed) | agent context and history, accumulated utility |

A round is **k = 5 episodes on one island**. Abilities, tastes, traders and the
island are identical across a round's episodes. What carries between them is
only what each agent has been told and has seen happen.

This inverts the vocabulary the earlier design used, where "period" meant
episode and "world" meant round.

## Two efficiencies, on two different objects

- **`eff_episode`** — the episode's utility vector against the one-episode
  frontier. A coverage measure: one agent at zero puts the vector maximally far
  from the frontier, so a single ruined trader zeroes the episode however well
  the other seven did.
- **`eff_round`** — the **accumulated** utility vector against the frontier of
  the total. **This is the primary.** An agent ruined in one episode and fed in
  four has positive accumulated utility, so the single-zero annihilation that
  made the old `W` near-binary cannot occur.

The frontier of the total is `k ×` the one-episode frontier, because Σα = 1
makes utility homogeneous of degree 1. `eff_round` is computed by dividing the
accumulated vector by `k` and scoring it against the one-episode frontier.
**That identity is 004's argument and its own review target #1**, so it is
gated: `k` identical episodes must score exactly what one episode scores, at
k = 2, 3, 5, 8.

`G` is demoted from companion primary to diagnostic. It was invented to survive
a metric problem that the round-level measure removes at the source.

## Memory is now implemented, and it is the point

Each agent carries a private record — what it did, what the world answered,
what it heard — appended every turn and handed back in the next prompt. It
resets at the round boundary and at no other time.

Without it a five-episode round is five unrelated one-episode rounds and there
is nothing for an agent to learn, which is the whole reason a round has more
than one episode. It is trimmed oldest-first past 14,000 characters, and the
trim is **announced in the prompt** rather than done silently: an agent that
has forgotten something should know that it has.

## What this costs

Prompts grow through a round, so the per-call price rises with episode number.
The record now stores the largest history any agent carried and whether anyone
was trimmed, so the cost is measured rather than assumed.

## Re-freeze

`base.md` changed — episode/round vocabulary, and a paragraph stating that
abilities and tastes are constant across a round and that only learning
carries. All five assembled cells are re-hashed in `PREREGISTRATION-v2.md`.
The protocol, placebo and hint blocks are **byte-identical** to before.
