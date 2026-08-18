# 001 — Switchboard coordination

**Status: run, not published. Nothing below is a result.**

This is a skeleton. The experiment has been run; the data has not been cleaned,
the analysis has not been written, and no outcome is claimed here. Where you'd
expect numbers, there are none — not because they're being withheld for effect,
but because publishing a number I haven't finished checking is worse than
publishing nothing. The design, the reasoning and the one negative result I
already know I need to preserve are here because those don't depend on the
numbers.

## Question

When multiple AI agents work the same shared resources, does coordination
improve because the agents reason harder about each other — or because good
coordination primitives leave them less to reason about?

These predict different things. If it's better reasoning, richer context about
the other agents should help, and the gains should scale with model capability.
If it's reduced reasoning load, then the mechanisms that win will be the ones
that *remove* inference — and a weaker model with a deterministic rendezvous
should do fine.

## Motivation

Multi-agent coordination is usually improved by giving agents more: more context
about each other, more explicit protocol in the prompt, more instructions about
when to defer. That treats coordination as an inference problem. But most of
what agents infer about each other — is anyone else on this file, when will they
be done, is it safe to start — is state that a system could simply *hold*, and
hand over as fact.

I ran into this building Lucille, a production assistant where several agents
edit one codebase. Adding coordination conventions helped. I couldn't say why,
because that system has far too many moving parts to attribute anything to
anything.
This experiment exists to make the attribution possible.

## Design: five stages

Each stage adds one mechanism to the one before it. The point of the ordering is
that the mechanisms move progressively *away* from inference and towards
guarantee.

1. **Baseline coordination** — agents share a task and can communicate, with no
   protocol imposed. Whatever coordination happens, they invent.
2. **Shared conventions** — an agreed protocol for announcing intent and
   yielding. Still entirely in-model: the convention is followed by reasoning
   about it.
3. **Richer primitives** — presence, leases, and a shared board. The system now
   holds coordination state, and answers questions the agents previously had to
   infer.
4. **Learned timing prediction** — agents get a predictor for how long others
   will hold what they hold. Inference, but informed by history rather than
   guesswork.
5. **Deterministic rendezvous** — coordination points where the outcome is
   decided by the system, not negotiated. Nothing left to infer.

The idea this circles is that **sometimes the best way to make agents work
better is to give them less to think about**. That is the hypothesis under test.
It is not a finding, and stage 5 beating stage 2 would not by itself establish
it — a rendezvous also changes the timing structure of the task, which is a
confounder that has to be handled separately.

## The negative result to preserve

Stage 4's timing predictor can become well calibrated — its predictions matching
observed hold durations closely — without improving completion time at all.

That is not a broken predictor. It's a predictor that solved a problem the task
didn't have: if timing was never the bottleneck, forecasting it better buys
nothing. It is the cleanest example in this experiment of why **calibration and
performance are separate claims and need separate metrics**. Reported as one
number, a well-calibrated predictor would look like a working mechanism, and the
flat completion time would get quietly attributed to noise.

This one is being written down first precisely because it's the result most
likely to get dropped.

## What will be published

- `experiment/` — harness, agent configuration, task definitions, stage
  implementations.
- `results/` — raw per-run records: model, prompt, stage, actions and messages
  with timestamps, lease and board state transitions, outcomes.
- `analysis/` — the write-up. Per-stage metrics, mechanism metrics reported
  separately from outcome metrics, confounders named, and the negative results
  kept.

All three are empty for now.
