"""The ledger: what every finished round scored, kept across rounds.

A game needs a number that survives the round it was won in. This is that
number, and the whole file is about being able to defend it later.

**A game is one attempt, and may be more than one round.** A round is what the
manager runs -- `k` episodes on one island -- and that vocabulary does not move.
A *game* is the unit somebody enters: one round, or several played as a single
attempt. A one-round game is a legitimate format and its score is that round; a
several-round game scores the **median** of its rounds, so within a declared
format the luck evens out while a lucky game still tops the board.

The rounds in a game have to be declared as one **before they are played**, or
the median is worthless: ten rounds played and the best three called "a game"
afterwards is cherry-picking with a statistic on top. The runner is what stamps
that, at launch, next to where it binds identities -- nothing an agent says
about which game it is in can be believed. Until joining exists nothing declares
a game, so every recorded round is a one-round game, which is why the boards
below read the same as they did before this existed.

**Two scores, because there are two things being played.**

*The island scored.* **`capture`** -- how much of the gains that were actually
*on this island* got taken, with autarky at 0.0 and the frontier at 1.0. It
belongs to the whole set of traders rather than to any one of them.

Not raw `eff_round`, and the difference decides games. Two islands are not
equally hard: one where autarky already scores 0.823 has almost nothing on the
table, and one where it scores 0.599 has a great deal. Ranking on raw efficiency
therefore ranks the draw. On the rounds recorded here it puts a disaster above
several successes -- a 0.734 whose floor was 0.823 sits fourth on a raw board,
while those traders ended up substantially worse off than if they had never
traded. `barter.economy.capture` already exists and already makes this argument;
this uses it rather than restating it. Negative is not clamped, because doing
worse than not trading is a real outcome and one of the more interesting ones.

What makes two scores comparable is playing the **same level**, and the level is
the **format** -- the number of traders, the goods, the episodes. Not the seed:
the island is drawn per round, so a seed is a roll rather than a level, and four
traders face a different frontier from two while thirty episodes is more room to
learn than three.

*A trader scored.* `u_i / autarky_i` -- what they ended with as a multiple of
what they would have had alone. Raw Cobb-Douglas utilities are not comparable
between traders (each is defined only up to its own monotone transformation), so
"T1 got more than T2" means nothing; "T1 ended at 1.4x what it would have had
alone" means something, and those ratios *are* comparable, being pure numbers
against a per-trader baseline. `barter.economy.gains` is where that argument
lives and this reuses it rather than restating it.

**Nothing here trusts anybody.** Every figure is recomputed from the run record
and the round's seed: the island is redrawn, autarky is resolved, and the
recorded `eff_round` is checked against a fresh one before an entry is written.
No agent's account of how it did is read, and no model is in the loop.

**Ranked, or kept and counted and not ranked.** `why_not_ranked` is the one
place that decides, and it names each reason apart from the others rather than
folding them into a flag: `practice`, `company`, `unfinished`, `not_scored`.
The boards ask it and so does `standing`, which is what a spectator is shown
the instant a game ends -- one rule, so the leaderboard and the ending cannot
give one game two official scores.

**The ledger is append-only and each entry is reproducible.** An entry carries
its seed, its trajectory and the digest of the board it came from, so any row
can be re-derived years later by somebody who does not trust this file.

    python viewer/scores.py --ingest results/v3/v3.json      # add finished rounds
    python viewer/scores.py --table                          # the boards
    python viewer/scores.py --verify                         # recompute every row
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))
sys.path.insert(0, str(HERE.parent))

from barter.economy import autarky, draw_island  # noqa: E402

from island.score import score as score_round  # noqa: E402

LEDGER = HERE / "scores" / "ledger.jsonl"

#: The experiments tree. A ledger that only holds one experiment's rounds is a
#: leaderboard of who remembered to run the ingest command, so run records from
#: anywhere in the repo are ingestable -- and a row from outside this experiment
#: has to store a path that still resolves in somebody else's checkout, which is
#: what this is for. Rows already written stay relative to the experiment and
#: are still read: `resolve` tries both.
ROOT = HERE.parent.parent

#: The checkout above it. Three rows in the ledger name `games/results/g1.json`
#: -- the island's own games, whose run records are not in the repository -- and
#: a path from outside the experiments tree has to be resolvable for the day one
#: of them is.
REPO = ROOT.parent

#: Reading the ledger is O(rounds) and computing the boards is O(rounds); doing
#: both per request is a page that gets slower every time somebody plays. The
#: record stays append-only and cold, and what the page actually reads is a
#: derived file the size of the boards themselves -- rewritten when rounds are
#: added, and rebuilt on demand if it ever falls behind the record.
#:
#: Measured on this machine at 72,000 rounds: 4.6 s to parse plus 0.9 s to
#: compute, against a 16 KiB answer that does not grow. The cache is the whole
#: difference between those two numbers and one file read.
CACHE = "boards.json"
INDEX = "index.json"

#: How a row is built. Bumped when that changes in a way `verify` would
#: otherwise report as tampering -- when `digest` moved from hashing a board's
#: bytes to hashing its contents, every stored digest became unreproducible, and
#: an unversioned ledger reports that as ten boards having changed. A row that
#: predates the current version is re-ingestable, not suspect, and the
#: difference has to be visible.
SCHEMA = 2

#: How the boards are computed. The cache is keyed on the ledger *and* on this,
#: because a ranking rule that changes while the record does not is exactly the
#: case where a cache keyed only on the record serves the old order forever.
#: Bump it when `boards` changes what it produces.
BOARDS_V = 8

#: How far back "this week" reaches, counted from the newest round in the
#: record rather than from the clock on the machine building the page.
RECENT_DAYS = 7

#: The recorded score and a freshly computed one will not match to the last bit
#: -- they are the same arithmetic on the same numbers, so this is float noise
#: and nothing else. A gap above this means the record and the seed disagree
#: about what island was played, which is a refusal, not a rounding.
TOLERANCE = 1e-6


def round_id(workspace: str, seed: int, trajectory: list[list[float]]) -> str:
    """A name for this round that two people computing it separately agree on.

    Deliberately not a timestamp or a counter: re-ingesting the same run record
    must land on the same id, or the ledger grows a duplicate every time
    somebody runs the command twice.
    """
    payload = json.dumps({"workspace": workspace, "seed": seed,
                          "trajectory": trajectory}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def relative(path: Path | None) -> str | None:
    """Paths are stored relative to the checkout, not to whoever ran this.

    A ledger row has to still resolve when it is read from another checkout, or
    `--verify` degrades into "the file moved" for every row. Inside this
    experiment the path stays relative to the experiment, which is what every
    row written before rounds from elsewhere were ingestable already says;
    outside it, relative to the repository.
    """
    if not path:
        return None
    resolved = path.resolve()
    for base in (HERE.parent, ROOT, REPO):
        try:
            return resolved.relative_to(base).as_posix()
        except ValueError:
            continue
    return str(path)


def resolve(stored: str | None) -> Path | None:
    """A stored path, read back. Tried against both bases, experiment first."""
    if not stored:
        return None
    for base in (HERE.parent, ROOT, REPO):
        candidate = base / stored
        if candidate.is_file() or candidate.with_suffix(
                candidate.suffix + ".gz").is_file():
            return candidate
    return HERE.parent / stored


def read_board(path: Path) -> dict | None:
    """A saved board, whether or not it has been packed, in either shape.

    `--pack` gzips boards in place, so every reader has to accept both names or
    packing a directory quietly breaks the tools that read it.

    Two shapes, because two runners wrote them. This experiment saves
    `{"messages": [...]}` beside its run record with `at` on each row; 006 and
    007 save the room's rows as a bare list under `boards/`, with `created_at`.
    They are the same board, so they are read into the same shape here rather
    than every caller learning both. A dict board is returned untouched: its
    `digest` is already in rows that have been written down, and normalising it
    would report every one of them as changed.
    """
    for candidate in (path, path.with_suffix(path.suffix + ".gz")):
        if candidate.is_file():
            try:
                raw = (gzip.decompress(candidate.read_bytes())
                       if candidate.name.endswith(".gz") else candidate.read_bytes())
                saved = json.loads(raw)
            except (ValueError, OSError):
                return None
            if isinstance(saved, list):
                return {"messages": [{"seq": m.get("seq"),
                                      "at": m.get("created_at") or m.get("at"),
                                      "from": str(m.get("from") or "?"),
                                      "body": m.get("body"),
                                      "workspace": m.get("workspace")}
                                     for m in saved]}
            return saved if isinstance(saved, dict) else None
    return None


#: Boards found by reading them, kept per directory. Without it a sweep re-reads
#: every board in a run for every round in that run.
_BOARD_INDEX: dict[Path, dict[str, Path]] = {}


def board_for(source: Path, workspace: str) -> Path | None:
    """The board this round was played on, in either place it might be kept.

    Beside the run record as `board-<workspace>.json`, which is what this
    experiment writes; or in a `boards/` directory next to it under a name built
    from the arm and the seed, which is what 006 and 007 write. The second
    cannot be found by name, so it is found by reading: every row of those
    boards carries the workspace it belongs to.
    """
    beside = source.with_name(f"board-{workspace}.json")
    if beside.is_file() or beside.with_suffix(".json.gz").is_file():
        return beside

    folder = source.parent / "boards"
    if folder not in _BOARD_INDEX:
        index: dict[str, Path] = {}
        for candidate in sorted(folder.glob("*.json*")) if folder.is_dir() else []:
            saved = read_board(candidate)
            for row in (saved or {}).get("messages", []):
                if row.get("workspace"):
                    index.setdefault(row["workspace"], candidate)
                    break
        _BOARD_INDEX[folder] = index
    return _BOARD_INDEX[folder].get(workspace)


def played_at(board: Path | None, rnd: dict | None = None,
              now: str | None = None) -> tuple[str | None, str | None]:
    """When the round actually ran, and where that answer came from.

    `recorded_at` is when somebody typed the ingest command, which may be months
    later; a feed sorted by that is a list of when files were touched, and a
    "this week" board built on it would call a game from March a game from
    Tuesday. So the date is taken from the round itself, best source first:

    - **the board** -- the last thing said in the room, exact to the second;
    - **`run_stamp`** -- the manager's own `MMDDThhmm` for the round, which is
      all there is when the board was not kept. It carries no year, so the year
      comes from when the row is being written, stepped back once if that puts
      the round in the future.

    The source is returned with the answer and stored beside it, because a date
    good to the minute from a stamp and a date read off the board are not the
    same evidence, and a page that showed both as a bare timestamp would be
    claiming the weaker one is the stronger.
    """
    saved = read_board(board) if board else None
    stamps = [m.get("at") for m in (saved or {}).get("messages", []) if m.get("at")]
    if stamps:
        return max(stamps), "board"

    stamp = (rnd or {}).get("run_stamp")
    if isinstance(stamp, str) and len(stamp) == 9 and stamp[4] == "T":
        end = datetime.fromisoformat(now) if now else datetime.now(timezone.utc)
        try:
            ran = datetime(end.year, int(stamp[:2]), int(stamp[2:4]),
                           int(stamp[5:7]), int(stamp[7:]), tzinfo=timezone.utc)
        except ValueError:
            return None, None
        if ran > end:                      # a stamp that has not happened yet
            ran = ran.replace(year=end.year - 1)   # belongs to last year
        return ran.isoformat(timespec="seconds"), "run_stamp"
    return None, None


def digest(path: Path | None) -> str | None:
    """Of the board's contents, not of the file that happens to hold them.

    Packing a board rewrites the file and must not invalidate the row that came
    from it, so this hashes the messages rather than the bytes on disk.
    """
    saved = read_board(path) if path else None
    if saved is None:
        return None
    return hashlib.sha256(
        json.dumps(saved, sort_keys=True).encode()).hexdigest()[:16]


def entry(record: dict, rnd: dict, *, players: dict[str, str] | None = None,
          source: Path | None = None) -> dict:
    """One finished round, scored from its own record and its own seed."""
    seed = rnd["seed"]
    agents = record.get("agents", 2)
    goods = record.get("goods", 4)
    trajectory = rnd.get("trajectory") or []
    if not trajectory:
        # Either no episode ever closed, or the round never started: 006 and 007
        # write a round that failed to launch as `{"failed": true, "error": ...}`
        # with no workspace and no trajectory at all. Both are kept and neither
        # is ranked, and the reason travels with the row.
        raise ValueError(f"{rnd.get('workspace') or 'a round that never started'}: "
                         + (str(rnd.get("error")) if rnd.get("failed")
                            else "a round with no closed episode cannot be scored"))

    island = draw_island(agents, goods, seed=seed)
    names = [f"T{i + 1}" for i in range(agents)]
    fresh = score_round(island, trajectory)

    # The recorded number is the one that was scored at the time; the fresh one
    # is this file's own reading of the same trajectory. They have to agree
    # before anything is written down.
    recorded = rnd.get("score") or {}
    if "eff_round" in recorded and abs(recorded["eff_round"] - fresh.eff_round) > TOLERANCE:
        raise ValueError(
            f"{rnd.get('workspace')}: recorded eff_round {recorded['eff_round']} "
            f"but seed {seed} gives {fresh.eff_round:.6f} -- the record and the "
            f"seed disagree about which island was played")

    _, auto = autarky(island)
    k = len(trajectory)
    totals = [sum(row[i] for row in trajectory) for i in range(agents)]
    # The same construction `island.score` uses: the round's accumulated vector
    # rescaled onto the one-episode frontier, then read against autarky.
    ratios = [(totals[i] / k) / auto[i] for i in range(agents)]

    board = board_for(source, rnd["workspace"]) if source else None
    kept = board is not None
    recorded = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ran, ran_from = played_at(board, rnd, recorded)
    who = players or {}
    # Which attempt this round belongs to. Declared by whatever ran it; a round
    # nobody grouped is a game of one, which is a real format and not a default
    # standing in for a missing answer.
    game = rnd.get("game") or record.get("game") or {}
    rid = round_id(rnd["workspace"], seed, trajectory)
    return {
        "v": SCHEMA,
        "round_id": rid,
        "game": {"id": game.get("id", rid), "rounds": int(game.get("rounds", 1))},
        "played_at": ran,
        # `board`, `run_stamp`, or absent when the round says nothing about when
        # it ran. Never inferred from when somebody typed the ingest command.
        "played_from": ran_from,
        "recorded_at": recorded,
        "workspace": rnd["workspace"],
        "arm": rnd.get("arm"),
        # Seat -> the policy mix it declared, for every heuristic player at
        # this table. Read off the board by `run_game.record`, so a round
        # re-ingested from an old result file has it and one re-read from the
        # board reaches the same answer. Empty for a table of agents.
        "npcs": rnd.get("npcs") or {},
        "island": {"seed": seed, "agents": agents, "goods": goods, "episodes": k,
                   "seconds": record.get("episode_seconds")},
        "players": [{"slot": n,
                     "id": who.get(n, record.get("model", "unknown")),
                     "model": record.get("model")} for n in names],
        # The table's score.
        "eff_round": round(fresh.eff_round, 6),
        "eff_round_upper": round(fresh.eff_round_upper, 6),
        "autarky_floor": round(fresh.floor, 6),
        "eff_episode": [round(x, 6) for x in fresh.eff_episode],
        # Each trader's, as a multiple of what they would have had alone.
        "ratios": {n: round(r, 6) for n, r in zip(names, ratios)},
        "utility_total": {n: round(t, 6) for n, t in zip(names, totals)},
        "autarky_utility": {n: round(a, 6) for n, a in zip(names, auto)},
        "zero_episodes": {n: sum(1 for row in trajectory if row[i] <= 1e-12)
                          for i, n in enumerate(names)},
        # Kept whole so any row can be re-derived without this file's arithmetic.
        "trajectory": trajectory,
        "traffic": {"settled": rnd.get("settled"), "refused": rnd.get("refused"),
                    "talk": rnd.get("talk")},
        # Whether anybody who took no seat wrote in this room. A room key can
        # be handed on and that cannot be prevented; what can be done is to
        # notice, and a round played through interference is kept, counted and
        # never ranked rather than quietly scored. Absent in older records,
        # which is why this reads the list rather than trusting a flag.
        "company": len(rnd.get("intrusions") or []),
        "intruders": rnd.get("intruders", []),
        # A round nobody reached is not a round somebody lost. It stays in the
        # ledger and in every denominator, and it is never ranked.
        "status": status(rnd, names),
        # Older records predate the manager's `spoke` set, so attendance cannot
        # be classified for them at all. That is different from classifying it
        # as fine, and the boards say how many rows are in that position.
        "attendance": "recorded" if "spoke" in rnd else "unrecorded",
        "acknowledged": rnd.get("acknowledged", []),
        "spoke": rnd.get("spoke", []),
        "source": {"result": relative(source),
                   "board": relative(board) if kept else None,
                   "board_sha256": digest(board)},
    }


def status(rnd: dict, names: list[str]) -> str:
    """Complete, or a fault that is not the players' doing.

    A session that never joined and a trader that chose to say nothing are
    different events, and a leaderboard that ranks them the same is scoring the
    harness. `spoke` is the manager's own record of who ever reached the board.
    """
    if rnd.get("relaunched"):
        return "relaunched"
    spoke = set(rnd.get("spoke", names))
    if not spoke.issuperset(set(names)):
        return "absent"
    return "complete"


def level(row: dict) -> tuple:
    """What has to match for two rounds to be the same challenge.

    The format, not the island. The seed is drawn per round, so it is the roll
    and not the level -- and `capture` is what makes two rolls comparable, by
    scoring each against what its own island had on the table.
    """
    i = row["island"]
    # **Episode length is part of the format and was missing from it.** A 60s
    # game and a 120s game with the same traders, goods and episode count were
    # ranked as one challenge and competed for the same best; the only trace
    # of the difference was prose inside a board message. 002 measured that
    # difference moving `capture` from -1.42 to -0.41, which is larger than
    # most gaps this function exists to keep apart.
    #
    # `None` for a row recorded before the field existed, and NOT backfilled to
    # 60: run 002 deliberately ran at 150s, so "it was probably the default" is
    # exactly the kind of guess that would put two different challenges back in
    # one bucket. An unstated length is its own bucket and says so.
    return (i["agents"], i["goods"], i["episodes"], i.get("seconds"))


def level_label(key: tuple) -> str:
    agents, goods, episodes = key[0], key[1], key[2]
    seconds = key[3] if len(key) > 3 else None
    clock = f"{seconds}s episodes" if seconds else "episode length unstated"
    return f"{agents} traders · {goods} goods · {episodes} episodes · {clock}"


def captured(eff_round: float | None, floor: float | None) -> float | None:
    """Gains taken as a fraction of gains available: autarky 0, frontier 1.

    Derived rather than stored: both halves are already in the row, and a
    number that can be recomputed from the record should be.
    """
    if eff_round is None or floor is None:
        return None
    if 1.0 - floor <= 1e-12:
        return 1.0
    return (eff_round - floor) / (1.0 - floor)


def parts(path: Path = LEDGER) -> list[Path]:
    """Every file the ledger is made of, oldest name first.

    A ledger that keeps every round played is a file that only grows, so older
    parts can be rolled off and gzipped -- `ledger-2026-08.jsonl.gz` beside
    `ledger.jsonl` -- and are read back the same way. Appends always go to the
    live part.
    """
    if not path.parent.is_dir():
        return []
    stem = path.name.split(".")[0]
    found = [p for p in path.parent.iterdir()
             if p.name.startswith(stem)
             and (p.name.endswith(".jsonl") or p.name.endswith(".jsonl.gz"))]
    return sorted(found, key=lambda p: p.name)


def _lines(path: Path):
    if path.name.endswith(".gz"):
        with gzip.open(path, "rt") as fh:
            yield from fh
    else:
        yield from path.read_text().splitlines()


def load(path: Path = LEDGER) -> list[dict]:
    return [json.loads(line) for part in parts(path)
            for line in _lines(part) if line.strip()]


def stamp(path: Path = LEDGER) -> list:
    """What the cache was built from. Cheap enough to check on every request."""
    return [[p.name, p.stat().st_size, p.stat().st_mtime_ns] for p in parts(path)]


def read_boards(path: Path = LEDGER) -> dict:
    """The boards, from the cache when it is current and from the record when not.

    Self-healing on purpose: the cache is derived, never authoritative, and
    deleting it must only ever cost one recomputation.
    """
    cache = path.with_name(CACHE)
    current = stamp(path)
    if cache.is_file():
        try:
            held = json.loads(cache.read_text())
            if held.get("stamp") == current and held.get("boards_v") == BOARDS_V:
                return held["boards"]
        except (ValueError, KeyError):
            pass                      # a damaged cache is rebuilt, not trusted
    return write_boards(path)["boards"]


def write_boards(path: Path = LEDGER) -> dict:
    rows = load(path)
    held = {"stamp": stamp(path), "boards_v": BOARDS_V,
            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "boards": boards(rows)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.with_name(CACHE).write_text(json.dumps(held, default=list))
    # Ids only: this is what ingest checks against, and it must not carry the
    # weight of a round to answer "have I seen this one".
    path.with_name(INDEX).write_text(json.dumps({
        "stamp": held["stamp"],
        "round_ids": [r["round_id"] for r in rows],
    }))
    return held


def seen(path: Path = LEDGER) -> set[str]:
    """Round ids already in the ledger, from the index when it is current."""
    index = path.with_name(INDEX)
    if index.is_file():
        try:
            held = json.loads(index.read_text())
            if held.get("stamp") == stamp(path):
                return set(held["round_ids"])
        except (ValueError, KeyError):
            pass
    return {r["round_id"] for r in load(path)}


def ingest(result: Path, *, ledger: Path = LEDGER,
           players: dict[str, str] | None = None) -> tuple[list[dict], list[dict]]:
    """Add every round in a run record that is not in the ledger already."""
    record = json.loads(result.read_text())
    have = seen(ledger)
    added, skipped = [], []
    for rnd in record.get("rounds", []):
        try:
            row = entry(record, rnd, players=players, source=result)
        except ValueError as exc:
            # A round that cannot be scored still happened. It goes in the file
            # so it stays in the denominators, and it is never ranked.
            row = unscored(record, rnd, result, str(exc))
        (skipped if row["round_id"] in have else added).append(row)
        have.add(row["round_id"])
    if added:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a") as fh:
            for row in added:
                fh.write(json.dumps(row) + "\n")
        write_boards(ledger)
    return added, skipped


def unscored(record: dict, rnd: dict, source: Path, why: str) -> dict:
    """A round that happened and cannot be scored. Kept, counted, never ranked.

    A round that never started has no workspace to be named by, and two of them
    in one run would otherwise hash to one id and be deduplicated -- which would
    quietly shrink the denominator by exactly the failures it is there to show.
    So when there is no workspace, the run it came from and the cell it was
    stands in for one.
    """
    name = rnd.get("workspace") or (f"{source.parent.name}:{rnd.get('arm')}:"
                                    f"{rnd.get('seed')}:failed")
    return {
        "v": SCHEMA,
        "round_id": (rid := round_id(name, rnd.get("seed", -1),
                                     rnd.get("trajectory") or [])),
        "game": {"id": rid, "rounds": 1},
        "played_at": None,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workspace": rnd.get("workspace"), "arm": rnd.get("arm"),
        "island": {"seed": rnd.get("seed"), "agents": record.get("agents"),
                   "goods": record.get("goods"),
                   "episodes": len(rnd.get("trajectory") or []),
                   "seconds": record.get("episode_seconds")},
        "players": [], "eff_round": None, "autarky_floor": None,
        "ratios": {}, "zero_episodes": {}, "trajectory": rnd.get("trajectory") or [],
        "status": "unscored", "why": why, "attendance": "unrecorded",
        "source": {"result": relative(source), "board": None, "board_sha256": None},
    }


def sweep(root: Path = ROOT) -> list[Path]:
    """Every run record in the tree, oldest path first.

    **A ledger that holds one experiment's rounds is a leaderboard of who
    remembered to run the ingest command.** A game that was played and scored
    but never ingested is invisible on a board that claims to hold every game,
    and invisible in the denominators too, which is worse: the page says "72
    games played" and means "72 games somebody typed a command for". So the
    sweep is the normal way to feed the ledger, and naming one record is the
    exception.

    Re-ingesting is free: a round's id is a hash of its own content, so a sweep
    adds what is new and skips what is there.
    """
    return sorted(root.glob("*/results/**/v3.json"))


def upgrade(ledger: Path = LEDGER) -> tuple[int, list[str]]:
    """Re-derive rows written by an older version of this file, in place.

    `--verify` skips a row whose schema predates the current one, because a
    field that did not exist yet is not tampering -- but a skipped row is an
    unchecked row, and a file that quietly accumulates them stops being a record
    anybody can defend. Re-ingesting cannot fix them: a round's id is a hash of
    its own content, so the sweep correctly skips a round it already holds.

    So the row is rebuilt from the run record it names, and **`recorded_at` is
    kept**: when a round was first written down is a fact about this file that
    re-deriving it must not overwrite. The id is recomputed too, and a row whose
    id moves is reported rather than replaced -- that would be a different round
    wearing an old row's name.
    """
    rows = load(ledger)
    if len(parts(ledger)) > 1:
        return 0, ["the ledger has rolled-off parts; upgrade them before packing"]
    changed, problems = 0, []
    out = []
    for row in rows:
        source = resolve((row.get("source") or {}).get("result"))
        if row.get("v") == SCHEMA or not source or not source.is_file():
            out.append(row)
            if row.get("v") != SCHEMA:
                problems.append(f"{row['round_id']}: v{row.get('v')} and its run "
                                f"record is not where the row says it is")
            continue
        record = json.loads(source.read_text())
        rnd = next((r for r in record.get("rounds", [])
                    if r.get("workspace") == row["workspace"]), None)
        if rnd is None:
            problems.append(f"{row['round_id']}: {row['workspace']} is not in "
                            f"{row['source']['result']} any more")
            out.append(row)
            continue
        try:
            fresh = entry(record, rnd, source=source)
        except ValueError as exc:
            fresh = unscored(record, rnd, source, str(exc))
        if fresh["round_id"] != row["round_id"]:
            problems.append(f"{row['round_id']}: re-derives to "
                            f"{fresh['round_id']}, which is a different round")
            out.append(row)
            continue
        fresh["recorded_at"] = row["recorded_at"]     # a fact about this file
        out.append(fresh)
        changed += 1
    if changed:
        ledger.write_text("".join(json.dumps(r) + "\n" for r in out))
        write_boards(ledger)
    return changed, problems


def verify(ledger: Path = LEDGER) -> list[str]:
    """Recompute every row from its own seed and trajectory."""
    problems = []
    stale = 0
    for row in load(ledger):
        if row["status"] == "unscored":
            continue
        if row.get("v") != SCHEMA:
            # Not a disagreement about the round -- a row built by an older
            # version of this file. Re-ingesting it is the fix.
            stale += 1
            continue
        island = draw_island(row["island"]["agents"], row["island"]["goods"],
                             seed=row["island"]["seed"])
        fresh = score_round(island, row["trajectory"])
        if abs(fresh.eff_round - row["eff_round"]) > TOLERANCE:
            problems.append(f"{row['round_id']}: eff_round {row['eff_round']} "
                            f"but recomputes to {fresh.eff_round:.6f}")
        board = row["source"].get("board")
        if board and (d := digest(resolve(board))) and d != row["source"]["board_sha256"]:
            problems.append(f"{row['round_id']}: the board it came from has changed")
    if stale:
        print(f"{stale} row(s) written by an older ledger version were not "
              f"checked; re-ingest to bring them up to v{SCHEMA}", file=sys.stderr)
    return problems


def games(rows: list[dict]) -> list[dict]:
    """Group rounds into the attempts they were played as, and score each.

    One round, one score. Several rounds declared as one game, the median of
    them -- for the table's efficiency and for every trader's ratio alike, so
    the two boards agree about what a game was worth.

    A game short of the rounds it declared is **not finished**. It is kept, it
    counts, and it is not ranked: abandoning the rounds that went badly is the
    cheapest way to launder a median, and a board that ranks partial games
    invites exactly that.
    """
    grouped: dict[str, list[dict]] = {}
    for r in rows:
        grouped.setdefault(r.get("game", {}).get("id", r["round_id"]), []).append(r)

    out = []
    for gid, members in grouped.items():
        members.sort(key=lambda r: r.get("played_at") or r["recorded_at"])
        declared = max(m.get("game", {}).get("rounds", 1) for m in members)
        scored = [m for m in members if m["status"] == "complete"]
        levels = {level(m) for m in members}
        slots = sorted({p["slot"] for m in members for p in m["players"]})

        # Each round scored against its own island first, then the median.
        # Taking the median of raw efficiencies and capturing that would be
        # scoring an average island that nobody played.
        captures = [captured(m["eff_round"], m["autarky_floor"]) for m in scored]

        ratios = {}
        for slot in slots:
            values = [m["ratios"][slot] for m in scored if slot in m["ratios"]]
            if values:
                ratios[slot] = statistics.median(values)

        out.append({
            "game_id": gid,
            "rounds": len(members),
            "declared": declared,
            # Every reason a game is not ranked, kept apart from each other.
            "finished": len(members) >= declared,
            "all_scored": len(scored) == len(members),
            # A game is only ranked if every round of it was played without
            # company. One round with a stranger writing in the room is enough
            # to hold the whole game out, because the rounds are one attempt.
            "uninterrupted": all(not m.get("company") for m in members),
            "company": sum(m.get("company", 0) for m in members),
            "level": list(levels.pop()) if len(levels) == 1 else None,
            # Which islands this game was rolled on -- one per round, since the
            # island is drawn per round rather than once per game.
            "seeds": sorted({m["island"]["seed"] for m in members}),
            "capture": statistics.median(captures) if captures else None,
            # Kept for the record and the feed. It is what was measured; it is
            # just not what two islands can be compared on.
            "eff_round": (statistics.median([m["eff_round"] for m in scored])
                          if scored else None),
            "floor": (statistics.median([m["autarky_floor"] for m in scored])
                      if scored else None),
            "ratios": ratios,
            "players": {p["slot"]: p["id"] for m in members for p in m["players"]},
            "workspace": members[0]["workspace"],
            "arm": members[0]["arm"],
            "npcs": sorted({slot for m in members
                            for slot in (m.get("npcs") or {})}),
            "played_at": members[-1].get("played_at"),
            "played_from": members[-1].get("played_from"),
            "recorded_at": members[-1]["recorded_at"],
            "round_ids": [m["round_id"] for m in members],
        })
    return out


def why_not_ranked(game: dict) -> str | None:
    """The one place that decides whether a game may be ranked, or `None`.

    Every reason is a case of the same standing rule: **the weaker thing is
    allowed, and never allowed to look like the stronger one.** Each of these
    games is kept, is counted, and stays in every denominator; what it does not
    get is a place.

    **They are two kinds of fact, not one.** `practice`, `company`,
    `unfinished` and `not_scored` are *observations of the board*: properties
    of the record that hold whether or not anybody says so. `heuristic` is
    *testimony* -- a line somebody chose to write. Switchboard is open, so a
    seat's nature is never a property; only what it signed is. The taxonomy is
    therefore incomplete on purpose, and knowing which half a reason lives in
    is the difference between a guarantee and a convention.

    - `practice` -- the table could not seal, so its private half was public.
      Every trader could read every other trader's tastes and capacities, which
      is a different game from the one being measured. **This is the correction
      of 2026-08-28**: the rule was written in `games/island.md` from the start
      and stated in the run record as `practice: true`, and the board ranked
      those games anyway because nothing here read the flag. A rule that lives
      only in prose is one the code does not have.
    - `heuristic` -- a seat was filled by an NPC rather than by an entrant's
      agent (`games/island/npc.py`). A table one seat short is played instead
      of lapsing, which is worth having; what it measures is play against a
      cheap fixed policy, and ranking that beside a game between agents would
      be ranking two different challenges as one.

      **Its limit, written down 2026-08-30**: this catches *our* filler and
      nothing else. An entrant's own heuristic bot is just an agent and ranks
      -- same fixed policy, same undeliberating trader, undetected -- so both
      reasons above are equally true of a stranger's bot that nothing here
      sees. `heuristic` means "our cheap policy played here", which is a
      narrower claim than it reads as.
    - `company` -- somebody who took no seat wrote in the room. A key can be
      handed on and that cannot be prevented; what can be done is to notice.
    - `unfinished` -- fewer rounds than the game declared. Abandoning the rounds
      that went badly is the cheapest way to launder a median.
    - `not_scored` -- some round of it could not be scored at all.
    """
    if game.get("arm") == "practice":
        return "practice"
    if game.get("npcs"):
        return "heuristic"
    if not game["uninterrupted"]:
        return "company"
    if not game["finished"]:
        return "unfinished"
    if not game["all_scored"] or game["capture"] is None:
        return "not_scored"
    return None


def is_ranked(game: dict) -> bool:
    return why_not_ranked(game) is None


def standing(rows: list[dict], game_id: str) -> dict | None:
    """One game's official score and its place, read off the whole ledger.

    This is what a spectator is shown the moment a game ends, and it exists so
    that the answer they get is **the ledger's answer**: the same `capture` the
    board ranks on, placed against the same peers, by the same rule. A page
    computing its own ranking from a reveal sidecar would be a second scoring
    surface that could disagree with the first, and the disagreement would show
    up as two different official scores for one game.

    **A place is only ever against the same level.** Two islands are not equally
    hard and neither are two formats: four traders face a different frontier
    from two, and thirty episodes is more room to learn than three. `capture`
    makes two *rolls* comparable; nothing makes two formats comparable, so a
    game is placed among the games that played its own format and nowhere else.

    A game that may not be ranked gets its numbers and no place, with the reason
    named -- never a place quietly withheld, and never a number quietly given a
    rank it did not earn.
    """
    played = games(rows)
    mine = next((g for g in played if g["game_id"] == game_id), None)
    if mine is None:
        return None

    why = why_not_ranked(mine)
    out = {
        "game_id": game_id,
        "workspace": mine["workspace"],
        "capture": mine["capture"],
        "eff_round": mine["eff_round"],
        "floor": mine["floor"],
        "level": mine["level"],
        "label": level_label(tuple(mine["level"])) if mine["level"] else None,
        "ranked": why is None,
        "why": why,
        "traders": [{"slot": slot, "id": mine["players"].get(slot),
                     "ratio": mine["ratios"].get(slot)}
                    for slot in sorted(mine["ratios"])],
    }
    if why is not None or not mine["level"]:
        return out

    # Ties share a place: two games that captured the same fraction of the same
    # format are the same result, and breaking that by recorded_at would rank
    # the clock.
    peers = [g for g in played if is_ranked(g) and g["level"] == mine["level"]]
    ahead = sum(1 for p in peers if p["capture"] > mine["capture"] + 1e-12)
    out["place"] = ahead + 1
    out["of"] = len(peers)
    out["best"] = max(p["capture"] for p in peers)
    out["first"] = ahead == 0

    # A trader's place is among every seat that played this format, not among
    # the seats of this table: a ratio is a pure number against that trader's
    # own baseline, which is exactly what makes seats comparable at all.
    field = [r for p in peers for r in p["ratios"].values()]
    for row in out["traders"]:
        if row["ratio"] is None:
            continue
        row["place"] = sum(1 for r in field if r > row["ratio"] + 1e-12) + 1
        row["of"] = len(field)
    return out


def when_played(item: dict) -> str | None:
    """When a round or a game happened, preferring the board over the ingest.

    `recorded_at` is when somebody typed the command, which may be months later,
    so a "this week" board built on it would be a list of when files were
    touched rather than of what was played lately.
    """
    return item.get("played_at") or item.get("recorded_at")


def within(item: dict, since: str | None) -> bool:
    """Whether this round or game is inside the window. No stamp, no window.

    A row with no time at all cannot be placed in a week, so it stays in the
    all-time boards -- where it is comparable -- and out of the recent one,
    rather than being given a date it does not have.
    """
    if since is None:
        return True
    stamp = when_played(item)
    return bool(stamp) and stamp >= since


def week_start(rows: list[dict], days: int = RECENT_DAYS) -> str | None:
    """The cutoff for the recent board, counted back from the last game played.

    From the newest round in the record rather than from the wall clock, so the
    page a spectator opens on a quiet Tuesday still shows the last week that had
    games in it instead of an empty board. Nothing here is served fresh anyway:
    the static site is built when somebody publishes it, and a window measured
    from build time would move every time the site was rebuilt without a round
    being played.
    """
    stamps = [s for s in (when_played(r) for r in rows) if s]
    if not stamps:
        return None
    newest = max(stamps)
    try:
        end = datetime.fromisoformat(newest.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (end - timedelta(days=days)).isoformat(timespec="seconds")


def level_rows(ranked: list[dict], played: list[dict]) -> list[dict]:
    """One row per format: who holds it, and how the field did on it."""
    levels: dict[tuple, list[dict]] = {}
    for g in ranked:
        if g["level"]:
            levels.setdefault(tuple(g["level"]), []).append(g)
    board = []
    for key, entries in sorted(levels.items()):
        best = max(entries, key=lambda e: e["capture"])
        attempts = sum(1 for g in played if g["level"] and tuple(g["level"]) == key)
        board.append({
            "level": list(key),
            "label": level_label(key),
            "agents": key[0], "goods": key[1], "episodes": key[2],
            "seconds": key[3] if len(key) > 3 else None,
            # Which islands this level has actually been rolled on, so a level
            # played once is not mistaken for a level played ten times.
            "seeds": sorted({seed for e in entries for seed in e["seeds"]}),
            "best": best["capture"],
            "best_eff_round": best["eff_round"],
            "floor": best["floor"],
            "by": [best["players"][s] for s in sorted(best["players"])],
            "workspace": best["workspace"],
            "arm": best["arm"],
            "game_id": best["game_id"],
            "game_rounds": best["rounds"],
            "played_at": best["played_at"],
            "played_from": best["played_from"],
            "recorded_at": best["recorded_at"],
            "ranked": len(entries),
            "attempts": attempts,
            # The spread says whether the best is a result or a lucky draw.
            "median": round(statistics.median([e["capture"] for e in entries]), 6),
            "worst": min(e["capture"] for e in entries),
            # How often anybody beat doing nothing at all on this format.
            "above_autarky": sum(1 for e in entries if e["capture"] > 0),
        })
    board.sort(key=lambda x: (-x["best"], x["level"]))
    return board


def game_rows(ranked: list[dict]) -> list[dict]:
    """Every ranked game, best first, each carrying its place on its own format.

    **The order is a display order, not a ranking across formats.** A place is
    only ever against the same level -- four traders face a different frontier
    from two -- so `place` and `of` are computed inside the format and the sort
    is what a person reads down. Saying both is the point: the list has to be
    orderable to be a list at all, and the number that means something has to be
    the one attached to the row.
    """
    by_level: dict[tuple, list[dict]] = {}
    for g in ranked:
        if g["level"]:
            by_level.setdefault(tuple(g["level"]), []).append(g)

    out = []
    for key, entries in by_level.items():
        for g in entries:
            # Ties share a place: two games that captured the same fraction of
            # the same format are the same result.
            ahead = sum(1 for p in entries if p["capture"] > g["capture"] + 1e-12)
            out.append({
                "game_id": g["game_id"],
                "level": list(key),
                "label": level_label(key),
                "agents": key[0], "goods": key[1], "episodes": key[2],
                "seconds": key[3] if len(key) > 3 else None,
                "capture": g["capture"],
                "eff_round": g["eff_round"],
                "floor": g["floor"],
                "place": ahead + 1,
                "of": len(entries),
                "by": [g["players"][s] for s in sorted(g["players"])],
                "rounds": g["rounds"],
                "seeds": g["seeds"],
                "workspace": g["workspace"],
                "arm": g["arm"],
                "played_at": g["played_at"],
                "played_from": g["played_from"],
                "recorded_at": g["recorded_at"],
            })
    out.sort(key=lambda x: (-x["capture"], x["label"]))
    return out


def trader_rows(ranked: list[dict], rows: list[dict]) -> list[dict]:
    """One row per player, ranked on their best game."""
    players: dict[str, dict] = {}
    for g in ranked:
        for slot, who in g["players"].items():
            if slot not in g["ratios"]:
                continue
            row = players.setdefault(who, {
                "id": who, "scores": [], "games": 0, "below": 0,
                "zero_episodes": 0, "agent_episodes": 0, "rounds": 0, "levels": set(),
                "best_game": None, "best_level": None, "last": None,
            })
            ratio = g["ratios"][slot]
            row["games"] += 1
            row["rounds"] += g["rounds"]
            row["below"] += 1 if ratio < 1.0 - 1e-9 else 0
            # Which game the top score came from, so a player's best is a game
            # a spectator can go and look at rather than a bare number.
            if not row["scores"] or ratio > max(row["scores"]):
                row["best_game"] = g["game_id"]
                row["best_level"] = (level_label(tuple(g["level"]))
                                     if g["level"] else None)
            row["scores"].append(ratio)
            row["last"] = max([t for t in (row["last"], g["played_at"]) if t],
                              default=None)
            if g["level"]:
                row["levels"].add(tuple(g["level"]))

    wanted = {rid for g in ranked for rid in g["round_ids"]}
    for r in rows:
        if r["round_id"] not in wanted:
            continue
        for p in r["players"]:
            if p["id"] in players:
                players[p["id"]]["zero_episodes"] += r["zero_episodes"].get(p["slot"], 0)
                players[p["id"]]["agent_episodes"] += r["island"]["episodes"]

    board = []
    for row in players.values():
        # The best game holds the place. A lucky island, or a partner who
        # happened to want what you could make, is what a high score is made of
        # -- and inside a game of several rounds the median has already taken
        # the luck out to whatever degree that format asked for. The rest of the
        # row says whether a top score was one game or a habit.
        board.append({
            "id": row["id"],
            "best": round(max(row["scores"]), 4),
            "median": round(statistics.median(row["scores"]), 4),
            "worst": round(min(row["scores"]), 4),
            "games": row["games"],
            "rounds": row["rounds"],
            "below_autarky": row["below"],
            "zero_episodes": row["zero_episodes"],
            "agent_episodes": row["agent_episodes"],
            "levels": len(row["levels"]),
            "best_game": row["best_game"],
            "best_level": row["best_level"],
            "last_played": row["last"],
        })
    board.sort(key=lambda x: (-x["best"], -x["median"], -x["games"]))
    return board


def board_set(rows: list[dict], played: list[dict]) -> dict:
    """The three rankings over one population of rounds.

    All-time and the recent week are the *same* boards over different rows, so
    they are computed once here and called twice. A week board with its own
    arithmetic would eventually rank differently from the all-time one, and the
    two would be right about different things.
    """
    ranked = [g for g in played if is_ranked(g)]
    return {
        "islands": level_rows(ranked, played),
        "games": game_rows(ranked),
        "traders": trader_rows(ranked, rows),
        "counts": {"games": len(played), "ranked": len(ranked),
                   "rounds": len(rows)},
    }


def best_ever(game_board: list[dict]) -> dict | None:
    """The single most successful game there has ever been, on any format.

    **It is a record, not a rank**, and the difference is the whole of this
    function. `capture` says how much of what *its own island* had on the table
    a game took, so the biggest one is a fact about the whole book: no game has
    ever taken a larger share of what was in front of it. What it is not is
    first place in a league of every format, because there is no such league --
    two formats are not one contest, and a game cannot beat a game it never had
    the chance to play against.

    So both denominators travel with it. `of_all` is every ranked game in the
    window, which is the field this is the best *of*; `first_of` is how many
    played its own format, which is the field it actually *beat*. A headline set
    on a format only one game ever played would otherwise read like a headline
    that beat everybody.
    """
    if not game_board:
        return None
    top = dict(game_board[0])
    top["first_of"] = top["of"]
    top["of_all"] = len(game_board)
    return top


def best_player(trader_board: list[dict], game_board: list[dict]) -> dict | None:
    """The best any single player has ever done, on any format.

    The one number a player's board is asked for, and it can be given honestly
    where the games board cannot: a ratio is what one trader ended with as a
    multiple of what *they* would have had alone, which is a pure number against
    their own baseline and does not carry the island it was drawn on with it.
    So this really is every format together, and not a format's number wearing
    an overall label.

    What it still cannot say is that every format is equally easy to post a big
    ratio on, so it names the one this was set on and how many games the player
    has behind it -- a 2× from a single game and a 2× from forty are different
    claims and the card has to be able to tell them apart.
    """
    if not trader_board:
        return None
    top = dict(trader_board[0])
    held = next((g for g in game_board if g["game_id"] == top["best_game"]), None)
    top["level"] = held["level"] if held else None
    top["played_at"] = held["played_at"] if held else top.get("last_played")
    top["played_from"] = held["played_from"] if held else None
    top["recorded_at"] = held["recorded_at"] if held else None
    top["with"] = held["by"] if held else []
    return top


#: What retention keeps, decided by Gal 2026-08-28: "keep the latest 100 and
#: the best 1000". Two ceilings, and what survives is their union.
LATEST, BEST = 100, 1000


def keepers(rows: list[dict], *, latest: int = LATEST, best: int = BEST) -> set[str]:
    """The game ids worth keeping the files of, newest-and-best.

    Everything else is prunable: the ledger row survives regardless, so a
    pruned game is still counted and still in every denominator -- what goes is
    the board and the reveal, which is to say the ability to *watch* it.

    **Two sets, and the union is what is kept.** `latest` is by when it was
    played and takes ranked and unranked games alike, because a game played an
    hour ago is the one somebody is asking about whatever it scored. `best` is
    by `capture` and takes ranked games only, because an unranked game has no
    score to be best by -- see `why_not_ranked`.

    **`best` is drawn level by level, not off one list.** Capture is comparable
    between two islands and *not* between two formats: a single ranked list
    would fill with whichever format is easiest to score well on, and quietly
    evict every game of the harder ones. So the best game of each level is
    taken, then the second of each, and so on until the budget is spent. Every
    format keeps its champions; no format can crowd out another's.

    The one property worth stating plainly, because it is the cost of "best":
    **a game can be evicted by a later, better game.** Nothing it did changed.
    That is why an evicted game keeps a row in the archive index rather than
    vanishing from it -- `games/island/live.py`.
    """
    played = games(rows)
    by_time = sorted(played, key=lambda g: g.get("played_at") or "", reverse=True)
    kept = {g["game_id"] for g in by_time[:max(0, latest)]}

    levels: dict[tuple, list[dict]] = {}
    for g in played:
        if is_ranked(g) and g["level"]:
            levels.setdefault(tuple(g["level"]), []).append(g)
    for ranking in levels.values():
        ranking.sort(key=lambda g: -g["capture"])

    budget = max(0, best)
    merit: list[str] = []
    for rank in range(max((len(v) for v in levels.values()), default=0)):
        if len(merit) >= budget:
            break
        # One level's rank-N game, then the next level's, in a fixed order so
        # the same ledger always keeps the same games -- a tie broken by dict
        # order would prune differently on two hosts holding one record.
        for key in sorted(levels):
            if rank < len(levels[key]) and len(merit) < budget:
                merit.append(levels[key][rank]["game_id"])
    return kept | set(merit)


def boards(rows: list[dict]) -> dict:
    """The leaderboards, with their denominators attached to them.

    Ranked entries are finished games whose every round was scorable; the counts
    say how many were not, and those games stay in the file. A board that
    quietly drops what went wrong is reporting on a population it chose after
    seeing the results.

    Two windows, the same rules: **all time**, which is every round ever played,
    and **the last week**, which is the same boards over the rounds inside
    `RECENT_DAYS` of the newest one. The week is a second view of one record and
    never a second record.
    """
    played = games(rows)
    all_time = board_set(rows, played)

    since = week_start(rows)
    recent_rows = [r for r in rows if within(r, since)]
    recent_played = [g for g in played if within(g, since)]
    week = board_set(recent_rows, recent_played)
    week["since"] = since
    week["days"] = RECENT_DAYS
    week["best_ever"] = best_ever(week["games"])
    week["best_player"] = best_player(week["traders"], week["games"])

    levels = {tuple(g["level"]) for g in played
              if g["level"] and is_ranked(g)}
    players = {who for g in played if is_ranked(g)
               for slot, who in g["players"].items() if slot in g["ratios"]}
    unfinished = sum(1 for g in played if not g["finished"])
    return {
        # The all-time boards keep the names they have always had: this is one
        # record read two ways, and a reader that only knows about `islands` and
        # `traders` still gets the all-time answer it always got.
        "islands": all_time["islands"],
        "games": all_time["games"],
        "traders": all_time["traders"],
        # The two overall records, one for a table and one for a player. They
        # are different kinds of claim and are labelled as such: the game's is
        # the biggest number in the book on a format nobody can compare to
        # another, the player's is a ratio against their own baseline and is
        # genuinely across every format.
        "best_ever": best_ever(all_time["games"]),
        "best_player": best_player(all_time["traders"], all_time["games"]),
        "week": week,
        "recent": sorted(rows, key=lambda r: r.get("played_at") or r["recorded_at"],
                         reverse=True)[:12],
        "totals": {
            "rounds": len(rows),
            "games": len(played),
            "ranked": all_time["counts"]["ranked"],
            "multi_round_games": sum(1 for g in played if g["declared"] > 1),
            "unfinished_games": unfinished,
            "not_ranked": {s: sum(1 for r in rows if r["status"] == s)
                           for s in sorted({r["status"] for r in rows} - {"complete"})},
            # Why the games that were not ranked were not, counted by reason
            # rather than folded into one number -- a practice game and a game
            # somebody wrote into are different events.
            "held_out": {why: sum(1 for g in played if why_not_ranked(g) == why)
                         for why in sorted(filter(None, {why_not_ranked(g)
                                                         for g in played}))},
            "levels": len(levels),
            "players": len(players),
            "attendance_unrecorded": sum(1 for r in rows if r["status"] == "complete"
                                         and r.get("attendance") == "unrecorded"),
        },
    }


def table(data: dict) -> str:
    t = data["totals"]
    out = [f"{t['ranked']} ranked of {t['games']} game(s) over {t['rounds']} round(s) · "
           f"{t['levels']} level(s) · {t['players']} player(s)"]
    if t["multi_round_games"]:
        out.append(f"  {t['multi_round_games']} game(s) of more than one round, "
                   f"scored on the median of their rounds")
    if t["unfinished_games"]:
        out.append(f"  {t['unfinished_games']} game(s) short of the rounds they "
                   f"declared, kept and not ranked")
    if t["not_ranked"]:
        out.append("  not ranked: " + ", ".join(f"{k} {v}" for k, v in t["not_ranked"].items()))
    if t.get("held_out"):
        out.append("  held out of the ranking: "
                   + ", ".join(f"{k} {v}" for k, v in t["held_out"].items())
                   + " — kept, counted, and in every denominator above")
    if t["attendance_unrecorded"]:
        out.append(f"  attendance not recorded on {t['attendance_unrecorded']} ranked round(s)")

    top = data.get("best_ever")
    if top:
        out.append(f"\nBEST GAME EVER — {top['capture']:+.3f} captured by "
                   f"{' + '.join(top['by'])} on {top['label']}")
        out.append(f"  the most successful of all {top['of_all']} ranked game(s); "
                   f"a record and not a rank, since it only ever played the "
                   f"{top['first_of']} game(s) on its own format")
    who = data.get("best_player")
    if who:
        out.append(f"\nBEST PLAYER — {who['id']} at {who['best']:.3f}x what they "
                   f"would have had alone")
        out.append(f"  over {who['games']} game(s) on {who['levels']} format(s); "
                   f"their best was on "
                   f"{level_label(tuple(who['level'])) if who['level'] else '?'}")

    out.append("\nLEVELS — best game on each format, as gains captured "
               "(autarky 0.0, frontier 1.0)")
    out.append(f"  {'best':>7}  {'median':>7}  {'>0':>7}  {'played':>6}  level")
    for row in data["islands"]:
        out.append(f"  {row['best']:>7.3f}  {row['median']:>7.3f}  "
                   f"{row['above_autarky']:>3}/{row['ranked']:<3}  "
                   f"{row['ranked']:>3}/{row['attempts']:<3}  {row['label']}")

    out += _ranking("ALL TIME", data)
    week = data.get("week") or {}
    if week.get("since"):
        out += _ranking(f"LAST {week['days']} DAYS "
                        f"(since {week['since'][:10]})", week)
    return "\n".join(out)


def _ranking(title: str, data: dict, top: int = 10) -> list[str]:
    """One window's two rankings: the games, and the players who played them."""
    out = [f"\n{title} — GAMES, as gains captured (place is within the format)"]
    out.append(f"  {'captured':>8}  {'place':>7}  level")
    for row in data["games"][:top]:
        out.append(f"  {row['capture']:>+8.3f}  {row['place']:>3}/{row['of']:<3}  "
                   f"{row['label']}  {' + '.join(row['by'])}")
    if not data["games"]:
        out.append("  (nothing ranked in this window)")

    out.append(f"\n{title} — PLAYERS, best game as a multiple of playing alone")
    out.append(f"  {'best':>7}  {'median':>6}  {'worst':>6}  {'games':>6}  "
               f"{'<1.0x':>6}  {'zeros':>9}  id")
    for row in data["traders"][:top]:
        out.append(f"  {row['best']:>7.3f}  {row['median']:>6.3f}  {row['worst']:>6.3f}  "
                   f"{row['games']:>6}  {row['below_autarky']:>6}  "
                   f"{row['zero_episodes']:>4}/{row['agent_episodes']:<4}  {row['id']}")
    if not data["traders"]:
        out.append("  (nobody ranked in this window)")
    return out


