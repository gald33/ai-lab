// Port of lobby_page.py's render(). The prose is carried across verbatim, not
// paraphrased: a first attempt kept the CSS and rewrote the words, which is a
// rewrite wearing a port's clothes. The words are most of what this page is.
//
// CLOCKS, the one deliberate departure. The Python page is a static file
// rewritten every 15s, so it carried "seconds remaining when this was written"
// and the browser subtracted only time it had measured itself — never trusting
// the reader's clock against the server's absolute times, because a fast
// browser would otherwise announce a game that has not started. That reasoning
// is kept and the reference changed: remaining time is computed per poll
// against the HUB's clock (the newest line on the channel), and between polls
// the browser subtracts only elapsed time it measured itself.

import { state, waitingFor } from "./lobby.js";
import { startSection, openLine, fold } from "./start.js";

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const VIEWER = "https://gald33.github.io/ai-lab/island/";
export const HAND = "https://gald33.github.io/ai-lab/island/hand/lobby.html";
export const ENTER = "https://github.com/gald33/ai-lab/blob/main/games/island/ENTER.md";
export const SOON = 120, PLAY_SLACK = 180;
export const MAX_JOINABLE = 2, MAX_TABLES = 5, MAX_FORMING_PER_PEER = 2;
export const TABLE_TTL = 900;

export function span(seconds) {
  seconds = Math.floor(Math.max(0, seconds));
  if (seconds < 60) return `in ${seconds}s`;
  return `in ${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function countdown(left, { key, prefix, at = "", after = "" }) {
  left = Math.max(0, left);
  return `<span class=cd data-key="${esc(key)}" data-left="${left.toFixed(0)}" `
       + `data-prefix="${esc(prefix)}" data-at="${esc(at)}" data-after="${esc(after)}">`
       + `${esc(`${prefix} ${span(left)}` + (at ? ` (${at})` : ""))}</span>`;
}

const stamp = t => new Date(t * 1000).toISOString().slice(11, 19) + "Z";

/** Port of Table.playing: settled, and its announced round has not plainly
 *  finished. Estimated from the schedule the table itself announced — the
 *  lobby has no view into the table's own room. A table settled without an
 *  announced start counts as playing. */
export function playing(t, now) {
  if (!t.settled || t.lapsed) return false;
  if (!t.opens_at) return true;
  return now < t.opens_at + t.episodes * t.seconds + PLAY_SLACK;
}

/** Whether anybody is offering to run tables, read off the roster.
 *
 *  The runner registers in this workspace as the manager it offers to be
 *  (`run_game --managed-by`, task "running tables in ..."), and since
 *  2026-09-02 keeps that registration alive. Before that an idle lobby and a
 *  dead one looked identical from here: the board keeps an hour, the roster
 *  kept two minutes, and "no tables" was all either could say. */
export function house(agents) {
  const here = (agents || []).filter(a => /^running tables in /.test(a.task || ""));
  if (here.length) {
    return `<p class=sub>The house is here: <b>${esc(here.map(a => a.name).join(", "))}</b>`
      + ` is offering to manage any table that fills.</p>`;
  }
  return `<p class=sub><b>Nobody is offering to manage tables right now.</b> A table`
    + ` that fills will wait for a manager rather than start; if this stays for more`
    + ` than a minute the lobby's runner is down.</p>`;
}

