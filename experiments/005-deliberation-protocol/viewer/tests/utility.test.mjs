// Utility, against the manager's own arithmetic.
//
//     node --test "viewer/tests/*.test.mjs"
//
// The test that matters is the last one: replay every saved board through the
// reducer the page draws with, score the rebuilt holdings with the revealed
// tastes, and put the result against the trajectory the manager scored at the
// time. If those disagree, the island is drawing a different economy from the
// one that ran -- which is the only way this wrapper could do real harm.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { reduce } from "../web/reducer.js";
import { utility, utilityOf, accumulate, audit, TOLERANCE } from "../web/utility.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const RESULTS = join(HERE, "..", "..", "results");
const read = (p) => JSON.parse(readFileSync(p, "utf8"));

function pairs() {
  const out = [];
  for (const dir of readdirSync(RESULTS, { withFileTypes: true })) {
    if (!dir.isDirectory()) continue;
    for (const f of readdirSync(join(RESULTS, dir.name))) {
      if (!f.startsWith("board-") || !f.endsWith(".json")) continue;
      const sidecar = join(RESULTS, dir.name, f.replace("board-", "reveal-"));
      if (existsSync(sidecar)) out.push({ board: join(RESULTS, dir.name, f), sidecar });
    }
  }
  return out;
}

test("Cobb-Douglas, including the zero that is not a rounding error", () => {
  const alpha = { bread: 0.5, salt: 0.5 };
  assert.equal(utility(alpha, { bread: 4, salt: 9 }), 6);        // sqrt(4*9)
  // Holding none of something is ruin, and ruin is zero however much else is held.
  assert.equal(utility(alpha, { bread: 100, salt: 0 }), 0);
  assert.equal(utility(alpha, { bread: 100 }), 0);
});

test("utility needs a taste, and says so rather than guessing", () => {
  assert.equal(utilityOf({ traders: {} }, "T1", { bread: 1 }), null);
  assert.equal(utilityOf(null, "T1", { bread: 1 }), null);
});

test("accumulating is what eff_round is scored on", () => {
  const trajectory = [[1, 2], [3, 4], [5, 6]];
  assert.equal(accumulate(trajectory, 0), 9);
  assert.equal(accumulate(trajectory, 1), 12);
});

test("every board with a sidecar reproduces the manager's scored trajectory", () => {
  const found = pairs();
  assert.ok(found.length >= 10, `only ${found.length} board/sidecar pairs`);
  for (const { board, sidecar } of found) {
    const timeline = reduce(read(board).messages);
    const result = audit(timeline, read(sidecar));
    assert.ok(result, `${board}: no recorded trajectory to check against`);
    assert.equal(result.disagreements.length, 0,
      `${board}: ${JSON.stringify(result.disagreements.slice(0, 2))}`);
    // Not exact, and cannot be: receipts carry four decimals while the manager
    // kept full precision. Agreement to ~1e-4 is agreement.
    assert.ok(result.worst < TOLERANCE,
      `${board}: worst gap ${result.worst.toExponential(2)}`);
    assert.ok(result.episodes > 0, `${board}: no closed episode`);
  }
});
