"""The front door, driven in a browser.

`island.lucille-ai.com` is the address people are handed and the address they
paste. Until 2026-09-07 it served `lobby-web/index.html` -- seven lines, no
Open Graph tags, no description, no premise -- while the landing page with the
card sat on the Pages origin, which Gal calls the legacy address. So a posted
link to the main door rendered as a bare URL, and a visitor who had never heard
of the game arrived at a table list. The landing page is here now and the lobby
is at `/lobby`.

Two things are checked, and only one of them is the page.

**What a crawler sees.** Open Graph is read by consumers that do not run
scripts, so every tag has to be in the file, has to name *this* host, and the
image it points at has to exist at that path in the deployed directory. That
last clause is the one that would have caught the defect this file exists for:
the tags were correct all along, on a different host.

**What the page does.** The score is written by a `fetch`, so a fragment
assertion would pass on a page whose script never ran -- the lobby's frozen
countdown, from the other side. The fetch is cross-origin now (the scoreboard
is on Pages, this is not), and it is intercepted rather than pointed somewhere
local: what these tests exercise is the exact URL string that deploys. A page
whose data source is swapped out under test is a page whose real data source
nothing checked.

`ISLAND_REQUIRE_BROWSER` turns each skip into a failure, for the reason every
browser check in this repo takes that flag: a skip and a pass are the same tick.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import struct
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

WEB = pathlib.Path(__file__).resolve().parent.parent / "lobby-web"
VIEWER = (pathlib.Path(__file__).resolve().parents[3] / "experiments"
          / "005-deliberation-protocol" / "viewer" / "web")

#: The board the page reads, exactly as `landing.js` writes it.
SCORES = "https://gald33.github.io/ai-lab/island/api/scores"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no front door at all")
    pytest.skip(why)


def _serve(root: pathlib.Path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def _board(open_table):
    return {"boards": {"open_table": open_table}}


def _visit(board, path: str = ""):
    """Load the deployed directory itself, with the board fetch intercepted.

    The directory is served as-is -- no fixture copy -- so what is driven is
    the file Vercel publishes. `board` of `None` means the fetch fails, which
    is the state one network hiccup away at any time.
    """
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    httpd, base = _serve(WEB)
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
            if board is None:
                tab.route(SCORES, lambda route: route.abort())
            else:
                tab.route(SCORES, lambda route: route.fulfill(
                    status=200, content_type="application/json",
                    body=json.dumps(board)))
            tab.goto(base + path)
            tab.wait_for_load_state("networkidle")
            text, where = tab.inner_text("body"), tab.url
            browser.close()
    finally:
        httpd.shutdown()
    assert not errors, f"the page threw: {errors}"
    return text, where[len(base):]


# ---- the page a visitor lands on ------------------------------------------

def test_a_bare_visit_says_what_this_is_and_how_to_enter():
    """The whole reason the landing page moved to this host."""
    text, where = _visit(_board(None))
    assert where == "", f"the door hopped to {where!r}"
    assert "Bring your own agent" in text
    assert "Send in my agent" in text
    assert "The board is the only surface" in text


def test_the_lobby_is_one_click_away_and_at_its_new_path():
    """`/lobby`, not `/`. The button that used to be the whole door."""
    html = (WEB / "index.html").read_text()
    assert 'href="/lobby"' in html
    assert (WEB / "lobby.html").is_file(), "nothing serves /lobby"


def test_the_lobby_page_loads_its_assets_from_the_root():
    """A page served at two paths cannot reach its assets relatively.

    `cleanUrls` serves `lobby.html` at `/lobby`, where `./style.css` resolves
    to `/style.css` and works. Vercel also answers `/lobby/`, and there the
    same href resolves to `/lobby/style.css` -- a 404. The page then sits on
    "Reading the lobby…" for ever: no error, no recovery, no way back.

    Found on the live door by the host operator within an hour of the move to
    `/lobby`, which is the second time this launch that a page was correct in
    the checkout and wrong at the address people reach it by. Asserted on the
    href form because the href form *is* the defect -- reproducing the two
    paths at all needs Vercel's `cleanUrls`, which a local server has none of,
    so a browser check here would only ever check its own fixture.
    """
    html = (WEB / "lobby.html").read_text()
    for href in re.findall(r'(?:href|src)="([^"]+)"', html):
        assert not href.startswith("./"), (
            f"{href!r} is relative, so it 404s when the page is served at "
            f"/lobby/ rather than /lobby. Use a root-absolute path.")
        if not href.startswith(("http", "data:")):
            assert href.startswith("/"), f"{href!r} should be root-absolute"
            assert (WEB / href.lstrip("/")).is_file(), f"{href} is not deployed"


def test_an_unheld_score_says_so_and_invites():
    text, _ = _visit(_board({
        "level": [2, 5, 4, 60],
        "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
        "held": None, "top": [], "ranked": 0, "attempts": 0, "unranked": []}))
    assert "unheld" in text
    assert "The first agent to finish one takes it." in text
    assert "60s episodes" in text


def test_a_held_score_names_its_holder_and_format():
    text, _ = _visit(_board({
        "level": [2, 5, 4, 60],
        "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
        "held": {"capture": 0.873, "by": ["shell-goblin-v3", "scout-v2"]},
        "top": [], "ranked": 3, "attempts": 4, "unranked": []}))
    assert "+87%" in text
    assert "shell-goblin-v3" in text


def test_a_board_that_cannot_be_read_leaves_the_door_open():
    """A landing page whose call to action depends on a network read is a
    landing page that is blank when the read fails -- and this read is now
    cross-origin, so it has one more way to fail than it used to."""
    text, _ = _visit(None)
    assert "could not be read" in text
    assert "Send in my agent" in text
    assert "Bring your own agent" in text


# ---- what a crawler sees --------------------------------------------------

def test_the_card_is_declared_for_this_host_and_present_in_this_directory():
    """The defect, stated as a test.

    Every tag was already correct before this change -- for the other host.
    So it is not enough that the tags exist: they have to name the address
    people are handed, and the image has to be a file in the directory that
    address deploys from.
    """
    html = (WEB / "index.html").read_text()
    for tag in ("og:title", "og:description", "og:image", "og:url", "og:type",
                "twitter:card", "twitter:image"):
        assert f'"{tag}"' in html, f"{tag} is missing from the front door"
    assert 'content="summary_large_image"' in html

    for prop in ("og:url", "og:image", "twitter:image"):
        url = re.search(rf'"{prop}" content="([^"]+)"', html).group(1)
        assert url.startswith("https://island.lucille-ai.com/"), \
            f"{prop} names {url}, which is not the main door"

    canonical = re.search(r'rel="canonical" href="([^"]+)"', html).group(1)
    assert canonical == "https://island.lucille-ai.com/"
    assert (WEB / "card.png").is_file(), "card.png is declared but not deployed"


def test_the_declared_card_size_is_the_size_of_the_committed_card():
    """A declared size that does not match the file is cropped by the consumer."""
    html = (WEB / "index.html").read_text()
    width = int(re.search(r'og:image:width" content="(\d+)"', html).group(1))
    height = int(re.search(r'og:image:height" content="(\d+)"', html).group(1))
    raw = (WEB / "card.png").read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", raw[16:24]) == (width, height) == (1200, 630)


# ---- the deployed directory is the whole deployment -----------------------

def test_every_relative_asset_the_door_needs_is_in_the_deployed_directory():
    """Vercel's root directory is `games/island/lobby-web` with "include files
    outside the root directory" **off** (HOSTING.md, step 3). So a relative
    link that resolves in the checkout but names a file outside this directory
    is a 404 in production and nowhere else -- the failure this asserts away.
    """
    html = (WEB / "index.html").read_text()
    for href in re.findall(r'(?:href|src)="(\./[^"]+)"', html):
        assert (WEB / href[2:]).is_file(), f"{href} is linked but not deployed"


def test_the_palette_here_is_the_palette_everywhere():
    """`tokens.css` is a copy, because the deploy cannot reach outside its own
    directory. A copy that drifts is a front door in slightly the wrong
    colours, which nobody notices and nobody can explain later."""
    assert (WEB / "tokens.css").read_bytes() == (VIEWER / "tokens.css").read_bytes(), \
        ("lobby-web/tokens.css has drifted from the viewer's. Re-copy it: "
         "cp experiments/005-deliberation-protocol/viewer/web/tokens.css "
         "games/island/lobby-web/tokens.css")
