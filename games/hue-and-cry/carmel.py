"""Carmel Taldiego: where she goes, what she takes, and what she says about it.

She is an NPC in her own process, and `games/hue-and-cry.md` is explicit
about why that matters: *"With a person or an agent playing Carmel,
ticks-to-arrest confounds how good the searchers were with how good she was;
against a fixed, stated policy it does not. The adversary held constant is
the control the 008 measurement needs."*

**So this file is the statement of that policy.** Every choice she makes is
a pure function of what she can see, with the reasoning next to it, and none
of it reads anything a searcher could not also read.

    python3 games/hue-and-cry/carmel.py            # watch a chase
    python3 games/hue-and-cry/carmel.py --calibrate

WHAT SHE DECIDES, WHICH IS THREE THINGS
=======================================

Per move, and no more than this:

1. **Where to go**, out of the exits her current landmark has.
2. **Whether to stand still and steal**, which is the only way she is ever
   catchable and the only way she ever wins.
3. **Which true hint to post** about where she has gone.

She posts `CLUE <hint> <workspace>` in the room she is **leaving** -- the
hint is the indirect route for everyone, the workspace token is the direct
one for whoever is standing where she stood. Both are in the grammar and
neither is optional: she may not move silently.

WHAT THIS FILE IS NOT
=====================

**It is not the runtime and it must not be lifted into one.** `chase()`
advances a virtual clock and calls both sides in order, which is exactly the
shape CLAUDE.md says has been accidentally built twice in this lab. It is
here for the same reason `gazetteer.py` simulates drawn maps: to put a
number on a design parameter before anybody pays for a real game. The real
Carmel is a long-lived process that reads a board and writes to it on her
own clock, and there is no bell.

THE NUMBERS BELOW ARE GUESSES AND ARE MARKED AS SUCH
====================================================

`games/hue-and-cry.md` says of her win condition: *"What is not settled
here: the values, the threshold, and whether the threshold is fixed or
scales with how many are hunting. Those are numbers to calibrate against a
played game, not decisions to invent now."* `--calibrate` is the beginning
of that, against a reference searcher rather than a played game, which is
weaker and is the most that exists.
"""

import argparse
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import treasures as T  # noqa: E402
from descriptors import NEIGHBOURHOOD, all_descriptors  # noqa: E402
from gazetteer import EXITS, kinship  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402
from secret_matrix import _prf, hints_for, token_for  # noqa: E402

EXIT_INFO = b"hue-and-cry/v1/exits"

#: How fast she travels, in km/h, averaged over everything -- the flight, the
#: waiting, the bus at the other end. A GUESS, and the one that decides
#: whether geography matters at all: at 800 the map is a day wide and
#: distance is noise, at 80 a hop is a week and nothing else matters. 400 is
#: chosen so that the median hop (about 4,200 km at the committed exit band)
#: costs about ten hours -- the same order as the longest theft, so the two
#: costs trade against each other instead of one dominating.
TRAVEL_KMH = 400

#: What she needs to win. ONE NUMBER, and the correction that made it one is
#: the whole shape of the game.
#:
#: This was a table keyed by how many searchers were hunting, calibrated so
#: each size came out near even. Gal, 2026-09-09: *"You don't know who
#: chases you. She does not know who chases her."* A threshold that reads
#: the size of the field is a threshold nobody at the table can compute --
#: she cannot, because she never learns who came; and it cannot be set at
#: setup either, because **the field is not closed at setup**. She opens a
#: campaign, posts a notice, and whoever wants to join joins, whenever they
#: like.
#:
#: So the number is fixed and the turnout is the weather. She is not playing
#: a balanced match against a known field; she is stealing until somebody
#: arrives. 140 is what a chase against a single searcher comes out even at,
#: which makes a solo hunt a contest and a crowd a hard game -- and that
#: asymmetry is now a property of the design rather than a bug in it.
REPUTATION_TO_WIN = 140

#: The lobby is a public room whose key is published -- the island's shape
#: (`games/island/lobby.py`) and for its reason: a room nobody can find is
#: not an announcement. Its name is fixed and salt-free, because a lobby
#: that moved with the game salt could not be found by anybody who was not
#: already playing.
LOBBY = "hue-and-cry"

