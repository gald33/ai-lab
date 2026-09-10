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

1. **Where to go**, which is anywhere on the map -- but the farther,
   the longer she must stand still first.
2. **Whether to stand still and steal**, which is how she wins. It is no
   longer the only way she is catchable: since a move costs her preparation
   she can also be reached while getting ready, or overtaken outright.
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
from descriptors import all_descriptors  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402
from secret_matrix import (RECIPE, _prf, hints_for,  # noqa: E402
                           room_token, salt_for)

#: How fast she travels, in km/h, averaged over everything -- the flight, the
#: waiting, the bus at the other end. A GUESS, and the one that decides
#: whether geography matters at all: at 800 the map is a day wide and
#: distance is noise, at 80 a hop is a week and nothing else matters. 400 is
#: chosen so that the median hop (about 4,200 km at the committed exit band)
#: costs about ten hours -- the same order as the longest theft, so the two
#: costs trade against each other instead of one dominating.
TRAVEL_KMH = 400

#: Hours of preparation per hour of travel. **The mechanic that gives the
#: map a shape again**, and the one thing in this file a searcher can use
#: the clock for.
#:
#: Gal, 2026-09-09: *"the farther she wants to move, the longer it takes her
#: to prepare. So we can decide how much longer, but it is longer... she has
#: more chance of running away to a close landmark."*
#:
#: The order matters and is the whole mechanic: **she posts, and then she
#: prepares, and then she travels.** So the message is a bet. A searcher
#: reading it knows when it was posted -- Switchboard stamps every line --
#: and therefore knows its own lag `e`. She does not know `e` for anybody,
#: and cannot: she never learns who came.
#:
#: The arithmetic, short enough to state completely. She leaves A for X,
#: posting at time p. Her prep is `PREP x t(A,X)`, so she reaches X at
#: `p + PREP*t + t`. A searcher reading at `p + e` reaches X at `p + e + t`.
#: Subtract:
#:
#:     searcher arrival - her arrival = e - PREP * t(A,X)
#:
#: **A searcher with lag `e` gets to X before she does whenever
#: `e <= PREP * t(A, X)`** -- and every term of that is public. That is what
#: her pursuers can deduce, which is the half of Gal's message he was unsure
#: about: not where she is, but *which of the places she might be they can
#: beat her to*. The far candidates are the beatable ones.
#:
#: So distance is a bet she takes and cannot price, against a number they
#: hold and she does not.
#:
#: **It is the capture dial, and it is monotone** -- Gal, same day: *"all
#: the times can be factored to adjust the difficulty. So the percentage of
#: capture is actually something we can tune. We do tune."* Measured, 24
#: campaigns per row, nearest-first ordering:
#:
#:     PREP    c@1    c@3   c@10   med hop km
#:     0.00     4%     4%    12%        3,943
#:     0.50     8%    17%    38%          883
#:     1.00    12%    33%    54%          429
#:     2.00    33%    46%    83%          266
#:     4.00    96%   100%   100%          226
#:
#: Every column rises at every turnout, 4% to 96% against a lone searcher.
#: **The cost is in the last column**: past about 2.0 the game is a manhunt
#: in one country, so the range is real and bounded. 0.5 is where it is
#: left -- 38% at ten, hops still most of a continent, room both ways.
#:
#: This only reads as a dial under the nearest-first searcher. Under the
#: "beatable" ordering the same parameter drove capture to ZERO; see
#: `pursue`.
PREP = 0.5

