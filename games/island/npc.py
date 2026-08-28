"""Cheap heuristic traders, and the schedule that switches between them.

An NPC exists for one reason: **a table that is one seat short does not have
to lapse.** Three seats are claimed and the fourth never comes, and today the
lobby waits out `TABLE_TTL` and posts `g7 lapsed: not full`. An NPC takes that
seat so the round is played. It is not a stand-in for an entrant and it is not
a scoreboard rival; it is the difference between a game and no game.

**Nothing here is privileged and nothing here is a second surface.** An NPC
enters through the same door a stranger's agent does -- it registers in the
lobby room, posts `JOIN`, waits for the invite, and then reads the board and
writes to it. The manager cannot tell it from an agent and is not told. All
this module holds is the *policy*: given what the board has said so far, what
line to write next. `run_npc.py` is the process that carries those lines.

## Why an NPC seat costs the table its ranking

An NPC declares itself on the board (`declaration`), and a game with one is
recorded as practice: kept, counted, never ranked. Three reasons, in order of
how much they matter.

1. **It is a different challenge.** `eff_round` against a heuristic is not
   `eff_round` against somebody's agent, and a scoreboard that mixed them
   would rank two different games as one -- the same defect
   `protocol.EPISODE_SECONDS_ALLOWED` exists to avoid.
2. **The mix is public and the schedule is not.** An NPC says which policies
   it draws from, so the table knows what it is sitting with; it does not say
   which one is live, because a trader announcing its next move is not playing
   the game the others are.
3. **A confession only ever weakens its own game.** `CLAUDE.md` says
   self-reports are non-authoritative and that is right about *claims of
   achievement*. This claim can only downgrade a round, never promote one, so
   believing it costs nothing: the worst a liar achieves is to unrank a game
   they were in.

## The three policies

Utility is Cobb-Douglas over the goods, `u = prod(x_g ** alpha_g)` with
`sum(alpha) == 1` -- the island's own, which is why `AUTARKY` can be written
down in closed form rather than searched for.

* **`autarky`** -- spends its whole labour budget on shares equal to its own
  taste weights, which is exactly optimal when nobody trades, and then trades
  with nobody. It is the floor every game so far has failed to beat, sitting
  at the table as a player rather than as a number in a report.
* **`greedy`** -- produces the autarky plan, approves any offer that raises
  its utility, and offers its most-abundant good for its scarcest at a markup
  over the rate that would leave it indifferent. Myopic and local: it never
  looks at a price, only at what it is holding.
* **`price-taker`** -- keeps a price vector, learned from the exchanges that
  have actually settled on the board and nothing else. It specialises
  production into the good with the highest `p*capacity`, buys towards the
  Cobb-Douglas demand bundle `alpha * wealth / p`, and approves what is at or
  better than its own prices.

## Switching policies, and the word for it

The live policy is redrawn from the mix at random intervals -- exponential
dwell times, seeded, so a round is reproducible from
`(mix, seed, mean_seconds)` alone. Redraws are **independent**, so repeats
happen and the marginal distribution over time is exactly the mix; a scheme
that avoided repeats would quietly make a 0.5 weight mean something else.

Gal called this changing the "arm", and the code does not, because `arm` is
already the ledger's word for a condition of the experiment (`"arm":
"sealed"` in `run_game.record`). Two meanings of one word inside one record is
how a scoreboard comes to be read wrong. Here it is a **policy**, and the
sequence of them is a `PolicySchedule`.
"""

from __future__ import annotations

import ast
import math
import random
import re
from dataclasses import dataclass, field

#: What a mix may name. Ordered, so a declaration reads the same every time.
POLICIES = ("autarky", "greedy", "price-taker")

#: Mean dwell time on one policy, in seconds. An episode is 60s by default, so
#: this is "about once an episode": long enough that a policy gets to finish
#: what it started, short enough that a round of eight episodes sees several.
SWITCH_MEAN_SECONDS = 60.0

#: What a mix defaults to when nobody says. Weighted towards `greedy` because
#: it is the only one of the three that both offers and accepts, so a table of
#: nothing but the other two can sit in silence for a whole round.
DEFAULT_MIX = {"autarky": 0.2, "greedy": 0.5, "price-taker": 0.3}

#: Kept out of `log` and every division: a trader holding nothing of a good has
#: infinite marginal utility for it under Cobb-Douglas, which is true and
#: unusable.
EPS = 1e-9


class BadMix(Exception):
    """A policy mix that does not name policies, or does not weigh them."""


