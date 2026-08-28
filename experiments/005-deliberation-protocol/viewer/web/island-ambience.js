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

//: The bed's own ceiling, under the master.
//:
//: **0.5 was a background nobody could hear.** Reported by ear, 2026-08-28 --
//: the day, the night and the sunrise are all barely there -- and the numbers
//: said the same thing at once: the whole world peaked at 0.051 after the
//: master gain while a single settlement chimed at 0.107 and the bell at
//: 0.125. The island was half the height of one accent.
//:
//: The fix is one number because of how this file is wired: the sites at work
//: and the sunrise both hang off `this.gain`, so raising the bed lifts the
//: whole world together and changes only its balance against the accents --
//: which is exactly what was wrong. Every ratio the checks hold (a site over
//: the bed, the sunrise over the bed it rises into) is untouched by it.
//:
//: The original note here still stands as the other wall: if a spectator ever
//: notices the sea rather than the island, this is too high.
const BED = 1.15;

//: How long a production receipt keeps its site sounding. Long enough to
//: outlast the clip that carries the crate home (`CARRY` in `scene.js` is
//: under two seconds), short enough that a busy day is not every site at once
//: forever.
const WORK_MS = 5000;

//: How loud a working site stands against the bed, at its peak.
//:
//: **Measurement set this to 8 and the ear sent it back.** At 1 a whole site
//: at work moved the mix by 7% and salt by nothing, which is inaudible; 8
//: cleared that by a mile and was reported as annoying, because loudness is
//: not the same question as harshness and RMS only answers the first. It sits
//: between the two now, with the sites rewritten to be worth hearing rather
//: than merely audible. The floor in `tests/audio.py` came down with it: a
//: check that forbids the quiet mistake must not mandate the loud one.
export const WORK_GAIN = 9;

//: The scheduler's horizon and how often it runs. Everything intermittent --
//: gulls, crackle, dolphins -- is placed on the audio clock this far ahead, so
//: a stalled frame or a busy main thread cannot make the sea stutter.
const AHEAD = 0.9, TICK_MS = 400;

