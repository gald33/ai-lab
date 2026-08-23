# Run 002a — Probe: does disclosure actually happen?

**Opened:** 2026-08-23 · **Status:** reported

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

- **Records:** `results/002a-probe/v3.json`, six rounds, run stamp `0823T0515`.
  Boards under `results/002a-probe/boards/`, the keyed store under
  `results/002a-probe/keys/`, roster captures under `.../roster/` for all three
  cells from the first minute.

- **Ran:** all six rounds, 5 episodes each, 4/4 traders acknowledged in every
  round, no rescues, no failed rounds, `drain_errors` 0.

- **Numbers — the manipulation check.** Denominator 4 traders × 2 rounds = 8
  trader-rounds per cell.

  | cell | cost keys written | cost-key revisions | worth-key revisions (per trader, over 5 episodes) |
  |---|---|---|---|
  | `r-bare` | **0 / 8** | — | — |
  | `r-ratios` | **0 / 8** | — | — |
  | `r-ratios-board` | **8 / 8** | **all exactly 1** | seed 1: 2, 2, 3, 5 · seed 2: 5, 6, 2, 6 |

  Against the pre-registered threshold — 3 of 4 traders in at least 4 of 5
  rounds, worth-key median ≥ 5 revisions over 10 episodes — the cost half is
  met at 4 of 4 in 2 of 2, and the worth half comes in at a median of **4
  revisions over 5 episodes**. The threshold was written for ten-episode
  rounds and this run had five; the record said in advance that a shorter round
  is a weaker test of the second half.

  Key contents are economic, in the traders' own units: *"Cost ratios (bread
  numeraire): cloth 5.99, iron 2.72, salt 3.56"*; *"bread:1.33_iron
  cloth:0.46_iron salt:8.33_iron (iron as reference)"*; *"Episode 2: holding
  salt=1.23, bread=0.20. Desperate for iron and cloth"*.

- **Numbers — not evidence, printed because the scorer produces them.** Two
  seeds, five episodes. Exchange: `r-bare` 0.93, `r-ratios` 0.60,
  `r-ratios-board` 0.86. Presence 1.00 in all six rounds — no trader-episode
  passed without production, which is the five-episode round and not a
  treatment effect. Above own autarky: 15/40, 11/40, 16/40.

  **Two rounds exceeded 1.0 on exchange** — `r-bare` seed 2 at 1.11 and
  `r-ratios-board` seed 2 at 1.05. These are the first cells in this lab to
  land above the point where trading beats staying home. At n=2 this is a thing
  to check at full size, not a finding.

- **Assumptions that did not hold:** none.

  **A2 held, and informatively.** All three cells held `board_set`,
  `board_get` and `board_list`. The two untreated cells wrote **zero** keys.
  The grant alone changes nothing; the instruction is the treatment.

  **A5 held** — keys persisted and were readable after the run, with revision
  counters intact.

  **A3 held by construction** — nothing on a key was settled or scored; the
  manager read the channel only.

- **Deviations:** none. Nothing departed from the record during the run.

## What this changed

**The decision this probe was written to make: run 002 goes ahead as written.**
The record named three outcomes in advance. This is the first — disclosure
happens — with the caveat the third anticipated: the "once" half is followed
exactly and the "every episode" half is partial, so it is reported as the weak
half from the start rather than discovered later.

**What run 001 could not distinguish, this separates.** Run 001's treated cell
produced 7 free-text messages in five rounds and its exchange number was about
traders who did not disclose. Here the same content, given a key and a moment,
is disclosed by every trader in every round. Whether disclosure *helps* is
still open and is what run 002 is for.

**The strongest single result is A2.** Three cells, identical tool grants, and
only the instructed cell wrote anything. An agent handed a shared keyed store
and no reason to use it does not discover a use for it — which is worth
remembering the next time a capability is added in the hope that agents will
find it.
