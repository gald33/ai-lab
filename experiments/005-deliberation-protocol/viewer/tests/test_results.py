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
import os
import pathlib
import re
import sys
import threading
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
ROOT = pathlib.Path(__file__).resolve().parents[4]
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
    assert f'href="{results.PAGES}/{results.PREFIX}/{name}.html"' in text


def test_the_declared_url_is_where_the_workflow_puts_the_page():
    """The 404 every result page had declared about itself since it existed.

    These pages are staged to `$RUNNER_TEMP/site/island/g` and said they lived
    at `<SITE>/g/`. Both true, neither checked against the other:

        .../ai-lab/g/<id>.html         404
        .../ai-lab/island/g/<id>.html  200

    It survived a test because that test restated the constant --
    `f'href="{results.SITE}/{results.PREFIX}/..."'` is a tautology, green for
    any value of `SITE`. Reading it off the workflow is the only version of
    this check that can fail, so this parses the staging path out of
    `pages.yml` and requires the declared URL to be the same place.

    Found by curling the live host after #239 merged, twenty minutes after
    that PR shipped a Copy-link button which had been putting the 404 on
    people's clipboards -- the honest version of "a test cannot load the live
    host, so it checks the workflow" is that somebody still has to look.
    """
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
    staged = re.search(r'results\.py "\$RUNNER_TEMP/site/(\S+?)"', workflow)
    assert staged, "pages.yml no longer stages the result pages"

    where = staged.group(1)                       # e.g. "island/g"
    assert where.endswith(f"/{results.PREFIX}"), \
        f"the workflow stages into {where!r}, which does not end in PREFIX"
    assert f"{results.PAGES}/{results.PREFIX}" == f"{results.SITE}/{where}", (
        f"pages declare {results.PAGES}/{results.PREFIX} and deploy to "
        f"{results.SITE}/{where} -- one of them is a 404")


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


# ---- the image those tags point at, which nothing used to put anywhere ------

def test_the_card_the_pages_declare_is_staged_here():
    """The 404 of 2026-09-08, as a test.

    Every page this repo publishes to Pages -- the viewer, the scoreboard and
    one of these per game -- declares `og:image` at `<SITE>/card.png`. Nothing
    in `pages.yml` copied a file there, so `curl` on the live host answered
    404 and every one of those previews rendered without an image, for as long
    as the pages had existed.

    `test_the_card_is_in_the_file_and_filled_in` above was green throughout:
    it asserts the tag *string*. That is the shape of failure this repo keeps
    finding -- an assertion about a page nobody loaded -- and the fix is not a
    better string check but a check on the thing the string promises.

    This reads the workflow rather than a built site because the staging is
    what CI does and there is no built site here to look at. It is a weaker
    check than loading the page, and it is the strongest one available from a
    test run: the live URL is verified by hand after a deploy, which is how
    the 404 was found.
    """
    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
    source = ROOT / "games" / "island" / "lobby-web" / "card.png"

    assert source.is_file(), \
        f"{source} is the only card in the repo and it is missing"
    assert "card.png" in workflow, (
        "pages.yml stages no card.png, so every og:image on the Pages origin "
        "is a 404 and every posted link previews with no image")

    staged = re.search(r'run: cp \S*card\.png "\$RUNNER_TEMP/site/"', workflow)
    assert staged, ("pages.yml mentions card.png but does not copy it to the "
                    "site root, which is where og:image names it")


def test_every_pages_hosted_card_names_the_pages_origin(tmp_path):
    """The other half of the same defect, from the other direction.

    A tag naming the *wrong* host is how the front door broke (`games/
    island.md`, "And it was built at the wrong address"). These pages are on
    Pages, so their card must be too -- the main door's own card is a separate
    file on a separate host and is checked by `test_front_door.py`.
    """
    web = ROOT / "experiments" / "005-deliberation-protocol" / "viewer" / "web"
    pages = [_only(_build(tmp_path, [_row()]))]
    pages += [(web / name).read_text() for name in ("index.html", "scores.html")]
    for text in pages:
        for prop in ("og:image", "twitter:image"):
            url = re.search(rf'"{prop}" content="([^"]+)"', text).group(1)
            assert url == f"{results.SITE}/card.png", \
                f"{prop} names {url}, which is not the card staged to this origin"


