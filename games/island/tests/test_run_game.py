"""A whole game, from an empty lobby to a row on the scoreboard.

Every seam the plan set out to close, in one pass against a real hub: the
lobby settles a table, the runner picks it up from the invite on the board,
deals, binds the manager to the witnessed keys, runs the episodes, writes the
board, and the ledger ingests the result and ranks it.

The traders are scripted `Client`s posting `PRODUCE`/`PROPOSE`/`APPROVE` --
real board writes through the real client, so everything under test is the
thing that runs, but no model is called and nothing is spent. A game with real
agents is a separate step and needs its own authorization.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest
from switchboard import signing
from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from games.island import run_game
from games.island.lobby import Lobby, Table

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "experiments" / "005-deliberation-protocol" / "viewer"))

WORKSPACE = "w_game-test"


@pytest.fixture
def identities():
    """One signing identity per entrant, held across both rooms.

    A seat binds by signing key, because a peer id is blinded per workspace
    and the lobby's is meaningless in the table's room. That only works if an
    entrant *has* one key in both -- which is what `switchboard-mcp` provides:
    `signing.SigningServer` listens on a socket keyed by `agent_id`, and every
    `Client` for that agent attaches to it instead of minting its own. Two
    bare `Client`s in one process would otherwise carry two different keys and
    the seat would never bind, so this models the real thing rather than
    working around it.
    """
    servers = []
    for agent_id in ("t1", "t2"):
        server = signing.SigningServer(signing.SigningIdentity.generate(), agent_id)
        if not server.start():                       # pragma: no cover
            pytest.skip("no AF_UNIX signer available on this platform")
        servers.append(server)
    yield
    for server in servers:
        server.close()


def _client(hub, agent_id, key, workspace=WORKSPACE):
    return Client(ClientConfig(url=hub, url_source="explicit",
                               workspace=workspace, key=key), agent_id=agent_id)


def _seated(hub, key, agent_id, name, table="g1"):
    """An entrant that registers (so its key is witnessable) and claims a seat."""
    client = _client(hub, agent_id, key)
    client.register(name=agent_id, kind="local", branch="main", task="")
    client.post("lobby", f"JOIN {table} as {name}")
    return client


@pytest.fixture
def settled(hub, identities):
    """A lobby with one full, managed, settled two-trader table."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    opener = _client(hub, "opener", key)
    opener.post("lobby", "OPEN traders=2 episodes=2 rounds=1")
    lobby.drain()

    t1 = _seated(hub, key, "t1", "scout-v2")
    t2 = _seated(hub, key, "t2", "trader-b")
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    table = lobby.tables["g1"]
    assert table.settled and table.seed is not None
    return lobby, table, {"scout-v2": t1, "trader-b": t2}, key


def test_a_settled_table_plays_through_and_lands_on_the_scoreboard(settled, hub, tmp_path):
    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    assert invite is not None, "the lobby posts an invite when it settles"
    assert invite.workspace == table.workspace

    # The entrants move to the table's room with the invite, keeping the agent
    # id -- and therefore the signing key -- each took its seat under.
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")

    # Scripted play: both produce, then one offers and the other accepts, so
    # the round exercises production *and* exchange.
    record, board = _play_scripted(table, invite, room, tmp_path)

    # --- the board is on disk, in the shape the viewer reads ---------------
    assert board.is_file()
    saved = json.loads(board.read_text())
    assert saved["workspace"] == table.workspace
    assert saved["channel"] == "island"
    assert {"seq", "at", "author", "body", "signature"} == set(saved["messages"][0])
    # The manager's reading of each line's signature travels with the board:
    # it is not re-verifiable, and `verify.py` says so, but it is what lets a
    # later reader check that a seat's lines carry the seat's witnessed key.
    signed = [m for m in saved["messages"] if m["author"].startswith("T")]
    assert signed and all(m["signature"]["status"] == "verified" and
                          m["signature"]["key"] in table.keys.values()
                          for m in signed)
    authors = {m["author"] for m in saved["messages"]}
    assert "manager" in authors and "T1" in authors, (
        "the board names seats, the way every saved board already does")

    # --- the manager settled real production and a real trade --------------
    assert record["rounds"][0]["settled"] >= 3
    assert record["rounds"][0]["refused"] == 0
    assert len(record["rounds"][0]["trajectory"]) == 2, "two episodes, two vectors"

    # --- and the ledger takes it, scoring it from the seed ------------------
    import scores  # the viewer's ledger, on the path via the fixture above

    result = tmp_path / "g1.json"
    result.write_text(json.dumps(record))
    ledger = tmp_path / "ledger.jsonl"
    added, _ = scores.ingest(result, ledger=ledger, players=record["players"])
    assert record["players"] == {"T1": "scout-v2", "T2": "trader-b"}

    assert len(added) == 1
    row = added[0]
    assert row["status"] != "unscored", row.get("why")
    assert row["island"]["seed"] == table.seed
    assert row["island"]["agents"] == 2 and row["island"]["episodes"] == 2
    # The seat names, not the model -- the gap the lobby closes.
    assert {p["id"] for p in row["players"]} == {"scout-v2", "trader-b"}
    assert row["eff_round"] is not None and row["autarky_floor"] is not None


