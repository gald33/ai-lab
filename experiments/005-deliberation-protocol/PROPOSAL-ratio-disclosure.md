# Proposal — disclosure of ratios, not levels

**Status: a proposal. Not part of experiment 005 and not to be run under it.**
Run 006 fixed a stopping rule for this experiment: *no further run in 005 adds
instruction text to see whether it helps.* What follows adds instruction text.
It therefore belongs to a **new experiment**, with 005's null as its baseline,
and is written down here only because that is where the idea arose.

## The idea

Have each trader post, in its own words, the ratios that describe it: how
costly one good is for it in terms of another, and how much it wants one good
in terms of another. Not stocks, not levels, not "I need salt" — ratios.

## Why it has economic sense

In Cobb-Douglas with a labour budget of 1, two ratios describe what an agent
brings to a trade:

- **the cost ratio** (MRT) `capacity_h / capacity_g` — what making one more
  unit of `g` costs in units of `h`;
- **the payoff ratio** (MRS) `(α_g/x_g) / (α_h/x_h)` — what the agent will pay
  for `g` in units of `h` at its current holdings.

**At the solo optimum these are the same number.** The optimum is `s_g = α_g`,
so `x_g = capacity_g · α_g`, so marginal utility is `α_g/x_g = 1/capacity_g`
and the tastes cancel: MRS = MRT, the tangency condition. Checked on seed 1,
they agree to every digit printed — T1 `[1.000, 0.407, 0.945, 1.317]` on both.

So an agent at its own optimum has **one** ratio to post, not two, and the two
come apart only in a specific and useful way:

- **The cost ratio is fixed for the entire round.** It is built from
  capacities, which never change. It is worth saying once and relying on for
  ten episodes — the one fact whose constancy actually pays to broadcast.
- **The payoff ratio moves the moment holdings leave own-production** — after
  any trade, or after a production choice that was not optimal. It is the live
  signal: what the *next* trade is worth to me. An agent posting both as equal
  is thereby saying it has not traded yet.

A disclosure block should therefore ask for the **cost ratio once per round**
and the **payoff ratio per offer**. Asking for both, every time, asks for the
same number twice.

All gains from trade in this island live in the **gap between one agent's cost
ratio and another's**. That is comparative advantage stated exactly, and it is
what a price is for. Two properties make ratios the right thing to put on a
board rather than levels:

- **Scale-free.** A ratio needs no numéraire, no shared unit, and no agreement
  on what "a lot" means. Two agents can compare cost ratios without either
  knowing the other's capacities.
- **Compressed and sufficient.** With four goods, three cost ratios and three
  taste ratios carry what eight raw private numbers carry, for the purpose of
  deciding who should make what.

**The islands do have the variation this would exploit.** Cost ratios against
bread, seed 1: T1 `[1.00, 2.46, 1.06, 0.76]`, T2 `[1.00, 0.95, 0.30, 1.53]`,
T3 `[1.00, 0.44, 0.77, 0.28]`, T4 `[1.00, 3.39, 2.53, 4.23]`. T2 makes iron at
0.30 bread; T4 pays 2.53. That is an eightfold difference in opportunity cost
on one good, and no message on any board in runs 005 or 006 ever said so.

## A diagnostic that falls out of this

MRS equals MRT exactly when an agent has produced its own optimum, so the gap
between them at production time says **which way** an agent misallocated, not
merely that it did. That is a refinement of run 007's solo capture — capture
says how much utility was lost, the gap says which good was over- or
under-made — and it costs nothing extra to compute, since both sides are
recoverable from the manager's own settlement notes plus private state the
manager already holds. It is added to run 007's analysis as a secondary read.

## The correction to the original form

The idea as first put was *production rate over need rate*. That pairing does
not mean anything: it divides across two different denominators, so an agent
good at salt **and** hungry for salt returns a middling number that cannot be
told from one bad at salt and indifferent to it. The informative ratios are
**within a category, across goods** — cost of `g` in `h`, and want for `g` in
`h` — never production over need for the same good.

## What an experiment would have to do

| | |
|---|---|
| **cells** | `bare` (base text) and `ratios` (base plus the disclosure block). Paired seeds. |
| **the block** | Says what a ratio is and that posting one is useful. It must **not** give a format, a schema or an example message — that is the protocol arm's job and mixing them is what made the 005 screen unreadable. |
| **primary** | Paired `eff_round − floor`, as in 005/006. |
| **manipulation check** | Share of board messages carrying a ratio; whether any trader posts a ratio the manager did not ask for. Both read from the board, not from self-report. |
| **the interesting secondary** | Whether an agent's settled exchanges move toward the goods its own cost ratios favour — specialisation, measured against the private state the manager already holds. |
| **a falsifiable check on the block** | If the block works as reasoned, a treated agent posts its cost ratio early and rarely again, and its payoff ratios change after each settled exchange. A treated agent that re-posts an unchanged payoff ratio after trading has not understood it. |

**It is a domain hint, squarely.** It tells agents what to say about the
economy. It is not a protocol and must never be described as one.

## Why it is not worth running yet

Run 007 is measuring whether an agent alone reaches the autarky optimum. If
solo capture comes back low, these agents are not solving the one-agent
allocation problem, and telling them to post ratios cannot help someone who
cannot act on their own optimum — the hint would be testing a competence that
is not the binding constraint. If capture comes back near 1, the deficit really
is in the trading, and ratio disclosure is aimed exactly at it.

**Decide after run 007 reports, not before.**
