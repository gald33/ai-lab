"""Bytes Python produced, for the browser to agree with.

`switchboard.js` is a second implementation of somebody else's wire format, so
the only check worth anything is against the first one. This module builds the
fixtures with the real `switchboard` library -- never with a local re-statement
of what it does -- and `tests/test_hand_crypto.py` drives them through a
browser.

**Both directions, deliberately.** A fixture that only asked the browser to
*open* what Python sealed would pass for an implementation that decrypts
correctly and encrypts garbage, and a hand whose lines nobody can open has
still lost every episode. So the test also takes what the browser produced and
opens it here, in Python.

The identities are seeded rather than generated: a fixture that changes every
run cannot be quoted in a bug report. The private halves are handed over as
PKCS#8, which is the only shape WebCrypto will import an Ed25519 or X25519
private key from -- a page in service generates its own non-extractable keys
and imports nothing, so this path exists for the test alone.
"""

from __future__ import annotations

import json
import os
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

from switchboard import crypto, signing

#: The lobby's published key. It protects nothing -- `ENTER.md` says so and
#: says why -- which is exactly what makes it the right one to commit here.
WORKSPACE_KEY = "Z822U5v1WFyeOEJUeLchMgLED-VgI_0chD4OjmRxej0"
WORKSPACE = "island-lobby"

#: A body the island would really send, and a string: Python sorts object keys
#: and formats floats differently from JavaScript, so the hand's client signs
#: and seals strings only. That is a rule in `switchboard.js`, not a property
#: of this sample.
BODY = "OFFER 2 bread for 3 fish"

#: What a seat is dealt, whispered to it alone.
DEALT = ("You are T1. Your production capacity per unit of labour: "
         "{'bread': 0.5, 'fish': 1.5}. Your taste weights: "
         "{'bread': 0.4, 'fish': 0.6}.")


#: Lengths that straddle every branch of `crypto.pad_bucket`: under the floor,
#: on it, through the powers of two, and past the point where buckets become
#: multiples of 4096.
_PAD_LENGTHS = [0, 1, 63, 64, 65, 127, 128, 129, 4095, 4096, 4097, 9000]


def _pkcs8(private) -> str:
    return crypto._b64e(private.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()))


def _identity(seed: bytes) -> tuple[signing.SigningIdentity, dict[str, str]]:
    """A deterministic identity, and the shape the browser needs to rebuild it."""
    ed = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    x = x25519.X25519PrivateKey.from_private_bytes(seed)
    identity = signing.SigningIdentity(_private=ed, _x25519_private=x)
    return identity, {
        "publicKey": identity.public_key,
        "exchangeKey": identity.exchange_key,
        "signingPkcs8": _pkcs8(ed),
        "exchangePkcs8": _pkcs8(x),
    }


def _seal_at_epoch(cipher: crypto.WorkspaceCipher, value: Any,
                   context: str, epoch: int) -> dict[str, Any]:
    """Seal under a named epoch rather than under the clock.

    A committed fixture must not depend on when it is read, and
    `WorkspaceCipher.seal` takes its epoch from `time.time()`. Relabelling an
    envelope sealed under a different epoch would not open, so the epoch goes
    in at the point the key is chosen.
    """
    envelope = crypto._seal_bytes(
        cipher._payload_key_for(epoch),
        crypto._pad(json.dumps(value, separators=(",", ":")).encode()),
        cipher._aad(context))
    envelope["e"] = epoch
    return envelope


def build() -> dict[str, Any]:
    """Every fixture the browser test needs, as one JSON-able dict."""
    hand, hand_wire = _identity(bytes(range(32)))
    peer, peer_wire = _identity(bytes(range(32, 64)))

    # epoch_period=0 so the ordinary sealed sample carries no `e` and stays
    # readable forever; the rotating cipher is only used to reach the epoch
    # subkey derivation, which the browser must also get right.
    cipher = crypto.WorkspaceCipher.from_key(WORKSPACE_KEY, WORKSPACE, epoch_period=0)
    payload = signing.message_payload(sender="T1", channel="table", seq=7, body=BODY)

    return {
        "workspace": WORKSPACE,
        "workspaceKey": WORKSPACE_KEY,
        "hand": hand_wire,
        "peer": {k: v for k, v in peer_wire.items() if not k.endswith("Pkcs8")},
        # --- signing --------------------------------------------------------
        "message": {
            "sender": "T1", "channel": "table", "seq": 7, "body": BODY,
            "payload": crypto._b64e(payload),
            "signature": hand.sign(payload),
        },
        # --- the workspace cipher -------------------------------------------
        "sealed": {
            "context": "messages.body",
            "value": BODY,
            "envelope": cipher.seal(BODY, "messages.body"),
        },
        "sealedAtEpoch": {
            "context": "messages.body",
            "value": BODY,
            "epoch": 1_900_000,
            "envelope": _seal_at_epoch(cipher, BODY, "messages.body", 1_900_000),
        },
        # The bucket table, and the length a real envelope comes out at.
        # `_pad` is the only part of this whose divergence a round-trip cannot
        # detect -- see the test of the same name.
        "padBuckets": {
            "lengths": _PAD_LENGTHS,
            "buckets": [crypto.pad_bucket(n) for n in _PAD_LENGTHS],
            "sealedLength": len(crypto._b64d(
                cipher.seal(BODY, "messages.body")["c"])),
        },
        "blind": {
            "channel": {"in": "lobby", "out": cipher.blind("lobby", "channel")},
            "agent": {"in": "@scout-v2", "out": "@" + cipher.blind("scout-v2", "agent")},
            # A hub-form id must pass through untouched: blinding it again
            # produces a channel no recipient's inbox resolves to.
            "hubForm": {"in": "@" + cipher.blind("scout-v2", "agent")},
        },
        # --- the whisper: sealed by the peer, for the hand to open -----------
        "whisper": {
            "context": "messages.body",
            "value": DEALT,
            "envelope": crypto.seal_to_peer(
                DEALT, my_identity=peer, peer_exchange_key=hand.exchange_key,
                context="messages.body"),
        },
    }


def open_workspace(envelope: dict[str, Any], context: str) -> Any:
    """Open, in Python, what the browser sealed to the workspace."""
    cipher = crypto.WorkspaceCipher.from_key(WORKSPACE_KEY, WORKSPACE, epoch_period=0)
    return cipher.unseal(envelope, context)


def open_whisper(envelope: dict[str, Any], context: str) -> Any:
    """Open, in Python, what the browser whispered to the peer."""
    hand, _ = _identity(bytes(range(32)))
    peer, _ = _identity(bytes(range(32, 64)))
    return crypto.unseal_from_peer(
        envelope, my_identity=peer, peer_exchange_key=hand.exchange_key,
        context=context)


def verify_signature(payload_b64: str, signature: str) -> bool:
    """Check, in Python, a signature the browser produced."""
    hand, _ = _identity(bytes(range(32)))
    return signing.verify(hand.public_key, crypto._b64d(payload_b64), signature)


def main() -> None:
    text = json.dumps(build(), indent=2, sort_keys=True)
    out = os.environ.get("ISLAND_FIXTURES", "-")
    if out == "-":
        print(text)
    else:
        with open(out, "w") as handle:
            handle.write(text)


if __name__ == "__main__":
    main()
