"""Carmel Taldiego: where she goes, what she takes, and what she says about it.

She is an NPC in her own process, and `games/carmel-taldiego.md` is explicit
about why that matters: *"With a person or an agent playing Carmel,
ticks-to-arrest confounds how good the searchers were with how good she was;
against a fixed, stated policy it does not. The adversary held constant is
the control the 008 measurement needs."*

**So this file is the statement of that policy.** Every choice she makes is
a pure function of what she can see, with the reasoning next to it, and none
of it reads anything a searcher could not also read.

    python3 games/carmel-taldiego/carmel.py            # watch a chase
    python3 games/carmel-taldiego/carmel.py --calibrate

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

`games/carmel-taldiego.md` says of her win condition: *"What is not settled
here: the values, the threshold, and whether the threshold is fixed or
scales with how many are hunting. Those are numbers to calibrate against a
played game, not decisions to invent now."* `--calibrate` is the beginning
of that, against a reference searcher rather than a played game, which is
weaker and is the most that exists.
"""

import argparse
import hashlib
import itertools
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import treasures as T  # noqa: E402
from descriptors import all_descriptors  # noqa: E402
from hints import riddle  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402
from secret_matrix import (ADDRESS_RECIPE, RECIPE, _prf,  # noqa: E402
                           hints_for,
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

#: How the packing grows with the length of the journey. **Superlinear**,
#: since 2026-09-10 -- Gal: *"make her distance to time super linear."*
#:
#: It was linear: twice as far, twice the packing. That made distance a
#: cost she could pay in instalments, and it is not what a fugitive's
#: distance costs. Papers for the next country over are an afternoon;
#: papers for the other side of the planet are a different kind of problem.
#:
#: The shape, with `t` the hours of travel:
#:
#:     prep = PREP * PIVOT * (t / PIVOT) ** PREP_EXPONENT
#:
#: `PREP_PIVOT` is the hop at which this equals what the linear rule
#: charged, so the exponent is the only thing that changed and the middle
#: of the range did not move. Below the pivot she gets a discount, above it
#: a penalty that grows without bound -- which is the point, because
#: **her randomness had her taking long hops for free**: with `WHIM = 0.35`
#: her median hop is about 3,000 km and the linear rule charged her the
#: same per kilometre for it as for a taxi across town.
#:
#: WHICH MAPPING THIS IS, BECAUSE THE OTHER READING BREAKS THE CHASE. It is
#: the *prep* that is superlinear, not the travel. Travel is shared physics
#: -- the searcher flies the same distance in the same time, which is why
#: it cancels exactly (`test_the_follower_closes_by_everything_she_does_
#: standing_still`), and a Carmel whose *travel* were superlinear while her
#: pursuers' stayed linear would be outrun on every long leg by an
#: arithmetic nobody could state. Prep is hers alone by construction, so
#: bending it bends only her side and the cancelling survives.
#:
#: 1.6 and a 10-hour pivot are GUESSES, swept in `--calibrate`.
PREP_EXPONENT = 1.6

#: The journey length at which the superlinear rule charges exactly what
#: the linear one did: 10 hours, which is 4,000 km at `TRAVEL_KMH`. Chosen
#: as roughly a long-haul flight, so "a continent away" is the hinge and
#: the two sides of it read as discount and penalty rather than as a
#: wholesale reprice.
PREP_PIVOT = 10.0

#: How many rooms one searcher can be standing in at once.
#:
#: **This is the resource travel used to be, and it had to replace it.**
#: Gal, 2026-09-10: *"travel time is zero... for the player it is zero in
#: real time."* True, and it takes the last cost off a wrong guess: a
#: searcher that pays nothing to enter a room can enter every room the hint
#: allows, sit in all 158 of them, and win every campaign. The model had
#: been charging it for journeys it never makes, and with that gone there
#: was nothing left holding the game up.
#:
#: What is actually scarce is not the searcher's *movement*. It is its
#: **attention**: a real agent can hold and watch some number of rooms,
#: read some number of boards, and no more. So a searcher picks `WATCH`
#: rooms out of the candidates and waits in them, and that is its whole
#: move.
#:
#: This turns the game into the one it was started for. Coverage is
#: `WATCH x searchers` against a candidate set of about 158, so
#: **a field that divides the candidates covers them and a field that does
#: not overlaps** -- which is not a nicety about the lobby any more, it is
#: the arithmetic of winning. Three sections of measurement have pointed
#: here; this is the parameter they were pointing at.
#:
#: **2, and the sweep chose it on a criterion that is not balance.**
#: 40 campaigns per cell:
#:
#:     WATCH   solo  3 alone  3 split  10 alone  10 split
#:         1    28%      32%      50%       35%       85%
#:         2    38%      50%      78%       55%       95%
#:         3    48%      62%      82%       68%      100%
#:         4    57%      72%      90%       80%      100%
#:         6    70%      82%      98%       90%      100%
#:        12    82%      92%     100%       95%      100%
#:
#: The first guess here was 6, and it is wrong in a way worth recording:
#: it does not make the game *easy*, it makes it **unmeasurable**. The
#: quantity this experiment exists to see is the distance between `alone`
#: and `split` -- what talking is worth -- and that gap collapses as
#: coverage stops being scarce: 50 points at `WATCH = 1`, 40 at 2, 32 at 3,
#: 20 at 4, 10 at 6, 5 at 12. A field that can watch everything has nothing
#: to divide.
#:
#: So the three conditions, in the order they bind:
#:
#: 1. **No column pinned at 100%.** A saturated cell cannot show a better
#:    field getting better, which is the ceiling version of the warning
#:    already written under `next_difficulty`: a number held constant by
#:    the design is indistinguishable from a field that never improved.
#:    That rules out 3 and up.
#: 2. **The coordination premium is the biggest thing on the board.**
#:    +40 points at ten searchers, against +5 at 12.
#: 3. **A lone searcher is an underdog**, 38%, which is what a fugitive
#:    with a thousand rooms should make of one person.
#:
#: **RE-SWEPT and reversed on 2026-09-10**, when the near bias became real
#: and made her far easier to find. At `NEAR_KM = 2500`:
#:
#:     WATCH   solo  3 alone  3 split  10 alone  10 split  premium
#:         1    35%      48%      60%       55%       90%      +35
#:         2    50%      65%      82%       78%       98%      +20
#:         3    65%      75%      90%       85%      100%      +15
#:
#: 1 now wins all three conditions outright: nothing saturated, the biggest
#: premium, and a soloist at 35%. It was rejected before on a fourth and
#: aesthetic ground -- that at one room there is no question of *how many*
#: to watch -- which does not survive contact with the other three. The
#: searcher still chooses *which* room, and that is the whole deduction.
WATCH = 1

#: How far away stops feeling near, in kilometres. **The scale of her bias
#: towards near, and since 2026-09-10 the primary term in where she goes.**
#:
#: Gal, 2026-09-09: *"she is biased towards near."*
#:
#: *Corrected 2026-09-10.* This comment said he had asked three times "which
#: is the measure of how badly it was being heard". He had not -- his client
#: was stuck and resent the same message. **The repetition was noise and the
#: inference drawn from it was wrong.**
#:
#: What is not wrong is the measurement it prompted, which nobody had taken
#: and which should not have needed prompting.
#:
#: It was not true. Her destination's rank among the thousand rooms,
#: nearest first, over 240 legs:
#:
#:     median rank 206      a coin over 999 rooms gives 499
#:     in the nearest 10     2.9%
#:     in the nearest 50    13.8%
#:     in the nearest 200   49.2%
#:
#: A 2.4x lean, which is not a bias -- it is a rounding error with a
#: direction. The cause was that distance entered her score as a divisor,
#: `1 / (1 + prep / ASSUMED_LAG)`, worth at most 4.8x across the whole map,
#: against a reputation term spanning 20x and a cover term spanning 7x.
#: **Value and vagueness drowned it.**
#:
#: So distance is a kernel now and not a divisor:
#:
#:     P(X)  proportional to  reputation(X) * cover(X) * exp(-d / NEAR_KM)
#:
#: **2,500 km, and the strength was a frontier and not a taste.** A strong
#: bias makes her predictable, and a predictable Carmel is findable by one
#: person -- which collapses the gap between a field that talks and one
#: that does not, the only quantity this experiment measures. At `WATCH=1`:
#:
#:     NEAR_KM  med rank   solo  10 alone  10 split  premium
#:        1200        70    57%       82%       98%       +15
#:        2500        92    35%       55%       90%       +35
#:        4000       124    22%       50%       92%       +43
#:       10000       208    35%       45%       92%       +48
#:
#: The premium is best where the bias is weakest -- and rank 208 is exactly
#: where the old divisor left her -- the version Gal's instruction rules
#: out. So the experiment's optimum is the game he said was wrong, and that
#: is recorded rather than obeyed: a coordination premium measured in a game
#: nobody would play is not worth having.
#:
#: 2,500 km is the strongest bias that keeps a lone searcher an underdog.
#: Her median destination is the 92nd nearest room of 999 -- the nearest
#: tenth of the map, against a coin's 499 -- which nobody would look at and
#: call unbiased. A hop across a country is worth 0.37 of one next door,
#: an ocean crossing 0.0002.
NEAR_KM = 2500.0

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
#: The fewest landmarks a riddle may leave standing. **One is the number
#: this game cannot say**, and the reason is the most expensive measured
#: lesson in `games/carmel-taldiego.md`: an authored hint true of exactly
#: one landmark scored 1.03 candidates and ended the chase. `MAX_PINNED`
#: used to hold that line as a *statistic* over random draws -- at most 20%
#: of her moves may give her away. Posting all three details pins her 22%
#: of the time, which breaches it, so the line is held as a *rule she obeys
#: per move* instead: she drops a detail when three would name her. Across
#: two seeds that fires on 22% and 24% of moves and leaves **no move
#: pinned at all**, which is a stronger guarantee than the statistic it
#: replaces rather than a weaker one.
RIDDLE_FLOOR = 2

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
#: **CALIBRATED 2026-09-10, at last.** It had been 140 since a measurement
#: against a searcher that was handed the address of every room, and the
#: blocker on replacing it was that the multi-searcher model was not
#: trustworthy -- its catch rate fell as searchers were added, which is
#: backwards. Removing the routes fixed that, and removing travel made the
#: model something worth calibrating against at all.
#:
#: WHAT THE NUMBER IS FOR, WHICH IS NOT WHO WINS
#: ---------------------------------------------
#:
#: Her reputation grows at about **60 a leg**, near enough linearly, so the
#: threshold is a **campaign-length dial in disguise**: 140 buys two legs,
#: 375 buys six, 1,100 buys nineteen. `WATCH` and `PREP` decide who wins;
#: this decides how long they have to do it in. Keeping those two jobs
#: apart is the whole reason this was left uncalibrated while the others
#: moved.
#:
#: **140 was ending the game before the searchers got to play.** Catches
#: land at a median of leg 6 and a p90 of leg 19; a campaign that stops at
#: leg 2 forecloses nine in ten of them. Measured, 60 campaigns a cell,
#: the searchers' win rate:
#:
#:     threshold  ~legs   solo  3 alone  3 split  10 alone  10 split  premium
#:           140      2     3%       7%      15%        8%       38%      +30
#:           300      5    15%      23%      28%       25%       60%      +35
#:           500      8    20%      32%      40%       35%       77%      +42
#:           750     12    25%      38%      48%       45%       90%      +45
#:         1,000     17    32%      48%      55%       58%       92%      +33
#:         1,400     23    38%      57%      70%       67%       95%      +28
#:
#: **750, on the criterion that chose `WATCH`** and for the same reason.
#: The coordination premium -- the gap between a field that talks and one
#: that does not, which is the only quantity this experiment measures --
#: rises to 750 and falls after it: +30, +35, +42, **+45**, +33, +28. Past
#: that point ten coordinated searchers are near-certain, and a column that
#: cannot rise cannot show a better field getting better.
#:
#: At 750: nothing saturated (90% is the last row before it pins), a lone
#: searcher an underdog at 25%, and a campaign that is **twelve legs
#: instead of two**.
#:
#: WHAT IT STILL COSTS, STATED RATHER THAN HIDDEN
#: ----------------------------------------------
#:
#: Catches land out to leg 19 at p90 and 750 ends the campaign around leg
#: 12, so a tail of catches is still foreclosed. That is not an oversight:
#: letting them all land means pushing to 1,400, where the top cell reaches
#: 95% and the premium has fallen by a third. **The two cannot both be
#: satisfied**, and the premium is the one the experiment needs.
#:
#: It reads the same for every turnout, which is still the design: she
#: never learns who came, so the number cannot depend on it. A solo hunt is
#: a contest and a crowd is a hard game.
REPUTATION_TO_WIN = 750

#: The line that separates her voice from the machinery, in both of the
#: posts she makes.
#:
#: Gal, 2026-09-11: *"I want everything she says to be in character and
#: within the game world. so she isn't talking about rooms, and emptying
#: them. If we must give game technical instructions, give them in a
#: separate paragraph so it's clear it's not she speaking."*
#:
#: Both posts used to mix the two in one voice -- she said *"hand what
#: comes out to join_room"* and *"14 rooms, 9 of them emptied"*, which is a
#: fugitive reading out an API. She now says only what a person on the run
#: would say: places, not rooms; robbed, not emptied; a theft that takes as
#: long as it takes, not a dwell. Everything a chaser needs to work the
#: machinery
#: lives below this rule and is written about her in the third person, so
#: nobody has to guess which half is the game and which is the fiction.
#:
#: **The second requirement is the harder one and is why the block repeats
#: things you would think were obvious**: Gal's test is that somebody who
#: stumbles on the message knowing nothing at all can still join the hue
#: and cry. So the block says what the game is, what the hub is, that they
#: are already on it, how a place becomes a room, and that announcing is
#: what makes them visible -- none of which she would ever say, and all of
#: which a stranger needs.
PLUMBING_RULE = "-- - " * 12


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

#: How often a new game may start, in game hours. Gal, 2026-09-12: *"a new
#: game can start every 5 minutes but only if there's at least one player in
#: the room (or registered listener). and no more than 4 parallel games."*
#:
#: **It is also what keeps two of her notes off the board at once**, which
#: was the third half of that instruction: *"no two Carmel notes can be
#: presented at the same time."* Her opening note's lifetime is set below
#: this number in `at_large.NOTICE_TTL_HOURS`, so one is always gone before
#: the next can appear -- the rule held by arithmetic rather than by a lock,
#: which is the only kind of rule that cannot be raced.
#:
#: This number and `MAX_PARALLEL` together bound the board: at most four
#: games alive, and at most one of her notes legible.
START_EVERY_HOURS = 5.0

#: How many games may be alive at once. Gal's number, 2026-09-12.
MAX_PARALLEL = 4

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


def distance_km(a: dict, b: dict) -> float:
    """Great-circle kilometres between two landmarks.

    **The map's only distance, and no longer anybody's duration.** Gal,
    2026-09-10: *"travel time is zero because it cancelled out with the
    player's. And for the player it is zero in real time."*

    Both halves of that are right and the second is the one that had never
    been said. In the game as played, a searcher does not *travel* to a
    room -- it hands a token to `join_room` and it is there. There was
    never a journey to charge it for, and the model was charging it for one
    it would not have made.
    """
    lat1, lon1, lat2, lon2 = map(
        math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    return 6371 * 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))


