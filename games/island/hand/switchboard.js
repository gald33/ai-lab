// The hand's half of Switchboard's cryptography, in the browser.
//
// **This file is a second implementation of somebody else's format**, which is
// the thing this repository refuses everywhere it can. It exists because the
// hand plays from a browser, phone included (`games/island.md`, "The hand's
// client is a browser"), and a browser cannot run `switchboard`'s Python. So
// the rule that keeps it honest is the one in `tests/test_hand_crypto.py`:
// every function here is checked against bytes Python produced, never against
// this file's own idea of what it should produce. A JS implementation checked
// only by JS agrees with itself perfectly while agreeing with nobody else.
//
// Everything below mirrors `switchboard/crypto.py` and `switchboard/signing.py`
// at 1.2.3. Where a constant looks arbitrary it is theirs, and the comment says
// which of their names it carries. Every NUL separator is written as the
// escape `\u0000`, never as a literal: a real NUL in this file would be
// invisible in every editor and diff that matters.

const ENVELOPE_KEY = "$swb";       // crypto.ENVELOPE_KEY
const ENVELOPE_VERSION = 1;        // crypto.ENVELOPE_VERSION
const WHISPER_MARKER = "ask";      // crypto.WHISPER_MARKER -- the wire value kept
                                   // from the release this shipped under, while
                                   // the tool is called `whisper` everywhere else.
const BLIND_BYTES = 16;            // crypto.BLIND_BYTES
const PAD_MIN = 64;                // crypto.PAD_MIN
const PAD_MAX_POWER = 4096;        // crypto.PAD_MAX_POWER
const PAD_MARKER = 0x00;           // crypto._PAD_MARKER
const DEFAULT_EPOCH_PERIOD = 900;  // crypto.DEFAULT_EPOCH_PERIOD

const utf8 = new TextEncoder();
const fromUtf8 = new TextDecoder();

// --- base64url, as `crypto._b64e`/`_b64d`: urlsafe alphabet, padding stripped.

export function b64e(bytes) {
  let s = "";
  for (const byte of bytes) s += String.fromCharCode(byte);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64d(text) {
  const padded = text.replace(/-/g, "+").replace(/_/g, "/") +
    "=".repeat((4 - (text.length % 4)) % 4);
  const raw = atob(padded);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

/** `crypto._decode_key`: the shapes people actually paste. */
export function decodeKey(key) {
  const text = key.trim();
  if (text.startsWith("hex:")) {
    const hex = text.slice(4);
    const out = new Uint8Array(hex.length / 2);
    for (let i = 0; i < out.length; i++) out[i] = parseInt(hex.substr(i * 2, 2), 16);
    return out;
  }
  return b64d(text);
}

function concat(...parts) {
  const total = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(total);
  let at = 0;
  for (const part of parts) { out.set(part, at); at += part.length; }
  return out;
}

// --- HKDF, padding, AEAD --------------------------------------------------

/** `crypto._derive`: HKDF-SHA256, no salt, `info` + NUL + workspace. */
async function derive(raw, info, workspace) {
  const base = await crypto.subtle.importKey("raw", raw, "HKDF", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "HKDF", hash: "SHA-256", salt: new Uint8Array(0),
      info: concat(info, new Uint8Array([0]), utf8.encode(workspace)) },
    base, 256);
  return new Uint8Array(bits);
}

/** `crypto.pad_bucket`. */
export function padBucket(length) {
  if (length <= PAD_MIN) return PAD_MIN;
  if (length >= PAD_MAX_POWER) return (Math.floor(length / PAD_MAX_POWER) + 1) * PAD_MAX_POWER;
  let size = PAD_MIN;
  while (size < length) size *= 2;
  return size;
}

/** `crypto._pad`: marker, 4-byte big-endian length, data, filler. */
function pad(plaintext) {
  const length = new Uint8Array(4);
  new DataView(length.buffer).setUint32(0, plaintext.length, false);
  const framed = concat(length, plaintext);
  const target = padBucket(framed.length + 1);
  return concat(new Uint8Array([PAD_MARKER]), framed,
                new Uint8Array(target - framed.length - 1));
}

/** `crypto._unpad`. An unpadded payload from another client passes through. */
function unpad(plaintext) {
  if (!plaintext.length || plaintext[0] !== PAD_MARKER) return plaintext;
  const view = new DataView(plaintext.buffer, plaintext.byteOffset, plaintext.byteLength);
  const length = view.getUint32(1, false);
  if (length > plaintext.length - 5) {
    throw new Error("padded payload declares a length beyond its own size");
  }
  return plaintext.slice(5, 5 + length);
}

async function aesKey(raw) {
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}

/** `crypto._seal_bytes`. */
async function sealBytes(keyBytes, plaintext, aad) {
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: aad },
    await aesKey(keyBytes), plaintext);
  return { [ENVELOPE_KEY]: ENVELOPE_VERSION, n: b64e(nonce),
           c: b64e(new Uint8Array(ciphertext)) };
}

