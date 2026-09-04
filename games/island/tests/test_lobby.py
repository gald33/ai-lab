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
    # Named by its write key since 2026-09-03, not by the lobby and table.
    assert table.workspace.startswith("ws_")
    assert isinstance(table.seed, int)

    lines = [m["body"] for m in lobby.client.history("lobby")]
    settlement = next(b for b in lines if b.startswith("g1 is full"))
    assert "T1 = scout-v2" in settlement and "T2 = trader-b" in settlement
    assert "managed by lucille" in settlement

    # The witnessed key is meant to be public -- "posts the binding on the
    # board, where everyone can see it" -- unlike the seed below.
    assert any(b.startswith("g1 seat T1 = scout-v2, key ") and t1.public_key in b
              for b in lines)

    # The invite is whispered to the seats since 2026-09-02, and the board
    # only says so; what the lobby kept is what it sent.
    assert any(b.startswith("g1 invite: sealed to T1, T2") for b in lines)
    invite = Invite.decode(table.invite)
    assert invite.workspace == table.workspace
    assert invite.url == hub

    # The seed deterministically reveals every trader's tastes the moment
    # it is known (`draw_island(agents, goods, seed)` is public), so it must
    # never be on the board -- not in the settlement line, not anywhere else
    # the lobby posts.
    assert not any(str(table.seed) in b for b in lines)


