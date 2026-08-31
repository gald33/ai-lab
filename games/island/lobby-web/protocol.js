// Port of games/island/protocol.py — the OPEN / JOIN / MANAGE grammar.
//
// Kept a faithful transliteration rather than a tidier rewrite: this decides
// which lines on the board count as acts, and a browser that disagrees with
// the lobby shows a table that is not there. Constants and bounds are copied
// from the Python and must be changed with it.

export const OPEN = "OPEN", JOIN = "JOIN", MANAGE = "MANAGE";

export const TRADERS_MIN = 2, TRADERS_MAX = 8;
export const GOODS_MIN = 2, GOODS_MAX = 12, GOODS_DEFAULT = 5;
export const ROUNDS_MAX = 1;
export const EPISODE_SECONDS_ALLOWED = [15, 30, 45, 60, 90, 120, 180, 300];
export const EPISODE_SECONDS_DEFAULT = 60;

const KV = /^([a-z]+)=(-?[0-9]+)$/;
const NAME = /^[A-Za-z0-9._-]{1,32}$/;
const RESERVED = /^(T[0-9]+|manager|lobby)$/i;
const NONCE = /^[0-9a-fA-F]{16,64}$/;

export class Malformed extends Error {}

/** Return {kind:"open"|"join"|"manage", ...} , or null if the line is just talk.
 *  Throws Malformed when a line opens with a keyword and then does not parse —
 *  somebody tried to act and got the format wrong, which they should be told. */
export function parse(text) {
  const stripped = (text || "").trim();
  if (!stripped) return null;
  const head = stripped.split(/\s+/, 1)[0].toUpperCase();
  if (head !== OPEN && head !== JOIN && head !== MANAGE) return null;
  const rest = stripped.slice(head.length).trim();

  if (head === OPEN) {
    const fields = {};
    for (const part of rest.split(/\s+/).filter(Boolean)) {
      const m = KV.exec(part);
      if (!m) throw new Malformed(`OPEN wants key=integer pairs, got ${JSON.stringify(part)}`);
      fields[m[1]] = parseInt(m[2], 10);
    }
    const missing = ["traders", "episodes"].filter(k => !(k in fields));
    if (missing.length) throw new Malformed(`OPEN is missing ${missing.join(", ")}`);
    const extra = Object.keys(fields)
      .filter(k => !["traders", "episodes", "rounds", "goods", "seconds"].includes(k));
    if (extra.length) throw new Malformed(`OPEN does not understand ${extra.sort().join(", ")}`);
    if (!(fields.traders >= TRADERS_MIN && fields.traders <= TRADERS_MAX))
      throw new Malformed(`traders must be between ${TRADERS_MIN} and ${TRADERS_MAX}, got ${fields.traders}`);
    if (fields.episodes < 1) throw new Malformed("a table needs at least 1 episode");
    const goods = fields.goods ?? GOODS_DEFAULT;
    if (!(goods >= GOODS_MIN && goods <= GOODS_MAX))
      throw new Malformed(`goods must be between ${GOODS_MIN} and ${GOODS_MAX}, got ${goods}`);
    const rounds = fields.rounds ?? 1;
    if (rounds < 1) throw new Malformed("a table needs at least 1 round");
    if (rounds > ROUNDS_MAX) throw new Malformed(`rounds may not exceed ${ROUNDS_MAX}`);
    const seconds = fields.seconds ?? EPISODE_SECONDS_DEFAULT;
    if (!EPISODE_SECONDS_ALLOWED.includes(seconds))
      throw new Malformed(`seconds must be one of ${EPISODE_SECONDS_ALLOWED.join(", ")}, got ${seconds}`);
    return { kind: "open", traders: fields.traders, episodes: fields.episodes,
             rounds, goods, seconds };
  }

  const parts = rest.split(/\s+/).filter(Boolean);
  if (head === MANAGE) {
    if (parts.length !== 1) throw new Malformed("MANAGE wants exactly a table id");
    return { kind: "manage", table: parts[0] };
  }

  // JOIN <table> <name> [nonce]
  if (parts.length < 2) throw new Malformed("JOIN wants a table id and a name");
  const [table, name, nonce] = parts;
  if (!NAME.test(name)) throw new Malformed(`a name must match ${NAME}`);
  if (RESERVED.test(name)) throw new Malformed(`${name} is reserved`);
  if (nonce !== undefined && !NONCE.test(nonce))
    throw new Malformed("a nonce is 16-64 hex digits");
  return { kind: "join", table, name, nonce: nonce || "" };
}
