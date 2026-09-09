# Run 002 — Does giving disclosure a place and a time make it happen?

**Opened:** 2026-08-23 · **Status:** reported

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
| go | Given by the owner on 2026-08-23 ("Go"), after run 002a cleared the manipulation gate. Expected spend: 60 agent sessions, ~64 min. |

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
| smoke | `python tools/check_stimuli.py`; `python -m pytest tests -q` | `5fc17c2` | **pass** — `OK`, `11 passed` |
| assembly | `python tools/show_prompt.py r-ratios-board` | `5fc17c2` | **pass** — base headings in order, then `## Two ratios, and where they go` naming `cost/<your name>` and `worth/<your name>`, then the private block |
| toolchain | `run_v3.preflight()` | `5fc17c2` | **pass** — an agent's `switchboard-mcp` reached the hub |
| board grant | a one-shot `claude -p` calling `board_set` under the run's own tool list | `5fc17c2` | **pass** — wrote `cost/T1`, read it back at `revision: 1`; `tools/board_dump.py` then read the same key. The revision counter the "written once" check depends on is live. |
| pilot | reused — run 001 of this experiment, and 005's runs 005–007 | reused | **plus run 002a**, this run's own probe: 8/8 cost keys written at revision 1, worth keys revised 2–6 times, and zero keys in either untreated cell |

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

- **Records:** `results/002-board/v3.json`, fifteen rounds, run stamp
  `0823T0543`. Boards under `boards/`, the keyed store under `keys/`, roster
  captures under `roster/` (10 of 15 workspaces produced any task string).

- **Ran:** all fifteen rounds, 10 episodes each, 4/4 acknowledged everywhere,
  no failed rounds. **One rescue** (D10 of the instrument): `r-ratios` seed 5
  T4 did not join and was relaunched once, its first log kept as
  `session-abandoned.log`.

- **Numbers — the manipulation check.** Denominator 4 traders × 5 rounds = 20
  trader-rounds per cell.

  | cell | cost keys | cost revisions | worth keys | worth revisions over 10 episodes |
  |---|---|---|---|---|
  | `r-bare` | **0 / 20** | — | 0 / 20 | — |
  | `r-ratios` | **0 / 20** | — | 0 / 20 | — |
  | `r-ratios-board` | **20 / 20** | **all exactly 1** | **18 / 20** | median **3** |

  Against the pre-registered thresholds: the cost half is met outright — 4 of 4
  traders in 5 of 5 rounds, every key at revision 1. The worth half is **not**:
  the threshold was a median of ≥ 5 revisions over 10 episodes and the median
  is 3. The comparative test the pre-registration made the manipulation
  contingent on — `r-ratios-board` exceeding `r-ratios` on keys written — is
  met absolutely, 20 against 0.

- **Numbers — primary (exchange, paired `r-ratios-board − r-ratios`).**

  | seed | `r-bare` | `r-ratios` | `r-ratios-board` | board − ratios |
  |---|---|---|---|---|
  | 1 | 0.63 | 0.78 | 0.56 | −0.22 |
  | 2 | 0.61 | 0.78 | 0.96 | +0.18 |
  | 3 | 0.35 | 0.73 | 0.79 | +0.06 |
  | 4 | 0.84 | 0.96 | 0.89 | −0.07 |
  | 5 | 0.38 | 0.93 | 0.61 | −0.32 |

  **Mean −0.074, median −0.075, 2 of 5 seeds favouring the protocol.**
  Denominator 5 seeds per cell; no round dropped. Against the pre-registered
  thresholds (≥ +0.10 on 4 of 5 to work, ≤ −0.10 on 4 of 5 to harm) this is a
  **null**.

  `r-ratios-board − r-bare`: mean **+0.197**, median +0.228, 4 of 5 favouring.
  Not the primary and not a pre-registered contrast.

- **Numbers — co-primary (presence).** `r-bare` **0.805**, `r-ratios` **0.750**,
  `r-ratios-board` **0.770**. Board minus ratios is **+0.02**, so the primary
  is **not** confounded by attrition — the first run in this sequence where
  that is true.

- **Numbers — the absolute test.** No cell reached exchange above 1.0. Best
  round: `r-ratios-board` seed 2 and `r-ratios` seed 4, both 0.96. Trader-
  episodes above their own autarky optimum: `r-bare` 15/161, `r-ratios`
  31/150, `r-ratios-board` 35/154.

- **A result this run did not predict and cannot explain.** `r-ratios` against
  `r-bare` was **−0.25** in run 001 (0.57 against 0.82) and is **+0.28** here
  (0.84 against 0.56). Same block, same seeds, same instrument except D2's tool
  grant. **The sign reversed.** Either the between-seed noise at n=5 is larger
  than any effect measured so far, or the grant changed the untreated cells
  despite their writing no keys. This is recorded here as an open problem, not
  resolved.

- **Assumptions that did not hold:** **A4 held** for once — presence moved by
  0.02 between the compared cells. **A2 held** — 0 keys in both untreated
  cells, so the grant alone does nothing *within* this run; the cross-run
  reversal above is a separate worry that A2 does not cover. **A1, A3, A5**
  held.

- **Deviations:** D2, as written before the run. No new deviation.

## What this changed

**The stopping rule fires, and it should be applied carefully.** The
pre-registration said: *if disclosure happens and exchange does not improve,
this experiment stops proposing content for agents to disclose.* Disclosure
happened — 20 of 20 cost keys, each written exactly once, in traders' own
units, where run 001 produced seven free-text messages in five rounds. Exchange
did not improve: −0.074, 2 of 5 seeds. So the rule fires.

**What makes this the cleanest negative in the sequence.** Every earlier
negative was confounded by attrition (005's A3, 006 run 001's A4). This one is
not: presence differs by 0.02 between the compared cells. The traders stated
their cost ratios, once, correctly, on a shared board any of them could read,
and updated their worth as they traded — and exchanged no better for it.

**What stops it being conclusive.** `r-ratios` moved from −0.25 against bare in
run 001 to +0.28 here. A block whose effect reverses sign between two runs on
the same five seeds is not a block whose effect has been measured. Either five
seeds cannot resolve differences of this size — which would mean **none** of
this experiment's numbers, including its null, are resolved — or the tool grant
in D2 changed the untreated cells in some way invisible to a key count.
Distinguishing those is the first thing worth doing, and it is cheap: re-run
run 001's exact three cells under the current grant.

**The one thing that did move, and is not the primary.** Trader-episodes
finishing above their own autarky optimum: 15/161 untreated, 31/150 with the
ratios block, 35/154 with the board protocol. Both treated cells roughly double
the untreated rate on a measure that needs no comparison between cells to
interpret. The pre-registration did not name it as an endpoint and it is
reported here as an observation, not a finding.

**What this does not license.** No claim that disclosure is useless in general
— only that this content, disclosed reliably in this place at this time, on
this island with this model, did not improve exchange. The capability
hypothesis in `PROPOSAL-capability-interaction.md` is untouched by this run and
is the obvious next question: the stopping rule closes *proposing new content*,
not *asking who the content was for*.
