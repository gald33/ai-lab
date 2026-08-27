/**
 * The island as a model, rather than as a drawing of one.
 *
 * Ported from the design delivered as `island.html` + `island-model.js`, with
 * two things generalised, because the design was authored against one board.
 *
 * **The goods.** It hardcoded bread, cloth, iron and salt with a site apiece.
 * The island has an ordered vocabulary of seven and a game is drawn over the
 * first N of it, so a five-good game would have had nowhere to make fish. The
 * four bespoke sites are kept and matched **by name**; anything else gets a
 * generic works, and fish gets nets on the shore, so a game can be played over
 * any prefix without the island quietly omitting one of its goods.
 *
 * **The seats.** It placed two settlements by hand. They are placed by the
 * caller here, in island coordinates, because the page already knows where a
 * trader's card is and the hut has to stand under it.
 *
 * Scenery colour is the viewer's scenery tokens. Good colour appears only on a
 * site's marker flag, and the trader colours are their own -- not `--util` and
 * `--eff`, which the design used and which mean utility and efficiency on the
 * card three centimetres away.
 */

import * as THREE from "./vendor/three/three.module.js";
//: What a good looks like when the island draws one -- the same face a crate
//: in a trader's yard wears.
import { face } from "./good-face.js";

const rng = (s) => () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296;

function mat(name, color, roughness = 0.9, metalness = 0.0, emissive = null) {
  const m = new THREE.MeshStandardMaterial({ color, roughness, metalness });
  if (emissive) { m.emissive = new THREE.Color(emissive); m.emissiveIntensity = 0.6; }
  m.name = name;
  return m;
}

export const M = {
  sea: mat("sea", 0x36718f, 0.35, 0.05),
  seaDeep: mat("sea_deep", 0x244a63, 0.4, 0.05),
  surf: mat("surf", 0xcfe6ef, 0.5),
  sand: mat("sand", 0xddbe83, 0.95),
  sandWet: mat("sand_wet", 0x96793f, 0.9),
  //: **Green, not olive.** These were 0x55803f and 0x3f6330, both around a
  //: hue of 100 degrees -- a third of the way from green to yellow before any
  //: light touched them. Under a key that is warm all day and frankly orange
  //: by the bell, the island read as a yellow one. Moved to 120-130 degrees,
  //: which is a leaf: the warmth in the picture is then the light's, and it
  //: still goes gold at dusk because the light does.
  grass: mat("grass", 0x4c8049, 0.92),
  grassDark: mat("grass_dark", 0x35633c, 0.95),
  rock: mat("rock", 0x6d757a, 0.85),
  thatch: mat("thatch", 0x7a4a34, 0.9),
  thatchLit: mat("thatch_lit", 0x96654a, 0.9),
  timber: mat("timber", 0x7a5a34, 0.9),
  cloth: mat("cloth", 0xe8e2d4, 0.85),
  salt: mat("salt_crust", 0xe9eef0, 0.7),
  wheat: mat("wheat", 0xc9a86a, 0.9),
  glass: mat("lantern", 0xffd79a, 0.4, 0.0, 0xffb45e),
  //: The fire's own. Emissive from the start and driven by the life layer,
  //: which turns it up as the day goes -- the one thing on this island that is
  //: brighter at the bell than at noon.
  flame: mat("flame", 0xffb347, 0.5, 0.0, 0xff7a1e),
};

//: The good slots, in the stylesheet's order, so a flag on the island is the
//: colour of that good's chip in the legend and its bar on a shelf.
/**
 * A good's colour, in the model.
 *
 * **The same list as `--good-1..7` in `tokens.css`, and it has to be.** These
 * had drifted apart from the fifth good on: the stylesheet said pink, green,
 * purple and this said purple, pink, cyan, so on any island with five goods --
 * which is the table default since fish -- a box standing on the ground was a
 * different colour from the bar counting it on the card and the chip naming it
 * in the legend. Nothing compared the two lists, because one is CSS and one is
 * hex integers for three.js.
 *
 * `test_palette.py` compares them now. The stylesheet is the source: its
 * colours are the ones `palette.py` runs the contrast and dichromacy gates
 * against, so a colour that exists only here has passed nothing.
 */
export const GOOD_COLOURS = [0x3987e5, 0xd95926, 0x199e70, 0xc98500,
                             0xd55181, 0x008300, 0x9085e9];

//: Seat colours, and deliberately not the metric tokens the design reached for.
//: `--util` and `--eff` name utility and efficiency, and both are drawn on the
//: card standing beside the hut; a banner in one of them would be the third
//: thing on screen wearing a colour that already means something else.
export const SEAT_COLOURS = [0xe8a13d, 0x6fc2a0, 0xc98bd8, 0xd9694f,
                             0x86a8e0, 0xd3c463];

export const goodMat = (good, i) =>
  mat(`good_${good}`, GOOD_COLOURS[i % GOOD_COLOURS.length], 0.6, 0.1);
export const seatMat = (name, i) =>
  mat(`trader_${name}`, SEAT_COLOURS[i % SEAT_COLOURS.length], 0.7);

function add(group, geo, material, name, pos = [0, 0, 0], rot = [0, 0, 0], scale = null) {
  const mesh = new THREE.Mesh(geo, material);
  mesh.name = name;
  mesh.position.set(...pos);
  mesh.rotation.set(...rot);
  if (scale) mesh.scale.set(...scale);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}

/**
 * The outline a slab is cut to: a radius at an angle, in the slab's own plane.
 *
 * Named and shared because the meadow's outline is not only drawn -- it is the
 * coastline everything standing on the island has to stay inside of, and a
 * second copy of these three terms would drift from the one that is rendered.
 */
const silhouette = (radius, wobble, phase) => (t) =>
  radius * (1 + wobble * Math.sin(3 * t + phase)
              + wobble * 0.6 * Math.sin(5 * t - phase * 1.7));

//: The meadow, as `slab()` is asked for it below. Kept beside the call.
const MEADOW = { radius: 3.25, wobble: 0.12, phase: 1.9 };

/**
 * How far the grass reaches, in the direction of an island point.
 *
 * A slab is cut in its own plane and then laid flat by `rotateX(-PI/2)`, which
 * sends the slab's `+y` to the island's `-z`. So the angle at which a point
 * `(x, z)` meets the outline is `atan2(-z, x)` and not the `atan2(z, x)` a
 * reader would reach for -- get that wrong and this follows a coastline
 * rotated against the one on screen, which is worse than no clamp at all.
 */
export const meadowEdge = (x, z) =>
  silhouette(MEADOW.radius, MEADOW.wobble, MEADOW.phase)(Math.atan2(-z, x));

//: Inside this, the island is the fire and the hill: a settlement dropped
//: there stands in the hearth or sinks into the upland. It is the upland that
//: sets it now -- its outline reaches 1.92 from the centre, and the fire's
//: clearing, since it stopped being a market's plaza, only 1.34.
const HOME_IN = 2.15;

/**
 * Where a settlement can actually stand: on the meadow, outside the middle.
 *
 * Same bearing, moved along it. The middle yields to the coast when a bearing
 * has no room for both -- better a hut close to the hill than one in the sea.
 */
