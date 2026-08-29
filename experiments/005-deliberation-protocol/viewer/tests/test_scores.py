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
import statistics
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
    # Measured, not assumed: the corpus already contains rounds the ranking
    # drops for its own reasons -- a relaunched session is a different
    # population and is never ranked -- and this test is about the *one* round
    # it marks, not about how many others happen to be unrankable today.
    before = scores.boards(rows)["totals"]
    # The newest round, so the assertion about the feed is about being unranked
    # rather than about being old enough to fall off it.
    newest = max(rows, key=lambda r: r.get("played_at") or r["recorded_at"])
    assert newest["status"] == "complete", "the round marked must start rankable"
    newest["status"] = "absent"
    data = scores.boards(rows)

    assert data["totals"]["rounds"] == len(rows) == before["rounds"]
    assert data["totals"]["ranked"] == before["ranked"] - 1
    assert (data["totals"]["not_ranked"].get("absent", 0)
            == before["not_ranked"].get("absent", 0) + 1)
    # It is still an attempt on its level and still in the feed. It is only
    # kept out of the ranking.
    key = scores.level(newest)
    island = next(i for i in data["islands"] if tuple(i["level"]) == key)
    assert island["attempts"] > island["ranked"]
    assert any(r["round_id"] == newest["round_id"] for r in data["recent"])
    # Each of these rounds is its own game, so the unranked one cannot be
    # holding the level.
    assert island["game_id"] != newest["game"]["id"]


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


def test_a_cache_built_by_an_older_ranking_is_ignored(tmp_path):
    """The record can be unchanged while the rule for reading it is not.

    A cache keyed only on the ledger serves the old order forever after a
    ranking change, which is the same trap the board digest fell into.
    """
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    cache = ledger.with_name(scores.CACHE)
    held = json.loads(cache.read_text())
    held["boards"]["totals"]["rounds"] = 9999
    held["boards_v"] = scores.BOARDS_V - 1     # same ledger, older rule
    cache.write_text(json.dumps(held))
    assert scores.read_boards(ledger)["totals"]["rounds"] != 9999


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


# --- a game is one attempt, and may be more than one round ------------------


def _grouped(tmp_path, size, *, finished=True):
    """A ledger whose rounds are declared as games of `size` rounds."""
    ledger = tmp_path / "ledger.jsonl"
    for path in RECORDS[:3]:
        scores.ingest(path, ledger=ledger)
    rows = scores.load(ledger)
    for i, row in enumerate(rows):
        row["game"] = {"id": f"g{i // size}", "rounds": size}
    if not finished:
        rows = rows[:-1]                     # last game is a round short
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return ledger, rows


def test_a_round_that_nobody_grouped_is_a_game_of_one(tmp_path):
    """The default is a format, not a placeholder for a missing answer."""
    ledger = tmp_path / "ledger.jsonl"
    scores.ingest(RECORDS[0], ledger=ledger)
    row = scores.load(ledger)[0]
    assert row["game"] == {"id": row["round_id"], "rounds": 1}

    played = scores.games(scores.load(ledger))
    assert len(played) == 1
    assert played[0]["rounds"] == 1 and played[0]["finished"]
    # A game of one scores the round it is, untouched by any averaging.
    assert played[0]["eff_round"] == row["eff_round"]
    assert played[0]["ratios"] == row["ratios"]


def test_a_game_of_several_rounds_scores_their_median(tmp_path):
    ledger, rows = _grouped(tmp_path, 3)
    played = {g["game_id"]: g for g in scores.games(scores.load(ledger))}
    assert played, "no games were grouped"

    for gid, game in played.items():
        members = [r for r in rows if r["game"]["id"] == gid]
        assert game["rounds"] == len(members)
        assert game["eff_round"] == pytest.approx(
            statistics.median([m["eff_round"] for m in members]))
        # Each round scored against its own island first, then the median --
        # not the capture of an averaged island that nobody played.
        assert game["capture"] == pytest.approx(statistics.median(
            [scores.captured(m["eff_round"], m["autarky_floor"]) for m in members]))
        for slot, value in game["ratios"].items():
            assert value == pytest.approx(
                statistics.median([m["ratios"][slot] for m in members]))


