"""Turn a run's preserved boards into compact recordings a player can replay.

The board is the whole surface, so the board *is* the recording: every message
in time order, with its offset from the first message. Nothing is reordered and
nothing is summarised away -- a replay that paraphrased the board would be
showing something the traders never saw.

Alongside it goes what the manager settled -- per-episode holdings and utility
per trader -- and the island's own constants, so a viewer can see the state the
words were moving. Those come from the run record, never from message text.

Usage: python tools/make_recording.py results/001-ceiling [out.json]
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island, utility, walras  # noqa: E402

GOODS = ("bread", "cloth", "iron", "salt")


def stamp(text: str) -> float:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def compact(board: list[dict]) -> list[dict]:
    """Board messages as (offset seconds, sender, body), oldest first."""
    msgs = sorted((m for m in board if m.get("body")), key=lambda m: m["seq"])
    if not msgs:
        return []
    base = stamp(msgs[0]["created_at"])
    return [{"t": round(stamp(m["created_at"]) - base, 1),
             "who": m.get("from", "?"),
             "body": str(m["body"])} for m in msgs]


def island_facts(seed: int, agents: int, goods: int) -> dict:
    isl = draw_island(agents, goods, seed=seed)
    _, opt = autarky(isl)
    plan = walras(isl)
    return {
        "alpha": [list(map(float, a)) for a in isl.alpha],
        "capacity": [list(map(float, c)) for c in isl.capacity],
        "autarky": [float(v) for v in opt],
        "plan": [utility(a, x) for a, x in zip(isl.alpha, plan.allocation)],
    }


def build(run: Path) -> dict:
    doc = json.load(open(run / "v3.json"))
    agents, goods = doc.get("agents", 4), doc.get("goods", 4)
    by_key = {(r["arm"], r["seed"]): r for r in doc["rounds"]}
    takes = []
    for path in sorted((run / "boards").glob("*.json")):
        arm, seed = re.match(r"(.+)-seed(\d+)$", path.stem).groups()
        rnd = by_key.get((arm, int(seed)))
        if rnd is None:
            continue
        takes.append({
            "arm": arm,
            "seed": int(seed),
            "messages": compact(json.load(open(path))),
            "episodes": rnd.get("episode_log", []),
            "island": island_facts(int(seed), agents, goods),
        })
    return {"run": run.name, "goods": list(GOODS), "agents": agents,
            "episodes_per_round": doc.get("episodes_per_round"),
            "schedule": doc.get("schedule"), "takes": takes}


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("recordings") / f"{src.name}.json"
    out.parent.mkdir(exist_ok=True)
    doc = build(src)
    out.write_text(json.dumps(doc, separators=(",", ":")))
    msgs = sum(len(t["messages"]) for t in doc["takes"])
    print(f"{out}  takes {len(doc['takes'])}  messages {msgs}  {out.stat().st_size/1e6:.2f} MB")
