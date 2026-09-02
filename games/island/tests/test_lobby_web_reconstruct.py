"""`lobby-web/lobby.js` against the lines a real lobby actually posts.

**The bug this was written for.** `lobby.py` names its tables `g1`, `g2`, ...
(`Table(id=f"g{self._next}")`), and every pattern in the port demanded
`T\\d+`. So against the live lobby the page matched nothing: the board showed
`g18 is forming`, seats filling and a settlement, and the page showed no
table at all. Nothing caught it, because the only lines the port was ever read
against were the ones `fixture.html` invented -- and it invented `T1`.

That is the same trap `test_lobby_web_levers.py` exists for one file over:
**a second implementation is never compared against its own idea of what it
should produce.** So this drives the port's `reconstruct` in a browser over
the exact bodies a `Lobby` posted to a real hub -- ids, seat labels, counts
and settlement wording all the Python's, none of them written here.

    python -m pytest games/island/tests/test_lobby_web_reconstruct.py -q
"""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from games.island.lobby import Lobby
from games.island.tests.test_hand_lobby_lines import _serve

WEB = pathlib.Path(__file__).resolve().parent.parent / "lobby-web"

#: What `lobby.js` imports, beside a page that imports it.
MODULES = ("lobby.js", "protocol.js")

WORKSPACE = "w_lobby-web-reconstruct"

_PAGE = """<!doctype html><meta charset=utf-8><title>reconstruct</title>
<script type=module>
import { reconstruct } from './lobby.js';
const snapshot = await (await fetch('./board.json')).json();
window.RESULT = reconstruct(snapshot, 'lobby');
</script>
"""


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"read no lobby line at all")
    pytest.skip(why)


def _client(hub, agent_id, key):
    return Client(ClientConfig(url=hub, url_source="explicit",
                               workspace=WORKSPACE, key=key), agent_id=agent_id)


@pytest.fixture
def board(hub):
    """A real table, opened, seated, managed and settled -- and its lines."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)

    seats = []
    for name in ("t1", "t2"):
        entrant = _client(hub, name, key)
        entrant.register(name=name, kind="local", branch="main", task="")
        seats.append(entrant)
    manager = _client(hub, "manager-claim", key)
    manager.register(name="lucille", kind="local", branch="main", task="")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    table_id = next(iter(lobby.tables))
    seats[0].post("lobby", f"JOIN {table_id} as scout-v2")
    seats[1].post("lobby", f"JOIN {table_id} as trader-b")
    lobby.drain()
    manager.post("lobby", f"MANAGE {table_id}")
    lobby.drain()

    rows = [{"channel": "lobby", "from": m.get("from", ""),
             "created_at": m.get("created_at", ""), "body": m["body"]}
            for m in lobby.client.history("lobby")]
    return {"id": table_id, "table": lobby.tables[table_id], "rows": rows}


@pytest.fixture
def viewed(board, tmp_path_factory):
    """What the port made of those lines, read by a browser that ran it."""
    tmp_path = tmp_path_factory.mktemp("lobby-web-reconstruct")
    try:
        from playwright import sync_api as play  # noqa: PLC0415
    except ImportError:
        _missing("no playwright to drive a page with")

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    for name in MODULES:
        (tmp_path / name).write_text((WEB / name).read_text())
    (tmp_path / "board.json").write_text(
        json.dumps({"messages": board["rows"], "agents": []}))
    (tmp_path / "reconstruct.html").write_text(_PAGE)
    server = _serve(tmp_path)
    url = f"http://127.0.0.1:{server.server_address[1]}/reconstruct.html"

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
        try:
            tab.wait_for_function("window.RESULT !== undefined", timeout=15_000)
        except Exception as exc:                       # noqa: BLE001
            browser.close()
            server.shutdown()
            pytest.fail(f"the module never ran: {exc!r}; page errors: {errors}")
        result = tab.evaluate("window.RESULT")
        browser.close()
    server.shutdown()
    return result


def test_the_port_sees_the_table_the_lobby_named(viewed, board):
    """The failure itself: `g18` on the board, nothing on the page."""
    ids = [t["id"] for t in viewed["tables"]]
    assert ids == [board["id"]], json.dumps(viewed["tables"])


def test_the_port_reads_the_forming_line_the_lobby_wrote(viewed, board):
    table = viewed["tables"][0]
    assert (table["traders"], table["episodes"], table["rounds"]) == (
        board["table"].traders, board["table"].episodes, board["table"].rounds)
    assert table["commit"]


def test_the_port_reads_every_seat_and_the_manager(viewed, board):
    table = viewed["tables"][0]
    assert [s["label"] for s in table["seats"]] == ["T1", "T2"]
    assert [s["name"] for s in table["seats"]] == ["scout-v2", "trader-b"]
    assert table["manager"] == board["table"].manager


def test_the_port_reads_the_settlement(viewed, board):
    """`opens` is a bare `19:40:00Z`, and the port has to make a time of it.

    Read with `Date.parse` it was NaN, so every settled table the live lobby
    announced arrived here with no start time at all.
    """
    table = viewed["tables"][0]
    assert table["settled"] and not table["lapsed"]
    assert table["opens_at"] == pytest.approx(board["table"].opens_at, abs=1)
    assert "scout-v2" in table["roster"] and "trader-b" in table["roster"]


def test_the_port_never_carries_an_invite_into_the_view(viewed):
    """A room credential is on that channel and must not reach the page.

    Asserted over a view that has a table in it: a port that saw no table at
    all would carry no credential either, and pass this for the wrong reason.
    """
    assert viewed["tables"]
    assert "swb1_" not in json.dumps(viewed)