def test_an_unfinished_game_is_kept_counted_and_not_ranked(tmp_path):
    """Abandoning the rounds that went badly is the cheapest way to launder a
    median, so a game short of what it declared cannot be ranked."""
    ledger, rows = _grouped(tmp_path, 3, finished=False)
    played = scores.games(scores.load(ledger))
    short = [g for g in played if not g["finished"]]
    assert len(short) == 1
    assert short[0]["rounds"] < short[0]["declared"]

    data = scores.boards(scores.load(ledger))
    assert data["totals"]["unfinished_games"] == 1
    assert data["totals"]["games"] == len(played)          # kept in the count
    assert data["totals"]["ranked"] == len(played) - 1     # out of the ranking
    ranked_ids = {i["game_id"] for i in data["islands"]}
    assert short[0]["game_id"] not in ranked_ids


def test_a_player_is_ranked_on_their_best_game(tmp_path):
    ledger, rows = _grouped(tmp_path, 3)
    rows = scores.load(ledger)
    for row in rows:
        for p in row["players"]:
            p["id"] = f"player-{p['slot']}"
    data = scores.boards(rows)
    assert data["traders"], "no players ranked"
    bests = [t["best"] for t in data["traders"]]
    assert bests == sorted(bests, reverse=True)
    for t in data["traders"]:
        # A game count, not a round count: the row is about attempts.
        assert t["games"] >= 1
        assert t["rounds"] >= t["games"]
        assert t["worst"] <= t["median"] <= t["best"]


def test_the_level_is_the_format_and_not_the_island(tmp_path):
    """Two rounds on different seeds, same shape, are the same challenge.

    The island is drawn per round, so a seed is a roll. What makes two rolls
    comparable is `capture`, not sharing a seed.
    """
    a = {"island": {"seed": 1, "agents": 2, "goods": 4, "episodes": 3}}
    b = {"island": {"seed": 9, "agents": 2, "goods": 4, "episodes": 3}}
    c = {"island": {"seed": 1, "agents": 4, "goods": 4, "episodes": 3}}
    assert scores.level(a) == scores.level(b)
    assert scores.level(a) != scores.level(c)
    assert "traders" in scores.level_label(scores.level(a))
    assert "island" not in scores.level_label(scores.level(a))


def test_capture_puts_two_islands_on_one_scale():
    """Autarky is 0 and the frontier is 1, whatever the island had on offer."""
    assert scores.captured(0.9, 0.8) == pytest.approx(0.5)
    assert scores.captured(0.8, 0.8) == pytest.approx(0.0)
    # Worse than not trading is a real outcome and is not clamped.
    assert scores.captured(0.734, 0.823) == pytest.approx(-0.5028, abs=1e-4)
    # An island with nothing on the table cannot be failed at.
    assert scores.captured(1.0, 1.0) == 1.0
    assert scores.captured(None, 0.5) is None


def test_a_high_raw_efficiency_can_be_a_worse_game(tmp_path):
    """The reason the board ranks on capture at all.

    These are two real rows from the recorded rounds: the higher raw efficiency
    is the one where the traders ended up worse off than never trading.
    """
    poor = scores.captured(0.734, 0.823)      # looked fourth-best on a raw board
    good = scores.captured(0.657, 0.523)      # looked fifth
    assert 0.734 > 0.657                       # raw efficiency says one thing
    assert good > 0 > poor                     # what was on the table says another


def test_a_game_spanning_levels_is_not_on_a_level_board(tmp_path):
    """A median across different islands is not a score on either of them."""
    ledger = tmp_path / "ledger.jsonl"
    for path in RECORDS:
        scores.ingest(path, ledger=ledger)
    rows = scores.load(ledger)
    mixed = [r for r in rows if scores.level(r) != scores.level(rows[0])][:1]
    assert mixed, "no round on a different format to build a mixed game from"
    for row in (rows[0], mixed[0]):
        row["game"] = {"id": "mixed", "rounds": 2}

    played = {g["game_id"]: g for g in scores.games(rows)}
    assert played["mixed"]["level"] is None
    assert played["mixed"]["eff_round"] is not None   # it still has a score
    data = scores.boards(rows)
    assert "mixed" not in {i["game_id"] for i in data["islands"]}


# --- a level is a format, and the goods are part of it ----------------------
#
# Added when the island gained a fifth good. `level()` already read the goods
# count, so a five-good round is a different challenge and lands on its own
# leaderboard -- but "already correct" is worth an assertion, because the
# alternative is 72 four-good rounds silently sharing a board with a game
# played against a different frontier.

