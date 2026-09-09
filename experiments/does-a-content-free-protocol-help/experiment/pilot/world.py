"""The pilot world: a market with a computable answer that nobody is told.

This is *not* the 005 experiment. It is the gate in front of it. The question
it answers is narrow and mechanical: **is there a market configuration where an
unguided population agrees sometimes, but neither immediately nor never?** If
there is not, no manipulation applied on top of it could be detected, and 005
stops here.

The agents are scripted, and that is a deliberate limitation rather than a
stand-in for the real thing. 002's Tier 3 established that scripted traders
have no beliefs about other agents, so they cannot be given a deliberation
protocol at all — the four cells of 005 would be byte-identical. What a script
*can* do is establish that the market has headroom: that the answer is neither
trivially agreed nor unreachable. That is all this file claims.

The model
---------
Each agent holds a private noisy signal about the island's true equilibrium
price. Each round it sees the positions **submitted by a subset of the others**
— never a broadcast, never an announced vector, never a harness-computed
average — and moves its own position part of the way toward what it saw, while
staying anchored to its own signal.

Three knobs, and they are the whole sweep:

``sigma``    how noisy the private signals are. At zero everybody starts on the
             answer and agreement is instant; large enough and the anchor
             pins each agent to its own noise forever.
``width``    how many other agents each one observes per round. At ``n - 1``
             this is a broadcast and converges fast; at 1 information moves
             through the population slowly and may not close.
``anchor``   how much weight an agent keeps on its own signal. This is the
             stubbornness term, and it is what makes non-convergence possible
             at all — pure averaging always converges.

Nothing here enforces a price. The harness fixes when a round opens and closes
and what a well-formed submission looks like, and scores. It never tells an
agent what to submit, and an agent's submission is the only thing that enters a
metric.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


def normalise(price: list[float]) -> list[float]:
    """Pin the numeraire at 1, exactly as ``barter.calibrate.normalise`` does.

    Every distance in this experiment is computed on normalised vectors, so a
    population that agrees on relative prices but not on scale counts as
    agreeing — which is the economically meaningful reading.
    """
    if price[0] <= 0:
        raise ValueError("numeraire must be positive")
    return [p / price[0] for p in price]


def dispersion(positions: list[list[float]]) -> float:
    """Max pairwise distance between submitted positions, relative to the mean.

    The *maximum*, not the mean: one agent acting on a different claim is the
    failure a deliberation protocol exists to prevent, and a mean pairwise
    distance lets exactly that agent average away.
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


@dataclass(frozen=True)
class Config:
    """One point on the sweep grid. Frozen so a record cannot be re-labelled."""

    n_agents: int
    n_goods: int
    sigma: float
    width: int
    anchor: float
    rounds: int

    @property
    def key(self) -> str:
        return (f"n{self.n_agents}-k{self.n_goods}-s{self.sigma:g}"
                f"-w{self.width}-a{self.anchor:g}-r{self.rounds}")

    def to_json(self) -> dict:
        return {"n_agents": self.n_agents, "n_goods": self.n_goods,
                "sigma": self.sigma, "width": self.width,
                "anchor": self.anchor, "rounds": self.rounds, "key": self.key}


@dataclass
class Agent:
    """An unguided participant. It has a signal and it can see some others."""

    index: int
    signal: list[float]
    position: list[float]

    def submit(self) -> list[float]:
        """The only thing that enters a metric. Never a self-report."""
        return normalise(self.position)

    def update(self, seen: list[list[float]], anchor: float) -> None:
        if not seen:
            return
        k = len(self.position)
        heard = [sum(p[g] for p in seen) / len(seen) for g in range(k)]
        self.position = [anchor * self.signal[g] + (1.0 - anchor) * heard[g]
                         for g in range(k)]


def draw_truth(cfg: Config, rng: random.Random) -> list[float]:
    """The market's answer. Computable, and told to nobody."""
    price = [1.0] + [math.exp(rng.gauss(0.0, 0.6)) for _ in range(cfg.n_goods - 1)]
    return normalise(price)


def draw_agents(cfg: Config, truth: list[float], rng: random.Random) -> list[Agent]:
    """Private signals: the truth in log space plus independent noise.

    Log space so a signal is never negative and so ``sigma`` means the same
    thing for a cheap good as for an expensive one.
    """
    out = []
    for i in range(cfg.n_agents):
        signal = normalise([math.exp(math.log(truth[g]) + rng.gauss(0.0, cfg.sigma))
                            for g in range(cfg.n_goods)])
        out.append(Agent(index=i, signal=signal, position=list(signal)))
    return out
