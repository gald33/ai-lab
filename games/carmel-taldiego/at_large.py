"""She runs, on a real hub and a real clock.

    python3 games/carmel-taldiego/at_large.py --dry-run      # the schedule, no hub
    python3 games/carmel-taldiego/at_large.py --once         # one campaign, live
    python3 games/carmel-taldiego/at_large.py                # campaign after campaign

Everything else in this directory simulates her: `carmel.itinerary` is a pure
function of a seed and `chase` runs a searcher nobody wrote. This module is
what makes her *available* -- it puts the same trail on a Switchboard hub in
wall-clock time, so the searcher can be anybody.

WHAT IS ACTUALLY NEW HERE, WHICH IS ONLY THE CLOCK
--------------------------------------------------

Her decisions are not re-made here. `itinerary` still decides where she goes,
what she says and how long she stands still, and it still decides all of it
from the seed before the campaign opens. This module reads that trail and
performs it: it posts what she was always going to post, at the wall-clock
moment the trail says, and it watches the room she is standing in.

So there is **nothing to settle and nobody to referee** -- `CLAUDE.md`,
"Carmel Taldiego has no manager and no settler. It has Carmel." The catch is
not adjudicated: a searcher who is in the room while she is in it is on her
roster, and that is the whole of it. She reads `agents()`; if somebody else is
there, she has been caught. No message is parsed, no verb is recognised, and
a searcher who says nothing at all still catches her by standing there.

THE ONE THING A SEARCHER NEEDS, AND WHY IT IS NOT AN SDK
--------------------------------------------------------

The lobby notice carries the recipe and the salt (`carmel.open_campaign`), and
the gap between what it gives and what Switchboard's tools do is exactly one
SHA-256 -- `secret_matrix.RECIPE`. That is deliberate and is checked in
`test_rooms_from_names`: an entrant needs a shell and no library from us.
`CLAUDE.md`: *"an entrant SDK is never the answer."*

THE CLOCK, WHICH IS A GUESS WITH A REASON
------------------------------------------

`HOUR_SECONDS` maps her game hours onto real seconds and is the only number
here that changes what kind of game this is. One game hour is one real minute,
which makes a campaign about **80 minutes** and a leg about **six**.

The floor is that a leg has to be long enough for an agent to read a hint,
think of a landmark, hash it and join the room -- minutes, not seconds. The
ceiling is that a campaign should be one sitting, so that somebody who reads
the notice can still be playing when it ends. Six minutes and eighty are the
two numbers that fit between those, and they are a guess in the sense that
nobody has watched a real searcher yet. Re-measure with `--dry-run` after
changing it; every other number here is derived from it.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import secrets
import threading
import sys
import time
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import treasures as T  # noqa: E402
from secret_matrix import room_token, salt_for  # noqa: E402


def _derived_key(info: bytes) -> str:
    """A workspace key from a constant, in the shape Switchboard wants:
    32 bytes, urlsafe-base64, unpadded."""
    return base64.urlsafe_b64encode(
        hashlib.sha256(info).digest()).decode().rstrip("=")


#: Real seconds to one of her game hours. See the module docstring -- this is
#: the only number here that decides what kind of game it is.
HOUR_SECONDS = 60.0

#: How long the lobby notice lives, in game hours.
#:
#: **This is Gal's constraint (2026-09-10): "making sure her lobby message is
#: long gone before the game ends."** It is not a margin picked to satisfy it,
#: though -- it is `JOIN_WINDOW_HOURS`, which already exists and already means
#: the right thing: *"How long people take to notice the notice and set off"*,
#: the parameter her head start is calibrated against. After it, the notice
#: has done its job; anybody arriving later is joining a game in flight, which
#: the hints in the rooms already support.
#:
#: Measured against 60 campaigns at `REPUTATION_TO_WIN = 750`: a campaign runs
#: a median of **80 game hours** and a p10 of 28, so the notice is gone about
#: a seventh of the way in. Reproduce with `--dry-run`.
#: **Sized in real minutes, not in game hours** (Gal, 2026-09-11: *"The game
#: time is less important. First I'd make the real world time seconds to
#: minutes per riddle."*). It was `C.JOIN_WINDOW_HOURS` -- twelve -- chosen
#: when a campaign ran for days of game time, and a twelve-hour notice was
#: comfortably inside one. With a riddle she is caught in a median of six
#: game hours, so the old value outlived every campaign instead of dying
#: long before it, and no value can do better while a quarter of campaigns
#: end inside forty seconds.
#:
#: What stops two salts being legible at once was never this number: it is
#: the floor in `plan`, which holds whatever the notice costs and is tested
#: separately. This is a **join window** and nothing else, so it is set to
#: what a person needs to read a notice and join a room.
#: How long her opening note stays readable. **Below `START_EVERY_HOURS`,
#: and that is the whole reason for the number.** Gal, 2026-09-12: *"no two
#: Carmel notes can be presented at the same time"* -- and a note that dies
#: before the next game may begin cannot overlap one, so the rule is held by
#: arithmetic and not by a lock. `test_two_of_her_notes_are_never_legible_at_once`
#: fails the moment this rises above the interval.
#:
#: *It was 12 for one day, and the reasoning that put it there is worth
#: keeping because it was correct about a game that no longer exists.* The
#: salt lives in this note and nowhere else, so a note dying before its
#: campaign left every later riddle uncomputable -- measured live, a
#: searcher joined two minutes in, found a riddle and no salt, and was
#: stuck. The fix then was to make the note outlive the campaign (12h), and
#: `test_the_salt_outlives_the_campaign_it_belongs_to` pinned it.
#:
#: **What dissolves that argument is the schedule, not a change of mind.**
#: A newcomer no longer needs a salt to survive an 84-minute campaign,
#: because a fresh game is never more than `START_EVERY_HOURS` away: you
#: take the next one. So the note may be short, and now must be -- a
#: long-lived note is exactly what would put two games' openings in the
#: lobby at once.
NOTICE_TTL_HOURS = 4.0

#: The quiet between campaigns, in game hours. Two hours is two minutes: long
#: enough that the close and the next open are not the same moment on a
#: reader's screen, short enough that she is a standing invitation.
INTERMISSION_HOURS = 2.0

#: How long a live game tolerates an empty lobby before closing itself.
#: Gal, 2026-09-12, agreeing that a game whose searchers have gone should
#: end: without it the four slots fill in twenty minutes and stay full for
#: the eighty-four an unopposed campaign runs, so the cap that was meant to
#: bound the board would instead bar every newcomer from it.
#:
#: **It reads the lobby and not her own room, which is not a detail.** She
#: only ever watches the place she has just named -- a searcher who guessed
#: wrong is invisible to her -- so "nobody is chasing me" is not a thing she
#: can observe from where she stands. The lobby roster is the only honest
#: signal, and it is the same one the start gate reads.
ABANDON_AFTER_HOURS = 10.0

#: How long the standing rules post lives, and it is reposted at half this
#: so the lobby is never without one. Long, because it is the one thing in
#: the room that is true between games: it carries no salt, no riddle and no
#: seed, so there is nothing in it that can go stale.
#:
#: Four real hours. The cap Switchboard puts on a message is 24 real hours,
#: so this is well inside it -- and short enough that a change to the rules
#: reaches the lobby the same afternoon rather than the next day.
RULES_TTL_HOURS = 240.0

#: What a hint left in a room is worth after she has gone: the rest of the
#: campaign. A searcher who works out leg 3 an hour late should still find
#: what she said there and be able to follow it, which is the design's *"you
#: will find me there or you will find what I said next"*. It dies with the
#: campaign because the salt moves and the room is nobody's next game.
HINT_TTL_HOURS = 120.0

#: How often she looks at the roster of the room she is standing in. Five
#: seconds against a leg of about six minutes: fine enough that the catch is
#: not luck, coarse enough not to hammer the hub.
POLL_SECONDS = 5.0

#: How long the hub may stay unreachable before she gives up the campaign,
#: and how long she waits between attempts while it is.
#:
#: **This exists because one dropped connection used to end everything.**
#: Found by playing rather than by testing, 2026-09-11: a campaign died 150
#: seconds in on a single `[SSL: UNEXPECTED_EOF_WHILE_READING]` raised by
#: `room.heartbeat` inside `_stand`. Nothing was retried and nothing was
#: caught, so the whole game went with it -- no close in the lobby, hints
#: left in rooms pointing at a fugitive who was never coming, and a searcher
#: standing in the right room forever.
#:
#: The arithmetic says this was never survivable. `_stand` polls twice per
#: `POLL_SECONDS` -- a roster read and a heartbeat -- so an eighty-minute
#: campaign makes about **1,900 hub calls**, every one of them a chance to
#: end it. At any believable per-call failure rate that is not a risk, it is
#: a certainty with a wait attached.
#:
#: Ninety seconds because it must outlast a blip and not a crash: it is well
#: past a dropped TLS connection and a hub restart, and well short of a leg,
#: so a campaign that gives up has really lost the hub rather than hiccupped.
OUTAGE_SECONDS = 90.0
RETRY_SECONDS = 2.0

#: The four ways a campaign ends, **in her voice**, because the runner puts
#: these words in her mouth and `carmel.close_campaign` prints them above
#: the rule where only she speaks.
#:
#: The outage line used to read *"The hub went dark on me"*, which is a
#: fugitive naming a message broker. `test_she_never_speaks_in_machinery`
#: did not catch it because it checked one outcome it made up itself rather
#: than the ones the runner actually uses -- a sample instead of the set,
#: which is the same defect as a hand-maintained path list. The test reads
#: this dict now, so a fifth ending cannot be added in machinery.
OUTCOMES = {
    "caught": "You have me",
    "wins": "I retire on the proceeds",
    "spent": "I ran out of road",
    "lost": "It ended badly, and not by your hand",
    "abandoned": "Nobody came, so I have stopped bothering",
}

#: The lobby is salt-free -- `carmel.LOBBY`'s reasoning: a lobby that moved
#: with the game salt could not be found by anybody who was not already
#: playing, and the salt is *inside* the notice, so a salted lobby could never
#: be found at all. An empty salt is what "salt-free" has to mean given that
#: rooms are `room_token(name, salt)` and there is only one such function.
LOBBY_SALT = b""

#: The channel she writes on. One channel, because there is one surface.
CHANNEL = "hue"

#: What every room in this game is encrypted with, **published on purpose**.
#:
#: `rooms_from_names.py` is explicit that *"knowing a landmark's NAME, plus
#: the game's salt, is exactly what admits you"*, and that only works if the
#: workspace key is not a second secret: a searcher who thinks of `Uluru`,
#: hashes it with the salt and calls `join_room` must be in. So **all of the
#: game's secrecy is in the token and none of it is in the key**, and the key
#: is derived from a constant so that it is publishable by construction
#: rather than by somebody remembering to publish it.
#:
#: It is deliberately **not** `SWITCHBOARD_KEY` from the environment. That is
#: a workspace key for the hub this happens to run on, and a game that needed
#: it would be a game you could only join by being handed a credential --
#: which is the invite mechanism this whole construction exists to replace.
#: A room whose key is a secret is not a lobby.
LOBBY_KEY = _derived_key(b"hue-and-cry/v1/room-key")


def lobby_token() -> str:
    """The lobby's token, which is fixed and publishable."""
    return room_token(C.LOBBY, LOBBY_SALT)


