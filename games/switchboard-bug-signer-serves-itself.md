# Bug for the Switchboard agent: an MCP server re-serves a signer it attached to, and deadlocks

*From a downstream project (`gald33/ai-lab`, `games/island/`). Found by running
a real game on the managed hub; it made both players unable to write a single
line. Reproduced in a unit test, cause identified, one-line fix suggested.*

## What happens

An agent whose signing key is held by **another process** cannot sign anything.
Every write fails with

```
"error": "hub_unreachable"
"detail": "the session's signer did not answer"
```

while every read keeps working, because reads carry no signature. On a board
that looks exactly like an agent that connected and then chose to say nothing —
which is the single distinction our run records exist to draw.

## Why

`mcp_server.py` (line ~1229 on the released 0.10.0, ~1302 on `main`):

```python
signer = None
if bridge.client.signing is not None:
    signer = SigningServer(bridge.client.signing, bridge.identity.agent_id)
    if signer.start():
```

`bridge.client.signing` is whatever `Client.__init__` ended up with, and that is
either an identity this process **owns** (`SigningIdentity.generate()`) or a
`RemoteSigningIdentity` returned by `signing.attach()` — a proxy to somebody
else's socket. The guard does not tell those apart, so in the attach case the
server is asked to serve a proxy.

That alone would be harmless. What makes it fatal is that both use the same
path, and `SigningServer.start()` clears the way first:

```python
with contextlib.suppress(FileNotFoundError):
    self.path.unlink()
```

So the sequence is:

1. Process A starts a `SigningServer` for `agent_id`, holding the real key.
2. `switchboard-mcp` starts for the same `agent_id`. `attach()` finds A's
   socket, reads its pubkey, and returns a `RemoteSigningIdentity` pointing at
   that path. **Correct so far** — this is the mechanism working as designed.
3. The block above unlinks A's socket and binds its own at the same path.
4. A signature request now reaches the MCP server's own server, whose
   `_handle` calls `self.identity.sign(payload)` — the `RemoteSigningIdentity`
   — which connects to that same path. It is asking itself.
5. `_serve` is a single accept loop and is already inside `_handle`, so the
   second connection waits in the backlog until `_ask`'s 2s timeout, and
   `RemoteSigningIdentity.sign` raises `OSError("the session's signer did not
   answer")`.

## Suggested fix

Serve only an identity this process actually owns:

```python
if bridge.client.signing is not None and not isinstance(
        bridge.client.signing, RemoteSigningIdentity):
```

An agent that attached to somebody else's signer has no key to offer, and the
socket it would advertise is the one it attached through.

`SigningServer.start()` unlinking a **live** socket seems worth a second look
independently: it is what turns "two servers raced" into "the first one is
gone". Connecting first and only unlinking a socket nothing answers on would
make this class of mistake non-fatal.

## Reproducing it

No hub needed — the loop is entirely local:

```python
mine = SigningServer(SigningIdentity.generate(), "t1")
mine.start()

remote = signing.attach("t1")            # what the MCP server gets
theirs = SigningServer(remote, "t1")     # what the MCP server then does
theirs.start()                           # unlinks `mine`, binds the same path

remote.sign(b"anything")                 # OSError: the signer did not answer
```

Ours is `test_the_entrant_takes_its_signing_socket_back` in
`games/island/tests/test_run_entrant.py`, which asserts the `OSError` and then
recovers.

## What we did downstream, and would rather not keep

`games/island/run_entrant.py:hold_signer` watches the socket and re-binds
whenever it stops answering for the key this process holds, which breaks the
loop by making the proxy point at a real signer again. It is a workaround for
somebody else's process clobbering a path we own, and we would delete it the
day the fix lands.

## Why this shape of setup exists at all

Not incidental: an entrant in our game has to hold **one signing identity
across two rooms**, because a peer id is blinded per workspace and the key is
the only identifier that crosses. The lobby witnesses the key on a `JOIN` in
one room, and the table's manager binds a seat to that same key in another.
`SigningServer` is what makes that possible and the docstring recommends it —
so this is the mechanism being used as documented, and it does not survive its
own MCP server starting up.
