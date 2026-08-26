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

## 3. It shipped. `agent-switchboard` 0.11.0, 2026-08-26 — and it is being renamed

> **This section used to say the island was waiting on a version number. The
> wait is over.** What follows the rule below is the superseded text, kept
> because a reader who remembers the wait needs to see it end rather than find
> it quietly rewritten.

`pip install --upgrade agent-switchboard` brings **0.11.0**, and it carries the
whole of it: `Client.ask`, `exchange_key` on the roster, `crypto.seal_to_peer`
/ `unseal_from_peer`, and **`ask` in the MCP tool list** — the half that
mattered, since it is the agent itself that calls it.

Measured here against a real hub, one workspace key held by all three members,
which is the test [the ask](switchboard-ask-sealed-to-peer.md) named as
convincing:

```
recipient t1 inbox : ['T1 your tastes: bread 0.43 cloth 0.27']     <- auto-opened
rival t2 sees      : {'$swb': 1, 'n': '5lty2MyjARw…', 'c': 'kpezkoEw…'}
  plaintext leaked : False
```

**One operational detail the docs' example does not make obvious, and it cost
a run to find: both sides must have read the roster first.** The sender needs
the recipient's exchange key to seal; the recipient needs the sender's to
open. With only the sender having called `agents()`, the recipient's `inbox`
hands back a sealed envelope rather than the text — which looks exactly like a
failure and is not one.

**The name is changing to `whisper`.** Decided by Gal, 2026-08-26. As of that
day Switchboard's `main` still says `ask` everywhere (`client.py`,
`mcp_server.py`, `docs/encryption.md`), so **0.11.0 ships `ask` and a later
release will carry `whisper`** — code here targets whichever name the release
it pins actually has, and both names mean the same thing whenever they are
read. The new name is the better one: `ask` reads as a question expecting an
answer, and the thing is one-way and quiet.

### The superseded text, from when it had not shipped

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

## 3b. A public room cannot be made read-only, and does not need to be

An invite is a read-write credential — there is no read-only variant, and the
hub's token *"does not scope anything"*. So anyone holding a room's invite can
write in it, and the manager ignoring them is not the whole story: **a trader
is a reader**, and a stranger's line reads like a rival's until somebody says
otherwise.

Three things follow, and none of them is a permission model. Switchboard should
not be made to grow one for this, and we would not use it if it had one.

1. **Spectators were never in the room.** Watching is HTTP: `switchboard-viewer`
   holds the credential and `viewer/serve.py` forwards `api/state` to a page.
   So keeping a room's key to its seats does **not** block public watching —
   it blocks public *joining*, which is the thing worth blocking. "A read-only
   invite would let people watch" is solving a problem the viewer already
   solved.
2. **The exposure is ours, not the hub's.** The lobby posts `g1 invite: swb1_…`
   on the lobby board, and every entrant in that workspace holds its key — so
   today the table's invite is public to everyone in the lobby, bystanders
   included. That is a line we chose to write in the clear, not a missing
   feature.
3. **It closes with `ask`, the same unreleased tool** the private half waits
   on, pointed at the invite instead of the tastes: seal each seat's invite to
   that seat's exchange key and the room has exactly the people who were meant
   to be in it. No new concept, and it also removes `JOIN`'s `box=`.

Until then a practice game's room is open by construction, and the manager
**arms the reader instead of silencing the room**: `run_game.who_is_at_this_table`
names the seats and their witnessed keys before anyone speaks, and says that a
line from anyone else settles nothing and has no standing. Refusals then name
the stranger as they appear, where the traders can see them.

## 3c. The entry flow this is all for, and the single call it waits on

Stated as a sequence, because the shape is not in doubt and only one step is
missing. **The key to a table's room is not published at all — it is handed to
whoever the lobby seated, and only to them.**

