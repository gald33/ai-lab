"""`switchboard.js` against the Python that defines the format.

**A JS implementation checked only by JS agrees with itself perfectly while
agreeing with nobody else.** That is the whole reason this file exists, and it
is why every assertion below crosses the language boundary: Python seals and
the browser opens it, then the browser seals and Python opens that. Neither
half is ever compared against its own output.

The failure this is written against is silent. A wrong byte in an HKDF `info`,
a NUL written as a space, a JSON key out of order -- none of them raises
anything at the point of the mistake. What happens instead is an envelope that
does not open and a signature nobody accepts, at the moment a hand is trying to
trade against a clock that does not stop.

Run it here with a browser installed, or in the `drawing-quick` CI job, which
has one. That job sets `ISLAND_REQUIRE_BROWSER`, which turns every skip below
into a failure -- for the reason `render.py --require` exists: a skip and a
pass are the same tick.

    python -m pytest games/island/tests/test_hand_crypto.py -q
"""

from __future__ import annotations

import json
import os
import pathlib


import pytest

from games.island.hand import fixtures

HAND = pathlib.Path(__file__).resolve().parent.parent / "hand"


def _missing(why: str):
    if os.environ.get("ISLAND_REQUIRE_BROWSER"):
        pytest.fail(f"{why}, and ISLAND_REQUIRE_BROWSER is set: this run "
                    f"checked no cryptography at all")
    pytest.skip(why)


# The page the browser loads. It imports the module under test as a module --
# not a concatenated copy -- so what is exercised is the file that ships.
_PAGE = """<!doctype html><meta charset=utf-8><title>hand crypto</title>
<script type=module>
import * as sb from './switchboard.js';

const fixtures = {fixtures};

async function identity(wire) {{
  // A page in service generates non-extractable keys and imports nothing;
  // the test needs a *known* identity, which is what PKCS#8 is here for.
  const der = (b64) => sb.b64d(b64);
  const signing = {{
    privateKey: await crypto.subtle.importKey(
      'pkcs8', der(wire.signingPkcs8), 'Ed25519', false, ['sign']),
    publicKey: await crypto.subtle.importKey(
      'raw', sb.b64d(wire.publicKey), 'Ed25519', false, ['verify']),
  }};
  const exchange = {{
    privateKey: await crypto.subtle.importKey(
      'pkcs8', der(wire.exchangePkcs8), 'X25519', false, ['deriveBits']),
  }};
  return {{ signing, exchange,
           publicKey: wire.publicKey, exchangeKey: wire.exchangeKey }};
}}

async function run() {{
  const out = {{}};
  const hand = await identity(fixtures.hand);
  const cipher = await sb.WorkspaceCipher.fromKey(
    fixtures.workspaceKey, fixtures.workspace, {{ epochPeriod: 0 }});

  // --- what Python made, opened here --------------------------------------
  const m = fixtures.message;
  out.payload = sb.b64e(sb.messagePayload(
    {{ sender: m.sender, channel: m.channel, seq: m.seq, body: m.body }}));
  out.verifiedPythonSignature = await sb.verify(
    fixtures.hand.publicKey, sb.b64d(m.payload), m.signature);
  out.openedSealed = await cipher.unseal(
    fixtures.sealed.envelope, fixtures.sealed.context);
  out.openedSealedAtEpoch = await cipher.unseal(
    fixtures.sealedAtEpoch.envelope, fixtures.sealedAtEpoch.context);
  out.openedWhisper = await sb.unsealFromPeer(
    fixtures.whisper.envelope,
    {{ identity: hand, peerExchangeKey: fixtures.peer.exchangeKey,
      context: fixtures.whisper.context }});
  out.blindChannel = await cipher.blindChannel(fixtures.blind.channel.in);
  out.blindAgent = await cipher.blindChannel(fixtures.blind.agent.in);
  out.blindHubForm = await cipher.blindChannel(fixtures.blind.hubForm.in);

  // --- what this makes, for Python to open --------------------------------
  out.signature = await sb.sign(hand, sb.messagePayload(
    {{ sender: m.sender, channel: m.channel, seq: m.seq, body: m.body }}));
  out.sealedHere = await cipher.seal(m.body, fixtures.sealed.context);
  out.whisperedHere = await sb.sealToPeer(
    m.body, {{ identity: hand, peerExchangeKey: fixtures.peer.exchangeKey,
              context: fixtures.whisper.context }});

  // --- padding, which no round-trip can see --------------------------------
  // A wrong bucket still decrypts: `unpad` reads the length it was given, so
  // an implementation that padded to the wrong size would interoperate
  // perfectly while announcing plaintext lengths the buckets exist to hide.
  // It has to be checked against the table itself, and against the one
  // observable it does move -- how long the ciphertext comes out.
  out.padBuckets = fixtures.padBuckets.lengths.map(sb.padBucket);
  out.sealedLength = sb.b64d(out.sealedHere.c).length;

  // --- the two refusals ----------------------------------------------------
  out.refusedWorkspaceEnvelopeAsWhisper = await sb.unsealFromPeer(
    fixtures.sealed.envelope,
    {{ identity: hand, peerExchangeKey: fixtures.peer.exchangeKey,
      context: fixtures.sealed.context }}).then(() => null, (e) => String(e.message));
  out.refusedWhisperAsWorkspace = await cipher.unseal(
    fixtures.whisper.envelope, fixtures.whisper.context)
    .then(() => null, (e) => String(e.message));
  out.refusedNonStringBody = (() => {{
    try {{ sb.messagePayload({{ sender: 'T1', channel: 'c', seq: 1, body: 1.0 }});
           return null; }}
    catch (e) {{ return String(e.message); }}
  }})();

  return out;
}}

run().then(
  (out) => {{ window.RESULT = out; }},
  (err) => {{ window.RESULT = {{ error: String(err && err.stack || err) }}; }},
);
</script>
"""


