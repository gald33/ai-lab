"""The cost claims in HOSTING.md, and the one that decides how many tables fit.

`cost.py` measures. This pins the parts a machine cannot change: the shape of
the traffic, and that the harness's own accounting works. Numbers that vary
with the box -- RSS, CPU seconds -- belong in `cost.py`'s output and in
HOSTING.md's table, not in an assertion.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from switchboard.client import Client
from switchboard.config import ClientConfig
from switchboard.crypto import generate_key

from games.island import cost

HOSTING = Path(__file__).resolve().parents[1] / "HOSTING.md"


def _client(hub, agent_id, key=None, workspace="w_cost-test"):
    client = Client(ClientConfig(url=hub, url_source="explicit",
                                 workspace=workspace, key=key),
                    agent_id=agent_id)
    client.register(name=agent_id, kind="local", branch="main", task="")
    return client


def test_every_poll_re_reads_the_whole_board(hub):
    """**The one that decides how many tables a host fits.**

    Nothing here holds a cursor: a drain asks for the last N messages and gets
    them all, every time. So hub traffic is not proportional to what was said
    since the last poll -- it is *polls x board length*, and both terms grow
    with the game. A quiet board is cheap and a long one is not, and the cost
    of a long one is paid by every reader at once.

    Pinned as a test because the number in HOSTING.md is only interesting if
    this is still how reading works. The day something grows a cursor, this
    fails and that table needs rewriting rather than quietly becoming wrong.
    """
    key = generate_key()
    writer = _client(hub, "writer", key)
    reader = _client(hub, "reader", key)

    sizes = []
    for batch in range(3):
        for line in range(10):
            writer.post("island", f"line {batch}-{line} " + "x" * 200)
        sizes.append(len(reader.history("island", limit=500)))

    assert sizes == [10, 20, 30], (
        "each read returned the whole board, so traffic per poll grows with "
        "the game rather than with what was just said")


def test_the_harness_counts_what_the_hub_serves():
    """`cost.py` reports what it counted, so what it counts has to be right:
    one request in, one request counted, bytes both ways."""
    import asyncio

    async def app(scope, receive, send):
        await receive()
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"hello"})

    before = dict(cost.COUNT)
    wrapped = cost.counting(app)

    async def drive():
        await wrapped({"type": "http"},
                      lambda: _body(b"ping"),
                      lambda message: _noop())

    asyncio.run(drive())

    assert cost.COUNT["req"] == before["req"] + 1
    assert cost.COUNT["in"] == before["in"] + len(b"ping")
    assert cost.COUNT["out"] == before["out"] + len(b"hello")


async def _body(payload: bytes) -> dict:
    return {"type": "http.request", "body": payload}


async def _noop() -> None:
    return None


def test_a_lifetimes_worth_of_cpu_is_read_out_of_proc():
    """Cumulative from process start, including the interpreter coming up --
    which is why every CPU figure in HOSTING.md is an upper bound on the
    steady state rather than a flattering one."""
    import os

    rss, cpu = cost.usage(os.getpid())
    assert rss > 1_000_000, "this interpreter is resident"
    assert cpu > 0.0

    # A pid that cannot exist reads as gone rather than raising: the sampler
    # runs against processes that end while it is watching them.
    assert cost.usage(2 ** 22 + 1) is None


def test_hosting_says_what_the_harness_measures():
    """The table in HOSTING.md is `cost.py`'s output. A reader who wants to
    check it needs the command, and it has to be the real one."""
    text = HOSTING.read_text()

    assert "What a game and an NPC actually cost" in text
    assert "games.island.cost" in text or "cost.py" in text
    # The four windows the harness reports are the four rows of the table.
    for row in ("lobby, idle", "a managed game", "one NPC seat", "an agent seat"):
        assert row in text, row


def test_an_npc_seat_is_measured_in_processes_and_an_agent_seat_in_tokens():
    """The comparison the whole exercise is for. It is not that an NPC is
    cheaper by some factor -- it is that the two are billed in different
    units, and only one of them is metered."""
    from games.island import run_entrant

    brief = run_entrant.instructions("scout-v2", 8, 5)
    assert len(brief) > 3000, "an agent seat starts by reading a real brief"
    assert "--max-turns" in Path(run_entrant.__file__).read_text()

    # An NPC's whole decision-making, by contrast, is a pure function of the
    # board that no model ever sees.
    from games.island import npc

    board = npc.Board(player="npc-1", tastes={"bread": 1.0},
                      capacity={"bread": 1.0}, episode_open=True)
    assert npc.lines("greedy", board, []) == ["PRODUCE bread=1.0"]
