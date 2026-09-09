"""One agent, one turn: call the model, parse actions, refuse to invent any.

The runtime is the `claude` CLI headless, one process per agent-turn, run in an
empty directory so the repository's own instructions cannot reach a
participant. The cell's stimulus is passed as a system prompt rather than as
user text: it is byte-identical across every turn of a cell, and sending it
through the channel the runtime caches saves re-reading ~1,300 words on each of
a round's 160 calls. An agent's memory of the run is exactly what `prompt.turn` puts in
front of it, which makes "what this agent knew" a recorded fact.

This module never repairs a malformed action into a plausible one. A production
plan invented by the harness is the harness making a production decision, which
the design forbids outright. One retry on unparseable output, then the world is
a `harness_failure` -- excluded from every rate and counted on its own.

Two kinds of failure, counted apart because they mean different things:

* **transport** -- the CLI exits non-zero or times out. Measured here at eight
  concurrent callers, this happens sporadically and with an empty stderr, and
  it retries clean. It is a fact about the runtime, not about the agent, so it
  is retried with backoff and counted separately.
* **content** -- the model replied but the reply is not a list of actions. That
  is the agent's output, so it gets exactly one more chance at the same prompt
  and is counted as an agent-level retry.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field

MODEL = "claude-haiku-4-5-20251001"
CALL_SECONDS = 240.0

#: Transport retries and the backoff between them. Sporadic non-zero exits
#: under concurrency are a runtime property; giving up on the first one would
#: turn a flaky process launch into a discarded world.
TRANSPORT_TRIES = 5
BACKOFF = (2.0, 4.0, 8.0, 16.0)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


class AgentFault(Exception):
    """The agent's output could not be read as a list of actions."""


class TransportFault(Exception):
    """The CLI itself failed. Not the agent's doing."""


@dataclass
class Turn:
    actions: list[dict]
    raw: str
    #: The model replied with something unreadable and was asked again.
    retried: bool = False
    #: The CLI failed to run and was relaunched. Counted apart from `retried`.
    transport_retries: int = 0
    seconds: float = 0.0
    faults: list[str] = field(default_factory=list)


def _extract(text: str) -> dict:
    fenced = _FENCE.search(text)
    blob = fenced.group(1) if fenced else text
    start, end = blob.find("{"), blob.rfind("}")
    if start < 0 or end <= start:
        raise AgentFault("no JSON object in reply")
    try:
        return json.loads(blob[start:end + 1])
    except json.JSONDecodeError as exc:
        raise AgentFault(f"unparseable JSON: {exc}") from exc


def _read(obj: dict) -> list[dict]:
    if "actions" not in obj:
        raise AgentFault("reply has no 'actions'")
    actions = obj["actions"]
    if not isinstance(actions, list):
        raise AgentFault("'actions' is not a list")
    for a in actions:
        if not isinstance(a, dict) or "call" not in a:
            raise AgentFault("every action needs a 'call'")
    return actions


def _launch(prompt: str, cwd: str, system: str | None = None) -> str:
    """One CLI call, retried through transport faults only."""
    last = ""
    argv = ["claude", "-p", "--model", MODEL, "--max-turns", "1"]
    if system:
        argv += ["--append-system-prompt", system]
    for attempt in range(TRANSPORT_TRIES):
        try:
            proc = subprocess.run(
                argv,
                input=prompt, capture_output=True, text=True, cwd=cwd,
                timeout=CALL_SECONDS)
            if proc.returncode == 0:
                return proc.stdout
            last = f"exit {proc.returncode}: {proc.stderr.strip()[:200]}"
        except subprocess.TimeoutExpired:
            last = f"timed out after {CALL_SECONDS:.0f}s"
        if attempt < len(BACKOFF):
            time.sleep(BACKOFF[attempt])
    raise TransportFault(f"cli failed {TRANSPORT_TRIES} times; last: {last}")


def ask(prompt: str, cwd: str, system: str | None = None) -> Turn:
    started = time.perf_counter()
    raw = _launch(prompt, cwd, system)
    try:
        return Turn(actions=_read(_extract(raw)), raw=raw,
                    seconds=time.perf_counter() - started)
    except AgentFault:
        pass
    raw = _launch(prompt, cwd, system)
    return Turn(actions=_read(_extract(raw)), raw=raw, retried=True,
                seconds=time.perf_counter() - started)
