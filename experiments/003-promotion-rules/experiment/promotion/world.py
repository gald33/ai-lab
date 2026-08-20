"""The pool, the payoff, and the two modes.

The promoter is the subject of this experiment, so everything here is
deliberately dumb: candidates have a true quality the harness sets, and a payoff
that is either independent of how many others use them (`strategy`) or scaled by
it (`protocol`). That single coupling is the only difference between the modes
and the only load-bearing thing in the design — with ``coupling`` removed, the
two modes are the same code path and the experiment says so.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Pool:
    """The candidates, with the qualities only the harness can see.

    Manufactured quality is the whole instrument. In a real system — Lucille,
    or anything that promotes solutions automatically — the true ranking is
    unknown, which is exactly why an entrenched wrong leader is invisible
    there. Here "did the promoter find the best one" is a lookup.
    """

    #: True quality per candidate. Never shown to a rule.
    quality: tuple[float, ...]
    #: Standard deviation of one observation. Same for every candidate, so a
    #: rule cannot win by exploiting a variance difference nobody designed in.
    noise: float = 0.15

    def __post_init__(self) -> None:
        if len(self.quality) < 2:
            raise ValueError("a competition needs at least two candidates")
        if self.noise < 0:
            raise ValueError("noise must be non-negative")

    @property
    def size(self) -> int:
        return len(self.quality)

    @property
    def best(self) -> int:
        """The index a correct promoter ends on."""
        return max(range(self.size), key=lambda i: self.quality[i])

    def rank(self, index: int) -> int:
        """0 for the best candidate, size-1 for the worst."""
        order = sorted(range(self.size), key=lambda i: -self.quality[i])
        return order.index(index)


def draw_pool(rng: random.Random, *, size: int = 5, spread: float = 0.4,
              noise: float = 0.15) -> Pool:
    """A pool whose qualities are spread over ``[1 - spread, 1]``.

    Qualities are kept close together on purpose. A pool with one obvious
    winner is promoted correctly by any rule, and would measure nothing.
    """
    quality = tuple(sorted(1.0 - spread * rng.random() for _ in range(size)))
    return Pool(quality=quality, noise=noise)


#: The coordination payoff. ``f(a)`` scales a candidate's quality by the
#: fraction of the population currently on it.
#:
#: This shape is invented, and the strength of any protocol-mode result depends
#: on it — so both forms are run and the form is recorded per run. `linear` is
#: the pure case: a protocol nobody else uses is worth nothing at all. `step` is
#: the forgiving one: a protocol is worth most of its quality once enough of the
#: population is on it, and a fraction of it below that.
def coupling(kind: str, share: float, *, threshold: float = 0.5,
             floor: float = 0.2) -> float:
    if kind == "none":
        return 1.0
    if kind == "linear":
        return share
    if kind == "step":
        return 1.0 if share >= threshold else floor
    raise ValueError(f"unknown coupling {kind!r}; expected none, linear or step")


#: The two payoff modes, as the coupling each uses. `strategy` is the mode where
#: payoff depends on the world; `protocol` is where it depends on the
#: population. Nothing else differs.
MODES: dict[str, str] = {
    "strategy": "none",
    "protocol-linear": "linear",
    "protocol-step": "step",
}


def best_payoff(pool: Pool, kind: str, **kw: float) -> float:
    """What the stream would have paid with the whole population on the best
    candidate. The regret baseline, and the reason regret is comparable across
    modes at all."""
    return pool.quality[pool.best] * coupling(kind, 1.0, **kw)


def observe(rng: random.Random, pool: Pool, index: int, share: float,
            kind: str, **kw: float) -> float:
    """One invocation's score.

    The share passed here is the candidate's *current* allocation, so a
    challenger being tried at 5% of traffic is scored at 5% of traffic. That is
    not a handicap added for effect — it is what a protocol under trial
    actually is.
    """
    mean = pool.quality[index] * coupling(kind, share, **kw)
    return mean + rng.gauss(0.0, pool.noise)


def allocate(shares: list[float], invocations: int, *, offset: int = 0) -> list[int]:
    """Turn float shares into whole invocations, largest remainder.

    Exact by construction: the counts sum to ``invocations``, so a step can
    never quietly run more or fewer trials than the record says it did.

    ``offset`` rotates the tie-break, and it is not cosmetic. An exploration
    share thinner than one invocation gives every challenger the *same*
    remainder, so a fixed tie-break hands the spare invocations to the same low
    indices on every step of every run — and the rest of the pool is never
    sampled at all, for any rule, however long the stream. Pass the step here
    and the ties rotate, which is the difference between a rule that explores
    and a harness that decides the result.
    """
    total = sum(shares)
    if total <= 0:
        raise ValueError("shares must not be all zero")
    size = len(shares)
    exact = [s / total * invocations for s in shares]
    counts = [int(math.floor(x)) for x in exact]
    remainder = invocations - sum(counts)
    if remainder == 0:
        return counts

    order = sorted(range(size), key=lambda i: -(exact[i] - counts[i]))
    # Rotate within the tie group that straddles the cutoff — not across the
    # whole index space. Only that group is contested: everything above it is
    # taking a slot on any rotation and everything below is taking none, so
    # rotating them changes nothing and rotating the full list hands the
    # contested slots out unevenly.
    cut = exact[order[remainder - 1]] - counts[order[remainder - 1]]
    lo = next(p for p in range(size) if exact[order[p]] - counts[order[p]] <= cut)
    hi = next((p for p in range(lo, size)
               if exact[order[p]] - counts[order[p]] < cut), size)
    group = order[lo:hi]
    if len(group) > 1:
        turn = (offset * (remainder - lo)) % len(group)
        order[lo:hi] = group[turn:] + group[:turn]

    for i in order[:remainder]:
        counts[i] += 1
    return counts
