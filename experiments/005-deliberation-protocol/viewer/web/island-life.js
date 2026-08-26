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
import { onMeadow, GRASS_Y, SAND_Y } from "./island3d.js";

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
export function enliven(island, { seed = 20260825 } = {}) {
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
  if (rings.length) {
    rings[0].material = rings[0].material.clone();
    rings[0].material.transparent = true;
    parts.push((t) => rings.forEach((ring, i) => {
      const p = ((t / 4.2) + i / rings.length) % 1;
      const s = 0.98 + p * 0.09;
      ring.scale.set(s, s, 0.5);
      ring.material.opacity = 0.9 * Math.sin(Math.PI * p) ** 0.7;
      ring.position.y = 0.055 + Math.sin(p * Math.PI) * 0.02;
    }));
  }

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
      l.position.set(at.x + Math.sin(p * 7 + ph * 6) * 0.12 + drift * p,
                     GRASS_Y + 0.95 - p * 0.9,
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
    sh.position.set(x * 0.72, GRASS_Y + 0.02, z * 0.85);
    sh.material.opacity = 0.26 * clamp01(Math.sin(Math.PI * p) * 1.8)
      * (Math.hypot(x * 0.72, z * 0.85) < 3.0 ? 1 : 0.15);
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
    a.position.set(x, GRASS_Y, z);
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
  const dock = island.getObjectByName("dock");
  const boats = dock ? dock.children.filter((c) => /^boat_/.test(c.name)).map((b, i) => ({
    b, ph: i * 2.1, y0: b.position.y })) : [];
  if (boats.length) {
    parts.push((t) => boats.forEach(({ b, ph, y0 }) => {
      b.position.y = y0 + Math.sin(t * 1.5 + ph) * 0.035;
      b.rotation.z = Math.sin(t * 1.2 + ph) * 0.07;
      b.rotation.x = Math.cos(t * 1.7 + ph) * 0.04;
    }));
  }

  // — the lanterns, which come up as the day goes —
  const lanterns = named(/lantern$/).map((l) => {
    l.material = l.material.clone();
    return l;
  });

  const dawn = new THREE.Color(0xffb07a);
  const noon = new THREE.Color(0xfff6e2);
  const dusk = new THREE.Color(0xd9603a);
  // The sky the key is under, which has to travel with it. Moving the key
  // alone does not make a sunset: by the bell the key comes in almost
  // horizontally and lights nothing the camera can see, so the island's colour
  // is whatever the ambient and the fill say it is -- and a cool ambient held
  // fixed makes the last light of the day read *bluer* than midday, which is
  // the one thing dusk is not.
  const skyDawn = new THREE.Color(0xd8c2c6);
  const skyNoon = new THREE.Color(0xbcd2dd);
  const skyDusk = new THREE.Color(0xa08a90);
  //: The far side of the sky, which the fill stands in for. Cyan while the sea
  //: is bright, deep indigo once the sun is down -- and **not** dimmed to
  //: nothing, because by then the key grazes the island and lights almost
  //: nothing the camera can see. Something has to keep the shaded faces darker
  //: than the lit ones or dusk arrives as a flat orange wash with no island
  //: left in it.
  const seaDay = new THREE.Color(0x6fa6c8);
  const seaDusk = new THREE.Color(0x3c4a7a);

  return {
    /**
     * @param {number} t     seconds, for anything on its own rhythm
     * @param {object} ctx   `{ day, key, ambient }` -- `day` from the page's
     *                       clock, so the light and the drawn sun agree.
     */
    update(t, { day = null, key = null, ambient = null, fill = null } = {}) {
      for (const part of parts) part(t);
      if (day === null) return;
      // The sun's own arc, not a twelve-second loop: dawn in the east, highest
      // at midday, and down in the west by the bell.
      const a = Math.PI * (0.08 + clamp01(day) * 0.84);
      if (key) {
        key.position.set(Math.cos(a) * 7, Math.max(0.6, Math.sin(a) * 7), 3.0);
        // A floor under it: the island still has to be readable at dusk, and
        // the cards standing on it are the part that matters most then.
        key.intensity = 0.75 + Math.sin(a) * 1.55;
        key.color.copy(day < 0.5 ? dawn.clone().lerp(noon, day / 0.5)
                                 : noon.clone().lerp(dusk, (day - 0.5) / 0.5));
      }
      if (ambient) {
        ambient.intensity = 0.62 + Math.sin(a) * 0.7;
        ambient.color.copy(day < 0.5 ? skyDawn.clone().lerp(skyNoon, day / 0.5)
                                     : skyNoon.clone().lerp(skyDusk, (day - 0.5) / 0.5));
      }
      if (fill) {
        fill.intensity = 0.75 * (0.55 + Math.sin(a) * 0.45);
        fill.color.copy(day < 0.5 ? seaDusk.clone().lerp(seaDay, day / 0.5)
                                  : seaDay.clone().lerp(seaDusk, (day - 0.5) / 0.5));
      }
      // Lit as the light goes, which is the one thing on the island that is
      // brighter at dusk than at noon.
      const lit = clamp01((day - 0.62) / 0.25) * 1.5 + 0.05;
      for (const l of lanterns) l.material.emissiveIntensity = lit;
    },
  };
}