def _serve(directory):
    """A localhost server for the page, because `file://` cannot do this.

    Two reasons, and both are properties of browsers rather than of this test.
    An ES module imported from a `file://` page is refused as a cross-origin
    request -- the origin is opaque, so nothing is ever same-origin with it.
    And `crypto.subtle` is only defined in a secure context, which `http://`
    is not, except on localhost, which is exactly why this is 127.0.0.1.

    It is also the shape the hand's page really runs in: served, on one
    origin, which is what `games/island.md` requires for IndexedDB to keep a
    key across the lobby and the game.
    """
    import functools
    import http.server
    import threading

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(directory))
    # Quiet: a request log per asset says nothing a failure would not.
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _run_in_browser(tmp_path):
    """Load the module in a real browser and return what it computed."""
    try:
        from playwright import sync_api as play
    except ImportError:
        _missing("no playwright to drive a page with")

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)

    # The module is imported by URL, so it has to sit beside the page. Copied
    # rather than symlinked: what runs must be the committed bytes.
    (tmp_path / "switchboard.js").write_text((HAND / "switchboard.js").read_text())
    page = tmp_path / "crypto.html"
    page.write_text(_PAGE.format(fixtures=json.dumps(fixtures.build())))
    server = _serve(tmp_path)
    url = f"http://127.0.0.1:{server.server_address[1]}/crypto.html"

    with play.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(
                executable_path=str(chrome) if chrome else None)
        except Exception as exc:                       # noqa: BLE001
            _missing(f"no chromium to drive a page with: {exc!r}")
        tab = browser.new_page()
        errors: list[str] = []
        tab.on("pageerror", lambda e: errors.append(str(e)))
        tab.goto(url)
        try:
            tab.wait_for_function("window.RESULT !== undefined", timeout=15_000)
        except Exception as exc:                       # noqa: BLE001
            browser.close()
            server.shutdown()
            pytest.fail(f"the module never finished: {exc!r}; page errors: {errors}")
        result = tab.evaluate("window.RESULT")
        browser.close()
    server.shutdown()

    if result.get("error"):
        pytest.fail(f"the module threw: {result['error']}")
    return result


@pytest.fixture(scope="module")
def ran(tmp_path_factory):
    return _run_in_browser(tmp_path_factory.mktemp("hand-crypto"))


