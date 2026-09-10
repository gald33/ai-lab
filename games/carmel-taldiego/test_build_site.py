"""What the published pages must be, and must not become.

    python3 -m pytest games/carmel-taldiego/test_build_site.py -q

Offline: built without imagery, so nothing here touches NASA. The deploy
turns imagery on (`pages.yml`), and `test_imagery.py` is what covers that
half.

The tests that matter are not about HTML. They are about the page being an
honest sample rather than a highlight reel, and about it disclosing no more
than a card does.
"""

import hashlib
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import build_site as BS  # noqa: E402
import carmel as C  # noqa: E402


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site")
    made = BS.build(out, imagery=None, count=3)
    return out, made


# --- the sample ----------------------------------------------------------

def test_the_seeds_are_the_first_n_and_not_a_chosen_n():
    """THE ONE THAT MATTERS. Publishing the six prettiest campaigns would
    be choosing a population after seeing the results, which `CLAUDE.md`
    forbids for a measurement and which is no more honest on a page. The
    seeds are a pure function of the root and the index, so there is
    nowhere for a thumb to go on the scale."""
    for i, seed in enumerate(BS.seeds(6)):
        assert seed == hashlib.sha256(
            BS.SEED_ROOT + i.to_bytes(4, "big")).digest()


def test_every_campaign_that_ran_is_on_the_page(site):
    """No campaign is dropped for being short, dull, or a loss."""
    out, made = site
    page = (out / "index.html").read_text(encoding="utf-8")
    assert len(made) == 3
    for m in made:
        assert f'{m["dir"]}/flight.html' in page
        assert f'{m["dir"]}/card.svg' in page
        assert m["seed"] in page, "the seed is printed so it can be re-run"


def test_a_caught_campaign_is_not_quietly_relabelled(site):
    """The outcome on the page is `chase`'s own word for it."""
    out, made = site
    page = (out / "index.html").read_text(encoding="utf-8")
    for m in made:
        assert m["outcome"] in ("she wins", "caught", "unfinished")
        assert f'>{m["outcome"]}<' in page


def test_the_files_are_actually_there(site):
    out, made = site
    for m in made:
        assert (out / m["dir"] / "card.svg").stat().st_size > 2000
        assert (out / m["dir"] / "flight.html").stat().st_size > 2000


# --- what it must not disclose -------------------------------------------

def test_the_index_names_no_landmark_off_the_trails(site):
    """Same rule as the card: post-reveal, the rooms she visited may be
    named and nothing else. The index shows her last stop, so this is the
    guard that it shows only that."""
    out, made = site
    page = (out / "index.html").read_text(encoding="utf-8")
    world = C.Map(bytes(32))

    walked = {C.LOBBY_LANDMARK}
    for seed_hex in (m["seed"] for m in made):
        seed = bytes.fromhex(seed_hex)
        result = C.chase(seed, C.LOBBY_LANDMARK, searchers=BS.SEARCHERS,
                         world=C.Map(seed))
        walked |= {leg["to"] for leg in result["moves"]}

    named = {name for name in world.places if name in page}
    assert named <= walked, named - walked


def test_the_page_needs_nothing_from_the_network(site):
    """It opens from a file. No CDN, no font host, no analytics -- the only
    absolute links are to GitHub, which are links a reader clicks rather
    than resources the page loads."""
    out, _ = site
    page = (out / "index.html").read_text(encoding="utf-8")
    loaded = re.findall(r'(?:src|href)\s*=\s*"(https?://[^"]+)"', page)
    assert all(u.startswith("https://github.com/") for u in loaded), loaded
    assert "<script" not in page.lower()
