# Gal's AI Lab

Experiments in how AI systems reason, coordinate, remember, and use tools.

I build AI systems, run into behaviour I can't explain, and design smaller
experiments to work out what's going on. This is where those experiments live.

## Where the questions come from

The questions come from systems that are already running, because that is where
the surprises are.

The first one came from Lucille, an assistant I run in production — persistent
memory, a job queue, a worker loop, several agents working the same codebase at
once. Over time I added coordination conventions between those agents, and
logic that ran outside the model's own loop rather than inside its prompt. Both
helped. Neither was explicable: the system had far too many moving parts for me
to say *which* part of "agents coordinate better now" was doing the work, or
why moving a decision out of the model improved it.

So I built a much smaller thing — [Switchboard](https://github.com/gald33/switchboard),
a coordination hub with presence, leases and a shared board — where one claim
can be changed at a time and the rest held still. That is the shape this repo
keeps returning to: the working system produces the question, and something
smaller gets built to answer it.

Coordination is where this started, not where it stops. Memory, tool use, and
how agents represent each other are all subject to the same problem — they get
adopted because they seem to help, and the system they help is too complicated
to say why.

## The loop

```
build → notice → isolate → experiment → understand → apply
```

`build` a real system. `notice` behaviour you can't explain. `isolate` it into
something small enough to be wrong about cheaply. `experiment`. `understand`
what actually carried the effect. `apply` it back to the real system, which
promptly produces the next thing you can't explain.

## How experiments are run

- **Start from a concrete question.** Not "does coordination help" — a question
  whose answer would change what you build next.
- **Isolate the mechanism, and make it load-bearing.** If you can remove the
  thing under test and the numbers don't move, you measured the harness, not the
  mechanism.
- **State what's held fixed.** Model, prompts, tools, task, seed, harness.
  Anything unstated is a variable, whether or not you meant it to be.
- **Measure mechanisms separately from outcomes.** A component can work exactly
  as designed and move nothing. Those are two claims and they need two metrics —
  conflating them is how a working part gets credit for an unrelated result.
- **Verify agent claims against system state.** An agent reporting that it did
  something is a claim. What the system recorded is an observation. Score the
  observation.
- **Keep negative results, and name the confounders.** The interesting failures
  are the ones where something worked and it didn't matter.
- **Reproduce where practical.** Non-determinism is real; run counts, seeds and
  raw records are how you stay honest about it.

## Lifecycle

```
Explore → Publish → Open → Play → Learn again
```

**Explore** privately, against a real system. **Publish** the design, the data
and the interpretation, including what failed. **Open** it to outside
participation when other people's strategies would tell me something I can't get
alone. **Play** — some open experiments get wrapped as games for AI agents,
which is a presentation choice, not a design one: playful surface, the same data
collection underneath. **Learn again** from the wider distribution of players,
which is usually stranger than anything I'd have thought to try.

Most experiments stop at Publish. That's fine.

## Experiments

| # | Experiment | Question | Status |
|---|---|---|---|
| 001 | [Switchboard coordination](experiments/001-switchboard-coordination/) | Does coordination improve because agents reason harder about each other, or because they have less to reason about? | Run; results not yet published |
| 002 | [Barter conventions](experiments/002-barter-conventions/) | Does a shared convention for talking about value make agents better off — and is it the words, the machinery, or the disposition that does the work? | Running; Tier 1 complete, Tier 3 designed |
| 003 | [Promotion rules](experiments/003-promotion-rules/) | When solutions to a task compete and the winner is promoted automatically, what rule converges on the good solution rather than the lucky one — and does a solution whose value depends on being shared need a different rule? | Tier 1 complete |
| 004 | [Stock and flow](experiments/004-stock-and-flow/) | Is 002's ruin a fact about the convention, or about a world where a production commitment can never be taken back? | Run |

## Layout

```
experiments/     one directory per experiment; number-prefixed, ordered by start
games/           experiments opened for participation — direction only, nothing playable
reports/         session reports: what was run, what it supports, where it is weakest
templates/       a starting point for a new experiment
tools/           shared utilities, once a second experiment needs them
```

[reports/](reports/) is where a working session is written up across experiments
— including the results that were wrong before they were right. Each report
grades its own claims and names what to attack first.

Each experiment owns its own code, results and analysis. There is no shared
framework, deliberately — experiments that have to fit a framework end up
measuring the framework.

## Grounding a run

An agent running an experiment is grounded in three things and nothing else:
the standing decisions in [CLAUDE.md](CLAUDE.md), the general
[experiments/GROUNDING.md](experiments/GROUNDING.md), and that experiment's own
`CLAUDE.md`. **No other experiment's directory is in scope** — grounding from a
sibling experiment arrives looking authoritative and silently imports a metric
or an assumption frozen for a different question.

`tools/ground.py <n>` prints exactly that bundle, and
`tools/ground.py <n> --new-run "<name>"` opens a run record.

Every run whose result is meant to be kept gets a record under
`experiments/<n>/runs/`, committed **before** the run. It carries the
**specification** (enough to rebuild the run without asking anyone), the
**assumptions** (what has to be true for the output to mean what it is meant
to mean, each written so it could be found false), and the **hypothesis**
(what is expected, and what would change your mind). Only the outcome is
written afterwards.

## License

MIT. See [LICENSE](LICENSE).
