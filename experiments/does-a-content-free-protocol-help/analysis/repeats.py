"""Repeat exchanges, read from the board a run left behind.

The behavioural endpoint of run 006: of the exchanges a round settled, what
share re-used a (pair, goods) combination the same round had already settled,
and in which episode did the first such repeat appear?

It is read from the manager's own settlement notes, which are settled state
written to the board -- never from what a trader said it did. A refusal reads
`@T2 not settled: ...` and is excluded by requiring the exchange body; a
production settlement is not an exchange and does not count here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

#: `p12 settled: T4 and T3 exchanged {...} for {...}`. The leading `p\d+ ` is
#: what separates a settlement from the `@T2 not settled:` refusal that would
#: otherwise match the verb.
SETTLED = re.compile(
    r"\bp\d+ settled: (T\d+) and (T\d+) exchanged (\{[^}]*\}) for (\{[^}]*\})")
EPISODE = re.compile(r"episode (\d+) of")
GOODS = re.compile(r"'(\w+)'")


def repeats(board: list[dict]) -> dict:
    """(settled exchanges, repeats, share, episode of the first repeat)."""
    episode, seen, first, total, repeated = 0, set(), None, 0, 0
    for msg in board:
        if msg.get("from") != "manager":
            continue
        body = str(msg.get("body"))
        if bell := EPISODE.search(body):
            episode = int(bell.group(1))
        if not (hit := SETTLED.search(body)):
            continue
        maker, taker, give, want = hit.groups()
        # Unordered in both dimensions: who proposed and which side of the
        # exchange a good sat on are not what "the same trade again" means.
        key = (frozenset((maker, taker)),
               frozenset((tuple(sorted(GOODS.findall(give))),
                          tuple(sorted(GOODS.findall(want))))))
        total += 1
        if key in seen:
            repeated += 1
            if first is None:
                first = episode
        seen.add(key)
    return {"exchanges": total, "repeats": repeated,
            "share": repeated / total if total else 0.0,
            "first_repeat_episode": first}


def main(boards: Path) -> None:
    rows = {}
    for path in sorted(boards.glob("*.json")):
        rows[path.stem] = repeats(json.load(path.open()))
        r = rows[path.stem]
        print(f"{path.stem:24} exchanges {r['exchanges']:3}  "
              f"repeats {r['repeats']:3}  share {r['share']:.2f}  "
              f"first repeat ep {r['first_repeat_episode']}")
    print()
    for seed in sorted({k[-1] for k in rows}):
        bare = rows.get(f"probe-bare-seed{seed}")
        treat = rows.get(f"probe-constant-seed{seed}")
        if bare and treat:
            print(f"seed {seed}: share bare {bare['share']:.2f} vs constant "
                  f"{treat['share']:.2f}  diff {treat['share']-bare['share']:+.2f}")


if __name__ == "__main__":
    import sys
    main(Path(sys.argv[1] if len(sys.argv) > 1
              else "results/006-probe/boards"))
