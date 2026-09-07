// The manager's three forms, composed in the browser -- and what the page can
// read back off its lines.
//
// Two halves, kept apart on purpose, because only one of them can lose a game.
//
// **Composing** is a second implementation of
// `experiments/005-deliberation-protocol/island/protocol.py`'s grammar, and it
// exists for `lobby_lines.js`'s reason: a page served from a static origin
// cannot call Python. `games/island.md` once required a composer to emit
// through the real parser; on a static origin that was never buildable, and
// the replacement is a cross-language test --
// `tests/test_hand_play_lines.py` hands every line these functions write to
// the real parser, and every input they refuse is checked to be one the real
// parser would have refused too. **Agreement in both directions**, because
// the two ways to drift are opposite and both silent: a line Python rejects
// loses an episode with no error the driver can see, and an input refused
// here that Python would have taken shrinks the game for nothing.
//
// **Reading** is the weaker half and is written to fail weakly. `openOffers`
// and `seatsNamed` scrape the manager's own prose so a child can pick an
// offer from a list instead of copying `p3` by eye. That prose is not a
// grammar and nobody promised it would hold still. So every reader here
// degrades to **nothing found** rather than to something wrong, the page
// shows the manager's lines verbatim beside whatever was found, and every
// field these fill can be typed by hand instead. The test pins them against
// lines a **real `Manager`** produced, not against invented ones -- the
// mistake `test_lobby_web_reconstruct.py` was written after.
//
// Nothing here posts. These functions return strings; the page shows the
// string it is about to send, and `room.js` sends it.

//: The island's goods, in the order `island/dealer.py` lists them. A table of
//: `goods=4` plays the first four. Duplicated rather than derived, because a
//: static page cannot import Python -- and asserted equal to `dealer.GOODS`
//: in `tests/test_hand_play_lines.py`, which is the only thing standing
//: between this list and drift.
export const GOODS = ["bread", "cloth", "iron", "salt", "fish"];

//: `protocol._SHARE` and `protocol._BUNDLE` both name a good this way. A
//: capital letter is not a near miss the manager repairs; it is a line that
//: did not parse.
const GOOD = /^[a-z]+$/;

//: The number both of those regexes accept, and the only shape a quantity may
//: reach the board in. No sign, no exponent: `-0.5` and `1e-3` are refused by
//: the parser rather than read as numbers, so they are refused here.
const NUMBER = /^[0-9]*\.?[0-9]+$/;

//: Where a float's own arithmetic error lives, and nothing a control on this
//: page can express. `0.1 + 0.2` is `0.30000000000000004`, and a slider
//: computes exactly that -- so a quantity is written out at this many places
//: and the trailing zeros trimmed. Writing at 9 places can move a number by
//: at most 5e-10, which is smaller than any step any control here offers, so
//: nothing a child chooses is ever rounded behind their back. Going through a
//: decimal string rather than `String(n)` is what keeps `0.0000001` out of
//: exponent form, which the parser's number regex refuses.
const PLACES = 9;

/** A refusal a driver can act on, and never a repaired line. The manager does
 *  not repair one either, and a page that quietly fixed an input would be
 *  playing a different game from the seats beside it. */
export class Malformed extends Error {}

/**
 * A quantity, as the parser's regexes will read it back.
 *
 * Accepts what an `<input>` hands over (a string -- passed through as typed,
 * at whatever precision) and what a slider computes (a float, complete with
 * `0.1 + 0.2` noise, written out at `PLACES` decimals so the noise does not
 * reach the board). A string is never reformatted: what the driver typed is
 * what the board says, and the regex below is the only thing it must pass.
 */
