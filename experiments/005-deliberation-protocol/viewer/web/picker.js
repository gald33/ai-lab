/** Choosing a round out of a hundred and fifty by what it *was*.
 *
 * The listing grew past the point where a name helps: nobody remembers which
 * seed was the interesting one, and matching text against `e-plan-seed12` only
 * answers questions somebody already knows the answer to. What a person
 * actually wants is the round's own properties -- which condition, how many
 * traders, did the island end up better off than the sum of its hermits, was
 * anybody ruined -- and every one of those is recorded in the reveal sidecar
 * that `serve.py` now carries into the listing.
 *
 * So this is a facet index, not a search box. Nothing here knows about the
 * DOM: the page draws chips and this decides what they mean.
 */

/** Which tree and run a board came from, as a heading a person recognises.
 *
 * The run matters as much as the tree: 007 replicated one cell four times, so
 * an arm and a seed alone name four different rounds.
 */
export function groupOf(board) {
  const parts = String(board || "").split("/").filter(Boolean);
  const [prefix, second] = parts;
  const tree = { results: "005", ceiling: "007", replays: "games" }[prefix]
    || prefix || "elsewhere";
  return parts.length > 2 && second ? `${tree} · ${second}` : tree;
}

/** The label without the part its own heading already says. */
export function shortLabel(label, group) {
  const run = String(group || "").split("·").pop().trim();
  const text = String(label || "");
  return run && text.startsWith(run + "-") ? text.slice(run.length + 1) : text;
}

/** Did the island make more than its traders would have made alone?
 *
 * Welfare is total utility over the sum of solo optima, so 1.0 is the sum of
 * hermits and the only threshold worth a chip. Summing utilities is sound
 * here specifically because Cobb-Douglas with weights summing to one is
 * homogeneous of degree 1 -- see reports/2026-08-24-a-second-benchmark.md.
 */
export function welfareBand(facets = {}) {
  const w = facets.welfare;
  if (typeof w !== "number") return undefined;
  return w > 1 ? "better than alone" : "worse than alone";
}

/** How much of the round was spent at zero utility.
 *
 * Under Cobb-Douglas a single missing good zeroes a trader outright, so ruin
 * is the loudest thing that happens on an island and deserves its own axis
 * rather than being folded into an average.
 */
export function ruinBand(facets = {}) {
  const { zero_agent_episodes: zero, agent_episodes: total } = facets;
  if (typeof zero !== "number" || !total) return undefined;
  if (zero === 0) return "nobody ruined";
  return zero / total < 0.25 ? "some ruined" : "much ruined";
}

/** The axes a round can be filtered on, and how to read each off an entry.
 *
 * Declared once so the page's chips and these tests cannot disagree about
 * what a facet means. `of` returning undefined means the entry does not
 * answer that axis -- an old sidecar, or a board with none -- and such an
 * entry is only ever dropped by a filter on that axis, never by one on
 * another.
 */
export const FACETS = [
  { key: "run", label: "Run", of: (e) => groupOf(e.board) },
  { key: "arm", label: "Condition", of: (e) => e.facets?.arm },
  { key: "traders", label: "Traders", of: (e) => e.facets?.agents },
  { key: "welfare", label: "Together", of: (e) => welfareBand(e.facets) },
  { key: "ruin", label: "Ruin", of: (e) => ruinBand(e.facets) },
];

/** Every value on one axis, with how many rounds carry it.
 *
 * Counted against the *other* axes' selections rather than the whole listing,
 * so a chip's number is what clicking it would actually leave. A count that
 * ignored the current filter would promise rounds the filter has already
 * removed.
 */
export function options(entries, facet, selection = {}) {
  const others = { ...selection };
  delete others[facet.key];
  const pool = apply(entries, others);
  const counts = new Map();
  for (const entry of pool) {
    if (entry.pinned) continue;
    const value = facet.of(entry);
    if (value === undefined || value === null) continue;
    counts.set(value, (counts.get(value) || 0) + 1);
  }
  return [...counts]
    .sort((a, b) => (b[1] - a[1]) || String(a[0]).localeCompare(String(b[0])))
    .map(([value, count]) => ({ value, count }));
}

