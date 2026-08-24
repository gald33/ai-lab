# Welfare, not just efficiency

**Every score this lab has used is a ratio to a ceiling. None of them says how
much utility the island actually produced.** This proposes welfare — total
utility against the sum of solo optima — as the headline reading, justifies
summing utilities in this economy specifically, shows what it does to the runs
already on disk, and says exactly what it cannot support.

Written 2026-08-24. Script: `experiments/007-execution-ceiling/analysis/utility_gain.py`.

## 1. What the existing scores answer, and what they miss

| score | what it is | what it answers |
|---|---|---|
| `eff_round` | accumulated utility vector against `k ×` the one-episode Walrasian frontier | how close to the best possible |
| `eff_episode` | one episode's vector against the one-episode frontier | coverage — one agent at zero puts the vector maximally far from the frontier however well the others did |
| captured gain | `(u − u_autarky) / (u_plan − u_autarky)` | how far along the road from alone to optimal |
| share above own autarky | count of traders with `u_i > u_i^autarky` | did anyone beat working alone |

All four are ratios to a ceiling, and three of the four divide by a frontier.
That family answers **was this effective**. It cannot answer **how much utility
now exists**, and it reads two islands with the same efficiency as the same
result when one produced twice the output of the other.

The concrete failure: a solo agent reaches **0.972** of its closed-form
optimum — a near-perfect efficiency score, on a problem a quarter the size.
Four agents on a full island score far worse against their frontier while
producing, in the better cells, more total utility than the four of them would
alone. The efficiency family reads that as the worse outcome. It is a bigger
problem solved less tidily, and the benchmark must be able to say so.

## 2. Welfare, and why the sum is legitimate here

**Welfare** `W = Σ_i u_i / Σ_i u_i^autarky`, per episode. Did the island produce
more than the sum of its hermits?

Summing utilities across agents is normally indefensible — utility is ordinal,
each agent's is fixed only up to a monotone transform, and the sum is an
artefact of arbitrary units. **It is defensible in this economy for a specific
reason.** Cobb-Douglas with Σ_g α_ig = 1 makes `u_i(x) = Π_g x_g^{α_ig}`
**homogeneous of degree 1** in the bundle: double a trader's holdings and its
utility exactly doubles. Utility is therefore measured in bundle-scale units,
not arbitrary utils, and the same units for every trader. The lab already
relies on this homogeneity when it sets the round frontier at `k ×` the
one-episode frontier; welfare is the same fact used once more.

The denominator is `autarky` — the closed-form best a trader can do with nobody
to trade with — because it is exact, per-trader, and it is the actual
alternative to participating.

Two supporting readings from the same pass:

- **gain** `= u_i / u_i^autarky` per trader per episode. Above 1.0 means this
  trader is better off in company than alone. The individual-rationality
  reading: an island can be far from its frontier and still be worth joining.
- **geometric mean of gain over non-zero traders**, reported next to the
  arithmetic mean. A ruined trader (`u = 0`) sends the geometric mean to zero
  where the arithmetic mean merely dips, so the pair says whether a cell is
  lifted by everyone or by two winners carrying two corpses.

Plus two counts that must always be printed alongside: **above-alone** (share of
trader-episodes with gain > 1) and **ruined** (share at exactly zero).

None of this replaces efficiency. `eff_round` stays primary for *how close to
optimal*; welfare says *how much was made*. Reporting either alone reports half
the outcome.

## 3. Welfare rises, and that is a level claim

```
run                    cell          n    mean  median  geo(live)  above-alone  ruined  WELFARE
001-ceiling            e-bare      240    0.72    0.90       0.97          32%     28%     0.75
001-ceiling            e-plan      240    0.86    1.05       1.27          51%     42%     0.85
001b-pilot45           e-bare       24    0.60    0.76       0.93          17%     38%     0.62
001b-pilot45           e-plan       24    1.50    1.46       1.50          92%      4%     1.44
002-tranche            t-plan      240    0.48    0.00       0.99          23%     54%     0.48
002-tranche            t-tranche   240    0.65    0.78       0.92          28%     32%     0.65
003-stability-a        e-plan      240    1.06    1.21       1.57          56%     38%     1.04
003-stability-b        e-plan      200    1.28    1.40       1.54          70%     24%     1.24
003-stability-c        e-plan        0     —       —          —             —       —        —   (12/12 rounds lost to a hub outage)
003-stability-c2       e-plan      240    1.11    1.16       1.43          57%     32%     1.09
004-ladder-a           l-bare      240    0.64    0.82       0.91          31%     33%     0.66
004-ladder-a           l-protocol  240    0.75    0.85       0.90          34%     21%     0.73
004-ladder-a           l-hint      240    0.83    0.94       0.97          42%     17%     0.82
004-ladder-a           l-both      240    0.83    0.95       0.99          40%     18%     0.81
005-ladder-b           l-bare      240    0.74    0.94       0.99          34%     28%     0.77
005-ladder-b           l-protocol  240    0.75    0.92       0.89          25%     20%     0.80
005-ladder-b           l-hint      240    0.79    0.93       0.98          35%     22%     0.81
005-ladder-b           l-both      240    0.78    0.96       0.97          38%     22%     0.74
```

