"""`play_lines.js` against the grammar the manager actually reads.

The kids' page composes the manager's forms from sliders and dropdowns rather
than from a keyboard, which makes it a **second implementation** of
`experiments/does-a-content-free-protocol-help/island/protocol.py`. It could not be
anything else: the page is served from a static origin and cannot call Python.
`test_hand_lobby_lines.py` settled the shape of the answer for the lobby's two
lines, and this is the same arrangement for the island's four -- the JS
composes, the real parser reads, and neither half is ever compared against its
own idea of what it should produce.

**Agreement is checked in both directions**, because the two ways to drift are
opposite and both silent:

- a line the buttons compose that Python refuses loses a child their day, with
  nothing on the page to say why -- the manager's refusal arrives privately
  and a nine-year-old is not reading their inbox;
- an input the buttons refuse that Python would have taken shrinks the game
  for no reason, and nothing anywhere would notice.

**And the readers are pinned to a real manager's output**, not to invented
lines. `openOffers`, `seatsNamed` and `whichDay` scrape prose so a child can
pick an offer from a list instead of copying `p3` by eye, and prose is not a
grammar. So the lines they are tested against are produced here by driving an
actual `Manager` and an actual `schedule_text` -- the mistake
`test_lobby_web_reconstruct.py` exists because of, where a port was only ever
read against fixtures its own author wrote.

Run it here with a browser installed, or in the `pages` CI job, which has one
and sets `ISLAND_REQUIRE_BROWSER` -- a skip and a pass are the same tick.

    python -m pytest games/island/tests/test_hand_play_lines.py -q
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

HAND = pathlib.Path(__file__).resolve().parent.parent / "hand"

# The economy's own tree, as `run_game.py` reaches it: the package is `island`
# while this one is `games.island`, so the two names do not collide.
_ISLAND = (pathlib.Path(__file__).resolve().parents[3]
           / "experiments" / "does-a-content-free-protocol-help")
if str(_ISLAND) not in sys.path:
    sys.path.insert(0, str(_ISLAND))

from island import protocol as economy  # noqa: E402
from island.dealer import GOODS as PYTHON_GOODS  # noqa: E402

#: What the buttons are asked to compose. Each case is `(kind, arguments)`,
#: and deliberately not a list of things that work: the awkward ones are the
#: point, since a grammar only drifts where nobody looks.
CASES = [
    # --- PRODUCE, inside the grammar --------------------------------------
    ("produce", {"plan": {"bread": 0.5, "fish": 0.5}}),
    ("produce", {"plan": {"bread": 1}}),
    ("produce", {"plan": {"bread": 0.25, "cloth": 0.25, "iron": 0.25,
                          "salt": 0.25}}),
    # A slider left at the bottom: dropped, not written as `cloth=0`.
    ("produce", {"plan": {"bread": 0.5, "cloth": 0}}),
    # Strings, because an <input> hands the page a string and never a number.
    ("produce", {"plan": {"bread": "0.5", "fish": " 0.5 "}}),
    ("produce", {"plan": {"bread": ".5"}}),
    # Float noise from a slider: 0.1 + 0.2 is not 0.3, and the board must not
    # be told about it.
    ("produce", {"plan": {"bread": 0.1 + 0.2}}),
    # **Over the labour budget.** `parse` reads it; the manager refuses it.
    # The page must compose it anyway and warn in words -- refusing here is
    # the direction that makes this page stricter than the game.
    ("produce", {"plan": {"bread": 0.9, "fish": 0.9}}),
    # --- PRODUCE, outside it ----------------------------------------------
    ("produce", {"plan": {}}),
    ("produce", {"plan": {"bread": 0}}),
    ("produce", {"plan": {"bread": -0.5}}),
    ("produce", {"plan": {"Bread": 0.5}}),
    ("produce", {"plan": {"bread cakes": 0.5}}),
    ("produce", {"plan": {"bread": "half"}}),
    ("produce", {"plan": {"bread": ""}}),
    ("produce", {"plan": {"bread": 1e-7}}),
    # More decimals than any control here offers: written out, never rounded.
    ("produce", {"plan": {"bread": 0.123456}}),
    # **A whole number above nine.** Trimming a float's trailing zeros with
    # `/0+$/` turns `10.000000000` into `1`, on a line that parses perfectly
    # and trades a tenth of what the driver offered.
    ("propose", {"to": "T2", "give": {"iron": 10}, "want": {"salt": 20}}),
    # --- PROPOSE, inside the grammar --------------------------------------
    ("propose", {"to": "T2", "give": {"iron": 0.4}, "want": {"salt": 0.3}}),
    ("propose", {"to": "T3", "give": {"iron": 0.4, "salt": 0.1},
                 "want": {"bread": 1}}),
    ("propose", {"to": "T2", "give": {"iron": "0.4"}, "want": {"salt": ".3"}}),
    # Addressed to nobody. `parse` reads it, so this composes: the page turns
    # its own button off, which is an affordance rather than a second grammar.
    ("propose", {"to": "", "give": {"iron": 0.4}, "want": {"salt": 0.3}}),
    # --- PROPOSE, outside it ----------------------------------------------
    # The partner an unwary composer splits into two fields.
    ("propose", {"to": "T 2", "give": {"iron": 0.4}, "want": {"salt": 0.3}}),
    ("propose", {"to": "T2\nPROPOSE to=T3", "give": {"iron": 0.4},
                 "want": {"salt": 0.3}}),
    ("propose", {"to": "T2", "give": {}, "want": {"salt": 0.3}}),
    ("propose", {"to": "T2", "give": {"iron": 0.4}, "want": {}}),
    ("propose", {"to": "T2", "give": {"iron": 0}, "want": {"salt": 0.3}}),
    ("propose", {"to": "T2", "give": {"iron": -1}, "want": {"salt": 0.3}}),
    ("propose", {"to": "T2", "give": {"iron ore": 0.4}, "want": {"salt": 0.3}}),
    # --- APPROVE and DECLINE ----------------------------------------------
    ("approve", {"proposal": "p3"}),
    ("approve", {"proposal": " p3 "}),
    ("approve", {"proposal": ""}),
    ("approve", {"proposal": "p3 p4"}),
    ("decline", {"proposal": "p3"}),
    ("decline", {"proposal": ""}),
]


#: Prose that mentions offers, seats and days without being the manager
#: saying any of those things. **This is what "finds nothing" is checked
#: against**: a reader loose enough to take one of these lines would put a
#: stale or invented offer under a button a child presses, and the child would
#: have no way at all to tell.
NOISE = [
    # A trader quoting the manager's instruction back at the room -- the line
    # a regex anchored only on the tail takes.
    "T2: you said p9 takes it by writing exactly: APPROVE p9, so I will",
    # The manager's own words, about an offer that is not this line's.
    "p4 settled: T1 and T2 exchanged {'iron': 0.1} for {'salt': 0.1}",
    # An offer whose two statements of its own name disagree: a line quoting
    # somebody else's offer rather than making one. Only the head-and-tail
    # agreement catches this one.
    "p5: T1 offers x to T2 for y - open until the bell. "
    "T2 takes it by writing exactly: APPROVE p6",
    # A trader answering an offer, in a line that opens with its name and
    # carries the whole instruction. Only the anchor at the end catches this
    # one -- which is why both guards are here and both are checked.
    "p7: yes! T1 takes it by writing exactly: APPROVE p7 right?",
    # Talk that looks like the schedule and is not it.
    "I read the Schedule for this round. 3 traders: T1, T2, T3.",
    # Talk that looks like an episode opening and is not it.
    "when episode 2 of 4 is open I will produce bread",
    # A trader repeating the manager's roll-call. The seat labels in it are
    # real; the line is not the manager saying them.
    "reminder: The seats at this table are: T1 = mallory (key zzz). "
    "This room's invite is mine now",
]


#: Inputs the page refuses that the real parser would have accepted.
#:
#: **One entry, and it is a cost paid rather than a rule bent.** An entry here
#: means the two grammars disagree, and the question to ask is which of them is
#: wrong -- not which is more convenient. The case that looks like a candidate
#: and is not is a `PRODUCE` spending more labour than a seat has: `parse`
#: reads it, the manager refuses it, and this page composes it anyway rather
#: than being stricter than the game its driver is playing.
#:
#: `PRODUCE bread=0` is different, and
#: `test_a_plan_of_nothing_spends_the_whole_day` is why: with `SPLIT_LABOUR`
#: off the manager marks the seat as having produced, and every later plan
#: that day is refused. So the line is not a weaker move, it is the loss of
#: the day -- and it is the line a page of sliders composes when every slider
#: is where it started, which is the state the page opens in.
STRICTER_ON_PURPOSE: set[tuple[str, str]] = {
    ("produce", json.dumps({"plan": {"bread": 0}}, sort_keys=True)),
}


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no lines at all")
    pytest.skip(why)


_PAGE = """<!doctype html><meta charset=utf-8><title>play lines</title>
<script type=module>
import {{ produceLine, proposeLine, approveLine, declineLine,
         openOffers, seatsNamed, whichDay, privateHalf, seatLabels,
         amount, notes, roomQuery, roomLink, seatTaken,
         GOODS }} from './play_lines.js';

