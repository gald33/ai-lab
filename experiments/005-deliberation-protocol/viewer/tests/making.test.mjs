// A receipt's crates land before their symbols leave, and the crates are open
// when they do.
//
//     node --test viewer/tests/making.test.mjs
//
// **Reported by eye: "for trades I see the boxes move and only then their
// symbols, but production isn't the same".** It was not. An exchange has had
// one schedule across both engines since `CARRY` was written -- three.js
// crates in seconds off a clip clock, SVG symbols in milliseconds off the same
// table -- and production had none: `island-events.js` flew its crates off
// hard-coded seconds while `scene.js:produce` filled the shelf off
// `DWELL.produced`, and the symbols left the yard a second and a half before
// the crates got there.
//
// This is the check that says they agree, and it is the *claim* that is
// checked, not the table: for each good, when its own crates stop moving,
// against when the card is told to send that good's symbol up.

import { test } from "node:test";
import assert from "node:assert/strict";

import * as THREE from "../web/vendor/three/three.module.js";
import { stageEvent } from "../web/island-events.js";
import { MAKE, madeBy, IN_LEG } from "../web/scene.js";

const GOODS = ["bread", "cloth", "iron"];

/** An island with a site per good, and a yard that keeps what arrives. */
function world() {
  const island = new THREE.Group();
  const anchors = { T1: new THREE.Vector3(0, 0, 0) };
  for (const [i, g] of GOODS.entries()) {
    const site = new THREE.Group();
    site.name = `site_${g}`;
    island.add(site);
    anchors[`site_${g}`] = new THREE.Vector3(3 + i, 0, i);
  }
  //: A stock small enough to read and real enough to answer the three
  //: questions a clip asks it: how many crates a quantity is, how many are
  //: standing, and where the next ones go.
  const held = Object.fromEntries(GOODS.map((g) => [g, []]));
  const stock = {
    want: (good, qty) => (qty > 1e-9 ? Math.max(1, Math.round(qty / 0.46)) : 0),
    count: (t, good) => held[good].length,
    mint(good, n, at) {
      return Array.from({ length: n }, () => {
        const m = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.15, 0.15),
                                 new THREE.MeshStandardMaterial());
        m.name = `box_${good}`;
        // The hinge a lid hangs off, which is what `openLid` turns.
        const hinge = new THREE.Group();
        hinge.name = "lid";
        hinge.add(new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.02, 0.15),
                                 new THREE.MeshStandardMaterial()));
        m.add(hinge);
        m.position.copy(at);
        island.add(m);
        return m;
      });
    },
    put(t, good, boxes) {
      const at = boxes.map((m, i) => new THREE.Vector3(
        held[good].length + i, 0.075, GOODS.indexOf(good)));
      held[good].push(...boxes);
      return at;
    },
  };
  return { island, anchors, goods: GOODS, traders: ["T1"], stock, held };
}

/** The moment each good's crates last moved, in milliseconds. */
function stops(clip, held) {
  const seen = {}, stopped = {};
  const place = (m) => `${m.position.x.toFixed(4)},${m.position.y.toFixed(4)},`
                     + `${m.position.z.toFixed(4)}`;
  for (let t = 0; t <= clip.dur + 0.2; t += 0.02) {
    clip.update(t);
    for (const [good, boxes] of Object.entries(held)) {
      if (!boxes.length) continue;
      const now = boxes.map(place).join("|");
      if (seen[good] !== undefined && now !== seen[good]) stopped[good] = Math.round(t * 1000);
      seen[good] = now;
    }
  }
  return stopped;
}

test("a receipt's crates are standing in the yard before its symbols leave", () => {
  const w = world();
  const made = { bread: 1.4, cloth: 0.5, iron: 2.2 };
  const c = stageEvent({ kind: "produced", trader: "T1", made }, w);
  assert.ok(c, "a receipt of three goods staged no clip at all");
  const stopped = stops(c, w.held);

  Object.keys(made).forEach((good, i) => {
    //: What the card is told, from the page's own table. The symbol is cued
    //: `MAKE.rest` after the last crate of that good has landed -- exactly the
    //: gap `carriedBy` leaves in an exchange, and for the same reason: cued on
    //: the landing frame itself, the two read as one motion.
    const cue = madeBy(i);
    const at = stopped[good];
    assert.ok(at !== undefined, `${good}: nothing of it ever moved`);
    assert.ok(at <= cue, `${good}: its crates were still moving at ${at}ms and the `
                       + `card was told to send its symbol at ${cue}ms -- the bar `
                       + `fills from goods that have not arrived`);
    //: And not *early* by more than the beat, either: a table could otherwise
    //: be made to pass by holding every symbol until long after the island had
    //: gone still.
    assert.ok(cue - at <= MAKE.rest + 60,
              `${good}: its crates stopped at ${at}ms and the symbol is not cued `
              + `until ${cue}ms; the two schedules have drifted apart`);
  });
});

test("a crate is open while its symbol is rising out of it", () => {
  const w = world();
  const c = stageEvent({ kind: "produced", trader: "T1", made: { bread: 1.4 } }, w);
  const open = (t) => {
    c.update(t);
    return Math.abs(w.held.bread[0].getObjectByName("lid").rotation.x);
  };
  //: Shut on the way over, open across the rise, and shut again after it.
  assert.equal(open(madeBy(0) / 1000 - (MAKE.land + MAKE.rest) / 1000 - 0.3), 0,
               "a crate was open while it was still crossing the island");
  assert.ok(open(madeBy(0) / 1000) > 1,
            "a crate was shut at the moment its symbol was told to leave it");
  assert.ok(open((madeBy(0) + IN_LEG / 2) / 1000) > 1,
            "a crate shut while its symbol was still rising out of it");
  assert.equal(open(c.dur), 0, "a crate was left standing open");
});
