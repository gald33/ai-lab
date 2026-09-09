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
import hashlib
import math
import os
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import treasures as T  # noqa: E402
from descriptors import NEIGHBOURHOOD, all_descriptors  # noqa: E402
from gazetteer import EXITS, kinship  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402
from secret_matrix import (RECIPE, _prf, hints_for,  # noqa: E402
                           room_token, salt_for)

EXIT_INFO = b"hue-and-cry/v1/exits"

#: How fast she travels, in km/h, averaged over everything -- the flight, the
#: waiting, the bus at the other end. A GUESS, and the one that decides
#: whether geography matters at all: at 800 the map is a day wide and
#: distance is noise, at 80 a hop is a week and nothing else matters. 400 is
#: chosen so that the median hop (about 4,200 km at the committed exit band)
#: costs about ten hours -- the same order as the longest theft, so the two
#: costs trade against each other instead of one dominating.
TRAVEL_KMH = 400

#: What she needs to win. ONE NUMBER, and **currently uncalibrated** -- see
#: the warning at the end of this comment.
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
#: arrives. A solo hunt is a contest and a crowd is a hard game, and that
#: asymmetry is a property of the design rather than a bug in it.
#:
#: **140 IS STALE AND IS NOT A CALIBRATED NUMBER.** It was measured against
#: a searcher that was handed the address of every room she went to. Gal
#: removed the addresses on 2026-09-09 -- *"I will not be giving you any
#: addresses"* -- and a searcher that has to deduce the landmark from the
#: hint is a different and much weaker animal: she now runs out the move
#: limit at about 2,600 reputation rather than being caught at 162.
#:
#: It is left at 140 rather than replaced with a fresh guess, because the
#: honest blocker is that **the multi-searcher model is not trustworthy
#: yet**: its catch rate falls as searchers are added, which is backwards
#: and is the model rather than the game. A threshold calibrated against a
#: pursuit nobody believes is worse than an obviously stale one.
REPUTATION_TO_WIN = 140

#: The lobby is a public room whose key is published -- the island's shape
#: (`games/island/lobby.py`) and for its reason: a room nobody can find is
#: not an announcement. Its name is fixed and salt-free, because a lobby
#: that moved with the game salt could not be found by anybody who was not
#: already playing -- and the salt is *inside* the notice, so a salted lobby
#: could never be found at all.
LOBBY = "hue-and-cry"

#: And the lobby is also a place ON the map, which is a separate fact and
#: the one that makes the opening playable.
#:
#: Gal, 2026-09-09: *"we should either place the lobby on the map, or hand
#: out where the hint was heard from on the map."* Those are the same
#: problem: **a hint means nothing without knowing where it was heard.** The
#: candidates are the exits of a landmark, so a hint read with no anchor is
#: read against all thousand.
#:
#: Measured, on the hint the opening notice actually carried: `older than
#: the records` is true of **45 of the 1000**. Anchored, it is read against
#: five. The opening was a ninefold harder problem than every step after it,
#: and for no reason anybody chose.
#:
#: So she sets out FROM the lobby, and says so. Every hint in the game is
#: then read the same way -- against the exits of a landmark the reader
#: knows -- and the first one is not a special case. Grand-Place because a
#: lobby that is literally a public square is the joke worth having.
LOBBY_LANDMARK = "Grand-Place"

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
        """Her five, drawn from the PUBLISHED SALT and not from the seed.

        The docstring here used to say "drawn from the seed... public
        knowledge in principle", which was false against its own next line:
        a searcher cannot compute anything from a secret only she holds.

        It is the same bug as the room addresses had, in the same file, and
        it is worse, because the exits are what make a hint mean anything.
        `games/hue-and-cry.md` settled this long ago -- each landmark has
        "a small fixed set of exits... committed with the rest of the table
        and **public**" -- and a clue is read "against her *reachable* set
        rather than the whole map". Derived from the seed, the reachable set
        is unknowable and the hint narrows nothing.

        So: salt. The gazetteer is public, the neighbourhood rule is public,
        the salt is published when she opens the campaign, and a searcher
        who works out where she is can work out where she may go.
        """
        if landmark not in self._exits:
            pool = self.band(landmark)
            out: list[str] = []
            i = 0
            while len(out) < EXITS and i < 400:
                digest = hashlib.sha256(
                    EXIT_INFO + b"\x00" + salt_for(self.seed) + b"\x00"
                    + landmark.encode("utf-8") + b"\x00" + bytes([i])
                ).digest()
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


