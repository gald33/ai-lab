// The reducer against the boards that actually ran.
//
//     node --test viewer/tests/
//
// Two things are being defended. First, that the page reads the manager rather
// than the traders: a self-report must move nothing. Second, that the grammar
// still matches the manager's wording -- these strings live in
// `island/manager.py` and `run_v3.py`, and if either is reworded this test is
// where that shows up, rather than in a silently emptier island.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { reduce, classify } from "../web/reducer.js";
import { readBoard } from "./board.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const RESULTS = join(HERE, "..", "..", "results");

const board = (name) => readBoard(join(RESULTS, name));

function boards() {
  const out = [];
  for (const dir of readdirSync(RESULTS, { withFileTypes: true })) {
    if (!dir.isDirectory()) continue;
    for (const f of readdirSync(join(RESULTS, dir.name))) {
      if (f.startsWith("board-") && (f.endsWith(".json") || f.endsWith(".json.gz"))) {
        out.push(`${dir.name}/${f}`);
      }
    }
  }
  return out;
}

const say = (seq, author, body) => ({ seq, at: null, author, body });

test("a receipt moves a stock", () => {
  const t = reduce([
    say(1, "manager", "Schedule for this round. 2 traders: T1, T2. 8 episodes, 60s each."),
    say(2, "manager", "episode 1 of 8 is open. PRODUCE is settled for the next 30s."),
    say(3, "manager", "@T1 produced {'bread': 0.5, 'salt': 0.25}; 0.0 labour unspent"),
  ]);
  assert.equal(t.final.stocks.T1.bread, 0.5);
  assert.equal(t.final.stocks.T1.salt, 0.25);
  assert.equal(t.final.labour.T1, 0);
});

test("a trader's own account of itself moves nothing", () => {
  const t = reduce([
    say(1, "manager", "Schedule for this round. 2 traders: T1, T2. 8 episodes, 60s each."),
    say(2, "manager", "episode 1 of 8 is open. PRODUCE is settled for the next 30s."),
    say(3, "T1", "PRODUCE bread=0.5 salt=0.5"),
    say(4, "T1", "I now hold 9 bread and I have already traded with T2."),
  ]);
  assert.equal(t.final.stocks.T1.bread ?? 0, 0);
  assert.equal(t.final.counters.produced, 0);
  assert.equal(t.frames[2].event.attempt, "PRODUCE");
});

test("a line that is nearly a receipt is not repaired into one", () => {
  const e = classify(say(1, "manager", "@T1 produced roughly half a loaf"), {});
  assert.equal(e.kind, "unknown");
});

test("an exchange moves both ways, and only what the receipt says", () => {
  const t = reduce([
    say(1, "manager", "Schedule for this round. 2 traders: T1, T2. 8 episodes, 60s each."),
    say(2, "manager", "episode 1 of 8 is open."),
    say(3, "manager", "@T1 produced {'cloth': 1.0}; 0.0 labour unspent"),
    say(4, "manager", "@T2 produced {'salt': 1.0}; 0.0 labour unspent"),
    say(5, "manager", "p1: T1 offers {'cloth': 0.4} to T2 for {'salt': 0.3} — open until the bell"),
    say(6, "manager", "p1 settled: T1 and T2 exchanged {'cloth': 0.4} for {'salt': 0.3}"),
  ]);
  const s = t.final;
  assert.equal(round(s.stocks.T1.cloth), 0.6);
  assert.equal(round(s.stocks.T1.salt), 0.3);
  assert.equal(round(s.stocks.T2.cloth), 0.4);
  assert.equal(round(s.stocks.T2.salt), 0.7);
  assert.equal(s.proposals[0].status, "settled");
});

test("an open offer commits stock without moving it", () => {
  const t = reduce([
    say(1, "manager", "Schedule for this round. 2 traders: T1, T2. 8 episodes, 60s each."),
    say(2, "manager", "episode 1 of 8 is open."),
    say(3, "manager", "@T1 produced {'cloth': 1.0}; 0.0 labour unspent"),
    say(4, "manager", "p1: T1 offers {'cloth': 0.4} to T2 for {'salt': 0.3} — open until the bell"),
  ]);
  assert.equal(round(t.final.stocks.T1.cloth), 1);
  assert.equal(round(t.committed(t.final, "T1", "cloth")), 0.4);
});

test("the bell lapses what is open and eats what is held", () => {
  const t = reduce([
    say(1, "manager", "Schedule for this round. 2 traders: T1, T2. 8 episodes, 60s each."),
    say(2, "manager", "episode 1 of 8 is open."),
    say(3, "manager", "@T1 produced {'cloth': 1.0}; 0.25 labour unspent"),
    say(4, "manager", "p1: T1 offers {'cloth': 0.4} to T2 for {'salt': 0.3} — open until the bell"),
    say(5, "manager", "bell — episode 1 closed. 1 proposal(s) lapsed. Everything held has been consumed; stocks and labour are reset."),
  ]);
  const s = t.final;
  assert.equal(s.stocks.T1.cloth, 0);
  assert.equal(s.labour.T1, null);
  assert.equal(s.proposals[0].status, "lapsed");
  assert.equal(s.counters.lapsed, 1);
  assert.equal(s.episodes_closed.length, 1);
  assert.equal(round(s.episodes_closed[0].holdings.T1.cloth), 1);
  // T2 held nothing at all, which is a zero episode and the thing the metric
  // is most sensitive to. It has to survive into the record.
  assert.deepEqual(s.episodes_closed[0].starved, ["T1", "T2"]);
});

test("a refusal is counted and kept with its reason", () => {
  const t = reduce([
    say(1, "manager", "Schedule for this round. 2 traders: T1, T2. 8 episodes, 60s each."),
    say(2, "manager", "@T2 not settled: shares sum to 1.4, over the budget of 1.0 by 0.4"),
  ]);
  assert.equal(t.final.counters.refused, 1);
  assert.match(t.frames[1].event.reason, /over the budget/);
});

test("both schedules that have run are recognised", () => {
  const staged = classify(
    say(1, "manager", "episode 1 of 8 is open. PRODUCE is settled for the next 30s."), {});
  assert.equal(staged.staged, true);
  const flat = classify(say(1, "manager",
    "episode 3 of 8 is open; the bell is at 18:04:12Z (60s). PRODUCE, PROPOSE and APPROVE all settle until the bell."), {});
  assert.equal(flat.kind, "open");
  assert.equal(flat.staged, undefined);
  assert.equal(flat.bell_at, "18:04:12Z");
  assert.equal(flat.seconds, 60);
});

test("every saved board parses with nothing left over", () => {
  const files = boards();
  assert.ok(files.length > 0, "no saved boards to read");
  for (const file of files) {
    const t = reduce(board(file).messages);
    assert.equal(t.final.counters.unknown, 0,
      `${file}: ${t.final.counters.unknown} manager line(s) the page cannot read`);
    assert.ok(t.traders.length >= 2, `${file}: no traders found`);
    assert.ok(t.final.episodes_closed.length > 0, `${file}: no episode closed`);
  }
});

const round = (x) => Math.round(x * 1e9) / 1e9;