# --- the schedule ---------------------------------------------------------
#
# Pure arithmetic, in game hours, so that Gal's constraint is a thing a test
# can fail on rather than a thing this file asserts about itself.


def plan(campaign_hours: float,
         notice_ttl: float | None = None,
         intermission: float | None = None) -> dict:
    """When the notice dies, when the campaign closes, when the next opens.

    **NOT THE SCHEDULE ANY MORE, since 2026-09-12.** Nothing in `forever`
    calls this: games now start on a fixed interval gated by demand
    (`may_start`), not when the previous one closes, and up to
    `C.MAX_PARALLEL` run at once. The floor described below -- the next
    campaign never opening while the last notice is readable -- was how "no
    two salts at once" used to be guaranteed; it is now guaranteed by
    `NOTICE_TTL_HOURS < C.START_EVERY_HOURS`, which is arithmetic rather
    than sequencing and survives four games running together.
    
    It is kept, unused by the runner, because `--dry-run` reads it and
    because deleting the reasoning below would delete the only record of why
    the old guarantee existed. **A reader should not mistake it for what
    governs the runner**, which is what this paragraph is for.

    All in game hours from the moment the notice goes up.

    The last line is the whole point. **The next campaign never opens while
    the last one's notice can still be read**, whatever happened to the
    campaign -- so two salts are never legible at once and a reader can never
    be looking at an address from a game that is over. Ordinarily the campaign
    outlives its own notice by a long way and the floor does nothing; it earns
    its place on the campaign that ends early.

    Measured over 60 campaigns: **one** ended inside its own 12-hour notice
    (the shortest ran 6.4 hours). One in sixty is exactly the rate at which a
    rule that is not enforced gets believed anyway.
    """
    # Read off the module rather than frozen into the signature's defaults.
    # A default binds at import and a constant that cannot be turned is a
    # constant nothing can test against: the loop's own check needs to see
    # the floor do its work, which only happens on a notice that outlives a
    # campaign, and that is a setting rather than a seed you go looking for.
    notice_ttl = NOTICE_TTL_HOURS if notice_ttl is None else notice_ttl
    intermission = INTERMISSION_HOURS if intermission is None \
        else intermission
    closes = float(campaign_hours)
    notice_gone = float(notice_ttl)
    return {
        "opens": 0.0,
        "notice_gone": notice_gone,
        "closes": closes,
        "next_opens": max(closes, notice_gone) + intermission,
    }


