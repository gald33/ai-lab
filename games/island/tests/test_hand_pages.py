"""The hand's pages, driven in a browser against a real hub.

`CLAUDE.md`: *a page's behaviour is checked in a browser, or it is not
checked* -- decided after the lobby's countdowns were found frozen while every
markup assertion around them passed. Everything here is a thing the page
*does*: mint a key, register, compose a line, post it, read the board back.

**And what it posts is read by a real Python client**, not by the page itself.
That is the only check that the wire format in `hub.js` is right: the sealing
contexts, the `{b, ch, s}` wrapper the transport puts around a body, the
signature computed over the blinded sender and the blinded channel. Every one
of those is invisible from inside the browser -- a page that got them wrong
would show its own lines back perfectly and be unreadable to everybody else.

The hub is given the page's **exact origin** rather than a wildcard, because
that is what the managed hub does (measured: an allowlist, not reflect-all --
see `games/island.md`), and a page that assumed a wildcard would work here and
fail in service.

    python -m pytest games/island/tests/test_hand_pages.py -q
"""

from __future__ import annotations

import functools
import http.server
import os
import pathlib
import shutil
import socket
import threading
import urllib.parse

import pytest

from games.island.hand.brief import brief as py_brief
from games.island.hand.declaration import declaration as py_declaration
from games.island.hand.declaration import hands_on_board

HAND = pathlib.Path(__file__).resolve().parent.parent / "hand"
#: The viewer's own web assets, which `kids-island.html` imports over `../`.
VIEWER = (pathlib.Path(__file__).resolve().parents[3] / "experiments"
          / "005-deliberation-protocol" / "viewer" / "web")
WORKSPACE = "island-hand-test"
#: The kids' page gets a room of its own, because `Room._findManager` takes
#: the first roster row called `manager` and this file registers several. A
#: shared roster would make which manager a whisper reached depend on the
#: order the tests happened to run in.
KIDS = "island-kids-test"
#: And the drawn page gets a third, for the same reason KIDS exists: which
#: manager a whisper reaches must not depend on the order the tests ran in.
#: **A room per test**, not one shared: `Room._findManager` takes the first
#: roster row called `manager`, so a shared roster makes which manager a
#: whisper reaches depend on the order the tests happened to run in.
KIDS_3D = "island-kids-3d"
KEY = "Z822U5v1WFyeOEJUeLchMgLED-VgI_0chD4OjmRxej0"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"drove no page at all")
    pytest.skip(why)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    """The hand's flat pages, served. Copied rather than served in place, so
    what runs is the committed bytes and nothing beside them.

    **`play.html` is not here any more**, and neither is `kids-island.html`:
    both import the viewer's modules from one directory up, so a flat fixture
    would serve a page that cannot exist and would 404 on its own reducer
    while passing. They are driven from `island_site`, which is the layout
    `pages.yml` actually stages. What is left here is the two pages that
    genuinely have no parent directory to reach into.
    """
    root = tmp_path_factory.mktemp("hand-site")
    for name in ("lobby.html", "kids.html", "switchboard.js",
                 "hub.js", "identity.js", "lobby_lines.js", "play_lines.js",
                 "declaration.js", "brief.js", "room.js", "transcript.js"):
        shutil.copy(HAND / name, root / name)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def island_site(tmp_path_factory):
    """The hand's pages served **the way the deploy serves them**: the viewer's
    modules at the root and the hand's pages one directory down.

    `kids-island.html` imports `../stage.js` and `../reducer.js`, which is a
    real path rather than a convenience -- `pages.yml` stages `viewer/web/`
    at `/island/` and `hand/` at `/island/hand/`. A flat fixture would serve a
    page that could never exist, and would pass while the deployed one 404ed
    on its own island.
    """
    root = tmp_path_factory.mktemp("island-site")
    shutil.copytree(VIEWER, root, dirs_exist_ok=True)
    hand = root / "hand"
    hand.mkdir(exist_ok=True)
    for name in ("kids-island.html", "kids.html", "play.html", "lobby.html",
                 "switchboard.js", "hub.js", "identity.js", "lobby_lines.js",
                 "play_lines.js", "declaration.js", "brief.js", "room.js",
                 "transcript.js"):
        shutil.copy(HAND / name, hand / name)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def cors_hub(site, island_site, tmp_path_factory):
    """A hub that allows the page's origin, and only it.

    The managed hub is an allowlist rather than reflect-all -- measured, with
    the reproduction in `games/island.md` -- so a wildcard here would be a
    friendlier hub than the real one and would hide a page that depended on
    the difference.
    """
    uvicorn = pytest.importorskip("uvicorn")
    from switchboard.config import ServerConfig
    from switchboard.server import create_app
    from switchboard.store import Store

    tmp_path = tmp_path_factory.mktemp("hand-hub")
    port = _free_port()
    store = Store(str(tmp_path / "hub.db"))
    app = create_app(ServerConfig(db_path=store.path,
                                  cors_origins=(site, island_site)),
                     store=store)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(200):
        if server.started:
            break
        threading.Event().wait(0.05)
    else:                                              # pragma: no cover
        pytest.fail("hub did not start")
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


def _client(hub_url, agent_id):
    """A real Python client on the same room, to read what the page wrote."""
    from switchboard.client import Client
    from switchboard.config import ClientConfig

    return Client(ClientConfig(url=hub_url, token="", workspace=WORKSPACE,
                               key=KEY), agent_id=agent_id)


def _wire_to(hub_url, agent_id):
    """The envelopes on an agent's `@` channel, opened no further than the
    workspace.

    A client opens a whisper for you, which is exactly what hides the thing
    this has to see: **which form the page sealed in**. `Client.inbox` hands
    back plaintext whether the marker said `whisper` or `ask`, so a test that
    reads it cannot tell a page that writes the current wire from one that
    writes the old one -- and that was the whole of the change on 2026-09-05.
    So this goes to the hub's own `/channels` and stops at the outer
    workspace envelope, leaving the inner one shut with its marker readable.
    """
    import json
    import urllib.request
    from switchboard import crypto

    cipher = crypto.WorkspaceCipher.from_key(KEY, WORKSPACE)
    channel = cipher.blind_channel(f"@{cipher.blind(agent_id, 'agent')}")
    url = (f"{hub_url}/channels/{urllib.parse.quote(channel, safe='')}"
           f"?workspace={urllib.parse.quote(WORKSPACE)}")
    with urllib.request.urlopen(url, timeout=10) as got:
        rows = json.load(got)["messages"]
    return [cipher.unseal(r["body"], "message.body") for r in rows]


@pytest.fixture(scope="module")
def browser():
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")
    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    with play.sync_playwright() as pw:
        try:
            launched = pw.chromium.launch(
                executable_path=str(chrome) if chrome else None)
        except Exception as exc:                       # noqa: BLE001
            _missing(f"no chromium to drive a page with: {exc!r}")
        yield launched
        launched.close()


def _tab(browser, url, errors):
    tab = browser.new_page()
    tab.on("pageerror", lambda e: errors.append(str(e)))
    tab.goto(url)
    return tab


def _fill_room(tab, hub_url, *, name):
    tab.fill("#url", hub_url)
    tab.fill("#token", "")
    tab.fill("#workspace", WORKSPACE)
    tab.fill("#key", KEY)
    tab.fill("#name", name)


# --- the lobby -------------------------------------------------------------

def test_the_lobby_previews_the_line_before_anything_is_posted(browser, site):
    """What the board says has to be what the driver saw.

    A composer that showed one thing and posted another would be a page
    telling its user a comfortable story, and every assertion about the
    grammar elsewhere would still pass.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    tab.fill("#traders", "3")
    tab.fill("#episodes", "12")
    tab.fill("#goods", "4")
    tab.select_option("#seconds", "90")

    assert tab.inner_text("#openPreview") == (
        "OPEN traders=3 episodes=12 rounds=1 goods=4 seconds=90")
    assert not errors, errors
    tab.close()


def test_the_lobby_refuses_a_bad_input_in_the_page_and_says_why(browser, site):
    """The refusal arrives before the press, not after the lobby says nothing.

    A driver whose `OPEN` was silently dropped has no way to tell that from a
    lobby that is simply busy.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    tab.fill("#traders", "9")

    assert "traders must be between 2 and 4" in tab.inner_text("#openPreview")
    assert tab.is_disabled("#open"), "and the button cannot be pressed"

    tab.fill("#traders", "3")
    assert tab.inner_text("#openPreview").startswith("OPEN ")
    assert tab.is_enabled("#open"), "and recovers when the input is fixed"
    assert not errors, errors
    tab.close()


def test_a_join_composed_in_the_page_is_read_by_the_real_parser(
        browser, site, cors_hub):
    """**End to end, and read by somebody else.**

    The page mints a key, registers, composes a JOIN with a nonce it drew
    itself, seals it, signs it and posts it. A Python client then reads the
    board and `protocol.parse` reads the line. Nothing in the browser is
    trusted to confirm any of that.
    """
    from games.island import protocol

    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="scout-v2")
    tab.fill("#table", "g7")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)

    rows = _client(cors_hub, "reader").history("lobby", limit=50)
    posted = [r["body"] for r in rows if isinstance(r.get("body"), str)]
    joins = [protocol.parse(line) for line in posted if line.startswith("JOIN")]

    assert joins, f"no JOIN on the board; saw {posted}"
    assert joins[0].table == "g7"
    assert joins[0].name == "scout-v2"
    assert protocol.NONCE.match(joins[0].nonce), (
        "the seat drew its own half of the seed, and it survived the round trip")
    assert not errors, errors
    tab.close()


