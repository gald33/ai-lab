# 005 — the deliberation protocol, with agents

**Date:** 2026-08-21 · **Status:** four cells run, reported
**Cost:** 1,920 model calls (Haiku 4.5), ~3h50m wall-clock. The lab's first paid run.
**Record:** [`results/agents.json`](../experiments/005-deliberation-protocol/results/agents.json)
**Pre-registration:** [`PREREGISTRATION.md`](../experiments/005-deliberation-protocol/PREREGISTRATION.md) ·
**Deviations, declared before the run:** [`DEVIATIONS.md`](../experiments/005-deliberation-protocol/DEVIATIONS.md)

## Question

Does a **content-free deliberation protocol** — a shared method for proposing,
objecting, checking agreement and stopping — improve coordination, holding the
hint fixed?

## Headline

**No. Not detectably, on this task, with this model.**

| cell | stimulus | hint | coordinated | 95% Wilson |
|---|---|---|---|---|
| `baseline` | placebo | — | 3/12 | 0.09–0.53 |
| `method-only` | **protocol** | — | **4/12** | 0.14–0.61 |
| `content-only` | placebo | common | 12/12 | 0.76–1.00 |
| `both` | protocol | common | 12/12 | 0.76–1.00 |

Prediction 1 — `method only > placebo baseline` — is **not supported**.

The rate comparison is under-powered by construction, and `DEVIATIONS.md` D2
pre-specified the reading that is not: **minimum dispersion reached**, paired by
seed, exact binomial sign test.

| comparison (lower is better) | better | worse | tie | median Δ | p |
|---|---|---|---|---|---|
| `baseline` < `method-only` | 5 | 7 | 0 | +0.010 | **0.774** |
| `baseline` < `content-only` | 0 | 12 | 0 | +0.137 | 0.000 |
| `method-only` < `content-only` | 0 | 12 | 0 | +0.121 | 0.000 |
| `content-only` < `both` | 0 | 0 | **12** | 0.000 | 1.000 |

Twelve worlds, same truth, same eight private signals, same observation
schedule, same hint in every cell. The protocol moves nothing.

## Claims

| # | claim | strength |
|---|---|---|
| 1 | The deliberation protocol produces **no detectable coordination gain** over a matched placebo | solid *within this task and model* |
| 2 | The protocol adds **exactly nothing** on top of a common hint — 12/12 ties, 6/12 byte-identical submission streams | solid |
| 3 | A common hint coordinates completely — and **part of that is a display artifact**, not deliberation | supported |
| 4 | **Agreement is not correctness.** The hint cells inherit the hint's error exactly; the unguided cells are *more accurate* and almost never agree | supported |
| 5 | Zero harness failures in 48 episodes, so no rate here is standing on a moving denominator | solid |

### Claim 3 — the finding that undercuts its own cell

`content-only` and `both` reach dispersion **exactly 0.000 at round 0**, before
anyone has spoken. That is not deliberation; it is copying.

But not copying the hint: **0 of 96 round-0 submissions equal the hint exactly.**
They equal the hint *as the prompt printed it*. The prompt formats vectors with
`f"{p:.3f}"`, and eight agents independently transcribing `cloth 1.136  iron
0.859  salt 1.209` produce eight identical vectors.

So the hint's perfect coordination is **partly manufactured by the harness's
own number formatting** — a focal point created by three decimal places. A hint
displayed at full precision, or displayed differently to each agent, would very
likely not produce 0.000. This is a harness fact wearing an agent's clothes,
which is the third time this lab has caught one, and it was caught only because
the record kept the raw submissions.

It does not touch claims 1 or 2: `baseline` and `method-only` never see a hint.

### Claim 4 — what the hint actually costs

| cell | median final error vs truth | paired vs baseline |
|---|---|---|
| `baseline` | **0.057** | — |
| `method-only` | 0.093 | 4 better / 8 worse, p = 0.388 |
| `content-only` | 0.084 | 3 better / 9 worse, p = 0.146 |
| `both` | 0.084 | 3 better / 9 worse, p = 0.146 |

