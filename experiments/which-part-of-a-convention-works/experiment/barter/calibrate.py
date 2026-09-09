"""Tier 3 instrument calibration: efficiency as a function of a convention's
content error, at known adherence.

[tier3-design.md](../../tier3-design.md) asks how wrong a shared convention can
be and still be worth holding. Answering that needs a curve nobody has yet:
what a convention of quality δ is *worth* when it is fully adopted. That curve
is free — it needs no models, only the scripted traders and the equilibrium the
island already knows how to compute.

The perturbation is applied to ``walras`` prices, which are the correct
convention by construction. Everything else about the arm is held at arm C:
same specialisation rule, same acceptance test, same proposal search, same
manager. Only where the price came from changes.

**What this tier cannot do.** A scripted trader has no beliefs about other
agents, so handing it the vector "as the island's convention" and handing it the
same vector privately produce byte-identical behaviour. The common-knowledge
half of the Tier 3 design — the CS − CP gap, which is the whole claim about
sharedness — is therefore *not measurable here at all*, at any δ. It is
irreducibly a model-tier question. This calibration measures the content axis
and the adherence axis, and is silent on the third.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from .economy import Island, walras
from .traders import NUMERAIRE


def normalise(price: Iterable[float]) -> list[float]:
    """Rescale so the numeraire reads 1.

    The scripted arms hold the numeraire at 1 and only relative prices carry
    meaning, so a perturbation that changed the overall level would register as
    an error it is not.
    """
    p = list(price)
    base = p[NUMERAIRE]
    if base <= 0:
        raise ValueError("the numeraire must have a positive price")
    return [x / base for x in p]


def perturb(price: Iterable[float], delta: float, direction: str) -> list[float]:
    """A convention of known wrongness.

    Two directions, because a single scalar hides the difference between them
    and they are not the same mistake:

    * ``flatten`` pulls every price toward their common mean. At ``delta = 1``
      the vector says every good is worth the same, which is what an agent that
      never heard a price believes — so this direction interpolates the
      convention toward *no convention*.
    * ``sharpen`` pushes prices away from the mean, exaggerating the spread. The
      vector still ranks the goods correctly; it overstates how much better the
      best one is, so agents specialise harder than the island can support. This
      is the direction that should hurt asymmetrically, because Tier 1 already
      showed that specialisation is a commitment and its downside is total.
    """
    p = normalise(price)
    if delta < 0:
        raise ValueError("delta must be non-negative")
    if direction == "flatten":
        mean = sum(p) / len(p)
        out = [(1.0 - delta) * x + delta * mean for x in p]
    elif direction == "sharpen":
        logs = [math.log(x) for x in p]
        mean = sum(logs) / len(logs)
        out = [math.exp(mean + (1.0 + delta) * (x - mean)) for x in logs]
    else:
        raise ValueError(f"unknown direction {direction!r}; expected flatten or sharpen")
    return normalise(out)


def distance(a: Iterable[float], b: Iterable[float]) -> float:
    """Realised relative distance between two price vectors, both normalised.

    ``delta`` is a knob on a perturbation, not a distance — the same delta means
    different things in the two directions and on different islands. This is
    what actually moved, and it is what the record reports alongside delta so a
    curve can be read against either.
    """
    x, y = normalise(a), normalise(b)
    num = math.sqrt(sum((p - q) ** 2 for p, q in zip(x, y)))
    den = math.sqrt(sum(q * q for q in y))
    return num / den if den else 0.0


@dataclass(frozen=True)
class Announcement:
    """One manufactured convention, and everything needed to interpret it."""

    delta: float
    direction: str
    price: tuple[float, ...]
    #: The equilibrium this was perturbed away from.
    truth: tuple[float, ...]
    #: Realised relative distance, ``delta``'s effect rather than its value.
    error: float
    #: The production split the announced vector implies for each agent — the
    #: answer key for strategy adoption once model agents are on the island.
    implied: tuple[tuple[float, ...], ...]

    def to_json(self) -> dict:
        return {
            "delta": self.delta,
            "direction": self.direction,
            "price": list(self.price),
            "truth": list(self.truth),
            "error": self.error,
            "implied": [list(r) for r in self.implied],
        }


def implied_plan(island: Island, price: list[float]) -> tuple[tuple[float, ...], ...]:
    """What each agent produces if it believes ``price``.

    This is arm C's rule — with linear technology and one unit of labour, a
    price-taker puts everything into the good with the highest ``price ×
    capacity``. It is duplicated here rather than imported because it is being
    used for a different purpose: in ``traders`` it is a policy, and here it is
    the answer key that policy is scored against.
    """
    rows = []
    for i in range(island.n_agents):
        cap = island.capacity[i]
        best = max(range(island.n_goods), key=lambda g: price[g] * cap[g])
        rows.append(tuple(1.0 if g == best else 0.0 for g in range(island.n_goods)))
    return tuple(rows)


def announce(island: Island, delta: float, direction: str = "flatten",
             *, rounds: int = 400) -> Announcement:
    """Manufacture a convention of known quality for one island."""
    truth = normalise(walras(island, rounds=rounds).prices)
    price = perturb(truth, delta, direction)
    return Announcement(
        delta=delta,
        direction=direction,
        price=tuple(price),
        truth=tuple(truth),
        error=distance(price, truth),
        implied=implied_plan(island, price),
    )


#: The sweep. Dense near zero because that is where the interesting question
#: lives: a convention slightly wrong is the realistic case, and a convention
#: wrong by half is a straw man.
DELTAS: tuple[float, ...] = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0)

#: Adherence levels. 1.0 is the calibration proper — what a convention of
#: quality δ is worth when everybody holds it. Below that the curve is the
#: partial-adoption term the model tier needs in order to subtract its own
#: adoption shortfall from its efficiency.
ADHERENCES: tuple[float, ...] = (1.0, 0.75, 0.5, 0.25)