def parse_mix(text: str) -> dict[str, float]:
    """`autarky=0.2,greedy=0.5,price-taker=0.3` -> normalised weights.

    Refused rather than repaired, the same rule the lobby and the manager
    hold: an unknown policy name is somebody expecting a player that does not
    exist, and quietly dropping it seats a different table than they asked
    for.
    """
    weights: dict[str, float] = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        name, sep, value = part.partition("=")
        name = name.strip()
        if not sep:
            raise BadMix(f"a mix wants policy=weight pairs, got {part!r}")
        if name not in POLICIES:
            raise BadMix(f"no such policy {name!r} -- "
                         f"{', '.join(POLICIES)}")
        try:
            weight = float(value)
        except ValueError:
            raise BadMix(f"{name}'s weight is not a number: {value!r}") from None
        if weight < 0:
            raise BadMix(f"{name}'s weight is negative")
        weights[name] = weights.get(name, 0.0) + weight
    total = sum(weights.values())
    if not weights or total <= 0:
        raise BadMix("a mix needs at least one policy with a positive weight")
    return {k: v / total for k, v in weights.items()}


def show_mix(mix: dict[str, float]) -> str:
    """A mix as it goes on the board -- in `POLICIES` order, so two NPCs
    drawing the same distribution say the same words for it."""
    return ", ".join(f"{p}={mix[p]:.3g}" for p in POLICIES if p in mix)


@dataclass
class PolicySchedule:
    """Which policy is live at a given moment, drawn once and reproducible.

    Segments are generated forward and kept, so `policy_at` is a pure function
    of the time asked about: asking about the same second twice cannot give two
    answers, and the trace written at the end is the schedule that was played
    rather than a re-draw of it.
    """

    mix: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_MIX))
    seed: int = 0
    mean_seconds: float = SWITCH_MEAN_SECONDS
    #: (elapsed seconds at which this segment starts, policy).
    segments: list[tuple[float, str]] = field(default_factory=list)
    _rng: random.Random = field(default=None, repr=False)  # type: ignore[assignment]
    _end: float = 0.0

    def __post_init__(self) -> None:
        if self.mean_seconds <= 0:
            raise BadMix("a dwell time has to be positive")
        self._rng = random.Random(self.seed)
        self.segments = []
        self._end = 0.0
        self._extend()

    def _extend(self) -> None:
        names = [p for p in POLICIES if p in self.mix]
        weights = [self.mix[p] for p in names]
        self.segments.append((self._end, self._rng.choices(names, weights)[0]))
        self._end += self._rng.expovariate(1.0 / self.mean_seconds)

    def policy_at(self, elapsed: float) -> str:
        """The policy live `elapsed` seconds into the round."""
        elapsed = max(0.0, elapsed)
        while self._end <= elapsed:
            self._extend()
        for start, policy in reversed(self.segments):
            if start <= elapsed:
                return policy
        return self.segments[0][1]

    def trace(self) -> list[dict]:
        """Every draw made so far, for the record written at the end. The
        authoritative account of what this seat played: the board carries the
        mix, and only this carries the order."""
        return [{"at": round(start, 3), "policy": policy}
                for start, policy in self.segments]


def declaration(name: str, mix: dict[str, float]) -> str:
    """What an NPC says on the board before it plays.

    Deliberately not a formatted message: the manager recognises PRODUCE,
    PROPOSE and APPROVE and this is none of them, so it is talk, which is what
    it is. What reads it afterwards is `npcs_on_board`.
    """
    return (f"NPC: {name} is a heuristic player, not an agent. It draws its "
            f"policy from {show_mix(mix)} and redraws at random intervals. "
            f"This game is therefore practice and is not ranked.")


#: The declaration as the record reads it back. Anchored, because a line
#: quoting somebody else's declaration is not itself one.
DECLARED = re.compile(r"^NPC: (\S+) is a heuristic player.*?"
                      r"policy from (.*?) and redraws", re.DOTALL)


def npcs_on_board(messages: list[dict]) -> dict[str, str]:
    """Seat name -> the mix it declared, for every NPC that spoke on a board.

    Read from the board rather than passed in from whoever launched the game,
    because the manager does not know who launched anybody -- and a game
    replayed from its board a year from now has to reach the same answer.
    """
    found: dict[str, str] = {}
    for msg in messages:
        body = msg.get("body")
        if not isinstance(body, str):
            continue
        m = DECLARED.match(body.strip())
        if m:
            found[m.group(1)] = m.group(2).strip()
    return found


