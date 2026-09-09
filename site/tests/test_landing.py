"""The legacy root, driven in a browser.

`https://gald33.github.io/ai-lab/` is not the front door any more -- that is
`island.lucille-ai.com`, decided by Gal 2026-09-07 -- and what is left here is
the half of this page that was never about the landing page.

**The redirect contract.** The links that rely on it are records rather than
documents: `games/runs/001` and `002` cite this root as where a finished game's
replay outlives its Switchboard room, and a live feed arrives as `?invite=…` or
`?workspace=…&key=…` on exactly these links. Those replays live on **this**
origin, so anything carrying a query or a fragment still hops into `island/`
here and is *not* sent to the main door. Only a bare visit goes onward. That is
behaviour, not markup -- the hop is a script -- so it is asserted by loading the
page in a browser and watching where it ends up.

**What a crawler sees.** A legacy link that is still posted should render the
card of the page it will land on, so every card tag and the canonical name the
main door rather than this address.

The landing page's own checks moved with it, to
`games/island/tests/test_front_door.py`.

`ISLAND_REQUIRE_BROWSER` turns each skip into a failure, for the reason every
browser check in this repo takes that flag: a skip and a pass are the same tick.
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import pytest

SITE = pathlib.Path(__file__).resolve().parents[1]
WEB = SITE.parent / "experiments" / "does-a-content-free-protocol-help" / "viewer" / "web"

DOOR = "https://island.lucille-ai.com/"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no legacy root at all")
    pytest.skip(why)


@pytest.fixture
def site(tmp_path):
    """The staged root: the page, and enough of `island/` to hop into."""
    shutil.copy(SITE / "index.html", tmp_path / "index.html")
    island = tmp_path / "island"
    island.mkdir()
    shutil.copy(WEB / "tokens.css", island / "tokens.css")
    (island / "index.html").write_text(
        "<!doctype html><title>the viewer</title><h1 id=v>viewer</h1>")
    return tmp_path


def _serve(root: pathlib.Path):
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def _visit(root: pathlib.Path, suffix: str = ""):
    """Load the root, let any hop happen, and report where we ended up.

    The hop off-site is intercepted rather than followed: this test has no
    business reaching the real main door, and a check that needs the network
    to pass is a check that goes red when somebody else's host has a bad day.
    """
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
            tab.route(DOOR + "**", lambda route: route.fulfill(
                status=200, content_type="text/html",
                body="<!doctype html><title>the door</title><h1>the door</h1>"))
            tab.goto(base + suffix)
            tab.wait_for_load_state("networkidle")
            where, text = tab.url, tab.inner_text("body")
            browser.close()
    finally:
        httpd.shutdown()
    assert not errors, f"the page threw: {errors}"
    return (where[len(base):] if where.startswith(base) else where), text


# ---- the redirect contract ------------------------------------------------

def test_a_bare_visit_goes_to_the_main_door(site):
    """One landing page, at the address people are handed. A second copy here
    would drift from it, and the visitor would find that out by clicking."""
    where, text = _visit(site)
    assert where == DOOR, f"a bare visit landed on {where!r}"
    assert "the door" in text


@pytest.mark.parametrize("suffix", [
    "?invite=swb1_abc",
    "?workspace=w_m-g1&key=Z822U5",
    "?board=replays/board-x.json&reveal=replays/reveal-x.json",
])
def test_a_query_still_hops_into_the_viewer_on_this_origin(site, suffix):
    """The live feed and replay links, which are records and cannot be edited.

    They must NOT follow the bare visit to the main door: the replay each one
    names is a file on this origin, and the main door does not have it.
    """
    where, text = _visit(site, suffix)
    assert where.startswith("island/"), f"{suffix} landed on {where!r}"
    assert where.endswith(suffix), f"{suffix} arrived as {where!r}"
    assert "viewer" in text


def test_a_fragment_still_hops_and_survives(site):
    where, _ = _visit(site, "#g20")
    assert where == "island/#g20", where


def test_the_hop_happens_before_anything_paints(site):
    """A browser passing through must not flash a page it is about to leave.

    Asserted on the source rather than by eye: the script has to come before
    the markup it would otherwise render. This is the lobby's frozen-countdown
    lesson from the other side -- order is invisible to a fragment assertion,
    so it is asserted explicitly.
    """
    text = (SITE / "index.html").read_text()
    assert text.index("location.replace") < text.index("<main>")


# ---- what a crawler sees --------------------------------------------------

def test_every_card_tag_names_the_main_door_not_this_address():
    """A legacy link that is still posted renders the card of the page it will
    land on. Pointing these at this address would advertise the address we are
    trying to stop handing out."""
    text = (SITE / "index.html").read_text()
    for prop in ("og:url", "og:image", "twitter:image"):
        url = re.search(rf'"{prop}" content="([^"]+)"', text).group(1)
        assert url.startswith(DOOR), f"{prop} names {url}"
    canonical = re.search(r'rel="canonical" href="([^"]+)"', text).group(1)
    assert canonical == DOOR


def test_every_relative_link_here_resolves(site):
    """A dead link is silent until somebody clicks it. Only the relative ones:
    the main door and the repository are other hosts."""
    text = (SITE / "index.html").read_text()
    staged = {"island/", "island/scores.html", "island/tokens.css"}
    for href in re.findall(r'(?:href|src)="([^"#:]+)"', text):
        assert href in staged, f"{href!r} is linked but nothing stages it"
