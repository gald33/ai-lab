"""What a GitHub Pages deploy needs in place of `serve.py`'s dynamic routes.

A static host has no process behind it to ask, so `/api/boards` and
`/api/scores` have to exist as files instead of routes. This runs the same
two computations `serve.py` runs per request -- `boards()` and
`scores.read_boards()` -- once, at publish time, and writes what they return
to disk under the exact relative paths the page already fetches. Nothing in
`web/` changes: `fetch("api/boards")` and `fetch("api/scores")` cannot tell
the difference.

    python viewer/freeze_static.py <staging-dir>/api
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import serve  # noqa: E402
import scores  # noqa: E402


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else HERE / "web" / "api"
    out.mkdir(parents=True, exist_ok=True)
    (out / "boards").write_text(json.dumps({"boards": serve.boards(), "live": None}))
    (out / "scores").write_text(json.dumps(scores.read_boards(), default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