#: The hours she guesses her nearest pursuer is behind her. **Her prior over
#: `e`, and the only defence she has against a number she can never learn.**
#:
#: This exists because the first version of the prep policy divided the
#: prize by `1 + prep hours` flat, and that is unboundedly distance-averse:
#: measured, she stopped using the map. Her median hop fell from 5,807 km at
#: `PREP = 0` to 246 km at 0.25 and 109 km at 1.0 -- she robbed one city
#: block by block, never travelled, and therefore never paid a prep worth
#: overtaking her during. **Raising the cost of distance made her safer**,
#: and the capture rate at ten searchers went 25% -> 67% -> 0%, which is not
#: a dial anybody can tune.
#:
#: The fix is to discount by the RISK the prep buys rather than by its
#: hours. What a prep of `h` hours actually costs her is the chance somebody
#: is within `h` of her, and that saturates: past the point where a pursuer
#: could be anywhere, going farther adds nothing. So:
#:
#:     score = reputation * cover / (1 + prep / ASSUMED_LAG)
#:
#: At `ASSUMED_LAG -> 0` she is the hugger above. At `-> infinity` she
#: ignores distance, which was the pre-prep game. 12 hours is A GUESS, and
#: it is *deliberately* a guess she can be wrong about: she never learns
#: what the field actually is, so a Carmel who priced this correctly would
#: be reading something she cannot see.
ASSUMED_LAG = 12.0

#: How much she plays her own preferences and how much she plays a hunch.
#:
#: Gal, 2026-09-09: *"add some randomness for all her decisions."* All three
#: of them, so all three sample rather than take the best: where to go,
#: what to say, and whether to stop and rob the place.
#:
#: **The reason it is worth having is on the searchers' side of the board.**
#: `carmel.py` is public, because she is a stated control -- and the last
#: measurement in this file found that her published preferences, not the
#: timestamp and not the gazetteer, are the strongest thing a searcher can
#: hold: probing near candidates first took capture from 0% to 50%. A
#: policy that always takes its own argmax is a policy that can be replayed
#: by anybody who has read it. Sampling means her preferences remain the
#: way to bet and stop being the way to *know*.
#:
#: The knob is a temperature over the score she already computes. Each
#: option is drawn with probability proportional to `score ** (1 / WHIM)`:
#:
#:     WHIM -> 0     argmax, which is what she was
#:     WHIM  = 1     straight proportional to score
#:     WHIM -> inf   uniform, and she is not playing at all
#:
#: **What it costs her and what it buys**, 24 campaigns per row:
#:
#:     WHIM    c@1    c@3   c@10   med hop km   rep@40
#:     0.00     8%     8%    21%          694      2,999
#:     0.20     0%     0%     4%        1,637      2,565
#:     0.35     0%     4%     8%        2,982      2,323
#:     0.60     0%     0%     4%        4,821      2,083
#:     1.00     0%     0%     0%        5,752      1,905
#:
#: **She trades reputation for safety, and the exchange rate is steep**:
#: at 0.35 she is caught a third as often and banks 23% less. Two things
#: are going on, and neither is that the randomness confuses the searcher
#: directly. She stops hugging (694 km -> 2,982), so prep costs her more
#: and she robs poorer rooms; and the near-first probe order stops fitting
#: her, because it was only ever fitting her *preference* for near.
#:
#: **A searcher cannot recover this by modelling her better.** Her score
#: has three terms and two of them are sealed until the reveal -- the
#: treasure's reputation and the seed-derived live hints that set cover.
#: Only the prep term is public, so "she prefers near" is the whole of
#: what a searcher can know about where she is going, and softening the
#: argmax is exactly what makes that one term a weaker predictor. `pursue`
#: reads no sealed field and a test holds that.
#:
#: 0.35 is A GUESS. It is also the row where she is still caught sometimes
#: at every turnout, which the rows either side of it are not.
WHIM = 0.35

#: How often she walks past a treasure she could have taken.
#:
#: The third decision, and the one where "random" means something different
#: from the other two: there is no score to soften, only a coin. A theft is
#: the only thing that makes her catchable, so a Carmel who *always* stops
#: is one whose next appearance is predictable in time as well as in place
#: -- a searcher that knows she is always mid-theft knows exactly how long
#: she will be there. Sometimes walking past costs her the prize and buys
#: back the uncertainty.
#:
#: A GUESS, and deliberately small: she is a thief, and one who mostly does
#: not steal is a different control.
SKIP_CHANCE = 0.15

