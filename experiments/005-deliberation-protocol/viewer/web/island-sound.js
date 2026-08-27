/**
 * The island, heard. The world it is in, the work going on in it, and one
 * quiet accent per event underneath both -- and silence until somebody asks.
 *
 * **The accents used to be the whole of it, and that was the wrong thing.**
 * One chime per board event over silence is a notification sound on a picture:
 * a spectator who leaves a replay running between offers heard nothing at all,
 * which is exactly backwards for a place with a sea round it. What you hear
 * now is `island-ambience.js` -- surf, wind, gulls at the right hours, the
 * fire, dolphins going past, and each site audibly at work when a receipt for
 * that good lands. The voices below survive at **less than half** their old
 * level, because the page already says what happened three times over (the
 * card, the transcript line, the clip on the ground) and sound must never be
 * the only place something is said.
 *
 * **Synthesised, not sampled.** Every other asset this viewer needs is in the
 * repository (`vendor/three`), and a set of audio files would be the first
 * binaries in it -- for six noises a few lines of oscillator each. Nothing is
 * fetched, so there is nothing to fail to load and nothing to keep in sync
 * with a deploy.
 *
 * **Off by default, and remembered.** A page that starts making noise is a
 * page somebody closes; browsers agree, and will not let an `AudioContext`
 * start before a gesture anyway. So the context is built the first time the
 * button is pressed and not before, which is also the moment the gesture
 * exists to unlock it.
 *
 * **Not tied to `prefers-reduced-motion`.** A reader who wants the island to
 * hold still has said nothing about hearing it, and `stage.fire()` is silent
 * under that setting -- so the sound is fired from the page beside the clip
 * rather than from inside it, and a still island can still be heard.
 */

import { Ambience } from "./island-ambience.js";

const KEY = "island:sound";

//: Peak of the master gain, well under 1: the bed, a site at work and several
//: voices can overlap on a busy settlement, and the sum -- not the loudest --
//: is what clips.
const MASTER = 0.32;

//: What an event voice keeps now that there is a world under it. Set by
//: listening: at full level the accents sat on top of the bed and the island
//: went back to being a picture with chimes over it.
const ACCENT = 0.42;

//: A floor between two soundings of the same voice. At 16x a scrub pours
//: events through in a few frames, and without this the bell rings forty
//: times in a second and reads as a fault in the page.
const FLOOR_MS = 90;

//: And a ceiling on everything at once, for the same reason from the other
//: side: a burst of different voices is still a burst.
const BUDGET = 6, BUDGET_MS = 700;

const now = () => (typeof performance !== "undefined" ? performance.now() : Date.now());

export class Sound {
  constructor() {
    this.on = false;
    this.ctx = null;
    this.master = null;
    this.last = new Map();
    this.recent = [];
    try { this.on = localStorage.getItem(KEY) === "on"; } catch { /* private mode */ }
  }

  /** What the button should show, and what the page remembers. */
  get enabled() { return this.on; }

  /**
   * Turn it on or off. Returns what it actually is afterwards -- a browser
   * that will not give us an `AudioContext` leaves it off, and the button
   * follows the truth rather than the request.
   */
  set(want) {
    this.on = !!want && this.wake();
    //: The island is either heard or it is not. One button, and the bed is
    //: the bulk of what it turns on.
    if (this.on) this.bed?.start(); else this.bed?.stop();
    try { localStorage.setItem(KEY, this.on ? "on" : "off"); } catch { /* private mode */ }
    return this.on;
  }

  toggle() { return this.set(!this.on); }

  /**
   * The hour, from the page's own clock -- the same day progress the drawn sun
   * and the model's light are on. The bed mixes to it: gulls at dawn and
   * through the day and none at night, the wind dropping with the light, the
   * fire the loudest thing left once it has gone.
   */
  setDay(day, closed = false) { this.bed?.setDay(day, closed); }

  /**
   * The page went away, or came back. A bed left running behind a hidden tab
   * is a browser tab making surf noises at somebody reading something else.
   */
  visible(shown) {
    if (!this.on) return;
    if (shown) this.bed?.start(); else this.bed?.stop();
  }

  /** The context, built on the gesture that asked for it. */
  wake() {
    if (this.ctx) { this.ctx.resume?.(); return true; }
    const Ctx = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!Ctx) return false;
    try {
      this.ctx = new Ctx();
      this.master = this.ctx.createGain();
      this.master.gain.value = MASTER;
      //: A limiter, not a taste: two settlements landing on the same frame
      //: would otherwise clip, and clipping is the one artefact a listener
      //: reads as broken rather than loud.
      const squeeze = this.ctx.createDynamicsCompressor();
      squeeze.threshold.value = -14;
      squeeze.ratio.value = 8;
      this.master.connect(squeeze).connect(this.ctx.destination);
      //: The voices go through their own gain rather than being written
      //: quieter one by one: their levels are set against each other, and a
      //: single bus is what keeps that balance while moving all of them.
      this.accent = this.ctx.createGain();
      this.accent.gain.value = ACCENT;
      this.accent.connect(this.master);
      this.bed = new Ambience(this.ctx, this.master);
      return true;
    } catch { this.ctx = null; return false; }
  }

  /** Whether this voice is allowed to sound now. */
  allowed(name) {
    const t = now();
    if (t - (this.last.get(name) ?? -1e9) < FLOOR_MS) return false;
    this.recent = this.recent.filter((x) => t - x < BUDGET_MS);
    if (this.recent.length >= BUDGET) return false;
    this.last.set(name, t);
    this.recent.push(t);
    return true;
  }

  /**
   * An event, heard. Silently does nothing when the sound is off, when the
   * event has no voice, and for a voice that has just sounded.
   */
  play(event) {
    const voice = VOICES[event?.kind];
    if (!this.on || !voice) return false;
    //: Remembered-on, first sounding of the session: the context was never
    //: built because no gesture had been made yet. Try now -- by the time an
    //: event is being painted somebody has pressed play, and a browser that
    //: still refuses simply leaves this silent.
    if (!this.ctx && !this.wake()) return false;
    if (this.ctx.state === "suspended") this.ctx.resume?.();
    if (!this.allowed(event.kind)) return false;
    //: A production is the one event that reaches the world rather than only
    //: being remarked on: the site that made it can be heard working for a few
    //: seconds afterwards. The bell takes the fire up with it, as the drawn
    //: island already does.
    if (event.kind === "produced") {
      for (const good of Object.keys(event.made || {})) this.bed?.working(good);
    } else if (event.kind === "bell") {
      this.bed?.flare();
    }
    try { voice(this.ctx, this.accent, this.ctx.currentTime); return true; }
    catch (err) { console.warn("the island went quiet", err); return false; }
  }
}

