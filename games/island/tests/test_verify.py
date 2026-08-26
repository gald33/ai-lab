"""The checker, against boards that hold together and boards that do not.

Every failing case here is a way a manager could favour somebody. The point of
the checker is that each one leaves a mark in the record, so these are written
as tampering rather than as malformed input.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from games.island import verify

NONCE = "ab" * 8
SEATS = {"T1": "1111111111111111", "T2": "2222222222222222"}


def _seed(nonce=NONCE, seats=SEATS):
    material = "|".join([nonce] + sorted(seats.values()))
    return int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big") >> 1


def _reveal(**over):
    payload = {
        "seed": _seed(),
        "traders": {
            "T1": {"capacity": {"bread": 2.0, "cloth": 1.0}, "taste": {}},
            "T2": {"capacity": {"bread": 1.0, "cloth": 4.0}, "taste": {}},
        },
        "seat_keys": {"T1": "key-one", "T2": "key-two"},
        "round": {"seed": _seed(), "workspace": "w", "trajectory": [[0.1, 0.2]]},
        "draw": {"method": "commit-reveal", "nonce": NONCE,
                 "commit": hashlib.sha256(NONCE.encode()).hexdigest(),
                 "seat_nonces": dict(SEATS)},
    }
    payload.update(over)
    return payload


def _line(seq, author, body, key=None):
    signature = {"status": "verified", "key": key} if key else {"status": "unsigned"}
    return {"seq": seq, "at": f"2026-08-26T05:0{seq}:00Z", "author": author,
            "body": body, "signature": signature}


def _board(**over):
    messages = [
        _line(1, "T1", "PRODUCE bread=0.5 cloth=0.5", "key-one"),
        _line(2, "manager", "@T1 produced {'bread': 1.0, 'cloth': 0.5}; 0.0 labour unspent"),
        _line(3, "T2", "PRODUCE bread=0.25 cloth=0.75", "key-two"),
        _line(4, "manager", "@T2 produced {'bread': 0.25, 'cloth': 3.0}; 0.0 labour unspent"),
        _line(5, "T1", "PROPOSE to=T2 give=bread:0.1 want=cloth:0.2", "key-one"),
        _line(6, "manager", "p1: T1 offers {'bread': 0.1} to T2 for {'cloth': 0.2} — open until the bell"),
        _line(7, "T2", "APPROVE p1", "key-two"),
        _line(8, "manager", "p1 settled: T1 and T2 exchanged {'bread': 0.1} for {'cloth': 0.2}"),
        _line(9, "manager", "bell — episode 1 closed. 0 proposal(s) lapsed."),
    ]
    board = {"workspace": "w", "channel": "island", "messages": messages}
    board.update(over)
    return board


def _run(tmp_path, board=None, reveal=None):
    b, r = tmp_path / "board-w.json", tmp_path / "reveal-w.json"
    b.write_text(json.dumps(board or _board()))
    r.write_text(json.dumps(reveal or _reveal()))
    return verify.verify(b)


def test_a_board_that_holds_together_passes_and_says_how_much_it_checked(tmp_path):
    report = _run(tmp_path)

    assert report.passed, report.failures
    assert report.checks["production"][0] >= 4
    assert report.checks["exchange"] == [1, 1]
    assert report.checks["draw"] == [2, 2]
    assert report.checks["authorship"][0] == 4, "every seat line, checked"


def test_a_receipt_that_does_not_equal_share_times_capacity_fails(tmp_path):
    """The manager credited somebody more than their labour bought."""
    board = _board()
    board["messages"][1]["body"] = (
        "@T1 produced {'bread': 1.9, 'cloth': 0.5}; 0.0 labour unspent")

    report = _run(tmp_path, board)

    assert not report.passed
    assert any("receipt says 1.9" in f for f in report.failures)


def test_a_settlement_that_moves_more_than_the_offer_named_fails(tmp_path):
    board = _board()
    board["messages"][7]["body"] = (
        "p1 settled: T1 and T2 exchanged {'bread': 0.1} for {'cloth': 0.9}")

    report = _run(tmp_path, board)

    assert not report.passed
    assert any("offered" in f and "settled" in f for f in report.failures)


def test_a_line_attributed_to_a_seat_it_did_not_come_from_fails(tmp_path):
    board = _board()
    board["messages"][4]["signature"]["key"] = "key-two"  # T1's line, T2's key

    report = _run(tmp_path, board)

    assert not report.passed
    assert any("another seat's key" in f for f in report.failures)


def test_a_seed_that_is_not_what_the_nonces_make_fails(tmp_path):
    """A manager that re-rolled its island until it liked one."""
    report = _run(tmp_path, reveal=_reveal(seed=12345))

    assert not report.passed
    assert any("the nonces make seed" in f for f in report.failures)


def test_a_nonce_that_does_not_match_the_commitment_fails(tmp_path):
    reveal = _reveal()
    reveal["draw"]["nonce"] = "ff" * 8

    report = _run(tmp_path, reveal=reveal)

    assert not report.passed
    assert any("does not hash to the commitment" in f for f in report.failures)


def test_bells_out_of_order_fail(tmp_path):
    board = _board()
    board["messages"].append(_line(10, "manager", "bell — episode 3 closed."))
    reveal = _reveal()
    reveal["round"]["trajectory"] = [[0.1, 0.2], [0.3, 0.4]]

    report = _run(tmp_path, board, reveal)

    assert not report.passed
    assert any("episode 3 closed after episode 1" in f for f in report.failures)


def test_a_sealed_round_says_which_arithmetic_it_could_not_redo(tmp_path):
    """Sealing hides the shares on purpose, so the checker must report that
    rather than passing as though it had checked them."""
    board = _board()
    board["messages"][0]["body"] = "SEALED abcdef"
    board["messages"][2]["body"] = "SEALED 123456"

    report = _run(tmp_path, board)

    assert report.passed
    assert any("sealed PRODUCE line" in s for s in report.skipped)


def test_a_game_with_no_reveal_beside_it_cannot_be_checked_at_all(tmp_path):
    board = tmp_path / "board-w.json"
    board.write_text(json.dumps(_board()))

    report = verify.verify(board)

    assert not report.passed
    assert any("no reveal sidecar" in f for f in report.failures)
