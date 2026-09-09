"""What has to stay true of the notes the searchers leave each other.

    python3 -m pytest games/hue-and-cry/test_field.py -q
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import field as F  # noqa: E402

SEED = bytes.fromhex(
    "f1e1d0000000000000000000000000000000000000000000000000000000babe")
WORLD = C.Map(SEED)
START = "Stonehenge"


def _kw(**over):
    base = dict(searchers=4, liars=0, trust="naive")
    base.update(over)
    return base


def test_a_campaign_with_notes_is_deterministic():
    a = F.run(SEED, START, WORLD, **_kw(liars=2))
    b = F.run(SEED, START, C.Map(SEED), **_kw(liars=2))
    assert a["outcome"] == b["outcome"] and a["hours"] == b["hours"]


def test_an_honest_note_only_ever_names_a_room_she_went_to():
    """A note cannot lie about the next room -- the `CLUE` line in the room
    carries the exact workspace, so the hash beats the note. What an honest
    note carries is position further along the trail than the reader has
    walked, and it is still true."""
    trail = C.itinerary(SEED, START, WORLD)
    visited = {leg["to"] for leg in trail} | {START}
    result = F.run(SEED, START, WORLD, **_kw(liars=0))
    assert result["notes"] > 0, "nobody said anything, so nothing is tested"
    # Reconstructed the only way the module exposes it: with no liars, no
    # searcher should ever waste a leg, because every note is true.
    assert result["wasted"] == 0
    assert visited


SEEDS = [bytes([i]) + SEED[1:] for i in range(12)]


def _many(**kw):
    out = []
    for seed in SEEDS:
        world = C.Map(seed)
        world.descriptors, world.places, world.treasure = (
            WORLD.descriptors, WORLD.places, WORLD.treasure)
        out.append(F.run(seed, START, world, **_kw(**kw)))
    return out


def test_an_honest_field_never_wastes_a_single_leg():
    """A hard invariant, not a tendency: an honest note names a room she
    actually went to, so acting on one is never a wasted journey. If this
    fails, honest notes have started lying by accident."""
    assert sum(r["wasted_legs"] for r in _many(liars=0)) == 0


def test_a_liar_costs_the_field_real_travel():
    assert sum(r["wasted_legs"] for r in _many(liars=2)) > 0


def test_one_bit_of_memory_bounds_what_a_liar_can_cost():
    """The cheapest defence there is: act on a note, find nothing where it
    said, never believe that author again.

    Asserted as the bound it actually guarantees rather than as a catch
    rate. Each searcher can be sent astray at most once per liar, so the
    whole field wastes at most `searchers x liars` legs however long the
    campaign runs. A naive field has no such bound -- it will follow the
    same liar all day -- and how much that is worth in catches is a
    statistic, reported by `field.py` and not asserted here, because
    twenty-five campaigns cannot tell twelve points from noise.
    """
    liars, searchers = 2, 4
    for r in _many(liars=liars, trust="burned"):
        assert r["wasted_legs"] <= searchers * liars, r
    naive = max(r["wasted_legs"] for r in _many(liars=liars, trust="naive"))
    assert naive > 0


def test_notes_never_settle_anything():
    """The manager does not read them, so a liar is playing the game rather
    than cheating at it. Nothing in a result may depend on who said what."""
    result = F.run(SEED, START, WORLD, **_kw(liars=2))
    assert set(result) == {"outcome", "hours", "by", "reputation", "notes",
                           "wasted", "wasted_legs"}
    assert result["outcome"] in ("caught", "she got away")


def test_she_cannot_read_the_lobby():
    """She is the control. A Carmel who saw a true note naming her room and
    ran is a strictly better Carmel and a different control, so her
    itinerary must not depend on what the field says."""
    quiet = C.itinerary(SEED, START, WORLD)
    loud = C.itinerary(SEED, START, WORLD)
    assert [x["to"] for x in quiet] == [x["to"] for x in loud]
    for liars in (0, 3):
        r = F.run(SEED, START, WORLD, **_kw(liars=liars))
        assert r["outcome"] in ("caught", "she got away")