def test_the_page_signs_with_the_key_it_published(browser, site, cors_hub):
    """The seat binding turns on this and nothing else.

    `Lobby._join` refuses a JOIN Switchboard did not verify, and the manager
    refuses a line whose key does not match the one the lobby witnessed. A
    page that posted unsigned, or signed with a key it had not published,
    would be refused a seat -- and would look, from inside the browser,
    exactly like a page that worked.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="trader-b")
    tab.fill("#table", "g8")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)
    published = tab.evaluate("window.HAND_SEAT.publicKey")

    reader = _client(cors_hub, "reader2")
    reader.agents()          # learn the roster's keys, as any reader must
    rows = reader.history("lobby", limit=50)
    mine = [r for r in rows
            if isinstance(r.get("body"), str) and "trader-b" in r["body"]]

    assert mine, "the page's line is not on the board"
    verdict = mine[-1].get("signature") or {}
    assert verdict.get("status") == "verified", verdict
    assert verdict.get("key") == published, (
        "verified under the very key the page published at registration")
    assert not errors, errors
    tab.close()


def test_the_lobby_keeps_the_seat_key_across_a_reload(browser, site, cors_hub):
    """IndexedDB on one served origin is what carries a seat from the lobby to
    the island. A page that minted a fresh key on reload would take a seat and
    then be unable to play it."""
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="steady")
    tab.fill("#table", "g9")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)
    first = tab.evaluate("window.HAND_SEAT.publicKey")

    tab.reload()
    _fill_room(tab, cors_hub, name="steady")
    tab.fill("#table", "g9")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)

    assert tab.evaluate("window.HAND_SEAT.publicKey") == first
    assert not errors, errors
    tab.close()


def test_the_invite_the_lobby_whispers_becomes_the_link_to_the_island_page(
        browser, site, cors_hub):
    """**The step between the two pages, which nothing else checked.**

    A driver who joined and saw no input field was looking at the right page
    at the wrong moment (2026-09-04): the input is on `play.html`, which this
    page links to only once the table settles and the lobby whispers the
    room. Every piece of that path was tested alone -- the JOIN was read by
    the real parser, the lobby whispers the seats, the island page takes an
    invite -- and the join between them, a whisper sealed by the Python
    lobby and opened by the page's JavaScript, was not. And it was broken:
    the page opened whispers under `message.body`, the outer envelope's
    context, where the library seals them under `ask.body`, so every invite
    came back "unreadable" and every driver was left pressing "Read the
    board" with nothing on the page to say why. This test fails on that
    page and passes on the fixed one.

    So: a real lobby on the page's hub, the page in one seat, a Python
    entrant in the other, a manager's claim, and then the page must show the
    link -- under the status message, where the message says it is --
    carrying the room, its key and its write key.
    """
    from switchboard.client import Client
    from switchboard.config import ClientConfig

    from games.island.lobby import Lobby

    def _client_for(agent_id):
        return Client(ClientConfig(url=cors_hub, url_source="explicit",
                                   workspace=WORKSPACE, key=KEY),
                      agent_id=agent_id)

    lobby = Lobby(client=_client_for("lobby-w"))
    lobby.present()
    opener = _client_for("opener-w")
    opener.register(name="opener-w", kind="local", branch="main", task="")
    opener.post("lobby", "OPEN traders=2 episodes=2 rounds=1 goods=3 seconds=60")
    lobby.drain()
    table = next(t for t in lobby.tables.values() if t.opened_by == opener.agent_id)

    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="hand-w")
    tab.fill("#table", table.id)
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)
    lobby.drain()
    assert len(table.seats) == 1, "the page's seat was witnessed"
    assert not table.settled, "and nothing to play yet: one seat is empty"
    assert tab.locator("#invite a").count() == 0, (
        "no link before the table settles -- the page must not invent one")

    other = _client_for("other-w")
    other.register(name="other-w", kind="local", branch="main", task="")
    other.post("lobby", f"JOIN {table.id} as other-w")
    manager = _client_for("manager-w")
    manager.register(name="lucille", kind="local", branch="main", task="")
    manager.post("lobby", f"MANAGE {table.id}")
    lobby.drain()
    assert table.settled

    # No button: after a JOIN the page keeps reading until the room is handed
    # out, so the link appears on its own within one poll.
    link = tab.locator("#invite #playLink")
    link.wait_for(timeout=15_000)
    # `text-transform: uppercase` is paint, so the words are compared and
    # not the casing the stylesheet happens to render them in.
    assert "send in my agent" in link.inner_text().lower()
    href = link.get_attribute("href")
    assert href.startswith("./play.html?"), href
    query = dict(urllib.parse.parse_qsl(href.split("?", 1)[1]))
    assert query["workspace"] == table.workspace
    assert query["name"] == "hand-w"
    assert query["write_key"], "the seat's invite carries the room's write key"
    # And the same room with buttons instead of a grammar. A page nobody can
    # reach is a page nobody plays, and this link is the only door to it.
    kids = tab.locator("#kidsLink")
    assert kids.get_attribute("href") == f"./kids.html?{href.split('?', 1)[1]}"
    drawn = tab.locator("#kidsIslandLink")
    assert drawn.get_attribute("href") == \
        f"./kids-island.html?{href.split('?', 1)[1]}"
    # They are behind the arrow rather than in the sentence, and the arrow is
    # a thing the page *does* -- checked in a browser below.
    assert not tab.locator("#waysIn").is_visible()

    # **And the seat, so nobody has to type `T1`.** The lobby witnessed this
    # driver into a labelled seat and said so on its own board; a page that
    # then asked for the label would be asking for something it already had --
    # and asking a child to find it on a board written for agents.
    assert query["seat"] == table.label(
        next(peer for peer, name in table.seats.items() if name == "hand-w")), \
        f"the link carries the seat the lobby gave: {query}"
    # Under the status message, not somewhere else on the page: the message
    # says where to look, and the test holds it to that.
    assert tab.evaluate(
        "document.getElementById('says').nextElementSibling.id") == "invite"

    # **And the room is on this page, entered under the key that joined.**
    # Decided by Gal, 2026-09-04, after g27: the controls appear here when
    # the game is active, and there is no second page to reach with the
    # wrong key. The declaration is on the room's board, and a line typed
    # here verifies under the very key the lobby witnessed on the JOIN.
    tab.wait_for_function("window.HAND_ROOM_READY === true", timeout=15_000)
    assert tab.is_visible("#say"), "the input field, on the lobby page"
    witnessed = tab.evaluate("window.HAND_SEAT.publicKey")
    tab.fill("#say", "hello from the hand")
    tab.click("#post")
    tab.wait_for_function(
        "document.getElementById('says').textContent === 'Posted.'", timeout=15_000)
    from switchboard.client import Client as _Client
    from switchboard.config import ClientConfig as _Config
    reader = _Client(_Config(url=cors_hub, token="", workspace=query["workspace"],
                             key=query["key"]), agent_id="reader-room-w")
    reader.agents()
    rows = reader.history("island", limit=50)
    assert hands_on_board([{"body": r.get("body")} for r in rows]) == {"T1": "driven"}
    mine = [r for r in rows if r.get("body") == "hello from the hand"]
    assert mine, [r.get("body") for r in rows]
    assert (mine[0].get("signature") or {}).get("key") == witnessed, \
        "the key that plays is the key the lobby witnessed"
    assert "hello from the hand" in tab.inner_text("#room"), \
        "and the room's board on this page shows it"

    # **And again after a reload.** The page's memory of its seat is gone;
    # the key is not (IndexedDB), and the whisper is still in the inbox
    # because the read that showed it was a peek. Same name, same table,
    # "Read the board", same link.
    tab.reload()
    _fill_room(tab, cors_hub, name="hand-w")
    tab.fill("#table", table.id)
    tab.click("#refresh")
    again = tab.locator("#invite #playLink")
    again.wait_for(timeout=15_000)
    assert again.get_attribute("href") == href
    assert not errors, errors
    tab.close()


def test_the_seat_stays_on_the_roster_for_as_long_as_a_table_may_form(
        browser, site, cors_hub):
    """**g27, 2026-09-04.** A hand joined; the second seat came 126 seconds
    later; the hand's roster row, registered with the hub's two-minute
    default, had lapsed by four seconds when the table settled, so the lobby
    could not seal the room to it and the page never showed a link. The page
    registers for the hub's ceiling now, which covers the whole of the 900s
    a table is allowed to form and a round besides. Read off the roster with
    a real client: the row's `expires_in`, not what the page asked for."""
    from games.island.lobby import TABLE_TTL

    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="patient")
    tab.fill("#table", "g11")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)

    rows = [a for a in _client(cors_hub, "reader-ttl").agents()
            if a.get("name") == "patient"]
    assert rows, "the page's seat is on the roster"
    assert rows[0]["expires_in"] > TABLE_TTL, rows[0]
    assert not errors, errors
    tab.close()


def test_the_page_shows_the_keys_it_holds_and_can_replace_or_forget_one(
        browser, site, cors_hub):
    """Asked for by Gal, 2026-09-04: a key the page keeps across reloads is
    a key its holder should be able to see, replace and throw away. The
    list shows the name with the very public key the lobby witnessed; "new
    key" mints a different one under the same name; "forget" removes it."""
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="keyed-1")
    tab.fill("#table", "g13")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)
    witnessed = tab.evaluate("window.HAND_SEAT.publicKey")

    tab.click("#seatsHeld > summary")           # the fold, opened as a driver would
    row = tab.locator(".seat[data-name='keyed-1']")
    row.wait_for(timeout=15_000)
    assert row.locator("code").get_attribute("title") == witnessed, \
        "the list shows the key the lobby witnessed, in full on hover"

    row.locator("button[data-act=new]").click()
    tab.wait_for_function(
        "document.querySelector(\".seat[data-name='keyed-1'] code\")"
        f".title !== {witnessed!r}", timeout=15_000)
    replaced = row.locator("code").get_attribute("title")
    assert replaced != witnessed
    assert tab.evaluate("window.HAND_SEAT") is None, \
        "the seat taken under the old key is no longer this page's seat"
    assert "manager refuses" in tab.inner_text("#says")

    row.locator("button[data-act=forget]").click()
    tab.wait_for_function(
        "document.querySelector(\".seat[data-name='keyed-1']\") === null",
        timeout=15_000)
    tab.reload()
    assert tab.locator(".seat[data-name='keyed-1']").count() == 0, \
        "and it is gone from the browser, not just from the page"
    assert not errors, errors
    tab.close()


