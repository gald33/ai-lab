// The island's geometry, which is the part of `scene.js` that can be wrong
// without anything throwing.
//
//     node --test viewer/tests/scene.test.mjs
//
// Everything here is a pure function, so none of it needs a DOM. That is the
// point: the drawing needs a browser and gets one in `render.py`, but where a
// hut stands and whether a palm lands on a shelf are arithmetic, and arithmetic
// should not need Chromium to check.
//
// The load-bearing one is `test_scenery_keeps_off_the_cards`. The old placement
// test was a circle around the seat while a card is a tall box hanging below
// it, so palms passed the test and then rendered on top of the only part of the
// picture carrying information.

import { test } from "node:test";
import assert from "node:assert/strict";

import { layout, cardBox, fits, placeScenery, coast, closedPath, PALM_BOX,
         DWELL, dwellFor, shortName, NAME_MAX } from "../web/scene.js";
import { stepDelay, MIN_STEP, MAX_STEP } from "../web/feeds.js";

const overlaps = (a, b) =>
  a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

test("two traders face each other, and that is the shape on disk", () => {
  const g = layout(2);
  assert.equal(g.seats.length, 2);
  assert.equal(g.seats[0].y, g.seats[1].y, "both huts stand on the same line");
  assert.ok(g.seats[0].x < g.fire.x && g.fire.x < g.seats[1].x,
            "the fire is between them");
});

for (const n of [1, 2, 3, 4, 5, 6, 8]) {
  test(`every card and hut fits on the canvas with ${n} trader(s)`, () => {
    const g = layout(n);
    assert.equal(g.seats.length, n);
    assert.ok(fits(g), `a card or a hut runs off the canvas at n=${n}`);
  });

  test(`no two cards overlap with ${n} trader(s)`, () => {
    const boxes = layout(n).seats.map((s) => cardBox(s));
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        assert.ok(!overlaps(boxes[i], boxes[j]),
                  `cards ${i} and ${j} overlap at n=${n}`);
      }
    }
  });
}

test("more traders means a wider canvas, not a more crowded one", () => {
  // The page scales the SVG to its column, so growing the viewBox is what keeps
  // a six-hander legible rather than overlapping.
  const widths = [3, 4, 6, 8].map((n) => layout(n).w);
  for (let i = 1; i < widths.length; i++) {
    assert.ok(widths[i] > widths[i - 1], "the canvas has to grow with the table");
  }
});

test("scenery keeps off the cards", () => {
  const g = layout(2);
  // Aimed straight at every card, which is what the old circle test let past.
  const onTheCards = g.seats.flatMap((s) => {
    const b = cardBox(s);
    return [[b.x + 4, b.y + 4], [b.x + b.w / 2, b.y + b.h / 2],
            [b.x + b.w - 4, b.y + b.h - 4], [b.x + b.w / 2, b.y + b.h - 8]];
  });
  assert.deepEqual(placeScenery(g.seats, onTheCards), [],
                   "a palm was planted on a trader's shelf");
});

test("a palm is kept off by its whole spread, not by where it is planted", () => {
  // The second version of this bug: the anchor cleared the card and the fronds
  // did not, because a palm reaches ~38 units right of its trunk.
  const g = layout(2);
  const card = cardBox(g.seats[0]);
  const justLeftOfTheCard = [[card.x - PALM_BOX.w / 2, card.y + card.h / 2]];
  assert.deepEqual(placeScenery(g.seats, justLeftOfTheCard), [],
                   "a palm planted beside a card still reaches onto it");
});

test("the palm footprint covers where a palm is actually drawn", () => {
  // Guards the constant against the drawing: fronds to x+38, crown to y-50,
  // shadow to y+8, and the sway swings a little past all of that.
  assert.ok(PALM_BOX.dx <= -14, "the shadow reaches left of the trunk");
  assert.ok(PALM_BOX.dx + PALM_BOX.w >= 42, "the fronds reach right of it");
  assert.ok(PALM_BOX.dy <= -54, "the crown stands above it");
  assert.ok(PALM_BOX.dy + PALM_BOX.h >= 10, "the shadow lies below it");
});

test("scenery keeps off anything else it is told to", () => {
  const g = layout(2);
  const square = { x: g.fire.x - 148, y: g.fire.y - 74, w: 296, h: 128 };
  const inTheFire = [[g.fire.x, g.fire.y], [g.fire.x - 40, g.fire.y - 20]];
  assert.deepEqual(placeScenery(g.seats, inTheFire, undefined, 46, [square]), [],
                   "a palm was planted in the fire");
});

test("scenery well clear of everything is still planted", () => {
  const g = layout(2);
  // Otherwise the fix is "return nothing", which passes every test above and
  // leaves an empty island.
  const clear = [[40, 40], [g.w - 40, 40]];
  assert.deepEqual(placeScenery(g.seats, clear), clear);
});

test("the coast closes, and stays inside the canvas", () => {
  const g = layout(2);
  const pts = coast(g, 1);
  assert.ok(pts.length >= 16, "too few points to read as a coastline");
  for (const [x, y] of pts) {
    assert.ok(x >= 0 && x <= g.w && y >= 0 && y <= g.h,
              `coast point ${x},${y} is off the canvas`);
  }
  const d = closedPath(pts);
  assert.match(d, /^M /, "a path starts with a move");
  assert.match(d, / Z$/, "an island's coastline is closed");
  assert.equal((d.match(/ C /g) || []).length, pts.length,
               "one cubic per point, so the loop has no seam");
});

