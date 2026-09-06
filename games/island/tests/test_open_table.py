"""The format the door hands out is the format the headline is set on.

Two files have to agree about one thing: `lobby_page.OPEN_DEFAULTS`, which is
what a reader's copy button puts in front of their agent, and
`scores.OPEN_TABLE`, which is the level the front door quotes a score to beat
from. If they drift, the page tells a stranger to play one format and then
measures them against a record set on another -- which is the exact defect the
open table exists to fix, reintroduced one level down.

The check is deliberately made through `open_line()` rather than by comparing
the two constants directly. `OPEN_DEFAULTS` is a dict of five fields in the
lobby's vocabulary and `OPEN_TABLE` is a four-tuple in the scoreboard's; what
has to match is not their spelling but the level a reader actually lands on
when they copy the default line, so the test parses that line the way the
lobby does and takes the level off it the way the ledger does.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "experiments" / "005-deliberation-protocol" / "viewer"))

import scores  # noqa: E402

from games.island import protocol  # noqa: E402
from games.island.lobby_page import OPEN_DEFAULTS, open_line  # noqa: E402


def test_the_default_line_lands_on_the_open_table():
    """Copy the button's line, play it, and you are on the quoted level."""
    opened = protocol.parse(open_line())
    assert opened is not None, "the page's own default OPEN line does not parse"
    level = (opened.traders, opened.goods, opened.episodes, opened.seconds)
    assert level == scores.OPEN_TABLE, (
        f"the lobby hands out {level} and the scoreboard quotes "
        f"{scores.OPEN_TABLE}; a reader would be measured against a format "
        f"they were not given"
    )


def test_the_open_table_is_a_level_the_lobby_will_accept():
    """Named, not merely written down: every field inside its own bound.

    A constant that names a format the lobby refuses would leave the front door
    quoting a score nobody can go after -- the same failure as before, arrived
    at from the other side.
    """
    traders, goods, episodes, seconds = scores.OPEN_TABLE
    assert protocol.TRADERS_MIN <= traders <= protocol.TRADERS_MAX
    assert 2 <= goods <= protocol.GOODS_MAX
    assert seconds in protocol.EPISODE_SECONDS_ALLOWED
    assert episodes >= 1
    assert OPEN_DEFAULTS["rounds"] == 1, "a table plays exactly one round"


def test_an_unheld_open_table_says_so_rather_than_borrowing_a_record():
    """The empty state is a fact, and must not fall back to another format.

    This is the whole reason `open_table` is separate from `best_ever`. On the
    day the door opened there were 238 ranked games and none of them on this
    level; a board that filled the gap with the nearest other format would have
    gone on quoting a record nobody arriving could play against.
    """
    board = scores.open_table([], [])
    assert board["held"] is None
    assert board["ranked"] == 0
    assert board["label"] == scores.level_label(scores.OPEN_TABLE)


def test_a_game_on_another_level_never_holds_the_open_table():
    other = list(scores.OPEN_TABLE[:3]) + [scores.OPEN_TABLE[3] * 2]
    game = {"level": other, "capture": 1.0, "game_id": "x"}
    board = scores.open_table([game], [game])
    assert board["held"] is None
    assert board["attempts"] == 0


def test_an_unscored_game_belongs_to_no_level():
    """`level` is None on a game that could not be scored, and that is kept.

    Nothing that went wrong is dropped from a denominator, so such a game is in
    `played` -- and it belongs to no level, this one included. It used to raise
    `TypeError` here rather than being counted as nothing.
    """
    board = scores.open_table([], [{"level": None, "game_id": "y"}])
    assert board["attempts"] == 0
