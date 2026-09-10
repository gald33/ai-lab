"""What has to stay true of the descriptor layer.

Four of these exist because something was already wrong and was invisible
until it was measured. They are not style checks.

    python3 -m pytest games/carmel-taldiego/test_descriptors.py -q
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import descriptors as D  # noqa: E402
import gazetteer  # noqa: E402
from landmarks import load  # noqa: E402


def test_every_landmark_has_something_to_say():
    per = D.all_descriptors()
    assert len(per) == 1000
    assert min(len(v) for v in per.values()) >= 3


def test_nothing_survives_below_the_collision_floor():
    """A descriptor true of a handful of landmarks ends the chase when she
    is forced to post it."""
    counts = Counter(d for s in D.all_descriptors().values() for d in s)
    assert [d for d, n in counts.items() if n < D.MIN_SHARED] == []


def test_the_map_plays():
    """The gate, at the committed parameters. Small trial count -- this is
    a floor against a map that cannot be run at all, not a re-measurement;
    `descriptors.py --sweep` is where the numbers get read."""
    gaz = {k: sorted(v) for k, v in D.all_descriptors().items()}
    places = list(gaz)
    ranked = {p: [x for _, x in sorted((-gazetteer.kinship(p, x, gaz), x)
                                       for x in places if x != p)]
              for p in places}
    pinned, posted = D._measure(gaz, ranked, D.NEIGHBOURHOOD, trials=1)
    assert pinned <= gazetteer.MAX_PINNED, f"pins {pinned:.1%} of her moves"
    # And the other side, which has no constant because it had never been
    # SUPERSEDED IN PLAY, 2026-09-09 ("we have no routes"): there are no
    # exits, so this measures a band that is not in the game. It is kept
    # as an indirect guard on MIN_SHARED and CANDIDATES -- a vocabulary
    # that fails it here is one whose descriptors have gone too coarse --
    # and the live claim about candidate-set size is now
    # test_carmel.test_a_hint_leaves_the_reader_a_hundred_places_not_five.
    # measured: a hint that leaves every exit standing has said nothing.
    assert posted <= 4.0, f"her hint leaves {posted:.2f} of 5 exits standing"


def test_elevation_is_metres_not_feet():
    """Wikidata's `wdt:P2044` serves the raw number and throws the unit
    away, so Area 51's 4463 feet arrived as 4463 metres and a desert
    airbase read as thinner air than Lhasa. `build_facts.py` asks for the
    SI-normalised value; this is the assertion that says so."""
    facts = D.facts()
    by_name = {p["name"]: facts[p["qid"]] for p in load()}
    assert 8000 < by_name["Mount Everest"]["elev"] < 9000
    assert by_name["Area 51"]["elev"] < 2000
    assert by_name["Dead Sea"]["elev"] < 0


def test_no_descriptor_is_derived_from_currency_language_or_time_zone():
    """The reintroduction is the easy mistake, so it is a test.

    Those four axes were the most evocative on the map and every one of
    them was false somewhere: France has not paid in francs since 2002,
    nobody speaks an Austronesian language in Nevada, and the United States
    spans fifteen time zones. They are gone deliberately -- see the long
    comment in `descriptors.py` -- and the columns stay in `facts.tsv` as
    the evidence, which is exactly what makes re-deriving them tempting.
    """
    banned = ("pays_in_", "signs_in_", "_tongue", "london", "_watch_")
    for name, words in D.all_descriptors().items():
        for word in words:
            assert not any(b in word for b in banned), f"{name}: {word}"


def test_the_descriptors_of_a_few_places_are_actually_true():
    """A fetch regression is silent otherwise: the file still parses, the
    counts still look reasonable, and the hints quietly start lying."""
    per = D.raw_descriptors()
    assert "in_europe" in per["Eiffel Tower"]
    assert "south_of_the_line" in per["Uluru"]
    assert "below_the_sea_outside" in per["Dead Sea"]
    assert "thin_air" in per["Lhasa"]
    assert "thin_air" not in per["Area 51"]
    assert "in_oceania" in per["Great Barrier Reef"]
    assert "no_coast_in_this_country" not in per["Eiffel Tower"]
