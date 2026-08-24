# What the barter island has taught, written for someone drafting a paper

**A self-contained account of experiments 002–007: what was built, what was
measured, what survived, and what the numbers will not support.** Written
2026-08-24. Everything here is from settled state, never from what an agent
said about what it did.

The intended reader is an agent or a person drafting a paper from this, who
has not been in the room. Section 1 is the setup, section 2 the instrument,
section 3 the findings in the order of their strength, section 4 what cannot
be claimed, section 5 the openings.

---

## 1. The setup

**The economy.** An *island* is `n` traders and `g` goods. Each trader `i` has
Cobb-Douglas tastes `α_i` over goods (Σ_g α_ig = 1) and a production capacity
vector `capacity_i`. A trader has one unit of labour per episode and splits it
in shares `s` across goods; producing share `s_g` of labour on good `g` yields
`s_g · capacity_ig` units. Utility is `u_i(x) = Π_g x_g^{α_ig}`.

Three reference points, all closed-form:

- **autarky** — the best a trader can do with nobody to trade with. Cobb-Douglas
  makes this exactly `s_g = α_ig`, and gives each trader a scalar `u_i^autarky`.
- **Walras** — the competitive equilibrium of the island: prices, an allocation,
  and each trader's utility there. This is the frontier.
- **exchange ceiling** — the gain available from trade alone, given production.

`α` and `capacity` are drawn per seed. A trader is told **only its own** `α`
and `capacity`, in a private block at launch. Nobody is told the prices, the
equilibrium, or anyone else's numbers — except in the one condition where they
deliberately were (§3, row "the plan").

**The surface.** There is one: a shared message board (Switchboard). Agents
read it and write to it. There is no tool API for the economy, no `produce()`,
no `offer()`. A *manager* process watches the board, recognises three formatted
message shapes — a declaration of production, a proposal of exchange, an
approval of one — and settles them into state. The manager enforces timing,
format and scoring, and nothing else. It never sets a price, never assigns a
role, never repairs a malformed message into a plausible one, and never asks an
agent for anything.

**No scheduler.** Every agent is its own long-lived session, running
concurrently and continuously. There are no turns, no rounds of play, no waves.
An agent reads when it wants and writes when it wants; nothing waits for it; the
bell rings on the clock. This matters for the paper's framing: the failures
below are failures of *self-organised* coordination under a deadline, not of
agents responding to prompts.

**Vocabulary** (used consistently and worth keeping):

| term | what resets at its boundary |
|---|---|
| **episode** | item stocks, labour, open proposals, episode utility |
| **round** | agent context and history, accumulated utility |

A round is `k` episodes on one island — same tastes, same capacities, same
traders throughout. Context persists across a round's episodes. That memory is
the learning channel and is the reason a round has more than one episode. Most
runs are `k = 5`, `n = 4`, `g = 4`.

**Model.** `claude-haiku-4-5` throughout, deliberately: the question is what
instruction does, and a model near its ceiling would hide the effect. Whether a
more capable model uses instruction better is written up as a hypothesis and has
not been run.

## 2. The instrument, and why this section comes before the findings

Experiment 007's run 003 replicated **one cell four times, changing nothing** —
same arm, same seeds, same stimulus, same model — and measured how far the
answer moves on its own.

| endpoint | between-run sd |
|---|---|
| captured gain `(u − u_autarky)/(u_plan − u_autarky)` | **0.229** (per-run mean sd; per-round sd 1.03) |
| `eff_round` | 0.155 |
| share of traders above own autarky | 0.085 |
| share of traders ruined (zero utility) | 0.073 |

Independently, a later run's control moved **0.114** on share-ruined between two
passes that differed in nothing.

Every threshold pre-registered in experiments 005, 006 and 007 was **0.10 to
0.15** — that is, at or below the instrument's own movement. So:

> **An absolute level, or a lopsided count, can be trusted. A difference
> between two cells smaller than about 0.15 cannot.**

One concrete illustration: experiment 006's ratio-disclosure block scored
**−0.242** in one run and **+0.271** in the next — same block, same seeds, sign
reversed. This is the single most important thing the programme has produced,
and a paper that reports the treatment effects without it would be reporting
noise. It should probably be the paper's spine rather than a limitations
paragraph.

