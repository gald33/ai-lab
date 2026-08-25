import { test } from "node:test";
import assert from "node:assert/strict";
import { reduce, instant } from "../web/reducer.js";

// The live board that broke it: authors are peer ids, not seat names, so
// nothing is literally called "manager".
const MGR = "ai-lab:claude/island-economy-game-wrapper-pcm5s6";
const rows = [
  { seq: 1, author: MGR,
    body: "Schedule for this round. 2 traders: T1, T2. 3 episodes, 150s each." },
  { seq: 2, author: "pjVS4UdhwLKxCkUS4xRFA", body: "ACK" },
  { seq: 3, author: MGR, body: "episode 1 of 3 is open; the bell is at 00:00:00Z (150s)." },
  { seq: 4, author: MGR, body: "@T1 produced {'bread': 0.5}; 0.0 labour unspent" },
];

test("live: the manager is whoever posts the schedule", () => {
  const t = reduce(rows);
  assert.equal(t.manager, MGR, "the manager was not recognised on a live board");
  assert.deepEqual(t.traders, ["T1", "T2"],
                   "the huts are the seats, not whoever happened to post");
});

test("live: the manager does not get a hut of its own", () => {
  const t = reduce(rows);
  assert.ok(!t.traders.includes(MGR), "the manager was drawn as a trader");
  assert.ok(!t.traders.includes("pjVS4UdhwLKxCkUS4xRFA"), "a peer id was drawn as a trader");
});

test("live: the manager's receipts are still read as receipts", () => {
  const t = reduce(rows);
  assert.ok(t.events.some((e) => e.kind === "produced" && e.trader === "T1"),
            "a production receipt from a peer-id manager was not recognised");
});

test("a saved board, written in seat names, is unaffected", () => {
  const saved = [
    { seq: 1, author: "manager",
      body: "Schedule for this round. 2 traders: T1, T2. 3 episodes, 60s each." },
    { seq: 2, author: "manager", body: "@T2 produced {'salt': 0.9}; 0.0 labour unspent" },
  ];
  const t = reduce(saved);
  assert.equal(t.manager, "manager");
  assert.deepEqual(t.traders, ["T1", "T2"]);
  assert.ok(t.events.some((e) => e.kind === "produced" && e.trader === "T2"));
});

// --- the bell as a moment --------------------------------------------------
// The manager writes "the bell is at 12:42:27Z", which has no date in it. Every
// comparison against a clock got NaN and quietly did nothing: the live
// countdown read "bell due" from the first second of every episode, and the sun
// had no way to know how far through the day it was.

test("a bare time of day takes its date from the line that announced it", () => {
  assert.equal(instant("12:42:27Z", "2026-08-25T12:39:57.348Z"),
               "2026-08-25T12:42:27.000Z");
  assert.ok(Number.isFinite(Date.parse(instant("12:42:27Z", "2026-08-25T12:39:57.348Z"))));
});

test("a bell before its own announcement is tomorrow's", () => {
  // An episode opening at 23:59 rings at 00:01, and the naive reading puts the
  // bell twenty-four hours in the past -- an episode that is over before it
  // opened, and a sun already set.
  assert.equal(instant("00:01:30Z", "2026-08-25T23:59:00.000Z"),
               "2026-08-26T00:01:30.000Z");
});

test("a full instant is left alone, and nonsense is passed through", () => {
  assert.equal(instant("2026-08-25T12:42:27Z", "2026-08-25T12:39:57Z"),
               "2026-08-25T12:42:27Z");
  assert.equal(instant("soon", "2026-08-25T12:39:57Z"), "soon");
  assert.equal(instant("12:42:27Z", null), "12:42:27Z");
  assert.equal(instant(null, "2026-08-25T12:39:57Z"), null);
});

test("the reducer hands the scene a bell it can parse", () => {
  const rows = [
    { seq: 1, at: "2026-08-25T12:37:54Z", author: "m",
      body: "Schedule for this round. 2 traders: T1, T2. 3 episodes, 150s each." },
    { seq: 2, at: "2026-08-25T12:39:57Z", author: "m",
      body: "episode 1 of 3 is open; the bell is at 12:42:27Z (150s)." },
  ];
  const t = reduce(rows, {});
  assert.ok(Number.isFinite(Date.parse(t.final.bell_at)), t.final.bell_at);
  assert.equal(t.final.seconds, 150);
  // And the frame knows when it is, which is the other half of the fraction.
  assert.equal(t.final.at, "2026-08-25T12:39:57Z");
});
