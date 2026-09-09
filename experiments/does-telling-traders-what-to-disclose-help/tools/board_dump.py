"""Read each workspace's keyed store. The manipulation check for run 002.

A key either exists or it does not, which is why this run puts disclosure on a
board rather than in prose: run 001's check had to match ratios out of free
text and found seven messages in five rounds. Here the question is answerable
without reading anyone's wording — was `cost/T1` written, once, and did
`worth/T1` change between episodes?
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from switchboard.client import Client  # noqa: E402
from switchboard.config import (  # noqa: E402
    MANAGED_HUB_TOKEN, MANAGED_HUB_URL, ClientConfig)


def dump(workspace: str) -> list[dict]:
    client = Client(ClientConfig(url=MANAGED_HUB_URL, url_source="explicit",
                                 token=MANAGED_HUB_TOKEN, workspace=workspace,
                                 agent_id="board-observer"))
    out = []
    for entry in client.board_list():
        key = entry.get("key")
        out.append({"key": key, "revision": entry.get("revision"),
                    "value": client.board_get(key)})
    return out


if __name__ == "__main__":
    stamp, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for arm in ("bare", "ratios", "ratios-board"):
        for seed in range(1, 6):
            workspace = f"island-r-{arm}-{seed}-{stamp}"
            try:
                rows = dump(workspace)
            except Exception as exc:  # noqa: BLE001
                print(f"{workspace}: FAILED {type(exc).__name__}")
                continue
            (out / f"r-{arm}-seed{seed}.json").write_text(
                json.dumps(rows, indent=1, default=str))
            keys = sorted(r["key"] for r in rows)
            print(f"r-{arm} seed {seed}: {len(rows)} keys  {keys[:6]}")