# --- reading the board -----------------------------------------------------

#: `@T1 (scout-v2) You are T1. Your production capacity per unit of labour:
#: {'bread': 0.5, ...}. Your taste weights: {...}.` -- the dealer's own words,
#: in the clear for a practice game and whispered for a sealed one. Both are
#: parsed here, since the text is identical either way (`run_game.deal`).
_DEALT = re.compile(
    r"You are (T\d+)\..*?capacity per unit of labour: (\{[^}]*\})"
    r".*?taste weights: (\{[^}]*\})", re.DOTALL)
_EPISODE_OPEN = re.compile(r"^episode (\d+) of (\d+) is open")
_OVER = re.compile(r"^the round is over")
_ACK_WANTED = re.compile(r"Acknowledge with a line beginning ACK")
#: How the manager addresses a seat in the clear: `@T1 (scout-v2) ...`. It is
#: what tells one seat's dealt line from another's on a practice board, where
#: every seat's is posted where everyone can read it.
_ADDRESSED = re.compile(r"^@(T\d+) \(([^)]*)\)")
#: `Schedule for this round. 2 traders: T1, T2.`
_SEATS = re.compile(r"^Schedule for this round\. \d+ traders: ([^.]+)\.")
#: `p3: T1 offers {'iron': 0.4} to T2 for {'salt': 0.3} — open until the bell.`
_OFFER = re.compile(r"^(p\d+): (\S+) offers (\{[^}]*\}) to (\S+) for (\{[^}]*\})")
_SETTLED = re.compile(r"^(p\d+) settled: (\S+) and (\S+) exchanged "
                      r"(\{[^}]*\}) for (\{[^}]*\})")
#: `@T1 produced {'bread': 0.25}; 0.0 labour unspent`
_PRODUCED = re.compile(r"^@(T\d+) produced (\{[^}]*\}); ([0-9.]+) labour unspent")


def _bundle(raw: str) -> dict[str, float]:
    """A dict the manager rendered with `repr`, read back. `literal_eval`
    rather than `eval`, and a shape check after it, because this string
    arrived over a board anybody can write to."""
    try:
        value = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return {}
    if not isinstance(value, dict):
        return {}
    out = {}
    for good, qty in value.items():
        if isinstance(good, str) and isinstance(qty, (int, float)):
            out[good] = float(qty)
    return out


def private_half(text: str) -> tuple[str, dict[str, float], dict[str, float]] | None:
    """(seat, capacity, tastes) out of the dealer's line, or None."""
    m = _DEALT.search(text)
    if not m:
        return None
    cap, taste = _bundle(m.group(2)), _bundle(m.group(3))
    if not cap or not taste:
        return None
    return m.group(1), cap, taste


@dataclass
class Offer:
    pid: str
    maker: str
    taker: str
    give: dict[str, float]
    want: dict[str, float]


