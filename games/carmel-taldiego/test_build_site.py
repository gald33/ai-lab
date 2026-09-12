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
import html
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import build_site as BS  # noqa: E402
import carmel as C  # noqa: E402
import trail_flight as TF  # noqa: E402


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
    page = (out / BS.GALLERY / "index.html").read_text(
        encoding="utf-8")
    assert len(made) == 3
    for m in made:
        assert f'{m["dir"]}/flight.html' in page
        assert f'{m["dir"]}/card.svg' in page
        assert m["seed"] in page, "the seed is printed so it can be re-run"


def test_a_caught_campaign_is_not_quietly_relabelled(site):
    """The outcome on the page is `chase`'s own word for it."""
    out, made = site
    page = (out / BS.GALLERY / "index.html").read_text(
        encoding="utf-8")
    for m in made:
        assert m["outcome"] in ("she wins", "caught", "unfinished")
        assert f'>{m["outcome"]}<' in page


def test_every_relative_link_on_the_gallery_resolves(site):
    """Named for the files until 2026-09-12, when the gallery moved under
    `GALLERY` and this test went looking for them at the old path.

    It reads the page's own `src` and `href` instead of the layout the
    builder happens to use today: a link on a published page either
    resolves or it is a broken link, whatever directory it is written from.
    """
    out, made = site
    gallery = out / BS.GALLERY / "index.html"
    page = gallery.read_text(encoding="utf-8")

    links = re.findall(r'(?:src|href)\s*=\s*"(?!https?:|data:|#)([^"]+)"',
                       page)
    assert len(links) >= 2 * len(made), links
    for link in links:
        target = (gallery.parent / link.split("#")[0]).resolve()
        assert target.exists(), f"{link} on the gallery goes nowhere"
        if target.is_file():
            assert target.stat().st_size > 2000, link


# --- what it must not disclose -------------------------------------------

def test_the_index_names_no_landmark_off_the_trails(site):
    """Same rule as the card: post-reveal, the rooms she visited may be
    named and nothing else. The index shows her last stop, so this is the
    guard that it shows only that."""
    out, made = site
    page = (out / BS.GALLERY / "index.html").read_text(
        encoding="utf-8")
    world = C.Map(bytes(32))

    walked = {C.LOBBY_LANDMARK}
    for seed_hex in (m["seed"] for m in made):
        seed = bytes.fromhex(seed_hex)
        result = C.chase(seed, C.LOBBY_LANDMARK, searchers=BS.SEARCHERS,
                         world=C.Map(seed))
        walked |= {leg["to"] for leg in result["moves"]}

    named = {name for name in world.places if name in page}
    assert named <= walked, named - walked


def test_no_page_needs_anything_from_the_network(site):
    """Every page opens from a file. No CDN, no font host, no analytics --
    the only absolute links are to GitHub, which are links a reader clicks
    rather than resources the page loads.

    It asked about one page until 2026-09-12, and that page stopped being
    the one a player is sent to on the same day. So it walks the tree: a
    page the build adds is covered by existing, not by being added here.
    """
    out, _ = site
    pages = sorted(out.rglob("*.html"))
    assert len(pages) >= 4, f"the build stopped writing pages: {pages}"
    for page in pages:
        text = page.read_text(encoding="utf-8")
        loaded = re.findall(r'(?:src|href)\s*=\s*"(https?://[^"]+)"', text)
        assert all(u.startswith("https://github.com/") for u in loaded), (
            page.relative_to(out), loaded)

    # The gallery carries no script at all. The front door and the film do
    # -- a copy button and the flight -- and both are local.
    gallery = (out / BS.GALLERY / "index.html").read_text(encoding="utf-8")
    assert "<script" not in gallery.lower()


def test_the_link_points_at_where_the_site_actually_puts_the_viewer(tmp_path):
    """`trail_flight.CHASE_PAGE` is what every chase link she posts points
    at, and this is what writes the page it points at. Two places, one
    fact -- so it is derived from the tree rather than agreed by hand, per
    `CLAUDE.md`'s rule about inventories that drift.
    """
    import trail_flight as TF

    BS.build(tmp_path, imagery=None, count=1)

    # The tail is what is left of the address after the site's own URL --
    # not its last segment, which was the same thing only while the page
    # sat one directory down, and which would read "carmel-taldiego" now.
    assert TF.CHASE_PAGE.startswith(BS.SITE_URL), (
        "the address a chase link carries is not under the published site")
    tail = TF.CHASE_PAGE[len(BS.SITE_URL):].strip("/")
    assert tail == BS.viewer_path()

    here = tmp_path / tail
    published = here / "index.html"
    assert published.exists(), f"nothing published at {tail or 'the base URL'}"
    assert (here / "basemap.js").exists()
    assert "BASEMAP" in (here / "basemap.js").read_text()
    assert 'src="basemap.js"' in published.read_text()
    assert 'id="data"></script>' in published.read_text(), (
        "a chase was baked into the page every link opens")

    # and the page at that address is the front door, which is the defect
    # this test did not catch: it was green on a tree whose base URL was
    # the gallery, because it only ever asked about `chase/`.
    assert 'id="take"' in published.read_text(), (
        "the address a player is given does not carry the copy button")


