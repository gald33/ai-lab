// Talking to a Switchboard hub from the page: register, post, read.
//
// Only what a driver needs, which is much less than the library does. There
// is no lease here, no rendezvous, no room minting -- the page takes a seat
// and plays it, and every verb it does not have is a verb nobody can call by
// accident.
//
// **The shapes below were read off a real client rather than out of its
// source**, because the encryption happens at the transport edge and the
// wire format is not obvious from any single method:
//
//   POST /agents/register  agent_id blinded; name, pubkey and exchange_key
//                          each sealed with `seal_text` -- a JSON *string* of
//                          an envelope, not an envelope -- under the contexts
//                          `agent.name`, `agent.pubkey`, `agent.exchange_key`
//   POST /messages         channel blinded; agent_id blinded; body sealed as
//                          an object under `message.body`, wrapping
//                          `{b: <line>, ch: <plaintext channel>, s: <sig>}`
//   GET  /channels/<blinded channel>
//
// The signature travels *inside* the ciphertext, which is the point: a hub
// cannot read it, alter it, or strip it without breaking the AEAD tag. And it
// is computed over the **blinded** sender and the **blinded** channel, since
// that is what a reader has to look it up against.
//
// `tests/test_hand_pages.py` posts from this page and reads it back with a
// real Python client, which is the only check that any of the above is right.

import { WorkspaceCipher, messagePayload, sign, isSealed, unsealFromPeer,
         sealToPeer, writerFromSeed, signRequest, WHISPER_CONTEXT,
         WHISPER_MARKERS } from "./switchboard.js";

export class Hub {
  constructor(url, token, cipher, identity, alias) {
    this.url = url.replace(/\/$/, "");
    this.token = token;
    this.cipher = cipher;
    this.identity = identity;
    this.alias = alias;
    this.agentId = null;      // the blinded form, filled in by `open`
    this._seq = 0;
    // Blinded sender -> exchange key, learned from the roster. Both sides
    // must have read the roster before a whisper opens, which is the one
    // thing about `whisper` no example makes obvious -- and the bug that
    // blinded both traders in g5 for eight episodes.
    this._peers = new Map();
  }

  static async open({ url, token, workspace, key, identity, alias, writeKey }) {
    const cipher = await WorkspaceCipher.fromKey(key, workspace);
    const hub = new Hub(url, token, cipher, identity, alias);
    hub.agentId = await cipher.blind(alias, "agent");
    // A write-protected room (2.0.0, `ws_…`) takes no line the room's write
    // key did not sign. The key comes from the invite the lobby whispered to
    // this seat; a page without it -- a read-only invite -- reads and is
    // refused on every write, by the hub and not by this page's manners.
    // A key that names another room is refused here, loudly, the way the
    // Python client refuses it: every write would otherwise 403 with a
    // message that cannot say why.
    hub.writer = null;
    if (writeKey) {
      const writer = await writerFromSeed(writeKey);
      if (writer.workspace !== workspace) {
        throw new Error(`the write key names room ${writer.workspace}, not ${workspace}`);
      }
      hub.writer = writer;
    }
    return hub;
  }

  get workspace() { return this.cipher.workspace; }

