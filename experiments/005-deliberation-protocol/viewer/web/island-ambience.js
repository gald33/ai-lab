/**
 * The island, going on. Sea, wind, gulls, the fire, dolphins passing, and the
 * sites at work -- the sound the place makes whether or not anything is
 * happening on the board.
 *
 * `island-sound.js` was one voice per event and nothing else, and that is a
 * chime on a picture rather than a place: a spectator who leaves the island
 * running between offers should hear the island, not silence with a bell in
 * it. This is the other half, and it is the half you actually listen to. The
 * event voices are still there and are now **accents underneath it**, at less
 * than half the level they had alone.
 *
 * **Still synthesised** (Gal, 2026-08-27, choosing this over recordings). The
 * standing reason is unchanged -- a folder of audio would be the first
 * binaries in the repository, and every one of them a thing to license, ship
 * and keep in step with a deploy. The cost is honest and worth writing down:
 * this is an *impression* of surf and a gull and a dolphin, not a recording of
 * one. Filtered noise with a swell on it reads as sea; a swept sine with
 * vibrato reads as a dolphin whistle, which is the one animal synthesis is
 * actually good at. A chisel is a bandpassed click and a listener who knows
 * quarries will not be fooled.
 *
 * **Nothing here is a loop of a file, so nothing here repeats.** Every gull,
 * every crackle, every chisel strike is scheduled individually a beat before
 * it sounds, off the audio clock rather than the frame clock. That is why the
 * bed can run for an hour without the seam a four-second loop would have.
 *
 * ## What responds to what
 *
 * | heard | driven by |
 * |---|---|
 * | sea, wind | always, swelling on their own slow clocks |
 * | gulls | the hour -- most at dawn and through the day, none at night |
 * | the fire at the centre | always, up at the bell as the light goes |
 * | dolphins | nobody. They pass when they pass |
 * | a site at work | a production receipt for that good, for as long as the work reads |
 *
 * A site's work is the one thing here that is *about* the board, and it is
 * still not a caption: what a production receipt buys is the sound of that
 * trade being done -- an oven and kneading for bread, strikes and a cart at
 * the quarry, nets going in for fish -- swelling as the clip carries the crate
 * home and gone a few seconds later.
 */

//: The bed's own ceiling, under the master. Everything here is background by
//: definition: if a spectator ever notices the sea rather than the island,
//: this is too high.
const BED = 0.5;

//: How long a production receipt keeps its site sounding. Long enough to
//: outlast the clip that carries the crate home (`CARRY` in `scene.js` is
//: under two seconds), short enough that a busy day is not every site at once
//: forever.
const WORK_MS = 6500;

//: How loud a working site stands against the bed, at its peak. Set by
//: measuring rather than by taste -- see the reproduction in the README: at 1
//: the whole of a site's work moved the mix by 7% and salt by nothing at all,
//: which is a site you cannot hear working.
export const WORK_GAIN = 8;

//: The scheduler's horizon and how often it runs. Everything intermittent --
//: gulls, crackle, dolphins -- is placed on the audio clock this far ahead, so
//: a stalled frame or a busy main thread cannot make the sea stutter.
const AHEAD = 0.9, TICK_MS = 400;

/** Sea, wind and fire in the mix at a given hour, and how likely a gull is. */
export function hour(day, closed = false) {
  //: Night is not silence -- the sea does not stop. It is the gulls stopping,
  //: the wind dropping and the fire being the loudest thing left, which is
  //: also what the island *looks* like once the light goes.
  if (closed) return { sea: 1, wind: 0.45, fire: 1.6, gull: 0 };
  const d = Math.min(1, Math.max(0, day));
  //: Dawn is the loudest hour for birds and the quietest for everything else,
  //: and this is the one place the bed says what time it is.
  const dawn = Math.max(0, 1 - Math.abs(d - 0.08) / 0.16);
  const dusk = Math.max(0, 1 - Math.abs(d - 0.92) / 0.16);
  const noon = Math.max(0, 1 - Math.abs(d - 0.5) / 0.6);
  return {
    sea: 0.85 + 0.25 * noon,
    wind: 0.5 + 0.6 * noon,
    fire: 0.5 + 1.1 * dusk,
    gull: 0.25 + 0.9 * dawn + 0.45 * noon + 0.3 * dusk,
  };
}

