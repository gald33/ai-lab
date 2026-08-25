"""Put this experiment's own package on the path for pytest, the same fix
`experiments/002-barter-conventions/experiment/conftest.py` uses -- and a real
hub on a real port, for the one test here that needs Switchboard's own signing
and verification rather than an assumption about how they behave.

    python -m pytest experiments/005-deliberation-protocol/island/tests/ -q

`island` here is the island economy the game runs; the game layer around it is
`games.island`, qualified by its own package rather than being a second
top-level `island`. The two no longer collide, so they can also be run in one
pytest process.
"""

from __future__ import annotations

import socket
import sys
import threading
from pathlib import Path

import pytest

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
