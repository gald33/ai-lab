"""The front door, driven in a browser.

Two things are being checked and only one of them is the landing page.

**The redirect contract.** The root used to be a redirect into the viewer, and
the links that rely on that are records rather than documents:
`games/runs/001` and `002` cite the root as where a finished game's replay
outlives its Switchboard room, and a live feed arrives as `?invite=…` or
`?workspace=…&key=…` on exactly these links. Turning the root into a landing
page is allowed to change what a *bare* visit does and is not allowed to break
any of those. That is behaviour, not markup -- the hop is a script -- so it is
asserted by loading the page in a browser and watching where it ends up.

**The score to beat.** Written by a fetch, so a fragment assertion would pass
on a page whose script never ran. The unheld and unreadable states are asserted
as well as the held one, because unheld was the true state on the day the door
opened and unreadable is one network failure away at any time.

`ISLAND_REQUIRE_BROWSER` turns each skip into a failure, for the reason every
browser check in this repo takes that flag: a skip and a pass are the same tick.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

SITE = pathlib.Path(__file__).resolve().parents[1]
WEB = SITE.parent / "experiments" / "005-deliberation-protocol" / "viewer" / "web"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no landing page at all")
    pytest.skip(why)


@pytest.fixture
def site(tmp_path):
    """The staged site: the front door, and enough of `island/` to hop into."""
    for name in ("index.html", "landing.css", "landing.js"):
        shutil.copy(SITE / name, tmp_path / name)
    island = tmp_path / "island"
    island.mkdir()
    shutil.copy(WEB / "tokens.css", island / "tokens.css")
    (island / "index.html").write_text(
        "<!doctype html><title>the viewer</title><h1 id=v>viewer</h1>")
    (island / "api").mkdir()
    return tmp_path


def _board(open_table):
    return {"boards": {"open_table": open_table}}


def _serve(root: pathlib.Path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def _visit(root: pathlib.Path, suffix: str = ""):
    """Load the root, let any hop happen, and report where we ended up."""
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    httpd, base = _serve(root)
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
            tab.goto(base + suffix)
            tab.wait_for_load_state("networkidle")
            where, text = tab.url, tab.inner_text("body")
            browser.close()
    finally:
        httpd.shutdown()
    assert not errors, f"the page threw: {errors}"
    return where[len(base):], text


# ---- the redirect contract ------------------------------------------------

def test_a_bare_visit_gets_the_landing_page(site):
    (site / "island" / "api" / "scores").write_text(json.dumps(_board(None)))
    where, text = _visit(site)
    assert where == "", f"a bare visit hopped to {where!r} instead of landing"
    assert "Bring your own agent" in text
    assert "Send in my agent" in text


@pytest.mark.parametrize("suffix", [
    "?invite=swb1_abc",
    "?workspace=w_m-g1&key=Z822U5",
    "?board=replays/board-x.json&reveal=replays/reveal-x.json",
])
def test_a_query_still_hops_into_the_viewer_carrying_itself(site, suffix):
    """The live feed and replay links, which are records and cannot be edited."""
    where, text = _visit(site, suffix)
    assert where.startswith("island/"), f"{suffix} landed on {where!r}"
    assert where.endswith(suffix), f"{suffix} arrived as {where!r}"
    assert "viewer" in text


def test_a_fragment_still_hops_and_survives(site):
    where, _ = _visit(site, "#g20")
    assert where == "island/#g20", where


def test_the_hop_happens_before_the_landing_paints(site):
    """A browser passing through must not flash a page it is about to leave.

    Asserted on the source rather than by eye: the script has to come before
    the markup it would otherwise render. This is the lobby's frozen-countdown
    lesson from the other side -- order is invisible to a fragment assertion,
    so it is asserted explicitly.
    """
    text = (SITE / "index.html").read_text()
    assert text.index("location.replace") < text.index("<main>")


# ---- the score to beat ----------------------------------------------------

def test_an_unheld_score_says_so_and_invites(site):
    (site / "island" / "api" / "scores").write_text(json.dumps(_board({
        "level": [2, 5, 4, 60],
        "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
        "held": None, "top": [], "ranked": 0, "attempts": 0, "unranked": []})))
    _, text = _visit(site)
    assert "unheld" in text
    assert "The first agent to finish one takes it." in text
    assert "60s episodes" in text


def test_a_held_score_names_its_holder_and_format(site):
    (site / "island" / "api" / "scores").write_text(json.dumps(_board({
        "level": [2, 5, 4, 60],
        "label": "2 traders · 5 goods · 4 episodes · 60s episodes",
        "held": {"capture": 0.873, "by": ["shell-goblin-v3", "scout-v2"]},
        "top": [], "ranked": 3, "attempts": 4, "unranked": []})))
    _, text = _visit(site)
    assert "+87%" in text
    assert "shell-goblin-v3" in text
    assert "60s episodes" in text


def test_a_board_that_cannot_be_read_leaves_the_door_open(site):
    """No `api/scores` at all. The hero must still work.

    A landing page whose call to action depends on a network read is a landing
    page that is blank when the read fails.
    """
    _, text = _visit(site)
    assert "could not be read" in text
    assert "Send in my agent" in text
    assert "Bring your own agent" in text


# ---- what a crawler sees --------------------------------------------------

def test_the_card_a_posted_link_renders_as_is_declared_and_present():
    """Open Graph is read by crawlers that do not run scripts.

    So every tag has to be in the file, and the image it names has to exist at
    the path the deploy puts it at -- `pages.yml` copies `card.png` to the site
    root, which is what the absolute URL here resolves to.
    """
    text = (SITE / "index.html").read_text()
    for tag in ("og:title", "og:description", "og:image", "og:url", "og:type",
                "twitter:card", "twitter:image"):
        assert f'"{tag}"' in text, f"{tag} is missing from the front door"
    assert 'content="summary_large_image"' in text
    assert (SITE / "card.png").is_file(), "card.png is declared but not committed"
    width = re.search(r'og:image:width" content="(\d+)"', text)
    height = re.search(r'og:image:height" content="(\d+)"', text)
    assert (int(width.group(1)), int(height.group(1))) == (1200, 630)


def test_the_declared_card_size_is_the_size_of_the_committed_card():
    """A declared size that does not match the file is cropped by the consumer."""
    import struct

    raw = (SITE / "card.png").read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", raw[16:24])
    assert (width, height) == (1200, 630)


def test_every_relative_link_on_the_front_door_resolves(site):
    """A dead link on a landing page is silent until somebody clicks it.

    Only the relative ones: the lobby and the repository are other hosts and
    are not this test's to reach.
    """
    text = (SITE / "index.html").read_text()
    staged = {"island/", "island/scores.html", "landing.css", "landing.js",
              "island/tokens.css", "card.png"}
    for href in re.findall(r'(?:href|src)="([^"#:]+)"', text):
        assert href in staged, f"{href!r} is linked but nothing stages it"
