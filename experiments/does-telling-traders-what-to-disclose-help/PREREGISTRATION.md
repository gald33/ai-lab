# 006 — Pre-registration

**Frozen 2026-08-22, before any cell of this experiment ran.** A
pre-registration is never revised in place: a revision is a new document at a
new version and this one stays in history.

## Question

Does a block telling traders **what** to disclose — cost ratios and worth
ratios — improve coordination on a Cobb-Douglas barter island, against a
length- and register-matched placebo?

## Cells

| cell | instructions |
|---|---|
| `r-bare` | `stimuli/v3/base.md` from the instrument, unchanged |
| `r-placebo` | base + `stimuli/placebo.md` |
| `r-ratios` | base + `stimuli/ratios.md` |

**Frozen by body hash** (title and note excluded, since they are not sent):

- `ratios.md` — `36cd95dc9bad3109823d172786366b5d5559468f20ed7a08192087ae96ad3116`, 240 words
- `placebo.md` — `817fcc8d38ff1c1df6c7be5b28fe59379647b6f4911a10722a333ed713d421c4`, 230 words

Assembled prompts: `r-bare` 1096 words, `r-placebo` 1327, `r-ratios` 1336 —
the two treated cells within 0.7% of each other.

## Units

5 seeds × 3 cells = **15 rounds**, paired on seed. 10 episodes × 180s, 4
traders. Seeds 1–5, the islands 005's runs 005–007 used. **The round is the
unit of analysis.**

## Primary endpoint

**Exchange**: for each trader-episode in which the trader produced, its utility
divided by that trader's own autarky optimum; averaged over the round.

Reported as the paired difference `r-ratios − r-placebo` per seed, with
`r-bare` printed alongside. Denominator = 5 seeds per cell; no round dropped, a
failed round reported as failed.

**Why not `eff_round`.** `eff_round` mixes the two mechanisms below into one
number, and 005 twice attributed to a treatment what was in fact a change in
attrition. `eff_round` is still computed and reported; it is not the primary.

## Co-primary endpoint

**Presence**: the share of trader-episodes with any settled production.
Reported per cell, always beside exchange. A change in exchange accompanied by
a change in presence of the same sign is **not** read as an exchange effect —
the two are confounded and the run says so.

## Thresholds, fixed now

- **The treatment works** if paired `r-ratios − r-placebo` on exchange is
  **≥ +0.10** with at least **4 of 5 seeds** in that direction, *and* presence
  does not fall by more than 0.05 relative to `r-placebo`.
- **The treatment is harmful** if the paired difference is ≤ −0.10 on the same
  counting rule. Given 005's two negative runs this is a live outcome, not a
  formality.
- **Anything else is a null**, including a difference of the right size carried
  by fewer than 4 seeds.
- **The absolute test, reported regardless:** does any cell get exchange above
  **1.0**? Below 1 the traders would have done better alone, whatever the
  cells' differences. No cell has yet managed it.

## Manipulation check

Share of board messages carrying a stated ratio, per cell, read from the board.
If `r-ratios` does not exceed `r-placebo` and `r-bare` on this, the block did
not reach behaviour and the primary is uninterpretable — **reported as a
manipulation failure, not as a null.**

## Stopping rule

If `r-ratios` is null or harmful on the primary **and** the manipulation check
passed — the traders said the ratios and it did not help — this experiment
stops proposing content for agents to disclose. The next question would be
about the exchange mechanism, not about what is said over it.

## What is not claimed

Nothing about deliberation protocols: this is a domain hint. Nothing about
other models, island shapes, agent counts or episode lengths. Nothing about why
sessions stop, which remains unexplained and is measured here rather than
solved.
