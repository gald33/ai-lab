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
         CARD_H_SHUT, CARD_H_SHUT_BARE, SHUT_SCORE_Y, SCORE_ROW_DEEP, appetiteWidth,
         NAME_ROW_DEEP, scoreAt, cardHold, CARD_LINGER,
         DWELL, dwellFor, CARRY, carriedBy,
         shortName, NAME_MAX, SHORT, NOT_YOURS, culprits, refused, stacking, glideTo, sunAt, SET } from "../web/scene.js";
import { stepDelay, paceDelay, quietBefore, PACES, PACE_DEFAULT,
         MIN_STEP, MAX_STEP, QUIET } from "../web/feeds.js";

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

for (const n of [1, 2, 3, 4, 5, 6, 8]) {
  for (const portrait of [false, true]) {
    test(`the cards leave the island alone with ${n} trader(s), `
         + `${portrait ? "portrait" : "landscape"}`, () => {
      // The whole point of the margins. A card standing on the island covers
      // the market, a settlement, or whatever crossed the ground between them
      // -- which is the picture the page exists to show.
      const g = layout(n, portrait);
      assert.equal(g.cards.length, n, "every trader has a card position");
      assert.ok(g.islandBox.w > 0 && g.islandBox.h > 0, "the island has a box");
      for (const [i, seat] of g.cards.entries()) {
        if (g.islandFoot !== undefined) {
          //: **Portrait straddles the island**: half its rows stand above and
          //: half below, so that an opened card covers the island rather than
          //: another trader's numbers. So a card clears the island by being
          //: wholly above where it starts *drawing* or wholly below where it
          //: stops -- not by clearing its box, whose top and bottom sixths are
          //: empty: the island is a disc under a tilted camera and is not as
          //: tall as it is wide.
          //:
          //: At the height the layout reserved, which is the shut nameplate.
          //: An opened card covering the island is the whole point of the
          //: arrangement and is asserted nowhere as a defect.
          const box = cardBox(seat, CARD_H_SHUT);
          assert.ok(box.y + box.h <= g.islandTop || box.y >= g.islandFoot,
                    `card ${i} of ${n} runs from ${box.y} to ${box.y + box.h}, `
                    + `across an island drawn from ${g.islandTop} to `
                    + `${g.islandFoot}`);
        } else {
          assert.ok(!overlaps(cardBox(seat), g.islandBox),
                    `card ${i} of ${n} stands on the island `
                    + `(${JSON.stringify(cardBox(seat))} in `
                    + `${JSON.stringify(g.islandBox)})`);
        }
      }
    });

    test(`no two cards overlap in the margins with ${n} trader(s), `
         + `${portrait ? "portrait" : "landscape"}`, () => {
      //: **At the height the layout reserved**, which portrait and landscape
      //: no longer answer the same way. Landscape stands its cards in margins
      //: nothing else wants and reserves the open card. Portrait pitches its
      //: rows at the *shut* nameplate, because every unit it does not reserve
      //: is island -- so a card somebody opens is drawn over whatever is under
      //: it, and at three traders or more that is another card's nameplate.
      //: Measuring the open box here would be asserting the opposite of the
      //: thing the layout was changed to do.
      const boxes = layout(n, portrait).cards
        .map((s) => cardBox(s, portrait ? CARD_H_SHUT : undefined));
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          assert.ok(!overlaps(boxes[i], boxes[j]),
                    `cards ${i} and ${j} overlap at n=${n}`);
        }
      }
    });

    test(`every card stays on the canvas with ${n} trader(s), `
         + `${portrait ? "portrait" : "landscape"}`, () => {
      const g = layout(n, portrait);
      for (const [i, seat] of g.cards.entries()) {
        const b = cardBox(seat);
        assert.ok(b.x >= 0 && b.x + b.w <= g.w && b.y >= 0 && b.y + b.h <= g.h,
                  `card ${i} of ${n} runs off the ${g.w}x${g.h} canvas`);
      }
    });
  }
}