## 3. What the data supports

Ordered by strength. `solid` = a level against a closed form, or a count so
lopsided that run noise cannot turn it over.

**(a) Agents solve their own labour allocation almost exactly — alone.**
`solid`. In solo rounds, production reached **0.972** of the closed-form
autarky optimum across 104 production acts; 85 of them within 1%; **zero**
corner bundles in 312 good-slots. The classical single-agent optimisation is
not the hard part.

**(b) Production quality collapses in company.** `supported`. The same agents,
on the same kind of island but with three other traders present, produce at
**0.49–0.78** of their own solo optimum. Trade then recovers only **+0.09 to
+0.13** of it. So the loss on a peopled island is a *production* loss, not an
exchange loss: agents distort their production in anticipation of trades that
do not arrive as expected. This is the most interesting economic result here
and the least expected.

**(c) Agents execute an instruction they are handed, exactly.** `solid`.
214/214 settled productions matched the handed plan's shares; 7 rounds fully
compliant from episode 1; the untreated control matched in 0/215. There is no
compliance problem and no comprehension problem.

**(d) Execution breaks in the exchange, and specifically in the quantities.**
`supported`. Given a full plan naming partners, goods and amounts: partners and
goods were almost always right (8/120 settled combinations off-plan), while
quantities were right only **53%** of the time — **22%** under half the amount,
**12%** over. Agents agree *who* and *what* and then get *how much* wrong.

**(e) Capability alone changes nothing; instruction changes everything.**
`solid`, twice, on two different capabilities. A board-key-writing tool granted
to three cells was used by only the instructed cell, **20 against 0**. Labour
splitting: **68%** of instructed trader-episodes split their labour, **0 of
149** uninstructed. Agents do not explore an affordance they were not told to
use. For a paper on agent tooling this is a sharp, cheap result.

**(f) Agents disclose when told where and when, not when told why.** `solid`.
Told to write a ratio to a named board key: 20/20 wrote it, each at revision 1.
Told only what was worth saying, with the same tools: **7 free-text messages
across 200 trader-episodes**, of which 3 carried a ratio. Specification of the
*channel and moment* is what produces disclosure; motivation does not.

**(g) Trade helps the trader who does it.** `supported`, modestly. Utility
after exchange ÷ utility of own production = **1.04 / 1.07 / 1.06** across
runs, majority above 1. Understated, because it must drop corner productions
that are worth zero before trade.

**(h) Handing over the whole solution beats handing over nothing.** The
best-supported *difference* in the programme: four independent replicates of the
plan cell all beat the control (rounds above floor 5, 4, 7, 5 against 1; mean
efficiency 0.390–0.737 against 0.192). **But the control is a single draw with
the same ~1.0 round-level noise**, so this is a repeated direction, not a
measured size.

And the sting: **the treatment that worked was the one that was cheating.** The
full plan contained numbers computed from all four traders' private data —
information no agent could legitimately have. Experiment 007's ladder
decomposed that block into three: what is against the rules (the cheat), what
is protocol (content-free coordination convention), and what is hint (domain
guidance with no private data). With the cheat removed, **every legitimate
treatment lands inside the noise.**

**(i) Welfare rises: the group makes more than the sum of its hermits.** `solid` as a level. Scoring the same runs by
`u_i / u_i^autarky` — is a trader better off in company than alone? — separates
cells that the efficiency framing had merged:

| cell | n | mean gain | median | geo(non-zero) | above-alone | ruined | total vs Σ autarky |
|---|---|---|---|---|---|---|---|
| plan, run 001 | 240 | 0.86 | 1.05 | 1.27 | 51% | 42% | 0.85 |
| bare, run 001 | 240 | 0.72 | 0.90 | 0.97 | 32% | 28% | 0.75 |
| plan, replicate A | 240 | 1.06 | 1.21 | 1.57 | 56% | 38% | 1.04 |
| plan, replicate B | 200 | 1.28 | 1.40 | 1.54 | 70% | 24% | 1.24 |
| plan, replicate C | 240 | 1.11 | 1.16 | 1.43 | 57% | 32% | 1.09 |
| equilibrium ceiling | — | — | — | — | — | — | 1.58–1.89 |