export function homeSite(x, z, margin = 0.55) {
  const d = Math.hypot(x, z);
  const [ux, uz] = d > 1e-6 ? [x / d, z / d] : [1, 0];
  const out = Math.max(0.4, meadowEdge(ux, uz) - margin);
  const r = Math.min(out, Math.max(Math.min(HOME_IN, out), d));
  return [ux * r, uz * r];
}

/**
 * Settlements turned apart until none is standing in another's doorway.
 *
 * Two seats can arrive at the same place: the page lays them out on screen and
 * a narrow frame collapses its ring, so on a phone with four traders two of
 * them unprojected to within a hut's width of each other. They are moved
 * *around* the island rather than in or out, so each keeps the distance from
 * the fire the layout gave it.
 */
/**
 * @param {Array<[number, number]>} seats  what may be turned
 * @param {Array<[number, number]>} fixed  what may not, and still pushes.
 *   **The good sites, mainly.** A settlement that only avoided other
 *   settlements still landed on the salt pans or inside the smithy: they are
 *   laid on their own ring at their own radii and nothing was comparing the
 *   two. Reported as things drawn on top of one another.
 */
/**
 * @param {number} min   how far a seat must stay from a `fixed` obstacle
 * @param {number} mine  how far two seats must stay from each other. Separate
 *   from `min` because a settlement and a production site are not the same
 *   size, so "far enough apart" is not the same number for a pair of huts as
 *   for a hut and a salt pan. One number for both is why a hut could come down
 *   half on a pan and still satisfy the rule.
 * @param {function} clamp  where a seat is allowed to be, applied after every
 *   push. `homeSite`, in practice.
 *
 * **This used to move seats only around the island**, never in or out, so that
 * each kept the distance from the fire the layout gave it. That is a nicer
 * arrangement and it cannot always be had: a seat squeezed between two sites
 * on the same ring has nowhere to turn to, and the passes then push it back
 * and forth between them until they run out -- measured at a four-trader,
 * five-good table, where a hut and the bread field overlapped by a quarter of
 * a unit and no number of passes moved it. It relaxes in two dimensions now
 * and lets `clamp` put it back on the grass; a seat keeps its bearing where it
 * can and gives up its radius where it must, because a hut standing on a salt
 * pan is worse than a hut a little further from the fire.
 */
function spaced(seats, fixed = [], min = 1.3, passes = 120, mine = min,
                clamp = (x, z) => [x, z]) {
  const at = seats.map(([x, z]) => [x, z]);
  //: A seat exactly on top of another has no side to be pushed to; the tie is
  //: broken by index so the pair still comes apart.
  const tie = (i) => [Math.cos(i * 2.4), Math.sin(i * 2.4)];
  for (let p = 0; p < passes; p++) {
    let worst = 0;
    for (let i = 0; i < at.length; i++) {
      for (let j = i + 1; j < at.length; j++) {
        const dx = at[i][0] - at[j][0], dz = at[i][1] - at[j][1];
        const d = Math.hypot(dx, dz);
        if (d >= mine) continue;
        worst = Math.max(worst, mine - d);
        const [ux, uz] = d > 1e-6 ? [dx / d, dz / d] : tie(i);
        const push = (mine - d) / 2;
        at[i][0] += ux * push; at[i][1] += uz * push;
        at[j][0] -= ux * push; at[j][1] -= uz * push;
      }
      // The immovable ones push and are not pushed, so a seat goes round them.
      for (const [fx, fz] of fixed) {
        const dx = at[i][0] - fx, dz = at[i][1] - fz;
        const d = Math.hypot(dx, dz);
        if (d >= min) continue;
        worst = Math.max(worst, min - d);
        const [ux, uz] = d > 1e-6 ? [dx / d, dz / d] : tie(i);
        at[i][0] += ux * (min - d); at[i][1] += uz * (min - d);
      }
      // Back onto the grass after every push, so the relaxation is solving the
      // problem the island actually has rather than one on an infinite plane.
      at[i] = clamp(at[i][0], at[i][1]);
    }
    if (!worst) break;
  }
  return at;
}

/**
 * The same point, moved inside the grass if it was not already.
 *
 * **The model owns where a settlement may stand.** The page picks seats in
 * screen coordinates and unprojects them, and how much island a screen
 * fraction covers depends on the frame's shape -- so on a wide window the
 * seats the layout chose landed in the sea. Pulling the point in along its own
 * bearing keeps the arrangement the page asked for and only takes back the
 * part of it the island does not have.
 *
 * `margin` is what has to fit inside the edge: a hut's footprint, or a goat.
 */
export function onMeadow(x, z, margin = 0.55) {
  const d = Math.hypot(x, z);
  if (!d) return [0, 0];
  const limit = Math.max(0.4, meadowEdge(x, z) - margin);
  // Scaling toward the centre does not change the bearing, so the edge this
  // was measured against is still the edge at the point it lands on.
  return d <= limit ? [x, z] : [x * (limit / d), z * (limit / d)];
}

/** A wobbly rounded landmass slab: irregular silhouette, soft bevelled edge. */
function slab(radius, depth, bevel, wobble, phase, baseY, material, name) {
  const edge = silhouette(radius, wobble, phase);
  const pts = [];
  const N = 96;
  for (let i = 0; i < N; i++) {
    const t = (i / N) * Math.PI * 2;
    const r = edge(t);
    pts.push(new THREE.Vector2(Math.cos(t) * r, Math.sin(t) * r));
  }
  const geo = new THREE.ExtrudeGeometry(new THREE.Shape(pts), {
    depth, bevelEnabled: true, bevelSize: bevel, bevelThickness: bevel,
    bevelSegments: 4, curveSegments: 12,
  });
  geo.rotateX(-Math.PI / 2);
  geo.computeBoundingBox();
  geo.translate(0, baseY - geo.boundingBox.min.y, 0);
  const mesh = new THREE.Mesh(geo, material);
  mesh.name = name;
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}

/**
 * A rope of water round the island, following the same wobbled outline the
 * land does.
 *
 * A torus is a circle, and the coast is not one: the surf ring used to run
 * along the sand on one bearing and sit a good half-unit out to sea on the
 * next. This is the shore's own silhouette, swept.
 */
function shoreRing(radius, wobble, phase, thickness, y, material, name) {
  const edge = silhouette(radius, wobble, phase);
  const N = 96;
  const pts = Array.from({ length: N }, (_, i) => {
    const t = (i / N) * Math.PI * 2;
    const r = edge(t);
    // The same mapping `slab` gets from its rotation: the shape's second axis
    // is the world's *negative* z, which is what `meadowEdge` reads back.
    return new THREE.Vector3(Math.cos(t) * r, 0, -Math.sin(t) * r);
  });
  const geo = new THREE.TubeGeometry(
    new THREE.CatmullRomCurve3(pts, true), N * 2, thickness, 8, true);
  const mesh = new THREE.Mesh(geo, material);
  mesh.name = name;
  mesh.position.y = y;
  // Flattened, as the torus was: surf lies on the water, it does not float
  // above it as a pipe.
  mesh.scale.y = 0.5;
  mesh.receiveShadow = true;
  return mesh;
}