def open_campaign(seed: bytes, start: str = LOBBY_LANDMARK) -> str:
    """What she leaves in the lobby when she starts stealing.

    Gal, 2026-09-09, in three passes: *"she needs to post a note in some
    lobby... whoever wants to join the hunt, just join the hunt"*, then
    *"including the technique to get the workspace from the landmark"*, then
    *"she can also taunt in her message there by explaining the game"*.

    Those are the same post, and the taunt is what makes it work. **She has
    to explain the game to have anybody to play it against** -- a fugitive
    nobody can find is not a fugitive -- so the rules, the recipe and the
    boast are one message, and her interest in being chased is why she
    publishes the method for chasing her.

    **It is not a command.** Nothing parses it, there is no verb to
    recognise and nothing to settle: *"we have no commands here, either
    Carmel sees you in the room and you win, or she goes to hiding with her
    loot with enough reputation and you lose."*

    WHAT THE RECIPE COSTS A READER, which had to be checked rather than
    hoped. It is the technique Switchboard already uses, one step earlier --
    `name + salt -sha256-> token -sha256-> workspace`, and the library owns
    the second arrow. So joining a room given a token needs no hashing by
    the agent at all; turning a landmark's *name* into that token is the one
    hash it must do itself, and none of Switchboard's 27 MCP tools hashes.
    The gap is exactly one SHA-256: a line for any agent with a shell, and
    impossible for one holding only Switchboard. See `secret_matrix.RECIPE`.

    The salt goes in the clear and the seed does not. Publishing the salt is
    what lets a searcher think of a name and go to it, which
    `games/hue-and-cry.md` says the game needs -- without it "you can follow
    her but never get ahead, which is too weak". The seed stays hers until
    the end, so the hints and the treasures stay sealed.
    """
    salt = salt_for(seed)
    world = Map(seed)
    gone_to = itinerary(seed, start, world, 1)[0]
    first = gone_to["hint"]
    return "\n".join([
        "I have begun, and I am telling you because it is no fun otherwise.",
        "",
        "The rules, since you will want them. I am somewhere on a map of a",
        "thousand famous places. Every message I leave is one true thing",
        "about the place I am in. Work out which place that is, and you can",
        "work out the room:",
        "",
        f"    {RECIPE}",
        f"    salt = {salt.hex()}",
        "",
        "Hand what comes out to join_room. That is the whole of it -- guess",
        "the landmark from what I say, compute the room, come and stand in",
        "it. You will find me there or you will find what I said next.",
        "",
        "Find me while I am standing still and you have me. Let me stand",
        "still often enough and I retire on what I take.",
        "",
        f"I set out from {start}, which is where you are reading this. Work",
        "from there: I can only have gone to a place that resembles it, and",
        "you can work out which places those are as easily as I can.",
        "",
        "I will not be giving you any addresses. The first thing I have to",
        "say about where I have gone is this:",
        "",
        f"    {first.replace('_', ' ')}",
    ])


def interrupted_theft(outcome: str, trail: list[dict]) -> int | None:
    """The index of the leg she was caught mid-theft in, or None.

    The last room of a caught campaign is ALWAYS a theft she was in the
    middle of, and that is not a coincidence to be re-derived per caller.
    `pursue` catches her only when `leg["arrived"] < clock <= leg["leaves"]`,
    and `leaves == arrived + dwell`, so a leg with no dwell has an empty
    window and cannot be the catch -- the dwell is the window and there is
    no other (`games/hue-and-cry.md`, "The theft is a dwell").

    So `chase` returns `trail[caught_on - 1]["reputation"]`, her total
    BEFORE that room, while a leg's own `dwell` and `reputation` record a
    theft she *started*. Anything counting rooms she emptied, or printing a
    figure beside that count, must drop this index or it will disagree with
    the scoreboard on the same page -- which is how the bug in
    `close_campaign` was found, by drawing the trail
    (https://github.com/gald33/ai-lab/pull/250).
    """
    if outcome != "caught" or not trail or not trail[-1]["dwell"]:
        return None
    return len(trail) - 1