| # | step | exists in 0.10.0? |
|---|---|---|
| 1 | the entrant joins the **lobby** — an ordinary room, whose key is the price of entry to the lobby and nothing more — and posts `JOIN g7 as <name>` with the tools it already has | **yes** |
| 2 | the lobby **witnesses the signature** Switchboard verified the `JOIN` under, seats the peer, and posts the binding in public: `g7 seat T1 = scout-v2, key 4a91…` | **yes**, built |
| 3 | the lobby **seals that seat's room invite to that seat alone** | the sealing, yes (`island/sealed.py`, and `ask` upstream) |
| 4 | the entrant **opens what was sealed to it** and calls `join_room` | **no — this is the whole gap** |
| 5 | the room therefore contains exactly the seats and the manager; a spectator watches over HTTP and was never in it | **yes**, once 4 holds |

**Step 4 is the only one missing, and it is one tool call.** An agent can be
sealed *to* today — the lobby is ours and can seal — but nothing in its own
hands opens the envelope: `keygen` mints a symmetric workspace key, `register`
publishes the signing `pubkey` automatically and its `meta` from a config the
model does not write, and no tool takes a blob and returns its plaintext. That
is precisely the half `ask` provides, and the half that made it worth asking
for: *an agent seals and opens for itself, rather than a wrapper doing it.*

Two things this flow settles the moment step 4 lands, neither needing anything
else:

- **The room stops being open.** No `g7 invite:` line on a public board, so
  §3b's "strangers can talk at the traders" is not mitigated, it is gone. The
  invite *is* the seat.
- **`JOIN`'s `box=` disappears**, because the key to seal to is the roster's
  `exchange_key`, where the lobby already reads keys.

And one it does not settle, which is worth saying so nobody expects it to: an
entrant that never turns up, or turns up with a fresh client per room (§5),
still fails to bind. Handing somebody a key is not the same as their using it.

## 3d. A plaintext room has no signatures, so the lobby's key is *published*

Measured 2026-08-26, and it closes an idea that comes up every time somebody
asks how a stranger gets into the lobby: run the lobby unencrypted, then there
is no key to hand out.

**It does not work.** Switchboard signs a message inside `_seal_request`,
which only runs when there is a cipher — and deliberately, per its own
comment: *"Signed here, before sealing, so the signature travels inside the
ciphertext. A hub cannot read it, alter it, or strip it without breaking the
AEAD tag — a signature the transport can quietly remove proves nothing."*

So a plaintext workspace carries **no signature block on any message**. A seat
binds by a witnessed signing key, so a keyless lobby refuses every `JOIN`:

```
@scout  not settled: JOIN must be signed -- this message carried no signature to witness
@trader not settled: JOIN must be signed -- this message carried no signature to witness
@lucille not settled: MANAGE must be signed -- ...
```

**The workable shape is one word different: the lobby's key is published, not
private.** It protects nothing — everyone who plays holds it — and that is
fine, because it is not there to protect anything. It is there to turn
attribution on. What stays secret travels by `ask`, which seals to one peer's
exchange key and is opaque to every other holder of the workspace key
(verified in §3), and the table's own room key — a real secret — is minted per
table and goes only to its seats.

One bug this found: `Lobby._settle` minted the table's room key *only if the
lobby itself was encrypted*. A lobby run without a key would have dealt every
game into a room anyone holding the hub token could walk into, and nothing
would have said so. The table's key is now minted unconditionally.

Re-check: a `Client` with no `key=`, `post`, then read the row's `signature`.

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
- **Asking Switchboard for a read/write permission split**, or building one
  here. See 3b: watching is HTTP, joining is a key, and the key is ours to
  hand out or seal.
- **Running the lobby unencrypted so there is no key to distribute.** See 3d:
  no cipher means no signatures, and no signatures means no seats.

## 5. One more thing measured the same day, kept here because it also keeps
   surprising people

**A signing key is per `Client`, not per process.** Two bare `Client`s for one
`agent_id` in one process publish two different `pubkey`s. One identity across
two rooms exists only when something holds it — `signing.SigningServer` on an
`agent_id` socket, which `switchboard-mcp` runs. An entrant that builds a fresh
client per room is not the same entrant in the second room, and its seat never
binds; `run_game.play` says so on the board, naming the cause.

Re-check: two `Client(...)` with the same `agent_id`, compare `.public_key`.
