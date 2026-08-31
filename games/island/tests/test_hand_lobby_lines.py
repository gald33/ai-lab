"""`lobby_lines.js` against `protocol.py`, which defines the grammar.

**The buttons are a second implementation and could not be anything else.**
The hand's lobby is JavaScript on a static origin and cannot call Python, so
`games/island.md`'s original rule -- a composer emits through `protocol.py` --
was unbuildable. This is what replaced it, and it is the same answer the
cryptography got: the JS composes, the real parser reads, and neither half is
ever compared against its own idea of what it should produce.

**Agreement is checked in both directions**, because the two ways to drift are
opposite and both silent:

- a line the buttons compose that Python refuses loses a driver their table,
  with no error anybody sees until the lobby says nothing back;
- an input the buttons refuse that Python would have accepted shrinks the game
  for no reason, and nothing anywhere would notice.

So every case below is run through the browser *and* through `protocol.parse`,
and the two must agree on whether it is a line at all -- and, when it is, on
what it means.

Run it here with a browser installed, or in the `drawing-quick` CI job, which
has one and sets `ISLAND_REQUIRE_BROWSER` -- a skip and a pass are the same
tick.

    python -m pytest games/island/tests/test_hand_lobby_lines.py -q
"""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from games.island import protocol

HAND = pathlib.Path(__file__).resolve().parent.parent / "hand"

#: A nonce shaped the way `protocol.NONCE` wants, fixed so a failure is
#: quotable rather than different every run.
NONCE = "0123456789abcdef"

#: What the buttons are asked to compose. Each case is `(kind, arguments)`,
#: and deliberately not a list of things that work: the awkward ones are the
#: point, since a grammar only drifts where nobody looks.
CASES = [
    # --- OPEN, inside the bounds ------------------------------------------
    ("open", {"traders": 2, "episodes": 8}),
    ("open", {"traders": 4, "episodes": 1, "goods": 2, "seconds": 15}),
    ("open", {"traders": 3, "episodes": 20, "goods": 5, "seconds": 300}),
    # Strings, because an <input> hands the page a string and never a number.
    ("open", {"traders": "2", "episodes": "8"}),
    ("open", {"traders": " 2 ", "episodes": "8"}),
    # --- OPEN, outside them -----------------------------------------------
    ("open", {"traders": 0, "episodes": 8}),
    ("open", {"traders": 1, "episodes": 8}),
    ("open", {"traders": 5, "episodes": 8}),
    ("open", {"traders": -1, "episodes": 8}),
    ("open", {"traders": 2, "episodes": 0}),
    ("open", {"traders": 2, "episodes": -3}),
    ("open", {"traders": 2, "episodes": 8, "goods": 1}),
    ("open", {"traders": 2, "episodes": 8, "goods": 6}),
    ("open", {"traders": 2, "episodes": 8, "rounds": 0}),
    # The field that parsed, was announced, and was never played.
    ("open", {"traders": 2, "episodes": 8, "rounds": 3}),
    # A rung close to a real one is exactly what somebody will guess.
    ("open", {"traders": 2, "episodes": 8, "seconds": 61}),
    ("open", {"traders": 2, "episodes": 8, "seconds": 0}),
    ("open", {"traders": 2, "episodes": 8, "seconds": 600}),
    # Not integers at all.
    ("open", {"traders": "two", "episodes": 8}),
    ("open", {"traders": 2.5, "episodes": 8}),
    ("open", {"traders": "", "episodes": 8}),
    ("open", {"traders": "2x", "episodes": 8}),
    # --- JOIN, inside the bounds ------------------------------------------
    ("join", {"table": "g7", "name": "scout-v2", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "a", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "a" * 32, "nonce": NONCE}),
    ("join", {"table": "g7", "name": "dot.name_9-x", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "scout", "nonce": "f" * 64}),
    # --- JOIN, outside them -----------------------------------------------
    # A name with a space in it: the one an unwary composer splits on.
    ("join", {"table": "g7", "name": "scout v2", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "a" * 33, "nonce": NONCE}),
    ("join", {"table": "g7", "name": "", "nonce": NONCE}),
    # The manager's own vocabulary.
    ("join", {"table": "g7", "name": "T1", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "t2", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "manager", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "lobby", "nonce": NONCE}),
    # A name that would smuggle a second field in.
    ("join", {"table": "g7", "name": "x nonce=deadbeefdeadbeef", "nonce": NONCE}),
    ("join", {"table": "g7", "name": "x\nJOIN g8 as y", "nonce": NONCE}),
    # A name that is only spaces: splits to nothing, so an unwary composer
    # writes `JOIN g7 as  nonce=...` and the parser reads the nonce as a name.
    ("join", {"table": "g7", "name": "   ", "nonce": NONCE}),
    # Nonces that are not nonces.
    ("join", {"table": "g7", "name": "scout", "nonce": "short"}),
    ("join", {"table": "g7", "name": "scout", "nonce": "z" * 16}),
    ("join", {"table": "g7", "name": "scout", "nonce": ""}),
    ("join", {"table": "g7", "name": "scout", "nonce": "f" * 65}),
    # A table id that is not one.
    ("join", {"table": "", "name": "scout", "nonce": NONCE}),
    ("join", {"table": "g 7", "name": "scout", "nonce": NONCE}),
]


