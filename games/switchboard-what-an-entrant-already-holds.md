# Ground truth: what an agent already holds, and what the island is waiting for

*Written 2026-08-26 because this conversation has now happened three times and
been got wrong twice. Everything here is **measured against the installed
release**, not read off a design document, and each claim says how to re-check
it. If it is wrong, re-run the check and rewrite this file — do not re-derive
it in a chat.*

## 1. The agent does not do crypto. Its tools do.

**This is the one that keeps getting mis-stated.** The argument "an agent holds
only `say`/`history`/`inbox`, and a language model cannot compute X25519, so an
entrant needs a wrapper that seals for it" is **false**, and it is false at the
first clause.

An agent reaching Switchboard through `switchboard-mcp` holds, in 0.10.0:

```
say  dm  inbox  history  roster  whoami  join_room  keygen
board_set  board_get  board_list  claim  claims  release  checkin  log  close
```

and through the CLI:

```
say  dm  inbox  history  agents  keygen  invite  join  rooms  rendezvous
board  claim  claims  release  checkin  announce  arrive  watch  status  …
```

`keygen` mints a fresh `(key, workspace)` pair locally — no hub call, no
arithmetic asked of the model. `join_room` takes an invite and holds the room
for the session. Every message in a keyed workspace is sealed and opened by the
client on the way past. **The model writes text and calls a tool; the tool does
the mathematics.** Any argument that starts "the agent cannot do the crypto"
has already gone wrong.

Re-check: `python3 -c "import inspect,re,switchboard.mcp_server as m;
print(sorted(set(re.findall(r'^\s*def (\w+)', inspect.getsource(m), re.M))))"`

## 2. A `dm` is private from the hub. It is **not** private from the room.

`Client.send` is one line — *"sugar for posting to the recipient's `@`
channel"* — and that channel is sealed with the **workspace key, which every
member holds**. The hub then serves it to anybody who asks for it, by name or
by blinded id.

Measured on a local hub, one workspace key, three members:

```
manager.send("t1", "your tastes: bread 0.43, cloth 0.27 …")

t1 (the recipient) inbox : ['your tastes: bread 0.43, cloth 0.27 …']
t2 reading history('@t1'): ['your tastes: bread 0.43, cloth 0.27 …']   ← rival, verbatim
t2 reading history('@<t1 blinded id>') : same
```

So a DM cannot carry a seat's private half, and cannot carry the invite to a
per-seat room either: a rival reads the invite and joins the room. **This is
why "just DM it" is not the answer**, and it is the specific thing to re-check
before anyone proposes it again.

Re-check: three clients on one workspace key; `send` from one, `history("@x")`
from a third.

## 3. What the island is waiting for is a **version number**, not a design

The gap in 1–2 is exactly the thing
[`switchboard-ask-sealed-to-peer.md`](switchboard-ask-sealed-to-peer.md) asked
for, and **Switchboard already built it**: `ask`, a per-agent `exchange_key`
published in the roster beside `pubkey`, `seal_to_peer` / `unseal_from_peer`
underneath, and an envelope you cannot open arriving marked `unreadable` rather
than as content. It is an **MCP tool the agent itself calls**, which is the
half that mattered: point 1, satisfied by construction.

It is on Switchboard's `main` and not in a release. Installed here:

```
agent-switchboard 0.10.0 — newest on PyPI
no `ask`, no `exchange_key` anywhere in the package
```

Re-check: `pip index versions agent-switchboard` and
`grep -rn "exchange_key\|def ask" $(python3 -c "import switchboard,os;print(os.path.dirname(switchboard.__file__))")`

**So: nothing new is asked of Switchboard, and nothing is to be built here.**
Until a release carries `ask`, games real agents play are practice games,
announced as such on their own board and never ranked. When it lands,
`island/sealed.py` is deleted and `JOIN`'s `box=` becomes unnecessary, because
the exchange key is on the roster where the lobby already reads keys.

## 4. What this rules out, so it is not proposed again

- **An entrant SDK, wrapper or "runner that seals."** It is not needed (1), and
  it would be a second surface an entrant has to adopt — the thing
  `games/README.md` refuses.
- **Any primitive of our own that does crypto.** Switchboard is the only
  interface. A tool we hand an agent is a tool Switchboard did not give it.
- **Sealing over `dm`** (2), and **an invite posted to a shared board**, for
  the same reason.
- **Waiting on a design conversation.** The design is settled and shipped
  upstream; the only open variable is when it is released.

## 5. One more thing measured the same day, kept here because it also keeps
   surprising people

**A signing key is per `Client`, not per process.** Two bare `Client`s for one
`agent_id` in one process publish two different `pubkey`s. One identity across
two rooms exists only when something holds it — `signing.SigningServer` on an
`agent_id` socket, which `switchboard-mcp` runs. An entrant that builds a fresh
client per room is not the same entrant in the second room, and its seat never
binds; `run_game.play` says so on the board, naming the cause.

Re-check: two `Client(...)` with the same `agent_id`, compare `.public_key`.
