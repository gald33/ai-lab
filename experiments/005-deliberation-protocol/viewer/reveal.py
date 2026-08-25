"""Regenerate an island's hidden half, for replay only.

Tastes and capacities are **private to each trader** and never appear on the
board. A live spectator must therefore not see them: a page that draws all four
hut interiors while the round is running knows more than any player does, and
what it shows is no longer the game the traders are playing.

They are recoverable after the fact because the island is a deterministic draw
from the round's seed -- so this writes them to a sidecar the replay reads, and
the run itself is not touched. Nothing here talks to a hub, and nothing here is
importable by the live page.

    python viewer/reveal.py --seed 1 --agents 2 --goods 4 \
        --result results/v3/v3.json --workspace island6-bare-1 \
        -o results/v3/reveal-island6-bare-1.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "002-barter-conventions" / "experiment"))

from barter.economy import autarky, draw_island, efficiency, utility  # noqa: E402

sys.path.insert(0, str(HERE.parent))

from island import dealer  # noqa: E402

#: The island's vocabulary, and the only mapping from a board word to an island
#: index. `barter.economy.GOOD_NAMES` is a different vocabulary for the same
#: positions and would silently mislabel every holding.
#:
#: Read from the dealer rather than from `Manager.goods`, which is only that
#: class's *default* -- a five-good round revealed against a four-word default
#: would quietly drop its fifth good and mislabel nothing, which is worse.
GOODS = dealer.GOODS


def reveal(seed: int, agents: int, goods: int, names: list[str] | None = None) -> dict:
    island = draw_island(agents, goods, seed=seed)
    names = names or [f"T{i + 1}" for i in range(agents)]
    words = GOODS[:goods]
    _, auto = autarky(island)
    return {
        "seed": seed,
        "agents": agents,
        "goods": list(words),
        "traders": {
            name: {
                "taste": {g: island.alpha[i][j] for j, g in enumerate(words)},
                "capacity": {g: island.capacity[i][j] for j, g in enumerate(words)},
            }
            for i, name in enumerate(names)
        },
        "autarky_utility": {n: auto[i] for i, n in enumerate(names)},
        "autarky_floor": efficiency(island, list(auto)).lower,
    }


def attach_round(payload: dict, result: Path, workspace: str) -> dict:
    """Add the recorded round to the sidecar, so the replay can show a score.

    The trajectory is the manager's, read from settled state at each bell. The
    replay recomputes nothing: a page that derives its own utilities is a
    second implementation of the metric, and the two would drift.
    """
    record = json.loads(result.read_text())
    rounds = [r for r in record.get("rounds", []) if r.get("workspace") == workspace]
    if not rounds:
        raise SystemExit(f"no round with workspace {workspace!r} in {result}")
    if len(rounds) > 1:
        raise SystemExit(f"{len(rounds)} rounds claim workspace {workspace!r}")
    r = rounds[0]
    payload["round"] = {
        "workspace": workspace, "arm": r.get("arm"), "episodes": r.get("episodes"),
        "trajectory": r.get("trajectory"), "score": r.get("score"),
    }
    return payload


#: A spectator cannot beat the board's own precision. `Manager._produce` writes
#: `round(qty, 4)` into its receipt while keeping full precision internally, so
#: a page that rebuilds stocks from receipts is accurate to ~1e-4 in quantity
#: and ~2e-5 in utility and no better. That is a property of the record, not a
#: fault in the reader -- which is why the replay shows the *recorded* score and
#: never its own recomputation of it.
TOLERANCE = 1e-3


def check(payload: dict, board: Path, tolerance: float = TOLERANCE) -> int:
    """Utilities rebuilt from the board's receipts against the manager's own.

    This is the honest test of the whole wrapper: if replaying what the manager
    *said* does not reproduce what the manager *scored*, the page is drawing a
    different economy from the one that ran. It will not reproduce it exactly --
    see `TOLERANCE` -- and a run that agrees only to 1e-4 is agreement.
    """
    from subprocess import run  # noqa: PLC0415

    out = run([  # noqa: S603, S607
        "node", str(HERE / "tests" / "holdings.mjs"), str(board),
    ], capture_output=True, text=True, check=False)
    if out.returncode:
        print(out.stderr.strip() or "the reducer would not run", file=sys.stderr)
        return 1
    episodes = json.loads(out.stdout)["episodes"]
    trajectory = payload.get("round", {}).get("trajectory")
    if not trajectory:
        print("no recorded trajectory to check against", file=sys.stderr)
        return 1
    names = list(payload["traders"])
    words = payload["goods"]
    worst = 0.0
    for i, (rebuilt, recorded) in enumerate(zip(episodes, trajectory)):
        for j, name in enumerate(names):
            held = [rebuilt["holdings"].get(name, {}).get(g, 0.0) for g in words]
            alpha = tuple(payload["traders"][name]["taste"][g] for g in words)
            gap = abs(utility(alpha, held) - recorded[j])
            worst = max(worst, gap)
            if gap > tolerance:
                print(f"episode {i + 1} {name}: board says {utility(alpha, held):.6f}, "
                      f"the manager scored {recorded[j]:.6f}", file=sys.stderr)
    print(f"{len(episodes)} episodes x {len(names)} traders rebuilt from the board; "
          f"worst gap {worst:.2e} against a tolerance of {tolerance:.0e} "
          f"(receipts carry four decimals)")
    return 0 if worst <= tolerance else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--agents", type=int, default=2)
    ap.add_argument("--goods", type=int, default=4)
    ap.add_argument("--result", type=Path, help="a v3.json to take the round from")
    ap.add_argument("--workspace", help="which round in that file")
    ap.add_argument("--check", type=Path, metavar="BOARD",
                    help="rebuild utilities from this board and compare")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args(argv)

    payload = reveal(args.seed, args.agents, args.goods)
    if args.result:
        if not args.workspace:
            raise SystemExit("--result needs --workspace")
        attach_round(payload, args.result, args.workspace)
    if args.out:
        args.out.write_text(json.dumps(payload, indent=1) + "\n")
        print(f"wrote {args.out}")
    else:
        print(json.dumps(payload, indent=1))
    return check(payload, args.check) if args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
