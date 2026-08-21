"""The island, the clock, and the Switchboard surface. No agents in this file.

This is the authoritative state. Everything the experiment scores is read from
here, and nothing an agent *says* enters it -- a message is stored and
delivered, never interpreted. The only calls that change the world are
``produce``, ``offer``, ``accept``, ``decline`` and ``cancel``.

Two invariants are asserted rather than trusted:

* **Conservation.** Goods are created only by ``produce`` and destroyed only at
  the bell. The check runs at the bell *before* anything is consumed, while the
  books still balance, so a flow episode is exactly as strongly checked as a
  stock one. This is 004's ordering, and the reason for it is that relaxing the
  invariant to accommodate eating is how a harness quietly lets an island
  manufacture goods and beat its own frontier.
* **Stage gating.** A call belonging to a closed stage raises. The clock is the
  one thing the system does enforce, and the design says so out loud.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "002-barter-conventions" / "experiment"))

from barter.economy import Island, utility  # noqa: E402

_EPS = 1e-9

FLOOR, PRODUCTION, MARKET, SETTLEMENT = "floor", "production", "market", "settlement"
STAGES = (FLOOR, PRODUCTION, MARKET, SETTLEMENT)


class ActionError(Exception):
    """A refused call. Always the agent's fault, never the harness's."""


@dataclass
class Message:
    sender: str
    text: str
    public: bool
    to: str | None
    episode: int
    stage: str

    def to_json(self) -> dict:
        return {"from": self.sender, "text": self.text,
                "public": self.public, "to": self.to,
                "episode": self.episode, "stage": self.stage}


@dataclass
class Offer:
    offer_id: str
    maker: str
    taker: str
    give: dict[str, float]
    want: dict[str, float]
    episode: int
    status: str = "open"

    def to_json(self) -> dict:
        return {"offer_id": self.offer_id, "from": self.maker, "to": self.taker,
                "give": self.give, "want": self.want,
                "episode": self.episode, "status": self.status}


@dataclass
class Trader:
    name: str
    index: int
    holdings: list[float]
    spent: float = 0.0
    produced_this_episode: bool = False
    #: Index into the message log of the last item this trader has read.
    read_cursor: int = 0


@dataclass
class World:
    """One island, one run. Deterministic given the island and the seed."""

    island: Island
    episodes: int
    goods: tuple[str, ...] = ("bread", "cloth", "iron", "salt")
    episode: int = 0
    stage: str = FLOOR
    traders: dict[str, Trader] = field(default_factory=dict)
    log: list[Message] = field(default_factory=list)
    offers: dict[str, Offer] = field(default_factory=dict)
    #: One row of per-agent utilities per closed episode.
    episode_utilities: list[list[float]] = field(default_factory=list)
    consumed: list[float] = field(default_factory=list)
    _next_offer: int = 1
    #: Counters that separate one kind of non-trade from another. A bell
    #: expiry is not a decline and must never be counted as one -- that
    #: conflation is a defect 004 found in its own scoring.
    made: int = 0
    executed: int = 0
    declined: int = 0
    cancelled: int = 0
    expired_at_bell: int = 0
    posts: int = 0
    directs: int = 0
    chars: int = 0

    def __post_init__(self) -> None:
        if len(self.goods) != self.island.n_goods:
            raise ValueError("goods names do not match the island")
        self.consumed = [0.0] * self.island.n_goods
        for i in range(self.island.n_agents):
            name = f"T{i + 1}"
            self.traders[name] = Trader(name=name, index=i,
                                        holdings=[0.0] * self.island.n_goods)

    # --- helpers ----------------------------------------------------------

    def _trader(self, name: str) -> Trader:
        if name not in self.traders:
            raise ActionError(f"no such trader {name!r}")
        return self.traders[name]

    def _good(self, name: str) -> int:
        if name not in self.goods:
            raise ActionError(f"no such good {name!r}; goods are "
                              f"{', '.join(self.goods)}")
        return self.goods.index(name)

    def _require(self, stage: str) -> None:
        if self.stage != stage:
            raise ActionError(f"that call belongs to the {stage} stage; "
                              f"the {self.stage} stage is open")

    def _escrowed(self, name: str) -> dict[str, float]:
        held: dict[str, float] = {}
        for o in self.offers.values():
            if o.status == "open" and o.maker == name:
                for g, q in o.give.items():
                    held[g] = held.get(g, 0.0) + q
        return held

    def free(self, name: str, good: str) -> float:
        """Holdings not tied up in an open offer."""
        t = self._trader(name)
        return t.holdings[self._good(good)] - self._escrowed(name).get(good, 0.0)

    # --- communication ----------------------------------------------------

    def post(self, name: str, text: str) -> dict:
        """Publish to the board. Visible to everyone, permanently."""
        self._trader(name)
        if not isinstance(text, str) or not text.strip():
            raise ActionError("a post needs text")
        self.log.append(Message(name, text, True, None, self.episode, self.stage))
        self.posts += 1
        self.chars += len(text)
        return {"ok": True, "channel": "board"}

    def message(self, name: str, to: str, text: str) -> dict:
        """Send to one trader. Nobody else ever sees it."""
        self._trader(name)
        self._trader(to)
        if to == name:
            raise ActionError("you cannot message yourself")
        if not isinstance(text, str) or not text.strip():
            raise ActionError("a message needs text")
        self.log.append(Message(name, text, False, to, self.episode, self.stage))
        self.directs += 1
        self.chars += len(text)
        return {"ok": True, "channel": "direct"}

    def read(self, name: str) -> list[dict]:
        """Everything on the board plus everything sent to you, since last read.

        The cursor advances, so an agent sees each item once. Its own messages
        are excluded: an agent knows what it said.
        """
        t = self._trader(name)
        out = []
        for item in self.log[t.read_cursor:]:
            if item.sender == name:
                continue
            if item.public or item.to == name:
                out.append(item.to_json())
        t.read_cursor = len(self.log)
        return out

    # --- economy ----------------------------------------------------------

    def produce(self, name: str, plan: dict[str, float]) -> dict:
        self._require(PRODUCTION)
        t = self._trader(name)
        if t.produced_this_episode:
            raise ActionError("you have already produced this episode")
        if not isinstance(plan, dict) or not plan:
            raise ActionError("a plan is {good: share} with at least one good")
        total = 0.0
        shares = [0.0] * self.island.n_goods
        for good, share in plan.items():
            g = self._good(good)
            try:
                s = float(share)
            except (TypeError, ValueError):
                raise ActionError(f"share for {good} is not a number")
            if s < 0:
                raise ActionError("shares cannot be negative")
            shares[g] += s
            total += s
        if total > 1.0 + 1e-6:
            raise ActionError(f"shares sum to {total:.3f}; the budget is 1.0")
        made = {}
        for g in range(self.island.n_goods):
            if shares[g] > 0:
                qty = shares[g] * self.island.capacity[t.index][g]
                t.holdings[g] += qty
                made[self.goods[g]] = round(qty, 4)
        t.spent = total
        t.produced_this_episode = True
        return {"ok": True, "produced": made, "labour_unspent": round(1 - total, 4)}

    def offer(self, name: str, to: str, give: dict, want: dict) -> dict:
        self._require(MARKET)
        self._trader(name)
        self._trader(to)
        if to == name:
            raise ActionError("you cannot trade with yourself")
        give_q = self._bundle(give, "give")
        want_q = self._bundle(want, "want")
        for good, qty in give_q.items():
            if self.free(name, good) + _EPS < qty:
                raise ActionError(
                    f"you have {self.free(name, good):.4f} {good} free, "
                    f"not {qty:.4f}; goods in open offers are already committed")
        oid = f"o{self._next_offer}"
        self._next_offer += 1
        self.offers[oid] = Offer(oid, name, to, give_q, want_q, self.episode)
        self.made += 1
        return {"ok": True, "offer_id": oid}

    def _bundle(self, raw: dict, label: str) -> dict[str, float]:
        if not isinstance(raw, dict) or not raw:
            raise ActionError(f"{label} is {{good: quantity}} and cannot be empty")
        out: dict[str, float] = {}
        for good, qty in raw.items():
            self._good(good)
            try:
                q = float(qty)
            except (TypeError, ValueError):
                raise ActionError(f"{label} quantity for {good} is not a number")
            if q <= 0:
                raise ActionError(f"{label} quantities must be positive")
            out[good] = out.get(good, 0.0) + q
        return out

    def accept(self, name: str, offer_id: str) -> dict:
        self._require(MARKET)
        o = self._open_offer(offer_id)
        if o.taker != name:
            raise ActionError(f"{offer_id} was not offered to you")
        for good, qty in o.want.items():
            if self.free(name, good) + _EPS < qty:
                raise ActionError(
                    f"you have {self.free(name, good):.4f} {good} free, "
                    f"not the {qty:.4f} this offer asks for")
        maker, taker = self._trader(o.maker), self._trader(name)
        for good, qty in o.give.items():
            g = self._good(good)
            maker.holdings[g] -= qty
            taker.holdings[g] += qty
        for good, qty in o.want.items():
            g = self._good(good)
            taker.holdings[g] -= qty
            maker.holdings[g] += qty
        o.status = "executed"
        self.executed += 1
        return {"ok": True, "executed": offer_id}

    def decline(self, name: str, offer_id: str) -> dict:
        self._require(MARKET)
        o = self._open_offer(offer_id)
        if o.taker != name:
            raise ActionError(f"{offer_id} was not offered to you")
        o.status = "declined"
        self.declined += 1
        return {"ok": True, "declined": offer_id}

    def cancel(self, name: str, offer_id: str) -> dict:
        self._require(MARKET)
        o = self._open_offer(offer_id)
        if o.maker != name:
            raise ActionError(f"{offer_id} is not yours to cancel")
        o.status = "cancelled"
        self.cancelled += 1
        return {"ok": True, "cancelled": offer_id}

    def _open_offer(self, offer_id: str) -> Offer:
        if offer_id not in self.offers:
            raise ActionError(f"no such offer {offer_id!r}")
        o = self.offers[offer_id]
        if o.status != "open":
            raise ActionError(f"{offer_id} is already {o.status}")
        return o

    def pending(self, name: str) -> dict:
        mine = [o.to_json() for o in self.offers.values()
                if o.status == "open" and o.maker == name]
        yours = [o.to_json() for o in self.offers.values()
                 if o.status == "open" and o.taker == name]
        return {"you_offered": mine, "offered_to_you": yours}

    def state(self, name: str) -> dict:
        t = self._trader(name)
        return {
            "you": name, "episode": self.episode, "of_episodes": self.episodes,
            "stage": self.stage,
            "capacity": {g: round(self.island.capacity[t.index][i], 4)
                         for i, g in enumerate(self.goods)},
            "taste": {g: round(self.island.alpha[t.index][i], 4)
                      for i, g in enumerate(self.goods)},
            "holdings": {g: round(t.holdings[i], 4)
                         for i, g in enumerate(self.goods)},
            "escrowed": {g: round(q, 4) for g, q in self._escrowed(name).items()},
            "labour_left": round(1.0 - t.spent, 4) if not t.produced_this_episode else 0.0,
            "utility_if_episode_ended_now": round(
                utility(self.island.alpha[t.index], t.holdings), 6),
            "traders": sorted(self.traders),
        }

    # --- clock ------------------------------------------------------------

    def open(self, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError(f"unknown stage {stage!r}")
        self.stage = stage

    def check_conservation(self) -> None:
        """Every unit ever made is held by somebody or has been eaten."""
        for g in range(self.island.n_goods):
            held = sum(t.holdings[g] for t in self.traders.values())
            if held < -_EPS:
                raise AssertionError(f"negative total of {self.goods[g]}")

    def close_episode(self) -> list[float]:
        """The bell. Order matters and is 004's, deliberately.

        Offers expire first so escrow returns -- goods in escrow are goods
        nobody can eat. Conservation is checked *before* consumption, while the
        books still balance. Only then is utility read and holdings zeroed.
        """
        self.open(SETTLEMENT)
        for o in self.offers.values():
            if o.status == "open":
                o.status = "expired"
                self.expired_at_bell += 1
        self.check_conservation()
        utils = []
        for name in sorted(self.traders, key=lambda n: self.traders[n].index):
            t = self.traders[name]
            utils.append(utility(self.island.alpha[t.index], t.holdings))
        self.episode_utilities.append(utils)
        for t in self.traders.values():
            for g in range(self.island.n_goods):
                self.consumed[g] += t.holdings[g]
                t.holdings[g] = 0.0
            t.spent = 0.0
            t.produced_this_episode = False
        self.episode += 1
        self.open(FLOOR)
        return utils
