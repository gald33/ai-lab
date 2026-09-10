#!/usr/bin/env python3
"""Rung 0b — does content error move the primary endpoint *on this island*?

    python calibrate.py --islands 48 --json ../results/rung0b-curve.json

`PREREGISTRATION.md`'s H0c, and `PREFLIGHT.md` gate 3. Scripted traders, no
models, nothing spent. **Refused if the zero-period share is flat in δ across
both directions**, because then there is no content axis for the distribution
axis to hold constant and rungs 1-3 are unrunnable whatever the distribution
does.

## Why this is not `which-part-of-a-convention-works/experiment/calibrate_experiment.py`

`PREFLIGHT.md` gate 3 used to name that runner with `--traders`, `--goods` and
`--flow`. Two of those flags do not exist: it takes `--agents`, it defaults to
12 of them, and it runs **stock** islands only. It also reports **efficiency
medians**, which is the endpoint correction C1 in `README.md` retired — Tier 3's
own calibration found survivor efficiency flat across the entire δ sweep, which
is the whole reason the primary here is a count.

So this is a separate runner, and that runner is left alone. It is the
published Tier 3 curve's reproduction; changing what it computes would make a
published number unreproducible, which the root `CLAUDE.md` forbids in the same
breath as it forbids rewriting the record.

**Everything measured here is imported, not reimplemented**: the same
`draw_island`, the same `perturb` on the same `walras` prices, and
`barter.run.run_island_flow`, which is 004's flow mode living in 002's tree
beside the stock one. Only the shape of the sweep and the endpoint are this
experiment's.

## What it sweeps, and the one thing that has to be swept

The **table shape**, alongside δ. The game island seats 2-4 traders and offers
2-5 goods (`games/island/protocol.py`), and the published curve was drawn at 12
agents and 5 goods. Whether the primary can read at all turns out to depend on
which of those cells you are in, and it is not a small dependence: see
`shape_note()`.

## What is *not* claimed

A scripted trader has no beliefs about other agents, so an announced vector and
a privately handed one produce byte-identical play. CS − CP — the claim this
experiment exists for — is **not measurable here at any δ**, and this rung is
silent on it. It measures the content axis, and it establishes whether the
content axis exists.

Nor is a scripted period an episode. `--rounds` per period matches 004's flow
runs so that trading intensity is comparable to the published flow numbers; it
is **not** a claim that 60 scripted rounds are 60 seconds of a real island.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "experiments" / "which-part-of-a-convention-works"
                       / "experiment"))

from barter.calibrate import (ADHERENCES, DELTAS, Announcement,  # noqa: E402
                              distance, implied_plan, normalise, perturb)
from barter.economy import (autarky, draw_island, efficiency,    # noqa: E402
                            exchange_ceiling, walras)
from barter.run import run_island_flow                           # noqa: E402


def announcements(island, deltas, directions, *, rounds: int = 400):
    """Every manufactured convention for one island, off **one** `walras()`.

    `barter.calibrate.announce()` solves the equilibrium per call, which is
    0.4s and the whole cost of this sweep once the shape axis multiplies the
    cells by twelve. The equilibrium does not depend on δ, so it is solved once
    and perturbed many times. Same functions, same numbers -- asserted in
    `tests/test_calibrate_flow.py` against `announce()` itself rather than
    argued for here.
    """
    truth = tuple(normalise(walras(island, rounds=rounds).prices))
    out = {}
    for direction in directions:
        for delta in deltas:
            price = tuple(perturb(truth, delta, direction))
            out[(direction, delta)] = Announcement(
                delta=delta, direction=direction, price=price, truth=truth,
                error=distance(price, truth),
                implied=implied_plan(island, list(price)))
    return out


def zero_period_share(outcome, agents: int, periods: int) -> float:
    """The primary, as this island can express it.

    `zero_periods` counts (agent, period) pairs scoring exactly zero, so the
    share is over agent-periods -- the same denominator `zero_episode_share`
    uses on the game island, which is what makes the two comparable at all.
    """
    return outcome.zero_periods / (agents * periods)


def shape_note(traders: int, goods: int) -> str | None:
    """Why a cell with more goods than traders cannot answer anything.

    Arm C's rule is full specialisation: a price-taker with linear technology
    and one unit of labour puts all of it into the good with the highest
    `price × capacity`. So at most `traders` distinct goods are ever produced,
    and Cobb-Douglas with a positive exponent on a good nobody made is zero for
    **every** agent in **every** period, whatever the price vector said.

    That is a property of the scripted stand-in, not of the island: the NPC
    seats on the real game island do not fully specialise, and at 4 traders and
    5 goods they return a zero-episode share of 0.5, not 1.0 (run 002). It is
    still the reason this rung cannot be run at the game's default of 5 goods,
    and the reason the published curve at 12 agents and 5 goods reads: 12 > 5.
    """
    if goods > traders:
        return (f"{goods} goods and only {traders} traders: full "
                f"specialisation cannot cover the goods, so every agent is "
                f"zero in every period by construction")
    return None


def sweep(args) -> tuple[list[dict], list[dict]]:
    """One row per (shape, direction, δ, adherence), plus a silent anchor row."""
    rows, records = [], []
    seeds = [args.seed0 + i for i in range(args.islands)]

    for traders in args.traders:
        for goods in args.goods:
            islands = [draw_island(traders, goods, seed=s) for s in seeds]
            brackets = [{"autarky": efficiency(i, autarky(i)[1]).lower,
                         "ceiling": exchange_ceiling(i).lower} for i in islands]
            notes = [announcements(i, args.deltas, args.directions)
                     for i in islands]

            # The anchor: no convention at all. Not a δ, so it is a row of its
            # own rather than a point on the curve, and it is what "worth
            # holding" is worth holding *against*.
            silent = [run_island_flow(island, "A", seed=seeds[i],
                                      periods=args.periods,
                                      rounds_per_period=args.rounds)
                      for i, island in enumerate(islands)]
            rows.append(summarise(
                silent, traders, goods, "silent", None, None, brackets,
                args.periods, [None] * len(islands)))

            for direction in args.directions:
                for delta in args.deltas:
                    for adherence in args.adherences:
                        outs, errors = [], []
                        for i, island in enumerate(islands):
                            note = notes[i][(direction, delta)]
                            errors.append(note.error)
                            outs.append(run_island_flow(
                                island, "C", seed=seeds[i],
                                periods=args.periods,
                                rounds_per_period=args.rounds,
                                announced=list(note.price),
                                adherence=adherence))
                        rows.append(summarise(
                            outs, traders, goods, direction, delta, adherence,
                            brackets, args.periods, errors))
                        for i, out in enumerate(outs):
                            records.append({
                                "island": seeds[i], "traders": traders,
                                "goods": goods, "direction": direction,
                                "delta": delta, "adherence": adherence,
                                "error": errors[i],
                                "zero_period_share": zero_period_share(
                                    out, traders, args.periods),
                                "always_zero": out.always_zero,
                                "recoveries": out.recoveries,
                                "efficiency": (None if out.efficiency.ruined
                                               else out.efficiency.lower),
                            })
    return rows, records


def summarise(outs, traders, goods, direction, delta, adherence, brackets,
              periods, errors) -> dict:
    shares = [zero_period_share(o, traders, periods) for o in outs]
    effs = [o.efficiency.lower for o in outs if not o.efficiency.ruined]
    real = [e for e in errors if e is not None]
    return {
        "traders": traders, "goods": goods, "direction": direction,
        "delta": delta, "adherence": adherence, "islands": len(outs),
        "error_median": round(statistics.median(real), 4) if real else None,
        # The primary. A mean over islands, because it is a share of a fixed
        # number of agent-periods on every island and the denominator is the
        # same everywhere.
        "zero_period_share": round(statistics.fmean(shares), 4),
        "always_zero": sum(o.always_zero for o in outs),
        "agents_total": traders * len(outs),
        "recoveries": sum(o.recoveries for o in outs),
        # Reported beside the primary and never summed with it, and never
        # substituted for it: correction C1.
        "efficiency_median": round(statistics.median(effs), 4) if effs else None,
        "scored": len(effs),
        "autarky": round(statistics.median(b["autarky"] for b in brackets), 4),
        "ceiling": round(statistics.median(b["ceiling"] for b in brackets), 4),
    }


PINNED = 1e-9


def curve(rows, traders, goods, direction, adherence) -> list[dict]:
    return sorted((r for r in rows
                   if r["traders"] == traders and r["goods"] == goods
                   and r["direction"] == direction
                   and r["adherence"] == adherence),
                  key=lambda r: r["delta"])


def span(points: list[dict]) -> float:
    """How far the primary moved across δ. Zero is the refusal in H0c."""
    values = [p["zero_period_share"] for p in points]
    return max(values) - min(values) if values else 0.0


def pinned_at_a_bound(points: list[dict]) -> bool:
    """Every δ on a bound. The `noise.py` refusal, on the other free rung."""
    values = [p["zero_period_share"] for p in points]
    return bool(values) and all(v <= PINNED or v >= 1.0 - PINNED
                                for v in values)


def verdict(rows, args) -> dict:
    """Which shapes the primary can read in, and what it did there."""
    shapes = []
    for traders in args.traders:
        for goods in args.goods:
            spans = {}
            pinned = True
            for direction in args.directions:
                points = curve(rows, traders, goods, direction,
                               args.adherences[0])
                spans[direction] = round(span(points), 4)
                pinned = pinned and pinned_at_a_bound(points)
            anchor = next((r for r in rows if r["traders"] == traders
                           and r["goods"] == goods
                           and r["direction"] == "silent"), None)
            shapes.append({
                "traders": traders, "goods": goods,
                "structural_note": shape_note(traders, goods),
                # Carried into the verdict because "reads: NO" is easy to
                # misread as "nothing happens in this cell". Where goods
                # outnumber traders the opposite is true and violently so: the
                # convention arm is at total ruin for every δ *including zero*
                # while the silent arm is at none. A huge convention effect and
                # no content-error effect are the same row here.
                "silent": (None if anchor is None
                           else anchor["zero_period_share"]),
                "spans": spans, "pinned": pinned,
                # H0c is refused only if the share is flat in δ across *both*
                # directions, so a shape reads if either direction moved.
                "reads": (not pinned) and max(spans.values()) > PINNED,
            })
    readable = [s for s in shapes if s["reads"]]
    best = max(readable, key=lambda s: max(s["spans"].values()), default=None)
    return {"shapes": shapes, "readable": len(readable),
            "shapes_swept": len(shapes), "widest": best}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--islands", type=int, default=48)
    p.add_argument("--seed0", type=int, default=1)
    # The game island's whole allowed range, because whether the primary reads
    # at all depends on where in it you are, and gate 3's job is to find that
    # out before rung 1 picks a cell.
    p.add_argument("--traders", type=int, nargs="*", default=[2, 3, 4])
    p.add_argument("--goods", type=int, nargs="*", default=[2, 3, 4, 5])
    p.add_argument("--periods", type=int, default=4,
                   help="the flow analogue of an episode; 4 matches the cell "
                        "rung 0a replicates")
    p.add_argument("--rounds", type=int, default=60,
                   help="scripted trading rounds per period, matching 004's "
                        "flow runs. Not a claim that a round is a second.")
    p.add_argument("--deltas", type=float, nargs="*", default=list(DELTAS))
    p.add_argument("--directions", nargs="*", default=["flatten", "sharpen"])
    p.add_argument("--adherences", type=float, nargs="*", default=[1.0],
                   help="1.0 is the calibration proper -- what a convention of "
                        f"quality δ is worth when everybody holds it, which is "
                        f"what H0c asks. The partial levels {ADHERENCES[1:]} "
                        "are the model tier's adoption-shortfall term and are "
                        "off by default because they multiply the sweep.")
    p.add_argument("--json", type=Path, default=None)
    args = p.parse_args(argv)

    print(f"{args.islands} islands, {args.periods} periods x {args.rounds} "
          f"rounds, traders {args.traders}, goods {args.goods}, "
          f"adherence {args.adherences}")
    print("scripted traders; no models, nothing spent. This rung measures the "
          "content\naxis only -- CS - CP is not measurable with scripted "
          "seats at any δ.\n")

    rows, records = sweep(args)
    result = verdict(rows, args)

    for traders in args.traders:
        for goods in args.goods:
            note = shape_note(traders, goods)
            print(f"\n## {traders} traders, {goods} goods"
                  + (f"  —  {note}" if note else ""))
            anchor = next((r for r in rows if r["traders"] == traders
                           and r["goods"] == goods
                           and r["direction"] == "silent"), None)
            if anchor:
                print(f"silent (no convention): zero-period share "
                      f"{anchor['zero_period_share']:.3f}   "
                      f"autarky {anchor['autarky']:.3f}  "
                      f"ceiling {anchor['ceiling']:.3f}")
            for direction in args.directions:
                points = curve(rows, traders, goods, direction,
                               args.adherences[0])
                if not points:
                    continue
                print(f"\n| {direction} δ | realised error | "
                      f"**zero-period share** | always-zero | recoveries | "
                      f"efficiency (survivors) | scored |")
                print("|---|---|---|---|---|---|---|")
                for r in points:
                    eff = ("—" if r["efficiency_median"] is None
                           else f"{r['efficiency_median']:.3f}")
                    print(f"| {r['delta']} | {r['error_median']:.3f} | "
                          f"**{r['zero_period_share']:.3f}** | "
                          f"{r['always_zero']}/{r['agents_total']} | "
                          f"{r['recoveries']} | {eff} | "
                          f"{r['scored']}/{r['islands']} |")

    print(f"\n\n## Verdict\n")
    print("| traders | goods | silent | "
          + " | ".join(f"{d} span" for d in args.directions)
          + " | reads | note |")
    print("|---|---|" + "---|" * (len(args.directions) + 3))
    for s in result["shapes"]:
        silent = "—" if s["silent"] is None else f"{s['silent']:.3f}"
        print(f"| {s['traders']} | {s['goods']} | {silent} | "
              + " | ".join(f"{s['spans'].get(d, 0):.3f}"
                           for d in args.directions)
              + f" | {'yes' if s['reads'] else 'NO'} | "
              + (s["structural_note"] or "") + " |")

    print(f"\n{result['readable']}/{result['shapes_swept']} shapes can read "
          f"the primary at all.")
    if result["widest"]:
        w = result["widest"]
        print(f"Widest: {w['traders']} traders x {w['goods']} goods, "
              f"span {max(w['spans'].values()):.3f}.")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "config": {k: (str(v) if isinstance(v, Path) else v)
                       for k, v in vars(args).items()},
            "verdict": result, "summary": rows, "records": records,
        }, indent=1))
        print(f"\nwrote {args.json} ({len(records)} records)")

    if not result["readable"]:
        print("\nFLAT IN δ EVERYWHERE, OR PINNED AT A BOUND EVERYWHERE.")
        print("H0c is refused: there is no content axis on this island for the")
        print("distribution axis to hold constant. PREFLIGHT gate 3 says stop "
              "and do\nnot spend, and this exits non-zero so that it is not "
              "read as a pass.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
