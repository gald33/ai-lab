"""The promotion rules — the actual subject of the experiment.

A rule is an **(allocation, promotion) pair**, not a promotion rule alone. How
much a candidate is tried and when it is promoted are the same decision in
practice, and entrenchment lives exactly in that coupling: a leader that holds
most of the traffic accumulates evidence faster than the challenger that would
displace it. Separating the two here would measure a promoter nobody would
build.

Every rule sees observations and nothing else. None of them can read
``Pool.quality``; that is the harness's, and a rule that could see it would be
answering a different question.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Stats:
    """Running count, mean and sum of squares per candidate."""

    n: list[int]
    total: list[float]
    sq: list[float]

    @classmethod
    def empty(cls, size: int) -> "Stats":
        return cls(n=[0] * size, total=[0.0] * size, sq=[0.0] * size)

    def add(self, index: int, score: float) -> None:
        self.n[index] += 1
        self.total[index] += score
        self.sq[index] += score * score

    def mean(self, index: int) -> float:
        if self.n[index] == 0:
            return 0.0
        return self.total[index] / self.n[index]

    def stderr(self, index: int) -> float:
        """Standard error of the mean. Infinite below two observations, which
        is what stops an interval rule from acting on a single sample."""
        k = self.n[index]
        if k < 2:
            return math.inf
        var = max(self.sq[index] / k - self.mean(index) ** 2, 0.0)
        return math.sqrt(var / k)


@dataclass
class Rule:
    """One (allocation, promotion) pair.

    ``explore`` is the fraction of traffic held off the leader. It is reported
    with every entrenchment number, because entrenchment measured in stream
    position is partly a restatement of how little a rule explores.
    """

    name: str
    explore: float = 0.10
    #: Minimum observations on a challenger before it may be promoted.
    n_min: int = 1
    #: Confidence multiplier. Above zero, a challenger must clear the leader by
    #: this many standard errors — the difference between "looks better" and
    #: "is distinguishable from better".
    z: float = 0.0
    #: Allocate by UCB rather than leader-plus-exploration.
    bandit: bool = False
    #: Never promote. Records what it would have done instead.
    gated: bool = False
    #: Exploration constant, bandit only.
    c: float = 1.0

    def shares(self, leader: int, stats: Stats, step: int) -> list[float]:
        """Traffic across candidates for this step."""
        size = len(stats.n)
        if self.bandit:
            return self._ucb_shares(stats, step, size)
        rest = self.explore / (size - 1) if size > 1 else 0.0
        shares = [rest] * size
        shares[leader] = 1.0 - self.explore
        return shares

    def _ucb_shares(self, stats: Stats, step: int, size: int) -> list[float]:
        """UCB1 over the invocations of one step.

        Allocation is decided before any of this step's scores exist, so in
        protocol mode a candidate the bandit is sampling thinly is *scored*
        thinly. The bandit is not being sabotaged; it is meeting the thing the
        mode is about.
        """
        total = max(sum(stats.n), 1)
        scores = []
        for i in range(size):
            if stats.n[i] == 0:
                scores.append(math.inf)
            else:
                bonus = self.c * math.sqrt(2.0 * math.log(total + 1) / stats.n[i])
                scores.append(stats.mean(i) + bonus)
        top = max(scores)
        winners = [i for i, s in enumerate(scores) if s == top]
        shares = [0.0] * size
        for i in winners:
            shares[i] = 1.0 / len(winners)
        return shares

    def challenger(self, leader: int, stats: Stats) -> int | None:
        """Who this rule would promote now, or None.

        ``gated`` returns the same answer as an ``interval`` rule would; the
        runner is what declines to act on it. That is the point of the arm — it
        is the person who looked at a single island and said no, and it makes
        the cost of automation legible rather than assumed.
        """
        size = len(stats.n)
        best, best_gap = None, 0.0
        for i in range(size):
            if i == leader or stats.n[i] < max(self.n_min, 1):
                continue
            gap = stats.mean(i) - stats.mean(leader)
            if gap <= 0:
                continue
            if self.z > 0:
                spread = self.z * (stats.stderr(i) + stats.stderr(leader))
                if not math.isfinite(spread) or gap <= spread:
                    continue
            if gap > best_gap:
                best, best_gap = i, gap
        return best


#: The five conditions. They run from careless to conservative, and `gated` is
#: the control rather than a contender: it never promotes, so its regret is
#: whatever the initial leader was worth, and its would-have record is what the
#: same evidence supported under a human hold.
RULES: dict[str, Rule] = {
    "greedy": Rule("greedy"),
    "nmin": Rule("nmin", n_min=30),
    "interval": Rule("interval", n_min=30, z=2.0),
    "bandit": Rule("bandit", bandit=True, n_min=30, z=2.0),
    "gated": Rule("gated", n_min=30, z=2.0, gated=True),
}

RULE_NAMES = tuple(RULES)
