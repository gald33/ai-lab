"""The world the four cells are run in, and the two things a cell can add.

The market is the pilot's accepted configuration — eight agents, four goods,
private log-normal signals with ``sigma = 0.15``, each agent seeing two others
per round — with the agents replaced by models. Everything a world needs is
derived from its seed, so the same seed produces the same truth, the same
private signals, the same observation draw and the same hint in **all four
cells**. That is what makes the comparison paired.

Nothing here enforces a price. The harness fixes when a round opens, what a
well-formed submission looks like, and how it is scored. What an agent submits
is its own.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

#: The accepted pilot configuration. Not free parameters — see PREREGISTRATION.
N_AGENTS = 8
N_GOODS = 4
SIGMA = 0.15
WIDTH = 2

#: Noise on the common hint. Tighter than a private signal, so the hint is
#: genuinely worth having, and non-zero so a population that copies it agrees
#: on something slightly wrong and pays for it in regret.
HINT_SIGMA = 0.10

GOODS = ("bread", "cloth", "iron", "salt")


def normalise(price: list[float]) -> list[float]:
    """Pin the numeraire at 1, exactly as the pilot and 002 both do."""
    if price[0] <= 0:
        raise ValueError("numeraire must be positive")
    return [p / price[0] for p in price]


def dispersion(positions: list[list[float]]) -> float:
    """Max pairwise distance between submitted positions, relative to the mean.

    Identical to ``pilot.world.dispersion``. The maximum rather than the mean:
    one agent acting on a different claim is the failure a deliberation
    protocol exists to prevent, and a mean lets exactly that agent average out.
    """
    if len(positions) < 2:
        raise ValueError("dispersion needs at least two positions")
    k = len(positions[0])
    bar = [sum(p[g] for p in positions) / len(positions) for g in range(k)]
    scale = math.sqrt(sum(x * x for x in bar))
    if scale <= 0:
        raise ValueError("mean position has zero norm")
    worst = 0.0
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            d = math.sqrt(sum((positions[i][g] - positions[j][g]) ** 2
                              for g in range(k)))
            worst = max(worst, d / scale)
    return worst


def distance(a: list[float], b: list[float]) -> float:
    """Relative distance from ``a`` to ``b``, both normalised."""
    num = math.sqrt(sum((a[g] - b[g]) ** 2 for g in range(len(a))))
    den = math.sqrt(sum(x * x for x in b))
    return num / den


@dataclass(frozen=True)
class World:
    """One draw. Derived entirely from the seed, shared by all four cells."""

    seed: int
    truth: list[float]
    signals: list[list[float]]
    hint: list[float]
    #: ``seen[r][i]`` — the agent indices agent ``i`` observes in round ``r``.
    seen: list[list[list[int]]]

    def to_json(self) -> dict:
        return {"seed": self.seed, "truth": self.truth,
                "signals": self.signals, "hint": self.hint}


def draw_world(seed: int, rounds: int) -> World:
    """Everything a world is, fixed before any model is called.

    The observation schedule is drawn here rather than inside the round loop on
    purpose: if it were drawn as the episode ran, a cell whose agents happened
    to retry more often would consume the stream differently and the four cells
    would stop being paired.
    """
    rng = random.Random(seed * 104729 + 17)
    truth = normalise([1.0] + [math.exp(rng.gauss(0.0, 0.6))
                               for _ in range(N_GOODS - 1)])
    signals = [normalise([math.exp(math.log(truth[g]) + rng.gauss(0.0, SIGMA))
                          for g in range(N_GOODS)])
               for _ in range(N_AGENTS)]
    hint = normalise([math.exp(math.log(truth[g]) + rng.gauss(0.0, HINT_SIGMA))
                      for g in range(N_GOODS)])
    seen = []
    for _ in range(rounds + 1):
        per_round = []
        for i in range(N_AGENTS):
            others = [j for j in range(N_AGENTS) if j != i]
            per_round.append(sorted(rng.sample(others, WIDTH)))
        seen.append(per_round)
    return World(seed=seed, truth=truth, signals=signals, hint=hint, seen=seen)
