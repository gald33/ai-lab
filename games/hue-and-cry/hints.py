"""Three sentences per landmark, which is what a person actually reads.

Gal, 2026-09-08: *"2) for every landmark create 3 hint sentences"*, and
earlier: *"I would love it if the hint could be given as a
report/sighting/rumor, and such, so we get a whole sentence"*, and *"we
'sell' on human interacting about it in social media, it must evoke
feelings"*.

    python3 games/hue-and-cry/hints.py --build     # writes hints.tsv
    python3 games/hue-and-cry/hints.py             # read some

WHY SIX AND NOT THREE. A landmark carries six candidate descriptors and the
game seed makes **three of them live**, so three is what any one game shows
and six is what has to exist for the seed to have a choice. Writing only
three would be deciding in the gazetteer what the seed is supposed to
decide. So: six sentences per landmark, 6,000 in the file, three of them
live in front of you.

HOW UNIQUENESS AND COLLISION BOTH HOLD, which sounded like a contradiction
and is not. Gal asked for sentences **unique per landmark**; this game's
oldest measured lesson is that a hint true of exactly one landmark ends the
chase. Both are satisfied because they are about different things:

- **The words are unique.** No two landmarks in the file carry the same
  sentence. Asserted by `test_hints.py`, not hoped for.
- **What the words assert is shared.** Every sentence is a rendering of one
  descriptor, and every descriptor is true of at least sixteen landmarks.
  Two places that share `traffic_keeps_left` get two different sentences
  about stepping off a kerb the wrong way.

So a reader who has seen a sentence before learns the descriptor, not the
room -- which is what a clue is supposed to do -- while nobody ever reads
the same line twice. The prose carries the feeling and the descriptor
carries the ambiguity.

**Nothing here is generated at run time and no model is in the loop.** The
clauses in `clauses.py` are written by a person; this file is the
deterministic assignment of one clause, one witness and one frame to each
(landmark, descriptor) pair, which is arithmetic.
"""

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from clauses import CLAUSES  # noqa: E402
from descriptors import all_descriptors  # noqa: E402

DATA = Path(__file__).with_name("hints.tsv")

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


def _index(landmark: str, descriptor: str, salt: int) -> int:
    """A stable number for this pair, so a rebuild does not reshuffle the
    file and a diff shows only what actually changed."""
    key = f"{landmark}\0{descriptor}\0{salt}".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def build() -> list[tuple[str, str, str]]:
    """(landmark, descriptor, sentence) for every candidate pair.

    Distinctness is enforced rather than assumed. The hash picks a clause, a
    witness and a frame; if that sentence is already used -- and it will be,
    because a descriptor carried by 189 landmarks is drawing from one clause
    and 624 witness-frame pairs -- the salt is bumped and it draws again.
    """
    rows, seen = [], set()
    for landmark, words in sorted(all_descriptors().items()):
        for descriptor in sorted(words):
            bank = CLAUSES[descriptor]
            for salt in range(4096):
                n = _index(landmark, descriptor, salt)
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


def write(rows, out) -> None:
    out.write("# Three of these six are live in any one game -- the seed\n"
              "# decides which. Written by hints.py from clauses.py; see\n"
              "# hints.py on why the sentences are unique and what they\n"
              "# assert is not.\n"
              "# landmark\tdescriptor\tsentence\n")
    for landmark, descriptor, sentence in rows:
        assert "\t" not in sentence
        out.write(f"{landmark}\t{descriptor}\t{sentence}\n")


def load() -> list[dict]:
    out = []
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        landmark, descriptor, sentence = line.split("\t")
        out.append({"landmark": landmark, "descriptor": descriptor,
                    "sentence": sentence})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true", help="rewrite hints.tsv")
    args = ap.parse_args()

    if args.build:
        rows = build()
        with open(DATA, "w", encoding="utf-8") as fh:
            write(rows, fh)
        print(f"{len(rows):,} sentences, {len(set(r[2] for r in rows)):,} distinct")
        return

    rows = load()
    by_landmark: dict[str, list[dict]] = {}
    for r in rows:
        by_landmark.setdefault(r["landmark"], []).append(r)
    print(f"{len(rows):,} sentences over {len(by_landmark):,} landmarks\n")

    for name in ("Stonehenge", "Uluru", "Area 51"):
        print(f"  {name}")
        for r in by_landmark[name][:3]:
            print(f"    {r['sentence']}")
        print()

    counts = Counter(r["descriptor"] for r in rows)
    word, n = counts.most_common(1)[0]
    same = [r for r in rows if r["descriptor"] == word][:3]
    print(f"  and the collision, which is the point -- {n} landmarks carry"
          f" {word}:")
    for r in same:
        print(f"    {r['landmark']}: {r['sentence']}")


if __name__ == "__main__":
    main()
