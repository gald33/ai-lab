"""A spectator reads a live game without holding anything they could write with.

`games/island.md` concluded that watching a running game needed a read-only
invite from Switchboard, because an invite is a read-write credential. The
credential half is true; the conclusion was not. Reading a room needs no
credential at all when somebody already in the room does the reading -- which
the manager does on every drain anyway.
"""

from __future__ import annotations

import json
from pathlib import Path

from switchboard.crypto import generate_key

from games.island import live
from games.island.tests.test_lobby import _client


def test_the_snapshot_is_the_shape_the_viewer_reads(hub):
    """`rowsFromState` wants `{messages: [{seq, created_at, from, body}]}`."""
    c = _client(hub, "mgr", generate_key())
    c.register(name="mgr", kind="local", branch="m", task="")
    c.post("island", "episode 1 of 8 is open")

    snap = live.snapshot(c, "island")

    assert snap["channel"] == "island"
    m = snap["messages"][0]
    assert {"seq", "created_at", "channel", "from", "body"} == set(m)
    assert isinstance(m["from"], dict) and "id" in m["from"]
    assert m["body"] == "episode 1 of 8 is open"


def test_it_carries_the_board_and_cannot_carry_the_sealed_half(hub):
    """Not a redaction step -- a property of where the two kinds of line live.

    A trader's plan is whispered to the manager's own channel, so it is not on
    the board and cannot reach a snapshot of the board. This test exists so
    that stops being an argument and starts being a check.
    """
    key = generate_key()
    mgr = _client(hub, "mgr", key)
    mgr.register(name="mgr", kind="local", branch="m", task="")
    t1 = _client(hub, "t1", key)
    t1.register(name="t1", kind="local", branch="m", task="")
    # Both sides read the roster before sealing -- and the manager registered
    # first, or t1 would hold no key to seal to it.
    t1.agents(); mgr.agents()

    t1.post("island", "PROPOSE to=T2 give=iron:0.4 want=salt:0.3")
    t1.whisper(mgr.agent_id, "PRODUCE salt=0.70 iron=0.30")

    bodies = [m["body"] for m in live.snapshot(mgr, "island")["messages"]]

    assert any("PROPOSE" in b for b in bodies), "the public half is there"
    assert not any("PRODUCE" in b for b in bodies), "the sealed half never was"


def test_it_is_replaced_atomically(hub, tmp_path):
    """A spectator polls it every few seconds; nobody reads half a board."""
    c = _client(hub, "mgr", generate_key())
    c.register(name="mgr", kind="local", branch="m", task="")
    c.post("island", "first")
    path = tmp_path / "views" / "g1.json"

    live.write(c, "island", path)
    assert json.loads(path.read_text())["messages"][0]["body"] == "first"

    c.post("island", "second")
    live.write(c, "island", path)
    saved = json.loads(path.read_text())
    assert [m["body"] for m in saved["messages"]] == ["first", "second"]
    assert not list(path.parent.glob("*.tmp")), "no leftover half-written file"


# --- the handover at the last bell -------------------------------------------
#
# A live game shows no score and cannot: utility needs a taste. So the moment a
# spectator most wants an answer is the moment the live file could least give
# one, and the answer sat in `--out`, which is not served. `live.finish` is the
# handover: at the last bell the seed is disclosed anyway, so the two files
# that disclose it are copied beside the live one and the live file says so.

def _live_file(tmp_path, body="first"):
    path = tmp_path / "views" / "g1.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"channel": "island",
                                "messages": [{"seq": 1, "body": body}]}) + "\n")
    return path


def test_the_finished_game_points_at_its_own_reveal_and_board(tmp_path):
    """What a page polling the board needs to find its ending: the seed, and
    the replay of the round it just watched, beside the file it already has."""
    path = _live_file(tmp_path)
    board = tmp_path / "out" / "board-island-game-g1.json"
    board.parent.mkdir()
    board.write_text('{"messages": []}')
    reveal = tmp_path / "out" / "reveal-island-game-g1.json"
    reveal.write_text('{"seed": 7}')

    named = live.finish(path, board=board, reveal=reveal)

    saved = json.loads(path.read_text())
    assert saved["finished"] == named == {"board": "board-g1.json",
                                          "reveal": "reveal-g1.json"}
    # The board it was already showing is still there: the handover adds an
    # ending, it does not replace the game with one.
    assert saved["messages"][0]["body"] == "first"
    beside = path.parent
    assert json.loads((beside / "reveal-g1.json").read_text())["seed"] == 7
    assert (beside / "board-g1.json").read_text() == '{"messages": []}'
    assert not list(beside.glob("*.tmp"))


def test_nothing_is_pointed_at_before_it_is_there(tmp_path, monkeypatch):
    """A poll landing mid-handover must see a game still running, never a
    pointer at a file that does not exist yet -- so the copies go first."""
    path = _live_file(tmp_path)
    board = tmp_path / "board.json"
    board.write_text("{}")
    reveal = tmp_path / "reveal.json"
    reveal.write_text("{}")

    seen = []
    real = Path.replace

    def watched(self, target):
        seen.append(str(target.name))
        return real(self, target)

    monkeypatch.setattr(Path, "replace", watched)
    live.finish(path, board=board, reveal=reveal)

    assert seen == ["board-g1.json", "reveal-g1.json", "g1.json"], (
        "the live file was updated before what it points at existed")
