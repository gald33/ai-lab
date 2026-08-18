# Games

A game here is **an experiment opened for participation.** The ordering matters
and it only runs one way: something is an experiment first, and becomes a game
if opening it to outside players would produce data I can't get alone. Nothing
is designed as a game first.

That constraint is the whole point. A game designed as a game optimises for
being fun to play, and what you learn from it is whatever the fun happened to
leave behind. An experiment wrapped as a game keeps its measurement intact and
gains a playful surface: a scoreboard, an invitation, something to beat — laid
over a data collection that was already justified without any of it.

**Nothing is playable yet.** There is no game here, no submission endpoint and
nothing to sign up for. This file is direction.

## What a game has to preserve

Wrapping an experiment in a game surface is allowed to change the presentation.
It is not allowed to change the measurement.

**Deterministic judging.** Scoring must be computable from the run record by
code, with no model in the loop. This is a real cost, not a preference — a
model-judge becomes part of what's being measured, and it varies across the same
axes as the players. If the judge is a model, a result about a player is
partially a result about the judge, and there's no clean way to separate them
after the fact. The consequence is that entire categories of interesting task
are off the table: anything where quality is genuinely a judgement call can't be
run as a game here, however good a game it would make.

**Structured per-run records.** Every run produces a record that stands on its
own: model, prompt, harness, tool set, declared strategy, the full sequence of
actions and messages with timestamps, outcomes and scores. A leaderboard row is
a summary of that record and never a replacement for it. Most of the analysis
value is in what players did, not in who won.

**Objectives kept uncollapsed.** Games usually have one score because one score
ranks cleanly. These won't. Where an experiment has several objectives that
genuinely trade off — speed against cost, coverage against precision, throughput
against interference — they stay separate and results read as a Pareto frontier.
Collapsing them into a weighted sum destroys the finding and replaces it with my
choice of weights, which nobody came here to learn about.

**Agent-agnostic entry.** Playable by whatever you already run: an MCP server, a
CLI agent, a custom harness. No SDK to adopt, no framework to inherit. If
entering requires using my code, the results are about my code.

## Deliberately not being built

- A submission service.
- Accounts.
- Leaderboards as a product.
- A game engine, or anything shared across games that don't exist yet.

Each of these becomes worth building the moment a second game needs it, and is a
distraction until then.
