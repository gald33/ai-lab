"""`lobby-web/start.js`'s levers against `lobby_page.py`'s, which define them.

**This check is the whole reason the bug it was written for was possible.**
`lobby-web/` is a hand port of `lobby_page.py` for the static origin the lobby
is actually served from, and nothing compared the two. So when `TRADERS_MAX`
came down to 4 and `GOODS_MAX` to 5 in `protocol.py`, the Python page followed
and the port did not: `lobby-web/protocol.js` kept 8 and 12, and `start.js`
kept its own *third* copy of those numbers -- re-declared locally under a
comment claiming they came from `protocol.js`.

The result is the exact trap the levers exist to avoid, on the one copy of the
page a stranger loads: it offered 8 traders and 12 goods, rewrote the OPEN line
with them, and left the reader's agent to have its OPEN come back Malformed.
Every test in the suite passed throughout, because every one of them read the
Python.

So the port is checked against the Python it ports, in a browser, the way
`test_hand_lobby_lines.py` checks the hand's composer against `protocol.py`.
The rule both follow: **a second implementation is never compared against its
own idea of what it should produce.**

    python -m pytest games/island/tests/test_lobby_web_levers.py -q
"""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from games.island import lobby_page, protocol
from games.island.tests.test_hand_lobby_lines import _serve

WEB = pathlib.Path(__file__).resolve().parent.parent / "lobby-web"

#: The port's modules the levers need, copied beside a page that imports them.
#: `config.js` comes along because `start.js` imports it for the prompt.
MODULES = ("start.js", "protocol.js", "config.js")

_PAGE = """<!doctype html><meta charset=utf-8><title>levers</title>
<script type=module>
import { LEVERS, OPEN_DEFAULTS, openLine } from './start.js';
import { TRADERS_MIN, TRADERS_MAX, GOODS_MIN, GOODS_MAX, ROUNDS_MAX }
  from './protocol.js';
window.RESULT = {
  levers: LEVERS,
  defaults: OPEN_DEFAULTS,
  line: openLine(),
  bounds: { TRADERS_MIN, TRADERS_MAX, GOODS_MIN, GOODS_MAX, ROUNDS_MAX },
};
</script>
"""


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no lever at all")
    pytest.skip(why)


@pytest.fixture(scope="module")
def ported(tmp_path_factory):
    """What the port's own modules say, read by a browser that ran them."""
    tmp_path = tmp_path_factory.mktemp("lobby-web-levers")
    try:
        from playwright import sync_api as play  # noqa: PLC0415
    except ImportError:
        _missing("no playwright to drive a page with")

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    for name in MODULES:
        (tmp_path / name).write_text((WEB / name).read_text())
    (tmp_path / "levers.html").write_text(_PAGE)
    server = _serve(tmp_path)
    url = f"http://127.0.0.1:{server.server_address[1]}/levers.html"

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


def test_the_ports_bounds_are_the_protocols_bounds(ported):
    """A number copied into a second file is a number that will go stale."""
    assert ported["bounds"] == {
        "TRADERS_MIN": protocol.TRADERS_MIN, "TRADERS_MAX": protocol.TRADERS_MAX,
        "GOODS_MIN": protocol.GOODS_MIN, "GOODS_MAX": protocol.GOODS_MAX,
        "ROUNDS_MAX": protocol.ROUNDS_MAX,
    }


def test_the_port_offers_exactly_the_levers_the_python_page_does(ported):
    """Same knobs, same labels, same rungs, same order.

    Order included: the levers read as a row and the Python page is what the
    row is specified by, so a port that shuffles them is a port that drifted.
    """
    assert [[f, label, list(values)] for f, label, values in lobby_page.LEVERS] \
        == [list(row[:2]) + [list(row[2])] for row in ported["levers"]]


def test_the_ports_open_line_is_the_python_pages(ported):
    """The line the reader copies, from both implementations."""
    assert ported["line"] == lobby_page.open_line()
    assert ported["defaults"] == {k: v for k, v in
                                  lobby_page.OPEN_DEFAULTS.items()}


def test_every_value_the_ports_levers_offer_is_a_line_the_lobby_parses(ported):
    """The check that bites even if both implementations drift together."""
    for field, _label, values in ported["levers"]:
        for v in values:
            protocol.parse(lobby_page.open_line(**{field: v}))


def test_rounds_is_not_a_knob_on_the_port_either(ported):
    """`ROUNDS_MAX` is 1, so the select offered a choice nobody has."""
    assert "rounds" not in [row[0] for row in ported["levers"]]
    assert "rounds=1" in ported["line"], json.dumps(ported["line"])
