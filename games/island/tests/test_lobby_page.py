"""The lobby as a page: does it say what the board says, and nothing more?"""

from __future__ import annotations

import re
import json
import time

import pytest

from switchboard.crypto import generate_key

from games.island import lobby_page
from games.island.lobby import Lobby
from games.island.tests.test_lobby import _client, _entrant


def _settled(hub, key):
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2 nonce=" + "ab" * 8)
    _entrant(hub, "t2", key).post("lobby", "JOIN g1 as trader-b nonce=" + "cd" * 8)
    _entrant(hub, "m", key).post("lobby", "MANAGE g1")
    lobby.drain()
    return lobby


def test_the_page_shows_the_seats_and_the_keys_they_were_witnessed_under(hub):
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0)

    table = lobby.tables["g1"]
    assert "scout-v2" in page and "trader-b" in page
    for key in table.keys.values():
        assert key in page, "a witnessed key is public and belongs on the page"
    assert "settled" in page and table.commit[:16] in page
    assert "draw is checkable" in page


def test_a_forming_table_shows_its_open_seats_and_when_it_lapses(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert "forming — 1/2 seated" in page
    assert "open seat" in page
    assert "lapses in 15m" in page


def test_an_empty_lobby_says_what_to_post(hub):
    page = lobby_page.render(Lobby(client=_client(hub, "lobby", generate_key())))

    assert "no tables" in page and "OPEN traders=2" in page


def test_nothing_secret_reaches_the_page(hub):
    """The seed is drawn at settlement and never posted; the lobby's own nonce
    is what makes the draw checkable afterwards. Neither belongs here."""
    lobby = _settled(hub, generate_key())
    table = lobby.tables["g1"]

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert str(table.seed) not in page
    assert table.nonce not in page
    assert table.commit in page or table.commit[:16] in page


def test_the_page_is_written_atomically(hub, tmp_path):
    lobby = _settled(hub, generate_key())
    out = tmp_path / "pages" / "lobby.html"

    lobby_page.write(lobby, out)

    assert out.read_text().startswith("<!doctype html>")
    assert not list(out.parent.glob("*.tmp")), "no half-written file left behind"


def test_the_page_names_the_key_the_lobby_is_listening_under(hub):
    """The one failure no other signal catches.

    A lobby holding the wrong workspace key stays up, keeps rewriting its
    page, runs as exactly one process, and hears nobody -- a key that does not
    match is silence rather than an error. So the key goes on the page, where
    anyone can compare it against ENTER.md.
    """
    key = generate_key()
    lobby = _settled(hub, key)

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert key in page
    assert "ENTER.md" in page


def test_a_keyless_lobby_says_it_can_witness_nothing(hub):
    lobby = Lobby(client=_client(hub, "lobby", None))

    page = lobby_page.render(lobby)

    assert "no key" in page


def test_the_page_points_at_where_a_finished_game_can_be_watched(hub):
    """Two live surfaces with no path between them is a door into a room
    nobody can see, and a spectacle nobody can find the door to."""
    page = lobby_page.render(Lobby(client=_client(hub, "lobby", generate_key())))

    assert lobby_page.VIEWER in page


def test_the_prompt_carries_the_key_the_lobby_actually_holds(hub):
    """Built from live config, never written down.

    A prompt with a stale key does not fail -- the agent writes into a room
    nobody is reading, and both sides call it silence. Deriving it from the
    running lobby is what makes that impossible rather than merely unlikely.
    """
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))

    text = lobby_page.prompt(lobby)

    assert key in text
    assert lobby.client.config.workspace in text
    assert lobby.client.config.url in text


def test_the_prompt_works_for_an_agent_without_mcp_tools(hub):
    """Some agents hold Switchboard's MCP tools. Some hold none and can
    install the client themselves. A door that only opens for the first kind
    is a door for people who already have the key."""
    text = lobby_page.prompt(Lobby(client=_client(hub, "lobby", generate_key())))

    assert 'pip install "agent-switchboard>=2.0.1"' in text
    assert "switchboard say lobby" in text, "the say-positional trap, warned"
    assert "join_room" in text and "switchboard join" in text


