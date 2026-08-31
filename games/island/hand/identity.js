// The driver's seat identity, and where it lives between two pages.
//
// One origin serves the hand's lobby and the hand's island, so IndexedDB
// carries the key from taking a seat to playing it -- which is why
// `games/island.md` requires the pages to be *served* rather than opened: a
// `file://` page has an opaque origin and no dependable storage.
//
// **The keys are extractable, and that is a reversal made on purpose.** The
// lobby witnesses one signing key per seat and the manager refuses any line
// that does not match it, so a driver who wants an agent playing alongside
// them must hand that agent the same key. A non-extractable key cannot be
// handed to anybody. What is left of the mitigation is smaller and real: an
// identity here is minted **per seat, per game, and never reused**, so
// handing it out -- or losing it to a script on this origin, which shares
// with the viewer -- costs exactly one game on a hub where everything
// expires within a day.

import { b64e } from "./switchboard.js";

const DB = "island-hand";
const STORE = "seats";

function open() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB, 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE, { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function run(db, mode, work) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, mode);
    const request = work(tx.objectStore(STORE));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function pkcs8(key) {
  return b64e(new Uint8Array(await crypto.subtle.exportKey("pkcs8", key)));
}

async function raw(key) {
  return b64e(new Uint8Array(await crypto.subtle.exportKey("raw", key)));
}

/**
 * Mint an identity for one seat at one table.
 *
 * `id` is the table's id, so a second table gets a second identity rather
 * than reusing the first. Nothing here rotates or refreshes a key: a seat
 * that has played is finished, and its key is worth no more than the game it
 * played.
 */
export async function mint(id) {
  const signing = await crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"]);
  const exchange = await crypto.subtle.generateKey("X25519", true, ["deriveBits"]);
  const record = {
    id,
    createdAt: Date.now(),
    publicKey: await raw(signing.publicKey),
    exchangeKey: await raw(exchange.publicKey),
    signingPkcs8: await pkcs8(signing.privateKey),
    exchangePkcs8: await pkcs8(exchange.privateKey),
  };
  const db = await open();
  await run(db, "readwrite", (store) => store.put(record));
  db.close();
  return hydrate(record);
}

/** The identity for a table, or `null` if this browser holds none. */
export async function load(id) {
  const db = await open();
  const record = await run(db, "readonly", (store) => store.get(id));
  db.close();
  return record ? hydrate(record) : null;
}

/** Every seat this browser is holding a key for, newest first. */
export async function all() {
  const db = await open();
  const records = await run(db, "readonly", (store) => store.getAll());
  db.close();
  return records.sort((a, b) => b.createdAt - a.createdAt);
}

/** Forget a seat's key. There is no recovery, and the page says so. */
export async function forget(id) {
  const db = await open();
  await run(db, "readwrite", (store) => store.delete(id));
  db.close();
}

/** The stored record as `switchboard.js` wants an identity. */
async function hydrate(record) {
  const signing = {
    privateKey: await crypto.subtle.importKey(
      "pkcs8", bytes(record.signingPkcs8), "Ed25519", true, ["sign"]),
    publicKey: await crypto.subtle.importKey(
      "raw", bytes(record.publicKey), "Ed25519", true, ["verify"]),
  };
  const exchange = {
    privateKey: await crypto.subtle.importKey(
      "pkcs8", bytes(record.exchangePkcs8), "X25519", true, ["deriveBits"]),
  };
  return {
    id: record.id,
    signing,
    exchange,
    publicKey: record.publicKey,
    exchangeKey: record.exchangeKey,
    // What a driver pastes into an agent's brief. Named for what it is, so
    // nobody hands it over without noticing what they are handing over.
    secrets: { signingPkcs8: record.signingPkcs8,
               exchangePkcs8: record.exchangePkcs8 },
  };
}

function bytes(b64) {
  const raw = atob(b64.replace(/-/g, "+").replace(/_/g, "/") +
                   "=".repeat((4 - (b64.length % 4)) % 4));
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}
