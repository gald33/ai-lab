/** Turning a long list of saved boards into something you can find one in.
 *
 * The listing grew from a handful to 156 the day 007's rounds were published,
 * and a flat dropdown of that length is a list you scroll rather than a
 * control you use. Nothing here knows about islands: it groups by where a
 * board came from and matches text against what a person can actually see.
 *
 * Kept out of `index.html` so it can be tested the way the reducer is. The
 * page does the DOM; this does the deciding.
 */

/** Which tree a board came from, as a heading a person would recognise.
 *
 * The path's first segment is the root prefix `serve.py` gave it, and for the
 * experiment trees the second is the run. Both matter: 007 replicated one
 * cell four times, so the run is what tells four otherwise identical rounds
 * apart.
 */
export function groupOf(board) {
  const parts = String(board || "").split("/").filter(Boolean);
  const [prefix, second] = parts;
  const tree = { results: "005", ceiling: "007", replays: "games" }[prefix]
    || prefix || "elsewhere";
  // A board sitting straight under its root has no run to name -- the games
  // tree is like this -- and the tree alone is the whole heading.
  return parts.length > 2 && second ? `${tree} · ${second}` : tree;
}

/** The label with the part its own heading already says taken off the front.
 *
 * `001-ceiling-e-plan-seed4` under the heading `007 · 001-ceiling` is
 * `e-plan-seed4`, which is the half that differs between siblings.
 */
export function shortLabel(label, group) {
  const run = String(group || "").split("·").pop().trim();
  const text = String(label || "");
  return run && text.startsWith(run + "-") ? text.slice(run.length + 1) : text;
}

/** Every needle must appear somewhere in the haystack. Order does not matter.
 *
 * Space-separated so "plan 12" finds `e-plan-seed12` without anybody having to
 * know that the label puts `seed` in between. Matching runs over the heading
 * as well as the label, so "007" narrows to one experiment even though no
 * label contains it.
 */
export function matches(query, ...fields) {
  const hay = fields.join(" ").toLowerCase();
  return String(query || "").toLowerCase().split(/\s+/).filter(Boolean)
    .every((needle) => hay.includes(needle));
}

/** The listing as headings and their entries, filtered, order preserved.
 *
 * Entries that are not saved boards -- a live round, a `?board=` from the URL
 * -- carry no path and are never grouped or shortened. They stay at the top
 * under their own heading, because the one you were sent a link to is the one
 * you came here for.
 */
export function organise(entries, query = "") {
  const groups = new Map();
  for (const entry of entries) {
    const group = entry.pinned ? "" : groupOf(entry.board);
    const label = entry.pinned ? entry.label : shortLabel(entry.label, group);
    if (!matches(query, label, group, entry.label || "")) continue;
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push({ ...entry, label, group });
  }
  return [...groups].map(([group, items]) => ({ group, items }));
}

/** How many boards a filter is showing, for a control that has to say so. */
export function countOf(organised) {
  return organised.reduce((n, g) => n + g.items.length, 0);
}