#: The PRF label for every one of those draws.
#:
#: **Her randomness comes out of the campaign seed and never out of
#: `random`**, and that is not a style preference. `close_campaign`
#: publishes the seed precisely so anybody holding the transcript can
#: re-derive every choice she was entitled to make and check that she made
#: them. A Carmel who rolled real dice would be a Carmel whose campaign
#: nobody can check -- the commit-reveal would still verify the hints and
#: the treasures, and would say nothing at all about her play.
WHIM_INFO = b"hue-and-cry/v1/whim"

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
#: hint is a different and much weaker animal. Gal then removed the routes
#: too -- *"we have no routes"* -- and she now runs out the forty-move
#: limit at about **3,626** reputation rather than being caught at 162,
#: winning 88% of campaigns against ten searchers and 98% against one.
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

#: And the lobby is also a place ON the map, which is a separate fact.
#:
#: Gal, 2026-09-09: *"we should either place the lobby on the map, or hand
#: out where the hint was heard from on the map."*
#:
#: **The reason that was given for this has since been withdrawn, and the
#: decision has not.** The argument was that a hint means nothing without
#: knowing where it was heard, because the candidates were the *exits* of a
#: landmark: `older than the records` was true of 45 of the 1000 unanchored
#: and of five when anchored, so the opening was a ninefold harder problem
#: than every step after it. Gal then removed the routes -- *"we have no
#: routes"* -- and every hint is now read against the whole map, so the
#: anchor narrows nothing and the opening is no longer a special case in
#: either direction.
#:
#: What is left is still worth having and is a different thing: it is where
#: she is, so it is where a searcher's first journey starts and what its
#: first leg costs. A campaign whose origin was nowhere would have no
#: clock. Grand-Place because a lobby that is literally a public square is
#: the joke worth having.
LOBBY_LANDMARK = "Grand-Place"

#: How long people take to notice the notice and set off. A GUESS, and the
#: parameter that decides how much of a head start she gets: nobody is
#: hunting her until somebody reads the lobby.
JOIN_WINDOW_HOURS = 12

#: What standing still costs her, as a multiplier on the hours. 1.0 is the
#: treasure's own dwell and the nominal prep.
#:
#: **It scales prep as well as dwell**, since 2026-09-09. Gal: *"all the
#: times can be factored to adjust the difficulty. So the percentage of
#: capture is actually something we can tune. We do tune."* Both are time
#: she spends not travelling, both are time her pursuers spend closing, and
#: a factor that moved only one of them would change what kind of game it
#: is rather than how hard it is.
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


def prep_hours(a: dict, b: dict, difficulty: float = 1.0) -> float:
    """What it costs her to get ready to make that hop.

    Scaled by `difficulty` with everything else of hers, because Gal's dial
    is *all* her times and not just the thefts: prep and dwell are the two
    things she does standing still, and the gap closes by both.

    A searcher pays none of this. It is her papers, her route and her
    luggage, and the asymmetry is the point.
    """
    return PREP * travel_hours(a, b) * difficulty


def _draw(seed: bytes, leg: int, kind: str) -> float:
    """A number in [0, 1) for one decision, from the seed and nothing else.

    `kind` separates the three decisions of a single leg so that softening
    one does not shift the others, and `leg` separates the legs. Both go
    through the same HMAC the rest of this game derives from, so a reader
    holding the published seed can reproduce every draw.
    """
    digest = _prf(seed, WHIM_INFO, kind, min(leg, 255))
    return int.from_bytes(digest[:8], "big") / 2 ** 64


def _sample(options: list, weights: list[float], roll: float):
    """One of `options`, with probability proportional to `weight ** (1 /
    WHIM)`. `roll` is the [0, 1) draw that decides it.

    At `WHIM -> 0` this is `max`, which is what all three decisions were
    before 2026-09-09.
    """
    if not options:
        return None
    if WHIM <= 0:
        return max(zip(weights, options))[1]
    scale = max(weights) or 1.0
    sharp = [(max(w, 0.0) / scale) ** (1.0 / WHIM) for w in weights]
    total = sum(sharp)
    if total <= 0:
        return options[int(roll * len(options)) % len(options)]
    mark = roll * total
    for option, weight in zip(options, sharp):
        mark -= weight
        if mark <= 0:
            return option
    return options[-1]


