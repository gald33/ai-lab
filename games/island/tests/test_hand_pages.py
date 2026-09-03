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

import pytest

from games.island.hand.brief import brief as py_brief
from games.island.hand.declaration import declaration as py_declaration
from games.island.hand.declaration import hands_on_board

HAND = pathlib.Path(__file__).resolve().parent.parent / "hand"
WORKSPACE = "island-hand-test"
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
    """The hand's pages, served. Copied rather than served in place, so what
    runs is the committed bytes and nothing beside them."""
    root = tmp_path_factory.mktemp("hand-site")
    for name in ("lobby.html", "play.html", "switchboard.js", "hub.js",
                 "identity.js", "lobby_lines.js", "declaration.js", "brief.js"):
        shutil.copy(HAND / name, root / name)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def cors_hub(site, tmp_path_factory):
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
    app = create_app(ServerConfig(db_path=store.path, cors_origins=(site,)),
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


# --- the island ------------------------------------------------------------

def test_entering_the_room_declares_the_driver_without_being_asked(
        browser, site, cors_hub):
    """**The mechanism by which declarations happen at all.**

    Nobody can be made to declare -- an open room means a person can drive a
    seat in silence and nothing notices. What can be done is to make declaring
    the thing that happens when the page is used, and that is this: entering
    the room posts the line, and `hands_on_board` reads it back off the board
    the same way the record will.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/play.html", errors)
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


def test_the_island_page_posts_whatever_is_typed(browser, site, cors_hub):
    """**There is no validation gate, on purpose.**

    An agent at the table can post a malformed line and lose the exchange; the
    manager never repairs one. A page that refused to let its driver do the
    same would be playing an easier game than the seats beside it -- which is
    the asymmetry that made a validating composer wrong in the first place.
    """
    errors: list[str] = []
    tab = _tab(browser, f"{site}/play.html", errors)
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


def test_a_shortcut_button_fills_the_bar_and_does_not_post(browser, site):
    """The buttons are a convenience over the input bar and never a second
    path to the board: what they do is put text where the driver can see and
    edit it before pressing."""
    errors: list[str] = []
    tab = _tab(browser, f"{site}/play.html", errors)
    tab.click("[data-fill='APPROVE p1']")

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


def test_the_page_signs_its_writes_with_the_rooms_write_key(browser, site, cors_hub):
    """**The JS half of `RoomWriteKey.sign_request`, checked by the hub.**

    A table's room is write-protected (2026-09-03): the hub refuses any
    write the room's key did not sign. The page derives the key, the token
    and the room from the seed in the invite, signs every request over what
    goes on the wire, and the hub -- real, with the Python verifier -- lets
    its line through. A Python client on the same room reads it back.
    """
    if not _hub_preflights_the_write_headers(cors_hub, site):
        pytest.xfail("this hub's CORS layer refuses the write-key headers "
                     "(agent-switchboard 2.0.0); see gald33/switchboard#208")
    seed, room = _write_protected_room()
    errors: list[str] = []
    tab = _tab(browser, f"{site}/play.html", errors)
    _enter(tab, cors_hub, room, write_key=seed, name="driver-w")
    tab.wait_for_function("window.HAND_READY === true", timeout=15_000)

    rows = _room_client(cors_hub, "reader-w", room).history("island", limit=50)
    assert hands_on_board([{"body": r.get("body")} for r in rows]) == {"T1": "driven"}
    assert not errors, errors
    tab.close()


def test_a_page_without_the_write_key_is_refused_by_the_hub(browser, site, cors_hub):
    """The read-only invite, from the page's side: the same room, the same
    read key, no write key -- and the hub, not the page, says no."""
    seed, room = _write_protected_room()
    # Somebody with the write key has spoken, so the room is readable and
    # provably not empty.
    writer = _room_client(cors_hub, "writer-r", room, write_key=seed)
    writer.post("island", "the round is open")

    errors: list[str] = []
    tab = _tab(browser, f"{site}/play.html", errors)
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