/** `crypto._unseal_bytes`. Raises the same shape of complaint they do. */
async function unsealBytes(keyBytes, envelope, aad, context) {
  try {
    const plain = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: b64d(envelope.n), additionalData: aad },
      await aesKey(keyBytes), b64d(envelope.c));
    return new Uint8Array(plain);
  } catch (err) {
    throw new Error(`could not open the value at ${context}: wrong key, ` +
                    "tampering, or a mismatched context");
  }
}

/** `crypto.is_sealed`, as much of it as a reader here needs. */
export function isSealed(value) {
  return !!value && typeof value === "object" && value[ENVELOPE_KEY] === ENVELOPE_VERSION;
}

// The one serialisation both languages have to agree on. Python writes
// `json.dumps(value, separators=(",", ":"))`; `JSON.stringify` matches it for
// strings, arrays and flat objects with ASCII keys, which is everything the
// island sends. It does NOT match for floats (`1.0` against `1`), so nothing
// here may seal a bare number -- see `tests/test_hand_crypto.py`.
function dumps(value) { return utf8.encode(JSON.stringify(value)); }

// --- the workspace cipher --------------------------------------------------

export class WorkspaceCipher {
  constructor(workspace, raw, payloadKey, blindKey, period) {
    this.workspace = workspace;
    this._raw = raw;
    this._payloadKey = payloadKey;
    this._blindKey = blindKey;
    this._period = period;
    this._subkeys = new Map();
  }

  /** `WorkspaceCipher.from_key`, including its two refusals. */
  static async fromKey(key, workspace, { epochPeriod = DEFAULT_EPOCH_PERIOD } = {}) {
    const raw = decodeKey(key);
    if (raw.length < 32) {
      throw new Error(`workspace key must be at least 32 bytes, got ${raw.length}`);
    }
    if (new Set(raw).size <= 2) {
      throw new Error("workspace key looks like a placeholder (almost no distinct bytes)");
    }
    return new WorkspaceCipher(
      workspace, raw,
      await derive(raw, utf8.encode("switchboard/v1/payload"), workspace),
      await derive(raw, utf8.encode("switchboard/v1/identifier"), workspace),
      epochPeriod);
  }

  /** `_payload_key_for`: epoch 0 is the original derivation, unchanged. */
  async _payloadKeyFor(epoch) {
    if (!epoch) return this._payloadKey;
    if (!this._subkeys.has(epoch)) {
      this._subkeys.set(epoch, await derive(
        this._raw, utf8.encode("switchboard/v1/payload"),
        `${this.workspace}\u0000${epoch}`));
    }
    return this._subkeys.get(epoch);
  }

  currentEpoch(now) {
    if (this._period <= 0) return 0;
    return Math.floor((now === undefined ? Date.now() / 1000 : now) / this._period);
  }

  /** `WorkspaceCipher._aad`: the workspace is bound in with the context. */
  _aad(context) {
    return utf8.encode(`switchboard/v1\u0000${this.workspace}\u0000${context}`);
  }

  async seal(value, context) {
    const epoch = this.currentEpoch();
    const envelope = await sealBytes(
      await this._payloadKeyFor(epoch), pad(dumps(value)), this._aad(context));
    // Omitted at epoch 0 so an older reader still understands the bytes.
    if (epoch) envelope.e = epoch;
    return envelope;
  }