//: A phone, and what its stylesheet declares the pill rows and the transport
//: come to. Fractions of the window's height, which is the form `layout` takes
//: them in -- see `chromeBands()` in `index.html`.
const PHONE = { w: 390, h: 844 };
const BANDS = { top: 98 / PHONE.h, foot: 146 / PHONE.h };
const shape = ({ w, h }) => Math.floor((w / h) * 100) / 100;

for (const n of [1, 2, 4]) {
  test(`the chrome's band is the chrome's, with ${n} trader(s)`, () => {
    // Reported twice by somebody looking at a phone: four rows of pills stand
    // across the top of the frame and the island was drawn underneath them.
    const g = layout(n, true, shape(PHONE), BANDS);
    const above = Math.round(g.h * BANDS.top);
    assert.ok(g.islandTop >= above,
              `the island starts at ${g.islandTop}, inside the chrome's band `
              + `which runs to ${above}`);
    //: The nameplate, which is what the band was divided around. An opened
    //: card is drawn over whatever is under it -- including the transport --
    //: and that is the bargain that gave the island the room: see `cardPlan`.
    const bottom = (c, h) => cardBox(c, h).y + cardBox(c, h).h;
    const last = Math.max(...g.cards.map((c) => bottom(c, CARD_H_SHUT)));
    const foot = g.h - Math.round(g.h * BANDS.foot);
    assert.ok(last <= foot,
              `the last shut card ends at ${last}, inside the transport's band `
              + `which starts at ${foot}`);
    //: What an opened card may *not* do is leave the canvas, because past the
    //: viewBox nothing is drawn at all -- there is nothing there to draw over.
    const opened = Math.max(...g.cards.map((c) => bottom(c)));
    assert.ok(opened <= g.h,
              `an opened card ends at ${opened}, off a ${g.h}-unit canvas`);
  });
}

test("the portrait frame is the window's own shape, so nothing letterboxes", () => {
  // The whole reservation rests on this. A viewBox of some other shape is
  // fitted inside the window with `meet` and *centred* in whichever direction
  // is slack, so a band at the top of the viewBox lands in the middle of the
  // window and reserves the wrong strip.
  for (const win of [{ w: 390, h: 844 }, { w: 393, h: 660 }, { w: 360, h: 640 }]) {
    const g = layout(2, true, shape(win), { top: 162 / win.h, foot: 146 / win.h });
    const scale = Math.min(win.w / g.w, win.h / g.h);
    assert.ok(Math.abs(g.h * scale - win.h) < 1,
              `a ${g.w}x${g.h} frame in a ${win.w}x${win.h} window leaves `
              + `${(win.h - g.h * scale).toFixed(0)}px of it unpainted`);
  }
});

test("a bigger band is paid for by the island, not by the cards", () => {
  // The cards carry every number on the page; the island is the term that
  // gives. On a short phone that leaves the island small, and that is the
  // deliberate half of the trade -- it was bigger before because it was drawn
  // underneath the pills.
  //: A short phone -- what a shared link opens into with the browser's own
  //: bars showing. On a tall one the island is already at the frame's full
  //: width with the bands taken out, so there is nothing to see.
  const win = { w: 393, h: 660 };
  const bands = { top: 162 / win.h, foot: 146 / win.h };
  const bare = layout(2, true, shape(win), { top: 0, foot: 0 });
  const full = layout(2, true, shape(win), bands);
  assert.equal(bare.h, full.h, "the frame is the window's shape either way");
  assert.ok(full.islandBox.w < bare.islandBox.w,
            `the island did not give anything up (${bare.islandBox.w} -> `
            + `${full.islandBox.w})`);
  const height = (g) => cardBox(g.cards[0]).h;
  assert.equal(height(bare), height(full), "a card is the same card");
});

