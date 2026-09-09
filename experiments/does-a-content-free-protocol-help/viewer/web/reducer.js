// The board, read as a game.
//
// One input: the channel's messages, oldest first. One output: a timeline of
// states you can scrub. Nothing here talks to a hub, and nothing here writes.
//
// The rule that shapes every line below: **only the manager's receipts move
// state.** A trader saying `PRODUCE bread=0.5` has attempted something; the
// stock changes when `@T1 produced {'bread': 0.44}` comes back. Self-reports
// are not authoritative in the experiment and they are not authoritative here
// either -- a page that believed them would show trades that never settled and
// stocks the manager never granted.
//
// The second rule: an unrecognised line is talk. Most lines are talk, and a
// line that is nearly a receipt is never repaired into one. If the manager's
// wording changes, this reducer must go quiet about it rather than guess --
// `unknown` counts them so the page can say so out loud.

export const MANAGER = "manager";

//: The line that says who is playing, and therefore who is dealing. Matched
//: against every author rather than only the one called "manager", because a
//: live board names its authors by peer id -- see `reduce`.
const SCHEDULE = /^Schedule for this round\. \d+ traders: ([^.]+)\./;

// Python's `repr` of a dict, which is what a receipt carries. Keys are the
// manager's own good names and values are its own rounding, so this matches
// exactly what it wrote rather than reformatting it into something tidier.
function bundle(text) {
  const out = {};
  const re = /'([a-z]+)':\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)/g;
  let m;
  while ((m = re.exec(text)) !== null) out[m[1]] = parseFloat(m[2]);
  return out;
}

/**
 * The bell as a moment, not a time of day.
 *
 * The manager writes "the bell is at 12:42:27Z", which `Date.parse` cannot read
 * -- it has no date in it. Everything downstream that compared it to a clock got
 * `NaN` and quietly did nothing: the live countdown read "bell due" from the
 * first second of every episode, and it is why the sun had no way to know how
 * far through the day it was.
 *
 * The date comes from the line that announced the bell, which is timestamped in
 * full. A bell earlier in the day than its own announcement is tomorrow's --
 * an episode opening at 23:59 rings at 00:01.
 */
export function instant(clock, anchor) {
  if (!clock) return null;
  if (/\d{4}-\d{2}-\d{2}/.test(clock)) return clock;
  const hms = /^(\d{1,2}):(\d{2})(?::(\d{2}))?Z?$/.exec(String(clock).trim());
  const base = anchor ? new Date(anchor) : null;
  if (!hms || !base || Number.isNaN(base.getTime())) return clock;
  const when = new Date(Date.UTC(base.getUTCFullYear(), base.getUTCMonth(),
                                 base.getUTCDate(), +hms[1], +hms[2], +(hms[3] || 0)));
  if (when.getTime() < base.getTime() - 60_000) when.setUTCDate(when.getUTCDate() + 1);
  return when.toISOString();
}