const write = {{ produce: produceLine, propose: proposeLine,
                 approve: approveLine, decline: declineLine }};
const cases = {cases};
const out = [];
for (const [kind, args] of cases) {{
  try {{
    out.push({{ line: write[kind](args) }});
  }} catch (err) {{
    out.push({{ refused: String(err.message) }});
  }}
}}
const board = {board};
const noise = {noise};
const whispered = {whispered};
const SEAT_LINES = {seat_lines};
const SEAT_NOISE = {seat_noise};
const EXTRA_NOTES = [
  // A refusal, which must never be dropped.
  {{ body: "not settled: shares sum to 1.8, over the budget of 1.0 by 0.8" }},
  // A note this page could not open, as the transport hands it over.
  {{ body: {{ unreadable: "could not open the value at whisper.body: wrong key, tampering, or a mismatched context" }} }},
];
window.RESULT = {{
  cases: out,
  goods: GOODS,
  offers: openOffers(board),
  // The same board as the rows `room.js` keeps, to check the reader takes
  // either shape -- the page hands it rows and the test hands it strings.
  offersFromRows: openOffers(board.map((b) => ({{ body: b }}))),
  seats: seatsNamed(board),
  day: whichDay(board),
  // Prose that talks *about* offers without any manager making one. A reader
  // that guessed would find offers here.
  noiseOffers: openOffers(noise),
  noiseSeats: seatsNamed(noise),
  noiseDay: whichDay(noise),
  half: privateHalf(whispered),
  // The room, hung on a link. Empty fields must not be written out blank.
  query: roomQuery({{ workspace: "island-g7", key: "K", seat: "T1",
                     name: "pip", write_key: "", token: "  ", channel: null }}),
  emptyLink: roomLink("./kids.html", {{}}),
  fullLink: roomLink("./kids.html", {{ workspace: "w", key: "k" }}),
  // The seat, off the lobby's own witnessing line.
  seatFromLobby: seatTaken(SEAT_LINES, {{ table: "g39", name: "Gal" }}),
  seatWrongTable: seatTaken(SEAT_LINES, {{ table: "g40", name: "Gal" }}),
  seatWrongName: seatTaken(SEAT_LINES, {{ table: "g39", name: "Mallory" }}),
  seatFromNoise: seatTaken(SEAT_NOISE, {{ table: "g39", name: "Gal" }}),
  labels: seatLabels(board),
  noiseLabels: seatLabels(noise),
  amounts: {amounts}.map((q) => amount(q)),
  // The notes a seat is shown, with the bars up and with them down.
  notesShown: notes(whispered.concat(EXTRA_NOTES), {{ privateShown: true }}),
  notesBare: notes(whispered.concat(EXTRA_NOTES), {{ privateShown: false }}),
  // The board is public and never carries this; a reader that found it there
  // would be reading somebody's sealed half off a page anyone can open.
  halfFromBoard: privateHalf(board),
  halfFromNoise: privateHalf(noise),
}};
</script>
"""


def _serve(directory):
    """A localhost server, because `file://` cannot import an ES module. Same
    reasoning as `test_hand_lobby_lines.py`, and the shape the page runs in."""
    import functools
    import http.server
    import threading

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class _Stub:
    """The two calls `Manager` makes of a client, and nothing else.

    A real hub would be testing Switchboard, which is not this repo's code.
    What is under test is the **text the manager writes**, which this keeps.
    """

    def __init__(self):
        self.said: list[str] = []

    def post(self, channel, text):
        self.said.append(text)

    def history(self, channel, limit=500, **kw):
        return []


@pytest.fixture(scope="module")
def real_board() -> list[str]:
    """A board a real manager wrote, from one day of a two-seat table.

    Driven rather than transcribed: a manager that reworded its receipt would
    change these lines, and the readers in `play_lines.js` would fail here
    instead of quietly finding nothing in a child's browser.
    """
    from island import schedule
    from island.dealer import Dealer
    from island.manager import Manager

    dealer = Dealer.draw(seed=1, agents=2)
    mgr = Manager(capacity=dealer.capacity, client=_Stub(), channel="c")
    for name in mgr.names:
        mgr.bind(name, name)

    WHISPERED[:] = [f"{dealer.private_state(name)} "
                    f"You are seated here as {name}."
                    for name in mgr.names]
    lines = [_roll_call(), schedule.schedule_text(4, mgr.names, opens_at=0.0)]
    lines.append("episode 1 of 4 is open; the bell is at 00:00:60Z (60s). "
                 "PRODUCE, PROPOSE and APPROVE all settle until the bell.")
    mgr.open_episode()
    mgr._produce("T1", economy.Produce(plan={g: 0.5 for g in mgr.goods[:2]}))
    mgr._produce("T2", economy.Produce(plan={g: 0.5 for g in mgr.goods[:2]}))
    # A tenth of what each seat actually made, so the offers are affordable
    # whatever island this seed deals -- an offer the manager refuses posts no
    # receipt at all, and there would be nothing for the page to read.
    give, want = mgr.goods[0], mgr.goods[1]
    part = min(mgr.holders["T1"].holdings[mgr.goods.index(give)],
               mgr.holders["T2"].holdings[mgr.goods.index(want)]) / 10
    # Three offers: one taken, one refused by its addressee, one left open.
    for _ in range(3):
        mgr._propose("T1", economy.Propose(to="T2", give={give: part},
                                           want={want: part}))
    open_ids = sorted(mgr.proposals)
    mgr._approve("T2", economy.Approve(proposal_id=open_ids[0]))
    mgr._decline("T2", economy.Decline(proposal_id=open_ids[1]))
    lines.extend(mgr.client.said)
    return lines, open_ids


#: What the manager whispers each seat, from the real dealer. Filled by
#: `real_board`, which draws the island these numbers belong to.
WHISPERED: list[str] = []

#: The lobby's own witnessing lines, in the shape `lobby._join` writes them.
#: The real thing is asserted end to end in `test_hand_pages.py`, against a
#: real `Lobby` that really seated somebody; these are here for the awkward
#: cases, which an integration test cannot reach on purpose.
SEAT_LINES = [
    "g39 seat T1 = Gal, key sWk00c5VlODNSpy96, sealed, nonce 479a0169 (1/2)",
    "g39 seat T2 = npc-g39-1, key wY2gDwO0hRu1RlW4, sealed, nonce 1525db05 (2/2)",
]

#: Lines that name a seat without being the lobby witnessing one. A wrong
#: answer here puts somebody else's label in a driver's declaration, which the
#: record then reads as that seat having a human on it.
SEAT_NOISE = [
    "g39 seat T1 = Gal was witnessed, key sWk00c5, and I am not Gal",
    "reminder: g39 seat T9 = Gal, key nope, sealed",
    "T1 = Gal, key sWk00c5VlODNSpy96, sealed",
]

#: Quantities as they really arrive in an offer, and the awkward ones around
#: them. The first is the one that was on the page: a twelfth of a loaf,
#: printed in full at an eight-year-old.
AMOUNTS = [0.12428327472728834, 0.5, 1, 0, 0.999, 0.005, 0.0034, 12.5,
           0.12, 2, 0.0000001, 1e-30]


def _roll_call() -> str:
    """The manager naming its seats, from `run_game` rather than by hand.

    The island draws a hut per seat and the board names authors by blinded hub
    id, so this line is the only thing standing between a child and an island
    of six-character hashes. Driven, not transcribed, for `real_board`'s
    reason.
    """
    from games.island.lobby import Table
    from games.island.run_game import who_is_at_this_table

    table = Table(id="g7", opened_by="opener", opened_at=0.0, traders=2,
                  episodes=4, rounds=1, goods=4, seconds=60)
    table.seats = {"peer-a": "alice", "peer-b": "bob"}
    table.keys = {"peer-a": "abc", "peer-b": "def"}
    return who_is_at_this_table(table)


@pytest.fixture(scope="module")
def composed(tmp_path_factory, real_board):
    """What the browser made of every case, and of a real manager's board."""
    lines, _ = real_board
    tmp_path = tmp_path_factory.mktemp("hand-play-lines")
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    (tmp_path / "play_lines.js").write_text((HAND / "play_lines.js").read_text())
    page = tmp_path / "lines.html"
    page.write_text(_PAGE.format(cases=json.dumps(CASES),
                                 board=json.dumps(lines),
                                 noise=json.dumps(NOISE),
                                 whispered=json.dumps(WHISPERED),
                                 amounts=json.dumps(AMOUNTS),
                                 seat_lines=json.dumps(SEAT_LINES),
                                 seat_noise=json.dumps(SEAT_NOISE)))
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
    """What the economy's parser makes of a line: the action, or the refusal."""
    try:
        return economy.parse(line), None
    except economy.Malformed as exc:
        return None, str(exc)


