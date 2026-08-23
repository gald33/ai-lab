"""Serve the island page, and stand between it and the Switchboard viewer.

Two jobs, both boring on purpose:

* serve `web/` and the saved boards in `results/`, so a replay works with
  nothing running but this;
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

Nothing here writes anywhere, and no route reaches outside `web/` and
`results/`.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
WEB = HERE / "web"
RESULTS = HERE.parent / "results"

TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".json": "application/json; charset=utf-8", ".css": "text/css; charset=utf-8"}

SCORES = HERE / "scores" / "ledger.jsonl"


def boards() -> list[dict]:
    """Every saved board under `results/`, with its sidecar if one exists."""
    out = []
    for path in sorted(RESULTS.rglob("board-*.json")):
        rel = path.relative_to(RESULTS).as_posix()
        sidecar = path.with_name(path.name.replace("board-", "reveal-", 1))
        out.append({
            "label": path.stem.replace("board-", ""),
            "board": f"results/{rel}",
            "reveal": (f"results/{sidecar.relative_to(RESULTS).as_posix()}"
                       if sidecar.exists() else None),
        })
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
            payload = scores.boards(scores.load(SCORES))
            return self._send(200, TYPES[".json"],
                              json.dumps(payload, default=list).encode())
        if path == "/api/state":
            return self._proxy()
        if path.startswith("/results/"):
            # Saved boards and their sidecars only. This process can read the
            # whole checkout and has no business turning that into an HTTP
            # surface, so the route is resolved and then checked for escape.
            return self._file(self._under(RESULTS, path[len("/results/"):], ".json"))
        return self._file(self._under(WEB, path.lstrip("/"), ".js", ".html", ".css"))

    def _under(self, root: Path, rel: str, *suffixes: str) -> Path | None:
        try:
            target = (root / rel).resolve()
            target.relative_to(root.resolve())
        except (ValueError, OSError):
            return None
        return target if target.suffix in suffixes and target.is_file() else None

    def _file(self, path: Path | None) -> None:
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

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
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
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    server = Server((args.host, args.port), Handler)
    server.upstream = args.viewer or None
    server.verbose = args.verbose
    found = boards()
    print(f"island view on http://{args.host}:{args.port}")
    print(f"  {len(found)} saved board(s) under {RESULTS}")
    print(f"  live via {args.viewer}" if args.viewer else "  replays only")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
