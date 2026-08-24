# A second benchmark: how much utility, not just how efficient

**Every score this lab has used is a ratio to a ceiling. None of them says
whether the island was worth living on.** This proposes the missing reading,
shows what it does to the runs already on disk, and says what it does not fix.

Written 2026-08-24. Script: `experiments/007-execution-ceiling/analysis/utility_gain.py`.

## What the current scores answer

| score | what it is | what it answers |
|---|---|---|
| `eff_round` | accumulated utility vector against `k ×` the one-episode Walrasian frontier | how close to the best possible |
| `eff_episode` | one episode's vector against the one-episode frontier | coverage — one agent at zero puts the vector maximally far from the frontier however well the others did |
| captured gain | `(u − u_autarky) / (u_plan − u_autarky)` | how far along the road from alone to optimal |
| share above own autarky | count of traders with `u_i > u_i^autarky` | did anyone beat working alone |

All four are ratios to a ceiling, and three of the four divide by a frontier.
That family answers **was this effective**. It cannot answer **how much utility
now exists**, and it cannot distinguish two islands with the same efficiency
where one produced twice the utility of the other.

The concrete failure: a solo agent hits **0.972** of its closed-form optimum,
which is a near-perfect efficiency score — on a problem that is a quarter the
size. Four agents on a full island score far worse against their frontier while
producing, in the better cells, *more total utility than the four of them would
alone*. The efficiency family reads that as a worse outcome. It is a bigger
problem solved less tidily, and the benchmark should be able to say so.

## The proposal

Two readings, both against `autarky` — the closed-form best a trader can do
with nobody to trade with. It is the right denominator because it is the
alternative to participating, it is exact, and it is per-trader.

- **gain** `= u_i / u_i^autarky`, per trader per episode. Above 1.0 means this
  trader is better off in company than alone. This is the
  individual-rationality reading: an island can be far from its frontier and
  still be worth joining, and no efficiency measure can see that.
- **total** `= Σ_i u_i / Σ_i u_i^autarky`, per episode. Whether the island
  produced more than the sum of its hermits. Cross-agent utility sums are not
  generally meaningful, but the *ratio to the same-units sum of solo optima* is
  the honest version of "did coordination create value", and it is the one that
  can be high while efficiency is low.

Report alongside them, from the same pass:

- **geometric mean over non-zero traders** — a ruined trader sends it to zero
  where the arithmetic mean merely dips, so the two together say whether a cell
  is lifted by everyone or by two winners carrying two corpses;
- **above-alone**, the share of trader-episodes with gain > 1;
- **ruined**, the share at exactly zero.

Neither reading replaces efficiency. `eff_round` stays primary for *how close to
optimal*; these say *how much, and for whom*. A paper reporting one without the
other is reporting half the outcome.

## What it says about the runs already on disk

```
run                    cell          n    mean  median  geo(live)  above-alone  ruined  total
001-ceiling            e-bare      240    0.72    0.90       0.97          32%     28%   0.75
001-ceiling            e-plan      240    0.86    1.05       1.27          51%     42%   0.85
001b-pilot45           e-bare       24    0.60    0.76       0.93          17%     38%   0.62
001b-pilot45           e-plan       24    1.50    1.46       1.50          92%      4%   1.44
002-tranche            t-plan      240    0.48    0.00       0.99          23%     54%   0.48
002-tranche            t-tranche   240    0.65    0.78       0.92          28%     32%   0.65
003-stability-a        e-plan      240    1.06    1.21       1.57          56%     38%   1.04
003-stability-b        e-plan      200    1.28    1.40       1.54          70%     24%   1.24
003-stability-c        e-plan        0     —       —          —             —       —      —   (12/12 rounds lost to a hub outage)
003-stability-c2       e-plan      240    1.11    1.16       1.43          57%     32%   1.09
004-ladder-a           l-bare      240    0.64    0.82       0.91          31%     33%   0.66
004-ladder-a           l-protocol  240    0.75    0.85       0.90          34%     21%   0.73
004-ladder-a           l-hint      240    0.83    0.94       0.97          42%     17%   0.82
004-ladder-a           l-both      240    0.83    0.95       0.99          40%     18%   0.81
005-ladder-b           l-bare      240    0.74    0.94       0.99          34%     28%   0.77
005-ladder-b           l-protocol  240    0.75    0.92       0.89          25%     20%   0.80
005-ladder-b           l-hint      240    0.79    0.93       0.98          35%     22%   0.81
005-ladder-b           l-both      240    0.78    0.96       0.97          38%     22%   0.74
```

Denominators are trader-episodes. No round is dropped: run 003's replicate C
lost all 12 rounds to a hub outage and is shown as a zero row, not omitted.
Equilibrium ceiling on the same reading, for scale: total **1.58–1.89**.

Three things fall out that the efficiency family did not show.

**1. The plan cell clears 1.0, and that is a different claim than "it is more
efficient".** Replicates A, B and C2 produce totals of 1.04, 1.24 and 1.09 —
these four agents, coordinating badly, still made **more utility than the four
of them working alone**. The median trader is above 1.0 in all four plan cells.
The bare cell is below 1.0 on the mean, the median *and* the total in every run
it appears in. "Is this island worth joining" has a cleaner answer than "is this
island efficient" ever did.

**2. The arithmetic and geometric means disagree, and the disagreement is the
finding.** Plan run 001: mean 0.86 but geometric-mean-over-live 1.27, with 42%
ruined. That cell is not mediocre for everyone — it is *good for the survivors
and fatal for the rest*. The bare cell has **less** ruin (28%) and a worse
result for those who live (0.97). Handing over the plan raises the ceiling and
the casualty count at the same time. No single-number score can carry that, and
`eff_episode` — which by construction is dominated by the worst agent — hid it
by reporting only the casualties.

**3. It does not escape the noise.** The same plan cell reads 0.85, 1.04, 1.24
and 1.09 across four replicates that differ in nothing. That spread is the
instrument's own movement, the same one that retired most treatment effects
(`reports/2026-08-24-hypothesis-ledger.md`). A new endpoint measured on the
same instrument inherits its noise floor. The bare-versus-plan gap here (0.75
vs 0.85 on total, in the one run holding both) is **inside** that spread and
must not be reported as an effect.

So: the new reading changes what we can *describe* — levels, who gained, the
survivor/casualty structure — and changes nothing about what we can *compare*.
That is exactly the split the whole programme keeps producing.

## What to change

1. Score `gain`, `total`, `geo(live)`, `above-alone` and `ruined` on every run,
   alongside `eff_round` and `eff_episode`. Backfilled above for runs already
   on disk; `utility_gain.py` reads the existing `v3.json` records, so nothing
   needs re-running.
2. Pre-register both families for any future run, with the noise floor named
   next to each threshold. A threshold below 0.15 on a ratio mean is not a
   threshold.
3. Report the arithmetic mean and the geometric-over-live mean together,
   always. Reporting either alone misdescribes the cells above.
4. Keep `eff_round` as the primary for closeness-to-optimal. This is an
   addition, not a replacement.