export class Ambience {
  constructor(ctx, out, { rng = Math.random } = {}) {
    this.ctx = ctx;
    this.out = out;
    this.rng = rng;
    this.running = false;
    this.timer = null;
    this.day = 0.5;
    this.closed = false;
    //: When each intermittent thing is next due, on the audio clock. Held here
    //: rather than in a timeout so a scheduler that ran late places the next
    //: one where it belonged, not where it noticed.
    this.due = { gull: 0, crackle: 0, dolphin: 0 };
    this.work = new Map();
    this.build();
  }

  /** A few seconds of noise, made once and started by everything that hisses. */
  noise(seconds = 3) {
    const ctx = this.ctx;
    const n = Math.max(1, Math.floor(ctx.sampleRate * seconds));
    const buf = ctx.createBuffer(1, n, ctx.sampleRate);
    const d = buf.getChannelData(0);
    //: Two poles of a one-pole lowpass, which is what turns white noise into
    //: something with sea in it rather than something with a radio in it.
    let a = 0, b = 0;
    for (let i = 0; i < n; i++) {
      const w = this.rng() * 2 - 1;
      a = a * 0.86 + w * 0.14;
      b = b * 0.5 + a * 0.5;
      d[i] = b * 3.2;
    }
    return buf;
  }

  /** A noise source, filtered, at a gain this object can reach later. */
  layer(type, freq, q, gain) {
    const ctx = this.ctx;
    const src = ctx.createBufferSource();
    src.buffer = this.bed;
    src.loop = true;
    const f = ctx.createBiquadFilter();
    f.type = type;
    f.frequency.value = freq;
    f.Q.value = q;
    const g = ctx.createGain();
    g.gain.value = gain;
    src.connect(f).connect(g).connect(this.gain);
    return { src, filter: f, gain: g, base: gain };
  }

  /**
   * A slow oscillator on somebody else's parameter -- the swell on the surf,
   * the wind coming and going. This is what a loop of a file cannot do, and
   * the reason two layers of noise do not sound like one.
   */
  drift(param, rate, depth) {
    const ctx = this.ctx;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = "sine";
    o.frequency.value = rate;
    g.gain.value = depth;
    o.connect(g).connect(param);
    o.start();
    return o;
  }

  build() {
    const ctx = this.ctx;
    this.bed = this.noise();
    this.gain = ctx.createGain();
    this.gain.gain.value = 0;
    this.gain.connect(this.out);

    //: The sea, which is two surfs a little out of step: one long and low that
    //: is the water, one brighter and slower that is the break on the shore.
    //: One alone was a hiss with a wobble in it.
    this.sea = this.layer("lowpass", 420, 0.6, 0.16);
    this.surf = this.layer("bandpass", 900, 0.5, 0.05);
    this.wind = this.layer("bandpass", 620, 0.7, 0.05);
    //: The fire at the centre: a rumble under the crackle the scheduler puts
    //: on top of it.
    this.fire = this.layer("lowpass", 190, 0.7, 0.03);

    this.lfo = [
      this.drift(this.sea.gain.gain, 0.083, 0.07),
      this.drift(this.surf.gain.gain, 0.051, 0.035),
      this.drift(this.surf.filter.frequency, 0.037, 260),
      this.drift(this.wind.gain.gain, 0.029, 0.038),
      this.drift(this.wind.filter.frequency, 0.019, 220),
    ];
    for (const l of [this.sea, this.surf, this.wind, this.fire]) l.src.start();
  }

