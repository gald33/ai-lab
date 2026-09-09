"""The worked example that found the hole, kept so the numbers can be re-checked.

SUPERSEDED IN PLAY, 2026-09-09: Gal, *"we have no routes."* The right-hand
half of what this file prints -- "with routes" -- is the game as it was
designed and is no longer the game. It is kept because it is the clearest
statement of what the routes were worth, which is the thing the decision
was made against; `games/hue-and-cry.md`, "There are no routes", carries
the decision and the numbers at 1000 landmarks. The left-hand half,
"without routes -- she may go anywhere", is now simply the game.


`games/hue-and-cry.md` claims, in "The map has routes, and without them there
is no game", that a fugitive free to move anywhere leaves a searcher 5 or 6 of
8 candidates while one confined to three exits leaves 2 or 3 of 3. That claim
is this file, and it is committed because a measurement without its
reproduction gets re-measured -- and, in this case, was very nearly not
measured at all: the design shipped without routes and the defect surfaced
only when somebody asked for an example.

    python3 games/hue-and-cry/worked_example.py

Not the settler and not the reference searcher, both of which are still
unbuilt (see "What would have to be built"). This is eight landmarks and one
forward filter, sized to be read rather than to be general.

READ THE POSTERIORS AS THE MANAGER'S VIEW, NOT A SEARCHER'S. Since
2026-09-07 the design says the matrix is large, sparse and *unknown to
players*, and that a zero in it is not a denial -- so nobody in a real game
can run the filter below, which needs the whole table in hand. What this
file still establishes, and the reason it is kept, is the point it was
written for: routes are what make a trail worth following at all. That
holds whether or not anyone can compute a posterior over them.
"""

from fractions import Fraction

#: Eight landmarks and the attributes true of each. A clue is exactly one of
#: these, true of where she has *gone*, posted in the room she has *left*.
ATTRIBUTES: dict[str, set[str]] = {
    "Reykjavik": {"northern", "coastal", "capital", "latin"},
    "Oslo":      {"northern", "coastal", "capital", "latin"},
    "Cairo":     {"northern", "capital"},
    "Kyoto":     {"northern"},
    "Mumbai":    {"northern", "coastal"},
    "Lima":      {"coastal", "capital", "latin"},
    "Nairobi":   {"capital", "latin", "highland"},
    "Quito":     {"capital", "latin", "highland"},
}

#: The exits. Three from each landmark, committed with the table and public.
#: This is the part the design was missing, and the reason it now has a floor.
ROUTES: dict[str, list[str]] = {
    "Reykjavik": ["Oslo", "Cairo", "Lima"],
    "Oslo":      ["Reykjavik", "Cairo", "Mumbai"],
    "Cairo":     ["Nairobi", "Mumbai", "Oslo"],
    "Kyoto":     ["Mumbai", "Lima", "Oslo"],
    "Mumbai":    ["Nairobi", "Kyoto", "Cairo"],
    "Lima":      ["Quito", "Kyoto", "Reykjavik"],
    "Nairobi":   ["Cairo", "Quito", "Mumbai"],
    "Quito":     ["Lima", "Nairobi", "Reykjavik"],
}


def her_best_clue(destination: str, reachable: list[str]) -> tuple[str, list[str]]:
    """The least informative true attribute, and what it leaves standing.

    Her whole strategy in one line: every attribute here is true of where she
    has gone, so she is choosing among honest clues for the one that separates
    least. `reachable` is what the searcher can rule against -- the exits of
    the room she left, or the whole map when there are no routes.
    """
    survivors = {a: [x for x in reachable if a in ATTRIBUTES[x]]
                 for a in ATTRIBUTES[destination]}
    best = max(survivors, key=lambda a: len(survivors[a]))
    return best, survivors[best]


def propagate(belief: dict[str, Fraction]) -> dict[str, Fraction]:
    """One blind tick: she moved and nobody was holding the room she left."""
    out: dict[str, Fraction] = {}
    for landmark, mass in belief.items():
        for exit_ in ROUTES[landmark]:
            out[exit_] = out.get(exit_, Fraction(0)) + mass / len(ROUTES[landmark])
    return out


def read_clue(left: str, clue: str) -> dict[str, Fraction]:
    """One tick with a warrant for the room she left: her exits, filtered."""
    live = [x for x in ROUTES[left] if clue in ATTRIBUTES[x]]
    return {x: Fraction(1, len(live)) for x in live}


def _show(tag: str, belief: dict[str, Fraction]) -> None:
    ranked = sorted(belief.items(), key=lambda kv: (-kv[1], kv[0]))
    print(f"  {tag}: {len(belief)} live -- "
          + ", ".join(f"{k} {float(v) * 100:.0f}%" for k, v in ranked))


def main() -> None:
    everywhere = list(ATTRIBUTES)

    print("without routes -- she may go anywhere, so a clue is read against all 8:")
    worst = 0
    for destination in everywhere:
        clue, left = her_best_clue(destination, everywhere)
        worst = max(worst, len(left))
        print(f"  gone to {destination:10} she posts {clue:9} -> {len(left)} of 8 survive")
    print(f"  worst case for the searcher: {worst} of 8\n")

    print("with routes -- the same clue, read by someone holding the room she left:")
    tightest = 0
    for left_room, exits in ROUTES.items():
        biggest = max((her_best_clue(d, exits) for d in exits), key=lambda r: len(r[1]))
        tightest = max(tightest, len(biggest[1]))
        print(f"  she left {left_room:10} exits {exits} -> her best clue leaves "
              f"{len(biggest[1])} of 3: {biggest[1]}")
    print(f"  worst case for the searcher: {tightest} of 3\n")

    print("three ticks. Ada holds Cairo and Mumbai; Bram holds Oslo and Nairobi.")
    ada = {landmark: Fraction(1, len(everywhere)) for landmark in everywhere}
    bram = dict(ada)
    _show("tick 0 prior            ", ada)

    print("  tick 1: Cairo -> Nairobi, CLUE capital posted in Cairo.")
    ada = read_clue("Cairo", "capital")          # Ada holds Cairo
    bram = propagate(bram)                        # Bram does not
    _show("       Ada  (read Cairo) ", ada)
    _show("       Bram (blind)      ", bram)
    print("       note: `highland` was also true of Nairobi and would have pinned")
    print("       her exactly. She posted the least informative true fact instead.")

    print("  tick 2: Nairobi -> Quito, CLUE latin posted in Nairobi.")
    ada = propagate(ada)                          # Ada does not hold Nairobi
    bram = read_clue("Nairobi", "latin")          # Bram does
    _show("       Ada  (blind)      ", ada)
    _show("       Bram (read Nairobi)", bram)
    print("       Bram can arrest here and win.")

    print("  tick 3: Quito -> Lima, CLUE coastal posted in Quito. Nobody holds Quito.")
    ada, bram = propagate(ada), propagate(bram)
    _show("       Ada               ", ada)
    _show("       Bram              ", bram)
    print("  truth at tick 3: Lima.")
    print("\n  Bram went from a certain arrest to a three-way tie in one blind tick.")
    print("  That decay is the branching factor, it is known in advance, and it is")
    print("  why this game is about when to commit rather than about where.")


if __name__ == "__main__":
    main()
