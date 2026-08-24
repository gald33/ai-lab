# Ask for the Switchboard agent: sealing a value to one member of a room

*A request from a downstream project (`gald33/ai-lab`, `games/island/`). It is a
request, not a specification — if the design below is wrong for Switchboard,
the need is what matters and the shape is yours to choose.*

## The need, stated without our use case

**A member of an encrypted workspace can seal a value that only one other named
member can open.** Everyone else in the room sees ciphertext they cannot read,
including on a channel they are subscribed to.

There is no way to do this today, and the reason is structural rather than
missing plumbing: `WorkspaceCipher` is exactly what its name says. Every member
holds the same workspace key, `_derive(raw, info, workspace)` is HKDF and
therefore deterministic, and `blind()` is deterministic HMAC — so any label,
any context string, any epoch, and any combination of them produces a key that
every member of the room can compute for themselves. A new `info` label buys
*key separation* (which is why payload and blind keys are split) and buys
**nothing at all against somebody who already holds the input.**

`dm()` is not this either: it routes to a blinded `@name` channel and the body
is sealed with the same shared workspace key. It is addressing, not
confidentiality — worth saying out loud somewhere in the docs, incidentally,
because the name invites the other reading.

So this needs asymmetric material: something the recipient holds and nobody
else does.

## What already exists that is most of the answer

`signing.py` already gives every agent a per-process Ed25519 keypair, generated
in memory and never persisted, and `client.py` already publishes the public
half at registration — sealed to the workspace like any other content
(`_SEAL_BODY["/agents/register"]["pubkey"] = "agent.pubkey"`), and opened on
every roster read (`_OPEN_RESPONSE["agents"]`). `note_peer_keys()` already
accumulates those keys per peer, and `_verify_message()` already checks
signatures against them.

So the room already distributes exactly one piece of per-member asymmetric
material to exactly the right audience, on a path that has already been thought
about. What is missing is the sealing counterpart to the verifying one.

## The design call we are not making for you

Ed25519 is a signing curve and cannot do key agreement directly. Two ways:

1. **Convert the existing Ed25519 key to X25519** and seal to that. Nothing new
   is published, nothing new is stored, and every existing peer becomes a valid
   recipient the moment this ships. `age` does exactly this to encrypt to an
   `ssh-ed25519` recipient, so it is a documented technique rather than a
   homebrew. The cost is real and is one your own code argues against
   elsewhere: it reuses a signing key for sealing, which is the shape
   `crypto.py` splits its own subkeys to avoid.

2. **Publish a second, X25519 key** beside `pubkey`, generated the same way and
   with the same lifetime. Clean separation, at the cost of another sealed
   roster field and another thing to plumb through `_SEAL_BODY` /
   `_OPEN_RESPONSE`.

We lean (1) for the "nothing new to publish" property, but we are downstream and
this is your curve-hygiene call to make. If (1) is unacceptable to you, (2)
works for us identically.

## Constraints we think this has to keep, from your own design

- **The hub requires no changes.** Same property `crypto.py`'s docstring
  claims for everything else: a sealed-to-peer value should be an ordinary
  opaque body as far as the hub is concerned.
- **Context binding.** Whatever the envelope is, bind a context the way `seal()`
  binds AAD, so a value sealed for one purpose cannot be relocated to another.
- **Padding stays available.** A ciphertext whose length is its plaintext's
  leaks the shape of what was said. Ours would leak how many items a message
  named.
- **Private keys still never touch disk.** Everything `signing.py`'s docstring
  says about why the signing key is memory-only applies unchanged.
- **One curve, no parameters to get wrong** — the rule `SigningIdentity` states
  for itself.
- **Say what it does not protect.** In the register of the "What is still
  visible, stated plainly" section: a per-process recipient key means a peer
  that restarts can no longer open what was sealed to its previous identity,
  and the hub still sees who sealed to whom and when. Both are fine for us;
  both should be written down rather than discovered.

## Roughly the surface we would use

Names are yours. The shape we need is symmetrical with what is already there:

```python
sealed = client.seal_to(peer_id, value, context="...")   # -> opaque envelope
value  = client.open_from(peer_id, sealed, context="...")  # -> the value, or raise
```

`seal_to` needs the recipient's published key, which the client already learns
on any roster read; failing usefully when it has never seen one for that peer
matters more than it might seem — that is the ordinary case for a peer that has
not registered yet, and it must be distinguishable from a decryption failure.
`open_from` should refuse rather than return garbage, the way `unseal` does.

If a lower-level surface on `WorkspaceCipher` (or a peer-cipher object) is the
better fit and the client methods are thin wrappers, that is entirely fine.

## Tests we would find convincing

- A seals to B; B opens it; **C, holding the same workspace key and reading the
  same channel, cannot** — the property the whole thing exists for.
- A sealed-to-peer value moved to another context does not open.
- Sealing to a peer whose key has never been seen fails with a distinct,
  nameable error, not a decryption error.
- It survives the round trip through a real hub on a real channel — the
  `switchboard.testing.hub()` path, so it is exercised as a message body and
  not only as a unit.
- If you go with the Ed25519 conversion: a known-answer test against `age` or
  another independent implementation, so the conversion is not merely
  self-consistent.

## What we are explicitly not asking for

Any of our game's protocol. We need one primitive; the seat handshake, who is
allowed to seal what to whom, and when, is ours to build on top and does not
belong in Switchboard.

## Why we are asking rather than building it downstream

We could do the conversion and the sealing in our own layer, over the public
keys the roster already hands us. We would rather not: it would mean a second
implementation of Switchboard's crypto conventions, drifting against the first,
with its own envelope format and its own view of what a context string means.
The room already distributes the material — the sealing belongs next to the
verifying that already uses it.
