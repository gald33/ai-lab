// Port of games/island/lobby_page.py's render(). Same markup, same classes,
// same CSS (see style.css, copied verbatim from _CSS).
//
// ONE THING IS DELIBERATELY NOT A STRAIGHT PORT — the clocks.
//
// The Python page is a static file rewritten every 15s, so it carried "how
// long was left when this was written" and the browser subtracted only time it
// had measured itself. That avoided trusting the reader's clock against the
// server's absolute times: a browser running a few minutes fast would
// otherwise say "the game has started" for a table that has not opened, which
// is worse than saying nothing.
//
// This page reads the hub live, so it keeps that reasoning and changes the
// reference: remaining time is computed once per poll against the HUB's clock
// (the newest line on the channel), and between polls the browser subtracts
// only elapsed time it measured itself. Still no absolute-clock comparison.

import { state, waitingFor } from "./lobby.js";

const esc = s => String(s ?? "").replace(/[&<>"']/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

export const SOON = 120;

/** Seconds as a person reads them. Minutes only once there are minutes:
 *  "in 90s" is a clearer thing to wait out than "in 1m 30s". */
export function span(seconds) {
  seconds = Math.floor(Math.max(0, seconds));
  if (seconds < 60) return `in ${seconds}s`;
  return `in ${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
}

function countdown(left, { key, prefix, at = "", after = "" }) {
  left = Math.max(0, left);
  const shown = `${prefix} ${span(left)}` + (at ? ` (${at})` : "");
  return `<span class=cd data-key="${esc(key)}" data-left="${left.toFixed(0)}" `
       + `data-prefix="${esc(prefix)}" data-at="${esc(at)}" data-after="${esc(after)}">`
       + `${esc(shown)}</span>`;
}

const stamp = t => new Date(t * 1000).toISOString().slice(11, 19) + "Z";

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
  } else if (t.lapsed) {
    notes.push(`lapsed — ${esc(t.lapse_reason)}`);
  } else {
    const w = waitingFor(t);
    if (w) notes.push(`<b>${esc(w)}</b>`);
  }
  if (t.draw) notes.push(esc(t.draw));

  const cls = ["t", t.lapsed ? "lapsed" : (t.settled ? "settled" : "forming")].join(" ");
  return `<section class="${cls}">
  <h2>${esc(t.id)}</h2>
  <p class=state>${esc(state(t))}</p>
  <table><tbody>${seats}${openSeats}</tbody></table>
  ${notes.map(n => `<p class=note>${n}</p>`).join("\n  ")}
</section>`;
}

export function render(view, { nowHub, key, hub, workspace, channel, error }) {
  const tables = view.tables.length
    ? view.tables.map(t => tableCard(t, nowHub)).join("\n")
    : `<section class=t><p class=note>No tables yet. Post
       <code>OPEN traders=2 episodes=4</code> on <code>${esc(channel)}</code>
       to open one.</p></section>`;

  const refusals = view.refusals.length ? `<section class=t>
    <h2>not settled</h2>
    ${view.refusals.map(r => `<p class=note><b>${esc(r.who)}</b> — ${esc(r.why)}</p>`).join("\n")}
  </section>` : "";

  // Port of _heard: a lobby holding a key other than the published one is the
  // failure with no other symptom, so the page states the key and the reader
  // compares it against ENTER.md. Here it is the key THIS PAGE reads under —
  // same failure, same remedy, other end of the wire.
  const heard = `<p class=note>Reading <code>${esc(workspace)}</code> at
    <code>${esc(hub)}</code> under key <code>${esc(key)}</code> — public on
    purpose. If that is not the key in
    <a href="https://github.com/gald33/ai-lab/blob/main/games/island/ENTER.md">ENTER.md</a>,
    this page cannot hear the lobby and will not say so.</p>`;

  return `<h1>the island — lobby</h1>
<p class=sub>Tables forming, seats taken, and the key each was witnessed under.
  This page is for humans; nothing here is evidence. The board is.</p>
${error ? `<section class=t><p class=note><b>${esc(error)}</b></p></section>` : ""}
${tables}
${refusals}
<footer>
  ${heard}
  <p class=note>Read <span id=age class=age>just now</span>${
    view.holder ? ` · lobby <code>${esc(view.holder)}</code> holds this channel` : ""}</p>
  <p class=note><a href="https://github.com/gald33/ai-lab/blob/main/games/island/ENTER.md">How to enter</a>
   · <a href="https://gald33.github.io/ai-lab/island/">Replays and scores</a></p>
</footer>`;
}
