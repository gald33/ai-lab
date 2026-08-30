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
import os
import sys
import time
from pathlib import Path
from unittest import mock

import pytest
from switchboard import signing
from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from games.island import live, npc, run_game
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

    # A table of agents says so by saying nothing: the flag has to default to
    # absent, or every game recorded before NPCs existed would be held out of
    # the ranking retrospectively.
    assert record["rounds"][0]["npcs"] == {}

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


def test_the_lobby_reads_sealability_off_the_roster_not_off_the_join(settled):
    """What a seat can be sealed to is what its client published when it
    registered -- not something it asserted on a JOIN line.

    Since `whisper` shipped, `register()` publishes an exchange key for every
    ordinary client, so a seat that could be witnessed at all can normally be
    sealed to. The lobby says so at settlement as a courtesy; the manager
    checks it again in the table's own room, which is where it decides
    anything (`run_game.sealable`).
    """
    lobby, table, _seated, _key = settled

    assert table.sealable(), "registered seats publish an exchange key"
    assert set(table.boxes) == set(table.seats)
    lines = [m["body"] for m in lobby.client.history("lobby")]
    full = next(b for b in lines if b.startswith("g1 is full"))
    assert "PRACTICE" not in full
    assert any("sealed" in b for b in lines if b.startswith("g1 seat"))


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


# --- the sealed round, through `whisper` --------------------------------------
#
# Rewritten 2026-08-26. It used to drive `island/sealed.py`, a stopgap that
# sealed to a key each seat posted on the lobby board with `box=`. Switchboard
# released it, so the key is the entrant's own published `exchange_key` and
# the sealing is Switchboard's. The property under test did not change: no
# taste and no share ever reaches the board.

@pytest.fixture
def sealed_table(hub, identities):
    """A settled table whose seats are ordinary registered clients.

    Nothing is offered on the JOIN line any more -- publishing an exchange key
    is what `register()` does, so a seat is sealable by being an ordinary
    Switchboard client and nothing else. That is the whole improvement.
    """
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=1 rounds=1")
    lobby.drain()

    for agent_id, name in (("t1", "scout-v2"), ("t2", "trader-b")):
        client = _client(hub, agent_id, key)
        client.register(name=agent_id, kind="local", branch="main", task="")
        client.post("lobby", f"JOIN g1 as {name}")
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")
    manager.post("lobby", "MANAGE g1")
    lobby.drain()

    table = lobby.tables["g1"]
    assert table.settled
    return lobby, table


