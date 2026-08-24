"""Sealing one value so that only one member of a room can open it.

**This is a stopgap and should be deleted.** It belongs in Switchboard, next
to the signature verification that already distributes per-member keys, and it
has been asked for there --
[`games/switchboard-ask-sealed-to-peer.md`](../../../games/switchboard-ask-sealed-to-peer.md).
Until that lands there is no way to hide anything from a room member: the
workspace key is held by everyone, HKDF is deterministic, and `dm()` is
addressing rather than confidentiality. So this exists to make a ranked game
possible at all, kept as small as it can be, and the ask stays open.

**Why a separate key rather than the signing key.** `games/island.md` settled
on reusing each agent's Ed25519 identity, converted to X25519 the way `age`
converts an `ssh-ed25519` recipient. That settlement assumed the conversion
was available as a documented, tested implementation. It is not, here:
`cryptography` exposes no Ed25519-to-X25519 conversion and PyNaCl is not a
dependency, so taking that route would mean hand-writing the birational map
between Edwards and Montgomery coordinates -- homebrew curve arithmetic on the
one path where a mistake is silent and total. That is the specific thing the
ask asks Switchboard *not* to do, and it would be no better done here.

So the recipient generates an X25519 keypair and publishes the public half,
which is the other option the ask sets out. It costs one more public key on
the board and buys native, reviewed primitives. `games/island.md` records the
correction.

**What this does.** Ephemeral-static X25519: the sender makes a throwaway
keypair, agrees a secret with the recipient's published key, derives an AES
key from it, and sends its ephemeral public half in the clear alongside the
ciphertext. Forward-secret against later compromise of the sender, since the
ephemeral private half is never kept.

**What it does not do.** It does not say who sealed it -- ECDH to a published
key is something anyone can do. Authorship comes from the signature Switchboard
already puts on every message, which is checked before any of this is opened.
Padding is on, because a ciphertext whose length is its plaintext's announces
how many goods a plan named.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

#: What a sealed line opens with, so a reader that cannot open it still knows
#: what it is looking at rather than treating a blob as talk. The viewer draws
#: these as locked lines; the manager refuses to guess at them.
MARKER = "SEALED"

#: Padding buckets, so a ciphertext's length does not report its plaintext's.
#: Framed exactly the way `switchboard.crypto._pad` frames it -- marker, then
#: a four-byte length, then the data, then filler. The length is what makes
#: the boundary unambiguous: marker and filler are the same byte, so scanning
#: for the marker cannot find it, which is a bug this had until an end-to-end
#: round trip caught what a `startswith` assertion had missed.
_PAD_MIN = 64
_PAD_MARKER = 0x00


class SealError(Exception):
    """A sealed value that will not open. Never a silent partial read."""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _bucket(length: int) -> int:
    size = _PAD_MIN
    while size < length:
        size *= 2
    return size


def _pad(raw: bytes) -> bytes:
    framed = len(raw).to_bytes(4, "big") + raw
    target = _bucket(len(framed) + 1)
    return bytes([_PAD_MARKER]) + framed + bytes(target - len(framed) - 1)


def _unpad(padded: bytes) -> bytes:
    if not padded or padded[0] != _PAD_MARKER:
        raise SealError("padding is malformed")
    length = int.from_bytes(padded[1:5], "big")
    if length > len(padded) - 5:
        raise SealError("padded payload declares a length beyond its own size")
    return padded[5:5 + length]


def _key(shared: bytes, context: str) -> bytes:
    """One AES key per (agreement, context).

    The context is bound into the derivation *and* into the AEAD below, so a
    value sealed for one purpose cannot be replayed as another even by
    somebody who can open both.
    """
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None,
                info=b"island.sealed.v1\x00" + context.encode()).derive(shared)


@dataclass
class BoxKey:
    """One recipient's keypair. The private half never leaves the process."""

    _private: X25519PrivateKey

    @classmethod
    def generate(cls) -> BoxKey:
        return cls(_private=X25519PrivateKey.generate())

    @property
    def public(self) -> str:
        """The half that goes on the board. Public keys are public."""
        from cryptography.hazmat.primitives import serialization
        return _b64e(self._private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw))

    def open(self, blob: str, context: str) -> str:
        """Open a value sealed to this key, or raise."""
        if not blob.startswith(MARKER):
            raise SealError(f"not a {MARKER} value")
        try:
            envelope = json.loads(_b64d(blob[len(MARKER):].strip()))
            ephemeral = X25519PublicKey.from_public_bytes(_b64d(envelope["e"]))
            shared = self._private.exchange(ephemeral)
            plain = AESGCM(_key(shared, context)).decrypt(
                _b64d(envelope["n"]), _b64d(envelope["c"]), context.encode())
        except SealError:
            raise
        except Exception as exc:                      # noqa: BLE001
            # Every failure is one failure: a wrong key, a wrong context and a
            # tampered ciphertext must not be distinguishable to whoever sent
            # it, and a caller cannot act differently on any of them anyway.
            raise SealError("this did not open with that key") from exc
        return _unpad(plain).decode()

    def __repr__(self) -> str:                        # pragma: no cover
        return f"<BoxKey {self.public[:12]}…>"


def seal_to(public: str, text: str, context: str) -> str:
    """Seal `text` so that only the holder of `public`'s private half opens it.

    Returns one board-safe line. Anybody may call this against a published
    key -- which is why it proves nothing about who sealed it, and why the
    message carrying it is signed.
    """
    try:
        recipient = X25519PublicKey.from_public_bytes(_b64d(public))
    except Exception as exc:                          # noqa: BLE001
        raise SealError(f"not a usable public key: {public[:16]}…") from exc
    ephemeral = X25519PrivateKey.generate()
    from cryptography.hazmat.primitives import serialization
    shared = ephemeral.exchange(recipient)
    nonce = os.urandom(12)
    ciphertext = AESGCM(_key(shared, context)).encrypt(
        nonce, _pad(text.encode()), context.encode())
    envelope = {
        "e": _b64e(ephemeral.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)),
        "n": _b64e(nonce),
        "c": _b64e(ciphertext),
    }
    return f"{MARKER} {_b64e(json.dumps(envelope, separators=(',', ':')).encode())}"


def is_sealed(text: str) -> bool:
    return text.strip().startswith(MARKER)
