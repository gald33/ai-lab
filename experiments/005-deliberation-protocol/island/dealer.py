"""Draws the island, and tells each trader its own half of it.

Split out of the manager on purpose. `games/island.md` sets four conditions
under which a stranger's manager could be trusted, and the first is that **the
manager holds no tastes**: it needs `alpha` for exactly one thing -- computing
utility at the bell -- and taking scoring out of it means it knows nothing a
spectator does not. That is the whole reason this file exists.

So the split is by *what each party knows*, not by convenience:

* the **dealer** draws the island from the seed and owns `alpha`. It is the
  only thing here that ever sees a taste.
* the **manager** settles production and exchange. It needs `capacity` and
  nothing else, and after this file it never receives an `Island` at all.
* **scoring** happens afterwards, from the seed and the holdings the manager
  recorded -- `score.trajectory_from`, and the ledger already redraws the
  island for itself rather than believing anybody.

Capacity is not secret and this file does not pretend it is: a trader's own
`PRODUCE` gives its shares and the manager's receipt gives the quantities, so
anyone reading the board can divide one by the other. `alpha` is the only
genuinely private thing in the game.

**The dealer never posts.** It hands back text and lets its caller decide how
that text travels -- in the clear for a practice game, sealed once there is a
private channel to seal it into (`games/island.md`, item 2c). Distribution is
a policy, and it belongs to whoever is running the game rather than to the
thing that drew it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# `..` twice to the experiments directory, then into 002's tree. A code
# dependency is not grounding -- 005's CLAUDE.md says so about this exact
# import.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import Island, draw_island  # noqa: E402

#: The goods every island in this experiment is drawn over, in the order the
#: manager and the reveal sidecar both read them in.
GOODS = ("bread", "cloth", "iron", "salt")


@dataclass
class Dealer:
    """One island, and the private half of it that belongs to each trader."""

    island: Island
    goods: tuple[str, ...] = GOODS
    names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.names:
            self.names = tuple(f"T{i + 1}" for i in range(self.island.n_agents))

    @classmethod
    def draw(cls, seed: int, agents: int, goods: tuple[str, ...] = GOODS,
             names: tuple[str, ...] = ()) -> Dealer:
        """The island this seed produces. Deterministic, and the reason the
        seed must not reach a board while a round is live: anybody holding it
        can run this and read every trader's tastes."""
        return cls(island=draw_island(agents, len(goods), seed=seed),
                   goods=goods, names=names)

    @property
    def capacity(self) -> tuple[tuple[float, ...], ...]:
        """What the manager settles production against, and all it gets."""
        return self.island.capacity

    def private_state(self, name: str) -> str:
        """What only this trader is told. Handed back, never posted."""
        index = self.names.index(name)
        cap = {g: round(self.island.capacity[index][i], 4)
               for i, g in enumerate(self.goods)}
        taste = {g: round(self.island.alpha[index][i], 4)
                 for i, g in enumerate(self.goods)}
        return (f"You are {name}. Your production capacity per unit of labour: "
                f"{cap}. Your taste weights: {taste}. Nobody else knows either.")
