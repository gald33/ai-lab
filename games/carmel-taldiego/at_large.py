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
import sys
import time
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
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
NOTICE_TTL_HOURS = float(C.JOIN_WINDOW_HOURS)

#: The quiet between campaigns, in game hours. Two hours is two minutes: long
#: enough that the close and the next open are not the same moment on a
#: reader's screen, short enough that she is a standing invitation.
INTERMISSION_HOURS = 2.0

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


def hours(seconds: float) -> float:
    return seconds / HOUR_SECONDS


def seconds(game_hours: float) -> float:
    return game_hours * HOUR_SECONDS


# --- the room she is standing in ------------------------------------------


def _invite(token: str, url: str, key: str):
    from switchboard.invite import Invite
    return Invite(url=url, workspace_token=token, key=key)


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
                 log: Callable[[str], None] = lambda line: None):
        self.hub, self.now, self.sleep = hub, now, sleep
        self.difficulty, self.poll, self.log = difficulty, poll, log

    # -- the two posts that bracket a campaign ----------------------------

    def open_campaign(self, seed: bytes) -> None:
        notice = C.open_campaign(seed, C.LOBBY_LANDMARK)
        self.hub.room(lobby_token()).post(
            CHANNEL, notice, ttl=seconds(NOTICE_TTL_HOURS))
        self.log(f"notice up, gone in {NOTICE_TTL_HOURS:.0f}h")

    def close_campaign(self, seed: bytes, outcome: str, reputation: int,
                       trail: list[dict]) -> None:
        self.hub.room(lobby_token()).post(
            CHANNEL, C.close_campaign(seed, outcome, reputation, trail),
            ttl=seconds(HINT_TTL_HOURS))
        self.log(f"closed: {outcome}, {reputation} reputation")

    # -- the campaign ------------------------------------------------------

    def run(self, seed: bytes) -> dict:
        """Perform one campaign. Returns the same shape `carmel.chase` does.

        She is caught the moment somebody else is on the roster of the room
        she is standing in. Nothing is parsed and nothing is judged.
        """
        salt = salt_for(seed)
        world = C.Map(seed)
        trail = C.itinerary(seed, C.LOBBY_LANDMARK, world,
                            difficulty=self.difficulty)
        started = self.now()
        self.open_campaign(seed)

        at = C.LOBBY_LANDMARK
        reputation, walked = 0, []
        for leg in trail:
            self._wait_until(started, leg["posted"])
            here = lobby_token() if at == C.LOBBY_LANDMARK \
                else room_token(at, salt)
            self.hub.room(here).post(CHANNEL, leg["hint"].replace("_", " "),
                                     ttl=seconds(HINT_TTL_HOURS))
            walked.append(leg)
            self.log(f"leg {len(walked)}: {at} -> {leg['to']}"
                     f"  ({leg['hint']})")

            leaving = None if at == C.LOBBY_LANDMARK \
                else self.hub.room(room_token(at, salt))
            caught_by = self._stand(seed, salt, leg, started, leaving)
            if caught_by:
                self.log(f"caught in {leg['to']} by {caught_by}")
                self.close_campaign(seed, "You have me", reputation, walked)
                return {"outcome": "caught", "moves": walked,
                        "reputation": reputation, "by": caught_by,
                        "hours": leg["leaves"]}

            at = leg["to"]
            reputation = leg["reputation"]
            if reputation >= C.REPUTATION_TO_WIN:
                self.close_campaign(seed, "I retire on it", reputation, walked)
                return {"outcome": "she wins", "moves": walked,
                        "reputation": reputation, "hours": leg["leaves"]}

        self.close_campaign(seed, "I ran out of road", reputation, walked)
        return {"outcome": "out of moves", "moves": walked,
                "reputation": reputation, "hours": trail[-1]["leaves"]}

    # -- standing still ----------------------------------------------------

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
            if not registered and elapsed >= leg["arrived"]:
                room.register(name="carmel", kind="fugitive",
                              ttl=max(120.0, self.poll * 4))
                registered = True
                # She is in one room at a time. Off the old roster at the
                # same moment she is on the new one, not a leg later.
                if leaving is not None:
                    self._leave(leaving)
            elif registered:
                room.heartbeat(ttl=max(120.0, self.poll * 4))
            other = self._stranger(room)
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


def forever(hub: Hub, *, seeds: Callable[[], bytes] = lambda: secrets
            .token_bytes(32),
            now: Callable[[], float] = time.time,
            sleep: Callable[[float], None] = time.sleep,
            limit: int | None = None, poll: float = POLL_SECONDS,
            log: Callable[[str], None] = print) -> list[dict]:
    """Campaign after campaign, at roughly the length of a campaign.

    Gal, 2026-09-10: *"let her start a new game every ~game_play_time."* The
    tilde is doing the work and is honoured by construction rather than by a
    timer: **the next campaign opens when the last one closes**, so the
    cadence is the play time by definition and two campaigns can never be
    live at once. A fixed period would have to be set to the worst case and
    would leave her idle through every campaign that was not it.

    The one wait that is not the campaign's own length is the floor in
    `plan`: after an early arrest she sits out the rest of the old notice.
    """
    done = []
    while limit is None or len(done) < limit:
        seed = seeds()
        result = Fugitive(hub, now=now, sleep=sleep, poll=poll,
                          log=log).run(seed)
        done.append(result)
        if limit is not None and len(done) >= limit:
            break
        after = plan(result["hours"])
        quiet = seconds(after["next_opens"] - after["closes"])
        log(f"quiet for {hours(quiet):.0f}h")
        # Her rooms go with the campaign that made them: the salt moves, so
        # every one of them is an address nobody will use again, and holding
        # the clients open would leak one per landmark per campaign.
        hub.close()
        sleep(quiet)
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
          "  <- what the floor in `plan` is for")
    example = plan(st.median(lengths))
    print(f"\n  a median campaign: notice gone at"
          f" {example['notice_gone']:.0f}h, closes at"
          f" {example['closes']:.0f}h, next opens at"
          f" {example['next_opens']:.0f}h")
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

    hub = Hub(args.url, args.key)
    print(address(args.url))
    try:
        if args.once:
            seed = bytes.fromhex(args.seed) if args.seed \
                else secrets.token_bytes(32)
            result = Fugitive(hub, log=print).run(seed)
            print(f"\n  {result['outcome']} after {result['hours']:.0f}h,"
                  f" {result['reputation']} reputation")
        else:
            forever(hub)
    except KeyboardInterrupt:
        print("\nshe stops")
    finally:
        hub.close()


if __name__ == "__main__":
    main()
