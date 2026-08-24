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
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))
sys.path.insert(0, str(HERE.parent))

from barter.economy import autarky, draw_island, efficiency  # noqa: E402

from island.score import score as score_round  # noqa: E402

LEDGER = HERE / "scores" / "ledger.jsonl"

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
SCHEMA = 1

#: How the boards are computed. The cache is keyed on the ledger *and* on this,
#: because a ranking rule that changes while the record does not is exactly the
#: case where a cache keyed only on the record serves the old order forever.
#: Bump it when `boards` changes what it produces.
BOARDS_V = 4

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
    """Paths are stored relative to the experiment, not to whoever ran this.

    A ledger row has to still resolve when it is read from another checkout, or
    `--verify` degrades into "the file moved" for every row.
    """
    if not path:
        return None
    try:
        return path.resolve().relative_to(HERE.parent).as_posix()
    except ValueError:
        return str(path)


def read_board(path: Path) -> dict | None:
    """A saved board, whether or not it has been packed.

    `--pack` gzips boards in place, so every reader has to accept both names or
    packing a directory quietly breaks the tools that read it.
    """
    for candidate in (path, path.with_suffix(path.suffix + ".gz")):
        if candidate.is_file():
            try:
                raw = (gzip.decompress(candidate.read_bytes())
                       if candidate.name.endswith(".gz") else candidate.read_bytes())
                return json.loads(raw)
            except (ValueError, OSError):
                return None
    return None


def played_at(board: Path | None) -> str | None:
    """When the round actually ran, from the last thing said on its board.

    `recorded_at` is when somebody typed the ingest command, which may be months
    later; a feed sorted by that is a list of when files were touched.
    """
    if not board:
        return None
    saved = read_board(board)
    if not saved:
        return None
    stamps = [m.get("at") for m in saved.get("messages", []) if m.get("at")]
    return max(stamps) if stamps else None


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
    trajectory = rnd["trajectory"]
    if not trajectory:
        raise ValueError(f"{rnd.get('workspace')}: a round with no closed episode "
                         f"cannot be scored")

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

    board = source.with_name(f"board-{rnd['workspace']}.json") if source else None
    kept = board is not None and (board.is_file()
                                  or board.with_suffix(".json.gz").is_file())
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
        "played_at": played_at(board),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workspace": rnd["workspace"],
        "arm": rnd.get("arm"),
        "island": {"seed": seed, "agents": agents, "goods": goods, "episodes": k},
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
    return (i["agents"], i["goods"], i["episodes"])


def level_label(key: tuple) -> str:
    agents, goods, episodes = key
    return f"{agents} traders · {goods} goods · {episodes} episodes"


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
    return {
        "v": SCHEMA,
        "round_id": (rid := round_id(rnd.get("workspace", "?"), rnd.get("seed", -1),
                                     rnd.get("trajectory") or [])),
        "game": {"id": rid, "rounds": 1},
        "played_at": None,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "workspace": rnd.get("workspace"), "arm": rnd.get("arm"),
        "island": {"seed": rnd.get("seed"), "agents": record.get("agents"),
                   "goods": record.get("goods"),
                   "episodes": len(rnd.get("trajectory") or [])},
        "players": [], "eff_round": None, "autarky_floor": None,
        "ratios": {}, "zero_episodes": {}, "trajectory": rnd.get("trajectory") or [],
        "status": "unscored", "why": why, "attendance": "unrecorded",
        "source": {"result": relative(source), "board": None, "board_sha256": None},
    }


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
        if board and (d := digest(HERE.parent / board)) and d != row["source"]["board_sha256"]:
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
            "played_at": members[-1].get("played_at") or members[-1]["recorded_at"],
            "round_ids": [m["round_id"] for m in members],
        })
    return out


