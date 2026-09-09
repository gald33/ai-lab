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
from secret_matrix import _prf, hints_for  # noqa: E402

EXIT_INFO = b"hue-and-cry/v1/exits"

#: How fast she travels, in km/h, averaged over everything -- the flight, the
#: waiting, the bus at the other end. A GUESS, and the one that decides
#: whether geography matters at all: at 800 the map is a day wide and
#: distance is noise, at 80 a hop is a week and nothing else matters. 400 is
#: chosen so that the median hop (about 4,200 km at the committed exit band)
#: costs about ten hours -- the same order as the longest theft, so the two
#: costs trade against each other instead of one dominating.
TRAVEL_KMH = 400

#: What she needs to win, per searcher hunting her. MEASURED rather than
#: guessed -- the first version of this file carried a flat 600, which
#: `--calibrate` showed she reaches in none of sixty chases against two
#: searchers. She is caught at a median of 162.
#:
#: `games/hue-and-cry.md` left it open "whether the threshold is fixed or
#: scales with how many are hunting". It cannot be fixed. Her whole budget
#: is the NEARER searcher's head start, so it falls as hunters are added:
#:
#:     searchers   her budget   she reaches
#:         1          19h          229
#:         2          11h          162
#:         3           8h          134
#:         5           6h          101
#:
#: These sit at about 60% of what she reaches, which is where a chase comes
#: out near even against the reference searcher. That searcher is a FLOOR --
#: it never reads a hint and never cooperates -- so a real one moves every
#: number here, and these are a starting point for a played game rather than
#: an answer to it.
REPUTATION_TO_WIN = {1: 140, 2: 100, 3: 80, 5: 60}


def reputation_to_win(searchers: int) -> int:
    """Interpolated for sizes the sweep did not run, and clamped at both
    ends rather than extrapolated: the curve is measured over 1..5 and says
    nothing about 20."""
    table = REPUTATION_TO_WIN
    if searchers in table:
        return table[searchers]
    known = sorted(table)
    if searchers < known[0]:
        return table[known[0]]
    if searchers > known[-1]:
        return table[known[-1]]
    lo = max(k for k in known if k < searchers)
    hi = min(k for k in known if k > searchers)
    span = (searchers - lo) / (hi - lo)
    return round(table[lo] + span * (table[hi] - table[lo]))


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

    def __init__(self, world: Map, start: str):
        self.world = world
        self.at = start
        self.reputation = 0
        self.emptied: set[str] = set()
        self.clock = 0.0

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

    def take(self, destination: str) -> int:
        prize = self.world.treasure[destination]
        self.emptied.add(destination)
        self.reputation += prize["reputation"]
        return prize["dwell"]


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


def itinerary(seed: bytes, start: str, world: Map,
              limit: int = 40) -> list[dict]:
    """Where she goes and how long she stands still, ignoring the searchers.

    She can be simulated on her own because **the reference searcher never
    gets ahead of her**. It follows the trail, and the trail only exists
    behind her, so it can never be in a room before she arrives -- which is
    the one thing that would change her behaviour (`will_steal`, seen). A
    searcher that guessed ahead would break this and would need the two
    simulated together; that is a reason to keep `seen` in her policy, not a
    reason to model it here.
    """
    her = Carmel(world, start)
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


def pursue(world: Map, start: str, home: str,
           trail: list[dict]) -> tuple[int | None, float]:
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
    clock = travel_hours(world.places[home], world.places[start])
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
          threshold: int | None = None) -> dict:
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
    threshold = reputation_to_win(searchers) if threshold is None \
        else threshold
    trail = itinerary(seed, start, world, limit)

    names = sorted(world.descriptors)
    caught_on, lags = None, []
    for i in range(searchers):
        digest = _prf(seed, b"hue-and-cry/v1/searcher-start", str(i), 0)
        home = names[int.from_bytes(digest[:8], "big") % len(names)]
        move, lag = pursue(world, start, home, trail)
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


