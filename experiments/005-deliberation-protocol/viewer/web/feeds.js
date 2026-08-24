// Where the messages come from. Two feeds, one shape.
//
// The wrapper never talks to a hub. The **live** feed reads the Switchboard
// viewer's own `api/state`, which is the thing that holds the token, the key
// and the read cursors -- so this page inherits every property that makes the
// viewer safe to point at a running round, including that reading here cannot
// advance any agent's cursor. The **replay** feed reads a saved board file and
// touches nothing at all.
//
// Both hand `reducer.js` the same rows: `{seq, at, author, body}`.

/** A board saved to disk: `{workspace, channel, messages: [...]}`. */
export async function loadBoard(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} reading ${url}`);
  const board = await response.json();
  if (!Array.isArray(board.messages)) throw new Error(`${url} has no messages`);
  return board;
}

/** The viewer's state, reduced to the rows this page reads. */
export function rowsFromState(state, { channel = null } = {}) {
  const sealed = [];
  const rows = [];
  for (const m of state.messages || []) {
    if (channel && m.channel !== channel) continue;
    if (m.sealed_body) { sealed.push(m.seq); continue; }
    if (typeof m.body !== "string") continue;
    rows.push({
      seq: m.seq,
      at: m.created_at,
      author: (m.from && (m.from.name || m.from.id)) || "?",
      body: m.body,
    });
  }
  return { rows, sealed };
}

/**
 * Poll the viewer. Never overlaps a request with itself, and a failed poll is
 * reported rather than swallowed: a page that quietly keeps showing the last
 * good state during an outage is a lie with a clock on it.
 */
export function liveFeed({ url = "api/state", channel = "island", every = 3000 } = {}, on = {}) {
  return pollFeed(async () => {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error(`${response.status} from ${url}`);
    return response.json();
  }, { channel, every }, on);
}

// The managed hub this wrapper points a hosted game at by default -- see
// games/island.md ("a hosted game points at the managed hub by default").
export const MANAGED_HUB = "https://switchboard.lucille-ai.com";

// Where Switchboard publishes the browser-side room reader. Reused rather
// than reimplemented: it is what already turns a hub's raw, sealed messages
// into readable rows in a browser, and `rowsFromState` below already reads
// the exact shape it returns (`{hub, agents, messages: [...]}`) -- both were
// written to the same contract on purpose. Importing it cross-origin works
// because it is published as a static file with no build step, on a host
// (GitHub Pages) that serves everything with permissive CORS.
const ROOM_READER_URL = "https://gald33.github.io/switchboard/switchboard-room.js";

let _room = null;
function loadRoomReader() {
  return (_room ??= import(ROOM_READER_URL));
}

/**
 * Read a room straight from a hub, in the browser -- no local viewer process
 * in between. `config` is `{url, workspace, key, token, probe}`, the exact
 * shape `decodeInvite()` below returns, so an invite can be handed to this
 * directly.
 */
export function hubFeed(config, { channel = "island", every = 3000 } = {}, on = {}) {
  return pollFeed(async () => {
    const { snapshot } = await loadRoomReader();
    return snapshot(config, { limit: 200, refresh: every / 1000 });
  }, { channel, every }, on);
}

/** An invite string, decoded -- re-exported so a page need import one module. */
export async function decodeInvite(text) {
  const { decodeInvite: decode } = await loadRoomReader();
  return decode(text);
}

function pollFeed(fetchState, { channel, every }, on) {
  let stop = false;
  let inflight = false;

  async function tick() {
    if (stop || inflight) return;
    inflight = true;
    try {
      const state = await fetchState();
      const { rows, sealed } = rowsFromState(state, { channel });
      on.update?.({
        rows, sealed, hub: state.hub, agents: state.agents || [], raw: state,
        // Only `hubFeed`'s snapshot carries these -- a hub it could not reach,
        // a room it could not open. `liveFeed`'s state has none, so this is
        // always [] there rather than undefined.
        notes: state.notes || [],
      });
    } catch (err) {
      on.error?.(err);
    } finally {
      inflight = false;
    }
  }

  tick();
  const timer = setInterval(tick, every);
  return { stop() { stop = true; clearInterval(timer); }, now: tick };
}

//: Real time between two board messages, compressed. A round is mostly silence
//: -- 60s episodes in which two traders each say three things -- so replaying
//: it at wall speed is minutes of a still picture. Gaps are clamped, and the
//: clamp is reported so the page can say a pause happened rather than pretend
//: the board was busy.
const MIN_STEP = 140, MAX_STEP = 2600, QUIET = 4000;

export function replayPlayer(timeline, on = {}) {
  let index = -1;
  let speed = 4;
  let playing = false;
  let timer = null;

  const at = (i) => Date.parse(timeline.frames[i]?.event?.at || "") || null;

  function gapBefore(i) {
    if (i <= 0) return 0;
    const a = at(i - 1), b = at(i);
    return a && b ? Math.max(0, b - a) : 0;
  }

  function stepDelay(i) {
    const gap = gapBefore(i);
    const clamped = Math.min(MAX_STEP, Math.max(MIN_STEP, gap));
    return clamped / speed;
  }

  function emit(animate) {
    const frame = timeline.frames[index];
    if (!frame) return;
    on.frame?.({
      index, frame, state: frame.state, event: frame.event,
      quiet: gapBefore(index) >= QUIET ? Math.round(gapBefore(index) / 1000) : 0,
      animate,
    });
  }

  function schedule() {
    clearTimeout(timer);
    if (!playing) return;
    if (index >= timeline.frames.length - 1) { playing = false; on.ended?.(); return; }
    timer = setTimeout(() => {
      index += 1;
      emit(true);
      schedule();
    }, stepDelay(index + 1));
  }

  return {
    get index() { return index; },
    get playing() { return playing; },
    get speed() { return speed; },
    play() { if (index >= timeline.frames.length - 1) index = -1; playing = true; schedule(); on.state?.(); },
    pause() { playing = false; clearTimeout(timer); on.state?.(); },
    toggle() { this.playing ? this.pause() : this.play(); },
    setSpeed(x) { speed = x; if (playing) schedule(); on.state?.(); },
    step(delta) {
      this.pause();
      index = Math.max(0, Math.min(timeline.frames.length - 1, index + delta));
      emit(delta > 0);
    },
    // Scrubbing replays state, never animation: dragging past six settled
    // trades should not fire six flights at once.
    seek(i) {
      index = Math.max(0, Math.min(timeline.frames.length - 1, i));
      emit(false);
      if (playing) schedule();
    },
    /** Jump to the frame that opened an episode -- the replay's chapters. */
    episodes() {
      return timeline.frames
        .map((f, i) => (f.event.kind === "open" ? { episode: f.event.episode, index: i } : null))
        .filter(Boolean);
    },
    stop() { playing = false; clearTimeout(timer); },
  };
}