@dataclass
class Board:
    """What this seat believes, entirely from lines the manager wrote.

    Holdings are tracked rather than asked for: the manager posts a receipt
    for every production and every settlement, so a seat that reads the board
    knows what it holds without anybody having to add a query -- which would
    be a second surface.
    """

    #: The name this seat claimed in the lobby. How a practice board's
    #: `@T1 (scout-v2)` is told from `@T2 (someone-else)`.
    player: str = ""
    seat: str = ""
    capacity: dict[str, float] = field(default_factory=dict)
    tastes: dict[str, float] = field(default_factory=dict)
    holdings: dict[str, float] = field(default_factory=dict)
    labour_left: float = 1.0
    episode: int = 0
    episodes: int = 0
    episode_open: bool = False
    #: The schedule asked for an ACK, and this seat has not sent one yet.
    ack_wanted: bool = False
    acked: bool = False
    over: bool = False
    #: Open offers addressed to this seat, by proposal id.
    inbox: dict[str, Offer] = field(default_factory=dict)
    #: Offers this seat made that are still open, so it does not re-offer.
    outstanding: dict[str, Offer] = field(default_factory=dict)
    #: Every seat at this table, from the schedule the manager posts.
    seats: tuple[str, ...] = ()
    #: Exchange rates learned from settlements: good -> price, numeraire-free
    #: and only ever relative.
    prices: dict[str, float] = field(default_factory=dict)
    produced_this_episode: bool = False
    #: A PRODUCE or PROPOSE this seat has written and not yet seen settled.
    #: **Optimistic, and it has to be.** A receipt takes a poll or two to come
    #: back, and a seat that waits for one before deciding again writes the
    #: same line each time it looks -- which the manager settles, because
    #: labour may be committed in pieces. So the first real sealed round had
    #: one seat spend its budget three times over. The cost of assuming a post
    #: landed is an episode's production lost if it did not; the cost of
    #: assuming it did not is spending a budget several times, which is worse
    #: and is silent.
    posted_produce: bool = False
    posted_offer: bool = False

    @property
    def goods(self) -> tuple[str, ...]:
        return tuple(self.tastes)

    def partners(self) -> list[str]:
        """Everyone at the table but this seat."""
        return [s for s in self.seats if s != self.seat]

    def held(self, good: str) -> float:
        return self.holdings.get(good, 0.0)

    def committed(self, good: str) -> float:
        """What an open offer of this seat's has already promised away. The
        manager refuses a proposal that spends the same unit twice, and a
        refusal is a wasted line."""
        return sum(o.give.get(good, 0.0) for o in self.outstanding.values())

    def free(self, good: str) -> float:
        return max(0.0, self.held(good) - self.committed(good))

    def read(self, text: str, *, mine: bool = False) -> None:
        """One board line. `mine` for something sealed to this seat alone.

        Order-independent except for what the manager itself orders, which is
        everything that matters here.
        """
        line = text.strip()

        m = _SEATS.match(line)
        if m:
            self.seats = tuple(s.strip() for s in m.group(1).split(",")
                               if s.strip())

        dealt = private_half(line)
        if dealt:
            # A practice board carries every seat's half in the clear, so a
            # dealt line is only ours if the manager addressed it to our name.
            # A whisper carries no address and is ours by having arrived.
            at = _ADDRESSED.match(line)
            if mine or (at is not None and at.group(2) == self.player):
                self.seat, self.capacity, self.tastes = dealt
                self.holdings = {g: 0.0 for g in self.tastes}
            return

        if _ACK_WANTED.search(line):
            self.ack_wanted = True
            return

        m = _EPISODE_OPEN.match(line)
        if m:
            self.episode, self.episodes = int(m.group(1)), int(m.group(2))
            self.episode_open = True
            self.produced_this_episode = False
            self.posted_produce = self.posted_offer = False
            self.labour_left = 1.0
            # The bell eats everything held and returns the labour, so an
            # episode starts from nothing whatever the last one ended on.
            self.holdings = {g: 0.0 for g in self.tastes}
            self.inbox.clear()
            self.outstanding.clear()
            return

        if _OVER.match(line):
            self.over = True
            self.episode_open = False
            return

        m = _PRODUCED.match(line)
        if m:
            if m.group(1) == self.seat:
                for good, qty in _bundle(m.group(2)).items():
                    self.holdings[good] = self.held(good) + qty
                self.labour_left = float(m.group(3))
                self.produced_this_episode = True
            return

        m = _OFFER.match(line)
        if m:
            offer = Offer(pid=m.group(1), maker=m.group(2), taker=m.group(4),
                          give=_bundle(m.group(3)), want=_bundle(m.group(5)))
            if offer.taker == self.seat:
                self.inbox[offer.pid] = offer
            if offer.maker == self.seat:
                self.outstanding[offer.pid] = offer
            return

        m = _SETTLED.match(line)
        if m:
            pid = m.group(1)
            give, want = _bundle(m.group(4)), _bundle(m.group(5))
            maker, taker = m.group(2), m.group(3)
            if self.seat == maker:
                self._move(give, -1.0)
                self._move(want, +1.0)
            elif self.seat == taker:
                self._move(give, +1.0)
                self._move(want, -1.0)
            self.inbox.pop(pid, None)
            self.outstanding.pop(pid, None)
            self.learn_price(give, want)
            return

    def _move(self, bundle: dict[str, float], sign: float) -> None:
        for good, qty in bundle.items():
            self.holdings[good] = self.held(good) + sign * qty

    def learn_price(self, give: dict[str, float], want: dict[str, float]) -> None:
        """One settled exchange, as evidence about relative prices.

        Only single-good-for-single-good trades teach anything without an
        assumption, so only those are read. Everything the price-taker knows
        about prices comes from here -- from exchanges that actually settled,
        never from what anybody said they would pay.
        """
        if len(give) != 1 or len(want) != 1:
            return
        (a, qa), (b, qb) = next(iter(give.items())), next(iter(want.items()))
        if qa <= 0 or qb <= 0 or a == b:
            return
        implied = qa / qb  # units of a per unit of b -> p_b / p_a
        pa = self.prices.get(a, 1.0)
        # Half a step towards the observed ratio, so one odd trade does not
        # become the price and a run of them does.
        target = pa * implied
        self.prices[a] = pa
        self.prices[b] = math.sqrt(max(self.prices.get(b, target), EPS) * target)


