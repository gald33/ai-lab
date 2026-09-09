"""Snapshot every workspace's roster, read-only, while a run is in flight.

Agents set a `task` string with `checkin`. It is workspace-scoped and every
other agent in the workspace can read it, so it is an information channel that
never touches the channel the manager settles from -- and every `talk 0` this
lab has reported measured the channel only.

This writes nothing to any hub and sends nothing to any agent. It reads the
roster and appends what it sees. Observation, not participation.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from switchboard.client import Client  # noqa: E402
from switchboard.config import (  # noqa: E402
    MANAGED_HUB_TOKEN, MANAGED_HUB_URL, ClientConfig)


def poll(workspaces: list[str], out: Path, seconds: float = 10.0) -> None:
    seen: set[tuple[str, str, str]] = set()
    clients = {w: Client(ClientConfig(url=MANAGED_HUB_URL, url_source="explicit",
                                      token=MANAGED_HUB_TOKEN, workspace=w,
                                      agent_id="roster-observer"))
               for w in workspaces}
    while True:
        for workspace, client in clients.items():
            try:
                agents = client.agents()
            except Exception:  # noqa: BLE001 -- a blip must not end the watch
                continue
            for agent in agents:
                task = str(agent.get("task") or "")
                key = (workspace, str(agent.get("agent_id")), task)
                if not task or key in seen:
                    continue
                seen.add(key)
                with (out / f"{workspace}.jsonl").open("a") as fh:
                    fh.write(json.dumps({"t": time.time(),
                                         "agent": agent.get("agent_id"),
                                         "task": task}) + "\n")
        time.sleep(seconds)


if __name__ == "__main__":
    stamp = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    poll([f"island-r-{arm}-{seed}-{stamp}"
          for arm in ("bare", "placebo", "ratios")
          for seed in range(1, 6)], out)
