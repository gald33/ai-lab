"""What the photograph must and must not do.

    python3 -m pytest games/carmel-taldiego/test_imagery.py -q

Nothing here touches the network, and that is **enforced rather than
intended**. `no_network` below replaces `urllib.request.urlopen` for every
test in the file, so a test that forgets to pass an opener fails saying so
instead of quietly fetching fifteen tiles from NASA.

IT WAS WRITTEN BECAUSE ONE ALREADY HAD.
`test_a_card_on_imagery_names_no_landmark_but_the_trail` called
`trail_card.card(..., imagery="relief")`, which takes no opener, so it went
to NASA for real -- and passed in CI only because the runner had a network.
A green tick that also silently asserted "NASA is up" is `CLAUDE.md`'s
disease exactly: the check was named after disclosure and was measuring
something else as well. Blocking the network turned it red in 0.9s.

Every test below was made to fail on purpose: the disclosure one by adding
GIBS's `Reference_Labels_15m` to `LAYERS`, the loudness one by returning
the vector basemap when no tile arrives, and the byte-fidelity one by
re-encoding a tile on the way through.
"""

import base64
import re
import sys
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import imagery as IM  # noqa: E402
import trail_card as TC  # noqa: E402

SEED = bytes.fromhex("a3" * 32)

#: Not a real JPEG. Nothing in `imagery.py` decodes a tile -- it base64s the
#: bytes and lets the renderer read them -- so a decodable one would only be
#: testing Pillow, which this repo deliberately does not have.
TILE = b"\xff\xd8\xff\xe0-not-really-a-jpeg-" + bytes(range(64))


class Served:
    """An opener that answers every tile and remembers being asked."""

    def __init__(self, body: bytes = TILE):
        self.body, self.asked = body, []

    def __call__(self, url, timeout=None):
        self.asked.append(url)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


class Refuses(Served):
    def __call__(self, url, timeout=None):
        self.asked.append(url)
        raise OSError("no network here")


@pytest.fixture(autouse=True)
def own_cache(tmp_path, monkeypatch):
    """Never read or write the real tile cache."""
    monkeypatch.setattr(IM, "CACHE", tmp_path / "tiles")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """No test in this file may reach NASA, whatever it forgets to pass.

    `fetch` resolves `opener or urllib.request.urlopen` at call time, so
    replacing the module attribute closes the one door a test can leave
    open. This guards the class rather than the instance -- the next test
    written here will be caught by it without anybody remembering to.
    """
    def refuse(*args, **kwargs):
        raise AssertionError(
            "a test reached the network. Pass an opener, or monkeypatch "
            "imagery.fetch: the suite must not depend on NASA being up.")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)


def frame(seed: bytes = SEED):
    world = C.Map(seed)
    result = C.chase(seed, C.LOBBY_LANDMARK, searchers=2, world=world)
    stops = [C.LOBBY_LANDMARK] + [leg["to"] for leg in result["moves"]]
    points = [(world.places[n]["lat"], world.places[n]["lon"]) for n in stops]
    plot_h = TC.HEIGHT - TC.TOP - TC.BOTTOM
    return world, result, TC.fit(points, 0, TC.TOP, TC.WIDTH, plot_h)


# --- what it must not show -----------------------------------------------

def test_no_layer_carries_a_name():
    """THE WHOLE REASON IMAGERY IS ALLOWED WHERE TILES WERE NOT. GIBS serves
    `Reference_Labels_15m` and `Reference_Features_15m` alongside the
    photographs, and either one would print the names of exactly the famous
    places this game hides -- which is the objection `games/carmel-taldiego.md`
    raised against Google's tiles and that a photograph escapes.

    So the escape is asserted rather than assumed."""
    for name, (layer, *_rest) in IM.LAYERS.items():
        assert not re.search(r"label|reference|feature|place|boundar|coastline",
                             layer, re.I), (name, layer)


def test_a_card_on_imagery_names_no_landmark_but_the_trail(monkeypatch):
    monkeypatch.setattr(IM, "fetch",
                        lambda *args, **kwargs: TILE)
    world, result, _ = frame()
    svg = TC.card(result, world, SEED, C.LOBBY_LANDMARK, imagery="relief")
    walked = {C.LOBBY_LANDMARK} | {leg["to"] for leg in result["moves"]}
    import xml.etree.ElementTree as ET
    body = "\n".join((n.text or "") for n in ET.fromstring(svg).iter()
                     if n.tag.endswith("text"))
    named = {name for name in world.places if name in body}
    assert named <= walked, named - walked


