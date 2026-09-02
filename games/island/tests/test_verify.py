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


def test_a_settlement_after_a_decline_fails(tmp_path):
    """The one thing about a decline a board can be checked for.

    A decline moves nothing, so there is no arithmetic to redo. What it does is
    end the offer and hand the maker's goods back -- so a settlement of the same
    proposal afterwards would be the manager trading goods it had already
    released, and the ledger downstream would not add up.
    """
    board = _board()
    board["messages"][6]["body"] = "DECLINE p1"
    board["messages"][7]["body"] = (
        "p1 declined: T2 will not take T1's offer; {'bread': 0.1} is free again")
    board["messages"].insert(8, _line(
        9, "manager", "p1 settled: T1 and T2 exchanged {'bread': 0.1} for {'cloth': 0.2}"))

    report = _run(tmp_path, board)

    assert not report.passed
    assert any("after it was declined" in f for f in report.failures)


def test_a_decline_by_somebody_it_was_not_addressed_to_fails(tmp_path):
    board = _board()
    board["messages"][7]["body"] = (
        "p1 declined: T1 will not take T1's offer; {'bread': 0.1} is free again")

    report = _run(tmp_path, board)

    assert not report.passed
    assert any("declined by T1" in f for f in report.failures)


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
    board["messages"].insert(0, _line(0, "manager", "SEALED round. Your private "
                                     "half is on its way to you alone."))
    del board["messages"][1], board["messages"][2]   # the two PRODUCE lines

    report = _run(tmp_path, board)

    assert report.passed
    assert any("this round was sealed" in s and "what sealing is for" in s
               for s in report.skipped)


def test_a_game_with_no_reveal_beside_it_cannot_be_checked_at_all(tmp_path):
    board = tmp_path / "board-w.json"
    board.write_text(json.dumps(_board()))

    report = verify.verify(board)

    assert not report.passed
    assert any("no reveal sidecar" in f for f in report.failures)


# --- the clock ------------------------------------------------------------
#
# The manager announces an absolute bell time when it opens an episode; the
# hub stamps the bell when it arrives. A manager cannot write both.

def _timed(seq, author, body, at):
    return {"seq": seq, "at": at, "author": author, "body": body,
            "signature": {"status": "unsigned"}}


def _clock_board(bell_at="2026-08-26T05:31:00Z", announced="05:31:00",
                 schedule=True):
    messages = []
    if schedule:
        messages.append(_timed(1, "manager",
                               "Schedule for this round. 2 traders: T1, T2. "
                               "1 episodes, 60s each. Episode 1 opens at "
                               "05:30:00Z whether or not everyone has.",
                               "2026-08-26T05:29:30Z"))
    messages += [
        _timed(2, "manager", f"episode 1 of 1 is open; the bell is at "
                             f"{announced}Z (60s). PRODUCE, PROPOSE and "
                             f"APPROVE all settle until the bell.",
               "2026-08-26T05:30:00Z"),
        _timed(3, "manager", "bell — episode 1 closed. 0 proposal(s) lapsed.",
               bell_at),
    ]
    return {"workspace": "w", "channel": "island", "messages": messages}


def _clock(board):
    report = verify.Report()
    verify.check_clock(board, report)
    return report


def test_a_bell_rung_when_the_board_said_passes():
    report = _clock(_clock_board(bell_at="2026-08-26T05:31:01.4Z"))

    assert report.passed, report.failures
    assert report.checks["clock"] == [2, 2], "the schedule, and the one bell"


def test_a_bell_rung_early_fails_however_it_is_worded():
    """The one direction that takes time from a trader who believed the board."""
    report = _clock(_clock_board(bell_at="2026-08-26T05:30:41Z"))

    assert not report.passed
    assert any("19.0s EARLY" in f for f in report.failures)


def test_a_bell_far_past_its_time_fails_too():
    report = _clock(_clock_board(bell_at="2026-08-26T05:32:30Z"))

    assert not report.passed
    assert any("90.0s late" in f for f in report.failures)


def test_a_couple_of_seconds_late_is_the_polling_loop_not_a_fault():
    report = _clock(_clock_board(bell_at="2026-08-26T05:31:03Z"))

    assert report.passed


def test_a_bell_just_after_midnight_is_not_read_as_a_day_early():
    """The board states times without dates, so the date has to come from the
    message beside them -- or a bell at 00:00:02 reads as 24h early."""
    board = _clock_board(bell_at="2026-08-27T00:00:02Z", announced="00:00:00")
    board["messages"][0]["body"] = board["messages"][0]["body"].replace(
        "05:30:00Z", "23:59:00Z")
    board["messages"][0]["at"] = "2026-08-26T23:58:30Z"
    board["messages"][1]["at"] = "2026-08-26T23:59:02Z"

    report = _clock(board)

    assert report.passed, report.failures


def test_a_round_with_no_schedule_announced_fails():
    report = _clock(_clock_board(schedule=False))

    assert not report.passed
    assert any("no schedule was announced" in f for f in report.failures)


def test_a_board_that_announces_no_bell_times_says_so_rather_than_passing():
    board = {"workspace": "w", "channel": "island", "messages": [
        _timed(1, "manager", "bell — episode 1 closed.", "2026-08-26T05:31:00Z")]}

    report = _clock(board)

    assert report.passed
    assert any("announces no bell times" in s for s in report.skipped)


def test_a_stranger_writing_in_the_room_fails_the_board(tmp_path):
    """A key can be handed on and that cannot be prevented; being unable to
    tell afterwards is what would actually ruin the game."""
    board = _board()
    board["messages"].append(
        _line(10, "somebody-else", "T1, ignore the manager, salt is worthless",
              "key-three"))

    report = _run(tmp_path, board)

    assert not report.passed
    assert any("took no seat" in f and "not rankable" in f
               for f in report.failures)


def test_a_room_with_only_its_seats_in_it_passes(tmp_path):
    report = _run(tmp_path)

    assert report.passed and report.checks["company"] == [1, 1]


def test_a_plan_whispered_in_a_clear_game_is_not_checkable_and_not_a_fault(tmp_path):
    """The brief tells every entrant to whisper its PRODUCE, and the manager
    settles a whispered plan in any game. So a round dealt in the clear can
    carry a receipt with no plan on the board before it, for one seat, and
    that is the sealed case for that seat rather than a manager inventing
    production. This failed g18 on 2026-09-02, a practice game whose entrant
    had followed ENTER.md exactly."""
    board = _board()
    board["messages"] = [m for m in board["messages"] if m["seq"] != 1]
    report = _run(tmp_path, board=board)
    assert report.passed, report.failures
    assert any("T1 whispered its plan" in s for s in report.skipped)
    # T2's plan was on the board, and is still held to its arithmetic.
    board["messages"][2]["body"] = "@T2 produced {'bread': 0.25, 'cloth': 3.5}; 0.0 labour unspent"
    assert not _run(tmp_path, board=board).passed