class Map:
    """The gazetteer as one game sees it: a thousand places, the treasures
    and descriptors that were fixed before the game started, and the three
    descriptors per place that this seed makes postable.

    THERE ARE NO ROUTES. Gal, 2026-09-09: *"we have no routes."* This class
    held `band()` and `exits()` -- a five-place reachable set per landmark,
    drawn from the published salt out of the 200 nearest look-alikes -- and
    both are gone. Nothing constrains where she goes next. See
    `games/hue-and-cry.md`, "There are no routes", for what that costs and
    what it buys; the short version is the measurement that preceded the
    decision:

        a hint alone, against the whole map   median 115 candidates
        the same hint, against her 5 exits    median   2

    and, now that a hint is read against the map, the one she actually
    posts is the commonest of her three: median 152, worst case 27.

    The second row was only ever available to a searcher who had cloned
    352 KB of tables and reimplemented three modules exactly. The first row
    is available to anybody who can read a sentence and run one SHA-256,
    which is who this game is for.
    """

    def __init__(self, seed: bytes):
        self.seed = seed
        self.places = {p["name"]: p for p in load_landmarks()}
        self.descriptors = {k: sorted(v) for k, v in all_descriptors().items()}
        self.treasure = {t["landmark"]: t for t in T.build()}
        #: How many landmarks each descriptor is true of. With no routes
        #: this IS the size of the candidate set a hint leaves, so it is
        #: the whole of what "cover" means now -- one pass over the map
        #: instead of a per-landmark band computed on demand.
        self.cover: dict[str, int] = {}
        for words in self.descriptors.values():
            for word in words:
                self.cover[word] = self.cover.get(word, 0) + 1

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
        #: Which hop she is on. It indexes her draws, so that the same seed
        #: replays the same campaign and two legs are not handed the same
        #: coin. `itinerary` advances it; nothing else may.
        self.leg = 0
        #: Scales what standing still costs her. She does not know it and
        #: cannot: it is set from campaigns she has already lost or won, and
        #: nothing she can read says what it is.
        self.difficulty = difficulty

    # --- 1. where to go ---------------------------------------------------
    def choose_destination(self) -> str:
        """Worth going to, describable once she gets there, and near enough
        that she is gone before anybody arrives.

        Three things pull now. A rich room is the point -- she wins on
        reputation and nothing else. The hint she will have to post about it
        is drawn from that room's descriptors, and a room whose live three
        are all rare announces her. And **distance is a bet**: she posts
        before she prepares, so the farther she goes the longer she stands
        in the room she has just advertised, and the wider the band of
        searchers who reach the destination before she does.

        The correction this makes, in the file that made it: two commits
        ago this docstring said she does *not* read distance, "deliberately:
        their travel cancels exactly, so distance costs her nothing it does
        not also cost her pursuer". The travel still cancels exactly. **The
        prep does not cancel at all** -- it is hers alone -- so the sentence
        was true of a game without prep and is false of this one.

        So she scores a room by the prize divided by the risk the journey
        buys, and then **draws** rather than taking the best:

            score = reputation * cover / (1 + prep / ASSUMED_LAG)
            P(X)  = score(X) ** (1 / WHIM), normalised

        Gal, 2026-09-09: *"add some randomness for all her decisions."* The
        argument is under `WHIM`, and the short form is that this file is
        public: a policy that always takes its own argmax can be replayed
        by anybody who has read it, and her preferences had become the way
        to *know* where she went rather than the way to bet on it.

        She cannot do better than a fixed risk preference, because pricing
        the bet needs `e` -- how far behind her nearest pursuer is -- and
        she never learns who came, let alone from where. `ASSUMED_LAG` is
        her standing guess at it, and the reason the discount saturates
        rather than growing without bound is written there: a flat `1 +
        prep hours` made her stop using the map, and a Carmel who never
        travels is one nobody can overtake.
        """
        rooms, scores = [], []
        for destination, prize in self.world.treasure.items():
            if destination in self.emptied or destination == self.at:
                continue
            prep = prep_hours(self.world.places[self.at],
                              self.world.places[destination], self.difficulty)
            rooms.append(destination)
            scores.append(prize["reputation"] * self.best_cover(destination)
                          / (1.0 + prep / ASSUMED_LAG))
        return _sample(rooms, scores,
                       _draw(self.world.seed, self.leg, "where"))

    def best_cover(self, destination: str) -> int:
        """How much of the map the most ambiguous live hint leaves standing.

        This is the quantity the descriptor layer was built to keep above
        one. It used to be counted against her five exits; with no routes
        it is counted against all thousand landmarks, which is the set the
        reader actually faces.
        """
        return max(self.world.cover[word]
                   for word in self.world.live_hints(destination))

    # --- 2. what to say ---------------------------------------------------
    def choose_hint(self, destination: str) -> str:
        """The least informative true thing she can say about where she went.

        `games/hue-and-cry.md`: *"the Fugitive's strategy is now sharp and
        stateable: post the least informative true fact, which is a real
        optimisation against a real posterior."* Least informative means
        covering the most of the set a reader can narrow her to -- and with
        no routes that set is the map, so the commonest of her three live
        descriptors is the one she wants.

        **She draws among the three rather than taking it**, weighted the
        same way as the room (`WHIM`). So she usually says the vaguest
        thing she holds and sometimes says a sharper one, which is the
        difference between a searcher knowing what she said and knowing
        only what she tends to say. Every draw is still one of the three
        the seed made live, so she is never posting something untrue: *she
        may lie in prose, she may not lie in a clue.*
        """
        live = sorted(self.world.live_hints(destination))
        return _sample(live, [float(self.world.cover[w]) for w in live],
                       _draw(self.world.seed, self.leg, "say"))

    # --- 3. whether to stand still ----------------------------------------
    def will_steal(self, destination: str) -> bool:
        """She steals wherever she has not already, and sometimes walks on.

        The third of Gal's *"randomness for all her decisions"*, and the
        one where random means something other than a softened argmax:
        there is no score here, only a coin. `SKIP_CHANCE` carries the
        argument -- a theft is the only thing that makes her catchable, so
        a Carmel who always stops is one whose next appearance is
        predictable in time as well as in place.

        **The `seen` argument is gone, and with it the abort rule.** It read
        the board on arrival and did not start if a searcher had posted
        there, which made being-seen an interruption rather than an ending.
        That cannot survive the prep clock: a searcher who overtakes her
        once is standing where she lands, reads her next hint the instant
        she posts it with a lag of nearly zero, and overtakes her again
        forever -- so an aborting Carmel is frozen rather than caught, and
        the game has no end.

        Gal's own statement of the outcomes settles it and is simpler than
        what this file had built: *"either Carmel sees you in the room and
        you win, or she goes to hiding with her loot with enough reputation
        and you lose."* **Being in the room with her is the win.** It does
        not matter who arrived first, and there is no third outcome for a
        searcher who gets there early -- it waits, which is what arriving
        early is *for*.
        """
        if destination in self.emptied:
            return False
        return _draw(self.world.seed, self.leg, "steal") >= SKIP_CHANCE

    def take(self, destination: str) -> float:
        prize = self.world.treasure[destination]
        self.emptied.add(destination)
        self.reputation += prize["reputation"]
        return prize["dwell"] * self.difficulty


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
        "One kindness, because it costs me nothing you could not work out.",
        "I post before I pack, and the farther I mean to go the longer the",
        f"packing takes -- {PREP} hours of it for every hour of the journey.",
        "My line is stamped with the hour I wrote it. Subtract, and you know",
        "how far behind me you are; and for any place you think I have gone,",
        "you know whether you can be standing in it before I get there.",
        "",
        "You cannot do that for everywhere. You can do it for the far ones.",
        "",
        f"I set out from {start}, which is where you are reading this.",
        "There is nowhere I cannot have gone from here. A thousand places,",
        "and the only thing narrowing them is what I choose to tell you.",
        "",
        "I will not be giving you any addresses. The first thing I have to",
        "say about where I have gone is this:",
        "",
        f"    {first.replace('_', ' ')}",
    ])


