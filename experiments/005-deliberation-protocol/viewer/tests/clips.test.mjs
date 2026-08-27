// What a clip borrows off the island, and what the island gets back.
//
//     node --test viewer/tests/clips.test.mjs
//
// `island-events.js` animates nodes the island owns -- the field plots ripen
// green to gold, the drying racks rise -- and hands them back when the clip
// retires. Two clips can hold the same node at once, and that overlap is the
// case this file is here for: it is the one that left the fields gold for the
// rest of the round.

import { test } from "node:test";
import assert from "node:assert/strict";

import * as THREE from "../web/vendor/three/three.module.js";
import { stageEvent } from "../web/island-events.js";

/** An island with one bread site, and one plot standing in its field. */
function world() {
  const island = new THREE.Group();
  const site = new THREE.Group();
  site.name = "site_bread";
  const plot = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1),
                              new THREE.MeshStandardMaterial({ color: 0x55803f }));
  plot.name = "field_plot_0";
  plot.position.set(0, 0.5, 0);
  site.add(plot);
  island.add(site);
  return {
    plot,
    world: {
      island,
      anchors: { A: new THREE.Vector3(), B: new THREE.Vector3(),
                 site_bread: new THREE.Vector3(2, 0, 0) },
      goods: ["bread"],
      stock: null,
    },
  };
}

const made = (trader) => ({ kind: "produced", trader, made: { bread: 1 } });

test("a field the island lent out comes back green", () => {
  const { plot, world: w } = world();
  const was = { mat: plot.material, y: plot.position.y, s: plot.scale.y,
                hex: plot.material.color.getHex() };

  const c = stageEvent(made("A"), w);
  c.update(1.4);                       // ripe: gold, grown, still standing
  assert.notEqual(plot.material, was.mat, "the clip scribbles on the island's own material");
  assert.notEqual(plot.material.color.getHex(), was.hex);
  c.restore();

  assert.equal(plot.material, was.mat);
  assert.equal(plot.material.color.getHex(), was.hex);
  assert.equal(plot.position.y, was.y);
  assert.equal(plot.scale.y, was.s);
});

test("two receipts over one field, and the field still comes back green", () => {
  // The bug this is here for: the second clip used to snapshot whatever the
  // node held *at that moment* -- which was the first clip's gold clone, and
  // which the first clip disposed on its way out. Restoring it left the plots
  // gold and dead for the rest of the round. Reported as fields that started
  // green, went yellow mid-day and never came back.
  const { plot, world: w } = world();
  const was = { mat: plot.material, y: plot.position.y, s: plot.scale.y,
                hex: plot.material.color.getHex() };

  const first = stageEvent(made("A"), w);
  first.update(1.4);                   // gold and grown when the second starts
  const second = stageEvent(made("B"), w);
  second.update(0.4);

  // Retired in either order, the island gets its own material back.
  first.restore();
  second.restore();

  assert.equal(plot.material, was.mat, "the island's own material is back on the plot");
  assert.equal(plot.material.color.getHex(), was.hex, "and it is still green");
  assert.equal(plot.position.y, was.y);
  assert.equal(plot.scale.y, was.s);
});

test("a clip that starts mid-way through another grows from the field's own size", () => {
  // The second clip reads the plot's height for its baseline, so the node is
  // put back to rest before it looks.
  const { plot, world: w } = world();
  const s0 = plot.scale.y;

  const first = stageEvent(made("A"), w);
  first.update(1.4);
  const grown = plot.scale.y;
  assert.ok(grown > s0, "the first clip has the plot grown");

  const second = stageEvent(made("B"), w);
  second.update(1.4);
  assert.ok(Math.abs(plot.scale.y - grown) < 1e-9,
            "the second clip ripens the same field to the same height, not off the first's");
});