def _play_scripted(table, invite, room, out: Path):
    """`run_game.play`, with the traders acting inside each episode.

    The runner's own loop waits on a wall clock, which a test must not: this
    drives the same calls in the same order with the waiting replaced by the
    traders acting. Everything being asserted -- dealing, binding, settling,
    the board, the record -- is the runner's own code.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    client = Client.from_invite(invite, agent_id=MANAGER)
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    bound = run_game.bind_seats(mgr, table)
    assert bound == {"T1", "T2"}, "both seats resolved by their witnessed key"

    run_game.deal(mgr, dealer, table)

    room["scout-v2"].post("island", "ACK ready")
    room["trader-b"].post("island", "ACK ready")
    mgr.drain()

    for episode in range(table.episodes):
        mgr.open_episode()
        room["scout-v2"].post("island", "PRODUCE bread=0.5 iron=0.5")
        room["trader-b"].post("island", "PRODUCE cloth=0.5 salt=0.5")
        mgr.drain()
        room["scout-v2"].post("island",
                              "PROPOSE to=T2 give=bread:0.05 want=cloth:0.05")
        mgr.drain()
        room["trader-b"].post("island", "APPROVE p%d" % (episode + 1))
        mgr.drain()
        mgr.close_episode()

    board = run_game.save_board(mgr, out)
    record = run_game.record(table, mgr, dealer, out, board=board, seconds=1.0)
    return record, board


def test_the_manager_is_bound_to_the_keys_the_lobby_witnessed(settled, hub, tmp_path):
    """The seat binding is carried through, so an impostor is refused by the
    round even though the lobby is the thing that witnessed the key."""
    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)

    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    client = Client.from_invite(invite, agent_id=MANAGER)
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)

    # Nothing to bind before the entrant turns up in this room -- a seat is
    # resolved by the key its holder publishes here, so it cannot be bound
    # from an empty roster.
    assert run_game.bind_seats(mgr, table) == set()

    real = Client.from_invite(invite, agent_id="t1")
    real.register(name="scout-v2", kind="local", branch="main", task="")
    assert run_game.bind_seats(mgr, table) == {"T1"}, (
        "the seat binds once its holder registers, by the witnessed key")

    # An impostor with the same agent id but its own keypair. `agent_id` is
    # self-asserted and blinds identically, so `from` cannot tell them apart;
    # only the signature can. Built without the entrant's signer so it mints
    # a key of its own, which is exactly what an impostor has.
    impostor = Client(ClientConfig(url=invite.url, url_source="explicit",
                                   workspace=invite.workspace, token=invite.token,
                                   key=invite.key),
                      agent_id="t1", key=invite.key)
    object.__setattr__(impostor, "signing", signing.SigningIdentity.generate())
    assert impostor.agent_id == real.agent_id
    assert impostor.public_key != real.public_key

    mgr.open_episode()
    impostor.post("island", "PRODUCE bread=1.0")
    mgr.drain()

    assert mgr.refused == 1
    assert mgr.refusals[0]["kind"] == "imposture"
    assert not mgr.holders["T1"].produced


def test_a_table_nobody_offered_a_key_for_cannot_be_ranked(settled):
    """A seat that gave the manager nothing to seal to can only play in the
    clear -- so the table is not sealable, its record says practice, and
    `--ranked` skips it rather than quietly producing a row that claims more
    than it can."""
    _lobby, table, _seated, _key = settled
    assert not table.sealable(), "these seats joined without a box key"

    lines = [m["body"] for m in _lobby.client.history("lobby")]
    assert any("PRACTICE" in b and "not ranked" in b
               for b in lines if b.startswith("g1 is full"))


def test_dealing_says_out_loud_that_it_is_public(settled, hub, tmp_path):
    """The one honestly-wrong step until 2c: it is announced, not glossed."""
    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)

    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    client = Client.from_invite(invite, agent_id=MANAGER)
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    run_game.bind_seats(mgr, table)

    run_game.deal(mgr, dealer, table)

    lines = [m["body"] for m in mgr.client.history("island")]
    assert any("PRACTICE" in b and "in the clear" in b for b in lines)
    assert any(b.startswith("@T1 (scout-v2) You are T1.") for b in lines), (
        "addressed by seat, and saying which entrant holds it")
    assert any("taste weights" in b for b in lines)


def test_the_replay_and_the_room_key_are_published_only_at_the_end(settled, hub, tmp_path):
    """Item 4. A seed still in play is not replayable by anyone, so the
    sidecar carries the tastes *and* the room key, and is written when the
    game is over rather than while it runs."""
    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")

    record, _ = _play_scripted(table, invite, room, tmp_path)
    sidecar = run_game.publish(table, invite, record, tmp_path)

    payload = json.loads(sidecar.read_text())
    assert sidecar.name == f"reveal-{table.workspace}.json"
    # The hidden half, now that hiding it no longer matters.
    assert set(payload["traders"]) == {"T1", "T2"}
    assert "taste" in payload["traders"]["T1"]
    assert "capacity" in payload["traders"]["T1"]
    # And the key that opens the room, so anybody can check who signed what.
    assert payload["room_key"] == invite.key
    assert payload["players"] == {"T1": "scout-v2", "T2": "trader-b"}
    assert payload["round"]["seed"] == table.seed


# --- the sealed round (item 2c) -------------------------------------------

@pytest.fixture
def sealed_table(hub, identities):
    """A table where both seats offered a key to seal to."""
    from island.sealed import BoxKey

    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=1 rounds=1")
    lobby.drain()

    boxes = {}
    for agent_id, name in (("t1", "scout-v2"), ("t2", "trader-b")):
        box = BoxKey.generate()
        boxes[name] = box
        client = _client(hub, agent_id, key)
        client.register(name=agent_id, kind="local", branch="main", task="")
        client.post("lobby", f"JOIN g1 as {name} box={box.public}")
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    table = lobby.tables["g1"]
    assert table.settled and table.sealable()
    return lobby, table, boxes


def test_a_sealed_round_keeps_tastes_and_shares_off_the_board(sealed_table, tmp_path):
    """The property the whole private channel exists for, end to end.

    Nothing a spectator can read tells them a taste or a share -- and the
    capacity leak closes with them, because capacity is the receipt's quantity
    divided by the share and the share is now sealed.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, SEALED_CONTEXT, Manager
    from island.sealed import BoxKey, seal_to

    lobby, table, boxes = sealed_table
    invite = run_game.pending_invite(lobby, table)
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")

    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity,
                  client=Client.from_invite(invite, agent_id=MANAGER),
                  channel="island", goods=dealer.goods, box=BoxKey.generate())
    assert run_game.bind_seats(mgr, table) == {"T1", "T2"}

    run_game.deal(mgr, dealer, table)

    # Each seat opens its own half; the other seat cannot.
    lines = [m["body"] for m in mgr.client.history("island")]
    mine = next(b for b in lines if b.startswith("@T1 (scout-v2) SEALED"))
    blob = mine.split(" ", 2)[2]
    assert boxes["scout-v2"].open(blob, run_game.PRIVATE_CONTEXT).startswith("You are T1.")
    with pytest.raises(Exception):
        boxes["trader-b"].open(blob, run_game.PRIVATE_CONTEXT)

    # A sealed PRODUCE settles, and the plan never reaches the board.
    mgr.open_episode()
    room["scout-v2"].post("island", seal_to(mgr.box.public,
                                            "PRODUCE bread=0.5 iron=0.5",
                                            SEALED_CONTEXT))
    room["trader-b"].post("island", seal_to(mgr.box.public,
                                            "PRODUCE cloth=1.0", SEALED_CONTEXT))
    mgr.drain()

    assert mgr.refused == 0
    assert mgr.holders["T1"].produced and mgr.holders["T2"].produced

    # Now the real assertion: read the whole board as a spectator would.
    board = " ".join(b for b in
                     [m["body"] for m in mgr.client.history("island")]
                     if isinstance(b, str))
    assert "taste weights" not in board, "a taste reached the board"
    assert "bread=0.5" not in board and "cloth=1.0" not in board, \
        "a production share reached the board"
    # The receipts are still public -- that is what the viewer draws.
    assert "produced" in board and "labour unspent" in board


