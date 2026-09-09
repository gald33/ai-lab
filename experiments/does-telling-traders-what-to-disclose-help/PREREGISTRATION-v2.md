# 006 — Pre-registration v2

**Frozen 2026-08-23, before run 002 ran.** v1 is not revised: it stands as the
frozen design of run 001 and stays in history. This document governs run 002
only.

## What run 001 established, and why v2 exists

Run 001 gave one cell a block saying what is worth disclosing. It did not say
where or when. The result, with denominators:

| cell | exchange | presence |
|---|---|---|
| `r-bare` | 0.82 | 0.83 |
| `r-placebo` | 0.79 | 0.85 |
| `r-ratios` | 0.57 | 0.73 |

Paired `r-ratios − r-placebo` on exchange: mean **−0.221**, 1 of 5 seeds
favouring; presence also fell in 4 of 5, so the difference is confounded and
was reported as such.

**But the manipulation barely happened.** Across five treated rounds and 200
trader-episodes there were **7 free-text messages**, of which 3 stated a ratio,
and **0 of 373** roster task strings did. The block said what was worth saying
and almost nothing was said. A treatment that is not enacted cannot be tested,
and v1's own rule calls that a manipulation failure rather than a null.

`r-placebo − r-bare` was **−0.021** (3 of 5 seeds favouring), so a paragraph's
mere presence is close to free. That is what makes it reasonable to compare
blocks of different lengths below.

## Question

Does telling traders **where and when** to disclose — a named key, written once
for cost and every episode for worth — make disclosure happen, and does
disclosure that happens improve exchange?

## Cells

| cell | instructions |
|---|---|
| `r-bare` | base, unchanged |
| `r-ratios` | base + `stimuli/ratios.md` — run 001's treatment, byte-identical |
| `r-ratios-board` | base + `stimuli/ratios-board.md` — the same content plus the protocol |

Frozen by body hash:

- `ratios.md` — `36cd95dc9bad3109823d172786366b5d5559468f20ed7a08192087ae96ad3116`, 240 words *(unchanged from v1)*
- `ratios-board.md` — `96d024f2a4d26e001881f0209690f50adfc93229c46e9d2fb9628bb3b68ccd3a`, 426 words

**`r-placebo` is dropped**, and its job is done by `r-ratios`: the contrast
that matters now is protocol-versus-no-protocol with content held constant, and
run 001 measured the cost of a bare paragraph at −0.021.

## The instrument change

`board_set`, `board_get` and `board_list` are granted **to every cell**. See
D2. Holding the grant constant is what makes the treatment the instruction and
not the tool: an untreated cell may discover the board and, on the evidence of
every run so far, will not.

## Units

5 seeds × 3 cells = **15 rounds**, paired on seed. 10 episodes × 180s, 4
traders. Seeds 1–5. The round is the unit.

## Primary endpoint

**Exchange**, as in v1: utility over the trader's own autarky optimum, for
trader-episodes in which it produced, averaged over the round. Reported as
paired `r-ratios-board − r-ratios` per seed, with `r-bare` printed alongside.

## Co-primary

**Presence**, as in v1, always reported beside exchange. A change in exchange
accompanied by a same-signed change in presence is reported as confounded.

## Manipulation check — the reason for this run

Read from the keyed store by `tools/board_dump.py`, not from prose:

1. **Cost keys written.** How many of the 4 traders per round wrote `cost/<name>`.
2. **Written once.** The revision count on each cost key. More than one revision
   means the "once" instruction was not followed.
3. **Worth keys updated.** Revisions on `worth/<name>`, against 10 episodes.
4. **Read as well as written.** Whether any board content is echoed in
   subsequent proposals.

**This is the run's real question.** If `r-ratios-board` does not exceed
`r-ratios` on (1) and (3), the protocol did not change behaviour and the
primary is uninterpretable — reported as a manipulation failure.

## Thresholds, fixed now

- **Disclosure happened** if in `r-ratios-board` at least **3 of 4 traders per
  round, in at least 4 of 5 rounds**, wrote a cost key, and worth keys carry a
  median of **≥ 5 revisions** over the round's 10 episodes.
- **The protocol works** if disclosure happened *and* paired
  `r-ratios-board − r-ratios` on exchange is **≥ +0.10** on at least 4 of 5
  seeds, with presence not falling more than 0.05.
- **The protocol is harmful** at ≤ −0.10 on the same counting rule.
- **Anything else is a null.**
- **The absolute test, reported regardless:** does any cell reach exchange
  above **1.0**? None has yet; `r-placebo` seed 2 came closest at 0.95.

## Stopping rule

If disclosure **happens** and exchange does not improve, this experiment stops
proposing things for agents to say. The traders would then have stated the
ratios, in a place designed for it, on time — and still not converted them into
better exchanges. The next question would be about the exchange mechanism
itself, not about what is disclosed over it.

## What is not claimed

Nothing about deliberation protocols in general. Nothing about other models,
islands, agent counts or episode lengths. The length asymmetry between the two
treated blocks (240 against 426 words) is a known impurity, bounded by run
001's `r-placebo − r-bare` of −0.021 and named in the run record's assumptions.
