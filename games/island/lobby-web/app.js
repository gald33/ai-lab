// Wire the hub to the page: read, reconstruct, render, repeat.
import { snapshot } from "./vendor/switchboard-room.js";
import { reconstruct } from "./lobby.js";
import { render } from "./render.js";
import { wireStart } from "./start.js";
import { CONFIG } from "./config.js";

const main = document.querySelector("main");
const POLL_MS = 5000;
let started = performance.now(), lastRead = Date.now();

function tick() {
  // Countdowns: subtract only time this browser measured itself since the
  // last read, never a comparison against an absolute clock. See render.js.
  const elapsed = (performance.now() - started) / 1000;
  for (const el of document.querySelectorAll(".cd")) {
    const left = Math.max(0, parseFloat(el.dataset.left) - elapsed);
    const { prefix, at, after } = el.dataset;
    el.textContent = left <= 0 && after ? after
      : `${prefix} ${left < 60 ? `in ${Math.floor(left)}s`
          : `in ${Math.floor(left / 60)}m ${String(Math.floor(left % 60)).padStart(2, "0")}s`}`
        + (at ? ` (${at})` : "");
    el.classList.toggle("soon", left > 0 && left <= 120);
    el.classList.toggle("now", left <= 0);
  }
  const age = document.getElementById("age");
  if (age) {
    const s = Math.floor((Date.now() - lastRead) / 1000);
    age.textContent = s < 5 ? "just now" : s < 60 ? `${s}s ago`
      : `${Math.floor(s / 60)}m ${s % 60}s ago`;
    // Warm past three poll intervals: by then we have missed two reads and
    // the page is describing a lobby it can no longer see.
    age.classList.toggle("stale", s > (POLL_MS / 1000) * 3);
  }
  requestAnimationFrame(tick);
}

async function poll() {
  let view = { tables: [], refusals: [], settledLines: 0, holder: null, agents: [] }, error = "";
  let nowHub = Date.now() / 1000;
  try {
    const snap = await snapshot(CONFIG, { limit: 200, refresh: 5 });
    view = reconstruct(snap, CONFIG.channel);
    // The hub's clock, not this browser's: the newest line we can see.
    if (view.lastLine) nowHub = view.lastLine;
    if (snap.notes && snap.notes.length) error = snap.notes[0];
    lastRead = Date.now();
  } catch (e) {
    error = `cannot read the lobby: ${e.message}`;
  }
  main.innerHTML = render(view, { ...CONFIG, nowHub, error });
  // innerHTML replaced the nodes the copy button and levers were
  // bound to, so they are re-wired every poll rather than once.
  wireStart();
  started = performance.now();
}

poll();
setInterval(poll, POLL_MS);
requestAnimationFrame(tick);