def test_a_sealed_produce_is_refused_when_the_round_has_no_channel(hub):
    """A manager with no box refuses a sealed line rather than counting it as
    talk -- silence and unreadability are different events."""
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager
    from island.sealed import BoxKey, seal_to

    key = generate_key()
    mgr = Manager(capacity=Dealer.draw(1, 2, GOODS).capacity,
                  client=_client(hub, MANAGER, key), channel="island",
                  goods=GOODS, names=("T1", "T2"))
    trader = _client(hub, "t1", key)
    mgr.bind(trader.agent_id, "T1")
    mgr.open_episode()

    trader.post("island", seal_to(BoxKey.generate().public,
                                  "PRODUCE bread=1.0", "island.produce"))
    mgr.drain()

    assert mgr.refused == 1
    assert mgr.refusals[0]["kind"] == "sealed"
    assert "no private channel" in mgr.refusals[0]["reason"]
    # And the ciphertext is not copied into the record that gets published.
    assert mgr.refusals[0]["line"] == "<sealed>"


# --- two lobbies, one table (the failure that reads as nobody turning up) ---

def test_a_table_settled_twice_is_refused_rather_than_played(settled, hub):
    """The seed is never on the board, so whoever settles a table is the only
    one who can deal it -- and a second lobby draining the same channel
    settles it again, mints a second room key, and puts the entrants and the
    manager in one workspace on two keys. Nobody can read anybody, the manager
    settles nothing, and the record says `absent` as though the table were
    empty. Every part works; the failure is silence. So it is refused.
    """
    lobby, table, _rooms, _key = settled

    # A second lobby on the same channel: exactly what running `run_lobby`
    # alongside `run_game` does.
    other = Lobby(client=lobby.client)
    other.drain()

    invites = [b for m in other.client.history(other.channel, limit=500)
               if isinstance(b := m.get("body"), str)
               and b.startswith(f"{table.id} invite: ")]
    assert len(invites) > 1, "the second lobby should have settled it again"

    with pytest.raises(run_game.SettledTwice, match="more than one lobby"):
        run_game.pending_invite(lobby, table)