def test_an_invite_posted_in_the_clear_is_still_the_link(browser, site, cors_hub):
    """The lobby's other way of handing a room out: when it cannot seal to
    every seat, the invite goes on the public board in the clear and the game
    is practice. Until g27 the page only read its inbox, so a driver whose
    room was posted in public saw nothing. Now it is the same link, and the
    page says which way it came."""
    from switchboard.invite import Invite

    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="hand-c")
    tab.fill("#table", "g12")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)
    assert tab.locator("#invite a").count() == 0

    lobby = _client(cors_hub, "lobby-c")
    lobby.register(name="lobby", kind="local", branch="main", task="")
    code = Invite(url=cors_hub, workspace="ws_clear12", token="", key=KEY,
                  write_key="seed-c", note="g12").encode()
    lobby.post("lobby", f"g12 invite: {code}")

    tab.click("#refresh")
    link = tab.locator("#invite #playLink")
    link.wait_for(timeout=15_000)
    query = dict(urllib.parse.parse_qsl(
        link.get_attribute("href").split("?", 1)[1]))
    assert query["workspace"] == "ws_clear12"
    assert query["write_key"] == "seed-c"
    assert "in the clear" in tab.inner_text("#invite")
    # The invite line is one 600-character token; the page must break it
    # rather than grow past the viewport (Gal, 2026-09-04, from a screenshot
    # of g32's `watch:` line running off the right edge).
    assert tab.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"), \
        "the page scrolls sideways"
    assert not errors, errors
    tab.close()



def test_the_arrow_opens_the_other_ways_in_and_all_of_them_carry_the_room(
        browser, site, cors_hub):
    """**A door, not a link in the middle of a sentence.**

    Gal, 2026-09-08: the ways into a table should be one button with "a small
    arrow ... that opens up a small menu of more options: hacker hand, hand
    and agent, nice buttons, my kid wants to play full visual UI". Until then
    three of the four were inline links in a paragraph of prose, where a
    reader finds a link and a driver does not find a door.

    The opening is a thing the page *does*, so it is driven rather than read
    off the markup: the menu is checked to be invisible, the arrow clicked,
    and every way in checked to carry the same room -- because a menu entry
    that dropped the key is a page that asks a driver to type one.
    """
    from switchboard.invite import Invite

    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    _fill_room(tab, cors_hub, name="hand-ways")
    tab.fill("#table", "g44")
    tab.click("#join")
    tab.wait_for_function("window.HAND_SEAT !== undefined", timeout=15_000)

    lobby = _client(cors_hub, "lobby-ways")
    lobby.register(name="lobby", kind="local", branch="main", task="")
    code = Invite(url=cors_hub, workspace="ws_ways44", token="", key=KEY,
                  write_key="seed-w", note="g44").encode()
    lobby.post("lobby", f"g44 invite: {code}")
    tab.click("#refresh")

    tab.locator("#invite #playLink").wait_for(timeout=15_000)
    menu = tab.locator("#waysIn")
    assert not menu.is_visible(), "the menu is shut until the arrow is pressed"
    assert tab.locator("#moreWays").get_attribute("aria-expanded") == "false"

    tab.click("#moreWays")
    menu.wait_for(state="visible", timeout=5_000)
    assert tab.locator("#moreWays").get_attribute("aria-expanded") == "true"

    ways = tab.eval_on_selector_all(
        "#waysIn a", "els => els.map(a => [a.id, a.getAttribute('href')])")
    assert [w[0] for w in ways] == \
        ["waysAgent", "hackerLink", "kidsLink", "kidsIslandLink"], ways
    pages = [href.split("?", 1)[0] for _, href in ways]
    assert pages == ["./play.html", "./play.html", "./kids.html",
                     "./kids-island.html"], pages
    # Every one of them, the same room. A menu entry that dropped the key
    # would hand a driver a page asking them to type one.
    for _, href in ways:
        query = dict(urllib.parse.parse_qsl(href.split("?", 1)[1]))
        assert query["workspace"] == "ws_ways44", href
        assert query["write_key"] == "seed-w", href
    # And the button is the first way, so the two cannot drift apart.
    assert tab.locator("#playLink").get_attribute("href") == ways[0][1]

    tab.click("#moreWays")
    assert not menu.is_visible(), "and it shuts again"
    assert not errors, errors
    tab.close()


# --- the island ------------------------------------------------------------

def test_entering_the_room_declares_the_driver_without_being_asked(
        browser, island_site, cors_hub):
    """**The mechanism by which declarations happen at all.**

    Nobody can be made to declare -- an open room means a person can drive a
    seat in silence and nothing notices. What can be done is to make declaring
    the thing that happens when the page is used, and that is this: entering
    the room posts the line, and `hands_on_board` reads it back off the board
    the same way the record will.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    tab.fill("#url", cors_hub)
    tab.fill("#token", "")
    tab.fill("#workspace", WORKSPACE)
    tab.fill("#key", KEY)
    tab.fill("#channel", "island")
    tab.fill("#name", "driver-1")
    tab.fill("#seat", "T1")
    tab.click("#enter")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)

    rows = _client(cors_hub, "reader3").history("island", limit=50)
    bodies = [{"body": r.get("body")} for r in rows]

    assert hands_on_board(bodies) == {"T1": "driven"}
    assert not errors, errors
    tab.close()


def test_a_line_whispered_from_the_page_opens_for_the_manager_under_the_seats_key(
        browser, island_site, cors_hub):
    """Gal, 2026-09-04: a command can go by `say` or by `whisper`, and the
    page needs both. The manager settles a whispered `PRODUCE` exactly as one
    said on the board -- same author, same signature check -- so what has to
    hold is that a real Python client registered as the manager opens what
    the page sealed, reads the text the driver typed, and verifies it under
    the very key the page plays with.

    **Sealed as `whisper`** (Gal, 2026-09-05: "don't use the legacy `ask`"),
    which is asserted off the wire rather than inferred from the open: the
    client opens either form, so a successful read says nothing at all about
    which one went out. `_wire_to` stops at the outer envelope to see it.
    """
    # Its own id: the lobby test above whispers an invite to a "manager-w",
    # and this inbox must hold exactly the one line the page sends.
    manager = _client(cors_hub, "manager-room")
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    _enter(tab, cors_hub, WORKSPACE, write_key=None, name="driver-whisper")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)
    seat_key = tab.evaluate("document.getElementById('who').textContent")

    tab.fill("#whisperLine", "PRODUCE bread=0.5 fish=0.5")
    tab.click("#whisper")
    tab.wait_for_function(
        "document.getElementById('says').textContent.startsWith('Whispered')",
        timeout=15_000)

    manager.agents()               # the page's exchange key and signing key
    [got] = [m for m in manager.inbox() if m.get("type") == "whisper"]
    assert got["body"] == "PRODUCE bread=0.5 fish=0.5"
    assert not got.get("unreadable")
    verdict = got.get("signature") or {}
    assert verdict.get("status") == "verified", verdict
    assert verdict["key"][:12] in seat_key, \
        "verified under the key this page plays with"
    board = [r.get("body") for r in _client(cors_hub, "reader-wh").history("island", limit=50)]
    assert "PRODUCE bread=0.5 fish=0.5" not in board, "and it is not on the board"

    [wrapped] = _wire_to(cors_hub, "manager-room")
    assert wrapped["b"]["m"] == "whisper", \
        f"the page sealed the {wrapped['b']['m']!r} form, not the current wire"
    assert not errors, errors
    tab.close()


def test_the_room_copies_itself_for_a_model_and_then_only_what_is_new(
        browser, island_site, cors_hub):
    """**The hand as intermediary, and the part that makes it worth having.**

    `games/island.md` ("A person may sit in a seat") describes a driver taking
    advice from "a chat window with no tools, no board access and no memory of
    the room beyond what the person pastes into it". These buttons are that
    paste. Asked for by Gal, 2026-09-04, with the requirement that matters: a
    copy that remembers, so a round is not re-pasted at every bell.

    So the whole room copies once, and the next copy carries only what arrived
    after it -- checked by posting a line between the two and requiring the
    second copy to hold that line and not the first one's.
    """
    manager = _client(cors_hub, "manager-copy")
    manager.register(name="manager", kind="local", branch="main", task="")
    manager.post("island", "Schedule for this round. 2 traders: T1, T2.")

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    _enter(tab, cors_hub, WORKSPACE, write_key=None, name="driver-copy")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)
    tab.wait_for_function(
        "(window.HAND_BOARD || []).some(r => String(r.body).startsWith('Schedule'))",
        timeout=15_000)

    tab.click("#copyAll")
    tab.wait_for_function("window.HAND_COPIED", timeout=15_000)
    whole = tab.evaluate("window.HAND_COPIED")
    assert whole["kind"] == "all"
    assert "You are advising the driver of seat T1" in whole["text"]
    assert "Schedule for this round" in whole["text"], whole["text"]
    assert "manager:" in whole["text"], "the roster's name, not a blinded id"
    assert "nothing here restates them" in whole["text"], (
        "the header points at the manager's own rules rather than paraphrasing")

    # A line arrives after that copy. Only it belongs in the next one.
    manager.post("island", "episode 1 of 4 is open")
    tab.wait_for_function(
        "(window.HAND_BOARD || []).some(r => String(r.body).startsWith('episode 1'))",
        timeout=15_000)
    tab.wait_for_function(
        "document.getElementById('copyNew').textContent.includes('(')",
        timeout=15_000)
    assert not tab.is_disabled("#copyNew"), "there is something new to send"

    tab.click("#copyNew")
    tab.wait_for_function("window.HAND_COPIED.kind === 'new'", timeout=15_000)
    update = tab.evaluate("window.HAND_COPIED")
    assert "episode 1 of 4 is open" in update["text"]
    assert "Schedule for this round" not in update["text"], (
        "a line already copied is not sent again")
    assert "continued" in update["text"] and "not repeated" in update["text"]

    # And with nothing further arriving, there is nothing to press.
    tab.wait_for_function(
        "document.getElementById('copyNew').disabled === true", timeout=15_000)

    # **The mark survives a reload**, which is why it is in `localStorage` and
    # not the `sessionStorage` this page uses for view state: a driver who
    # reloads mid-round should not have to re-send the round. Asserted rather
    # than assumed, because the comment in `transcript.js` claims it.
    manager.post("island", "bell — episode 1 closed")
    tab.reload()
    _enter(tab, cors_hub, WORKSPACE, write_key=None, name="driver-copy")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)
    tab.wait_for_function(
        "document.getElementById('copyNew').disabled === false", timeout=15_000)
    tab.click("#copyNew")
    tab.wait_for_function("window.HAND_COPIED.kind === 'new'", timeout=15_000)
    after = tab.evaluate("window.HAND_COPIED")["text"]
    assert "bell — episode 1 closed" in after
    assert "Schedule for this round" not in after and "episode 1 of 4" not in after, \
        "the reload did not forget what had already been sent"
    assert not errors, errors
    tab.close()


def test_the_pages_declaration_is_byte_for_byte_the_pythons(browser, site):
    """`declaration.js` restates `declaration.py` because a static origin
    cannot call Python. The record parses the line with an anchored regular
    expression, so a near-miss declares nothing while looking as though it
    had -- and no assertion inside the browser could tell."""
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    from_js = tab.evaluate(
        """() => import('./declaration.js').then(m => m.declaration('T3'))""")

    assert from_js == py_declaration("T3")
    assert not errors, errors
    tab.close()


def test_the_pages_brief_is_byte_for_byte_the_pythons(browser, site):
    """Same arrangement, and the one that matters more: the brief is what
    withholds the lobby from an agent. A JS copy that drifted could put the
    lobby's coordinates back and nothing would fail."""
    errors: list[str] = []
    tab = _tab(browser, f"{site}/lobby.html", errors)
    from_js = tab.evaluate(
        """() => import('./brief.js').then(m => m.brief({
             seat: 'T1', workspace: 'island-g7', roomKey: 'RK',
             channel: 'island', agentId: 't1',
             signingKey: 'SK', exchangeKey: 'XK',
             episodes: 8, seconds: 90 }))""")

    assert from_js == py_brief(
        seat="T1", workspace="island-g7", room_key="RK", channel="island",
        agent_id="t1", signing_key="SK", exchange_key="XK",
        episodes=8, seconds=90)
    assert "island-lobby" not in from_js, "and it still withholds the lobby"
    assert not errors, errors
    tab.close()