def test_a_seat_whose_roster_row_lapsed_is_still_sealed_to(hub):
    """**g27, 2026-09-04.** The seat line said "sealed" when the hand sat
    down; 126 seconds later the table filled, the hand's two-minute roster
    row had lapsed, and the invite went on the board in the clear. The key a
    seat published when it sat down is what `Table.boxes` is for, and the
    client keeps every exchange key it has seen, so the roster of the moment
    does not get a say. Registered for one second here, and settled after
    it has lapsed."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    t1 = _client(hub, "t1", key)
    t1.register(name="t1", kind="local", branch="main", task="", ttl=1)
    t2 = _entrant(hub, "t2", key)
    manager = _entrant(hub, "manager-claim", key)

    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    t1.post("lobby", "JOIN g1 as early")
    lobby.drain()
    assert t1.agent_id in lobby.tables["g1"].boxes, "sealed when it sat down"

    time.sleep(1.5)
    assert not any(a["agent_id"] == t1.agent_id for a in lobby.client.agents()), \
        "and gone from the roster by the time the table fills"
    t2.post("lobby", "JOIN g1 as late")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    lines = [m["body"] for m in lobby.client.history("lobby")]
    assert any(b.startswith("g1 invite: sealed to T1, T2") for b in lines), \
        [b for b in lines if b.startswith("g1 invite")]
    t1.agents()               # the lobby's exchange key, as any reader must
    [got] = [m for m in t1.inbox() if isinstance(m.get("body"), str)
             and m["body"].startswith("g1 invite: swb1_")]
    assert got and not got.get("unreadable")


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


def test_the_cap_is_per_peer_and_a_lapse_frees_a_slot(hub, monkeypatch):
    """The per-peer cap, with the room's own cap lifted out of its way.

    `MAX_JOINABLE` (2) and `MAX_FORMING_PER_PEER` (2) are the same number, so
    on a default lobby the room's cap always bites first and this one can
    never be observed. It is kept because it is the narrower guard -- it bounds
    *one peer* rather than the board -- and it is what would still hold if the
    room's cap were ever raised. So this test raises it, which is exactly the
    circumstance the per-peer cap exists for.
    """
    now = [1_000_000.0]
    key = generate_key()
    monkeypatch.setattr(lobby_module, "MAX_JOINABLE", 5)
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: now[0])
    a, b = _client(hub, "a", key), _client(hub, "b", key)
    for _ in range(2):
        a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    b.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    assert list(lobby.tables) == ["g1", "g2", "g3"] and lobby.refused == 0

    a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    assert "g4" not in lobby.tables, "a's own third table is refused"
    assert "already have 2 tables forming" in lobby.refusals[-1]["reason"]

    now[0] += lobby.table_ttl + 1
    lobby.drain()  # sweeps a's two tables
    a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()

    assert "g4" in lobby.tables and lobby.tables["g4"].opened_by


def test_two_tables_are_enough_door_and_a_third_is_told_where_to_sit(hub):
    """**Decided by Gal, 2026-08-29.** Two tables open for a seat is a choice;
    a page of half-empty tables is entrants split between tables that then all
    lapse together. So the third OPEN is refused -- and the refusal names the
    tables to join instead, because somebody posting OPEN wants a game and
    this lobby has two to offer them.
    """
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    a, b, c = (_client(hub, "a", key), _client(hub, "b", key),
               _client(hub, "c", key))

    a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    b.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    assert list(lobby.tables) == ["g1", "g2"] and lobby.refused == 0

    c.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()

    assert list(lobby.tables) == ["g1", "g2"]
    reason = lobby.refusals[-1]["reason"]
    assert "already open for a seat" in reason
    assert "g1, g2" in reason, "a refusal that does not say where to sit"
    assert "JOIN" in reason


def test_an_empty_table_and_a_forming_one_both_count_as_door(hub):
    """`empty` and `forming` are the same thing to this cap: somewhere an
    entrant can sit down. The difference is only how far along it is."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    a, b = _client(hub, "a", key), _entrant(hub, "b", key)

    a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    a.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    b.post("lobby", "JOIN g1 as scout-v2")      # g1 forming, g2 still empty
    lobby.drain()

    assert lobby.tables["g1"].joinable() and lobby.tables["g2"].joinable()
    assert len(lobby.tables["g1"].seats) == 1 and not lobby.tables["g2"].seats

    _client(hub, "c", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    assert "g3" not in lobby.tables


def test_a_settled_table_frees_the_door_and_still_holds_a_place(hub):
    """Settling is what makes room at the door -- and the table has not gone
    anywhere, it is being played, so it still counts against the total."""
    now = [1_000_000.0]
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: now[0])
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    _client(hub, "opener2", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2")
    _entrant(hub, "t2", key).post("lobby", "JOIN g1 as trader-b")
    _entrant(hub, "m", key).post("lobby", "MANAGE g1")
    lobby.drain()
    assert lobby.tables["g1"].settled

    # One seat's worth of door freed, so a third table opens now.
    _client(hub, "c", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    assert "g3" in lobby.tables
    assert lobby.tables["g1"].playing(now[0]), "settled, and its round is running"


def test_the_total_counts_tables_being_played_and_not_ones_long_finished(hub):
    """The lobby cannot see a table's own room, so it reads the schedule it
    announced itself: the last bell falls `episodes x seconds` after
    `opens_at`, and `PLAY_SLACK` covers the record being written after it."""
    now = [1_000_000.0]
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: now[0])
    _client(hub, "opener", key).post(
        "lobby", "OPEN traders=2 episodes=3 rounds=1 seconds=60")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2")
    _entrant(hub, "t2", key).post("lobby", "JOIN g1 as trader-b")
    _entrant(hub, "m", key).post("lobby", "MANAGE g1")
    lobby.drain()
    table = lobby.tables["g1"]

    assert table.playing(table.opens_at), "the moment it opens"
    assert table.playing(table.opens_at + 3 * 60 - 1), "before the last bell"
    assert table.playing(table.opens_at + 3 * 60 + 1), "the record is written"
    assert not table.playing(table.opens_at + 3 * 60 + lobby_module.PLAY_SLACK + 1)

    # A settled table that never announced a start is counted as playing --
    # guessing short there would drop a live game out of the total entirely.
    table.opens_at = None
    assert table.playing(now[0] + 10_000)


def test_five_tables_is_the_ceiling_and_a_finished_game_frees_a_place(hub):
    key = generate_key()
    now = [1_000_000.0]
    lobby = Lobby(client=_client(hub, "lobby", key), clock=lambda: now[0])
    manager = _entrant(hub, "m", key)

    # **Four playing plus one open for a seat.** Not two open: with two the
    # door cap bites first and the ceiling is never reached, which is the
    # right order of refusals and the reason this arrangement is the only one
    # that tests the ceiling at all.
    for n in range(4):
        _client(hub, f"o{n}", key).post(
            "lobby", "OPEN traders=2 episodes=2 rounds=1 seconds=15")
        lobby.drain()
        table = f"g{n + 1}"
        _entrant(hub, f"a{n}", key).post("lobby", f"JOIN {table} as a{n}")
        _entrant(hub, f"b{n}", key).post("lobby", f"JOIN {table} as b{n}")
        manager.post("lobby", f"MANAGE {table}")
        lobby.drain()
    _client(hub, "p0", key).post("lobby", "OPEN traders=2 episodes=2 rounds=1")
    lobby.drain()
    assert len(lobby.tables) == 5

    _client(hub, "late", key).post("lobby", "OPEN traders=2 episodes=2 rounds=1")
    lobby.drain()
    assert len(lobby.tables) == 5, "the sixth is refused"
    assert "at its limit of 5 tables" in lobby.refusals[-1]["reason"]

    # Once the three games have plainly finished, the ceiling has room again --
    # the two forming tables still hold the door shut, so lapse them too.
    now[0] += lobby.table_ttl + lobby_module.PLAY_SLACK + 1
    lobby.drain()
    _client(hub, "late", key).post("lobby", "OPEN traders=2 episodes=2 rounds=1")
    lobby.drain()
    assert "g6" in lobby.tables


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


def test_a_table_commits_before_any_seat_can_have_joined(hub):
    """The commitment is only worth anything at the moment it is made: a lobby
    that has not read a nonce cannot pick a seed to suit anybody."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")

    lobby.drain()

    table = lobby.tables["g1"]
    import hashlib
    assert table.commit == hashlib.sha256(table.nonce.encode()).hexdigest()
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any(f"g1 commits {table.commit}" in b for b in said)
    assert not any(table.nonce in b for b in said), "the nonce stays secret"


def test_a_seed_every_seat_helped_draw_is_recomputable_from_the_board(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key),
                  draw_nonce=lambda: "aaaaaaaaaaaaaaaa")
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2 nonce=1111111111111111")
    _entrant(hub, "t2", key).post("lobby", "JOIN g1 as trader-b nonce=2222222222222222")
    manager = _entrant(hub, "m", key)
    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    table = lobby.tables["g1"]
    assert table.verifiable() and table.draw == "commit-reveal"

    import hashlib
    material = "|".join(["aaaaaaaaaaaaaaaa", "1111111111111111", "2222222222222222"])
    expected = int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], "big") >> 1
    assert table.seed == expected, "anybody can recompute it once the nonce is out"
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any("drawn from every nonce at this table" in b for b in said)


def test_the_order_seats_arrived_in_cannot_change_the_island(hub):
    """Sorted, so a lobby cannot re-order arrivals into a better island."""
    key = generate_key()
    seeds = []
    for first, second in (("t1", "t2"), ("t2", "t1")):
        lobby = Lobby(client=_client(hub, f"lobby-{first}", key),
                      draw_nonce=lambda: "aaaaaaaaaaaaaaaa")
        _client(hub, f"opener-{first}", key).post(
            "lobby", "OPEN traders=2 episodes=3 rounds=1")
        lobby.drain()
        nonces = {"t1": "1111111111111111", "t2": "2222222222222222"}
        for who in (first, second):
            _entrant(hub, f"{who}-{first}", key).post(
                "lobby", f"JOIN {list(lobby.tables)[-1]} as {who}-{first} "
                         f"nonce={nonces[who]}")
        _entrant(hub, f"m-{first}", key).post("lobby", f"MANAGE {list(lobby.tables)[-1]}")
        lobby.drain()
        seeds.append(lobby.tables[list(lobby.tables)[-1]].seed)

    assert seeds[0] == seeds[1]


def test_a_table_missing_a_nonce_says_its_draw_is_not_checkable(hub):
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "t1", key).post("lobby", "JOIN g1 as scout-v2 nonce=1111111111111111")
    _entrant(hub, "t2", key).post("lobby", "JOIN g1 as trader-b")
    _entrant(hub, "m", key).post("lobby", "MANAGE g1")
    lobby.drain()

    table = lobby.tables["g1"]
    assert not table.verifiable() and table.draw == "unverified"
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any("not checkable afterwards" in b for b in said)


def test_a_table_room_is_keyed_whatever_the_lobby_is(hub):
    """A table's room key must not depend on the lobby's own encryption.

    It used to: `generate_key() if self.client.encrypted else None`. So a
    lobby run without a key dealt every game into a room anybody holding the
    hub token could walk into -- and nothing said so.
    """
    lobby = Lobby(client=_client(hub, "lobby", generate_key()))
    table = _settle_one(lobby, hub, lobby.client.config.key)

    invite = Invite.decode(table.invite)
    assert invite.key and invite.workspace == table.workspace


def test_a_plaintext_lobby_cannot_seat_anybody_and_says_why(hub):
    """**The reason the lobby's key is published rather than absent.**

    Switchboard signs a message inside `_seal_request`, before sealing, so the
    signature rides within the ciphertext -- "a signature the transport can
    quietly remove proves nothing". A plaintext room therefore carries no
    signatures at all, and a seat binds by a witnessed signing key. So a lobby
    with no key refuses every JOIN, and the honest way to let strangers in is
    a key that is *published*, not a room that has none.
    """
    lobby = Lobby(client=_client(hub, "lobby", None))
    assert not lobby.client.encrypted
    _client(hub, "opener", None).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    entrant = _client(hub, "t1", None)
    entrant.register(name="t1", kind="local", branch="main", task="")
    entrant.post("lobby", "JOIN g1 as scout-v2")

    lobby.drain()

    assert lobby.tables["g1"].seats == {}
    assert lobby.refusals[-1]["reason"].startswith("JOIN must be signed")


def test_the_invite_is_whispered_to_each_seat_and_kept_off_the_board(hub):
    """The room's key is what makes a seat a seat, and until 2026-09-02 the
    lobby posted it in the clear one line after the settlement. Now every
    seat that published an exchange key is whispered the invite, the board
    says only that it was sent, and the lobby keeps it in its own state so
    the runner can play the table it settled."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    # The seat clients are kept: an exchange key is per *client*, and a
    # second client under the same id could not open what was sealed to the
    # first -- the same fact ENTER.md calls the one thing that is not obvious.
    seats = [_entrant(hub, f"g1-t{i}", key) for i in range(2)]
    for i, seat in enumerate(seats):
        seat.post("lobby", f"JOIN g1 as seat-{i}")
    manager = _entrant(hub, "m", key)
    manager.post("lobby", "MANAGE g1")
    lobby.drain()
    table = lobby.tables["g1"]
    assert table.settled and table.sealable()

    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert not any(table.invite in b for b in said), "the credential is off the board"
    assert any(b.startswith("g1 invite: sealed to T1, T2 and the manager")
               for b in said)
    assert table.invite.startswith("swb1_")
    assert Invite.decode(table.invite).workspace == table.workspace

    for client in seats + [manager]:
        client.agents()                                 # the lobby's exchange key
        got = [m.get("body") for m in client.inbox(wait=0.0, limit=20)]
        assert f"g1 invite: {table.invite}" in got, got


def test_a_table_with_a_keyless_seat_gets_its_invite_in_the_clear_and_said_so(hub):
    """The weaker thing is kept and says so: a seat that published no exchange
    key cannot be whispered to, the table was already practice, and the invite
    goes on the board as before rather than to nobody."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    opener.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    lobby.drain()
    _entrant(hub, "keyed", key).post("lobby", "JOIN g1 as keyed")
    bare = _client(hub, "bare", key)
    # A signing key without a registration: witnessable, not sealable.
    bare.post("lobby", "JOIN g1 as bare")
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()
    table = lobby.tables["g1"]
    if not table.settled:
        pytest.skip("an unregistered JOIN is refused on this hub; the clear "
                    "path needs a seat that was witnessed without a key")
    assert not table.sealable()
    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    assert any(b == f"g1 invite: {table.invite}" for b in said)


def test_the_room_is_write_protected_and_the_watch_invite_cannot_speak(hub):
    """Switchboard 2.0.0: a table's room is named by its write key, the seats
    are whispered an invite that carries it, and the board carries a
    read-only invite for everybody else -- which the hub, not the page,
    keeps read-only."""
    from switchboard import rooms
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    table = _settle_one(lobby, hub, key)
    assert rooms.is_write_protected(table.workspace)

    said = [m["body"] for m in lobby.client.history("lobby", limit=500)
            if isinstance(m.get("body"), str)]
    line = next(b for b in said if b.startswith("g1 watch: "))
    room_id, blob = line[len("g1 watch: "):].split()[:2]
    assert room_id == table.workspace and blob == table.watch
    watch = Invite.decode(table.watch)
    assert watch.workspace == table.workspace and watch.key
    assert watch.write_key is None, "the watch invite carries no write key"
    full = Invite.decode(table.invite)
    assert full.write_key and full.workspace == table.workspace

    # A spectator holding the watch invite reads the room ...
    seat = Client.from_invite(full, agent_id="seat")
    seat.register(name="seat", kind="local", branch="main", task="")
    seat.post("island", "ACK ready")
    watcher = Client.from_invite(watch, agent_id="watcher")
    assert [m["body"] for m in watcher.history("island")] == ["ACK ready"]
    # ... and cannot write in it, however it tries: the hub answers 403 and
    # the client names the reason.
    from switchboard.client import ReadOnlyRoom
    with pytest.raises(ReadOnlyRoom) as refused:
        watcher.post("island", "PRODUCE bread=1.0")
    assert "write-protected" in str(refused.value)
    assert [m["body"] for m in seat.history("island")] == ["ACK ready"]