#: Inputs the page refuses that `protocol.parse` would have accepted -- and
#: where the page is right and the parser is loose.
#:
#: **There is exactly one shape of these, and it is a finding rather than a
#: convenience.** `parse` strips `key=value` pairs off the end of a JOIN while
#: more than three words remain, so a *name* containing `nonce=<hex>` puts a
#: second nonce on the line and the parser silently takes one of the two:
#:
#:     JOIN g7 as x nonce=aaaa... nonce=bbbb...
#:     -> Join(table='g7', name='x', nonce='aaaa...')
#:
#: The name that arrives is not the name that was written, and a line carrying
#: two nonces settles as though it carried one. That is a malformed message
#: being repaired into a plausible one, which `CLAUDE.md` forbids the system
#: to do -- so the page refuses the input rather than composing a line whose
#: meaning it cannot predict.
#:
#: Listed here rather than quietly excluded, so that the asymmetry is visible
#: and so this check still bites for every other case. If `protocol.parse`
#: ever refuses duplicate fields, this list empties and the entry can go.
STRICTER_ON_PURPOSE = {
    ("join", json.dumps({"table": "g7", "name": "x nonce=deadbeefdeadbeef",
                         "nonce": NONCE}, sort_keys=True)),
    ("join", json.dumps({"table": "g7", "name": "   ", "nonce": NONCE},
                        sort_keys=True)),
}


def test_the_parser_accepts_a_join_that_smuggles_a_second_nonce(composed):
    """**A defect in `protocol.py`, pinned here because this test found it.**

    Not the page's bug and not fixed by this change: the lobby's grammar is
    used by every entrant, and quietly tightening it in a change about the
    hand's pages would be exactly the kind of drive-by nobody asked for. What
    this test does is stop it being rediscovered -- and fail the day it is
    fixed, so the note above and `STRICTER_ON_PURPOSE` get updated together.

    The line below carries two nonces and a name with a space in it. It parses.
    """
    smuggled = protocol.parse(
        "JOIN g7 as x nonce=aaaaaaaaaaaaaaaa nonce=bbbbbbbbbbbbbbbb")

    assert smuggled.name == "x", "the name written was 'x nonce=aaaa...'"
    assert smuggled.nonce == "a" * 16, "and one of the two nonces was chosen"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no lines at all")
    pytest.skip(why)


_PAGE = """<!doctype html><meta charset=utf-8><title>lobby lines</title>
<script type=module>
import {{ openLine, joinLine, nonce, LIMITS }} from './lobby_lines.js';

const cases = {cases};
const out = [];
for (const [kind, args] of cases) {{
  try {{
    out.push({{ line: kind === 'open' ? openLine(args) : joinLine(args) }});
  }} catch (err) {{
    out.push({{ refused: String(err.message) }});
  }}
}}
window.RESULT = {{
  cases: out,
  limits: LIMITS,
  // Ten draws, to catch a nonce generator that is the right shape and the
  // same every time -- which would settle every table on a seed one seat
  // chose in advance.
  nonces: Array.from({{ length: 10 }}, () => nonce()),
}};
</script>
"""


def _serve(directory):
    """A localhost server, because `file://` cannot import an ES module and
    `crypto.getRandomValues` wants a secure context. Same reasoning as
    `test_hand_crypto.py`, and the shape the page really runs in."""
    import functools
    import http.server
    import threading

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture(scope="module")
def composed(tmp_path_factory):
    """What the browser made of every case, in order."""
    tmp_path = tmp_path_factory.mktemp("hand-lines")
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    (tmp_path / "lobby_lines.js").write_text((HAND / "lobby_lines.js").read_text())
    page = tmp_path / "lines.html"
    page.write_text(_PAGE.format(cases=json.dumps(CASES)))
    server = _serve(tmp_path)
    url = f"http://127.0.0.1:{server.server_address[1]}/lines.html"

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


def _python_reads(line: str):
    """What `protocol.parse` makes of a line: the object, or the refusal."""
    try:
        return protocol.parse(line), None
    except protocol.Malformed as exc:
        return None, str(exc)


def test_the_two_grammars_agree_on_what_is_a_line_at_all(composed):
    """**The assertion the buttons exist under.**

    For every case, the browser either composed a line or refused the input,
    and `protocol.parse` either read that line or refused it. The two must
    reach the same verdict. A disagreement in either direction is silent in
    service: a composed line Python rejects loses a table with no error a
    driver sees, and an input the page rejects that Python would have taken
    shrinks the game for nothing.
    """
    disagreements = []
    for (kind, args), got in zip(CASES, composed["cases"]):
        if "refused" in got:
            continue
        parsed, why = _python_reads(got["line"])
        if parsed is None:
            disagreements.append(
                f"{kind} {args} -> composed {got['line']!r}, "
                f"which protocol.py refuses: {why}")
    assert not disagreements, "\n".join(disagreements)


