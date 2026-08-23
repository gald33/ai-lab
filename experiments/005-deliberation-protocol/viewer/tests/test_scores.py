"""The ledger, against the records it claims to summarise.

    python -m pytest viewer/tests/test_scores.py -q

A leaderboard is only worth having if a row can be defended a year later, so
what is tested here is mostly refusal: that a row cannot be written when the
record and the seed disagree, that re-ingesting cannot duplicate a round, that
a tampered row is caught, and that no round is ever dropped from a denominator.

The load-bearing one is `test_ratios_match_the_recorded_gains`: the per-trader
score is recomputed here from the seed and the trajectory, and it has to come
out equal to the gains the manager recorded at the time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import scores  # noqa: E402

RESULTS = HERE.parent.parent / "results"
RECORDS = sorted(RESULTS.glob("*/v3.json"))


def rounds():
    for path in RECORDS:
        record = json.loads(path.read_text())
        for rnd in record.get("rounds", []):
            yield path, record, rnd


def test_there_are_records_to_test_against():
    assert RECORDS, "no v3.json to read; this file would pass vacuously"


@pytest.mark.parametrize("path,record,rnd", list(rounds()),
                         ids=[r["workspace"] for _, _, r in rounds()])
def test_every_recorded_round_scores_the_same_twice(path, record, rnd):
    """Scored once here from the seed, and once by the manager at the time.

    `island.score` records only the median and the worst of the per-trader
    ratios, so those are what can be checked -- but both are computed from the
    whole vector, so a ratio wrong for any trader moves one of them.

    One round, one scoring: the frontier search is the expensive part of this
    file, and doing it twice per round to make two prettier tests would double
    the suite for nothing.
    """
    row = scores.entry(record, rnd, source=path)
    recorded = rnd["score"]
    assert row["eff_round"] == pytest.approx(recorded["eff_round"], abs=1e-6)
    assert row["autarky_floor"] == pytest.approx(recorded["autarky_floor"], abs=1e-6)

    ratios = sorted(row["ratios"].values())
    mid = len(ratios) // 2
    median = ratios[mid] if len(ratios) % 2 else 0.5 * (ratios[mid - 1] + ratios[mid])
    assert ratios[0] == pytest.approx(recorded["gain_worst"], abs=1e-6)
    assert median == pytest.approx(recorded["gain_median"], abs=1e-6)


def test_a_record_that_disagrees_with_its_seed_is_refused():
    """The one thing a ledger must never do is write down a number it was told.

    A run record claiming an efficiency its own seed cannot produce is either a
    different island or an edited file, and both are refusals.
    """
    path, record, rnd = next(rounds())
    tampered = json.loads(json.dumps(rnd))
    tampered["score"]["eff_round"] = 0.999
    with pytest.raises(ValueError, match="disagree about which island"):
        scores.entry(record, tampered, source=path)


def test_a_round_with_no_closed_episode_cannot_be_scored():
    path, record, rnd = next(rounds())
    empty = {**rnd, "trajectory": []}
    with pytest.raises(ValueError, match="no closed episode"):
        scores.entry(record, empty, source=path)


def test_the_id_is_the_round_not_the_moment_it_was_read():
    path, record, rnd = next(rounds())
    first = scores.entry(record, rnd, source=path)
    second = scores.entry(record, rnd, source=path)
    assert first["round_id"] == second["round_id"]
    assert first["recorded_at"] is not None
    # A different island, or a different outcome on it, is a different round.
    moved = {**rnd, "seed": rnd["seed"] + 1}
    assert scores.round_id(moved["workspace"], moved["seed"], moved["trajectory"]) \
        != first["round_id"]


def test_ingesting_twice_does_not_duplicate(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    added, skipped = scores.ingest(RECORDS[0], ledger=ledger)
    assert added and not skipped
    again_added, again_skipped = scores.ingest(RECORDS[0], ledger=ledger)
    assert not again_added
    assert len(again_skipped) == len(added)
    assert len(scores.load(ledger)) == len(added)


def test_verify_catches_an_edited_row(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    assert scores.verify(ledger) == []
    rows = scores.load(ledger)
    rows[0]["eff_round"] = 0.99
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    problems = scores.verify(ledger)
    assert len(problems) == 1
    assert "recomputes to" in problems[0]


def test_a_round_nobody_reached_is_not_a_round_somebody_lost():
    """Absent and relaunched rounds stay in the file, and out of the ranking."""
    assert scores.status({"spoke": ["T1", "T2"]}, ["T1", "T2"]) == "complete"
    assert scores.status({"spoke": ["T1"]}, ["T1", "T2"]) == "absent"
    assert scores.status({"spoke": ["T1", "T2"], "relaunched": ["T2"]},
                         ["T1", "T2"]) == "relaunched"


def test_denominators_keep_what_the_ranking_drops(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    for path in RECORDS:
        scores.ingest(path, ledger=ledger)
    rows = scores.load(ledger)
    # The newest round, so the assertion about the feed is about being unranked
    # rather than about being old enough to fall off it.
    newest = max(rows, key=lambda r: r.get("played_at") or r["recorded_at"])
    newest["status"] = "absent"
    data = scores.boards(rows)

    assert data["totals"]["rounds"] == len(rows)
    assert data["totals"]["ranked"] == len(rows) - 1
    assert data["totals"]["not_ranked"] == {"absent": 1}
    # It is still an attempt on its level and still in the feed. It is only
    # kept out of the ranking.
    key = scores.level(newest)
    island = next(i for i in data["islands"] if tuple(i["level"]) == key)
    assert island["attempts"] > island["ranked"]
    assert any(r["round_id"] == newest["round_id"] for r in data["recent"])
    assert island["round_id"] != newest["round_id"]


def test_a_player_is_ranked_on_the_median_not_the_best(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    for path in RECORDS:
        scores.ingest(path, ledger=ledger)
    rows = scores.load(ledger)
    for row in rows:                      # one player per slot, whatever the table size
        for p in row["players"]:
            p["id"] = f"player-{p['slot']}"
    data = scores.boards(rows)
    slots = {p["slot"] for row in rows for p in row["players"]}
    assert {t["id"] for t in data["traders"]} == {f"player-{s}" for s in slots}
    for t in data["traders"]:
        assert t["rounds"] == sum(1 for r in rows
                                  if any(p["id"] == t["id"] for p in r["players"]))
        assert t["worst"] <= t["median"] <= t["best"]
        assert 0 <= t["below_autarky"] <= t["rounds"]
    # Sorted by median, and the denominator travels with the number.
    medians = [t["median"] for t in data["traders"]]
    assert medians == sorted(medians, reverse=True)


# --- keeping many rounds affordable -----------------------------------------


def test_the_boards_are_read_from_a_cache_and_the_cache_follows_the_record(tmp_path):
    """Reading the boards must not cost a full parse of every round ever played."""
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    cache = ledger.with_name(scores.CACHE)
    assert cache.is_file(), "ingest should leave the derived boards behind it"

    first = scores.read_boards(ledger)
    assert first["totals"]["rounds"] == len(scores.load(ledger))

    # A round arriving has to move the boards, not be masked by the cache.
    scores.ingest(RECORDS[1], ledger=ledger)
    second = scores.read_boards(ledger)
    assert second["totals"]["rounds"] > first["totals"]["rounds"]

    # And the cache is derived, never authoritative: damaged, it is rebuilt.
    cache.write_text("{ not json")
    assert scores.read_boards(ledger)["totals"] == second["totals"]


def test_a_stale_cache_is_ignored(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    cache = ledger.with_name(scores.CACHE)
    held = json.loads(cache.read_text())
    held["boards"]["totals"]["rounds"] = 9999
    held["stamp"] = [["ledger.jsonl", 1, 1]]
    cache.write_text(json.dumps(held))
    assert scores.read_boards(ledger)["totals"]["rounds"] != 9999


def test_dedupe_reads_ids_not_rounds(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    assert scores.seen(ledger) == {r["round_id"] for r in scores.load(ledger)}
    # Without the index, and with a stale one, the answer is the same.
    ledger.with_name(scores.INDEX).write_text('{"stamp": [], "round_ids": []}')
    assert scores.seen(ledger) == {r["round_id"] for r in scores.load(ledger)}


def test_a_rolled_off_ledger_part_is_still_read(tmp_path):
    """Old rounds can be gzipped and set aside; they stay in the boards."""
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    scores.ingest(RECORDS[1], ledger=ledger)
    everything = scores.load(ledger)

    rows = everything[:1]
    keep = everything[1:]
    import gzip
    with gzip.open(tmp_path / "ledger-old.jsonl.gz", "wt") as fh:
        fh.write("\n".join(json.dumps(r) for r in rows) + "\n")
    ledger.write_text("\n".join(json.dumps(r) for r in keep) + "\n")

    assert len(scores.parts(ledger)) == 2
    assert len(scores.load(ledger)) == len(everything)
    assert scores.seen(ledger) == {r["round_id"] for r in everything}


def test_packing_a_board_keeps_it_readable_and_keeps_its_identity(tmp_path):
    """A packed board is the same board: same digest, same messages, one file."""
    results = tmp_path / "results" / "v3"
    results.mkdir(parents=True)
    original = next(RESULTS.rglob("board-*.json"))
    target = results / original.name
    target.write_bytes(original.read_bytes())
    before = scores.digest(target)

    assert scores.pack(tmp_path / "results") == 0
    assert not target.is_file()
    packed = target.with_suffix(".json.gz")
    assert packed.is_file()
    assert packed.stat().st_size < original.stat().st_size

    # Asked for by its unpacked name, which is what every reader and every
    # saved link uses.
    assert scores.read_board(target)["messages"] == json.loads(original.read_text())["messages"]
    # The digest is of the contents, so packing must not make `--verify` claim
    # the board it came from has changed.
    assert scores.digest(target) == before


def test_a_row_from_an_older_ledger_is_not_reported_as_tampering(tmp_path, capsys):
    """Changing how a row is built must not look like ten boards changing.

    It did once: `digest` moved from hashing a board's bytes to hashing its
    contents, and every stored digest became unreproducible at the same moment.
    A version on the row is what tells "built differently" from "changed".
    """
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    rows = scores.load(ledger)
    for row in rows:
        row["v"] = scores.SCHEMA - 1
        row["source"]["board_sha256"] = "0" * 16
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    assert scores.verify(ledger) == []
    assert "older ledger version" in capsys.readouterr().err
