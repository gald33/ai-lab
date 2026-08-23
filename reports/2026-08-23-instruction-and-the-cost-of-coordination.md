# 2026-08-23 — Instruction, disclosure, and where the loss actually is

**Covers:** 005 runs 005–007, and experiment 006 (runs 001, 002a, 002) in full.
**Model throughout:** `claude-haiku-4-5-20251001`, 4 traders, 180-second
episodes, on the Cobb-Douglas island from 002.

This session set out to show that telling agents useful things improves how
they coordinate. It did not show that. What it did establish is more useful
than the thing it was after, and one of its own instruments turned out to be
too blunt for most of what was asked of it.

## What was asked, and what came back

| run | treatment | primary result |
|---|---|---|
| 005-005 | maximal "talk, explain, use prices" | **−0.207**, 1 of 5 seeds favouring |
| 005-006 | minimal hint: capacities are constant | **−0.269**, 0 of 3 |
| 006-001 | disclose your cost and worth ratios | **−0.221** vs matched placebo, 1 of 5 |
| 006-002 | the same, with a named key and a schedule | **−0.074**, 2 of 5 |

Four treatments, four different contents, from a 426-word protocol to a single
paragraph. None helped. Three appeared to hurt.

The obvious reading — *the cost is in the adding* — is the one this report
declines to draw, for a reason established below.

## Claims

| # | claim | strength |
|---|---|---|
| 1 | Alone, these agents solve their own labour allocation almost exactly: mean **0.972** of the closed-form optimum over **104** production acts, **85** of them within 1%, and **zero** corner bundles in 312 good-slots. | `solid` |
| 2 | Trade improves the utility of the trader doing it. `u(after) ÷ u(own production)` = **1.04 / 1.07 / 1.06** across three cells, majority above 1 — and understated, since it must drop the corner productions worth zero alone, of which trade rescued 16/48, 4/5 and 18/48. | `supported` |
| 3 | The loss is in **production, not exchange**. In company, production quality falls to **0.49–0.78** of each trader's own optimum, from 0.97 alone; trade then recovers only **+0.09 to +0.13**. | `supported` |
| 4 | Told *where* and *when* to disclose, agents disclose. **20 of 20** cost keys written, every one at revision 1, against **0 of 20** in two untreated cells holding identical tools. | `solid` |
| 5 | Told only *what* is worth disclosing, they do not. Run 006-001's treated cell produced **7 free-text messages** across 200 trader-episodes; 3 carried a ratio. | `solid` |
| 6 | A shared keyed store, granted and unmentioned, goes unused. Zero keys in every untreated cell of both runs that had it. | `solid` |
| 7 | **The five-seed design cannot resolve the effects it was written to detect.** Paired differences have sd **0.322** pooled, **0.175** within a run; the pre-registered threshold has been 0.10 throughout, which needs ≈25 seeds. | `solid` |
| 8 | Instruction is harmful. | `refuted` — see below |
| 9 | Disclosure of ratios improves exchange. | `refuted` at the sizes tested; pooled effect **+0.015**, 5 of 10 seeds |

### Why claim 8 is marked refuted rather than supported

`r-ratios` is one frozen block, run twice on the same five islands. Against
`r-bare` on exchange it came in at **−0.242 (0 of 5)** in run 001 and **+0.271
(5 of 5)** in run 002. Every seed flipped sign. Pooled over ten paired rounds:
**+0.015, 5 of 10 favouring** — indistinguishable from nothing.

It is not a labelling error; workspaces match arms in both result files and
only `r-ratios` boards carry the block's vocabulary, both checked.

So the four negative numbers in the table above all sit at or below one
within-run standard deviation of a quantity whose run-to-run swing is larger
than any of them. **What has been shown is that this instrument cannot tell
these treatments apart from doing nothing** — not that instruction hurts. Two
stopping rules fired on differences of this size and should be read as *not yet
tested*, not as settled.

## What is solid, and why

The claims that survive are **absolute** measurements — a level against a
closed form, or a count. The ones that do not are **between-cell differences**.
That is the dividing line, and it is worth carrying forward as a design rule
rather than a coincidence.

- **Claim 1** compares production against `autarky()`'s closed form,
  `s_g = α_g`. No cell comparison is involved.