def test_the_two_grammars_agree_on_what_is_a_line_at_all(composed):
    """**The assertion the buttons exist under.**

    For every case the browser either composed a line or refused the input,
    and the real parser either read that line or refused it. The two must
    reach the same verdict.
    """
    disagreements = []
    for (kind, args), got in zip(CASES, composed["cases"]):
        if "refused" in got:
            continue
        parsed, why = _python_reads(got["line"])
        if parsed is None:
            disagreements.append(
                f"{kind} {args} -> composed {got['line']!r}, "
                f"which the parser refuses: {why}")
        elif parsed is None:                          # pragma: no cover
            pass
    assert not disagreements, "\n".join(disagreements)


def test_a_composed_line_is_never_read_as_talk(composed):
    """The failure a refusal cannot show you.

    `parse` returns `None` for a line that is not a formatted message at all,
    and the manager settles nothing and says nothing about it -- so a composer
    that wrote `Produce bread=0.5` would post, appear on the board, and be
    silently ignored for the whole day.
    """
    talk = []
    for (kind, args), got in zip(CASES, composed["cases"]):
        if "refused" in got:
            continue
        parsed, _ = _python_reads(got["line"])
        if parsed is None:
            talk.append(f"{kind} {args} -> {got['line']!r} is talk, not a move")
    assert not talk, "\n".join(talk)


