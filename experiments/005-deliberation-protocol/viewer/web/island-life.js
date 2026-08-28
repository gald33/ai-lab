/**
 * The island, moving. Ported from the delivered `island-anims.js`.
 *
 * **What that file is, and why this is not a copy of it.** Each of its clips
 * builds a diorama of its own -- its own patch of ground, its own three palms,
 * its own camera -- because it was a browser for looking at motion one clip at
 * a time. The motion is the part worth having; the scaffolding around it is a
 * preview stand. So the `update(t)` of each ambient clip is re-aimed here at
 * the nodes of the **real** island, which `island3d.js` names systematically
 * for exactly this.
 *
 * Seven of the nine ambient clips needed something the island did not have --
 * gulls, clouds, goats, hearth smoke, falling leaves, mooring ripples, more
 * than one surf ring -- so those are added here rather than in the model. The
 * model is what the island *is*; this is what happens on it.
 *
 * The tenth thing the design animated on a twelve-second loop is the daylight,
 * and that one is not on a loop of its own: the page already has a clock, the
 * sun already crosses the sky on it, and a second sun in the lighting keeping
 * its own time would be two days at once. `update()` takes the day's progress
 * and the light follows it.
 */

import * as THREE from "./vendor/three/three.module.js";
import { onMeadow, GRASS_Y, SAND_Y, SEA_Y } from "./island3d.js";

const clamp01 = (x) => Math.max(0, Math.min(1, x));
const rng = (s) => () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;

function mesh(geo, material, name, pos = [0, 0, 0], rot = [0, 0, 0], scale = null) {
  const m = new THREE.Mesh(geo, material);
  m.name = name;
  m.position.set(...pos);
  m.rotation.set(...rot);
  if (scale) m.scale.set(...scale);
  return m;
}

function gull(i) {
  const g = new THREE.Group();
  g.name = `gull_${i}`;
  const body = new THREE.MeshStandardMaterial({ color: 0xe8e2d4, roughness: 0.85 });
  g.add(mesh(new THREE.SphereGeometry(0.05, 12, 8), body, "body", [0, 0, 0], [0, 0, 0], [1.7, 0.8, 0.8]));
  const wing = new THREE.BoxGeometry(0.22, 0.012, 0.07);
  const l = mesh(wing, body, "wing_l", [0, 0.01, 0.07]);
  const r = mesh(wing, body, "wing_r", [0, 0.01, -0.07]);
  g.add(l, r);
  g.userData = { l, r };
  return g;
}

function goat(i) {
  const g = new THREE.Group();
  g.name = `goat_${i}`;
  const hide = new THREE.MeshStandardMaterial({ color: 0xd8cdb6, roughness: 0.9 });
  const horn = new THREE.MeshStandardMaterial({ color: 0x7a4a34, roughness: 0.9 });
  g.add(mesh(new THREE.CapsuleGeometry(0.07, 0.16, 8, 12), hide, "body", [0, 0.17, 0], [0, 0, Math.PI / 2]));
  const head = new THREE.Group();
  head.position.set(0.15, 0.2, 0);
  head.add(mesh(new THREE.SphereGeometry(0.055, 12, 10), hide, "head", [0, 0, 0], [0, 0, 0], [1.3, 1, 1]));
  head.add(mesh(new THREE.ConeGeometry(0.016, 0.06, 6), horn, "horn_a", [-0.03, 0.05, 0.025], [0, 0, -0.3]));
  head.add(mesh(new THREE.ConeGeometry(0.016, 0.06, 6), horn, "horn_b", [-0.03, 0.05, -0.025], [0, 0, -0.3]));
  g.add(head);
  const legs = [];
  for (let k = 0; k < 4; k++) {
    const leg = mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.16, 6), horn,
      `leg_${k}`, [(k < 2 ? 0.08 : -0.08), 0.08, (k % 2 ? 0.05 : -0.05)]);
    g.add(leg);
    legs.push(leg);
  }
  g.userData = { head, legs };
  return g;
}

function cloud(i, scale = 1) {
  const g = new THREE.Group();
  g.name = `cloud_${i}`;
  const m = new THREE.MeshStandardMaterial({
    color: 0xf2f5f6, roughness: 0.95, transparent: true, opacity: 0.92 });
  g.add(mesh(new THREE.SphereGeometry(0.3, 16, 12), m, "a", [0, 0, 0], [0, 0, 0], [1, 0.62, 1]));
  g.add(mesh(new THREE.SphereGeometry(0.22, 16, 12), m, "b", [0.3, -0.03, 0.06], [0, 0, 0], [1, 0.6, 1]));
  g.add(mesh(new THREE.SphereGeometry(0.18, 16, 12), m, "c", [-0.28, -0.04, -0.05], [0, 0, 0], [1, 0.62, 1]));
  g.scale.setScalar(scale);
  g.userData = { m };
  return g;
}

/**
 * A dolphin, side-on: it is only ever seen in silhouette against the water, so
 * it is built along +x and steered by `rotation.y` like the gulls are.
 */
