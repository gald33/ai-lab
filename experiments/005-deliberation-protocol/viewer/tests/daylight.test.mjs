// The island's two clocks, and the rule that they are one clock.
//
//     node --test viewer/tests/daylight.test.mjs
//
// The page draws the day twice: `scene.sky()` moves the sun's disc, and
// `Stage.setDay()` moves the light the model is lit by. A viewer sees one of
// them at a time -- `.has-3d .sun` hides the disc as soon as there is a model,
// and the disc is all a fallback island has -- so the two disagreeing is not a
// cosmetic difference. It is the island telling one viewer it is dusk and
// another that it is midday.
//
// Both are handed the same pair: where the day is now, and where it will be
// when the next line lands. Where there is time to animate, both travel. Where
// there is not -- a scrub, or a viewer who asked for less motion -- `sky()`
// puts the disc **at the far end**, and the light used to stay at the near
// one. `alive` in `render.py` caught what that comes to on the pixels; this is
// the same rule with no browser in it.
//
// `Stage` needs a WebGL context and there is none here, so the rule is
// exercised on the method rather than on a built stage. That is the whole of
// what is being asked: given the two ends and a duration, which hour does the
// island light itself by.

import { test } from "node:test";
import assert from "node:assert/strict";

import { Stage } from "../web/stage.js";

/** A stage's daylight state, with nothing rendered under it. */
const clockOf = (still = false) => ({ still, day: null, glide: null, life: null,
                                      // A still frame is drawn as soon as it is
                                      // set, and there is nothing to draw it on.
                                      render() {},
                                      setDay: Stage.prototype.setDay,
                                      dayNow: Stage.prototype.dayNow });

test("with no journey to run, the light lands where the disc lands", () => {
  // What a scrub hands the page: the frame's own hour, the hour the next line
  // lands at, and no time in which to cross between them.
  const s = clockOf();
  s.setDay(0.38, 1, 0);
  assert.equal(s.dayNow(), 1,
               "the disc jumps to the end of the silence; so must the light");

  // And the same for a viewer who asked for less motion, who gets no
  // animation however long the frame is held.
  const quiet = clockOf(true);
  quiet.setDay(0.38, 1, 800);
  assert.equal(quiet.dayNow(), 1);
});

test("with a journey, it starts at this hour and arrives at the next", () => {
  const s = clockOf();
  s.setDay(0.2, 0.6, 1000);
  assert.ok(Math.abs(s.dayNow() - 0.2) < 0.05, "it sets out from where the day is");
  s.glide.t0 -= 1000;   // the frame's whole hold, spent
  assert.equal(s.dayNow(), 0.6);
  assert.equal(s.glide, null, "and the glide is done with");
});

test("the day never travels backwards", () => {
  // A new day is a jump, not a rewind -- the same reason `scene.sky` refuses
  // it. `until` behind `day` is the next line falling in the next episode.
  const s = clockOf();
  s.setDay(0.9, 0.1, 900);
  assert.equal(s.dayNow(), 0.9);
  assert.equal(s.glide, null);
});

test("a board with no clock leaves the light where it is", () => {
  // `null` is "this page cannot read this board's schedule", which is not the
  // same as morning: a live board that drops a poll must not flicker to dawn.
  const s = clockOf();
  s.setDay(0.7, null, 0);
  assert.equal(s.dayNow(), 0.7);
  s.setDay(null, null, 0);
  assert.equal(s.dayNow(), null);
});