/** Sea, wind and fire in the mix at a given hour, and how likely a gull is. */
export function hour(day, closed = false) {
  //: **Night is the fire, and the fire is the whole of it.** It used to be the
  //: sea with the fire a little up behind it, which is a beach at night and
  //: not this island: once the light has gone, every trader is round the one
  //: fire at the centre and that is what a spectator should be sitting at.
  //: Asked for by Gal, 2026-08-28 -- "night background sound should be
  //: fireplace" -- and the number that makes it one is this: the fire is
  //: twice the sea rather than half of it, and the crackle rate below is
  //: divided by it, so a louder fire is also a busier one.
  if (closed) return { sea: 0.62, wind: 0.22, fire: 4.2, gull: 0 };
  const d = Math.min(1, Math.max(0, day));
  //: Dawn is the loudest hour for birds and the quietest for everything else,
  //: and this is the one place the bed says what time it is.
  const dawn = Math.max(0, 1 - Math.abs(d - 0.08) / 0.16);
  const dusk = Math.max(0, 1 - Math.abs(d - 0.92) / 0.16);
  const noon = Math.max(0, 1 - Math.abs(d - 0.5) / 0.6);
  return {
    sea: 0.85 + 0.25 * noon,
    wind: 0.5 + 0.6 * noon,
    fire: 0.27 + 0.6 * dusk,
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
    //: The fire's own bed. Wider than it was (190Hz) because a hearth you are
    //: sitting at has the air moving in it, not just the low roll a distant
    //: fire has -- at night this is the loudest thing on the island and a
    //: lowpassed rumble alone reads as traffic.
    this.fire = this.layer("lowpass", 340, 0.6, 0.055);

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
      //: One spit in twelve is a proper pop -- a log settling rather than the
      //: surface ticking. A fire without them is a hiss, which is the thing
      //: that stops a bed from being a hearth.
      const pop = this.rng() < 0.08;
      this.crackle(this.due.crackle, m.fire * (pop ? 2.6 : 1), pop);
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

  /** One spit of the fire; a `pop` is a log settling, lower and longer. */
  crackle(at, loud = 1, pop = false) {
    const ctx = this.ctx;
    const src = ctx.createBufferSource();
    src.buffer = this.bed;
    //: A different slice of the same noise each time, which is what keeps a
    //: hundred crackles from being one crackle a hundred times.
    const off = this.rng() * (this.bed.duration - 0.1);
    const f = ctx.createBiquadFilter();
    f.type = "bandpass";
    f.frequency.value = pop ? 260 + this.rng() * 500 : 900 + this.rng() * 2600;
    f.Q.value = pop ? 1.6 : 3;
    const dur = pop ? 0.16 : 0.05;
    const g = ctx.createGain();
    const peak = 0.05 * loud * (0.3 + this.rng());
    g.gain.setValueAtTime(peak, at);
    g.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    src.connect(f).connect(g).connect(this.gain);
    src.start(at, off, dur + 0.03);
    src.stop(at + dur + 0.04);
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

  /**
   * The day opening: **the sun coming up, heard.**
   *
   * Asked for by Gal, 2026-08-28 -- the episode's open should be a rising sun
   * rather than the three-note chime it was. A chime is an announcement; a
   * sunrise is a thing that takes its time, and the difference is entirely in
   * the shape of it.
   *
   * So this is one gesture over six seconds, and everything in it goes the
   * same way at once: a warm low chord swells from nothing, a lowpass opens
   * over it so the sound *brightens* as it grows (which is what reads as
   * light rather than as volume), the octave above arrives late and quiet as
   * the top of it, and the birds start -- the dawn chorus is the loudest hour
   * for gulls and this is that hour arriving.
   *
   * The fire goes the other way, because a fire at sunrise is a fire being
   * left.
   */
  sunrise() {
    if (!this.running) return;
    const ctx = this.ctx;
    const t = ctx.currentTime;
    const DUR = 6;

    //: The chord, on a filter that opens. Fifths and an octave: nothing that
    //: resolves anywhere, because a sunrise is not a cadence.
    const swell = ctx.createGain();
    const open = ctx.createBiquadFilter();
    open.type = "lowpass";
    open.frequency.setValueAtTime(180, t);
    open.frequency.exponentialRampToValueAtTime(2400, t + DUR * 0.8);
    open.Q.value = 0.5;
    swell.gain.setValueAtTime(0.0001, t);
    swell.gain.exponentialRampToValueAtTime(0.42, t + DUR * 0.62);
    swell.gain.exponentialRampToValueAtTime(0.0001, t + DUR);
    swell.connect(open).connect(this.gain);
    for (const [f, at, level] of [[130.81, 0, 1], [196.00, 0.5, 0.8],
                                  [261.63, 1.4, 0.7], [392.00, 2.6, 0.45],
                                  [523.25, 3.8, 0.3]]) {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      //: A few cents of drift on each so the chord breathes instead of
      //: standing still. Static sines are an organ, and this is weather.
      o.frequency.setValueAtTime(f * (0.999 + this.rng() * 0.002), t);
      g.gain.setValueAtTime(0.0001, t + at);
      g.gain.exponentialRampToValueAtTime(level, t + at + 1.6);
      g.gain.exponentialRampToValueAtTime(0.0001, t + DUR);
      o.connect(g).connect(swell);
      o.start(t + at); o.stop(t + DUR + 0.05);
    }

    //: And the light on the water: the surf brightens with it and settles
    //: back, which is the bed itself taking part rather than a sound laid
    //: over the top of one.
    this.surf.filter.frequency.cancelScheduledValues(t);
    this.surf.filter.frequency.setTargetAtTime(1800, t + 1, 2);
    this.surf.filter.frequency.setTargetAtTime(900, t + DUR, 4);

    //: The light itself, **after** the warmth rather than with it. Started
    //: at 0.6s it put its riser and first sparkles inside the sunrise's own
    //: first seconds, and the check caught what that costs: the gesture grew
    //: without brightening, because there was nothing left for the second
    //: half to be brighter *than*. The sun is felt before it is seen.
    this.shine(t + 1.5, DUR * 0.73);

    //: The chorus. Not scheduled through `due` -- these are extra birds, on
    //: top of whatever the hour was already going to give.
    for (let i = 0; i < 7; i++) this.gull(t + 1.5 + this.rng() * 5, 0.5 + this.rng() * 0.7);

    //: A fire at sunrise is a fire being left.
    this.fire.gain.gain.cancelScheduledValues(t);
    this.fire.gain.gain.setTargetAtTime(this.fire.base * 0.5, t, 3);
  }

  /**
   * The light itself: a bell-and-sparkle shimmer over the top of the swell.
   *
   * Asked for by Gal, 2026-08-28, pointing at a four-second game accent
   * (Envato `shining`, tagged *bless, enlightenment, illumination, magic,
   * shine*) and saying: synthesise something like this. **Like it, and not
   * it** -- what is taken is the idiom, which is not anybody's property: a
   * cluster of bell partials with long tails, detuned in pairs so they beat
   * against each other, sparkles scattered above them, and a riser climbing
   * underneath into the moment they arrive. No part of that recording is
   * here, and nothing is fetched at runtime.
   *
   * Two things keep it from becoming the harsh mistake this file has already
   * made once. Every partial is a **sine** -- the square wave is what made
   * the quarry unbearable, and a bright sound is not the same thing as a
   * sharp one -- and every envelope has a few milliseconds of attack, so a
   * sparkle is struck rather than switched on.
   */
  shine(t, dur = 4.2) {
    const ctx = this.ctx;
    const shimmer = ctx.createGain();
    shimmer.gain.value = 1;
    shimmer.connect(this.gain);

    //: C major with the second and sixth in it -- bright, and it resolves
    //: nowhere, which is what lets it sit over a bed that is not in any key.
    const NOTES = [523.25, 587.33, 659.25, 783.99, 880, 987.77,
                   1046.5, 1174.66, 1318.51, 1567.98, 2093];

    /** One struck partial with a long tail, as a pair a few cents apart. */
    const bell = (freq, at, peak, ring) => {
      for (const detune of [0.9985, 1.0015]) {
        const o = ctx.createOscillator();
        const g = ctx.createGain();
        o.type = "sine";
        o.frequency.value = freq * detune;
        g.gain.setValueAtTime(0.0001, at);
        g.gain.exponentialRampToValueAtTime(peak / 2, at + 0.006);
        g.gain.exponentialRampToValueAtTime(0.0001, at + ring);
        o.connect(g).connect(shimmer);
        o.start(at); o.stop(at + ring + 0.05);
      }
      //: A quiet inharmonic partial above each, which is the difference
      //: between a bell and a flute. 2.76 is roughly where a struck bar puts
      //: its first overtone, and it is far enough off the octave to ring
      //: rather than to double the note.
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = freq * 2.76;
      g.gain.setValueAtTime(0.0001, at);
      g.gain.exponentialRampToValueAtTime(peak * 0.18, at + 0.004);
      g.gain.exponentialRampToValueAtTime(0.0001, at + ring * 0.55);
      o.connect(g).connect(shimmer);
      o.start(at); o.stop(at + ring * 0.6 + 0.05);
    };

    //: The riser: a sine climbing two and a half octaves into the moment the
    //: bells land, with air behind it. It is what makes the arrival *arrive*
    //: -- the bells alone are a chime, and a chime is what this replaced.
    const r = ctx.createOscillator();
    const rg = ctx.createGain();
    const rf = ctx.createBiquadFilter();
    r.type = "sine";
    r.frequency.setValueAtTime(330, t);
    r.frequency.exponentialRampToValueAtTime(1900, t + dur * 0.42);
    rf.type = "lowpass";
    rf.frequency.setValueAtTime(700, t);
    rf.frequency.exponentialRampToValueAtTime(4200, t + dur * 0.42);
    rg.gain.setValueAtTime(0.0001, t);
    rg.gain.exponentialRampToValueAtTime(0.1, t + dur * 0.34);
    rg.gain.exponentialRampToValueAtTime(0.0001, t + dur * 0.52);
    r.connect(rf).connect(rg).connect(shimmer);
    r.start(t); r.stop(t + dur * 0.55);

    //: The arrival: four notes of the chord together, low to high, each
    //: ringing longer than the one before it.
    const land = t + dur * 0.4;
    [0, 3, 5, 7].forEach((i, k) => {
      bell(NOTES[i], land + k * 0.05, 0.15 - k * 0.016, 2.4 + k * 0.5);
    });

    //: And the sparkle over it: grains climbing on average as the light
    //: comes up, thickest just after the arrival and thinning into the tail.
    //: The climb is the point -- a sparkle that does not go anywhere is a
    //: wind chime.
    const grains = 18;
    for (let i = 0; i < grains; i++) {
      const p = i / grains;
      const at = t + dur * 0.18 + p * dur * 0.72 + this.rng() * 0.12;
      //: Weighted to the top of the set as it goes on, rather than jumping
      //: there: the low notes thin out, the high ones do not start at once.
      const lo = Math.floor(p * (NOTES.length - 5));
      const note = NOTES[lo + Math.floor(this.rng() * 5)];
      bell(note, at, 0.04 + this.rng() * 0.045, 0.5 + this.rng() * 1.1);
    }
    return shimmer;
  }

  /** The bell: the fire comes up as the light goes, and is heard doing it. */
  flare() {
    if (!this.running) return;
    const t = this.ctx.currentTime;
    this.fire.gain.gain.cancelScheduledValues(t);
    this.fire.gain.gain.setTargetAtTime(this.fire.base * 4, t, 0.6);
    //: **Handed over to the hearth rather than settling back to daytime.**
    //: The bell is where the night's fire begins, and `setDay(_, closed)`
    //: arrives a beat later with the same value -- so the flare and the night
    //: are one continuous fire instead of a swell that dies and a second one
    //: that starts.
    this.fire.gain.gain.setTargetAtTime(this.fire.base * 4.2, t + 3, 4);
    for (let i = 0; i < 24; i++) this.crackle(t + this.rng() * 2.5, 1.6, this.rng() < 0.25);
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

/**
 * A struck thing: a short transient with a body ringing under it.
 *
 * **This was a square wave with no attack, and it was the worst thing on the
 * island.** Reported as the production sound being annoying, and it was: a
 * square at 2.4-3kHz carries odd harmonics the whole way up, an instant
 * `setValueAtTime` on the gain is a click rather than a strike, and twelve of
 * them at one pitch and one level is a machine stamping. The RMS check could
 * not see any of it -- harsh transient content is exactly what RMS rewards,
 * which is why a level set by measurement alone came out unlistenable.
 *
 * What replaces it is how a struck thing actually sounds: a filtered noise
 * transient for the contact, a damped body under it, a few milliseconds of
 * attack on both so neither starts as a discontinuity, and **every hit a
 * little different in pitch and weight**, because two hammer blows never are.
 */
function strike(a, at, gain, { freq = 2400, body = 180, peak = 0.09, ring = 0.09 }) {
  const ctx = a.ctx;
  //: No two hits alike. Without this the site is one sample retriggered, and
  //: a listener hears the retrigger rather than the work.
  const vary = 0.85 + a.rng() * 0.3;
  const loud = peak * (0.7 + a.rng() * 0.6);

  //: The contact: noise, not an oscillator. A pitched click is a beep; the
  //: moment a tool meets stone is broadband and over in 20ms.
  const src = ctx.createBufferSource();
  src.buffer = a.bed;
  const nf = ctx.createBiquadFilter();
  nf.type = "bandpass";
  nf.frequency.value = freq * vary;
  nf.Q.value = 1.4;
  const ng = ctx.createGain();
  ng.gain.setValueAtTime(0.0001, at);
  ng.gain.exponentialRampToValueAtTime(loud * 0.9, at + 0.003);
  ng.gain.exponentialRampToValueAtTime(0.0001, at + 0.03 + ring * 0.2);
  src.connect(nf).connect(ng).connect(gain);
  src.start(at, a.rng() * (a.bed.duration - 0.2), 0.12);
  src.stop(at + 0.14);

  //: The body, which is what says whether the thing struck was stone, wood or
  //: a loom. A triangle under a lowpass rather than a square: the harmonics
  //: above the fourth were never carrying anything except the irritation.
  const b = ctx.createOscillator();
  const bf = ctx.createBiquadFilter();
  const bg = ctx.createGain();
  b.type = "triangle";
  b.frequency.setValueAtTime(body * vary, at);
  b.frequency.exponentialRampToValueAtTime(body * vary * 0.55, at + ring + 0.05);
  bf.type = "lowpass";
  bf.frequency.value = body * 6;
  bg.gain.setValueAtTime(0.0001, at);
  bg.gain.exponentialRampToValueAtTime(loud, at + 0.006);
  bg.gain.exponentialRampToValueAtTime(0.0001, at + ring + 0.06);
  b.connect(bf).connect(bg).connect(gain);
  b.start(at); b.stop(at + ring + 0.08);
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
    scatter(a, t, until, 5, (at) =>
      strike(a, at, gain, { freq: 320, body: 110, peak: 0.06, ring: 0.07 }));
    scatter(a, t, until, 14, (at) => a.crackle(at, 1.1));
  },

  //: The looms: fast, wooden, and nearly even -- the one site with a rhythm,
  //: which is what tells it apart from the quarry at a glance.
  cloth(a, t, until, gain) {
    let at = t + 0.1;
    while (at < until - 0.3) {
      strike(a, at, gain, { freq: 1400, body: 240, peak: 0.15, ring: 0.08 });
      at += 0.23 + a.rng() * 0.08;
    }
    scatter(a, t, until, 7, (x) =>
      wash(a, x, gain, { dur: 0.2, freq: 2600, sweep: 0.6, peak: 0.06 }));
  },

  //: The quarry: hard strikes, sparse and irregular, over the cart's rumble.
  iron(a, t, until, gain) {
    //: The cart is what carries this site between strikes, and the strikes
    //: are sparse on purpose -- a quarry is not a drum. Both were raised
    //: after the check caught iron dipping under the floor on one run in six:
    //: a margin that thin is a check that reports the scheduler's dice.
    under(a, t, until, gain, { freq: 150, peak: 0.075 });
    scatter(a, t, until, 10, (at) =>
      strike(a, at, gain, { freq: 2600, body: 190, peak: 0.115, ring: 0.13 }));
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
      wash(a, at, gain, { dur: 0.5, freq: 1500, sweep: 0.3, peak: 0.26, q: 0.8 });
      at += 0.34 + a.rng() * 0.16;
    }
  },

  //: The axe: deeper than the quarry's chisel and slower, with the tree in it.
  timber(a, t, until, gain) {
    scatter(a, t, until, 10, (at) =>
      strike(a, at, gain, { freq: 850, body: 90, peak: 0.14, ring: 0.22 }));
    scatter(a, t, until, 4, (at) =>
      wash(a, at, gain, { dur: 0.9, freq: 600, sweep: 0.25, peak: 0.085, q: 0.5 }));
  },

  //: A good this island has no site for still gets worked at. `island3d.js`
  //: draws a generic works for one; this is what a generic works sounds like.
  works(a, t, until, gain) {
    under(a, t, until, gain, { freq: 260, peak: 0.05 });
    scatter(a, t, until, 9, (at) =>
      strike(a, at, gain, { freq: 1700, body: 200, peak: 0.12, ring: 0.11 }));
  },
};

export const WORK_NAMES = Object.keys(WORK);