def test_the_start_block_shows_the_prompt_it_copies(hub):
    """A button that copies something the reader cannot see asks them to paste
    an unread instruction into an agent they answer for."""
    lobby = Lobby(client=_client(hub, "lobby", generate_key()))

    page = lobby_page.render(lobby)

    assert "Copy the prompt" in page
    assert "OPEN traders=2" in page, "the text is on the page, not only behind it"
    # And the clipboard is not assumed: plain http and embedded browsers have none.
    assert "isSecureContext" in page and "Select-copy" in page


def test_the_lobby_links_to_the_door_a_hand_goes_through(hub):
    """**The link is the whole dependency between the two, so it is checked.**

    The hand's pages are separate, and this one stays static, keyless and
    read-only because of it -- the originals are untouched, which is the
    property that separation buys. What survives of the relationship is one
    link, and a static file pointing at a URL fails silently when either end
    moves: nothing here would notice, and a hand would simply never find the
    door. An assertion is the difference between a convention and a check.

    The sentence beside it moved too. It used to read "You do not play this
    yourself -- your agent does", which stopped being true the moment a person
    could take a seat.
    """
    page = lobby_page.render(_settled(hub, generate_key()), now=1_000_000.0)

    assert lobby_page.HAND in page
    assert "rather take the seat yourself" in page
    assert "never ranked" in page, "and what it costs, beside the offer"
    assert "Ordinarily you do not play this yourself" in page
    # **The offer says the person plays, and never that they help an agent
    # play.** Both declared modes are person-driven -- in `advised` the hand
    # carries the model's line, in `assisted` it may deviate -- and there is
    # no mode where the agent plays while somebody assists it. Copy implying
    # one would blur the two words the declaration exists to keep apart, and
    # that blur would end up in somebody's `HAND:` line.
    assert "you play the seat" in page
    # And the offer is honest about the joint case, which is the intended
    # one: a driver may hand the seat to an agent, and then nothing on the
    # board separates them. Naming that here stops the page promising a
    # distinction the record cannot keep.
    assert "drive alongside it" in page
    assert "how much you drove" in page
    assert "help" not in page.lower().split("<footer>")[0]


def _live(tmp_path, table_id="g1", finished=False):
    """A `--live` directory holding one game's board, running or finished."""
    d = tmp_path / "live"
    d.mkdir(exist_ok=True)
    state = {"episode": 1}
    if finished:
        state["finished"] = {"board": f"board-{table_id}.json",
                             "reveal": f"reveal-{table_id}.json"}
    (d / f"{table_id}.json").write_text(json.dumps(state))
    return d


def test_a_running_game_gets_a_live_button(hub, monkeypatch, tmp_path):
    """The door to a game in progress, drawn as a door.

    It used to be a `&middot;`-separated link at the tail of the "managed by"
    line, which is the one place on the page a reader scanning for something
    to look at does not read. A game nobody finds the door to is the failure
    the viewer exists to prevent.
    """
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live/")
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0, live_dir=_live(tmp_path))

    assert "Watch this game live" in page
    assert "https%3A%2F%2Fhost.example%2Flive%2Fg1.json" in page
    assert "class=\'t settled live\'" in page, "the table itself is marked live"
    assert "1 playing now · 0 forming" in page


def test_a_finished_game_says_recording_and_not_live(hub, monkeypatch, tmp_path):
    """"Live" is a claim about right now, and the board cannot make it: a table
    settles and the board never mentions it again. The last bell is written
    into the live file as its `finished` block, so that is what decides the
    word -- otherwise the page calls an hour-old game live because it was live
    once."""
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0,
                             live_dir=_live(tmp_path, finished=True))

    assert "Watch the recording" in page
    assert "Watch this game live" not in page
    assert "class=\'t settled\'" in page, "not outlined as live"
    assert "0 playing now · 0 forming · 1 to watch back" in page
    # Same URL either way: the live file is the archive.
    assert "https%3A%2F%2Fhost.example%2Flive%2Fg1.json" in page


