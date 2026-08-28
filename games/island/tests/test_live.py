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
    """Nothing is ever pointed at before it is there.

    A poll landing mid-handover must see a game still running rather than a
    pointer at a file that is not written yet -- so the copies go first, the
    live file that names them second, and the archive's index, which is what a
    page believes about what is watchable, only once the game genuinely is.
    """
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

    assert seen == ["board-g1.json", "reveal-g1.json", "g1.json", "index.json"], (
        "something was pointed at before it existed: the copies come first, "
        "then the live file that names them, then the index that lists the game")


def test_the_official_score_travels_with_the_handover(tmp_path):
    """A spectator gets the ledger's answer, not the page's own arithmetic.

    `live.finish` never computes a score: it carries the one
    `viewer/scores.py:standing` read back out of the ledger the game was just
    written into. Two scoring surfaces would be two official scores for one
    game.
    """
    path = _live_file(tmp_path)
    board = tmp_path / "board.json"
    board.write_text("{}")
    reveal = tmp_path / "reveal.json"
    reveal.write_text("{}")
    told = {"capture": 0.41, "eff_round": 0.72, "floor": 0.60, "ranked": True,
            "place": 2, "of": 7, "best": 0.63,
            "label": "2 traders · 4 goods · 3 episodes",
            "traders": [{"slot": "T1", "ratio": 1.2, "place": 3, "of": 14}]}

    live.finish(path, board=board, reveal=reveal, standing=told)

    saved = json.loads(path.read_text())["finished"]
    assert saved["standing"] == told
    assert saved["reveal"] == "reveal-g1.json", "the replay still points home"


def test_a_game_with_no_standing_still_hands_over(tmp_path):
    """An older runner, or a run with no ledger, ends as it always did rather
    than not ending at all."""
    path = _live_file(tmp_path)
    for name in ("board.json", "reveal.json"):
        (tmp_path / name).write_text("{}")

    live.finish(path, board=tmp_path / "board.json",
                reveal=tmp_path / "reveal.json")

    assert "standing" not in json.loads(path.read_text())["finished"]


# --- the live directory is the archive ----------------------------------------
#
# Nothing under --live is ever pruned, so the file a spectator polled while the
# game ran is the file that keeps its replay afterwards. What was missing
# between "a game ended" and "a recording anybody can watch" was a listing.

def test_a_finished_game_is_listed_as_a_recording(tmp_path):
    path = _live_file(tmp_path)
    board = tmp_path / "board.json"
    board.write_text('{"messages": []}')
    reveal = tmp_path / "reveal.json"
    reveal.write_text('{"seed": 7}')

    live.finish(path, board=board, reveal=reveal,
                standing={"capture": 0.4, "ranked": True},
                facets={"agents": 2, "arm": "sealed"})

    index = json.loads((path.parent / live.INDEX).read_text())
    assert [g["label"] for g in index["games"]] == ["g1"]
    row = index["games"][0]
    # Named relative to the index, so a page reaching the archive from another
    # origin resolves them against the URL it already has.
    assert row["board"] == "board-g1.json" and row["reveal"] == "reveal-g1.json"
    assert row["live"] == "g1.json"
    assert row["standing"]["capture"] == 0.4 and row["facets"]["agents"] == 2
    assert row["finished_at"].endswith("+00:00")


def test_re_finishing_a_game_replaces_its_row_rather_than_doubling_it(tmp_path):
    path = _live_file(tmp_path)
    for name in ("board.json", "reveal.json"):
        (tmp_path / name).write_text("{}")
    args = {"board": tmp_path / "board.json", "reveal": tmp_path / "reveal.json"}

    live.finish(path, **args)
    live.finish(path, **args, standing={"capture": 0.9})

    games = json.loads((path.parent / live.INDEX).read_text())["games"]
    assert len(games) == 1, "the same game was listed twice"
    assert games[0]["standing"] == {"capture": 0.9}, "the later reading lost"


def test_many_games_list_newest_first(tmp_path):
    """With everything kept forever, the one somebody wants is the last one."""
    beside = tmp_path / "views"
    for name in ("board.json", "reveal.json"):
        (tmp_path / name).write_text("{}")
    for label in ("g1", "g2", "g3"):
        path = beside / f"{label}.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps({"channel": "island", "messages": []}))
        live.finish(path, board=tmp_path / "board.json",
                    reveal=tmp_path / "reveal.json")

    games = json.loads((beside / live.INDEX).read_text())["games"]
    assert len(games) == 3
    stamps = [g["finished_at"] for g in games]
    assert stamps == sorted(stamps, reverse=True)


def test_an_evicted_game_keeps_a_row_that_says_it_was_played(tmp_path):
    """A game evicted by a later, better game did nothing to deserve it, and a
    link that fails into silence cannot say so. The files go; the row stays."""
    path = _live_file(tmp_path)
    for name in ("board.json", "reveal.json"):
        (tmp_path / name).write_text("{}")
    live.finish(path, board=tmp_path / "board.json", reveal=tmp_path / "reveal.json",
                facets={"agents": 2})
    beside = path.parent
    assert (beside / "board-g1.json").exists()

    gone = live.forget(beside, "g1")

    assert sorted(p.name for p in gone) == ["board-g1.json", "g1.json",
                                            "reveal-g1.json"]
    row = json.loads((beside / live.INDEX).read_text())["games"][0]
    assert row["label"] == "g1" and row["kept"] is False
    assert row["dropped_at"].endswith("+00:00")
    # What it was is still on the row; what it pointed at is not, because
    # pointing at a deleted file is the failure this exists to prevent.
    assert row["facets"] == {"agents": 2} and row["finished_at"]
    assert "board" not in row and "reveal" not in row and "live" not in row


def test_forgetting_twice_is_not_a_second_eviction(tmp_path):
    path = _live_file(tmp_path)
    for name in ("board.json", "reveal.json"):
        (tmp_path / name).write_text("{}")
    live.finish(path, board=tmp_path / "board.json", reveal=tmp_path / "reveal.json")

    live.forget(path.parent, "g1")
    again = live.forget(path.parent, "g1")

    assert again == [], "a game already let go was let go a second time"
    rows = json.loads((path.parent / live.INDEX).read_text())["games"]
    assert len(rows) == 1 and rows[0]["kept"] is False