def test_one_lobby_still_yields_its_invite(settled):
    """The guard must not fire on the ordinary case."""
    lobby, table, _rooms, _key = settled

    invite = run_game.pending_invite(lobby, table)

    assert invite is not None and invite.workspace == table.workspace


# --- claiming a table nobody else will run ---------------------------------

def test_the_runner_offers_to_manage_a_table_nobody_claimed(hub, identities):
    """The gap a real run found and every test here had hidden.

    A table settles when it is full **and** managed. Every fixture above posts
    `MANAGE` by hand, so `run_game` was only ever pointed at tables that were
    already settled -- and in a real run nobody posts it, so two entrants took
    their seats, the table sat full and unmanaged, and it would have lapsed
    without a single line being played.

    The runner is the thing that would manage it, so it says so on the board,
    in the grammar, and its lobby settles that claim like anybody else's.
    """
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    manager = _client(hub, "manager", key)
    manager.register(name="lucille", kind="local", branch="main", task="")

    _seated(hub, key, "t1", "scout-v2")
    opener = _client(hub, "opener", key)
    opener.post("lobby", "OPEN traders=2 episodes=1 rounds=1")
    lobby.drain()
    _seated(hub, key, "t1", "scout-v2")
    _seated(hub, key, "t2", "trader-b")
    lobby.drain()

    table = lobby.tables["g1"]
    assert table.full() and not table.settled, "full, and nobody to run it"

    claimed: set[str] = set()
    run_game.claim(manager, lobby, "lobby", claimed)
    lobby.drain()

    assert table.settled, "the runner's own claim is what settles it"
    assert table.manager == "lucille"