# --- the policies ----------------------------------------------------------


def utility(tastes: dict[str, float], holdings: dict[str, float]) -> float:
    """Cobb-Douglas, in logs and shifted, so a zero holding is very bad rather
    than an exception. Only ever compared against itself."""
    return sum(a * math.log(max(holdings.get(g, 0.0), EPS))
               for g, a in tastes.items())


def _after(holdings: dict[str, float], give: dict[str, float],
           want: dict[str, float]) -> dict[str, float]:
    out = dict(holdings)
    for good, qty in want.items():
        out[good] = out.get(good, 0.0) + qty
    for good, qty in give.items():
        out[good] = out.get(good, 0.0) - qty
    return out


def budgeted(shares: dict[str, float]) -> dict[str, float]:
    """Shares rounded to what a board can carry, and still inside the budget.

    **Rounding each share on its own can break the budget**, and the manager
    refuses the whole line when it does: tastes of 0.136, 0.8595 and 0.0046
    sum to exactly 1 and their rounded forms sum to 1.0001, which is over by
    1e-4 and therefore not a production plan. That is not a hypothetical --
    it is what one seat wrote every poll for a whole round, collecting fifteen
    refusals and ending at zero utility while its partner, whose shares
    happened to round down, played normally.

    So the excess comes off the largest share, which is the one it changes
    least, and a share that rounds to nothing is dropped rather than written.
    """
    plan = {g: round(a, 4) for g, a in shares.items() if a > 0}
    plan = {g: v for g, v in plan.items() if v > 0}
    excess = round(sum(plan.values()) - 1.0, 6)
    if plan and excess > 0:
        largest = max(plan, key=lambda g: plan[g])
        plan[largest] = round(plan[largest] - excess, 4)
        if plan[largest] <= 0:
            del plan[largest]
    return plan


def autarky_plan(board: Board) -> dict[str, float]:
    """Shares equal to tastes -- the closed-form optimum for a trader who will
    not trade, under `sum(alpha) == 1` and linear production."""
    return budgeted(board.tastes)


def _prices(board: Board) -> dict[str, float]:
    """This seat's prices, with anything it has not seen traded at 1.0. A
    price-taker with no market to read is a trader who thinks everything is
    worth the same, which is the honest thing for it to believe."""
    return {g: max(board.prices.get(g, 1.0), EPS) for g in board.goods}


def specialise_plan(board: Board) -> dict[str, float]:
    """All the labour into whatever earns most at current prices.

    Full specialisation is what linear production and a fixed labour budget
    imply: revenue is linear in every share, so the maximum sits on a corner.
    That is the whole of the case for trading at all, and this is the policy
    that acts on it.
    """
    prices = _prices(board)
    if not board.capacity:
        return {}
    best = max(board.capacity, key=lambda g: prices.get(g, 1.0) * board.capacity[g])
    return budgeted({best: 1.0})


def demand(board: Board) -> dict[str, float]:
    """The Cobb-Douglas bundle this seat would buy at its own prices."""
    prices = _prices(board)
    wealth = sum(prices[g] * board.held(g) for g in board.goods)
    return {g: board.tastes.get(g, 0.0) * wealth / prices[g] for g in board.goods}


def plan_for(policy: str, board: Board) -> dict[str, float]:
    """What this policy writes on a PRODUCE line, or `{}` for nothing."""
    if not board.tastes or not board.capacity:
        return {}
    if policy == "price-taker":
        return specialise_plan(board)
    return autarky_plan(board)


def approve(policy: str, board: Board, offer: Offer) -> bool:
    """Whether to take an offer addressed to this seat.

    Every policy checks it can afford the offer first: the manager refuses one
    it cannot, and an NPC that spends the round collecting refusals is noise on
    somebody else's board.
    """
    if any(board.free(g) + 1e-9 < q for g, q in offer.want.items()):
        return False
    if policy == "autarky":
        return False
    after = _after(board.holdings, offer.want, offer.give)
    better = utility(board.tastes, after) > utility(board.tastes, board.holdings)
    if policy == "greedy":
        return better
    # price-taker: at or better than its own prices, *and* an improvement --
    # a trade that is cheap and useless is still useless.
    prices = _prices(board)
    paid = sum(prices[g] * q for g, q in offer.want.items() if g in prices)
    got = sum(prices[g] * q for g, q in offer.give.items() if g in prices)
    return better and got + 1e-9 >= paid


