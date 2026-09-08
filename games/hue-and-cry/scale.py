"""Why the matrix is sparse, and what that buys against harvesting.

Gal's argument, 2026-09-07, and it corrects the reason this document had
given for sparsity. Marking only a few hints per landmark is not primarily a
game-design choice about information -- it is a GENERATION COST choice.
Deciding every (landmark, hint) cell is N*M work, and since the vocabulary
grows with the map, N*M is superlinear. Selecting a few hints per landmark
is N*3, which is linear, and linear is what makes a LARGE matrix affordable
at all.

The consequence, which is this file's reason for existing: harvesting cost
is also linear in N, so the defence against a reconstructed matrix is simply
a bigger one -- and a bigger one is exactly what linear generation buys. The
permutation trick this document previously floated is withdrawn; see
`games/hue-and-cry.md`, "The harvesting gap".

    python3 games/hue-and-cry/scale.py
"""

#: Hints selected per landmark. The "3" in Gal's "N*3".
HINTS_PER_LANDMARK = 3

#: Ticks in a game, so also the number of (landmark, hint) pairs a single
#: game can expose to somebody writing them down.
TICKS_PER_GAME = 12


def costs(landmarks: int, vocabulary: int) -> dict[str, float]:
    """Generation cost both ways, and what a harvester has to pay.

    `dense` is the N*M every cell would take. `sparse` is the N*3 actually
    generated. `landmarks_per_hint` is how many places share a hint on
    average, which is what decides how much a hint narrows. `games_to_harvest`
    is how many games it takes to observe every selected pair once -- a floor
    on reconstruction, and a generous one, since it assumes no repeats.
    """
    sparse = landmarks * HINTS_PER_LANDMARK
    return {
        "dense": landmarks * vocabulary,
        "sparse": sparse,
        "landmarks_per_hint": sparse / vocabulary,
        "games_to_harvest": sparse / TICKS_PER_GAME,
    }


def _row(landmarks: int, vocabulary: int) -> None:
    c = costs(landmarks, vocabulary)
    print(f"  N={landmarks:>7,} M={vocabulary:>7,}"
          f"  dense={c['dense']:>15,.0f}  sparse={c['sparse']:>9,.0f}"
          f"  {c['dense'] / c['sparse']:>8,.0f}x cheaper"
          f"   {c['landmarks_per_hint']:>7.1f} landmarks/hint"
          f"   {c['games_to_harvest']:>9,.0f} games to harvest")


def main() -> None:
    sizes = (100, 1_000, 10_000, 100_000)

    print("vocabulary grows with the map (M = N):")
    for n in sizes:
        _row(n, n)

    print("\nvocabulary held small while the map grows (M = 200):")
    for n in sizes:
        _row(n, 200)

    print("""
Two things to read off this, and the second is the useful one.

Sparsity is worth 33x at a hundred landmarks and 33,000x at a hundred
thousand, because the saving is the ratio M/3 and M grows. That is the
whole of "linear versus superlinear": the dense matrix cannot be made
large and the sparse one can.

And N and M are SEPARABLE KNOBS. Harvesting cost depends only on N -- the
rows are identical between the two tables -- while how much a hint narrows
depends only on M, running from 3 landmarks per hint to 1,500. So a hint's
informativeness is tuned with the vocabulary and resistance to harvesting
is bought with the map, independently. This document previously worried
that the two moved together and in opposite directions; on this parameter
they do not.""")


if __name__ == "__main__":
    main()
