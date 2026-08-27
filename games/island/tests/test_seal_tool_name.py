"""The sealed-to-one-peer tool is `whisper`, and only half of the rename is an alias.

`ask` before 1.0.0, `whisper` from it. `Client.ask()` survives as an alias, so
every library call kept working across that release -- but the MCP tool list
carries `whisper` only. An entrant is an agent holding MCP tools, so the half
that is not aliased is precisely the half entrants live on: a briefing or an
allowlist that says `ask` leaves an agent able to read what it was dealt and
unable to answer, with nothing failing loudly anywhere. This repo pins `>=1.0`
and uses the new name alone, on both sides.
"""

from __future__ import annotations

import inspect

from games.island import run_entrant, run_game


def test_the_manager_whispers_and_says_so():
    src = inspect.getsource(run_game.deal)

    assert "mgr.client.whisper(" in src
    assert "`whisper`" in src, "the name it tells a seat to answer with"
    assert ".ask(" not in src and "`ask`" not in src


def test_an_entrant_holds_whisper_and_not_the_old_name():
    assert "mcp__switchboard__whisper" in run_entrant.TOOLS
    assert "mcp__switchboard__ask" not in run_entrant.TOOLS


def test_the_installed_client_actually_has_it():
    """The pin is in prose, so this is what enforces it.

    Nothing in `games/island/` declares a dependency, so a host that installed
    an older release gets a `Client` without `whisper` and finds out halfway
    through dealing a settled table -- after the seed is drawn and the seats
    are told a sealed round is coming. Fail here instead.
    """
    from switchboard.client import Client

    assert hasattr(Client, "whisper"), (
        "agent-switchboard >=1.0 is required: `whisper` is the only name the "
        "MCP surface carries, and the manager deals through it")