def test_a_five_good_round_is_its_own_level():
    four = {"island": {"agents": 2, "goods": 4, "episodes": 3}}
    five = {"island": {"agents": 2, "goods": 5, "episodes": 3}}
    assert scores.level(four) != scores.level(five)
    # The fourth slot is episode length, added when it turned out a 60s game
    # and a 120s game were being ranked as one level. `None` here because
    # these rows predate the field -- see the clock tests below.
    assert scores.level(five) == (2, 5, 3, None)
    assert "5 goods" in scores.level_label(scores.level(five))


def test_adding_a_five_good_level_leaves_the_recorded_ones_alone():
    """Every round on disk keeps the level it was played at.

    **Reshaped 2026-08-29**, and the reshape is the point of it. It used to
    assert `all(key[1] == 4)` over the whole ledger -- true only for as long as
    nobody played a five-good round -- and its own comment said that when that
    stopped being true the test was the wrong shape, not the ledger. Four
    five-good rounds arrived with `fab5419` and it went red, and **nothing
    noticed through the three pull requests merged after it**, because this
    suite had never run in CI. It is the failure that started
    `.github/workflows/tests.yml:viewer-python`.

    The shape it should always have had is the one the docstring claims: a
    round's level reports the goods it was actually played over, and rounds
    over different goods never share a board. That holds whatever is on disk
    tomorrow.
    """
    rows = scores.load(scores.LEDGER)
    if not rows:
        pytest.skip("no ledger to read")
    for row in rows:
        assert scores.level(row)[1] == row["island"]["goods"], (
            "a round's level must report the goods it was played over")
    by_goods = {}
    for row in rows:
        by_goods.setdefault(row["island"]["goods"], set()).add(scores.level(row))
    assert 4 in by_goods, "the four-good rounds are still on four-good levels"
    seen = [key for keys in by_goods.values() for key in keys]
    assert len(seen) == len(set(seen)), (
        "no level key is shared by rounds played over different goods")


# --- the official score, and who may have one ---------------------------------
#
# What a spectator is shown the moment a game ends. The rule these test is the
# standing one: the weaker thing is kept, is counted, and is never allowed to
# look like the stronger one -- so a practice game keeps its numbers, stays in
# every denominator, and has no place.

def _ledger_of(tmp_path, n=3, **rowfix):
    ledger = tmp_path / "ledger.jsonl"
    for path in RECORDS[:n]:
        scores.ingest(path, ledger=ledger)
    rows = scores.load(ledger)
    for row in rows:
        row.update(rowfix)
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return ledger, rows


def test_a_practice_game_keeps_its_numbers_and_never_gets_a_place(tmp_path):
    """The correction of 2026-08-28. `games/island.md` has said from the start
    that a practice game is never ranked and the run record has said
    `practice: true`; nothing in this file read either, so the board ranked
    them. A rule that lives only in prose is one the code does not have."""
    ledger, rows = _ledger_of(tmp_path)
    played = scores.games(scores.load(ledger))
    one = played[0]
    assert scores.is_ranked(one), "a sealed game is ranked"

    _, rows = _ledger_of(tmp_path, arm="practice")
    played = scores.games(scores.load(ledger))
    assert [scores.why_not_ranked(g) for g in played] == ["practice"] * len(played)

    data = scores.boards(scores.load(ledger))
    assert data["totals"]["ranked"] == 0
    # Kept and counted: out of the ranking is not out of the record.
    assert data["totals"]["games"] == len(played)
    assert data["totals"]["rounds"] == len(rows)
    assert data["totals"]["held_out"] == {"practice": len(played)}

    told = scores.standing(scores.load(ledger), played[0]["game_id"])
    assert told["ranked"] is False and told["why"] == "practice"
    assert told["capture"] is not None, "the score is kept, only the place goes"
    assert "place" not in told