  /** The bed comes up over a few seconds. Nothing on this island starts suddenly. */
  start() {
    if (this.running) return;
    this.running = true;
    const t = this.ctx.currentTime;
    this.gain.gain.cancelScheduledValues(t);
    this.gain.gain.setValueAtTime(this.gain.gain.value, t);
    this.gain.gain.linearRampToValueAtTime(BED, t + 2.5);
    this.due = { gull: t + 2, crackle: t + 1, dolphin: t + 25 };
    this.timer = setInterval(() => this.pump(), TICK_MS);
    //: A browser's `setInterval` returns a number and ignores this. Node's
    //: returns a handle that holds the process open, and a test that builds a
    //: bed against a fake context would hang on it forever rather than
    //: failing -- which is worse than failing.
    this.timer?.unref?.();
    this.pump();
  }

  /** And goes down over one, rather than being cut off mid-wave. */
  stop() {
    if (!this.running) return;
    this.running = false;
    clearInterval(this.timer);
    this.timer = null;
    const t = this.ctx.currentTime;
    this.gain.gain.cancelScheduledValues(t);
    this.gain.gain.setValueAtTime(this.gain.gain.value, t);
    this.gain.gain.linearRampToValueAtTime(0.0001, t + 1);
  }

  /** The hour, from the page's own clock. Mixed, not switched. */
  setDay(day, closed = false) {
    this.day = typeof day === "number" ? day : this.day;
    this.closed = !!closed;
    const m = hour(this.day, this.closed);
    const t = this.ctx.currentTime;
    const to = (l, x) => l.gain.gain.setTargetAtTime(l.base * x, t, 6);
    to(this.sea, m.sea);
    to(this.surf, m.sea);
    to(this.wind, m.wind);
    to(this.fire, m.fire);
  }

  /** Everything intermittent, placed on the audio clock a beat before it sounds. */
  pump() {
    if (!this.running) return;
    const t = this.ctx.currentTime;
    const m = hour(this.day, this.closed);
    const gap = (lo, hi) => lo + this.rng() * (hi - lo);

    for (const k of Object.keys(this.due)) if (this.due[k] < t) this.due[k] = t;

    while (this.due.crackle < t + AHEAD) {
      this.crackle(this.due.crackle, m.fire);
      this.due.crackle += gap(0.08, 0.45) / Math.max(0.2, m.fire);
    }
    while (this.due.gull < t + AHEAD) {
      if (m.gull > 0.05) this.gull(this.due.gull, m.gull);
      this.due.gull += gap(3, 14) / Math.max(0.05, m.gull);
    }
    while (this.due.dolphin < t + AHEAD) {
      this.dolphin(this.due.dolphin);
      this.due.dolphin += gap(40, 110);
    }
  }

  // --- the things that happen now and then --------------------------------

  /** One spit of the fire. */
  crackle(at, loud = 1) {
    const ctx = this.ctx;
    const src = ctx.createBufferSource();
    src.buffer = this.bed;
    //: A different slice of the same noise each time, which is what keeps a
    //: hundred crackles from being one crackle a hundred times.
    const off = this.rng() * (this.bed.duration - 0.1);
    const f = ctx.createBiquadFilter();
    f.type = "bandpass";
    f.frequency.value = 900 + this.rng() * 2600;
    f.Q.value = 3;
    const g = ctx.createGain();
    const peak = 0.05 * loud * (0.3 + this.rng());
    g.gain.setValueAtTime(peak, at);
    g.gain.exponentialRampToValueAtTime(0.0001, at + 0.05);
    src.connect(f).connect(g).connect(this.gain);
    src.start(at, off, 0.06);
    src.stop(at + 0.08);
  }

