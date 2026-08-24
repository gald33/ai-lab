"""`Manager.bind`'s witnessed-key half, against a real hub.

Two different `Client`s configured with the same `agent_id` string blind to
the same hub-form peer id -- confirmed against the real cipher, not assumed --
so `msg["from"]` alone cannot tell them apart. Each still signs with its own
process's key, which is exactly the gap `games/island.md`'s "Seats, and who
is in one" names: `bind(..., key=...)` closes it, and this is the imposture
scenario it exists for.

Every existing caller -- `run_v3.py` included -- calls `bind()` with no key,
so the other half of this file is the boring one: confirm that path stays
exactly as it was.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]
                       / "002-barter-conventions" / "experiment"))
from barter.economy import draw_island  # noqa: E402

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from island.manager import Manager

GOODS = ("bread", "cloth", "iron", "salt")
WORKSPACE = "w_manager-keys"


def _client(hub, agent_id, key):
    return Client(ClientConfig(url=hub, url_source="explicit",
                               workspace=WORKSPACE, key=key), agent_id=agent_id)


def _manager(hub, key):
    island = draw_island(n_agents=2, n_goods=4, seed=1)
    return Manager(island=island, client=_client(hub, "manager", key),
                   channel="island", goods=GOODS, names=("T1", "T2"))


def test_an_unkeyed_bind_checks_nothing_new(hub):
    """The exact same-apparent-identity, different-key situation the
    imposture test below catches -- except bind() is never given a key here,
    which is every existing 005 caller. Nothing new fires: a fresh keypair
    under the same peer id settles exactly as it always has, which is what
    lets a relaunch mint one without becoming a false imposture report."""
    key = generate_key()
    mgr = _manager(hub, key)
    t2 = _client(hub, "t2", key)
    mgr.bind(t2.agent_id, "T2")   # no key -- the path every existing caller takes

    also_t2 = _client(hub, "t2", key)   # same agent_id string, own keypair
    assert also_t2.agent_id == t2.agent_id
    assert also_t2.public_key != t2.public_key

    mgr.episode_open = True
    also_t2.post("island", "PRODUCE bread=1.0")
    mgr.drain()

    assert mgr.refused == 0
    assert mgr.holders["T2"].produced


def test_a_witnessed_key_lets_the_real_seat_through(hub):
    key = generate_key()
    mgr = _manager(hub, key)
    t2 = _client(hub, "t2", key)
    t2.register(name="T2", kind="local", branch="main", task="")
    mgr.bind(t2.agent_id, "T2", key=t2.public_key)

    mgr.episode_open = True
    t2.post("island", "PRODUCE bread=1.0")
    mgr.drain()

    assert mgr.refused == 0
    assert mgr.holders["T2"].produced


def test_a_different_key_under_the_same_apparent_identity_is_refused(hub):
    """The imposture scenario `games/island.md` names: two Clients built with
    the same agent_id string blind to the same hub-form peer id, so `from`
    cannot tell them apart -- only the signature can."""
    key = generate_key()
    mgr = _manager(hub, key)
    t2 = _client(hub, "t2", key)
    t2.register(name="T2", kind="local", branch="main", task="")
    mgr.bind(t2.agent_id, "T2", key=t2.public_key)

    impostor = _client(hub, "t2", key)   # same agent_id string, own keypair
    assert impostor.agent_id == t2.agent_id
    assert impostor.public_key != t2.public_key

    mgr.episode_open = True
    impostor.post("island", "PRODUCE bread=1.0")
    mgr.drain()

    assert mgr.refused == 1
    assert mgr.refusals[0]["kind"] == "imposture"
    assert mgr.refusals[0]["reason"] == \
        "this did not come from the key T2 took its seat with"
    assert not mgr.holders["T2"].produced

    lines = [m["body"] for m in mgr.client.history("island")]
    assert any(b == "@T2 not settled: this did not come from the key T2 "
                    "took its seat with" for b in lines)
