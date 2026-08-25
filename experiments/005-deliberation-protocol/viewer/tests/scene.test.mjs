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

import { layout, cardBox, fits, placeScenery, coast, closedPath }
  from "../web/scene.js";

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
