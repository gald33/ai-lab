"""Run the lobby as a standing process.

    python -m games.island.run_lobby --workspace island-lobby

Polls the lobby channel forever, until interrupted. This is the whole of what
the lobby needs to be a process rather than a class: connect once, hold the
channel, drain on an interval, stay up, and keep its state in a file so a
restart picks up its own tables rather than settling them a second time.

**Run this or `run_game.py` against a workspace, never both.** Both drain the
same board, and two lobbies settle every table twice -- two seeds, two room
keys, two invites, and a game that plays to nobody. Starting one now says so
on the board and the older one stands down (`lobby.HOLD`), but the table
whichever of them was mid-settlement is still better not risked. It launches nothing -- not an entrant's agent, not the
island manager for a table it just settled -- see `lobby.py`'s module
docstring for why that boundary is deliberate.

Defaults to the managed hub, the same one `run_v3.py` and the deployed viewer
point at by default, so a lobby run without flags is already where a hosted
game would look for one.

A settled table's seed is never posted to the board -- see `lobby.py`'s
`Table.seed` docstring for why -- so this prints it here instead, to this
process's own stdout, the moment a table settles. That is the whole of how
the seed reaches anybody right now: whoever is running this, reading its own
log, and about to go start the round by hand. Carrying it to a seat over the
board instead is build-order item 2c, unbuilt.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from switchboard.client import Client
from switchboard.config import ClientConfig, MANAGED_HUB_TOKEN, MANAGED_HUB_URL

from .lobby import Held, Lobby


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hub", default=os.environ.get("SWITCHBOARD_URL") or MANAGED_HUB_URL)
    ap.add_argument("--token", default=os.environ.get("SWITCHBOARD_TOKEN") or MANAGED_HUB_TOKEN)
    ap.add_argument("--workspace", default=os.environ.get("SWITCHBOARD_WORKSPACE", "island-lobby"))
    ap.add_argument("--key", default=os.environ.get("SWITCHBOARD_KEY"))
    ap.add_argument("--channel", default="lobby")
    ap.add_argument("--every", type=float, default=3.0, help="seconds between polls")
    ap.add_argument("--state", type=Path, default=None,
                    help="where this lobby keeps what the board does not "
                         "carry -- the seeds it drew and the lines it has "
                         "already acted on -- so a restart does not settle a "
                         "table twice (default: games/results/lobby-<ws>-<ch>.json)")
    args = ap.parse_args(argv)

    client = Client(ClientConfig(url=args.hub, url_source="explicit", token=args.token,
                                 workspace=args.workspace, key=args.key),
                    agent_id="lobby")
    state = args.state or Path("games/results") / f"lobby-{args.workspace}-{args.channel}.json"
    lobby = Lobby(client=client, channel=args.channel, state_path=state)
    try:
        lobby.lock()
    except Held as exc:
        print(exc)
        return 1
    lobby.load()
    lobby.hold()
    print(f"lobby on {args.hub}/{args.workspace}#{args.channel}"
         f"{' (encrypted)' if client.encrypted else ''}, "
         f"holding as {lobby.holder}, state in {state}")
    reported: set[str] = set()
    try:
        while True:
            lobby.drain()
            if lobby.stood_down:
                print("another lobby holds this channel; stopping")
                return 0
            for table in lobby.tables.values():
                if table.settled and table.id not in reported:
                    reported.add(table.id)
                    print(f"{table.id} settled: seed={table.seed} "
                         f"workspace={table.workspace} managed by {table.manager}")
            time.sleep(args.every)
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
