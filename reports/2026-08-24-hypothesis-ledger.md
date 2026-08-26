# The hypothesis ledger

**What has actually been asked across experiments 005, 006 and 007, what each
answer rests on, and which answers survive run 003's measurement of the
instrument's own movement.**

Written 2026-08-24. Model throughout: `claude-haiku-4-5`, 4 traders,
Cobb-Douglas island from 002.

## The rule that sorts this table

Run 007's run 003 replicated one cell four times, changing nothing, and
measured how much the answer moves on its own:

| endpoint | run-mean sd |
|---|---|
| captured gain (a ratio) | **0.229** |
| `eff_round` | 0.155 |
| share above own autarky | 0.085 |
| share ruined | 0.073 |
| *observed again in 007 run 005's control* | *0.073 → **0.114*** |

So: **an absolute level, or a lopsided count, can be trusted. A difference
between two cells smaller than ~0.15 cannot**, on any endpoint this lab has
used. Every row below is graded on that basis and nothing else.

## Answered, and safe to build on

| # | hypothesis | answer | evidence | strength |
|---|---|---|---|---|
| 1 | Agents can solve their own labour allocation alone | **Yes, almost exactly** | 0.972 of the closed-form optimum over 104 production acts, 85 within 1%, zero corner bundles in 312 good-slots | `solid` — a level against a closed form |
| 2 | Agents execute a production instruction they are handed | **Yes, immediately and exactly** | 214/214 settled productions matched the plan's shares; 7 rounds fully compliant in episode 1; control 0/215 | `solid` — a count, 214 against 0 |
| 3 | Agents disclose when told *where* and *when* | **Yes** | 20/20 cost keys written, each at revision 1; two untreated cells holding identical tools wrote 0/20 | `solid` |
| 4 | Agents disclose when told only *what* is worth saying | **No** | 7 free-text messages across 200 trader-episodes; 3 carried a ratio | `solid` |
| 5 | Granting a capability, unmentioned, changes behaviour | **No** | `board_set` granted to all three cells; only the instructed cell used it, 20 against 0. Repeated with split labour: 68% of treated trader-episodes split, 0 of 149 untreated | `solid` — twice, on different capabilities |
| 6 | Trade improves the utility of the trader doing it | **Yes, modestly** | u(after) ÷ u(own production) = 1.04 / 1.07 / 1.06, majority above 1; understated, since it must drop corner productions worth zero alone | `supported` |
| 7 | The loss in a peopled round is in production, not exchange | **Production** | production quality falls to 0.49–0.78 of each trader's own optimum in company, from 0.97 alone; trade then recovers +0.09 to +0.13 | `supported` |
| 8 | Execution breaks in the exchange, and specifically in the quantities | **Yes** | partners and goods almost always right (8/120 settled combinations off-plan); quantities right 53% of the time, 22% under half, 12% over | `supported` |
| 9 | This instrument can resolve the effects it was built to test | **No** | same cell, same seeds, four times: between-run sd 1.03 on captured gain, mean range 2.13, one seed spanning +1.00 to −4.44 | `solid` — and it retires most of the rows below |

## Answered, and the answer is "we cannot tell"

| # | hypothesis | verdict | why |
|---|---|---|---|
| 10 | A content-free deliberation protocol improves coordination (005's founding question) | **unresolved** | measured at −0.207 to +0.044 across runs; the design's threshold was 0.10 against noise of 0.23+ |
| 11 | A domain hint improves coordination | **unresolved** | 006's ratio block: −0.242 in one run, **+0.271** in the next, same block, same seeds, sign reversed. Pooled +0.015 |
| 12 | Disclosure of cost/worth ratios improves exchange | **unresolved** | manipulation succeeded (row 3); the outcome difference is inside the noise |
| 13 | Committing labour in pieces improves the outcome | **unresolved** | manipulation succeeded (row 5); primary 4/12 seeds, and its own control failed to replicate — exchange completion 78% → 33% with no mechanical difference |
| 14 | Handing over the whole solution beats handing over nothing | **probably yes, and it is the best-supported difference here** | four independent replicates of the plan cell all beat the control: rounds above floor 5, 4, 7, 5 against 1; mean efficiency 0.390–0.737 against 0.192. **But the control is a single draw** and has the same ~1.0 noise |
| 15 | With the cheat removed, protocol or hint raises the share of traders above their own autarky | **null, and protocol flips** | pass A +0.044 / +0.130 / +0.134; pass B −0.126 / +0.015 / +0.043. No cell met "≥ +0.15 on 8 of 12" in either pass; `l-protocol` reverses sign between passes |
| 16 | With the cheat removed, protocol or hint reduces ruin | **directionally yes, at the edge of resolvability** | all three cells lower in **both** passes; pooled over 24 seeds: −0.108, −0.118, **−0.161**. But the control's own ruin rate moved **0.114** between the same two passes, so only `l-both` is clearly outside it | `weak` |

## The shape of the whole thing

**Nine questions of the form "do they do it at all" have clean answers. Seven
questions of the form "does it help, and by how much" do not.**

That split is not an accident of any one design. It is what an instrument with
a run-to-run movement of 1.03 on its natural outcome measure can and cannot
produce. The manipulation checks are counts of an event that either happened or
did not — 214 against 0, 20 against 0, 68% against 0% — and no amount of run
noise turns those over. The outcome differences are means of a heavy-tailed
ratio, and the noise swamps them.

**The one thing that repeatedly worked was the thing that was cheating.** The
full plan is the only treatment whose advantage survived replication (row 14) —
and it contained numbers computed from all four traders' private data. Every
legitimate treatment derived from it, once the cheat was stripped out, lands
inside the noise (rows 15, 16).

**What that does not license.** It does not say instruction is useless: rows
2–5 show instruction reliably changes behaviour, immediately and exactly. It
says this island, this outcome measure and this sample size cannot price that
behaviour change in utility.

## What is missing to see real comparisons

1. **An outcome measure that is not dominated by the Cobb-Douglas zero.** The
   variance is concentrated in exactly the seeds whose plans fail to complete;
   one trader at zero moves a round by units. Bounded shares already cut the
   noise threefold (0.229 → 0.073) and were still not enough.
2. **A mechanism where a partial plan degrades smoothly.** Run 002 reached for
   this and could not demonstrate it against the noise. It remains the most
   promising unexplored change, and it is a change to the game rather than to
   the prompt.
3. **Replicated controls, always.** Row 14 — the lab's best difference — rests
   on four treated draws against **one** control draw. Two more control
   replicates would settle it, and cost about an hour.
4. **Honest power, pre-registered.** 0.15 at the observed spread needs roughly
   370 paired seeds on captured gain, or n≈25 on the bounded shares. Every
   threshold set so far was 0.10–0.15 at n=3–12.

## The rows worth spending on next

Row 14, because it is nearly a result and is cheap to finish. Row 16, because
it is the only surviving signal from the legitimate blocks and one more pass
would separate it from the control's own movement. Nothing else on this table
is close.
