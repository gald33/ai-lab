"""What has to stay true of what she takes.

    python3 -m pytest games/hue-and-cry/test_treasures.py -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import treasures as T  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402


def test_the_committed_file_is_what_the_builder_makes():
    built = [(r["landmark"], r["treasure"], r["reputation"], r["dwell"],
              r["absurd"]) for r in T.build()]
    stored = [(r["landmark"], r["treasure"], r["reputation"], r["dwell"],
               r["absurd"]) for r in T.load()]
    assert built == stored, "run: python3 games/hue-and-cry/treasures.py --build"


def test_every_landmark_has_exactly_one_treasure():
    rows = T.load()
    names = [p["name"] for p in load_landmarks()]
    assert sorted(r["landmark"] for r in rows) == sorted(names)


def test_every_hand_written_treasure_reaches_a_real_landmark():
    """The one that earns its keep. `ABSURD` is keyed by landmark name, and
    a rebuild of `landmarks.tsv` can rename or drop a row -- at which point
    the hand-authored line silently stops being used and nothing else in
    the repository notices. Seventy-nine of these are the only writing in
    the game that is about a specific place."""
    names = {p["name"] for p in load_landmarks()}
    assert sorted(set(T.ABSURD) - names) == []


def test_standing_still_costs_more_where_the_prize_is_bigger():
    """The theft is a dwell and the dwell is the whole risk. A cheap
    treasure that took as long as an expensive one would make the choice
    free."""
    rows = T.load()
    cheap = [r["dwell"] for r in rows if r["reputation"] < 25]
    dear = [r["dwell"] for r in rows if r["reputation"] > 75]
    assert min(r["dwell"] for r in rows) >= 1
    assert sum(dear) / len(dear) > sum(cheap) / len(cheap) * 3


def test_the_impossible_ones_are_worth_more_than_the_rest():
    rows = T.load()
    absurd = [r["reputation"] for r in rows if r["absurd"]]
    rest = [r["reputation"] for r in rows if not r["absurd"]]
    assert min(absurd) > sorted(rest)[len(rest) // 2], (
        "an impossible theft is a big score wherever it happens")


def test_the_richest_rooms_are_the_most_exposed():
    """The tension the game needs, and it comes out of real geography
    rather than out of a balance pass: fame runs against cover, so the
    rooms worth the most are the ones where her hint hides her least. If a
    future change to the descriptors flips this sign, the theft stops being
    a gamble and the whole trade collapses."""
    rows = T.load()
    cover = T.cover()
    r = T.correlation([cover[x["landmark"]] for x in rows],
                      [x["reputation"] for x in rows])
    assert r < -0.15, f"correlation(cover, reputation) = {r:+.3f}"
