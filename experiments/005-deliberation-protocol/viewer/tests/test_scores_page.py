"""The scoreboard's open-table card, driven in a browser.

**A test that reads rendered markup cannot see a script that never ran**
(`CLAUDE.md`). The card this checks is written entirely by `openTable()` from
data it fetches, so a fragment assertion against `scores.html` would pass on a
page whose script threw on the first line and left the card empty. So the page
is served, loaded and read back out of the live DOM.

Two states matter and both are asserted, because they are the two a visitor can
arrive at and the empty one is the state the board was actually in on the day
the door opened:

- **unheld** -- no ranked game on the open table yet. The card must say so on
  its own terms and must *not* borrow the record from another format, which is
  the failure the whole open table exists to fix;
- **held** -- somebody has one. The card shows their score and who holds it.

Like every browser check here it takes `ISLAND_REQUIRE_BROWSER`, because a skip
and a pass are the same green tick.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

WEB = pathlib.Path(__file__).resolve().parents[1] / "web"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no scoreboard at all")
    pytest.skip(why)


def _site(tmp_path: pathlib.Path, board: dict) -> pathlib.Path:
    """The page, its stylesheet, and the one endpoint it fetches."""
    for name in ("scores.html", "tokens.css"):
        shutil.copy(WEB / name, tmp_path / name)
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "scores").write_text(json.dumps(board))
    return tmp_path


def _serve(root: pathlib.Path):
    """A real origin. `fetch("api/scores")` cannot run from a `file://` page."""
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/scores.html"


def _text(root: pathlib.Path, selector: str) -> str:
    """Whatever the page put in `selector`, after its script has run."""
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    httpd, url = _serve(root)
    try:
        with play.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(
                    executable_path=str(chrome) if chrome else None)
            except Exception as exc:                       # noqa: BLE001
                _missing(f"no chromium to drive a page with: {exc!r}")
            tab = browser.new_page()
            errors: list[str] = []
            tab.on("pageerror", lambda e: errors.append(str(e)))
            tab.goto(url)
            tab.wait_for_selector(selector, timeout=10_000)
            out = tab.inner_text(selector)
            browser.close()
    finally:
        httpd.shutdown()
    assert not errors, f"the page threw: {errors}"
    return out


def _card(root: pathlib.Path) -> str:
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    httpd, url = _serve(root)
    try:
        with play.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(
                    executable_path=str(chrome) if chrome else None)
            except Exception as exc:                       # noqa: BLE001
                _missing(f"no chromium to drive a page with: {exc!r}")
            tab = browser.new_page()
            errors: list[str] = []
            tab.on("pageerror", lambda e: errors.append(str(e)))
            tab.goto(url)
            tab.wait_for_selector("#open-table .score", timeout=10_000)
            text = tab.inner_text("#open-table")
            browser.close()
    finally:
        httpd.shutdown()
    assert not errors, f"the page threw: {errors}"
    return text


def _board(**over) -> dict:
    """A board shaped like the real one, with only what this card reads."""
    empty = {"islands": [], "games": [], "traders": [], "best_ever": None,
             "best_player": None, "recent": [],
             "totals": {"games": 0, "ranked": 0, "levels": 0, "players": 0,
                        "rounds": 0, "not_ranked": {}, "held_out": {},
                        "multi_round_games": 0, "unfinished_games": 0,
                        "attendance_unrecorded": 0}}
    week = dict(empty, since=None, days=7, open_table=None)
    return dict(empty, week=week, **over)


def test_an_unheld_open_table_says_so_and_borrows_nothing(tmp_path):
    """The state the board was actually in when the door opened.

    238 ranked games sat on the boards, none of them on a format a stranger
    could open. The card must read as unheld rather than reaching for the
    biggest number in the book.
    """
    other = {"game_id": "old", "level": [4, 4, 5, None], "capture": 0.9954,
             "by": ["claude-haiku-4-5-20251001"], "of": 126, "first_of": 126,
             "of_all": 238, "rounds": 1, "played_at": "2026-08-23T17:40:00+00:00",
             "played_from": "run_stamp", "recorded_at": "2026-08-28T11:00:56+00:00",
             "agents": 4, "goods": 4, "episodes": 5, "seconds": None}
    text = _card(_site(tmp_path, _board(
        best_ever=other, games=[other],
        open_table={"level": [2, 5, 4, 60],
                    "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
                    "held": None, "top": [], "ranked": 0, "attempts": 0,
                    "unranked": []})))
    assert "unheld" in text
    assert "Nobody has played a ranked game on the open table yet" in text
    # The other format's record is on the page, but not in this card.
    assert "99.5" not in text and "claude-haiku" not in text


def test_a_held_open_table_shows_the_score_and_who_holds_it(tmp_path):
    text = _card(_site(tmp_path, _board(
        open_table={"level": [2, 5, 4, 60],
                    "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
                    "held": {"game_id": "g", "level": [2, 5, 4, 60],
                             "capture": 0.873, "by": ["shell-goblin-v3", "scout-v2"],
                             "of": 3, "rounds": 1,
                             "played_at": "2026-09-06T10:00:00+00:00",
                             "played_from": "board",
                             "recorded_at": "2026-09-06T10:01:00+00:00"},
                    "top": [], "ranked": 3, "attempts": 4, "unranked": ["practice"]})))
    # `pct` prints a whole percent with a sign -- the page's own convention,
    # which reserves a decimal for the 99.5-100 band so a game that left
    # something on the table cannot round to the number that says it did not.
    assert "+87%" in text
    assert "shell-goblin-v3" in text
    assert "3 ranked games" in text
    # The attempt that could not be ranked is still in the denominator.
    assert "4 attempts" in text


def test_the_card_names_the_format_the_door_hands_out(tmp_path):
    """The label is the contract: play this and you are on this board."""
    text = _card(_site(tmp_path, _board(
        open_table={"level": [2, 5, 4, 60],
                    "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
                    "held": None, "top": [], "ranked": 0, "attempts": 0,
                    "unranked": []})))
    assert "2 traders · 5 goods · 4 episodes · 60s episodes" in text


# ---- what a seat said about itself ----------------------------------------

def _game(**over):
    base = {"game_id": "g", "level": [2, 5, 4, 60],
            "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
            "agents": 2, "goods": 5, "episodes": 4, "seconds": 60,
            "capture": 0.5, "eff_round": 0.8, "floor": 0.6, "place": 1, "of": 1,
            "by": ["shell-goblin-v3", "scout-v2"], "told": {}, "rounds": 1,
            "seeds": [1], "workspace": "w", "arm": "sealed",
            "played_at": "2026-09-06T10:00:00+00:00", "played_from": "board",
            "recorded_at": "2026-09-06T10:01:00+00:00"}
    return {**base, **over}


def test_the_leaderboard_shows_what_a_seat_said_it_was_running(tmp_path):
    """A label recorded and never displayed is a label not recorded.

    The whole reason `harness=` exists is so a public board can answer "did
    fifty lines of Python ever beat a frontier model". That answer has to be
    visible on the row.
    """
    game = _game(told={"T1": {"harness": "bash", "by": "gald33"},
                       "T2": {"harness": "claude-code"}})
    text = _text(_site(tmp_path, _board(games=[game])), "#games")
    assert "bash" in text and "claude-code" in text
    assert "brought by gald33" in text


def test_a_game_that_declared_nothing_shows_nothing(tmp_path):
    """Absent is not unknown. Most rows in this ledger predate the field."""
    text = _text(_site(tmp_path, _board(games=[_game()])), "#games")
    assert "shell-goblin-v3" in text
    assert "brought by" not in text


def test_one_harness_across_both_seats_is_said_once(tmp_path):
    """The same reason `roster` says a repeated name once with a count.

    Two seats on one harness read as two harnesses until you look.
    """
    game = _game(told={"T1": {"harness": "python"}, "T2": {"harness": "python"}})
    text = _text(_site(tmp_path, _board(games=[game])), "#games")
    assert text.count("python") == 1