def pack(results: Path | None = None) -> int:
    """Gzip saved boards in place.

    A kept replay is one file per round, and a round's board compresses about
    sevenfold -- it is mostly the manager saying similar things. `serve.py`
    serves a `.json.gz` with `Content-Encoding: gzip`, so the page fetches it
    without knowing anything changed.

    The original is removed only after the compressed copy has been read back
    and compared byte for byte. A replay that cannot be re-read is a replay
    that is gone.
    """
    results = results or HERE.parent / "results"
    before = after = 0
    packed = 0
    for path in sorted(results.rglob("board-*.json")):
        raw = path.read_bytes()
        target = path.with_suffix(".json.gz")
        target.write_bytes(gzip.compress(raw, 6))
        if gzip.decompress(target.read_bytes()) != raw:
            target.unlink(missing_ok=True)
            print(f"{path}: did not read back the same; left alone", file=sys.stderr)
            continue
        before += len(raw)
        after += target.stat().st_size
        path.unlink()
        packed += 1
    if packed:
        print(f"packed {packed} board(s): {before / 1024:.0f} KiB → "
              f"{after / 1024:.0f} KiB ({before / max(after, 1):.1f}x)")
    else:
        print("nothing to pack")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ingest", type=Path, nargs="*", metavar="RESULT",
                    help="run records to add; a round already in the ledger is skipped")
    ap.add_argument("--sweep", action="store_true",
                    help="ingest every run record in the experiments tree, so the "
                         "boards do not depend on who ran the command")
    ap.add_argument("--player", action="append", default=[], metavar="SLOT=ID",
                    help="who played a slot, e.g. --player T1=haiku-scout")
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--upgrade", action="store_true",
                    help="re-derive rows written by an older version of this "
                         "file, so --verify checks every row rather than "
                         "skipping the old ones")
    ap.add_argument("--refresh", action="store_true",
                    help="rebuild the derived boards and index from the record")
    ap.add_argument("--results", type=Path, default=None,
                    help="which results tree to pack (default: this experiment's)")
    ap.add_argument("--pack", action="store_true",
                    help="gzip the saved boards in results/ (about 7x), keeping "
                         "them readable by the viewer; each is read back and "
                         "compared before the original is removed")
    args = ap.parse_args(argv)

    players = dict(p.split("=", 1) for p in args.player)

    if args.sweep:
        found = sweep()
        print(f"sweeping {len(found)} run record(s)")
        args.ingest = list(args.ingest or []) + found

    if args.ingest:
        for result in args.ingest:
            added, skipped = ingest(result, ledger=args.ledger, players=players)
            print(f"{result}: {len(added)} added, {len(skipped)} already there")

    if args.upgrade:
        changed, problems = upgrade(args.ledger)
        for p in problems:
            print(p, file=sys.stderr)
        print(f"{changed} row(s) re-derived to v{SCHEMA}; {len(problems)} could not be")
        if problems:
            return 1

    if args.verify:
        problems = verify(args.ledger)
        for p in problems:
            print(p, file=sys.stderr)
        print(f"{len(load(args.ledger))} row(s) recomputed from their own seeds; "
              f"{len(problems)} disagreed")
        if problems:
            return 1

    if args.pack:
        return pack(args.results)

    if args.refresh:
        held = write_boards(args.ledger)
        print(f"rebuilt from {len(load(args.ledger))} row(s) in "
              f"{len(parts(args.ledger))} ledger part(s)")

    data = read_boards(args.ledger)
    if args.json:
        print(json.dumps(data, default=list, indent=1))
    elif args.table or not (args.ingest or args.verify):
        print(table(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
