// Replay a saved board and print what each trader held at each bell.
//
// Not a viewer: this exists so `reveal.py --check` can put the reducer against
// the manager's own scored trajectory. If the two disagree, the page is drawing
// a different economy from the one that ran.

import { reduce } from "../web/reducer.js";
import { readBoard } from "./board.mjs";

const path = process.argv[2];
if (!path) {
  console.error("usage: node holdings.mjs <board.json>");
  process.exit(2);
}
const board = readBoard(path);
const t = reduce(board.messages);
console.log(JSON.stringify({
  traders: t.traders,
  goods: t.goods,
  counters: t.final.counters,
  episodes: t.final.episodes_closed,
}, null, 1));
