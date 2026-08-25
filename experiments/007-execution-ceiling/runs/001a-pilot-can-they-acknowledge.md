# Run 001a — Pilot: does a 30-second window survive?

**Opened:** 2026-08-23 · **Status:** reported

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards.

---

## Why this run

D2 drops the announcement window from 120s to 30s and asks for acknowledgement
by an absolute time 20s in. A session takes roughly twenty seconds to boot its
MCP server and make a first call, so the margin is thin and the risk is named
rather than discovered: acknowledgement counts fall, and D10's rescue has
almost no time to fire.

This pilot spends 16 sessions to find out before 96 are committed to it. It
does **not** test the treatment and no efficiency claim may be drawn from it.

## Specification

| | |
|---|---|
| entry point | `run.py` at `c19386a`, the commit the gates were recorded against |
| conditions | `e-bare`, `e-plan` — as run 001 will use, unchanged |
| units / counts | 2 seeds × 2 cells = **4 rounds**, **3 episodes** × 180s, 4 traders |
| timing | announcement window **30s**, acknowledgement asked by **20s** (D2) |
| command | `python run.py --arms e-bare e-plan --rounds 2 --episodes 3 --episode-seconds 180 --ack-seconds 30 --ack-by-seconds 20 --agents 4 --out results/001a-pilot` |
| cost | **16 agent sessions**, one wave, **~11 min** |
| go | Given by the owner on 2026-08-23 ("go ahead and try, with a small probe just to see that they can acknowledge on time"), before launch. |

## What is measured

1. **Acknowledged count** per round, against 4.
2. **Production count** — did traders produce in every episode regardless of
   whether they acknowledged. This is the one that matters: participation is
   measured by production, not by acknowledgement.
3. Whether the plan reached the treated cell's prompts at all — one settled
   production in `e-plan` matching its planned shares is enough to show it did.

## The decision this pilot makes

- **Acknowledgement holds and traders produce** → run 001 proceeds at 30/20.
- **Acknowledgement fails but traders produce** → the window is survivable and
  the ack count is a known artefact; the owner's instruction was to extend it
  a little if needed, so run 001 proceeds at **45/30** and D2 is amended
  before it, not after.
- **Traders do not produce** → the window is breaking participation. Back to
  120s, and the timing change is abandoned rather than nursed.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `results/001a-pilot/v3.json`, four rounds, 3 episodes each.
- **Ran:** all four rounds, no failed rounds, no rescues.

- **Numbers — the question this pilot asked.** Denominator 4 traders per round
  for acknowledgement, 12 trader-episodes per round for production.

  | cell | seed | acknowledged | produced |
  |---|---|---|---|
  | `e-bare` | 1 | 2/4 | **12/12** |
  | `e-bare` | 2 | 3/4 | **11/12** |
  | `e-plan` | 1 | 1/4 | **12/12** |
  | `e-plan` | 2 | 1/4 | **9/12** |

  Acknowledgement degraded as D2 said it would: 7 of 16 traders acknowledged
  inside 20s. **Production did not**: 44 of 48 trader-episodes carried a
  settled production, and every round had traders acting from episode 1.

- **Numbers — not what this pilot was for, printed because they are stark.**
  Captured gain, mean over acting trader-episodes: `e-bare` −0.36 and −0.29;
  `e-plan` **+0.73** and −8.60. `e-plan` seed 1 scored **eff_round 0.914
  against a floor of 0.642**, with per-episode efficiency **0.98** in episodes
  2 and 3 — the first cell in this lab to finish above autarky. Two seeds, three
  episodes: this is a pilot and none of it is a result.

- **A measurement note for run 001.** Seed 2's −8.60 is one trader ending near
  zero utility, which the ratio turns into a large negative. The measure is
  correct but heavy-tailed, so run 001 reports **median alongside mean** and
  states both. Written here rather than discovered later.

- **Deviations:** D1 and D2 as written. D2 is **amended below**, before the run
  it affects.