const RECEIPTS = [
  // The schedule. `hide` rounds announce a span instead of a total, so the
  // episode count is optional and the page has to survive not knowing it.

  [/^Schedule for this round\. \d+ traders: ([^.]+)\./, (m, e) => {
    e.kind = "schedule";
    e.traders = m[1].split(",").map((s) => s.trim()).filter(Boolean);
    const span = /(\d+) episodes, (\d+)s each/.exec(e.body);
    if (span) { e.episodes = +span[1]; e.seconds = +span[2]; }
    else {
      const each = /Episodes are (\d+)s each/.exec(e.body);
      if (each) e.seconds = +each[1];
    }
  }],
  [/^(\d+)\/(\d+) acknowledged \(([^)]*)\)/, (m, e) => {
    e.kind = "acknowledged";
    e.count = +m[1]; e.of = +m[2];
    e.traders = m[3] === "nobody" ? [] : m[3].split(",").map((s) => s.trim());
  }],
  [/^episode (\d+)(?: of (\d+))? is open/, (m, e) => {
    e.kind = "open";
    e.episode = +m[1];
    if (m[2]) e.of = +m[2];
    // Two schedules have run: one with a production window inside the episode,
    // one with no stages at all. Both are drawable; which one this is can only
    // be read off the wording, so read it and let the page adapt.
    const window = /PRODUCE is settled for the next (\d+)s/.exec(e.body);
    if (window) { e.staged = true; e.production_seconds = +window[1]; }
    const bell = /the bell is at (\S+?)[\s(]/.exec(e.body);
    if (bell) e.bell_at = instant(bell[1], e.at);
    const span = /\((\d+)s\)/.exec(e.body);
    if (span) e.seconds = +span[1];
  }],
  [/^production is closed\./, (m, e) => { e.kind = "production_closed"; }],
  [/^@(\S+) produced (\{[^}]*\}); (-?[\d.]+) labour unspent/, (m, e) => {
    e.kind = "produced";
    e.trader = m[1]; e.made = bundle(m[2]);
    // `-0.0` is a real receipt: a plan summing to exactly 1.0 leaves float
    // noise behind. It means nothing was left, not that labour went negative.
    e.unspent = Math.abs(parseFloat(m[3])) < 1e-9 ? 0 : parseFloat(m[3]);
  }],
  [/^(p\d+): (\S+) offers (\{[^}]*\}) to (\S+) for (\{[^}]*\})/, (m, e) => {
    e.kind = "offer";
    e.pid = m[1]; e.maker = m[2]; e.give = bundle(m[3]);
    e.taker = m[4]; e.want = bundle(m[5]);
  }],
  [/^(p\d+) settled: (\S+) and (\S+) exchanged (\{[^}]*\}) for (\{[^}]*\})/, (m, e) => {
    e.kind = "settled";
    e.pid = m[1]; e.maker = m[2]; e.taker = m[3];
    e.give = bundle(m[4]); e.want = bundle(m[5]);
  }],
  //: The offer's other ending. A decline closes the proposal and hands the
  //: maker back what it had escrowed, so it moves state; the manager says so
  //: on the board exactly as it says a settlement.
  [/^(p\d+) declined: (\S+) will not take (\S+)'s offer/, (m, e) => {
    e.kind = "declined"; e.pid = m[1]; e.taker = m[2]; e.maker = m[3];
  }],
  [/^@(\S+) not settled: (.+)$/s, (m, e) => {
    e.kind = "refused"; e.trader = m[1]; e.reason = m[2].trim();
  }],
  [/^bell — episode (\d+) closed\. (\d+) proposal\(s\) lapsed/, (m, e) => {
    e.kind = "bell"; e.episode = +m[1]; e.lapsed = +m[2];
  }],
  [/^the round is over\./, (m, e) => { e.kind = "over"; }],
  [/^(\d+)s remain in this episode/, (m, e) => { e.kind = "tick"; e.left = +m[1]; }],
  [/^episodes (\d+) to (\d+) are scheduled next/, (m, e) => {
    e.kind = "upcoming"; e.from = +m[1]; e.to = +m[2];
  }],
  // Not economy, but the page must never draw these as quiet: a session that
  // could not start is a different event from a trader choosing to say nothing.
  [/^harness fault: (.+)$/, (m, e) => { e.kind = "fault"; e.detail = m[1]; }],
  [/^(\S+)'s session did not join/, (m, e) => { e.kind = "restart"; e.trader = m[1]; }],
];

// What a trader said, classified by the same grammar the manager parses with --
// so the page can show an attempt as an attempt while it is in flight, and
// still let the receipt be the thing that moves a stock.
function attempt(text) {
  const head = (text.trim().split(/\s+/)[0] || "").toUpperCase();
  if (head === "PRODUCE" || head === "PROPOSE" || head === "APPROVE") return head;
  if (head.startsWith("ACK")) return "ACK";
  // A sealed line is an action this page cannot read, which is different from
  // talk and must not be counted as it. In a sealed round a trader's PRODUCE
  // arrives like this -- the manager opens it and the receipt is still public,
  // so the island is drawn from the receipt exactly as before.
  if (head === "SEALED") return "SEALED";
  return null;
}