- **Claim 4** is 20 against 0. No power argument is needed for that.
- **Claim 2** compares a trader with itself, same episode, before and after
  exchanging — no floor, no cross-setting inference.

## A correction this session made to itself

After run 007 this report's author wrote that *"the deficit in runs 003–006 is
a trading failure."* That was too strong, and the owner caught it.

Run 007 measures solution quality on a strictly **easier** problem: a solo
agent has no access to half the joint one — who to trade with, at what rate, in
what order. A harder problem being harder is not a failure at it.

What survives is the autarky utility as a **participation constraint**: an
agent below it would rather not have traded. That needs no assumption about
difficulty. What does not survive is treating the solo score as the expectation
for the joint score. The correction is appended, dated, to run 007's record
rather than edited into it.

## The mechanism the numbers point at

Production in company is a **bet placed before the outcome is known**. Labour
commits inside the same episode as the negotiating, so specialising is a wager
on counterparties who may never answer. Cobb-Douglas makes a lost wager total:
one good at zero is utility zero.

The evidence: **48 corner productions** in the control cell of run 002, worth
nothing without a completed trade, of which **16** were completed. A 27% lapse
rate on proposals at the bell. And a fall from 0.97 to 0.49 in production
quality between playing alone and playing in company.

No disclosure hint can fix that, which is consistent with four of them not
fixing it. What would address it is a change to the **mechanism** — letting an
exchange be agreed before production settles, or letting proposals survive the
bell — rather than a change to what agents are told.

## Harness failures, classified separately

Three runs died to infrastructure, none of it agent behaviour:

- **D13** — a Cloudflare 502 on a manager read killed six rounds mid-run.
  Fixed with a bounded retry on transient reads.
- **D16** — `httpx.RemoteProtocolError`, a *dropped connection* rather than a
  bad answer, went past D13's `except` clause and killed nine rounds that had
  already played all ten episodes. Fixed by catching transport faults too, and
  — the more important fix — by isolating round failures so one round's death
  no longer destroys every other round's record.
- Run 007's `v3.json` was never written, so alive fraction and rescue count are
  **not reported** for it. Reconstructing them from message counts would be a
  self-report by another name.

Also found: the hosted Switchboard viewer reads the **first** 50 messages of a
room (`since: 0, limit: 50`) and never advances, which reads as "the run has
stalled." Reported upstream; it is not this repo's code.

## Review targets, ranked

1. **Is the run effect the tool grant, or noise?** Run 002 granted
   `board_set`/`board_get`/`board_list` to all cells (D2) and that is the only
   known instrument difference between the two runs whose signs disagree.
   **Settled by:** re-running run 001's three cells under the current grant,
   same seeds. 15 rounds, 60 sessions. If the reversal follows the grant, a
   capability grant changed untreated behaviour invisibly — a finding in its
   own right. If not, claim 7 is the whole story.
2. **Claim 3's between-cell ordering.** The 0.97-alone versus 0.49–0.78-in-
   company gap is robust; the ordering *among* the three cells is exactly the
   kind of difference claim 7 says five seeds cannot resolve. Do not build on
   the ordering.
3. **Claim 2's magnitude.** 1.04–1.07 is small and the corner-bundle exclusion
   biases it downward by an unknown amount. The direction is safe; the size is
   not.
4. **Whether any of this generalises past one model.** Every number here is
   `claude-haiku-4-5` at 180-second episodes. The standing hypothesis — that a
   more capable agent has attention to spare for instruction, making the
   treatment effect a function of capability — is untested and would need a
   2×2 sized against a 0.25 effect, not 0.10.

## What changed in the instrument

- Transport faults retried; round failures isolated and recorded as failed
  rather than dropped (D13, D16).
- A solo mode: one trader per board, island still drawn at four, so capacities
  and the autarky optimum are unchanged.
- `board_*` granted, to every cell, so the treatment is the instruction and not
  the tool (D2).
- New measures, each as a script rather than a number in a message:
  `solo_floor.py` (capture and the MRS/MRT gap), `decompose.py` (presence and
  exchange, always together), `trade_gain.py` (the floor-free measure),
  `repeats.py`.