  async unseal(envelope, context) {
    if (!isSealed(envelope)) {
      throw new Error(`expected an encrypted value at ${context} but found plaintext`);
    }
    if (envelope.m === WHISPER_MARKER) {
      throw new Error(`the value at ${context} is sealed to one peer with ` +
                      "whisper, not to the workspace");
    }
    // The epoch comes from the message and never from our own clock.
    const epoch = envelope.e === undefined ? 0 : envelope.e;
    if (!Number.isInteger(epoch) || epoch < 0) throw new Error(`invalid key epoch ${epoch}`);
    const plain = await unsealBytes(
      await this._payloadKeyFor(epoch), envelope, this._aad(context), context);
    return JSON.parse(fromUtf8.decode(unpad(plain)));
  }

  /** `WorkspaceCipher.blind`: HMAC-SHA256, truncated, deterministic. */
  async blind(identifier, domain) {
    const key = await crypto.subtle.importKey(
      "raw", this._blindKey, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const mac = new Uint8Array(await crypto.subtle.sign(
      "HMAC", key, utf8.encode(`${domain}\u0000${identifier}`)));
    return b64e(mac.slice(0, BLIND_BYTES));
  }

  /** `blind_channel`: a hub-form id passes through, a local alias is blinded. */
  async blindChannel(channel) {
    if (!channel.startsWith("@")) return this.blind(channel, "channel");
    const target = channel.slice(1);
    // `_HUB_FORM_ID`: BLIND_BYTES of base64url and nothing else.
    const width = Math.ceil((BLIND_BYTES * 4) / 3);
    if (new RegExp(`^[A-Za-z0-9_-]{${width}}$`).test(target)) return channel;
    return "@" + await this.blind(target, "agent");
  }
}

// --- signing ---------------------------------------------------------------

/** `signing.message_payload`: the exact bytes a message signature covers.
 *
 *  Python serialises with sorted keys and no whitespace. `JSON.stringify`
 *  does not sort, so the four keys are written here in sorted order by hand
 *  -- `b`, `by`, `ch`, `n` -- and the body is refused unless it is a string,
 *  because a nested object would need sorting all the way down and a float
 *  formats differently in the two languages.
 */
export function messagePayload({ sender, channel, seq, body }) {
  if (typeof body !== "string") {
    throw new Error("the hand's client signs string bodies only");
  }
  return utf8.encode(JSON.stringify({ b: body, by: sender, ch: channel, n: seq }));
}

/** A fresh identity: Ed25519 to sign with, X25519 to seal with.
 *
 *  Non-extractable, so the page can use them and nothing -- a bug, a pasted
 *  script -- can lift the private halves out. That is the whole mitigation
 *  for sharing an origin with the viewer, and it stops theft, not use.
 */
export async function generateIdentity() {
  const signing = await crypto.subtle.generateKey("Ed25519", false, ["sign", "verify"]);
  const exchange = await crypto.subtle.generateKey("X25519", false, ["deriveBits"]);
  return {
    signing,
    exchange,
    publicKey: b64e(new Uint8Array(await crypto.subtle.exportKey("raw", signing.publicKey))),
    exchangeKey: b64e(new Uint8Array(await crypto.subtle.exportKey("raw", exchange.publicKey))),
  };
}

export async function sign(identity, message) {
  return b64e(new Uint8Array(
    await crypto.subtle.sign("Ed25519", identity.signing.privateKey, message)));
}

/** `signing.verify`: false for a bad signature, never an exception. */
export async function verify(publicKey, message, signature) {
  try {
    const key = await crypto.subtle.importKey(
      "raw", b64d(publicKey), "Ed25519", false, ["verify"]);
    return await crypto.subtle.verify("Ed25519", key, b64d(signature), message);
  } catch {
    return false;
  }
}

// --- the room's write key ---------------------------------------------------
//
// Switchboard 2.0.0: a write-protected room is named by the hash of an
// Ed25519 public key, and the hub refuses any write the private half did not
// sign (`writekey.py`). The seed travels in a peer's invite as `wk`; a
// read-only invite has none, and a page holding one can read and never post.
// This is the JS half of `RoomWriteKey.sign_request`, and like every other
// half here it is checked against the Python (`test_hand_pages.py`), never
// against itself.

const WRITE_DOMAIN = "switchboard/v1/write-request";
const WRITE_TOKEN_PREFIX = "pk1_";
const ROOM_ID_INFO = "switchboard/room";
const ROOM_ID_VERSION = 1;
//: PKCS#8 wrapping of a raw 32-byte Ed25519 seed, which is the only form
//: WebCrypto imports a private key in. Constant for the algorithm.
const PKCS8_ED25519 = new Uint8Array([
  0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70,
  0x04, 0x22, 0x04, 0x20,
]);

/** `RoomWriteKey.from_seed`: the private key, its token and the room it names. */
export async function writerFromSeed(seed) {
  const raw = b64d(seed);
  if (raw.length !== 32) throw new Error("a write key decodes to 32 bytes");
  const pkcs8 = concat(PKCS8_ED25519, raw);
  const privateKey = await crypto.subtle.importKey(
    "pkcs8", pkcs8, "Ed25519", true, ["sign"]);
  // The public half is not derivable through WebCrypto from a pkcs8 import,
  // so it is read back out of the JWK form, which carries `x`.
  const jwk = await crypto.subtle.exportKey("jwk", privateKey);
  const token = WRITE_TOKEN_PREFIX + jwk.x.replace(/=+$/, "");
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", concat(
    utf8.encode(ROOM_ID_INFO), new Uint8Array([0, ROOM_ID_VERSION]), b64d(jwk.x))));
  const workspace = "ws_" + b64e(digest).slice(0, 22);
  return { privateKey, token, workspace };
}

