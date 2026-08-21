# 005 v2 — pre-registration

Frozen in the same commit as the stimuli, before any pilot or paid cell runs.
Nothing here may be revised after the pilot; a revision is a new document with a
new commit and this one stays in history.

## Frozen stimuli

`tools/check_v2.py` recomputes these and fails if any file has moved. Body
hashes exclude the repo-facing title and italic note, which are not sent to
agents.

| file | body sha256 | words |
|---|---|---|
| `stimuli/v2/base.md` | `c6daef3b7fcdd54c7228377d04864af65642cb51af45c191834fdd19cd185b0f` | 866 |
| `stimuli/v2/protocol.md` | `377ff6f82295098daf1a5b4b407de80d0040ed1e9fce5eb4736356e89bc5bf99` | 355 |
| `stimuli/v2/hint.md` | `a56382aa74077c57df6c5d11c2b0f5a741819c36df75c539058fad320f10afec` | 225 |

## Frozen assembled cells

| cell | protocol | hint | words | sha256 (first 16) |
|---|---|---|---|---|
| `baseline` | no | no | 866 | `c6daef3b7fcdd54c` |
| `protocol` | **yes** | no | 1221 | `fd2c97fdf48925ce` |
| `hint` | no | **yes** | 1091 | `9d17d9e48703056a` |
| `both` | **yes** | **yes** | 1446 | `7eec9478511e9fe4` |

## Frozen primary metric

`W` = mean over a world's periods of the **lower bound** of
`economy.efficiency` on the realised holdings at that period's bell. Continuous
in `[0, 1]`; no threshold. Higher is better.

Paired by seed; the **world** is the unit of analysis. Two main effects and one
interaction, each an exact binomial sign test on paired per-world differences,
ties reported. Autarky floor and exchange ceiling printed with every cell.

## Frozen pilot acceptance

All four must hold. Criteria, and the full sweep table with every configuration
scored against every criterion, are reported whether or not any configuration
passes.

| # | test |
|---|---|
| P1 | median `W` ≤ 0.85 × exchange ceiling |
| P2 | `W` ≥ 1.05 × autarky floor in ≥ 40% of worlds |
| P3 | ≥ 15% of agent-periods are zero-utility |
| P4 | IQR of `W` ≥ 0.10 across ≥ 12 scored worlds |

If baseline saturates, difficulty rises; agents are never weakened.

## Frozen predictions

1. **Hint main effect > protocol main effect** on `W`. The coupling is the
   binding constraint; conversational form is second-order when there is
   something specific to say.
2. **Protocol main effect > 0 but small**, and mostly via fewer zero-utility
   periods rather than higher `W` among worlds that already cover all goods.
3. **Interaction positive**: the protocol is worth more when agents have
   something structural to coordinate about (`both` − `hint` > `protocol` −
   `baseline`).
4. The most likely single failure is the pilot: unguided agents on an open
   public board may solve coverage in period 1, and P1 or P3 then fails.

## Declared in advance

- **No placebo cell.** `protocol` differs from `baseline` by the advice and by
  the existence of advice. A positive protocol effect will not separate the two.
  Recommended and not adopted; recorded here so it cannot be discovered later.
- **Treatments are not length-matched to each other** (355 vs 225 words).
- **Adoption is not measured.** No transcript scoring, no compliance judging.
  The mechanism is reported as unmeasured.