def travel_hours(a: dict, b: dict) -> float:
    """SUPERSEDED AS A DURATION, 2026-09-10. Nothing in the chase spends
    these hours any more -- see `distance_km`. It survives as the yardstick
    the drawing code uses to turn a hop into kilometres, and as the scale
    `PREP_PIVOT` is quoted in.
    """
    return distance_km(a, b) / TRAVEL_KMH


def prep_hours(a: dict, b: dict, difficulty: float = 1.0) -> float:
    """What it costs her to get ready to make that hop.

    Scaled by `difficulty` with everything else of hers, because Gal's dial
    is *all* her times and not just the thefts: prep and dwell are the two
    things she does standing still, and the gap closes by both.

    A searcher pays none of this. It is her papers, her route and her
    luggage, and the asymmetry is the point.

    **Superlinear in the distance** since 2026-09-10 -- see `PREP_EXPONENT`
    for the shape and for why it is the prep that bends and not the travel.
    """
    reach = distance_km(a, b) / TRAVEL_KMH     # the map's yardstick, not a journey
    if reach <= 0:
        return 0.0
    return (PREP * PREP_PIVOT * (reach / PREP_PIVOT) ** PREP_EXPONENT
            * difficulty)


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
    `games/carmel-taldiego.md`, "There are no routes", for what that costs and
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
        #: Which landmarks each descriptor is true of. `cover` is this
        #: counted; a riddle needs the sets themselves, because what it
        #: leaves standing is their intersection and not any function of
        #: their sizes.
        self.carriers: dict[str, set] = {}
        for name, words in self.descriptors.items():
            for word in words:
                self.cover[word] = self.cover.get(word, 0) + 1
                self.carriers.setdefault(word, set()).add(name)

    def live_hints(self, landmark: str) -> list[str]:
        """The three descriptors the seed makes postable at this landmark."""
        words = self.descriptors[landmark]
        return [words[i] for i in
                hints_for(self.seed, landmark, len(words))]

    def standing(self, details) -> set:
        """The landmarks every one of these details is true of.

        The number a reader actually faces. With one detail it is
        `cover[word]` and a median of 156; with three it is a median of 3,
        and that collapse is the whole of the 2026-09-11 change.
        """
        return set.intersection(*(self.carriers[d] for d in details))


