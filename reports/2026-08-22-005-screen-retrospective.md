# 005 — the ten-arm screen, written up after the fact

**This is a retrospective, not a run record, and it is not grounding.**

The screen ran on 2026-08-22, before `experiments/GROUNDING.md` required a
record under `runs/` written and committed *before* a run. It therefore has no
specification, no assumptions and no hypothesis fixed in advance, and one
cannot be supplied now: a pre-registration written after the numbers are in is
not a pre-registration. So the fifty rounds below are **exploratory output**.
They are evidence about the environment and about the instrument. They are not
a result about any advice block, and nothing here should be cited as one.

What it is for: the mechanisms it exposed are what the next design has to
answer to, and they would otherwise live only in a session transcript.

## What ran

Ten one-off advice blocks (`stimuli/screen/`, never frozen, not citable), one
per arm, five seeds each. 3 episodes × 180s, 2 traders, `claude-haiku-4-5`,
managed Switchboard hub, one workspace per arm × seed. All 50 rounds completed
and are in the denominator; 10/10 acknowledgement in every arm; no harness
failures after the TLS fix described below.

`results/screen/v3.json` is the record. `analysis/screen.py` reads it.

**There was no control arm.** All ten cells carried a block, so the numbers are
measured against the autarky floor and nothing else. The screen cannot say
whether any block beat *saying nothing*, and a baseline cannot be borrowed from
an earlier run whose code, clock and trust settings differed. `run_v3.py` now
refuses a run with no control unless `--no-control` is passed.

## The numbers

The autarky floor moves with the seed — 0.523 to 0.823 — so raw `eff_round`
says more about which island a round drew than about which block it ran. Every
figure is the paired difference `eff_round − floor`.

| arm | block | seed1 | seed2 | seed3 | seed4 | seed5 | mean | median | >floor | zero ep. |
|---|---|---|---|---|---|---|---|---|---|---|
| `s05` | comparative advantage | −0.357 | +0.052 | −0.109 | +0.059 | +0.159 | −0.039 | +0.052 | 3/5 | 2 |
| `s04` | coverage | −0.380 | −0.031 | −0.176 | +0.096 | +0.237 | −0.051 | −0.031 | 2/5 | 2 |
| `s01` | the manager | −0.368 | −0.046 | −0.185 | +0.030 | +0.211 | −0.072 | −0.046 | 2/5 | 2 |
| `s02` | talking convention | −0.823 | −0.024 | −0.043 | +0.135 | +0.161 | −0.119 | −0.024 | 2/5 | 4 |
| `s07` | checklist | −0.823 | +0.134 | −0.269 | +0.157 | −0.003 | −0.161 | −0.003 | 2/5 | 4 |
| `s09` | failure modes | −0.823 | +0.065 | −0.346 | +0.139 | +0.150 | −0.163 | +0.065 | 3/5 | 5 |
| `s03` | coupling | −0.226 | −0.258 | −0.391 | −0.263 | +0.102 | −0.207 | −0.258 | 1/5 | 5 |
| `s10` | asking | −0.642 | −0.121 | +0.087 | −0.180 | −0.206 | −0.212 | −0.180 | 1/5 | 6 |
| `s08` | population | −0.282 | +0.041 | −0.666 | −0.027 | −0.174 | −0.222 | −0.174 | 1/5 | 7 |
| `s06` | worked example | −0.497 | −0.523 | −0.353 | −0.362 | +0.256 | −0.296 | −0.362 | 1/5 | 10 |

**No block beat autarky on either statistic.** The ranking is not defensible:
the top five span 0.12 of mean while a single arm's own rounds span up to 0.78.
The spread of seed means is **0.612**; the spread of arm means is **0.256**. The
island outweighs the advice by 2.4×, and at one round per cell there is no
power to resolve anything smaller than that.

Two arms separate on mean and median together — `s06` and `s03` at the bottom —
and only `s06` has a mechanism behind it (below).

## What it actually found

