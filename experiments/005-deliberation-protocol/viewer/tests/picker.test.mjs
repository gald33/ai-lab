/** The round picker's deciding half: facets, counts, filtering, order.
 *
 * These exist because choosing among 157 rounds is a real task, and the ways
 * a filter can quietly do damage -- dropping the round being watched, or
 * promising counts it cannot deliver -- are not visible by looking at it.
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  FACETS, SORTS, groupOf, shortLabel, welfareBand, ruinBand,
  options, matches, apply, activeCount, organise, countOf,
} from "../web/picker.js";

const facet = (key) => FACETS.find((f) => f.key === key);

function round(label, board, facets, at = 0) {
  return { label, board, facets, at, value: label };
}

const LISTING = [
  { label: "live — the running round", pinned: true, value: "live" },
  round("001-ceiling-e-plan-seed4", "ceiling/001-ceiling/board-a.json",
        { arm: "e-plan", agents: 4, welfare: 1.41, zero_agent_episodes: 3, agent_episodes: 20 }, 3),
  round("001-ceiling-e-bare-seed4", "ceiling/001-ceiling/board-b.json",
        { arm: "e-bare", agents: 4, welfare: 0.98, zero_agent_episodes: 0, agent_episodes: 20 }, 2),
  round("001-ceiling-e-plan-seed8", "ceiling/001-ceiling/board-c.json",
        { arm: "e-plan", agents: 4, welfare: 0.0, zero_agent_episodes: 20, agent_episodes: 20 }, 4),
  round("island7-hint-1", "results/v3-arms/board-d.json",
        { arm: "hint", agents: 2, welfare: 1.05, zero_agent_episodes: 0, agent_episodes: 16 }, 1),
];

// --- reading a round -----------------------------------------------------

test("a board is grouped by its tree and its run", () => {
  assert.equal(groupOf("ceiling/001-ceiling/board-a.json"), "007 · 001-ceiling");
  assert.equal(groupOf("results/v3-arms/board-d.json"), "005 · v3-arms");
  assert.equal(groupOf("replays/board-game-002.json"), "games");
  assert.equal(groupOf(""), "elsewhere");
});

test("the heading's own words come off the front of the label", () => {
  assert.equal(shortLabel("001-ceiling-e-plan-seed4", "007 · 001-ceiling"), "e-plan-seed4");
  assert.equal(shortLabel("island7-hint-1", "005 · v3-arms"), "island7-hint-1");
});

test("welfare is banded at 1.0, the sum of hermits, and nowhere else", () => {
  assert.equal(welfareBand({ welfare: 1.0001 }), "better than alone");
  assert.equal(welfareBand({ welfare: 1 }), "worse than alone");
  assert.equal(welfareBand({ welfare: 0 }), "worse than alone");
});

test("a round with no welfare recorded answers no welfare question", () => {
  assert.equal(welfareBand({}), undefined);
  assert.equal(welfareBand(), undefined);
});

test("ruin is none, some, or much, and needs both numbers", () => {
  assert.equal(ruinBand({ zero_agent_episodes: 0, agent_episodes: 20 }), "nobody ruined");
  assert.equal(ruinBand({ zero_agent_episodes: 3, agent_episodes: 20 }), "some ruined");
  assert.equal(ruinBand({ zero_agent_episodes: 20, agent_episodes: 20 }), "much ruined");
  assert.equal(ruinBand({ zero_agent_episodes: 3 }), undefined);
  assert.equal(ruinBand({}), undefined);
});

// --- the axes ------------------------------------------------------------

test("an axis offers every value in the listing, commonest first", () => {
  assert.deepEqual(options(LISTING, facet("arm")),
                   [{ value: "e-plan", count: 2 },
                    { value: "e-bare", count: 1 },
                    { value: "hint", count: 1 }]);
});

test("a pinned entry is never counted into an axis", () => {
  const total = options(LISTING, facet("run")).reduce((n, o) => n + o.count, 0);
  assert.equal(total, LISTING.length - 1);
});

test("a count is what clicking would leave, given the other axes", () => {
  // Two e-plan rounds overall, but only one of them ruined nobody... and none:
  // both e-plan rounds here have ruin. Counted against the ruin filter, e-plan
  // must disappear rather than keep promising two.
  const under = options(LISTING, facet("arm"), { ruin: ["nobody ruined"] });
  assert.deepEqual(under, [{ value: "e-bare", count: 1 }, { value: "hint", count: 1 }]);
});

test("an axis counts itself against the other axes, not against itself", () => {
  // Choosing e-plan must not collapse the arm axis to only e-plan; the other
  // arms have to keep offering the way back.
  const arms = options(LISTING, facet("arm"), { arm: ["e-plan"] }).map((o) => o.value);
  assert.deepEqual(arms, ["e-plan", "e-bare", "hint"]);
});

// --- filtering -----------------------------------------------------------

test("values within one axis are alternatives", () => {
  const got = apply(LISTING, { arm: ["e-bare", "hint"] });
  assert.deepEqual(got.filter((e) => !e.pinned).map((e) => e.facets.arm), ["e-bare", "hint"]);
});

test("axes are all required at once", () => {
  const got = apply(LISTING, { arm: ["e-plan"], ruin: ["much ruined"] })
    .filter((e) => !e.pinned);
  assert.equal(got.length, 1);
  assert.equal(got[0].label, "001-ceiling-e-plan-seed8");
});

test("a pinned entry survives every filter", () => {
  const got = apply(LISTING, { arm: ["nothing-matches-this"] });
  assert.deepEqual(got.map((e) => e.label), ["live — the running round"]);
});

test("a round that cannot answer an axis is only dropped by that axis", () => {
  const quiet = round("no-facets", "ceiling/001-ceiling/board-e.json", {});
  const listing = [...LISTING, quiet];
  assert.ok(apply(listing, { run: ["007 · 001-ceiling"] }).includes(quiet));
  assert.ok(!apply(listing, { arm: ["e-plan"] }).includes(quiet));
});

test("the name box still matches label and heading, words in any order", () => {
  assert.equal(matches("plan 4", "e-plan-seed4", "007 · 001-ceiling"), true);
  assert.equal(matches("4 plan", "e-plan-seed4", "007 · 001-ceiling"), true);
  assert.equal(matches("007", "e-plan-seed4", "007 · 001-ceiling"), true);
  assert.equal(matches("plan 9", "e-plan-seed4", "007 · 001-ceiling"), false);
  assert.equal(matches("", "anything", ""), true);
});

test("the name box and the chips narrow together", () => {
  const got = apply(LISTING, { arm: ["e-plan"], text: "seed8" }).filter((e) => !e.pinned);
  assert.equal(got.length, 1);
  assert.equal(got[0].label, "001-ceiling-e-plan-seed8");
});

test("the badge counts axes narrowed, not values chosen", () => {
  assert.equal(activeCount({}), 0);
  assert.equal(activeCount({ arm: ["e-plan", "e-bare"] }), 1);
  assert.equal(activeCount({ arm: ["e-plan"], ruin: ["some ruined"] }), 2);
  assert.equal(activeCount({ arm: ["e-plan"], text: "seed8" }), 2);
  assert.equal(activeCount({ arm: [], text: "  " }), 0);
});

// --- the listing ---------------------------------------------------------

test("the listing comes back grouped, pinned entries first and ungrouped", () => {
  const out = organise(LISTING);
  assert.deepEqual(out.map((g) => g.group), ["", "007 · 001-ceiling", "005 · v3-arms"]);
  assert.equal(out[0].items[0].label, "live — the running round");
  assert.equal(countOf(out), 5);
});

test("labels are shortened under their heading", () => {
  const [, ceiling] = organise(LISTING);
  assert.deepEqual(ceiling.items.map((e) => e.label).sort(),
                   ["e-bare-seed4", "e-plan-seed4", "e-plan-seed8"]);
});

test("order sorts inside a heading, never across it", () => {
  const byWelfare = organise(LISTING, {}, "welfare");
  assert.deepEqual(byWelfare.map((g) => g.group), ["", "007 · 001-ceiling", "005 · v3-arms"]);
  assert.deepEqual(byWelfare[1].items.map((e) => e.facets.welfare), [1.41, 0.98, 0]);
});

test("newest is the default order", () => {
  const [, ceiling] = organise(LISTING, {}, "newest");
  assert.deepEqual(ceiling.items.map((e) => e.at), [4, 3, 2]);
  assert.deepEqual(organise(LISTING)[1].items.map((e) => e.at), [4, 3, 2]);
});

test("most ruined puts the ruined round first", () => {
  const [, ceiling] = organise(LISTING, {}, "ruin");
  assert.equal(ceiling.items[0].label, "e-plan-seed8");
});

test("every declared sort is a sort the listing accepts", () => {
  for (const { key } of SORTS) {
    assert.equal(countOf(organise(LISTING, {}, key)), 5, `sort ${key} lost rounds`);
  }
});

test("an unknown order falls back rather than emptying the list", () => {
  assert.equal(countOf(organise(LISTING, {}, "nonsense")), 5);
});

test("a filter matching nothing yields only what is pinned", () => {
  const out = organise(LISTING, { text: "seed999" });
  assert.equal(countOf(out), 1);
  assert.equal(out[0].items[0].pinned, true);
});