def test_nothing_the_page_refuses_would_have_been_a_good_line(composed):
    """The other direction, which no amount of care catches on its own: a
    composer that refused everything would pass the test above perfectly.

    The line the page *would* have had to write is rebuilt here in the
    crudest way there is -- string concatenation, no shared helper -- because
    a helper shared with the composer would agree with it by construction.
    """
    over_strict = []
    for (kind, args), got in zip(CASES, composed["cases"]):
        if "refused" not in got:
            continue
        if (kind, json.dumps(args, sort_keys=True)) in STRICTER_ON_PURPOSE:
            continue
        line = _naively(kind, args)
        if line is None:
            continue
        parsed, _ = _python_reads(line)
        if parsed is not None:
            over_strict.append(
                f"{kind} {args} refused ({got['refused']}), but {line!r} parses")
    assert not over_strict, "\n".join(over_strict)


def _naively(kind, args):
    """The line a composer with no scruples would write for these arguments.

    `None` where there is no such line -- an empty plan has nothing to
    concatenate, and its refusal cannot be over-strict.
    """
    def num(v):
        return v if isinstance(v, str) else repr(v)

    if kind == "produce":
        plan = args["plan"]
        if not plan:
            return None
        return "PRODUCE " + " ".join(f"{g}={num(s)}" for g, s in plan.items())
    if kind == "propose":
        if not args["give"] or not args["want"]:
            return None
        give = ",".join(f"{g}:{num(q)}" for g, q in args["give"].items())
        want = ",".join(f"{g}:{num(q)}" for g, q in args["want"].items())
        return f"PROPOSE to={args['to']} give={give} want={want}"
    return f"{kind.upper()} {args['proposal']}"


