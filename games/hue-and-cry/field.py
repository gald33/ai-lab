"""The searchers: what they tell each other, and what that is worth.

Gal, 2026-09-09: *"The players can also write notes to help or to confuse
others."*

    python3 games/hue-and-cry/field.py            # what one liar costs
    python3 games/hue-and-cry/field.py --sample

A NOTE CANNOT LIE ABOUT THE NEXT ROOM, WHICH IS WHAT MAKES IT INTERESTING
========================================================================

The first thing to work out is what a note can even say. Not "she went from
here to X" -- the `CLUE` line in the room she left already carries the exact
workspace, so anybody standing there reads the truth and a note contradicting
it is simply ignored. **The hash beats the note, always.**

What a note can carry is *position further along the trail than the reader
has walked*. A searcher four rooms behind cannot know room seven exists. A
note saying "she is at <address>" lets them skip straight there instead of
walking the chain -- and that is the only thing in this game that beats the
arithmetic in `carmel.py`, where a trail-follower's gap can never close by
more than what she steals.

So the trade is sharp on both sides:

- **A true note is worth a great deal**, because it converts somebody else's
  walking into your position.
- **A false note is worth as much**, because acting on it costs the reader a
  whole leg of travel in the wrong direction, and they cannot tell which
  they have until they arrive.

And the reader cannot verify before travelling. That is the whole game the
notes create, and it is the one this document calls the interesting
behaviour: *"the coordination is the interesting behaviour, it is recorded
verbatim in the transcript, and none of it is settled or scored."*

WHERE THEY GO
=============

The lobby, which is public and which nobody has to leave to read -- rooms
here cannot forbid multi-membership, so a searcher watches the lobby while
travelling. That is the same property that made the omnipresence problem
real, used deliberately: notes are broadcast, and so is the lie.

NOT THE RUNTIME
===============

Same warning as `carmel.py`. This advances a virtual clock to put a number
on a design question; the real searchers are long-lived sessions reading
boards on their own clocks.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
from secret_matrix import _prf  # noqa: E402


class Note:
    """One line in the lobby: somebody says she is at a room, at a time.

    Nothing settles it. The manager does not read it and no score depends
    on it, which is why a liar is playing the game rather than cheating at
    it.
    """

    __slots__ = ("room", "at", "by", "true")

    def __init__(self, room: str, at: float, by: int, true: bool):
        self.room, self.at, self.by, self.true = room, at, by, true


def run(seed: bytes, start: str, world: C.Map, searchers: int = 4,
        liars: int = 0, trust: str = "naive", limit: int = 40,
        join_window: float = C.JOIN_WINDOW_HOURS,
        difficulty: float = C.DIFFICULTY) -> dict:
    """One campaign with a talking field. Returns what happened to her.

    She is simulated first and does not react: she is the control, and she
    cannot read the lobby in this model. A Carmel who *did* read it -- who
    saw a true note naming her room and ran -- is a strictly better Carmel
    and a different control, which is a change to make deliberately rather
    than by leaving it in.
    """
    trail = C.itinerary(seed, start, world, limit, difficulty)
    index = {leg["from"]: i for i, leg in enumerate(trail)}
    index[trail[-1]["to"]] = len(trail)

    names = sorted(world.descriptors)
    lobby: list[Note] = []
    clocks, wheres, honest = [], [], []
    for i in range(searchers):
        digest = _prf(seed, b"hue-and-cry/v1/searcher-start", str(i), 0)
        home = names[int.from_bytes(digest[:8], "big") % len(names)]
        joined = join_window * (int.from_bytes(digest[8:16], "big") / 2 ** 64)
        clocks.append(joined + C.travel_hours(world.places[home],
                                              world.places[start]))
        wheres.append(start)
        honest.append(i >= liars)

    # Everyone's first target is the opening landmark, from the notice.
    pending = [(clocks[i], start, i) for i in range(searchers)]
    wasted = 0.0
    wasted_legs = 0
    # Who each searcher has stopped believing. The cheapest possible
    # defence: act on a note, find nothing where it said, never believe
    # that author again. No reputation system, no voting, no gossip.
    burned: list[set[int]] = [set() for _ in range(searchers)]
    acting_on: list[int | None] = [None for _ in range(searchers)]

    for _ in range(limit * searchers * 2):
        if not pending:
            break
        pending.sort()
        clock, room, who = pending.pop(0)
        wheres[who] = room

        # Did the note that sent it here turn out to be nothing?
        if trust == "burned" and acting_on[who] is not None:
            if index.get(room) is None:
                burned[who].add(acting_on[who])
            acting_on[who] = None

        # Is she still standing there?
        pos = index.get(room)
        if pos is not None and pos < len(trail):
            leg = trail[pos - 1] if pos else None
            if leg and leg["arrived"] < clock <= leg["leaves"]:
                return {"outcome": "caught", "hours": clock, "by": who,
                        "reputation": leg["reputation"],
                        "notes": len(lobby), "wasted": wasted,
                        "wasted_legs": wasted_legs}

        # What it learns here, and what it says about it.
        knows = trail[pos]["to"] if pos is not None and pos < len(trail) \
            else None
        if honest[who]:
            if knows:
                lobby.append(Note(knows, clock, who, True))
        else:
            digest = _prf(seed, b"hue-and-cry/v1/lie", f"{who}:{clock}", 0)
            lie = names[int.from_bytes(digest[:8], "big") % len(names)]
            lobby.append(Note(lie, clock, who, False))

        # Where next. A truster takes the freshest note that is not its own
        # and not where it already is; otherwise it walks the trail.
        target = None
        if trust != "none":
            for note in reversed(lobby):
                if (note.at <= clock and note.by != who
                        and note.room != room
                        and note.by not in burned[who]):
                    target = note.room
                    acting_on[who] = note.by
                    break
        if target is None:
            target = knows
        if target is None:
            continue

        leg_hours = C.travel_hours(world.places[room], world.places[target])
        if index.get(target) is None:
            wasted += leg_hours
            wasted_legs += 1
        pending.append((clock + leg_hours, target, who))

    end = trail[-1]
    return {"outcome": "she got away", "hours": end["leaves"], "by": None,
            "reputation": end["reputation"], "notes": len(lobby),
            "wasted": wasted, "wasted_legs": wasted_legs}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--trials", type=int, default=60)
    args = ap.parse_args()

    world = C.Map(os.urandom(32))
    names = sorted(world.descriptors)
    seeds = [os.urandom(32) for _ in range(args.trials)]

    def sweep(**kw):
        caught = 0
        rep, wasted = [], []
        for seed in seeds:
            w = C.Map(seed)
            w.descriptors, w.places, w.treasure = (
                world.descriptors, world.places, world.treasure)
            start = names[int.from_bytes(seed[:4], "big") % len(names)]
            r = run(seed, start, w, **kw)
            caught += r["outcome"] == "caught"
            rep.append(r["reputation"])
            wasted.append(r["wasted"])
        rep.sort()
        return (caught / len(seeds), rep[len(rep) // 2],
                sum(wasted) / len(wasted))

    print(f"{args.trials} campaigns per row, four searchers\n")
    print("  Nobody talks -- each walks the trail alone, which is the"
          " reference searcher:\n")
    rate, rep, _ = sweep(searchers=4, liars=0, trust="none")
    print(f"    caught {rate:.0%}   she takes {rep}\n")

    print("  Everybody talks, and some of them lie. A note carries position"
          "\n  further along the trail than the reader has walked, which is"
          " the only\n  thing that beats walking it:\n")
    print(f"  {'liars of 4':>11}{'believes anyone':>17}"
          f"{'stops believing a liar':>24}")
    for liars in (0, 1, 2, 3):
        naive, _, w1 = sweep(searchers=4, liars=liars, trust="naive")
        wary, _, w2 = sweep(searchers=4, liars=liars, trust="burned")
        print(f"  {liars:>11}{naive:>16.0%}{wary:>23.0%}")
    print("\n  The second column is the cheapest defence there is: act on a"
          " note, find\n  nothing where it said, never believe that author"
          " again. No reputation\n  system, no voting, no gossip -- one bit"
          " per person.\n")


if __name__ == "__main__":
    main()