These hold across arms, and matter more than the ranking.

**Coverage is the outcome, not a symptom.** Sorting rounds by how many
agent-episodes ended holding none of some good:

| zero agent-episodes | n | mean vs floor |
|---|---|---|
| 0 | 24 | **+0.059** |
| 1 | 4 | −0.157 |
| 2 | 10 | −0.212 |
| 3 | 9 | −0.470 |
| 4 | 2 | −0.654 |
| 5 | 1 | −0.823 |

Monotone across all six buckets, and rounds with no holes beat autarky on
average. Trade volume barely separates the groups (16.5 settlements above floor
against 15.4 below). The game is not trading well; it is never ending an
episode with a hole.

**Episode 1 is where rounds are lost.** Mean `eff_episode` climbs 0.373 → 0.509
→ 0.534, and 23 of 50 first episodes score zero against 11 of the last. The
mechanism, read off the boards: both traders produce, both send an offer,
neither approves the other's, the bell rings, both proposals lapse, and both eat
a bundle with a hole in it.

**Above-floor rounds are flat.** The 18 rounds that beat autarky have a mean
within-round spread of 0.059 and contain **no zero episode at all**. The 32 at
or below average 0.442 spread and hold 47 zeros. The best round found a
three-trade pattern in episode 1 and replayed it byte-identically twice. What
good rounds share is repetition, not deliberation — and nothing in the ten
blocks was written to induce it.

**The traders do not talk.** Across 50 rounds and ~790 settled actions,
free-text discussion totals **30 messages**, 19 of them in `s10` alone. A
PROPOSE *is* the message. This is the finding that most affects what to run
next: the protocol-versus-hint decomposition assumes a communication channel
live enough to manipulate, and this one is not.

**The worked example anchors the wrong shape.** `s06` showed a two-good island;
its traders opened episode 1 with two-good production lines against a four-good
product utility, which is a hole by construction. It carries 10 zero episodes,
more than double any other arm — and also the single best round in the screen
(+0.256), which is why the honest claim is narrow: *the example anchors
first-episode production on two goods*, not that it reliably hurts. The block
has since been revised to four goods, so its number here belongs to the earlier
text and the two are not comparable.

**Seed 1 is unwinnable as drawn.** Ten arms, none above floor, best −0.226,
three exact zeros. Its floor is 0.823: autarky already sits near the frontier,
so there is little to win and a hole loses everything. It contributes a large
constant penalty to every mean.

## Harness failures, classified

Recorded here because the grounding rules ask for them to be separated from
agent behaviour, and because both cost a run.

**Attempt 1 died four minutes in.** Every session started, found every
Switchboard tool returning "internal error", asked to have the connection
fixed, and stopped. Cause: the CA bundle this session's proxy points tools at
carries the proxy's roots but not the public ones, while the hub presents a
real public chain — `curl` survives that, Python's `ssl` does not. The manager
was unaffected because it inherits the parent environment; the agents' MCP
subprocesses get an explicit env and inherit nothing. A pre-flight canary now
spawns `switchboard-mcp` exactly as an agent gets it and calls one tool.

**Attempt 2 was contaminated and was stopped by hand.** Workspaces were named
per arm and seed and therefore reused; hub messages live an hour, so traders
calling `history` read a schedule, an episode opening and a bell belonging to
the previous run. Workspaces are now stamped per run.

Neither is agent behaviour, and neither would have been visible in the metrics.

## What was fixed afterwards

Episode gating (the acknowledgement window was part of episode 1, making it
longer than its siblings and longer for whoever produced early); the control-arm
refusal; the canary; a per-episode ledger recording lapsed proposals, who went
without what, and every refusal with its reason; coverage promoted to a reported
endpoint; a schema check on the analysis. 34 gates, five pinned to these.

## What this cannot support

Any claim that one block beats another. Any claim that a block beats no block.
Any number cited as a result. The screen narrowed a space and exposed three
mechanisms; the next run is where those become testable, with a record written
first.
