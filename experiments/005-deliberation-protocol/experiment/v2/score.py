"""Scoring a finished episode. Reads world state; never reads what agents said.

The primary metric is the design's ``W``: the mean over a world's periods of
``economy.efficiency``'s **lower** bound on that period's realised utilities.
The lower bound is the conservative end of a certified sandwich, so a world is
never credited with more than an achievable allocation proves.

The exchange ceiling is 1.0 and is not estimated: the competitive equilibrium
is Pareto-optimal, so the only benchmark worth computing per island is the
autarky floor.
"""

from __future__ import annotations

import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import Island, autarky, efficiency, gains  # noqa: E402

_ZERO = 1e-12


@dataclass
class Score:
    w: float
    w_upper: float
    by_period: list[float]
    floor: float
    zero_agent_periods: int
    agent_periods: int
    first_above_floor: int | None
    #: Companion primary, declared in AMENDMENT-v2.md: median gains over
    #: autarky across agents, then mean across periods. One ruined agent moves
    #: a median by one rank instead of destroying it, which is exactly what W
    #: could not survive.
    g: float = 0.0
    g_by_period: list[float] = None  # type: ignore[assignment]
    #: Never folded into G. A median says nothing about the tail, and the tail
    #: is what broke the first metric.
    worst: float = 0.0
    below: int = 0

    def to_json(self) -> dict:
        return {"W": round(self.w, 6), "W_upper": round(self.w_upper, 6),
                "by_period": [round(x, 6) for x in self.by_period],
                "autarky_floor": round(self.floor, 6),
                "zero_agent_periods": self.zero_agent_periods,
                "agent_periods": self.agent_periods,
                "first_above_floor": self.first_above_floor,
                "G": round(self.g, 6),
                "G_by_period": [round(x, 6) for x in self.g_by_period],
                "worst_gain": round(self.worst, 6),
                "below_autarky": self.below}


def score(island: Island, trajectory: list[list[float]]) -> Score:
    if not trajectory:
        raise ValueError("an episode with no closed period cannot be scored")
    _, auto = autarky(island)
    floor = efficiency(island, list(auto)).lower
    lowers, uppers, first = [], [], None
    for p, utils in enumerate(trajectory):
        e = efficiency(island, list(utils))
        lowers.append(e.lower)
        uppers.append(e.upper)
        if first is None and e.lower > floor:
            first = p
    zero = sum(1 for row in trajectory for u in row if u <= _ZERO)
    per_period = [gains(island, list(utils)) for utils in trajectory]
    return Score(w=statistics.mean(lowers), w_upper=statistics.mean(uppers),
                 by_period=lowers, floor=floor,
                 zero_agent_periods=zero,
                 agent_periods=sum(len(r) for r in trajectory),
                 first_above_floor=first,
                 g=statistics.mean(p.median for p in per_period),
                 g_by_period=[p.median for p in per_period],
                 worst=min(p.worst for p in per_period),
                 below=sum(p.below for p in per_period))
