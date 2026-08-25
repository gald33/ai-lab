"""The entrant's side of the board, against a real hub and no model.

`launch()` spawns a `claude` session and is the one thing here that costs
money, so it is not called: everything it depends on -- the seat claim, the
invite, and above all the one signing identity across two rooms -- is a
separate function precisely so it can be driven without one.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from switchboard import signing
from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key
from switchboard.invite import Invite

from games.island import run_entrant
from games.island.lobby import Lobby

WORKSPACE = "w_entrant-test"


@pytest.fixture
def signer():
    """One signer for `scout-v2`, the way `switchboard-mcp` runs one."""
    server = signing.SigningServer(signing.SigningIdentity.generate(), "scout-v2")
    if not server.start():                                # pragma: no cover
        pytest.skip("no AF_UNIX signer available on this platform")
    yield server
    server.close()


@pytest.fixture
def running_lobby(hub):
    """A lobby draining in the background, the way `run_lobby.py` runs.

    The entrant waits for lines the lobby posts in response to its own, so a
    lobby that only drains when a test remembers to would deadlock the wait
    -- and would be testing a shape that does not exist. In production these
    are two processes; here they are two threads.
    """
    key = generate_key()
    lobby = Lobby(client=_client(hub, "lobby", key))
    stop = threading.Event()

    def pump():
        while not stop.is_set():
            lobby.drain()
            stop.wait(0.05)

    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    yield lobby, key
    stop.set()
    thread.join(timeout=5)


def _client(hub, agent_id, key, workspace=WORKSPACE):
    return Client(ClientConfig(url=hub, url_source="explicit",
                               workspace=workspace, key=key), agent_id=agent_id)


def _entrant(hub, key, name="scout-v2"):
    client = _client(hub, name, key)
    client.register(name=name, kind="local", branch="main", task="")
    return client


def test_one_signing_identity_answers_in_both_rooms(hub, signer):
    """The property the whole entrant is arranged around.

    A seat binds by signing key because a peer id is blinded per workspace --
    so the same agent in the lobby's room and in the table's room must carry
    one key, or the seat never binds and every line it writes is ignored.
    Two clients, two workspaces, one `agent_id`: the ids differ and the key
    does not.
    """
    key = generate_key()
    in_lobby = _client(hub, "scout-v2", key, workspace="w_lobby")
    in_table = _client(hub, "scout-v2", key, workspace="w_table")

    assert in_lobby.agent_id != in_table.agent_id, "peer ids are blinded per room"
    assert in_lobby.public_key == in_table.public_key
    assert in_lobby.public_key == signer.identity.public_key


def test_without_a_signer_the_two_rooms_disagree(hub):
    """The failure the signer prevents, shown rather than asserted about.

    Two bare clients for one agent mint their own keypairs, so the key that
    claimed the seat is not the key that plays it. This is why `main()`
    refuses to continue when it cannot start a signer.
    """
    key = generate_key()
    a = _client(hub, "no-signer", key, workspace="w_lobby")
    b = _client(hub, "no-signer", key, workspace="w_table")

    assert a.public_key != b.public_key


def test_an_entrant_opens_a_table_claims_a_seat_and_is_witnessed(running_lobby, hub, signer):
    lobby, key = running_lobby
    entrant = _entrant(hub, key)

    table, episodes, goods = run_entrant.claim(
        entrant, "lobby", name="scout-v2", table=None, opening=(2, 3, 1),
        goods=5, every=0.05, deadline=time.time() + 10)

    # The goods come back with the rest of the format: the entrant has to brief
    # its agent on the island it is about to sit down at.
    assert (table, episodes, goods) == ("g1", 3, 5)
    deadline = time.time() + 5
    while time.time() < deadline and not lobby.tables.get("g1", None):
        time.sleep(0.05)
    seated = lobby.tables["g1"]
    while time.time() < deadline and not seated.seats:
        time.sleep(0.05)
    assert seated.seats == {entrant.agent_id: "scout-v2"}
    assert seated.keys[entrant.agent_id] == entrant.public_key


def test_a_second_entrant_waits_for_a_table_it_did_not_open(running_lobby, hub, signer):
    """What the other seat does: no --open, no --table, just wait."""
    lobby, key = running_lobby
    opener = _entrant(hub, key)
    run_entrant.claim(opener, "lobby", name="scout-v2", table=None,
                      opening=(2, 3, 1), goods=5, every=0.05,
                      deadline=time.time() + 10)

    second = _client(hub, "trader-b", key)
    second.register(name="trader-b", kind="local", branch="main", task="")
    table, episodes, goods = run_entrant.claim(
        second, "lobby", name="trader-b", table=None, opening=None,
        goods=4, every=0.05, deadline=time.time() + 10)

    # It joined a table it did not open, so the *table's* goods are the ones it
    # gets briefed on -- not the count it happened to be started with.
    assert (table, episodes, goods) == ("g1", 3, 5)
    deadline = time.time() + 5
    while time.time() < deadline and len(lobby.tables["g1"].seats) < 2:
        time.sleep(0.05)
    assert set(lobby.tables["g1"].seats.values()) == {"scout-v2", "trader-b"}


def test_the_invite_arrives_once_the_table_settles(running_lobby, hub, signer):
    lobby, key = running_lobby
    first = _entrant(hub, key)
    run_entrant.claim(first, "lobby", name="scout-v2", table=None,
                      opening=(2, 3, 1), goods=5, every=0.05,
                      deadline=time.time() + 10)
    second = _client(hub, "trader-b", key)
    second.register(name="trader-b", kind="local", branch="main", task="")
    second.post("lobby", "JOIN g1 as trader-b")
    manager = _client(hub, "m", key)
    manager.register(name="lucille", kind="local", branch="main", task="")
    manager.post("lobby", "MANAGE g1")

    invite = run_entrant.wait_for_invite(first, "lobby", "g1", every=0.05,
                                         deadline=time.time() + 10)

    assert isinstance(invite, Invite)
    assert invite.workspace == lobby.tables["g1"].workspace
    assert invite.url == hub


def test_a_refused_seat_is_raised_rather_than_waited_out(running_lobby, hub):
    """A JOIN the lobby refused is not a seat, and the entrant should say so
    now rather than sit out the clock waiting for an invite that is not
    coming. No signer fixture here on purpose: an unregistered peer has no
    witnessable key, which is one of the ways a seat gets refused."""
    lobby, key = running_lobby
    bare = _client(hub, "unregistered", key)
    bare.post("lobby", "OPEN traders=2 episodes=3 rounds=1")
    deadline = time.time() + 5
    while time.time() < deadline and "g1" not in lobby.tables:
        time.sleep(0.05)
    bare.post("lobby", "JOIN g1 as nobody")

    with pytest.raises(SystemExit, match="the lobby refused this seat"):
        run_entrant.wait_for_invite(bare, "lobby", "g1", every=0.05,
                                    deadline=time.time() + 10)


def test_the_prompt_never_carries_the_private_half(hub):
    """`run_v3.py` injects capacities and tastes at spawn because it launches
    every trader itself. This does not, and must not: the manager deals onto
    the board, so the agent reads its own there and this process never learns
    them. One surface."""
    text = run_entrant.instructions("scout-v2", 3)

    # The specific shapes a dealt private half takes -- see Dealer.private_state.
    assert "taste weights:" not in text
    assert "Your production capacity per unit of labour:" not in text
    assert "Nobody else knows either." not in text
    # And it says where to go and get them instead.
    assert "post your own capacities and taste weights" in text
    assert "read the channel and find them" in text


def test_the_prompt_carries_the_island_s_actual_rules(hub):
    """It reads 005's frozen base stimulus rather than paraphrasing it, so the
    grammar an entrant is taught cannot drift from the one the manager
    settles."""
    text = run_entrant.instructions("scout-v2", 3)

    assert "PRODUCE bread=0.5 iron=0.5" in text
    assert "PROPOSE to=T2 give=iron:0.4 want=salt:0.3" in text
    assert "APPROVE p3" in text
    # ...and not the file's repo-facing heading.
    assert "FROZEN" not in text


# --- what a relative workdir does to a launched session --------------------

def test_the_session_is_pointed_at_an_absolute_mcp_config(tmp_path, monkeypatch):
    """The bug a real run found, on both seats, in the first second.

    The session runs with `cwd=home`. A relative `--mcp-config` therefore
    resolves *inside* the directory it already names, and `claude` exits 1
    with "MCP config file not found" at the doubled path -- which on the
    board looks exactly like two traders who joined and then said nothing.
    `--workdir` defaults to a relative `games/entrants`, so this was the
    ordinary case rather than an edge one.
    """
    seen = {}

    class _Popen:
        def __init__(self, argv, **kw):
            seen["argv"], seen["cwd"] = argv, kw.get("cwd")

    monkeypatch.setattr(run_entrant.subprocess, "Popen", _Popen)
    monkeypatch.chdir(tmp_path)

    invite = Invite(url="http://127.0.0.1:1", workspace="w_table",
                    token="t", key=generate_key())
    run_entrant.launch(invite, name="scout-v2", agent_id="t1", episodes=1, goods=4,
                       model="m", workdir=Path("games/entrants"), max_turns=5)

    config = Path(seen["argv"][seen["argv"].index("--mcp-config") + 1])
    assert config.is_absolute(), f"relative config path: {config}"
    assert config.is_file(), "the config has to exist where the session looks"
    # The specific failure: resolved from the session's own cwd, it must be
    # the same file rather than one nested inside it.
    assert (Path(seen["cwd"]) / config).resolve() == config.resolve()


# --- holding the signer against the MCP server's own ------------------------

def test_the_entrant_takes_its_signing_socket_back(tmp_path, monkeypatch):
    """Reproduces the upstream bug that made the first real game unplayable.

    `switchboard-mcp` attaches to a signer already listening for its agent_id
    and then starts a `SigningServer` of its own on the same path, whose
    `start()` unlinks ours first. Its server then proxies to a
    `RemoteSigningIdentity` pointing back at that same path -- it asks itself,
    and every signature times out as "the session's signer did not answer".
    Both seats of game 001 failed exactly this way, on every `say`, while
    reads kept working.

    Here the agent's server is stood up the same way, and the entrant has to
    end up owning the socket again.
    """
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))

    mine = signing.SigningServer(signing.SigningIdentity.generate(), "t1")
    if not mine.start():                                  # pragma: no cover
        pytest.skip("no AF_UNIX signer available on this platform")

    stop = threading.Event()
    try:
        remote = signing.attach("t1")
        assert remote is not None and remote.public_key == mine.identity.public_key

        # What the MCP server does: serve the identity it just attached to,
        # on the very path it attached through.
        theirs = signing.SigningServer(remote, "t1")
        assert theirs.start()
        assert theirs.path == mine.path, "the same socket, which is the bug"

        # Signing now loops back into itself and times out -- the symptom.
        with pytest.raises(OSError):
            remote.sign(b"anything")

        run_entrant.hold_signer(mine, every=0.05, stop=stop)
        for _ in range(100):
            if signing._ask(mine.path, {"op": "pubkey"}) \
                    == {"pubkey": mine.identity.public_key}:
                break
            time.sleep(0.05)

        # Recovered: the socket answers for the key this process actually
        # holds, so a signature completes instead of timing out.
        assert remote.sign(b"anything"), "signing has to work again"
        theirs.close()
    finally:
        stop.set()
        mine.close()
