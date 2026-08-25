# 005 — instrument review of the v1 agent run

*Written 2026-08-22 against `results/agents.json` (48 episodes, 1,920 messages,
4 cells × 12 worlds × 5 rounds). Offline: nothing was run and nothing spent.*

This answers three roadmap items — `005-display-precision-artifact`,
`005-word-cap-fits-the-protocol`, `005-transport-retry-audit` — which between
them ask whether v1's **null measured the manipulation or the instrument**.

Short answer: **one of the three is a real artifact and it is decisive**, one is
ruled out, and one is separated by construction with a named residual.

## 1. Display precision — confirmed, and larger than the report claimed

Every number an agent sees is rendered by `prompt._vector`, which formats with
`f"{p:.3f}"`. There are exactly three render points and all three use it:

| render point | in `build()` | creates a focal point? |
|---|---|---|
| the hint | `HINT_BLOCK.format(hint=_vector(hint))` | **yes — decisively** |
| the agent's own private signal | `_vector(signal)` | snaps submissions to a grid |
| other traders' prices heard | `_vector(price)` | imitation lands on the grid |

What the record shows:

- **99.2%** of submitted numbers (5,714 / 5,760, excluding bread which the
  format pins at 1.0) already sit exactly on the 3-decimal grid. Agents submit
  what they were shown.
- Round-0 dispersion, **before anyone has spoken**: exactly `0.000` in **11/12**
  `content-only` worlds and **6/12** `both` worlds, and **0/12** in the two
  cells with no hint. Both hinted cells have `median_rounds_to_coordinate = 0`
  and a coordination rate of **1.000**; the unhinted cells score 3/12 and 4/12.

So the hint cells did not coordinate by deliberating. They coordinated because
every agent was handed the same number rounded to three places and copied it.
The earlier report put this at "may account for 24 of the 48 episodes"; on the
record it accounts for the entire hint effect — every hinted world is
coordinated at round 0 by rounding.

**Consequence.** Any comparison involving `content-only` or `both` in v1 is a
measurement of the renderer. The two unhinted cells (`baseline` 3/12,
`method-only` 4/12) are not affected by this artifact and remain readable.

## 2. The 60-word cap — ruled out

The concern was that the protocol's five steps could not fit in a capped
message, so a null would be a result about the format rather than the
manipulation. The record says the cap never bound:

    words per message   min 5   median 22   mean 22.0   max 52
    at or over the 60-word cap:  0 / 1920

Not one message came within eight words of the cap. The format could express
the manipulation.

The steps were nonetheless barely performed. Counting how many of the five
moves appear per message, by generous regex on the *move* rather than the
wording:

| cell | mean steps/message | messages with ≥3 of 5 |
|---|---|---|
| `baseline` | 0.70 | 0 / 480 |
| `content-only` | 0.25 | 0 / 480 |
| `method-only` | 0.77 | 2 / 480 |
| `both` | 0.92 | 2 / 480 |

Four or five steps never co-occur in any message in any cell. The protocol
raised step-presence over `baseline` only slightly (0.77 vs 0.70).

This **strengthens** the null rather than undermining it: the manipulation was
expressible and was simply not performed. It also reframes what v1 tested — not
"does a protocol help" but "does printing a protocol cause agents to follow it",
to which the answer here is mostly no.

## 3. Transport retries — separated by construction, with one residual

`agents/runner.py` has two layers. `_invoke` retries up to `TRANSPORT_ATTEMPTS
= 3` on a timeout, a non-zero exit, or empty stdout, and does not count them.
`ask` catches `AgentFault` from **parsing** and retries once, recording
`retried=True`, which reaches the record as `retries`.

A model refusing the format returns exit 0 with non-empty stdout containing
prose. That path cannot reach `_invoke`'s retry — it fails later, in
`_read(_extract(raw))`, and is therefore counted. So the two are separated by
construction, and the recorded counts (`retries`: 3, 0, 2, 0 by cell; 45/48
episodes at zero) are counts of content retries.

**The residual, which the record cannot rule out:** a refusal that produces
*empty stdout* or a non-zero exit is indistinguishable from a transport
failure, and would be retried up to three times silently. Nothing in
`results/agents.json` distinguishes those cases after the fact.

**What claim 5 may say:** that no content-retry rate stands on a moving
denominator — true. Not that the harness-failure count of zero is complete.

## What this means for the re-run

`005-rerun-at-twenty-one-rounds` was blocked on these two reviews precisely so a
second paid run would not buy the same artifact. It should not be unblocked as
specified: re-running the same four cells at twenty-one rounds would reproduce
the round-0 focal point in both hinted cells, and 24 of 48 worlds would again be
"coordinated" before anyone spoke.

What has to change first is the renderer, not the round count — the hint (and
arguably the signal) must be shown at a precision that does not hand every agent
an identical string, or the hint cells must be dropped.

---

**Followed up 2026-08-25.** The prescription in the paragraph above — render
the hint at a higher precision — does not work, and `RENDER-PRECISION.md` shows
why from this same record: the hint is one number given to everyone by design,
184 of 192 round-0 hinted submissions are that number as printed, and the
3-decimal grid never once collided two agents' private signals. The choice is
between dropping the hinted cells and redefining the hint, and the round-0
check that decides it is now `analysis/focal.py`.