def close_campaign(seed: bytes, outcome: str, reputation: int,
                   trail: list[dict]) -> str:
    """What she leaves in the lobby when it is over.

    Gal: *"She also posts the results back in the lobby when the game
    ends."* This is where the seed goes, and the seed is the only thing that
    makes the rest of it checkable: with it, anybody holding the transcript
    can re-derive every hint she was entitled to post and every treasure
    that was in every room, and see whether she played the game she said
    she was playing.

    Nothing enforces that she posts it. She is not refereed and there is no
    component that could withhold a result until she did. What there is
    instead is that a campaign nobody can check is a campaign nobody counts,
    which is a weaker guarantee than the design once claimed for it and an
    honest one.

    WHAT SHE SAYS ABOUT THE ROOM SHE WAS CAUGHT IN, which is a design
    question and not a rounding error -- `games/hue-and-cry.md`, "The room
    she was caught in is counted apart and named". She counts it apart and
    names it. The post used to fold it into the emptied count while the
    reputation figure beside it excluded it, so the two halves of one
    sentence disagreed; dropping it silently would have made them agree and
    left a reader who re-derives the trail from the published seed unable to
    tell which of the two counts was wrong.
    """
    caught_in = interrupted_theft(outcome, trail)
    took = [leg["to"] for i, leg in enumerate(trail)
            if leg["dwell"] and i != caught_in]
    lines = [
        f"It is over. {outcome}.",
        "",
        f"{len(trail)} room{'' if len(trail) == 1 else 's'},"
        f" {len(took)} of them emptied,"
        f" {reputation} reputation.",
        "",
    ]
    if caught_in is not None:
        lost = trail[caught_in]["reputation"] - (
            trail[caught_in - 1]["reputation"] if caught_in else 0)
        # Wrapped rather than hand-broken because the landmark's name is as
        # long as it is, and a ragged paragraph reads as a slip in a post
        # whose whole job is to be believed.
        lines += textwrap.wrap(
            f"You walked in on me in {trail[caught_in]['to']}, and I was"
            " still working when you did, so that room is not among the"
            f" emptied ones. It is {lost} reputation I had my hands on and"
            " do not get to count.", width=68) + [""]
    lines += [
        "The seed, so you can check every word of it -- which rooms I could",
        "have gone to, which hints I was allowed to post, and what was in",
        "each room before I got there:",
        "",
        f"    seed = {seed.hex()}",
    ]
    return "\n".join(lines)


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
           joined_at: float = 0.0, share: tuple[int, int] = (0, 1)
           ) -> tuple[int | None, float]:
    """Run one searcher, deducing. Returns (the move it catches her on, its
    head start).

    THE SEARCHER'S ACTUAL PROBLEM, which this file did not model until now.
    Gal, 2026-09-09: *"a player guesses the landmark from the hint, plugs in
    the algorithm, gets the workspace, go to the workspace, looks for her or
    at least her next hint."*

    So there is no address anywhere. Standing in the room she was in, it
    reads the one thing she said on her way out, and has to work out which
    place she meant:

    1. The room it is in is a landmark it named, so it knows her exits --
       the gazetteer is public and the exits come from the published salt.
    2. Her hint is true of where she went, so the candidates are the exits
       the hint is true of. Measured at about **2.7 of her 5**.
    3. It picks one and travels. If she was never there the room is empty
       and it has learned only that, at the price of the journey; it tries
       the next candidate from the same hint.

    A wrong guess costs a leg and buys one bit. That is the whole game, and
    it is what the descriptor layer was built for -- every number in "The
    map is a thousand landmarks now" is about the size of this candidate
    set, and until this function existed none of them was load-bearing.
    """
    clock = joined_at + travel_hours(world.places[home], world.places[start])
    lag = clock

    here, hint = start, trail[0]["hint"]
    for i, leg in enumerate(trail):
        # Which of her exits is the hint true of? She is in one of these.
        candidates = [x for x in world.exits(here)
                      if hint in world.descriptors[x]] or world.exits(here)
        # `share` is (which searcher, how many). A field that divides the
        # candidates checks them in parallel instead of everybody walking
        # the same wrong rooms in the same order. Nothing enforces it and
        # nothing settles it -- it is talk, and it is the whole reason the
        # lobby is worth having.
        mine, of = share
        rota = [c for i, c in enumerate(candidates) if i % of == mine] \
            or candidates
        for guess in rota:
            clock += travel_hours(world.places[here], world.places[guess])
            if guess == leg["to"]:
                if leg["arrived"] < clock <= leg["leaves"]:
                    return i, lag
                here, hint = guess, (trail[i + 1]["hint"]
                                     if i + 1 < len(trail) else hint)
                break
            # Empty room. It knows only that she is not here.
        else:
            return None, lag          # the hint fitted nothing she took
    return None, lag


def chase(seed: bytes, start: str = LOBBY_LANDMARK, searchers: int = 2,
          limit: int = 40, world: Map | None = None,
          threshold: int = REPUTATION_TO_WIN,
          join_window: float = JOIN_WINDOW_HOURS,
          difficulty: float = DIFFICULTY,
          cooperate: bool = False) -> dict:
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
        move, lag = pursue(world, start, home, trail, joined_at=joined,
                           share=(i, searchers) if cooperate else (0, 1))
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
         join_window: float = JOIN_WINDOW_HOURS,
         cooperate: bool = False) -> dict:
    w = Map(seed)
    w.descriptors, w.places, w.treasure = (
        world.descriptors, world.places, world.treasure)
    # Every campaign sets out from the lobby, which is a place on the map.
    return chase(seed, LOBBY_LANDMARK, searchers=searchers, world=w,
                 threshold=10 ** 9, limit=40, join_window=join_window,
                 cooperate=cooperate)


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

    result = chase(seed, world=world)
    print(f"seed {seed.hex()[:16]}...  setting out from"
          f" {LOBBY_LANDMARK}\n")
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
    print("\n  Three searchers throughout, each deducing alone: it reads her"
          " hint, computes\n  the exits of the room it is standing in, keeps"
          " the ones the hint is true of\n  (about 2.7 of 5) and tries them."
          " A wrong guess costs a leg and buys one bit.\n")
    print("  So a lone searcher spends about 1.9 legs per room and she"
          " spends 1: the gap\n  GROWS on every hop. That is the opposite of"
          " the handed-address game this file\n  measured until the"
          " addresses were removed, where the gap shrank by her dwell.\n")


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
