# Game 002 — does the clock explain it?

*Opened from [`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and committed **before** the run, per
[`experiments/005-deliberation-protocol/CLAUDE.md`](../../experiments/005-deliberation-protocol/CLAUDE.md).*

## Why this run

[Game 001](001-the-first-game-anybody-played.md) answered its question — an
agent plays — and produced a finding nobody had ordered: **both traders
finished below autarky**. `eff_round` 0.2986 against a floor of 0.7103, so
`capture` **−1.42**. They would each have done better never trading at all.

The record deliberately did not guess why, and named three candidates: the
agents, the sixty-second episode, or the model. This run takes the cheapest and
most testable of the three.

**The clock is the best candidate on the evidence.** T1 spent its whole labour
on a single good twice — zero utility under Cobb-Douglas without a trade — and
the trade it needed did not settle until episode 3. That is the shape of a
trader that has not had time to notice its own mistake, and sixty seconds is
the only thing in the design that decides how long noticing takes.

## Specification

| | |
|---|---|
| entry points | `games/island/run_entrant.py`, `run_game.py` (commit `45e5f38`) |
| conditions | one changed variable against game 001: **episode length, 60s → 150s**. Everything else held |
| units / counts | 1 game · 1 round · 3 episodes · 2 traders · **4 goods** |
| seeds | drawn by the lobby at settlement, not chosen. Recorded in the outcome |
| models | `claude-haiku-4-5-20251001`, both seats — the same as 001 |
| stimuli | the four-good brief, `games/island/brief.py`, body sha256 `a8dda7f5d79bc832…` — **byte-identical to `stimuli/v3/base.md`'s body**, which `test_brief.py` asserts and which is the whole reason a four-good game is comparable to 001 at all |
| command | `run_game --workspace island-game-002 --episode-seconds 150`; `run_entrant --name scout-v2 --open 2 3 1 --goods 4`; `run_entrant --name trader-b`. **No `run_lobby`** — `run_game` embeds one, and two settle every table twice (game 001's rehearsal finding) |
| cost | **2 agent sessions**, ~10 min wall clock (120s acknowledgement window + 3 × 150s episodes, plus startup). Longer than 001 by the 4½ minutes that are the point of the run. The lobby, dealer and manager are ordinary processes and cost nothing |
| go | **Given by Gal, 2026-08-25**, in answer to a proposal naming episode length as the variable to change. Recorded here before the run |

## Four goods, not five, and why that is not a mistake

The island gained a fifth good (fish) in `#45`, and the table default is now
five. **This run passes `--goods 4` on purpose.**

`viewer/scores.py:level()` is `(agents, goods, episodes)`: a five-good game is a
different level against a different frontier, on its own leaderboard, and
nothing about it could be compared to game 001. Changing the clock *and* the
goods would answer neither question. Fish gets game 003, where it is the
variable rather than a confound.

## What this is not

**Practice, and unranked** — for the same reason as 001: no released
`agent-switchboard` carries sealed-to-peer messaging (checked at 0.10.0 on the
day: no `crypto.seal_to_peer`), so the private half is dealt in the clear and
every trader can read every other's capacities and tastes.

**Both seats are the lab's own agents**, so the farming caveat in
`games/island.md` applies and the per-trader ratios are not a competitive
result.

**Not a result.** One game against one game is n=1 against n=1. Two islands
drawn from different seeds differ in how much room they leave for gains, which
is exactly what `capture` normalises for — but a single pair cannot separate a
real effect from the variance of two draws. This is a **probe**: it says
whether the clock is worth a proper paired design, not whether the clock is the
answer.

## Assumptions

| # | assumption | how it would show up as false |
|---|---|---|
| 1 | 150s is long enough to matter and short enough to stay affordable | capture unchanged at −1.4ish, with the same shape of play in the transcript |
| 2 | `capture` makes two seeds comparable at one level | the two games differ wildly on a metric that is supposed to be island-normalised, with no behavioural difference in the boards |
| 3 | the four-good brief is what 001's agents read | `test_brief.py` asserts byte-identity; if it were false the two games are not at the same level and nothing here compares |
| 4 | both sessions start and reach the board | denominators below; a session that fails to launch is a harness failure and is counted apart from a silent agent |

## Hypothesis

**Stated before the run, and it may be wrong — 001's was.**

Longer episodes raise `capture` above 001's **−1.42**, because the failure in
001 was a trader spending all its labour on one good and not getting the
trade it needed until the last episode. More time inside an episode is more
time to notice that and offer again.

**What would falsify it:** capture at or below −1.4 with the same shape of play
— all-in production on one good, trades arriving late or not at all. That would
move suspicion to the agents or the model and away from the clock.

**A real possibility either way:** more time may just mean more talk. 001 had
**0** lines of talk; if 002 fills the extra minutes with conversation and still
settles one trade, that is a finding about what these agents do with time.

## Metrics for this run

- **Primary:** `capture` — gains taken as a fraction of gains available,
  autarky 0 and frontier 1. Against 001's **−1.42**.
- `eff_round` and the autarky floor, both recorded, since capture is derived
  from them and a derived number should be checkable.
- Per-trader `u_i / autarky_i`, and **zero episodes per trader** — the specific
  mechanism 001 failed by.
- Denominators, kept apart: sessions started / reached the board / seats bound;
  lines settled / refused / talk. **A silent agent has said nothing; a session
  that could not start is a harness failure.**

## Preflight

Run and recorded before the go is acted on. A failed gate is a finding and goes
here rather than being quietly fixed until it passes.

| gate | result |
|---|---|
| `pytest games/island/tests/ .../island/tests/ .../tests/ -q` | **135 passed**, on commit `45e5f38` |
| `tools/check_stimuli.py` | **stimuli unchanged** — 005's frozen text is what the four-good brief reproduces |
| the agent's own toolchain against the live hub | **pass** — a client built the way an entrant's is (`island/ca.py` bundle, managed hub, managed token) registered on `switchboard.lucille-ai.com`, posted to a channel and read the line back. This is the gate that was broken until game 001 and that PREFLIGHT records a fifty-round run being lost to |

`switchboard` at **0.10.0**: no `crypto.seal_to_peer` and no
`RemoteSigningIdentity` guard in `mcp_server`. Both checked on the day, and
both are why this is a practice game and why `hold_signer` is still carrying
the run.

## Failure modes anticipated

- **The signer deadlock.** Still unfixed upstream at 0.10.0 (checked: no
  `RemoteSigningIdentity` guard in `mcp_server`). `run_entrant.hold_signer` is
  the workaround and it is load-bearing; if it regresses, both agents play the
  whole round awake and unable to write, which on the board is indistinguishable
  from two traders who said nothing.
- **A relative `--mcp-config`**, which killed both seats in 001's second
  attempt. Fixed and tested, named here because it cost a run.
- **Two lobbies settling one table twice**, which is why `run_lobby` is not in
  the command list.

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `games/results/g1.json`,
  `board-island-game-002b-g1.json`, `reveal-island-game-002b-g1.json`;
  ledger row `island-game-002b-g1`, round `7ad2ab4efa5b0156`, status
  **`complete`**, arm **`practice`**, level **`2 traders · 4 goods · 3
  episodes`** — the same level as game 001, which is what makes the two
  comparable at all. `scores.py --verify` redraws all 75 rows from their own
  seeds: **0 disagreed**.
- **Watchable:** board and reveal kept in [`games/replays/`](../replays/) and
  published — <https://gald33.github.io/ai-lab/>, `island-game-002b-g1` in the
  dropdown.
- **Ran:** 2026-08-25, managed hub, workspace `island-game-002b`, table `g1`,
  seed **6789904112895503135** (drawn at settlement, not chosen). 3 episodes of
  **150s**, 2 traders. Both seats `claude-haiku-4-5-20251001` run by
  `run_entrant`; the record's `model` field reads `entrants` for the same
  reason as 001.
- **Ran, in denominators:** sessions started **2/2**; reached the board
  **2/2**; seats bound **2/2**; acknowledged **2/2** (`T1`, `T2`); lines
  settled **16**; refused **4**; **talk 0**; proposals lapsed **4** (3 in
  episode 2, 1 in episode 3); channel messages **54**; wall clock **577.2s**.
  **Relaunched 1** — attempt 1 spent and produced nothing; see *Deviations*.
- **Numbers:** `eff_round` **0.5925** (upper 0.5950) against an autarky floor
  of **0.7115**, so `capture` = **−0.4127**. Per-trader `u_i / autarky_i`:
  T1 **0.691**, T2 **0.927** — both still below 1.00×. Zero episodes:
  T1 **1 of 3**, T2 **0 of 3**. `eff_episode` `[0.641, 0.000, 0.795]`.
  Per-episode utilities `[[0.230, 0.161], [0, 0.192], [0.208, 0.269]]`.
  Three exchanges settled (`p1`, `p2` in episode 1; `p7` in episode 3).

### Against game 001, at the same level

| | 001 (60s) | 002 (150s) |
|---|---|---|
| `capture` | **−1.4209** | **−0.4127** |
| `eff_round` / floor | 0.2986 / 0.7103 | 0.5925 / 0.7115 |
| lines settled | 8 | **16** |
| lines refused | 4 | 4 |
| **talk** | **0** | **0** |
| exchanges that settled | 1 | 3 |
| T1 zero episodes | 2 of 3 | 1 of 3 |
| T1 · T2 vs playing alone | 0.26× · 0.83× | 0.69× · 0.93× |

- **The four refusals, as the manager stated them.** No two share a reason.

  | line | manager's reason | state at that moment |
  |---|---|---|
  | T2 `PRODUCE`, 12:39:45 | *this episode has closed* | written before the acknowledgement window closed and episode 1 opened |
  | T1 `APPROVE p3` | *p3 was not addressed to you* | `p3` is T1's own proposal |
  | T2 `APPROVE p3` | *you have 0.0413 bread uncommitted, not the 0.1000 it asks for* | T2 held 0.1413 bread, 0.1 of it committed to its own **still-open** `p4` |
  | T1 `APPROVE p6` | *you have 0.3868 cloth uncommitted, not the 0.4000 it asks for* | T1 held 0.8868 cloth and had given 0.5 in `p7`, which **settled** 8s earlier |

- **Episode 2, the round's only zero.** T1 produced no iron and ended holding
  none. `p3` (T1 offering cloth for iron, bread, salt) and `p4` (T2 offering
  bread, salt for cloth) were both open; T1 held 0.5368 cloth uncommitted
  against the 0.4 `p4` asked. T1 wrote `APPROVE p3`, T2's `APPROVE p3` was
  refused, T1's replacement `p5` went up 30s before the bell and drew no reply.
  Three proposals lapsed.
- **How much of the clock was used.** The last agent line of each episode
  landed **56s, 31s and 49s** before its bell — **136s of 453s, 30% of the
  round's episode time, after both traders had stopped acting.** Median gap
  between an agent's own consecutive lines: T1 **42s**, T2 **51s**, so a 150s
  episode is about three actions per trader. Game 001's idle tails were
  **2s, 13s, 22s of 62s**.
- **Production did not change across episodes.** T1 wrote
  `PRODUCE cloth=0.6 bread=0.2 salt=0.2` in all three; T2 wrote the same bundle
  in episodes 2 and 3. Every produce line landed within 7–22s of the episode
  opening. No labour went unspent in any episode by either trader.
- **Production plans, against 001's.** In 001 T1 wrote `PRODUCE cloth=1` in two
  of three episodes — all labour on one good. In 002 the same entrant, on a
  different island, spread across three goods in all three.

### Deviations

Two attempts. **Both stay in the denominator**; a run that spent and produced
nothing is still a run.

- **Attempt 1, `island-game-002`, seed 6532871921561426033 — died, spent,
  produced nothing.** Both entrant sessions were launched with `nohup … &` from
  a tool call. The harness kills the process group when the call returns and
  `nohup` does not survive that, so both sessions started, were killed
  mid-round, and wrote nothing to the board. **A harness fault of mine, not an
  agent one**, and on the board indistinguishable from two traders who chose
  silence — which is the distinction `PREFLIGHT.md` requires a run to be able
  to draw, and it was drawn from the session logs, not the board.
- **The fix:** `setsid`, verified to survive a tool call returning *before* the
  entrants were started rather than after.
- **Attempt 2, `island-game-002b`** — the run recorded above.

**A viewer bug was found by watching the run, not by testing it.** The huts on
the island were labelled with a session id and a peer key, because the reducer
recognised the manager only by the literal author name `manager` and a card had
no clamp on a name it did not choose. Live boards use blinded peer ids, so
neither held. Fixed in [#46](https://github.com/gald33/ai-lab/pull/46). It is
recorded here because *watching the game is what found it*, which is the first
concrete argument for the viewer existing.

## The reading

**Not written here.** What this result means — whether the hypothesis held, what
it says about the clock, and what should follow from it — belongs to the
experiment, not to the game layer that ran it. This record carries what
happened: the numbers, the denominators, the boards they came from, and the
deviations. `games/runs/README.md` already says a game is not an experimental
cell; that cuts both ways, and interpreting one here would be this layer
answering a question it did not ask.

The replay is in [`games/replays/`](../replays/) and the row is in the ledger,
so the reading can be done from settled state by whoever owns it.
