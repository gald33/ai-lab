"""Two efficiencies, on two different objects.

**Per-episode.** The distance of that episode's utility vector from the
one-episode Pareto frontier. This is a coverage measure whether or not it was
meant as one: with Cobb-Douglas preferences a single agent at zero utility puts
the whole vector maximally far from the frontier, so one ruined trader zeroes
the episode however well the other seven did. That is arithmetically correct and
it is why this number must not be read as welfare.

**Per-round.** The distance of the **accumulated** utility vector -- summed over
the round's `k` episodes -- from the frontier of the total. An agent that is
ruined in one episode and fed in the other four has positive accumulated
utility, so the single-zero annihilation cannot happen here. This is the
welfare measure.

The frontier of the total is `k` times the one-episode frontier. Cobb-Douglas
exponents sum to 1 on this island, so utility is homogeneous of degree 1: `k`
identical episodes sum to `k x` one episode's utility against `k x` the
one-episode frontier. Dividing the accumulated vector by `k` therefore puts it
back on the one-episode frontier's scale, which is what `round_efficiency`
does. That identity is 004's argument and its review target #1, so it is gated
in `tests/test_v2.py` rather than asserted here.
"""

from __future__ import annotations

import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import Island, autarky, efficiency, gains  # noqa: E402

_ZERO = 1e-12


@dataclass
class Score:
    #: THE primary. Accumulated utility against the frontier of the total.
    eff_round: float
    eff_round_upper: float
    #: One per episode. Coverage, not welfare.
    eff_episode: list[float] = field(default_factory=list)
    #: Same construction as eff_round, on autarky and on the equilibrium.
    floor: float = 0.0
    #: Diagnostics that a median cannot show: who was ruined, and how often.
    gain_median: float = 0.0
    gain_worst: float = 0.0
    below_autarky: int = 0
    zero_agent_episodes: int = 0
    agent_episodes: int = 0
    #: First episode index whose per-episode efficiency exceeded the floor.
    first_above_floor: int | None = None

    def to_json(self) -> dict:
        return {"eff_round": round(self.eff_round, 6),
                "eff_round_upper": round(self.eff_round_upper, 6),
                "eff_episode": [round(x, 6) for x in self.eff_episode],
                "autarky_floor": round(self.floor, 6),
                "gain_median": round(self.gain_median, 6),
                "gain_worst": round(self.gain_worst, 6),
                "below_autarky": self.below_autarky,
                "zero_agent_episodes": self.zero_agent_episodes,
                "agent_episodes": self.agent_episodes,
                "first_above_floor": self.first_above_floor}


def accumulate(trajectory: list[list[float]]) -> list[float]:
    """Sum each agent's utility across the round's episodes."""
    n = len(trajectory[0])
    return [sum(row[i] for row in trajectory) for i in range(n)]


def round_efficiency(island: Island, trajectory: list[list[float]]):
    """Accumulated utility against the frontier of the total.

    Dividing by the episode count rescales the total onto the one-episode
    frontier, which is exact because utility is homogeneous of degree 1 here.
    """
    k = len(trajectory)
    mean_vector = [u / k for u in accumulate(trajectory)]
    return efficiency(island, mean_vector)


def score(island: Island, trajectory: list[list[float]]) -> Score:
    if not trajectory:
        raise ValueError("a round with no closed episode cannot be scored")
    _, auto = autarky(island)
    # The floor is built the same way the metric is: an autarkic round is k
    # identical autarkic episodes, so its accumulated vector over k is `auto`.
    floor = efficiency(island, list(auto)).lower

    per_episode = [efficiency(island, list(utils)).lower for utils in trajectory]
    first = next((i for i, e in enumerate(per_episode) if e > floor), None)

    whole = round_efficiency(island, trajectory)
    k = len(trajectory)
    g = gains(island, [u / k for u in accumulate(trajectory)])
    per_episode_gains = [gains(island, list(utils)) for utils in trajectory]

    return Score(
        eff_round=whole.lower, eff_round_upper=whole.upper,
        eff_episode=per_episode, floor=floor,
        gain_median=g.median, gain_worst=g.worst, below_autarky=g.below,
        zero_agent_episodes=sum(1 for row in trajectory
                                for u in row if u <= _ZERO),
        agent_episodes=sum(len(r) for r in trajectory),
        first_above_floor=first,
    )