def test_a_sealed_round_keeps_tastes_and_shares_off_the_board(sealed_table, tmp_path):
    """The property the whole private channel exists for, end to end.

    Nothing a spectator can read tells them a taste or a share -- and the
    capacity leak closes with them, because capacity is the receipt's quantity
    divided by the share and the share never reaches the board.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    lobby, table = sealed_table
    invite = run_game.pending_invite(lobby, table)
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")
        client.agents()          # both sides read the roster before sealing

    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    manager_client = Client.from_invite(invite, agent_id=MANAGER)
    # The manager publishes an exchange key too: sealing is pairwise, and a
    # seat opens what was sealed to it with the *sender's* key.
    manager_client.register(name=MANAGER, kind="local", branch="main", task="")
    for client in room.values():
        client.agents()
    mgr = Manager(capacity=dealer.capacity, client=manager_client,
                  channel="island", goods=dealer.goods)
    assert run_game.bind_seats(mgr, table) == {"T1", "T2"}
    assert run_game.sealable(mgr), "both seats published an exchange key"

    assert run_game.deal(mgr, dealer, table) is True

    # Each seat opens its own half out of its inbox; the other seat never sees
    # it at all -- a `whisper` is delivered to one peer's channel.
    mine = [m["body"] for m in room["scout-v2"].inbox()]
    assert any(isinstance(b, str) and b.startswith("You are T1") for b in mine)
    theirs = [str(m.get("body")) for m in room["trader-b"].inbox()]
    assert not any("You are T1" in b for b in theirs)

    # A sealed PRODUCE settles: sent with `whisper`, read out of the manager's
    # inbox, and the plan never reaches the board.
    mgr.open_episode()
    room["scout-v2"].whisper(mgr.client.agent_id, "PRODUCE bread=0.5 iron=0.5")
    room["trader-b"].whisper(mgr.client.agent_id, "PRODUCE cloth=1.0")
    mgr.drain()

    assert mgr.refused == 0
    assert mgr.sealed_in == 2
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


def test_a_practice_table_is_dealt_in_the_clear_and_says_so(hub, identities):
    """A seat whose client publishes no exchange key cannot be sealed to, and
    the table says that on its own board rather than quietly playing on."""
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    _client(hub, "opener", key).post("lobby", "OPEN traders=2 episodes=1 rounds=1")
    lobby.drain()
    for agent_id, name in (("t1", "scout-v2"), ("t2", "trader-b")):
        c = _client(hub, agent_id, key)
        c.register(name=agent_id, kind="local", branch="main", task="")
        c.post("lobby", f"JOIN g1 as {name}")
    m = _client(hub, "m", key)
    m.register(name="lucille", kind="local", branch="main", task="")
    m.post("lobby", "MANAGE g1")
    lobby.drain()
    table = lobby.tables["g1"]
    invite = run_game.pending_invite(lobby, table)

    # Only one seat turns up in the room, so `sealable` is empty.
    only = Client.from_invite(invite, agent_id="t1")
    only.register(name="scout-v2", kind="local", branch="main", task="")
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity,
                  client=Client.from_invite(invite, agent_id=MANAGER),
                  channel="island", goods=dealer.goods)
    run_game.bind_seats(mgr, table)

    assert run_game.deal(mgr, dealer, table) is False
    board = " ".join(str(m["body"]) for m in mgr.client.history("island"))
    assert "PRACTICE" in board and "Nothing here is ranked" in board

def test_a_sealed_blob_posted_on_the_board_is_refused_with_the_way_to_send_it():
    """Sealed payloads used to ride the board under a `SEALED` marker. They do
    not any more -- `whisper` delivers them to the manager's own channel -- so a
    blob here settles nothing, and the refusal says what to do instead rather
    than leaving an entrant to guess."""
    from island.dealer import GOODS, Dealer
    from island.manager import Manager

    m = Manager(capacity=Dealer.draw(1, 2, GOODS).capacity,
                client=_FakeRoom(), channel="island", goods=GOODS,
                names=("T1", "T2"))
    m.bind("peer-t1", "T1")
    m.open_episode()

    m._consider("T1", "SEALED abcdefghijklmnop")

    assert m.refused == 1
    assert m.refusals[0]["kind"] == "sealed"
    assert m.refusals[0]["line"] == "<sealed>", "never keep the ciphertext"
    assert "whisper" in m.refusals[0]["reason"]
    assert not m.holders["T1"].produced


class _FakeRoom:
    """The two calls a Manager makes when nothing is being drained."""

    def __init__(self) -> None:
        self.said: list[str] = []

    def post(self, channel: str, body: str) -> None:
        self.said.append(body)

    def history(self, channel: str, **kw) -> list:
        return []

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

    lobby = _StubLobby(tables)
    monkeypatch.setattr(run_game, "pending_invite", lambda lobby, table: "invite")
    watcher = threading.Thread(
        target=run_game.watch,
        args=(lobby,),
        kwargs={"every": 0.05, "episode_seconds": 1, "ack_seconds": 1,
                "out": tmp_path},
        daemon=True)
    watcher.start()
    for _ in range(100):
        if len(started) == 2:
            break
        time.sleep(0.05)
    release.set()
    lobby.stood_down = True
    watcher.join(timeout=5)          # let the watcher end with its test
    watcher.join(timeout=5)

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


def test_the_manager_names_the_seats_before_anybody_speaks():
    """The room is not the table: the invite was posted on a lobby board, so
    strangers may be here. The manager cannot silence them and says so."""
    table = Table(id="g1", traders=2, episodes=1, rounds=1, opened_at=0.0,
                  seats={"p1": "scout-v2", "p2": "trader-b"},
                  keys={"p1": "key-one", "p2": "key-two"})

    said = run_game.who_is_at_this_table(table)

    assert "T1 = scout-v2 (key key-one)" in said
    assert "T2 = trader-b (key key-two)" in said
    assert "settles nothing" in said and "no standing" in said


def test_a_table_says_the_same_thing_with_one_seat_missing():
    """A seat that never bound is not a reason to say nothing about the rest."""
    table = Table(id="g1", traders=2, episodes=1, rounds=1, opened_at=0.0,
                  seats={"p1": "scout-v2"}, keys={})

    said = run_game.who_is_at_this_table(table)

    assert "T1 = scout-v2 (key ?)" in said


def test_no_more_tables_play_at_once_than_the_cap(monkeypatch, tmp_path):
    """The lab pays for the manager of every table that settles, and OPEN is
    free to whoever writes it. Without a cap the bill is set by strangers."""
    import threading
    running, release = [], threading.Event()

    def slow_play(table, invite, **kw):
        running.append(table.id)
        release.wait(5)
        return {"players": {}, "rounds": []}

    monkeypatch.setattr(run_game, "play", slow_play)
    monkeypatch.setattr(run_game, "publish", lambda *a, **k: tmp_path / "x.json")
    monkeypatch.setattr(run_game._scores, "ingest", lambda *a, **k: ([], None))
    monkeypatch.setattr(run_game, "pending_invite", lambda lobby, table: "invite")

    tables = {f"g{i}": Table(id=f"g{i}", traders=2, episodes=1, rounds=1,
                             opened_at=0.0, settled=True, seed=1,
                             workspace=f"w{i}") for i in (1, 2, 3, 4)}

    lobby = _StubLobby(tables)
    watcher = threading.Thread(
        target=run_game.watch, args=(lobby,),
        kwargs={"every": 0.05, "episode_seconds": 1, "ack_seconds": 1,
                "out": tmp_path, "max_concurrent": 2}, daemon=True)
    watcher.start()
    for _ in range(60):
        if len(running) >= 2:
            break
        time.sleep(0.05)
    time.sleep(0.5)

    assert len(running) == 2, f"the cap held: {running}"
    release.set()
    lobby.stood_down = True
    watcher.join(timeout=5)


class _StubLobby:
    """A lobby with tables and nothing else, and a way to stop the watcher.

    `watch` never returns on its own, so a test that starts one has to be able
    to end it -- a thread left running outlives its own test and reaches into
    the next one's unpatched code, which is exactly the kind of failure that
    gets blamed on the next test.
    """

    def __init__(self, tables: dict, stop_after: int | None = None) -> None:
        self.tables = tables
        self.stood_down = False
        self._stop_after = stop_after
        self._drains = 0

    def drain(self) -> None:
        self._drains += 1
        if self._stop_after is not None and self._drains >= self._stop_after:
            self.stood_down = True


def test_the_runner_writes_the_lobby_page_because_nothing_else_can(monkeypatch, tmp_path):
    """`run_lobby --page` cannot be the answer: it would be a second lobby on
    the channel, and one of the two would stand down.

    Driven synchronously -- the stub stands down after one drain, so `watch`
    writes the page and returns. A thread here would be testing the scheduler.
    """
    page = tmp_path / "lobby.html"
    monkeypatch.setattr(run_game, "write_page",
                        lambda lob, path, **kw: path.write_text("<!doctype html>rendered"))

    run_game.watch(_StubLobby({}, stop_after=1), every=0, episode_seconds=1,
                   ack_seconds=1, out=tmp_path, page=page)

    assert page.read_text().startswith("<!doctype html>")


def test_a_page_that_cannot_be_written_does_not_stop_the_runner(monkeypatch, tmp_path, capsys):
    """A page is not a game. If rendering throws -- a full disk, a bad path --
    the tables still play and the fault is said out loud."""
    def boom(lobby, path, **kw):
        raise OSError("no space left on device")

    monkeypatch.setattr(run_game, "write_page", boom)

    run_game.watch(_StubLobby({}, stop_after=1), every=0, episode_seconds=1,
                   ack_seconds=1, out=tmp_path, page=tmp_path / "lobby.html")

    assert "lobby page not written" in capsys.readouterr().out



def _finished_game(out, gid, workspace, when):
    (out / f"{gid}.json").write_text(json.dumps(
        {"rounds": [{"workspace": workspace}]}))
    (out / f"board-{workspace}.json").write_text("{}")
    (out / f"reveal-{workspace}.json").write_text("{}")
    for name in (f"{gid}.json", f"board-{workspace}.json", f"reveal-{workspace}.json"):
        os.utime(out / name, (when, when))


def test_pruning_drops_the_bulk_of_old_games_and_keeps_the_newest(tmp_path):
    """The board and replay of a finished game are the only thing here that
    grows without limit, and a disk that fills stops the lobby."""
    for i, gid in enumerate(("g1", "g2", "g3", "g4")):
        _finished_game(tmp_path, gid, f"w{i}", 1_000_000 + i)

    dropped = run_game.prune(tmp_path, keep=2)

    left = sorted(p.name for p in tmp_path.iterdir())
    assert left == ["board-w2.json", "board-w3.json", "g3.json", "g4.json",
                    "reveal-w2.json", "reveal-w3.json"]
    assert len(dropped) == 6


def test_pruning_leaves_a_game_that_never_finished_alone(tmp_path):
    """A board with no record beside it is a game that did not finish, not a
    game to tidy away."""
    _finished_game(tmp_path, "g1", "w1", 1_000_000)
    (tmp_path / "board-w9.json").write_text("{}")

    run_game.prune(tmp_path, keep=0)          # 0 keeps everything
    assert (tmp_path / "g1.json").exists()

    run_game.prune(tmp_path, keep=1)
    assert (tmp_path / "board-w9.json").exists(), "an unfinished game is left"


def test_pruning_never_touches_the_ledger(tmp_path):
    """A pruned game is still counted and still in every denominator."""
    _finished_game(tmp_path, "g1", "w1", 1_000_000)
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text('{"round_id": "r1"}\n')

    run_game.prune(tmp_path, keep=1)
    assert ledger.read_text() == '{"round_id": "r1"}\n'


def test_a_real_room_gets_a_second_copy_and_the_two_agree(settled, hub, tmp_path):
    """Condition 3, end to end against a real hub.

    The archivist is built the way the runner builds it, reads the room the
    way the runner reads it, and its copy is compared with the manager's the
    way the runner compares them. What is asserted is that it saw the game --
    an archive of an empty room agrees with everything and is worth nothing.
    """
    from games.island import archive as _archive

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")

    # A stranger manages this table, so the copy is the independent kind.
    archivist = run_game.archivist_for(table, invite, lab_manages=False)
    assert archivist.standing == _archive.INDEPENDENT

    record, board = _play_scripted(table, invite, room, tmp_path)
    archivist.catch_up()
    archivist.close()

    saved = json.loads(archivist.save(tmp_path, table.workspace).read_text())
    assert saved["lines"] > 5, "it watched a game, not an empty room"
    assert saved["writer"] == table.manager
    assert saved["failed_polls"] == 0

    diff = _archive.compare(json.loads(board.read_text()), archivist.payload())
    assert diff["missing"] == [], "nothing the room said is absent from the board"
    assert diff["altered"] == []
    assert diff["unexplained_extra"] == []


def test_the_archivist_takes_no_seat_and_is_refused_if_it_speaks(settled, hub, tmp_path):
    """It reads. A witness that could write would be a player."""
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    archivist = run_game.archivist_for(table, invite, lab_manages=True)

    client = Client.from_invite(invite, agent_id=MANAGER)
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    run_game.bind_seats(mgr, table)
    mgr.open_episode()

    archivist.client.post("island", "PRODUCE bread=1.0")
    mgr.drain()

    assert mgr.intrusions, "a line from a key that took no seat is recorded"
    assert run_game.ARCHIVIST not in {s for s in mgr.names}


def test_the_archivist_in_the_room_does_not_cost_a_table_its_ranking(settled, hub, tmp_path):
    """A third member of the room must not turn a ranked game into a practice one.

    `sealable` answers "can this table seal?" from who turned up, so an extra
    body on the roster is exactly the shape of thing that could silently
    downgrade a round -- and a silent downgrade is the worst failure this
    design has, because the game still plays and simply stops counting.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")

    client = Client.from_invite(invite, agent_id=MANAGER)
    client.register(name=MANAGER, kind="local", branch="main", task="running")
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    run_game.bind_seats(mgr, table)
    assert run_game.sealable(mgr), "sealable before the archivist arrives"

    run_game.archivist_for(table, invite, lab_manages=True)
    run_game.bind_seats(mgr, table)

    assert run_game.sealable(mgr), "and still sealable with it watching"


