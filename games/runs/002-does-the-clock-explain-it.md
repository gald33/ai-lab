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

## What this changed

*Written after.*
