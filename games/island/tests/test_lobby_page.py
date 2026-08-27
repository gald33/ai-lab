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
