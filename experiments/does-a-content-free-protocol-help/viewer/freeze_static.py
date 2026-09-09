"""What a GitHub Pages deploy needs in place of `serve.py`'s dynamic routes.

A static host has no process behind it to ask, so `/api/boards` and
`/api/scores` have to exist as files instead of routes. This runs the same
two computations `serve.py` runs per request -- `boards()` and
`scores.read_boards()` -- once, at publish time, and writes what they return
to disk under the exact relative paths the page already fetches. Nothing in
`web/` changes: `fetch("api/boards")` and `fetch("api/scores")` cannot tell
the difference.

    python viewer/freeze_static.py <staging-dir>/api

It also stamps a build fingerprint onto every module import in the staged copy,
so a redeploy is actually picked up by a browser holding the old one. Nothing in
the source tree is touched -- only what has been copied into the staging dir.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import serve  # noqa: E402
import scores  # noqa: E402

#: `import "./scene.js"` is the same URL after a deploy as before it, and GitHub
#: Pages serves this tree with `cache-control: max-age=600`. So somebody who had
#: the page open kept running the old modules and saw nothing change -- which
#: happened, and looked exactly like the deploy having failed.
#:
#: Every import gets the same build's hash, in every file rather than only in
#: the page: `feeds.js` imports `scene.js` too, and versioning one side only
#: would leave two URLs for one module and therefore two copies of it.
IMPORT = re.compile(r'(from\s+")(\./[\w./-]+\.js)(")')


def stamp(site: Path) -> str | None:
    """Put this build's fingerprint on every module URL under `site`."""
    files = sorted(site.glob("*.js")) + sorted(site.glob("*.html"))
    if not files:
        return None
    digest = hashlib.sha256()
    # Every module, vendored ones included: three.js is the largest thing the
    # page loads and an upgrade to it has to change the build's fingerprint,
    # or a browser holding the old one keeps it. Only the top-level files have
    # their imports rewritten -- vendored code is left as it was shipped, and
    # its own relative imports resolve inside its directory either way.
    for f in sorted(site.rglob("*.js")):
        digest.update(f.read_bytes())
    version = digest.hexdigest()[:10]
    for f in files:
        text = f.read_text()
        stamped = IMPORT.sub(rf'\1\2?v={version}\3', text)
        if stamped != text:
            f.write_text(stamped)
    return version


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else HERE / "web" / "api"
    out.mkdir(parents=True, exist_ok=True)
    (out / "boards").write_text(json.dumps({"boards": serve.boards(), "live": None}))
    (out / "scores").write_text(json.dumps(scores.read_boards(), default=list))
    # `api/` sits at the root of the staged site, so its parent is the site.
    version = stamp(out.parent)
    if version:
        print(f"stamped module imports with ?v={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