def propose(policy: str, board: Board, partners: list[str],
            markup: float = 1.25) -> tuple[str, dict[str, float], dict[str, float]] | None:
    """(partner, give, want), or None if this policy has nothing to offer.

    One good for one good, always. Bundles are legal and a heuristic that
    builds them is a heuristic nobody can read off a board afterwards, which
    matters more here than the extra gains from trade would.
    """
    if policy == "autarky" or not partners or not board.tastes:
        return None
    goods = [g for g in board.goods if board.tastes.get(g, 0.0) > 0]
    if len(goods) < 2:
        return None

    if policy == "greedy":
        # Most abundant relative to how much it is wanted, for the least.
        def surplus(g: str) -> float:
            return board.free(g) / max(board.tastes.get(g, EPS), EPS)
        give_good = max(goods, key=surplus)
        want_good = min(goods, key=surplus)
        if give_good == want_good or board.free(give_good) <= EPS:
            return None
        qty = 0.25 * board.free(give_good)
        # The rate that would leave it exactly indifferent, then a markup: it
        # is asking, so it may as well ask for more than nothing.
        x_g = max(board.held(give_good), EPS)
        x_w = max(board.held(want_good), EPS)
        a_g = max(board.tastes.get(give_good, EPS), EPS)
        a_w = max(board.tastes.get(want_good, EPS), EPS)
        breakeven = qty * (a_g / x_g) * (x_w / a_w)
        ask = breakeven * markup
    else:
        prices = _prices(board)
        target = demand(board)
        excess = {g: board.free(g) - target.get(g, 0.0) for g in goods}
        give_good = max(goods, key=lambda g: excess[g])
        want_good = min(goods, key=lambda g: excess[g])
        if give_good == want_good or excess[give_good] <= EPS:
            return None
        qty = min(excess[give_good],
                  max(0.0, -excess[want_good]) * prices[want_good] / prices[give_good])
        qty = min(qty, board.free(give_good))
        if qty <= EPS:
            return None
        ask = qty * prices[give_good] / prices[want_good]

    if qty <= EPS or ask <= EPS:
        return None
    partner = partners[0] if len(partners) == 1 else random.choice(partners)
    return partner, {give_good: round(qty, 4)}, {want_good: round(ask, 4)}


def _num(x: float) -> str:
    """A quantity as the manager's own regexes will read it back.

    Fixed point, never exponent: `PRODUCE` and `PROPOSE` both parse digits and
    at most one dot, so a share of `1e-05` is a malformed line rather than a
    small one -- and the manager does not repair.
    """
    text = f"{x:.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def wrote(board: Board, line: str) -> None:
    """Record that a line went to the board, so it is not written twice.

    Called by whatever carries the line, because only that knows it was
    actually posted. See `Board.posted_produce` for why this is optimistic.
    """
    if line.startswith("PRODUCE"):
        board.posted_produce = True
    elif line.startswith("PROPOSE"):
        board.posted_offer = True


def lines(policy: str, board: Board, partners: list[str]) -> list[str]:
    """Everything this policy would write right now, in order, as board text.

    The whole of an NPC's decision-making is this function. It returns text
    because text is the only thing an NPC ever produces -- there is no action
    it can take that is not a line somebody could have typed.
    """
    out: list[str] = []
    if board.over or not board.episode_open or not board.tastes:
        return out

    if not (board.produced_this_episode or board.posted_produce):
        plan = plan_for(policy, board)
        if plan:
            out.append("PRODUCE " + " ".join(f"{g}={_num(s)}"
                                              for g, s in plan.items()))
            return out  # one line at a time; the receipt is what says it landed

    for pid, offer in sorted(board.inbox.items()):
        if approve(policy, board, offer):
            out.append(f"APPROVE {pid}")
            return out

    if not board.outstanding and not board.posted_offer:
        made = propose(policy, board, partners)
        if made:
            partner, give, want = made
            out.append("PROPOSE to={} give={} want={}".format(
                partner,
                ",".join(f"{g}:{_num(q)}" for g, q in give.items()),
                ",".join(f"{g}:{_num(q)}" for g, q in want.items())))
    return out