export function classify(message, { manager = MANAGER, traders = [] } = {}) {
  const body = typeof message.body === "string" ? message.body : "";
  const e = { seq: message.seq, at: message.at, author: message.author, body };
  const fromManager = message.author === manager
    || (traders.length > 0 && !traders.includes(message.author));
  if (fromManager) {
    for (const [re, fill] of RECEIPTS) {
      const m = re.exec(body.trim());
      if (m) { fill(m, e); return e; }
    }
    e.kind = "unknown";
    return e;
  }
  e.kind = "said";
  e.attempt = attempt(body);
  return e;
}

const empty = (traders, goods) =>
  Object.fromEntries(traders.map((t) => [t, Object.fromEntries(goods.map((g) => [g, 0]))]));

function blank(goods) {
  return Object.fromEntries(goods.map((g) => [g, 0]));
}

/** Fold the board into a scrubbable timeline. Pure: same board, same frames. */
export function reduce(messages, { manager = MANAGER, goods = null } = {}) {
  const rows = [...messages].sort((a, b) => (a.seq ?? 0) - (b.seq ?? 0));

  // Two passes. The first learns who is playing and in what, because the
  // opening state has to be drawn before the first receipt arrives -- four
  // empty huts, not an empty island that fills in as names are discovered.
  let traders = [];
  // Whoever announces the schedule *is* the manager. A saved board has already
  // been written in seat names -- `manager`, `T1`, `T2` -- but a live one
  // carries raw peer ids, so insisting the manager be literally called
  // "manager" meant the schedule was never recognised live: `traders` stayed
  // empty, the fallback below made a trader of every author, and the manager's
  // own session id got a hut of its own on the island.
  for (const r of rows) {
    const found = SCHEDULE.exec(String(r.body ?? "").trim());
    if (found) {
      manager = r.author;
      traders = found[1].split(",").map((x) => x.trim()).filter(Boolean);
      break;
    }
  }
  if (!traders.length) {
    const seen = new Set();
    for (const r of rows) if (r.author !== manager) seen.add(r.author);
    traders = [...seen].sort();
  }
  const words = goods ? [...goods] : (() => {
    const seen = new Set();
    for (const r of rows) {
      const e = classify(r, { manager, traders });
      for (const b of [e.made, e.give, e.want]) if (b) Object.keys(b).forEach((g) => seen.add(g));
    }
    // The manager's own order, which is the order every receipt is written in.
    const canonical = ["bread", "cloth", "iron", "salt", "fish", "grain", "timber"];
    return [...seen].sort((a, b) => {
      const ia = canonical.indexOf(a), ib = canonical.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.localeCompare(b);
    });
  })();

  let state = {
    phase: "before",          // before | ack | production | market | closed | over
    episode: 0,
    episodes: null,
    staged: false,
    bell_at: null,
    at: null,
    seconds: null,
    stocks: empty(traders, words),
    made: empty(traders, words),      // this episode's production, for the labour wheel
    labour: Object.fromEntries(traders.map((t) => [t, null])),
    proposals: [],                    // {pid, maker, taker, give, want, status}
    acknowledged: [],
    spoke: [],
    counters: { settled: 0, declined: 0, refused: 0, lapsed: 0, produced: 0,
                talk: 0, unknown: 0 },
    episodes_closed: [],              // holdings at each bell, before the reset
    last: null,
  };

  const frames = [];
  const events = [];
  const clone = (s) => ({
    ...s,
    stocks: Object.fromEntries(Object.entries(s.stocks).map(([t, b]) => [t, { ...b }])),
    made: Object.fromEntries(Object.entries(s.made).map(([t, b]) => [t, { ...b }])),
    labour: { ...s.labour },
    proposals: s.proposals.map((p) => ({ ...p })),
    acknowledged: [...s.acknowledged],
    spoke: [...s.spoke],
    counters: { ...s.counters },
    episodes_closed: s.episodes_closed.map((x) => ({
      ...x, holdings: Object.fromEntries(Object.entries(x.holdings).map(([t, b]) => [t, { ...b }])),
    })),
  });

  // How much of a stock is already promised to an open proposal. The manager
  // checks exactly this before it settles anything, so a shelf that does not
  // show it will look like it holds goods the maker cannot in fact offer.
  const committed = (s, trader, good) => s.proposals
    .filter((p) => p.status === "open" && p.maker === trader)
    .reduce((n, p) => n + (p.give[good] || 0), 0);

  for (const row of rows) {
    const e = classify(row, { manager, traders });
    events.push(e);
    const s = state;
    s.last = e;
    // When this frame is, by the board's own clock. The scene needs it to know
    // how far through the episode the frame sits -- the sun's position is that
    // fraction, and a state that cannot say when it is cannot be drawn at a
    // time of day.
    s.at = e.at ?? s.at;

    switch (e.kind) {
      case "schedule":
        s.phase = "ack";
        s.episodes = e.episodes ?? s.episodes;
        s.seconds = e.seconds ?? s.seconds;
        break;
      case "acknowledged":
        s.acknowledged = e.traders;
        break;
      case "open":
        s.episode = e.episode;
        s.episodes = e.of ?? s.episodes;
        s.staged = !!e.staged;
        s.phase = e.staged ? "production" : "market";
        s.bell_at = e.bell_at ?? null;
        s.seconds = e.seconds ?? s.seconds;
        break;
      case "production_closed":
        s.phase = "market";
        break;
      case "produced": {
        if (!s.stocks[e.trader]) break;
        for (const [g, qty] of Object.entries(e.made)) {
          s.stocks[e.trader][g] = (s.stocks[e.trader][g] || 0) + qty;
          s.made[e.trader][g] = (s.made[e.trader][g] || 0) + qty;
        }
        s.labour[e.trader] = e.unspent;
        s.counters.produced += 1;
        break;
      }
      case "offer":
        s.proposals.push({
          pid: e.pid, maker: e.maker, taker: e.taker,
          give: e.give, want: e.want, status: "open", episode: s.episode, seq: e.seq,
        });
        break;
      case "settled": {
        const p = s.proposals.find((x) => x.pid === e.pid);
        if (p) p.status = "settled";
        // Move what the receipt says was moved, not what the proposal said.
        // They agree today; if they ever stop, the receipt is the truth.
        for (const [g, qty] of Object.entries(e.give)) {
          s.stocks[e.maker][g] -= qty;
          s.stocks[e.taker][g] += qty;
        }
        for (const [g, qty] of Object.entries(e.want)) {
          s.stocks[e.taker][g] -= qty;
          s.stocks[e.maker][g] += qty;
        }
        s.counters.settled += 1;
        break;
      }
      case "declined": {
        const p = s.proposals.find((x) => x.pid === e.pid);
        if (p) p.status = "declined";
        //: No stock moves. The goods were never anywhere but the maker's own
        //: shelf -- the escrow is `manager.py:_free` refusing to let them be
        //: spent twice, not a pile standing somewhere else -- so what a
        //: decline changes is what the maker may commit next, not what it has.
        s.counters.declined += 1;
        break;
      }
      case "refused":
        s.counters.refused += 1;
        break;
      case "bell": {
        const open = s.proposals.filter((p) => p.status === "open");
        open.forEach((p) => { p.status = "lapsed"; });
        s.counters.lapsed += open.length;
        s.episodes_closed.push({
          episode: e.episode,
          holdings: Object.fromEntries(traders.map((t) => [t, { ...s.stocks[t] }])),
          lapsed: open.map((p) => p.pid),
          starved: traders.filter((t) => words.some((g) => (s.stocks[t][g] || 0) <= 1e-12)),
        });
        // The bell eats everything. Stocks and labour reset; the proposals stay
        // in the list, closed, because the page shows the episode it just ran.
        s.stocks = empty(traders, words);
        s.made = empty(traders, words);
        s.labour = Object.fromEntries(traders.map((t) => [t, null]));
        s.phase = "closed";
        break;
      }
      case "over":
        s.phase = "over";
        break;
      case "said":
        if (!s.spoke.includes(e.author)) s.spoke.push(e.author);
        if (!e.attempt) s.counters.talk += 1;
        break;
      case "unknown":
        s.counters.unknown += 1;
        break;
      default:
        break;
    }
    frames.push({ event: e, state: clone(s) });
  }

  return {
    traders, goods: words, events, frames,
    manager,
    committed,
    final: frames.length ? frames[frames.length - 1].state : clone(state),
    blank: () => blank(words),
  };
}