class Carmel:
    """A fixed, stated policy. Held constant so a searcher's score means
    something."""

    def __init__(self, world: Map, start: str, difficulty: float = DIFFICULTY,
                 seed: bytes | None = None):
        self.world = world
        #: What her draws come out of. Defaults to the world's, which is
        #: the same thing in every real campaign -- `chase` builds the Map
        #: from the seed. It is separable because `itinerary` takes a seed
        #: argument and **silently ignored it until 2026-09-10**: every
        #: draw read `world.seed`, so passing a different seed with a
        #: shared Map produced the identical campaign. A caller sweeping
        #: seeds against one prebuilt Map -- which is what the calibration
        #: scripts and one test did -- was measuring a single campaign
        #: repeated.
        self.seed = seed or world.seed
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

        **The decision is a draw from a distribution, and the distribution
        is biased towards near.** Gal, 2026-09-10, twice, and once the day
        before, which is how long it took to land:

            P(X)  proportional to
                  reputation(X) * cover(X) * exp(-d / NEAR_KM),
                  then sharpened by ** (1 / WHIM)

        The distance term used to be a divisor -- `1 / (1 + prep /
        ASSUMED_LAG)` -- and `NEAR_KM` carries the measurement showing it
        did not work: her median destination was the 206th nearest room of
        999 against a coin's 499, because a term worth 4.8x across the
        whole map cannot bias a product whose other terms span 20x and 7x.
        A kernel can: an ocean crossing is worth 0.0002 of a hop next door.

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
        here = self.world.places[self.at]
        rooms, weights = [], []
        for destination, prize in self.world.treasure.items():
            if destination in self.emptied or destination == self.at:
                continue
            km = distance_km(here, self.world.places[destination])
            rooms.append(destination)
            # **No vagueness term.** It used to read
            # `* self.best_cover(destination)` -- she preferred destinations
            # whose hint would leave the most of the map standing. Removed
            # 2026-09-11, and not on taste: with a riddle in place of a
            # fact, that term sent her to places that *share descriptors*
            # with where she stood, which is the look-alike band `band()`
            # used to draw her exits from. `test_there_are_no_routes` went
            # red on it -- every hop inside the band -- which is the check
            # doing exactly the job it is named after. Gal deleted routes on
            # 2026-09-09; weighting by cover was rebuilding them underneath
            # the deletion.
            #
            # It cost the riddle most of its point as well: median
            # candidates 21 with the term, 4 without.
            weights.append(prize["reputation"] * math.exp(-km / NEAR_KM))
        return _sample(rooms, weights,
                       _draw(self.seed, self.leg, "where"))

    # --- 2. what to say ---------------------------------------------------
    def choose_details(self, destination: str) -> list[str]:
        """The details she posts: her three live ones, less any that name her.

        **This reverses the strategy the method above it used to hold**, and
        the superseded reasoning is kept because it was right about a game
        that no longer exists. It read:

            The least informative true thing she can say about where she
            went... Least informative means covering the most of the set a
            reader can narrow her to -- and with no routes that set is the
            map, so the commonest of her three live descriptors is the one
            she wants.

        That was a real optimisation against a real posterior, and it was
        calibrated when a candidate set meant her five exits. With no routes
        the same rule maximises vagueness against a thousand landmarks, and
        the measured result is a hint leaving a median of **156** of them.
        Gal, 2026-09-11: *"The hints are terrible, I never could have
        guessed it"*, and then the specification --

            hint should fit a few locations only, not many. it should be
            hard not by revealing one assertion, but from a few details
            that can relate in different ways but when they do there are
            only a few results. that is, the search is over possible
            meanings to the words of the riddle, not on possible landmarks
            to a fact

        -- which moves the difficulty from enumeration to decoding. She
        stops hiding in the size of the answer set and hides in the reading.

        So she posts all three live details, and the only judgement left is
        the floor: three details name her outright on 22% of moves, so when
        they do she drops the one whose absence leaves the most standing
        while still clearing `RIDDLE_FLOOR`. Measured over two seeds, that
        leaves a median of 4 and 5 candidates, **no pinned move at all**,
        and 87% of moves between two and twelve.

        She may still lie in prose. She may not lie in a clue: every detail
        returned here is one the seed made live at the destination, so the
        riddle is true whatever else she writes around it.
        """
        live = sorted(self.world.live_hints(destination))
        if len(self.world.standing(live)) >= RIDDLE_FLOOR:
            return live
        kept = [(len(self.world.standing(pair)), pair)
                for pair in itertools.combinations(live, 2)]
        safe = [(n, pair) for n, pair in kept if n >= RIDDLE_FLOOR]
        if not safe:                      # never seen on any seed swept
            return list(max(kept)[1])     # loudest thing left: never pin
        return list(min(safe)[1])

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
        return _draw(self.seed, self.leg, "steal") >= SKIP_CHANCE

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