def test_a_plan_of_nothing_spends_the_whole_day():
    """**The one thing this page refuses that the grammar allows.**

    `PRODUCE bread=0` parses. What it does at the manager is spend the day:
    `SPLIT_LABOUR` is off, so the seat is marked as having produced and every
    later plan that day is refused -- and a page of sliders composes exactly
    that line when every slider is where the page opened it.

    Asserted against a real manager rather than argued, because the entry in
    `STRICTER_ON_PURPOSE` above stands on it. If `SPLIT_LABOUR` is ever turned
    on, this fails and the entry has to go.
    """
    from island import manager as M
    from island.dealer import Dealer

    assert M.SPLIT_LABOUR is False, "the default must stay off"
    dealer = Dealer.draw(seed=1, agents=2)
    mgr = M.Manager(capacity=dealer.capacity, client=_Stub(), channel="c")
    for name in mgr.names:
        mgr.bind(name, name)
    mgr.open_episode()

    nothing = economy.parse("PRODUCE bread=0")
    assert nothing == economy.Produce(plan={"bread": 0.0}), "it is a move"
    mgr._produce("T1", nothing)
    with pytest.raises(M.Refused, match="already produced"):
        mgr._produce("T1", economy.Produce(plan={"bread": 0.5}))


def test_every_composed_produce_means_what_the_sliders_showed(composed):
    """Parsed field by field, not merely parsed.

    A line can be well-formed and say something the child did not ask for --
    two goods transposed parse perfectly and spend the day on the wrong one.
    """
    checked = 0
    for (kind, args), got in zip(CASES, composed["cases"]):
        if kind != "produce" or "refused" in got:
            continue
        plan, _ = _python_reads(got["line"])
        assert isinstance(plan, economy.Produce), got
        wanted = {g: float(str(s).strip()) for g, s in args["plan"].items()
                  if float(str(s).strip()) != 0}
        assert plan.plan.keys() == wanted.keys(), got["line"]
        for g, share in wanted.items():
            assert abs(plan.plan[g] - share) < 1e-9, got["line"]
        checked += 1
    assert checked >= 6, "the good PRODUCE cases are not being reached"