function hut(id, traderMat) {
  const g = new THREE.Group();
  g.name = `settlement_${id}`;
  add(g, new THREE.CylinderGeometry(0.34, 0.38, 0.42, 24), M.cloth, `hut_${id}_wall`, [0, 0.21, 0]);
  add(g, new THREE.ConeGeometry(0.52, 0.42, 24), M.thatch, `hut_${id}_roof`, [0, 0.63, 0]);
  add(g, new THREE.SphereGeometry(0.05, 12, 10), M.thatchLit, `hut_${id}_finial`, [0, 0.86, 0]);
  //: **The hut had a flag and does not any more.** With a flag over every good
  //: site as well, a four-trader seven-good island carried eleven of them, and
  //: a flag stopped meaning anything: it was just what this island's skyline
  //: was made of. The rule is now that a flag says *which good is made here*
  //: and nothing else says anything with a flag.
  //:
  //: A hut still has to say whose it is, so the trader's colour moved onto the
  //: hut itself -- the door it faces the fire with, and a painted band under
  //: the eaves that is visible from any bearing the camera swings to. That is
  //: more of the colour than the banner ever showed, on a shape a viewer is
  //: already looking at, and it costs the island a pole and a scrap of cloth.
  add(g, new THREE.BoxGeometry(0.14, 0.24, 0.02), traderMat, `hut_${id}_door`, [0, 0.12, 0.379]);
  add(g, new THREE.CylinderGeometry(0.385, 0.4, 0.055, 24), traderMat, `hut_${id}_band`, [0, 0.41, 0]);
  //: **The hut had a lantern and does not any more.** A 0.05 emissive sphere
  //: by the door, ramped up as the day went (`island-life.js`), on the
  //: argument that it was the one thing brighter at dusk than at noon. Cut as
  //: unnecessary: the campfire already carries nightfall, and a second warm
  //: dot per hut is a light that says nothing the fire has not said -- while
  //: on this island a small bright dot already means a good in flight, which
  //: is the same reason the fireflies are held clear of the fire below.
  //: **The two crates by the door are gone.** They were scenery from before
  //: goods stood on the island at all -- a hut with some things outside it --
  //: and they became a lie the moment a trader's holdings became crates in a
  //: yard beside that same hut. A brown cube with no colour and no glyph, next
  //: to a stack of coloured ones that each say what they are, is a good a
  //: viewer cannot identify. Asked about by name: "what are the brown boxes?"
  //:
  //: The same rule as the flags. A shape on this island means one thing, and a
  //: crate means a quantity of a good somebody is holding.
  return g;
}

/**
 * The flag over a site: whose work this is, in the good's own colour and mark.
 *
 * **It carried only the colour.** A crate standing in a trader's yard has the
 * good's symbol on every face, and the flag over the site that *made* that
 * good had a plain coloured rectangle -- which asks a viewer to tell pink from
 * purple across an island eight units wide, and the palette does not promise
 * that: it clears adjacent pairs and not all pairs, which is the whole reason
 * a good carries a glyph anywhere. Same texture as the crates now.
 *
 * Square, where it used to be a banner. The mark is drawn in a square and a
 * flag 0.16 by 0.22 stretched it by a third across.
 */
function marker(name, colour) {
  const g = new THREE.Group();
  g.name = `marker_${name}`;
  add(g, new THREE.CylinderGeometry(0.018, 0.024, 0.62, 10), M.timber, `marker_${name}_post`, [0, 0.31, 0]);
  const mark = face(name, colour, { lip: false });
  const flag = new THREE.MeshStandardMaterial(
    mark ? { map: mark, roughness: 0.85 } : { color: colour, roughness: 0.85 });
  add(g, new THREE.BoxGeometry(0.025, 0.2, 0.2), flag, `marker_${name}_flag`, [0, 0.52, 0.1]);
  return g;
}

function tree(i, scale = 1) {
  const g = new THREE.Group();
  g.name = `tree_${i}`;
  add(g, new THREE.CylinderGeometry(0.045, 0.075, 0.55, 12), M.timber, `tree_${i}_trunk`, [0, 0.275, 0], [0, 0, 0.06]);
  add(g, new THREE.SphereGeometry(0.3, 20, 16), M.grass, `tree_${i}_canopy_a`, [0.02, 0.72, 0], [0, 0, 0], [1, 0.8, 1]);
  add(g, new THREE.SphereGeometry(0.2, 18, 14), M.grassDark, `tree_${i}_canopy_b`, [-0.16, 0.62, 0.1], [0, 0, 0], [1, 0.85, 1]);
  add(g, new THREE.SphereGeometry(0.17, 18, 14), M.grass, `tree_${i}_canopy_c`, [0.16, 0.6, -0.1]);
  g.scale.setScalar(scale);
  return g;
}

function palm(i) {
  const g = new THREE.Group();
  g.name = `palm_${i}`;
  add(g, new THREE.CylinderGeometry(0.04, 0.065, 0.95, 12), M.timber, `palm_${i}_trunk`, [0, 0.47, 0], [0.12, 0, 0.1]);
  for (let f = 0; f < 5; f++) {
    const a = (f / 5) * Math.PI * 2;
    add(g, new THREE.SphereGeometry(0.26, 16, 12), f % 2 ? M.grass : M.grassDark,
      `palm_${i}_frond_${f}`, [Math.cos(a) * 0.18 - 0.1, 0.94, Math.sin(a) * 0.18],
      [0, a, 0], [1, 0.22, 0.55]);
  }
  return g;
}

function boat(i, sailMat) {
  const g = new THREE.Group();
  g.name = `boat_${i}`;
  add(g, new THREE.SphereGeometry(0.3, 24, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2),
    M.timber, `boat_${i}_hull`, [0, 0.1, 0], [0, 0, 0], [1, 0.55, 2.1]);
  add(g, new THREE.TorusGeometry(0.3, 0.028, 8, 28), M.thatchLit, `boat_${i}_gunwale`, [0, 0.1, 0], [Math.PI / 2, 0, 0], [1, 2.1, 1]);
  add(g, new THREE.CylinderGeometry(0.018, 0.022, 0.8, 10), M.timber, `boat_${i}_mast`, [0, 0.5, 0]);
  add(g, new THREE.BoxGeometry(0.012, 0.44, 0.32), sailMat, `boat_${i}_sail`, [0, 0.62, 0.14]);
  return g;
}

export const GRASS_Y = 0.70, HILL_Y = 1.12, SAND_Y = 0.40;

