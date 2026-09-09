"""One stream, one rule, one mode — and the record it leaves.

Outcome and mechanism are kept apart in the record, per the repo's standing
rule. A rule can end on the right leader having starved it for most of the
stream: that is a correct outcome from a mechanism that would have failed on a
shorter run, and they are two claims.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field, asdict
from typing import Any

from .rules import Rule, Stats
from .world import MODES, Pool, allocate, best_payoff, coupling, observe


@dataclass
class Record:
    """Everything one stream produced. Kept whole; anything anyone later wants
    should come out of this rather than a re-run."""

    rule: str
    mode: str
    seed: int
    start: str
    steps: int
    invocations: int
    quality: tuple[float, ...]
    noise: float
    explore: float

    # Outcome
    regret: float = 0.0
    final_leader: int = -1
    final_correct: bool = False
    first_correct_step: int | None = None

    # Mechanism
    promotions: list[tuple[int, int, int]] = field(default_factory=list)
    entrenched_steps: int = 0
    starved_share: float = 0.0
    reversals: int = 0
    would_have: list[tuple[int, int, int]] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["quality"] = list(self.quality)
        return d


def play(pool: Pool, rule: Rule, mode: str, *, seed: int, start: str = "worst",
         steps: int = 400, invocations: int = 20,
         threshold: float = 0.5, floor: float = 0.2) -> Record:
    """Run one stream.

    Every rule under one seed sees the same pool and the same noise draws for
    the same (candidate, step) — the RNG is keyed off the stream, not off the
    rule's choices — so a difference between rules is the rule rather than the
    draw.
    """
    kind = MODES[mode]
    kw = {"threshold": threshold, "floor": floor} if kind == "step" else {}
    rng = random.Random(seed * 1_000_003 + 17)

    leader = _start_index(pool, start)
    stats = Stats.empty(pool.size)
    seen_leaders = {leader}
    ceiling = best_payoff(pool, kind, **kw)

    rec = Record(rule=rule.name, mode=mode, seed=seed, start=start, steps=steps,
                 invocations=invocations, quality=pool.quality, noise=pool.noise,
                 explore=rule.explore)

    starved_total, starved_steps = 0.0, 0

    for step in range(steps):
        shares = rule.shares(leader, stats, step)
        counts = allocate(shares, invocations, offset=step)
        realised = 0.0
        for i, k in enumerate(counts):
            if k == 0:
                continue
            share = k / invocations
            for _ in range(k):
                score = observe(rng, pool, i, share, kind, **kw)
                stats.add(i, score)
                realised += score
        rec.regret += ceiling - realised / invocations

        if leader != pool.best:
            rec.entrenched_steps += 1
            starved_total += counts[pool.best] / invocations
            starved_steps += 1

        target = rule.challenger(leader, stats)
        if target is not None:
            if rule.gated:
                rec.would_have.append((step, leader, target))
            else:
                rec.promotions.append((step, leader, target))
                if target in seen_leaders:
                    rec.reversals += 1
                seen_leaders.add(target)
                leader = target
                if leader == pool.best and rec.first_correct_step is None:
                    rec.first_correct_step = step

    rec.final_leader = leader
    rec.final_correct = leader == pool.best
    rec.starved_share = starved_total / starved_steps if starved_steps else 0.0
    return rec


def _start_index(pool: Pool, start: str) -> int:
    """Where the stream begins.

    Varied deliberately: a rule that only looks good when it starts on a good
    leader has not been tested.
    """
    order = sorted(range(pool.size), key=lambda i: -pool.quality[i])
    if start == "best":
        return order[0]
    if start == "worst":
        return order[-1]
    if start == "middle":
        return order[len(order) // 2]
    raise ValueError(f"unknown start {start!r}; expected best, middle or worst")