def may_start(live: int, listeners: int, waited: float,
              max_parallel: int | None = None,
              start_every: float | None = None) -> bool:
    """May another game begin right now? Three conditions, all necessary.

    Gal, 2026-09-12: *"a new game can start every 5 minutes but only if
    there's at least one player in the room (or registered listener). and no
    more than 4 parallel games."*

    **Pure on purpose.** The supervisor that uses this runs games in
    threads, and a thread plus a fake clock is a test that passes for
    whatever reason the scheduler happened to interleave. The policy is the
    part worth checking exhaustively, so it is a function of three numbers
    and nothing else -- no hub, no clock, no thread. `test_may_start_*`
    covers every boundary; the threading above it is thin enough to read.

    `listeners` is how many are registered in the lobby who are not her.
    **Zero means no game starts**, which is the demand gate: an unopposed
    campaign posts riddles nobody reads, wins by default, and fills the
    record with games that answer no question. It also means an idle lobby
    costs nothing at all.
    """
    if listeners <= 0:
        return False
    max_parallel = C.MAX_PARALLEL if max_parallel is None else max_parallel
    start_every = C.START_EVERY_HOURS if start_every is None else start_every
    if live >= max_parallel:
        return False
    return waited >= start_every


def hours(seconds: float) -> float:
    return seconds / HOUR_SECONDS