function dolphin(i) {
  const g = new THREE.Group();
  g.name = `dolphin_${i}`;
  const skin = new THREE.MeshStandardMaterial({ color: 0x51707f, roughness: 0.35 });
  const belly = new THREE.MeshStandardMaterial({ color: 0xc8d4d8, roughness: 0.45 });
  //: Fusiform rather than a capsule: an ellipsoid for the head and shoulders
  //: with a cone tapering off the back of it. A capsule is a tube with two
  //: round ends and reads as a torpedo at any size -- the taper from a thick
  //: shoulder down to a thin peduncle is what says dolphin in silhouette, and
  //: silhouette is all there is at this scale.
  g.add(mesh(new THREE.SphereGeometry(0.1, 16, 12), skin, "body",
             [0.04, 0, 0], [0, 0, 0], [1.55, 0.9, 0.72]));
  g.add(mesh(new THREE.ConeGeometry(0.088, 0.3, 14), skin, "flank",
             [-0.09, 0, 0], [0, 0, Math.PI / 2], [1, 1, 0.74]));
  g.add(mesh(new THREE.SphereGeometry(0.075, 12, 10), belly, "belly",
             [0.03, -0.032, 0], [0, 0, 0], [1.5, 0.55, 0.66]));
  //: The beak is long and thin, and it is the whole difference between a
  //: dolphin and a fish at this size: the head is the only end of the
  //: silhouette a viewer can tell apart at forty pixels.
  g.add(mesh(new THREE.ConeGeometry(0.036, 0.17, 12), skin, "beak",
             [0.25, -0.012, 0], [0, 0, -Math.PI / 2], [1, 1, 0.8]));
  g.add(mesh(new THREE.ConeGeometry(0.045, 0.12, 4), skin, "dorsal",
             [-0.01, 0.075, 0], [0, Math.PI / 4, -0.8], [1, 1, 0.22]));
  g.add(mesh(new THREE.ConeGeometry(0.036, 0.11, 4), skin, "flipper",
             [0.08, -0.05, 0.04], [0.6, 0, 1.2], [1, 1, 0.2]));
  // The tail is its own group so the stroke swings the flukes and not the fish.
  const tail = new THREE.Group();
  tail.position.set(-0.22, 0, 0);
  tail.add(mesh(new THREE.ConeGeometry(0.028, 0.1, 6), skin, "peduncle",
                [-0.04, 0, 0], [0, 0, Math.PI / 2], [1, 1, 0.7]));
  //: Flat and horizontal -- flukes, not a fish's tail fin. A dolphin's tail is
  //: the one thing about it that is unmistakable from above.
  tail.add(mesh(new THREE.ConeGeometry(0.085, 0.14, 4), skin, "flukes",
                [-0.1, 0, 0], [Math.PI / 2, 0, Math.PI / 2], [1, 1, 0.13]));
  g.add(tail);
  g.userData = { tail };
  return g;
}

//: The island's own dimensions come from `island3d.js` rather than being
//: restated here: everything added on top has to land on the same ground the
//: model built, and two copies of the ground's height is one of them wrong.

/**
 * Put life on a built island, and return the thing that moves it.
 *
 * `update(t, ctx)` takes seconds and `{ day, lights }` -- `day` being how far
 * through the episode the page's own clock says it is, so the light and the
 * drawn sun cannot disagree about the time.
 */