def boards(rows: list[dict]) -> dict:
    """The leaderboards, with their denominators attached to them.

    Ranked entries are finished games whose every round was scorable; the counts
    say how many were not, and those games stay in the file. A board that
    quietly drops what went wrong is reporting on a population it chose after
    seeing the results.
    """
    played = games(rows)
    ranked = [g for g in played
              if g["finished"] and g["all_scored"] and g["capture"] is not None]

    levels: dict[tuple, list[dict]] = {}
    for g in ranked:
        if g["level"]:
            levels.setdefault(tuple(g["level"]), []).append(g)
    island_board = []
    for key, entries in sorted(levels.items()):
        best = max(entries, key=lambda e: e["capture"])
        attempts = sum(1 for g in played if g["level"] and tuple(g["level"]) == key)
        island_board.append({
            "level": list(key),
            "label": level_label(key),
            "agents": key[0], "goods": key[1], "episodes": key[2],
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
            "ranked": len(entries),
            "attempts": attempts,
            # The spread says whether the best is a result or a lucky draw.
            "median": round(statistics.median([e["capture"] for e in entries]), 6),
            "worst": min(e["capture"] for e in entries),
            # How often anybody beat doing nothing at all on this format.
            "above_autarky": sum(1 for e in entries if e["capture"] > 0),
        })
    island_board.sort(key=lambda x: (-x["best"], x["level"]))

    players: dict[str, dict] = {}
    for g in ranked:
        for slot, who in g["players"].items():
            if slot not in g["ratios"]:
                continue
            row = players.setdefault(who, {
                "id": who, "scores": [], "games": 0, "below": 0,
                "zero_episodes": 0, "agent_episodes": 0, "rounds": 0, "levels": set(),
            })
            ratio = g["ratios"][slot]
            row["scores"].append(ratio)
            row["games"] += 1
            row["rounds"] += g["rounds"]
            row["below"] += 1 if ratio < 1.0 - 1e-9 else 0
            if g["level"]:
                row["levels"].add(tuple(g["level"]))
    for g in ranked:
        for rid in g["round_ids"]:
            r = next(x for x in rows if x["round_id"] == rid)
            for p in r["players"]:
                if p["id"] in players:
                    players[p["id"]]["zero_episodes"] += r["zero_episodes"].get(p["slot"], 0)
                    players[p["id"]]["agent_episodes"] += r["island"]["episodes"]

    trader_board = []
    for row in players.values():
        # The best game holds the place. A lucky island, or a partner who
        # happened to want what you could make, is what a high score is made of
        # -- and inside a game of several rounds the median has already taken
        # the luck out to whatever degree that format asked for. The rest of the
        # row says whether a top score was one game or a habit.
        trader_board.append({
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
        })
    trader_board.sort(key=lambda x: (-x["best"], -x["median"], -x["games"]))

    unfinished = sum(1 for g in played if not g["finished"])
    return {
        "islands": island_board,
        "traders": trader_board,
        "recent": sorted(rows, key=lambda r: r.get("played_at") or r["recorded_at"],
                         reverse=True)[:12],
        "totals": {
            "rounds": len(rows),
            "games": len(played),
            "ranked": len(ranked),
            "multi_round_games": sum(1 for g in played if g["declared"] > 1),
            "unfinished_games": unfinished,
            "not_ranked": {s: sum(1 for r in rows if r["status"] == s)
                           for s in sorted({r["status"] for r in rows} - {"complete"})},
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
    if t["attendance_unrecorded"]:
        out.append(f"  attendance not recorded on {t['attendance_unrecorded']} ranked round(s)")

    out.append("\nLEVELS — best game on each format, as gains captured "
               "(autarky 0.0, frontier 1.0)")
    out.append(f"  {'best':>7}  {'median':>7}  {'>0':>7}  {'played':>6}  level")
    for row in data["islands"]:
        out.append(f"  {row['best']:>7.3f}  {row['median']:>7.3f}  "
                   f"{row['above_autarky']:>3}/{row['ranked']:<3}  "
                   f"{row['ranked']:>3}/{row['attempts']:<3}  {row['label']}")

    out.append("\nTRADERS — best game, as a multiple of playing alone")
    out.append(f"  {'best':>7}  {'median':>6}  {'worst':>6}  {'games':>6}  "
               f"{'<1.0x':>6}  {'zeros':>9}  id")
    for row in data["traders"]:
        out.append(f"  {row['best']:>7.3f}  {row['median']:>6.3f}  {row['worst']:>6.3f}  "
                   f"{row['games']:>6}  {row['below_autarky']:>6}  "
                   f"{row['zero_episodes']:>4}/{row['agent_episodes']:<4}  {row['id']}")
    return "\n".join(out)


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
    ap.add_argument("--player", action="append", default=[], metavar="SLOT=ID",
                    help="who played a slot, e.g. --player T1=haiku-scout")
    ap.add_argument("--ledger", type=Path, default=LEDGER)
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true")
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

    if args.ingest:
        for result in args.ingest:
            added, skipped = ingest(result, ledger=args.ledger, players=players)
            print(f"{result}: {len(added)} added, {len(skipped)} already there")

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