def seconds(game_hours: float) -> float:
    return game_hours * HOUR_SECONDS


# --- the room she is standing in ------------------------------------------


def _invite(token: str, url: str, key: str):
    from switchboard.invite import Invite
    return Invite(url=url, workspace_token=token, key=key)


class Abandoned(RuntimeError):
    """Nobody has been in the lobby for `ABANDON_AFTER_HOURS`.

    Raised out of the watch and turned into an ending, rather than a silent
    stop, for the reason `Outage` gives: a game that looks live and is not
    is the failure this whole file keeps finding.
    """


class Outage(RuntimeError):
    """The hub stayed unreachable for longer than `OUTAGE_SECONDS`.

    Deliberately not a silent stop. A campaign that ends this way still
    tries to say so in the lobby, because the alternative -- which is what
    happened on 2026-09-11 -- is a game that looks live and is not.
    """


class Hub:
    """Where the rooms come from.

    A seam and not an abstraction: `live_hub` returns real clients against a
    real hub, and `switchboard.testing` returns real clients against a real
    hub in the test process. Nothing here is mocked -- there is no second
    implementation of a room to drift from the first.
    """

    def __init__(self, url: str, key: str, agent_id: str = "carmel"):
        self.url, self.key, self.agent_id = url, key, agent_id
        self._open: dict[str, object] = {}

    def room(self, token: str):
        from switchboard.client import Client
        if token not in self._open:
            self._open[token] = Client.from_invite(
                _invite(token, self.url, self.key), agent_id=self.agent_id)
        return self._open[token]

    def close(self) -> None:
        for client in self._open.values():
            try:
                client.close()
            except Exception:                                   # noqa: BLE001
                pass
        self._open.clear()