Three of four plan replicates make **more total utility than the same four
traders would alone** (1.04, 1.24, 1.09 against Σ autarky); the bare cell never
clears 1.0. Summing utilities is legitimate in this economy specifically:
Cobb-Douglas with Σα = 1 is homogeneous of degree 1, so utility is in
bundle-scale units and the same units for every trader. Paired on the one run
carrying both arms, the plan cell reaches super-autarkic welfare on **6 of 12
islands against 1 of 12** — but the mean difference is +0.104 against a spread
of 0.640, so the count is reportable and the size is not. Three plan seeds read
exactly 0.00: one missing good zeroes a trader under Cobb-Douglas, so welfare
is dominated by ruin and the ruin count must travel with it. The efficiency
measures never said any of this, because a group can be far from the Walrasian
frontier and still be well worth joining. Full argument, tables and caveats:
`reports/2026-08-24-a-second-benchmark.md`.

## 4. What cannot be claimed

Seven questions of the form *does it help, and by how much* have no answer:

- whether a content-free deliberation protocol improves coordination (005's
  founding question) — measured between −0.207 and +0.044;
- whether a domain hint improves coordination — −0.242 then +0.271;
- whether disclosing cost/worth ratios improves exchange;
- whether committing labour in pieces (tranching) improves the outcome — its
  own control failed to replicate, exchange completion 78% → 33% with no
  mechanical difference;
- whether protocol or hint, with the cheat removed, raises the share above
  autarky — null in both passes, and the protocol cell **reverses sign**
  between them;
- whether protocol or hint reduces ruin — directionally yes in both passes
  (pooled −0.108, −0.118, −0.161) but the control's own ruin rate moved 0.114,
  so only the both-blocks cell is arguably outside it;
- whether a more capable model uses instruction better — never run.

**The pattern is not an accident of any one design.** Questions of the form
*do they do it at all* are counts of an event that happened or did not — 214
against 0, 20 against 0, 68% against 0% — and no amount of run noise turns
those over. Questions of the form *does it help* are means of a heavy-tailed
ratio, and the noise swamps them. An instrument with a run-to-run movement of
1.03 on its natural outcome cannot produce the second kind.

## 5. The openings a paper could take

1. **The noise floor as the result.** Multi-agent LLM coordination benchmarks
   report treatment effects; this programme measured the same cell four times
   and found the effect size it could resolve is larger than most effects
   anyone reports. That is a methods paper with teeth, and it comes with the
   remedy: lopsided-count manipulation checks resolve; ratio means do not.
2. **Production collapses, exchange does not.** (b) plus (d): agents are
   near-optimal alone and degrade in company, and what degrades is what they
   *make*, not who they trade with. The failure is anticipatory
   mis-specialisation.
3. **Instruction, not capability.** (e) plus (f): granted-but-unmentioned
   affordances are invisible; specifying the channel and moment produces
   compliance where specifying the purpose does not.
4. **The cheat boundary.** (h): the only treatment that repeatedly worked
   required information no participant could have. What survives when you take
   it away is the real question, and the honest answer today is "not enough
   signal to say".
5. **Welfare as the benchmark.** (i): coordination benchmarks that score only against
   a frontier cannot distinguish a group worth joining from one that is not.

## 6. Where the material lives

- Economy and closed forms: `experiments/002-barter-conventions/experiment/barter/economy.py`
- The shared instrument (runner, manager, stimuli delivery):
  `experiments/005-deliberation-protocol/run_v3.py`, `island/manager.py`
- Ratio disclosure: `experiments/006-ratio-disclosure/`
- The plan, the ladder, the noise measurement: `experiments/007-execution-ceiling/`
  (`plan.py`, `stimuli/decomposed/`, `results/003-stability-*`)
- Per-hypothesis grading with evidence: `reports/2026-08-24-hypothesis-ledger.md`
- Narrative report: `reports/2026-08-23-instruction-and-the-cost-of-coordination.md`
- Utility-magnitude scoring: `experiments/007-execution-ceiling/analysis/utility_gain.py`

Two runs are on the roadmap and have no go: replicating the control
(`007-replicate-the-control`, 96 sessions) and a third pass on ruin
(`007-third-pass-on-ruin`, 192 sessions). Both exist because (h) rests on a
single control draw and (16) sits at the edge of resolvability.