/** `writekey.request_digest`, then `sign_request`: the two headers. */
export async function signRequest(writer, method, path, query, bodyText) {
  const ts = Math.floor(Date.now() / 1000);
  const nonce = b64e(crypto.getRandomValues(new Uint8Array(12)));
  const bodyHash = new Uint8Array(await crypto.subtle.digest(
    "SHA-256", utf8.encode(bodyText || "")));
  const zero = new Uint8Array([0]);
  const parts = [
    utf8.encode(WRITE_DOMAIN), utf8.encode(method.toUpperCase()), utf8.encode(path),
    utf8.encode(query), utf8.encode(String(ts)), utf8.encode(nonce), bodyHash,
  ];
  const digest = parts.reduce((acc, p, i) => i ? concat(acc, zero, p) : p);
  const sig = b64e(new Uint8Array(await crypto.subtle.sign("Ed25519", writer.privateKey, digest)));
  return {
    "X-Switchboard-Write-Key": writer.token,
    "X-Switchboard-Write-Sig": `${ts}.${nonce}.${sig}`,
  };
}

// --- sealed to one peer ----------------------------------------------------

/** `crypto._derive_whisper_key`: ECDH, then HKDF binding the unordered pair. */
async function whisperKey(identity, peerExchangeKey) {
  const peer = await crypto.subtle.importKey("raw", b64d(peerExchangeKey), "X25519", false, []);
  const secret = new Uint8Array(await crypto.subtle.deriveBits(
    { name: "X25519", public: peer }, identity.exchange.privateKey, 256));
  // Sorted, so the two ends land on the same 32 bytes without negotiating.
  const pair = [identity.exchangeKey, peerExchangeKey].sort().join("\u0000");
  const base = await crypto.subtle.importKey("raw", secret, "HKDF", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "HKDF", hash: "SHA-256", salt: new Uint8Array(0),
      info: concat(utf8.encode("switchboard/v1/ask\u0000"), utf8.encode(pair)) },
    base, 256);
  return new Uint8Array(bits);
}

/** `crypto._whisper_aad`. No workspace: the pair key already binds two identities. */
function whisperAad(context) {
  return utf8.encode(`switchboard/v1/ask\u0000${context}`);
}

export async function sealToPeer(value, { identity, peerExchangeKey, context }) {
  const envelope = await sealBytes(
    await whisperKey(identity, peerExchangeKey), pad(dumps(value)), whisperAad(context));
  envelope.m = WHISPER_MARKER;
  return envelope;
}

/** `crypto.unseal_from_peer`. `peerExchangeKey` is the *sender's*. */
export async function unsealFromPeer(envelope, { identity, peerExchangeKey, context }) {
  if (!isSealed(envelope)) {
    throw new Error(`expected a value sealed with whisper at ${context}`);
  }
  if (envelope.m !== WHISPER_MARKER) {
    throw new Error(`the value at ${context} is sealed to the workspace, not to you`);
  }
  const plain = await unsealBytes(
    await whisperKey(identity, peerExchangeKey), envelope, whisperAad(context), context);
  return JSON.parse(fromUtf8.decode(unpad(plain)));
}
