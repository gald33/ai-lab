"""A real hub on a real port, for tests that drive the lobby against it.

Not a mock: `Lobby` reads through `switchboard.client.Client` the same way it
does in production, so the thing under test is exactly the thing that runs --
mocking the client would mean testing an assumption about its behaviour
rather than the behaviour itself.
"""

from __future__ import annotations

import socket
import sys
import threading
from pathlib import Path

import pytest

# `island` sits next to this file's grandparent rather than being installed,
# same reason and same fix as experiments/002's own conftest.py: put its
# package on the path so these tests run from any cwd, not just games/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def hub(tmp_path):
    uvicorn = pytest.importorskip("uvicorn")
    from switchboard.server import create_app
    from switchboard.config import ServerConfig
    from switchboard.store import Store

    port = _free_port()
    store = Store(str(tmp_path / "hub.db"))
    app = create_app(ServerConfig(db_path=store.path), store=store)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(200):
        if server.started:
            break
        threading.Event().wait(0.05)
    else:  # pragma: no cover - only on a very slow machine
        pytest.fail("hub did not start")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
