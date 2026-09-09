// Reading a saved board, packed or not.
//
// `scores.py --pack` gzips boards in place to keep many replays affordable, so
// everything that reads one has to accept both names. The page never needs this
// -- the server sends `Content-Encoding: gzip` and the browser unwraps it.

import { readFileSync, existsSync } from "node:fs";
import { gunzipSync } from "node:zlib";

export function readBoard(path) {
  if (existsSync(path)) {
    return JSON.parse(path.endsWith(".gz")
      ? gunzipSync(readFileSync(path)).toString("utf8")
      : readFileSync(path, "utf8"));
  }
  const packed = `${path}.gz`;
  if (existsSync(packed)) return JSON.parse(gunzipSync(readFileSync(packed)).toString("utf8"));
  throw new Error(`no board at ${path}`);
}