  /**
   * A gull, which is two or three cries and not one: a single descending
   * squawk is a duck, and the repeat is what makes it a seabird.
   */
  gull(at, loud = 1) {
    const ctx = this.ctx;
    const cries = 2 + Math.floor(this.rng() * 3);
    //: Somewhere out there rather than overhead -- the same bird, quieter or
    //: louder, is the cheapest distance a mono bed can have.
    const far = 0.35 + this.rng() * 0.65;
    for (let i = 0; i < cries; i++) {
      const t0 = at + i * (0.16 + this.rng() * 0.1);
      const top = 1500 + this.rng() * 500;
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      const f = ctx.createBiquadFilter();
      o.type = "sawtooth";
      o.frequency.setValueAtTime(top, t0);
      o.frequency.exponentialRampToValueAtTime(top * 0.55, t0 + 0.13);
      f.type = "bandpass";
      f.frequency.value = 2200;
      f.Q.value = 1.6;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.05 * loud * far, t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.15);
      o.connect(f).connect(g).connect(this.gain);
      o.start(t0);
      o.stop(t0 + 0.18);
    }
  }

  /**
   * Dolphins going past: a few clicks, then two or three whistles that sweep
   * up and back down with a fast vibrato on them.
   *
   * **The one thing here that answers to nothing at all.** Everything else on
   * this island is the board or the clock; the dolphins are the island having
   * something of its own, and a spectator who hears them twice in a round and
   * cannot work out what caused them has understood it correctly.
   */
  dolphin(at) {
    const ctx = this.ctx;
    for (let i = 0; i < 6 + Math.floor(this.rng() * 6); i++) {
      this.crackle(at + i * (0.03 + this.rng() * 0.05), 0.5);
    }
    const whistles = 2 + Math.floor(this.rng() * 2);
    for (let i = 0; i < whistles; i++) {
      const t0 = at + 0.35 + i * (0.3 + this.rng() * 0.25);
      const dur = 0.28 + this.rng() * 0.22;
      const lo = 1100 + this.rng() * 500;
      const hi = lo * (2.2 + this.rng());
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.setValueAtTime(lo, t0);
      o.frequency.exponentialRampToValueAtTime(hi, t0 + dur * 0.55);
      o.frequency.exponentialRampToValueAtTime(lo * 1.3, t0 + dur);
      //: The vibrato is the whole trick. The same sweep without it is a
      //: theremin; with it, it is an animal.
      const vib = ctx.createOscillator();
      const vibg = ctx.createGain();
      vib.frequency.value = 22 + this.rng() * 14;
      vibg.gain.value = 60;
      vib.connect(vibg).connect(o.frequency);
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.045, t0 + 0.04);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      o.connect(g).connect(this.gain);
      vib.start(t0); vib.stop(t0 + dur + 0.02);
      o.start(t0); o.stop(t0 + dur + 0.02);
    }
  }

  // --- the sites at work ---------------------------------------------------

  /**
   * A production receipt: that good's site is working, and can be heard doing
   * it for a few seconds.
   *
   * Re-triggering an already-sounding site does not stack a second copy of it
   * -- it puts the clock back. Three traders all making bread is one busier
   * bakery, not three bakeries.
   */
  working(good) {
    if (!this.running) return false;
    const make = WORK[good] || WORK.works;
    const t = this.ctx.currentTime;
    let w = this.work.get(good);
    if (!w) {
      const g = this.ctx.createGain();
      g.gain.value = 0.0001;
      g.connect(this.gain);
      w = { gain: g, until: 0 };
      this.work.set(good, w);
    }
    w.until = t + WORK_MS / 1000;
    w.gain.gain.cancelScheduledValues(t);
    w.gain.gain.setValueAtTime(Math.max(0.0001, w.gain.gain.value), t);
    w.gain.gain.exponentialRampToValueAtTime(WORK_GAIN, t + 0.7);
    w.gain.gain.setValueAtTime(WORK_GAIN, w.until - 2.2);
    w.gain.gain.exponentialRampToValueAtTime(0.0001, w.until);
    make(this, t, w.until, w.gain);
    return true;
  }

  /** The bell: the fire comes up as the light goes, and is heard doing it. */
  flare() {
    if (!this.running) return;
    const t = this.ctx.currentTime;
    this.fire.gain.gain.cancelScheduledValues(t);
    this.fire.gain.gain.setTargetAtTime(this.fire.base * 3, t, 0.6);
    this.fire.gain.gain.setTargetAtTime(this.fire.base * 1.4, t + 3, 4);
    for (let i = 0; i < 24; i++) this.crackle(t + this.rng() * 2.5, 1.6);
  }

  /** Every node this holds, stopped. The page is going away. */
  dispose() {
    this.stop();
    for (const l of [this.sea, this.surf, this.wind, this.fire]) {
      try { l.src.stop(); } catch { /* already stopped */ }
    }
    for (const o of this.lfo) { try { o.stop(); } catch { /* already stopped */ } }
  }
}

