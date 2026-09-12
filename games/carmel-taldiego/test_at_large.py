"""What she must get right when she is actually running.

    python3 -m pytest games/carmel-taldiego/test_at_large.py -q

**These drive a real hub.** `switchboard.testing.hub` is the FastAPI app over
the real store, in this process, with a clock the test sets -- not a mock, not
a fake room. So a message that expires here expires the way it expires on
`switchboard.lucille-ai.com`, and presence lapses for the same reason. That
matters more than usual in this file, because the thing under test *is* the
expiry: `CLAUDE.md`'s "a check is green for the reason it names" would be
badly served by a stub that dropped messages when we told it to.

Every test below has been made to fail on purpose. The schedule ones by
raising `NOTICE_TTL_HOURS` over a campaign's length; the end-to-end ones by
posting the notice with no ttl at all, and by having her ignore the roster.
"""

import base64
import hashlib
import os
import re
import statistics as st
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import at_large as L  # noqa: E402
from secret_matrix import room_token, salt_for  # noqa: E402

KEY = "k" * 43 + "="

#: A poll coarse enough that a campaign runs in seconds against the test
#: hub, and still four times finer than the shortest leg.
POLL = 60.0


def lengths(count: int = 40) -> list[float]:
    """How long campaigns actually run, in game hours."""
    out = []
    for b in range(1, count + 1):
        seed = bytes.fromhex(f"{b:02x}" * 32)
        world = C.Map(seed)
        out.append(C.chase(seed, C.LOBBY_LANDMARK, searchers=2,
                           world=world)["hours"])
    return out


# --- the schedule ---------------------------------------------------------


