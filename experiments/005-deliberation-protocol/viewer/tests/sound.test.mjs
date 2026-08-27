// The island's voices, against a fake AudioContext.
//
//     node --test viewer/tests/sound.test.mjs
//
// What can be wrong here without anything throwing: sound that starts itself,
// an event kind with no voice, and a scrub at 16x ringing the bell forty times
// in a second. None of that needs a browser -- WebAudio is a graph you build,
// and a stub that records what was built is enough to check what was asked
// for. Whether it *sounds* right is not a thing a test can say.

import { test } from "node:test";
import assert from "node:assert/strict";

import { Sound, VOICE_NAMES } from "../web/island-sound.js";

class FakeParam {
  constructor(v = 0) { this.value = v; }
  setValueAtTime() { return this; }
  exponentialRampToValueAtTime() { return this; }
}
const node = (extra = {}) => Object.assign({
  connect(next) { return next; },
  start() {}, stop() {},
}, extra);

class FakeCtx {
  constructor() {
    this.state = "running";
    this.currentTime = 0;
    this.sampleRate = 48000;
    this.started = 0;
    this.destination = node();
  }
  createGain() { return node({ gain: new FakeParam(1) }); }
  createOscillator() {
    const self = this;
    return node({ type: "sine", frequency: new FakeParam(440),
                  start() { self.started++; } });
  }
  createBufferSource() {
    const self = this;
    return node({ buffer: null, start() { self.started++; } });
  }
  createBuffer(_ch, n) { const d = new Float32Array(n); return { getChannelData: () => d }; }
  createBiquadFilter() { return node({ type: "", frequency: new FakeParam(1), Q: new FakeParam(1) }); }
  createDynamicsCompressor() {
    return node({ threshold: new FakeParam(0), ratio: new FakeParam(1),
                  knee: new FakeParam(0), attack: new FakeParam(0),
                  release: new FakeParam(0) });
  }
  resume() { this.state = "running"; }
}

function armed() {
  globalThis.AudioContext = FakeCtx;
  const s = new Sound();
  assert.equal(s.set(true), true, "the fake context is accepted");
  return s;
}

test("silent until asked", () => {
  globalThis.AudioContext = FakeCtx;
  const s = new Sound();
  assert.equal(s.enabled, false, "off is the default");
  assert.equal(s.play({ kind: "bell" }), false, "and nothing sounds while it is off");
  assert.equal(s.ctx, null, "no context is built before the gesture that asks for one");
});

test("a browser with no audio leaves the button off", () => {
  delete globalThis.AudioContext;
  delete globalThis.webkitAudioContext;
  const s = new Sound();
  assert.equal(s.set(true), false, "asking does not make it so");
  assert.equal(s.enabled, false);
});

test("every event the island animates has a voice, and nothing else does", () => {
  assert.deepEqual(new Set(VOICE_NAMES),
                   new Set(["produced", "offer", "settled", "refused", "bell", "open"]));
  const s = armed();
  for (const kind of VOICE_NAMES) {
    s.last.clear(); s.recent = [];
    assert.equal(s.play({ kind }), true, `${kind} sounds`);
  }
  s.last.clear(); s.recent = [];
  assert.equal(s.play({ kind: "note" }), false, "a message with no clip makes no noise");
  assert.equal(s.play(null), false, "and neither does nothing at all");
});

test("a voice will not sound twice in the same instant", () => {
  const s = armed();
  assert.equal(s.play({ kind: "settled" }), true);
  assert.equal(s.play({ kind: "settled" }), false, "the floor holds it back");
});

test("a scrub at speed does not empty the whole board at once", () => {
  const s = armed();
  const kinds = ["produced", "offer", "settled", "refused", "bell", "open"];
  const rang = kinds.concat(kinds).filter((k) => s.play({ kind: k })).length;
  assert.ok(rang <= 6, `at most the budget sounds at once, got ${rang}`);
  assert.ok(rang > 0, "and it is not simply mute");
});
