// The bed, against a fake AudioContext.
//
//     node --test viewer/tests/ambience.test.mjs
//
// What can be wrong here without anything throwing: a bed that runs while the
// page is hidden, gulls at midnight, a good with no site sound at all, and the
// scheduler placing nothing (silence) or everything (a wall). None of that
// needs a browser -- what is asserted is which nodes were started and what the
// mix says at a given hour.

import { test } from "node:test";
import assert from "node:assert/strict";

import { Ambience, WORK, WORK_NAMES, hour } from "../web/island-ambience.js";
import { GLYPH } from "../web/scene.js";

class FakeParam {
  constructor(v = 0) { this.value = v; this.calls = 0; }
  setValueAtTime(v) { this.value = v; this.calls++; return this; }
  exponentialRampToValueAtTime(v) { this.value = v; this.calls++; return this; }
  linearRampToValueAtTime(v) { this.value = v; this.calls++; return this; }
  setTargetAtTime(v) { this.value = v; this.calls++; return this; }
  cancelScheduledValues() { return this; }
}
const node = (extra = {}) => Object.assign({
  connect(next) { return next; }, start() {}, stop() {},
}, extra);

class FakeCtx {
  constructor() {
    this.currentTime = 0;
    this.sampleRate = 8000;          // small: the noise buffer is filled for real
    this.destination = node();
    this.started = { osc: 0, buf: 0 };
    this.oscs = [];
  }
  createGain() { return node({ gain: new FakeParam(1) }); }
  createOscillator() {
    const self = this;
    const o = node({ type: "sine", frequency: new FakeParam(440),
                     start() { self.started.osc++; } });
    this.oscs.push(o);
    return o;
  }
  createBufferSource() {
    const self = this;
    return node({ buffer: null, loop: false, start() { self.started.buf++; } });
  }
  createBuffer(_ch, n, rate) {
    const d = new Float32Array(n);
    return { getChannelData: () => d, duration: n / rate, length: n };
  }
  createBiquadFilter() {
    return node({ type: "", frequency: new FakeParam(1), Q: new FakeParam(1) });
  }
}

// A fixed sequence in place of Math.random, so "what did the scheduler place"
// is a question with one answer.
const fixedRng = () => { let i = 0; return () => ((i = (i * 7 + 3) % 97), i / 97); };

const bed = () => {
  const ctx = new FakeCtx();
  return { ctx, a: new Ambience(ctx, ctx.destination, { rng: fixedRng() }) };
};

test("the hour is mixed, not switched", () => {
  const dawn = hour(0.08), noon = hour(0.5), night = hour(0.5, true);
  assert.ok(dawn.gull > noon.gull, "most gulls at dawn");
  assert.equal(night.gull, 0, "and none once the light has gone");
  assert.ok(night.sea > 0, "the sea does not stop at night");
  assert.ok(night.fire > noon.fire, "the fire is what is left");
  assert.ok(noon.wind > night.wind, "and the wind drops with the light");
  for (const d of [0, 0.25, 0.5, 0.75, 1]) {
    for (const [k, v] of Object.entries(hour(d))) {
      assert.ok(v >= 0 && v < 3, `${k} at day ${d} is a sane multiplier (${v})`);
    }
  }
});

test("nothing sounds until the bed is started, and stopping stops it", () => {
  const { ctx, a } = bed();
  assert.equal(a.running, false);
  assert.equal(a.gain.gain.value, 0, "silent at rest");
  assert.ok(ctx.started.buf >= 4, "the standing layers exist, at zero gain");
  assert.equal(a.working("bread"), false, "and a receipt does not wake it");
  a.start();
  assert.equal(a.running, true);
  //: The first crackle is a second out and the first gull two, so the pump
  //: inside `start()` correctly places nothing: the bed comes up over two and
  //: a half seconds and the intermittent things arrive into it.
  const built = ctx.started.buf;
  ctx.currentTime = 3;
  a.pump();
  assert.ok(ctx.started.buf > built, "the scheduler placed something once it was due");
  a.stop();
  const quiet = ctx.started.buf;
  a.pump();
  assert.equal(ctx.started.buf, quiet, "a stopped bed schedules nothing further");
  a.dispose();
});

