/** The board picker's deciding half: grouping, shortening, matching.
 *
 * These exist because the listing is now long enough that finding a board is
 * a real task, and a filter that quietly drops the round being watched is
 * worse than no filter at all.
 */
import test from "node:test";
import assert from "node:assert/strict";

import { groupOf, shortLabel, matches, organise, countOf } from "../web/picker.js";

const CEILING = "ceiling/001-ceiling/board-001-ceiling-e-plan-seed4.json";

test("a board is grouped by its tree and its run", () => {
  assert.equal(groupOf(CEILING), "007 · 001-ceiling");
  assert.equal(groupOf("results/v3-arms/board-island7-hint-1.json"), "005 · v3-arms");
});

test("a board with no run under it is grouped by its tree alone", () => {
  assert.equal(groupOf("replays/board-game-002.json"), "games");
});

test("an unknown prefix is still a heading rather than a crash", () => {
  assert.equal(groupOf("somewhere/else/board-x.json"), "somewhere · else");
  assert.equal(groupOf(""), "elsewhere");
  assert.equal(groupOf(undefined), "elsewhere");
});

test("the heading's own words come off the front of the label", () => {
  assert.equal(shortLabel("001-ceiling-e-plan-seed4", "007 · 001-ceiling"), "e-plan-seed4");
});

test("a label that does not start with its run is left alone", () => {
  assert.equal(shortLabel("island7-hint-1", "005 · v3-arms"), "island7-hint-1");
});

test("every word must match, in any order", () => {
  assert.equal(matches("plan 12", "e-plan-seed12", "007 · 001-ceiling"), true);
  assert.equal(matches("12 plan", "e-plan-seed12", "007 · 001-ceiling"), true);
  assert.equal(matches("plan 13", "e-plan-seed12", "007 · 001-ceiling"), false);
});

test("a word can match the heading, which no label contains", () => {
  assert.equal(matches("007", "e-plan-seed4", "007 · 001-ceiling"), true);
});

test("an empty filter matches everything", () => {
  assert.equal(matches("", "anything", ""), true);
  assert.equal(matches("   ", "anything", ""), true);
});

const LISTING = [
  { label: "live — the running round", pinned: true, value: "live" },
  { label: "001-ceiling-e-plan-seed4", board: CEILING, value: "a" },
  { label: "001-ceiling-e-bare-seed4", board: CEILING.replace("e-plan", "e-bare"), value: "b" },
  { label: "island7-hint-1", board: "results/v3-arms/board-island7-hint-1.json", value: "c" },
];

test("the listing comes back grouped, in the order it arrived", () => {
  const out = organise(LISTING);
  assert.deepEqual(out.map((g) => g.group), ["", "007 · 001-ceiling", "005 · v3-arms"]);
  assert.equal(countOf(out), 4);
  assert.deepEqual(out[1].items.map((e) => e.label), ["e-plan-seed4", "e-bare-seed4"]);
});

test("a pinned entry is never grouped or shortened", () => {
  const [first] = organise(LISTING);
  assert.equal(first.group, "");
  assert.equal(first.items[0].label, "live — the running round");
});

test("filtering narrows without reordering, and the count follows", () => {
  const out = organise(LISTING, "plan");
  assert.equal(countOf(out), 1);
  assert.equal(out[0].items[0].label, "e-plan-seed4");
});

test("a filter matching nothing yields nothing rather than everything", () => {
  assert.equal(countOf(organise(LISTING, "seed99")), 0);
});

test("the full label still matches after it has been shortened", () => {
  // Somebody who pasted a label from a run record types the long form; the
  // list shows the short one. Both have to find it.
  assert.equal(countOf(organise(LISTING, "001-ceiling-e-plan-seed4")), 1);
});
