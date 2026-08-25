import { test } from "node:test";
import assert from "node:assert/strict";
import { reduce } from "../web/reducer.js";

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
