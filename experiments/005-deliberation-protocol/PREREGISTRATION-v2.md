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
| `stimuli/v2/base.md` | `23b4f5d5eec7624c1ecf17e5b6a534e37aa1058cf754dbc0f5944a5e434affce` | 911 |
| `stimuli/v2/protocol.md` | `377ff6f82295098daf1a5b4b407de80d0040ed1e9fce5eb4736356e89bc5bf99` | 355 |
| `stimuli/v2/placebo.md` | `72a9211f69061fd50bb622d7f674e52f1f4fdee2e5a91034c3553277f0639a5c` | 365 |
| `stimuli/v2/hint.md` | `a56382aa74077c57df6c5d11c2b0f5a741819c36df75c539058fad320f10afec` | 225 |

## Frozen assembled cells

Five cells. Hashes are recomputed and pinned by `tools/check_v2.py`, which
fails the suite if any assembled cell moves.

| cell | stimulus | hint | words | sha256 (first 16) |
|---|---|---|---|---|
| `bare` | none | no | 911 | `23b4f5d5eec7624c` |
| `placebo` | placebo | no | 1276 | `7de97b2991f95507` |
| `protocol` | protocol | no | 1266 | `c8430038af54e962` |
| `hint` | none | **yes** | 1136 | `b04f3305abcddb3d` |
| `both` | protocol | **yes** | 1491 | `d879c962269bf3b1` |

**Primary protocol contrast: `protocol` − `placebo`.** `protocol` − `bare` is
secondary, and the gap between the two contrasts estimates document-presence.

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

The autarky floor is an `economy.efficiency` lower bound, the same scale as `W`
itself, so no criterion crosses units. The exchange ceiling is **1.0 by the
first welfare theorem**, asserted in the probe rather than estimated, so P1
reduces to `median W ≤ 0.85`.
| P3 | ≥ 15% of agent-periods are zero-utility |
| P4 | IQR of `W` ≥ 0.10 across ≥ 12 scored worlds |

If baseline saturates, difficulty rises; agents are never weakened.

## Frozen population size

`N = 8` traders, 4 goods. Chosen from `analysis/world_probe.py` before any run,
on the efficiency scale: the gap from the autarky floor to the frontier is 0.508
at `N = 8` and flat to `N = 12`, against 0.239 at `N = 2`; `N = 8` also has the
tightest efficiency bracket measured (0.0022 against 0.0251 at `N = 2`) and the
narrowest island-to-island gap range below `N = 12`. `N` is a parameter and the
pilot may move it; any move is recorded as a deviation.

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

- **The placebo is not crossed with the hint.** There is no `placebo + hint`
  cell, so the interaction term is estimated against `bare`, not against the
  matched control.
- **The placebo is not perfectly inert.** It passes the domain-leak check and is
  length-matched, but general advice about deciding under uncertainty is not
  nothing on this task. `protocol` − `placebo` should be read as a floor on the
  protocol effect.
- **Treatments are not length-matched to each other** (355 vs 225 words).
- **Adoption is not measured.** No transcript scoring, no compliance judging.
  The mechanism is reported as unmeasured.