def test_the_front_door_says_everything_a_stranger_needs():
    """Gal, 2026-09-12: *"the base url for the page is the landing page for
    the game, giving the user the agent prompt."*

    This game has published instructions that did not work twice -- a recipe
    one step short of an address, and a notice that never said announcing
    yourself is what makes you visible -- and both survived 140 tests
    because, in the record's words, *sentences are not executed*. So the
    page is held to the strings the code computes rather than to strings
    somebody typed next to them.
    """
    import at_large as L
    import trail_flight as TF
    from secret_matrix import ADDRESS_RECIPE, RECIPE

    # What the *reader* sees: the recipe is full of quotes, so the markup
    # carries `&quot;` where the page shows `"`. Asserting on the source
    # would be asserting on the escaping.
    front = html.unescape(BS.landing())

    # the three publishable things, as the runtime computes them today
    assert L.HUB_URL in front
    assert L.lobby_token() in front
    assert L.LOBBY_KEY in front

    # both steps of the recipe, because stopping at the first one is the
    # defect this game already shipped once
    assert RECIPE in front and ADDRESS_RECIPE in front

    # and the one way to play perfectly and still lose
    words = " ".join(front.split()).lower()
    assert "register" in words and "roster" in words
    assert "lapses" in words, "nothing says presence has to be renewed"

    # The prompt is a block to hand over, not a description of one -- and
    # it is found by the id the copy button binds to, so this and the button
    # cannot end up talking about different blocks.
    prompt = front.split('<pre id="ask">')[1].split("</pre>")[0]
    assert L.lobby_token() in prompt and L.HUB_URL in prompt
    assert "hue and cry" in prompt.lower()

    # and the page it lands on is the one that shows it
    assert TF.viewer(BS.landing()).count(BS.landing()) == 1


def test_the_front_door_is_only_the_front_door(tmp_path):
    """It is published bare, with no chase in it: the same URL carries a
    campaign only when somebody sends you one in a fragment."""
    BS.build(tmp_path, imagery=None, count=1)
    page = (tmp_path / BS.viewer_path() / "index.html").read_text()
    assert "Hand this to your agent" in page
    assert 'id="data"></script>' in page, "a chase was baked into the door"


def test_the_front_door_names_the_game():
    """Gal, 2026-09-12: *"we didn't write carmel taldiego anywhere."*

    The game was renamed to hers on 2026-09-10 -- *"a picture of this game
    is a picture of Carmel Taldiego"* -- with two deliberate exceptions,
    the wire and a roadmap id, both identifiers rather than names. A landing
    page that called it by the old name was the rename missing the one
    surface a stranger reads first.

    `hue and cry` still belongs on the page and this does not forbid it:
    it is the phrase for the chase, and the searchers are still the Hue.
    What is checked is that the game is named.
    """
    import html as htmlmod

    front = htmlmod.unescape(BS.landing())
    assert "Carmel Taldiego" in front.split("<h1>")[1].split("</h1>")[0], (
        "the front door is titled something other than the game")
    prompt = front.split('<pre id="ask">')[1].split("</pre>")[0]
    assert "Carmel Taldiego" in prompt, (
        "an agent is asked to play a game nobody named")


def test_the_prompt_tells_an_agent_to_announce_itself_in_her_room():
    """Gal, 2026-09-12: *"the agent actually has to announce himself so she
    sees him, I hope that's in the prompt."*

    It is the one way to play perfectly and still lose, and the version
    before this said it only of the lobby -- an agent that followed the
    prompt exactly would solve the riddle, walk into her room, wait in
    silence and be invisible. Asserted on the instruction the agent is
    handed rather than on the rules it quotes, because the first paragraph
    is what a model acts on.
    """
    import html as htmlmod

    prompt = htmlmod.unescape(BS.landing()).split('<pre id="ask">')[1]
    ask = " ".join(prompt.split("</pre>")[0].split()).lower()
    head = ask.split("hue and cry --")[0]   # its own words, before the rules
    assert "every room" in head and "register" in head, (
        "the prompt scopes registering to the lobby it starts in")
    assert "reading a room is not being in it" in head


