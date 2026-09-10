"""Three sentences per landmark, which is what a person actually reads.

Gal, 2026-09-08: *"2) for every landmark create 3 hint sentences"*, and
earlier: *"I would love it if the hint could be given as a
report/sighting/rumor, and such, so we get a whole sentence"*, and *"we
'sell' on human interacting about it in social media, it must evoke
feelings"*.

    python3 games/carmel-taldiego/hints.py --seed <64 hex>            # read some
    python3 games/carmel-taldiego/hints.py --seed <64 hex> --backup   # write the blob

THIS FILE WAS WRONG, AND THE CORRECTION IS THE POINT OF IT
==========================================================

The first version built a committed `hints.tsv`: 5,963 lines of
`landmark <TAB> descriptor <TAB> sentence`, in the repository, in plain
text. Gal, 2026-09-09: *"I hope you remembered the table is secret"*.

**It destroyed the game.** Every sentence is unique to a landmark -- that
is what he asked for and it is the right ask -- so a published table turns
each one into a lookup key. Carmel posts a sentence; a searcher greps the
file; the room is named exactly. No descriptor reasoning, no ambiguity, no
chase. Twelve thousand lines of careful collision work, and one committed
file routed around all of it.

It is worse than the `Reykjavik: desert` failure, because that one was
visible in the output. This one measured perfectly: `test_hints.py` proved
every sentence distinct and every descriptor shared by sixteen or more
landmarks, and both facts stayed true while the game stopped working. **A
property measured on the mechanism says nothing about a leak beside it.**

AND ENCRYPTING IT WOULD HAVE BEEN THEATRE
-----------------------------------------

Gal's instruction was *"you can commit an encrypted backup but no more
than that"*. Taken literally against the old builder, that buys nothing:
the assignment was `sha256(landmark, descriptor)`, a pure function of
`clauses.py` and `descriptors.py`, both public and both staying public.
Anyone could re-run the builder and reproduce the table byte for byte.
**Encrypting the output of a deterministic function of public inputs
protects nothing.**

So the rendering is drawn from the **game seed**, like everything else
here (`secret_matrix.py`). The clause bank is public -- it is the
authorship and it should be read -- and which clause, which witness and
which frame carry a given landmark's descriptor is not knowable until the
seed is.

WHAT THE ENCRYPTED BACKUP IS FOR, THEN
--------------------------------------

Not secrecy -- the seed already does that. It is a **commitment**. The
blob is written before play from a seed nobody has, and the key is derived
from that same seed, so publishing the seed at the reveal lets anybody
decrypt the blob and check that the sentences Carmel actually posted are
the ones the seed says she was entitled to post. That is the island's
commit-play-reveal pattern, and it is the thing `games/carmel-taldiego.md`
means by "a manager nobody has to trust".

WHY SIX AND NOT THREE. A landmark carries six candidate descriptors and
the seed makes three live, so three is what any one game shows and six is
what has to exist for the seed to have a choice.

HOW UNIQUENESS AND COLLISION BOTH HOLD, which sounded like a contradiction
and is not:

- **The words are unique.** No two landmarks carry the same sentence.
- **What the words assert is shared.** Every sentence renders one
  descriptor, and every descriptor is true of at least sixteen landmarks.

So a reader who has seen a sentence learns the descriptor, not the room --
*provided the mapping is not lying around in the repository*, which is the
whole of the correction above.
"""

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from clauses import CLAUSES  # noqa: E402
from descriptors import all_descriptors  # noqa: E402
from secret_matrix import _prf  # noqa: E402

#: The encrypted commitment. There is deliberately no plaintext counterpart
#: and `.gitignore` refuses one.
BACKUP = Path(__file__).with_name("hints.enc")

RENDER_INFO = b"hue-and-cry/v1/hint-rendering"
BACKUP_INFO = b"hue-and-cry/v1/hints-backup"

#: Who saw her. Deliberately small people in transit trades -- the ones who
#: notice a stranger and remember a face, and whose word is worth exactly
#: as much as the reader decides it is.
WITNESSES = [
    "a night porter", "a boatman", "a ticket clerk", "a hotel maid",
    "a customs officer off duty", "a taxi driver", "a bar steward",
    "a postal sorter", "a fisherman mending nets", "a museum guard",
    "a coach driver", "a girl selling cigarettes", "a locksmith",
    "a railway guard", "a money changer", "a stringer for the wire service",
    "a priest who would not give his name", "a laundry woman",
    "a doctor's receptionist", "a border guard's wife", "a shoeshine boy",
    "a hotel telephonist", "a baggage handler", "a market porter",
    "a chemist", "a barber", "a car hire clerk", "a lighthouse keeper",
    "a schoolmaster on holiday", "a nurse coming off shift",
    "a bookseller", "a tailor", "a photographer touting for trade",
    "a waiter who served her twice", "a nun", "a bus conductor",
    "a printer's apprentice", "a watchmaker", "a customs broker",
    "a diver working the harbour", "a road mender", "a ferry hand",
    "a cook", "a groundsman", "a piano tuner", "a signalman",
    "a bank teller", "a woman selling flowers", "an ambulance driver",
    "a cleaner at the terminus", "a hall porter", "a scene-shifter",
]

