"""Calling one agent for one round, and refusing to guess when it goes wrong.

The agent runtime is the `claude` CLI in headless mode, one process per agent
per round, run in an empty working directory so the repository's own
instructions cannot leak into a participant's context. Each call is
independent: an agent's memory of the episode is exactly what this module puts
in the prompt, which is what makes "what an agent saw" a recorded fact rather
than an inference about a conversation.

Two things this module will not do. It will not repair a malformed submission
into a plausible one — a price vector invented by the harness is the harness
enforcing a price, which the design forbids outright. And it will not let a
failure become a datum: an agent that cannot produce a well-formed submission
after one retry raises, and the world above turns into a `harness_failure` that
is excluded from every rate and counted separately.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass

from .market import GOODS, N_GOODS, normalise

MODEL = "claude-haiku-4-5-20251001"

#: Wall-clock ceiling for one agent-round. The pre-registration classifies an
#: overrun as a harness fault rather than a stubborn agent, so this number
#: decides which of those a slow call is called.
CALL_SECONDS = 180.0

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


class AgentFault(Exception):
    """Raised when an agent's output cannot be read as a submission."""


@dataclass
class Reply:
    message: str
    prices: list[float]
    raw: str
    retried: bool


def _extract(text: str) -> dict:
    """Pull one JSON object out of a reply, tolerating a code fence.

    Tolerating the fence is not leniency about content — the numbers are taken
    exactly as given — it is refusing to score a model down for markdown.
    """
    fenced = _FENCE.search(text)
    body = fenced.group(1) if fenced else text
    start, end = body.find("{"), body.rfind("}")
    if start < 0 or end <= start:
        raise AgentFault("no JSON object in reply")
    try:
        return json.loads(body[start:end + 1])
    except json.JSONDecodeError as exc:
        raise AgentFault(f"unparseable JSON: {exc}") from exc


def _read(obj: dict) -> tuple[str, list[float]]:
    if "prices" not in obj:
        raise AgentFault("reply has no 'prices'")
    raw = obj["prices"]
    if isinstance(raw, dict):
        missing = [g for g in GOODS if g not in raw]
        if missing:
            raise AgentFault(f"prices missing {missing}")
        values = [raw[g] for g in GOODS]
    elif isinstance(raw, list):
        values = list(raw)
    else:
        raise AgentFault(f"prices is {type(raw).__name__}, not object or list")
    if len(values) != N_GOODS:
        raise AgentFault(f"expected {N_GOODS} prices, got {len(values)}")
    try:
        values = [float(v) for v in values]
    except (TypeError, ValueError) as exc:
        raise AgentFault(f"non-numeric price: {exc}") from exc
    if any(v <= 0 or v != v or v in (float("inf"), float("-inf")) for v in values):
        raise AgentFault(f"non-positive or non-finite price in {values}")
    message = obj.get("message", "")
    if not isinstance(message, str):
        raise AgentFault("message is not a string")
    return message, normalise(values)


#: Transport attempts before a call is declared a fault. A non-zero exit or a
#: timeout is the runtime failing to deliver a turn, not an agent deliberating
#: badly, so retrying it is not a scientific retry and is not counted as one.
TRANSPORT_ATTEMPTS = 3


def _invoke(prompt: str, cwd: str) -> str:
    last = ""
    for attempt in range(TRANSPORT_ATTEMPTS):
        try:
            proc = subprocess.run(
                ["claude", "-p", "--model", MODEL, "--max-turns", "1"],
                input=prompt, capture_output=True, text=True, cwd=cwd,
                timeout=CALL_SECONDS)
        except subprocess.TimeoutExpired:
            last = f"timeout after {CALL_SECONDS}s"
        else:
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout
            last = (f"cli exit {proc.returncode}: "
                    f"{(proc.stderr or proc.stdout).strip()[:200]}")
        time.sleep(2.0 * (attempt + 1))
    raise AgentFault(last)


def ask(prompt: str, cwd: str) -> Reply:
    """One agent, one round. Retries once, then gives up loudly."""
    try:
        raw = _invoke(prompt, cwd)
        message, prices = _read(_extract(raw))
        return Reply(message=message, prices=prices, raw=raw, retried=False)
    except AgentFault:
        pass
    raw = _invoke(prompt, cwd)
    message, prices = _read(_extract(raw))
    return Reply(message=message, prices=prices, raw=raw, retried=True)