class Fugitive:
    """One campaign, performed on a clock.

    `now` and `sleep` are arguments so that a test can run a whole campaign in
    no time at all against the hub's own settable clock. They default to the
    wall clock, which is what `main` uses.
    """

    def __init__(self, hub: Hub, *, now: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep,
                 difficulty: float = C.DIFFICULTY,
                 poll: float = POLL_SECONDS,
                 log: Callable[[str], None] = lambda line: None,
                 listening: Callable[[], bool] = lambda: True):
        self.hub, self.now, self.sleep = hub, now, sleep
        self.difficulty, self.poll, self.log = difficulty, poll, log
        #: Is anybody in the lobby? Read from the lobby's roster by the
        #: supervisor, handed in rather than looked up, because she must not
        #: register there -- standing in the lobby would otherwise be a
        #: catch on her first second. Defaults to "yes, always", so a
        #: single-campaign run and every existing test are unaffected.
        self.listening = listening
        self._lonely_since: float | None = None
        # What she has done so far, kept on the instance so that a campaign
        # cut short by an outage can still report it rather than losing it
        # with the stack frame.
        self._walked: list[dict] = []
        self._banked = 0
        self._salt: bytes | None = None
        self._world = None

    # -- talking to a hub that is allowed to stumble -----------------------

    def _tolerate(self, what: str, call):
        """Make one hub call, surviving a blip and giving up on an outage.

        Every call she makes goes through here, because there is no such
        thing as an unimportant one: a failed roster read loses a catch, a
        failed heartbeat drops her off the roster, and a failed post loses
        the hint that is the whole of a leg.

        **Retrying is not optimism, it is arithmetic** -- see
        `OUTAGE_SECONDS`. What it must not become is a loop that hides a
        real fault, so the budget is wall-clock and small: past
        `OUTAGE_SECONDS` it raises `Outage` carrying the last error, and the
        campaign ends saying so.
        """
        failing_since = None
        while True:
            try:
                out = call()
            except Exception as exc:                            # noqa: BLE001
                now = self.now()
                if failing_since is None:
                    failing_since = now
                    self.log(f"hub unreachable on {what}"
                             f" ({type(exc).__name__}), retrying")
                if now - failing_since > OUTAGE_SECONDS:
                    raise Outage(
                        f"{what} failed for {OUTAGE_SECONDS:.0f}s:"
                        f" {type(exc).__name__}: {exc}") from exc
                self.sleep(RETRY_SECONDS)
                continue
            if failing_since is not None:
                self.log(f"hub back after {self.now() - failing_since:.0f}s")
            return out

    # -- the two posts that bracket a campaign ----------------------------

    def open_campaign(self, seed: bytes) -> None:
        notice = C.open_campaign(seed, C.LOBBY_LANDMARK)
        room = self.hub.room(lobby_token())
        self._tolerate("the notice", lambda: room.post(
            CHANNEL, notice, ttl=seconds(NOTICE_TTL_HOURS)))
        self.log(f"notice up, gone in {NOTICE_TTL_HOURS:.0f}h")

    def close_campaign(self, seed: bytes, outcome: str, reputation: int,
                       trail: list[dict], salt: bytes | None = None,
                       caught_by: str | None = None) -> None:
        """Say it is over, in the lobby **and in every place she robbed**.

        Gal, 2026-09-11: *"she should post a note (without announcing
        herself) that the game is over, in every room she's been at."*

        The close used to go to the lobby alone, and a searcher deep in a
        hunt left the lobby long ago. One of them swept 898 rooms for twenty
        minutes after she had been caught, and said afterwards exactly why
        it could not have known: *"an empty room and a dead holder produce
        the same silence, so 'no clue yet' gave me no signal to distinguish
        a working search from a broken one."* A searcher standing anywhere
        on her trail now finds out.

        **Posting is not announcing**, which is what makes this safe and is
        not obvious: `post` leaves a message, `register` puts you on the
        roster, and only the roster is the catch. She writes in each place
        without ever standing in it again -- verified by
        `test_she_says_it_is_over_without_standing_in_the_room`, because
        the tempting implementation is to join each room properly and that
        one would hand a catch to anybody still waiting there.
        """
        body = C.close_campaign(seed, outcome, reputation, trail,
                                caught_by=caught_by, world=self._world)
        where = [("the lobby", lobby_token())]
        if salt is not None:
            # Every place she reached, which is every leg's destination.
            # Deduplicated, because she revisits a place she did not empty.
            for name in dict.fromkeys(leg["to"] for leg in trail):
                where.append((name, room_token(name, salt)))
        for name, token in where:
            room = self.hub.room(token)
            try:
                self._tolerate(f"the close in {name}", lambda: room.post(
                    CHANNEL, body, ttl=seconds(HINT_TTL_HOURS)))
            except Outage:
                # The lobby is the one that matters; a place she has left is
                # a courtesy. Losing the hub mid-close should not turn a
                # finished campaign into a crash.
                self.log(f"could not say so in {name}")
        self.log(f"closed: {outcome}, {reputation} reputation,"
                 f" said in {len(where)} rooms")

    # -- the campaign ------------------------------------------------------

    def run(self, seed: bytes) -> dict:
        """Perform one campaign. Returns the same shape `carmel.chase` does.

        She is caught the moment somebody else is on the roster of the room
        she is standing in. Nothing is parsed and nothing is judged.

        **It returns rather than raising when the hub goes dark**, and says
        so in the lobby if it still can. A campaign that vanishes leaves
        hints in rooms pointing at somebody who is not coming, and a
        searcher has no way to tell that from a fugitive who is simply good
        at hiding -- so "she lost the hub" is an outcome with a name.
        """
        try:
            return self._run(seed)
        except Abandoned as alone:
            self.log(f"stopping: {alone}")
            try:
                self.close_campaign(seed, OUTCOMES["abandoned"],
                                    self._banked, self._walked, self._salt)
            except Outage:
                self.log("could not say so: the lobby is unreachable")
            return {"outcome": "abandoned", "moves": self._walked,
                    "reputation": self._banked, "why": str(alone),
                    "hours": self._walked[-1]["leaves"] if self._walked
                    else 0.0}
        except Outage as gone:
            self.log(f"giving up: {gone}")
            try:
                self.close_campaign(seed, OUTCOMES["lost"],
                                    self._banked, self._walked, self._salt)
            except Outage:
                self.log("could not even say so: the lobby is unreachable")
            return {"outcome": "lost the hub", "moves": self._walked,
                    "reputation": self._banked, "why": str(gone),
                    "hours": self._walked[-1]["leaves"] if self._walked
                    else 0.0}

    def _run(self, seed: bytes) -> dict:
        salt = self._salt = salt_for(seed)
        world = self._world = C.Map(seed)
        trail = C.itinerary(seed, C.LOBBY_LANDMARK, world,
                            difficulty=self.difficulty)
        started = self.now()
        self.open_campaign(seed)

        at = C.LOBBY_LANDMARK
        reputation, walked = 0, self._walked
        for leg in trail:
            self._wait_until(started, leg["posted"])
            here = lobby_token() if at == C.LOBBY_LANDMARK \
                else room_token(at, salt)
            said = "\n".join(C.riddle(seed, leg["to"], leg["details"]))
            room = self.hub.room(here)
            self._tolerate(f"leg {len(walked) + 1}'s riddle",
                           lambda: room.post(CHANNEL, said,
                                             ttl=seconds(HINT_TTL_HOURS)))
            walked.append(leg)
            self.log(f"leg {len(walked)}: {at} -> {leg['to']}"
                     f"  ({', '.join(leg['details'])})")

            leaving = None if at == C.LOBBY_LANDMARK \
                else self.hub.room(room_token(at, salt))
            caught_by = self._stand(seed, salt, leg, started, leaving)
            if caught_by:
                self.log(f"caught in {leg['to']} by {caught_by}")
                self.close_campaign(seed, OUTCOMES["caught"], reputation,
                                    walked, salt, caught_by=caught_by)
                return {"outcome": "caught", "moves": walked,
                        "reputation": reputation, "by": caught_by,
                        "hours": leg["leaves"]}

            at = leg["to"]
            reputation = self._banked = leg["reputation"]
            if reputation >= C.REPUTATION_TO_WIN:
                self.close_campaign(seed, OUTCOMES["wins"], reputation, walked,
                                    salt)
                return {"outcome": "she wins", "moves": walked,
                        "reputation": reputation, "hours": leg["leaves"]}

        self.close_campaign(seed, OUTCOMES["spent"], reputation, walked,
                            salt)
        return {"outcome": "out of moves", "moves": walked,
                "reputation": reputation, "hours": trail[-1]["leaves"]}

    # -- standing still ----------------------------------------------------

    def _check_the_lobby_is_not_empty(self) -> None:
        """Stop a game whose searchers have all gone home.

        The clock starts at the first look that finds nobody and resets on
        any look that finds somebody, so a searcher whose presence lapses
        between polls does not end the game -- lapsing is normal, and
        `ABANDON_AFTER_HOURS` is many multiples of the two minutes it takes.
        """
        if self.listening():
            self._lonely_since = None
            return
        if self._lonely_since is None:
            self._lonely_since = self.now()
            return
        alone = hours(self.now() - self._lonely_since)
        if alone >= ABANDON_AFTER_HOURS:
            raise Abandoned(f"the lobby has been empty for {alone:.0f}h")

    def _stand(self, seed: bytes, salt: bytes, leg: dict,
               started: float, leaving=None) -> str | None:
        """Watch the destination from the moment she named it until she goes.

        The window is `posted -> leaves`, which is `prep + dwell` and is
        exactly the window `carmel.pursue` gives a searcher. She is not
        *present* in the room until `arrived` -- she is still packing -- but
        somebody who gets there first and waits has caught her all the same,
        which is why the watch starts at `posted` and not at `arrived`.
        """
        room = self.hub.room(room_token(leg["to"], salt))
        registered = False
        # Note what is not here: she never registers in the lobby. The lobby
        # is where everybody reads the notice, so if standing in it counted
        # as finding her every campaign would end on its first second --
        # which is why `carmel.pursue` only ever checks a leg's destination
        # and never its origin.
        while True:
            elapsed = hours(self.now() - started)
            if elapsed >= leg["leaves"]:
                return None
            self._check_the_lobby_is_not_empty()
            ttl = max(120.0, self.poll * 4)
            if not registered and elapsed >= leg["arrived"]:
                self._tolerate("arriving", lambda: room.register(
                    name="carmel", kind="fugitive", ttl=ttl))
                registered = True
                # She is in one room at a time. Off the old roster at the
                # same moment she is on the new one, not a leg later.
                if leaving is not None:
                    self._leave(leaving)
            elif registered:
                # The line that ended a live campaign on 2026-09-11, on one
                # dropped TLS connection. It is the most-called hub call in
                # the program and was the least protected.
                self._tolerate("a heartbeat",
                               lambda: room.heartbeat(ttl=ttl))

            # **Whichever room she is actually in.** Gal, 2026-09-11: *"she
            # could be caught whenever she is in the room with a player,
            # nevermind her state."* Before `arrived` she is still in the
            # room she wrote from, packing, and that room used to go
            # unwatched -- so her own notice promised that a fresh line
            # meant she was still there while the code made it untrue.
            here = room if registered else (leaving or room)
            other = self._tolerate("the roster",
                                   lambda: self._stranger(here))
            if other:
                return other
            self.sleep(min(self.poll,
                           max(0.0, seconds(leg["leaves"]) -
                               (self.now() - started))))

    def _leave(self, room) -> None:
        """Off the roster of the room she has finished with.

        Presence would lapse on its own inside two game hours, so this is
        not correctness -- it is that a searcher walking into the room she
        has just left would otherwise read her on the roster and believe
        they had her. The catch is hers to declare and they would be wrong,
        which is a worse thing for them to see than an empty room.
        """
        try:
            room.deregister()
        except Exception:                                       # noqa: BLE001
            pass

    def _stranger(self, room) -> str | None:
        """Anybody on this room's roster who is not her.

        **By signing key, not by name and not by agent id.** A name is
        whatever a searcher types, so a searcher called `carmel` would be
        invisible to her; the roster's `agent_id` is only assigned once she
        has registered, and she watches this room from before she arrives in
        it. `public_key` is neither -- it is on the client from the moment it
        exists, and it is on the roster row for everybody else.

        Per client, not per process (`CLAUDE.md`, the measured facts about
        Switchboard): her lobby client and her room clients have different
        keys, so the comparison is always between this room's roster and
        *this room's* client.

        The first version compared `agent.get("id")` -- not a key the roster
        has -- against `room.peer_id`, which is a method and so never equals
        anything. Every agent read as a stranger and **she caught herself on
        leg one of every campaign**. What found it was not the catch test,
        which went green on her arresting herself; it was
        `test_an_empty_room_is_not_a_catch`, written only to stop the catch
        test being vacuous. `CLAUDE.md`, "a check is green for the reason it
        names": the complement is the check.
        """
        for agent in room.agents():
            if agent.get("pubkey") != room.public_key:
                return agent.get("name") or agent.get("agent_id")
        return None

    def _wait_until(self, started: float, game_hour: float) -> None:
        target = started + seconds(game_hour)
        while True:
            gap = target - self.now()
            if gap <= 0:
                return
            self.sleep(min(gap, self.poll))


