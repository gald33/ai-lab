# Run 002a — Probe: does disclosure actually happen?

**Opened:** 2026-08-23 · **Status:** running

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run, and why it is a probe

Run 002 as specified is 15 rounds and 60 sessions. Its whole premise is that
naming a key and a moment turns disclosure from a disposition into an act — and
if that premise is false, the 60 sessions buy nothing that run 001's 7 free-text
messages did not already buy.

So this probe asks **only the manipulation question**, at 40% of the size.
It does not test the primary and no efficiency claim may be drawn from it.

## Specification

| | |
|---|---|
| entry point | `run.py` at `5fc17c2`, the commit run 002's gates were recorded against |
| conditions | `r-bare`, `r-ratios`, `r-ratios-board` — as run 002, unchanged |
| units / counts | 2 seeds × 3 cells = **6 rounds**, 5 episodes × 180s, 4 traders |
| seeds | 1–2 |
| command | `python run.py --arms r-bare r-ratios r-ratios-board --rounds 2 --episodes 5 --episode-seconds 180 --agents 4 --out results/002a-probe` |
| cost | **24 agent sessions**, one wave, **~17 min** |
| go | Given by the owner on 2026-08-23 ("around just the probe test, don't run the full test"), before launch. |

**Five episodes, not ten**, because the "written once" half of the instruction
shows up in episode 1 and the "every episode" half shows up in the revision
count either way. A shorter round is a weaker test of the second half and is
reported as such.

## What is measured

The manipulation check from `PREREGISTRATION-v2.md`, read by
`tools/board_dump.py` — cost keys written, their revision counts, worth-key
revisions against 5 episodes — plus, for A2, whether `r-bare` or `r-ratios`
touch the keyed store at all when nothing tells them to.

**Not measured here:** the primary. Exchange and presence are computed and
printed because the scorer produces them, and they are **not** to be read as
evidence at 2 seeds and half the episodes.

## The decision this probe makes

- **Disclosure happens** — most traders in `r-ratios-board` write a cost key,
  and worth keys carry repeated revisions. → Run 002 goes ahead as written.
- **Disclosure does not happen** — the protocol is named, addressable, granted,
  and still not enacted. → Run 002 does **not** run as written. The finding is
  that these agents do not disclose even when told exactly where and when, and
  the next question is why, not whether it helps.
- **Partial** — cost keys written, worth keys not revised. → Run 002 goes ahead,
  and the "every episode" half is reported as the weak half from the start.

## Assumptions

Carried unchanged from run 002's record: A1–A5. A5 (board writes persist and
are readable at the end) is the one this probe checks first, since the whole
measurement depends on it.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
