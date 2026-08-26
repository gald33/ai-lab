"""Publish this experiment's rounds as replays the island viewer can play.

The viewer already knows how to play a board back -- 005 built it, and
`viewer/serve.py` finds a replay by walking any directory named in its `ROOTS`
for `board-*.json` with an optional `reveal-*.json` beside it. So 007 does not
need a player of its own; it needs its boards in that shape and its directory
in that list.

Two conversions, and nothing else:

* **the board.** 007 preserved raw hub rows -- `from`, `created_at`, `seq`.
  The viewer reads `{workspace, channel, messages: [{seq, at, author, body}]}`,
  which is what 005's runner wrote. Same messages, same order, renamed keys.
* **the sidecar.** Tastes and capacities are private while a round is live and
  recoverable afterwards from the seed, which is exactly what `viewer/reveal.py`
  exists for. It is imported rather than reimplemented: a second copy of the
  reveal would be a second island, and the two would drift.

Nothing is recomputed. The score and trajectory in the sidecar are the
manager's own, copied from the run record.

    python tools/export_replays.py            # every run that kept boards
    python tools/export_replays.py 001-ceiling
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
VIEWER = EXP.parent / "005-deliberation-protocol" / "viewer"
sys.path.insert(0, str(VIEWER))

import reveal as reveal_mod  # noqa: E402

OUT = EXP / "replays"


def as_viewer_board(rows: list[dict], workspace: str, channel: str) -> dict:
    """The hub's rows in the shape 005's runner saved, oldest first."""
    return {
        "workspace": workspace,
        "channel": channel,
        "messages": [{"seq": m.get("seq"), "at": m.get("created_at"),
                      "author": m.get("from"), "body": m.get("body")}
                     for m in sorted(rows, key=lambda m: m.get("seq", 0))],
    }


def export_run(run: Path, out: Path) -> int:
    """Every board this run kept, as a board/reveal pair under `out`."""
    doc = json.loads((run / "v3.json").read_text())
    agents, goods = doc.get("agents", 4), doc.get("goods", 4)
    by_key = {(r["arm"], r["seed"]): r for r in doc["rounds"]}
    boards = run / "boards"
    if not boards.is_dir():
        return 0

    out.mkdir(parents=True, exist_ok=True)
    written = 0
    for path in sorted(boards.glob("*.json")):
        arm, seed = re.match(r"(.+)-seed(\d+)$", path.stem).groups()
        rnd = by_key.get((arm, int(seed)))
        if rnd is None:
            # A board with no round in the record is a round that died before
            # it was scored. It is not published: a replay whose score cannot
            # be read from settled state would invite the page to derive one.
            print(f"  skipped {path.stem}: no round in the record")
            continue
        # The label a viewer sees. Prefixed with the run so two runs that share
        # an arm and a seed -- which the replicates do -- stay distinguishable.
        label = f"{run.name}-{arm}-seed{seed}"
        rows = json.loads(path.read_text())
        workspace = rnd.get("workspace") or label
        (out / f"board-{label}.json").write_text(json.dumps(
            as_viewer_board(rows, workspace, rnd.get("channel", "island"))))

        side = reveal_mod.reveal(int(seed), agents, goods)
        side = reveal_mod.attach_round(side, run / "v3.json", workspace)
        (out / f"reveal-{label}.json").write_text(json.dumps(side))
        written += 1
    return written


def main(argv: list[str]) -> int:
    runs = [EXP / "results" / a for a in argv] if argv else sorted(
        (EXP / "results").iterdir())
    total = 0
    for run in runs:
        if not (run / "v3.json").exists():
            continue
        n = export_run(run, OUT / run.name)
        if n:
            print(f"{run.name}: {n} replay(s)")
        total += n
    print(f"{total} replay(s) under {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
