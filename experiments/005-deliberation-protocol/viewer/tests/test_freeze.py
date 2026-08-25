"""What the publish step does to the staged copy of the page.

    python -m pytest viewer/tests/test_freeze.py -q

`import "./scene.js"` is the same URL after a deploy as before it, and GitHub
Pages serves this tree with `cache-control: max-age=600`. So a browser that had
the page open before a deploy kept running the old modules and showed nothing
new -- which happened, and was indistinguishable from the deploy having failed.

The two properties worth holding: every module URL carries the same build's
fingerprint, **including the imports inside the modules themselves** (versioning
only the page would leave `feeds.js` importing an unversioned `scene.js`, so one
module would be fetched under two URLs and instantiated twice); and the source
tree is never touched, because publishing must not edit what it publishes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import freeze_static  # noqa: E402

WEB = HERE.parent / "web"
IMPORTS = re.compile(r'from "(\./[\w./-]+\.js)(\?v=(\w+))?"')


@pytest.fixture
def site(tmp_path):
    """A staged copy, the way `pages.yml` makes one.

    `cp -r viewer/web/. site/` copies the **tree**, and this used to copy only
    the files at the top of it -- so a module importing one in a subdirectory
    was never staged, and "every stamped URL still points at a file" could not
    have caught a broken one. It could not have been broken until `stage.js`
    started importing the vendored three.js, which is exactly when a fixture
    that lies stops being harmless.
    """
    # A directory of its own, so a test that wants a twin can put one beside it.
    # With the staged site *as* `tmp_path`, a twin made inside it became part of
    # the tree the next walk hashed -- every file counted twice, and the build
    # fingerprint stopped being a function of the build.
    root = tmp_path / "site"
    for f in WEB.rglob("*"):
        if f.is_file():
            out = root / f.relative_to(WEB)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(f.read_bytes())
    return root


def imports(path: Path):
    return IMPORTS.findall(path.read_text())


def test_every_module_url_carries_the_build(site):
    version = freeze_static.stamp(site)
    assert version, "nothing was stamped"
    found = [m for f in site.glob("*.js") for m in imports(f)]
    found += [m for f in site.glob("*.html") for m in imports(f)]
    assert found, "no module imports were found to stamp"
    for target, _, got in found:
        assert got == version, f"{target} was left on {got or 'no version'}"


def test_a_module_is_not_left_with_two_urls(site):
    # The failure this guards: version the page's imports but not the ones
    # inside the modules, and `scene.js` is fetched as both `scene.js` and
    # `scene.js?v=...` -- two instances of one module.
    freeze_static.stamp(site)
    for f in list(site.glob("*.js")) + list(site.glob("*.html")):
        for target, query, _ in imports(f):
            assert query, f"{f.name} imports {target} unversioned"


def test_every_stamped_url_still_points_at_a_file(site):
    freeze_static.stamp(site)
    for f in list(site.glob("*.js")) + list(site.glob("*.html")):
        for target, _, _ in imports(f):
            assert (site / target).exists(), f"{f.name} imports missing {target}"


def test_the_same_build_stamps_the_same_way(site, tmp_path):
    # Otherwise every deploy invalidates every cache, which is the opposite
    # problem and just as bad.
    files = [f for f in site.rglob("*") if f.is_file()]
    twin = tmp_path / "twin"
    twin.mkdir()
    for f in files:
        out = twin / f.relative_to(site)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(f.read_bytes())
    assert freeze_static.stamp(site) == freeze_static.stamp(twin)


def test_a_changed_module_changes_the_build(site, tmp_path):
    before = freeze_static.stamp(site)
    twin = tmp_path / "twin"
    twin.mkdir()
    for f in WEB.iterdir():
        if f.is_file():
            (twin / f.name).write_bytes(f.read_bytes())
    (twin / "scene.js").write_text((WEB / "scene.js").read_text() + "\n// moved\n")
    assert freeze_static.stamp(twin) != before


def test_publishing_does_not_edit_what_it_publishes(site):
    # `stamp` is pointed at the staged copy. If it ever reached back into the
    # checkout, a deploy would leave the working tree dirty and the next one
    # would stamp a stamp.
    original = {f.name: f.read_bytes() for f in WEB.iterdir() if f.is_file()}
    freeze_static.stamp(site)
    for name, body in original.items():
        assert (WEB / name).read_bytes() == body, f"{name} was edited in the source tree"


def test_a_directory_with_nothing_to_stamp_is_not_an_error(tmp_path):
    assert freeze_static.stamp(tmp_path) is None