# --- what Python made, opened in the browser -------------------------------

def test_the_signed_payload_is_byte_for_byte_the_python_one(ran):
    """The canonicalisation, which is the likeliest thing to be quietly wrong.

    Python serialises with sorted keys and no whitespace; `JSON.stringify`
    sorts nothing, so `switchboard.js` writes the four keys in sorted order by
    hand. Nothing about that arrangement fails loudly if it drifts -- the
    signature simply stops verifying, in someone else's process.
    """
    assert ran["payload"] == fixtures.build()["message"]["payload"]


def test_the_browser_verifies_a_python_signature(ran):
    assert ran["verifiedPythonSignature"] is True


def test_the_browser_opens_what_python_sealed_to_the_workspace(ran):
    assert ran["openedSealed"] == fixtures.BODY


def test_the_browser_follows_the_message_epoch_and_not_a_clock(ran):
    """An epoch subkey, derived from the envelope's own `e`.

    The hub rotates payload subkeys every 900s by default, so a client that
    only ever derived epoch 0 would open nothing anybody wrote -- and would
    look, from the page, exactly like a wrong key.
    """
    assert ran["openedSealedAtEpoch"] == fixtures.BODY


def test_the_browser_opens_a_whisper_addressed_to_it(ran):
    """The dealt private half, which is the whole reason a hand needs X25519.

    Sealed by the peer to this identity's exchange key: the pairwise key, the
    sorted pair in HKDF's `info`, and the `switchboard/v1/ask` AAD all have to
    be right together, and no subset of them fails visibly.
    """
    assert ran["openedWhisper"] == fixtures.DEALT


def test_blinding_agrees_with_python(ran):
    built = fixtures.build()["blind"]
    assert ran["blindChannel"] == built["channel"]["out"]
    assert ran["blindAgent"] == built["agent"]["out"]
    # A hub-form id passes through untouched -- blinding it twice produces a
    # channel no recipient's inbox resolves to.
    assert ran["blindHubForm"] == built["hubForm"]["in"]


# --- what the browser made, opened in Python -------------------------------
#
# The direction that a one-way fixture would have missed entirely: a client
# that opens correctly and seals garbage passes every test above.

def test_python_verifies_a_signature_the_browser_made(ran):
    assert fixtures.verify_signature(
        fixtures.build()["message"]["payload"], ran["signature"])


def test_python_opens_what_the_browser_sealed_to_the_workspace(ran):
    assert fixtures.open_workspace(ran["sealedHere"], "messages.body") == fixtures.BODY


def test_python_opens_what_the_browser_whispered(ran):
    assert fixtures.open_whisper(ran["whisperedHere"], "messages.body") == fixtures.BODY


def test_padding_matches_python_bucket_for_bucket(ran):
    """The one divergence a round-trip cannot see.

    `unpad` reads the length the payload declares, so a client padding to the
    wrong bucket decrypts correctly everywhere and quietly gives back the leak
    the buckets exist to close: ciphertext length reporting plaintext length
    to the byte. Nothing fails; the privacy is just gone. So the table is
    compared directly, and so is the length of a real sealed envelope.
    """
    built = fixtures.build()["padBuckets"]
    assert ran["padBuckets"] == built["buckets"]
    assert ran["sealedLength"] == built["sealedLength"]


# --- the refusals ----------------------------------------------------------

def test_the_two_ciphers_refuse_each_other(ran):
    """Symmetric with Python's, and for its reason: silently accepting either
    envelope in the other's place would make a mix-up look like it worked."""
    assert "sealed to the workspace" in (ran["refusedWorkspaceEnvelopeAsWhisper"] or "")
    assert "whisper" in (ran["refusedWhisperAsWorkspace"] or "")


def test_a_non_string_body_is_refused_rather_than_signed_wrongly(ran):
    """`1.0` is `1.0` in Python and `1` in JavaScript.

    A client that signed it would produce a signature that verifies nowhere,
    which is worse than not signing: the refusal is the feature.
    """
    assert "string bodies only" in (ran["refusedNonStringBody"] or "")