def test_a_game_with_a_heuristic_seat_is_kept_counted_and_never_ranked(tmp_path):
    """An NPC fills a seat so a table one short is played instead of lapsing
    (`games/island/npc.py`), and the game it plays is not the game the board
    ranks: `eff_round` against a fixed policy is a different challenge from
    `eff_round` against somebody's agent. It is a separate reason from
    `practice` because it says something different -- this round could have
    sealed perfectly well, and one of the players was arithmetic.
    """
    ledger, rows = _ledger_of(tmp_path)
    assert all(scores.is_ranked(g) for g in scores.games(scores.load(ledger)))

    _, rows = _ledger_of(tmp_path, npcs={"npc-1": "greedy=1"})
    played = scores.games(scores.load(ledger))
    assert [scores.why_not_ranked(g) for g in played] == ["heuristic"] * len(played)

    data = scores.boards(scores.load(ledger))
    assert data["totals"]["ranked"] == 0
    assert data["totals"]["games"] == len(played)
    assert data["totals"]["held_out"] == {"heuristic": len(played)}

    told = scores.standing(scores.load(ledger), played[0]["game_id"])
    assert told["ranked"] is False and told["why"] == "heuristic"
    assert told["capture"] is not None, "the score is kept, only the place goes"


def test_a_table_of_agents_says_so_by_saying_nothing(tmp_path):
    """The flag has to default to absent, or every game recorded before NPCs
    existed would be held out of the ranking retrospectively."""
    ledger, _ = _ledger_of(tmp_path)
    for game in scores.games(scores.load(ledger)):
        assert game["npcs"] == []
        assert scores.why_not_ranked(game) is None


def test_the_official_score_is_the_place_among_the_same_format(tmp_path):
    """What the ending shows: this game's capture, and where it stands among
    the games that played its own format -- never against another format."""
    ledger, _ = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    everything = scores.games(rows)
    # A level with more than one score on it, and no two of them equal: ties
    # are a real case and get their own test below.
    by_level = {}
    for g in everything:
        by_level.setdefault(tuple(g["level"]), []).append(g)
    played = sorted(next(v for v in by_level.values()
                         if len(v) > 1 and len({g["capture"] for g in v}) == len(v)),
                    key=lambda g: -g["capture"])
    best, worst = played[0], played[-1]

    top = scores.standing(rows, best["game_id"])
    assert top["ranked"] and top["place"] == 1 and top["first"] is True
    assert top["of"] == len(played)
    assert top["capture"] == best["capture"] == top["best"]
    assert top["label"] == scores.level_label(tuple(best["level"]))

    last = scores.standing(rows, worst["game_id"])
    assert last["place"] == len(played) and last["first"] is False
    assert last["best"] == best["capture"], "the leader is named, not implied"

    # A seat is placed among every seat that played this format, because a
    # ratio is a pure number against that trader's own baseline.
    field = sum(len(g["ratios"]) for g in played)
    assert all(t["of"] == field and 1 <= t["place"] <= field
               for t in top["traders"])


def test_two_games_that_captured_the_same_share_a_place(tmp_path):
    """Breaking a tie by when it was recorded would rank the clock."""
    ledger, _ = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    by_capture = {}
    for g in scores.games(rows):
        by_capture.setdefault((tuple(g["level"]), g["capture"]), []).append(g)
    tied = max(by_capture.values(), key=len)
    assert len(tied) > 1, "no tie in the fixtures to test against"

    places = [scores.standing(rows, g["game_id"])["place"] for g in tied]
    assert len(set(places)) == 1, "the same result was given different places"


def test_a_game_the_ledger_never_saw_has_no_standing(tmp_path):
    ledger, _ = _ledger_of(tmp_path, n=1)
    assert scores.standing(scores.load(ledger), "no-such-game") is None


def test_the_all_time_high_is_the_best_game_and_says_what_it_beat(tmp_path):
    """One headline number, and enough beside it that it cannot mislead.

    Nothing makes two formats comparable, so the record is the biggest score in
    the book rather than first place in a league of every format -- and the
    field it actually beat has to travel with it, or a record set on a format
    only one game ever played reads like a record that beat everybody.
    """
    ledger, _ = _ledger_of(tmp_path)
    data = scores.boards(scores.load(ledger))
    best = data["best_ever"]
    ranked = [g for g in scores.games(scores.load(ledger)) if scores.is_ranked(g)]

    assert best["capture"] == max(g["capture"] for g in ranked)
    assert best["game_id"] == data["games"][0]["game_id"]
    assert best["place"] == 1
    # Both denominators: the field it is the best *of*, and the smaller field it
    # actually *beat*. A record set on a format only one game ever played must
    # not read like a record that beat everybody.
    same = [g for g in ranked if g["level"] == best["level"]]
    assert best["of_all"] == len(ranked)
    assert best["first_of"] == len(same) <= best["of_all"]