// --- what each site sounds like -------------------------------------------
//
// Each is a scatter of small scheduled sounds between `t` and `until`, hung on
// the site's own gain so the swell and the fade belong to the site rather than
// to every grain in it. They are impressions and are meant to be: what has to
// come across is *which kind of work*, and that is carried by rhythm and
// brightness far more than by timbre. A quarry is sparse, hard and irregular; a
// loom is fast, wooden and even.

/** A struck thing: a click with a body under it. */
function strike(a, at, gain, { freq = 2400, body = 180, peak = 0.09, ring = 0.09 }) {
  const ctx = a.ctx;
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = "square";
  o.frequency.setValueAtTime(freq, at);
  o.frequency.exponentialRampToValueAtTime(freq * 0.4, at + ring);
  g.gain.setValueAtTime(peak, at);
  g.gain.exponentialRampToValueAtTime(0.0001, at + ring);
  o.connect(g).connect(gain);
  o.start(at); o.stop(at + ring + 0.02);

  const b = ctx.createOscillator();
  const bg = ctx.createGain();
  b.type = "sine";
  b.frequency.setValueAtTime(body, at);
  b.frequency.exponentialRampToValueAtTime(body * 0.6, at + 0.12);
  bg.gain.setValueAtTime(peak * 1.1, at);
  bg.gain.exponentialRampToValueAtTime(0.0001, at + 0.12);
  b.connect(bg).connect(gain);
  b.start(at); b.stop(at + 0.14);
}

/** A swept-noise gesture: a swish, a splash, a shovel through brine. */
function wash(a, at, gain, { dur = 0.35, freq = 1200, sweep = 0.4, peak = 0.07, q = 0.9 }) {
  const ctx = a.ctx;
  const src = ctx.createBufferSource();
  src.buffer = a.bed;
  const f = ctx.createBiquadFilter();
  f.type = "bandpass";
  f.frequency.setValueAtTime(freq, at);
  f.frequency.exponentialRampToValueAtTime(Math.max(80, freq * sweep), at + dur);
  f.Q.value = q;
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(peak, at + dur * 0.25);
  g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  src.connect(f).connect(g).connect(gain);
  src.start(at, a.rng() * (a.bed.duration - dur - 0.05), dur + 0.05);
  src.stop(at + dur + 0.06);
}

/** A steady rumble for as long as the site works: an oven, a cart, the tide. */
function under(a, at, until, gain, { freq = 260, peak = 0.05, q = 0.6 }) {
  const ctx = a.ctx;
  const src = ctx.createBufferSource();
  src.buffer = a.bed;
  src.loop = true;
  const f = ctx.createBiquadFilter();
  f.type = "lowpass";
  f.frequency.value = freq;
  f.Q.value = q;
  const g = ctx.createGain();
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(peak, at + 0.5);
  g.gain.setValueAtTime(peak, Math.max(at + 0.6, until - 1.5));
  g.gain.exponentialRampToValueAtTime(0.0001, until);
  src.connect(f).connect(g).connect(gain);
  src.start(at);
  src.stop(until + 0.05);
}

/** Scatter `n` gestures across the working window, unevenly. */
function scatter(a, at, until, n, each) {
  const span = Math.max(0.2, until - at - 0.4);
  for (let i = 0; i < n; i++) {
    each(at + 0.05 + span * ((i + a.rng()) / n), i);
  }
}