def test_a_riddle_is_worth_seconds_to_minutes_of_real_time():
    """Gal, 2026-09-11: *"The game time is less important. First I'd make
    the real world time seconds to minutes per riddle."*

    **This replaced the test that used to stand here**, and the superseded
    one is quoted rather than deleted because it was right about a game
    that no longer exists:

        def test_the_notice_dies_long_before_the_campaign_it_announces():
            ran = lengths()
            assert st.median(ran) > 4 * L.NOTICE_TTL_HOURS
            inside = [h for h in ran if h <= L.NOTICE_TTL_HOURS]
            assert len(inside) / len(ran) < 0.10

    That asserted a ratio between two *game*-time quantities, as a proxy
    for Gal's *"making sure her lobby message is long gone before the game
    ends"*. The proxy held while a campaign ran for days of game time. With
    a riddle she is caught in a median of six game hours and a quarter of
    campaigns end inside forty seconds, so no notice length satisfies it --
    and the property it was standing in for is held by the floor in `plan`
    anyway, which is tested immediately below and does not depend on this
    number at all.

    So this pins what Gal actually asked for, in the units he asked for it
    in: **what one riddle is worth in real seconds.** The window is the
    whole time a searcher has to read it, solve it, and be standing there
    -- her packing, her theft, and her packing before the next leg, which
    is the same three stretches `pursue` counts.

    Made to fail on purpose by moving `HOUR_SECONDS`: at 6 the median
    window falls to 40 real seconds and the lower bound goes red; at 600 it
    is over an hour and the upper bound does.
    """
    windows = []
    for b in range(1, 21):
        seed = bytes.fromhex(f"{b:02x}" * 32)
        world = C.Map(seed)
        trail = C.itinerary(seed, C.LOBBY_LANDMARK, world, 25)
        for i, leg in enumerate(trail):
            windows.append((leg["prep"] + leg["dwell"]
                            + (trail[i + 1]["prep"]
                               if i + 1 < len(trail) else 0.0))
                           * L.HOUR_SECONDS)
    windows.sort()
    median = st.median(windows)
    assert 60 <= median <= 600, (
        f"a riddle is worth {median:.0f} real seconds: Gal asked for"
        " seconds to minutes")
    quick = windows[len(windows) // 10]
    assert quick > 10, (
        f"a tenth of riddles give under {quick:.0f} real seconds, which is"
        " not time to read one")


def test_the_salt_outlives_the_campaign_it_belongs_to():
    """The notice carries the salt, and the salt is how every room in the
    game is computed. If it expires first, her later riddles name places
    nobody can reach.

    **This replaced a test that asserted the opposite**, written the same
    day and wrong within hours:

        def test_the_notice_is_a_join_window_a_person_could_use():
            real = L.NOTICE_TTL_HOURS * L.HOUR_SECONDS
            assert 60 <= real <= 600

    That treated the notice as an invitation, done once somebody had
    joined, and cut it to two minutes. A searcher joined a live campaign
    two minutes in, found a riddle and no salt, and was stuck. **The notice
    is not an invitation, it is the key to the map**, and it has to last as
    long as the game it opens.

    Made to fail on purpose by restoring the two-hour value.
    """
    ran = lengths()
    covered = [h for h in ran if h <= L.NOTICE_TTL_HOURS]
    assert len(covered) / len(ran) > 0.5, (
        f"only {len(covered)}/{len(ran)} campaigns finish while their own"
        f" salt is still readable, at {L.NOTICE_TTL_HOURS:.0f}h")
    assert L.NOTICE_TTL_HOURS >= st.median(ran), (
        f"the salt dies at {L.NOTICE_TTL_HOURS:.0f}h and the median campaign"
        f" runs {st.median(ran):.0f}h")


def test_the_next_campaign_never_opens_while_the_old_notice_can_be_read():
    """The floor, which is what makes the sentence above true of *every*
    campaign rather than of most of them.

    A campaign she is caught in on leg one is over in a few game hours, and
    its notice is not. `CLAUDE.md`: the weaker thing is allowed and is never
    allowed to look like the stronger one -- so the early arrest is played
    out and counted, and what it is not allowed to do is put two salts on
    one screen.
    """
    for ran in [0.0, 1.0, 6.4, 11.9, 12.0, 12.1] + lengths():
        after = L.plan(ran)
        assert after["next_opens"] > after["notice_gone"], ran
        assert after["next_opens"] > after["closes"], ran


def test_the_cadence_is_the_play_time_and_not_a_timer():
    """*"start a new game every ~game_play_time"* -- honoured by the next
    campaign opening when the last one closed, so the tilde is structural.
    On an ordinary campaign the gap is the intermission and nothing else."""
    for ran in lengths():
        after = L.plan(ran)
        if ran > L.NOTICE_TTL_HOURS:
            assert after["next_opens"] - after["closes"] \
                == pytest.approx(L.INTERMISSION_HOURS)


# --- the address, which is the whole of "available" ------------------------


def test_the_lobby_is_publishable_in_full_and_borrows_no_credential():
    """What "available to play" reduces to: three strings a stranger needs,
    none of which is a secret belonging to anybody.

    The key is derived from a constant on purpose (`at_large.LOBBY_KEY`) --
    a room whose key must be handed over is an invite, and the invite is
    the mechanism the whole name-is-the-room construction replaces. The
    guard below is the one that matters, because the easy mistake is
    reaching for `SWITCHBOARD_KEY`: it is right there in the environment,
    it works, and publishing the resulting address would publish it too.
    """
    body = L.address("https://hub.example")
    assert L.lobby_token() in body
    assert L.LOBBY_KEY in body
    assert L.LOBBY_KEY == L._derived_key(b"hue-and-cry/v1/room-key")

    for name, value in os.environ.items():
        if len(value) > 16 and any(word in name.upper()
                                   for word in ("KEY", "TOKEN", "SECRET")):
            assert value not in body, f"the address carries ${name}"


def test_the_salt_is_not_in_the_address_because_it_is_in_the_notice():
    """The lobby is a place to stand before she has begun, not a bookmark
    that plays the game for you. Nothing derived from a seed may appear in
    something published once and left up."""
    body = L.address("https://hub.example")
    for b in range(1, 6):
        seed = bytes.fromhex(f"{b:02x}" * 32)
        assert salt_for(seed).hex() not in body
        assert seed.hex() not in body


# --- against a real hub ---------------------------------------------------


class Rooms(L.Hub):
    """`at_large.Hub`'s seam, pointed at the in-process hub.

    Same `Client`, same wire, same store -- only the transport is in this
    process. The workspace identifier is computed the way `Invite` computes
    it, so a room here is the room a searcher's `join_room` would reach.
    """

    def __init__(self, hub, agent_id: str = "carmel"):
        self.hub, self.agent_id, self._open = hub, agent_id, {}

    @staticmethod
    def workspace(token: str) -> str:
        from switchboard.invite import Invite
        return Invite(url="http://hub.test", workspace_token=token,
                      key=KEY).workspace

    def room(self, token: str):
        if token not in self._open:
            self._open[token] = self.hub.client(
                agent_id=self.agent_id, workspace=self.workspace(token),
                key=KEY)
        return self._open[token]

    def close(self) -> None:
        self._open.clear()


def driven(hub, **kwargs) -> L.Fugitive:
    """Her, with the hub's own clock under her feet."""
    return L.Fugitive(Rooms(hub), now=hub.clock,
                      sleep=lambda s: hub.clock.advance(max(s, 1.0)),
                      poll=POLL, **kwargs)


def notices(client) -> list[str]:
    """The live lobby notices -- the ones carrying a salt to go and use."""
    return [m["body"] for m in client.history(L.CHANNEL, limit=200)
            if "salt = " in m["body"]]


@pytest.fixture
def board():
    from switchboard.testing import hub
    with hub(key=KEY) as h:
        yield h


def test_the_lobby_holds_one_notice_at_the_moment_the_next_one_goes_up(board):
    """The invariant the whole schedule exists for, checked at the only
    moment it can break: the instant the second campaign opens.

    Two salts legible at once is a reader following an address from a game
    that is over -- and it would look exactly like playing.
    """
    rooms = Rooms(board)
    lobby = rooms.room(L.lobby_token())

    first = driven(board).run(bytes.fromhex("55" * 32))
    if first["hours"] > L.NOTICE_TTL_HOURS:
        # Gal's constraint, at the close: an ordinary campaign has already
        # outlived its notice by the time it ends. Conditional because an
        # early arrest is allowed not to, and is what the floor below is
        # for -- `absurd.tsv` is gitignored, so which kind this seed is
        # differs between a checkout that holds it and CI.
        assert notices(lobby) == [], "the notice outlived the campaign"

    after = L.plan(first["hours"])
    board.clock.advance(L.seconds(after["next_opens"] - after["closes"]))
    assert notices(lobby) == [], (
        "the old notice outlived the quiet between campaigns")

    driven(board).open_campaign(bytes.fromhex("77" * 32))
    assert len(notices(lobby)) == 1


def test_the_notice_really_carries_the_ttl_the_constant_names(board):
    """That `NOTICE_TTL_HOURS` reaches the wire, which is a smaller claim
    than it first looks and is deliberately named as the smaller one.

    **It cannot fail on a badly chosen TTL**, because it advances the clock
    by whatever `NOTICE_TTL_HOURS` says: set the constant to 500 and this
    stays green. What it does catch is the constant not being *applied* --
    posting with no `ttl=` leaves the hub's own hour-long default and this
    goes red, which is the bug worth having a test for, since a parameter's
    presence is not its effect.

    Gal's actual constraint is the margin, and it is
    `test_the_notice_dies_long_before_the_campaign_it_announces` that fails
    at 500. Naming this one after the constraint would have been a third
    green tick claiming to check something two others check -- and the run
    that found the overclaim was the deliberate break, not the passing
    suite.
    """
    rooms = Rooms(board)
    lobby = rooms.room(L.lobby_token())
    her = driven(board)
    her.open_campaign(bytes.fromhex("55" * 32))
    assert len(notices(lobby)) == 1

    board.clock.advance(L.seconds(L.NOTICE_TTL_HOURS + 1))
    assert notices(lobby) == []


def test_a_stranger_standing_in_the_room_is_the_whole_catch(board):
    """No message, no verb, nothing settled. The searcher below never
    speaks -- it registers in the room she named and waits.

    `CLAUDE.md`: Carmel Taldiego has no manager and no settler. If this test
    ever needs the searcher to *say* something, that is the settler arriving
    in new clothes.
    """
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    world = C.Map(seed)
    first = C.itinerary(seed, C.LOBBY_LANDMARK, world, limit=1)[0]

    searcher = board.client(agent_id="searcher",
                            workspace=Rooms.workspace(
                                room_token(first["to"], salt)),
                            key=KEY)
    searcher.register(name="searcher", kind="searcher", ttl=3600)

    result = driven(board).run(seed)
    assert result["outcome"] == "caught"
    assert result["by"] == "searcher"
    assert len(result["moves"]) == 1, "she should not have got past leg one"
    assert result["reputation"] == 0, "an interrupted theft is not banked"


def test_the_catcher_is_handed_a_chase_to_watch(board):
    """Gal, 2026-09-12: *"at the end of a chase, if you catch her, your
    agent can give you a link to a website that shows your chase
    animation."*

    The searcher still says nothing and asks for nothing: it stands in the
    room, and what it reads afterwards is her closing post. The link is in
    that post, so an agent that can read the lobby can hand its human a
    film -- which is the only shape this game's asymmetry allows, since a
    searcher never saw where she went.

    Driven live rather than through `close_campaign` directly, because what
    is being checked is that the *runtime* mints it: `_watch` swallows its
    own failures on purpose, so a broken link here is a silent one.
    """
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    world = C.Map(seed)
    first = C.itinerary(seed, C.LOBBY_LANDMARK, world, limit=1)[0]

    searcher = board.client(agent_id="searcher",
                            workspace=Rooms.workspace(
                                room_token(first["to"], salt)),
                            key=KEY)
    searcher.register(name="searcher", kind="searcher", ttl=3600)

    result = driven(board).run(seed)
    assert result["outcome"] == "caught"

    lobby = board.client(agent_id="reader",
                         workspace=Rooms.workspace(L.lobby_token()), key=KEY)
    said = [m["body"] for m in lobby.history(L.CHANNEL, limit=200)]
    closing = [body for body in said if "seed = " in body]
    assert closing, "she never closed the campaign"

    import trail_flight as TF
    address = [line.strip() for line in closing[-1].splitlines()
               if TF.CHASE_PAGE in line]
    assert address, f"no chase to watch in:\n{closing[-1]}"
    assert len(address[0]) > len(TF.CHASE_PAGE) + 200, "an empty address"


def test_she_is_caught_in_the_room_she_is_packing_in(board):
    """Gal, 2026-09-11: *"she could be caught whenever she is in the room
    with a player, nevermind her state. You don't have to wait for her, you
    can usually catch her when you land in the room she's in."*

    The route that did not exist. Between writing her line and arriving
    somewhere new she is standing in the room she wrote from, packing --
    and `_stand` used to watch her *destination* through that whole
    stretch, so the one room she was provably in went unwatched. Her notice
    promises a fresh line means she is still there; this is what makes the
    promise true.

    Driven through `_stand` directly rather than a whole campaign, because
    the window is the packing minutes of one leg and a fake clock cannot
    drop a searcher into the middle of a run.
    """
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    world = C.Map(seed)
    trail = C.itinerary(seed, C.LOBBY_LANDMARK, world, limit=6)
    # A leg she packs for, leaving somewhere that is not the lobby -- the
    # lobby is where everyone reads her notice and she is never on its
    # roster, which is why `leaving` is None on leg one.
    leg = next(l for l in trail[1:] if l["prep"] > 0)

    rooms = Rooms(board)
    packing_in = rooms.room(room_token(leg["from"], salt))
    searcher = board.client(agent_id="latecomer",
                            workspace=Rooms.workspace(
                                room_token(leg["from"], salt)), key=KEY)
    searcher.register(name="latecomer", kind="searcher", ttl=3600)

    her = L.Fugitive(rooms, now=board.clock,
                     sleep=lambda s: board.clock.advance(max(s, 1.0)),
                     poll=POLL, log=lambda line: None)
    started = board.clock() - L.seconds(leg["posted"])
    caught = her._stand(seed, salt, leg, started, packing_in)
    assert caught == "latecomer", (
        "she packed in a room with a searcher in it and walked out free")


def test_an_empty_room_is_not_a_catch(board):
    """The other half, and the reason the test above is not vacuous: with
    nobody standing anywhere, the same seed runs to its own end."""
    result = driven(board).run(bytes.fromhex("55" * 32))
    assert result["outcome"] != "caught"
    assert len(result["moves"]) > 1


def test_an_uncontested_campaign_is_the_one_the_simulation_predicted(board):
    """The claim this whole module rests on: it adds a clock and nothing
    else.

    `carmel.chase(searchers=0)` is her trail with nobody chasing, computed
    from the seed and no network. Run the same seed on a hub with nobody
    standing anywhere and every number must match -- outcome, reputation,
    legs, and the hour it ended on. If the live path ever starts making a
    decision of its own, this is where it shows: a docstring saying "the
    itinerary still decides" cannot fail, and this can.
    """
    seed = bytes.fromhex("55" * 32)
    world = C.Map(seed)
    predicted = C.chase(seed, C.LOBBY_LANDMARK, searchers=0, world=world)
    happened = driven(board).run(seed)

    assert happened["outcome"] == predicted["outcome"]
    assert happened["reputation"] == predicted["reputation"]
    assert len(happened["moves"]) == len(predicted["moves"])
    assert happened["hours"] == pytest.approx(predicted["hours"])
    assert [leg["to"] for leg in happened["moves"]] \
        == [leg["to"] for leg in predicted["moves"]]


def test_she_keeps_going_and_never_shows_two_notices(board, monkeypatch):
    """The loop itself, which is the part that has to survive unattended.

    Two campaigns end to end through `forever`, on the hub's clock. The
    lobby is read at the one moment that can break -- immediately after the
    second notice goes up -- and holds one. It also exercises the client
    cache being dropped between campaigns, which is untested wiring
    everywhere else and is exactly what fails at three in the morning.
    """
    # A notice that outlives every campaign, so the floor in `plan` is
    # what is under test rather than a lucky seed. At the shipped 12 hours
    # a campaign runs seven times longer than its notice and this passes
    # whether or not the floor exists -- which it does, deleting the floor
    # leaves this green at 12 and reddens it here.
    monkeypatch.setattr(L, "NOTICE_TTL_HOURS", 500.0)

    rooms = Rooms(board)
    made = iter([bytes.fromhex("55" * 32), bytes.fromhex("77" * 32)])

    # Sampled at each open rather than at the end: by the time the loop
    # returns both notices have expired, so a count taken then is 0 and
    # says nothing. The only moment the invariant can break is the instant
    # a notice goes up, and that is the moment she logs.
    standing = []

    def watch(line: str) -> None:
        if line.startswith("notice up"):
            standing.append(len(notices(rooms.room(L.lobby_token()))))

    done = L.forever(rooms, seeds=lambda: next(made), now=board.clock,
                     sleep=lambda s: board.clock.advance(max(s, 1.0)),
                     limit=2, poll=POLL, log=watch)

    assert len(done) == 2
    assert standing == [1, 1], (
        f"notices legible at each open: {standing}"
        " -- anything but 1 is two salts on one screen")


# --- her notice, taken at its word -----------------------------------------


def follow(notice: str, landmark: str) -> tuple[bytes, str]:
    """Do what the notice says, using only what the notice says.

    Nothing from `secret_matrix` is imported here on purpose. This is a
    stranger with the text in front of them: it pulls the domain separator
    out of the quoted recipe and the salt out of the line below it, and
    builds the address by hand. If the notice's wording stops describing
    what the code does, this stops producing her room.
    """
    recipe = next(l for l in notice.splitlines() if "sha256(" in l)
    info = re.search(r'sha256\("([^"]+)"', recipe).group(1)
    salt = bytes.fromhex(
        next(l for l in notice.splitlines() if "salt = " in l).split("= ")[1])

    # the order the recipe states, byte for byte
    assert recipe.index("salt") < recipe.index("name"), recipe
    assert "0x00" in recipe, recipe
    token = "w_" + hashlib.sha256(
        info.encode() + b"\x00" + salt + b"\x00" + landmark.encode()
    ).hexdigest()

    address = next(l for l in notice.splitlines() if "base64url" in l)
    assert "sha256(token)" in address and "[:22]" in address, address
    room = "w_" + base64.urlsafe_b64encode(
        hashlib.sha256(token.encode()).digest()).decode().rstrip("=")[:22]
    return salt, room


def test_a_stranger_who_does_exactly_what_the_notice_says_reaches_her(board):
    """The test this game never had, and the reason two defects survived
    into a live game.

    Every other test here drives *her*. The searcher's half of the game
    exists only as sentences in `carmel.open_campaign`, and sentences are
    not executed -- so the notice told players to *"hand what comes out to
    `join_room`"*, which refuses a bare token outright, and nobody found out
    until Gal and I tried to play on 2026-09-10.

    So this follows the notice rather than the source: it parses the recipe
    and the salt out of the posted text and rebuilds the address by hand. A
    notice that stops matching the code stops reaching her room, and this
    goes red.
    """
    seed = bytes.fromhex("55" * 32)
    world = C.Map(seed)
    first = C.itinerary(seed, C.LOBBY_LANDMARK, world, limit=1)[0]

    notice = C.open_campaign(seed, C.LOBBY_LANDMARK)
    salt, room = follow(notice, first["to"])

    # the address the notice describes is the room she is really in
    assert room == Rooms.workspace(room_token(first["to"], salt))

    # and standing in it, as the notice says to, is what she can see
    searcher = board.client(agent_id="stranger", workspace=room, key=KEY)
    searcher.register(name="stranger", kind="searcher", ttl=3600)
    result = driven(board).run(seed)
    assert result["outcome"] == "caught"
    assert result["by"] == "stranger"


def test_the_notice_says_that_reading_a_room_is_not_standing_in_it(board):
    """The other defect the same afternoon, and the crueller one.

    `say` does not put you on a roster -- only announcing does -- so a
    searcher who works out the right room, joins it and reads it in silence
    is invisible to her and cannot win. The notice said nothing about it.

    Asserted on her words *and* on the mechanism, because either alone is
    half a check: the first paragraph proves she warns them, the second
    proves the warning is true.
    """
    notice = C.open_campaign(bytes.fromhex("55" * 32), C.LOBBY_LANDMARK)
    # Below the rule, because this is the machinery talking and not her --
    # see `test_she_never_speaks_in_machinery`.
    plumbing = notice.split(C.PLUMBING_RULE)[1]
    assert "does not put you on its roster" in plumbing
    assert "announce yourself" in plumbing

    seed = bytes.fromhex("55" * 32)
    world = C.Map(seed)
    first = C.itinerary(seed, C.LOBBY_LANDMARK, world, limit=1)[0]
    _, room = follow(notice, first["to"])

    lurker = board.client(agent_id="lurker", workspace=room, key=KEY)
    lurker.post(L.CHANNEL, "I am here, surely that is enough")
    assert lurker.agents() == [], (
        "posting put somebody on the roster, so the warning is now false")

    result = driven(board).run(seed)
    assert result["outcome"] != "caught", (
        "a silent lurker was caught, so the notice's warning is wrong")


# --- a hub that is allowed to stumble --------------------------------------


class Flaky:
    """A room client that fails chosen calls and otherwise behaves.

    Wraps a real client rather than replacing one, so everything not being
    broken on purpose goes to the real hub and the campaign is a real
    campaign.
    """

    def __init__(self, inner, fails: set[int] | None = None,
                 after: int | None = None):
        self._inner, self._fails, self._after = inner, fails or set(), after
        self.calls = 0
        #: Injections that actually fired. Counted rather than inferred:
        #: asserting `calls > 20` made the test's own non-vacuity depend on
        #: how long the campaign ran, which depends on the treasure table,
        #: which differs between a checkout holding `absurd.tsv` and CI.
        #: It passed here and failed there for a reason that was not a bug.
        self.broke = 0

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if not callable(attr):
            return attr                      # `public_key` and friends

        def call(*a, **k):
            self.calls += 1
            if self.calls in self._fails or (
                    self._after is not None and self.calls > self._after):
                self.broke += 1
                raise ConnectionError(f"injected failure #{self.calls}")
            return attr(*a, **k)
        return call


class Stumbling(Rooms):
    """`Rooms`, but every client it hands out is `Flaky`."""

    def __init__(self, hub, **how):
        super().__init__(hub)
        self._how = how

    def room(self, token: str):
        if token not in self._open:
            self._open[token] = Flaky(
                self.hub.client(agent_id=self.agent_id,
                                workspace=self.workspace(token), key=KEY),
                **self._how)
        return self._open[token]


def test_a_dropped_connection_does_not_end_the_campaign(board):
    """The bug a live game found and the suite did not, 2026-09-11.

    A campaign died 150 seconds in on one
    `[SSL: UNEXPECTED_EOF_WHILE_READING]` from `room.heartbeat`. Nothing
    retried it, so the game ended with no close in the lobby and hints left
    pointing at a fugitive who was not coming.

    It was never survivable: `_stand` polls twice per `POLL_SECONDS`, so an
    eighty-minute campaign makes about 1,900 hub calls and any one of them
    could end it. This fails the 3rd, 9th and 20th call in every room she
    touches and requires the campaign to come out the same as an unbroken
    one.

    Made to fail on purpose by dropping the `_tolerate` around the
    heartbeat: the injected error propagates and the campaign never
    returns.
    """
    seed = bytes.fromhex("55" * 32)
    world = C.Map(seed)
    predicted = C.chase(seed, C.LOBBY_LANDMARK, searchers=0, world=world)

    rooms = Stumbling(board, fails={3, 9, 20})
    her = L.Fugitive(rooms, now=board.clock,
                     sleep=lambda s: board.clock.advance(max(s, 1.0)),
                     poll=POLL, log=lambda line: None)
    happened = her.run(seed)

    assert happened["outcome"] == predicted["outcome"]
    assert happened["reputation"] == predicted["reputation"]
    assert len(happened["moves"]) == len(predicted["moves"])
    broke = sum(r.broke for r in rooms._open.values())
    assert broke >= 2, (
        f"only {broke} injected failures fired: this campaign was too short"
        " to prove anything, so the test would pass on no retry at all")


def test_a_hub_that_never_comes_back_ends_it_out_loud(board):
    """The other half: a blip is survived, an outage is not pretended away.

    `CLAUDE.md`'s weaker-thing rule, on the wire. A campaign that has lost
    the hub must not look like one still being played -- it returns an
    outcome with a name, and it does not raise into whatever started it.
    """
    rooms = Stumbling(board, after=4)
    her = L.Fugitive(rooms, now=board.clock,
                     sleep=lambda s: board.clock.advance(max(s, 1.0)),
                     poll=POLL, log=lambda line: None)
    happened = her.run(bytes.fromhex("55" * 32))

    assert happened["outcome"] == "lost the hub"
    assert "ConnectionError" in happened["why"]


def test_she_does_not_retry_forever(board):
    """A retry loop that never gives up is an outage pretending to be a
    game. The budget is wall-clock, so the give-up is bounded however the
    call fails -- including on a bug that is not the network at all."""
    rooms = Stumbling(board, after=4)
    her = L.Fugitive(rooms, now=board.clock,
                     sleep=lambda s: board.clock.advance(max(s, 1.0)),
                     poll=POLL, log=lambda line: None)
    began = board.clock()
    her.run(bytes.fromhex("55" * 32))
    spent = board.clock() - began
    assert spent < 4 * L.OUTAGE_SECONDS, (
        f"{spent:.0f}s of clock to give up on a {L.OUTAGE_SECONDS:.0f}s"
        " budget")


def test_she_says_it_is_over_everywhere_she_robbed(board):
    """Gal, 2026-09-11: *"she should post a note (without announcing
    herself) that the game is over, in every room she's been at."*

    The close went to the lobby alone, and a searcher deep in a hunt left
    the lobby long ago. One swept 898 rooms for twenty minutes after she was
    caught, and could not have known: from inside a room, a finished game
    and a quiet one are the same silence. Now anybody standing anywhere on
    her trail is told.
    """
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    rooms = Rooms(board)
    result = driven(board).run(seed)

    visited = list(dict.fromkeys(leg["to"] for leg in result["moves"]))
    assert len(visited) >= 2, "too short a campaign to prove anything"
    for name in visited:
        said = [m["body"] for m in
                rooms.room(room_token(name, salt)).history(L.CHANNEL, limit=50)]
        assert any(b.startswith("It is over") for b in said), (
            f"{name} was never told the game had ended")
        assert any(seed.hex() in b for b in said), (
            f"{name} got the news without the seed that makes it checkable")


def test_she_says_it_is_over_without_standing_in_the_room(board):
    """The half that makes the above safe, and the one a reimplementation
    would get wrong.

    `post` leaves a message; `register` puts you on the roster; **only the
    roster is the catch**. The tempting way to write the broadcast is to
    join each room properly on the way out, and that version hands a catch
    to every searcher still waiting in a place she has left.

    Made to fail on purpose by registering before the close post: every
    visited room then shows `carmel` on its roster after the campaign.
    """
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    rooms = Rooms(board)
    result = driven(board).run(seed)

    # She is allowed to still be on the roster of the last place -- she was
    # standing in it when it ended. Everywhere earlier she must be gone.
    earlier = list(dict.fromkeys(leg["to"] for leg in result["moves"]))[:-1]
    for name in earlier:
        roster = rooms.room(room_token(name, salt)).agents()
        assert not [a for a in roster if a.get("name") == "carmel"], (
            f"she is on {name}'s roster after posting the close there,"
            " which would hand a catch to anyone still waiting")


def test_the_hint_is_left_in_the_room_she_is_leaving(board):
    """The chain a searcher actually follows: what she says about leg two is
    in the room leg one took them to, so a searcher who guesses right is
    handed the next question and one who guesses wrong is handed nothing."""
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    world = C.Map(seed)
    trail = C.itinerary(seed, C.LOBBY_LANDMARK, world, limit=3)

    rooms = Rooms(board)
    driven(board).run(seed)

    lobby = rooms.room(L.lobby_token())
    said = [m["body"] for m in lobby.history(L.CHANNEL, limit=200)]
    assert any(C.riddle(seed, trail[0]["to"], trail[0]["details"])[0] in line
               for line in said), \
        "the first riddle belongs in the lobby, which is where she starts"

    second = rooms.room(room_token(trail[0]["to"], salt))
    said = [m["body"] for m in second.history(L.CHANNEL, limit=200)]
    assert any(C.riddle(seed, trail[1]["to"], trail[1]["details"])[0] in line
               for line in said), \
        "the second hint belongs in the room the first one pointed at"


def test_she_names_no_room_and_no_landmark_she_has_not_been_in(board):
    """The disclosure guard, on the wire this time rather than on a card.
    A hint that carried an address, or a name, would end the game."""
    seed = bytes.fromhex("55" * 32)
    salt = salt_for(seed)
    world = C.Map(seed)
    rooms = Rooms(board)
    result = driven(board).run(seed)

    walked = [C.LOBBY_LANDMARK] + [leg["to"] for leg in result["moves"]]
    spoken = []
    for name in walked:
        token = L.lobby_token() if name == C.LOBBY_LANDMARK \
            else room_token(name, salt)
        spoken += [m["body"] for m in
                   rooms.room(token).history(L.CHANNEL, limit=200)]
    body = "\n".join(spoken)

    for place in world.places:
        if place in walked:
            continue
        assert place not in body, place
    for name in walked[1:]:
        assert room_token(name, salt) not in body, "she published an address"
