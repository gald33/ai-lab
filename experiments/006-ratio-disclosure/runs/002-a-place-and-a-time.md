# Run 002 — Does giving disclosure a place and a time make it happen?

**Opened:** 2026-08-23 · **Status:** specified

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

---

## Why this run

Run 001 said what was worth disclosing and left where and when to the trader.
Almost nothing was disclosed: **7 free-text messages across five treated rounds
and 200 trader-episodes**, 3 of them carrying a ratio, and 0 of 373 roster task
strings. Exchange in that cell was 0.57 against `r-placebo`'s 0.79, but with a
manipulation that thin the number is about traders who did not disclose, not
about disclosure.

This run names a key and a moment: cost ratios once, worth ratios after every
production. Design frozen in [`PREREGISTRATION-v2.md`](../PREREGISTRATION-v2.md).

## Specification

| | |
|---|---|
| entry point | `run.py`, driving `005-deliberation-protocol/run_v3.py` (commit at the gates below) |
| conditions | `r-bare`, `r-ratios` (run 001's block, byte-identical), `r-ratios-board` |
| units / counts | 5 seeds × 3 cells = **15 rounds**, paired; 10 episodes × 180s; 4 traders |
| seeds | 1–5, as in run 001 |
| models | `claude-haiku-4-5-20251001` |
| instrument change | `board_set`, `board_get`, `board_list` granted **to every cell** — D2 |
| command | `python run.py --arms r-bare r-ratios r-ratios-board --rounds 5 --episodes 10 --episode-seconds 180 --agents 4 --out results/002-board` |
| cost | **60 agent sessions**, 15 rounds at 10 concurrent = 2 waves, **~64 min** |
| go | *(not yet given — nothing runs until it is, and it is recorded here)* |

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | The length gap between the treated blocks (240 against 426 words) does not drive the primary. Bounded by run 001's `r-placebo − r-bare` of −0.021. | `r-ratios-board` differs from `r-ratios` by roughly the placebo's cost and no more, in which case length is the parsimonious reading and is reported as such. |
| A2 | Granting the keyed store to all three cells leaves the untreated cells unchanged in practice — they will not spontaneously use it. | `r-bare` or `r-ratios` writes board keys. That is a finding, not a fault, and it makes the grant part of the treatment. |
| A3 | A board key is a place traders talk to each other, not a second settlement surface. The manager reads the channel only. | Any board key affects what settles. It cannot: the manager never reads them. |
| A4 | Presence and exchange can still be read apart. | Both move together in every seed — reported as confounded, per the pre-registration. |
| A5 | Board writes persist for the round and are readable when the run ends. Switchboard keys have no TTL unless one is set, and none is asked for. | `board_list` comes back short or empty at the end while the boards show writes happening. The dump then runs during the round instead. |

## Hypothesis

- **Expect:** disclosure happens — most traders write a cost key, worth keys
  get revised repeatedly — because the instruction is now a concrete act rather
  than a disposition. Whether exchange improves I genuinely do not know, and
  that is the point of separating the two.
- **Would surprise me:** disclosure happening and exchange still falling. That
  fires the stopping rule and moves the question to the exchange mechanism.
- **Would not surprise me:** the cost key written once by everyone and the
  worth key written once and then forgotten — the "every episode" half being
  the harder half, since it requires acting on what just settled.

## Metrics

Primary **exchange**, co-primary **presence**, both per the pre-registration.
The manipulation check is read from the keyed store by `tools/board_dump.py`:
cost keys written, their revision counts, worth-key revisions against 10
episodes, and whether board content is echoed in later proposals.

## Preflight

| gate | command | commit | result |
|---|---|---|---|
| smoke | `python tools/check_stimuli.py`; `python -m pytest tests -q` | | |
| assembly | `python tools/show_prompt.py r-ratios-board` | | |
| toolchain | `run_v3.preflight()` | | |
| board grant | a one-shot `claude -p` calling `board_set` under the run's own tool list | | |
| pilot | reused — run 001 of this experiment, and 005's runs 005–007 | reused | |

## Failure modes anticipated

- **The board grant not actually taking**, which would silently turn the
  treated cell into a cell told to use a tool it cannot reach. The board-grant
  gate exists for exactly this and is new.
- **Keys written but never read**, which the echo check is for.
- **A hub blip**, now retried on both a bad answer and a dropped connection,
  with a failed round reported as failed.
- **Boards and keys not saved** — both are pulled off the hub immediately after
  the run, before the TTL.
- **Roster coverage** — the poller runs from launch this time, so all three
  cells are covered from their first minute, unlike run 001 (D1).

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:**
- **Ran:**
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:**

## What this changed
