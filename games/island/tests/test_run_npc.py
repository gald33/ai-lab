"""The NPC as a process: against a real hub, on a real board.

`test_npc.py` covers what a policy decides. What is left to prove here is the
part that only a hub can show -- that an NPC's lines land on a board as posts
from a registered client, that it plays a whole episode by reading receipts it
did not write, and that the watcher counts unfilled seats off the lobby's own
board rather than out of a lobby object it is not given.
"""

from __future__ import annotations

import threading
import time

import pytest

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from games.island import npc
from games.island.lobby import Lobby
from games.island.run_npc import missing, play

WORKSPACE = "w_npc-test"


def _client(hub, agent_id, key=None, workspace=WORKSPACE):
    """Registered and on a keyed workspace, because a `JOIN` the lobby will
    not witness is a `JOIN` it refuses -- the same requirement a real entrant
    meets, and the reason `test_lobby.py` does this too."""
    client = Client(ClientConfig(url=hub, url_source="explicit",
                                 workspace=workspace, key=key),
                    agent_id=agent_id)
    client.register(name=agent_id, kind="local", branch="main", task="")
    return client


def _bodies(client, channel):
    return [m["body"] for m in sorted(client.history(channel, limit=200),
                                      key=lambda r: r.get("seq", 0))
            if isinstance(m.get("body"), str)]


def test_a_seat_plays_an_episode_off_the_board_and_stops_at_the_bell(hub):
    """One NPC, one manager-shaped voice, one episode. The NPC is told nothing
    that is not on the board and calls nothing that is not `post`."""
    seat = _client(hub, "npc-1")
    manager = _client(hub, "manager")
    schedule = npc.PolicySchedule(mix={"greedy": 1.0}, seed=1,
                                  mean_seconds=1000.0)

    done: list[npc.Board] = []
    thread = threading.Thread(
        target=lambda: done.append(
            play(seat, "island", name="npc-1", schedule=schedule, every=0.1,
                 deadline=time.time() + 20, log=lambda *a, **k: None)),
        daemon=True)
    thread.start()

    manager.post("island", "Schedule for this round. 2 traders: T1, T2. "
                           "8 episodes, 60s each. Acknowledge with a line "
                           "beginning ACK, by 12:00:00Z.")
    manager.post("island", "@T2 (npc-1) You are T2. Your production capacity "
                           "per unit of labour: {'bread': 0.9, 'iron': 0.2}. "
                           "Your taste weights: {'bread': 0.3, 'iron': 0.7}. "
                           "Nobody else knows either.")
    manager.post("island", "episode 1 of 1 is open; the bell is at 12:01:00Z "
                           "(60s).")

    produced = None
    for _ in range(200):
        for body in _bodies(manager, "island"):
            if body.startswith("PRODUCE"):
                produced = body
        if produced:
            break
        time.sleep(0.1)
    assert produced == "PRODUCE bread=0.3 iron=0.7"

    # The receipt is what the seat believes, so it can offer against it.
    manager.post("island", "@T2 produced {'bread': 0.27, 'iron': 0.04}; "
                           "0.0 labour unspent")
    for _ in range(200):
        if any(b.startswith("PROPOSE") for b in _bodies(manager, "island")):
            break
        time.sleep(0.1)
    else:
        pytest.fail("the seat never offered anything")

    manager.post("island", "the round is over. Stop; nothing further will "
                           "settle.")
    thread.join(timeout=10)
    assert done and done[0].over and done[0].seat == "T2"

    said = _bodies(manager, "island")
    assert any(b.startswith("NPC: npc-1 is a heuristic player") for b in said)
    assert any(b.startswith("ACK") for b in said)
    # And the board is the only thing it touched: everything it said is a line.
    assert npc.npcs_on_board([{"body": b} for b in said]) == {
        "npc-1": npc.show_mix({"greedy": 1.0})}


def test_the_watcher_counts_unfilled_seats_off_the_lobby_board(hub):
    """It has no privileged view of the lobby and is not given one, so what it
    can see is what it can count."""
    key = generate_key()
    lobby_client = _client(hub, "lobby", key)
    reader = _client(hub, "watcher", key)
    opener = _client(hub, "opener", key)
    lobby = Lobby(client=lobby_client, channel="lobby")

    opener.post("lobby", "OPEN traders=2 episodes=2 goods=2")
    lobby.drain()
    now = time.time()
    # Patient by default: a table that just opened is somebody else's to fill.
    assert missing(reader, "lobby", patience=300.0, now=now) == {}
    short = missing(reader, "lobby", patience=0.0, now=now)
    assert list(short.values()) == [2]
    table = next(iter(short))

    opener.post("lobby", f"JOIN {table} as scout-v2")
    lobby.drain()
    assert missing(reader, "lobby", patience=0.0, now=now) == {table: 1}


def test_a_settled_or_lapsed_table_is_not_offered_a_filler(hub):
    key = generate_key()
    lobby_client = _client(hub, "lobby", key)
    reader = _client(hub, "watcher", key)
    seat_a, seat_b = _client(hub, "a", key), _client(hub, "b", key)
    lobby = Lobby(client=lobby_client, channel="lobby")

    seat_a.post("lobby", "OPEN traders=2 episodes=2 goods=2")
    lobby.drain()
    table = next(iter(missing(reader, "lobby", patience=0.0)))
    seat_a.post("lobby", f"JOIN {table} as a")
    seat_b.post("lobby", f"JOIN {table} as b")
    _client(hub, "manager-claim", key).post("lobby", f"MANAGE {table}")
    lobby.drain()
    assert missing(reader, "lobby", patience=0.0) == {}
