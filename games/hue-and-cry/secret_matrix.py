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
NONCE_INFO = b"hue-and-cry/v1/nonce"
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


def nonce_for(seed: bytes, landmark: str) -> bytes:
    """This row's blinding factor. Derived, so it costs no storage."""
    return hmac.new(
        seed, NONCE_INFO + b"\x00" + landmark.encode("utf-8"), hashlib.sha256
    ).digest()


def leaf(landmark: str, hints: list[int], nonce: bytes) -> bytes:
    """One landmark's row, as a HIDING commitment.

    The nonce is why the tree can be published in full. Without it the leaf
    is `H(name, hints)` over a finite, enumerable input, and a leaf is broken
    by guessing: 13 SECONDS on one GPU at a 200-word vocabulary, and still
    only decades at 100,000. See `main` for the table. With 256 bits of
    blinding the same attack costs 2^256 whatever the vocabulary is, and the
    row is revealed when -- and only when -- the nonce is.

    It also decouples the vocabulary again. Without the nonce, M would be
    setting how much a hint narrows AND how hard a leaf is to break, which
    are unrelated jobs that would have had to be traded against each other.
    """
    body = b",".join(str(h).encode() for h in hints)
    return hashlib.sha256(
        LEAF_INFO + b"\x00" + landmark.encode("utf-8") + b"\x00" + body
        + b"\x00" + nonce
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


def opens(root: bytes, landmark: str, hints: list[int], nonce: bytes,
          index: int, path: list[bytes]) -> bool:
    """Did this row really come from the matrix that was committed to?

    What a player runs after a game, against a root published before it. The
    nonce arrives with the opening; it is the row's own secret until then.
    """
    digest = leaf(landmark, hints, nonce)
    for sibling in path:
        digest = (_pair(digest, sibling) if index % 2 == 0
                  else _pair(sibling, digest))
        index //= 2
    return digest == root


def main() -> None:
    import os
    import time
    from math import comb, log2

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

    print("\nwhy the leaves are blinded -- cost of guessing ONE unsalted leaf,")
    print("at 1e10 hashes/s against a 100,000-name list:")
    for M in (200, 1_000, 10_000, 100_000):
        seconds = comb(M, 3) * 100_000 / 1e10
        human = (f"{seconds:.0f} seconds" if seconds < 90 else
                 f"{seconds / 60:.0f} minutes" if seconds < 5400 else
                 f"{seconds / 86400 / 365:.1f} years")
        print(f"  vocabulary {M:>7,}   {log2(comb(M, 3) * 100_000):>5.1f} bits"
              f"   {human}")
    print("  with a 256-bit per-row nonce: 2^256, whatever the vocabulary is.")

    start = time.perf_counter()
    leaves = [leaf(n, hints_for(seed, n, vocabulary), nonce_for(seed, n))
              for n in names]
    layers = tree(leaves)
    built = time.perf_counter() - start
    root = layers[-1][0]

    index = 42_195
    name = names[index]
    path = opening(layers, index)
    verified = opens(root, name, hints_for(seed, name, vocabulary),
                     nonce_for(seed, name), index, path)
    withheld = opens(root, name, hints_for(seed, name, vocabulary),
                     b"\x00" * 32, index, path)
    invented = opens(root, name, [1, 2, 3], nonce_for(seed, name), index, path)

    print(f"\ncommitment over {landmarks:,} rows, built in {built:.1f}s:")
    print(f"  the whole tree can be published:  "
          f"{len(leaves) * 32 / 1e6:.1f} MB of leaves, root {len(root)} bytes")
    print(f"  one row opened afterwards:        {len(path)} steps,"
          f" {len(path) * 32 + 32} bytes with its nonce  ->  {verified}")
    print(f"  the same row without its nonce:   {withheld}")
    print(f"  a row the manager invented:       {invented}")
    print(f"  a 12-tick game publishes:         "
          f"{12 * (len(path) * 32 + 72) / 1024:.1f} KB")
    print(f"  games before the map is spent:    {landmarks // 12:,}")

    print("""
So the manager keeps its secret and still cannot lie, and now the tree
itself can be published: every leaf is visible, so the shape of the
commitment is auditable in advance -- N rows, no additions mid-game -- while
each leaf stays opaque until its nonce is handed over.

And the reveals are PUBLIC and EQUAL. Everyone who reads them accumulates
the same partial map at the same rate, so building one is a technique
available to every player rather than a private edge belonging to whoever
played most.

The map is finite, so it is spent by being played. That is a season, not a
leak: when the rows run out the seed is published, the whole matrix becomes
checkable at once, and the next season starts from a new one.""")


if __name__ == "__main__":
    main()
