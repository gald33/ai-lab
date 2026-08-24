"""The lobby against a real hub: a table opened, seated, managed, settled."""

from __future__ import annotations

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key
from switchboard.invite import Invite

from island.lobby import Lobby

WORKSPACE = "w_lobby-test"


def _client(hub, agent_id, key=None, workspace=WORKSPACE):
    return Client(ClientConfig(url=hub, url_source="explicit",
                               workspace=workspace, key=key), agent_id=agent_id)


def test_open_announces_a_forming_table(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    entrant = _client(hub, "scout", key)
    entrant.post("lobby", "OPEN traders=2 episodes=8 rounds=1")

    lobby.drain()

    assert list(lobby.tables) == ["g1"]
    table = lobby.tables["g1"]
    assert (table.traders, table.episodes, table.rounds) == (2, 8, 1)
    posted = [m["body"] for m in lobby.client.history("lobby")
             if m.get("from") == lobby.client.agent_id]
    assert any("g1 is forming" in b for b in posted)


def test_a_table_settles_the_moment_it_is_full_and_managed(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1 = _client(hub, "t1", key)
    t2 = _client(hub, "t2", key)
    manager = _client(hub, "manager-claim", key)
    manager.register(name="lucille", kind="local", branch="main", task="running g1")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t2.post("lobby", "JOIN g1 as trader-b")
    lobby.drain()
    table = lobby.tables["g1"]
    assert table.seats == {t1.agent_id: "scout-v2", t2.agent_id: "trader-b"}
    assert not table.settled

    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    assert table.settled
    assert table.manager == "lucille"
    assert table.workspace == f"{lobby.client.config.workspace}-g1"

    lines = [m["body"] for m in lobby.client.history("lobby")]
    settlement = next(b for b in lines if b.startswith("g1 is full"))
    assert "T1 = scout-v2" in settlement and "T2 = trader-b" in settlement
    assert "managed by lucille" in settlement

    invite_line = next(b for b in lines if b.startswith("g1 invite: "))
    invite = Invite.decode(invite_line.removeprefix("g1 invite: "))
    assert invite.workspace == table.workspace
    assert invite.url == hub


def test_settling_on_manage_before_the_table_is_full(hub):
    """Order should not matter: MANAGE arriving before the last seat also
    settles the instant the table becomes full."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1 = _client(hub, "t1", key)
    t2 = _client(hub, "t2", key)
    manager = _client(hub, "m", key)
    manager.register(name="gal", kind="local", branch="main", task="")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()
    assert not lobby.tables["g1"].settled

    t2.post("lobby", "JOIN g1 as trader-b")
    lobby.drain()
    assert lobby.tables["g1"].settled


def test_a_peer_cannot_hold_two_seats_at_one_table(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1 = _client(hub, "t1", key)

    opener.post("lobby", "OPEN traders=3 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t1.post("lobby", "JOIN g1 as scout-v2-again")
    lobby.drain()

    assert len(lobby.tables["g1"].seats) == 1
    assert lobby.refused == 1
    assert "already hold seat" in lobby.refusals[0]["reason"]


def test_a_name_cannot_be_reused_at_one_table(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1, t2 = _client(hub, "t1", key), _client(hub, "t2", key)

    opener.post("lobby", "OPEN traders=3 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t2.post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    assert len(lobby.tables["g1"].seats) == 1
    assert "already seated" in lobby.refusals[0]["reason"]


def test_a_second_manage_claim_is_refused(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    a, b = _client(hub, "a", key), _client(hub, "b", key)
    a.register(name="first", kind="local", branch="main", task="")
    b.register(name="second", kind="local", branch="main", task="")

    opener.post("lobby", "OPEN traders=4 episodes=3 rounds=1")
    lobby.drain()
    a.post("lobby", "MANAGE g1")
    b.post("lobby", "MANAGE g1")
    lobby.drain()

    assert lobby.tables["g1"].manager == "first"
    assert "already managed by first" in lobby.refusals[0]["reason"]


def test_join_and_manage_against_a_table_that_does_not_exist(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    entrant = _client(hub, "e", key)

    entrant.post("lobby", "JOIN g99 as somebody")
    entrant.post("lobby", "MANAGE g99")
    lobby.drain()

    assert lobby.refused == 2
    assert all("no such table" in r["reason"] for r in lobby.refusals)


def test_a_malformed_line_is_refused_and_never_repaired(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    entrant = _client(hub, "e", key)

    entrant.post("lobby", "OPEN traders=1 episodes=3")     # too few traders
    entrant.post("lobby", "JOIN g1")                        # missing "as name"
    entrant.post("lobby", "MANAGE")                         # missing table id
    lobby.drain()

    assert lobby.tables == {}
    assert lobby.refused == 3
    assert lobby.settled == 0


def test_talk_is_talk(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    entrant = _client(hub, "e", key)
    entrant.post("lobby", "good luck everyone")

    lobby.drain()

    assert lobby.talk == 1
    assert lobby.refused == 0


def test_a_table_lapses_if_it_does_not_fill_in_time(hub):
    key = generate_key()
    now = [1_000_000.0]
    lobby = Lobby(client=_client(hub, "lobby", key), table_ttl=60.0,
                 clock=lambda: now[0])
    opener = _client(hub, "opener", key)
    t1 = _client(hub, "t1", key)

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()
    assert not lobby.tables["g1"].lapsed

    now[0] += 61.0
    lobby.drain()

    assert lobby.tables["g1"].lapsed
    lines = [m["body"] for m in lobby.client.history("lobby")]
    assert any(b.startswith("g1 lapsed: not full") for b in lines)

    # Lapsed means gone: nobody can join or manage it after.
    t1.post("lobby", "JOIN g1 as too-late")
    lobby.drain()
    assert "lapsed" in lobby.refusals[-1]["reason"]


def test_a_settled_table_never_lapses(hub):
    key = generate_key()
    now = [0.0]
    lobby = Lobby(client=_client(hub, "lobby", key), table_ttl=10.0,
                 clock=lambda: now[0])
    opener = _client(hub, "opener", key)
    t1, t2 = _client(hub, "t1", key), _client(hub, "t2", key)
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t2.post("lobby", "JOIN g1 as trader-b")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()
    assert lobby.tables["g1"].settled

    now[0] += 100.0
    lobby.drain()

    assert not lobby.tables["g1"].lapsed