# --- the standing invitation ----------------------------------------------


def treasure_warning() -> str | None:
    """Say so if this host is playing with a different treasure table.

    `treasures.py` unseals `treasures.enc` when `HUE_TREASURE_KEY` is in the
    environment and **builds its own table when it is not** -- so a host
    without the key runs a game whose rooms hold different prizes worth
    different reputation, and every number calibrated against the sealed
    table is measuring something else.

    Nothing said so until 2026-09-12. `at_large.py` did not mention the
    variable at all, which is `CLAUDE.md`'s *"the weaker thing is allowed,
    and never allowed to look like the stronger one"* failing in the
    quietest possible way: the game ran, posted riddles, took treasures and
    closed, and looked exactly like the canonical one.

    It is a warning and not a refusal, because the weaker game is allowed:
    a host without the key can still play, and what it may not do is pass
    for the other thing.
    """
    if os.environ.get(T.KEY_ENV):
        return None
    return (f"  !! {T.KEY_ENV} is not set, so the treasures are REBUILT and"
            " not the sealed ones.\n"
            "     The game plays, and its reputation numbers are not"
            " comparable to a\n"
            "     host that has the key. This is a different table, not a"
            " missing one.")


def listeners(room, log=lambda line: None) -> int:
    """How many are registered in the lobby who are not her.

    She reads this and never registers here -- standing in the lobby would
    otherwise be a catch on her first second (`_stand` says why). A read
    does not put you on a roster, which is the same fact the rules warn
    searchers about, working in her favour for once.

    Unreachable counts as **nobody**, deliberately: a hub she cannot read is
    not a hub anybody is playing on, and the alternative is starting games
    into a void because the gate failed open.
    """
    try:
        return sum(1 for a in room.agents()
                   if (a.get("name") or "") != "carmel")
    except Exception as why:                      # noqa: BLE001
        log(f"could not read the lobby ({type(why).__name__})")
        return 0