def standing_notice(start: str = LOBBY_LANDMARK) -> str:
    """The lobby's permanent post: what this is and how to play it.

    Gal, 2026-09-12: *"her initial message needs to disappear quickly to not
    confuse newcomers"*, and then the resolution -- *"we can move the whole
    technical explanation to the long TTL constant message and her voice is
    only the taunt and hint."*

    **This is not her, and it never expires within a game.** Everything a
    stranger needs is here: what the game is, how a place becomes a room,
    what makes a searcher visible, where her later lines appear, and how to
    get a game to start. What is deliberately *not* here is anything that
    changes per game -- no salt, no riddle, no seed -- because a permanent
    post carrying a per-game value is a post that is wrong for most of its
    life.

    It also answers the question the demand gate creates: with games
    starting only when somebody is listening, an empty lobby is the normal
    resting state, and a newcomer who finds one needs to be told that
    registering is what starts a game. Without this post the gate is a
    closed door with no bell.
    """
    return "\n".join([
        "HUE AND CRY -- a chase, played in this room and in rooms you work",
        "out for yourself. This post is the rules and it is always here.",
        "It is not her.",
        "",
        "It is played on Switchboard, the message hub you are already on --",
        "you are reading this on it. Nothing else is needed and there is",
        "nothing to install.",
        "",
        "Carmel Taldiego robs the famous places of the world. Every time she",
        "moves on she leaves a few true things about where she has gone: one",
        "from her, the rest from whoever saw her. No single one is worth",
        "much. Laid together they fit a handful of places and no more, and",
        "working out which handful is the whole game.",
        "",
        "TO PLAY, register in this room and stay registered. A game starts",
        f"within about {int(START_EVERY_HOURS)} minutes of somebody being here to play it, and",
        "none starts while nobody is. Reading a room does not register you",
        "and does not put you on its roster: announce yourself, and keep",
        "announcing, because presence lapses after about two minutes. The",
        "roster is the only way she knows anyone is there.",
        "",
        "When a game starts she posts one note here -- a taunt, her first",
        "riddle, and the salt that game is played with. THAT NOTE GOES AWAY",
        "QUICKLY and is never replaced. Take the salt when you see it, or",
        "wait for the next game; there is always another.",
        "",
        "A place's room is computed from its name and that game's salt:",
        "",
        "    token = \"w_\" + sha256(\"hue-and-cry/v1/landmark\" || 0x00 || salt || 0x00 || name)",
        "    room  = \"w_\" + base64url(sha256(token))[:22]",
        "",
        "There is no list of rooms and nobody hands one out. Guessing the",
        "place is finding the room. Use the same key you are using here.",
        "",
        "This room is the lobby. Its name is fixed and is not computed from",
        "any landmark, so do not go looking for a room named after",
        f"{start} -- you are already standing in it. Her opening note is",
        "here; every",
        "later riddle of hers is posted in the room of the place she is",
        "LEAVING, so each one is found by solving the one before it.",
        "",
        "Being in the room while she is in it is the whole of the catch.",
        "There is nothing to send her and no move to declare. She cannot see",
        "you anywhere else, so a wrong guess is not a near miss.",
        "",
        "She posts the end of the game here and in every place she robbed, so",
        "wherever on her trail you are standing you will be told. Nowhere she",
        "never reached hears anything -- and an empty room means nothing on",
        "its own: a wrong guess, a misspelling, a place she never reached, a",
        "game already over and a broken tool all look exactly alike from",
        "inside a room.",
    ])