test("the coast is the same island on every reload", () => {
  // Wobble by `Math.random` would redraw the country under a scrub bar.
  const g = layout(2);
  assert.deepEqual(coast(g, 1), coast(g, 1));
});

test("surf and wet sand come off the same coast", () => {
  // Three hand-written paths would drift apart the first time the island moved.
  const g = layout(2);
  const [shore] = coast(g, 1);
  const [out] = coast(g, 1.05);
  const [inn] = coast(g, 0.95);
  assert.ok(Math.hypot(out[0] - g.cx, out[1] - g.ly)
            > Math.hypot(shore[0] - g.cx, shore[1] - g.ly));
  assert.ok(Math.hypot(inn[0] - g.cx, inn[1] - g.ly)
            < Math.hypot(shore[0] - g.cx, shore[1] - g.ly));
});


// --- how long a frame is held ---------------------------------------------
//
// The complaint this answers: "the animations were so quick I didn't catch
// what's going on". The cause was not animation length. `feeds.js` stepped
// every `MIN_STEP / speed` -- 35ms at the default 4x -- while a parcel took a
// second to cross, so six events started during one.

test("every event that draws something is held long enough to watch", () => {
  // Read off `play()` in scene.js. A kind that draws and is missing here is a
  // frame that flashes past, which is the whole bug.
  for (const kind of ["settled", "produced", "refused", "said", "bell", "open",
                      "over", "fault"]) {
    assert.ok(DWELL[kind] > 0, `${kind} draws something and has no dwell`);
  }
});

test("an attempt is not held, because it draws nothing", () => {
  // Its receipt or its refusal is the tell; a bubble as well would say it
  // twice, and holding a frame that draws nothing is just waiting.
  assert.equal(dwellFor({ kind: "said", attempt: true }), 0);
  assert.ok(dwellFor({ kind: "said", attempt: false }) > 0);
});

test("nothing is held for a viewer who asked for less motion", () => {
  // `play()` collapses every animation to 1ms for them, so holding the frame
  // would be making them wait for a still picture.
  for (const kind of Object.keys(DWELL)) {
    assert.equal(dwellFor({ kind }, true), 0, `${kind} still holds under reduce`);
  }
});

test("speed compresses the waiting, not the events", () => {
  const settled = { kind: "settled" };
  for (const speed of [1, 4, 16]) {
    assert.equal(stepDelay(0, speed, settled), DWELL.settled,
                 `a settle is cut short at ${speed}x`);
  }
  // The bug, stated as an assertion: this used to be MIN_STEP / 4 = 35ms.
  assert.ok(stepDelay(0, 4, settled) > MIN_STEP / 4);
});

test("a frame with nothing to watch still gets out of the way", () => {
  // Otherwise every speed above 1x stops meaning anything.
  const quiet = { kind: "acknowledged" };
  assert.ok(stepDelay(MAX_STEP * 4, 16, quiet) < stepDelay(MAX_STEP * 4, 1, quiet));
  assert.equal(stepDelay(0, 1, quiet), MIN_STEP);
});

test("a long silence is still clamped", () => {
  // A round is mostly silence; replaying it at wall speed is a still picture.
  assert.equal(stepDelay(60_000, 1, { kind: "acknowledged" }), MAX_STEP);
});


// --- a name the card can hold ----------------------------------------------
//
// Found live, watching game 002: the huts were labelled
// `ai-lab:claude/island-economy-game-wrapper-pcm5s6` and a base64 peer id, both
// rendered straight across the island at full length. A saved board is written
// in seat names, but a live one carries raw peer ids -- and an entrant picks
// its own name anyway, so nothing has ever stopped a trader being called
// something 40 characters long.

test("a name that fits is left alone", () => {
  for (const name of ["T1", "T2", "scout-v2", "trader-b"]) {
    assert.equal(shortName(name), name);
  }
});

test("a name that does not fit is clamped", () => {
  const long = "ai-lab:claude/island-economy-game-wrapper-pcm5s6";
  const got = shortName(long);
  assert.ok(got.length <= NAME_MAX, `${got.length} characters is still too many`);
  assert.notEqual(got, long);
});

test("the clamp keeps the end, because that is where names differ", () => {
  // Two sessions on one repo share every character of their prefix. Clamping
  // from the front would give both huts the same label.
  const a = shortName("ai-lab:claude/island-economy-game-wrapper-pcm5s6");
  const b = shortName("ai-lab:claude/island-economy-game-wrapper-zzzzzz");
  assert.notEqual(a, b, "two long names clamped to the same label name nobody");
});

test("nothing is lost: a clamped name still carries its own tail", () => {
  const long = "abcdefghijklmnopqrstuvwxyz";
  assert.ok(long.endsWith(shortName(long).replace("…", "")));
});

test("an empty or missing name does not throw", () => {
  assert.equal(shortName(""), "");
  assert.equal(shortName(undefined), "");
  assert.equal(shortName(null), "");
});