/** Where a good is made. Four are the design's; the rest are built to fit. */
const SITES = {
  bread(g, r) {                                  // the fields
    for (let x = 0; x < 4; x++) for (let z = 0; z < 3; z++) {
      add(g, new THREE.BoxGeometry(0.3, 0.11, 0.24), (x + z) % 2 ? M.wheat : M.grass,
        `field_plot_${x}_${z}`, [(x - 1.5) * 0.34, 0.055, (z - 1) * 0.28]);
    }
    return [0.85, 0, 0.3];
  },
  cloth(g) {                                     // the drying racks
    for (let i = 0; i < 3; i++) {
      const x = (i - 1) * 0.46;
      add(g, new THREE.CylinderGeometry(0.022, 0.022, 0.62, 8), M.timber, `rack_${i}_post_a`, [x - 0.16, 0.31, 0]);
      add(g, new THREE.CylinderGeometry(0.022, 0.022, 0.62, 8), M.timber, `rack_${i}_post_b`, [x + 0.16, 0.31, 0]);
      add(g, new THREE.BoxGeometry(0.42, 0.02, 0.02), M.timber, `rack_${i}_beam`, [x, 0.6, 0]);
      add(g, new THREE.BoxGeometry(0.34, 0.4, 0.014), i === 1 ? M.wheat : M.cloth, `rack_${i}_cloth`, [x, 0.38, 0.01]);
    }
    return [0.95, 0, 0.25];
  },
  iron(g) {                                      // the quarry
    //: **The terraces step up into the hill, not down into it.**
    //:
    //: They were cut downward -- centred at -0.08, -0.24 and -0.40 below the
    //: site's own origin -- which is what a quarry is, and which on this
    //: island means three slabs of rock entirely underneath a grass hill.
    //: Measured: the first one's top face at exactly the ground, the second a
    //: sixth of a unit under and the third a third of a unit under. What was
    //: left above the grass was a flag, a cart and two lumps of spoil, and it
    //: was reported as the quarry being inside the hill.
    //:
    //: `follow` cannot rescue that. It walks each part down onto the ground
    //: *under it*, which corrects for the slope and nothing else -- and the
    //: slope across a site is a hundredth of a unit where the burial was a
    //: third of one.
    //:
    //: A hillside quarry seen from below is a stepped rock face, so that is
    //: what it is now: three ledges standing on the ground, each stepping back
    //: uphill (-z is into the hill, because a site faces the fire) and up. The
    //: cut faces are what a viewer sees, which is the thing that says stone.
    for (let i = 0; i < 3; i++) {
      add(g, new THREE.BoxGeometry(1.0 - i * 0.22, 0.16, 0.62 - i * 0.12), M.rock,
        `quarry_terrace_${i}`, [i * 0.1, 0.08 + i * 0.14, -i * 0.1]);
    }
    add(g, new THREE.DodecahedronGeometry(0.14), M.rock, "quarry_spoil_a", [0.5, 0.06, 0.34], [0.4, 0.2, 0.7]);
    add(g, new THREE.DodecahedronGeometry(0.1), M.rock, "quarry_spoil_b", [0.62, 0.03, 0.2], [0.9, 0.5, 0.1]);
    //: **A cart, not a cube.** It was a 0.2 box of timber called `quarry_cart`
    //: and it read as a crate, which is the one thing it must not read as --
    //: the island is full of crates now and they are the goods. Reported as
    //: not recognisable. Four parts is enough for a cart at this size: a
    //: tipped body, two wheels, and the shaft you pull it by.
    const cart = new THREE.Group();
    cart.name = "quarry_cart";
    cart.position.set(-0.5, 0.0, 0.3);
    cart.rotation.y = 0.6;
    //: Half again the size of the box it replaces, and the wheels in stone
    //: rather than timber. A cart is a quarter of a unit long on an island
    //: eight across -- about twenty pixels on a laptop -- and at that size a
    //: shape is read by its silhouette and its contrast, not by its parts.
    add(cart, new THREE.BoxGeometry(0.38, 0.2, 0.26), M.timber, "cart_body",
      [0, 0.22, 0], [0.2, 0, 0]);
    add(cart, new THREE.BoxGeometry(0.34, 0.03, 0.22), M.rock, "cart_load", [0, 0.31, 0.03]);
    for (const [i, z] of [[0, -0.15], [1, 0.15]]) {
      add(cart, new THREE.CylinderGeometry(0.11, 0.11, 0.035, 14), M.rock,
        `cart_wheel_${i}`, [0, 0.11, z], [0, 0, Math.PI / 2]);
    }
    add(cart, new THREE.CylinderGeometry(0.018, 0.018, 0.4, 6), M.timber, "cart_shaft",
      [-0.28, 0.2, 0], [0, 0, Math.PI / 2.4]);
    g.add(cart);
    return [-0.15, 0.02, 0.42];
  },
  salt(g) {                                      // the pans
    for (let i = 0; i < 4; i++) {
      const x = (i % 2) * 0.62 - 0.31, z = Math.floor(i / 2) * 0.56 - 0.28;
      add(g, new THREE.BoxGeometry(0.56, 0.05, 0.5), M.sandWet, `pan_${i}_bed`, [x, 0.025, z]);
      add(g, new THREE.BoxGeometry(0.48, 0.03, 0.42), M.salt, `pan_${i}_brine`, [x, 0.055, z]);
    }
    add(g, new THREE.ConeGeometry(0.16, 0.22, 16), M.salt, "salt_heap", [0.66, 0.11, -0.5]);
    return [-0.7, 0, -0.42];
  },
  fish(g) {                                      // nets, and a rack of the catch
    for (let i = 0; i < 3; i++) {
      const x = (i - 1) * 0.5;
      add(g, new THREE.CylinderGeometry(0.02, 0.02, 0.7, 8), M.timber, `net_${i}_post`, [x, 0.35, -0.2], [0.1, 0, 0.05]);
      add(g, new THREE.BoxGeometry(0.44, 0.36, 0.01), M.cloth, `net_${i}_mesh`, [x, 0.42, -0.19], [0, 0, 0.05]);
    }
    add(g, new THREE.BoxGeometry(0.7, 0.06, 0.34), M.timber, "fish_table", [0, 0.28, 0.34]);
    add(g, new THREE.CylinderGeometry(0.02, 0.02, 0.28, 8), M.timber, "fish_table_leg_a", [-0.28, 0.14, 0.34]);
    add(g, new THREE.CylinderGeometry(0.02, 0.02, 0.28, 8), M.timber, "fish_table_leg_b", [0.28, 0.14, 0.34]);
    return [0.78, 0, 0.1];
  },
};

/** Any good the design did not draw a site for: a works, plainly built. */
function works(g) {
  add(g, new THREE.BoxGeometry(0.7, 0.34, 0.5), M.timber, "works_shed", [0, 0.17, 0]);
  add(g, new THREE.BoxGeometry(0.78, 0.06, 0.58), M.thatch, "works_roof", [0, 0.37, 0]);
  add(g, new THREE.CylinderGeometry(0.09, 0.11, 0.3, 12), M.rock, "works_kiln", [0.5, 0.15, 0.24]);
  //: A barrel, not a crate. This is the site a good with no workshop of its
  //: own gets, and it carried a plain timber cube -- the same shape a trader's
  //: holdings are drawn as, in the one colour that says nothing. It is only
  //: drawn for a sixth good and nobody has run a table that wide, which is
  //: exactly why it would still have been there when somebody did.
  add(g, new THREE.CylinderGeometry(0.1, 0.1, 0.22, 12), M.timber, "works_barrel",
    [-0.48, 0.11, 0.26]);
  return [0, 0, -0.42];
}

