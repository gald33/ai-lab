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

const RE = {
  commits: /^(T\d+) commits ([0-9a-f]+)/,
  forming: /^(T\d+) is forming: (\d+) traders, (\d+) goods, (\d+) episodes, (\d+) round/,
  seat:    /^(T\d+) seat (T\d+) = (\S+?), key (\S+?)(, sealed|, in the clear)?(?:, nonce ([0-9a-f]+))? \((\d+)\/(\d+)\)$/,
  manager: /^(T\d+) will be managed by (\S+?), key (\S+)$/,
  full:    /^(T\d+) is full: (.*?); managed by (.*?); opens (\S+?)(;.*)?$/,
  island:  /^(T\d+): the island is (.+)$/,
  lapsed:  /^(T\d+) lapsed: (.+?) within \d+s \((\d+)\/(\d+) seated(?:, managed by (.+?))?\)$/,
  refusal: /^@(\S+) not settled: (.+)$/,
  invite:  /^(T\d+) invite: /,
};

function table(tables, id) {
  if (!tables.has(id)) {
    tables.set(id, {
      id, traders: 0, goods: 0, episodes: 0, rounds: 1,
      opened_at: 0, seats: [], commit: "", manager: null, manager_key: null,
      settled: false, lapsed: false, opens_at: null, draw: "",
      practice: false, lapse_reason: "", roster: "",
    });
  }
  return tables.get(id);
}

/** Build the lobby view from a decrypted snapshot ({agents, messages}).
 *  `messages` are the channel's history, oldest first. */
export function reconstruct(snapshot, channel) {
  const tables = new Map();
  const refusals = [];
  let holder = null, lastLine = 0;

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
    if (RE.invite.test(body)) continue;   // a room credential; never rendered

    if ((m = RE.commits.exec(body)))  { table(tables, m[1]).commit = m[2]; continue; }
    if ((m = RE.forming.exec(body)))  {
      const t = table(tables, m[1]);
      Object.assign(t, { traders: +m[2], goods: +m[3], episodes: +m[4],
                         rounds: +m[5], opened_at: t.opened_at || at });
      continue;
    }
    if ((m = RE.seat.exec(body))) {
      const t = table(tables, m[1]);
      if (!t.seats.some(s => s.label === m[2]))
        t.seats.push({ label: m[2], name: m[3], key: m[4],
                       sealed: m[5] === ", sealed", nonce: m[6] || "" });
      if (!t.traders) t.traders = +m[8];
      continue;
    }
    if ((m = RE.manager.exec(body))) {
      const t = table(tables, m[1]); t.manager = m[2]; t.manager_key = m[3]; continue;
    }
    if ((m = RE.full.exec(body))) {
      const t = table(tables, m[1]);
      Object.assign(t, { settled: true, roster: m[2], manager: t.manager || m[3],
                         opens_at: Date.parse(m[4]) / 1000 || null,
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