function quantity(value, field, { positive }) {
  let text;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Malformed(`${field} must be a number`);
    // Only the zeros *after the point*: a bare `/0+$/` turns 10 into 1, which
    // is a quantity nobody asked for on a line that parses perfectly.
    // `toFixed` above 1e21 hands back exponent form; the regex below catches
    // it rather than this pretending such a number could be a quantity.
    text = value.toFixed(PLACES).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
  } else if (typeof value === "string") {
    text = value.trim();
  } else {
    throw new Malformed(`${field} must be a number`);
  }
  // The last gate, and the reason it is here rather than trusted: every path
  // above can produce a token the parser's regex refuses -- an exponent from
  // `String`, a stray sign or space from an input -- and such a token posts
  // perfectly and settles nothing.
  if (!NUMBER.test(text)) {
    throw new Malformed(`${field} must be a plain number like 0.5, got ${
      typeof value === "string" ? value.trim() : value}`);
  }
  if (positive && Number(text) <= 0) {
    throw new Malformed(`${field} must be more than zero`);
  }
  return text;
}

function good(name, field) {
  if (typeof name !== "string" || !GOOD.test(name)) {
    throw new Malformed(`${field} is a good's name in lower-case letters, ` +
                        `like bread -- got ${JSON.stringify(name)}`);
  }
  return name;
}

/**
 * `PRODUCE bread=0.5 fish=0.5` -- how this seat spends the day's labour.
 *
 * `plan` is `{good: share}`, and a share of zero is dropped rather than
 * written: a slider left at the bottom is a good the child did not pick, and
 * `bread=0` on the board says the same thing at more length.
 *
 * **The total is not checked here, and that is deliberate.** The manager
 * refuses a plan spending more than one unit of labour, but `protocol.parse`
 * reads it fine, so refusing it here would make this page stricter than the
 * grammar -- the direction that shrinks the game for nothing. The page warns
 * in words instead, where the driver can overrule it.
 */
export function produceLine({ plan } = {}) {
  if (!plan || typeof plan !== "object") throw new Malformed("nothing to make");
  const parts = [];
  for (const [name, share] of Object.entries(plan)) {
    const written = quantity(share, `the share of ${name}`, { positive: false });
    if (Number(written) === 0) continue;
    parts.push(`${good(name, "a plan")}=${written}`);
  }
  if (!parts.length) {
    throw new Malformed("pick at least one thing to make, and how much of " +
                        "the day to spend on it");
  }
  return `PRODUCE ${parts.join(" ")}`;
}

/** `iron:0.4,salt:0.1` -- one side of a swap. */
function bundle(items, label) {
  if (!items || typeof items !== "object") throw new Malformed(`${label} is empty`);
  const parts = [];
  for (const [name, qty] of Object.entries(items)) {
    const written = quantity(qty, `the amount of ${name}`, { positive: true });
    parts.push(`${good(name, label)}:${written}`);
  }
  if (!parts.length) throw new Malformed(`${label} is empty`);
  return parts.join(",");
}

/**
 * `PROPOSE to=T2 give=iron:0.4 want=salt:0.3` -- an offer, in the open.
 *
 * `to` is passed through as the parser sees it: any single token. Whitespace
 * is the one thing refused, because `parse` splits on it and a partner named
 * "T 2" becomes a field nobody wrote. An empty `to` composes, because
 * `parse` reads `to=` as a proposal addressed to nobody and the two grammars
 * must agree even about a line that is useless -- the page turns its own
 * button off instead, which is an affordance and not a rule.
 */
export function proposeLine({ to, give, want } = {}) {
  if (typeof to !== "string") throw new Malformed("say who the swap is with");
  if (/\s/.test(to)) {
    throw new Malformed("a partner is one word, like T2 -- a space in it " +
                        "makes a line the manager cannot read");
  }
  return `PROPOSE to=${to} give=${bundle(give, "what you give")} ` +
         `want=${bundle(want, "what you want")}`;
}

function proposalId(id, head) {
  if (typeof id !== "string" || !id.trim() || /\s/.test(id.trim())) {
    throw new Malformed(`${head} wants one offer's name, like p3`);
  }
  return id.trim();
}