def test_a_host_that_wrote_no_live_file_offers_no_button(hub, monkeypatch, tmp_path):
    """A door onto a 404 is worse than no door."""
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0, live_dir=tmp_path / "live")

    assert 'class="watchbtn' not in page


def test_with_no_live_directory_the_page_claims_neither(hub, monkeypatch):
    """`run_lobby --page` plays nothing and reads no live directory, so it
    cannot tell a running game from a finished one. It says so rather than
    guessing: claiming "live" from a fact that was true once is the bug."""
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert "Watch this game</a>" in page
    assert "does not say whether the game is still running" in page


def test_the_live_base_is_read_at_render_time_not_at_import(hub, monkeypatch, tmp_path):
    """As a module constant this was fixed by whatever the environment held
    when the first import ran, so a host that exported it after start-up got
    no button and no error saying why -- a feature shipped turned off."""
    monkeypatch.delenv("ISLAND_LIVE_BASE", raising=False)
    lobby = _settled(hub, generate_key())
    live = _live(tmp_path)

    # Unset, the button is still there since 2026-09-03 -- pointed at the
    # room's read-only invite, which needs no live file from this host.
    page = lobby_page.render(lobby, now=1_000_000.0, live_dir=live)
    assert 'class="watchbtn' in page and "?invite=" in page
    assert "host.example" not in page

    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")

    # Set at render time, the host's own live file is what the button reads,
    # because the file knows the ending for sure and the schedule only guesses.
    page = lobby_page.render(lobby, now=1_000_000.0, live_dir=live)
    assert 'class="watchbtn' in page and "host.example" in page


def test_a_lapsed_table_offers_nothing_to_watch(hub, monkeypatch, tmp_path):
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")
    lobby = _settled(hub, generate_key())
    lobby.tables["g1"].lapsed = True

    assert 'class="watchbtn' not in lobby_page.render(lobby, now=1_000_000.0,
                                               live_dir=_live(tmp_path))


def test_the_page_says_how_old_the_copy_in_front_of_the_reader_is(hub):
    """A static page is stale the moment after it is written, and a lobby that
    has stopped being rewritten looks exactly like one where nothing is
    happening. The reload is one half of the fix; saying the age is the other,
    because a frozen page carries a perfectly plausible-looking timestamp."""
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert f"http-equiv=refresh content={lobby_page.PAGE_REFRESH}" in page
    assert "data-at='1000000'" in page
    assert "STALE" in page and str(lobby_page.STALE_AFTER) in page