def test_the_island_page_posts_whatever_is_typed(browser, island_site, cors_hub):
    """**There is no validation gate, on purpose.**

    An agent at the table can post a malformed line and lose the exchange; the
    manager never repairs one. A page that refused to let its driver do the
    same would be playing an easier game than the seats beside it -- which is
    the asymmetry that made a validating composer wrong in the first place.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    tab.fill("#url", cors_hub)
    tab.fill("#token", "")
    tab.fill("#workspace", WORKSPACE)
    tab.fill("#key", KEY)
    tab.fill("#channel", "island-2")
    tab.fill("#name", "driver-2")
    tab.fill("#seat", "T2")
    tab.click("#enter")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)

    tab.fill("#say", "PRODUC bread=oops")     # not a form, and posted anyway
    tab.click("#post")
    tab.wait_for_function(
        "window.HAND_BOARD.some(r => r.body === 'PRODUC bread=oops')",
        timeout=15_000)

    rows = _client(cors_hub, "reader4").history("island-2", limit=50)
    assert "PRODUC bread=oops" in [r.get("body") for r in rows]
    assert not errors, errors
    tab.close()


def test_a_shortcut_button_fills_the_bar_and_does_not_post(browser, island_site):
    """The buttons are a convenience over the input bar and never a second
    path to the board: what they do is put text where the driver can see and
    edit it before pressing."""
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    tab.click("[data-fill='APPROVE p1']")
    tab.click("[data-fill='PRODUCE ']")
    assert tab.input_value("#whisperLine") == "PRODUCE ", \
        "a plan is drafted on the manager's line, where it goes sealed"

    assert tab.input_value("#say") == "APPROVE p1"
    assert not errors, errors
    tab.close()


def _write_protected_room():
    """A room named by its own write key, as the lobby mints one (2.0.0)."""
    from switchboard.writekey import RoomWriteKey, generate_write_key
    seed = generate_write_key()
    return seed, RoomWriteKey.from_seed(seed).workspace


def _room_client(hub_url, agent_id, workspace, *, write_key=None):
    from switchboard.client import Client
    from switchboard.config import ClientConfig
    return Client(ClientConfig(url=hub_url, token="", workspace=workspace,
                               key=KEY, write_key=write_key), agent_id=agent_id)


def _enter(tab, hub_url, workspace, *, write_key, name):
    tab.fill("#url", hub_url)
    tab.fill("#token", "")
    tab.fill("#workspace", workspace)
    tab.fill("#key", KEY)
    tab.fill("#write_key", write_key or "")
    tab.fill("#channel", "island")
    tab.fill("#name", name)
    tab.fill("#seat", "T1")
    tab.click("#enter")


def _hub_preflights_the_write_headers(hub_url: str, origin: str) -> bool:
    """Whether this hub lets a browser send the write-key headers at all.

    agent-switchboard 2.0.0's CORS layer allows only `Authorization` and
    `Content-Type`, so a browser's preflight for `X-Switchboard-Write-Key`
    and `X-Switchboard-Write-Sig` is refused and a signed request never
    leaves the page. Found 2026-09-03; fixed in gald33/switchboard#208.
    Probed rather than pinned to a version, so the test below is a real
    check on a hub that carries the fix and an *explicit* xfail on one that
    does not -- never a skip, which would be the same green tick either way.
    """
    import httpx
    from switchboard import writekey
    answer = httpx.options(f"{hub_url}/messages", headers={
        "Origin": origin, "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers":
            f"content-type, {writekey.KEY_HEADER}, {writekey.SIG_HEADER}"})
    return answer.status_code == 200


def test_the_page_signs_its_writes_with_the_rooms_write_key(browser, island_site, cors_hub):
    """**The JS half of `RoomWriteKey.sign_request`, checked by the hub.**

    A table's room is write-protected (2026-09-03): the hub refuses any
    write the room's key did not sign. The page derives the key, the token
    and the room from the seed in the invite, signs every request over what
    goes on the wire, and the hub -- real, with the Python verifier -- lets
    its line through. A Python client on the same room reads it back.
    """
    if not _hub_preflights_the_write_headers(cors_hub, island_site):
        pytest.xfail("this hub's CORS layer refuses the write-key headers "
                     "(agent-switchboard 2.0.0); see gald33/switchboard#208")
    seed, room = _write_protected_room()
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    _enter(tab, cors_hub, room, write_key=seed, name="driver-w")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)

    rows = _room_client(cors_hub, "reader-w", room).history("island", limit=50)
    assert hands_on_board([{"body": r.get("body")} for r in rows]) == {"T1": "driven"}
    assert not errors, errors
    tab.close()


def test_a_page_without_the_write_key_is_refused_by_the_hub(browser, island_site, cors_hub):
    """The read-only invite, from the page's side: the same room, the same
    read key, no write key -- and the hub, not the page, says no."""
    seed, room = _write_protected_room()
    # Somebody with the write key has spoken, so the room is readable and
    # provably not empty.
    writer = _room_client(cors_hub, "writer-r", room, write_key=seed)
    writer.post("island", "the round is open")

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    _enter(tab, cors_hub, room, write_key=None, name="watcher-r")
    tab.wait_for_function(
        "window.HAND_READY === true || document.querySelector('.warn') !== null",
        timeout=15_000)

    rows = _room_client(cors_hub, "reader-r", room).history("island", limit=50)
    assert [r.get("body") for r in rows] == ["the round is open"], \
        "nothing the keyless page tried reached the board"
    assert "write-protected" in tab.inner_text("body"), \
        "and the page says the hub refused it rather than going quiet"
    tab.close()


# --- what this table is ----------------------------------------------------
#
# The panel a driver was going back to the lobby to read, plus the two things
# only the room can say: which day it is and what the seat is holding.

TABLE = "island-table-test"


def _table_client(hub_url, agent_id):
    from switchboard.client import Client
    from switchboard.config import ClientConfig
    return Client(ClientConfig(url=hub_url, token="", workspace=TABLE,
                               key=KEY), agent_id=agent_id)


def _a_day_in_play(*, episodes=8, seconds=90):
    """The lines a real game writes on its board through one played day.

    Driven rather than transcribed, for the reason `_real_offer_line` is: the
    panel reads the shape, the roll-call, the day, the bell and every holding
    out of these exact sentences. A manager that reworded one should fail
    here, rather than leave a driver reading a table of zeroes on a table
    that is full.

    Returns the board's lines, the `Manager` that wrote them and the `Dealer`
    that drew the island, so what the page shows is checked against the state
    the manager actually settled rather than against a number typed into this
    file.
    """
    import sys
    import time

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island import schedule
    from island.dealer import Dealer
    from island.manager import Manager
    from island.protocol import Produce

    from games.island.lobby import Table
    from games.island.run_game import who_is_at_this_table

    class _Stub:
        def __init__(self):
            self.said = []

        def post(self, channel, text):
            self.said.append(text)

        def history(self, channel, limit=500, **kw):
            return []

    dealer = Dealer.draw(seed=5, agents=2)
    mgr = Manager(capacity=dealer.capacity, client=_Stub(), channel="c")
    for name in mgr.names:
        mgr.bind(name, name)

    table = Table(id="g7", opened_by="opener", opened_at=0.0, traders=2,
                  episodes=episodes, rounds=1, goods=len(mgr.goods),
                  seconds=seconds)
    table.seats = {"peer-a": "pip", "peer-b": "robin"}
    table.keys = {"peer-a": "abc123", "peer-b": "def456"}

    lines = [who_is_at_this_table(table),
             schedule.schedule_text(episodes, mgr.names, opens_at=0.0)]
    mgr.open_episode()
    bell = time.time() + seconds
    lines.append(f"episode 2 of {episodes} is open; the bell is at "
                 f"{schedule.stamp(bell)} ({seconds}s). PRODUCE, PROPOSE and "
                 f"APPROVE all settle until the bell.")
    mgr._produce("T1", Produce(plan={mgr.goods[0]: 0.6, mgr.goods[1]: 0.4}))
    mgr._produce("T2", Produce(plan={mgr.goods[2]: 1.0}))
    lines.extend(mgr.client.said)
    return lines, mgr, dealer


def test_the_playing_page_says_what_this_table_is_and_what_the_seat_holds(
        browser, island_site, cors_hub):
    """**The lobby's card, on the page where the game is played.**

    Gal, 2026-09-08: *"the hand page is not organized and you can't even see
    your table stats as you see them in the lobby"*. The lobby's card carries
    the table's shape and who is in which seat; this page carried neither, and
    the two numbers only the room knows -- which day it is, and what this seat
    is holding -- were on no page at all. A driver could watch every receipt
    scroll past on the board and still not be able to answer "how much bread
    do I have".

    Checked against the manager's own settled state rather than against the
    text of a receipt: `mgr.holders["T1"].holdings` is what the island granted,
    and the panel has to agree with it good for good.
    """
    lines, mgr, dealer = _a_day_in_play()
    manager = _table_client(cors_hub, "manager-table")
    manager.register(name="manager", kind="local", branch="main", task="")
    for line in lines:
        manager.post("island", line)

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    _enter(tab, cors_hub, TABLE, write_key=None, name="pip")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)
    tab.wait_for_function("(window.HAND_TABLE || {}).traders?.length === 2",
                          timeout=15_000)

    shown = tab.evaluate("window.HAND_TABLE")
    assert shown["traders"] == list(mgr.names)
    assert shown["episode"] == 2 and shown["episodes"] == 8

    # **The weaker knowledge, and it says so.** Nobody has produced the last
    # good, so it has left no receipt: read off the board alone this island
    # deals three goods and not four. The panel shows the three it can see
    # and says on its own face that they are what the receipts show.
    assert shown["goodsFrom"] == "receipts"
    assert shown["goods"] == list(mgr.goods)[:-1], \
        "a good nobody has produced has left no receipt to read it from"
    assert "goods seen so far" in tab.inner_text("#tableShape")

    # The stronger one: the manager whispers this seat one capacity per good,
    # which is the whole island from the first moment of the round.
    seat_id = next(a["agent_id"] for a in manager.agents()
                   if a.get("name") == "pip")
    manager.whisper(seat_id, dealer.private_state("T1"))
    tab.wait_for_function(
        f"(window.HAND_TABLE || {{}}).goods?.length === {len(mgr.goods)}",
        timeout=15_000)
    shown = tab.evaluate("window.HAND_TABLE")
    assert shown["goodsFrom"] == "whispered"
    assert shown["goods"] == list(mgr.goods)
    assert f"{len(mgr.goods)} goods:" in tab.inner_text("#tableShape")

    # And what the seat is holding, good for good against what the island
    # actually granted -- including the good it produced none of.
    for good, qty in zip(mgr.goods, mgr.holders["T1"].holdings):
        assert shown["stocks"]["T1"][good] == pytest.approx(qty, abs=5e-4), good

    panel = tab.inner_text("#table")
    assert "Day 2 of 8" in panel, panel
    assert "the bell in " in panel, panel
    assert "2 traders" in panel, panel
    # The roll-call names the seat; a row labelled with six characters of a
    # blinded hub id is a row nobody can find themselves in.
    assert "T1 (you)" in panel and "pip" in panel, panel
    assert "robin" in panel, panel
    # Every seat, not only this one. Holdings are public -- the manager posts
    # a receipt for each -- so hiding the other seat's here would leave the
    # driver worse informed than the agent across the table.
    biggest = mgr.goods[0]
    assert f"{biggest} " in panel, panel
    assert not errors, errors
    tab.close()


def test_the_bell_counts_down_on_the_playing_page_with_no_new_line(
        browser, island_site, cors_hub):
    """**The frozen countdown, one page further on.**

    `CLAUDE.md`: the lobby's clocks all showed the number the server wrote and
    never moved, and every markup assertion around them passed. A panel that
    read the bell off the newest line would sit still through a quiet stretch
    of an open day -- which is exactly when a driver looks at it. So the
    countdown is required to *fall* while the board says nothing new, and the
    board is checked to have said nothing new.
    """
    lines, _, _dealer = _a_day_in_play(seconds=600)
    manager = _table_client(cors_hub, "manager-tick")
    manager.register(name="manager", kind="local", branch="main", task="")
    for line in lines:
        manager.post("island", line)

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    _enter(tab, cors_hub, TABLE, write_key=None, name="pip-tick")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)
    tab.wait_for_function(
        "document.getElementById('tableDay').textContent.includes('the bell in')",
        timeout=15_000)

    first = tab.inner_text("#tableDay")
    lines_before = tab.evaluate("(window.HAND_BOARD || []).length")
    tab.wait_for_function(
        f"document.getElementById('tableDay').textContent !== {first!r}",
        timeout=15_000)
    later = tab.inner_text("#tableDay")
    assert tab.evaluate("(window.HAND_BOARD || []).length") == lines_before, \
        "the clock moved because a line arrived, which is not what this checks"

    def seconds_left(text):
        stamp = text.rsplit("the bell in ", 1)[1].strip()
        minutes, secs = stamp.split(":")
        return int(minutes) * 60 + int(secs)

    assert seconds_left(later) < seconds_left(first), (first, later)
    assert not errors, errors
    tab.close()


def test_the_setup_folds_away_once_it_has_been_used(
        browser, island_site, cors_hub):
    """A form filled in once does not stay at the top of the page for the rest
    of the round. It folds, rather than disappearing, because a driver who
    mistyped a key has to be able to fix it without reloading and losing the
    room they are in.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/play.html", errors)
    assert tab.evaluate("document.getElementById('setup').open"), \
        "and it is open before it has been used, or nobody can enter"
    _enter(tab, cors_hub, TABLE, write_key=None, name="pip-fold")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)

    tab.wait_for_function(
        "document.getElementById('setup').open === false", timeout=15_000)
    # Folded, not gone: the key is still there to be corrected.
    assert tab.locator("#key").count() == 1
    tab.click("#setup > summary")
    assert tab.locator("#key").is_visible()
    assert not errors, errors
    tab.close()


