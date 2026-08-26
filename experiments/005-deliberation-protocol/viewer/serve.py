"""Serve the island page, and stand between it and the Switchboard viewer.

Two jobs, both boring on purpose:

* serve `web/` and the saved boards under each of `ROOTS`, so a replay works
  with nothing running but this;
* forward `api/state` to a local `switchboard-viewer`, so the live page reads
  the viewer rather than the hub.

That forwarding is the whole architecture. The viewer holds the token, the key
and the read cursors, and it is the component that has already been argued
about -- reading through it means this page cannot advance an agent's cursor,
cannot post, and never sees a key. It also sidesteps the browser: `api/state`
sends no CORS headers, so a page on another origin cannot read it at all, and
one served from here is on the same origin by construction.

    switchboard-viewer                       # in the checkout that coordinates
    python viewer/serve.py                   # -> http://127.0.0.1:8790

Nothing here writes anywhere, and no route reaches outside `web/` and the
directories named in `ROOTS`.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
WEB = HERE / "web"

#: URL prefix -> the directory it serves saved boards from. More than one,
#: because a replay worth keeping is not always this experiment's: a game
#: played in `games/` writes its board somewhere else entirely, and the page
#: that knows how to play a board back should not care which tree it came
#: from. A root that does not exist is skipped rather than refused -- a
#: checkout with no published replays serves exactly what it did before.
ROOTS = {
    "results": HERE.parent / "results",
    "replays": HERE.parents[2] / "games" / "replays",
    # 007's rounds, exported into this shape by its own
    # `tools/export_replays.py`. A separate prefix rather than a second tree
    # under `results`, because the label a page shows has to say which
    # experiment a round came from: 007 replicated one cell four times, so an
    # arm and a seed alone name four different rounds.
    "ceiling": HERE.parents[1] / "007-execution-ceiling" / "replays",
}

TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".json": "application/json; charset=utf-8", ".css": "text/css; charset=utf-8"}

SCORES = HERE / "scores" / "ledger.jsonl"


#: Walking the results tree costs a stat per file, and the listing changes only
#: when a round is saved -- so it is walked at most this often rather than once
#: per page load. Short enough that a board saved during a run still turns up.
LISTING_TTL = 5.0
_listing: tuple[float, list[dict]] = (0.0, [])


def facets(sidecar: Path) -> dict:
    """What a round *was*, for filtering by, read from its reveal sidecar.

    A listing of 157 boards is not searched by name -- nobody remembers which
    seed was the interesting one -- it is searched by what happened: which
    condition, how many traders, did anyone end up better off than alone, was
    anybody ruined. All of that is already recorded; it was simply never
    carried in the listing.

    Everything here is read, never recomputed. `score` is the manager's, and
    `welfare` is the one derived number: the round's utility against the sum
    of its traders' solo optima, episode by episode, which is the reading
    `reports/2026-08-24-a-second-benchmark.md` argues for. A sidecar that
    predates any of these fields yields the keys it can and omits the rest --
    a board with no facets still lists, it just does not answer a filter.
    """
    try:
        doc = json.loads(sidecar.read_text())
    except (OSError, ValueError):
        return {}

    out = {}
    for key in ("seed", "agents"):
        if isinstance(doc.get(key), int):
            out[key] = doc[key]
    if isinstance(doc.get("goods"), list):
        out["goods"] = len(doc["goods"])

    rnd = doc.get("round") or {}
    if rnd.get("arm"):
        out["arm"] = rnd["arm"]
    if isinstance(rnd.get("episodes"), int):
        out["episodes"] = rnd["episodes"]

    score = rnd.get("score") or {}
    for key in ("eff_round", "gain_median", "below_autarky",
                "zero_agent_episodes", "agent_episodes"):
        if isinstance(score.get(key), (int, float)):
            out[key] = score[key]

    # Welfare needs the trajectory and the solo optima together, and both are
    # in this file. Mean over episodes rather than the last one: an episode is
    # a day and the round is all of them, which is how every table in the
    # reports reads it.
    solo = sum((doc.get("autarky_utility") or {}).values())
    steps = [row for row in (rnd.get("trajectory") or []) if isinstance(row, list)]
    if solo and steps:
        out["welfare"] = round(sum(sum(row) for row in steps) / (solo * len(steps)), 4)
    return out


def boards() -> list[dict]:
    """Every saved board under any of `ROOTS`, with its sidecar if one exists.

    Newest first, because with many rounds kept the interesting one is the one
    that just finished, and a dropdown sorted by filename buries it. Each
    entry's `board` and `reveal` are paths under the root's URL prefix, which
    is what makes the tree a board came from invisible to the page.
    """
    global _listing  # noqa: PLW0603 - one process, one cache
    now = time.monotonic()
    if _listing[1] and now - _listing[0] < LISTING_TTL:
        return _listing[1]

    out = []
    for prefix, root in ROOTS.items():
        if not root.is_dir():
            continue
        for path in root.rglob("board-*.json*"):
            if path.suffix not in (".json", ".gz"):
                continue
            rel = path.relative_to(root).as_posix()
            stem = path.name.split(".")[0]
            sidecar = path.with_name(stem.replace("board-", "reveal-", 1) + ".json")
            out.append({
                "label": stem.replace("board-", ""),
                "board": f"{prefix}/{rel}",
                "reveal": (f"{prefix}/{sidecar.relative_to(root).as_posix()}"
                           if sidecar.exists() else None),
                "at": path.stat().st_mtime,
                # Read once per listing rather than per page load: the sidecars
                # are small and the listing is already cached behind
                # `LISTING_TTL`.
                "facets": facets(sidecar) if sidecar.exists() else {},
            })
    out.sort(key=lambda b: -b["at"])
    _listing = (now, out)
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "island-view/1"
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's spelling
        path = urlsplit(self.path).path.rstrip("/") or "/"

        if path == "/":
            return self._file(WEB / "index.html")
        if path == "/api/boards":
            payload = {"boards": boards(),
                       "live": "api/state" if self.server.upstream else None}
            return self._send(200, TYPES[".json"], json.dumps(payload).encode())
        if path == "/api/scores":
            # Computed on the way out rather than stored: the ledger is the
            # record, and a leaderboard is a reading of it that must never be
            # the thing anybody edits.
            import scores  # noqa: PLC0415 - imported here so a replay-only run needs nothing
            # Read through the derived cache: recomputing the boards per request
            # is a page that gets slower every time somebody plays.
            payload = scores.read_boards(SCORES)
            return self._send(200, TYPES[".json"],
                              json.dumps(payload, default=list).encode())
        if path == "/api/state":
            return self._proxy()
        prefix = path.lstrip("/").split("/", 1)[0]
        if prefix in ROOTS and "/" in path.lstrip("/"):
            # Saved boards and their sidecars only. This process can read the
            # whole checkout and has no business turning that into an HTTP
            # surface, so the route is resolved and then checked for escape --
            # per root, so one prefix cannot reach into another's tree either.
            return self._file(self._under(ROOTS[prefix],
                                          path.lstrip("/")[len(prefix) + 1:],
                                          ".json", ".gz"))
        return self._file(self._under(WEB, path.lstrip("/"), ".js", ".html", ".css"))

    def _under(self, root: Path, rel: str, *suffixes: str) -> Path | None:
        """Resolve a request inside one directory, or refuse it.

        Existence is deliberately *not* checked here: a board asked for by its
        unpacked name may only exist packed, and `_file` is where that is
        worked out. What is checked here is escape and file type, which is what
        this is for.
        """
        try:
            target = (root / rel).resolve()
            target.relative_to(root.resolve())
        except (ValueError, OSError):
            return None
        return target if target.suffix in suffixes else None

    def _file(self, path: Path | None) -> None:
        if path is not None and not path.is_file():
            # A board that has been packed is still the board that was asked
            # for. The browser decompresses it; the page never learns.
            packed = path.with_suffix(path.suffix + ".gz")
            if packed.is_file():
                return self._send(200, TYPES.get(path.suffix, "application/json"),
                                  packed.read_bytes(), encoding="gzip")
        if path is None or not path.is_file():
            return self._send(404, "text/plain; charset=utf-8", b"not found\n")
        self._send(200, TYPES.get(path.suffix, "application/octet-stream"),
                   path.read_bytes())

    def _proxy(self) -> None:
        upstream = self.server.upstream
        if not upstream:
            return self._send(
                503, TYPES[".json"],
                json.dumps({"error": "no viewer configured; pass --viewer"}).encode())
        url = f"{upstream.rstrip('/')}/api/state{urlsplit(self.path).query and '?' + urlsplit(self.path).query}"
        try:
            with urllib.request.urlopen(url, timeout=20) as answer:  # noqa: S310
                body = answer.read()
        except (urllib.error.URLError, OSError) as exc:
            # Said out loud rather than served as an empty room: a live page
            # that goes quiet when its source dies is the one failure this
            # whole design is trying to avoid.
            return self._send(502, TYPES[".json"],
                              json.dumps({"error": f"{upstream} unreachable: {exc}"}).encode())
        self._send(200, TYPES[".json"], body)

    def _send(self, status: int, content_type: str, body: bytes,
              encoding: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if encoding:
            self.send_header("Content-Encoding", encoding)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        if getattr(self.server, "verbose", False):
            super().log_message(fmt, *args)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    upstream: str | None = None
    verbose: bool = False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--viewer", default="http://127.0.0.1:8799",
                    help="a running switchboard-viewer; '' to serve replays only")
    ap.add_argument("--results", type=Path, default=None,
                    help="which results tree to serve replays from "
                         "(default: this experiment's)")
    ap.add_argument("--replays", type=Path, default=None,
                    help="which tree of kept game replays to serve "
                         "(default: games/replays)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    # Rebound rather than threaded through every route: the roots are chosen
    # once at startup and do not change while the process runs.
    for name, chosen in (("results", args.results), ("replays", args.replays)):
        if chosen:
            ROOTS[name] = chosen.resolve()

    server = Server((args.host, args.port), Handler)
    server.upstream = args.viewer or None
    server.verbose = args.verbose
    found = boards()
    print(f"island view on http://{args.host}:{args.port}")
    for prefix, root in ROOTS.items():
        kept = sum(1 for b in found if b["board"].startswith(f"{prefix}/"))
        print(f"  {kept} saved board(s) under {root}"
              f"{'' if root.is_dir() else ' (absent)'}")
    print(f"  live via {args.viewer}" if args.viewer else "  replays only")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
