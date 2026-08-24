"""Put this experiment's own package on the path for pytest, the same fix
`experiments/002-barter-conventions/experiment/conftest.py` uses -- and a real
hub on a real port, for the one test here that needs Switchboard's own signing
and verification rather than an assumption about how they behave.

    python -m pytest experiments/005-deliberation-protocol/island/tests/ -q

Run scoped to this path, the way every test suite in this repo is invoked --
there is no combined runner. That matters here specifically: `games/island/`
is also a top-level package named `island`, for the same reason this one is
(it names its own domain). Running both in one pytest process would have the
second import of `island` resolve to whichever loaded first; run them
separately, as documented.
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