def test_a_forming_table_names_what_it_is_waiting_for(hub):
    """"1/2 seated" says how far along it is, not what would move it -- and an
    empty seat and a missing manager are jobs for different people."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert "Waiting for 1 more entrant to sit down and somebody to offer to " \
           "manage it." in page


# --- the levers -------------------------------------------------------------


def test_the_levers_offer_exactly_the_ladder_the_lobby_will_accept():
    """A lever that offers a value the lobby refuses is a trap on the page."""
    from games.island.protocol import EPISODE_SECONDS_ALLOWED
    seconds = dict((f, vals) for f, _, vals in lobby_page.LEVERS)["seconds"]
    assert tuple(seconds) == EPISODE_SECONDS_ALLOWED


def test_every_value_any_lever_offers_is_a_line_the_lobby_parses():
    """**The check the `seconds` assertion above was too narrow to make.**

    `goods` offered 6, 7 and 8 -- the viewer's palette -- long after
    `GOODS_MAX` came down to the island's five, and `rounds` offered 2, 3 and
    5, which the host has never played. Both showed a reader a value, rewrote
    the OPEN line with it, and left their agent's OPEN to come back Malformed.
    So this walks every rung of every lever rather than one ladder.
    """
    from games.island.protocol import parse  # noqa: PLC0415

    for field, _label, values in lobby_page.LEVERS:
        for v in values:
            parse(lobby_page.open_line(**{field: v}))  # raises if refused


def test_rounds_is_in_the_open_line_but_is_not_a_knob():
    """A select with one option is a choice the reader does not have.

    `ROUNDS_MAX` is 1, so a ladder built from the protocol's bounds had a
    single rung. The field still belongs in the OPEN line -- that is how an
    entrant learns it exists -- but the control claimed a choice the lobby
    will not honour, so it is gone until `ROUNDS_MAX` rises.
    """
    from games.island.protocol import ROUNDS_MAX  # noqa: PLC0415

    assert ROUNDS_MAX == 1
    assert "rounds" not in [f for f, _l, _v in lobby_page.LEVERS]
    assert "rounds=1" in lobby_page.open_line()


def test_only_the_start_is_unfolded_and_the_prompt_is_never_folded(hub):
    """**What a reader meets before they have scrolled.**

    The page had grown to ~1,200 words before the first table, all of it true,
    which is why none of it could simply be deleted. Only one thing on it is
    immediate: your agent plays this, here is what to give it. So the title,
    the one line of orientation, the button and the prompt stay; the rest waits
    behind a summary.

    The prompt is deliberately not among the folds, for the reason `_start`
    already gives: a button that copies something the reader cannot see asks
    them to paste an instruction they have not read into an agent they are
    responsible for. Folding it would put the text behind the button again by
    another route.
    """
    page = lobby_page.render(_settled(hub, generate_key()), now=1_000_000.0)

    folded = set(re.findall(r"<details class=fold data-fold=(\w+)>", page))
    assert folded == set(lobby_page.FOLDS)
    # None of them is open on arrival: `<details>` without `open` is shut.
    assert "<details class=fold data-fold" in page
    assert "<details open" not in page and "open class=fold" not in page

    # The prompt and its button are in no fold at all.
    before_first_fold = page[:page.index("<details class=fold")]
    assert "<pre id=pr>" in page
    body = page[page.index("<button id=cp>"):]
    assert body.index("</pre>") < body.index("<details class=fold"), \
        "the prompt must come before -- and outside -- any fold"
    assert "The island — lobby" in before_first_fold


def test_a_fold_a_reader_opened_survives_the_meta_refresh(hub):
    """**A page that reloads every 15s and forgets is worse than no fold.**

    Same trap the levers hit and the countdowns before them: the reload puts
    every `<details>` back on what the server wrote. A reader who opened the
    levers and chose four traders would watch the section shut a few seconds
    later -- and the levers restore their *value*, so the choice would still be
    live and no longer visible, which is worse than losing it.
    """
    page = lobby_page.render(_settled(hub, generate_key()), now=1_000_000.0)

    assert f"sessionStorage.getItem('{lobby_page.FOLDS_KEY}'" in page
    assert f"sessionStorage.setItem('{lobby_page.FOLDS_KEY}'" in page
    assert "'toggle'" in page, "a fold is remembered when the reader moves it"


def test_the_fold_script_comes_after_the_folds_it_restores(hub):
    """The frozen-countdown failure, in a second shape.

    `querySelectorAll('details.fold')` running above the folds matches nothing,
    every fold stays on the server's default, and no markup assertion can see
    it -- `data-fold` present, `sessionStorage` present, the listener present,
    all of it in the wrong order. Asserted rather than trusted, because that is
    exactly how the ticker shipped broken.
    """
    page = lobby_page.render(_settled(hub, generate_key()), now=1_000_000.0)

    assert page.index("details.fold") > page.rindex("<details class=fold"), \
        "the restoring script must come after every fold it looks for"


def test_the_page_names_the_harnesses_somebody_has_actually_played_from():
    """"Anything holding Switchboard's tools" is true and no help to a reader.

    The list is what has been sat from, and the caveat is the one that
    catches people: cached browsing cannot hold a live board.
    """
    out = lobby_page._harnesses()
    for name in ("Cursor", "Claude Code", "ChatGPT"):
        assert name in out
    assert "MCP" in out and "cache" in out


def test_the_levers_survive_the_meta_refresh(hub):
    """**The reload was putting every knob back on its default.**

    The page reloads every `PAGE_REFRESH` and a `<select>` comes back on its
    `selected` option, so a reader who set traders=4 watched it snap to 2 --
    and then copied a prompt whose OPEN line was not the one they had read.
    Carried across the reload in `sessionStorage`, like the countdowns.

    A restored value is applied only if it is still one of the options: the
    ladders move, and a stored value the lobby now refuses is the trap the
    fixed lists exist to avoid.
    """
    page = lobby_page.render(_settled(hub, generate_key()), now=1_000_000.0)

    assert f"sessionStorage.setItem('{lobby_page.LEVERS_KEY}'" in page
    assert f"sessionStorage.getItem('{lobby_page.LEVERS_KEY}')" in page
    assert "s.options" in page and "if(ok) s.value=v;" in page
    # Saved on the way out and re-read on the way in, or a reload loses the
    # choice it was meant to carry.
    assert "restore();" in page and "save(); redraw();" in page


def test_the_prompt_carries_the_open_line_the_levers_rewrite(hub):
    """The copy button reads the whole block, so the span must be in it.

    If the wrap ever misses, the page silently goes back to copying a fixed
    line while the levers appear to work -- which is worse than no levers.
    """
    lobby = Lobby(client=_client(hub, "lobby", generate_key()))
    html_out = lobby_page._start(lobby)
    assert "<span id=ol>" in html_out
    assert lobby_page.open_line() in lobby_page.prompt(lobby)


def test_the_suggested_open_spells_out_seconds_so_the_knob_is_discoverable():
    assert "seconds=60" in lobby_page.open_line()


# --- the countdown ---------------------------------------------------------
#
# A settled table announces `opens 19:40:00Z` and then the page sits in
# somebody's browser. The time is correct, in a timezone the reader is not in,
# for a moment that may already have passed.

def test_a_settled_table_counts_down_to_its_own_start(hub):
    lobby = _settled(hub, generate_key())
    table = lobby.tables["g1"]
    assert table.opens_at, "the lobby settles the moment it announces"

    page = lobby_page.render(lobby, now=table.opens_at - 95)

    assert "opens in 1m 35s" in page
    # And the absolute time stays beside it: it is the one thing a reader with
    # no script still needs, and the fixed point two readers can compare.
    assert time.strftime("%H:%M:%SZ", time.gmtime(table.opens_at)) in page
    assert "the game has started" in page


def test_the_countdown_carries_what_is_left_and_never_an_instant(hub):
    """**The whole of the design, and the reason it is not the obvious one.**

    Putting the absolute instant in the page and subtracting `Date.now()`
    reads a browser whose clock runs three minutes fast as "the game has
    started" for a table that has not opened. Telling a reader the game began
    when it did not is worse than telling them nothing, so the page carries
    how long was left when it was written and the script subtracts only time
    it has measured itself.
    """
    lobby = _settled(hub, generate_key())
    table = lobby.tables["g1"]

    page = lobby_page.render(lobby, now=table.opens_at - 42)

    assert "data-left='42'" in page
    assert str(int(table.opens_at)) not in page, (
        "an epoch instant on the page is something a browser would subtract "
        "its own clock from")
    assert "Date.now()-t0" in page, "elapsed since the script ran, not a clock"


def test_a_moment_already_past_counts_to_zero_rather_than_backwards(hub):
    lobby = _settled(hub, generate_key())
    table = lobby.tables["g1"]

    page = lobby_page.render(lobby, now=table.opens_at + 600)

    assert "data-left='0'" in page
    assert "-600" not in page and "opens in -" not in page


def test_the_lapse_clock_ticks_too_rather_than_freezing_at_write(hub):
    """It read `lapses in 14m 03s` and stayed there, on a page that refreshes
    every 15 seconds and may have been open for longer."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()

    page = lobby_page.render(lobby, now=1_000_000.0 + 60)

    assert "lapses in 14m 00s" in page
    assert "data-prefix='lapses'" in page