/** `APPROVE p3` -- take the offer. Public, because an exchange is agreed in
 *  the open and so is calling one off. */
export function approveLine({ proposal } = {}) {
  return `APPROVE ${proposalId(proposal, "APPROVE")}`;
}

/** `DECLINE p3` -- the fourth form. An open offer holds the maker's goods
 *  until the bell and the maker cannot free them; only the trader it was
 *  addressed to can, and this is how. */
export function declineLine({ proposal } = {}) {
  return `DECLINE ${proposalId(proposal, "DECLINE")}`;
}


// --- reading the manager back ---------------------------------------------
//
// Everything below scrapes prose. It is a convenience over the board and
// never a substitute for it: the page renders every line the manager wrote,
// and a reader here that finds nothing costs a child a dropdown, not a move.

//: The one literal the manager tells a trader to copy: "`T2` takes it by
//: writing exactly: `APPROVE p3`". Read off that instruction rather than off
//: the offer's own rendering, because the instruction is the part the manager
//: promises to a trader and the rendering is the part it is free to reword.
const OFFERED = /(\S+) takes it by writing exactly: APPROVE (\S+)$/;

//: How an offer stops being open, in the manager's own words: `p3 settled:`,
//: `p3 declined:`. The bell closes the rest without naming them, which is why
//: `BELL` is here too.
const CLOSED = /^(\S+) (settled|declined|lapsed)\b/;
const BELL = /^bell — episode \b/;

/**
 * The offers still open, oldest first, from the board as it stands.
 *
 * `lines` is the board in order -- strings, or the rows `room.js` keeps, from
 * which the body is taken. Each entry is `{ id, to }`: the offer's name and
 * the seat that may take it.
 *
 * **Empty is the failure mode**, and the only one worth having. If the
 * manager rewords its receipt this finds nothing, the child reads the board
 * and types `p3`, and the game goes on. A reader that guessed instead would
 * put a stale offer under a button.
 */
export function openOffers(lines) {
  const open = new Map();
  for (const row of lines || []) {
    const body = typeof row === "string" ? row
               : (row && typeof row.body === "string" ? row.body : "");
    const text = body.trim();
    if (!text) continue;
    if (BELL.test(text)) { open.clear(); continue; }
    const closed = CLOSED.exec(text);
    if (closed) { open.delete(closed[1]); continue; }
    const made = OFFERED.exec(text);
    // The offer's name is stated twice in that line -- `p3: ...` at the head
    // and `APPROVE p3` at the tail -- and they must agree, or this is a line
    // quoting somebody else's offer rather than making one.
    if (made && text.startsWith(`${made[2]}:`)) {
      open.set(made[2], { id: made[2], to: made[1] });
    }
  }
  return [...open.values()];
}

//: `schedule.schedule_text`: "Schedule for this round. 2 traders: T1, T2."
const SEATS = /^Schedule for this round\. \d+ traders: ([^.]+)\./;

/** The seats at this table, from the manager's schedule. `[]` when it has not
 *  said yet, or has said differently -- and then the partner is typed. */
export function seatsNamed(lines) {
  for (const row of lines || []) {
    const body = typeof row === "string" ? row
               : (row && typeof row.body === "string" ? row.body : "");
    const found = SEATS.exec(body.trim());
    if (found) return found[1].split(",").map((s) => s.trim()).filter(Boolean);
  }
  return [];
}

//: `run_game`: "episode 3 of 8 is open; the bell is at ...". The game calls
//: an episode a **day** (`CLAUDE.md`) -- the manager writes "episode" on the
//: board and this page says "day", which is why the number is dug out rather
//: than the sentence quoted.
const OPENED = /^episode (\d+) of (\d+) is open\b/;
const CLOSED_EPISODE = /^bell — episode (\d+) closed\b/;
//: `run_game`'s closing line, which `room.js` also watches for.
const OVER = /^the round is over\b/;