/** Every chosen word must appear somewhere, in any order. */
export function matches(query, ...fields) {
  const hay = fields.join(" ").toLowerCase();
  return String(query || "").toLowerCase().split(/\s+/).filter(Boolean)
    .every((needle) => hay.includes(needle));
}

/** The entries a selection leaves. Order is preserved; pinned entries stay.
 *
 * A selection is `{facetKey: [value, ...], text}`. Within one axis the chosen
 * values are alternatives, across axes they are all required -- which is what
 * makes "both ladder passes, the bare arm, nobody ruined" expressible.
 *
 * Pinned entries -- a live round, a `?board=` somebody was linked to -- are
 * never filtered out. Whatever else is being narrowed, the round you were
 * sent is the one you came for.
 */
export function apply(entries, selection = {}) {
  return entries.filter((entry) => {
    if (entry.pinned) return true;
    for (const facet of FACETS) {
      const chosen = selection[facet.key];
      if (!chosen || !chosen.length) continue;
      if (!chosen.includes(facet.of(entry))) return false;
    }
    return matches(selection.text, entry.label || "", groupOf(entry.board));
  });
}

/** How many axes a selection actually narrows on. */
export function activeCount(selection = {}) {
  const axes = FACETS.filter((f) => (selection[f.key] || []).length).length;
  return axes + (String(selection.text || "").trim() ? 1 : 0);
}

const ORDERS = {
  newest: (a, b) => (b.at || 0) - (a.at || 0),
  welfare: (a, b) => (b.facets?.welfare ?? -Infinity) - (a.facets?.welfare ?? -Infinity),
  ruin: (a, b) => (b.facets?.zero_agent_episodes ?? -Infinity)
    - (a.facets?.zero_agent_episodes ?? -Infinity),
};
export const SORTS = [
  { key: "newest", label: "newest" },
  { key: "welfare", label: "welfare" },
  { key: "ruin", label: "most ruined" },
];

/** The filtered listing as headings and entries, sorted within each heading.
 *
 * Sorting inside the heading rather than across it, because the heading is
 * the round's provenance and a listing that interleaved four experiments by
 * score would lose the one thing every label is short for.
 */
export function organise(entries, selection = {}, sort = "newest") {
  const order = ORDERS[sort] || ORDERS.newest;
  const groups = new Map();
  for (const entry of apply(entries, selection)) {
    const group = entry.pinned ? "" : groupOf(entry.board);
    const label = entry.pinned ? entry.label : shortLabel(entry.label, group);
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push({ ...entry, label, group });
  }
  return [...groups].map(([group, items]) => ({
    group,
    items: group ? [...items].sort(order) : items,
  }));
}

/** How many rounds a filtered listing is showing. */
export function countOf(organised) {
  return organised.reduce((n, g) => n + g.items.length, 0);
}

/** Which round the page opens on when the URL named none.
 *
 * A pinned entry -- a `?board=` somebody was linked to, an invite, a live game
 * the URL named -- is what the reader came for, so it always wins. The
 * listing's own live pointer is not that: see `openingCandidates`. With nothing pinned the page used to
 * open whatever happened to sort first, which made every unadorned visit the
 * same round forever; a random record is the cheap fix, and it is also the
 * honest one, since no round in the listing is the canonical one to show.
 *
 * `random` is injected so this is testable and so a caller can make the choice
 * reproducible; it must behave like `Math.random`.
 */
export function openingChoice(entries = [], random = Math.random) {
  if (!entries.length) return undefined;
  const pinned = entries.find((e) => e.pinned);
  if (pinned) return pinned;
  return entries[Math.floor(random() * entries.length)] || entries[0];
}

/** The entries the opening choice may consider.
 *
 * The listing's live pointer is a *standing offer*, not a request: `serve.py`
 * publishes it whether or not a game is running, so it is pinned and first in
 * the list every time. Opening it when the room has said nothing is how an
 * unadorned visit landed on an empty island -- and, until `scenery` was
 * taught about a cast of nobody, on a thrown error as well. So an offered
 * live entry is dropped from the opening choice unless it has a game in it;
 * it stays in the listing either way, where picking it is the reader asking.
 */
export function openingCandidates(entries = [], liveHasGame = false) {
  return liveHasGame ? entries : entries.filter((e) => !e.offered);
}