def test_the_ticker_comes_after_the_countdowns_it_drives(hub):
    """**It did not, and every countdown on the page was frozen.**

    The script runs at parse time and takes its elements once, with one
    `querySelectorAll('.cd')`. It sat above the table rows, so it matched
    nothing, and each countdown showed the number the server had written and
    never moved -- for `PAGE_REFRESH` at a time, on a page whose whole point
    is that the number is live.

    Every test around this one asserted on markup and passed throughout:
    `data-key` was there, `sessionStorage` was there, the resync bound was
    there. All of it was there, in the wrong order, and order is the one thing
    a fragment assertion cannot see. Hence this test, and the browser one
    below it.
    """
    page = lobby_page.render(_settled(hub, generate_key()), now=1_000_000.0)

    assert page.rindex("class=cd") < page.index("querySelectorAll('.cd')")


def test_a_countdown_actually_moves_in_a_browser(hub):
    """The only assertion that was ever really being made: the number changes.

    Skipped where there is no browser, and run for real in the `drawing` CI
    job, which has one -- see `.github/workflows/tests.yml`. That job sets
    `ISLAND_REQUIRE_BROWSER`, which turns each skip below into a failure, for
    the reason `render.py --require` exists: a skip and a pass are the same
    tick, and a job that quietly rendered nothing is worse than no job.
    """
    import os
    import pathlib

    def missing(why: str):
        if os.environ.get("ISLAND_REQUIRE_BROWSER"):
            pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                        f"checked no countdown at all")
        pytest.skip(why)

    try:
        from playwright import sync_api as play
    except ImportError:
        missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)

    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    page = tmp_page(lobby)

    with play.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(
                executable_path=str(chrome) if chrome else None)
        except Exception as exc:                       # noqa: BLE001
            missing(f"no chromium to drive a page with: {exc!r}")
        tab = browser.new_page()
        tab.goto(page.as_uri())
        first = tab.inner_text(".cd")
        tab.wait_for_timeout(3000)
        second = tab.inner_text(".cd")
        browser.close()

    assert first.startswith("lapses in "), first
    assert second != first, f"the countdown froze at {first!r}"