export function enliven(island, { ground = null, seed = 20260825 } = {}) {
  //: How high the island is at a point, from the model that built it. Without
  //: it everything here would stand at one flat height, which is how the goats
  //: came to walk through the hill rather than over it.
  const high = ground ?? (() => GRASS_Y);
  const r = rng(seed);
  const parts = [];
  const named = (re) => {
    const out = [];
    island.traverse((n) => { if (re.test(n.name)) out.push(n); });
    return out;
  };

  // — surf, which the model has one ring of —
  const surf = island.getObjectByName("surf_ring");
  const rings = surf ? [surf, ...[1, 2].map((i) => {
    const c = surf.clone();
    c.name = `surf_ring_${i}`;
    c.material = surf.material.clone();
    c.material.transparent = true;
    island.add(c);
    return c;
  })] : [];
  //: **The surf was scaled on the wrong axes and stopped being the coast.**
  //: `shoreRing` in `island3d.js` sweeps the shore's own silhouette in the xz
  //: plane and then lies it down on the water with `scale.y = 0.5`; the swell
  //: here has to grow that ring outward, which is x and z together. It read
  //: `scale.set(s, s, 0.5)` -- so the growth went onto **y**, where a
  //: half-height tube only got taller, and **z** was pinned at 0.5, squashing
  //: the outline to half its depth along one world axis. The white water was
  //: therefore an ellipse over an island that is not one: reported by eye as
  //: the swell not being shaped like the island, and visible worst on the
  //: bearings where the coast's wobble runs along z.
  //:
  //: The flattening belongs to the mesh and is already set once, at build
  //: time; this only ever wanted the radial term.
  if (rings.length) {
    rings[0].material = rings[0].material.clone();
    rings[0].material.transparent = true;
    parts.push((t) => rings.forEach((ring, i) => {
      const p = ((t / 4.2) + i / rings.length) % 1;
      const s = 0.98 + p * 0.09;
      ring.scale.set(s, 0.5, s);
      ring.material.opacity = 0.9 * Math.sin(Math.PI * p) ** 0.7;
      //: The ring's own resting height, set where the water was
      //: measured -- see `shoreRing`. A constant here is a second
      //: opinion about where the sea is, and it was the wrong one.
      ring.position.y = ring.userData.restY + Math.sin(p * Math.PI) * 0.02;
    }));
  }

  //: **The open sea used to be a flat blue disc.** Sixteen units of it, one
  //: colour, perfectly still, with all the motion in the picture crowded into
  //: the two surf rings at the shore -- so the island read as sitting on a
  //: painted floor, and the further from the coast a pixel was the more
  //: obviously it was not water. The swell is that disc's surface: an annulus
  //: starting clear of the shallows, displaced by three sine trains crossing
  //: at different bearings and speeds, with the normals recomputed so the
  //: crests actually take the day's light and go gold with it at the bell.
  //:
  //: It is a *surface over* the deep disc rather than a replacement for it:
  //: the disc still covers the corners of any window, and this only has to
  //: reach as far as the camera ever frames. Transparent, so the deep colour
  //: is what shows through the troughs -- and so a dolphin under it is a shape
  //: in the water rather than nothing at all.

  //: **The inner edge is a circle and the coast is not**, which is the same
  //: mistake the surf ring was rebuilt to fix -- see `shoreRing` in
  //: `island3d.js`. At 4.4 the sheet cleared the drawn shallows on three
  //: quarters of the bearings and fell *outside* them on the rest: on those,
  //: an annulus up to 0.44 wide had neither the shallows above it nor the
  //: sheet under it, so the deep disc at y = -0.30 showed through as a step
  //: in the water a little way off the sand. Reported by eye as the waves
  //: near the shore looking wrong.
  //:
  //: The narrowest the drawn shallows ever get is 3.96, so an inner edge at
  //: 3.86 is tucked under them on every bearing and the gap cannot open. The
  //: sheet under the island is hidden by the slabs above it, which is what
  //: "tucked" has always meant here.
  const swellGeo = new THREE.RingGeometry(3.86, 17, 128, 16);
  swellGeo.rotateX(-Math.PI / 2);
  const swellRest = swellGeo.attributes.position.array.slice();
  const swell = mesh(swellGeo, new THREE.MeshStandardMaterial({
    color: 0x2d5d79, roughness: 0.3, metalness: 0.06,
    transparent: true, opacity: 0.9, side: THREE.DoubleSide }), "swell",
    [0, SEA_Y, 0]);
  //: Same reason the deep disc neither casts nor receives: water in a shadow
  //: map this wide is the flickering rectangle all over again.
  swell.castShadow = false;
  swell.receiveShadow = false;
  island.add(swell);
  //: How high the water is at a point, for anything that has to float, swim or
  //: break the surface. One definition of the sea, read by everyone who needs
  //: it -- two copies of this is one of them out of phase with the water.
  const seaAt = (x, z, t) =>
    SEA_Y + fade(x, z) * (Math.sin(x * 0.62 + t * 0.85) * 0.07
                          + Math.sin(z * 0.48 - t * 0.62) * 0.058
                          + Math.sin((x + z) * 0.95 + t * 1.35) * 0.03);
  //: Flat where it meets the shore and full height out at sea: swell running
  //: up under the surf rings would put the open ocean over the beach. The
  //: sheet's inner edge is tucked *under* the shallows slab rather than left
  //: in the gap beside it, so there is no seam between the two to catch.
  function fade(x, z) {
    return clamp01((Math.hypot(x, z) - 4.75) / 1.9);
  }
  parts.push((t) => {
    const pos = swellGeo.attributes.position;
    const a = pos.array;
    for (let i = 0; i < a.length; i += 3) {
      a[i + 1] = seaAt(swellRest[i], swellRest[i + 2], t) - SEA_Y;
    }
    pos.needsUpdate = true;
    //: Without this the crests are lit as though the sheet were still flat,
    //: which is a flat blue disc that happens to have bumps in its outline.
    swellGeo.computeVertexNormals();
  });

  // — dolphins, once in a while, out past the surf —
  //
  //: **Occasional, and that is the whole design.** A pod circling the island
  //: all day is scenery and stops being seen by the second minute; a pod that
  //: crosses the frame every so often and is gone is something a spectator
  //: catches. So a pass is a chord across the open water lasting `PASS`
  //: seconds out of every `POD_CYCLE`, on a bearing that is different each
  //: time round, and between passes the pod is not in the scene at all.
  //:
  //: They porpoise rather than swim flat: the arc out of the water and back
  //: into it is the read, and the pitch follows the arc's own slope rather
  //: than being animated separately, so a dolphin never enters the water nose
  //: up. Below the surface they stay drawn -- the swell is transparent, and a
  //: shape moving under the water between leaps is what joins one leap to the
  //: next.
  const POD_CYCLE = 52, PASS = 13, POD_R = 5.8;
  const pod = [0, 1, 2].map((i) => {
    const d = dolphin(i);
    d.visible = false;
    island.add(d);
    // Strung out along the line of travel and offset across it, so they read
    // as a pod travelling together rather than as one dolphin drawn three
    // times; the phase offset is what makes them break the surface in turn.
    return { d, lag: i * 0.055, across: (i - 1) * 0.55, ph: i * 0.42,
             size: 1 - i * 0.12 };
  });
  parts.push((t) => {
    const cycle = Math.floor(t / POD_CYCLE);
    const u = (t % POD_CYCLE) / PASS;
    if (u > 1) { pod.forEach(({ d }) => { d.visible = false; }); return; }
    //: A different bearing every cycle, from the cycle number rather than from
    //: `Math.random()`: the island is seeded, and a pass that cannot be
    //: reproduced cannot be looked at twice.
    const bearing = (cycle * 2.399963) % (Math.PI * 2);
    const cos = Math.cos(bearing), sin = Math.sin(bearing);
    pod.forEach(({ d, lag, across, ph, size }) => {
      const p = clamp01(u - lag);
      d.visible = p > 0 && p < 1;
      if (!d.visible) return;
      // Along the chord, and offset across it. The chord passes at POD_R from
      // the middle of the island -- a little over a unit outside the surf
      // ring, so the pod is in open water and still inside the frame on the
      // narrowest window this page is framed for.
      const along = -11 + p * 22;
      const off = POD_R + across;
      const x = cos * along - sin * off;
      const z = sin * along + cos * off;
      // One leap per LEAP seconds of the pass, as a raised sine: above zero it
      // is out of the water, below it the dolphin is under it.
      const LEAP = 2.6;
      const leap = Math.sin(((t / LEAP) + ph) * Math.PI * 2);
      const rise = leap > 0 ? leap ** 0.85 : leap * 0.35;
      const sea = seaAt(x, z, t);
      d.position.set(x, sea + rise * 0.5 + 0.02, z);
      //: A dolphin is built along +x, and `rotation.y` of `-bearing` is what
      //: sends that axis along the chord: the gulls' `-a + PI/2` is a *tangent*
      //: to a circle and putting it here swam the pod broadside, nose to the
      //: camera, for a whole pass.
      d.rotation.y = -bearing;
      // The slope of the arc it is on, so the nose leads.
      d.rotation.z = Math.cos(((t / LEAP) + ph) * Math.PI * 2) * 0.85;
      d.userData.tail.rotation.z = Math.sin(t * 6 + ph) * 0.4;
      // Small at both ends of the pass and full size across the middle of it,
      // so a dolphin is never seen to appear: with no perspective to shrink
      // one, coming up the chord *is* how the pod arrives from far off.
      const near = Math.min(1, Math.min(p, 1 - p) * 6);
      d.scale.setScalar(size * (0.55 + near * 0.45));
    });
  });

  // — palms in the wind —
  const palms = named(/^palm_\d+$/).map((p, i) => ({
    p, fronds: p.children.filter((o) => o.name.includes("frond")), ph: i * 1.7 }));
  if (palms.length) {
    parts.push((t) => palms.forEach(({ p, fronds, ph }) => {
      const gust = Math.sin(t * 1.15 + ph) * 0.5 + Math.sin(t * 2.7 + ph) * 0.18;
      p.rotation.z = gust * 0.075;
      p.rotation.x = Math.cos(t * 0.9 + ph) * 0.03;
      fronds.forEach((f, k) => {
        f.rotation.z = Math.sin(t * 2.4 + ph + k) * 0.16;
        f.scale.y = 0.22 + Math.sin(t * 3.1 + k * 1.3) * 0.03;
      });
    }));
  }

  // — canopies, and leaves coming off them —
  const canopies = named(/^tree_\d+_canopy/);
  if (canopies.length) {
    parts.push((t) => canopies.forEach((cn, i) => {
      const s = 1 + Math.sin(t * 1.4 + i * 0.8) * 0.025;
      cn.scale.set(s, cn.name.includes("canopy_a") ? 0.8 * s : s, s);
      cn.rotation.z = Math.sin(t * 1.1 + i) * 0.03;
    }));
    const trees = named(/^tree_\d+$/);
    const leafGeo = new THREE.PlaneGeometry(0.05, 0.035);
    const leaves = Array.from({ length: 14 }, (_, i) => {
      const host = trees[i % Math.max(1, trees.length)];
      const m = new THREE.MeshStandardMaterial({
        color: i % 3 ? 0x55803f : 0x3f6330, roughness: 0.9,
        transparent: true, side: THREE.DoubleSide });
      const l = mesh(leafGeo, m, `leaf_${i}`);
      island.add(l);
      return { l, m, at: host ? host.position : new THREE.Vector3(),
               ph: r(), spin: 2 + r() * 3, drift: (r() - 0.5) * 0.5 };
    });
    parts.push((t) => leaves.forEach(({ l, m, at, ph, spin, drift }) => {
      const p = ((t / 6) + ph) % 1;
      // Off its own tree and down to its own tree's ground, not to the
      // meadow's: a tree on the upland drops its leaves onto the upland.
      l.position.set(at.x + Math.sin(p * 7 + ph * 6) * 0.12 + drift * p,
                     at.y + 0.97 - p * 0.9,
                     at.z + drift * p * 0.6);
      l.rotation.set(p * spin * 3, p * spin * 2, p * spin);
      m.opacity = Math.min(1, (1 - p) * 3.2);
    }));
  }

  // — gulls over the water —
  const birds = [0, 1, 2].map((i) => {
    const b = gull(i);
    b.scale.setScalar(1.1 - i * 0.15);
    island.add(b);
    // Height has to be bought with screen position. An orthographic camera
    // gives no perspective cue for it, and the tilt maps a unit of world
    // height to about 0.65 of a unit up the screen -- so low fliers read as
    // something dropped on the grass, and the first correction put them off
    // the top of the frame entirely. This clears the island and stays in it.
    // Out over the water, not over the meadow. Height alone will not sell a
    // bird here -- with no perspective a gull above the grass just looks like
    // something lying on it -- but a gull over the sea has nothing behind it
    // to be mistaken for.
    return { b, ph: i * 2.3, rad: 5.0 + i * 0.45, h: 2.6 + i * 0.3 };
  });
  parts.push((t) => birds.forEach(({ b, ph, rad, h }) => {
    const a = t * 0.32 + ph;
    b.position.set(Math.cos(a) * rad, h + Math.sin(t * 0.9 + ph) * 0.12, Math.sin(a) * rad);
    b.rotation.y = -a + Math.PI / 2;
    b.rotation.z = Math.sin(a * 2) * 0.1;
    const flap = Math.sin(t * 7 + ph) * 0.55;
    b.userData.l.rotation.x = flap;
    b.userData.r.rotation.x = -flap;
  }));

  //: **How much sun there is to cast anything**, on the day's own clock: 1
  //: through the middle of the day, 0 for the first and last of it. Anything
  //: that only exists because the sun is high reads this rather than `day`,
  //: because "the sun is up" and "it is late" are not the same curve -- the
  //: sun is up at dawn too, and casts almost nothing.
  //:
  //: 1 until the page says otherwise, so a board with no clock on it keeps the
  //: island it already had rather than losing half of it to a missing number.
  let sunUp = 1;

  // — clouds, and their shadows crossing the meadow —
  const shadowMat = new THREE.MeshStandardMaterial({
    color: 0x3f6330, roughness: 1, transparent: true, opacity: 0.34 });
  const clouds = [1.25, 0.9, 1.05].map((s, i) => {
    const cl = cloud(i, s);
    island.add(cl);
    const sh = mesh(new THREE.CircleGeometry(0.5 * s, 24), shadowMat.clone(),
      `cloud_shadow_${i}`, [0, GRASS_Y + 0.02, 0], [-Math.PI / 2, 0, 0]);
    island.add(sh);
    // Same reason as the gulls, and a little higher: a cloud below this crosses
    // the island rather than the sky over it.
    return { cl, sh, ph: i / 3, z: -1.4 + i * 1.5, h: 4.5 + i * 0.45 };
  });
  parts.push((t) => clouds.forEach(({ cl, sh, ph, z, h }) => {
    const p = ((t / 22) + ph) % 1;
    const x = -6.4 + p * 12.8;
    cl.position.set(x, h, z);
    cl.userData.m.opacity = 0.9 * clamp01(Math.sin(Math.PI * p) * 2.2);
    const sx = x * 0.72, sz = z * 0.85;
    sh.position.set(sx, high(sx, sz) + 0.03, sz);
    //: **Gone by dusk.** A shadow is the sun being blocked, so a hard dark
    //: patch crossing the meadow at the bell -- while the key has swung almost
    //: to the horizon and every other shadow on the island has gone long and
    //: soft -- is the one thing on screen still claiming it is noon. It fades
    //: out with the light and comes back with it.
    sh.material.opacity = 0.26 * clamp01(Math.sin(Math.PI * p) * 1.8)
      * (Math.hypot(x * 0.72, z * 0.85) < 3.0 ? 1 : 0.15) * sunUp;
  }));

  // — goats, on the meadow and out of everyone's way —
  //
  //: **A goat is the slowest thing on the island.** The clip ran its wander on
  //: a diorama a metre across, and the same numbers on the real island sent
  //: them at about a body length a second across a meadow six wide -- reading
  //: as a chase, not a graze. `WANDER` is the seconds of one amble-and-graze
  //: cycle and `ARC` how far round its little circuit a goat gets in one, and
  //: between them they set the speed: a body length now takes some seconds.
  const WANDER = 26, ARC = 1.7;
  const herd = [0, 1].map((i) => {
    const a = goat(i);
    a.scale.setScalar(1.15 - i * 0.15);
    island.add(a);
    // Their circuits are kept small and their centres well inside the grass:
    // wandering off the beach and out over the water was the other half of
    // running the diorama's numbers at island scale.
    return { a, ph: i * 3.6, rad: 0.62 - i * 0.1, about: i ? [1.15, -1.35] : [-1.3, -1.1] };
  });
  parts.push((t) => herd.forEach(({ a, ph, rad, about }) => {
    const cyc = ((t + ph) % WANDER) / WANDER;
    // Out, graze, back, graze. The clip walked one way and snapped to its
    // start when the loop came round, which at island scale is a goat
    // teleporting a metre every time the cycle turns over; a circuit that
    // closes has no seam in it.
    const leg = cyc < 0.4 ? cyc / 0.4
      : cyc < 0.5 ? 1
      : cyc < 0.9 ? 1 - (cyc - 0.5) / 0.4
      : 0;
    const walking = cyc < 0.4 || (cyc >= 0.5 && cyc < 0.9);
    const back = cyc >= 0.5 && cyc < 0.9;
    const ang = ph + leg * ARC;
    // Clamped even so, so that a change to the numbers above can make a goat
    // wander somewhere silly but never into the sea.
    const [x, z] = onMeadow(about[0] + Math.cos(ang) * rad,
                            about[1] + Math.sin(ang) * rad, 0.25);
    a.position.set(x, high(x, z), z);
    a.rotation.y = -ang + Math.PI / 2 + 1.57 + (back ? Math.PI : 0);
    // The legs swing with the walk rather than at a rate of their own: at the
    // old eight radians a second a goat this slow was pedalling on the spot.
    const pace = (ARC * rad) / (WANDER * 0.4);
    a.userData.legs.forEach((l, i) => {
      l.rotation.x = walking ? Math.sin(t * pace * 26 + i * 1.6) * 0.4 : 0;
    });
    const graze = walking ? 0
      : Math.sin((cyc < 0.5 ? (cyc - 0.4) : (cyc - 0.9)) / 0.1 * Math.PI);
    a.userData.head.rotation.z = -graze * 0.95;
    a.userData.head.position.y = 0.2 - graze * 0.07;
  }));

  // — hearth smoke, one column per settlement —
  const smokeMat = new THREE.MeshStandardMaterial({
    color: 0xd7dcde, roughness: 1, transparent: true, opacity: 0.5 });
  const chimneys = named(/^settlement_/).flatMap((s, si) =>
    Array.from({ length: 6 }, (_, i) => {
      const p = mesh(new THREE.SphereGeometry(0.05, 12, 10), smokeMat.clone(), `smoke_${si}_${i}`);
      island.add(p);
      return { p, at: s.position, ph: i / 6, sway: i % 2 ? 1 : -1 };
    }));
  parts.push((t) => chimneys.forEach(({ p, at, ph, sway }) => {
    const k = ((t / 5.5) + ph) % 1;
    p.position.set(at.x + Math.sin(k * 4 + ph * 6) * 0.12 * sway,
                   at.y + 1.25 + k * 1.0,
                   at.z + Math.cos(k * 3) * 0.07);
    p.scale.setScalar(0.5 + k * 2.3);
    p.material.opacity = 0.4 * (1 - k) ** 1.4;
  }));

  // — the boats at their moorings —
  //: Found by name across the island rather than off the dock's child list.
  //: They were children of the jetty and are not any more -- a boat a side is
  //: all a 0.7-wide deck can take, so they moor along the shore now -- and a
  //: lookup through `dock` silently returned none of them, which is a bob
  //: that quietly stops rather than an error anyone would see.
  const boats = [];
  island.traverse((o) => { if (/^boat_\d+$/.test(o.name)) boats.push(o); });
  const bobbing = boats.map((b, i) => ({ b, ph: i * 2.1, y0: b.position.y }));
  if (bobbing.length) {
    parts.push((t) => bobbing.forEach(({ b, ph, y0 }) => {
      b.position.y = y0 + Math.sin(t * 1.5 + ph) * 0.035;
      b.rotation.z = Math.sin(t * 1.2 + ph) * 0.07;
      b.rotation.x = Math.cos(t * 1.7 + ph) * 0.04;
    }));
  }

  // — the fire at the centre, which is the point of the middle of the island —
  //
  //: It burns low all day and comes up as the light goes, so by the bell it is
  //: the brightest thing left. A `PointLight` with it, because a fire that
  //: glows and throws nothing on the ground beside it reads as a decal.
  const flames = [0, 1, 2].map((i) => island.getObjectByName(`flame_${i}`))
    .filter(Boolean).map((f) => ({ f, y0: f.position.y, s0: f.scale.y }));
  const hearth = island.getObjectByName("fire");
  //: **A pool, not a floodlight.** This was `(0xff9a3c, 0, 4.2, 2)` and the
  //: bell drove it to 5.5, which at half a unit is nearly three times as much
  //: light as the island gets at midday -- and firelight is orange while the
  //: island is green, so what the near field actually did was beat the
  //: material's green channel down until the grass, the trees standing in it
  //: and the hill the fire stands on all came out olive. Reported by eye,
  //: twice, as the trees and the hill going yellow.
  //:
  //: It is not the colour that was wrong: a fire is orange and the ground
  //: beside a fire is warm. It is the reach. At 2.4 units and 1.2 the pool
  //: covers the hearth and its clearing, never out-shines the day, and is back
  //: to leaf-green by the foot of the hill. Measured in
  //: `viewer/tests/firelight.test.mjs`, which is the reproduction:
  //: `node --test viewer/tests/firelight.test.mjs`.
  const glow = new THREE.PointLight(0xff9a3c, 0, 2.4, 2);
  if (hearth) {
    //: Just above the flames, which are shorter than they were.
    glow.position.copy(hearth.position).setY(hearth.position.y + 0.22);
    island.add(glow);
  }

  // — the fireflies, which are only out after dark —
  //
  //: The one thing on the island a spectator gets for waiting. They are over
  //: the meadow, not the sea or the sand, and they are nothing at midday: a
  //: firefly visible in daylight is a bright dot, which on this island already
  //: means a good in flight.
  //:
  //: **And never over the fire.** They were seeded on a ring about the
  //: island's centre, which the fire is very nearly at, so the densest part of
  //: the swarm hung in the smoke -- and against flames that are themselves
  //: small warm dots, a firefly beside them is not a firefly, it is a spark
  //: coming off the fire. `CLEAR` is the fire's own clearing (0.63) plus the
  //: widest drift below, so no firefly wanders back over it either.
  const hearthAt = hearth ? hearth.position : new THREE.Vector3(0, 0, 0);
  const CLEAR = 1.5;
  const sparks = Array.from({ length: 26 }, (_, i) => {
    const m = new THREE.Mesh(
      new THREE.SphereGeometry(0.035, 8, 6),
      new THREE.MeshStandardMaterial({ color: 0xfff0a8, emissive: 0xffd24a,
        emissiveIntensity: 0, transparent: true, opacity: 0 }));
    m.name = `firefly_${i}`;
    const a = (i / 26) * Math.PI * 2 * 3.7 + 0.4;
    const rad = 1.5 + ((i * 37) % 100) / 100 * 1.7;
    let px = Math.cos(a) * rad, pz = Math.sin(a) * rad;
    //: Pushed straight out from the fire rather than re-drawn, so the swarm
    //: keeps the spread it was seeded with and only the near ones move.
    const dx = px - hearthAt.x, dz = pz - hearthAt.z;
    const d = Math.hypot(dx, dz);
    if (d < CLEAR) {
      const [ux, uz] = d > 1e-6 ? [dx / d, dz / d] : [Math.cos(a), Math.sin(a)];
      px = hearthAt.x + ux * CLEAR;
      pz = hearthAt.z + uz * CLEAR;
    }
    const [x, z] = onMeadow(px, pz, 0.5);
    m.position.set(x, ground(x, z) + 0.35, z);
    island.add(m);
    return { m, x, z, base: ground(x, z), phase: i * 1.37, drift: 0.35 + (i % 5) * 0.08 };
  });

  parts.push((t) => {
    for (const { m, x, z, base, phase, drift } of sparks) {
      m.position.x = x + Math.sin(t * 0.5 + phase) * drift;
      m.position.z = z + Math.cos(t * 0.37 + phase * 1.6) * drift;
      m.position.y = base + 0.32 + Math.sin(t * 0.9 + phase * 2.1) * 0.16;
    }
  });

  //: A little more saturated than they were (0xffb07a and 0xd9603a). The
  //: ramp below is unchanged and stays linear in `lit`, so this is the whole
  //: of the change: the ends of the day are the same shape of day, in a
  //: slightly stronger colour. See the note under the sky colours for why the
  //: warmth is the key's and nothing else's.
  //:
  //: **These lights are deliberately not on `burnAt`.** `scene.js` has a
  //: curve -- flat through the middle of the day, all of it in the last
  //: quarter at each end -- and the drawn island's burn reads it. Running the
  //: lights off it too was tried, to stop a warm ambient tinting the whole
  //: day. The reason evaporated: the ambient below is *cool* now (see the
  //: note under the sky colours), so there is nothing bleeding across the day
  //: to hold back, and all a flat-middle curve does to the lights is hold
  //: them at noon for half the day. The distinction worth keeping is that the
  //: day's light is continuous while the sky's *colour wash* is an
  //: end-of-day event, so one curve does not fit both.
  const dawn = new THREE.Color(0xffa15c);
  const noon = new THREE.Color(0xfff6e2);
  const dusk = new THREE.Color(0xdd5c33);
  // The sky the key is under, which has to travel with it. Moving the key
  // alone does not make a sunset: by the bell the key comes in almost
  // horizontally and lights nothing the camera can see, so the island's colour
  // is whatever the ambient and the fill say it is -- and a cool ambient held
  // fixed makes the last light of the day read *bluer* than midday, which is
  // the one thing dusk is not.
  //
  //: **But the warmth is the key's, not the ambient's**, and putting it in
  //: the ambient is what turned the trees and the hill yellow. The ambient
  //: reaches every face, including the ones the low sun has stopped touching,
  //: so a warm mauve ambient (`0xa08a90`, and `0xd8c2c6` at dawn) multiplied
  //: the island's green by an orange nothing was casting: measured over the
  //: rendered grass -- meadow, upland, ridge, canopies, fronds -- 60% of it
  //: came out on the yellow side of 90 degrees at `day` 0.95, against 0% for
  //: the whole middle of the day. That is the report, and it is why the
  //: campfire's reach (which is real, and was fixed first) was not the end of
  //: it.
  //:
  //: Twilight is a cool sky with one warm light in it. The key keeps its
  //: sunset colour and the ambient goes to what the sky over an island
  //: actually is at that hour, so the warmth in the picture is what the sun
  //: is still touching. The sand still reads warm (hue ~22 at `day` 0.95) and
  //: the grass comes back to a leaf. Measured on the rendered pixels by
  //: `twilight` in `viewer/tests/render.py`, which is the reproduction:
  //: `python viewer/tests/render.py`.
  const skyDawn = new THREE.Color(0xb3bccb);
  const skyNoon = new THREE.Color(0xbcd2dd);
  const skyDusk = new THREE.Color(0x8497b0);
  //: The far side of the sky, which the fill stands in for. Cyan while the sea
  //: is bright, deep indigo once the sun is down -- and **not** dimmed to
  //: nothing, because by then the key grazes the island and lights almost
  //: nothing the camera can see. Something has to keep the shaded faces darker
  //: than the lit ones or dusk arrives as a flat orange wash with no island
  //: left in it.
  //: **What the water outside the picture is, at this hour.**
  //:
  //: The renderer draws into the letterboxed rectangle the `<svg>` fits its
  //: viewBox into, and the bands beside or above that rectangle are not drawn
  //: at all -- so however wide the sea disc is, the frame ends in the page's
  //: own dark backing. That is the void a spectator asked to be rid of. The
  //: bands cannot be *rendered* into without breaking the mapping that puts a
  //: hut under its card, so they are **cleared to the sea's own colour**
  //: instead, and this is that colour: the deep water's material as this
  //: hour's light leaves it, so the band and the water inside the frame are
  //: the same blue and the join does not show. It goes down with the light
  //: like everything else.
  const deep = new THREE.Color(0x244a63);
  const water = new THREE.Color(0x244a63);
  const seaDay = new THREE.Color(0x6fa6c8);
  const seaDusk = new THREE.Color(0x3c4a7a);

  //: How much a clip is adding to the fire on top of the day's own value.
  //: **An event may make the fire flare and that has to move the light**, not
  //: just the cones: three flames are a few hundred pixels on an island eight
  //: units across, and a fire that brightens without lighting the ground round
  //: it is a decal. The day owns the base level and this is added to it, so a
  //: clip never fights the clock -- it leans on it and lets go.
  let flare = 0;
  //: How far into night a clip is holding the light, or `null` for "the day's
  //: own clock". **The bell is nightfall and the dawn is the light coming
  //: back**, and both were previously only a prop moving: the sun going down
  //: is the page's clock, so at a bell the island snapped to dusk and the clip
  //: rang a bell the size of a plum beside it. This lets the two clips carry
  //: the light itself, which is the largest thing either of them is about.
  let held = null;
  //: **Whether this island has ever been told the time.**
  //:
  //: `day === null` means "the page cannot read this board's clock", and the
  //: rule for it is to leave the light where it is -- not knowing the hour is
  //: not the same as it being dawn, and a live board that drops a poll should
  //: not flicker to morning and back.
  //:
  //: That rule is right *within* a round and was wrong *across* one. The key,
  //: the ambient and the fill belong to the stage and outlive the island: a
  //: round watched to its bell leaves them at dusk, and the next round built
  //: on top of them inherits that dusk and holds it, for every frame, if its
  //: own clock is one this page cannot read. Reported as a second replay whose
  //: daylight never changed, on a board that was dark from the first frame to
  //: the last.
  //:
  //: So the hold only applies once there is something to hold. An island that
  //: has never had an hour gets the middle of the day, which is the honest
  //: reading of "this board does not say" and is what the drawn island did
  //: before there was a clock at all.
  let told = false;
  //: The last hour the page's own clock gave, which is what the shadows point
  //: at. `null` until an island is told one. Kept apart from the light level
  //: so that a clip holding a night does not also move the sun -- see
  //: `update`.
  let hour = null;
  const NOON = 0.42;

  return {
    /**
     * A clip's own contribution to the fire and to the light, for **this frame
     * only**.
     *
     * Consumed by the next `update` and reset. A clip sets them every frame it
     * runs, so one that ends -- or is cut off half way, or is thrown away with
     * the island under it -- stops contributing by not saying anything, and
     * there is no state left holding the island at midnight because a restore
     * did not run. That was the first shape of this and it left the whole
     * island dark after a bell.
     */
    flare(v) { flare = v; },
    hold(v) { held = v; },

    /** The sea's colour at this hour, for whatever has to paint water. */
    water,

    /**
     * @param {number} t     seconds, for anything on its own rhythm
     * @param {object} ctx   `{ day, key, ambient }` -- `day` from the page's
     *                       clock, so the light and the drawn sun agree.
     */
    update(t, { day = null, turn = 0, key = null, ambient = null,
                fill = null } = {}) {
      //: **A hold is a level of night, not a time of day.**
      //:
      //: A clip holding the light wins over the clock and never goes backwards
      //: from it: at a real bell the page has already put the day at dusk, and
      //: a clip that pulled it back would fight its own page. But `hold` used
      //: to *be* the day for as long as it ran, and the day owns the key's
      //: bearing as well as its brightness -- so the dawn clip, which holds a
      //: night that is lifting (`1` down to `0` over four seconds), dragged the
      //: sun backwards through a whole day and swept every shadow across the
      //: island at the moment a new day opened. Reported as shadows crossing
      //: the island at the start of a day, in the dark.
      //:
      //: So the hold is spent on the light *level* -- how bright, how warm,
      //: how high the fire -- and the bearing stays on the clock. The bell
      //: loses nothing by it: the day is already at dusk when it rings, so the
      //: shadow is where the hold would have put it anyway. The dawn gains the
      //: thing the drawn sun has always had -- a jump, made under cover of the
      //: night that is still being drawn over it, rather than a rewind.
      let lit = day;
      if (held !== null) lit = day === null ? held : Math.max(day, held);
      const lift = flare;
      // Spent. Whoever wants them next frame has to ask again.
      held = null;
      flare = 0;
      //: **Resolved before the parts run, and the parts run either way.** The
      //: loose animations are the island being alive and none of them need a
      //: clock -- gulls, goats, boats keep going on a board that never said
      //: what time it is -- but the one that does read the sun has to read
      //: *this* frame's, not the last one's, or a bell leaves a shadow behind
      //: for a frame.
      if (lit === null && !told) lit = NOON;
      if (lit !== null) {
        told = true;
        sunUp = clamp01((Math.sin(Math.PI * clamp01(lit)) - 0.1) / 0.45);
      }
      //: The hour the shadows point at. Only the clock moves it, and a frame
      //: whose clock has gone quiet keeps the last one -- a dropped poll is
      //: not an island turning back to morning.
      if (day !== null) hour = clamp01(day);
      for (const part of parts) part(t);
      if (lit === null) return;
      lit = clamp01(lit);
      const bear = hour === null ? lit : hour;
      // The sun's own arc, not a twelve-second loop: dawn in the east, highest
      // at midday, and down in the west by the bell.
      const a = Math.PI * (0.08 + lit * 0.84);
      if (key) {
        /*
         * Where the light stands, **reckoned from the camera and not from the
         * island**.
         *
         * The island's shadows are what tells a viewer the time now -- the
         * drawn sun is hidden the moment there is a model to light -- and the
         * camera goes right round the island every hundred and fifty seconds.
         * A key at a fixed world bearing would hold its shadow due north-west
         * all day and let the camera sweep it across the frame, so the shadow
         * a person sees would be reading the bearing rather than the hour.
         *
         * So the day owns the angle *to the camera*: the light comes over one
         * shoulder at the open, stands behind the viewer and high at midday --
         * where the shadows are shortest, which is the other half of what a
         * time of day looks like -- and is over the far shoulder and long by
         * the bell. `turn` is the camera's own bearing and is added straight
         * back in, which is what cancels the revolution.
         */
        const swing = turn + (0.5 - bear) * 2.2;
        const high = 1.1 + Math.sin(Math.PI * bear) * 8.0;
        key.position.set(Math.sin(swing) * 7.5, high, Math.cos(swing) * 7.5);
        // A floor under it: the island still has to be readable at dusk, and
        // the cards standing on it are the part that matters most then.
        key.intensity = 0.75 + Math.sin(a) * 1.55;
        key.color.copy(lit < 0.5 ? dawn.clone().lerp(noon, lit / 0.5)
                                 : noon.clone().lerp(dusk, (lit - 0.5) / 0.5));
      }
      if (ambient) {
        ambient.intensity = 0.62 + Math.sin(a) * 0.7;
        ambient.color.copy(lit < 0.5 ? skyDawn.clone().lerp(skyNoon, lit / 0.5)
                                     : skyNoon.clone().lerp(skyDusk, (lit - 0.5) / 0.5));
      }
      if (fill) {
        fill.intensity = 0.75 * (0.55 + Math.sin(a) * 0.45);
        fill.color.copy(lit < 0.5 ? seaDusk.clone().lerp(seaDay, lit / 0.5)
                                  : seaDay.clone().lerp(seaDusk, (lit - 0.5) / 0.5));
      }
      //: The same sum the renderer does for a flat surface facing up, done
      //: once: the material's colour under the ambient, plus what the key and
      //: the fill add at the angle they arrive from. It is an approximation --
      //: the check that keeps it honest compares this band against a rendered
      //: sea pixel a few pixels inside the frame, so it cannot drift far
      //: without being caught.
      if (ambient && key && fill) {
        water.copy(deep).multiply(ambient.color).multiplyScalar(ambient.intensity);
        water.add(deep.clone().multiply(key.color)
          .multiplyScalar(key.intensity * Math.max(0, Math.sin(a)) * 0.42));
        water.add(deep.clone().multiply(fill.color).multiplyScalar(fill.intensity * 0.3));
        water.r = Math.min(1, water.r);
        water.g = Math.min(1, water.g);
        water.b = Math.min(1, water.b);
      }
      //: **The fire is the bell, so it does not light at lunchtime.**
      //:
      //: It used to rise from `0.52` and stand at full by `0.82` -- from just
      //: past midday, and full while the island was still producing and still
      //: settling trades, which is exactly what a spectator reported seeing.
      //: The viewer's own glossary says the bell *is* nightfall and the
      //: campfire taking over, and a fire lit halfway through the day says the
      //: day is ending when it is not. Decided by Gal, 2026-08-27; the
      //: reasoning is in `viewer/README.md`, "The fire is the bell".
      //:
      //: It is still banked all day -- the embers are the `0.35` floor below --
      //: and still comes up a little before the light has quite gone, which is
      //: what the last stretch of the day buys. Full is the bell itself, where
      //: the bell clip's own hold and flare carry it the rest of the way.
      const burn = clamp01(clamp01((lit - 0.86) / 0.14) + lift);
      for (const { f, y0, s0 } of flames) {
        f.material.emissiveIntensity = 0.35 + burn * 2.6;
        // Flicker, which is what makes a cone read as flame at all.
        const lick = 1 + Math.sin(t * 7.3 + y0 * 21) * 0.12 + Math.sin(t * 11.7) * 0.06;
        f.scale.set(0.8 + burn * 0.35, (0.7 + burn * 0.5) * lick * (s0 || 1), 0.8 + burn * 0.35);
        f.position.y = y0 + burn * 0.05;
      }
      glow.intensity = burn * 1.2 * (1 + Math.sin(t * 6.1) * 0.06);
      //: **Only after dark**, and out over the meadow. `night` runs a little
      //: behind the fire: the fire is built before the light goes and the
      //: fireflies come once it has.
      const night = clamp01((lit - 0.92) / 0.08);
      for (const { m } of sparks) {
        m.material.opacity = night * 0.95;
        m.material.emissiveIntensity = night * 2.4;
        m.visible = night > 0.02;
      }
    },
  };
}
