"""One seed per game. It is the matrix, the room addresses, and the proof.

Gal, 2026-09-07: *"maybe the hash is over landmark and game seed - just one
seed per game"*. It collapses most of what this file used to contain, and it
resolves a contradiction the design document had walked into.

WHAT IT IS. A game draws one 32-byte seed. Everything comes from it:

    hints_for(seed, landmark)   the hints that landmark may post
    salt_for(seed)              the room salt, published at the open
    room_token(name, salt)      the room a landmark lives in
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
`games/carmel-taldiego.md` had already decided the map is drawn rather than
authored, on the grounds that *a memorisable map means the instrument has
quietly stopped measuring search* -- and harvesting a durable matrix is
memorising the map. The two positions contradicted each other and this is
the one that survives: navigation is measured inside a game, and every game
starts from a map nobody has seen.

    python3 games/carmel-taldiego/secret_matrix.py
"""

import base64
import hashlib
import hmac

#: Domain separators, so a digest minted for one purpose can never be
#: mistaken for one minted for another.
MATRIX_INFO = b"hue-and-cry/v1/matrix"
ROOM_INFO = b"hue-and-cry/v1/landmark"  # matches rooms_from_names.INFO
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


SALT_INFO = b"hue-and-cry/v1/salt"

#: The algorithm she hands out in her first message. Gal, 2026-09-09, gave
#: it in this exact form:
#:
#:     "w_" + hash(landmark, <salt>)
#:
#: and the `w_` is part of the string you hand to `join_room`, not the hub's
#: own identifier. Any string is a legal Switchboard token -- the client
#: hashes whatever you give it to get the wire address -- so a player never
#: sees two steps. One name, one line, one room.
#:
#: It is the technique Switchboard already uses, one link earlier: checked
#: against the installed wheel, `rooms.workspace_for` is
#: `sha256(info || version || token)` truncated and prefixed. Ours is
#: `sha256(info || salt || name)`. Same primitive, same shape.
#:
#: A bare digest with no HMAC and no KDF parameters, because that is what a
#: player can actually compute: Switchboard's MCP surface is 27 tools --
#: `say`, `dm`, `whisper`, `inbox`, `history`, `roster`, `whoami`,
#: `checkin`, `claim`, `renew`, `release`, `claims`, `join_room`, `keygen`,
#: `subscribe`, `unsubscribe`, `leave`, `rendezvous`, `help`, `switchboard`,
#: `session_*`, `board_*` -- and **not one of them hashes**. The game must
#: not require a tool nobody was given.
RECIPE = 'token = "w_" + sha256("hue-and-cry/v1/landmark" || 0x00 || salt || 0x00 || name)'

#: The second step, and it is Switchboard's rather than ours.
#:
#: `rooms.workspace_for` names a room by the hash of its token, so the token
#: alone is not an address -- and the notice used to stop at the first line
#: and say "hand what comes out to join_room", which **refuses it**:
#: `InviteError: not a switchboard invite (expected it to start with
#: 'swb1_')`. That was wrong from the day it was written and nothing caught
#: it, because every test in this game drives *her* and the searcher's side
#: existed only as words in a notice. Found by trying to play, 2026-09-10.
ADDRESS_RECIPE = 'room = "w_" + base64url(sha256(token))[:22]'


def room_address(landmark: str, salt: bytes) -> str:
    """The wire identifier a searcher actually joins, from a name and a salt.

    Both steps of the published recipe, in one place, so the notice and the
    test that follows it cannot drift from each other. It is deliberately
    the same arithmetic as `switchboard.rooms.workspace_for` and is checked
    against it in `test_rooms_from_names`.
    """
    digest = hashlib.sha256(room_token(landmark, salt).encode()).digest()
    return ROOM_PREFIX + base64.urlsafe_b64encode(
        digest).decode().rstrip("=")[:22]

ROOM_PREFIX = "w_"


def salt_for(seed: bytes) -> bytes:
    """The room salt, published when a campaign opens.

    A game still has exactly one secret -- everything comes from the seed --
    but the salt is a one-way step off it, so publishing the salt says
    nothing about the hints or the treasures, which stay sealed until the
    reveal.

    This exists because the alternative was measured against the design and
    lost. Deriving rooms from the seed itself means nobody but her can
    compute any address while the game runs, and `games/carmel-taldiego.md` is
    explicit that this "becomes a pure chain -- you can follow her but never
    get ahead, which is too weak". The salt is what lets a searcher think of
    a name and go there.
    """
    return hashlib.sha256(SALT_INFO + b"\x00" + seed).digest()


def room_token(landmark: str, salt: bytes) -> str:
    """The room a landmark lives in, given the published salt.

    Any string is a legal Switchboard token -- the library hashes it to get
    the wire identifier -- so the only requirements are that it is
    infeasible to guess without the name, and that both sides derive the
    same one. `rooms_from_names.py` checks it against the installed wheel.
    """
    return ROOM_PREFIX + hashlib.sha256(
        ROOM_INFO + b"\x00" + salt + b"\x00" + landmark.encode("utf-8")
    ).hexdigest()


def token_for(seed: bytes, landmark: str) -> str:
    """Deprecated: the room from the SEED rather than the published salt.

    Kept only so the failure is loud if anything still calls it. A room
    nobody but her can derive is the "pure chain" the design rejects.
    """
    raise RuntimeError(
        "rooms come from the published salt, not the seed: "
        "room_token(landmark, salt_for(seed))")


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
    against `hints_for`, and every room address against `room_token`.
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
              f"   room {room_token(landmark, salt_for(seed))[:24]}...")

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
              f"  room {room_token(landmark, salt_for(seed))[:16]}...")
        print(f"  {landmark} in game B   hints {hints_for(other, landmark, vocabulary)}"
              f"  room {room_token(landmark, salt_for(other))[:16]}...")

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