def interrupted_theft(outcome: str, trail: list[dict]) -> int | None:
    """The index of the leg she was caught mid-theft in, or None.

    `chase` returns `trail[caught_on - 1]["reputation"]`, her total BEFORE
    the room she was caught in, while that leg's own `dwell` and
    `reputation` record a theft she *started*. Anything counting rooms she
    emptied, or printing a figure beside that count, must drop this index
    or it will disagree with the scoreboard on the same page -- which is
    how the bug in `close_campaign` was found, by drawing the trail
    (https://github.com/gald33/ai-lab/pull/250).

    WHY THE `dwell` GUARD IS LOAD-BEARING, which it did not used to be.
    This first read "the last leg of a caught campaign, always", because
    `pursue` then caught her only inside `arrived < clock <= leaves` and a
    leg with no dwell had an empty window. #249 replaced that rule:
    **sharing a room with her is the win, however you came to be in it**
    (`games/hue-and-cry.md`, "Sharing a room with her is the win"), so the
    test is now `clock <= leg["leaves"]` and a searcher that beats her to a
    room and waits catches her there. A caught campaign can therefore end
    in a room she never dwelt in -- she walked into somebody already
    standing in it -- and that is a catch with **no interrupted theft**:
    nothing was taken, nothing is owed to the count, and there is nothing
    for her to name. Hence None, rather than the last index unconditionally.
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

    She does NOT say who walked in on whom. Since #249 a searcher may beat
    her to a room and wait, so "you walked in on me" -- which this sentence
    said first -- is false exactly when the searcher played it best. What
    the trail supports is that they shared the room while she was working,
    and that is all she claims.
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
            f"You were in {trail[caught_in]['to']} with me while I was"
            " still working, so it is not one of the emptied rooms. It is"
            f" {lost} reputation I had my hands on and do not get to"
            " count.", width=68) + [""]
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
    """Where she goes, when she says so, and how long she stands still.

    Each leg is one hop and reads in the order she lives it:

        posted   she puts the hint up in the room she is leaving
        prep     she gets ready, still standing in that room
        arrived  posted + prep + travel
        leaves   arrived + dwell, and is when she posts the next one

    **She is still simulated on her own, and the reason changed.** It used
    to be that the searcher could never get ahead of her, so it could never
    change her behaviour. Under the prep clock it certainly can get ahead of
    her -- that is the whole mechanic -- but with the abort rule gone
    (`will_steal`), being reached is the end of the game rather than a
    change to her plan. Nothing a searcher does alters a leg she would
    otherwise have flown, so the trail is still a pure function of the seed.
    """
    her = Carmel(world, start, difficulty)
    out, posted = [], 0.0
    for leg in range(limit):
        her.leg = leg
        destination = her.choose_destination()
        hint = her.choose_hint(destination)
        leaves_from = her.at
        prep = prep_hours(world.places[leaves_from],
                          world.places[destination], difficulty)
        travel = travel_hours(world.places[leaves_from],
                              world.places[destination])
        her.at = destination
        arrived = posted + prep + travel
        dwell = her.take(destination) if her.will_steal(destination) else 0
        out.append({"from": leaves_from, "to": destination, "hint": hint,
                    "posted": posted, "prep": prep, "travel": travel,
                    "arrived": arrived, "leaves": arrived + dwell,
                    "dwell": dwell, "reputation": her.reputation})
        posted = arrived + dwell
    return out


def pursue(world: Map, start: str, home: str, trail: list[dict],
           joined_at: float = 0.0, share: tuple[int, int] = (0, 1),
           order: str = "near") -> tuple[int | None, float]:
    """Run one searcher, deducing. Returns (the move it reaches her on, its
    head start).

    WHAT IT READS, WHICH IS TWO THINGS
    ----------------------------------

    A line and a timestamp. The hint says something true of where she went;
    the timestamp says when she said it, and therefore -- against its own
    clock -- what its lag `e` is. Gal, 2026-09-09: *"she does not know how
    close her pursuers are, but they do know when she left the message. So
    they know how close they are."*

    WHAT IT CAN DEDUCE FROM THEM, WHICH IS THE PART THAT WAS UNKNOWN
    ---------------------------------------------------------------

    Not where she is. **Which of the places she might be it can beat her
    to.** She posts before she prepares, so for a candidate X she does not
    reach X until `PREP * t(here, X)` after posting, while the searcher
    needs only `e`. So:

        it arrives before her   <=>   e <= PREP * t(here, X)

    Every term is public: the gazetteer, `PREP`, and the stamp on her line.
    **The far candidates are the ones it can guarantee**, which is the exact
    complement of her preference for near ones. So it sorts the candidates
    the hint allows into the ones it can beat her to and the ones it cannot,
    and walks the beatable ones nearest-first, since a wrong guess still
    costs a leg and the cheapest wrong guess is the near one.

    It computes prep at difficulty 1.0 because it does not know the dial.
    Above 1.0 that makes it conservative -- she is slower than it assumed,
    so more candidates are beatable than it thinks -- and below 1.0 it is
    optimistic and loses journeys it expected to win. That asymmetry is a
    property of a dial only one side can see, and is left rather than fixed.
    """
    clock = joined_at + travel_hours(world.places[home], world.places[start])
    lag = clock

    here = start
    for i, leg in enumerate(trail):
        if clock < leg["posted"]:
            # It got here before she had even posted. It waits for the line
            # rather than guessing from one she has not written.
            clock = leg["posted"]
        elapsed = clock - leg["posted"]

        def beatable(x: str) -> bool:
            return elapsed <= prep_hours(world.places[here], world.places[x])

        def rank(x: str) -> tuple:
            near = travel_hours(world.places[here], world.places[x])
            # "near" is the default and "beatable" is kept only because
            # deleting it would delete the measurement that chose between
            # them. See `--calibrate`; the short version is that chasing the
            # guaranteed interception first is a TRAP, and an expensive one:
            #
            #     PREP  order       caught@3  caught@10
            #     0.50  beatable          0%         6%
            #     0.50  near              6%        19%
            #     1.00  beatable          0%         0%
            #     1.00  near             38%        50%
            #
            # Beatability and probability point opposite ways. The
            # candidates it can beat her to are the FAR ones, by
            # construction -- and she prefers near ones, by policy. So an
            # ordering that chases guarantees walks to the wrong end of the
            # map first, every time, and the prep factor that was supposed
            # to expose her instead hides her.
            #
            # What is worth reading the stamp for is therefore not "where
            # do I go first" but "will this journey be worth making at
            # all". It stays as the tiebreak, which is what a certainty
            # that is rarely relevant is worth.
            return ((not beatable(x), near, x) if order == "beatable"
                    else (near, not beatable(x), x))

        candidates = sorted(
            (x for x in world.descriptors
             if leg["hint"] in world.descriptors[x] and x != here), key=rank)
        # `share` is (which searcher, how many). A field that divides the
        # candidates checks them in parallel instead of everybody walking
        # the same wrong rooms in the same order. Nothing enforces it and
        # nothing settles it -- it is talk, and it is the whole reason the
        # lobby is worth having.
        mine, of = share
        rota = [c for j, c in enumerate(candidates) if j % of == mine] \
            or candidates
        for guess in rota:
            clock += travel_hours(world.places[here],
                                  world.places[guess])
            if guess == leg["to"]:
                # In the room with her -- whether it beat her there and
                # waited, or walked in while she was still stealing. Gal:
                # "either Carmel sees you in the room and you win".
                if clock <= leg["leaves"]:
                    return i, lag
                here = guess
                break
            # Empty room. It knows only that she is not here.
        else:
            # Her room fell in somebody else's share of the rota, and
            # nothing in this model carries what they found back. The
            # channel that would is the notes in the lobby, unmodelled.
            return None, lag
    return None, lag


def chase(seed: bytes, start: str = LOBBY_LANDMARK, searchers: int = 2,
          limit: int = 40, world: Map | None = None,
          threshold: int = REPUTATION_TO_WIN,
          join_window: float = JOIN_WINDOW_HOURS,
          difficulty: float = DIFFICULTY,
          cooperate: bool = False, order: str = "near") -> dict:
    """One game. NOT THE RUNTIME -- see the module head.

    **One rule, where this used to have two.** It said:

    > - *Being seen aborts the theft.* When she arrives she reads the board;
    >   if a searcher has posted there she does not start, and leaves at
    >   once, so she is not standing there to be caught.
    > - *The catch is walking in while she is still there.* She is only
    >   still there while she is stealing. The dwell is the window and there
    >   is no other.

    The prep clock makes that pair unplayable: a searcher who overtakes her
    once stands where she lands, so under the first rule she aborts, posts
    from that room with the searcher reading over her shoulder, and is
    overtaken again for ever -- never caught, never scoring, no end. See
    `Carmel.will_steal`.

    So it is Gal's rule instead, which was always the simpler statement:
    *"either Carmel sees you in the room and you win, or she goes to hiding
    with her loot with enough reputation and you lose."* **Sharing a room
    with her is the win**, however you came to be in it. Arriving early is
    not a wasted journey, it is the good outcome: you wait.
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
                           share=(i, searchers) if cooperate else (0, 1),
                           order=order)
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
         cooperate: bool = False, order: str = "near") -> dict:
    w = Map(seed)
    w.descriptors, w.places, w.treasure = (
        world.descriptors, world.places, world.treasure)
    # Every campaign sets out from the lobby, which is a place on the map.
    return chase(seed, LOBBY_LANDMARK, searchers=searchers, world=w,
                 threshold=10 ** 9, limit=40, join_window=join_window,
                 cooperate=cooperate, order=order)


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
    print("\n  Three searchers throughout, each deducing alone. It reads her"
          " hint and keeps\n  every landmark on the map the hint is true of"
          " -- a median of 152 of the\n  1000, since there are no routes."
          " Then it reads the STAMP on her line.\n")
    print("  She posts before she packs, and packing takes"
          f" {PREP} hours per hour of\n  journey, so a searcher whose lag is"
          " e reaches X before she does whenever\n  e <= PREP * t(here, X)."
          " Every term of that is public. It cannot deduce\n  where she is;"
          " it can deduce which of the places she might be it can beat\n"
          "  her to, and those are the far ones.\n")

    print("  What the prep factor buys, which is not monotonic and is the"
          " reason\n  ASSUMED_LAG exists. Raise it far enough and she stops"
          " using the map:\n")
    print(f"  {'PREP':>6}{'median hop':>13}{'she reaches':>13}"
          f"{'caught, 10':>12}")
    was = globals()["PREP"]
    for factor in (0.0, 0.5, 1.0, 2.0):
        globals()["PREP"] = factor
        rs = [_run(world, sd, names, searchers=10) for sd in seeds[:24]]
        trail = itinerary(seeds[0], LOBBY_LANDMARK, world, 40)
        hops = sorted(leg["travel"] * TRAVEL_KMH for leg in trail)
        caught = sum(1 for r in rs if r["outcome"] == "caught") / len(rs)
        print(f"  {factor:>6.2f}{hops[len(hops) // 2]:>11,.0f}km"
              f"{trail[-1]['reputation']:>13,}{caught:>12.0%}")
    globals()["PREP"] = was
    print("\n  A Carmel who never travels pays no prep, and a prep nobody"
          " pays is a clock\n  nobody can read. The dial that tunes capture"
          " is DIFFICULTY, which scales\n  every hour she spends standing"
          " still -- both the packing and the theft.\n")


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