# --- the kids' island ------------------------------------------------------
#
# The same room as `play.html`, behind sliders and dropdowns. Everything here
# is a thing the page *does*: compose a line from controls, show it before
# sending it, seal it to the manager, and read an offer back off the board.
# `test_hand_play_lines.py` checks the grammar those controls compose against
# the manager's real parser; this checks that the page composes from the
# controls a child actually touches, and posts what it showed.

def _kids_room(hub_url, agent_id, *, write_key=None):
    from switchboard.client import Client
    from switchboard.config import ClientConfig
    return Client(ClientConfig(url=hub_url, token="", workspace=KIDS, key=KEY,
                               write_key=write_key), agent_id=agent_id)


def _enter_kids(tab, hub_url, *, name, seat="T1", channel="island"):
    tab.fill("#url", hub_url)
    tab.fill("#token", "")
    tab.fill("#workspace", KIDS)
    tab.fill("#key", KEY)
    tab.fill("#channel", channel)
    tab.fill("#name", name)
    tab.fill("#seat", seat)
    tab.click("#enter")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)


def _real_offer_line(to="T1", maker="T2"):
    """The line a real `Manager` writes when it opens a proposal.

    Driven rather than transcribed: the page reads its offers off this text,
    and a manager that reworded it should fail here rather than leave a child
    with an empty list and no reason.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island.dealer import Dealer
    from island.manager import Manager
    from island.protocol import Produce, Propose

    class _Stub:
        def __init__(self):
            self.said = []

        def post(self, channel, text):
            self.said.append(text)

        def history(self, channel, limit=500, **kw):
            return []

    dealer = Dealer.draw(seed=1, agents=2)
    mgr = Manager(capacity=dealer.capacity, client=_Stub(), channel="c")
    for name in mgr.names:
        mgr.bind(name, name)
    mgr.open_episode()
    mgr._produce(maker, Produce(plan={mgr.goods[0]: 1.0}))
    held = mgr.holders[maker].holdings[0]
    mgr._propose(maker, Propose(to=to, give={mgr.goods[0]: held / 4},
                                want={mgr.goods[1]: held / 4}))
    return [line for line in mgr.client.said if line.startswith("p")][-1]


def test_the_kids_page_declares_the_driver_in_the_records_own_words(
        browser, site, cors_hub):
    """**The mark, and it is the same mark.**

    A younger driver is still a human driver, and there is no second word for
    one: `games/island.md` settled that a taxonomy the record cannot support
    is worse than one word that is true. So this page posts the declaration
    `play.html` posts, byte for byte, `hands_on_board` reads it back, and the
    page quotes the line it sent rather than describing it.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-1", channel="kids-declare")

    rows = _kids_room(cors_hub, "reader-kids-1").history("kids-declare", limit=50)
    assert hands_on_board([{"body": r.get("body")} for r in rows]) == {"T1": "driven"}

    banner = tab.inner_text("#humanPlay")
    assert "kept and counted" in banner and "never ranked" in banner
    assert py_declaration("T1") in tab.inner_text("#declared"), (
        "the page quotes the line it put on the board, rather than a "
        "description of one")
    assert not errors, errors
    tab.close()


def test_the_sliders_compose_a_plan_and_seal_it_to_the_manager(
        browser, site, cors_hub):
    """The one control a child will touch first, end to end.

    Two sliders, a preview that says exactly what will be sent, and a whisper
    a real Python manager opens and the real parser reads as the plan the
    sliders showed. Sealed rather than said, for the reason the manager gives
    on its own board: a plan in public states the share, the receipt states
    the quantity, and the two together are this seat's capacity.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island import protocol as economy

    manager = _kids_room(cors_hub, "manager-kids-plan")
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-plan", channel="kids-plan")

    sliders = tab.locator("#makeGrid input[type=range]")
    assert sliders.count() >= 2, "a slider for each of the island's goods"
    sliders.nth(0).fill("0.6")
    sliders.nth(1).fill("0.4")
    first = sliders.nth(0).get_attribute("data-good")
    second = sliders.nth(1).get_attribute("data-good")

    tab.wait_for_function(
        "document.getElementById('producePreview').textContent.startsWith('PRODUCE')",
        timeout=15_000)
    shown = tab.inner_text("#producePreview")
    assert shown == f"PRODUCE {first}=0.6 {second}=0.4", shown
    assert "0 of the day still free" in tab.inner_text("#labourLeft")

    tab.click("#produceSend")
    tab.wait_for_function(
        "document.getElementById('says').textContent.startsWith('Whispered')",
        timeout=15_000)

    manager.agents()
    [got] = [m for m in manager.inbox() if m.get("type") == "whisper"]
    assert got["body"] == shown, "what was sent is what the preview showed"
    plan = economy.parse(got["body"])
    assert isinstance(plan, economy.Produce)
    assert plan.plan == {first: 0.6, second: 0.4}
    board = [r.get("body")
             for r in _kids_room(cors_hub, "reader-kids-plan").history(
                 "kids-plan", limit=50)]
    assert shown not in board, "and the plan is not on the board"
    assert not errors, errors
    tab.close()


def test_a_swap_built_from_dropdowns_is_read_by_the_real_parser(
        browser, site, cors_hub):
    """`PROPOSE` is public, and the child never types a colon.

    The partner comes off the manager's own schedule line, so the dropdown
    holds real seats rather than a spelling test -- and the line that lands on
    the board is parsed here by the grammar the manager reads it with.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island import protocol as economy
    from island import schedule

    manager = _kids_room(cors_hub, "manager-kids-swap")
    manager.register(name="manager", kind="local", branch="main", task="")
    manager.post("kids-swap", schedule.schedule_text(4, ("T1", "T2"), opens_at=0.0))

    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-swap", channel="kids-swap")

    # The partner appears on its own, off the board, within one repaint.
    tab.wait_for_function(
        "document.querySelectorAll('#swapTo option')[0]?.value === 'T2'",
        timeout=15_000)
    assert tab.locator("#swapTo option").count() == 1, (
        "this seat is not offered as its own partner")

    tab.select_option("#giveGood", index=0)
    tab.select_option("#wantGood", index=1)
    tab.fill("#giveQty", "0.25")
    tab.fill("#wantQty", "0.5")
    give = tab.input_value("#giveGood")
    want = tab.input_value("#wantGood")

    shown = tab.inner_text("#proposePreview")
    assert shown == f"PROPOSE to=T2 give={give}:0.25 want={want}:0.5", shown

    tab.click("#proposeSend")
    tab.wait_for_function(
        "window.HAND_BOARD.some(r => String(r.body).startsWith('PROPOSE'))",
        timeout=15_000)

    rows = _kids_room(cors_hub, "reader-kids-swap").history("kids-swap", limit=50)
    posted = [r.get("body") for r in rows if str(r.get("body")).startswith("PROPOSE")]
    assert posted == [shown], "the board carries what the preview showed"
    offer = economy.parse(posted[0])
    assert isinstance(offer, economy.Propose)
    assert offer.to == "T2"
    assert offer.give == {give: 0.25}
    assert offer.want == {want: 0.5}
    assert not errors, errors
    tab.close()


