"""What has to stay true of what she takes.

These run without the treasure key, which is the point: `build()` returns a
complete table with placeholders where the hand-written eighty would be, so
the invariants and the balance finding are checked in CI while the mapping
stays sealed. See `WHY THIS IS SEALED` in `treasures.py`.

    python3 -m pytest games/carmel-taldiego/test_treasures.py -q
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import treasures as T  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402

REPO = Path(__file__).resolve().parents[2]

#: A stand-in for the sealed eighty, so the absurd-treasure rules can be
#: tested without the key: real landmark names, no real prose. Taken from
#: the top of the fame ranking so the reputation assertions have something
#: to bite on.
FAKE_ABSURD = {p["name"]: "a placeholder"
               for p in sorted(load_landmarks(),
                               key=lambda p: -p["sitelinks"])[:80]}


def test_no_plaintext_treasure_mapping_is_tracked_by_git():
    """The one that matters. A committed `treasures.tsv` names the room for
    any public line naming what was taken, and the hand-written eighty were
    worse than the data file -- they were a dict in the source, keyed by
    landmark."""
    tracked = subprocess.run(
        ["git", "ls-files", "games/carmel-taldiego/"],
        capture_output=True, text=True, cwd=REPO).stdout.split()
    leaks = [f for f in tracked
             if Path(f).name in ("treasures.tsv", "absurd.tsv")]
    assert leaks == [], f"the treasure mapping is in the repository: {leaks}"


def test_no_source_file_maps_a_landmark_to_a_treasure():
    """`ABSURD` used to live in `treasures.py` as a dict keyed by landmark.
    If it comes back, the seal is decorative.

    Structural rather than a list of forbidden phrases, because a test that
    names the secrets it is protecting is itself the leak -- the first
    version of this test quoted three of them, and the design document had
    a table of five.
    """
    import ast

    names = {p["name"] for p in load_landmarks()}
    for path in sorted(Path(__file__).parent.glob("*.py")):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = {k.value for k in node.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)}
            landmarks = keys & names
            # A handful is the correction tables in build_landmarks.py, which
            # are about coordinates and countries and are meant to be read.
            values = [v for v in node.values
                      if isinstance(v, ast.Constant)
                      and isinstance(v.value, str) and len(v.value) > 30]
            assert not (len(landmarks) > 5 and values), (
                f"{path.name} maps {len(landmarks)} landmarks to prose")


def test_every_landmark_has_exactly_one_treasure():
    rows = T.build(FAKE_ABSURD)
    names = [p["name"] for p in load_landmarks()]
    assert sorted(r["landmark"] for r in rows) == sorted(names)


def test_a_checkout_without_the_key_still_builds_a_whole_table():
    """The cost of sealing, asserted so it stays only this much: no key
    means placeholders, not a crash and not a short table."""
    rows = T.build({})
    assert len(rows) == 1000
    assert sum(r["absurd"] for r in rows) == 0
    assert all(r["treasure"] for r in rows)


def test_standing_still_costs_more_where_the_prize_is_bigger():
    """The theft is a dwell and the dwell is the whole risk."""
    rows = T.build(FAKE_ABSURD)
    cheap = [r["dwell"] for r in rows if r["reputation"] < 25]
    dear = [r["dwell"] for r in rows if r["reputation"] > 75]
    assert min(r["dwell"] for r in rows) >= 1
    assert sum(dear) / len(dear) > sum(cheap) / len(cheap) * 3


def test_the_impossible_ones_are_worth_more_than_the_rest():
    rows = T.build(FAKE_ABSURD)
    absurd = [r["reputation"] for r in rows if r["absurd"]]
    rest = sorted(r["reputation"] for r in rows if not r["absurd"])
    assert min(absurd) > rest[len(rest) // 2], (
        "an impossible theft is a big score wherever it happens")


def test_the_richest_rooms_are_the_most_exposed():
    """The tension the game needs, and it comes out of real geography
    rather than a balance pass: fame runs against cover, so the rooms worth
    the most are the ones where her hint hides her least. It holds without
    the hand-written eighty, which is why it can be checked here at all."""
    rows = T.build({})
    cover = T.cover()
    r = T.correlation([x["landmark"] for x in rows] and
                      [cover[x["landmark"]] for x in rows],
                      [x["reputation"] for x in rows])
    assert r < -0.15, f"correlation(cover, reputation) = {r:+.3f}"


def test_the_seal_opens_with_its_key_and_not_another(tmp_path):
    from cryptography.exceptions import InvalidTag

    key = "11" * 32
    other = "22" * 32
    rows = T.build(FAKE_ABSURD)
    path = tmp_path / "treasures.enc"

    import os
    os.environ[T.KEY_ENV] = key
    T.seal(rows, path)
    assert T.unseal(path) == rows
    os.environ[T.KEY_ENV] = other
    try:
        T.unseal(path)
    except InvalidTag:
        pass
    else:
        raise AssertionError("the seal opened under the wrong key")
    finally:
        os.environ.pop(T.KEY_ENV, None)