def test_nothing_the_page_refuses_would_have_been_a_good_line(composed):
    """The other direction, which no amount of care catches on its own.

    A composer that refused everything would pass the test above perfectly.
    """
    over_strict = []
    for (kind, args), got in zip(CASES, composed["cases"]):
        if "refused" not in got:
            continue
        if (kind, json.dumps(args, sort_keys=True)) in STRICTER_ON_PURPOSE:
            continue
        # Build the line the page *would* have had to write, and ask the real
        # parser whether it was allowed. Anything that parses here is an input
        # the page turned away for no reason.
        if kind == "open":
            line = ("OPEN traders={traders} episodes={episodes} "
                    "rounds={rounds} goods={goods} seconds={seconds}").format(
                traders=args.get("traders"), episodes=args.get("episodes"),
                rounds=args.get("rounds", 1),
                goods=args.get("goods", protocol.GOODS_DEFAULT),
                seconds=args.get("seconds", protocol.EPISODE_SECONDS_DEFAULT))
        else:
            line = (f"JOIN {args.get('table')} as {args.get('name')} "
                    f"nonce={args.get('nonce')}")
        parsed, _ = _python_reads(line)
        if parsed is not None:
            over_strict.append(f"{kind} {args} refused, but {line!r} parses")
    assert not over_strict, "\n".join(over_strict)


def test_every_composed_open_means_what_the_buttons_showed(composed):
    """Parsed field by field, not merely parsed.

    A line can be well-formed and still say something the driver did not ask
    for -- two fields transposed parse perfectly and open the wrong table.
    Every field is written out rather than defaulted for this reason: what the
    board says is what the page showed.
    """
    checked = 0
    for (kind, args), got in zip(CASES, composed["cases"]):
        if kind != "open" or "refused" in got:
            continue
        opened, _ = _python_reads(got["line"])
        assert isinstance(opened, protocol.Open), got
        assert opened.traders == int(str(args["traders"]).strip())
        assert opened.episodes == int(str(args["episodes"]).strip())
        assert opened.rounds == args.get("rounds", 1)
        assert opened.goods == args.get("goods", protocol.GOODS_DEFAULT)
        assert opened.seconds == args.get(
            "seconds", protocol.EPISODE_SECONDS_DEFAULT)
        checked += 1
    assert checked >= 5, "the good OPEN cases are not being reached"


def test_every_composed_join_means_what_the_buttons_showed(composed):
    checked = 0
    for (kind, args), got in zip(CASES, composed["cases"]):
        if kind != "join" or "refused" in got:
            continue
        joined, _ = _python_reads(got["line"])
        assert isinstance(joined, protocol.Join), got
        assert joined.table == args["table"]
        assert joined.name == args["name"]
        assert joined.nonce == args["nonce"], (
            "the seat's half of the seed survives composition intact")
        checked += 1
    assert checked >= 5, "the good JOIN cases are not being reached"


def test_the_page_always_brings_a_nonce(composed):
    """`protocol.parse` accepts a JOIN without one, and the page never writes
    one that way.

    A table where a seat brought no nonce settles on a draw that seat cannot
    check afterwards -- the weaker game -- and a page that quietly left it out
    would be making that choice on the driver's behalf.
    """
    for (kind, _args), got in zip(CASES, composed["cases"]):
        if kind == "join" and "refused" not in got:
            assert "nonce=" in got["line"]


def test_the_nonce_is_drawn_fresh_every_time(composed):
    """A generator of the right shape that returns the same value would pass
    every other test here, and would settle every table on a seed one seat
    knew in advance."""
    nonces = composed["nonces"]

    assert len(set(nonces)) == len(nonces), "a nonce repeated within ten draws"
    for value in nonces:
        assert protocol.NONCE.match(value), value


def test_the_bounds_the_page_shows_are_the_bounds_python_enforces(composed):
    """The numbers on the controls come from `LIMITS`, so a slider that
    offered a value the lobby refuses would be an invitation to a refusal.

    Duplicated rather than derived -- a static page cannot import Python --
    which is exactly why they are asserted equal here.
    """
    limits = composed["limits"]

    assert limits["tradersMin"] == protocol.TRADERS_MIN
    assert limits["tradersMax"] == protocol.TRADERS_MAX
    assert limits["goodsMin"] == protocol.GOODS_MIN
    assert limits["goodsMax"] == protocol.GOODS_MAX
    assert limits["goodsDefault"] == protocol.GOODS_DEFAULT
    assert limits["roundsMax"] == protocol.ROUNDS_MAX
    assert limits["secondsDefault"] == protocol.EPISODE_SECONDS_DEFAULT
    assert tuple(limits["secondsAllowed"]) == protocol.EPISODE_SECONDS_ALLOWED
    assert limits["nameMax"] == 32