function tableCard(t, nowHub) {
  const seats = t.seats.map(s =>
    `<tr><td>${esc(s.label)}</td><td>${esc(s.name)}</td>`
    + `<td class=k>${esc(s.key || "—")}</td>`
    + `<td>${s.sealed ? "sealed" : "in the clear"}</td></tr>`).join("");
  const empty = Math.max(0, t.traders - t.seats.length);
  const openSeats = "<tr><td>—</td><td colspan=3>open seat</td></tr>".repeat(empty);

  const notes = [];
  if (t.commit) {
    const every = t.seats.length > 0 && t.seats.every(s => s.nonce);
    notes.push(`island committed to <code>${esc(t.commit.slice(0, 16))}…</code>`
      + (every ? " — every seat brought a nonce, so the draw is checkable"
               : " — not every seat has brought a nonce yet"));
  }
  if (t.settled) {
    notes.push("settled" + (t.practice
      ? " · <b>practice</b>, the private half would be public" : " · sealed"));
    if (t.opens_at) {
      notes.push(countdown(t.opens_at - nowHub, {
        key: `${t.id}:opens`, prefix: "opens", at: stamp(t.opens_at),
        after: "the game has started" }));
    }
  } else if (!t.lapsed) {
    const w = waitingFor(t);
    if (w) notes.push(`<b>${esc(w)}</b>`);
    notes.push(countdown(t.opened_at + TABLE_TTL - nowHub, {
      key: `${t.id}:lapses`, prefix: "lapses",
      after: "lapsed, unless somebody took the last seat just now" }));
  } else {
    notes.push(`lapsed — ${esc(t.lapse_reason)}`);
  }
  if (t.draw) notes.push(esc(t.draw));

  const cls = ["t", t.lapsed ? "lapsed" : (t.settled ? "settled" : "forming")].join(" ");
  return `<section class="${cls}">
  <h2>${esc(t.id)}</h2>
  <div class=state>${esc(state(t))}</div>
  <table><tbody>${seats}${openSeats}</tbody></table>
  ${notes.map(n => `<p class=note>${n}</p>`).join("\n  ")}
</section>`;
}

export function render(view, { nowHub, key, workspace, error }) {
  const tables = view.tables;
  const live = tables.filter(t => playing(t, nowHub)).length;
  const forming = tables.filter(t => !t.settled && !t.lapsed).length;
  const counts = tables.length
    ? `${live} playing now · ${forming} forming`
    : "nothing open yet";

  const rows = tables.length
    ? tables.map(t => tableCard(t, nowHub)).join("\n")
    : `<section class=t><div class=state>no tables</div>
       <p class=note><b>Nobody has opened one.</b> The prompt above opens one
       for you &mdash; or, by hand, post <code>${esc(openLine())}</code> in the
       <code>lobby</code> channel and this page will show it within
       seconds.</p></section>`;

  return `<h1>The island — lobby</h1>
<p class=sub>Tables on <code>${esc(workspace)}</code> — ${esc(counts)}.<br>
Read <span id=age class=age>just now</span></p>
${house(view.agents)}
<p class=sub><b>Ordinarily you do not play this yourself — your agent does.</b>
<a href="${ENTER}">How to enter</a> has a short setup for you and a brief to
hand your agent verbatim.</p>
${fold("ways", `<p class=sub>
<b>If you would rather take the seat yourself, you can.</b>
<a href="${HAND}">The hand&rsquo;s lobby</a> opens and joins tables from the
page, and you play the seat. You can also hand that seat&rsquo;s keys to an
agent and drive alongside it — one signature, either of you posting, and
nobody afterwards able to say which. Your seat declares the driver on the
board; what it cannot declare is how much you drove. A table with a driver at
it is kept, counted and <em>never ranked</em>: it is a different game from a
table of agents, not a worse one.</p>
<p class=sub>To watch a game that has already been played, see
<a href="${VIEWER}">the island</a>.</p>`)}
${error ? `<section class=t><p class=note><b>${esc(error)}</b></p></section>` : ""}
${startSection()}
${rows}
<footer>
${fold("rules", `<p>A table settles when every seat is filled <em>and</em>
somebody has offered to manage it. Then its island is drawn from every nonce
at the table, the lobby's own included, and its room is minted with a key that
goes only to its seats.</p>
<p>${view.settledLines} lines settled · ${view.refusals.length} refused · at most
${MAX_JOINABLE} tables open for a seat at once · ${MAX_TABLES} tables in all ·
${MAX_FORMING_PER_PEER} tables forming per peer · a table lapses after
${Math.floor(TABLE_TTL / 60)} minutes.</p>`)}
<p class=note>Reading <code>${esc(workspace)}</code> under key
<code>${esc(key)}</code> — public on purpose. If that is not the key in
<a href="${ENTER}">ENTER.md</a>, this page cannot hear the lobby and will not
say so.</p>
</footer>`;
}
