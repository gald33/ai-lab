// Replay a saved board and print what each trader held at each bell.
//
// Not a viewer: this exists so `reveal.py --check` can put the reducer against
// the manager's own scored trajectory. If the two disagree, the page is drawing
// a different economy from the one that ran.

import { readFileSync } from "node:fs";
import { reduce } from "../web/reducer.js";

const path = process.argv[2];
if (!path) {
  console.error("usage: node holdings.mjs <board.json>");
  process.exit(2);
}
const board = JSON.parse(readFileSync(path, "utf8"));
const t = reduce(board.messages);
console.log(JSON.stringify({
  traders: t.traders,
  goods: t.goods,
  counters: t.final.counters,
  episodes: t.final.episodes_closed,
}, null, 1));