def test_the_games_board_places_each_game_inside_its_own_format(tmp_path):
    """The list is sorted so a person can read down it; the *place* is the
    number that means something, and it never crosses a format."""
    ledger, _ = _ledger_of(tmp_path)
    board = scores.boards(scores.load(ledger))["games"]
    assert board, "no ranked game to place"
    assert [g["capture"] for g in board] == sorted(
        (g["capture"] for g in board), reverse=True)

    by_level = {}
    for g in board:
        by_level.setdefault(tuple(g["level"]), []).append(g)
    for entries in by_level.values():
        assert all(g["of"] == len(entries) for g in entries)
        assert min(g["place"] for g in entries) == 1
        for g in entries:
            ahead = sum(1 for p in entries if p["capture"] > g["capture"] + 1e-12)
            assert g["place"] == ahead + 1


def test_the_week_board_is_the_same_rules_over_the_last_seven_days(tmp_path):
    """A second view of one record, never a second record.

    The window is counted back from the newest round rather than from the clock
    on the machine: the site is static and is rebuilt when somebody publishes
    it, so a window measured from build time would empty itself on a quiet week
    without a game having been played.
    """
    ledger, rows = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    newest = max(r["played_at"] or r["recorded_at"] for r in rows)

    # Push every round but one well outside the window.
    old = "2020-01-01T00:00:00+00:00"
    for row in rows[1:]:
        row["played_at"] = old
    rows[0]["played_at"] = newest
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    data = scores.boards(scores.load(ledger))
    week = data["week"]
    assert week["days"] == scores.RECENT_DAYS
    assert week["since"] < newest
    assert week["counts"]["rounds"] == 1
    assert len(week["games"]) <= 1
    # All time still holds everything: the week narrows the view, not the record.
    assert data["totals"]["rounds"] == len(rows)
    assert len(data["games"]) >= len(week["games"])


def test_a_round_with_no_time_stays_out_of_the_week_and_in_the_record(tmp_path):
    """A row that cannot be placed in a week is not given a date it does not
    have -- it keeps its place all-time, where it is comparable."""
    ledger, _ = _ledger_of(tmp_path, n=1)
    rows = scores.load(ledger)
    for row in rows:
        row["played_at"] = None
        row["recorded_at"] = "2020-01-01T00:00:00+00:00"
    ledger.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    rows = scores.load(ledger)

    assert scores.within(rows[0], None) is True
    assert scores.within(rows[0], "2026-01-01T00:00:00+00:00") is False
    data = scores.boards(rows)
    assert data["totals"]["rounds"] == len(rows)


def test_a_players_best_game_is_one_a_spectator_can_go_and_look_at(tmp_path):
    """A number with nothing behind it is a number nobody can check."""
    ledger, _ = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    data = scores.boards(rows)
    played = {g["game_id"]: g for g in scores.games(rows)}
    for row in data["traders"]:
        game = played[row["best_game"]]
        assert row["best"] == pytest.approx(max(game["ratios"].values()), abs=5e-5) \
            or row["best"] in [round(v, 4) for v in game["ratios"].values()]
        assert row["best_level"] == scores.level_label(tuple(game["level"]))


def test_the_best_player_overall_is_the_top_of_the_players_board(tmp_path):
    """The other overall record, and the one that really is across formats.

    A player's score is a multiple of what *they* would have had alone, which is
    a number about them rather than about the island they drew -- so unlike a
    game's capture it can be read across every format at once. What it still
    cannot say is that every format is equally easy to post a big ratio on, so
    the record names the one it was set on and the games behind it.
    """
    ledger, _ = _ledger_of(tmp_path)
    data = scores.boards(scores.load(ledger))
    who = data["best_player"]

    assert who["id"] == data["traders"][0]["id"]
    assert who["best"] == max(t["best"] for t in data["traders"])
    # It names the game it was set on, and that game is on the board.
    held = next(g for g in data["games"] if g["game_id"] == who["best_game"])
    assert who["level"] == held["level"]
    assert who["id"] in who["with"]
    # And the record says how much is behind it: one game and forty games are
    # different claims for the same number.
    assert who["games"] >= 1 and who["levels"] >= 1


