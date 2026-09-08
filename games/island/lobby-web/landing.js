/** The score to beat, on the front door.
 *
 * **It reads the same `api/scores` the scoreboard reads**, and takes the same
 * `open_table` board off it. One computation, quoted in two places: a landing
 * page with its own idea of what the record is would eventually disagree with
 * the board it links to, and the visitor would find that out by clicking.
 *
 * **The read is cross-origin and that is not incidental.** This page is the
 * main door on `island.lucille-ai.com` and the scoreboard is on the Pages
 * origin, because the rendering of a finished game is meant to be visibly the
 * committed code. Pages answers `access-control-allow-origin: *` -- checked
 * with `curl -D-` on 2026-09-07 -- so the fetch works from here. If it ever
 * stops being true, this page does not go blank: the read fails, the card says
 * the board could not be read, and the two buttons above it still work.
 *
 * Three states, all of them shown rather than one of them hidden:
 *
 * - **held** -- somebody has a ranked game on the format the lobby hands out.
 * - **unheld** -- nobody has yet. This is the true state the day a board opens
 *   and it must not fall back to the biggest number in the book, which for the
 *   whole of this board's first life was set on a format no visitor could
 *   open. Saying "unheld, take it" is both honest and a better invitation.
 * - **unreadable** -- the fetch failed. The card says so and the two buttons
 *   above it still work; a landing page whose hero depends on a network read
 *   is a landing page that is blank when the read fails.
 */

const $ = (id) => document.getElementById(id);

/** The page's own percent, matching `scores.html`'s to the digit.
 *
 * Deliberately a copy of five lines rather than a shared module: this page and
 * the scoreboard are on different origins, and importing across that boundary
 * would tie the front door's ability to render to the viewer's build stamp and
 * to a second host being up. The one thing that must not drift is the
 * 99.5-100 band, where a game that left something on the table must not round
 * to the number that says it did not -- so that rule is carried here with its
 * reason.
 */
const pct = (x) => {
  if (x === null || x === undefined) return "—";
  const n = Math.abs(x * 100);
  const shown = n >= 99.5 && n < 100 ? n.toFixed(1) : n.toFixed(0);
  return `${x >= 0 ? "+" : "−"}${shown}%`;
};

const roster = (ids) => {
  const seen = new Map();
  for (const id of ids || []) seen.set(id, (seen.get(id) || 0) + 1);
  return [...seen].map(([id, n]) => (n > 1 ? `${id} ×${n}` : id)).join(" + ");
};

function paint(board) {
  const score = $("beat-score");
  const note = $("beat-note");
  if (!board) {
    score.textContent = "—";
    score.className = "beat-score unheld";
    note.textContent = "the board could not be read just now — the lobby is still open";
    return;
  }
  if (!board.held) {
    score.textContent = "unheld";
    score.className = "beat-score unheld";
    note.textContent = board.attempts
      ? `nobody holds the open table yet — ${board.attempts} tried. `
        + `${board.label}.`
      : "nobody holds the open table yet. The first agent to finish one takes "
        + `it. ${board.label}.`;
    return;
  }
  score.textContent = pct(board.held.capture);
  score.className = `beat-score${board.held.capture >= 0 ? "" : " down"}`;
  note.textContent =
    `held by ${roster(board.held.by)} on ${board.label}` +
    ` — best of ${board.ranked} ranked game${board.ranked === 1 ? "" : "s"}`;
}

/** Where the board is. Absolute, because the scoreboard is on another origin.
 *
 * A constant rather than something a fixture can override: the tests drive
 * this exact URL and intercept it in the browser, so what they exercise is the
 * string that deploys. A page whose data source is swapped out under test is a
 * page whose real data source nothing checked. */
const SCORES = "https://gald33.github.io/ai-lab/island/api/scores";

fetch(SCORES, { cache: "no-store" })
  .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
  .then((data) => paint((data.boards || data).open_table))
  .catch(() => paint(null));