//: The parts of the island that are *ground* -- the things something can stand
//: on. Not the rocks: a tree balanced on a boulder is not what anybody meant.
const GROUND = /^(shore_shelf|beach|meadow|upland|ridge)$/;

/**
 * How high the island is at a point, measured off the island itself.
 *
 * **The terrain is not flat and nothing on it knew that.** Every scattered
 * tree, every site and both goats were placed at one of three constants, so
 * anything that happened to land on the upland -- which rises four tenths of a
 * unit above the meadow -- stood buried up to its canopy in the hill, and
 * anything on the meadow's bevelled rim sank into the slope.
 *
 * A raycast rather than a formula: the slabs are extruded with a bevel and a
 * wobbled outline, the ridge is a squashed dome, and re-deriving the height
 * they add up to would be a second model of the island that could disagree
 * with the one on screen.
 */
/**
 * Let everything in a placed group follow the ground **under itself**.
 *
 * **A site is placed by its origin and its parts are not.** The group asks the
 * island how high it is at one point and every part inside it inherits that one
 * answer -- right on the flat, wrong on a slope. The iron site stands at radius
 * 1.7, a hair outside the upland's own 1.55, so the offsets its parts are built
 * at carried them into the side of the hill: three flags were drawn inside the
 * mountain with only their poles showing, and the quarry's own spoil was six
 * tenths of a unit under the rock it came out of.
 *
 * Each part keeps the height it was *designed* at relative to its site's ground
 * -- a salt pan is meant to sit a little into the sand and still does -- and
 * the terrain under it is added on top. So this follows the slope rather than
 * flattening the design onto it.
 */
function follow(group, ground, base) {
  group.updateMatrixWorld(true);
  for (const part of group.children) {
    const at = part.getWorldPosition(new THREE.Vector3());
    part.position.y += (ground(at.x, at.z, base) - base) / (group.scale.y || 1);
  }
  group.updateMatrixWorld(true);
  return group;
}

function grounder(island) {
  const meshes = island.children.filter((n) => GROUND.test(n.name));
  const ray = new THREE.Raycaster();
  const down = new THREE.Vector3(0, -1, 0);
  const from = new THREE.Vector3();
  return (x, z, fallback = GRASS_Y) => {
    ray.set(from.set(x, 12, z), down);
    const hit = ray.intersectObjects(meshes, false)[0];
    return hit ? hit.point.y : fallback;
  };
}

/**
 * The island, for this round's traders and goods.
 *
 * `seats` are island-space `[x, z]` positions, one per trader in order --
 * the caller places them, because the page already knows where a trader's card
 * is and the hut belongs under it.
 */