#: How the report reached us. `{w}` is the witness, `{c}` the clause.
FRAMES = [
    "REPORT. {W} states that {c}.",
    "SIGHTING. {W} puts her there. {C}.",
    "RUMOUR. They are saying, on the word of {w}, that {c}.",
    "WIRE. From {w}, unconfirmed: {c}.",
    "STATEMENT. {W} will swear to this and to nothing else: {c}.",
    "HEARSAY. {W} told it to somebody who told us. {C}.",
    "REPORT. Taken from {w}, who was reluctant: {c}.",
    "SIGHTING. {W} saw a woman answering the description. {C}.",
    "NOTE. Left for us by {w}. {C}.",
    "RUMOUR. {W} has been paid twice for this and it has not changed: {c}.",
    "WIRE. Relayed by {w} and not yet checked: {c}.",
    "STATEMENT. {W}, who has no reason to invent it, says {c}.",
]


def _cap(text: str) -> str:
    return text[0].upper() + text[1:] if text else text


def compose(clause: str, witness: str, frame: str) -> str:
    return frame.format(w=witness, W=_cap(witness), c=clause, C=_cap(clause))


def build(seed: bytes) -> list[tuple[str, str, str]]:
    """(landmark, descriptor, sentence) for every candidate pair, this game.

    Distinctness is enforced rather than assumed: a descriptor carried by
    189 landmarks draws 189 sentences from one clause bank crossed with 52
    witnesses and 12 frames, so collisions happen and the counter is bumped
    until the sentence is unused.
    """
    rows, seen = [], set()
    for landmark, words in sorted(all_descriptors().items()):
        for descriptor in sorted(words):
            bank = CLAUSES[descriptor]
            for counter in range(4096):
                digest = _prf(seed, RENDER_INFO,
                              f"{landmark}\0{descriptor}", counter)
                n = int.from_bytes(digest[:8], "big")
                sentence = compose(
                    bank[n % len(bank)],
                    WITNESSES[(n // 8) % len(WITNESSES)],
                    FRAMES[(n // 4096) % len(FRAMES)])
                if sentence not in seen:
                    break
            else:
                raise RuntimeError(
                    f"no unused sentence left for {descriptor!r}: it is "
                    f"carried by more landmarks than "
                    f"{len(bank) * len(WITNESSES) * len(FRAMES)} "
                    "clause-witness-frame combinations. Add clauses.")
            seen.add(sentence)
            rows.append((landmark, descriptor, sentence))
    return rows


def _key(seed: bytes) -> bytes:
    return _prf(seed, BACKUP_INFO, "", 0)


def _serialise(rows) -> bytes:
    return "\n".join("\t".join(r) for r in rows).encode("utf-8")


def write_backup(seed: bytes, path: Path = BACKUP) -> int:
    """Seal this game's renderings under a key only the seed yields.

    AES-256-GCM, nonce prepended. The point is not that the bytes are
    unreadable -- the seed already keeps them unknowable -- but that they
    were fixed BEFORE play and can be opened at the reveal.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    rows = build(seed)
    nonce = os.urandom(12)
    blob = AESGCM(_key(seed)).encrypt(nonce, _serialise(rows), None)
    path.write_bytes(nonce + blob)
    return len(rows)


def read_backup(seed: bytes, path: Path = BACKUP) -> list[dict]:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    raw = path.read_bytes()
    plain = AESGCM(_key(seed)).decrypt(raw[:12], raw[12:], None)
    out = []
    for line in plain.decode("utf-8").splitlines():
        landmark, descriptor, sentence = line.split("\t")
        out.append({"landmark": landmark, "descriptor": descriptor,
                    "sentence": sentence})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", required=True,
                    help="the game seed, 64 hex characters")
    ap.add_argument("--backup", action="store_true",
                    help=f"seal this game's renderings into {BACKUP.name}")
    args = ap.parse_args()
    seed = bytes.fromhex(args.seed)

    if args.backup:
        n = write_backup(seed)
        print(f"{n:,} sentences sealed into {BACKUP.name}"
              " -- open it with the same seed")
        return

    rows = build(seed)
    by_landmark: dict[str, list[tuple]] = {}
    for row in rows:
        by_landmark.setdefault(row[0], []).append(row)
    print(f"{len(rows):,} sentences over {len(by_landmark):,} landmarks,"
          " for this seed only\n")

    for name in ("Stonehenge", "Uluru", "Area 51"):
        print(f"  {name}")
        for _, _, sentence in by_landmark[name][:3]:
            print(f"    {sentence}")
        print()

    counts = Counter(d for _, d, _ in rows)
    word, n = counts.most_common(1)[0]
    print(f"  and the collision, which is the point -- {n} landmarks carry"
          f" {word}:")
    for landmark, descriptor, sentence in rows:
        if descriptor == word:
            print(f"    {landmark}: {sentence}")
            if landmark > "Ag":
                break


if __name__ == "__main__":
    main()
