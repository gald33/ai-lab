"""The lobby as a page: does it say what the board says, and nothing more?"""

from __future__ import annotations

import time

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

    assert 'pip install "agent-switchboard>=1.2.2"' in text
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


def test_a_settled_table_gets_a_watch_button_when_a_live_board_is_served(hub, monkeypatch):
    """The door to a game in progress, drawn as a door.

    It used to be a `&middot;`-separated link at the tail of the "managed by"
    line, which is the one place on the page a reader scanning for something
    to look at does not read. A game nobody finds the door to is the failure
    the viewer exists to prevent.
    """
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live/")
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert "Watch this game live" in page
    assert "watchbtn" in page
    assert "https%3A%2F%2Fhost.example%2Flive%2Fg1.json" in page
    assert "no key needed" in page, "a spectator reads and cannot write"
    assert "class='t settled live'" in page, "the table itself is marked live"


def test_the_live_base_is_read_at_render_time_not_at_import(hub, monkeypatch):
    """As a module constant this was fixed by whatever the environment held
    when the first import ran, so a host that exported it after start-up got
    no button and no error saying why -- a feature shipped turned off."""
    monkeypatch.delenv("ISLAND_LIVE_BASE", raising=False)
    lobby = _settled(hub, generate_key())

    assert "Watch this game live" not in lobby_page.render(lobby, now=1_000_000.0)

    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")

    assert "Watch this game live" in lobby_page.render(lobby, now=1_000_000.0)


def test_a_lapsed_table_offers_nothing_to_watch(hub, monkeypatch):
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")
    lobby = _settled(hub, generate_key())
    lobby.tables["g1"].lapsed = True

    assert "Watch this game live" not in lobby_page.render(lobby, now=1_000_000.0)


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


def test_the_header_counts_what_is_playing_and_what_is_forming(hub, monkeypatch):
    monkeypatch.setenv("ISLAND_LIVE_BASE", "https://host.example/live")
    lobby = _settled(hub, generate_key())

    page = lobby_page.render(lobby, now=1_000_000.0)

    assert "1 playing now · 0 forming" in page