# ---- something a person can actually send ----------------------------------

def test_the_page_offers_both_ways_to_send_it(tmp_path):
    """A result page exists to be sent, and until now said so and offered
    nothing to send it with."""
    text = _only(_build(tmp_path, [_row()]))
    url = re.search(r'"og:url" content="([^"]+)"', text).group(1)

    assert f'data-url="{url}"' in text, \
        "the copy button must hand over the canonical URL, not location.href"
    assert ">Copy link<" in text
    assert ">Post it<" in text


def test_the_post_text_is_the_same_sentence_as_the_card(tmp_path):
    """One phrasing. A post whose text disagrees with the preview underneath
    it is a worse post than one with no text at all."""
    text = _only(_build(tmp_path, [_row()]))
    title = html.unescape(
        re.search(r'"og:title" content="([^"]+)"', text).group(1))
    intent = html.unescape(
        re.search(r'href="(https://x\.com/intent/[^"]+)"', text).group(1))

    query = urllib.parse.parse_qs(urllib.parse.urlparse(intent).query)
    assert query["text"] == [title]
    assert query["url"] == [
        re.search(r'"og:url" content="([^"]+)"', text).group(1)]


def test_a_name_with_markup_in_it_cannot_reach_the_share_row(tmp_path):
    """The escaping test above, extended to the two attributes this adds.

    Both carry a URL built from the game id and the trader's name, and both
    sit in `href`/`data-` attributes where an unescaped quote would end the
    attribute and start whatever came next.
    """
    text = _only(_build(tmp_path, [_row(players=[
        {"slot": "T1", "id": '"><script>alert(1)</script>', "model": "entrants"},
        {"slot": "T2", "id": "b", "model": "entrants"}])]))
    assert "<script>alert(1)</script>" not in text
    assert "%3Cscript%3E" in text or "&lt;script&gt;" in text


# ---- and the half of it a fragment assertion cannot see ---------------------
#
# `CLAUDE.md`: "anything a page *does* -- a countdown that ticks, a control
# that keeps its value, a button that copies -- is asserted by loading the page
# in a real browser and watching it happen." It names this button. Until this
# change these pages did nothing at all, which is why the CI step that runs
# them said no browser was needed; that comment moved with this code.

def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no result page at all")
    pytest.skip(why)


def _clicks_copy(root: pathlib.Path, name: str) -> tuple[str, str]:
    """Serve the built page, click Copy, and read the clipboard back.

    Served over http on loopback rather than opened as `file://`, because
    `window.isSecureContext` is false for a file URL and the page would take
    its fallback path -- which would make this a test of the fallback while
    reading as a test of the copy.
    """
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)

    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}/"
    try:
        with play.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(
                    executable_path=str(chrome) if chrome else None)
            except Exception as exc:                       # noqa: BLE001
                _missing(f"no chromium to drive a page with: {exc!r}")
            context = browser.new_context()
            context.grant_permissions(["clipboard-read", "clipboard-write"])
            tab = context.new_page()
            errors: list[str] = []
            tab.on("pageerror", lambda e: errors.append(str(e)))
            tab.goto(base + name)
            tab.click("#copy")
            tab.wait_for_function(
                "document.getElementById('copy').textContent !== 'Copy link'")
            label = tab.inner_text("#copy")
            pasted = tab.evaluate("navigator.clipboard.readText()")
            browser.close()
    finally:
        httpd.shutdown()
    assert not errors, f"the page threw: {errors}"
    return pasted, label


def test_the_copy_button_copies_the_canonical_url(tmp_path):
    """Watched happening, not read off the markup.

    The lobby's countdowns were the lesson: every fragment assertion passed
    while the script that drove them had never run, because it was emitted
    above the rows it selected. Order is invisible to a text check.
    """
    out = _build(tmp_path, [_row()])
    page = sorted(out.glob("*.html"))[0]
    want = re.search(r'"og:url" content="([^"]+)"', page.read_text()).group(1)

    pasted, label = _clicks_copy(out, page.name)
    assert pasted == want, \
        f"the button put {pasted!r} on the clipboard, not the canonical URL"
    assert label == "Copied"
