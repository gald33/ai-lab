"""One agent, one turn: call the model, parse actions, refuse to invent any.

The runtime is the `claude` CLI headless, one process per agent-turn, run in an
empty directory so the repository's own instructions cannot reach a
participant. An agent's memory of the run is exactly what `prompt.turn` puts in
front of it, which makes "what this agent knew" a recorded fact.

This module never repairs a malformed action into a plausible one. A production
plan invented by the harness is the harness making a production decision, which
the design forbids outright. One retry on unparseable output, then the world is
a `harness_failure` -- excluded from every rate and counted on its own.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field

MODEL = "claude-haiku-4-5-20251001"
CALL_SECONDS = 240.0

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


class AgentFault(Exception):
    """The agent's output could not be read as a list of actions."""


@dataclass
class Turn:
    actions: list[dict]
    raw: str
    retried: bool = False
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


def _invoke(prompt: str, cwd: str) -> str:
    proc = subprocess.run(
        ["claude", "-p", "--model", MODEL, "--max-turns", "1"],
        input=prompt, capture_output=True, text=True, cwd=cwd,
        timeout=CALL_SECONDS)
    if proc.returncode != 0:
        raise AgentFault(f"cli exit {proc.returncode}: "
                         f"{proc.stderr.strip()[:200]}")
    return proc.stdout


def ask(prompt: str, cwd: str) -> Turn:
    try:
        raw = _invoke(prompt, cwd)
        return Turn(actions=_read(_extract(raw)), raw=raw)
    except (AgentFault, subprocess.TimeoutExpired):
        pass
    raw = _invoke(prompt, cwd)
    return Turn(actions=_read(_extract(raw)), raw=raw, retried=True)
