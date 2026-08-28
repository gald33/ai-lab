# Game runs

One record per game whose result is meant to be kept, numbered `NNN-slug.md`,
created from
[`templates/experiment/runs/RUN-TEMPLATE.md`](../../templates/experiment/runs/RUN-TEMPLATE.md)
and committed **before** the game is played. Specification, assumptions and
hypothesis are written before and not edited after; only the Outcome section is
filled in later.

**Separate from `experiments/005-deliberation-protocol/runs/` on purpose.**
Those records answer 005's question, which has a recorded null and is not being
revisited. A game runs on the same island and much of the same code, but it is
not an experimental cell: nothing here is pre-registered against 005's metric,
and a row on the scoreboard is not evidence about the deliberation protocol.
Numbering them in the same sequence would invite exactly that misreading.

What carries over unchanged is the process, because it is the part that stops a
result meaning less than it appears to: the record is committed first, the
preflight gates are recorded with the commit they ran on, denominators are
printed, harness failures are classified apart from agent behaviour, and a paid
run does not start without an explicit go written down here.

## What has been played

| run | what it changed | level | `capture` |
|---|---|---|---|
| [`001`](001-the-first-game-anybody-played.md) | first game played by agents; 60s episodes | (2, 4, 3) | **−1.42** |
| [`002`](002-does-the-clock-explain-it.md) | episode length 60s → 150s, everything else held | (2, 4, 3) | **−0.41** |

Both are **practice** games — unranked, both hands face up, both seats the
lab's own agents. Neither is evidence about anybody else's agent.

**Games played on the open board are not recorded here.** `g1`, `g3`, `g5` and
`g6`, played by agents nobody in this lab wrote, were not pre-registered and
could not have been — they were the door being used, not a cell being run.
Numbering them alongside these would claim a discipline they did not have. What
they produced is a defect list, and it is in
[`../island/what-the-first-games-found.md`](../island/what-the-first-games-found.md).

**What these numbers mean is not recorded here.** A record in this directory
carries what happened and with what denominators; the reading of a result is
the experiment's, for the reason stated above — a game is not an experimental
cell, and this layer interpreting one would be answering a question it did not
ask.
