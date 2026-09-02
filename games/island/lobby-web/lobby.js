// Reconstruct the lobby's view from what is on the channel.
//
// THE DESIGN DECISION, and it is the whole reason this file is short:
// **the lobby's own lines are authoritative and this file only parses them.**
// The Python lobby decides — it verifies signatures, draws the seed, settles
// and lapses — and then it SAYS what it decided. A browser that re-derived
// those decisions would be a second lobby that can disagree with the first,
// and the page is what a person reads before deciding to sit down. So an
// entrant's OPEN/JOIN/MANAGE is read only as intent; a table exists, seats
// fill, and games settle because the lobby said so.
//
// Ported from games/island/lobby.py. The formats below are produced by
// `Lobby.say(...)` there; change them together or this page goes quiet about
// tables that exist.

import { parse, Malformed } from "./protocol.js";

export const HOLD = "LOBBY holding this channel: ";

//: **A table's id is the lobby's to choose, and it is not `T<n>`.**
//: `lobby.py` names tables `g1`, `g2`, ... (`Table(id=f"g{self._next}")`),
//: and every pattern here demanded `T\d+` -- so against the live lobby this
//: file matched nothing: no forming table, no seat, no settlement, on a page
//: whose whole job is to show them. It went unseen because the fixture the
//: port was read against invented `T1` itself, which is the trap
//: `test_lobby_web_levers.py` was written for one file over: **a second
//: implementation checked against its own idea of what it should produce.**
//: The id is read as a prefix and a number now, so a lobby that renames its
//: tables again does not silence this page.
//:
//: A *seat's* label is a different thing and really is `T<n>` --
//: `Lobby._label` builds it from the seat's index -- so `seat` keeps that
//: literally where the seat goes, and takes `{T}` only for the table.
const TABLE = String.raw`[A-Za-z]+\d+`;

/** A lobby line's pattern, written with `{T}` where the table's id goes. */
const rx = (src) => new RegExp(src.replaceAll("{T}", TABLE));

const RE = {
  commits: rx(String.raw`^({T}) commits ([0-9a-f]+)`),
  forming: rx(String.raw`^({T}) is forming: (\d+) traders, (\d+) goods, (\d+) episodes(?: of (\d+)s)?, (\d+) round`),
  seat:    rx(String.raw`^({T}) seat (T\d+) = (\S+?), key (\S+?)(, sealed|, in the clear)?(?:, nonce ([0-9a-f]+))? \((\d+)\/(\d+)\)$`),
  manager: rx(String.raw`^({T}) will be managed by (\S+?), key (\S+)$`),
  full:    rx(String.raw`^({T}) is full: (.*?); managed by (.*?); opens (\S+?)(;.*)?$`),
  island:  rx(String.raw`^({T}): the island is (.+)$`),
  lapsed:  rx(String.raw`^({T}) lapsed: (.+?) within \d+s \((\d+)\/(\d+) seated(?:, managed by (.+?))?\)$`),
  refusal: /^@(\S+) not settled: (.+)$/,
  invite:  rx(String.raw`^({T}) invite: `),
};

//: **`opens` is a time of day, not a timestamp.** `Lobby._stamp` writes
//: `19:40:00Z` -- "the same convention `run_v3.py` uses for every deadline it
//: posts" -- and this read it with `Date.parse`, which returns NaN for a bare
//: clock time. So `opens_at` was null on every settled table the live lobby
//: ever announced: no countdown to the start, and `playable()` in `render.js`
//: treating the game as running forever. Unseen for the same reason the id was:
//: `fixture.html` wrote a full ISO timestamp there, which `Date.parse` does
//: read, so the port only ever met a format the lobby does not use.
//:
//: The day comes from the line's own hub timestamp, since the stamp does not
//: carry one. A table that opens just after midnight is announced just before
//: it, so a stamp more than twelve hours behind the line is tomorrow's.
function opensAt(stamp, at) {
  const m = /^(\d{2}):(\d{2}):(\d{2})Z$/.exec(stamp);
  if (!m) return Date.parse(stamp) / 1000 || null;
  if (!at) return null;                       // no day to hang the time on
  const day = new Date(at * 1000);
  let when = Date.UTC(day.getUTCFullYear(), day.getUTCMonth(), day.getUTCDate(),
                      +m[1], +m[2], +m[3]) / 1000;
  if (when < at - 12 * 3600) when += 24 * 3600;
  return when;
}

