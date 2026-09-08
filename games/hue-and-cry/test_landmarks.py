"""The map's invariants, which the chase depends on and a rebuild can break.

`build_landmarks.py` talks to the network and is not run in CI; this reads
the committed file and is. What it guards is not "the data is nice" but the
four properties the game would silently misbehave without.

    python3 -m pytest games/hue-and-cry/test_landmarks.py -q
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from landmarks import load  # noqa: E402

MIN_KM = 1.0  # must match build_landmarks.MIN_KM


def haversine(a, b):
    la1, lo1, la2, lo2 = map(
        math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    return 6371 * 2 * math.asin(math.sqrt(
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


def test_there_are_a_thousand():
    assert len(load()) == 1000


def test_every_name_is_unique():
    """The landmark hashes to the room, so a repeated name is one room
    reachable by two entries in the map, and the seed cannot tell them
    apart."""
    places = load()
    assert len({p["name"] for p in places}) == len(places)


def test_no_two_landmarks_are_the_same_place():
    """Two rooms inside a kilometre are one place under two names: their
    hints are interchangeable, and travel between them is free, which is
    the one cost the chase leans on."""
    places = load()
    close = [(a["name"], b["name"], haversine(a, b))
             for i, a in enumerate(places) for b in places[i + 1:]
             if haversine(a, b) < MIN_KM]
    assert close == []


def test_coordinates_are_on_the_earth():
    for p in load():
        assert -90 <= p["lat"] <= 90, p
        assert -180 <= p["lon"] <= 180, p
        assert (p["lat"], p["lon"]) != (0.0, 0.0), p  # the null-island tell


def test_the_places_the_map_was_rebuilt_for_are_on_it():
    """Gal named four when he rejected the city-based map. If a rebuild
    drops one, the map has drifted back to being a list of coordinates."""
    names = {p["name"] for p in load()}
    for wanted in ("Eiffel Tower", "Dead Sea", "Area 51", "Stonehenge"):
        assert wanted in names


def test_every_landmark_has_a_country_to_be_reported_from():
    """A hint says where she was seen. A blank country is a sentence that
    cannot be written."""
    assert [p["name"] for p in load() if not p["country"]] == []


def test_every_landmark_has_a_wikidata_item():
    """The name is not an identifier -- "Eiffel Tower" returns four items,
    three of them in the United States. Enrichment is exact with a Q-number
    and a guess without one."""
    bad = [p["name"] for p in load()
           if not p["qid"].startswith("Q") or not p["qid"][1:].isdigit()]
    assert bad == []


def test_no_two_landmarks_are_the_same_wikidata_item():
    places = load()
    assert len({p["qid"] for p in places}) == len(places)