/**
 * Which day it is, and whether it is open: `{ day, of, open, over }`.
 *
 * `null` until the manager has opened one. The page shows the manager's own
 * line either way; this only decides which words go in the big banner.
 */
export function whichDay(lines) {
  let state = null;
  for (const row of lines || []) {
    const body = typeof row === "string" ? row
               : (row && typeof row.body === "string" ? row.body : "");
    const text = body.trim();
    const opened = OPENED.exec(text);
    if (opened) {
      state = { day: Number(opened[1]), of: Number(opened[2]),
                open: true, over: false };
      continue;
    }
    const shut = CLOSED_EPISODE.exec(text);
    if (shut && state) { state = { ...state, open: false }; continue; }
    if (OVER.test(text) && state) state = { ...state, open: false, over: true };
  }
  return state;
}

//: `dealer.private_state`, as it arrives sealed to one seat: "You are T1. Your
//: production capacity per unit of labour: {'bread': 0.87, ...}. Your taste
//: weights: {'bread': 0.31, ...}. Nobody else knows either." Two Python dict
//: reprs, which is what it is rather than what anybody would design.
const PRIVATE = /Your production capacity per unit of labour: \{([^}]*)\}\. ?Your taste weights: \{([^}]*)\}/;
const ENTRY = /'([a-z]+)':\s*([0-9]*\.?[0-9]+)/g;

function dictOf(text) {
  const out = {};
  for (const [, name, value] of text.matchAll(ENTRY)) out[name] = Number(value);
  return out;
}

/**
 * This seat's private half, out of the manager's whisper:
 * `{ seat, capacity, taste }`, or `null` if nothing here says it.
 *
 * **Read to be shown, never to be sent.** It is what makes the page playable
 * by a child -- how good this island is at each thing, and how much this seat
 * wants each thing, as bars rather than a dict -- and it is also the one thing
 * on the page that must not reach the board: a capacity posted in public is a
 * seal broken by the seat it protects. Nothing here composes a line, and the
 * page never puts these numbers in one.
 *
 * It also names the goods this island actually deals, which `GOODS` can only
 * guess at: a table of `goods=3` plays three, and a plan naming a fourth is
 * refused by name. `null` falls back to `GOODS`, which is the whole list and
 * therefore sometimes too long -- a visible refusal rather than a wrong guess.
 */
export function privateHalf(whispers) {
  for (const row of whispers || []) {
    const body = typeof row === "string" ? row
               : (row && typeof row.body === "string" ? row.body : "");
    const found = PRIVATE.exec(body);
    if (!found) continue;
    const capacity = dictOf(found[1]);
    const taste = dictOf(found[2]);
    if (!Object.keys(capacity).length) continue;
    const seat = /You are (\S+?)\./.exec(body);
    return { seat: seat ? seat[1] : null, capacity, taste };
  }
  return null;
}