def test_an_offer_on_the_board_becomes_a_button_that_takes_it(
        browser, site, cors_hub):
    """**The step a child cannot do by eye**: an offer's id.

    A real manager's receipt goes on the board; the page must show a button
    for the offer addressed to this seat, show the exact line it will send,
    and send that line when it is pressed.
    """
    manager = _kids_room(cors_hub, "manager-kids-offer")
    manager.register(name="manager", kind="local", branch="main", task="")
    offer = _real_offer_line(to="T1", maker="T2")
    manager.post("kids-offer", offer)

    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-offer", channel="kids-offer")

    card = tab.locator("#offers .offer")
    card.first.wait_for(timeout=15_000)
    assert card.count() == 1, tab.inner_text("#offers")
    pid = card.first.get_attribute("data-offer")
    assert offer.startswith(f"{pid}:"), (offer, pid)
    assert card.first.locator(".preview").inner_text() == f"APPROVE {pid}"

    card.first.locator("button[data-act=approve]").click()
    tab.wait_for_function(
        f"window.HAND_BOARD.some(r => r.body === 'APPROVE {pid}')", timeout=15_000)

    rows = _kids_room(cors_hub, "reader-kids-offer").history("kids-offer", limit=50)
    assert f"APPROVE {pid}" in [r.get("body") for r in rows]
    assert not errors, errors
    tab.close()


def test_an_offer_the_manager_has_settled_stops_being_a_button(
        browser, site, cors_hub):
    """The other half, and the one that matters more: a button offering a
    trade that is already done would have a child spend a day on a line the
    manager refuses, and the refusal arrives privately where they will not
    read it."""
    manager = _kids_room(cors_hub, "manager-kids-gone")
    manager.register(name="manager", kind="local", branch="main", task="")
    offer = _real_offer_line(to="T1", maker="T2")
    pid = offer.split(":", 1)[0]
    manager.post("kids-gone", offer)

    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-gone", channel="kids-gone")
    tab.locator("#offers .offer").first.wait_for(timeout=15_000)

    manager.post("kids-gone",
                 f"{pid} settled: T2 and T1 exchanged x for y")
    tab.wait_for_function(
        "document.querySelectorAll('#offers .offer').length === 0", timeout=15_000)
    assert "Nothing waiting for you" in tab.inner_text("#offers")
    assert not errors, errors
    tab.close()


def test_the_kids_page_still_posts_whatever_is_typed(browser, site, cors_hub):
    """**There is no validation gate here either.**

    Buttons are a convenience over the board and never a fence around it. A
    page that would not let its driver post a malformed line would be playing
    an easier game than the seats beside it, which is the asymmetry that made
    a validating composer wrong in the first place.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-typed", channel="kids-typed")

    tab.fill("#say", "PRODUC bread=oops")      # not a form, and posted anyway
    tab.click("#post")
    tab.wait_for_function(
        "window.HAND_BOARD.some(r => r.body === 'PRODUC bread=oops')",
        timeout=15_000)

    rows = _kids_room(cors_hub, "reader-kids-typed").history("kids-typed", limit=50)
    assert "PRODUC bread=oops" in [r.get("body") for r in rows]
    assert not errors, errors
    tab.close()


def test_the_page_refuses_to_compose_and_says_so_where_the_line_would_be(
        browser, site, cors_hub):
    """A refusal is shown in the driver's words, in the place the line would
    have been, and the button that would send it is off.

    The failure this is against is a page that shows a stale preview: the
    child reads a line, presses the button, and something else goes out.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-refuse", channel="kids-refuse")

    # Nothing on any slider: there is no plan to write, and the manager would
    # count `PRODUCE bread=0` as the day spent.
    assert tab.is_disabled("#produceSend")
    assert "pick at least one thing" in tab.inner_text("#producePreview")

    tab.locator("#makeGrid input[type=range]").nth(0).fill("0.5")
    tab.wait_for_function(
        "document.getElementById('produceSend').disabled === false", timeout=15_000)

    # And nobody has said who is at this table, so there is nobody to swap
    # with and the offer cannot be composed.
    assert tab.is_disabled("#proposeSend")
    assert "who you want to swap with" in tab.inner_text("#proposePreview")
    assert not errors, errors
    tab.close()


def test_the_private_half_is_shown_as_bars_and_never_posted(
        browser, site, cors_hub):
    """What makes the island playable by a child, and the one thing on the
    page that must not reach the board.

    The manager whispers this seat its capacities and tastes. The page draws
    them, names the island's goods from them -- so the sliders are the goods
    actually dealt rather than the whole list -- and posts none of it.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island.dealer import Dealer

    dealer = Dealer.draw(seed=1, agents=2)
    private = dealer.private_state("T1")

    manager = _kids_room(cors_hub, "manager-kids-half")
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-half", channel="kids-half")
    manager.agents()                       # this seat's exchange key
    seat_id = next(a["agent_id"] for a in manager.agents()
                   if a.get("name") == "kid-half")
    manager.whisper(seat_id, private)

    tab.wait_for_function("document.querySelectorAll('#myHalf .bar').length > 0",
                          timeout=15_000)
    assert tab.locator("#myHalf .bar").count() == 2 * len(dealer.goods), (
        "one bar per good, twice: what you make well and what you like")
    assert tab.locator("#makeGrid input[type=range]").count() == len(dealer.goods), (
        "and the sliders are the goods this island deals, off the same note")

    rows = _kids_room(cors_hub, "reader-kids-half").history("kids-half", limit=50)
    said = " ".join(str(r.get("body")) for r in rows)
    assert "capacity" not in said and "taste" not in said, (
        "nothing of the private half reached the public board")
    assert not errors, errors
    tab.close()


def test_the_page_will_not_enter_without_a_seat_to_declare(browser, site, cors_hub):
    """**The failure that would make this page the dangerous kind of weak.**

    Entering the room posts the declaration, and `declaration.DECLARED` is
    anchored: a blank seat writes `HAND:  has a human driver`, which matches
    nothing. The board would carry a line that looks like a declaration, the
    ledger would record a game between agents, and it would be ranked -- the
    weaker thing wearing the stronger thing's face, which is the one failure
    this page is not allowed to have.

    So the refusal comes before the press, and nothing is posted at all.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    tab.fill("#url", cors_hub)
    tab.fill("#token", "")
    tab.fill("#workspace", KIDS)
    tab.fill("#key", KEY)
    tab.fill("#channel", "kids-noseat")
    tab.fill("#name", "kid-noseat")
    tab.fill("#seat", "")
    tab.click("#enter")

    tab.wait_for_function(
        "document.getElementById('says').classList.contains('bad')",
        timeout=15_000)
    assert "Which seat did you take" in tab.inner_text("#says")
    assert tab.evaluate("window.HAND_READY") is not True, "it did not go in"
    rows = _kids_room(cors_hub, "reader-kids-noseat").history("kids-noseat",
                                                             limit=50)
    assert rows == [], "and nothing at all reached the board"
    assert not errors, errors
    tab.close()


