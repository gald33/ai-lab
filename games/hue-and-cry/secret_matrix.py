"""A matrix nobody stores, and a way to prove it was played honestly.

Gal, 2026-09-07: *"next we need to compile a matrix, but, it should not be
public, that's a problem"*. It is a problem, and it has two halves that pull
against each other:

  SECRECY   the whole access model rests on players being unable to
            enumerate landmark names (`rooms_from_names.py`). A published
            matrix hands them the enumeration.
  HONESTY   this repo's manager is one nobody has to trust. A secret table
            is a manager saying "the hint was legal, take my word for it",
            which is the thing the island's commit-reveal exists to refuse.

The first half turns out not to need solving, because there is nothing to
publish: THE MATRIX IS NOT COMPILED, IT IS DERIVED. One 32-byte seed and a
PRF give a row on demand in microseconds, so a hundred-thousand-landmark
matrix costs 32 bytes at rest and nothing to build. The seed lives in the
environment, never in the repo -- the pattern `.gitignore` and Switchboard's
own `SWITCHBOARD_KEY_<ID>` already set.

This is still not "on-the-fly generation" in the sense Gal ruled out: no
model, no payment, no run-to-run variation. It is a pure function of the
seed, so a game replays exactly.

The second half is what the Merkle half of this file is for. See
`games/hue-and-cry.md`, "A matrix nobody sees and nobody has to trust".

    python3 games/hue-and-cry/secret_matrix.py
"""

import hashlib
import hmac

#: Domain separators, so a digest minted for one purpose can never be
#: mistaken for one minted for another.
MATRIX_INFO = b"hue-and-cry/v1/matrix"
LEAF_INFO = b"hue-and-cry/v1/leaf"
NODE_INFO = b"hue-and-cry/v1/node"

#: Hints selected per landmark -- the "3" in the N*3 of `scale.py`.
HINTS_PER_LANDMARK = 3


def hints_for(seed: bytes, landmark: str, vocabulary: int,
              count: int = HINTS_PER_LANDMARK) -> list[int]:
    """The hints this landmark may post, derived rather than looked up.

    Unpredictable without the seed and identical with it, which is the whole
    requirement: secret during play, and exactly reproducible for a replay.
    Rejection-samples so the hints are distinct; the loop runs `count` times
    plus collisions, which at any sane vocabulary is `count`.
    """
    chosen: list[int] = []
    counter = 0
    while len(chosen) < count:
        digest = hmac.new(
            seed,
            MATRIX_INFO + b"\x00" + landmark.encode("utf-8") + b"\x00" + bytes([counter]),
            hashlib.sha256,
        ).digest()
        candidate = int.from_bytes(digest[:8], "big") % vocabulary
        if candidate not in chosen:
            chosen.append(candidate)
        counter += 1
    return sorted(chosen)


def leaf(landmark: str, hints: list[int]) -> bytes:
    """One landmark's row, as a commitment leaf."""
    body = b",".join(str(h).encode() for h in hints)
    return hashlib.sha256(
        LEAF_INFO + b"\x00" + landmark.encode("utf-8") + b"\x00" + body
    ).digest()


def _pair(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(NODE_INFO + b"\x00" + left + right).digest()


def tree(leaves: list[bytes]) -> list[list[bytes]]:
    """Layers, bottom-up. Odd layers duplicate their last node."""
    layers = [list(leaves)]
    while len(layers[-1]) > 1:
        current = layers[-1]
        if len(current) % 2:
            current.append(current[-1])
        layers.append([_pair(current[i], current[i + 1])
                       for i in range(0, len(current), 2)])
    return layers


def opening(layers: list[list[bytes]], index: int) -> list[bytes]:
    """The siblings needed to walk one row up to the root."""
    path = []
    for layer in layers[:-1]:
        sibling = index ^ 1
        path.append(layer[sibling] if sibling < len(layer) else layer[index])
        index //= 2
    return path


def opens(root: bytes, landmark: str, hints: list[int],
          index: int, path: list[bytes]) -> bool:
    """Did this row really come from the matrix that was committed to?

    What a player runs after a game, against a root published before it.
    """
    digest = leaf(landmark, hints)
    for sibling in path:
        digest = (_pair(digest, sibling) if index % 2 == 0
                  else _pair(sibling, digest))
        index //= 2
    return digest == root


def main() -> None:
    import os
    import time

    seed = os.urandom(32)
    vocabulary, landmarks = 100_000, 100_000
    names = [f"landmark-{i}" for i in range(landmarks)]

    print("derived, not compiled -- three rows from one 32-byte seed:")
    for name in ("Reykjavik", "Cairo", "Quito"):
        print(f"  {name:<10} {hints_for(seed, name, vocabulary)}")

    start = time.perf_counter()
    for name in names[:20_000]:
        hints_for(seed, name, vocabulary)
    each = (time.perf_counter() - start) / 20_000
    print(f"\n  {each * 1e6:.0f} us per row"
          f"   |  {landmarks:,}-landmark matrix at rest: 32 bytes"
          f"   |  materialised it would be"
          f" {landmarks * HINTS_PER_LANDMARK * 4 / 1e6:.1f} MB")

    start = time.perf_counter()
    layers = tree([leaf(n, hints_for(seed, n, vocabulary)) for n in names])
    built = time.perf_counter() - start
    root = layers[-1][0]

    index = 42_195
    path = opening(layers, index)
    verified = opens(root, names[index], hints_for(seed, names[index], vocabulary),
                     index, path)

    print(f"\ncommitment over {landmarks:,} rows, built in {built:.1f}s:")
    print(f"  root published before the game:  {len(root)} bytes")
    print(f"  one row opened afterwards:       {len(path)} steps,"
          f" {len(path) * 32} bytes  ->  verifies: {verified}")
    print(f"  a 12-tick game publishes:        "
          f"{12 * (len(path) * 32 + 40) / 1024:.1f} KB")
    print(f"  games before the map is spent:   "
          f"{landmarks // 12:,}")

    tampered = opens(root, names[index], [1, 2, 3], index, path)
    print(f"  a row the manager made up:       verifies: {tampered}")

    print("""
So the manager keeps its secret and still cannot lie. It publishes the root
before play, opens only the rows a game actually used, and each opening is
checkable by anyone against that root. What was never used stays unknown,
which is what the access model needs; what was used is proved, which is what
the record needs.

And the reveals are PUBLIC and EQUAL. Everyone who reads them accumulates
the same partial map at the same rate, so building one is a technique
available to every player rather than a private edge belonging to whoever
played most -- which is the harvesting problem turning into the thing the
experiment wanted to watch.""")


if __name__ == "__main__":
    main()
