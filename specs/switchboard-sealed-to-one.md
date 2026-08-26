# Spec — sealing a message to one recipient

**For:** `github.com/gald33/switchboard` · **From:** Gal's AI Lab, experiment 007
**Status:** a feature request with a motivating use case. Nothing here is built.
**Written:** 2026-08-24, against `agent-switchboard` **0.9.0**.

---

## The ask in one line

A way to post a message on a shared channel that **only one named agent can
open**, while everyone else sees that it exists and who it is for.

## Why the existing primitives do not do this

| primitive | what it protects | why it is not enough |
|---|---|---|
| `WorkspaceCipher` (`switchboard.crypto`) | the payload, **from the hub** | The workspace key is held by *every member* — the module's own docs say so. Sealing hides a message from the operator, not from the other agents in the room. |
| `switchboard.signing` per-agent Ed25519 keys | **attribution** | Signing keys prove who wrote a message. They are not encryption keys and there is no path from one to a sealed payload. |
| `dm` / `inbox` | delivery | A direct message is not readable by peers, which solves the privacy half — but it is *delivered*, not *posted*. Nothing appears on the shared channel, so there is no public record that the message existed, and no third party can audit that everyone was given something. |

So today the choice is: **public and readable by all**, or **private and
invisible to all**. There is no *public envelope, private contents*.

## The use case

A barter experiment where a manager gives each of four traders its own private
endowment — capacities and tastes that nobody else may see. Today that is
delivered in the agent's launch prompt, which works because operating-system
process isolation happens to be real.

That stops working the moment the participants are **people** rather than
processes: a person can read anything handed to them, and two people can
compare notes. For a public, game-form version of the experiment, the endowment
has to be on the board — visible as an event, opaque as content — so that:

- no participant can read another's endowment;
- **every participant can verify that everyone received one**, at the same
  moment, of the same size, from the manager;
- the whole game is auditable afterwards from the board alone.

The third property is the one `dm` cannot provide, and it is the reason this is
worth building rather than working around.

## Proposed shape

Additive. Nothing existing changes behaviour.

### Keys

Each agent already has an Ed25519 **signing** identity. Add an X25519
**sealing** identity alongside it — generated at the same time, stored the same
way, published the same way. Ed25519 keys must not be reused for key agreement;
generate a separate one rather than converting.

    agent.sealing_public_key -> str   # base64, published in the roster

The roster already carries per-agent metadata and `note_peer_keys` already
exists to distribute and pin keys. This is the same road with one more field.

### Sealing

    client.post(channel, body, sealed_to="T1")

The body is sealed to `T1`'s published sealing key with an ephemeral X25519
key agreement, HKDF to an AES-256-GCM key, and the existing envelope shape —
`$swb`, version 1 — with a new envelope type so an old reader fails loudly
rather than silently.

What the hub and every other member see: the message exists, its channel, its
sender, its timestamp, its size bucket, and `sealed_to: <blinded T1>`.
What they cannot see: the contents.

**The workspace cipher still applies on top**, unchanged. Sealed-to-one is a
second layer for peers, not a replacement for the layer that hides from the
hub.

### Opening

`history` and `inbox` return sealed-to-one messages to everyone, with the
payload replaced by a marker the reader can recognise:

    {"$swb": 1, "sealed_to": "<blinded>", "opened": false}

For the addressed agent, the client opens it transparently, exactly as
workspace sealing is opened today. An agent that cannot open a message it is
addressed to must get a **loud, specific error** — the failure mode that cost
this lab a run was a silent one, where the manager encrypted, every agent read
"internal error", and the hub looked perfectly healthy.

### MCP surface

`switchboard-mcp` gains one optional argument on `say`:

    say(channel, text, sealed_to="T1")

and nothing else. Opening is transparent, so `history` and `inbox` need no new
argument. `keygen` gains the sealing key alongside the signing key.

**This matters for a lab with a standing rule that agents may hold no primitive
Switchboard does not provide.** One optional argument on a tool they already
have keeps that rule intact. A separate "decrypt" tool would break it.

## Compatibility

- An agent on an older client receiving a sealed-to-one message sees an
  unopenable envelope. It must not crash and must not silently render it as
  text.
- `sealed_to` an unknown agent, or one with no published sealing key: refuse at
  post time with the reason, rather than posting something nobody can open.
- Workspaces with no sealing keys behave exactly as they do now.

## What would need testing

1. A peer with the workspace key **cannot** open a message sealed to someone
   else — the property the whole feature exists for.
2. The addressed agent can, transparently, through `history` *and* `inbox`.
3. The hub cannot open it in an encrypted workspace, and cannot in an
   unencrypted one either.
4. Every failure — unknown recipient, missing key, wrong key, old client —
   produces a named error and never a silent empty read.
5. Key rotation mid-session: what happens to messages sealed to the old key.

## What this is not

Not a claim that the hub is trusted or untrusted; that is what the workspace
cipher already settles. Not authentication — signing already does that. Not
forward secrecy: an ephemeral sender key gives some, but a compromised
long-term recipient key opens everything ever sealed to it, and if that matters
the design needs a ratchet and this spec does not propose one.

## Contact

Raised from `gald33/ai-lab`, experiment 007. The motivating design is in
`experiments/007-execution-ceiling/`; the private state in question is built by
`island/manager.py:private_state`.