test("every good the island can draw has a site sound", () => {
  for (const good of Object.keys(GLYPH)) {
    assert.ok(WORK[good], `${good} has one`);
  }
  assert.ok(WORK.works, "and a good with no site of its own still has one");
  assert.deepEqual(WORK_NAMES.slice(-1), ["works"], "the fallback is last");
});

test("a production is heard at its own site, and re-triggering does not stack", () => {
  const { ctx, a } = bed();
  a.start();
  for (const good of WORK_NAMES) {
    const before = ctx.started.osc + ctx.started.buf;
    assert.equal(a.working(good), true, `${good} sounds`);
    assert.ok(ctx.started.osc + ctx.started.buf > before, `${good} placed something`);
  }
  assert.equal(a.work.size, WORK_NAMES.length, "one bus per good");
  a.working("bread");
  assert.equal(a.work.size, WORK_NAMES.length,
               "a second receipt for bread is the same bakery, busier");
  a.dispose();
});

test("night is a fireplace, not a beach with a fire on it", () => {
  const day = hour(0.5), night = hour(0.5, true);
  assert.ok(night.fire > night.sea * 3,
            "the fire is what the island is once the light has gone");
  assert.ok(night.fire > day.fire * 4, "and far more of it than by day");
  assert.ok(night.sea < day.sea && night.wind < day.wind,
            "the sea and the wind pull back for it");
});

test("the sun comes up over seconds, and takes the fire down with it", () => {
  const { ctx, a } = bed();
  a.start();
  const before = ctx.started.osc;
  a.sunrise();
  //: A chord, its drifting partials and a chorus of gulls -- a chime would be
  //: three oscillators and this must not be a chime.
  assert.ok(ctx.started.osc - before > 12,
            `a sunrise is a swell, not a chime (${ctx.started.osc - before})`);
  assert.equal(a.running, true);
  a.stop();
  const quiet = ctx.started.osc;
  a.sunrise();
  assert.equal(ctx.started.osc, quiet, "and none of it while the bed is off");
  a.dispose();
});

test("the shine is bells and sparkle, and only sines", () => {
  const { ctx, a } = bed();
  a.start();
  const before = ctx.started.osc, mark = ctx.oscs.length;
  a.shine(0, 4);
  const made = ctx.started.osc - before;
  //: Four notes of the chord and eighteen sparkles, each a detuned pair plus
  //: an inharmonic partial, over one riser. Counted rather than eyeballed
  //: because "it is a cluster" is the whole difference from a chime.
  assert.ok(made > 50, `a shine is a cluster, not a note (${made})`);
  //: And every one of them a sine. The square wave is what made the quarry
  //: unbearable, and the brightest thing on the island is the last place it
  //: should come back: bright is not the same as sharp.
  const sharp = ctx.oscs.slice(mark).filter((o) => o.type !== "sine");
  assert.equal(sharp.length, 0,
               `the shine has ${sharp.length} non-sine partial(s) in it`);
  a.dispose();
});

test("no gulls at night, and the fire is still there", () => {
  const { ctx, a } = bed();
  a.start();
  a.setDay(0.5, true);
  a.due = { gull: 0, crackle: 0, dolphin: 1e9 };
  const before = ctx.started.osc;
  a.pump();
  assert.equal(ctx.started.osc, before, "a gull is oscillators; none were started");
  assert.ok(ctx.started.buf > 0, "the fire is noise, and it crackled");
  a.dispose();
});

test("the scheduler places a bounded amount of work per pump", () => {
  const { ctx, a } = bed();
  a.start();
  const before = ctx.started.buf + ctx.started.osc;
  for (let i = 0; i < 5; i++) a.pump();
  const placed = ctx.started.buf + ctx.started.osc - before;
  assert.ok(placed < 400, `a pump does not schedule a wall of sound (${placed})`);
  a.dispose();
});
