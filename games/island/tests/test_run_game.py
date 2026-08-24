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
from pathlib import Path

import pytest
from switchboard import signing
from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from games.island import run_game
from games.island.lobby import Lobby

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
    assert {"seq", "at", "author", "body"} == set(saved["messages"][0])
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
    from island.score import trajectory_from

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


def test_a_ranked_game_is_refused_while_the_private_half_is_public():
    """Practice games run in plaintext and are not ranked -- and asking for a
    ranked one says why rather than quietly producing an unranked row."""
    with pytest.raises(SystemExit) as exc:
        run_game.main(["--ranked", "--hub", "http://127.0.0.1:1"])
    assert "item 2c" in str(exc.value)


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