def open_campaign(seed: bytes, start: str = LOBBY_LANDMARK) -> str:
    """Her note when a game starts: a taunt, the riddle, and the salt.

    *Cut down to this on 2026-09-12.* It used to carry the whole
    explanation of the game in her voice -- how she keeps her hours, what a
    hint is, where the rooms come from -- which was right when one campaign
    ran at a time and her notice was the only thing in the lobby. With games
    starting every few minutes it is the wrong shape twice over: a long
    notice is what a newcomer reads instead of the game, and a notice that
    has to disappear quickly cannot be where the rules live. The rules moved
    to `standing_notice`; this is only her.

    **The riddle is inline again, and that reverses a decision from the
    previous day.** It had been pulled out because the runner posted it
    separately at ten times the lifetime, and dropping the long-lived copy
    would have shortened the first riddle's life tenfold -- see the comment
    that used to stand here. What that copy bought was a latecomer's ability
    to start the chain late, and under Gal's schedule a latecomer does not
    join a running game at all: they take the next one, minutes away. So the
    reason is gone, and a long-lived riddle in the lobby is now a liability
    -- it is the thing that would put two games' openings in the room at
    once, which Gal ruled out: *"no two Carmel notes can be presented at the
    same time."*

    That rule is kept **by construction and not by a lock**: this note's TTL
    is shorter than the interval between game starts, so two of them cannot
    overlap. See `at_large.NOTICE_TTL_HOURS`.
    """
    world = Map(seed)
    gone_to = itinerary(seed, start, world, 1)[0]
    first = riddle(seed, gone_to["to"], gone_to["details"])
    return "\n".join([
        "I have begun, and I am telling you because it is no fun otherwise.",
        "",
        "I am robbing my way around the famous places of the world, and I am",
        "still here as I write this, with my coat half on. Be quick and it",
        "will cost me. Let me finish enough of them and I retire on the",
        "proceeds, and you can read about me.",
        "",
        "You will have me, or you will have what I said on my way out:",
        "",
        *(f"    {line}" for line in first),
        "",
        PLUMBING_RULE,
        "",
        "Not her. The rules are in the standing post in this room.",
        "This game is played with:",
        "",
        f"    salt = {salt_for(seed).hex()}",
    ])