def _run(world: Map, seed: bytes, names: list[str], searchers: int) -> dict:
    w = Map(seed)
    w.descriptors, w.places, w.treasure = (
        world.descriptors, world.places, world.treasure)
    start = names[int.from_bytes(seed[:4], "big") % len(names)]
    return chase(seed, start, searchers=searchers, world=w,
                 threshold=10 ** 9, limit=40)


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
    """Where the threshold has to sit for the game to be a contest.

    Too low and she wins before anyone reads a board; too high and the
    reference searcher catches her every time. What is wanted is a number
    where neither side is a formality -- and the honest report is the whole
    curve, since the reference searcher is a floor and a better one moves it.
    """
    names = sorted(world.descriptors)
    seeds = [os.urandom(32) for _ in range(trials)]

    print(f"{trials} chases per row, travel at {TRAVEL_KMH} km/h\n")
    print("  How many are hunting, and what it costs her -- the question"
          " games/hue-and-cry.md\n  left open as \"whether the threshold is"
          " fixed or scales with how many are hunting\":\n")
    print(f"  {'searchers':>10}{'her budget':>12}{'she reaches':>13}")
    for n in (1, 2, 3, 5):
        rs = [_run(world, s, names, searchers=n) for s in seeds]
        budget = sorted(min(r["lags"]) for r in rs if r["lags"])
        got = sorted(r["moves"][-1]["reputation"] for r in rs if r["moves"])
        print(f"  {n:>10}{budget[len(budget) // 2]:>10.0f}h"
              f"{got[len(got) // 2]:>13,.0f}")
    print("\n  The head start is the nearer searcher's, so it falls as they"
          " add hunters --\n  which answers the open question: the threshold"
          " CANNOT be fixed. The same\n  number that is a contest against one"
          " is unreachable against five.\n")

    results = []
    for i in range(trials):
        # Run with no threshold and read every candidate off one history.
        # The first version of this called chase() at the default 600 and
        # then asked what happened at 800, which no run could reach because
        # it had already stopped: every row above the threshold it was run
        # at read 0% wins and 92% "neither", which looks like a finding and
        # is an artefact.
        results.append(_run(world, seeds[i], names, searchers=2))

    print("  Two reference searchers, and what threshold makes a contest:\n")
    # The quantity the whole chase turns on. A searcher follows the same
    # legs she does, so its travel cancels hers exactly: the only thing that
    # closes the gap is her standing still. Lag falls by one dwell per hop
    # and by nothing else, which is what "the theft is the dwell and the
    # dwell is the exposure" means arithmetically.
    best = sorted(min(r["lags"]) for r in results if r["lags"])
    dwells = sorted(m["dwell"] for r in results for m in r["moves"]
                    if m["dwell"])
    print(f"  the nearer searcher settles {best[len(best) // 2]:.0f}h behind"
          f" her (median), and her longest theft is {max(dwells)}h.")
    print("  EVERY THEFT HANDS THE FOLLOWER THE HOURS SHE SPENT ON IT. Their"
          " travel cancels\n  exactly -- it walks her legs -- so the only"
          " asymmetry is that she stands still\n  and it does not. The gap"
          " is her head start minus everything she has stolen,\n  and it"
          " catches her on the first room where that reaches zero.\n")
    print("  So her win condition is a BUDGET, not a race: about"
          f" {best[len(best) // 2]:.0f} hours of standing\n  still in total,"
          " to be spent on the most valuable rooms she can reach.\n")
    reached = sorted(r["moves"][-1]["reputation"] for r in results
                     if r["moves"])
    print(f"  she reaches a median of {reached[len(reached) // 2]:,}"
          f" reputation before the chase ends or runs out of moves\n")
    print(f"  {'threshold':>10}{'she wins':>10}{'caught':>9}{'neither':>9}")
    for threshold in (50, 100, 150, 200, 300, 600):
        wins = caught = neither = 0
        for r in results:
            hit = next((m for m in r["moves"]
                        if m["reputation"] >= threshold), None)
            caught_at = r["hours"] if r["outcome"] == "caught" else None
            if hit and (caught_at is None or hit["leaves"] <= caught_at):
                wins += 1
            elif caught_at is not None:
                caught += 1
            else:
                neither += 1
        print(f"  {threshold:>10}{wins/trials:>10.0%}"
              f"{caught/trials:>9.0%}{neither/trials:>9.0%}")


if __name__ == "__main__":
    main()