def test_a_share_left_at_zero_is_not_written_at_all(composed):
    """A slider at the bottom is a good the child did not pick. `bread=0`
    parses and means the same thing, and puts a choice on the board that
    nobody made -- which is what the other traders then read."""
    case = CASES.index(("produce", {"plan": {"bread": 0.5, "cloth": 0}}))
    assert composed["cases"][case]["line"] == "PRODUCE bread=0.5"


def test_float_noise_never_reaches_the_board(composed):
    """`0.1 + 0.2` is `0.30000000000000004`, and `String` says so. A slider
    computes exactly that, and the parser's number regex would refuse the
    exponent forms nearby -- so the composer writes the number out."""
    case = CASES.index(("produce", {"plan": {"bread": 0.1 + 0.2}}))
    assert composed["cases"][case]["line"] == "PRODUCE bread=0.3"


def test_a_number_finer_than_the_controls_is_written_out_rather_than_rounded(
        composed):
    """A quantity is never quietly re-rounded to something the driver did not
    choose. The only rounding here is at the ninth decimal, which is where a
    float's own arithmetic error lives and below anything any control offers.
    """
    case = CASES.index(("produce", {"plan": {"bread": 0.123456}}))
    assert composed["cases"][case]["line"] == "PRODUCE bread=0.123456"


def test_a_whole_number_keeps_its_zeros(composed):
    """The trailing-zero trim, and the one input that catches it wrong.

    `(10).toFixed(9)` is `10.000000000`, and a trim that took every trailing
    zero would write `1` -- a line that parses, posts, and offers a tenth of
    what the driver chose, with nothing anywhere to say so.
    """
    case = CASES.index(
        ("propose", {"to": "T2", "give": {"iron": 10}, "want": {"salt": 20}}))
    assert composed["cases"][case]["line"] == \
        "PROPOSE to=T2 give=iron:10 want=salt:20"


def test_every_composed_propose_means_what_the_buttons_showed(composed):
    checked = 0
    for (kind, args), got in zip(CASES, composed["cases"]):
        if kind != "propose" or "refused" in got:
            continue
        offer, _ = _python_reads(got["line"])
        assert isinstance(offer, economy.Propose), got
        assert offer.to == args["to"]
        for side, wanted in (("give", args["give"]), ("want", args["want"])):
            got_side = getattr(offer, side)
            assert got_side.keys() == wanted.keys(), got["line"]
            for g, qty in wanted.items():
                assert abs(got_side[g] - float(str(qty).strip())) < 1e-9
        checked += 1
    assert checked >= 3, "the good PROPOSE cases are not being reached"


def test_approve_and_decline_carry_the_offer_they_were_given(composed):
    for (kind, args), got in zip(CASES, composed["cases"]):
        if kind not in ("approve", "decline") or "refused" in got:
            continue
        action, _ = _python_reads(got["line"])
        assert action.proposal_id == args["proposal"].strip(), got


def test_the_goods_the_page_offers_are_the_islands(composed):
    """The sliders are labelled from this list, and a good the island does not
    have is a plan the manager refuses by name. Duplicated rather than derived
    -- a static page cannot import Python -- which is exactly why it is
    asserted equal here."""
    assert tuple(composed["goods"]) == tuple(PYTHON_GOODS)


# --- reading the manager back ---------------------------------------------

