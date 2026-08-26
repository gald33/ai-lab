"""The lobby against a real hub: a table opened, seated, managed, settled."""

from __future__ import annotations

import time

import pytest

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key
from switchboard.invite import Invite

from games.island import lobby as lobby_module
from games.island.lobby import Lobby

WORKSPACE = "w_lobby-test"


def _client(hub, agent_id, key=None, workspace=WORKSPACE):
    return Client(ClientConfig(url=hub, url_source="explicit",
                               workspace=workspace, key=key), agent_id=agent_id)


def _entrant(hub, agent_id, key=None, workspace=WORKSPACE):
    """A client whose signing key is witnessable -- registered, the way a
    real entrant would be before it could ever JOIN. `_client` stays bare for
    the tests that specifically want an unregistered peer."""
    client = _client(hub, agent_id, key, workspace)
    client.register(name=agent_id, kind="local", branch="main", task="")
    return client


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
    t1 = _entrant(hub, "t1", key)
    t2 = _entrant(hub, "t2", key)
    manager = _client(hub, "manager-claim", key)
    manager.register(name="lucille", kind="local", branch="main", task="running g1")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t2.post("lobby", "JOIN g1 as trader-b")
    lobby.drain()
    table = lobby.tables["g1"]
    assert table.seats == {t1.agent_id: "scout-v2", t2.agent_id: "trader-b"}
    assert table.keys == {t1.agent_id: t1.public_key, t2.agent_id: t2.public_key}
    assert not table.settled

    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    assert table.settled
    assert table.manager == "lucille"
    assert table.workspace == f"{lobby.client.config.workspace}-g1"
    assert isinstance(table.seed, int)

    lines = [m["body"] for m in lobby.client.history("lobby")]
    settlement = next(b for b in lines if b.startswith("g1 is full"))
    assert "T1 = scout-v2" in settlement and "T2 = trader-b" in settlement
    assert "managed by lucille" in settlement

    # The witnessed key is meant to be public -- "posts the binding on the
    # board, where everyone can see it" -- unlike the seed below.
    assert any(b.startswith("g1 seat T1 = scout-v2, key ") and t1.public_key in b
              for b in lines)

    invite_line = next(b for b in lines if b.startswith("g1 invite: "))
    invite = Invite.decode(invite_line.removeprefix("g1 invite: "))
    assert invite.workspace == table.workspace
    assert invite.url == hub

    # The seed deterministically reveals every trader's tastes the moment
    # it is known (`draw_island(agents, goods, seed)` is public), so it must
    # never be on the board -- not in the settlement line, not anywhere else
    # the lobby posts.
    assert not any(str(table.seed) in b for b in lines)


def test_settling_on_manage_before_the_table_is_full(hub):
    """Order should not matter: MANAGE arriving before the last seat also
    settles the instant the table becomes full."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1 = _entrant(hub, "t1", key)
    t2 = _entrant(hub, "t2", key)
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
    t1 = _entrant(hub, "t1", key)

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
    t1, t2 = _entrant(hub, "t1", key), _entrant(hub, "t2", key)

    opener.post("lobby", "OPEN traders=3 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t2.post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    assert len(lobby.tables["g1"].seats) == 1
    assert "already seated" in lobby.refusals[0]["reason"]


def test_a_join_from_an_unregistered_peer_is_refused(hub):
    """A name typed on a board proves nothing -- so does a JOIN from a peer
    this lobby has never seen a key for. Register and it goes through."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1 = _client(hub, "t1", key)   # bare: never registered

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    assert lobby.tables["g1"].seats == {}
    assert "no signing key known" in lobby.refusals[0]["reason"]

    t1.register(name="t1", kind="local", branch="main", task="")
    t1.post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    assert lobby.tables["g1"].seats == {t1.agent_id: "scout-v2"}
    assert lobby.tables["g1"].keys[t1.agent_id] == t1.public_key


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
    t1 = _entrant(hub, "t1", key)

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
    t1, t2 = _entrant(hub, "t1", key), _entrant(hub, "t2", key)
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


def test_a_seed_is_not_drawn_before_the_table_settles(hub):
    key = generate_key()
    drawn = []
    lobby = Lobby(client=_client(hub, "lobby", key), draw_seed=lambda: drawn.append(1) or 42)
    opener = _client(hub, "opener", key)
    t1 = _entrant(hub, "t1", key)

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    lobby.drain()

    assert drawn == []
    assert lobby.tables["g1"].seed is None