def test_the_levers_rewrite_the_open_line_into_one_the_lobby_parses(hub):
    """Driven in a browser, because the levers are behaviour and not markup.

    The ladders are asserted against `parse` above, but that check reads the
    Python tuples; what a reader copies is whatever the script wrote into the
    `#ol` span. So this moves every lever to its last rung in a real browser
    and hands the resulting line back to the lobby's own parser.
    """
    import os
    import pathlib

    def missing(why: str):
        if os.environ.get("ISLAND_REQUIRE_BROWSER"):
            pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                        f"checked no lever at all")
        pytest.skip(why)

    try:
        from playwright import sync_api as play
    except ImportError:
        missing("no playwright to drive a page with")
    from games.island.protocol import parse  # noqa: PLC0415

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    page = tmp_page(lobby)

    with play.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(
                executable_path=str(chrome) if chrome else None)
        except Exception as exc:                       # noqa: BLE001
            missing(f"no chromium to drive a page with: {exc!r}")
        tab = browser.new_page()
        tab.goto(page.as_uri())
        default = tab.inner_text("#ol")
        # The levers are folded shut on arrival, so a reader opens them
        # before touching one -- and a select inside a shut `<details>` is
        # not reachable, which is why this line is here rather than assumed.
        tab.click("details.fold[data-fold=levers] > summary")
        for field, _label, values in lobby_page.LEVERS:
            tab.select_option(f".levers select[data-f={field}]", str(values[-1]))
        topped = tab.inner_text("#ol")
        browser.close()

    # What the page shows before anybody touches it, and after every knob is
    # turned to its far end: both must be lines the lobby will take.
    assert parse(default) == parse(lobby_page.open_line())
    top = parse(topped)
    assert top.traders == lobby_page.LEVERS[0][2][-1]
    assert top.rounds == 1


def tmp_page(lobby, now: float = 1_000_000.0):
    """The rendered page on disk, for a browser to open."""
    import tempfile
    from pathlib import Path

    path = Path(tempfile.mkdtemp()) / "lobby.html"
    return lobby_page.write(lobby, path, now=now)