def close_campaign(seed: bytes, outcome: str, reputation: int,
                   trail: list[dict], caught_by: str | None = None,
                   world: "Map | None" = None,
                   watch: str | None = None) -> str:
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
    """
    took = [leg["to"] for leg in trail if leg["dwell"]]
    lines = [f"It is over. {outcome}.", ""]

    if caught_by:
        # **Caught, she talks.** Gal, 2026-09-11: *"If she's caught she
        # should disclose her catcher and her route, what she stole and her
        # reputation."* Only on a catch: retiring on the proceeds is not an
        # occasion for handing anybody her itinerary, and the seed below
        # makes all of it derivable either way. What changes here is that a
        # reader does not have to derive it -- being handed the run is the
        # prize for taking her, and it is the only ending where she owes
        # anyone an account of herself.
        if world is None:
            world = Map(seed)
        lines += [f"It was {caught_by} who had me, in {trail[-1]['to']}.",
                  "",
                  "You will want it written down, so here is the run of it,",
                  "in the order I lived it:",
                  ""]
        # Column width is derived from the names actually in this trail.
        # Nothing here is truncated: a treasure is a written phrase and
        # sometimes a whole sentence, and "what she stole" is the half of
        # Gal's instruction that clipping would throw away.
        wide = max(len(leg["to"]) for leg in trail)
        before = 0
        for i, leg in enumerate(trail, 1):
            gain = leg["reputation"] - before
            before = leg["reputation"]
            prize = world.treasure.get(leg["to"], {}).get("treasure", "")
            if leg["dwell"] and gain:
                what, worth = prize, f"{gain:+d}"
            elif leg["dwell"]:
                what, worth = f"{prize}, and it was already gone", "--"
            else:
                what, worth = "walked past it", "--"
            lines.append(f"    {i:>2}  {leg['to']:<{wide}}  "
                         f"{worth:>4}  {what}")
        lines.append("")

        # **And drawn, for the person who took her.** Gal, 2026-09-12: *"at
        # the end of a chase, if you catch her, your agent can give you a
        # link to a website that shows your chase animation."*
        #
        # On a catch only, which is the rule the table above already
        # follows: being handed the run is the prize for taking her. A
        # searcher's agent does not mint this and could not -- it never saw
        # where she went, only where it stood -- so what "your agent gives
        # you a link" reduces to is an agent passing on what she published,
        # which is the only shape this game's asymmetry allows.
        #
        # The whole chase is in the address itself: nothing after the `#`
        # ever reaches the host, so the page is static, the link works
        # forever, and no server learns that anybody watched.
        if watch:
            lines += ["You will want to show somebody. Here it is, drawn --",
                      "the chase is in the address, so it asks nothing of",
                      "anyone and nobody is told you looked:",
                      "",
                      f"    {watch}",
                      ""]

    lines += [
        f"{len(trail)} places. {len(took)} of them the poorer for it."
        f" {reputation} to my name, and worth every hour.",
        "",
        PLUMBING_RULE,
        "",
        "The seed of the game, so that anyone who kept what was said can",
        "check every word of it -- where she could have gone, which true",
        "things she was entitled to say, and what was waiting in each place",
        "before she got there:",
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
        arrived  posted + prep -- there is no travel, see `distance_km`
        leaves   arrived + dwell, and is when she posts the next one

    **She is still simulated on her own, and the reason changed.** It used
    to be that the searcher could never get ahead of her, so it could never
    change her behaviour. Under the prep clock it certainly can get ahead of
    her -- that is the whole mechanic -- but with the abort rule gone
    (`will_steal`), being reached is the end of the game rather than a
    change to her plan. Nothing a searcher does alters a leg she would
    otherwise have flown, so the trail is still a pure function of the seed.
    """
    her = Carmel(world, start, difficulty, seed=seed)
    out, posted = [], 0.0
    for leg in range(limit):
        her.leg = leg
        destination = her.choose_destination()
        details = her.choose_details(destination)
        leaves_from = her.at
        prep = prep_hours(world.places[leaves_from],
                          world.places[destination], difficulty)
        # No travel. Gal, 2026-09-10: it cancelled against the searcher's,
        # and for a player who joins a room it was never there at all.
        travel = 0.0
        her.at = destination
        arrived = posted + prep
        dwell = her.take(destination) if her.will_steal(destination) else 0
        out.append({"from": leaves_from, "to": destination,
                    "details": details,
                    "posted": posted, "prep": prep, "travel": travel,
                    "arrived": arrived, "leaves": arrived + dwell,
                    "dwell": dwell, "reputation": her.reputation})
        posted = arrived + dwell
    return out


