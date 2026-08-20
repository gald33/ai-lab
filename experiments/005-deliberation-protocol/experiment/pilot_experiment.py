"""The 005 pilot: unguided worlds only, swept over a grid fixed before the run.

Nothing here applies a manipulation. The pilot's only job is to find out whether
any market configuration gives unguided agents headroom — agreement that is
neither immediate nor unreachable — because a configuration without headroom
makes all four cells of 005 read the same and the money is wasted.

**Every configuration on the grid is reported**, accepted or not, in sweep
order. Searching for a workable task is legitimate; searching until an effect
appears is not, and publishing the whole search is the only defence against the
second reading of the first.

The grid is a full factorial spanning both extremes of each knob rather than a
neighbourhood around a guess: `anchor` runs from near-pure averaging (which must
converge) to stubborn (which must not), `width` from one neighbour to half the
population, `sigma` from a tight prior to a loose one. If the band is reachable
at all it is inside this box; if the whole box misses, that is the finding.
"""

from __future__ import annotations

import argparse
import json
import sys

from pilot.gate import BAND, MAX_INSTANT, MAX_LATE, MIN_COORDINATED, MIN_IQR, evaluate
from pilot.run import TAU, TAU_CURVE, run_world
from pilot.world import Config

N_AGENTS = 8
N_GOODS = 4
ROUNDS = 20

SIGMAS = (0.15, 0.30, 0.60)
WIDTHS = (1, 2, 4)
ANCHORS = (0.05, 0.15, 0.30)


def grid() -> list[Config]:
    return [Config(N_AGENTS, N_GOODS, s, w, a, ROUNDS)
            for s in SIGMAS for w in WIDTHS for a in ANCHORS]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worlds", type=int, default=40,
                    help="seeded worlds per configuration")
    ap.add_argument("--json", type=str, default=None)
    args = ap.parse_args()

    configs = grid()
    print(f"005 pilot — unguided worlds only, no manipulation applied")
    print(f"{len(configs)} configurations x {args.worlds} worlds, "
          f"tau={TAU}, band={BAND}, rounds={ROUNDS}\n")

    verdicts = []
    for cfg in configs:
        worlds = [run_world(cfg, seed) for seed in range(1, args.worlds + 1)]
        v = evaluate(worlds, ROUNDS)
        verdicts.append((v, worlds))

    head = (f"{'configuration':<28} {'rate':>6} {'n':>4} {'inst':>6} {'late':>6} "
            f"{'IQR':>5} {'med':>4} {'err':>6}  P1 P2 P3 P4  verdict")
    print(head)
    print("-" * len(head))
    for v, _ in verdicts:
        mark = lambda b: " Y" if b else " ."
        med = f"{v.median_rounds:.0f}" if v.median_rounds is not None else "  -"
        err = f"{v.median_error:.3f}" if v.median_error is not None else "     -"
        print(f"{v.key:<28} {v.rate:>6.3f} {v.coordinated:>4} "
              f"{v.instant_share:>6.2f} {v.late_share:>6.2f} {v.iqr:>5.1f} "
              f"{med:>4} {err:>6} "
              f"{mark(v.p1)}{mark(v.p2)}{mark(v.p3)}{mark(v.p4)}  "
              f"{'ACCEPTED' if v.accepted else ''}")

    accepted = [v for v, _ in verdicts if v.accepted]
    broken = sum(v.harness_failures for v, _ in verdicts)
    print(f"\n{len(configs)} configurations evaluated, {len(accepted)} accepted.")
    print(f"harness failures across the whole sweep: {broken}")
    if not accepted:
        print("\nNo configuration met the band. Under the pre-registration, 005"
              "\nstops at the pilot and reports this.")
    else:
        best = min(accepted, key=lambda v: abs(v.rate - sum(BAND) / 2))
        print(f"\nClosest to band centre: {best.key} (rate {best.rate:.3f})")
        print("sensitivity curve for that configuration:")
        for t in TAU_CURVE:
            k = f"{t:g}"
            star = "  <- pre-registered" if t == TAU else ""
            print(f"  tau={k:<5} rate {best.curve[k]:.3f}{star}")

    if args.json:
        payload = {
            "experiment": "005-pilot",
            "manipulation": None,
            "tau": TAU,
            "tau_curve": list(TAU_CURVE),
            "band": list(BAND),
            "criteria": {"max_instant": MAX_INSTANT, "max_late": MAX_LATE,
                         "min_iqr": MIN_IQR, "min_coordinated": MIN_COORDINATED},
            "worlds_per_config": args.worlds,
            "rounds": ROUNDS, "n_agents": N_AGENTS, "n_goods": N_GOODS,
            "configurations_evaluated": len(configs),
            "accepted": [v.key for v in accepted],
            "verdicts": [v.to_json() for v, _ in verdicts],
            "worlds": {v.key: [w.to_json() for w in ws] for v, ws in verdicts},
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=1)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