def test_the_page_does_not_describe_a_game_that_was_replaced(tmp_path):
    """The public page's blurb is hand-written prose, so it drifts from the
    code silently — and it had, for a day, on a page anybody could read.

    Found by being asked for the game's link. CI had rebuilt the page
    minutes earlier, so it was *current*, and it still said she posts
    **"one true thing ... the least informative true thing she can say"**
    and that she is **"only catchable while she is standing still stealing
    something"**. All three claims were true when written and all three had
    been superseded: the riddle replaced one fact with three details, the
    least-informative strategy was reversed, and Gal's *"she could be caught
    whenever she is in the room with a player, nevermind her state"* ended
    the standing-still rule.

    **A rebuilt page is not a current page.** The build was derived and the
    words were not, which is this repo's recurring shape — an inventory that
    drifts while the mechanism around it stays right.

    So the retired phrases are pinned. Not the whole blurb, which should
    stay editable prose, but the specific claims that are now false: a page
    that reintroduces any of them fails here rather than going live.
    """
    made = BS.build(tmp_path, imagery=None, count=1)

    retired = [
        "one true thing",
        "least informative",
        "only catchable while she is standing still",
    ]

    # Every page the build writes, found by walking the tree rather than
    # by naming the two that exist today. `landing()` arrived in the same
    # afternoon as this test and is now the front door -- the phrase list
    # is already an inventory, and a *page* list would be a second one
    # (`CLAUDE.md`, "derive the list rather than maintaining it").
    pages = sorted(tmp_path.rglob("*.html"))
    assert len(pages) >= 3, f"the build stopped writing pages: {pages}"
    for page in pages:
        text = page.read_text()
        for phrase in retired:
            assert phrase not in text, (
                f"{page.relative_to(tmp_path)} says {phrase!r}, which"
                " describes the game as it was before the riddle and"
                " before co-presence became the catch")

    # And the replacement is present, so this cannot pass by the blurb
    # having been deleted instead of corrected.
    assert "few true" in BS.index(made, imagery=None), (
        "the blurb no longer describes the riddle")


def test_the_address_a_player_is_given_is_the_front_door(tmp_path):
    """Gal, 2026-09-12: *"This is not the page we designed with the button
    to copy."*

    `landing()` shipped the same afternoon with a docstring quoting the
    decision it was built for — *"the base url for the page is the landing
    page for the game"* — and `build()` published it at `chase/` while the
    base URL kept the campaign gallery. Every test around it was green:
    the door said the right things, the button worked in a real browser,
    the recipe was complete. **Nothing asked where it was**, so the one
    address a stranger is handed showed them six recordings and no way to
    play.

    A skip and an absence are the two shapes `CLAUDE.md` warns about, and
    this is the second: no check named the base URL, so nothing failed.
    """
    BS.build(tmp_path, imagery=None, count=1)

    base = tmp_path / "index.html"
    assert base.exists(), "nothing at all is published at the base URL"
    front = base.read_text(encoding="utf-8")

    assert 'id="take"' in front, "the base URL has no copy button"
    assert 'id="ask"' in front, "the base URL does not carry the prompt"
    assert "Hand this to your agent" in front

    # and it is the address she posts, so the link and the door are one page
    assert TF.CHASE_PAGE == BS.SITE_URL
    assert BS.viewer_path() == ""


def test_a_link_already_handed_out_still_opens_its_chase(tmp_path):
    """The door moved, and a chase she has already posted is somebody's
    copy of a game they won. Every retired address keeps a forwarder.

    **It has to carry the fragment**, which is why the forwarder is script
    and not a `<meta refresh>`: the whole chase is after the `#`
    (`trail_flight.link`), so a redirect that drops it opens an empty film
    — which looks like a bug in the drawing rather than a moved page.
    """
    BS.build(tmp_path, imagery=None, count=1)

    for old in BS.RETIRED_DOORS:
        page = (tmp_path / old / "index.html")
        assert page.exists(), f"{old}/ was retired without a forwarder"
        text = page.read_text(encoding="utf-8")
        assert "location.hash" in text, (
            f"{old}/ forwards without the chase, so the film opens empty")
        assert "location.replace" in text
        # it points at the door, and the door is where the door is
        to = text.split("location.replace(")[1].split(" +")[0].strip("'\"")
        assert (tmp_path / old / to).resolve() == (
            tmp_path / BS.viewer_path()).resolve()
        # and a reader with no script gets a link rather than a blank page
        assert f'href="{to}"' in text