def forever(make_hub: Callable[[], Hub], *,
            seeds: Callable[[], bytes] = lambda: secrets.token_bytes(32),
            now: Callable[[], float] = time.time,
            sleep: Callable[[float], None] = time.sleep,
            limit: int | None = None, poll: float = POLL_SECONDS,
            log: Callable[[str], None] = print,
            spawn: Callable | None = None,
            rounds: int | None = None) -> list[dict]:
    """Up to four games at once, a new one every five minutes, and only
    while somebody is in the lobby to play it.

    Gal, 2026-09-12: *"a new game can start every 5 minutes but only if
    there's at least one player in the room (or registered listener). and no
    more than 4 parallel games."*

    **This replaces a sequential loop, and the reasoning it replaces was
    sound for the game it described:**

        Campaign after campaign, at roughly the length of a campaign. Gal,
        2026-09-10: *"let her start a new game every ~game_play_time."* The
        tilde is doing the work and is honoured by construction rather than
        by a timer: the next campaign opens when the last one closes, so the
        cadence is the play time by definition and two campaigns can never
        be live at once.

    What broke it is the riddle. A campaign used to run for days of game
    time, so "one at a time" and "always joinable" were the same
    arrangement. Now an *unopposed* campaign runs a median of 84 minutes
    while a *contested* one ends in about six, so a lone sequential game
    means a newcomer waits on whichever kind happens to be running -- and
    with nobody chasing, that is always the long kind.

    **Four independent runners is the permitted shape, not the forbidden
    one.** `CLAUDE.md`'s "Agents run themselves. There is no scheduler."
    forbids a loop that calls each agent in turn and applies its replies.
    Nothing here calls an agent: these are four long-lived games that
    neither read nor wait for one another, and the supervisor only decides
    whether to begin another. It never drives one that has begun.

    `spawn` is the seam. Production hands threads; a test hands something
    that runs the game inline, so the policy can be checked without a
    scheduler deciding the answer.
    """
    if spawn is None:
        def spawn(fn):
            t = threading.Thread(target=fn, daemon=True)
            t.start()
            return t

    done: list[dict] = []
    live: list = []
    lobby = make_hub().room(lobby_token())
    last_start = now() - seconds(C.START_EVERY_HOURS)   # ready immediately
    posted_rules = 0.0

    def play(seed: bytes, hub: Hub) -> None:
        try:
            done.append(Fugitive(hub, now=now, sleep=sleep, poll=poll,
                                 log=log,
                                 listening=lambda: listeners(lobby) > 0
                                 ).run(seed))
        finally:
            hub.close()

    # `limit` counts *finished* games and `rounds` counts supervisor passes.
    # Both exist because a test that never lets a game finish cannot bound
    # the loop by games, and one that bounds it by passes cannot say how
    # many games it wanted. Production passes neither.
    passes = 0
    while ((limit is None or len(done) < limit)
           and (rounds is None or passes < rounds)):
        passes += 1
        live = [t for t in live if getattr(t, "is_alive", lambda: False)()]

        # The rules post is kept fresh whether or not anybody is here: it is
        # what tells a newcomer that registering is what starts a game, so a
        # lobby that has gone quiet must still explain itself. Without it the
        # demand gate is a closed door with no bell.
        if now() - posted_rules >= seconds(RULES_TTL_HOURS) / 2:
            try:
                lobby.post(CHANNEL, C.standing_notice(),
                           ttl=seconds(RULES_TTL_HOURS))
                posted_rules = now()
            except Exception as why:              # noqa: BLE001
                log(f"could not post the rules ({type(why).__name__})")

        here = listeners(lobby, log)
        if may_start(len(live), here, hours(now() - last_start)):
            seed = seeds()
            last_start = now()
            log(f"starting a game: {here} listening, {len(live) + 1} live")
            live.append(spawn(lambda s=seed: play(s, make_hub())))
        sleep(poll)
    return done