export function buildIsland({ traders = ["T1", "T2"], goods = ["bread", "cloth", "iron", "salt"],
                              seats = null, seed = 20260825 } = {}) {
  const island = new THREE.Group();
  island.name = "the_island";
  const r = rng(seed);
  const anchors = {};

  // — sea and shelf —
  //: **The deep sea's top used to sit at exactly y=0, and so does the shore
  //: shelf's underside.** Two coplanar faces, one of them blue, fought for
  //: every pixel where they overlap -- which is the whole coast -- and the
  //: fight only shows while the camera moves, so it read as blue flickering
  //: round the island rather than as anything a still screenshot could catch.
  //: Dropped clear of it.
  //: **Wider than the frame, on every frame.** The disc used to stop at 4.95,
  //: which is a little past the shore and a long way short of the corners: on
  //: a wide window the camera's frustum reaches past the water and the page's
  //: own background shows through, so the island sat in a void with a round
  //: blue puddle under it. Reported as exactly that. Sixteen units covers the
  //: long side of any viewport this frames, and it is one flat disc that casts
  //: nothing and receives nothing, so the whole cost is the fill.
  //: **The open sea neither casts a shadow nor takes one**, and that is a bug
  //: fix, not a nicety.
  //:
  //: Reported as a dark, soft-edged rectangle sitting on the meadow and
  //: flickering rather than sitting still. It is the shadow map: a flat disc
  //: this wide, lit from forty-five degrees, has a far edge that is *closer to
  //: the light* than the middle of the island is -- so in the shadow camera's
  //: own space the water lands on the same texels as the land and wins them.
  //: The land is then compared against the water's depth and comes out
  //: shadowed, over exactly the footprint where the two overlap: the rectangle
  //: is the shadow frustum's own box clipped against the disc, and it crawls
  //: as the light swings through the day, which is the flicker.
  //:
  //: The disc going from five units to sixteen made it obvious; it did not
  //: cause it. Water casting a shadow is meaningless in any case -- and
  //: nothing on this island stands far enough out to sea to throw one onto
  //: the deep water, so it does not need to receive one either. The shallows,
  //: the shelf and the beach still do both, which is where the coast's own
  //: shadows are.
  //: **Dropped again, for the swell.** The life layer lays a moving surface
  //: over this disc, and its troughs go a tenth of a unit below the still
  //: water line -- so with the disc's top at -0.04 every trough sank *into*
  //: it and the open sea got a ring of intersection lines where the two
  //: surfaces cut. The disc is the deep colour behind the swell; it only has
  //: to be below the lowest trough, and this is well below it.
  const sea = add(island, new THREE.CylinderGeometry(16, 16, 0.12, 128), M.seaDeep,
    "sea", [0, -0.30, 0]);
  sea.castShadow = false;
  sea.receiveShadow = false;
  //: The water follows the coast rather than a circle. A round shallows and a
  //: round line of surf against a wobbled shore put the white water a long way
  //: out on one bearing and up on the sand at another.
  island.add(slab(4.62, 0.09, 0.05, 0.10, 0.7, -0.05, M.sea, "shallows"));
  island.add(shoreRing(4.30, 0.10, 0.7, 0.075, 0.05, M.surf, "surf_ring"));

  // — land —
  island.add(slab(4.15, 0.14, 0.14, 0.10, 0.7, 0.0, M.sandWet, "shore_shelf"));
  island.add(slab(3.9, 0.24, 0.20, 0.11, 0.7, 0.08, M.sand, "beach"));
  island.add(slab(MEADOW.radius, 0.34, 0.20, MEADOW.wobble, MEADOW.phase, 0.36, M.grass, "meadow"));
  island.add(slab(1.55, 0.44, 0.22, 0.16, 3.1, 0.68, M.grassDark, "upland"));

  add(island, new THREE.SphereGeometry(1.05, 32, 20, 0, Math.PI * 2, 0, Math.PI / 2),
    M.grassDark, "ridge", [-0.35, HILL_Y - 0.04, -0.35], [0, 0, 0], [1, 0.55, 0.9]);
  add(island, new THREE.DodecahedronGeometry(0.34), M.rock, "summit_rock", [-0.55, HILL_Y + 0.42, -0.5], [0.3, 0.6, 0.2]);
  add(island, new THREE.DodecahedronGeometry(0.2), M.rock, "summit_rock_2", [-0.15, HILL_Y + 0.34, -0.72], [0.5, 1.1, 0.3]);

  // From here on, everything standing on the island asks the island how high it
  // is rather than assuming one of three constants.
  const ground = grounder(island);

  // — the fire at the centre —
  //
  //: **This was a market and the market had no purpose.** A roofed stall with
  //: six posts and a plaza stood in the middle of the island because a barter
  //: game sounds like it should have one -- but nothing on the board ever
  //: happens there. A trade is struck between two traders and settled by the
  //: manager; nobody walks to a stall. So the biggest building on the island
  //: was a label for a thing that does not exist, and it was reported as
  //: exactly that.
  //:
  //: A fire is what the middle of this island is actually for. It is the point
  //: every settlement faces and every trail runs to, it is the one thing that
  //: has something to say at the bell -- it comes up as the light goes -- and
  //: the drawn island the model replaced had a campfire there all along.
  const fire = new THREE.Group();
  fire.name = "fire";
  fire.position.set(0.45, ground(0.45, 0.55), 0.55);
  //: **The fire is a fire, not a plaza.** It inherited the market's footprint
  //: when it replaced it -- a two-unit sand disc with a two-foot ring of ash
  //: in the middle of it, on an island whose huts are eight-tenths of a unit
  //: across -- so the thing that was meant to be a campfire read as the
  //: largest structure on the island, which is the complaint the market got.
  //: The clearing is now about a hut and a half wide and the hearth inside it
  //: is something four people could sit round.
  // The cleared ground round it, which is where the trails end.
  add(fire, new THREE.CylinderGeometry(0.62, 0.66, 0.06, 48), M.sand, "hearth_ground", [0, 0.03, 0]);
  add(fire, new THREE.CylinderGeometry(0.22, 0.24, 0.05, 24), M.sandWet, "hearth_ash", [0, 0.06, 0]);
  // A ring of stones, set by hand rather than drawn as a torus: a hearth is
  // stones somebody carried, and a smooth ring reads as masonry.
  for (let i = 0; i < 9; i++) {
    const a = (i / 9) * Math.PI * 2 + 0.3;
    add(fire, new THREE.DodecahedronGeometry(0.055 + (i % 3) * 0.011), M.rock,
      `hearth_stone_${i}`, [Math.cos(a) * 0.27, 0.06, Math.sin(a) * 0.27],
      [i * 0.7, i * 1.3, i * 0.4]);
  }
  // Logs, leaning in.
  for (let i = 0; i < 4; i++) {
    const a = (i / 4) * Math.PI * 2 + 0.6;
    add(fire, new THREE.CylinderGeometry(0.026, 0.032, 0.33, 8), M.timber,
      `hearth_log_${i}`, [Math.cos(a) * 0.072, 0.11, Math.sin(a) * 0.072],
      [Math.cos(a) * 0.5, 0, -Math.sin(a) * 0.5]);
  }
  // The flames. Named so the life layer can find them: they are the one thing
  // on this island that is brighter the later it gets, and it owns the day.
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI * 2;
    add(fire, new THREE.ConeGeometry(0.075 - i * 0.012, 0.19 + i * 0.055, 8), M.flame,
      `flame_${i}`, [Math.cos(a) * 0.035, 0.17 + i * 0.028, Math.sin(a) * 0.035]);
  }
  // The bell keeps its post beside the fire. It is the island's clock, not the
  // market's -- it was only ever hanging there because the stall was.
  add(fire, new THREE.CylinderGeometry(0.02, 0.025, 0.72, 8), M.timber, "bell_post", [0.52, 0.4, -0.3]);
  add(fire, new THREE.BoxGeometry(0.3, 0.02, 0.02), M.timber, "bell_arm", [0.39, 0.74, -0.3]);
  add(fire, new THREE.SphereGeometry(0.075, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.62),
    M.thatchLit, "bell", [0.28, 0.68, -0.3], [Math.PI, 0, 0]);
  //: **Smaller than it was, twice.** Every prop was built at about a third
  //: again its drawn size, and between them the market, two settlements, four
  //: sites, the jetty and twenty-two trees left an island with no ground
  //: showing on it. The first cut took a fifth off and it was still reported
  //: as crowded; this is the second, down to about three-quarters of what the
  //: model shipped with. They all move together, because shrinking one of them
  //: only makes the rest look bigger.
  fire.scale.setScalar(0.95);
  island.add(fire);
  anchors.fire = fire.position.clone();

  // — how much room each thing gets, which depends on how many things there are —
  //
  //: **An element's drawn size falls as the table grows.** Every prop was a
  //: constant, tuned by eye at one table, so the same island that reads well
  //: with two traders and four goods is a solid mat of props with eight and
  //: five: a hut ends up drawn against a production site, which is a layout
  //: accident and not something the manager settled.
  //:
  //: The rule is area-preserving. `room` is `sqrt(REF / crowd)`, so the *total*
  //: footprint of the settlements and sites stays about what it is at `REF` --
  //: twice as many things, each about seven-tenths the size, covering the same
  //: grass. `REF` is 8 because that is the table the current sizes were tuned
  //: at (four traders, four goods), so nothing moves on the islands already
  //: drawn.
  //:
  //: Clamped both ways. A tiny table does not get to grow props until the
  //: island is a diorama of three enormous huts, and a huge one does not get
  //: to shrink them past the point where a spectator can tell a hut from a
  //: crate.
  const crowd = traders.length + goods.length;
  const room = Math.max(0.72, Math.min(1.1, Math.sqrt(8 / Math.max(1, crowd))));
  //: How far apart two of them have to stand: **the room the two of them
  //: actually take up, plus a gap.**
  //:
  //: It was a flat 1.5 between every pair, and a hut's own footprint is 1.4
  //: across at the corner it is rotated to while a salt pan is 1.5 -- so 1.5
  //: between their middles is two things touching, and that is what was
  //: reported. `RHUT` and `RSITE` are the widest half-footprint each of them
  //: has at scale 1, measured off the model (`render.py:island` reads the same
  //: boxes back and fails if a pair ever overlaps), and `GAP` is the bare
  //: grass between them.
  //:
  //: The size part scales with `room` and the gap does not. A separation held
  //: fixed while the props shrink leaves them where they were on an island
  //: that now has room for more; one that shrank with them closes the grass
  //: between two things that are not the same thing.
  const RHUT = 0.73 * 0.95 * room, RSITE = 0.87 * 0.92 * room;
  const GAP = 0.18;
  const apart = { seat: 2 * RHUT + GAP, site: RHUT + RSITE + GAP };

  // — settlements, one per seat —
  const ring = (i, n, rad, turn = 0) => {
    const a = turn + (i / n) * Math.PI * 2;
    return [Math.cos(a) * rad, Math.sin(a) * rad];
  };
  const placed = [];
  //: Where the good sites will stand, worked out **before** the settlements so
  //: that a settlement can be turned off one. Each good's own ring radius: the
  //: wet work is out on the shelf, iron up on the upland, the rest on the
  //: meadow -- the same arithmetic the loop below uses, and the one place it
  //: is written.
  //: **Settlements and sites share one schedule of bearings.**
  //:
  //: They used to be laid on two independent rings -- the sites on their own
  //: at their own radii, the seats evenly round a third -- and the comment
  //: said "a ring the settlements are not on", which was not true: a dry site
  //: sits at 2.15 and a settlement may stand anywhere from 2.15 out to the
  //: grass's edge, so the two rings are the same band and which bearings
  //: collided was down to how `traders.length` and `goods.length` happened to
  //: divide the circle. Relaxing the seats afterwards could not fix it either,
  //: because a seat caught between the hill and a site on its own bearing has
  //: the push taken straight back off it by the clamp.
  //:
  //: So there is one schedule now, `crowd` slots wide, and the two kinds are
  //: dealt into it alternately. **The angular pitch is the density rule**: it
  //: is `2π/crowd`, so every element on the island gets a share of the circle
  //: that shrinks exactly as the table grows -- which is the same arithmetic
  //: that shrinks the props themselves, applied to the ground they stand on.
  const deal = [];
  for (let k = 0, gi = 0, ti = 0; k < crowd; k++) {
    if (gi < goods.length && gi * traders.length <= ti * goods.length) {
      deal.push(["site", gi++]);
    } else deal.push(["seat", ti++]);
  }
  const bearing = (k) => -0.6 + (k / crowd) * Math.PI * 2;
  const slotOf = (kind, i) => bearing(deal.findIndex(([w, j]) => w === kind && j === i));
  const polar = (a, rad) => [Math.cos(a) * rad, Math.sin(a) * rad];
  const siteAt = goods.map((good, i) => polar(slotOf("site", i),
    good === "salt" || good === "fish" ? 2.75 : good === "iron" ? 1.7 : 2.15));
  // Clamped and separated before any of them is built, because a seat arrives
  // from the page in screen coordinates and the island is the only thing that
  // knows where its own grass ends -- or that two of them landed in one place.
  //
  // Separated from the **sites** as well, which they were not: those are laid
  // on their own ring at their own radii and nothing compared the two, so a
  // hut could come down on the salt pans. Reported as elements drawn on top of
  // one another.
  const homes = spaced(traders.map((_, i) =>
    homeSite(...(seats?.[i] ?? polar(slotOf("seat", i), 2.45)))),
    siteAt, apart.site, 120, apart.seat, homeSite)
    .map(([x, z]) => homeSite(x, z));
  traders.forEach((name, i) => {
    const [x, z] = homes[i];
    const g = hut(name, seatMat(name, i));
    g.position.set(x, ground(x, z), z);
    // Facing the fire, which is what a settlement on an island with one fire
    // in the middle of it would do.
    g.rotation.y = Math.atan2(0.45 - x, 0.55 - z);
    g.scale.setScalar(0.95 * room);
    island.add(g);
    anchors[name] = g.position.clone();
  });

  // — a site per good —
  goods.forEach((good, i) => {
    const site = new THREE.Group();
    site.name = `site_${good}`;
    // Salt is worked on the wet shelf and iron cut out of the upland; the rest
    // sit on the meadow. Placed on a ring the settlements are not on.
    const wet = good === "salt" || good === "fish";
    const [x, z] = siteAt[i];
    // Wet work sits a little into the sand; everything else stands on top of
    // whatever the island is at that point.
    const floor = ground(x, z);
    site.position.set(x, floor - (wet ? 0.02 : 0), z);
    site.rotation.y = Math.atan2(0.45 - x, 0.55 - z);
    const at = (SITES[good] || works)(site, r);
    const flag = marker(good, GOOD_COLOURS[i % GOOD_COLOURS.length]);
    flag.position.set(...at);
    site.add(flag);
    site.scale.setScalar((wet ? 0.88 : 0.92) * room);
    island.add(site);
    //: `follow` is **not** run here. It walks a site's parts down onto the
    //: slope under each of them, reading the ground once and adding the
    //: difference -- so it can only be applied when the site has stopped
    //: moving, and the settling below may still walk one along its ring.
    //: Running it twice would apply the slope twice.
    site.userData.ring = Math.hypot(x, z);
    site.userData.dip = wet ? 0.02 : 0;
  });

  // — and then everything placed is measured, and settled —
  //
  //: **The rule the bearings were dealt by is not the thing a viewer sees.**
  //: The schedule above works on anchors -- the point a group is placed at --
  //: and what a spectator reads as "these two are drawn against each other" is
  //: the ground the props actually cover, which is not centred on the anchor:
  //: a hut carries two crates beside its door and a site carries a flag on a
  //: pole, so both boxes sit off to one side of the point the rule was
  //: satisfied at. Measured at a four-trader, five-good table, a hut cleared
  //: the bread field by the rule and still overlapped it by a tenth of a unit.
  //:
  //: So the props are built, and *then* the footprints are measured and any
  //: overlapping pair is separated along whichever axis is cheaper -- the
  //: standard resolution for two boxes, and the same statement
  //: `render.py:island` reads back.
  //:
  //: **A settlement moves freely; a site moves only along its own ring.** A
  //: site's radius is what it means -- salt is worked on the wet shelf, iron
  //: is cut out of the upland -- so it may be walked round the island but
  //: never in or out. A hut's place is a suggestion, and gives way.
  {
    const box = new THREE.Box3();
    const flat = (o) => {
      box.setFromObject(o);
      return [box.min.x, box.min.z, box.max.x, box.max.z];
    };
    const face = (o, x, z) => {
      o.rotation.y = Math.atan2(0.45 - x, 0.55 - z);
    };
    const movers = [
      ...traders.map((t) => ({ o: island.getObjectByName(`settlement_${t}`), ring: 0 })),
      ...goods.map((g) => {
        const o = island.getObjectByName(`site_${g}`);
        return o ? { o, ring: o.userData.ring, dip: o.userData.dip } : null;
      }),
    ].filter((m) => m && m.o);
    const put = (m, x, z) => {
      let nx = x, nz = z;
      if (m.ring) {
        // Round the island, never in or out.
        const a = Math.atan2(nz, nx);
        nx = Math.cos(a) * m.ring;
        nz = Math.sin(a) * m.ring;
      } else {
        [nx, nz] = homeSite(nx, nz);
      }
      m.o.position.set(nx, ground(nx, nz) - (m.dip || 0), nz);
      face(m.o, nx, nz);
    };
    //: Bare grass between two footprints, in island units. Not zero: two boxes
    //: that touch exactly still read as one thing at the size this is drawn.
    const CLEAR = 0.06;
    for (let pass = 0; pass < 80; pass++) {
      let worst = 0;
      for (let i = 0; i < movers.length; i++) {
        let a = flat(movers[i].o);
        for (let j = 0; j < movers.length; j++) {
          if (j === i) continue;
          const b = flat(movers[j].o);
          const ox = (a[2] - a[0] + b[2] - b[0]) / 2
                   - Math.abs((a[0] + a[2]) / 2 - (b[0] + b[2]) / 2);
          const oz = (a[3] - a[1] + b[3] - b[1]) / 2
                   - Math.abs((a[1] + a[3]) / 2 - (b[1] + b[3]) / 2);
          //: Overlapping on **both** axes is what two boxes touching means; a
          //: negative overlap is the bare grass between them, so the test is
          //: against `-CLEAR` rather than against zero.
          if (ox <= -CLEAR || oz <= -CLEAR) continue;
          worst = Math.max(worst, Math.min(ox, oz) + CLEAR);
          //: Half each, so a pair settles between them rather than one of them
          //: being walked across the island by the other.
          const move = (Math.min(ox, oz) + CLEAR + 0.03) / 2;
          const sx = (a[0] + a[2]) / 2 >= (b[0] + b[2]) / 2 ? 1 : -1;
          const sz = (a[1] + a[3]) / 2 >= (b[1] + b[3]) / 2 ? 1 : -1;
          const [dx, dz] = ox < oz ? [move * sx, 0] : [0, move * sz];
          put(movers[i], movers[i].o.position.x + dx, movers[i].o.position.z + dz);
          put(movers[j], movers[j].o.position.x - dx, movers[j].o.position.z - dz);
          // Measured where it now is, rather than against a box that has
          // stopped being true.
          a = flat(movers[i].o);
        }
      }
      if (worst <= 0) break;
    }
    traders.forEach((name, i) => {
      const h = island.getObjectByName(`settlement_${name}`);
      if (!h) return;
      anchors[name] = h.position.clone();
      placed.push([h.position.x, h.position.z, 0.95 * room]);
    });
    goods.forEach((good) => {
      const o = island.getObjectByName(`site_${good}`);
      if (!o) return;
      // Every part of the site stands where the ground is under *it*, not
      // where it is under the site's origin. See `follow` -- and it is only
      // safe now that the site has stopped moving.
      follow(o, ground, ground(o.position.x, o.position.z));
      // The site's own height, not the meadow's: salt is worked down on the
      // wet shelf and iron up on the ridge, and anything staged at a site has
      // to arrive where the site actually is.
      anchors[`site_${good}`] = o.position.clone();
      placed.push([o.position.x, o.position.z, 1.0 * room]);
    });
  }

  // — the dock and the boats —
  const dock = new THREE.Group();
  dock.name = "dock";
  dock.position.set(3.15, 0, 1.35);
  dock.rotation.y = -1.35;
  for (let i = 0; i < 7; i++) {
    add(dock, new THREE.BoxGeometry(0.7, 0.05, 0.24), M.timber, `dock_plank_${i}`, [0, 0.3, i * 0.26]);
  }
  for (let i = 0; i < 4; i++) {
    add(dock, new THREE.CylinderGeometry(0.035, 0.035, 0.62, 8), M.timber,
      `dock_pile_${i}`, [(i % 2 ? 0.3 : -0.3), 0.0, 0.3 + Math.floor(i / 2) * 1.1]);
  }
  add(dock, new THREE.CylinderGeometry(0.05, 0.05, 0.5, 10), M.thatchLit, "dock_bollard", [0.3, 0.5, 1.62]);
  // One boat per seat, up to what the jetty holds: the traders arrived somehow.
  traders.slice(0, 3).forEach((name, i) => {
    const b = boat(i + 1, seatMat(name, i));
    b.position.set(-0.75 + i * 0.85, 0.02, 1.5 - i * 0.4);
    b.rotation.y = 0.22 - i * 0.57;
    dock.add(b);
  });
  dock.scale.setScalar(0.95);
  island.add(dock);
  placed.push([2.9, 1.2, 0.9]);

  // — the trail: the fire to each settlement, each site, and the dock head —
  const trail = new THREE.Group();
  trail.name = "trails";
  const ends = [...traders.map((n) => [anchors[n].x, anchors[n].z]),
                ...goods.map((g) => [anchors[`site_${g}`].x, anchors[`site_${g}`].z]),
                [2.75, 1.15]];
  for (const [ex, ez] of ends) {
    for (let s = 1; s <= 7; s++) {
      const k = s / 8;
      const x = 0.45 + (ex - 0.45) * k, z = 0.55 + (ez - 0.55) * k;
      const onSand = Math.hypot(x, z) > 3.1;
      const jx = x + (r() - 0.5) * 0.08, jz = z + (r() - 0.5) * 0.08;
      add(trail, new THREE.CylinderGeometry(0.1, 0.11, 0.03, 12), onSand ? M.sand : M.sandWet,
        `trail_step_${ex.toFixed(2)}_${ez.toFixed(2)}_${s}`,
        [jx, ground(jx, jz) + 0.01, jz]);
    }
  }
  island.add(trail);

  // — scattered planting, off everything that carries meaning —
  //: **And off each other.** The keep-out list held what the island had put
  //: down on purpose and nothing else, so two trees drawn a tenth of a unit
  //: apart stood inside one another -- which is what a canopy sphere at 0.3
  //: does at that distance. Every tree planted joins the list, so the next one
  //: has to find room rather than a gap in the meaning.
  const keepOut = [[0.45, 0.55, 1.3], ...placed];
  let n = 0;
  //: Fewer of them on a crowded island, and smaller. Trees are not the table's
  //: elements, but they are most of what makes the grass look full, and an
  //: island whose huts have made room only to have it taken by planting has
  //: not made any.
  const trees = Math.round(16 * room);
  for (let i = 0; i < 900 && n < trees; i++) {
    const a = r() * Math.PI * 2, rad = 0.9 + r() * 3.1;
    const x = Math.cos(a) * rad, z = Math.sin(a) * rad;
    const wob = 1 + 0.12 * Math.sin(3 * a + 1.9) + 0.07 * Math.sin(5 * a - 3.2);
    if (rad > 3.9 * wob) continue;
    if (keepOut.some(([kx, kz, kr]) => Math.hypot(x - kx, z - kz) < kr)) continue;
    const onGrass = rad < 3.0 * wob;
    const g = onGrass ? tree(n, (0.62 + r() * 0.26) * room) : palm(n);
    if (!onGrass) g.scale.setScalar(0.82 * room);
    //: A canopy is about 0.3 across at scale 1, so this is two of them: they
    //: can lean together and they cannot share a trunk. The gap is kept whole
    //: as they shrink -- planting that closes up as it gets smaller is the
    //: crowding this is here to stop.
    keepOut.push([x, z, 0.62 * room + 0.12]);
    // Rooted a little into whatever is under it -- which on the upland is a
    // third of a unit above the meadow, and on the meadow's rim is a slope.
    g.position.set(x, ground(x, z) - 0.02, z);
    g.rotation.y = r() * Math.PI * 2;
    island.add(g);
    n++;
  }
  for (let i = 0; i < 6; i++) {
    const a = r() * Math.PI * 2, rad = 3.4 + r() * 1.0;
    const rx = Math.cos(a) * rad, rz = Math.sin(a) * rad;
    add(island, new THREE.DodecahedronGeometry(0.08 + r() * 0.1), M.rock, `shore_rock_${i}`,
      [rx, ground(rx, rz, 0.16) + 0.04, rz], [r(), r(), r()]);
  }

  // The height function goes out with the island: anything added on top of it
  // afterwards -- the life layer, a clip's props -- has the same question to
  // ask, and asking it twice from two models is how they drift apart.
  return { island, anchors, ground };
}