def test_both_overall_records_are_computed_for_the_week_too(tmp_path):
    """The headline follows the window, so it can never be an all-time number
    wearing this week's label."""
    ledger, _ = _ledger_of(tmp_path)
    data = scores.boards(scores.load(ledger))
    for window in (data, data["week"]):
        assert (window["best_ever"] is None) == (not window["games"])
        assert (window["best_player"] is None) == (not window["traders"])
        if window["best_ever"]:
            assert window["best_ever"]["capture"] == window["games"][0]["capture"]
            assert window["best_player"]["best"] == window["traders"][0]["best"]


# --- what retention keeps -----------------------------------------------------
#
# "Keep the latest 100 and the best 1000", Gal, 2026-08-28. Two ceilings whose
# union survives; the ledger row survives either way, so what is at stake is
# whether a game can still be watched, never whether it counted.

def test_the_latest_are_kept_whatever_they_scored(tmp_path):
    ledger, _ = _ledger_of(tmp_path, arm="practice")
    rows = scores.load(ledger)
    played = scores.games(rows)
    assert not any(scores.is_ranked(g) for g in played), "all unranked here"

    # Unranked games have no score to be best by, so merit keeps none of them.
    assert scores.keepers(rows, latest=0, best=100) == set()
    # Recency does not care: a game played an hour ago is the one somebody is
    # asking about, whatever it scored and whether it could be scored at all.
    newest = max(played, key=lambda g: g.get("played_at") or "")
    assert newest["game_id"] in scores.keepers(rows, latest=1, best=0)


def test_the_best_are_kept_after_they_stop_being_recent(tmp_path):
    ledger, _ = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    ranked = sorted((g for g in scores.games(rows) if scores.is_ranked(g)),
                    key=lambda g: -g["capture"])
    champion = ranked[0]

    # Nothing is recent enough; the top game survives on merit alone.
    kept = scores.keepers(rows, latest=0, best=1)
    assert champion["game_id"] in kept


def test_best_is_drawn_level_by_level_so_no_format_crowds_another_out(tmp_path):
    """Capture compares two islands, never two formats. A single ranked list
    would fill with whichever format is easiest to score well on and evict
    every game of the harder ones."""
    ledger, _ = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    levels = {tuple(g["level"]) for g in scores.games(rows) if scores.is_ranked(g)}
    assert len(levels) > 1, "no second format in the fixtures to be crowded out"

    kept = scores.keepers(rows, latest=0, best=len(levels))
    got = {tuple(g["level"]) for g in scores.games(rows) if g["game_id"] in kept}
    assert got == levels, "a format lost its champion to another format's field"


def test_the_two_sets_are_a_union_and_the_same_ledger_keeps_the_same_games(tmp_path):
    ledger, _ = _ledger_of(tmp_path)
    rows = scores.load(ledger)
    latest_only = scores.keepers(rows, latest=2, best=0)
    best_only = scores.keepers(rows, latest=0, best=2)
    both = scores.keepers(rows, latest=2, best=2)
    assert both == latest_only | best_only

    # Deterministic: two hosts holding one record must prune to the same set,
    # so nothing here may depend on dict order or on when a row was read.
    assert both == scores.keepers(list(reversed(rows)), latest=2, best=2)


# --- episode length is part of the level ------------------------------------


def _lvl_row(seconds, episodes=8):
    return {"island": {"agents": 2, "goods": 5, "episodes": episodes,
                       **({"seconds": seconds} if seconds is not None else {})}}


def test_two_clocks_are_two_levels():
    """**The fault this fixes.** A 60s game and a 120s game with the same
    traders, goods and episodes were one level competing for one best. 002
    measured that difference moving `capture` from -1.42 to -0.41 -- larger
    than most gaps `level` exists to keep apart.
    """
    assert scores.level(_lvl_row(60)) != scores.level(_lvl_row(120))


def test_the_same_clock_is_still_the_same_level():
    assert scores.level(_lvl_row(60)) == scores.level(_lvl_row(60))


def test_a_row_from_before_the_field_existed_is_its_own_level():
    """Not backfilled to 60: run 002 deliberately ran at 150s, so assuming
    the default would put two different challenges back in one bucket."""
    assert scores.level(_lvl_row(None)) != scores.level(_lvl_row(60))
    assert scores.level(_lvl_row(None))[3] is None


def test_the_label_says_which_clock_it_was():
    assert "120s episodes" in scores.level_label(scores.level(_lvl_row(120)))
    assert "unstated" in scores.level_label(scores.level(_lvl_row(None)))