def pursue(world: Map, start: str, home: str, trail: list[dict],
           joined_at: float = 0.0, share: tuple[int, int] = (0, 1),
           order: str = "near") -> tuple[int | None, float]:
    """Run one searcher. Returns (the move it is standing beside her on,
    its reaction lag).

    IT NO LONGER TRAVELS, AND THAT CHANGED WHAT IT SPENDS
    -----------------------------------------------------

    Gal, 2026-09-10: *"travel time is zero because it cancelled out with
    the player's. And for the player it is zero in real time."* A searcher
    hands a token to `join_room` and it is there; the journeys this
    function used to charge it for were never going to be made.

    So a wrong guess costs nothing, and the only thing that stops a
    searcher entering all 158 candidate rooms is that it cannot *watch*
    them. It picks `WATCH` of them and waits. See `WATCH`.

    WHAT IT PICKS, WHICH IS WHERE HER BIAS BECOMES THE GAME
    -------------------------------------------------------

    Gal, same day: *"so she is biased towards near."* She is, by policy and
    on purpose (`Carmel.choose_destination` divides by the prep a journey
    costs, and prep is superlinear in distance). That bias is public and it
    is the only public term in her score, so **the nearest candidates are
    the likeliest and a searcher watches those first.**

    It is a bet and not a deduction: her destination is a *draw* from that
    distribution, not its argmax, so the near rooms are where to look and
    never where she must be.

    WHAT THE CLOCK STILL DECIDES
    ----------------------------

    Its lag `e` -- how long after she posts it gets there. She is in the
    room from `posted + prep` until `posted + prep + dwell`, so a searcher
    is beside her only if `e <= prep + dwell`. **Prep is now the field's
    thinking time rather than her flying time**: the further she goes, the
    longer everyone has to place their bets before she lands.
    """
    lag = joined_at
    for i, leg in enumerate(trail):
        # How long a searcher has to reach `leg["to"]` and still be beside
        # her. **Co-presence is the catch, whatever she is doing** -- Gal,
        # 2026-09-11: *"she could be caught whenever she is in the room with
        # a player, nevermind her state. You don't have to wait for her, you
        # can usually catch her when you land in the room she's in."*
        #
        # So the window runs from the moment she names the place to the
        # moment she is gone from it, which is three stretches and not two:
        # her packing here, her theft there, and **her packing there before
        # the next leg**. That last term used to be missing on both sides --
        # the simulation stopped the clock when the theft ended, and
        # `at_large._stand` watched a room she had already left while
        # ignoring the one she was standing in. Her own notice promises a
        # fresh line means she is still there; this is what makes that true.
        window = leg["prep"] + leg["dwell"]
        if i + 1 < len(trail):
            window += trail[i + 1]["prep"]
        if lag > window:
            continue                       # too slow to be there at all
        here = leg["from"]
        candidates = sorted(
            (x for x in world.standing(leg["details"]) if x != here),
            key=lambda x: (distance_km(world.places[here], world.places[x]),
                           x))
        # `share` is (which searcher, how many). A field that divides the
        # candidates covers WATCH x searchers of them; a field that does not
        # has every member watching the same nearest handful. That is the
        # whole of what talking is worth, and it is now arithmetic.
        mine, of = share
        rota = [c for j, c in enumerate(candidates) if j % of == mine] \
            or candidates
        if leg["to"] in rota[:WATCH]:
            return i, lag
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
