"""What has to stay true of the sentences a person actually reads.

These build the table in memory from a fixed test seed. Nothing reads a
committed rendering, because there is not one and there must not be --
see the top of `hints.py`.

    python3 -m pytest games/carmel-taldiego/test_hints.py -q
"""

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import hints  # noqa: E402
from clauses import CLAUSES  # noqa: E402
from descriptors import MIN_SHARED, all_descriptors  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402

SEED = bytes.fromhex(
    "5eed0000000000000000000000000000000000000000000000000000cafef00d")
ROWS = hints.build(SEED)


def test_no_plaintext_rendering_is_tracked_by_git():
    """THE ONE THAT MATTERS, and the only test here that would have caught
    the bug it exists for.

    A committed `hints.tsv` made every unique sentence a lookup key: post a
    sentence, grep the file, name the room. Every other test in this file
    passed the whole time it was broken, because they measure the mechanism
    and the leak was beside it.
    """
    tracked = subprocess.run(
        ["git", "ls-files", "games/carmel-taldiego/"],
        capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[2]).stdout.split()
    leaks = [f for f in tracked
             if Path(f).name.startswith("hints") and not f.endswith(".enc")
             and not f.endswith(".py")]
    assert leaks == [], f"the hint matrix is in the repository: {leaks}"


def test_the_rendering_changes_with_the_seed():
    """Encrypting a deterministic function of public inputs protects
    nothing: `clauses.py` and `descriptors.py` are both public and both
    stay public, so if the assignment did not depend on the seed anybody
    could re-run the builder and reproduce the table exactly."""
    other = hints.build(bytes(32))
    mine = {(a, b): c for a, b, c in ROWS}
    theirs = {(a, b): c for a, b, c in other}
    shared = set(mine) & set(theirs)
    same = sum(1 for k in shared if mine[k] == theirs[k])
    assert same < len(shared) * 0.05, (
        f"{same}/{len(shared)} sentences unchanged across seeds")


def test_no_sentence_appears_twice():
    """Gal asked for sentences unique per landmark. Asserted rather than
    hoped for -- a descriptor carried by 189 landmarks draws 189 sentences
    out of one clause bank."""
    counts = Counter(s for _, _, s in ROWS)
    assert [s for s, n in counts.items() if n > 1] == []


def test_every_candidate_descriptor_has_its_sentence():
    have = {(a, b) for a, b, _ in ROWS}
    want = {(name, d) for name, ds in all_descriptors().items() for d in ds}
    assert want - have == set()


def test_what_a_sentence_asserts_is_shared_by_many_landmarks():
    """Unique words, shared meaning. A sentence whose descriptor is true of
    one landmark ends the chase."""
    counts = Counter(d for _, d, _ in ROWS)
    assert min(counts.values()) >= MIN_SHARED


def test_no_sentence_names_a_place():
    """A hint that identifies the room is not a hint."""
    places = load_landmarks()
    banned = {n for n in ({p["name"] for p in places}
                          | {p["country"] for p in places})
              if " " in n or len(n) > 6}
    for _, _, sentence in ROWS:
        for word in banned:
            assert word not in sentence, f"{word!r} in {sentence!r}"


def test_no_clause_gives_the_witness_a_gender():
    """The frame supplies the witness -- a nun, a laundry woman, a night
    porter -- and the clause does not know which, so the clause says
    "they". Clauses used to say "he", and a nun duly reported that he had
    tracked her across Africa.

    `she` and `her` are not checked: they are Carmel, who is the one thing
    every clause may assume. Orion is exempt; he is a constellation.
    """
    for descriptor, bank in CLAUSES.items():
        for clause in bank:
            if "Orion" in clause:
                continue
            assert not re.search(r"\b(he|his|him)\b", clause), (
                f"{descriptor}: {clause}")


def test_a_landmark_never_repeats_a_clause():
    seen: dict[str, set] = {}
    for landmark, descriptor, sentence in ROWS:
        clause = next(c for c in CLAUSES[descriptor]
                      if c in sentence or c[0].upper() + c[1:] in sentence)
        assert clause not in seen.setdefault(landmark, set()), landmark
        seen[landmark].add(clause)


def test_the_backup_opens_with_its_seed_and_not_another(tmp_path):
    """The blob is a commitment, not a hiding place: sealed before play,
    opened at the reveal by anybody holding the published seed."""
    from cryptography.exceptions import InvalidTag

    path = tmp_path / "hints.enc"
    hints.write_backup(SEED, path)
    back = hints.read_backup(SEED, path)
    assert [(r["landmark"], r["descriptor"], r["sentence"]) for r in back] \
        == ROWS
    try:
        hints.read_backup(bytes(32), path)
    except InvalidTag:
        pass
    else:
        raise AssertionError("the backup opened under the wrong seed")