//: `run_game.who_is_at_this_table`: "The seats at this table, witnessed in
//: public on the lobby board before this room existed: T1 = alice (key abc),
//: T2 = bob (key def). This room's invite was posted there too, ..."
//:
//: Anchored at the head, so a trader quoting the line back at the room is not
//: read as the manager saying it -- the same guard `openOffers` carries, and
//: for the same reason.
const SEATED = /^The seats at this table\b[^:]*: (.+?)\. This room's invite\b/;
const SEAT_OF = /^(\S+) = (\S+) \(key /;

/**
 * Alias -> seat label, from the manager's roll-call: `{ alice: "T1" }`.
 *
 * **What it is for is the picture, not a move.** The board names an author by
 * their blinded hub id; the island draws a hut per *seat*. Without this every
 * hut is labelled with six characters of a hash, which is the island a child
 * is asked to play on. Nothing composed from it ever reaches the board -- the
 * partner in a `PROPOSE` comes from the seat label the manager itself
 * published, which is what this reads.
 *
 * `{}` when the manager has not said, or has said differently, and then the
 * huts keep the ids: a wrong name over somebody's hut is worse than a short
 * one, because a child would trade against it.
 */
export function seatLabels(lines) {
  for (const row of lines || []) {
    const body = typeof row === "string" ? row
               : (row && typeof row.body === "string" ? row.body : "");
    const found = SEATED.exec(body.trim());
    if (!found) continue;
    const out = {};
    for (const part of found[1].split(",")) {
      const seat = SEAT_OF.exec(part.trim());
      if (seat) out[seat[2]] = seat[1];
    }
    if (Object.keys(out).length) return out;
  }
  return {};
}

// --- what a child is shown, as opposed to what is sent --------------------
//
// Both of these are **display only**, and that is the property that makes
// them safe. A quantity here is never composed into a line: `APPROVE p3`
// carries an id and no numbers, and the manager settles the offer it already
// holds. So rounding for a reader cannot change what is traded -- which is
// exactly the argument that would *not* hold if these numbers went into a
// `PROPOSE`, and the reason they are kept apart from the composers above.

/**
 * A quantity as a child reads it: `0.12428327472728834` -> `0.12`.
 *
 * Two decimals, which is the step every slider on the page offers. A number
 * too small to survive that is written at one significant figure instead of
 * as `0`, because "offers you 0 iron" is a sentence about a trade nobody is
 * making.
 */
export function amount(value) {
  const q = Number(value);
  if (!Number.isFinite(q)) return String(value);
  if (q === 0) return "0";
  const trim = (text) => text.includes(".")
    ? text.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "") : text;
  if (Number(q.toFixed(2)) !== 0) return trim(q.toFixed(2));
  // Smaller than two places can hold. Written at enough places to reach its
  // first real digit -- **never `toPrecision`**, which hands back `1e-7` for
  // a tenth of a millionth, and an exponent is not an improvement on the
  // number it replaced.
  const places = Math.min(20, Math.max(2, 1 - Math.floor(Math.log10(Math.abs(q)))));
  const small = trim(q.toFixed(places));
  return Number(small) === 0 ? "almost none" : small;
}


/**
 * The manager's notes to this seat, as lines to show: `[{kind, text}]`.
 *
 * Three things it does, and each is a defect it was written to fix -- all
 * three visible in one screenshot of the page on 2026-09-07:
 *
 * - **A note this page could not open is said in words**, not printed as
 *   `{"unreadable":"could not open the value at whisper.body: ..."}`. The
 *   hand's lobby has said it in words since g27; this is the same courtesy on
 *   the page a child reads. It matters more here, because the usual cause is
 *   mundane and fixable: the seat key lives in one browser, so a second
 *   browser or a private window reads with a key the lobby never witnessed.
 * - **The private half is not printed twice.** When the bars are drawn from
 *   it, the note itself is two Python dict reprs saying the same thing at
 *   more length -- so it is dropped, and only while the bars are actually
 *   showing (`privateShown`), because losing it entirely would be worse than
 *   printing it.
 * - **Everything else is shown untouched**, which is the part that must not
 *   be lost: the manager's refusals arrive this way, and a refusal a child
 *   does not see is a day they do not know they lost.
 */
export function notes(whispers, { privateShown = false } = {}) {
  const out = [];
  for (const row of whispers || []) {
    const body = row && typeof row === "object" ? row.body : row;
    if (body && typeof body === "object" && body.unreadable) {
      out.push({ kind: "unreadable", text:
        "A secret note arrived that this page could not open. That usually " +
        "means this is not the browser that took your seat — the key is kept " +
        "in one browser, so a different one, or a private window, reads with " +
        `a key nobody witnessed. (${body.unreadable})` });
      continue;
    }
    const text = typeof body === "string" ? body : JSON.stringify(body);
    if (privateShown && PRIVATE.test(text)) continue;
    out.push({ kind: "note", text });
  }
  return out;
}