#: How long people take to notice the notice and set off. A GUESS, and the
#: parameter that decides how much of a head start she gets: nobody is
#: hunting her until somebody reads the lobby.
JOIN_WINDOW_HOURS = 12

#: What a theft costs her, as a multiplier on the hours. 1.0 is the
#: treasure's own dwell.
#:
#: Gal, 2026-09-09: *"We could take her time values and use them with a
#: factor for difficulty so we can balance the next game based on recent
#: ones."* It is the right knob -- her dwell is the only thing that closes
#: the gap, so scaling it scales the whole contest, and it does so without
#: touching the map, the treasures or what anything is worth.
#:
#: **A campaign run at a factor other than 1.0 is not comparable to one run
#: at 1.0, and must not be pooled with it.** See `next_difficulty` for why
#: that is a rule and not a caution.
DIFFICULTY = 1.0


def travel_hours(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(
        math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    km = 6371 * 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    return km / TRAVEL_KMH


class Map:
    """The gazetteer as one game sees it: exits drawn from the seed, and the
    treasures and descriptors that were fixed before it started."""

    def __init__(self, seed: bytes):
        self.seed = seed
        self.places = {p["name"]: p for p in load_landmarks()}
        self.descriptors = {k: sorted(v) for k, v in all_descriptors().items()}
        self.treasure = {t["landmark"]: t for t in T.build()}
        self._near: dict[str, list[str]] = {}
        self._exits: dict[str, list[str]] = {}

    def band(self, landmark: str) -> list[str]:
        """The look-alikes a game draws exits from. Computed once and kept:
        it is O(places) per landmark and the chase asks repeatedly."""
        if landmark not in self._near:
            gaz = self.descriptors
            self._near[landmark] = [
                x for _, x in sorted((-kinship(landmark, x, gaz), x)
                                     for x in gaz if x != landmark)
            ][:NEIGHBOURHOOD]
        return self._near[landmark]

    def exits(self, landmark: str) -> list[str]:
        """Her five, drawn from the seed. Public knowledge in principle --
        the gazetteer and the band rule are both published -- so a searcher
        who works out where she is can work out where she may go."""
        if landmark not in self._exits:
            pool = self.band(landmark)
            out: list[str] = []
            i = 0
            while len(out) < EXITS and i < 400:
                digest = _prf(self.seed, EXIT_INFO, landmark, i)
                pick = pool[int.from_bytes(digest[:8], "big") % len(pool)]
                if pick not in out:
                    out.append(pick)
                i += 1
            self._exits[landmark] = out
        return self._exits[landmark]

    def live_hints(self, landmark: str) -> list[str]:
        """The three descriptors the seed makes postable at this landmark."""
        words = self.descriptors[landmark]
        return [words[i] for i in
                hints_for(self.seed, landmark, len(words))]


class Carmel:
    """A fixed, stated policy. Held constant so a searcher's score means
    something."""

    def __init__(self, world: Map, start: str, difficulty: float = DIFFICULTY):
        self.world = world
        self.at = start
        self.reputation = 0
        self.emptied: set[str] = set()
        self.clock = 0.0
        #: Scales what standing still costs her. She does not know it and
        #: cannot: it is set from campaigns she has already lost or won, and
        #: nothing she can read says what it is.
        self.difficulty = difficulty

    # --- 1. where to go ---------------------------------------------------
    def choose_destination(self) -> str:
        """Worth going to, and describable once she gets there.

        Two things pull. A rich room is the point -- she wins on reputation
        and nothing else -- but the hint she will have to post about it is
        drawn from that room's descriptors, and a room whose live three are
        shared with none of her other exits announces her.

        So she scores a destination by what it pays and by the cover it will
        buy, and takes the best. She does NOT take the richest: the richest
        rooms are systematically the most exposed (`treasures.py`,
        `correlation(cover, reputation) = -0.28`), so a value-only Carmel
        walks into the most legible room on the map every time, which is
        the failure `--calibrate` shows as a low catch time.
        """
        reachable = self.world.exits(self.at)
        best, best_score = reachable[0], -1.0
        for destination in reachable:
            if destination in self.emptied:
                continue
            pay = self.world.treasure[destination]["reputation"]
            cover = self.best_cover(destination, reachable)
            score = pay * cover
            if score > best_score:
                best, best_score = destination, score
        return best

    def best_cover(self, destination: str, reachable: list[str]) -> int:
        """How many of her exits the most ambiguous live hint covers.

        This is the quantity the whole descriptor layer was built to keep
        above one, measured here from her side rather than over drawn maps.
        """
        gaz = self.world.descriptors
        return max(len([x for x in reachable if word in gaz[x]])
                   for word in self.world.live_hints(destination))

    # --- 2. what to say ---------------------------------------------------
    def choose_hint(self, destination: str) -> str:
        """The least informative true thing she can say about where she went.

        `games/hue-and-cry.md`: *"the Fugitive's strategy is now sharp and
        stateable: post the least informative true fact, which is a real
        optimisation against a real posterior."* Least informative means
        covering the most of the set a reader can narrow her to, which is
        her reachable set -- not the whole map, which is the mistake the
        gate itself made twice.
        """
        gaz = self.world.descriptors
        reachable = self.world.exits(self.at)
        return max(self.world.live_hints(destination),
                   key=lambda w: (len([x for x in reachable if w in gaz[x]]), w))

    # --- 3. whether to stand still ----------------------------------------
    def will_steal(self, destination: str, seen: bool) -> bool:
        """Standing still is the only way she is caught and the only way she
        wins, so the rule is short: steal unless somebody showed themselves.

        Being seen aborts the theft by the settled definition -- a searcher
        posted in that room -- and she does not re-attempt a room she has
        emptied. There is no cleverness here on purpose: a Carmel who
        skipped cheap thefts to stay safe would win more slowly and be
        harder to hold constant, and holding her constant is her whole job.
        """
        return not seen and destination not in self.emptied

    def take(self, destination: str) -> float:
        prize = self.world.treasure[destination]
        self.emptied.add(destination)
        self.reputation += prize["reputation"]
        return prize["dwell"] * self.difficulty


class Searcher:
    """The reference searcher: run to the last place she was seen, then
    follow the trail room by room.

    Deliberately the simplest thing that uses the mechanism. The hash beside
    the hint is the exact address, so a searcher standing where she stood
    needs no deduction at all -- it never reads a hint, never reasons about
    a descriptor, and never cooperates. It is a floor for the searchers'
    score, not a good player, and every cleverer thing has to beat it.

    It is always behind, and by exactly how much is the whole game: it loses
    her travel time on every hop and gains only what she spends standing
    still.
    """

    def __init__(self, world: Map, start: str):
        self.world = world
        self.at = start
        self.clock = 0.0

    def next_room(self, trail: dict) -> str | None:
        """`trail` is what a room's board says: where she went from here.

        Read only from the room it is standing in, because that is the only
        place it can be read. Nothing is broadcast.
        """
        return trail.get(self.at)


#: What the controller aims at, and the widest it may move. The target is a
#: guess; the bounds are a safety rail.
TARGET_WIN_RATE = 0.5
DIFFICULTY_BOUNDS = (0.4, 3.0)

#: How hard it corrects, and over how many campaigns. MEASURED, and the
#: measurement makes the point this whole function is fenced with.
#:
#: Swept over 120 campaigns at three searchers, discarding the first third:
#:
#:     gain  window   win rate   mean factor   factor swing
#:     1.20      10       51%        0.85           0.27
#:     1.20      20       51%        1.19           0.55
#:     1.10      20       51%        0.94           0.18
#:     1.05      20       44%        0.94           0.15
#:     1.02      20       48%        0.91           0.03   <- here
#:     1.02      40       52%        0.91           0.04
#:
#: **Every row hits the target.** A controller aimed at 50% produces 50%
#: whatever its gain, which is what a controller is for and is exactly why
#: the win rate cannot be read as a result: it is the same number for a
#: well-damped loop and for one swinging between 0.4 and 1.5. The column
#: that discriminates is the factor, and the factor is therefore the only
#: thing here worth reporting.
DIFFICULTY_GAIN = 1.02
DIFFICULTY_WINDOW = 20


def next_difficulty(recent: list[bool], current: float = DIFFICULTY,
                    target: float = TARGET_WIN_RATE) -> float:
    """The factor for the next campaign, from how the last few went.

    `recent` is oldest-first, one boolean per finished campaign: did she
    win. Above target she gets slower thefts, below it faster ones, by a
    proportional step that is bounded at both ends -- a controller that can
    reach any factor can make the game trivially easy or unwinnable, and the
    numbers either side of that would still be recorded as results.

    WHAT THIS COSTS, AND IT IS NOT SMALL
    ------------------------------------

    **An adaptive difficulty erases the thing the experiment measures.**
    Suppose the searchers get better -- new tools, better coordination, a
    real note-reading policy instead of a trail-walker. Their win rate goes
    up, the controller lowers the difficulty, and the win rate comes back to
    50%. *The improvement is absorbed and the metric never moves.* A
    controller holding an outcome constant is indistinguishable from a field
    that never improved, and this lab already has that result written down
    in a different costume: 001's timing predictor became well calibrated
    and bought no completion time at all.

    So:

    - **A ranked campaign runs at a fixed, published factor.** Adaptive
      difficulty is for play, not for measurement, and a game whose factor
      moved during or between the campaigns being compared is kept and
      counted and **never ranked**, which is CLAUDE.md's rule for the weaker
      thing verbatim.
    - **The factor is part of the level key**, recorded with every campaign
      beside the branching factor and the exit count, so a pooled result can
      be split by it afterwards rather than discovered to be unsplittable.
    - **What the controller produces is a difficulty curve, and that is the
      finding it can honestly support** -- how much slower she has to be
      made, over time, to stay at 50%. That number moves when the field
      improves, which is exactly what the win rate stops doing. The sweep
      under `DIFFICULTY_GAIN` shows this is not a worry but an arithmetic
      fact: four settings, four win rates within a point of each other, and
      factor swings differing by twentyfold.

    There is no ledger here yet. This is a pure function of outcomes somebody
    else keeps, deliberately: where campaign records live is a decision about
    the manager, and the manager is not built.
    """
    if not recent:
        return current
    recent = recent[-DIFFICULTY_WINDOW:]
    rate = sum(recent) / len(recent)
    lo, hi = DIFFICULTY_BOUNDS
    factor = current * (DIFFICULTY_GAIN ** ((rate - target) / max(target, 1e-9)))
    return round(min(hi, max(lo, factor)), 3)


def open_campaign(seed: bytes, start: str) -> str:
    """The notice she posts in the lobby when she starts stealing.

    Gal, 2026-09-09: *"she would start a new campaign for stealing things.
    Then once she goes to the first room, she also posts a note in some
    lobby. And then whoever wants to join the hunt, just join the hunt."*

    Two things follow, and they are the reason this function exists at all
    rather than the game simply beginning.

    **She starts it.** Nobody convenes a match. A campaign is a thing she
    does, and the field assembles around it or does not.

    **Joining is not a move.** There is no `JOIN` line and nothing to
    approve, because "knowing a landmark's name is what admits you" and this
    game has no permission model to ask. The notice carries the room she is
    starting from; going there is the whole of joining. That is a smaller
    lobby than the island's, which settles `OPEN`, `JOIN` and `MANAGE` --
    here only the first is a line, and the other two are somebody walking in.

    The address is the opening landmark's, not her current one. She posts it
    on the way out, so by the time anybody reads it she has gone -- which is
    the same one-room head start the trail gives everybody afterwards, and
    the reason the game is findable at all: with a thousand rooms and nothing
    broadcast, a searcher with no lead never finds her.
    """
    return f"OPEN {token_for(seed, start)}"


def itinerary(seed: bytes, start: str, world: Map,
              limit: int = 40, difficulty: float = DIFFICULTY) -> list[dict]:
    """Where she goes and how long she stands still, ignoring the searchers.

    She can be simulated on her own because **the reference searcher never
    gets ahead of her**. It follows the trail, and the trail only exists
    behind her, so it can never be in a room before she arrives -- which is
    the one thing that would change her behaviour (`will_steal`, seen). A
    searcher that guessed ahead would break this and would need the two
    simulated together; that is a reason to keep `seen` in her policy, not a
    reason to model it here.
    """
    her = Carmel(world, start, difficulty)
    out = []
    for _ in range(limit):
        destination = her.choose_destination()
        hint = her.choose_hint(destination)
        leaves_from = her.at
        her.clock += travel_hours(world.places[her.at],
                                  world.places[destination])
        her.at = destination
        arrived = her.clock
        dwell = her.take(destination) if her.will_steal(destination, False) \
            else 0
        her.clock += dwell
        out.append({"from": leaves_from, "to": destination, "hint": hint,
                    "arrived": arrived, "leaves": arrived + dwell,
                    "dwell": dwell, "reputation": her.reputation})
    return out


def pursue(world: Map, start: str, home: str, trail: list[dict],
           joined_at: float = 0.0) -> tuple[int | None, float]:
    """Run one searcher along the trail. Returns (move it catches her on,
    the lag it settles at).

    The arithmetic that decides the game, and it is short -- and it is the
    opposite of what this docstring said first, which was that the gap never
    changes. It changes constantly, in one direction:

        gap at her room i  =  initial lag  -  everything she has stolen so far

    A searcher walks the same legs she does, so their travel cancels exactly.
    **The only asymmetry is that she stands still and it does not.** So every
    theft she makes hands the follower precisely the hours she spent on it,
    and it catches her on the first room where her cumulative dwell has eaten
    the head start she began with.

    Which turns her win condition into a budget rather than a race: she has
    `initial lag` hours of standing still in her, total, and has to be worth
    `REPUTATION_TO_WIN` before she spends them.
    """
    clock = joined_at + travel_hours(world.places[home], world.places[start])
    lag = clock  # she left `start` at t=0
    for i, leg in enumerate(trail):
        # It is standing where she stood, so it reads the address and goes.
        clock += travel_hours(world.places[leg["from"]],
                              world.places[leg["to"]])
        if leg["arrived"] < clock <= leg["leaves"]:
            return i, lag
    return None, lag


def chase(seed: bytes, start: str, searchers: int = 2,
          limit: int = 40, world: Map | None = None,
          threshold: int = REPUTATION_TO_WIN,
          join_window: float = JOIN_WINDOW_HOURS,
          difficulty: float = DIFFICULTY) -> dict:
    """One game. NOT THE RUNTIME -- see the module head.

    Two rules that look like one and are not, both from
    `games/hue-and-cry.md`:

    - **Being seen aborts the theft.** When she arrives she reads the board;
      if a searcher has posted there she does not start, and leaves at once,
      so she is not standing there to be caught.
    - **The catch is walking in while she is still there.** She is only
      still there while she is stealing. *The dwell is the window and there
      is no other.*
    """
    world = world or Map(seed)
    trail = itinerary(seed, start, world, limit, difficulty)

    names = sorted(world.descriptors)
    caught_on, lags = None, []
    for i in range(searchers):
        digest = _prf(seed, b"hue-and-cry/v1/searcher-start", str(i), 0)
        home = names[int.from_bytes(digest[:8], "big") % len(names)]
        # When this one read the lobby and set off. Nobody is dispatched;
        # they arrive at the notice on their own time, which is why her head
        # start is not a property of the field's size.
        joined = join_window * (
            int.from_bytes(digest[8:16], "big") / 2 ** 64)
        move, lag = pursue(world, start, home, trail, joined_at=joined)
        lags.append(lag)
        if move is not None and (caught_on is None or move < caught_on):
            caught_on = move

    hit = next((i for i, leg in enumerate(trail)
                if leg["reputation"] >= threshold), None)
    if caught_on is not None and (hit is None or caught_on <= hit):
        end = trail[caught_on]
        return {"outcome": "caught", "moves": trail[:caught_on + 1],
                "lags": lags, "reputation": trail[caught_on - 1]["reputation"]
                if caught_on else 0, "hours": end["arrived"]}
    if hit is not None:
        return {"outcome": "she wins", "moves": trail[:hit + 1], "lags": lags,
                "reputation": trail[hit]["reputation"],
                "hours": trail[hit]["leaves"]}
    return {"outcome": "unfinished", "moves": trail, "lags": lags,
            "reputation": trail[-1]["reputation"], "hours": trail[-1]["leaves"]}


def _run(world: Map, seed: bytes, names: list[str], searchers: int,
         join_window: float = JOIN_WINDOW_HOURS) -> dict:
    w = Map(seed)
    w.descriptors, w.places, w.treasure = (
        world.descriptors, world.places, world.treasure)
    start = names[int.from_bytes(seed[:4], "big") % len(names)]
    return chase(seed, start, searchers=searchers, world=w,
                 threshold=10 ** 9, limit=40, join_window=join_window)


def main() -> None:
    import os

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--calibrate", action="store_true",
                    help="what REPUTATION_TO_WIN makes it a contest")
    ap.add_argument("--seed", help="64 hex characters; random if omitted")
    args = ap.parse_args()
    seed = bytes.fromhex(args.seed) if args.seed else os.urandom(32)

    world = Map(seed)
    if args.calibrate:
        calibrate(world)
        return

    result = chase(seed, "Stonehenge", world=world)
    print(f"seed {seed.hex()[:16]}...  starting at Stonehenge\n")
    for i, m in enumerate(result["moves"][:12], 1):
        print(f"  {i:2}. +{m['arrived']:6.1f}h  she is somewhere"
              f" {m['hint'].replace('_', ' ')}")
        print(f"          {f'stood {m[chr(39) + chr(39)]}h and took it' if False else ''}"
              f"{'took it, ' + str(m['dwell']) + 'h' if m['dwell'] else 'moved straight on'}"
              f"   reputation {m['reputation']}")
    print(f"\n  {result['outcome']} after {result['hours']:.0f} hours"
          f" with {result['reputation']} reputation")


def calibrate(world: Map, trials: int = 60) -> None:
    """What a fixed threshold means when the field is not fixed.

    The previous version of this asked what threshold balanced a chase
    against N searchers, and answered with a table keyed by N. That question
    is not available any more: she never learns who came, and the field is
    not closed when she opens the campaign. So the number is fixed and the
    turnout is weather -- what is worth measuring is how hard the weather
    makes it, and what she is actually buying with the hours before anybody
    reads the lobby.
    """
    names = sorted(world.descriptors)
    seeds = [os.urandom(32) for _ in range(trials)]

    print(f"{trials} campaigns per row, travel {TRAVEL_KMH} km/h,"
          f" threshold {REPUTATION_TO_WIN}\n")
    print("  She opens a campaign and whoever turns up, turns up. She never"
          " learns how many.\n")
    print(f"  {'turnout':>8}{'her budget':>12}{'she reaches':>13}"
          f"{'she wins':>10}")
    for n in (1, 2, 3, 5, 10):
        rs = [_run(world, sd, names, searchers=n) for sd in seeds]
        budget = sorted(min(r["lags"]) for r in rs if r["lags"])
        got = sorted(r["moves"][-1]["reputation"] for r in rs if r["moves"])
        wins = sum(1 for r in rs if _wins(r, REPUTATION_TO_WIN))
        print(f"  {n:>8}{budget[len(budget) // 2]:>10.0f}h"
              f"{got[len(got) // 2]:>13,.0f}{wins / trials:>10.0%}")
    print("\n  A fixed threshold cannot be fair to every turnout, and that is"
          " now a property\n  of the design rather than a number to tune: she"
          " is not playing a balanced\n  match against a known field, she is"
          " stealing until somebody arrives.\n")

    print("  What the lobby's latency buys her -- the hours before anybody"
          " has read the\n  notice are hours nobody is behind her at all,"
          " and it is the only lever\n  that does not require changing what"
          " a theft is worth:\n")
    print(f"  {'join window':>13}{'her budget':>12}{'she reaches':>13}"
          f"{'she wins':>10}")
    for window in (0, 6, 12, 24, 48):
        rs = [_run(world, sd, names, searchers=3, join_window=window)
              for sd in seeds]
        budget = sorted(min(r["lags"]) for r in rs if r["lags"])
        got = sorted(r["moves"][-1]["reputation"] for r in rs if r["moves"])
        wins = sum(1 for r in rs if _wins(r, REPUTATION_TO_WIN))
        print(f"  {window:>11}h{budget[len(budget) // 2]:>10.0f}h"
              f"{got[len(got) // 2]:>13,.0f}{wins / trials:>10.0%}")
    print("\n  Three searchers throughout. Everything above is measured"
          " against the reference\n  searcher, which follows the exact"
          " address in each room and never reads a hint,\n  never cooperates"
          " and never guesses ahead. It is a floor, and a real searcher\n"
          "  moves every number here.\n")


def _wins(result: dict, threshold: int) -> bool:
    hit = next((m for m in result["moves"]
                if m["reputation"] >= threshold), None)
    if hit is None:
        return False
    if result["outcome"] != "caught":
        return True
    return hit["leaves"] <= result["hours"]


if __name__ == "__main__":
    main()