def test_the_runner_does_not_claim_a_table_somebody_else_took(hub, identities):
    """`MANAGE` is an offer, not a seizure: a second claim is refused, so the
    runner must not make one for a table that already has somebody."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    mine = _client(hub, "manager", key)
    mine.register(name="lucille", kind="local", branch="main", task="")
    theirs = _client(hub, "other", key)
    theirs.register(name="somebody-else", kind="local", branch="main", task="")

    opener = _client(hub, "opener", key)
    opener.post("lobby", "OPEN traders=2 episodes=1 rounds=1")
    lobby.drain()
    theirs.post("lobby", "MANAGE g1")
    lobby.drain()
    assert lobby.tables["g1"].manager == "somebody-else"

    before = lobby.refused
    run_game.claim(mine, lobby, "lobby", set())
    lobby.drain()

    assert lobby.tables["g1"].manager == "somebody-else"
    assert lobby.refused == before, "no refusal, because no second claim"


def test_a_table_is_claimed_once_however_often_the_loop_turns(hub, identities):
    """The loop runs every few seconds; a claim per turn would be a refusal
    per turn on the board of a table it already offered to run."""
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    manager = _client(hub, "manager", key)
    manager.register(name="lucille", kind="local", branch="main", task="")
    opener = _client(hub, "opener", key)
    opener.post("lobby", "OPEN traders=2 episodes=1 rounds=1")
    lobby.drain()

    claimed: set[str] = set()
    for _ in range(3):
        run_game.claim(manager, lobby, "lobby", claimed)
    lobby.drain()

    lines = [m["body"] for m in lobby.client.history("lobby", limit=100)]
    assert sum(1 for b in lines if b == "MANAGE g1") == 1
    assert lobby.refused == 0


def test_a_seat_is_not_absent_before_the_time_the_board_announced():
    """An entrant that turns up when the board said is on time, even if this
    runner's own ack window would have closed first."""
    table = Table(id="g1", traders=2, episodes=2, rounds=1, opened_at=0.0,
                  opens_at=1_000_120.0)

    assert run_game.ack_close(1_000_000.0, 60, table) == 1_000_120.0
    assert run_game.ack_close(1_000_000.0, 300, table) == 1_000_300.0


def test_a_table_that_announced_no_time_keeps_the_runner_s_own_window():
    table = Table(id="g1", traders=2, episodes=2, rounds=1, opened_at=0.0)

    assert run_game.ack_close(1_000_000.0, 60, table) == 1_000_060.0


def test_the_lobby_keeps_reading_while_a_game_is_on():
    calls = []
    run_game._tick(lambda: calls.append(1))

    assert calls == [1]


def test_a_lobby_that_throws_mid_game_does_not_stop_the_game(capsys):
    """A game in progress is the thing with a clock on it."""
    def boom():
        raise RuntimeError("hub blinked")

    run_game._tick(boom)  # must not raise

    assert "continuing" in capsys.readouterr().out


def test_tables_play_at_the_same_time_rather_than_in_turn(monkeypatch, tmp_path):
    """Two tables settling a minute apart must not mean the second one's
    traders sit in a silent room for the length of somebody else's game."""
    import threading
    started, release = [], threading.Event()

    def slow_play(table, invite, **kw):
        started.append(table.id)
        release.wait(5)
        return {"players": {}, "rounds": []}

    monkeypatch.setattr(run_game, "play", slow_play)
    monkeypatch.setattr(run_game, "publish", lambda *a, **k: tmp_path / "x.json")
    monkeypatch.setattr(run_game._scores, "ingest", lambda *a, **k: ([], None))

    tables = {f"g{i}": Table(id=f"g{i}", traders=2, episodes=1, rounds=1,
                             opened_at=0.0, settled=True, seed=1,
                             workspace=f"w{i}") for i in (1, 2)}

    class StubLobby:
        stood_down = False
        def __init__(self, tables): self.tables = tables
        def drain(self): pass

    monkeypatch.setattr(run_game, "pending_invite", lambda lobby, table: "invite")
    watcher = threading.Thread(
        target=run_game.watch,
        args=(StubLobby(tables),),
        kwargs={"every": 0.05, "episode_seconds": 1, "ack_seconds": 1,
                "out": tmp_path},
        daemon=True)
    watcher.start()
    for _ in range(100):
        if len(started) == 2:
            break
        time.sleep(0.05)
    release.set()

    assert sorted(started) == ["g1", "g2"], "both tables started, neither waited"


def test_a_game_that_raises_does_not_take_the_others_with_it(monkeypatch, tmp_path, capsys):
    def boom(table, invite, **kw):
        raise RuntimeError("the hub blinked")

    monkeypatch.setattr(run_game, "play", boom)
    table = Table(id="g9", traders=2, episodes=1, rounds=1, opened_at=0.0,
                  settled=True, seed=1, workspace="w9")

    run_game._play_table(table, "invite", episode_seconds=1, ack_seconds=1,
                         out=tmp_path, ledger=None)  # must not raise

    assert "g9: game failed" in capsys.readouterr().out
