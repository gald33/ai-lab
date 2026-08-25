"""Which trees the page can serve a replay from, and which it must refuse.

    python -m pytest viewer/tests/test_serve.py -q

`serve.boards()` used to walk exactly one directory, and the second one --
`games/replays/`, where a finished game's board is kept on purpose -- is why
this file exists. Two properties are worth holding onto:

* a board is listed under its root's URL prefix, so the page never learns
  which tree it came from, and `freeze_static.py` writes the same paths the
  live server would answer on;
* a request under one prefix cannot reach out of that root, or into another's.

The listing cache is global to the module, so every test here clears it --
otherwise the first test's answer is every test's answer.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import serve  # noqa: E402


@pytest.fixture
def roots(tmp_path, monkeypatch):
    """Two named roots, neither of them the checkout's."""
    results, replays = tmp_path / "results", tmp_path / "replays"
    results.mkdir()
    replays.mkdir()
    monkeypatch.setattr(serve, "ROOTS", {"results": results, "replays": replays})
    monkeypatch.setattr(serve, "_listing", (0.0, []))
    return results, replays


def board(root: Path, name: str, *, reveal: bool = False, at: float | None = None) -> Path:
    path = root / f"board-{name}.json"
    path.write_text(json.dumps({"messages": []}))
    if reveal:
        (root / f"reveal-{name}.json").write_text(json.dumps({"seed": 1}))
    if at is not None:
        import os
        os.utime(path, (at, at))
    return path


def test_boards_are_listed_from_every_root(roots):
    results, replays = roots
    board(results, "round-a")
    board(replays, "island-game-001d-g1")

    found = {b["label"]: b for b in serve.boards()}

    assert set(found) == {"round-a", "island-game-001d-g1"}
    assert found["round-a"]["board"] == "results/board-round-a.json"
    assert found["island-game-001d-g1"]["board"] == (
        "replays/board-island-game-001d-g1.json")


def test_a_sidecar_is_found_only_where_one_exists(roots):
    results, replays = roots
    board(results, "bare")
    board(replays, "revealed", reveal=True)

    found = {b["label"]: b for b in serve.boards()}

    assert found["bare"]["reveal"] is None
    assert found["revealed"]["reveal"] == "replays/reveal-revealed.json"


def test_a_root_that_does_not_exist_is_skipped_not_refused(roots, tmp_path):
    results, _ = roots
    board(results, "round-a")
    serve.ROOTS["replays"] = tmp_path / "nothing-here"

    assert [b["label"] for b in serve.boards()] == ["round-a"]


def test_newest_first_holds_across_roots(roots):
    """The interesting board is the one that just finished, wherever it lives."""
    results, replays = roots
    now = time.time()
    board(results, "older", at=now - 600)
    board(replays, "newer", at=now)
    board(results, "oldest", at=now - 6000)

    assert [b["label"] for b in serve.boards()] == ["newer", "older", "oldest"]


def test_a_listing_path_resolves_back_to_the_file_it_names(roots):
    """The contract `freeze_static.py` relies on: what is listed is fetchable."""
    _, replays = roots
    written = board(replays, "island-game-001d-g1", reveal=True)
    entry, = serve.boards()

    for rel in (entry["board"], entry["reveal"]):
        prefix, tail = rel.split("/", 1)
        resolved = serve.Handler._under(None, serve.ROOTS[prefix], tail, ".json", ".gz")
        assert resolved is not None and resolved.is_file()
    assert entry["board"].endswith(written.name)


@pytest.mark.parametrize("escape", [
    "../results/board-round-a.json",
    "../../etc/passwd.json",
    "sub/../../results/board-round-a.json",
])
def test_a_request_cannot_climb_out_of_its_root(roots, escape):
    results, replays = roots
    board(results, "round-a")

    assert serve.Handler._under(None, replays, escape, ".json", ".gz") is None


def test_only_replay_file_types_are_served(roots):
    _, replays = roots
    (replays / "notes.md").write_text("not a board")

    assert serve.Handler._under(None, replays, "notes.md", ".json", ".gz") is None
    assert serve.Handler._under(None, replays, "b.json", ".json", ".gz") is not None
    assert serve.Handler._under(None, replays, "b.json.gz", ".json", ".gz") is not None


def test_a_listing_carries_what_each_round_was(tmp_path, monkeypatch):
    """Facets come off the sidecar, so the page can filter by what happened.

    Read, never recomputed -- except welfare, which is the round's utility
    against the sum of its traders' solo optima and needs the trajectory and
    the optima together. Both are in the same file.
    """
    root = tmp_path / "results"
    root.mkdir()
    (root / "board-x.json").write_text(json.dumps({"messages": []}))
    (root / "reveal-x.json").write_text(json.dumps({
        "seed": 4, "agents": 2, "goods": ["bread", "cloth"],
        "autarky_utility": {"T1": 1.0, "T2": 1.0},
        "round": {"arm": "e-plan", "episodes": 2,
                  "trajectory": [[1.0, 1.0], [2.0, 2.0]],
                  "score": {"eff_round": 0.9, "zero_agent_episodes": 1,
                            "agent_episodes": 4}},
    }))
    monkeypatch.setattr(serve, "ROOTS", {"results": root})
    serve._listing = (0.0, [])
    try:
        [entry] = serve.boards()
    finally:
        serve._listing = (0.0, [])

    got = entry["facets"]
    assert got["seed"] == 4 and got["agents"] == 2 and got["goods"] == 2
    assert got["arm"] == "e-plan" and got["episodes"] == 2
    assert got["eff_round"] == 0.9
    assert got["zero_agent_episodes"] == 1 and got["agent_episodes"] == 4
    # (2 + 4) / (2 solo * 2 episodes) = 1.5, the mean over episodes.
    assert got["welfare"] == 1.5


def test_a_round_with_no_sidecar_still_lists(tmp_path, monkeypatch):
    """A board with nothing to say about itself is listed, not hidden.

    It simply answers no filter. Dropping it would make the picker the arbiter
    of what exists, which is the listing's job and not the filter's.
    """
    root = tmp_path / "results"
    root.mkdir()
    (root / "board-y.json").write_text(json.dumps({"messages": []}))
    monkeypatch.setattr(serve, "ROOTS", {"results": root})
    serve._listing = (0.0, [])
    try:
        [entry] = serve.boards()
    finally:
        serve._listing = (0.0, [])
    assert entry["reveal"] is None
    assert entry["facets"] == {}


def test_a_damaged_sidecar_costs_its_facets_and_nothing_else(tmp_path, monkeypatch):
    """Half-written JSON is a thing that happens to a file being copied."""
    root = tmp_path / "results"
    root.mkdir()
    (root / "board-z.json").write_text(json.dumps({"messages": []}))
    (root / "reveal-z.json").write_text("{ not json")
    monkeypatch.setattr(serve, "ROOTS", {"results": root})
    serve._listing = (0.0, [])
    try:
        [entry] = serve.boards()
    finally:
        serve._listing = (0.0, [])
    assert entry["facets"] == {}
    assert entry["board"].endswith("board-z.json")
