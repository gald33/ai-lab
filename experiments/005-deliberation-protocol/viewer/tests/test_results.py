"""The per-game result pages: what somebody actually sends.

These are **static files with their Open Graph tags baked in**, and that is the
property most of these tests are about. A crawler does not run scripts, so a
result page that computed itself in the browser would render a correct card for
a human and an empty one for every link preview -- which is the audience a
result URL exists for. So the tags have to be *in the file*, filled in, per
game.

The second property is that a page exists for every game and stops existing for
none. Boards get pruned (`scores.keepers()` keeps the latest 100 and the best
1000); ledger rows do not. Building from the row rather than the board is what
keeps an old game's result reachable, saying its replay is gone, instead of
404ing.
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import results  # noqa: E402
import scores  # noqa: E402


def _row(**over):
    base = {"v": 2, "round_id": "r1", "game": {"id": "g1", "rounds": 1},
            "played_at": "2026-09-06T10:00:00+00:00", "played_from": "board",
            "recorded_at": "2026-09-06T10:01:00+00:00", "workspace": "w_open-g1",
            "arm": "sealed", "npcs": {}, "hands": {}, "draw": "commit-reveal",
            "island": {"seed": 5, "agents": 2, "goods": 5, "episodes": 4,
                       "seconds": 60},
            "players": [{"slot": "T1", "id": "shell-goblin-v3", "model": "entrants",
                         "harness": "bash", "by": "gald33"},
                        {"slot": "T2", "id": "scout-v2", "model": "entrants",
                         "harness": "claude-code"}],
            "eff_round": 0.9, "eff_round_upper": 1.0, "autarky_floor": 0.6,
            "eff_episode": [0.9] * 4,
            "ratios": {"T1": 1.4, "T2": 1.2},
            "utility_total": {"T1": 1.0, "T2": 1.0},
            "autarky_utility": {"T1": 0.7, "T2": 0.8},
            "zero_episodes": {"T1": 0, "T2": 0},
            "trajectory": [[0.9, 0.9]] * 4,
            "traffic": {"settled": 11, "refused": 0, "talk": 3},
            "company": 0, "intruders": [], "status": "complete",
            "attendance": "recorded", "acknowledged": [], "spoke": [],
            "source": {"result": "x.json", "board": "board-w_open-g1.json"}}
    base.update(over)
    return base


def _build(tmp_path, rows, listing=None):
    out = tmp_path / "g"
    results.build(out, rows=rows, listing=listing or [])
    return out


def _only(out: pathlib.Path) -> str:
    files = sorted(out.glob("*.html"))
    assert len(files) == 1, f"expected one page, got {[f.name for f in files]}"
    return files[0].read_text()


# ---- what a crawler reads -------------------------------------------------

def test_the_card_is_in_the_file_and_filled_in(tmp_path):
    """Baked, not fetched. This is the whole reason these are static."""
    text = _only(_build(tmp_path, [_row()]))
    tags = dict(re.findall(r'property="(og:[^"]+)" content="([^"]*)"', text))
    assert tags["og:type"] == "article"
    assert "shell-goblin-v3" in tags["og:title"]
    assert "%" in tags["og:title"]
    assert "trades settled" in tags["og:description"]
    assert tags["og:image"].endswith("/card.png")
    assert tags["og:url"].endswith(".html")
    assert 'name="twitter:card" content="summary_large_image"' in text


def test_the_canonical_url_is_the_page_s_own(tmp_path):
    out = _build(tmp_path, [_row()])
    name = sorted(out.glob("*.html"))[0].stem
    text = (out / f"{name}.html").read_text()
    assert f'href="{results.SITE}/{results.PREFIX}/{name}.html"' in text


def test_a_name_with_markup_in_it_cannot_reach_the_page(tmp_path):
    """A trader name is bounded, but this file writes it into HTML and a tag.

    The protocol refuses anything but letters, digits, dash, underscore and
    dot -- so this can never happen through the door. It is asserted anyway,
    because the page builder does not import the protocol and would have no way
    of knowing if that ever changed.
    """
    row = _row(players=[{"slot": "T1", "id": '<img src=x onerror=alert(1)>',
                         "model": "entrants"},
                        {"slot": "T2", "id": "scout-v2", "model": "entrants"}])
    text = _only(_build(tmp_path, [row]))
    assert "<img src=x" not in text
    assert html.escape("<img src=x onerror=alert(1)>") in text


# ---- what a person reads --------------------------------------------------

def test_the_page_says_the_score_the_format_and_the_trades(tmp_path):
    text = _only(_build(tmp_path, [_row()]))
    assert "shell-goblin-v3" in text and "scout-v2" in text
    assert ">11<" in text                       # trades settled
    assert "4</b><span>days" in text.replace("\n", "")
    # The game's own voice: an episode is a day to whoever is looking.
    assert "5 goods" in text


def test_the_page_shows_what_the_seats_said_they_were_running(tmp_path):
    text = _only(_build(tmp_path, [_row()]))
    assert "bash" in text and "claude-code" in text
    assert "brought by gald33" in text


def test_a_game_with_no_labels_says_nothing_about_them(tmp_path):
    row = _row(players=[{"slot": "T1", "id": "a", "model": "entrants"},
                        {"slot": "T2", "id": "b", "model": "entrants"}])
    text = _only(_build(tmp_path, [row]))
    assert "brought by" not in text


# ---- the two states that are easy to get wrong ----------------------------

def test_a_pruned_replay_says_so_rather_than_linking_nowhere(tmp_path):
    """An empty listing is a game whose board files are gone. Normal, and said.

    A dead link is silent -- it only shows up if somebody clicks.
    """
    text = _only(_build(tmp_path, [_row()], listing=[]))
    assert "have been pruned" in text
    assert "Watch the replay" not in text


def test_a_kept_replay_is_linked_with_its_sidecar(tmp_path):
    listing = [{"label": "w_open-g1", "board": "replays/board-w_open-g1.json",
                "reveal": "replays/reveal-w_open-g1.json", "at": 0, "facets": {}}]
    text = _only(_build(tmp_path, [_row()], listing=listing))
    assert "Watch the replay" in text
    assert "board=replays/board-w_open-g1.json" in text
    assert "reveal=replays/reveal-w_open-g1.json" in text


def test_an_unranked_game_still_gets_a_page_and_it_says_which(tmp_path):
    """Nothing that went wrong is dropped -- from a denominator or from view.

    A practice game whose page calls it practice is honest. The same game with
    no page is a quiet edit.
    """
    text = _only(_build(tmp_path, [_row(arm="practice")]))
    assert "Not ranked" in text
    assert "practice" in text
    # And it must not claim a place, because it has none.
    assert "of this format" not in text
    assert "#None" not in text and "None" not in text


def test_a_ranked_game_carries_its_place_on_its_own_format(tmp_path):
    text = _only(_build(tmp_path, [_row()]))
    assert "#1 of 1 on this format" in text


def test_a_game_that_could_not_be_scored_gets_no_page_rather_than_a_blank_one(tmp_path):
    """It has no format to name and no score to print. Its ledger row stands.

    The one case where silence is the honest answer, and it is asserted so that
    a later change cannot start emitting an empty page instead.
    """
    # The shape `scores.unscored()` writes: no agents and no goods, so
    # `games()` derives no level for it. One row in the real ledger looks like
    # this, which is why the empty-page branch is reachable at all.
    out = _build(tmp_path, [_row(
        island={"seed": 5, "agents": None, "goods": None, "episodes": 0,
                "seconds": None},
        players=[], trajectory=[], eff_round=None, autarky_floor=None,
        ratios={}, status="unscored")])
    assert not list(out.glob("*.html"))


def test_every_game_in_the_real_ledger_gets_a_page(tmp_path):
    """The record, end to end. 300-odd games, none of which may throw."""
    rows = scores.load()
    assert rows, "the ledger is empty; this test is checking nothing"
    out = _build(tmp_path, rows)
    pages = list(out.glob("*.html"))
    scorable = [g for g in scores.games(rows) if g.get("level")]
    assert len(pages) == len(scorable)
    for page in pages:
        text = page.read_text()
        assert "og:title" in text
        # The failure this catches is an f-string that printed a None.
        assert "None" not in text, f"{page.name} leaked a None"


@pytest.mark.parametrize("capture,shown", [
    (0.873, "+87%"), (0.9954, "+99.5%"), (1.0, "+100%"), (-0.4, "−40%"),
])
def test_the_percent_is_the_scoreboard_s_percent(capture, shown):
    """Including the 99.5 rule, which exists so a game that left something on
    the table cannot print the number that says it did not."""
    assert results.pct(capture) == shown