// --- the voices ------------------------------------------------------------
//
// Each is a few oscillators and an envelope, started and stopped: a WebAudio
// node that has run is finished, and the graph collects itself.

/** One tone, with an envelope that starts at zero and ends there. */
function tone(ctx, out, { freq, at, dur, peak = 0.2, type = "sine", to = null,
                          attack = 0.008 }) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.setValueAtTime(freq, at);
  if (to !== null) o.frequency.exponentialRampToValueAtTime(to, at + dur);
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(peak, at + attack);
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  o.connect(g).connect(out);
  o.start(at);
  o.stop(at + dur + 0.02);
}

/** A short burst of filtered noise -- wood, grit, a thing landing. */
function knock(ctx, out, { at, dur = 0.12, peak = 0.3, freq = 900, q = 1.2 }) {
  const n = Math.max(1, Math.floor(ctx.sampleRate * dur));
  const buf = ctx.createBuffer(1, n, ctx.sampleRate);
  const d = buf.getChannelData(0);
  //: Deterministic noise. `Math.random()` would do, and a fixed cheap PRNG
  //: means two soundings of the same voice are the same sound -- which is
  //: what makes it a voice rather than a texture.
  let s = 1234567;
  for (let i = 0; i < n; i++) {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    d[i] = (s / 0x3fffffff - 1) * (1 - i / n) ** 2;
  }
  const src = ctx.createBufferSource();
  src.buffer = buf;
  const f = ctx.createBiquadFilter();
  f.type = "bandpass";
  f.frequency.value = freq;
  f.Q.value = q;
  const g = ctx.createGain();
  g.gain.setValueAtTime(peak, at);
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  src.connect(f).connect(g).connect(out);
  src.start(at);
  src.stop(at + dur + 0.02);
}

const VOICES = {
  //: Something was made and it is standing in a yard: a crate put down on
  //: ground, which is a knock and the thud under it.
  //: **Quieter and lower than it was**, because it no longer arrives alone:
  //: the site it came from starts working in the same instant, and the two
  //: onsets together were most of what made a production unpleasant. The
  //: accent is now the crate touching down under the work, not a second
  //: announcement of it.
  produced(ctx, out, t) {
    knock(ctx, out, { at: t, dur: 0.12, freq: 430, peak: 0.13 });
    tone(ctx, out, { freq: 130, to: 84, at: t, dur: 0.2, peak: 0.14, type: "sine" });
  },

  //: An offer is a question. Two notes up, and it stops on the second rather
  //: than resolving -- nothing has been agreed yet.
  offer(ctx, out, t) {
    tone(ctx, out, { freq: 523.25, at: t, dur: 0.1, peak: 0.14, type: "triangle" });
    tone(ctx, out, { freq: 783.99, at: t + 0.09, dur: 0.14, peak: 0.14, type: "triangle" });
  },

  //: A settlement is the answer. A fifth arriving together and a third over
  //: it: the one sound on the island that agrees with itself.
  settled(ctx, out, t) {
    tone(ctx, out, { freq: 392.00, at: t, dur: 0.34, peak: 0.16, type: "sine" });
    tone(ctx, out, { freq: 587.33, at: t, dur: 0.36, peak: 0.13, type: "sine" });
    tone(ctx, out, { freq: 987.77, at: t + 0.06, dur: 0.4, peak: 0.09, type: "sine" });
  },

  //: A refusal: one note, low, falling, over before it is interesting. It is
  //: not a buzzer -- a refusal is an ordinary thing to happen and the island
  //: should not scold anybody for it.
  refused(ctx, out, t) {
    tone(ctx, out, { freq: 233.08, to: 174.61, at: t, dur: 0.2, peak: 0.15, type: "triangle" });
  },

  //: The bell, which is the island's clock. Struck partials over a long
  //: decay, and the only voice allowed to be heard over everything else --
  //: the day is ending and that is the loudest fact on the board.
  bell(ctx, out, t) {
    knock(ctx, out, { at: t, dur: 0.05, freq: 2600, peak: 0.16, q: 0.8 });
    for (const [f, p, d] of [[440, 0.2, 1.6], [880, 0.12, 1.2],
                             [1174.66, 0.08, 0.9], [2093, 0.05, 0.6]]) {
      tone(ctx, out, { freq: f, at: t, dur: d, peak: p, type: "sine", attack: 0.004 });
    }
  },

  //: A day opening: the same partials from underneath, quiet and slow, more
  //: light than event.
  open(ctx, out, t) {
    for (const [f, at] of [[261.63, 0], [392.00, 0.08], [523.25, 0.16]]) {
      tone(ctx, out, { freq: f, at: t + at, dur: 0.7, peak: 0.09,
                       type: "sine", attack: 0.12 });
    }
  },
};

export const VOICE_NAMES = Object.keys(VOICES);