function table(tables, id) {
  if (!tables.has(id)) {
    tables.set(id, {
      id, traders: 0, goods: 0, episodes: 0, rounds: 1,
      opened_at: 0, seats: [], commit: "", manager: null, manager_key: null,
      settled: false, lapsed: false, opens_at: null, draw: "",
      practice: false, lapse_reason: "", roster: "", seconds: 60,
    });
  }
  return tables.get(id);
}

/** Build the lobby view from a decrypted snapshot ({agents, messages}).
 *  `messages` are the channel's history, oldest first. */
export function reconstruct(snapshot, channel) {
  const tables = new Map();
  const refusals = [];
  // What Lobby.settled counts: every accepted JOIN and MANAGE, incremented in
  // _join and _manage. Counted here from the lobby's own confirmations rather
  // than from entrants' lines, for the same reason everything else here is.
  let holder = null, lastLine = 0, settledLines = 0;

  const rows = (snapshot.messages || [])
    .filter(m => !channel || m.channel === channel)
    .slice()
    .sort((a, b) => String(a.created_at || "").localeCompare(String(b.created_at || "")));

  for (const row of rows) {
    const body = typeof row.body === "string" ? row.body
               : (row.body && row.body.text) || "";
    const at = Date.parse(row.created_at || "") / 1000 || 0;
    if (at) lastLine = Math.max(lastLine, at);
    let m;

    if (body.startsWith(HOLD)) { holder = body.slice(HOLD.length).trim(); continue; }
    // Since 2026-09-02 the lobby whispers the room to its seats and this
    // line only says so; an older lobby put the credential itself here. Either
    // way it is not the page's to show.
    if (RE.invite.test(body)) continue;

    if ((m = RE.commits.exec(body)))  { table(tables, m[1]).commit = m[2]; continue; }
    if ((m = RE.forming.exec(body)))  {
      const t = table(tables, m[1]);
      // `seconds` joined the line on 2026-09-02; a lobby that predates it
      // announced the default, which is what the schedule ran on.
      Object.assign(t, { traders: +m[2], goods: +m[3], episodes: +m[4],
                         seconds: m[5] ? +m[5] : 60,
                         rounds: +m[6], opened_at: t.opened_at || at });
      continue;
    }
    if ((m = RE.seat.exec(body))) {
      const t = table(tables, m[1]);
      if (!t.seats.some(s => s.label === m[2])) {
        t.seats.push({ label: m[2], name: m[3], key: m[4],
                       sealed: m[5] === ", sealed", nonce: m[6] || "" });
        settledLines++;
      }
      if (!t.traders) t.traders = +m[8];
      continue;
    }
    if ((m = RE.manager.exec(body))) {
      const t = table(tables, m[1]);
      if (!t.manager) settledLines++;
      t.manager = m[2]; t.manager_key = m[3]; continue;
    }
    if ((m = RE.full.exec(body))) {
      const t = table(tables, m[1]);
      Object.assign(t, { settled: true, roster: m[2], manager: t.manager || m[3],
                         opens_at: opensAt(m[4], at),
                         practice: /PRACTICE/.test(m[5] || "") });
      continue;
    }
    if ((m = RE.island.exec(body)))  { table(tables, m[1]).draw = m[2]; continue; }
    if ((m = RE.lapsed.exec(body)))  {
      const t = table(tables, m[1]);
      Object.assign(t, { lapsed: true, lapse_reason: m[2] });
      if (!t.traders) t.traders = +m[4];
      continue;
    }
    if ((m = RE.refusal.exec(body))) { refusals.push({ who: m[1], why: m[2], at }); continue; }

    // An entrant's own line. Read as intent only — it creates nothing.
    try { parse(body); } catch (e) {
      if (e instanceof Malformed) refusals.push({ who: row.from || "someone", why: e.message, at });
    }
  }

  return {
    tables: [...tables.values()].sort((a, b) => b.opened_at - a.opened_at),
    refusals: refusals.slice(-5),
    settledLines,
    holder,
    lastLine,
    agents: snapshot.agents || [],
  };
}

/** What a forming table is still short of — named rather than inferred.
 *  Port of lobby_page._waiting_for: an empty seat and a missing manager are
 *  different jobs for different people, and a reader who cannot tell which is
 *  being asked of them does neither. */
export function waitingFor(t) {
  const wants = [];
  const empty = t.traders - t.seats.length;
  if (empty > 0) wants.push(`${empty} more entrant${empty === 1 ? "" : "s"} to sit down`);
  if (!t.manager) wants.push("somebody to offer to manage it");
  return wants.length ? "Waiting for " + wants.join(" and ") + "." : "";
}

export function state(t) {
  if (t.lapsed) return "lapsed";
  if (t.settled) return "settled";
  return `forming — ${t.seats.length}/${t.traders} seated`;
}
