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

// The one thing this file borrows from the drawing: how long an event needs to
// be watched. It is defined beside the animations it mirrors so the two cannot
// drift -- see `scene.js:DWELL`.
import { dwellFor } from "./scene.js";

const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

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
    // A broadcast row: the manager re-posting a room line into the lobby
    // workspace (`run_game._broadcast`). The hub names it by the poster,
    // which is always the manager, so the author it carries inside is the
    // one that counts, and the room's own seq keeps the order the room had.
    if (m.body && typeof m.body === "object" && typeof m.body.text === "string"
        && typeof m.body.as === "string") {
      rows.push({ seq: m.body.seq ?? m.seq, at: m.body.at || m.created_at,
                  author: m.body.as, body: m.body.text });
      continue;
    }
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
export const MIN_STEP = 140, MAX_STEP = 2600, QUIET = 4000;

//: How much `tightened` compresses a silence by. It was the transport's
//: default speed when the transport had speeds, and it stays the default
//: pace, so the page a viewer opens plays exactly as it did before.
const TIGHTEN = 4;

/**
 * The three ways the replay can be paced.
 *
 * **They replaced 1x / 4x / 16x, which were not three things.** `stepDelay`
 * divides only the gap term and never the animation, so at 16x the gap came to
 * `MAX_STEP / 16` = 162ms -- under almost every `dwellFor`. On any stretch
 * where something was actually happening, 4x and 16x rendered identically and
 * differed only across silence: two controls doing one job, and neither of them
 * the one that was missing.
 *
 * The missing one is `live`. The gap was clamped at `MAX_STEP` *before* speed
 * touched it, so a forty-second silence and a three-second silence played the
 * same at every speed, and no setting anywhere showed a round at the pace it
 * was actually played. On these boards -- 150s days in which two traders say
 * three things each -- that is most of what happened.
 *
 * So these are three *rules*, not three numbers, and each looks different on
 * every board:
 *
 * | pace | the waiting | the animation |
 * |---|---|---|
 * | `live` | the real gap, uncompressed | never cut short |
 * | `tight` | clamped, then divided by `TIGHTEN` | never cut short |
 * | `step` | none at all | never cut short |
 *
 * The animation floor is the same in all three because it was never about
 * speed: a frame that draws a parcel crossing the square needs the time that
 * crossing takes, whatever the clock is doing.
 */
export const PACES = {
  //: The island already has a clock -- the sun crosses on `dayProgress` -- so
  //: stillness here reads as time passing rather than as a stalled page. That
  //: is what makes real time watchable at all, and it is why this pace can
  //: exist now and could not have before the sun did.
  live: { label: "real time", says: "The round at the pace it was played" },
  tight: { label: "tightened", says: "Silences compressed, animations kept whole" },
  step: { label: "one at a time", says: "No waiting: each line held only for what it draws" },
};

/** The pace a viewer who has chosen nothing gets. */
export const PACE_DEFAULT = "tight";

/**
 * How long to hold one frame, under a given pace.
 *
 * `gap` is the real time since the previous board message, in ms.
 */
export function paceDelay(gap, pace, event, isStill = false) {
  const dwell = dwellFor(event, isStill);
  if (pace === "live") return Math.max(gap, dwell);
  //: A floor even here, or a board with no timestamps -- every gap zero --
  //: plays every silent line in one frame and reads as a page that skipped.
  if (pace === "step") return Math.max(MIN_STEP, dwell);
  return stepDelay(gap, TIGHTEN, event, isStill);
}

/**
 * Whether a frame arrived after a silence long enough to be worth saying so.
 *
 * Only under a pace that compressed it. Under `live` the viewer has just sat
 * through the pause and does not need to be told there was one -- and saying it
 * anyway is the page narrating what the viewer can see, which is the habit
 * `QUIET` was declared to break and then never used to break.
 */
export function quietBefore(gap, pace) {
  return pace !== "live" && gap >= QUIET ? gap : 0;
}

/**
 * How long to hold one frame: the compressed gap, or the time its animation
 * needs -- whichever is longer.
 *
 * The floor is deliberately **not** divided by speed. Speed compresses the
 * waiting between events; it has no business compressing the events. Before
 * this, `4x` -- the default -- stepped every `MIN_STEP / 4` = 35ms while a
 * parcel took a second to cross the square, so a busy stretch played six
 * animations on top of each other and read as a flicker.
 *
 * So `16x` is no longer sixteen times faster on a busy board. That is the
 * point of it: it is the clock that is compressed, not the picture.
 */
export function stepDelay(gap, speed, event, isStill = false) {
  const clamped = Math.min(MAX_STEP, Math.max(MIN_STEP, gap));
  return Math.max(clamped / speed, dwellFor(event, isStill));
}

export function replayPlayer(timeline, on = {}) {
  let index = -1;
  let pace = PACE_DEFAULT;
  let playing = false;
  let timer = null;

  const at = (i) => Date.parse(timeline.frames[i]?.event?.at || "") || null;

  function gapBefore(i) {
    if (i <= 0) return 0;
    const a = at(i - 1), b = at(i);
    return a && b ? Math.max(0, b - a) : 0;
  }

  //: The frame being *stepped to* is the one about to be animated, so it is
  //: that frame's event that decides how long the step takes.
  const delayTo = (i) =>
    paceDelay(gapBefore(i), pace, timeline.frames[i]?.event, still());

  function emit(animate) {
    const frame = timeline.frames[index];
    if (!frame) return;
    on.frame?.({
      index, frame, state: frame.state, event: frame.event, animate,
      // When the next line lands on the board, and how long this frame is on
      // screen before it. Together they let the sun cross the whole of the
      // time nobody acted, over the moment the replay holds here -- which is
      // what makes a silence look long instead of being counted out in a pill.
      until: timeline.frames[index + 1]?.event?.at ?? null,
      hold: animate ? delayTo(index + 1) : 0,
      //: How long the board was silent before this line, when the pace just
      //: compressed that silence away. Zero otherwise -- including under
      //: `live`, where the viewer sat through it.
      quiet: quietBefore(gapBefore(index), pace),
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
    }, delayTo(index + 1));
  }

  return {
    get index() { return index; },
    get playing() { return playing; },
    get pace() { return pace; },
    play() { if (index >= timeline.frames.length - 1) index = -1; playing = true; schedule(); on.state?.(); },
    pause() { playing = false; clearTimeout(timer); on.state?.(); },
    toggle() { this.playing ? this.pause() : this.play(); },
    //: A pace change reschedules the frame in flight rather than waiting for
    //: it to land. Switching to `step` in the middle of a forty-second `live`
    //: silence should not make the viewer sit out the rest of the silence they
    //: just asked to stop sitting through.
    setPace(name) {
      pace = PACES[name] ? name : PACE_DEFAULT;
      if (playing) schedule();
      on.state?.();
    },
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
