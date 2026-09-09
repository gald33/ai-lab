"""What has to stay true of the sentences a person actually reads.

    python3 -m pytest games/hue-and-cry/test_hints.py -q
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import hints  # noqa: E402
from clauses import CLAUSES  # noqa: E402
from descriptors import MIN_SHARED, all_descriptors  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402


def test_the_committed_file_is_what_the_builder_makes():
    """Otherwise the file drifts from the clauses that are supposed to
    explain it, and the explanation is the part a person reads."""
    built = [(a, b, c) for a, b, c in hints.build()]
    stored = [(r["landmark"], r["descriptor"], r["sentence"])
              for r in hints.load()]
    assert built == stored, "run: python3 games/hue-and-cry/hints.py --build"


def test_no_sentence_appears_twice():
    """Gal asked for sentences unique per landmark. This is that, and it is
    asserted rather than hoped for -- a descriptor carried by 189 landmarks
    is drawing 189 sentences out of one clause bank."""
    rows = hints.load()
    counts = Counter(r["sentence"] for r in rows)
    assert [s for s, n in counts.items() if n > 1] == []


def test_every_candidate_descriptor_has_its_sentence():
    """Three of a landmark's six are live in a given game and the seed
    picks which, so a missing sentence is a game that cannot post a hint
    it is entitled to."""
    per = all_descriptors()
    have = {(r["landmark"], r["descriptor"]) for r in hints.load()}
    want = {(name, d) for name, ds in per.items() for d in ds}
    assert want - have == set()


def test_what_a_sentence_asserts_is_shared_by_many_landmarks():
    """The other half of the same requirement, and the one that is easy to
    lose: unique words, shared meaning. A sentence whose descriptor is true
    of one landmark ends the chase."""
    counts = Counter(r["descriptor"] for r in hints.load())
    assert min(counts.values()) >= MIN_SHARED


def test_no_sentence_names_a_place():
    """A hint that identifies the room is not a hint. The clause bank is
    written to name nothing; this checks the writing, since a single
    absent-minded 'in Peru' would hand over a landmark."""
    names = {p["name"] for p in load_landmarks()}
    countries = {p["country"] for p in load_landmarks()}
    # Single common words that happen to be landmark names ("Bath", "Jaipur"
    # is not one) would fire on ordinary prose, so only multi-word names and
    # country names are checked, which is where the real risk is.
    banned = {n for n in names | countries if " " in n or len(n) > 6}
    for r in hints.load():
        for word in banned:
            assert word not in r["sentence"], f"{word!r} in {r['sentence']!r}"


def test_no_clause_gives_the_witness_a_gender():
    """The frame supplies the witness -- a nun, a laundry woman, a night
    porter -- and the clause does not know which, so the clause says
    "they". Clauses used to say "he", and a nun duly reported that he had
    tracked her across Africa: wrong about the person and wrong about the
    grammar.

    `she` and `her` are not checked, because they are Carmel, who is the
    one thing every clause may assume. Orion is exempt; he is a
    constellation.
    """
    for descriptor, bank in CLAUSES.items():
        for clause in bank:
            if "Orion" in clause:
                continue
            assert not re.search(r"\b(he|his|him)\b", clause), (
                f"{descriptor}: {clause}")


def test_a_landmark_never_repeats_a_clause():
    """Six sentences that are the same observation in six voices are one
    hint, not six."""
    seen: dict[str, set] = {}
    for r in hints.load():
        bank = CLAUSES[r["descriptor"]]
        clause = next(c for c in bank if c in r["sentence"]
                      or c[0].upper() + c[1:] in r["sentence"])
        assert clause not in seen.setdefault(r["landmark"], set()), r
        seen[r["landmark"]].add(clause)