def test_the_seed_is_injectable_and_settlement_uses_it(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), draw_seed=lambda: 20260824)
    opener = _client(hub, "opener", key)
    t1, t2 = _entrant(hub, "t1", key), _entrant(hub, "t2", key)
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as scout-v2")
    t2.post("lobby", "JOIN g1 as trader-b")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    assert lobby.tables["g1"].seed == 20260824


def test_two_tables_draw_different_seeds(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    a1, a2 = _entrant(hub, "a1", key), _entrant(hub, "a2", key)
    b1, b2 = _entrant(hub, "b1", key), _entrant(hub, "b2", key)
    ma, mb = _client(hub, "ma", key), _client(hub, "mb", key)
    ma.register(name="ma", kind="local", branch="main", task="")
    mb.register(name="mb", kind="local", branch="main", task="")

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    a1.post("lobby", "JOIN g1 as scout-a1")
    a2.post("lobby", "JOIN g1 as scout-a2")
    ma.post("lobby", "MANAGE g1")
    b1.post("lobby", "JOIN g2 as scout-b1")
    b2.post("lobby", "JOIN g2 as scout-b2")
    mb.post("lobby", "MANAGE g2")
    lobby.drain()

    assert lobby.tables["g1"].seed != lobby.tables["g2"].seed


def _settle_one(lobby, hub, key, table="g1", seats=("scout-v2", "trader-b")):
    """Open, seat and manage one table on an already-constructed lobby."""
    opener = _client(hub, f"opener-{table}", key)
    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    for i, name in enumerate(seats):
        _entrant(hub, f"{table}-t{i}", key).post("lobby", f"JOIN {table} as {name}")
    manager = _client(hub, f"m-{table}", key)
    manager.register(name=f"lucille-{table}", kind="local", branch="main", task="")
    manager.post("lobby", f"MANAGE {table}")
    lobby.drain()
    return lobby.tables[table]


def test_a_restarted_lobby_does_not_settle_a_table_a_second_time(hub, tmp_path):
    """The seed is never on the board, so a lobby that forgot a settlement
    would draw a second one and mint a second room for one table."""
    key = generate_key()
    state = tmp_path / "lobby.json"
    first = Lobby(client=_client(hub, "lobby", key), state_path=state)
    table = _settle_one(first, hub, key)
    assert table.settled and table.seed is not None

    second = Lobby(client=_client(hub, "lobby", key), state_path=state)
    second.load()
    second.drain()

    # Same table, same seed, same room -- restored, not re-settled.
    assert second.tables["g1"].seed == table.seed
    assert second.tables["g1"].workspace == table.workspace
    assert second.tables["g1"].seats == table.seats
    assert second.tables["g1"].keys == table.keys
    posted = [m["body"] for m in second.client.history("lobby", limit=500)
              if isinstance(m.get("body"), str)]
    assert sum(b.startswith("g1 invite: ") for b in posted) == 1
    assert sum(b.startswith("g1 is full:") for b in posted) == 1
    # And the next table it opens is g2, not a second g1.
    assert _settle_one(second, hub, key, table="g2",
                       seats=("scout-c", "trader-d")).id == "g2"


def test_a_lobby_with_no_state_file_starts_clean(hub, tmp_path):
    lobby = Lobby(client=_client(hub, "lobby", generate_key()),
                  state_path=tmp_path / "absent.json")
    lobby.load()

    assert lobby.tables == {} and lobby.seen == set()


def test_the_newest_lobby_holds_the_channel_and_the_older_one_stands_down(hub):
    """Two lobbies on one board settle every table twice -- two seeds, two
    room keys -- and the game that follows plays to nobody."""
    key = generate_key()
    old = Lobby(client=_client(hub, "lobby", key))
    old.hold()
    new = Lobby(client=_client(hub, "lobby-2", key))
    new.hold()

    opener = _client(hub, "opener", key)
    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    old.drain()
    new.drain()

    assert old.stood_down and old.tables == {}
    assert not new.stood_down and list(new.tables) == ["g1"]
    said = [m["body"] for m in new.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any("stands down" in b for b in said)
    assert sum(b.startswith("g1 is forming") for b in said) == 1


def test_a_lobby_that_holds_alone_keeps_reading(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    lobby.hold()
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")

    lobby.drain()

    assert not lobby.stood_down and list(lobby.tables) == ["g1"]


def test_the_hold_line_is_not_read_as_talk_or_refused(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    lobby.hold()

    lobby.drain()

    assert lobby.refused == 0


def test_the_time_the_board_announces_is_the_time_the_table_opens(hub):
    """One number behind both: the line the entrants read and the clock the
    manager keeps. A board that announces a time and runs from another lies."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: 1_000_000.0)
    table = _settle_one(lobby, hub, key)

    assert table.opens_at == 1_000_000.0 + lobby.open_lead
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    stamp = time.strftime("%H:%M:%SZ", time.gmtime(table.opens_at))
    assert any(b.startswith("g1 is full:") and f"opens {stamp}" in b for b in said)


def test_a_manage_from_an_unregistered_peer_is_refused(hub):
    """The claimant is the one party whose absence means no game happens, so
    it is witnessed exactly like a seat."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _client(hub, "stranger", key).post("lobby", "MANAGE g1")

    lobby.drain()

    assert lobby.tables["g1"].manager is None
    assert lobby.refusals[-1]["kind"] == "manage"
    assert "MANAGE" in lobby.refusals[-1]["reason"]


def test_the_manager_s_key_goes_on_the_board_with_the_claim(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    manager = _entrant(hub, "m", key)
    manager.post("lobby", "MANAGE g1")

    lobby.drain()

    table = lobby.tables["g1"]
    assert table.manager_key
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any(f"g1 will be managed by" in b and table.manager_key in b
               for b in said)


def test_one_peer_cannot_mint_tables_without_limit(hub):
    """OPEN costs its author nothing, and a lobby faces strangers."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    noisy = _client(hub, "noisy", key)
    for _ in range(4):
        noisy.post("lobby", "OPEN traders=2 episodes=3 rounds=1")

    lobby.drain()

    assert list(lobby.tables) == ["g1", "g2"]
    assert lobby.refused == 2
    assert "already have 2 tables forming" in lobby.refusals[-1]["reason"]


def test_the_cap_is_per_peer_and_a_lapse_frees_a_slot(hub):
    now = [1_000_000.0]
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: now[0])
    a, b = _client(hub, "a", key), _client(hub, "b", key)
    for _ in range(2):
        a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    b.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    assert list(lobby.tables) == ["g1", "g2", "g3"] and lobby.refused == 0

    now[0] += lobby.table_ttl + 1
    lobby.drain()  # sweeps a's two tables
    a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()

    assert "g4" in lobby.tables and lobby.tables["g4"].opened_by


def test_two_lobbies_cannot_hold_one_state_file(hub, tmp_path):
    """`hold` keeps a second lobby off the board; this keeps one off the file,
    where a second writer is invisible rather than merely wrong."""
    from games.island.lobby import Held

    key = generate_key()
    first = Lobby(client=_client(hub, "lobby", key), state_path=tmp_path / "s.json")
    first.lock()
    second = Lobby(client=_client(hub, "lobby-2", key), state_path=tmp_path / "s.json")

    with pytest.raises(Held) as exc:
        second.lock()

    assert "another lobby already holds" in str(exc.value)
    # A different file is a different lobby, and is fine.
    Lobby(client=_client(hub, "lobby-3", key), state_path=tmp_path / "t.json").lock()


def test_a_board_that_outran_the_window_is_said_out_loud(hub, monkeypatch):
    """A missed line must not look like a line nobody wrote."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    talker = _client(hub, "talker", key)
    talker.post("lobby", "hello")
    lobby.drain()
    assert lobby.missed == 0

    # More arrives than one window holds, so the oldest of it falls out before
    # this lobby ever reads it. Shrinking the window is how a three-message
    # test reproduces what a busy board does to a 500-message one.
    talker.post("lobby", "chatter")
    talker.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    monkeypatch.setattr(lobby_module, "WINDOW", 1)
    lobby.drain()

    assert lobby.missed == 1
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any("never read" in b for b in said)
    # And it still settled the line it *did* read.
    assert list(lobby.tables) == ["g1"]


def test_an_ordinary_drain_reports_nothing_missed(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    talker = _client(hub, "talker", key)
    for _ in range(3):
        talker.post("lobby", "chatter")
        lobby.drain()

    assert lobby.missed == 0 and lobby.last_seq > 0