Denominators are trader-episodes. No round is dropped: run 003's replicate C
lost all 12 rounds to a hub outage and is shown as a zero row. Equilibrium
ceiling on the same reading, for scale: welfare **1.58–1.89**.

**The headline: three of four plan replicates make more utility than the same
four traders would alone** — welfare 1.04, 1.24, 1.09. The bare cell never
clears 1.0 in any run it appears in. That is a *level* against a closed form,
and levels are exactly the class of claim this instrument supports (§5). It is
the true task result, and no efficiency score can express it: efficiency stays
mediocre in those very cells, because "how close to the best possible" and "how
much got made" are different questions and only the second is what the group
was for.

**The two means disagree, and the disagreement is a finding.** Plan run 001:
arithmetic 0.86, geometric-over-survivors 1.27, ruined 42%. That cell is not
mediocre for everyone — it is good for the survivors and fatal for the rest.
The bare cell has *less* ruin (28%) and a worse result for those who live
(0.97). Handing over the plan raises the ceiling and the casualty count at
once. `eff_episode`, dominated by construction by the worst agent, showed only
the casualties.

## 4. Paired on the island: what welfare does and does not prove

Run 001 is the only run carrying both arms on the same seeds, and a seed *is* an
island, so pairing on it removes the draw from the comparison:

```
seed      e-bare      e-plan     diff
   1        0.35        1.53    +1.18
   2        0.61        0.63    +0.03
   3        0.54        0.00    −0.54
   4        0.98        1.41    +0.43
   5        0.56        0.53    −0.03
   6        1.07        1.43    +0.36
   7        0.66        1.06    +0.39
   8        0.94        0.00    −0.94
   9        0.92        0.00    −0.92
  10        0.75        1.43    +0.67
  11        0.76        0.83    +0.07
  12        0.85        1.39    +0.54

seeds 12    e-bare above 1.0 on 1/12    e-plan above 1.0 on 6/12
            e-plan − e-bare: mean +0.104  sd 0.640  wins 8/12
```

Reproduce with `python analysis/utility_gain.py --paired results/001-ceiling/v3.json`.

Two different claims live in that table and only one of them holds.

- **The difference does not.** +0.104 against a spread of 0.640 is noise, the
  same noise that retired every other treatment effect in the programme
  (`reports/2026-08-24-hypothesis-ledger.md`). *Do not report "the plan raises
  welfare by 0.10."*
- **The count does.** The plan cell reaches super-autarkic welfare on **6 of 12**
  islands and the bare cell on **1 of 12**. That is the lopsided-count form of
  evidence — the same form as 214-against-0 and 20-against-0 — and run noise
  does not turn it over. *This* is the reportable comparative statement.

**The caveat that must travel with welfare.** Three plan seeds read exactly
**0.00** — every trader at zero. Under Cobb-Douglas one missing good zeroes a
trader, so a sum of utilities is dominated by ruin far more than the median
trader is. Seeds 8 and 9 went from 0.94 and 0.92 under bare to 0.00 under plan.
That is not a small loss; it is the whole island, and it is what drags the
paired mean to +0.10 while 8 of 12 seeds improved. Welfare as a headline needs
the ruin count printed beside it, for the same reason the geometric mean does.

## 5. Why welfare escapes the noise where the old scores did not

It does not escape it — it sidesteps it by changing the *form* of the claim.
The same plan cell reads welfare 0.85, 1.04, 1.24 and 1.09 across four
replicates differing in nothing, so any welfare *difference* under ~0.6 is
unresolvable, exactly as before. A new endpoint on the same instrument inherits
its noise floor.

What changes is that welfare has a **meaningful absolute zero point at 1.0** —
the sum of hermits — which captured gain and `eff_round` do not. "Three of four
replicates exceeded 1.0" and "6 of 12 islands against 1 of 12" are a level and
a count. Those survive. The programme's recurring split holds here too: this
reading changes a great deal about what can be *described*, and nothing about
what can be *compared* by size.

## 6. What to change

1. Report **welfare** as the headline outcome of every run, with **ruined**
   immediately beside it, and `gain` mean / median / geometric-over-live /
   above-alone underneath. Backfilled above; `utility_gain.py` reads existing
   `v3.json` records, so nothing needs re-running.
2. Keep `eff_round` as the primary for closeness-to-optimal. This is an
   addition, not a replacement.
3. State claims about welfare as **levels against 1.0 and counts of islands
   clearing it**, never as differences in mean welfare, until the instrument's
   movement is brought under the effect being claimed.
4. Pre-register both families for any future run, with the noise floor named
   next to each threshold. A threshold below the measured run-to-run spread is
   not a threshold.