def test_the_open_offers_are_the_ones_the_manager_still_holds(
        composed, real_board):
    """Against a real manager's own receipts: three offers made, one taken,
    one declined, and the page must list exactly the third."""
    _lines, ids = real_board
    still_open = [o["id"] for o in composed["offers"]]

    assert still_open == [ids[2]], composed["offers"]
    assert composed["offers"][0]["to"] == "T2", (
        "and who may take it, so the page can say whose turn this is")
    assert composed["offersFromRows"] == composed["offers"], (
        "the reader takes the rows the page keeps as well as bare strings")


def test_the_reader_finds_nothing_rather_than_something_wrong(composed):
    """**The failure mode this half is designed around.**

    The manager's receipts are prose and nobody promised they would hold
    still. A reader that guessed would put a stale offer under a button a
    child presses, and nothing on the page would look wrong; one that finds
    nothing costs them a dropdown, and the offer is still on the board to be
    read and typed.

    So it is handed prose that talks *about* offers, seats and days without
    any manager saying one -- a trader quoting the manager's instruction back
    at the room among them, which is the line a regex anchored on the tail
    alone takes -- and it must come back empty every time.
    """
    assert composed["noiseOffers"] == [], composed["noiseOffers"]
    assert composed["noiseSeats"] == [], composed["noiseSeats"]
    assert composed["noiseDay"] is None, composed["noiseDay"]


def test_the_seats_are_read_from_the_managers_schedule(composed):
    """So the partner is a dropdown of real seats rather than a spelling
    test. `[]` when the manager has not said, and then it is typed."""
    assert composed["seats"] == ["T1", "T2"]


def test_the_day_is_read_from_the_managers_episode_line(composed):
    """The game calls an episode a day (`CLAUDE.md`), so the number is dug
    out of the manager's line rather than the sentence being quoted -- and
    the manager's own word still goes on the page beside it."""
    assert composed["day"] == {"day": 1, "of": 4, "open": True, "over": False}


def test_the_seats_private_half_is_read_out_of_the_managers_whisper(
        composed, real_board):
    """What makes this page playable by a child: how good this island is at
    each thing, and how much this seat wants each thing, as bars rather than
    as a Python dict repr.

    Pinned to `dealer.private_state`'s real output, because that text is prose
    around two `repr(dict)`s and neither half was designed to be read back.
    """
    from island.dealer import Dealer

    dealer = Dealer.draw(seed=1, agents=2)
    half = composed["half"]

    assert half is not None, WHISPERED
    assert half["seat"] == "T1"
    assert list(half["capacity"]) == list(dealer.goods), (
        "and it names the goods this island actually deals, which is what the "
        "sliders are built from")
    index = dealer.names.index("T1")
    for i, good in enumerate(dealer.goods):
        assert abs(half["capacity"][good]
                   - round(dealer.island.capacity[index][i], 4)) < 1e-9
        assert abs(half["taste"][good]
                   - round(dealer.island.alpha[index][i], 4)) < 1e-9


def test_no_private_half_is_ever_found_on_the_public_board(composed):
    """A sealed round keeps these numbers off the board, and this reader must
    not be the thing that puts them back. Nothing composes from them either --
    the page shows them and never writes them into a line."""
    assert composed["halfFromBoard"] is None
    assert composed["halfFromNoise"] is None


def test_the_seats_are_matched_to_their_players_names(composed):
    """So the island draws huts with seat labels on them.

    The board names an author by their blinded hub id; the manager's roll-call
    is the one place those ids' *aliases* are tied to `T1` and `T2`. Read off
    the line `run_game.who_is_at_this_table` really writes.
    """
    assert composed["labels"] == {"alice": "T1", "bob": "T2"}


def test_no_roll_call_is_found_in_talk_about_one(composed):
    """The same guard the offers reader carries: a wrong name over somebody's
    hut is worse than a short one, because a child would trade against it."""
    assert composed["noiseLabels"] == {}


# --- what a child is shown, as opposed to what is sent ---------------------

def test_a_quantity_is_written_the_way_a_child_reads_it(composed):
    """**The line that was actually on the page**: "T2 offers you
    0.12428327472728834 iron for 0.12428327472728834 bread".

    Two decimals, which is the step every slider offers. A number too small
    to survive that is written at one significant figure rather than as `0`,
    because "offers you 0 iron" describes a trade nobody is making.
    """
    got = dict(zip(AMOUNTS, composed["amounts"]))

    assert got[0.12428327472728834] == "0.12"
    assert got[0.5] == "0.5" and got[1] == "1" and got[0] == "0"
    assert got[0.999] == "1", "rounded for reading, like any other number"
    assert got[0.005] == "0.01"
    assert got[0.0034] == "0.0034", "too small for two places, and not zero"
    assert got[0.0000001] == "0.0000001", (
        "written out -- `toPrecision` would hand back `1e-7`, and an exponent "
        "is not an improvement on the number it replaced")
    assert got[1e-30] == "almost none", "and below any of that, said in words"
    assert got[12.5] == "12.5" and got[2] == "2"


