"""One seed per game. It is the matrix, the room addresses, and the proof.

Gal, 2026-09-07: *"maybe the hash is over landmark and game seed - just one
seed per game"*. It collapses most of what this file used to contain, and it
resolves a contradiction the design document had walked into.

WHAT IT IS. A game draws one 32-byte seed. Everything comes from it:

    hints_for(seed, landmark)   the hints that landmark may post
    token_for(seed, landmark)   the room it lives in this game
    commitment(seed)            what is published before play

Nothing is compiled, nothing is stored, and a hundred-thousand-landmark
matrix costs 32 bytes at rest. The seed is secret while the game runs and
published when it ends, so every hint anybody posted can be re-derived and
checked by anyone holding the transcript. Commit, play, reveal -- the
island's pattern, at the size of a game.

WHAT IT REPLACES, and why the replacement is smaller. This file previously
built a Merkle tree over the rows so that a game could open the twelve rows
it used and keep the rest secret. That machinery existed to make a DURABLE
matrix survive being partially revealed. A per-game seed has nothing to keep
secret afterwards, so the tree, the per-row nonces, the inclusion proofs and
the season bookkeeping all go. The leaf-brute-force problem goes with them:
the seed is 256 bits of blinding over the whole matrix at once.

WHAT IT COSTS, AND WHY THAT IS A GAIN. Nothing accumulates across games, so
the cross-game map-building this document had called "the most interesting
technique available" cannot happen. It should not have been called that.
`games/hue-and-cry.md` had already decided the map is drawn rather than
authored, on the grounds that *a memorisable map means the instrument has
quietly stopped measuring search* -- and harvesting a durable matrix is
memorising the map. The two positions contradicted each other and this is
the one that survives: navigation is measured inside a game, and every game
starts from a map nobody has seen.

    python3 games/hue-and-cry/secret_matrix.py
"""

import hashlib
import hmac

#: Domain separators, so a digest minted for one purpose can never be
#: mistaken for one minted for another.
MATRIX_INFO = b"hue-and-cry/v1/matrix"
ROOM_INFO = b"hue-and-cry/v1/landmark"
COMMIT_INFO = b"hue-and-cry/v1/commit"

#: Hints selected per landmark -- the "3" in the N*3 of `scale.py`.
HINTS_PER_LANDMARK = 3


def _prf(seed: bytes, info: bytes, landmark: str, counter: int = 0) -> bytes:
    return hmac.new(
        seed,
        info + b"\x00" + landmark.encode("utf-8") + b"\x00" + bytes([counter]),
        hashlib.sha256,
    ).digest()


def hints_for(seed: bytes, landmark: str, vocabulary: int,
              count: int = HINTS_PER_LANDMARK) -> list[int]:
    """The hints this landmark may post. Derived, never looked up.

    Unpredictable without the seed and identical with it: secret while the
    game runs, exactly reproducible once it is revealed.
    """
    chosen: list[int] = []
    counter = 0
    while len(chosen) < count:
        candidate = int.from_bytes(
            _prf(seed, MATRIX_INFO, landmark, counter)[:8], "big"
        ) % vocabulary
        if candidate not in chosen:
            chosen.append(candidate)
        counter += 1
    return sorted(chosen)


def token_for(seed: bytes, landmark: str) -> str:
    """The room this landmark lives in, this game.

    The same seed that mints the matrix mints the addresses, so a game has
    exactly one secret. See `rooms_from_names.py` for why knowing a name is
    what admits you, and for the check against the Switchboard wheel.
    """
    return _prf(seed, ROOM_INFO, landmark).hex()


def commitment(seed: bytes) -> str:
    """What is published before play. The seed itself is published after.

    Binding, because a second seed with this digest cannot be found; hiding,
    because the digest says nothing about the matrix it generates. That is
    the whole proof -- there is no tree and no inclusion path, because
    revealing the seed reveals everything at once and nothing is being held
    back.
    """
    return hashlib.sha256(COMMIT_INFO + b"\x00" + seed).hexdigest()


def replays(published_seed: bytes, published_commitment: str) -> bool:
    """Did the manager play the matrix it committed to?

    What anybody runs after a game, on the seed the manager published. If
    this holds, every hint in the transcript can be re-derived and checked
    against `hints_for`, and every room address against `token_for`.
    """
    return commitment(published_seed) == published_commitment


def main() -> None:
    import os
    import time

    vocabulary = 100_000
    seed = os.urandom(32)

    print("one seed per game. everything below comes from these 32 bytes:\n")
    print(f"  commitment published before play   {commitment(seed)}")
    print(f"  seed published after play          {seed.hex()}\n")

    for landmark in ("Reykjavik", "Cairo", "Quito"):
        print(f"  {landmark:<10} hints {hints_for(seed, landmark, vocabulary)}"
              f"   room {token_for(seed, landmark)[:24]}...")

    start = time.perf_counter()
    for i in range(20_000):
        hints_for(seed, f"landmark-{i}", vocabulary)
    each = (time.perf_counter() - start) / 20_000
    print(f"\n  {each * 1e6:.0f} us per row  |  100,000-landmark matrix at rest:"
          f" 32 bytes  |  materialised: 1.2 MB")

    print("\nthe proof, in full:")
    print(f"  the seed it committed to replays        "
          f"{replays(seed, commitment(seed))}")
    print(f"  a different seed does not               "
          f"{replays(os.urandom(32), commitment(seed))}")
    print(f"  published before a game: {len(commitment(seed)) // 2} bytes."
          f"  After: {len(seed)} bytes.")

    other = os.urandom(32)
    print("\nand a second game is a different world:")
    for landmark in ("Cairo",):
        print(f"  {landmark} in game A   hints {hints_for(seed, landmark, vocabulary)}"
              f"  room {token_for(seed, landmark)[:16]}...")
        print(f"  {landmark} in game B   hints {hints_for(other, landmark, vocabulary)}"
              f"  room {token_for(other, landmark)[:16]}...")

    print("""
So there is nothing to harvest, and that is the point rather than a
consolation. A durable matrix would reward memorising the map, and this
design had already ruled that out once -- the map is drawn precisely because
a memorisable one stops the instrument measuring search. Navigation is what
happens inside a game, against a map nobody has seen.

What went away with the durable matrix: a Merkle tree over the rows,
per-row nonces to blind the leaves, inclusion proofs to open twelve of them,
the arithmetic for how many games a map survives, and per-cohort reporting
to keep early players comparable with late ones. None of it is needed when
the reveal is total and the next game starts from a new seed.""")


if __name__ == "__main__":
    main()