  async _call(method, path, { body, params } = {}) {
    const url = new URL(this.url + path);
    for (const [k, v] of Object.entries(params || {})) url.searchParams.set(k, v);
    const text = body === undefined ? undefined : JSON.stringify(body);
    // Signed over exactly what goes on the wire -- method, path, query and
    // the serialised body -- so the hub verifies the same bytes. Every call
    // is signed, reads included: `/inbox` commits a cursor, and the hub
    // notes the signature on every guarded route.
    const signed = this.writer
      ? await signRequest(this.writer, method, url.pathname, url.search.slice(1), text)
      : {};
    const response = await fetch(url, {
      method,
      headers: {
        "content-type": "application/json",
        ...(this.token ? { authorization: `Bearer ${this.token}` } : {}),
        ...signed,
      },
      body: text,
    });
    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;
      try {
        const problem = await response.json();
        if (problem && problem.detail) detail = problem.detail;
      } catch { /* a non-JSON error body is still an error */ }
      throw new Error(detail);
    }
    return response.json();
  }

  /** `seal_text`: the envelope as a JSON string, for fields that stay strings
   *  on the wire. Not interchangeable with `seal` -- the hub stores what it is
   *  given and a reader unseals what it expects. */
  async _sealText(value, context) {
    return JSON.stringify(await this.cipher.seal(value, context));
  }

  async _openText(value, context) {
    if (typeof value !== "string") return value;
    let envelope;
    try { envelope = JSON.parse(value); } catch { return value; }
    if (!isSealed(envelope)) return value;
    try { return await this.cipher.unseal(envelope, context); }
    catch { return null; }
  }

  /** Publish this identity, so the lobby and the manager witness its key.
   *
   *  `ttl` is how long the row stays on the roster. **The hub's default is
   *  two minutes**, and a page has no heartbeat: on g27 (2026-09-04) the
   *  second seat arrived 126 seconds after the hand's JOIN, the hand's row
   *  had lapsed, and the lobby could not seal the room to it. The hub clamps
   *  at 3600 (`run_game.PRESENCE_CEILING`, measured), which covers a table's
   *  whole 900s wait and a round besides. */
  async register(name, { kind = "hand", ttl = 3600 } = {}) {
    return this._call("POST", "/agents/register", {
      body: {
        workspace: this.workspace,
        agent_id: this.agentId,
        name: await this._sealText(name, "agent.name"),
        kind,
        branch: null,
        task: null,
        channels: [],
        meta: {},
        ttl,
        pubkey: await this._sealText(this.identity.publicKey, "agent.pubkey"),
        exchange_key: await this._sealText(this.identity.exchangeKey,
                                           "agent.exchange_key"),
      },
    });
  }

  /** Everyone the hub knows here, with their names and exchange keys opened. */
  async roster() {
    const reply = await this._call("GET", "/agents",
                                   { params: { workspace: this.workspace } });
    const agents = [];
    for (const agent of reply.agents || []) {
      const exchangeKey = await this._openText(agent.exchange_key,
                                               "agent.exchange_key");
      if (exchangeKey) this._peers.set(agent.agent_id, exchangeKey);
      agents.push({
        ...agent,
        name: await this._openText(agent.name, "agent.name"),
        pubkey: await this._openText(agent.pubkey, "agent.pubkey"),
        exchange_key: exchangeKey,
      });
    }
    return agents;
  }

  /**
   * Post one line, signed.
   *
   * The signature covers sender, channel, sequence and body, so a line cannot
   * be replayed into another channel and a gap in the sequence is visible.
   * `switchboard.js` refuses a non-string body -- which every line this game
   * sends is.
   */
  async say(channel, body) {
    const blinded = await this.cipher.blindChannel(channel);
    this._seq += 1;
    // **The signature covers the plaintext channel, not the blinded one**, and
    // the wrapper carries the plaintext name for the same reason. The library
    // signs before it blinds, and a reader restores `ch` over the identifier
    // the hub routed on before checking -- so signing the blinded form
    // produces a line that posts, arrives, opens, and verifies as `mismatch`.
    // Which is what it did: this comment exists because
    // `test_the_page_signs_with_the_key_it_published` caught it, and nothing
    // inside the browser could have.
    const wrapped = {
      b: body,
      ch: channel,
      s: {
        by: this.agentId,
        n: this._seq,
        sig: await sign(this.identity, messagePayload({
          sender: this.agentId, channel, seq: this._seq, body,
        })),
      },
    };
    return this._call("POST", "/messages", {
      body: {
        workspace: this.workspace,
        channel: blinded,
        agent_id: this.agentId,
        body: await this.cipher.seal(wrapped, "message.body"),
        type: "note",
        thread: null,
        ttl: null,
      },
    });
  }

  /**
   * Whisper one line to one peer: sealed to its published exchange key,
   * delivered to its `@` channel, signed like everything else.
   *
   * Gal, 2026-09-04: a command can go by `say` or by `whisper`, and the page
   * needs both -- the manager settles a `PRODUCE` whispered to it exactly as
   * one said on the board, and a plan whispered keeps the labour behind a
   * public receipt off the board (`ENTER.md`, "Play"). Same shape as the
   * Python client's `whisper`: `send("@<peer>", envelope, type="whisper")`,
   * the signature over the plaintext channel and the envelope as an object.
   *
   * **Sealed as `whisper`, always** (Gal, 2026-09-05: "don't use the legacy
   * `ask`"). This page had answered a peer in whatever form that peer last
   * whispered in and sealed `ask` to one it had not heard from, on the
   * reasoning that every release opens `ask` while only 2.1.0 and later open
   * `whisper`. That reasoning is over: the floor is 2.2.2, which writes
   * `whisper`, so a page still writing `ask` is the last thing in the room
   * speaking a form the library it is pinned against no longer produces.
   *
   * Reading is unchanged and stays two-formed -- `_openInbox` opens either --
   * because the compatibility only ever ran one way: a 2.1.0 reader opens
   * what any earlier release sealed, an earlier reader opens nothing new.
   * **What this costs is a peer whose host has not reinstalled**, since a
   * floor obliges an install and does not perform one; such a peer gets an
   * envelope it cannot open. That is the accepted price of the decision
   * above, and `test_python_opens_what_the_browser_whispered` pins it as a
   * fact rather than leaving it to be discovered under a clock.
   */
  async whisper(to, body) {
    if (!this._peers.size) await this.roster();
    const exchangeKey = this._peers.get(to);
    if (!exchangeKey) {
      throw new Error(`no exchange key for ${to.slice(0, 8)}… on the roster yet`);
    }
    const envelope = await sealToPeer(body, {
      identity: this.identity, peerExchangeKey: exchangeKey,
      context: WHISPER_CONTEXT,
    });
    const channel = `@${to}`;
    this._seq += 1;
    const wrapped = {
      b: envelope,
      ch: channel,
      s: {
        by: this.agentId,
        n: this._seq,
        sig: await sign(this.identity, messagePayload({
          sender: this.agentId, channel, seq: this._seq, body: envelope,
        })),
      },
    };
    return this._call("POST", "/messages", {
      body: {
        workspace: this.workspace,
        channel: await this.cipher.blindChannel(channel),
        agent_id: this.agentId,
        body: await this.cipher.seal(wrapped, "message.body"),
        type: "whisper",
        thread: null,
        ttl: null,
      },
    });
  }

  /** A channel's lines, oldest first, opened. */
  async history(channel, { limit = 200 } = {}) {
    const blinded = await this.cipher.blindChannel(channel);
    const reply = await this._call("GET", `/channels/${blinded}`,
                                   { params: { workspace: this.workspace, limit } });
    const rows = [];
    for (const row of reply.messages || []) {
      rows.push({ ...row, body: await this._open(row.body) });
    }
    return rows.sort((a, b) => (a.seq || 0) - (b.seq || 0));
  }

  /**
   * What has been whispered to this seat, opened.
   *
   * The roster is read first because a whisper is sealed pairwise and needs
   * the *sender's* exchange key: a client that has never read a roster sees
   * every whisper as unreadable, which is exactly the CLI bug fixed in 1.2.3.
   */
  async inbox({ limit = 50, peek = false } = {}) {
    if (!this._peers.size) await this.roster();
    // `peek` leaves the cursor where it is: a read that does not turn a
    // whisper into something the driver sees must not be the read that
    // consumes it. (An unsigned read is a peek whatever it asks for; the
    // room's reads are signed, so there it matters.)
    const reply = await this._call("GET", "/inbox", {
      params: { workspace: this.workspace, agent_id: this.agentId, limit,
                ...(peek ? { peek: "true" } : {}) },
    });
    const out = [];
    for (const row of reply.messages || []) {
      out.push({ ...row, body: await this._openInbox(row) });
    }
    return out;
  }

  /** The wrapper the transport puts around every message body. */
  async _open(value) {
    if (!isSealed(value)) return value;
    let opened;
    try {
      opened = await this.cipher.unseal(value, "message.body");
    } catch (err) {
      return { unreadable: String(err.message) };
    }
    return opened && typeof opened === "object" && "b" in opened ? opened.b : opened;
  }

  async _openInbox(row) {
    const outer = await this._open(row.body);
    // A whisper is sealed to this seat *inside* the ordinary workspace
    // envelope, so what comes back from `_open` may itself be sealed.
    if (!isSealed(outer)) return outer;
    if (!WHISPER_MARKERS.has(outer.m)) return outer;
    const peer = this._peers.get(row.from);
    if (!peer) {
      // Not a bad key: the roster simply has not been read, or the sender is
      // between turns and absent from it. Saying "unreadable" and saying
      // "forged" are different things and must stay different.
      return { unreadable: "no exchange key for the sender yet" };
    }
    // **The whisper's own context, not `message.body`.** A whisper is sealed
    // under its own context -- `Client._seal_whisper_body` binds it into the
    // AEAD -- and the outer workspace envelope is the one under
    // `message.body`. This page opened whispers under the outer context from
    // 2026-08-31 to 2026-09-04, so every invite the lobby sealed to a seat
    // came back as "unreadable" and the page showed nothing: a driver who had
    // joined saw no link to the island, and no error either.
    // `test_hand_pages.py` now opens a whisper the real Python lobby sealed.
    // The context is `whisper.body` since Switchboard 2.1.0 and was
    // `ask.body` before; `unsealFromPeer` reads the marker and opens either.
    try {
      return await unsealFromPeer(outer, {
        identity: this.identity, peerExchangeKey: peer,
        context: WHISPER_CONTEXT,
      });
    } catch (err) {
      return { unreadable: String(err.message) };
    }
  }
}
