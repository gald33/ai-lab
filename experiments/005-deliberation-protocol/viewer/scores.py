"""The ledger: what every finished round scored, kept across rounds.

A game needs a number that survives the round it was won in. This is that
number, and the whole file is about being able to defend it later.

**Two scores, because there are two things being played.**

*The island scored.* `eff_round` -- accumulated utility against the frontier of
the total. It belongs to the table, not to any trader in it: it says how much of
what this island could have produced actually got produced. That is the
cooperative high score, and what makes two of them comparable is playing the
**same level**: the same seed, the same number of traders, the same goods and
the same number of episodes. The seed alone is not enough -- four traders on
seed 1 face a different frontier from two, and thirty episodes is more room to
learn than three. **The configuration is the level.**

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


def played_at(board: Path | None) -> str | None:
    """When the round actually ran, from the last thing said on its board.

    `recorded_at` is when somebody typed the ingest command, which may be months
    later; a feed sorted by that is a list of when files were touched.
    """
    if not board or not board.is_file():
        return None
    try:
        stamps = [m.get("at") for m in json.loads(board.read_text()).get("messages", [])]
    except (ValueError, OSError):
        return None
    stamps = [s for s in stamps if s]
    return max(stamps) if stamps else None


def digest(path: Path | None) -> str | None:
    if not path or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


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
    who = players or {}
    return {
        "round_id": round_id(rnd["workspace"], seed, trajectory),
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
                   "board": relative(board) if board and board.is_file() else None,
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
    """What has to match for two rounds to be the same challenge."""
    i = row["island"]
    return (i["seed"], i["agents"], i["goods"], i["episodes"])


def level_label(key: tuple) -> str:
    seed, agents, _goods, episodes = key
    return f"island {seed} · {agents} traders · {episodes} episodes"


def load(path: Path = LEDGER) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def ingest(result: Path, *, ledger: Path = LEDGER,
           players: dict[str, str] | None = None) -> tuple[list[dict], list[dict]]:
    """Add every round in a run record that is not in the ledger already."""
    record = json.loads(result.read_text())
    have = {e["round_id"] for e in load(ledger)}
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
    return added, skipped


def unscored(record: dict, rnd: dict, source: Path, why: str) -> dict:
    return {
        "round_id": round_id(rnd.get("workspace", "?"), rnd.get("seed", -1),
                             rnd.get("trajectory") or []),
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
    for row in load(ledger):
        if row["status"] == "unscored":
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
    return problems


def boards(rows: list[dict]) -> dict:
    """The leaderboards, with their denominators attached to them.

    Ranked rows are complete rounds only; the counts say how many were not, and
    those rounds stay in the file. A board that quietly drops what went wrong is
    reporting on a population it chose after seeing the results.
    """
    ranked = [r for r in rows if r["status"] == "complete"]

    islands: dict[tuple, list[dict]] = {}
    for r in ranked:
        islands.setdefault(level(r), []).append(r)
    island_board = []
    for key, entries in sorted(islands.items()):
        best = max(entries, key=lambda e: e["eff_round"])
        attempts = sum(1 for r in rows if level(r) == key)
        island_board.append({
            "level": list(key),
            "label": level_label(key),
            "seed": key[0], "agents": key[1], "goods": key[2], "episodes": key[3],
            "best": best["eff_round"],
            "floor": best["autarky_floor"],
            "by": [p["id"] for p in best["players"]],
            "workspace": best["workspace"],
            "arm": best["arm"],
            "round_id": best["round_id"],
            "ranked": len(entries),
            "attempts": attempts,
            # The spread says whether the best is a result or a lucky draw.
            "median": round(statistics.median([e["eff_round"] for e in entries]), 6),
            "worst": min(e["eff_round"] for e in entries),
        })
    island_board.sort(key=lambda x: (-x["best"], x["level"]))

    players: dict[str, dict] = {}
    for r in ranked:
        for p in r["players"]:
            slot = p["slot"]
            row = players.setdefault(p["id"], {
                "id": p["id"], "ratios": [], "rounds": 0, "below": 0,
                "zero_episodes": 0, "agent_episodes": 0, "best": None, "seeds": set(),
            })
            ratio = r["ratios"][slot]
            row["ratios"].append(ratio)
            row["rounds"] += 1
            row["below"] += 1 if ratio < 1.0 - 1e-9 else 0
            row["zero_episodes"] += r["zero_episodes"][slot]
            row["agent_episodes"] += r["island"]["episodes"]
            row["seeds"].add(level(r))
            if row["best"] is None or ratio > row["best"]:
                row["best"] = ratio

    trader_board = []
    for row in players.values():
        # The median, not the best: one lucky round is not a player, and a board
        # topped by a single outlier is a board that rewards playing often.
        trader_board.append({
            "id": row["id"],
            "median": round(statistics.median(row["ratios"]), 4),
            "best": round(row["best"], 4),
            "worst": round(min(row["ratios"]), 4),
            "rounds": row["rounds"],
            "below_autarky": row["below"],
            "zero_episodes": row["zero_episodes"],
            "agent_episodes": row["agent_episodes"],
            "levels": len(row["seeds"]),
        })
    trader_board.sort(key=lambda x: (-x["median"], -x["rounds"]))

    return {
        "islands": island_board,
        "traders": trader_board,
        # When it was played, falling back to when it was written down.
        "recent": sorted(rows, key=lambda r: r.get("played_at") or r["recorded_at"],
                         reverse=True)[:12],
        "totals": {
            "rounds": len(rows),
            "ranked": len(ranked),
            "not_ranked": {s: sum(1 for r in rows if r["status"] == s)
                           for s in sorted({r["status"] for r in rows} - {"complete"})},
            "levels": len(islands),
            "players": len(players),
            "attendance_unrecorded": sum(1 for r in ranked
                                         if r.get("attendance") == "unrecorded"),
        },
    }


def table(data: dict) -> str:
    t = data["totals"]
    out = [f"{t['ranked']} ranked of {t['rounds']} round(s) recorded · "
           f"{t['levels']} level(s) · {t['players']} player(s)"]
    if t["not_ranked"]:
        out.append("  not ranked: " + ", ".join(f"{k} {v}" for k, v in t["not_ranked"].items()))
    if t["attendance_unrecorded"]:
        out.append(f"  attendance not recorded on {t['attendance_unrecorded']} ranked round(s)")

    out.append("\nLEVELS — best eff_round on each configuration")
    out.append(f"  {'best':>6}  {'median':>6}  {'floor':>6}  {'played':>6}  level")
    for row in data["islands"]:
        out.append(f"  {row['best']:>6.3f}  {row['median']:>6.3f}  {row['floor']:>6.3f}  "
                   f"{row['ranked']:>3}/{row['attempts']:<3}  {row['label']}")

    out.append("\nTRADERS — utility as a multiple of playing alone (median across rounds)")
    out.append(f"  {'median':>7}  {'best':>6}  {'worst':>6}  {'rounds':>6}  "
               f"{'<1.0x':>6}  {'zeros':>9}  id")
    for row in data["traders"]:
        out.append(f"  {row['median']:>7.3f}  {row['best']:>6.3f}  {row['worst']:>6.3f}  "
                   f"{row['rounds']:>6}  {row['below_autarky']:>6}  "
                   f"{row['zero_episodes']:>4}/{row['agent_episodes']:<4}  {row['id']}")
    return "\n".join(out)


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

    data = boards(load(args.ledger))
    if args.json:
        print(json.dumps(data, default=list, indent=1))
    elif args.table or not (args.ingest or args.verify):
        print(table(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