# --- what it looks like without a hub -------------------------------------


def address(url: str) -> str:
    """The three things a searcher needs to stand in the lobby.

    All three are publishable and none of them is a credential: the hub is
    an address, the token is derived from the game's own name, and the key
    is derived from a constant (`LOBBY_KEY`). What is *not* here is the
    salt -- that arrives in the notice, once she has begun, which is what
    makes the lobby worth standing in rather than a thing to bookmark.
    """
    return "\n".join([
        f"    url   {url}",
        f"    token {lobby_token()}",
        f"    key   {LOBBY_KEY}",
    ])


def dry_run(count: int = 20) -> None:
    """The schedule, measured, with no network and no clock.

    This is the reproduction for every number in this module's comments.
    """
    import statistics as st

    print(f"one game hour = {HOUR_SECONDS:.0f}s,"
          f" notice lives {NOTICE_TTL_HOURS:.0f}h"
          f" ({seconds(NOTICE_TTL_HOURS) / 60:.0f} real minutes)\n")
    lengths, inside = [], 0
    for b in range(1, count + 1):
        seed = bytes.fromhex(f"{b:02x}" * 32)
        world = C.Map(seed)
        result = C.chase(seed, C.LOBBY_LANDMARK, searchers=2, world=world)
        lengths.append(result["hours"])
        if result["hours"] <= NOTICE_TTL_HOURS:
            inside += 1
    print(f"  {count} campaigns: {st.median(lengths):.0f}h median"
          f" ({seconds(st.median(lengths)) / 60:.0f} real minutes),"
          f" {min(lengths):.0f}h shortest")
    print(f"  ended inside their own notice: {inside}/{count}"
          "  <- fine: a newcomer takes the next game, minutes away")
    print(f"\n  a new game every {C.START_EVERY_HOURS:.0f}h"
          f" ({seconds(C.START_EVERY_HOURS) / 60:.0f} real minutes),"
          f" at most {C.MAX_PARALLEL} alive,")
    print(f"  and none at all while the lobby is empty."
          f" A game whose lobby stays")
    print(f"  empty for {ABANDON_AFTER_HOURS:.0f}h closes itself.")
    print(f"\n  her note lives {NOTICE_TTL_HOURS:.0f}h, under the"
          f" {C.START_EVERY_HOURS:.0f}h between starts, so two of")
    print("  her notes can never be legible at once.")
    print("\n  the lobby, which is publishable in full:")
    print(address("https://switchboard.lucille-ai.com"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the schedule and exit; no hub, no clock")
    ap.add_argument("--once", action="store_true",
                    help="run one campaign and stop")
    ap.add_argument("--url", default=os.environ.get(
        "SWITCHBOARD_URL", "https://switchboard.lucille-ai.com"))
    ap.add_argument("--key", default=LOBBY_KEY,
                    help="the game's room key, which is published (see"
                         " LOBBY_KEY) -- override only to run a private game")
    ap.add_argument("--seed", help="hex, for a campaign you can re-derive")
    args = ap.parse_args()

    if args.dry_run:
        dry_run()
        return

    # A hub per game, not one shared: each game holds its own clients, on
    # its own salt's rooms, from its own thread. Sharing one would put two
    # threads through a client that was never asked to carry both.
    print(address(args.url))
    warning = treasure_warning()
    if warning:
        print(warning)
    if args.once:
        hub = Hub(args.url, args.key)
        try:
            seed = bytes.fromhex(args.seed) if args.seed \
                else secrets.token_bytes(32)
            result = Fugitive(hub, log=print).run(seed)
            print(f"\n  {result['outcome']} after {result['hours']:.0f}h,"
                  f" {result['reputation']} reputation")
        except KeyboardInterrupt:
            print("\nshe stops")
        finally:
            hub.close()
        return

    try:
        forever(lambda: Hub(args.url, args.key))
    except KeyboardInterrupt:
        print("\nshe stops")


if __name__ == "__main__":
    main()