def test_a_vanishing_move_is_answered_every_time(settled, hub, tmp_path):
    """The gap the first real entrant fell into, reported in their own words.

    They whispered a correctly formed PRODUCE three times from a client whose
    key their seat was not bound to. Each one settled nothing and each one got
    silence: the once-per-key notice had gone out three episodes earlier and
    read as a note about somebody else. Chatter still gets one line per key --
    a stranger writing ten lines must not make the manager write ten more --
    but a move is answered every time, because a move vanishing is the thing
    its author cannot see.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    stranger = Client.from_invite(invite, agent_id="not-a-seat")
    stranger.register(name="not-a-seat", kind="local", branch="m", task="")

    client = Client.from_invite(invite, agent_id=MANAGER)
    client.register(name=MANAGER, kind="local", branch="main", task="")
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    run_game.bind_seats(mgr, table)
    mgr.open_episode()

    def said():
        return [str(m.get("body", "")) for m in mgr.client.history("island", limit=200)]

    # Chatter: one notice, and no more however often it repeats.
    stranger.post("island", "hello, is this the island?")
    stranger.post("island", "hello again")
    mgr.drain()
    assert sum("took no seat" in b for b in said()) == 1

    # A move: answered on its own terms, every single time -- and answered to
    # the writer rather than to the room, because a refusal is addressed to
    # whoever wrote the line and the board does not need it.
    stranger.agents()          # both sides read the roster before sealing
    mgr.client.agents()
    stranger.post("island", "PRODUCE salt=0.70 iron=0.30")
    mgr.drain()
    stranger.post("island", "PRODUCE salt=0.70 iron=0.30")
    mgr.drain()

    got = [str(m.get("body", "")) for m in stranger.inbox()]
    receipts = [b for b in got if "settled nothing" in b]
    assert len(receipts) == 2, "a move that vanished is answered each time"
    assert "PRODUCE" in receipts[0]
    # And it says what to do, not merely that something is wrong.
    assert "the same one the lobby saw" in receipts[0]
    # The board carries the company notice and nothing else about it.
    assert not [b for b in said() if "settled nothing" in b], (
        "a receipt addressed to one writer does not belong on the board")


def test_a_private_refusal_leaves_a_public_pointer_and_no_reason(settled, hub, tmp_path):
    """A whisper announces itself to some agents and not others.

    Switchboard's MCP layer bumps presence on every tool call and returns
    `unread_dms`, so an agent holding those tools sees a counter rise without
    ever opening its inbox. The CLI returns the message record and no count --
    and both entrants who played here used the CLI. So the reason goes
    privately and a pointer stays public: the fact of a refusal, which the
    board already showed, and none of its content, which it never should have.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)

    # **The manager registers first, as `play` does.** Sealing is pairwise: a
    # trader that reads the roster before the manager is on it cannot open
    # what the manager seals, and receives an envelope rather than a reason.
    client = Client.from_invite(invite, agent_id=MANAGER)
    client.register(name=MANAGER, kind="local", branch="main", task="")

    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, c in room.items():
        c.register(name=name, kind="local", branch="main", task="trading")
        c.agents()
    client.agents()
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    run_game.bind_seats(mgr, table)
    mgr.open_episode()

    room["scout-v2"].post("island", "PRODUCE bread=9.0 iron=9.0")   # over budget
    mgr.drain()

    board = [str(m.get("body", "")) for m in mgr.client.history("island", limit=50)]
    pointer = [b for b in board if "read your inbox" in b]
    assert len(pointer) == 1, "the board says something is waiting"
    assert "T1" in pointer[0]

    # The reason itself never reaches the board.
    private = [str(m.get("body", "")) for m in room["scout-v2"].inbox()]
    assert any("not settled" in b for b in private), "the reason is whispered"
    reason = next(b for b in private if "not settled" in b)
    assert reason.split("not settled: ", 1)[1][:20] not in " ".join(board)

    # **Per failure, not once per episode.** g3 showed why: a trader spent its
    # one pointer early, then approved against stock the bell had consumed,
    # and the board said nothing -- so it went on negotiating from a holding
    # it never received.
    from island.manager import POINTERS_PER_EPISODE

    room["scout-v2"].post("island", "PRODUCE bread=9.0 iron=9.0")
    mgr.drain()
    board = [str(m.get("body", "")) for m in mgr.client.history("island", limit=80)]
    assert len([b for b in board if "read your inbox" in b]) == 2, (
        "a second failure in one episode is told about")

    # Capped, so a stranger writing ten lines cannot make the manager write ten.
    for _ in range(4):
        room["scout-v2"].post("island", "PRODUCE bread=9.0 iron=9.0")
        mgr.drain()
    board = [str(m.get("body", "")) for m in mgr.client.history("island", limit=80)]
    assert len([b for b in board if "read your inbox" in b]) == POINTERS_PER_EPISODE

    # A new episode restores the allowance.
    mgr.close_episode(); mgr.open_episode()
    room["scout-v2"].post("island", "PRODUCE bread=9.0 iron=9.0")
    mgr.drain()
    board = [str(m.get("body", "")) for m in mgr.client.history("island", limit=80)]
    assert len([b for b in board if "read your inbox" in b]) == POINTERS_PER_EPISODE + 1


