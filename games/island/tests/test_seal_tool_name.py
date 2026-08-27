"""The sealed-to-one-peer tool changed name, and only half of it is an alias.

`ask` in 0.11.0, `whisper` from 1.0.0. `Client.ask()` survives as an alias, so
every library call kept working across that release -- but the MCP tool list
carries `whisper` only. An entrant is an agent holding MCP tools, so the half
that is not aliased is precisely the half entrants live on: a briefing or an
allowlist that says `ask` leaves an agent able to read what it was dealt and
unable to answer, with nothing failing loudly anywhere.
"""

from __future__ import annotations

from games.island import run_entrant, run_game


class _Whispers:
    def whisper(self, to, body):
        return ("whisper", to, body)

    def ask(self, to, body):           # the alias, still there
        return ("ask", to, body)


class _OnlyAsks:
    def ask(self, to, body):
        return ("ask", to, body)


def test_the_manager_says_the_name_this_release_actually_has():
    assert run_game._seal_tool(_Whispers()) == "whisper"
    assert run_game._seal_tool(_OnlyAsks()) == "ask"


def test_it_seals_under_whichever_name_is_there():
    assert run_game._seal(_Whispers(), "t1", "hi")[0] == "whisper"
    assert run_game._seal(_OnlyAsks(), "t1", "hi")[0] == "ask"


def test_an_entrant_is_allowed_both_names():
    """An allowlist entry for a tool the server does not expose is inert, so
    naming both is what lets the pin move either way without disarming every
    entrant."""
    assert "mcp__switchboard__whisper" in run_entrant.TOOLS
    assert "mcp__switchboard__ask" in run_entrant.TOOLS
