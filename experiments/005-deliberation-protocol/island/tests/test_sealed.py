"""The one property the private channel exists for, and the ways it can fail."""

from __future__ import annotations

import pytest

from island.sealed import MARKER, BoxKey, SealError, is_sealed, seal_to

CONTEXT = "island.private-half"


def test_only_the_intended_recipient_opens_it():
    """The whole point: a third party holding everything public -- the board,
    the ciphertext, its own perfectly good key -- still cannot read it."""
    seat = BoxKey.generate()
    rival = BoxKey.generate()
    blob = seal_to(seat.public, "You are T1. Your taste weights: ...", CONTEXT)

    assert seat.open(blob, CONTEXT) == "You are T1. Your taste weights: ..."
    with pytest.raises(SealError):
        rival.open(blob, CONTEXT)


@pytest.mark.parametrize("text", [
    "",
    "PRODUCE iron=1.0",
    "x" * 63, "x" * 64, "x" * 65,          # either side of a bucket edge
    "You are T1. " + "taste " * 200,        # several buckets up
    "unicode: \u00e9\u00e8\u00ea and a tab\tand a newline\n",
])
def test_what_goes_in_comes_back_exactly(text):
    """Byte-exact, not merely close. The padding boundary was wrong once and
    a `startswith` assertion did not notice; this is what noticed."""
    seat = BoxKey.generate()
    assert seat.open(seal_to(seat.public, text, CONTEXT), CONTEXT) == text


def test_a_sealed_line_announces_itself():
    """A reader that cannot open it must still know what it is looking at,
    rather than counting a blob as talk."""
    seat = BoxKey.generate()
    blob = seal_to(seat.public, "PRODUCE iron=0.7 salt=0.3", CONTEXT)

    assert blob.startswith(MARKER)
    assert is_sealed(blob) and not is_sealed("PRODUCE iron=0.7")
    assert "iron" not in blob and "0.7" not in blob


def test_a_value_cannot_be_replayed_into_another_context():
    """Context is bound into the derivation and the AEAD, so a private half
    cannot be lifted and presented as a production plan."""
    seat = BoxKey.generate()
    blob = seal_to(seat.public, "You are T1.", CONTEXT)

    with pytest.raises(SealError):
        seat.open(blob, "island.produce")


def test_tampering_is_refused_rather_than_half_read():
    seat = BoxKey.generate()
    blob = seal_to(seat.public, "PRODUCE iron=1.0", CONTEXT)
    body = blob[len(MARKER):].strip()
    mangled = f"{MARKER} {body[:-4]}AAAA"

    with pytest.raises(SealError):
        seat.open(mangled, CONTEXT)


def test_two_sealings_of_one_value_differ():
    """Fresh ephemeral key and nonce every time, so an eavesdropper cannot
    tell that a trader produced the same plan twice."""
    seat = BoxKey.generate()
    once = seal_to(seat.public, "PRODUCE iron=1.0", CONTEXT)
    twice = seal_to(seat.public, "PRODUCE iron=1.0", CONTEXT)

    assert once != twice
    assert seat.open(once, CONTEXT) == seat.open(twice, CONTEXT)


@pytest.mark.parametrize("plan,other", [
    ("PRODUCE iron=1.0", "PRODUCE bread=0.5 cloth=0.2 iron=0.2 salt=0.1"),
    ("PRODUCE a=1.0", "PRODUCE bread=0.25 cloth=0.25 iron=0.25 salt=0.25"),
])
def test_length_does_not_report_how_many_goods_a_plan_named(plan, other):
    """Padding, and the reason for it: an unpadded ciphertext would let every
    spectator count the goods in a sealed plan."""
    seat = BoxKey.generate()
    assert len(seal_to(seat.public, plan, CONTEXT)) == \
           len(seal_to(seat.public, other, CONTEXT))


def test_a_bad_public_key_fails_at_the_seal_not_later():
    with pytest.raises(SealError, match="not a usable public key"):
        seal_to("obviously-not-a-key", "PRODUCE iron=1.0", CONTEXT)


def test_opening_something_that_is_not_sealed_says_so():
    seat = BoxKey.generate()
    with pytest.raises(SealError, match=f"not a {MARKER}"):
        seat.open("PRODUCE iron=1.0", CONTEXT)


def test_the_private_half_never_appears_in_a_repr():
    """A key that reaches a log or a traceback is a key that has leaked."""
    seat = BoxKey.generate()
    assert "X25519PrivateKey" not in repr(seat)
    assert seat.public[:12] in repr(seat)