def test_a_seat_the_manager_disagrees_with_is_said_out_loud(
        browser, site, cors_hub):
    """The declaration can name the wrong seat, and only the manager knows.

    Its private note opens "You are T1.", which is the one place this seat is
    told its label by somebody who knows. If it disagrees with what the page
    put on the board, the mark names a seat this driver is not in -- said
    plainly rather than corrected, because the line is already posted and a
    page that quietly fixed itself would leave it standing and unread.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island.dealer import Dealer

    manager = _kids_room(cors_hub, "manager-kids-seat")
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    tab = _tab(browser, f"{site}/kids.html", errors)
    _enter_kids(tab, cors_hub, name="kid-seat", seat="T1", channel="kids-seat")
    seat_id = next(a["agent_id"] for a in manager.agents()
                   if a.get("name") == "kid-seat")
    manager.whisper(seat_id, Dealer.draw(seed=1, agents=2).private_state("T2"))

    warning = tab.locator("#seatWarning")
    tab.wait_for_function(
        "document.getElementById('seatWarning').hidden === false", timeout=15_000)
    text = warning.inner_text()
    assert "manager says you are T2" in text
    assert "told the board you are T1" in text
    assert not errors, errors
    tab.close()


# --- the drawn island a child plays on -------------------------------------
#
# `kids-island.html` puts the controls under the model the spectator watches.
# What is checked here is the **join** between the two halves, because each
# half is already checked elsewhere and the join is what is new: the viewer's
# `Stage` and `reducer` drawing rows that came from the hand's own room, under
# controls that compose through `play_lines.js`.
#
# **The picture is read back, not assumed.** `Stage` keeps
# `preserveDrawingBuffer` precisely so a check can say the island drew rather
# than that a canvas exists -- and a canvas that exists and never drew is the
# frozen-countdown failure again, in a form no markup assertion can see.
#
# **A room per test.** `Room._findManager` takes the first roster row called
# `manager`, so a shared workspace makes which manager a whisper reaches
# depend on the order the tests happened to run in.


def _island_room(hub_url, agent_id, room):
    from switchboard.client import Client
    from switchboard.config import ClientConfig
    return Client(ClientConfig(url=hub_url, token="", workspace=room,
                               key=KEY), agent_id=agent_id)


def _enter_island(tab, hub_url, room, *, name, seat="T1", channel="island"):
    tab.fill("#url", hub_url)
    tab.fill("#token", "")
    tab.fill("#workspace", room)
    tab.fill("#key", KEY)
    tab.fill("#channel", channel)
    tab.fill("#name", name)
    tab.fill("#seat", seat)
    tab.click("#enter")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)


def _played_board(manager, channel, *, seats=("T1", "T2")):
    """A real round's opening, posted by a real client.

    Driven from `who_is_at_this_table`, `schedule_text` and a receipt in the
    manager's own words rather than written here: the reducer reads those
    words, and words nobody checks are words that drift.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island import schedule

    from games.island.lobby import Table
    from games.island.run_game import who_is_at_this_table

    table = Table(id="g7", opened_by="opener", opened_at=0.0, traders=2,
                  episodes=4, rounds=1, goods=4, seconds=60)
    table.seats = {"peer-a": "alice", "peer-b": "bob"}
    table.keys = {"peer-a": "abc", "peer-b": "def"}

    manager.post(channel, who_is_at_this_table(table))
    manager.post(channel, schedule.schedule_text(4, tuple(seats), opens_at=0.0))
    manager.post(channel, "episode 1 of 4 is open; the bell is at 23:59:59Z "
                          "(60s). PRODUCE, PROPOSE and APPROVE all settle "
                          "until the bell.")
    # And somebody has made something, so there is stock standing on the sand
    # as well as huts on it.
    manager.post(channel, "@T2 produced {'bread': 0.87, 'cloth': 0.5}; "
                          "0.0 labour unspent")


def test_the_island_is_actually_drawn_on_the_playing_page(
        browser, island_site, cors_hub):
    """**The join, and the half of it a fragment assertion cannot see.**

    The page hands `reduce` the rows the hand's own room read, and hands
    `Stage` what came back. Checked two ways, because either alone would pass
    on a broken page: the world the island was built from is read off the page
    (who has a hut, in what goods), and the canvas is read back as pixels, so
    a `Stage` that threw and left a blank rectangle fails here.
    """
    room = f"{KIDS_3D}-drawn"
    manager = _island_room(cors_hub, "manager-drawn", room)
    manager.register(name="manager", kind="local", branch="main", task="")
    _played_board(manager, "island-drawn")

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-drawn", channel="island-drawn")

    tab.wait_for_function("window.KIDS_ISLAND_WORLD?.built === true", timeout=20_000)
    world = tab.evaluate("window.KIDS_ISLAND_WORLD")
    assert world["traders"] == ["T1", "T2"], (
        "the huts carry seat labels, not six characters of a blinded id")
    assert world["goods"], world
    assert world["episode"] == 1 and world["phase"] not in ("before", "ack")

    # And the picture. `preserveDrawingBuffer` is what makes this readable;
    # a uniform canvas is one that never drew.
    drawn = tab.evaluate("""() => {
      const c = document.getElementById('island');
      if (!c.width || !c.height) return { why: 'canvas has no size' };
      const gl = c.getContext('webgl2') || c.getContext('webgl');
      if (!gl) return { why: 'no webgl' };
      const px = new Uint8Array(c.width * c.height * 4);
      gl.readPixels(0, 0, c.width, c.height, gl.RGBA, gl.UNSIGNED_BYTE, px);
      const seen = new Set();
      for (let i = 0; i < px.length; i += 4 * 97) {
        seen.add(`${px[i]},${px[i+1]},${px[i+2]},${px[i+3]}`);
      }
      return { colours: seen.size, w: c.width, h: c.height };
    }""")
    assert "why" not in drawn, drawn
    assert drawn["colours"] > 8, (
        f"the canvas is all one colour -- the island did not draw: {drawn}")
    assert not errors, errors
    tab.close()


def test_the_island_is_there_before_anybody_has_produced(
        browser, island_site, cors_hub):
    """**Day one, and the reason `reduce` is handed its goods.**

    The reducer works the goods out from the manager's receipts, which is
    right for a finished board and leaves a live one with none until somebody
    trades -- so a child opening this page at the start of the round would
    watch an empty sea until another trader moved. The page hands in the goods
    it knows instead, and there is an island to look at from the first line.
    """
    room = f"{KIDS_3D}-early"
    manager = _island_room(cors_hub, "manager-early", room)
    manager.register(name="manager", kind="local", branch="main", task="")
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island import schedule
    # The schedule alone: the seats are named, and **nothing has settled**.
    manager.post("island-early",
                 schedule.schedule_text(4, ("T1", "T2"), opens_at=0.0))

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-early", channel="island-early")

    tab.wait_for_function("window.KIDS_ISLAND_WORLD?.built === true", timeout=20_000)
    world = tab.evaluate("window.KIDS_ISLAND_WORLD")
    assert world["traders"] == ["T1", "T2"]
    assert world["goods"], "an island with no goods on it is no island"
    assert not errors, errors
    tab.close()


def test_the_playing_island_declares_the_driver_like_every_other_hand_page(
        browser, island_site, cors_hub):
    """Same room, same declaration, same mark. A page that drew a prettier
    island and declared nothing would be the ranked game this whole design is
    arranged against."""
    room = f"{KIDS_3D}-declare"
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-idrv", channel="island-declare")

    rows = _island_room(cors_hub, "reader-idrv", room).history("island-declare",
                                                               limit=50)
    assert hands_on_board([{"body": r.get("body")} for r in rows]) == {"T1": "driven"}
    assert py_declaration("T1") in tab.inner_text("#declared")
    assert "never ranked" in tab.inner_text("#humanPlay")
    assert not errors, errors
    tab.close()


def test_the_playing_island_will_not_enter_without_a_seat(
        browser, island_site, cors_hub):
    """The guard travels with the declaration, not with the page: a blank seat
    writes a line the record cannot read, whichever page wrote it."""
    room = f"{KIDS_3D}-noseat"
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    tab.fill("#url", cors_hub)
    tab.fill("#token", "")
    tab.fill("#workspace", room)
    tab.fill("#key", KEY)
    tab.fill("#channel", "island-noseat")
    tab.fill("#name", "kid-inoseat")
    tab.fill("#seat", "")
    tab.click("#enter")

    tab.wait_for_function(
        "document.getElementById('says').classList.contains('bad')", timeout=15_000)
    assert "Which seat did you take" in tab.inner_text("#says")
    assert tab.evaluate("window.HAND_READY") is not True
    assert _island_room(cors_hub, "reader-inoseat", room).history(
        "island-noseat", limit=50) == [], "nothing reached the board"
    assert not errors, errors
    tab.close()


def test_an_offer_the_manager_opened_becomes_a_button_on_the_island(
        browser, island_site, cors_hub):
    """Offers come off `reduce`'s proposals here rather than off a scrape.

    That is the point of drawing this page on the viewer's reducer: the
    proposals it keeps are the ones the manager's receipts built, read the
    same way the spectator's page reads them, so there is one reading of the
    board on this page and not two.
    """
    room = f"{KIDS_3D}-offer"
    manager = _island_room(cors_hub, "manager-ioffer", room)
    manager.register(name="manager", kind="local", branch="main", task="")
    _played_board(manager, "island-offer")
    offer = _real_offer_line(to="T1", maker="T2")
    pid = offer.split(":", 1)[0]
    manager.post("island-offer", offer)

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-ioffer", channel="island-offer")

    card = tab.locator("#offers .offer")
    card.first.wait_for(timeout=20_000)
    assert card.first.get_attribute("data-offer") == pid
    assert card.first.locator(".preview").inner_text() == f"APPROVE {pid}"
    assert "T2 offers you" in card.first.inner_text(), (
        "and it says what the swap is, which a proposal id cannot")

    card.first.locator("button[data-act=approve]").click()
    tab.wait_for_function(
        f"window.HAND_BOARD.some(r => r.body === 'APPROVE {pid}')", timeout=15_000)
    rows = _island_room(cors_hub, "reader-ioffer", room).history("island-offer",
                                                                 limit=50)
    assert f"APPROVE {pid}" in [r.get("body") for r in rows]
    assert not errors, errors
    tab.close()


def test_the_button_to_the_real_viewer_carries_this_room(
        browser, island_site, cors_hub):
    """The way out, and the reason this page is allowed to be narrow: it does
    not have to grow a replay player, because the page that has one is one
    button away and this hands it the room."""
    room = f"{KIDS_3D}-view"
    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    assert tab.locator("#toViewer").is_hidden(), (
        "no way out of a room this page is not in yet")
    _enter_island(tab, cors_hub, room, name="kid-iview", channel="island-view")

    tab.wait_for_selector("#toViewer:not([hidden])", timeout=15_000)
    with tab.context.expect_page() as opened:
        tab.click("#toViewer")
    spectator = opened.value
    query = dict(urllib.parse.parse_qsl(spectator.url.split("?", 1)[1]))
    assert spectator.url.split("?")[0].endswith("/index.html"), spectator.url
    assert query["workspace"] == room
    assert query["key"] == KEY
    # A new tab on purpose: a child who followed it in this one would have
    # left the game, and the bell does not wait.
    assert tab.url.endswith("kids-island.html"), "the game is still open here"
    spectator.close()
    assert not errors, errors
    tab.close()


