# Run NNN — <short name>

**Opened:** YYYY-MM-DD · **Status:** specified | running | done | abandoned

Everything above the Outcome line is written **before** the run starts and is
not edited afterwards. If it turns out wrong, record a deviation — do not
rewrite the record.

Same rule as the experiment template: **a heading kept with nothing under it is
worse than no heading.** Delete what does not apply.

---

## Why this run

One paragraph. What question this particular execution answers, and what the
previous run left open. If this is a repeat, say what changed and why.

## Specification

What is being executed, precisely enough to rebuild without asking anyone.

| | |
|---|---|
| entry point | `experiment/....py` (commit `<sha>`) |
| conditions | |
| units / counts | rounds, episodes, agents |
| seeds | listed, or the rule that generates them |
| models | exact ids and versions |
| stimuli | path + body sha256, or "none" |
| command | `...` |
| cost | expected spend, and the explicit go if it is a paid run |

Anything environment-specific that will silently change the result belongs
here too.

## Assumptions

The load-bearing beliefs — what has to be true for the output to mean what it
is intended to mean. Each one written so it could be found false.

| # | assumption | how it would show up as false |
|---|---|---|
| A1 | | |
| A2 | | |

Not a caveats list. If an item cannot fail, it is background, not an
assumption.

## Hypothesis

What you expect, stated in this run's metric, before seeing it — and what
result would change your mind.

- **Expect:**
- **Would surprise me:**
- **Would make me abandon the design:**

## Metrics for this run

Which pre-registered metrics this run reports, and their denominators. If the
run introduces a metric that is not already pre-registered, say so explicitly
— that is a new commitment, not a detail.

## Failure modes anticipated

Harness and timing failures that would make this run uninformative, and how
they are told apart from agent behaviour. Classified separately, per the
standing decisions.

---

## Outcome

*Written after. Numbers with denominators; no interpretation here.*

- **Records:** `results/...`
- **Ran:** counts attempted / completed / failed, and which failures were
  harness rather than behaviour
- **Numbers:**
- **Assumptions that did not hold:**
- **Deviations:** links to the dated entries

## What this changed

One or two lines: what the next run does differently, or why there is no next
run.
