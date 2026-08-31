// The two lobby lines a driver's buttons compose, in the browser.
//
// **This is a second implementation of `games/island/protocol.py`'s grammar**,
// and it exists because it has to: the hand's lobby is JavaScript served from
// a static origin and cannot call Python. `games/island.md` once said a
// composer emits through `protocol.py` rather than restating it; on a static
// origin that was unbuildable, and this file is the correction.
//
// What keeps it honest is `tests/test_hand_lobby_lines.py`: every line these
// functions produce is handed to the real parser, and every input they refuse
// is checked to be one the real parser would have refused too. **Agreement in
// both directions**, because the two ways to be wrong are opposite and both
// silent -- composing a line Python rejects loses a table with no error a
// driver can see, and refusing an input Python would have taken shrinks the
// game for no reason.
//
// The bounds below are `protocol.py`'s and are commented with the names they
// carry there. They are duplicated, not derived, so the test is the only
// thing standing between them and drift. When one moves, the test fails and
// says so -- which is the whole point of it existing.

export const LIMITS = {
  tradersMin: 2, tradersMax: 4,        // protocol.TRADERS_MIN / TRADERS_MAX
  goodsMin: 2, goodsMax: 5,            // protocol.GOODS_MIN / GOODS_MAX
  goodsDefault: 5,                     // protocol.GOODS_DEFAULT
  roundsMax: 1,                        // protocol.ROUNDS_MAX
  secondsAllowed: [15, 30, 45, 60, 90, 120, 180, 300],  // EPISODE_SECONDS_ALLOWED
  secondsDefault: 60,                  // protocol.EPISODE_SECONDS_DEFAULT
  nameMax: 32,                         // protocol._NAME
};

// protocol._NAME and protocol._RESERVED. The reserved list is the manager's
// own vocabulary: a trader called `T2` makes `g7 seat T1 = T2` a line nobody
// can read twice the same way.
const NAME = /^[A-Za-z0-9._-]{1,32}$/;
const RESERVED = /^(T[0-9]+|manager|lobby)$/i;

/** A refusal a driver can act on. Never a repaired line: the lobby does not
 *  repair one either, and a page that quietly fixed an input would be playing
 *  a different table from the one the driver asked for. */
export class Malformed extends Error {}

function integer(value, field) {
  // `protocol._KV` matches an integer and nothing else, so "3.0", "3 " and
  // "" are all refusals rather than things to coerce.
  if (typeof value === "number") {
    if (!Number.isInteger(value)) throw new Malformed(`${field} must be a whole number`);
    return value;
  }
  if (typeof value !== "string" || !/^-?[0-9]+$/.test(value.trim())) {
    throw new Malformed(`${field} must be a whole number`);
  }
  return parseInt(value.trim(), 10);
}

/**
 * `OPEN traders=2 episodes=8 rounds=1 goods=5 seconds=60`
 *
 * Every field is written out rather than left to default. A default is a
 * thing the driver did not see, and the whole point of the page is that they
 * did: what the board says is what the buttons showed.
 */
export function openLine({ traders, episodes, rounds = 1,
                           goods = LIMITS.goodsDefault,
                           seconds = LIMITS.secondsDefault } = {}) {
  traders = integer(traders, "traders");
  episodes = integer(episodes, "episodes");
  rounds = integer(rounds, "rounds");
  goods = integer(goods, "goods");
  seconds = integer(seconds, "seconds");

  if (traders < LIMITS.tradersMin || traders > LIMITS.tradersMax) {
    throw new Malformed(
      `traders must be between ${LIMITS.tradersMin} and ${LIMITS.tradersMax}`);
  }
  if (episodes < 1) throw new Malformed("a table needs at least 1 episode");
  if (rounds < 1) throw new Malformed("a table needs at least 1 round");
  if (rounds > LIMITS.roundsMax) {
    // The host plays a table's episodes once and records one round, so a
    // larger number would be announced on the board and never played.
    throw new Malformed(`a table runs ${LIMITS.roundsMax} round`);
  }
  if (goods < LIMITS.goodsMin || goods > LIMITS.goodsMax) {
    throw new Malformed(
      `goods must be between ${LIMITS.goodsMin} and ${LIMITS.goodsMax}`);
  }
  if (!LIMITS.secondsAllowed.includes(seconds)) {
    throw new Malformed(
      `seconds must be one of ${LIMITS.secondsAllowed.join(", ")}`);
  }
  return `OPEN traders=${traders} episodes=${episodes} rounds=${rounds} ` +
         `goods=${goods} seconds=${seconds}`;
}

/**
 * `JOIN g7 as scout-v2 nonce=<hex>`
 *
 * The nonce is this seat's half of the seed. It is not optional here even
 * though the parser allows its absence: a table where a seat brought none is
 * settled on a draw that seat cannot check, and a page that silently left it
 * out would be choosing that for the driver.
 */
export function joinLine({ table, name, nonce } = {}) {
  if (typeof table !== "string" || !/^[A-Za-z0-9._-]{1,32}$/.test(table)) {
    throw new Malformed("a table id is 1-32 characters of letters, digits, dash, underscore or dot");
  }
  if (typeof name !== "string" || !NAME.test(name)) {
    throw new Malformed(
      "a trader name is 1-32 characters of letters, digits, dash, " +
      "underscore or dot");
  }
  if (RESERVED.test(name)) {
    throw new Malformed(
      `${name} is the manager's own vocabulary -- a seat label, or one of ` +
      "the two roles. Pick a name that is yours");
  }
  if (typeof nonce !== "string" || !/^[0-9a-fA-F]{16,64}$/.test(nonce)) {
    throw new Malformed("a nonce is 16-64 hex digits");
  }
  return `JOIN ${table} as ${name} nonce=${nonce}`;
}

/** A seat's half of the seed: 32 hex digits from the browser's own CSPRNG.
 *
 *  Drawn here and not by anybody else, which is the entire reason a nonce
 *  exists -- a seed every seat helped draw is one no seat chose. */
export function nonce() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}
