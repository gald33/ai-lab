// The room, from the page: enter it, show its board, post to it.
//
// Shared by `lobby.html`, which enters the room the moment the lobby hands
// it out, and `play.html`, which enters on a button for a driver arriving
// with an invite in the URL. One module, because g27 (2026-09-04) was lost
// between two pages: the lobby page found no link to the second page, and
// the manager's line for an empty seat -- "a client built fresh for this
// room mints a new one" -- was read by the other trader as the driver having
// come in under a different key, when the driver had never come in at all.
// A page that enters the room with the identity it joined under has nothing
// to hand across, so there is nothing to hand across wrongly.
//
// **Reading only, on a clock.** The board is polled while the round is on,
// because a driver has one minute per episode and cannot be asked to press a
// button to find out what the bell said. Nothing here prompts anyone; the
// bell rings on the clock whatever this page shows. Polling stops when the
// manager says the round is over.

import { Hub } from "./hub.js";
import { declaration } from "./declaration.js";

//: The manager's closing line. `island/manager.py` writes it; the page reads
//: it back to know there is nothing more to poll for.
const OVER = /^the round is over\b/;
const POLL_MS = 3000;

export class Room {
  /**
   * @param {object} els  `board`, `whispers` and `who` elements to render
   *   into; `say` (the input) and `post` (its button) for the board; and
   *   `whisperLine` (the input) and `whisper` (its button) for the manager.
   *   Two lines, not one with two buttons (Gal, 2026-09-04): what goes on
   *   the board and what goes sealed to the manager are different acts,
   *   and a driver should not have to remember which button they meant.
   * @param {(text: string, bad?: boolean) => void} status  the page's status line
   */
  constructor(els, status) {
    this.els = els;
    this.status = status;
    this.hub = null;
    this.identity = null;
    this.channel = "island";
    this.seat = null;
    this._poll = null;
    this._over = false;
    this.manager = null;   // the manager's hub id, off the room's roster
    if (els.post) {
      els.post.addEventListener("click", () => this.postTyped());
    }
    if (els.whisper) {
      els.whisper.addEventListener("click", () => this.whisperTyped());
    }
    if (els.whisperLine) {
      els.whisperLine.addEventListener("keydown", (event) => {
        if (event.key === "Enter") this.whisperTyped();
      });
    }
    if (els.say) {
      els.say.addEventListener("keydown", (event) => {
        if (event.key === "Enter") this.postTyped();
      });
    }
  }

  /** Enter: register this identity, read the roster, declare the driver,
   *  and start reading. The declaration is posted once, on arrival, as a
   *  side effect of using the page -- the only mechanism there is. */
  async enter({ url, token, workspace, key, writeKey, identity, alias, seat, channel }) {
    this.stop();
    this.identity = identity;
    this.seat = seat;
    this.channel = channel || "island";
    this._over = false;
    this.hub = await Hub.open({
      url, token, workspace, key, writeKey: writeKey || null, identity, alias,
    });
    await this.hub.register(alias);
    this._findManager(await this.hub.roster());
    await this.hub.say(this.channel, declaration(seat));
    if (this.els.who) {
      this.els.who.textContent =
        `${alias} in ${workspace}, seat ${seat}, key ` +
        `${identity.publicKey.slice(0, 12)}… — declared as driven.`;
    }
    await this.refresh();
    window.HAND_READY = true;
    this._poll = setInterval(() => {
      this.refresh().catch(() => { /* the next tick reads again */ });
    }, POLL_MS);
    return this.hub;
  }

  stop() {
    clearInterval(this._poll);
    this._poll = null;
  }

  /** The manager is whoever the roster calls `manager` (`run_game.MANAGER`);
   *  the page learns its id here and nowhere else. */
  _findManager(agents) {
    const row = agents.find((a) => a.name === "manager");
    this.manager = row ? row.agent_id : null;
    return this.manager;
  }

  async refresh() {
    if (!this.hub) return;
    if (!this.manager) this._findManager(await this.hub.roster());
    const rows = await this.hub.history(this.channel, { limit: 200 });
    this.els.board.replaceChildren(...rows.slice(-80).map((row) => {
      const line = document.createElement("div");
      if (row.from === this.hub.agentId) line.className = "mine";
      const who = document.createElement("span");
      who.className = "who";
      who.textContent = `${String(row.from || "?").slice(0, 6)} `;
      line.append(who, document.createTextNode(
        typeof row.body === "string" ? row.body : JSON.stringify(row.body)));
      return line;
    }));
    const whispers = await this.hub.inbox({ limit: 20, peek: true });
    this.els.whispers.replaceChildren(...whispers.map((row) => {
      const line = document.createElement("div");
      line.textContent = typeof row.body === "string"
        ? row.body : JSON.stringify(row.body);
      return line;
    }));
    window.HAND_BOARD = rows;
    window.HAND_WHISPERS = whispers;
    if (!this._over && rows.some((r) => typeof r.body === "string" && OVER.test(r.body))) {
      this._over = true;
      this.stop();
      this.status("The round is over. Nothing further settles.");
    }
  }

  /** Whisper exactly what is in the input to the manager, sealed. What the
   *  room sees is that a whisper happened; the receipt the manager posts is
   *  public. A `PRODUCE` goes this way; a `PROPOSE` or `APPROVE` whispered
   *  here is still settled, but an exchange is meant to be agreed in the
   *  open, and the manager's refusal, if any, comes back by whisper too. */
  async whisperTyped() {
    if (!this.hub) return this.status("Enter the room first.", true);
    if (!this.manager) this._findManager(await this.hub.roster());
    if (!this.manager) {
      return this.status("No manager on this room's roster yet.", true);
    }
    const line = this.els.whisperLine.value;
    if (!line.trim()) return;
    try {
      await this.hub.whisper(this.manager, line);
      this.els.whisperLine.value = "";
      this.status("Whispered to the manager. Its answer, if any, arrives " +
                  "under \"What was whispered to you\".");
      await this.refresh();
    } catch (err) { this.status(String(err.message), true); }
  }

  /** Post exactly what is in the input. No validation gate: the manager
   *  never repairs a malformed line, and a page that refused to post one
   *  would be playing a different game from the agents at the table. */
  async postTyped() {
    if (!this.hub) return this.status("Enter the room first.", true);
    const line = this.els.say.value;
    if (!line.trim()) return;
    try {
      await this.hub.say(this.channel, line);
      this.els.say.value = "";
      this.status("Posted.");
      await this.refresh();
    } catch (err) { this.status(String(err.message), true); }
  }
}

/** The shortcut buttons: fill a line, never post. A button with
 *  `data-to="whisper"` fills the manager's line (PRODUCE goes sealed);
 *  the rest fill the board's. */
export function bindShortcuts(root, say, whisperLine) {
  for (const button of root.querySelectorAll("[data-fill]")) {
    button.addEventListener("click", () => {
      const target = button.dataset.to === "whisper" && whisperLine ? whisperLine : say;
      target.value = button.dataset.fill;
      target.focus();
    });
  }
}
