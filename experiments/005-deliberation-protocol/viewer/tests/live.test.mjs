// `rowsFromState` against a real snapshot, not an assumed one.
//
// It reads a shape -- `{hub, agents, messages: [...]}`, each message carrying
// `channel`, `sealed_body`, `body`, `seq`, `created_at`, `from` -- that this
// page never defines. Two things build it instead: the local viewer's
// `api/state` (Python, `switchboard_viewer/viewer.py`) and the hub-direct
// feed's `snapshot()` (JS, `switchboard-room.js`). Switchboard keeps those two
// in sync with its own contract test; nothing kept this page's assumption in
// sync with either, which is exactly the kind of drift that renders as a
// silently empty island rather than a failure anywhere.
//
// `fixtures/snapshot-sample.json` is real output, not written by hand: a hub
// was started, a manager and a trader posted through it, a third agent under
// a different key posted alongside them, and `viewer_app.snapshot()` -- the
// same function `api/state` calls -- read it back. Regenerate it the same way
// if this ever needs to change; the recipe is `switchboard`'s own
// `tests/test_web_snapshot.py`, run once and captured rather than reimplemented
// here.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { rowsFromState } from "../web/feeds.js";
import { reduce } from "../web/reducer.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const snapshot = JSON.parse(readFileSync(join(HERE, "fixtures", "snapshot-sample.json")));

test("a real snapshot's readable messages become rows, in order, untouched", () => {
  const { rows } = rowsFromState(snapshot);
  assert.deepEqual(rows.map((r) => r.seq), [1, 2, 3]);
  assert.deepEqual(rows.map((r) => r.author), ["manager", "manager", "T1"]);
  assert.equal(rows[1].body, "@T1 produced {'iron': 0.44}; 0.1 labour unspent");
  assert.equal(rows[0].at, "2026-08-24T08:29:32.457200Z");
});

test("a message this reader cannot open never becomes a row", () => {
  const { rows, sealed } = rowsFromState(snapshot);
  assert.equal(rows.some((r) => r.seq === 4), false);
  assert.deepEqual(sealed, [4]);
});

// The sealed message's `channel` field is the hub's blinded token, not
// "island" -- a name only travels in the clear once its body opens. So a
// channel filter drops it before the sealed check ever runs: it is absent
// from a filtered read entirely, not counted as sealed. Real behaviour,
// pinned rather than assumed -- `hubFeed`/`liveFeed` both filter by channel.
test("a channel filter drops what it cannot open before it can count it as sealed", () => {
  const { rows, sealed } = rowsFromState(snapshot, { channel: "island" });
  assert.deepEqual(rows.map((r) => r.seq), [1, 2, 3]);
  assert.deepEqual(sealed, []);
});

test("what a real manager posted still reduces to a receipt", () => {
  // The end of the pipeline `startHub`/`startLive` actually run: a real
  // snapshot's rows, fed to the reducer that draws the island.
  const { rows } = rowsFromState(snapshot, { channel: "island" });
  const { frames } = reduce(rows);
  const produced = frames.find((f) => f.event.kind === "produced");
  assert.equal(produced?.event.trader, "T1");
  assert.equal(produced?.event.made.iron, 0.44);
});
