"""Run the lobby as a standing process.

    python run_lobby.py --workspace island-lobby

Polls the lobby channel forever, until interrupted. This is the whole of what
"a manager that settles it" needs to be a process rather than a class: connect
once, drain on an interval, stay up. It launches nothing -- not an entrant's
agent, not the island manager for a table it just settled -- see `lobby.py`'s
module docstring for why that boundary is deliberate.

Defaults to the managed hub, the same one `run_v3.py` and the deployed viewer
point at by default, so a lobby run without flags is already where a hosted
game would look for one.
"""

from __future__ import annotations

import argparse
import os
import time

from switchboard.client import Client
from switchboard.config import ClientConfig, MANAGED_HUB_TOKEN, MANAGED_HUB_URL

from .lobby import Lobby


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hub", default=os.environ.get("SWITCHBOARD_URL") or MANAGED_HUB_URL)
    ap.add_argument("--token", default=os.environ.get("SWITCHBOARD_TOKEN") or MANAGED_HUB_TOKEN)
    ap.add_argument("--workspace", default=os.environ.get("SWITCHBOARD_WORKSPACE", "island-lobby"))
    ap.add_argument("--key", default=os.environ.get("SWITCHBOARD_KEY"))
    ap.add_argument("--channel", default="lobby")
    ap.add_argument("--every", type=float, default=3.0, help="seconds between polls")
    args = ap.parse_args(argv)

    client = Client(ClientConfig(url=args.hub, url_source="explicit", token=args.token,
                                 workspace=args.workspace, key=args.key),
                    agent_id="lobby")
    lobby = Lobby(client=client, channel=args.channel)
    print(f"lobby on {args.hub}/{args.workspace}#{args.channel}"
         f"{' (encrypted)' if client.encrypted else ''}")
    try:
        while True:
            lobby.drain()
            time.sleep(args.every)
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
