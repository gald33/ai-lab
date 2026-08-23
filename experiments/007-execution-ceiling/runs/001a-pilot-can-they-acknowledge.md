# Run 001a — Pilot: does a 30-second window survive?

**Opened:** 2026-08-23 · **Status:** running

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

- **Records:**
- **Ran:**
- **Numbers:**
- **Deviations:**
