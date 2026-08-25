# Run 001b — Re-pilot at 45/30

**Opened:** 2026-08-23 · **Status:** reported

**A note on form, first.** This run's specification was committed before it
launched — in [D2a](../DEVIATIONS.md), which named the timing, the size and the
purpose. What did not exist beforehand is *this file*. The grounding layer asks
for a record under `runs/` before the run, and that is a gap in form even
though the substance was fixed in advance and is unchanged below. Recorded here
rather than tidied away; the next pilot gets its own record before it launches.

---

## Specification, as fixed in D2a

| | |
|---|---|
| entry point | `run.py` at `c19386a` |
| conditions | `e-bare`, `e-plan`, unchanged |
| units | 2 seeds × 2 cells = 4 rounds, 3 episodes × 180s, 4 traders |
| timing | window **45s**, acknowledgement asked by **30s** |
| command | `python run.py --arms e-bare e-plan --rounds 2 --episodes 3 --episode-seconds 180 --ack-seconds 45 --ack-by-seconds 30 --agents 4 --out results/001b-pilot45` |
| cost | 16 agent sessions, ~11 min |
| go | The owner's instruction on 2026-08-23: *"if not, just extend it by a little and see if it works."* |

## Outcome

- **Records:** `results/001b-pilot45/v3.json`. All four rounds ran; none failed.

- **Numbers.** Denominators: 4 traders per round for acknowledgement, 12
  trader-episodes per round for production.

  | cell | seed | ack | produced | captured mean | captured median | eff_round | floor |
  |---|---|---|---|---|---|---|---|
  | `e-bare` | 1 | 4/4 | 12/12 | −0.94 | −0.44 | 0.000 | 0.642 |
  | `e-bare` | 2 | 4/4 | 12/12 | −2.68 | −0.81 | 0.000 | 0.674 |
  | `e-plan` | 1 | 0/4 | 12/12 | **+0.91** | **+0.91** | **0.978** | 0.642 |
  | `e-plan` | 2 | 2/4 | 12/12 | −1.45 | **+1.00** | **0.887** | 0.674 |

  `e-plan` seed 1 scored **0.98 per-episode efficiency in all three episodes**.
  Seed 2 scored 0.99, 0.00, 0.99 — one collapsed episode inside an otherwise
  near-frontier round, which is what drags its mean below its median.

- **The timing question is settled.** Production is **48/48 trader-episodes**.
  The window does not break participation, so run 001 uses 45/30.

- **The acknowledgement deficit is not timing.** At the same window `e-bare`
  acknowledged 4/4 in both rounds and `e-plan` managed 0/4 and 2/4. Whatever
  suppresses acknowledgement in the treated cell is the treatment, not the
  clock — plausibly a much longer prompt read before acting. And `e-plan` seed
  1 reached 0.978 **with zero acknowledgements**, so acknowledgement does not
  predict outcome. It is reported in run 001 and interpreted as nothing.

- **Deviations:** D1, D2, D2a. No new deviation; the form gap above is noted at
  the head of this record.

## What this changed

**The feasibility question has an answer: yes.** Handed the island's
equilibrium, agents reach 0.978 and 0.887 against floors of 0.642 and 0.674 —
the first cells in this lab to finish clearly above autarky, and close to the
frontier. Both `e-bare` rounds at the same timing finished at 0.000.

Four rounds and three episodes is not a result, and the pre-registered run
stands as written: **12 seeds, 10 episodes, thresholds fixed in advance.** What
the pilot licenses is spending on it.

It also makes the dismantling ladder in [`CLAUDE.md`](../CLAUDE.md) worth
walking. Rung 1 works; rungs 4 and 5 are measured and null. The finding is
where in between it breaks.