The hint's own error is **0.084**. The hint cells match it to three digits,
because they are the hint.

Unguided populations land at 0.057 — **more accurate than the advice** — by
averaging eight independent signals, and then fail to agree. That is the whole
trade in two numbers: the common hint buys agreement and caps accuracy at its
own error; deliberation buys accuracy and does not close.

Neither paired comparison is significant at twelve worlds. The direction is
consistent across three cells and the mechanism is arithmetic, so it is reported
as *supported*, not solid.

## Outcome classification

No rate above is computed over a denominator that hides a timeout.

| cell | coordinated | agent_failure | budget_exhausted | harness_failure | retries |
|---|---|---|---|---|---|
| `baseline` | 3 | 7 | 2 | **0** | 3 |
| `method-only` | 4 | 5 | 3 | **0** | 2 |
| `content-only` | 12 | 0 | 0 | **0** | 0 |
| `both` | 12 | 0 | 0 | **0** | 0 |

Five `budget_exhausted` worlds across the two unguided cells were **still
converging when the clock stopped**. At five submissions instead of the pilot's
twenty-one (D1), that is the deviation biting exactly where it was predicted to.

## Threats to validity

Ranked by how much they would change the conclusion.

1. **Five rounds is not twenty-one.** The protocol's steps — propose, object,
   check convergence, stop — are a *procedure over rounds*, and five rounds may
   simply be too few for a procedure to pay for itself. Three `method-only`
   worlds were still converging at the bell. **This is the most likely reason
   for the null and it is a design choice, not a finding.**
2. **One model, and a small one.** D3 chose Haiku 4.5 on the argument that a
   protocol should help a weak deliberator most. If the effect needs a model
   that can actually execute a five-step procedure under a 60-word cap, this
   design looked in the wrong place.
3. **Twelve worlds.** The rate comparison cannot separate 0.25 from 0.33, and
   the paired test on min dispersion (5/7, p = 0.77) is not evidence of absence
   either — it is a null at n = 12.
4. **A 60-word message cap.** The protocol asks for a proposal, a falsifier, an
   accept-or-object and a convergence check. Sixty words may not fit it, in
   which case the manipulation was partly suppressed by the format the harness
   enforces.
5. **Adoption is not measured**, by design. So this is a null about *giving
   agents the document*, not about agents *using the method*. The two are only
   the same thing if agents read and follow it, and nothing here establishes
   that they did.
6. **The placebo may be too strong.** It is length- and register-matched, and
   both unguided cells behave similarly. That is what a good placebo looks
   like — and it is also what a manipulation that never landed looks like.

## What would change the answer

Run the same four cells at **twenty-one rounds**, which is what the pilot
accepted and what the protocol is a procedure over. If the null survives at
twenty-one rounds on a model that can execute the steps, it is a result about
deliberation protocols. Until then it is a result about five rounds of Haiku.

## Review targets

1. **The display-precision artifact.** `prompt._vector` formats at `.3f`, and
   that alone may explain 24 of the 48 episodes. Does anything else in the
   instrument create a focal point this way?
2. **The 60-word cap versus the protocol's five steps.** Is the manipulation
   physically expressible in the space the format allows?
3. **`agents/runner.py`'s two retry paths.** Transport retries (non-zero exit,
   timeout) are silent and uncounted; content retries are counted. Confirm a
   transport retry cannot mask a model refusing the format.
4. **The paired sign test on min dispersion**, which was pre-specified in
   `DEVIATIONS.md` before the run — check the commit order (`b384417` precedes
   `1701a25` precedes the results).
5. Whether `min_r D(r)` is the right paired statistic, given that a world can
   dip below threshold once and diverge again.

## Reproduction

```bash
cd experiments/005-deliberation-protocol/experiment
python agent_experiment.py --worlds 12 --rounds 4 --concurrency 1 \
    --json ../results/agents.json
python ../analysis/paired.py ../results/agents.json
```
