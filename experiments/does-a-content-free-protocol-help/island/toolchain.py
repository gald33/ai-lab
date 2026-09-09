"""Prove an agent's own MCP toolchain works, before a run spends on it.

An agent reaches the hub through `switchboard-mcp` with the environment its
runner hands it, and nothing else -- the manager reaches it through the parent
environment instead. So the manager can be fine while every agent is broken,
and `PREFLIGHT.md` records a fifty-round run lost to exactly that: every
session started, found every Switchboard tool returning "internal error",
asked to have the connection fixed, and stopped. Nothing upstream looked wrong,
and a session that starts and stops reads as a choice.

**This check was wrong until it was tested against a broken hub.** It called
`whoami`, which answers out of local config and never touches the hub, and it
looked for `"isError": true` in the raw output. A tool that cannot reach the
hub does not come back that way: it comes back as a JSON-RPC *error object* --

    {"jsonrpc": "2.0", "id": 2,
     "error": {"code": -32603, "message": "internal error (see stderr)"}}

-- whose `id` is present and whose text is the very phrase the gate was written
to catch. So the gate passed a config pointed at nothing, which is the one
thing it exists to fail. It now calls a tool that must reach the hub and reads
the response as JSON rather than searching the text of it.
"""

from __future__ import annotations

import json
import shutil
import subprocess

#: A tool that cannot be answered without the hub. `whoami` can: it reports
#: this process's own identity, so it passes whether or not anything is
#: listening -- which is how the first version of this check came to be
#: useless.
_PROBE = "roster"

_CALLS = [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "preflight", "version": "0"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
     "params": {"name": _PROBE, "arguments": {}}},
]


class Broken(Exception):
    """The toolchain an agent would get does not work. Always a harness fault."""


def _verdict(out: str) -> str | None:
    """What went wrong with the probe, or None if it answered.

    Reads the responses as JSON. Three distinct failures, kept distinct
    because they point at different things: no answer at all (the server did
    not start), an error object (it started and could not reach the hub), and
    a result flagged `isError` (it reached something that refused).
    """
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            message = json.loads(line)
        except ValueError:
            continue
        if message.get("id") != 2:
            continue
        if "error" in message:
            return f"the {_PROBE} tool failed: {message['error'].get('message', message['error'])}"
        result = message.get("result") or {}
        if result.get("isError"):
            return f"the {_PROBE} tool returned an error: {json.dumps(result)[:300]}"
        return None
    return f"no answer to the {_PROBE} call at all -- the MCP server did not start"


def check(env: dict[str, str], *, where: str) -> None:
    """Spawn the MCP server exactly as an agent gets it and call one tool.

    Raises `Broken` with the reason. Ten seconds here against a run of silence
    is not a close trade.
    """
    if not shutil.which("switchboard-mcp"):
        raise Broken("switchboard-mcp is not on PATH")
    try:
        done = subprocess.run(  # noqa: S603
            ["switchboard-mcp"],
            input="\n".join(json.dumps(c) for c in _CALLS),
            env=env, capture_output=True, text=True, timeout=45, check=False)
    except subprocess.TimeoutExpired:
        raise Broken("switchboard-mcp did not answer in 45s") from None
    wrong = _verdict(done.stdout + done.stderr)
    if wrong:
        raise Broken(
            f"an agent's own MCP server could not work against {where}, so "
            f"every agent would start, find its tools broken and stop. That "
            f"is a harness fault, not agent behaviour.\n  {wrong}\n"
            + (done.stderr or done.stdout)[-600:])
