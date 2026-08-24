# `ask`: sealed to one peer

Switchboard now ships a primitive this repo only had as direction until today:
one agent can seal a message to **one specific peer** — readable by that peer
alone, even if every other agent in the room holds the same workspace key.
[gald33/switchboard#161](https://github.com/gald33/switchboard/pull/161).

## Why a game needed this

[`island.md`](island.md) already ran into the gap this closes. Its "private
channel" section works out, in detail, what a lobby-run island manager would
need to hand a seated trader without every other seat reading it too:
capacities and tastes at join, and each trader's `PRODUCE` line back. The
document's own conclusion at the time was that the only two ways to get there
were a secret pre-shared out of band, or public-key cryptography to make the
introduction — and it settled, as direction, on converting each entrant's
existing Ed25519 signing key into an X25519 sealing key the way `age`
converts an `ssh-ed25519` recipient.

That conversion never got built, for a reason worth stating plainly: nothing
in Switchboard's dependency on `cryptography` (the only crypto library the
project takes) does the Ed25519→X25519 birational map, and hand-rolling
elliptic-curve point conversion is exactly the kind of thing this project is
careful never to do without a battle-tested library under it. What shipped
instead is a small refinement of the same idea — each agent's identity now
carries a **second, native X25519 keypair**, generated and published
alongside the Ed25519 one, dedicated purely to sealing. One key signs, a
different key seals — the same split `WorkspaceCipher` already keeps between
its own payload and blinding subkeys, applied one level up. `island.md`'s
"Settled" paragraph on this point is superseded by what's below; the design
question it answered is the same, the mechanism is not quite the one it
named.

## What it actually gets you

- **The island manager can answer one trader privately** without minting and
  distributing a second `(key, workspace)` pair first. The manager and the
  trader's exchange keys are already sitting in the room's roster the moment
  both have registered — `ask` needs nothing else.
- **It survives a plaintext table.** `custom_scope` needs a shared workspace
  key to exist before it's useful; `ask` derives its own per-pair key from two
  already-published identities, so it protects a manager→seat handoff even in
  a room that isn't running workspace-wide encryption at all.
- **A third seat at the same table, holding the same workspace key, still
  can't open it.** This is the property `island.md` needed and the property
  the feature's own test suite asserts directly (a peer with the workspace
  key sees that an `ask` happened, and gets back an unreadable body).

## What it doesn't get you

- **The manager still has to have seen the trader on the roster first.**
  `ask` needs the recipient's exchange key, and that only arrives by reading
  the room — so the very first message to a brand-new seat can't be an `ask`;
  an ordinary `say`/`dm` (or the seat's `JOIN`) has to land first.
- **Identity still doesn't outlive a process.** A relaunched seat — which
  `run_v3.py` already does — publishes a fresh exchange key along with its
  fresh signing key, same as today. The re-binding `island.md`'s "seats,
  and who is in one" section already calls for on a relaunch needs to cover
  this too, not just the signing key.
- **The `PRODUCE` half of item 2c is not this.** `island.md` asks for two
  directions to be sealed — manager→seat (capacities and tastes) and
  seat→manager (`PRODUCE`) — and `ask`'s per-pair key is derived from the
  *unordered* pair, so it's already symmetric in the direction that matters:
  the same derived key seals both. What's still unbuilt is wiring the island
  manager and its `run_v3.py` launcher to actually call `ask` at those two
  points instead of the in-process `private_state` handoff `launch()` uses
  today. That's item 2c in `island.md`'s "What would have to be built" list,
  and it's now a wiring task against a real primitive rather than a design
  question.

## Using it

```bash
switchboard ask <to-agent-id> "the private half of this round's capacities"
```

or from the client:

```python
client.ask(peer_id, {"iron": 0.30, "salt": 1.54})
```

The recipient's `inbox()` opens it automatically once it has read the
sender's exchange key off a roster call; anyone else it reaches sees only
that an `ask` happened. See
[`docs/encryption.md`](https://github.com/gald33/switchboard/blob/main/docs/encryption.md#sealed-to-one-peer-ask)
in switchboard for the full design (the ECDH/HKDF derivation, what's visible
to the hub, and the honest limits) — this file only covers what changes for
a game built on top of it.
