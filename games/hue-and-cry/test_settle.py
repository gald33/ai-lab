"""What has to stay true of settlement.

These are the design's central claim made checkable: a transcript and a
seed decide the game, the same way, a year later, with nothing else
consulted.

    python3 -m pytest games/hue-and-cry/test_settle.py -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import settle as S  # noqa: E402
from secret_matrix import commitment, token_for  # noqa: E402

SEED = bytes.fromhex(
    "5e111e0000000000000000000000000000000000000000000000000000000d00")
WORLD = C.Map(SEED)
START = "Stonehenge"
HER = "carmel"


def honest():
    return S.demonstration(SEED, START, WORLD)


def test_an_honest_game_settles_and_every_line_is_accepted():
    result = S.settle(honest(), her=HER)
    assert all(v["ok"] for v in result["verdicts"]), \
        [v for v in result["verdicts"] if not v["ok"]]
    assert result["reputation"] > 0
    assert result["ranked"]


def test_settlement_is_the_same_answer_twice():
    a, b = S.settle(honest(), her=HER), S.settle(honest(), her=HER)
    assert (a["outcome"], a["reputation"], a["moves"]) \
        == (b["outcome"], b["reputation"], b["moves"])


def test_no_seed_no_win():
    """*"A game whose seed is never revealed is scored as a loss for her,
    not as void."* Withholding costs her the game it would have cost her
    anyway."""
    lines = [l for l in honest() if not l.text.startswith("SEED")]
    result = S.settle(lines, her=HER)
    assert result["outcome"] == "she loses"
    assert result["why"] == "no seed, no win"
    assert result["reputation"] == 0


def test_a_seed_that_does_not_open_the_commitment_is_not_a_seed():
    lines = honest()
    lines[-1] = S.Line(S.LOBBY, HER, "SEED " + ("11" * 32))
    result = S.settle(lines, her=HER)
    assert result["outcome"] == "she loses"
    assert any("does not open the commitment" in v["why"]
               for v in result["verdicts"])


def test_a_hint_that_is_not_live_is_refused_and_does_not_move_her():
    """And the cost is the whole rest of the game, not one move: a rejected
    clue leaves her where she was, so every later line is posted somewhere
    she is not standing. That is the incentive against lying in a clue."""
    lines = honest()
    for i, line in enumerate(lines):
        if line.text.startswith("CLUE"):
            _, _, where = line.text.split()
            lines[i] = S.Line(line.room, HER, f"CLUE in_oceania {where}")
            break
    result = S.settle(lines, her=HER)
    assert result["reputation"] == 0
    assert any("not live" in v["why"] for v in result["verdicts"])


def test_a_move_that_is_not_on_a_route_is_refused():
    lines = honest()
    far = next(n for n in WORLD.descriptors
               if n not in WORLD.exits(START) and n != START)
    for i, line in enumerate(lines):
        if line.text.startswith("CLUE"):
            hint = line.text.split()[1]
            lines[i] = S.Line(line.room, HER,
                              f"CLUE {hint} {token_for(SEED, far)}")
            break
    result = S.settle(lines, her=HER)
    assert any("no route to" in v["why"] for v in result["verdicts"])


def test_a_room_cannot_be_emptied_twice():
    lines = honest()
    take = next(i for i, l in enumerate(lines) if l.text == "TAKE")
    lines.insert(take + 1, S.Line(lines[take].room, HER, "TAKE"))
    result = S.settle(lines, her=HER)
    assert any("already emptied" in v["why"] for v in result["verdicts"])


def test_her_lines_are_hers():
    """Nothing settles from another key. A searcher who posts `TAKE` has
    written talk."""
    lines = honest()
    for i, line in enumerate(lines):
        if line.text == "TAKE":
            lines[i] = S.Line(line.room, "a searcher", "TAKE")
            break
    result = S.settle(lines, her=HER)
    assert any("not her key" in v["why"] for v in result["verdicts"])


def test_nothing_malformed_is_ever_repaired():
    """A `CLUE` with one argument is not read as the two-argument line it
    nearly was, however obvious the intent."""
    lines = honest()
    for i, line in enumerate(lines):
        if line.text.startswith("CLUE"):
            lines[i] = S.Line(line.room, HER, "CLUE " + line.text.split()[1])
            break
    result = S.settle(lines, her=HER)
    assert any("takes a hint and a workspace" in v["why"]
               for v in result["verdicts"])
    assert result["reputation"] == 0


def test_her_own_report_of_capture_is_conclusive():
    lines = honest()
    lines.insert(-1, S.Line(lines[2].room, HER, "CAUGHT"))
    result = S.settle(lines, her=HER)
    assert result["outcome"] == "caught"
    assert "herself" in result["why"]


def test_an_unrefuted_claim_catches_her_and_a_refuted_one_costs_the_ranking():
    """*"Her report that she was caught is conclusive. A searcher's report
    is a claim she may refute"*, and a disputed capture is kept, counted and
    never ranked."""
    lines = honest()
    room = lines[2].room
    claimed = lines[:-1] + [S.Line(room, "a searcher", "CLAIM"), lines[-1]]
    assert S.settle(claimed, her=HER)["outcome"] == "caught"

    both = lines[:-1] + [S.Line(room, "a searcher", "CLAIM"),
                         S.Line(room, HER, "REFUTE"), lines[-1]]
    result = S.settle(both, her=HER)
    assert result["disputed"] and not result["ranked"]


def test_she_cannot_claim_her_own_capture_as_a_searcher():
    lines = honest()
    lines.insert(-1, S.Line(lines[2].room, HER, "CLAIM"))
    result = S.settle(lines, her=HER)
    assert any("searcher's line" in v["why"] for v in result["verdicts"])


def test_talk_settles_nothing():
    lines = honest()
    noise = [S.Line(S.LOBBY, "a searcher", "she is heading east I think"),
             S.Line(lines[2].room, "a liar", "TAKE everything, she is here")]
    result = S.settle(lines[:2] + noise + lines[2:], her=HER)
    honest_result = S.settle(honest(), her=HER)
    assert result["reputation"] == honest_result["reputation"]
    assert result["outcome"] == honest_result["outcome"]
