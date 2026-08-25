"""Assemble the replay player: head + body + every recording, one HTML file.

The page is published as an Artifact, where a strict CSP blocks every outbound
request, so the recordings cannot be fetched -- they are embedded. Google Fonts
is the one host that loads; every other asset must be inline.

Usage: python tools/player/build.py   (from the experiment directory)
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent.parent
RECS = EXP / "recordings"


def main() -> None:
    docs = {}
    for path in sorted(RECS.glob("*.json")):
        if path.name == "all.json":
            continue
        doc = json.load(path.open())
        docs[doc["run"]] = doc
    if not docs:
        raise SystemExit("no recordings -- run tools/make_recording.py first")

    blob = json.dumps(docs, separators=(",", ":"))
    if "</script" in blob:
        raise SystemExit("a message body would close the data script tag")
    (RECS / "all.json").write_text(blob)

    out = RECS / "island-replay.html"
    out.write_text((HERE / "head.html").read_text()
                   + (HERE / "body.html").read_text().replace("__DATA__", blob))
    takes = sum(len(d["takes"]) for d in docs.values())
    print(f"{out}  runs {len(docs)}  takes {takes}  {out.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
