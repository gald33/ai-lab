// What the campfire is allowed to do to the colour of the island.
//
//     node --test viewer/tests/firelight.test.mjs
//
// The fire throws a `PointLight` so that it lights the ground beside it rather
// than reading as a decal. Its light is orange and the island's grass is
// green, and the product of the two is yellow: at close range a warm light
// beats the material's own green channel down and the grass, the trees
// standing in it and the hill behind it all come out olive. That is the bug
// this file is here for -- reported by eye as the trees and the hill going
// yellow -- and it is a bug about *how much* light, not about its colour: a
// fire is orange and the ground beside a fire is warm.
//
// So the rule measured here is a ceiling, in the two terms a spectator
// actually reads: the fire may not out-shine the day it replaced, and beyond
// its own clearing it may not take a leaf off the green side of yellow.
//
// The sum below is the renderer's own for an up-facing surface -- ambient,
// plus each light by its angle -- the same approximation `island-life.js`
// already makes for the sea band, and for the same reason: it is checkable in
// a test with no GPU in it.

import { test } from "node:test";
import assert from "node:assert/strict";

import * as THREE from "../web/vendor/three/three.module.js";
import { buildIsland, M, GRASS_Y } from "../web/island3d.js";
import { enliven } from "../web/island-life.js";

/** The rig the stage builds, with the same colours and strengths. */
function rig() {
  const ambient = new THREE.AmbientLight(0xbcd2dd, 1.15);
  const key = new THREE.DirectionalLight(0xffd9a8, 2.1);
  key.position.set(4, 7, 3);
  const fill = new THREE.DirectionalLight(0x6fa6c8, 0.75);
  fill.position.set(-5, 3, -4);
  return { ambient, key, fill };
}

const UP = new THREE.Vector3(0, 1, 0);

/**
 * What an up-facing patch of `mat` at `at` comes out as, under the rig and
 * whatever point lights the island is carrying.
 */
function shade(mat, at, { ambient, key, fill }, points) {
  const c = new THREE.Color(0, 0, 0);
  const add = (light, ndl, atten = 1) => {
    const t = mat.color.clone().multiply(light.color);
    c.add(t.multiplyScalar(light.intensity * ndl * atten));
  };
  add(ambient, 1);
  for (const d of [key, fill]) {
    const dir = d.position.clone().normalize();
    add(d, Math.max(0, dir.dot(UP)) * 0.42);
  }
  for (const p of points) {
    const to = p.getWorldPosition(new THREE.Vector3()).sub(at);
    const dist = to.length();
    if (!p.intensity || (p.distance && dist >= p.distance)) continue;
    //: Three's own windowed inverse square, which is what the renderer does.
    const w = p.distance ? Math.pow(Math.max(0, 1 - Math.pow(dist / p.distance, 4)), 2) : 1;
    add(p, Math.max(0, to.normalize().dot(UP)), w / Math.max(dist * dist, 1e-6));
  }
  c.r = Math.min(1, c.r); c.g = Math.min(1, c.g); c.b = Math.min(1, c.b);
  return c;
}

const hue = (c) => c.getHSL({}).h * 360;
const lum = (c) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;

/** The island, its life layer, and the lights, at a given hour. */
function at(day) {
  const made = buildIsland({ traders: ["T1", "T2", "T3", "T4"],
                             goods: ["bread", "cloth", "iron", "salt"] });
  const life = enliven(made.island, { ground: made.ground });
  const lights = rig();
  life.update(1, { day, turn: 0, ...lights });
  const points = [];
  made.island.traverse((n) => { if (n.isPointLight) points.push(n); });
  return { made, life, lights, points };
}

//: The hearth's own clearing, outside which the island is grass a spectator
//: reads as grass. The fire's ring of stones is a quarter of a unit across and
//: `island3d.js` keeps 0.63 clear round it.
const CLEAR = 0.7;

test("the fire does not out-shine the day it replaced", () => {
  const noon = at(0.5);
  const day = shade(M.grass, new THREE.Vector3(0.45, GRASS_Y, 1.2),
                    noon.lights, noon.points);
  const night = at(1);
  //: A patch of meadow just outside the fire's clearing: the brightest grass
  //: the fire lights, once its own ground is excluded.
  const fire = night.made.anchors.fire;
  const near = new THREE.Vector3(fire.x + CLEAR, GRASS_Y, fire.z);
  const burning = shade(M.grass, near, night.lights, night.points);
  assert.ok(night.points.length, "the fire threw no light at all");
  assert.ok(lum(burning) <= lum(day),
            `grass beside the fire at nightfall is ${(lum(burning) / lum(day)).toFixed(2)}x `
            + "as bright as the same grass at midday; the island's night is lit "
            + "brighter than its noon");
});

test("the trees and the hill are still green once the fire is up", () => {
  const { made, lights, points } = at(1);
  const fire = made.anchors.fire;
  const bad = [];
  for (const n of [made.island.getObjectByName("upland"),
                   made.island.getObjectByName("ridge"),
                   ...[...made.island.children].filter((o) => /^tree_\d+$/.test(o.name))]) {
    if (!n) continue;
    const p = n.getWorldPosition(new THREE.Vector3());
    if (p.distanceTo(fire) < CLEAR) continue;
    const mat = n.isMesh ? n.material : M.grass;
    const h = hue(shade(mat, p, lights, points));
    //: 90 degrees is the yellow-green line. The materials sit at 118-128
    //: unlit and the day's own light never takes them below about 100 (see
    //: `island3d.js`, "Green, not olive"), so anything under 90 is the fire.
    if (h < 90) bad.push(`${n.name} at ${p.distanceTo(fire).toFixed(2)} from the fire: hue ${h.toFixed(0)}`);
  }
  assert.deepEqual(bad, [], "the firelight turned green things yellow:\n" + bad.join("\n"));
});