def test_the_sliders_still_seal_a_plan_to_the_manager_from_the_island(
        browser, island_site, cors_hub):
    """The controls are the same controls, on a page that draws. Checked here
    rather than assumed from `kids.html`: they are wired to a different shell,
    and a shell that failed to bind them would look identical."""
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island import protocol as economy

    room = f"{KIDS_3D}-plan"
    manager = _island_room(cors_hub, "manager-iplan", room)
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-iplan", channel="island-plan")

    tab.locator("#makeGrid input[type=range]").nth(0).fill("0.7")
    tab.wait_for_function(
        "document.getElementById('producePreview').textContent.startsWith('PRODUCE')",
        timeout=15_000)
    shown = tab.inner_text("#producePreview")
    tab.click("#produceSend")
    tab.wait_for_function(
        "document.getElementById('says').textContent.startsWith('Whispered')",
        timeout=15_000)

    manager.agents()
    [got] = [m for m in manager.inbox() if m.get("type") == "whisper"]
    assert got["body"] == shown
    assert isinstance(economy.parse(got["body"]), economy.Produce)
    board = [r.get("body") for r in _island_room(
        cors_hub, "reader-iplan", room).history("island-plan", limit=50)]
    assert shown not in board, "the plan stayed off the board"
    assert not errors, errors
    tab.close()


# --- what the pages show, as opposed to what they send ---------------------
#
# Three defects, all visible in one screenshot of `kids-island.html` taken
# against a real hub on 2026-09-07, and all of them presentation rather than
# play: the composed lines were right the whole time. That is exactly why
# nothing already here caught them -- every check asserted on what went to the
# board, and these are about what came back to the reader.
#
# `test_hand_play_lines.py` pins the decisions (`amount`, `notes`); these pin
# that the pages actually use them, which is the half a pure test cannot see.


def test_an_offer_reads_in_numbers_a_child_can_read(browser, island_site, cors_hub):
    """**The line that was on the page**: "T2 offers you 0.12428327472728834
    iron for 0.12428327472728834 bread".

    A real manager's proposal carries an unrounded float, and the card printed
    it. What the button sends is unchanged and is asserted alongside, because
    that is the property making the rounding safe: `APPROVE p1` carries an id
    and no quantity, so the manager settles the offer it holds whatever the
    card says.
    """
    room = f"{KIDS_3D}-reads"
    manager = _island_room(cors_hub, "manager-reads", room)
    manager.register(name="manager", kind="local", branch="main", task="")
    _played_board(manager, "island-reads")
    offer = _real_offer_line(to="T1", maker="T2")
    pid = offer.split(":", 1)[0]
    manager.post("island-reads", offer)

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-reads", channel="island-reads")

    card = tab.locator("#offers .offer")
    card.first.wait_for(timeout=20_000)
    said = card.first.inner_text()

    assert "0.12428327472728834" not in said, said
    import re as _re
    long = _re.findall(r"\d+\.\d{4,}", said)
    assert not long, f"a quantity nobody can read is still on the card: {long}"
    assert _re.search(r"\d", said), "and it still says how much"

    # The line under it is untouched, and so is what lands on the board.
    assert card.first.locator(".preview").inner_text() == f"APPROVE {pid}"
    card.first.locator("button[data-act=approve]").click()
    tab.wait_for_function(
        f"window.HAND_BOARD.some(r => r.body === 'APPROVE {pid}')", timeout=15_000)
    rows = _island_room(cors_hub, "reader-reads", room).history("island-reads",
                                                                limit=50)
    assert f"APPROVE {pid}" in [r.get("body") for r in rows]
    assert not errors, errors
    tab.close()


def _half_and_notes(browser, site, cors_hub, room, channel, page, name):
    """Enter, get whispered the private half and a refusal, and hand back what
    the notes panel ended up showing."""
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island.dealer import Dealer

    manager = _island_room(cors_hub, f"manager-{name}", room)
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    tab = _tab(browser, f"{site}/{page}", errors)
    tab.fill("#url", cors_hub)
    tab.fill("#token", "")
    tab.fill("#workspace", room)
    tab.fill("#key", KEY)
    tab.fill("#channel", channel)
    tab.fill("#name", name)
    tab.fill("#seat", "T1")
    tab.click("#enter")
    tab.wait_for_function("window.HAND_READY === true", timeout=20_000)

    seat_id = next(a["agent_id"] for a in manager.agents() if a.get("name") == name)
    manager.whisper(seat_id, Dealer.draw(seed=1, agents=2).private_state("T1"))
    manager.whisper(seat_id, "not settled: shares sum to 1.8, over the budget "
                             "of 1.0 by 0.8")

    tab.wait_for_function(
        "document.querySelectorAll('#myHalf .bar').length > 0", timeout=20_000)
    tab.wait_for_function(
        "document.getElementById('whispers').textContent.includes('not settled')",
        timeout=20_000)
    return tab, errors


def test_the_private_half_is_not_printed_under_its_own_bars(
        browser, island_site, cors_hub):
    """It was shown twice: as the bars, and again as the manager's raw Python
    dict repr underneath. The bars exist so a child does not have to read
    that."""
    tab, errors = _half_and_notes(browser, island_site, cors_hub,
                                  f"{KIDS_3D}-notes", "island-notes",
                                  "hand/kids-island.html", "kid-notes")

    shown = tab.inner_text("#whispers")
    assert "production capacity" not in shown, shown
    assert "taste weights" not in shown
    assert tab.locator("#myHalf .bar").count() > 0, "and the bars are what says it"
    # The refusal is still there, which is the thing that must not be tidied
    # away: a refusal a child does not see is a day they do not know they lost.
    assert "not settled" in shown

    # **And `room` is writing somewhere else**, asserted structurally rather
    # than by what is on screen. Both renderers can reach `#whispers`, and
    # this page repaints every second, so pointing `room` back at it leaves a
    # page that merely *flickers* between the two renderings -- which a
    # snapshot of the text cannot see, and which passed this check until it
    # was written this way.
    raw = tab.evaluate(
        "document.getElementById('rawWhispers')?.textContent || ''")
    assert "production capacity" in raw, (
        "room.js renders into the hidden element, so the visible list is this "
        "page's alone")
    assert tab.locator("#rawWhispers").is_hidden()
    assert not errors, errors
    tab.close()


def test_a_note_that_could_not_be_opened_is_said_in_words(
        browser, island_site, cors_hub):
    """It rendered as `{"unreadable":"could not open the value at
    whisper.body: ..."}`.

    Produced here the way it really happens rather than by injecting one: a
    second browser context is a second IndexedDB, so the same name mints a new
    key, the roster row is replaced, and a whisper sealed to the first key
    cannot be opened by the second. That is a real key mismatch, which is
    exactly the case the words have to explain.
    """
    import sys

    island = (pathlib.Path(__file__).resolve().parents[3]
              / "experiments" / "005-deliberation-protocol")
    if str(island) not in sys.path:
        sys.path.insert(0, str(island))
    from island.dealer import Dealer

    room = f"{KIDS_3D}-unreadable"
    manager = _island_room(cors_hub, "manager-unreadable", room)
    manager.register(name="manager", kind="local", branch="main", task="")

    errors: list[str] = []
    first = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(first, cors_hub, room, name="twinned",
                  channel="island-unreadable")
    seat_id = next(a["agent_id"] for a in manager.agents()
                   if a.get("name") == "twinned")
    manager.whisper(seat_id, Dealer.draw(seed=1, agents=2).private_state("T1"))
    first.close()

    # A second context under the same name: a new key, and the note above is
    # now sealed to somebody this page cannot be.
    other = browser.new_context()
    tab = other.new_page()
    tab.on("pageerror", lambda e: errors.append(str(e)))
    tab.goto(f"{island_site}/hand/kids-island.html")
    _enter_island(tab, cors_hub, room, name="twinned",
                  channel="island-unreadable")

    tab.wait_for_function(
        "document.querySelector('#whispers .unreadable') !== null", timeout=20_000)
    said = tab.inner_text("#whispers .unreadable")

    assert "could not open" in said
    assert "browser" in said, "and why, in something a person can act on"
    assert not said.strip().startswith("{"), f"still the raw object: {said}"
    assert not errors, errors
    other.close()


def test_the_board_page_says_its_notes_the_same_way(browser, site, cors_hub):
    """`kids.html` had both defects too -- the same `room.js` renderer, the
    same audience. Fixed in one place, so it is checked in both."""
    tab, errors = _half_and_notes(browser, site, cors_hub,
                                  f"{KIDS}-notes", "kids-notes",
                                  "kids.html", "kid-bnotes")

    shown = tab.inner_text("#whispers")
    assert "production capacity" not in shown, shown
    assert "not settled" in shown
    assert tab.locator("#myHalf .bar").count() > 0
    assert not errors, errors
    tab.close()


def test_the_nav_between_the_playing_pages_carries_the_room(
        browser, island_site, cors_hub):
    """**They used to carry nothing at all.**

    Clicking "the same game without the picture" mid-round dropped the
    workspace, the key and the seat, and landed on an empty form with the bell
    still running -- and the only way back to the invite was the lobby page in
    the browser that joined. Followed for real here rather than asserted on an
    `href`, because what matters is the page you arrive at.
    """
    room = f"{KIDS_3D}-nav"
    manager = _island_room(cors_hub, "manager-nav", room)
    manager.register(name="manager", kind="local", branch="main", task="")
    _played_board(manager, "island-nav")

    errors: list[str] = []
    tab = _tab(browser, f"{island_site}/hand/kids-island.html", errors)
    _enter_island(tab, cors_hub, room, name="kid-nav", channel="island-nav")

    tab.click("#toKids")
    tab.wait_for_url("**/kids.html?*", timeout=15_000)
    query = dict(urllib.parse.parse_qsl(tab.url.split("?", 1)[1]))
    assert query["workspace"] == room
    assert query["key"] == KEY
    assert query["seat"] == "T1"
    assert query["name"] == "kid-nav"
    assert query["channel"] == "island-nav"

    # And the page it lands on is ready to play, not a blank form: the fields
    # are filled and the grown-up fold is shut, which is the whole point.
    assert tab.input_value("#workspace") == room
    assert tab.input_value("#seat") == "T1"
    assert not tab.locator("#setup").get_attribute("open"), \
        "arriving with a room means the setup fold is shut"

    # Back again, still carrying it.
    tab.click("#toIsland")
    tab.wait_for_url("**/kids-island.html?*", timeout=15_000)
    assert dict(urllib.parse.parse_qsl(
        tab.url.split("?", 1)[1]))["workspace"] == room
    assert not errors, errors
    tab.close()