test("a wider window is spent on the island, never on the cards", () => {
  // The viewBox only ever widens with the frame. On a landscape phone the
  // fixed one letterboxed to a quarter of the screen and the rest was black.
  const narrow = layout(2, false, 1.4), wide = layout(2, false, 2.4);
  assert.equal(narrow.w, layout(2).w, "a window no wider changes nothing");
  assert.ok(wide.w > narrow.w, "a wider window makes a wider canvas");
  assert.ok(wide.islandBox.w - narrow.islandBox.w === wide.w - narrow.w,
            "every unit of the extra width goes to the island");
});

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
  for (const kind of ["settled", "produced", "refused", "declined", "said",
                      "bell", "open", "over", "fault"]) {
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

test("the symbols wait for the boxes, and the frame waits for the symbols", () => {
  // `carriedBy` is what `hands()` cues the gaining card's symbols at and what
  // `island-events.js` lands the boxes by. Two engines, one table; these are
  // the properties both of them lean on.
  for (const back of [false, true]) {
    for (let i = 1; i < 6; i++) {
      assert.ok(carriedBy(i, back) > carriedBy(i - 1, back),
                `good ${i} is cued no later than the one before it`);
      assert.equal(carriedBy(i, back) - carriedBy(i - 1, back), CARRY.step,
                   `good ${i} is cued off a different step than the table's`);
    }
    // The boxes are down, and standing there a beat, before anything rises.
    //
    // **Strictly later than the landing**, which is the whole assertion: with
    // the beat at zero this reads `>=` against its own definition and cannot
    // fail, and the symbol leaves on the same frame the hop finishes -- which
    // is the two reading as one motion rather than one following the other.
    assert.ok(carriedBy(0, back) > CARRY.off + CARRY.spread + CARRY.cross
                                   + CARRY.land,
              "the symbols are cued no later than the boxes stop moving");
  }
  // The return bundle follows the first, by the table's own number.
  assert.equal(carriedBy(0, true) - carriedBy(0, false), CARRY.back);

  // And the frame is held past the last symbol setting off -- otherwise the
  // replay steps on while a bar is still filling.
  const bundle = (n) => Object.fromEntries(
    ["bread", "cloth", "iron", "salt"].slice(0, n).map((g) => [g, 1]));
  for (let n = 1; n <= 4; n++) {
    const e = { kind: "settled", give: bundle(n), want: bundle(n) };
    assert.ok(dwellFor(e) > carriedBy(n - 1, true),
              `a ${n}-good exchange is let go before its last symbols leave`);
  }
  // A settle the reducer gave no bundle to still gets the table's own floor,
  // rather than nothing.
  assert.equal(dwellFor({ kind: "settled" }), DWELL.settled);
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


// --- three rules, not three numbers ----------------------------------------
//
// `1x / 4x / 16x` were a rate on the waiting only, which is why the top two
// were the same control wherever anything was happening -- the assertion for
// that is `the old speeds collapsed` below, kept as the reason these exist.

test("the old speeds collapsed into each other on a busy board", () => {
  // The defect, stated as an assertion so it cannot come back under new names:
  // once the gap term falls under the animation's own dwell, the rate stops
  // changing anything at all.
  const busy = { kind: "settled" };
  assert.equal(stepDelay(MAX_STEP, 4, busy), stepDelay(MAX_STEP, 16, busy),
               "4x and 16x held a settle for different lengths of time");
});

test("live is the pace that was missing: a real gap, uncompressed", () => {
  const quiet = { kind: "acknowledged" };
  // The whole point. Every old speed clamped this to MAX_STEP before dividing.
  assert.equal(paceDelay(60_000, "live", quiet), 60_000);
  assert.ok(paceDelay(60_000, "live", quiet) > paceDelay(60_000, "tight", quiet),
            "a minute of silence plays no longer than a compressed one");
  // Two silences of different lengths must look different, which is the
  // question the pace exists to answer.
  assert.ok(paceDelay(40_000, "live", quiet) > paceDelay(3_000, "live", quiet));
  assert.equal(paceDelay(40_000, "tight", quiet), paceDelay(3_000, "tight", quiet),
               "tightened is expected to flatten them -- that is what it is for");
});

test("step drops the waiting and keeps the picture", () => {
  const quiet = { kind: "acknowledged" };
  assert.equal(paceDelay(60_000, "step", quiet), MIN_STEP,
               "a silent line still gets out of the way, and no faster");
  // A board with no timestamps has every gap at zero; a floor is what stops
  // that playing as one skipped frame.
  assert.equal(paceDelay(0, "step", quiet), MIN_STEP);
});

test("no pace cuts an animation short", () => {
  // The one rule all three share, and the reason speed never touched it.
  const settled = { kind: "settled" };
  for (const pace of Object.keys(PACES)) {
    assert.equal(paceDelay(0, pace, settled), DWELL.settled,
                 `a settle is cut short under ${pace}`);
  }
});

test("an unknown pace is the default rather than a stopped player", () => {
  const quiet = { kind: "acknowledged" };
  assert.ok(PACES[PACE_DEFAULT], "the default names a pace that exists");
  assert.equal(paceDelay(60_000, "nonsense", quiet),
               paceDelay(60_000, PACE_DEFAULT, quiet));
});

test("a compressed silence is owned up to, and a lived-through one is not", () => {
  // `QUIET` was declared to draw exactly this distinction and then never used.
  assert.equal(quietBefore(QUIET + 1, "tight"), QUIET + 1);
  assert.equal(quietBefore(QUIET - 1, "tight"), 0, "a short gap is not a pause");
  assert.equal(quietBefore(60_000, "live"), 0,
               "real time announced a silence the viewer just sat through");
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

// --- why the manager refused -----------------------------------------------
// The reasons below are copied from game 002's board, not invented: the
// manager's wording is what the page matches on, so a paraphrase here would be
// testing a string nothing ever writes.

test("the shortfall refusal names the good it was short of", () => {
  const found = SHORT.exec("you have 0.0413 bread uncommitted, not the 0.1000 it asks for");
  assert.ok(found);
  assert.equal(found[2], "bread");
  assert.equal(found[1], "0.0413");
  assert.equal(found[3], "0.1000");
});

test("a refusal with no picture matches neither shape", () => {
  // Timing. There is nothing on the square to point at, so the badge and its
  // tooltip are the whole of what the page can honestly say.
  assert.equal(SHORT.exec("this episode has closed"), null);
  assert.equal(NOT_YOURS.exec("this episode has closed"), null);
});

test("approving somebody else's offer names the offer", () => {
  assert.equal(NOT_YOURS.exec("p3 was not addressed to you")[1], "p3");
  // Must not fire on a shortfall that happens to mention a proposal id.
  assert.equal(NOT_YOURS.exec("you have 0.3868 cloth uncommitted, not the 0.4000 it asks for"), null);
});

test("the culprit is the trader's own open offer holding that good", () => {
  // Game 002 episode 3, exactly: T1 offered 0.5 cloth in p7, then tried to
  // approve p6, which asked for 0.4 cloth, holding 0.3868 uncommitted.
  const proposals = [
    { pid: "p6", maker: "T2", taker: "T1", give: { iron: 0.25, salt: 0.05 }, status: "open" },
    { pid: "p7", maker: "T1", taker: "T2", give: { cloth: 0.5 }, status: "open" },
    { pid: "p2", maker: "T1", taker: "T2", give: { cloth: 0.35 }, status: "settled" },
  ];
  assert.deepEqual(culprits(proposals, "T1", "cloth").map((p) => p.pid), ["p7"]);
  // Not somebody else's offer, not a settled one, not a different good.
  assert.deepEqual(culprits(proposals, "T2", "cloth"), []);
  assert.deepEqual(culprits(proposals, "T1", "iron"), []);
  assert.deepEqual(culprits(undefined, "T1", "cloth"), []);
});


test("a refusal blinks the offer the manager was answering", () => {
  const proposals = [
    { pid: "p6", maker: "T2", taker: "T1", want: { cloth: 0.4 }, status: "open" },
    { pid: "p7", maker: "T1", taker: "T2", want: { iron: 0.5 }, status: "open" },
    { pid: "p2", maker: "T2", taker: "T1", want: { cloth: 0.3 }, status: "settled" },
  ];
  // Named outright by the manager.
  assert.deepEqual(
    refused(proposals, "T1", "p6 was not addressed to you").map((p) => p.pid), ["p6"]);
  assert.deepEqual(
    refused(proposals, "T1", "p7 is already settled").map((p) => p.pid), ["p7"]);
  // A pid the board never carried: nothing on the square to point at.
  assert.deepEqual(refused(proposals, "T1", "no such proposal 'p9'"), []);
  // Named by the good instead: the open offer addressed to this trader that
  // asks for it, and not the settled one that also did.
  assert.deepEqual(
    refused(proposals, "T1",
            "you have 0.3868 cloth uncommitted, not the 0.4000 it asks for")
      .map((p) => p.pid), ["p6"]);
  // At proposal time the offer does not exist yet: nothing blinks.
  assert.deepEqual(
    refused(proposals, "T1", "you have 0.0000 cloth uncommitted, not 0.1500"), []);
  assert.deepEqual(refused(undefined, "T1", "p6 was not addressed to you"), []);
});


test("pills waiting on one hut stack, oldest at the bottom", () => {
  const open = [
    { pid: "p1", maker: "T1", taker: "T4" },
    { pid: "p2", maker: "T2", taker: "T4" },
    { pid: "p3", maker: "T2", taker: "T3" },
    { pid: "p4", maker: "T3", taker: "T4" },
  ];
  // By taker, not by pair: three different makers offering T4 used to land on
  // that one roof on top of each other, all of them at pair fan 0.
  assert.deepEqual([...stacking(open)].map(([pid, s]) => [pid, s.i]),
                   [["p1", 0], ["p2", 1], ["p3", 0], ["p4", 2]]);
  // How tall the pile is, on every member of it: the fifth of five and the
  // fifth of nine sit at different heights once the pile has to fit the frame.
  assert.deepEqual([...stacking(open)].map(([pid, s]) => [pid, s.of]),
                   [["p1", 3], ["p2", 3], ["p3", 1], ["p4", 3]]);
  assert.deepEqual([...stacking([])], []);
  assert.deepEqual([...stacking(undefined)], []);
});


test("a pill closes the gap to its target, and never in one step", () => {
  const was = { x: 0, y: 0 }, target = { x: 0, y: 38 };
  // A frame's worth of animation moves part of the way, not all of it.
  const one = glideTo(was, target, 16);
  assert.ok(one.y > 0 && one.y < 38 * 0.25, `one frame moved ${one.y}`);
  // Successive steps converge without overshooting.
  let at = was;
  for (let i = 0; i < 40; i++) at = glideTo(at, target, 16);
  assert.ok(Math.abs(at.y - 38) < 0.5, `forty frames landed at ${at.y}`);
  assert.ok(at.y <= 38, "never past the target");
  // **The regression this exists for.** A pill sitting still is not being
  // stepped, so when its pile changes under it the gap since the last step is
  // however long it sat there. Measured before the clamp: the whole 38 units
  // in one frame -- a jump wearing an ease.
  const idle = glideTo(was, target, 9000);
  assert.ok(idle.y < 38 * 0.4, `after a long idle moved ${idle.y}`);
  assert.deepEqual(idle, glideTo(was, target, 48), "capped at one slow frame");
  // Nothing moves in no time.
  assert.deepEqual(glideTo(was, target, 0), was);
});


// --- the sun marks the day -------------------------------------------------
// An episode is a day. The page used to say how long the board had been quiet
// in a pill -- a number about the replay, not about the island -- while the sun
// sat in one place for the whole episode.

test("the sun crosses the sky from one side to the other", () => {
  for (const g of [layout(2), layout(2, true), layout(4)]) {
    const dawn = sunAt(g, 0), noon = sunAt(g, 0.5), dusk = sunAt(g, 1);
    assert.ok(dawn.x < noon.x && noon.x < dusk.x, "it should travel east to west");
    assert.ok(noon.y < dawn.y && noon.y < dusk.y, "and be highest in the middle");
    // Symmetric about the island, so noon is overhead rather than off to a side.
    assert.ok(Math.abs((dawn.x + dusk.x) / 2 - g.cx) < 1);
  }
});

test("it clears the island at noon, and never sets behind the wrong edge", () => {
  // The sun is drawn *behind* the land so that it can set behind it. An arc
  // that dipped under the island's top edge would take the sun through the
  // island at midday and simply vanish.
  for (const g of [layout(1), layout(2), layout(4), layout(2, true), layout(4, true)]) {
    const top = g.ly - g.ry;
    for (let p = 0; p <= 1.0001; p += 0.05) {
      assert.ok(sunAt(g, p).y < top,
                `at p=${p.toFixed(2)} the sun is at ${sunAt(g, p).y}, below the island top ${top}`);
    }
  }
});

test("portrait has a sky for it to cross", () => {
  // It did not: the island ran from 40 to 900 of a 940 viewBox, which left the
  // sun a strip to sit in and nowhere to travel.
  const g = layout(2, true);
  assert.ok(g.ly - g.ry >= 120, `only ${g.ly - g.ry} units of sky`);
  assert.ok(fits(g));
});

test("a point outside the day is held to its ends", () => {
  const g = layout(2);
  // Before the day, dawn. After it, fully set -- not the horizon: the sun goes
  // on down past the bell, and `SET` is where it has finished doing so.
  assert.deepEqual(sunAt(g, -3), sunAt(g, 0));
  assert.deepEqual(sunAt(g, 12), sunAt(g, SET));
  assert.notDeepEqual(sunAt(g, SET), sunAt(g, 1));
});

test("the day runs on past the bell rather than stopping at the horizon", () => {
  const g = layout(2);
  const horizon = sunAt(g, 1), setting = sunAt(g, (1 + SET) / 2), gone = sunAt(g, SET);
  // Down and further west, continuously: the bell rings while this is
  // happening rather than causing it.
  assert.ok(horizon.y < setting.y && setting.y < gone.y);
  assert.ok(horizon.x < setting.x && setting.x < gone.x);
  assert.ok(gone.y > g.ly - g.ry, "it should end behind the island");
  assert.equal(horizon.dim, 1);
  assert.ok(setting.dim > 0 && setting.dim < 1);
  assert.equal(gone.dim, 0);
});

test("a day begins with the sun still out of sight", () => {
  // Otherwise the night's jump from west to east is a sun popping into
  // existence at dawn, which is the one moment the eye is on the sky.
  for (const g of [layout(2), layout(2, true)]) {
    assert.equal(sunAt(g, 0).dim, 0);
    assert.ok(sunAt(g, 0.02).dim < 0.4);
    assert.equal(sunAt(g, 0.1).dim, 1);
  }
});


// --- a card that is shut ---------------------------------------------------
//
// Landscape's answer to the question portrait answers with `FOCUS`. The
// geometry that can be wrong without anything throwing is the relation between
// where the score row is put and how tall the card is drawn: get it backwards
// and the ALONE mark hangs through the card's bottom edge, which is a thing a
// browser renders perfectly happily.

test("a shut card is tall enough for the row it keeps", () => {
  // Card coordinates start at the seat, so a card's box runs from CARD_TOP to
  // CARD_TOP + height -- the height is the box's depth, not the drop to its
  // foot. Written as a literal 88 first, and right by luck; this is the
  // relation it was lucky about.
  const CARD_TOP = 22;
  const foot = CARD_TOP + CARD_H_SHUT;
  assert.ok(SHUT_SCORE_Y + SCORE_ROW_DEEP <= foot,
            `the score row reaches ${SHUT_SCORE_Y + SCORE_ROW_DEEP} and the `
            + `card ends at ${foot}: the ALONE mark is through the edge`);
  // And not so tall that the card is mostly empty, which is the whole point of
  // shutting it. One padding's worth of slack, no more.
  assert.ok(foot - (SHUT_SCORE_Y + SCORE_ROW_DEEP) <= 12,
            "a shut card is carrying dead height");
});

test("a shut card is shorter than the card it shuts", () => {
  // If this ever stops being true the mechanism is costing height rather than
  // giving it back, and there is no reason to have it.
  const g = layout(2);
  const open = cardBox(g.seats[0]);
  assert.ok(CARD_H_SHUT < open.h,
            `shut ${CARD_H_SHUT} is not shorter than open ${open.h}`);
  // Worth roughly half the card: less than that and the island gains too
  // little to be worth a click, and the number is here so that a change to
  // either height has to look at this.
  assert.ok(CARD_H_SHUT < open.h * 0.6,
            `shut is ${(CARD_H_SHUT / open.h * 100) | 0}% of open`);
});

test("the score row moves rather than hides when a card shuts", () => {
  // The one mark whose *position* depends on the state. Everything else on a
  // shut card is where it always was and is only not drawn, which is why the
  // stylesheet can do the rest and cannot do this.
  const BASE = 104;
  assert.ok(SHUT_SCORE_Y < BASE + 52,
            "the shut row is not above where the open row sits");
});

test("a live island's shut card is sized for what a live card actually has", () => {
  // Live has no score row at all -- tastes are private and never reach the
  // board -- so a shut card there is a name and a labour dial and nothing
  // else. Sized at the scored height it was two dark rectangles holding one
  // word each, with 55 units of empty box underneath. Reported by eye.
  const CARD_TOP = 22;
  assert.ok(CARD_H_SHUT_BARE < CARD_H_SHUT,
            "a card with no utility row is not shorter than one with it");
  assert.ok(CARD_H_SHUT_BARE >= NAME_ROW_DEEP,
            "the labour dial is through the bottom of a bare shut card");
  // And no more than a padding taller than the row it holds, which is the
  // whole complaint: the box must not be mostly empty.
  assert.ok(CARD_H_SHUT_BARE - NAME_ROW_DEEP <= 12,
            `a bare shut card carries ${CARD_H_SHUT_BARE - NAME_ROW_DEEP} `
            + "units of dead height");
  // The symbol a settlement flies at a shut card aims at the card's middle.
  // On a bare card the old target -- the score row at SHUT_SCORE_Y -- is below
  // the card's own foot, so every symbol landed just under the card.
  assert.ok(SHUT_SCORE_Y > CARD_TOP + CARD_H_SHUT_BARE,
            "this test no longer describes the bug it was written for");
  assert.ok(CARD_TOP + CARD_H_SHUT_BARE / 2 < CARD_TOP + CARD_H_SHUT_BARE,
            "the aim point is outside the card it aims at");
});

test("a card opened by an event outlives the animation that opened it", () => {
  // The bug, stated as an assertion. The hold was `dwellFor` exactly -- which
  // is when the animation *ends*, and the animation ending is the frame the
  // new quantity appears on the bar. So the card shut on the one frame the
  // thing it was opened for became readable.
  for (const e of [{ kind: "settled" }, { kind: "produced" },
                   { kind: "settled", give: { bread: 1, cloth: 1 }, want: { iron: 1 } }]) {
    assert.ok(cardHold(e) > dwellFor(e),
              `a ${e.kind} card shuts as its last number lands`);
    assert.equal(cardHold(e) - dwellFor(e), CARD_LINGER,
                 "the linger is not the whole of the difference");
  }
  // Long enough to read four quantities and a utility. If this ever drops to
  // something reflex-speed the card is flashing, not showing.
  assert.ok(CARD_LINGER >= 800, "too short to read the numbers it opened for");
  // And not so long that a busy market is simply every card open.
  assert.ok(CARD_LINGER <= 3000, "the card is no longer shut by default");
});

test("reduced motion still holds the card long enough to read", () => {
  // With motion off `dwellFor` is 0 -- there is no animation to wait for -- so
  // the linger is the whole hold. Without it a card would open and shut inside
  // one frame for a viewer who asked for less movement, not more.
  const e = { kind: "settled" };
  assert.equal(dwellFor(e, true), 0);
  assert.equal(cardHold(e, true), CARD_LINGER);
});

test("the score row's animated position is valid CSS, not an SVG attribute", () => {
  // The bug this pins, which is the worst shape one can take here: the row is
  // *positioned* with an SVG transform attribute -- `translate(0 156)` -- and
  // handing that to `Element.animate` gives keyframes the engine silently
  // drops, because CSS wants units. The animation still exists and still
  // reports its duration; it just moves nothing. Every visible sign says it
  // works. Found by reading the keyframes back off the running animation.
  for (const open of [true, false]) {
    const t = scoreAt(open);
    assert.match(t, /^translate\(0px, \d+px\)$/,
                 `${t} is not a CSS transform a keyframe will keep`);
  }
  // And the two ends are different, or there is nothing to animate.
  assert.notEqual(scoreAt(true), scoreAt(false));
  // Open sits below shut: the row scores the shelf, so with a shelf above it
  // it has to move down, not up.
  const y = (t) => Number(/(\d+)px\)$/.exec(t)[1]);
  assert.ok(y(scoreAt(true)) > y(scoreAt(false)),
            "the open row is not below the shut one");
  // It lands inside the card it is drawn on, both ways.
  assert.ok(y(scoreAt(false)) + SCORE_ROW_DEEP <= 22 + CARD_H_SHUT);
});


// --- what a trader wants, as the width of its column ------------------------
//
// `appetiteWidth` is the whole of the taste drawing, and it is arithmetic, so
// it is checked here rather than in a browser. What `render.py` checks is that
// the shelf actually uses it, and that a board with no reveal has no widths at
// all.

const STEP = 34;                    // five goods on a 170-unit shelf
const TASTE = { bread: 0.6979, cloth: 0.1184, iron: 0.0913, salt: 0.0924 };
const TOP = Math.max(...Object.values(TASTE));

test("the good a trader wants most gets the widest column", () => {
  const w = Object.fromEntries(Object.entries(TASTE)
    .map(([g, a]) => [g, appetiteWidth(a, TOP, STEP)]));
  const order = Object.keys(w).sort((a, b) => w[b] - w[a]);
  assert.equal(order[0], "bread", "bread is 0.70 of this trader's taste");
  //: The order is the claim -- see `appetiteWidth`. A column twice as wide is
  //: not a taste twice as large, because there is a floor under the width, so
  //: what is asserted is the ranking and not a ratio.
  for (const [a, b] of [["bread", "cloth"], ["cloth", "salt"], ["salt", "iron"]]) {
    assert.ok(w[a] >= w[b], `${a} (${TASTE[a]}) is at least as wide as ${b}`);
  }
});

test("the widest column leaves a gutter, at every good count", () => {
  // The shelf is 170 units wide inside its card, whatever is standing on it.
  for (const n of [1, 2, 3, 4, 5, 6, 7]) {
    const step = (196 - 26) / n;
    const w = appetiteWidth(1, 1, step);
    assert.ok(w <= step, `the widest of ${n} columns is ${w} in a ${step} slot`);
  }
});

test("a taste too small to draw is floored rather than vanishing", () => {
  // A column has to stay visible and stay tappable. Cobb-Douglas puts no floor
  // under an alpha, so the drawing has to.
  const tiny = appetiteWidth(1e-6, 1, STEP);
  assert.ok(tiny > 6, `a near-zero taste still draws ${tiny} units wide`);
  assert.ok(tiny < appetiteWidth(1, 1, STEP), "and is still the narrowest");
});

test("no taste is no width, which is not the same as an even one", () => {
  // The distinction the whole thing rests on: live has no reveal, so nobody
  // outside a trader's head knows what they want. That is drawn as *no*
  // appetite, and `hut()` falls back to the fixed bar -- never as an even
  // appetite, which would be a claim.
  assert.equal(appetiteWidth(undefined, TOP, STEP), null);
  assert.equal(appetiteWidth(0, TOP, STEP), null);
  assert.equal(appetiteWidth(0.3, 0, STEP), null);
});
