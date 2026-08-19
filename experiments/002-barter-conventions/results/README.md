# Run log

Every record in this directory, what shape produced it, and what it showed. An
island costs money and cannot be re-run cheaply, so the raw records are kept
whole and this says what each one is — a directory of undated JSON is not a
result, it is an archive nobody can read.

Records are listed **oldest first**, which is also the order in which the
harness was wrong in different ways. Several of these measure the harness rather
than the arms; where that is true it is said here rather than left for a reader
to infer.

All Tier 2 runs use `claude-haiku-4-5-20251001`. Costs are the SDK's own token
valuation, quoted as a measure of effort.

---

## Tier 1 — scripted, free, replicated

| file | shape | what it holds |
|---|---|---|
| `tier1.json` | 12 agents, 5 goods, 12 islands, 4 arms | The main ladder. Per-island efficiency, ruin, gain ratios, trade counts. |
| `tier1_rounds.json` | same, swept over round budgets | How each arm's result moves with more trading rounds — whether an arm is slow or simply worse. |
| `tier1_labour.json` | same, swept over instalments | One-shot labour against the same total spread across rounds. The scissors: rolling labour drives ruin to zero and halves efficiency. |

Medians across 12 islands: autarky floor 0.405, exchange ceiling 0.493.

| arm | median efficiency | islands with someone ruined |
|---|---|---|
| A `silent` | 0.476 | 0/12 |
| B `disclose` | 0.457 | 0/12 |
| C `price` | 0.997 | 6/12 |
| D `money` | 0.872 | 10/12 |

---

## Tier 2 — models, paid, n=1 per arm

### The first ladder — `tier2_seed1_*.json`

Six arms on one island (seed 1, floor 0.374, ceiling 0.413), under the original
six-stage turn-taking flow. **Superseded**: the flow these ran under no longer
exists, and no arm cleared its own autarky floor.

| arm | efficiency | settled | cost |
|---|---|---|---|
| `free` | 0.386 | 5/30 | $1.93 |
| `built` | 0.368 | 3/16 | $2.16 |
| `told` | 0.316 | 2/25 | $1.94 |
| `spend` | 0.272 | 9/30 | $4.63 |
| `bound` | ruined 1 | 1/21 | $2.79 |
| `paid` | ruined 2 | 0/26 | $4.50 |

### `tier2_seed41_bound.json`

The first Tier 2 island to finish **above its exchange ceiling**: 0.578 against
a ceiling of 0.539 and a floor of 0.448. Kept because it is the only existing
evidence that models changed what got *made* rather than only who held it.

### `tier2_windows.json` — the seven-arm sweep

The first sweep under the wall-clock flow. 4 agents, 3 rounds of three 60s
windows, seed 41, floor 0.448, ceiling 0.539. $19.07 for seven islands.

| arm | efficiency | below autarky | settled | cost |
|---|---|---|---|---|
| `bound` | **0.507** | 1/4 | 6/26 | $3.04 |
| `free` | **0.457** | 2/4 | 7/27 | $2.87 |
| `built` | 0.397 | 2/4 | 6/25 | $2.59 |
| `told` | 0.392 | 3/4 | 3/20 | $2.93 |
| `silent` | 0.374 | 4/4 | 0/18 | $2.21 |
| `paid` | 0.372 | 3/4 | 1/23 | $2.85 |
| `spend` | 0.371 | 3/4 | 4/20 | $2.60 |

Only `bound` and `free` clear the floor. The ladder is not monotone: `bound`
beats both rungs above it.

**Read with care.** 60–85% of every island's turns landed in the first window,
where the only manager action available can be taken once. `silent` spent 84%
of its turns there and settled nothing — that is the window shape, not a finding
about silence.

### `tier2_oneround.json` — three agents, one round

The same seven arms at minimum size: 3 agents, 1 round, three 60s windows.
$4.48. Floor 0.626, ceiling 0.713 — **every arm finished below the floor.**

Its value is diagnostic rather than comparative. It made the settle-window
starvation countable:

| arm | settle turns | agents who got one | settled |
|---|---|---|---|
| `paid` | 1 | 1/3 | 0/6 |
| `built` | 1 | 1/3 | 0/8 |
| `bound` | 2 | 2/3 | 0/5 |
| `free` | 2 | 2/3 | 2/8 |
| `told` | 3 | 3/3 | 2/4 |
| `spend` | 4 | 2/3 | 2/7 |
| `silent` | 5 | 3/3 | 2/11 |

Both islands where all three agents reached the settle window settled trades;
two of the three where only one did settled nothing.

### The `paid` probes

Three single-arm islands, each isolating one harness change. Same island
throughout (seed 41, 3 agents, 1 round, floor 0.626, ceiling 0.713), so they are
directly comparable to each other.

| file | change under test | eff | settled | missed | cut | held | cost |
|---|---|---|---|---|---|---|---|
| `tier2_paid_muster.json` | schedule published in absolute times, all traders must acknowledge before anything opens | 0.540 | 1/7 | 2 | — | — | $0.74 |
| `tier2_paid_batched.json` | list-taking tools (one call, many deals), 60/150/150 windows, hard round deadline | 0.546 | 0/7 | 1 | 0 | 3 | $0.80 |
| `tier2_paid_unstaged.json` | everything open for one 300s window | ruined 1 | **2/17** | 0 | 0 | 3 | $0.63 |

What they establish, in order:

1. **The muster worked and changed nothing.** One schedule, all three acked,
   nobody absent — and the settlement rate did not move. It was built to stop
   agents missing windows they had never been told about; the per-turn
   timestamps it added then showed that was not why they were missing them.
2. **The timestamps found the real cause.** A production turn runs 18–33
   seconds; a trading turn runs 68–169. Every offer turn outlived its
   sixty-second window. One agent began a turn at t=60.8 and was still inside it
   at t=229.8 — through the offer window, the settle window, and past the end of
   the round.
3. **Batching and the hard deadline fixed the mechanics.** Nothing cut, every
   turn inside the round, one window unreached instead of two. Settlement went
   to *zero*, because the level ladder refused an approve decided at t=150 for a
   window that opened at t=210 — and that agent announced on the floor that it
   had approved.
4. **Unstaging fixed that and exposed the economics.** Volume up 2.4×, first
   settlements, no missed windows. Then all three traders announced grain, all
   three produced grain, and one finished holding zero of three goods. One had
   asked *"What are you producing?"* in the same turn it committed its whole
   unit of labour.

---

## What a Tier 2 record contains

Beyond the headline numbers: the resolved switch vector (all seventeen), both
efficiency brackets, both benchmarks, per-agent gain ratios, the manager's
summary and its rejection log, every floor message, the final quote board, the
per-round trajectory, the harness counters, and the full transcript with each
turn's start time and duration.

Older records lack fields added later — `tier2_seed1_*` predates `flow`,
`below_autarky` and the harness counters. Absent is absent, not zero.
