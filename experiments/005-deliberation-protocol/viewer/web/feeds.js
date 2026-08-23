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
  let stop = false;
  let inflight = false;

  async function tick() {
    if (stop || inflight) return;
    inflight = true;
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) throw new Error(`${response.status} from ${url}`);
      const state = await response.json();
      const { rows, sealed } = rowsFromState(state, { channel });
      on.update?.({ rows, sealed, hub: state.hub, agents: state.agents || [], raw: state });
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
