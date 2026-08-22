"""What the screen found, read off settled state.

The screen ran ten advice blocks against five seeds each. Two things about
that shape decide how it must be read.

The floor moves with the seed -- autarky scores 0.523 on one island and 0.823
on another -- so a raw `eff_round` says more about which island a round drew
than about which block it ran. Every number here is therefore the paired
difference `eff_round - floor`: what the block achieved on an island, against
what its traders would have got by never trading at all on that same island.

And ten arms on five seeds is still a screen. Five paired differences give a
spread, not a result. What earns a re-run is a block whose whole spread sits
somewhere another's does not, and even that is a hypothesis.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(path: Path) -> None:
    data = json.loads(path.read_text())
    rounds = data["rounds"]
    by_arm: dict[str, list[dict]] = {}
    for r in rounds:
        by_arm.setdefault(r["arm"], []).append(r)

    seeds = sorted({r["seed"] for r in rounds})
    print(f"{len(rounds)} rounds, {len(by_arm)} arms, seeds {seeds}, "
          f"{data['episodes_per_round']} episodes of "
          f"{data['schedule']['episode_seconds']}s, model {data['model']}\n")

    floors = {r["seed"]: r["score"]["autarky_floor"] for r in rounds}
    print("floor by seed (autarky, the same for every arm):")
    print("  " + "  ".join(f"s{s}={floors[s]:.3f}" for s in seeds) + "\n")

    head = f"{'arm':5s} " + " ".join(f"{'seed' + str(s):>8s}" for s in seeds)
    print(head + f" {'mean':>8s} {'median':>8s} {'>floor':>7s} {'zeros':>6s}")
    print("-" * len(head + "    mean   median   >floor  zeros"))

    rows = []
    for arm in sorted(by_arm):
        got = {r["seed"]: r for r in by_arm[arm]}
        diffs, cells = [], []
        zeros = 0
        for s in seeds:
            r = got.get(s)
            if r is None:
                cells.append(f"{'--':>8s}")
                continue
            d = r["score"]["eff_round"] - r["score"]["autarky_floor"]
            diffs.append(d)
            zeros += sum(1 for e in r["score"]["eff_episode"] if e == 0.0)
            cells.append(f"{d:+8.3f}")
        if not diffs:
            continue
        mean = statistics.fmean(diffs)
        med = statistics.median(diffs)
        above = sum(1 for d in diffs if d > 0)
        rows.append((mean, arm))
        print(f"{arm:5s} " + " ".join(cells) +
              f" {mean:+8.3f} {med:+8.3f} {above:>4d}/{len(diffs)} {zeros:>6d}")

    print("\nranked by mean paired difference:")
    for mean, arm in sorted(rows, reverse=True):
        print(f"  {arm:5s} {mean:+.3f}")

    print("\nbehaviour, summed over each arm's rounds:")
    print(f"{'arm':5s} {'settled':>8s} {'refused':>8s} {'talk':>6s} "
          f"{'acked':>7s} {'msgs':>6s}")
    for arm in sorted(by_arm):
        rs = by_arm[arm]
        print(f"{arm:5s} {sum(r['settled'] for r in rs):8d} "
              f"{sum(r['refused'] for r in rs):8d} "
              f"{sum(r['talk'] for r in rs):6d} "
              f"{sum(len(r['acknowledged']) for r in rs):4d}/"
              f"{2 * len(rs):<3d}"
              f"{sum(r['channel_messages'] for r in rs):6d}")

    print("\nepisode position, mean eff_episode over all arms and seeds:")
    k = data["episodes_per_round"]
    for i in range(k):
        vals = [r["score"]["eff_episode"][i] for r in rounds
                if len(r["score"]["eff_episode"]) > i]
        z = sum(1 for v in vals if v == 0.0)
        print(f"  episode {i + 1}: {statistics.fmean(vals):.3f} "
              f"over {len(vals)} rounds, {z} of them zero")

    print("\nA zero episode is one trader holding none of some good: the "
          "vector\nsits maximally far from the frontier however well the "
          "other did. It is\ncoverage, not welfare, and it is worth counting "
          "separately from the mean.")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "results/screen/v3.json"
    main(Path(arg) if Path(arg).is_absolute() else HERE.parent / arg)