def test_rounding_for_display_cannot_change_what_is_traded():
    """**Why the rounding above is safe, stated as a check rather than a
    claim.** A quantity a child reads never becomes a quantity anybody sends:
    the button under an offer composes `APPROVE <id>`, which carries no
    numbers at all, and the manager settles the offer it already holds.

    This is the property that would *not* hold for a `PROPOSE`, whose
    quantities do go on the wire -- and those come from the input, through
    `produceLine`/`proposeLine`, which round nothing. Asserted here so that
    moving `amount` into a composer fails.
    """
    approve = economy.parse("APPROVE p1")
    assert isinstance(approve, economy.Approve)
    assert approve.proposal_id == "p1"
    assert not [f for f in vars(approve) if "give" in f or "want" in f], \
        "an APPROVE carries an id and nothing a display could have altered"


def test_a_note_that_could_not_be_opened_is_said_in_words(composed):
    """It used to render as `{"unreadable":"could not open the value at
    whisper.body: ..."}` -- a wall of JSON at a child.

    The usual cause is mundane and fixable, so the words say it: the seat key
    lives in one browser, and a second browser or a private window reads with
    a key the lobby never witnessed.
    """
    [bad] = [n for n in composed["notesShown"] if n["kind"] == "unreadable"]

    assert "could not open" in bad["text"]
    assert "browser" in bad["text"], "and why, in something a person can act on"
    assert not bad["text"].startswith("{"), "not the raw object"


def test_the_private_half_is_not_printed_under_its_own_bars(composed):
    """Two Python dict reprs saying what the bars above already say.

    Dropped only while the bars are actually showing: losing it altogether
    would be worse than printing it, which is what `privateShown` is for.
    """
    shown = [n["text"] for n in composed["notesShown"]]
    bare = [n["text"] for n in composed["notesBare"]]

    assert not [t for t in shown if "production capacity" in t], \
        "the bars are up, so the note they were drawn from is not repeated"
    assert [t for t in bare if "production capacity" in t], \
        "and with no bars it is still shown rather than lost"


def test_a_refusal_is_never_dropped(composed):
    """The part that must survive the tidying: the manager's refusals arrive
    as notes, and a refusal a child does not see is a day they do not know
    they lost."""
    for key in ("notesShown", "notesBare"):
        assert [n for n in composed[key]
                if "not settled" in n["text"]], f"{key} lost the refusal"


# --- getting from one page to another without losing the room --------------

def test_a_link_between_the_pages_carries_the_room(composed):
    """**They used to carry nothing.**

    Clicking "the same game with the island drawn" mid-round dropped the
    workspace, the key and the seat, and landed on an empty form with the bell
    still running.
    """
    import urllib.parse

    got = dict(urllib.parse.parse_qsl(composed["query"]))

    assert got == {"workspace": "island-g7", "key": "K", "seat": "T1",
                   "name": "pip"}, got
    assert "write_key" not in got and "token" not in got and "channel" not in got, (
        "an empty field is left out rather than written blank")
    assert composed["emptyLink"] == "./kids.html", (
        "and a link built before anybody entered is still a link to the page")
    assert composed["fullLink"] == "./kids.html?workspace=w&key=k"


def test_the_seat_comes_off_the_lobbys_own_witnessing_line(composed):
    """**Which is why nobody should have to type `T1`.**

    The lobby says which label it gave you, in public, at the moment it seated
    you. Asking the driver for it asked for something the page already had --
    and asked a child to go and find a label on a board written for agents.
    """
    assert composed["seatFromLobby"] == "T1"
    assert composed["seatWrongTable"] == "", "a seat at another table is not yours"
    assert composed["seatWrongName"] == "", "and neither is somebody else's"


def test_no_seat_is_taken_from_talk_about_one(composed):
    """The consequence of guessing here is worse than the consequence of
    asking: a wrong label goes into this driver's declaration, and the record
    then reads a seat as having a human on it that does not."""
    assert composed["seatFromNoise"] == ""