# --- the tiles -----------------------------------------------------------

def test_the_zoom_is_never_asked_to_stretch():
    """Rounded up, so the imagery is at least as fine as the camera."""
    for scale in (300, 2_000, 28_478, 80_000):
        z = IM.zoom_for(scale, "relief")
        assert 256 * 2 ** z >= scale or z == IM.LAYERS["relief"][4]


def test_the_zoom_is_clamped_to_what_the_layer_serves():
    """Asking GIBS for a zoom it has not got returns 404s, and 404s here
    would read as 'no imagery available' rather than 'you asked too deep'."""
    for name, (_l, _d, _m, _e, top) in IM.LAYERS.items():
        assert IM.zoom_for(10 ** 9, name) == top


def test_the_tiles_cover_the_whole_frame():
    _, _, camera = frame()
    z = IM.zoom_for(camera.scale)
    got = set(IM.tiles_for(camera.box(), z))
    n = 2 ** z
    x0, y0, x1, y1 = camera.box()
    import math
    for ty in range(math.floor(y0 * n), math.floor(y1 * n) + 1):
        for tx in range(math.floor(x0 * n), math.floor(x1 * n) + 1):
            assert (tx, ty) in got


def test_a_tile_is_fetched_once_and_then_cached():
    served = Served()
    _, _, camera = frame()
    first = IM.background(camera, "relief", opener=served)
    asked = len(served.asked)
    assert asked == len(first) > 0
    second = IM.background(camera, "relief", opener=served)
    assert len(served.asked) == asked, "went back to the network"
    assert first == second


def test_the_tiles_are_the_bytes_nasa_served():
    """Nothing is recompressed on the way through, which is what lets a
    reader check the imagery against NASA rather than against this repo."""
    served = Served()
    _, _, camera = frame()
    for element in IM.background(camera, "relief", opener=served):
        blob = re.search(r'base64,([^"]+)"', element).group(1)
        assert base64.b64decode(blob) == TILE


def test_the_tiles_overlap_so_there_is_no_grid_of_seams():
    served = Served()
    _, _, camera = frame()
    sizes = {float(re.search(r'width="([\d.]+)"', e).group(1))
             for e in IM.background(camera, "relief", opener=served)}
    z = IM.zoom_for(camera.scale)
    assert sizes == {round(camera.scale / 2 ** z + IM.BLEED, 2)}


# --- failure is loud -----------------------------------------------------

def test_imagery_that_cannot_be_had_is_an_error_not_a_quiet_vector_card():
    """`CLAUDE.md`'s "a skip drawn as a pass", wearing a different hat: a
    card that silently drew the vector basemap instead would look fine and
    be a different picture from the one that was asked for."""
    _, _, camera = frame()
    with pytest.raises(IM.Unavailable) as caught:
        IM.background(camera, "relief", opener=Refuses())
    assert "--imagery" in str(caught.value)


def test_an_unknown_layer_says_which_ones_exist():
    _, _, camera = frame()
    with pytest.raises(IM.Unavailable) as caught:
        IM.background(camera, "sattelite", opener=Served())
    assert "relief" in str(caught.value)


def test_a_card_without_imagery_asks_for_no_tile():
    """The default path stays offline. It is what CI runs."""
    served = Refuses()
    world, result, _ = frame()
    import unittest.mock as mock
    with mock.patch.object(IM, "background",
                           side_effect=AssertionError("fetched a tile")):
        TC.card(result, world, SEED, C.LOBBY_LANDMARK)
    assert served.asked == []


# --- what changes on the card --------------------------------------------

def test_over_a_photograph_the_borders_are_drawn_and_the_coastlines_are_not():
    """A photograph has coastlines already and better ones; it has no
    borders, and `no_passport_needed_next_door` is a hint in this game."""
    _, _, camera = frame()
    over = TC.geometry(camera, over_imagery=True)
    plain = TC.geometry(camera, over_imagery=False)
    assert over and all(TC.INK["frontier"] in shape for shape in over)
    assert any(TC.INK["land"] in shape for shape in plain)
    assert not any(TC.INK["land"] in shape for shape in over)


def _deliberately_forgets_the_opener():
    """Not a test. Kept as the demonstration that `no_network` bites:
    rename it to `test_...` and it fails with the assertion above rather
    than fetching fifteen tiles."""
    _, _, camera = frame()
    return IM.background(camera, "relief")