def test_one_ticker_however_many_countdowns(hub):
    """A script per countdown would be several intervals disagreeing about the
    same second."""
    key = generate_key()
    lobby = _settled(hub, key)
    _client(hub, "opener2", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert page.count("class=cd") >= 2, "more than one countdown on the page"
    assert page.count("querySelectorAll('.cd')") == 1


def test_minutes_appear_only_once_there_are_minutes():
    """`in 90s` is a clearer thing to wait out than `in 1m 30s`."""
    assert lobby_page._span(0) == "in 0s"
    assert lobby_page._span(59) == "in 59s"
    assert lobby_page._span(60) == "in 1m 00s"
    assert lobby_page._span(95) == "in 1m 35s"
    assert lobby_page._span(-5) == "in 0s"


def test_a_countdown_escapes_what_it_is_given():
    marked = lobby_page._countdown(30, key="g1'<b>:opens", prefix="opens<b>",
                                   at="x'y", after="&")

    assert "<b>" not in marked and "&lt;b&gt;" in marked
    assert "x'y" not in marked and "&#x27;" in marked


def test_a_countdown_carries_across_the_meta_refresh(hub):
    """**The refresh was making the second hand lurch backwards.**

    The page reloads every `PAGE_REFRESH`, and the copy it reloads was written
    up to an interval before it is read -- so every reload replaced a number
    the browser had been ticking down with an older one and the countdown
    jumped. The deadline was never wrong; what a reader watched was.

    So each countdown is named, and the script carries what it was counting
    across the reload in `sessionStorage`, resyncing to the server only when
    the two have drifted further apart than page staleness can explain.
    """
    lobby = _settled(hub, generate_key())
    table = lobby.tables["g1"]

    page = lobby_page.render(lobby, now=table.opens_at - 42)

    assert f"data-key='{table.id}:opens'" in page
    assert "sessionStorage" in page
    # And it is still elapsed time, never a browser clock against a server one:
    # both readings in the comparison come from this browser's own `Date.now`.
    assert "saw.left-(t0-saw.t)/1000" in page
    assert f"<={lobby_page.RESYNC}" in page


def test_a_fold_stays_open_across_a_reload_in_a_real_browser(hub):
    """**The assertion the markup one above cannot make.**

    Everything the fold needs can be present and still not work: the store, the
    key, the listener, the `data-fold` names. What decides it is whether the
    script runs after the elements exist and whether the browser really puts
    the section back. That is behaviour, so it is watched happening -- see
    `CLAUDE.md`, "A page's behaviour is checked in a browser".

    Opens the levers, reloads the page the way the meta refresh does, and
    requires the levers still open and the other folds still shut. A fold that
    reopened *every* section would pass a weaker check and be its own bug.
    """
    import os
    import pathlib

    def missing(why: str):
        if os.environ.get("ISLAND_REQUIRE_BROWSER"):
            pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                        f"checked no fold at all")
        pytest.skip(why)

    try:
        from playwright import sync_api as play  # noqa: PLC0415
    except ImportError:
        missing("no playwright to drive a page with")

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    page = tmp_page(_settled(hub, generate_key()))

    with play.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(
                executable_path=str(chrome) if chrome else None)
        except Exception as exc:                       # noqa: BLE001
            missing(f"no chromium to drive a page with: {exc!r}")
        tab = browser.new_page()
        tab.goto(page.as_uri())

        shut = tab.eval_on_selector_all(
            "details.fold", "els => els.map(e => e.open)")
        tab.click("details.fold[data-fold=levers] > summary")
        opened = tab.is_visible(".levers select")

        tab.reload()
        after = tab.eval_on_selector_all(
            "details.fold", "els => els.map(e => [e.dataset.fold, e.open])")
        browser.close()

    assert shut and not any(shut), "every fold is shut on arrival"
    assert opened, "opening a fold reveals what is inside it"
    state = dict(after)
    assert state["levers"] is True, \
        "the fold the reader opened shut itself on the refresh"
    assert [f for f, o in after if o] == ["levers"], \
        "only the fold the reader opened comes back open"


def test_every_countdown_on_the_page_is_named_apart(hub):
    """One `sessionStorage` key for two countdowns would have each reload hand
    the other's remainder over, which is the jump again with worse arithmetic.
    """
    key = generate_key()
    lobby = _settled(hub, key)
    _client(hub, "opener2", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()

    page = lobby_page.render(lobby, now=1_000_000.0)

    keys = re.findall(r"data-key='([^']*)'", page)
    assert len(keys) >= 2 and len(set(keys)) == len(keys), keys