def test_the_manager_stays_on_the_roster_for_the_whole_round(settled, hub, tmp_path):
    """Reported by the trader in g3, who blamed its own setup for it.

    Registration lapses in about two minutes and a round runs eight. A manager
    that registers once is absent from the roster for most of its own game --
    and a peer that is not on the roster cannot be whispered to, because
    sealing needs its exchange key from there. So every sealed PRODUCE after
    the first couple of minutes had nowhere to go, which is exactly what they
    saw: "one early whisper worked and later ones failed".
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    client = Client.from_invite(invite, agent_id=MANAGER)
    client.register(name=MANAGER, kind="local", branch="main", task="")
    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)

    beats: list[bool] = []

    class _Counting:
        def __getattr__(self, name):
            return getattr(client, name)

        def heartbeat(self, **kw):
            beats.append(kw.get("renew_leases"))
            return client.heartbeat(**kw)

    run_game._stay_present(_Counting())
    run_game._stay_present(_Counting())

    assert len(beats) == 2, "presence is refreshed every drain, not once"
    assert beats == [False, False], (
        "and never renews leases: an unrelated op renewing every held lease "
        "would be a real behaviour change, per Switchboard's own reasoning")


def test_a_manager_that_cannot_reach_the_hub_keeps_playing(settled, hub, tmp_path):
    """A failed heartbeat may cost reachability. A raised one costs the round."""
    class _Broken:
        def heartbeat(self, **kw):
            raise RuntimeError("hub blinked")

    run_game._stay_present(_Broken())      # must not raise


def test_the_board_carries_the_grammar_it_settles():
    """g3's traders had read the brief and still guessed.

    A document read once before a round is not where an agent checks itself
    mid-round -- the room is. So the three shapes, and the four things that
    cost whole episodes, are said on the board where a trader is looking.
    """
    said = run_game.house_rules()

    assert "PRODUCE bread=0.5 iron=0.5" in said
    assert "PROPOSE to=T2 give=iron:0.4 want=salt:0.3" in said
    assert "APPROVE p3" in said
    # The four that actually cost episodes, each in its own words.
    assert "consumed at each bell" in said
    assert "open offer reserves" in said
    assert "inside one episode" in said
    assert "announcements are not input" in said


def test_an_offer_names_the_command_that_accepts_it(settled, hub, tmp_path):
    """A trader copied this line's shape back as input and lost four episodes.

    The prefix is unchanged because `verify.OFFER` parses it and every saved
    board must stay checkable; the fix is the tail, which names the one thing
    the reader should write next.
    """
    from island.dealer import GOODS, Dealer
    from island.manager import MANAGER, Manager
    from games.island import verify

    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    client = Client.from_invite(invite, agent_id=MANAGER)
    client.register(name=MANAGER, kind="local", branch="main", task="")
    room = {n: Client.from_invite(invite, agent_id=a)
            for n, a in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for n, c in room.items():
        c.register(name=n, kind="local", branch="main", task="trading")

    dealer = Dealer.draw(table.seed, table.traders, GOODS)
    mgr = Manager(capacity=dealer.capacity, client=client, channel="island",
                  goods=dealer.goods)
    # Bound before every drain, which is what `run_game.until` does and what
    # `bind_seats` asks for in its own docstring: a seat binds only once its
    # holder's registration has been *read*, so a single bind before a single
    # drain is one roster read away from a trader the manager never recognises.
    # An unbound holder of a witnessed key is dropped in silence by design
    # (`Manager._intrusion`: "it binds on a later drain"), so that race shows up
    # here as a board with no offer line on it at all -- which is how it showed
    # up, once, in CI on 2026-08-30 -- and never here, in 15 runs of this test
    # alone and 2 of the whole directory, on agent-switchboard 1.2.3, the
    # version CI installs. The bind is the fix; the count is why it is not a
    # reproduction.
    def turn(line: str) -> None:
        room["scout-v2"].post("island", line)
        for _ in range(5):
            run_game.bind_seats(mgr, table)
            mgr.drain()

    run_game.bind_seats(mgr, table)
    mgr.open_episode()
    turn("PRODUCE bread=1.0")
    turn("PROPOSE to=T2 give=bread:0.1 want=cloth:0.2")

    board = [str(m.get("body", "")) for m in mgr.client.history("island", limit=60)]
    offer = next((b for b in board if b.startswith("p1: ")), "")
    assert offer, "the proposal was settled and the offer posted:\n" + "\n".join(board)

    assert "APPROVE p1" in offer, "the line says what to write next"
    assert verify.OFFER.match(offer), "and stays parseable for saved boards"


def test_presence_ttl_covers_the_whole_round_and_then_some():
    """The manager asks to stay listed for longer than it plays.

    A round is not over at its last bell: the record is written and the
    archive compared after it, and a manager doing that is still a peer
    somebody may be trying to whisper to.
    """
    table = Table(id="g1", traders=2, episodes=8, rounds=1, opened_at=0.0)
    ttl = run_game.presence_ttl(table, episode_seconds=60, ack_seconds=120)
    played = 120 + 8 * 60
    assert ttl > played
    assert ttl == played + 120


def test_presence_ttl_clamps_here_rather_than_trusting_the_hub():
    """**The hub clamps at 3600 and says nothing.** So we clamp first.

    Measured 2026-08-28: `--ttl 86400` comes back as 3599 with the same
    success line as `--ttl 900`. Code that asks for more than the ceiling is
    code whose model of its own presence is wrong, and nothing will tell it.
    See `games/switchboard-what-an-entrant-already-holds.md` section 6.
    """
    huge = Table(id="g2", traders=2, episodes=500, rounds=1, opened_at=0.0)
    assert run_game.presence_ttl(
        huge, episode_seconds=60, ack_seconds=120) == run_game.PRESENCE_CEILING
    assert run_game.PRESENCE_CEILING == 3600.0


# --- the latest and the best --------------------------------------------------

def test_a_good_old_game_survives_a_run_of_newer_ones(tmp_path):
    """Retention is the union of two sets, so being good is a way to survive
    ceasing to be recent. The verdict comes from the ledger, which is where
    every game's score lives -- a game's own file does not know how it did."""
    out = tmp_path / "out"
    out.mkdir()
    for i, gid in enumerate(("g1", "g2", "g3")):
        _finished_game(out, gid, f"w{i}", 1_000_000 + i)

    spared = {"g1"}                      # the ledger's verdict, mocked at its seam
    with mock.patch.object(run_game._scores, "load", return_value=[]), \
         mock.patch.object(run_game._scores, "keepers", return_value=spared):
        dropped = run_game.prune(out, keep=0, best=5, ledger=tmp_path / "l.jsonl")

    left = sorted(p.name for p in out.iterdir())
    assert left == ["board-w0.json", "g1.json", "reveal-w0.json"]
    assert len(dropped) == 6, ("two games went, and each was a record, "
                               "a board and a reveal")


def test_a_ledger_that_cannot_be_read_prunes_nothing(tmp_path):
    """"Cannot judge" reads as "keep". Deleting on a failed read would make an
    unreachable ledger delete the archive it exists to describe."""
    out = tmp_path / "out"
    out.mkdir()
    _finished_game(out, "g1", "w1", 1_000_000)

    with mock.patch.object(run_game._scores, "load",
                           side_effect=OSError("no ledger here")):
        dropped = run_game.prune(out, keep=0, best=5, ledger=tmp_path / "gone.jsonl")

    assert dropped == []
    assert (out / "g1.json").exists()


def test_pruning_lets_the_spectator_s_copies_go_and_says_so(tmp_path):
    """The files a link names go with the record, and the archive index keeps
    a row saying the game was played -- never a link that fails into silence."""
    out = tmp_path / "out"
    live_dir = tmp_path / "live"
    out.mkdir()
    live_dir.mkdir()
    _finished_game(out, "g1", "w1", 1_000_000)
    (live_dir / "g1.json").write_text(json.dumps({"channel": "island", "messages": []}))
    (out / "board-w1.json").write_text("{}")
    live.finish(live_dir / "g1.json", board=out / "board-w1.json",
                reveal=out / "reveal-w1.json")

    with mock.patch.object(run_game._scores, "load", return_value=[]), \
         mock.patch.object(run_game._scores, "keepers", return_value=set()):
        run_game.prune(out, keep=0, best=5, ledger=tmp_path / "l.jsonl",
                       live_dir=live_dir)

    assert not (live_dir / "board-g1.json").exists()
    row = json.loads((live_dir / live.INDEX).read_text())["games"][0]
    assert row["kept"] is False, "the game vanished instead of being marked gone"


def test_a_seat_that_declared_itself_a_heuristic_costs_the_game_its_ranking(
        settled, hub, tmp_path):
    """The record names the NPCs and holds the game out, and it learns both
    from the board rather than from whoever launched anybody.

    That matters because the manager does not know what started a seat and
    must not have to: a game re-read from its board next year has to reach the
    same answer this does.
    """
    lobby, table, seated, key = settled
    invite = run_game.pending_invite(lobby, table)
    room = {name: Client.from_invite(invite, agent_id=aid)
            for name, aid in (("scout-v2", "t1"), ("trader-b", "t2"))}
    for name, client in room.items():
        client.register(name=name, kind="local", branch="main", task="trading")

    room["trader-b"].post("island", npc.declaration(
        "trader-b", npc.parse_mix("autarky=1,greedy=1")))
    record, _ = _play_scripted(table, invite, room, tmp_path)

    assert record["rounds"][0]["npcs"] == {
        "trader-b": "autarky=0.5, greedy=0.5"}
    assert record["practice"] is True


def test_the_record_carries_the_clock_the_table_settled_on():
    """**The record said nothing about episode length, and the board ranked on it.**

    Until this field existed the only trace of how long an episode ran was
    prose inside a board message -- so a 60s game and a 120s game were the
    same level and competed for the same best. 002 measured that difference
    moving `capture` from -1.42 to -0.41.
    """
    table = Table(id="g1", traders=2, episodes=2, rounds=1, opened_at=0.0,
                  seconds=120)
    assert table.seconds == 120


def test_a_table_settled_before_the_field_existed_still_runs_at_sixty():
    """The dataclass default is not a fresh choice: it is what g1..g6 ran at,
    so a table pickled before `seconds` existed plays exactly as it did."""
    assert Table(id="g2", traders=2, episodes=2, rounds=1,
                 opened_at=0.0).seconds == 60


# --- the manager checks the table in front of it ----------------------------


def test_the_manager_refuses_a_table_of_a_size_it_has_never_played():
    """**Checked here as well as at the lobby's format, on purpose.**

    `protocol` refuses a badly-sized OPEN to the entrant's face, which is the
    right place for it. But the manager also plays tables it did not parse:
    ones restored from a state file written before these bounds existed, and
    ones a caller built by hand. Dealing an island for a size nothing here has
    run would fail as a game rather than as a message.
    """
    ok = Table(id="g1", traders=2, episodes=4, rounds=1, opened_at=0.0)
    run_game.refuse_out_of_bounds(ok)  # the sizes that are played

    for bad, says in (
        (Table(id="g2", traders=5, episodes=4, rounds=1, opened_at=0.0), "2-4"),
        (Table(id="g3", traders=2, episodes=4, rounds=1, opened_at=0.0,
               goods=6), "goods"),
        (Table(id="g4", traders=2, episodes=4, rounds=3, opened_at=0.0),
         "one round"),
        (Table(id="g5", traders=2, episodes=0, rounds=1, opened_at=0.0),
         "no episodes"),
    ):
        with pytest.raises(ValueError) as e:
            run_game.refuse_out_of_bounds(bad)
        assert says in str(e.value)