export const WORK = {
  //: The ovens, and somebody knocking dough down on a board in front of them.
  //: The roar is the loudest continuous thing any site has, because an oven is.
  bread(a, t, until, gain) {
    under(a, t, until, gain, { freq: 320, peak: 0.06 });
    scatter(a, t, until, 7, (at) =>
      strike(a, at, gain, { freq: 320, body: 110, peak: 0.05, ring: 0.06 }));
    scatter(a, t, until, 14, (at) => a.crackle(at, 1.1));
  },

  //: The looms: fast, wooden, and nearly even -- the one site with a rhythm,
  //: which is what tells it apart from the quarry at a glance.
  cloth(a, t, until, gain) {
    let at = t + 0.1;
    while (at < until - 0.3) {
      strike(a, at, gain, { freq: 1500, body: 240, peak: 0.085, ring: 0.05 });
      at += 0.22 + a.rng() * 0.06;
    }
    scatter(a, t, until, 7, (x) =>
      wash(a, x, gain, { dur: 0.2, freq: 2600, sweep: 0.6, peak: 0.06 }));
  },

  //: The quarry: hard strikes, sparse and irregular, over the cart's rumble.
  iron(a, t, until, gain) {
    under(a, t, until, gain, { freq: 150, peak: 0.05 });
    scatter(a, t, until, 12, (at) =>
      strike(a, at, gain, { freq: 3000, body: 190, peak: 0.075, ring: 0.11 }));
  },

  //: The pans: brine moving in a shallow tray, and a rake dragged through it.
  //: Nothing is struck here, which is why salt is the quietest site.
  salt(a, t, until, gain) {
    scatter(a, t, until, 12, (at) =>
      wash(a, at, gain, { dur: 0.7, freq: 1700, sweep: 0.35, peak: 0.16, q: 0.7 }));
    scatter(a, t, until, 6, (at) =>
      wash(a, at, gain, { dur: 1.1, freq: 800, sweep: 0.5, peak: 0.11, q: 0.4 }));
  },

  //: Nets going in and coming back out, and the water round them.
  fish(a, t, until, gain) {
    under(a, t, until, gain, { freq: 420, peak: 0.035 });
    scatter(a, t, until, 5, (at) => {
      wash(a, at, gain, { dur: 0.45, freq: 2200, sweep: 0.2, peak: 0.075 });
      wash(a, at + 0.1, gain, { dur: 0.8, freq: 700, sweep: 0.4, peak: 0.04, q: 0.5 });
    });
  },

  //: Scythes through standing grain: a long swish and the fall after it.
  grain(a, t, until, gain) {
    let at = t + 0.15;
    while (at < until - 0.5) {
      wash(a, at, gain, { dur: 0.5, freq: 1500, sweep: 0.3, peak: 0.19, q: 0.8 });
      at += 0.38 + a.rng() * 0.2;
    }
  },

  //: The axe: deeper than the quarry's chisel and slower, with the tree in it.
  timber(a, t, until, gain) {
    scatter(a, t, until, 11, (at) =>
      strike(a, at, gain, { freq: 900, body: 90, peak: 0.085, ring: 0.16 }));
    scatter(a, t, until, 4, (at) =>
      wash(a, at, gain, { dur: 0.9, freq: 600, sweep: 0.25, peak: 0.07, q: 0.5 }));
  },

  //: A good this island has no site for still gets worked at. `island3d.js`
  //: draws a generic works for one; this is what a generic works sounds like.
  works(a, t, until, gain) {
    under(a, t, until, gain, { freq: 260, peak: 0.035 });
    scatter(a, t, until, 9, (at) =>
      strike(a, at, gain, { freq: 1800, body: 200, peak: 0.075, ring: 0.08 }));
  },
};

export const WORK_NAMES = Object.keys(WORK);
