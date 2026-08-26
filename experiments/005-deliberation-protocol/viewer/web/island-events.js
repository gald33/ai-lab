/**
 * The island, doing something. The mechanic half of the delivered clips.
 *
 * `island-life.js` is what the island does anyway -- gulls, weather, goats,
 * the light. This is what it does *because something happened on the board*:
 * a production receipt, an offer, a settlement, a refusal, the bell, a new
 * day. One clip per event, each with its own clock, each thrown away when it
 * has run.
 *
 * **Where the delivered clips had to change.** Every one of them built a
 * diorama: its own patch of ground, its own pair of huts, its own field of
 * plots, and then animated that. On the real island those things already
 * exist, in the right places, belonging to the right traders -- so a clip that
 * brought its own would be a second set standing inside the first. What is
 * kept is the *motion*, re-aimed at the island's own nodes; what is spawned is
 * only what genuinely appears and then goes: the crate a production yields,
 * the notice on an offer, the dust where a crate lands, the ring the bell
 * sends out.
 *
 * That change is also what makes them mean anything. A crate that leaves the
 * bread fields and lands at the settlement that produced it says who made it;
 * a crate in a diorama says only that bread exists.
 */

import * as THREE from "./vendor/three/three.module.js";
import { M, goodMat, seatMat, onMeadow } from "./island3d.js";

const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const easeOut = (x) => 1 - (1 - clamp01(x)) ** 3;
const easeIn = (x) => clamp01(x) ** 3;
const easeInOut = (x) => ((x = clamp01(x)) < 0.5
  ? 4 * x * x * x : 1 - (-2 * x + 2) ** 3 / 2);
//: Progress across a segment of the clip's own clock. The delivered clips are
//: written almost entirely in terms of this.
const win = (t, a, b) => clamp01((t - a) / (b - a));

const clone = (m, extra = {}) => Object.assign(m.clone(), extra);

function mesh(geo, material, name, pos = [0, 0, 0], rot = [0, 0, 0]) {
  const m = new THREE.Mesh(geo, material);
  m.name = name;
  m.position.set(...pos);
  m.rotation.set(...rot);
  return m;
}

const crate = (material, size = 0.17) =>
  mesh(new THREE.BoxGeometry(size, size, size), material, "crate");

/** A box, standing squarely in the slot it belongs to and nowhere else. */
function land_(box, at) {
  box.position.copy(at);
  box.rotation.set(0, 0, 0);
  box.scale.setScalar(1);
  box.visible = true;
}

//: Everything a clip spawns is bigger than the delivered clip drew it.
//: The clips were watched one at a time in a frame about two units across;
//: the island is eight, and half of it is behind the traders' cards. A crate
//: the size the diorama used is four pixels on a phone -- present, but not
//: something a spectator would ever notice crossing the ground.
const PROP = 1.7;

//: **There are no ground marks left on this island.** There was a ring under
//: every event, then -- when those were reported as shockwaves -- a patch of
//: light in the same places instead. Both were reported again, and by then the
//: reading was the right one: a coloured disc on the grass is not a thing that
//: happened, it is a caption for one, and the island already shows what
//: happened. Goods are made and carried by boxes that stand there afterwards;
//: the bell is the fire coming up and the light going. A ring said none of it
//: and covered the ground that did.

/** A few puffs behind something crossing the island, so the path reads. */
function trail(c, material, n = 5) {
  const puffs = Array.from({ length: n }, (_, i) => {
    const m = mesh(new THREE.SphereGeometry(0.11 + i * 0.02, 10, 8),
      own(c, clone(material, { transparent: true, opacity: 0 })), `puff_${i}`);
    m.visible = false;
    c.root.add(m);
    return m;
  });
  return (from, to, p, lift) => puffs.forEach((m, i) => {
    const q = p - (i + 1) * 0.07;
    m.visible = q > 0 && p < 1;
    if (!m.visible) return;
    m.position.lerpVectors(from, to, q);
    m.position.y += Math.sin(q * Math.PI) * lift;
    m.material.opacity = 0.5 * (1 - i / n) * Math.min(1, p * 4);
    m.scale.setScalar(1 + i * 0.12);
  });
}

/** A post with a cloth on it, which is how this island says "an offer". */
function bannerPost(material, h = 1.35) {
  const g = new THREE.Group();
  g.name = "banner_post";
  g.add(mesh(new THREE.CylinderGeometry(0.035, 0.042, h, 10), M.timber, "post", [0, h / 2, 0]));
  const banner = mesh(new THREE.BoxGeometry(0.03, 0.42, 0.48), material, "banner", [0, h * 0.78, 0.24]);
  g.add(banner);
  g.userData = { banner };
  return g;
}

/**
 * A clip, ready to be advanced.
 *
 * `root` goes into the island; `update(t)` is called with seconds since it
 * started; `dur` is when the stage may throw it away. Materials cloned per
 * clip are collected so they can be disposed with it -- the model's own
 * materials are shared and must not be.
 */
function clip(dur) {
  const c = {
    root: new THREE.Group(), dur, mine: [], borrowed: [], settle: [], update() {},
    //: Run when the clip retires **and** when it is cleared mid-flight, which
    //: is what a scrub is. Two things happen here: what the clip borrowed off
    //: the island goes back, and what it was carrying is put down where the
    //: board says it ended up. A clip cut short must never leave a box in the
    //: air or a field still cut.
    restore() {
      for (const put of c.borrowed) put();
      for (const down of c.settle) down();
    },
  };
  return c;
}

/** A material this clip owns, and will dispose with itself. */
function own(c, material) {
  c.mine.push(material);
  return material;
}

/**
 * A node of the island, borrowed.
 *
 * **Anything a clip moves that it did not build has to go through here.** The
 * first cut of these clips restored the two that were obviously borrowed --
 * the hut banners, the crates by a door -- and quietly kept the rest: after a
 * single production the fields stayed cut and gold, the drying racks stayed
 * up and the salt pans stayed dry, for the remainder of the round.
 *
 * What is snapshotted is the transform, and the material when the clip is
 * going to recolour it -- in which case the clip gets a clone to scribble on
 * and the island gets its own back at the end.
 */
function borrow(c, node, { material = false } = {}) {
  const was = { p: node.position.clone(), r: node.rotation.clone(),
                s: node.scale.clone(), m: node.material };
  if (material && node.material) {
    node.material = own(c, node.material.clone());
  }
  c.borrowed.push(() => {
    node.position.copy(was.p);
    node.rotation.copy(was.r);
    node.scale.copy(was.s);
    if (was.m) node.material = was.m;
  });
  return node;
}

/**
 * A spot beside a settlement, on the grass.
 *
 * Along the hut's own side rather than on the line to the fire: a prop set
 * out toward the middle from a hut two and a half units out lands *on the
 * fire*, which is where the first cut of this put every offer and every
 * refusal -- standing in the flames, or under the roof that used to be there.
 */
function beside(home, centre, ground, side = 1.15, out = 0.25) {
  const away = new THREE.Vector3(centre.x - home.x, 0, centre.z - home.z).normalize();
  const x = home.x + -away.z * side + away.x * out;
  const z = home.z + away.x * side + away.z * out;
  const [cx, cz] = onMeadow(x, z, 0.35);
  // On the island's own ground, not the meadow's: a post set down at a flat
  // height on the upland stands with its foot buried in the hill.
  return { at: new THREE.Vector3(cx, ground(cx, cz), cz),
           face: Math.atan2(away.x, away.z) };
}

/**
 * The event, staged on the island -- or `null` if this is not one the island
 * has anything to say about.
 *
 * @param {object} event  a reduced board event: `kind`, and whatever that kind
 *                        carries (`trader`, `made`, `maker`, `taker`, ...)
 * @param {object} world  `{ island, anchors, traders, goods }` from the build
 */
/**
 * The piles a clip is about to move with its own hands.
 *
 * The page sets the island to what the board says before it plays the frame's
 * event, and a settlement whose boxes are still on the maker's side would be
 * snapped to the taker's yard under the very animation carrying them. These
 * are the pairs `Stage.showStock` leaves alone; every other pile is set.
 */
export function carried(event) {
  //: The bell eats everything every trader is holding, and eating it is the
  //: animation. Nothing in any yard is reconciled while that plays, or the
  //: boxes would be swept off the ground the instant the frame painted and the
  //: clip would be animating an empty island.
  if (event?.kind === "bell") return "all";
  const keep = new Set();
  if (event?.kind === "produced") {
    for (const good of Object.keys(event.made || {})) keep.add(`${event.trader}:${good}`);
  } else if (event?.kind === "settled") {
    for (const good of Object.keys(event.give || {})) {
      keep.add(`${event.maker}:${good}`);
      keep.add(`${event.taker}:${good}`);
    }
    for (const good of Object.keys(event.want || {})) {
      keep.add(`${event.maker}:${good}`);
      keep.add(`${event.taker}:${good}`);
    }
  }
  return keep;
}

export function stageEvent(event, world) {
  switch (event?.kind) {
    case "produced": return produced(event, world);
    case "offer": return offered(event, world);
    case "settled": return settled(event, world);
    case "refused": return refused(event, world);
    case "bell": return belled(event, world);
    case "open": return opened(event, world);
    default: return null;
  }
}

/**
 * Production: the site works, and what it made walks home **and stays there**.
 *
 * The site's own parts are animated in place -- the fields ripen and are cut,
 * the racks fill, the quarry cart runs, the pans dry -- because they are
 * already standing where that good is made. What the clip adds is the yield.
 *
 * **The yield is real now.** It used to be a crate that appeared at the site,
 * crossed the island and shrank out of existence at the hut, so the ground
 * held nothing between one receipt and the next. The boxes this makes come
 * from the standing stock, and they are still standing in the trader's yard
 * when the clip is long finished -- until a trade carries them off or the bell
 * eats them. Production is one of the two moments a good is allowed to appear
 * from nothing, because it is the moment one is made.
 */
function produced(event, { island, anchors, goods, stock }) {
  const made = Object.entries(event.made || {}).filter(([, q]) => q > 1e-9);
  const home = anchors[event.trader];
  if (!made.length || !home) return null;

  const c = clip(4.4);
  const legs = [];
  const works = [];
  for (const [good, qty] of made) {
    const site = island.getObjectByName(`site_${good}`);
    const from = anchors[`site_${good}`];
    if (!from) continue;
    works.push(...siteWork(good, site, c));
    // What says *here* is the site's own parts working and the crates coming
    // out of it. There used to be a ring on the ground as well; see the note
    // on `ring` for why there is not.
    // How many boxes this receipt is worth: what the yard should hold after it,
    // less what it holds now. A production too small to move the count by a
    // whole box still works its site -- the receipt happened -- it just does
    // not put another crate in the yard, which is the honest picture.
    if (!stock) continue;
    const add = stock.want(good, (event.after?.[good] ?? qty))
              - stock.count(event.trader, good);
    if (add <= 0) continue;
    const born = from.clone().setY(from.y + 0.28);
    const boxes = stock.mint(good, add, born);
    // The slots are claimed now, at the start, so the flight has somewhere to
    // aim and a second receipt arriving mid-air stacks after these rather than
    // on top of them.
    const rest = stock.put(event.trader, good, boxes);
    boxes.forEach((box, k) => {
      legs.push({ box, wake: trail(c, goodMat(good, goods.indexOf(good))),
                  from: born, to: rest[k] });
    });
  }
  if (!legs.length) {
    // Nothing crossed the ground, but the site still worked and the mark still
    // went down: a receipt is a thing that happened.
    if (!works.length) return null;
    c.update = (t) => { for (const w of works) w(t); };
    return c;
  }

  const dustMat = own(c, clone(M.sand, { transparent: true, opacity: 0 }));
  const dust = mesh(new THREE.CircleGeometry(0.22 * PROP, 20), dustMat, "dust",
    [home.x, home.y + 0.03, home.z], [-Math.PI / 2, 0, 0]);
  c.root.add(dust);

  c.update = (t) => {
    for (const w of works) w(t);
    legs.forEach(({ box, wake, from, to }, i) => {
      const t0 = 0.9 + i * 0.3;
      // Coming into being at the site that made it: the one place a box is
      // allowed to grow out of nothing.
      const pop = easeOut(win(t, t0 - 0.6, t0));
      const p = easeInOut(win(t, t0, t0 + 1.9));
      box.visible = pop > 0.01;
      box.scale.setScalar(pop);
      box.position.lerpVectors(from, to, p);
      box.position.y += Math.sin(p * Math.PI) * 0.6;
      box.rotation.set(p * 4.2, p * 3.1, p * 1.8);
      wake(from, to, p, 0.75);
      // The hop as it lands on the pile, and then it is simply standing there.
      const land = win(t, t0 + 1.8, t0 + 2.4);
      if (land > 0) {
        box.position.copy(to);
        box.position.y = to.y + Math.abs(Math.sin(land * Math.PI * 2)) * 0.12 * (1 - land);
        box.rotation.set(0, 0, 0);
        box.scale.setScalar(1);
        dustMat.opacity = Math.max(dustMat.opacity, 0.4 * (1 - land));
        dust.scale.setScalar(1 + land * 1.5);
      }
    });
    if (t < 0.9) dustMat.opacity = 0;
  };
  // Scrubbed away mid-flight, the boxes are still the trader's: the receipt
  // happened. Put them down in the slots they were already promised.
  c.settle.push(() => { for (const { box, to } of legs) land_(box, to); });
  return c;
}

/**
 * The site at work, as a list of things to advance.
 *
 * Each of these is the delivered clip's `update` with its diorama taken away
 * and the real site's nodes put in. A good with no site of its own -- anything
 * past the five the design drew -- gets the shed shaking, which is honest: the
 * island does not know how that good is made either.
 */
function siteWork(good, site, c) {
  if (!site) return [];
  const part = (re) => site.children.filter((n) => re.test(n.name));
  const named = (n) => site.getObjectByName(n);

  if (good === "bread") {
    const green = new THREE.Color(0x55803f), gold = new THREE.Color(0xc9a86a);
    const plots = part(/^field_plot_/).map((p, i) => {
      borrow(c, p, { material: true });
      return { p, k: i / 12, y0: p.position.y, s0: p.scale.y };
    });
    return [(t) => plots.forEach(({ p, k, y0, s0 }) => {
      const grow = easeOut(win(t, 0.1 + k * 0.7, 1.4 + k * 0.7));
      const cut = easeInOut(win(t, 2.2 + k * 0.4, 2.7 + k * 0.4));
      p.scale.y = s0 * (0.55 + grow * 1.5) * (1 - cut * 0.72);
      p.position.y = y0 * (p.scale.y / s0);
      p.material.color.copy(green).lerp(gold, grow);
    })];
  }
  if (good === "cloth") {
    const cloths = part(/_cloth$/).map((p, i) => {
      borrow(c, p);
      return { p, i, y0: p.position.y, s0: p.scale.y };
    });
    return [(t) => cloths.forEach(({ p, i, y0, s0 }) => {
      const raise = easeOut(win(t, 0.15 + i * 0.3, 1.2 + i * 0.3));
      p.scale.y = s0 * Math.max(0.02, raise);
      p.position.y = y0 + (1 - raise) * 0.18;
      const settle = win(t, 1.3 + i * 0.3, 4.4);
      p.rotation.y = Math.sin(t * 3.4 + i) * 0.12 * settle;
    })];
  }
  if (good === "iron") {
    const cart = named("quarry_cart");
    if (cart) borrow(c, cart);
    const spoil = part(/^quarry_spoil_/).map((s, i) => {
      borrow(c, s);
      return { s, i, y0: s.position.y };
    });
    const x0 = cart?.position.x ?? 0;
    return [(t) => {
      if (cart) {
        const run = easeInOut(win(t, 0.2, 1.4)) - easeInOut(win(t, 2.4, 3.6));
        cart.position.x = x0 + run * 0.75;
        cart.rotation.z = Math.sin(t * 9) * 0.05 * win(t, 0.2, 3.6) * (1 - win(t, 3.2, 3.6));
      }
      spoil.forEach(({ s, i, y0 }) => {
        const hit = easeOut(win(t, 1.3 + i * 0.3, 1.75 + i * 0.3));
        s.position.y = y0 + Math.sin(hit * Math.PI) * 0.2;
        s.rotation.y += hit * 0.03;
      });
    }];
  }
  if (good === "salt") {
    const brine = new THREE.Color(0x6fa8b8), crust = new THREE.Color(0xe9eef0);
    const pans = part(/_brine$/).map((b, i) => {
      borrow(c, b, { material: true });
      return { b, k: i / 4, y0: b.position.y, s0: b.scale.y };
    });
    const heap = named("salt_heap");
    if (heap) borrow(c, heap);
    const h0 = heap?.scale.x ?? 1;
    return [(t) => {
      pans.forEach(({ b, k, y0, s0 }) => {
        const dry = easeInOut(win(t, 0.1 + k * 0.5, 2.2 + k * 0.5));
        b.scale.y = s0 * (1 - dry * 0.78);
        b.position.y = y0 - dry * 0.02;
        b.material.color.copy(brine).lerp(crust, dry);
      });
      if (heap) heap.scale.setScalar(h0 * (0.4 + easeOut(win(t, 2.1, 3.1)) * 0.6));
    }];
  }
  if (good === "fish") {
    const nets = part(/_mesh$/);
    for (const n of nets) borrow(c, n);
    return [(t) => nets.forEach((n, i) => {
      const haul = win(t, 0.2 + i * 0.3, 2.4);
      n.rotation.x = Math.sin(t * 2.6 + i) * 0.22 * haul;
      n.scale.y = 1 + Math.sin(t * 3.1 + i * 2) * 0.08 * haul;
    })];
  }
  // The plainly-built works: the kiln runs and the shed shakes with it.
  const kiln = named("works_kiln"), shed = named("works_shed");
  if (kiln) borrow(c, kiln);
  if (shed) borrow(c, shed);
  return [(t) => {
    const run = win(t, 0.2, 3.0) * (1 - win(t, 3.0, 3.8));
    if (kiln) kiln.scale.set(1 + Math.sin(t * 12) * 0.03 * run, 1, 1 + Math.sin(t * 12) * 0.03 * run);
    if (shed) shed.rotation.z = Math.sin(t * 17) * 0.012 * run;
  }];
}

/** An offer: a post goes up beside the maker's hut and a notice unrolls on it. */
function offered(event, { anchors, traders, ground, stock }) {
  const home = anchors[event.maker];
  if (!home) return null;
  const c = clip(3.0);
  const spot = beside(home, anchors.fire, ground);
  const post = bannerPost(own(c, seatMat(event.maker, traders.indexOf(event.maker))));
  post.position.copy(spot.at);
  post.rotation.y = spot.face;
  c.root.add(post);

  const scrollMat = own(c, clone(M.cloth));
  const scroll = mesh(new THREE.BoxGeometry(0.03, 0.5, 0.56), scrollMat, "notice", [0, 0.95, 0.28]);
  post.add(scroll);

  // A post and a notice are a metre of timber on an island eight across, so
  // something has to carry this out to somebody watching the whole island.
  //
  //: **It used to be a ring going out from the post**, and it is a lamp on the
  //: post now. Every expanding ring on this island has gone the same way: five
  //: clips fired one, a four-good production put four up at once, and at 4x
  //: they arrived on top of each other -- reported twice by somebody watching,
  //: the second time as simply too distracting to read. A lamp on the post and
  //: the light it throws on the ground say the same thing and say it *in one
  //: place*, which is where the offer actually is.
  //: **The boxes it is offering lift off the pile.** A post and a notice are a
  //: metre of timber on an island eight across, and with the ring gone they
  //: were most of what an offer had -- a clip nobody can see is not an
  //: animation. These are the crates the trader is putting on the table, they
  //: are already standing in its yard, and they are the biggest thing the
  //: event has any business touching. They settle back at the end: an offer is
  //: a proposal, and nothing has moved yet.
  const offered = Object.keys(event.give || {}).flatMap((good) => {
    const pile = stock?.take(event.maker, good, stock.want(good, event.give[good])) ?? [];
    return pile.map((box) => ({ box, at: box.position.clone(), turn: box.rotation.y }));
  });
  if (offered.length) {
    c.settle.push(() => {
      for (const { box, at, turn } of offered) { land_(box, at); box.rotation.y = turn; }
      for (const good of Object.keys(event.give || {})) {
        stock.put(event.maker, good, offered.filter((o) => o.box.name === `box_${good}`)
          .map((o) => o.box));
      }
    });
  }
  const lampMat = own(c, clone(M.glass, { transparent: true, opacity: 0 }));
  const lamp = mesh(new THREE.SphereGeometry(0.11, 16, 12), lampMat, "offer_lamp",
                    [0, 1.32, 0.1]);
  post.add(lamp);
  //: And the light it throws. A lamp that lights nothing is a decal -- the
  //: same argument the fire is built on -- and this is what carries an offer
  //: out to somebody watching the whole island now that the ring is gone.
  const beam = new THREE.PointLight(0xffc978, 0, 2.6, 2);
  beam.position.set(spot.at.x, spot.at.y + 1.1, spot.at.z);
  c.root.add(beam);

  c.update = (t) => {
    const rise = easeOut(win(t, 0, 0.5));
    post.scale.y = Math.max(0.02, rise);
    const unroll = easeOut(win(t, 0.45, 1.3));
    scroll.scale.y = Math.max(0.001, unroll);
    scroll.position.y = 1.2 - 0.25 * unroll;
    scroll.visible = unroll > 0.01;
    const flut = win(t, 1.2, 3.0);
    scroll.rotation.y = Math.sin(t * 4.2) * 0.1 * flut;
    post.userData.banner.rotation.y = Math.sin(t * 3.6) * 0.12 * flut;
    const p = win(t, 0.6, 2.8);
    const shine = Math.sin(Math.PI * p) ** 0.6;
    lampMat.opacity = 0.85 * shine;
    lampMat.emissiveIntensity = 0.4 + shine * 1.6;
    beam.intensity = shine * 4.2;
    offered.forEach(({ box, at, turn }, k) => {
      const up = Math.sin(Math.PI * win(t, 0.35 + k * 0.1, 2.9)) ** 0.6;
      box.position.y = at.y + up * 0.42;
      box.rotation.y = turn + up * 1.6;
      box.scale.setScalar(1 + up * 0.12);
    });
    // Taken down at the end rather than left standing: the rope on the card is
    // what says an offer is still open, and two things saying it disagree the
    // moment one of them is a second behind.
    const down = win(t, 2.6, 3.0);
    post.scale.y = Math.max(0.02, rise) * (1 - down);
  };
  return c;
}

/** A settlement: the goods actually cross the island, both ways. */
function settled(event, { island, anchors, goods, stock, life }) {
  const a = anchors[event.maker], b = anchors[event.taker];
  if (!a || !b || !stock) return null;
  const c = clip(4.2);

  const legs = [];
  //: **The same boxes, moved.** They used to be crates conjured at one hut and
  //: dissolved at the other, which is a picture of goods being destroyed and
  //: re-created rather than changing hands. These come off the maker's own
  //: pile and go onto the taker's, and the count in each yard is the count the
  //: board says after the exchange.
  const push = (bundle, giver, taker, base) => {
    Object.entries(bundle || {}).filter(([, q]) => q > 1e-9)
      .forEach(([good, q], i) => {
        //: Exactly what the giver's pile loses, which is what the taker's
        //: gains. **Not a forced minimum of one**: a trader that gives part of
        //: a holding and keeps the rest may still be owed the same number of
        //: boxes afterwards, and moving one anyway left its yard a box short
        //: of what the board says -- which the next paint then put back, out
        //: of nowhere, in front of the viewer.
        const move = Math.max(0, stock.count(giver, good)
                      - stock.want(good, event.after?.[giver]?.[good] ?? 0));
        const boxes = stock.take(giver, good, move);
        if (!boxes.length) return;
        const rest = stock.put(taker, good, boxes);
        boxes.forEach((box, k) => {
          legs.push({ box, wake: trail(c, goodMat(good, goods.indexOf(good))),
                      a: box.position.clone(), b: rest[k],
                      t0: base + i * 0.3 + k * 0.12 });
        });
      });
  };
  //: Started when the losing card has finished emptying into these boxes.
  //: `scene.js` runs that leg in 820ms and this is the middle of the three:
  //: symbols down to the pile, pile across the island, symbols up to the other
  //: card. A box that set off first would be carrying goods the bar it came
  //: from still showed.
  push(event.give, event.maker, event.taker, 0.85);
  push(event.want, event.taker, event.maker, 1.05);
  if (!legs.length) return null;
  c.settle.push(() => { for (const { box, b: at } of legs) land_(box, at); });

  const dustMat = own(c, clone(M.sand, { transparent: true, opacity: 0 }));
  const dust = legs.map((l) => {
    const d = mesh(new THREE.CircleGeometry(0.18 * PROP, 20), own(c, dustMat.clone()), "dust",
      [l.b.x, l.b.y - 0.06, l.b.z], [-Math.PI / 2, 0, 0]);
    c.root.add(d);
    return d;
  });

  // Where the deal was struck, the fire flares once: it belongs to neither
  // trader, it is at the centre both of them face, and it is already the thing
  // this island lights up with. The ground mark that used to be here is gone
  // -- see the note on `ring`.

  c.update = (t) => {
    legs.forEach((l, i) => {
      const p = easeInOut(win(t, l.t0, l.t0 + 1.5));
      //: **It is standing in the maker's yard until it sets off.** This used
      //: to hide the box until its own leg started, so for the first second of
      //: an exchange the goods were simply gone from the ground and then
      //: appeared in mid-air -- which is the one thing this whole layer exists
      //: to stop. `p` is zero before `t0`, so it waits where it already was.
      l.box.position.lerpVectors(l.a, l.b, p);
      l.box.position.y = l.a.y + (l.b.y - l.a.y) * p + Math.sin(p * Math.PI) * 0.85;
      l.box.rotation.set(p * 5, p * 3.4, p * 2);
      l.wake(l.a, l.b, p, 0.85);
      const down = win(t, l.t0 + 1.5, l.t0 + 2.0);
      if (down > 0) {
        // The hop as it settles onto the new owner's pile -- and then it is
        // simply standing there. Nothing vanishes: the good did not stop
        // existing, it changed hands.
        land_(l.box, l.b);
        l.box.position.y = l.b.y
          + Math.abs(Math.sin(down * Math.PI * 2)) * 0.12 * (1 - down);
        dust[i].material.opacity = 0.42 * (1 - down);
        dust[i].scale.setScalar(1 + down * 1.6);
      } else dust[i].material.opacity = 0;
    });
    life?.flare(Math.sin(Math.PI * win(t, 1.9, 3.6)) ** 0.7 * 0.55);
  };
  return c;
}

/** A refusal: the notice is torn up where it was posted. */
function refused(event, { anchors, traders, ground }) {
  const home = anchors[event.trader];
  if (!home) return null;
  const c = clip(3.0);
  const spot = beside(home, anchors.fire, ground);
  const post = bannerPost(own(c, seatMat(event.trader, traders.indexOf(event.trader))));
  post.position.copy(spot.at);
  post.rotation.y = spot.face;
  c.root.add(post);

  const noticeMat = own(c, clone(M.cloth));
  const half = new THREE.BoxGeometry(0.03, 0.5, 0.27);
  const left = mesh(half, noticeMat, "notice_l", [0, 0.95, 0.15]);
  const right = mesh(half, noticeMat, "notice_r", [0, 0.95, 0.43]);
  post.add(left, right);

  const flashMat = own(c, clone(M.cloth, {
    transparent: true, opacity: 0, color: new THREE.Color(0xd03b3b),
    emissive: new THREE.Color(0xd03b3b), emissiveIntensity: 0.8 }));
  const flash = mesh(new THREE.CylinderGeometry(1.55, 1.55, 0.01, 40), flashMat, "refusal_flash",
    [post.position.x, post.position.y + 0.04, post.position.z]);
  c.root.add(flash);

  c.update = (t) => {
    const shake = win(t, 0.1, 0.8);
    post.rotation.z = Math.sin(t * 44) * (1 - shake) * 0.06;
    const tear = easeIn(win(t, 0.8, 2.4));
    left.position.set(-Math.sin(tear * 1.2) * 0.07, 0.95 - tear * 1.05, 0.15 - tear * 0.35);
    right.position.set(Math.sin(tear * 1.2) * 0.07, 0.95 - tear * 0.98, 0.43 + tear * 0.4);
    left.rotation.set(tear * 1.4, tear * 0.6, tear * 2.2);
    right.rotation.set(-tear * 1.1, -tear * 0.5, -tear * 1.9);
    const fl = win(t, 0.3, 2.4);
    flashMat.opacity = 0.6 * Math.sin(Math.PI * fl) ** 0.9;
    flash.scale.setScalar(0.55 + fl * 0.75);
    const down = win(t, 2.5, 3.0);
    post.scale.y = 1 - down;
  };
  return c;
}

/**
 * The bell: **night falls and the fire comes up.**
 *
 * The bell itself is a plum-sized thing on a post and it was carrying the
 * whole event. What a day ending actually looks like on this island is the
 * light going and the campfire taking over, and both of those are the size of
 * the island. The bell still swings -- it is what rang -- but it is the detail
 * now and not the animation.
 */
function belled(event, { island, anchors, traders, stock, life }) {
  const c = clip(4.2);
  //: **The one place a good is allowed to stop existing.** Everything held at
  //: the bell is consumed -- that is the rule the manager settles by -- so the
  //: boxes in every yard go down into the ground and are gone. They are not
  //: swept away between frames: a spectator watches the day's holdings being
  //: eaten, which is the whole reason a zero episode is worth looking at.
  const eaten = (stock ? traders.flatMap((t) => stock.all(t)) : []).map((box) => ({
    box, y0: box.position.y, turn: box.rotation.y }));
  c.settle.push(() => {
    if (!stock) return;
    for (const t of traders) stock.clear(t);
  });
  const bell = island.getObjectByName("bell");
  if (bell) borrow(c, bell);
  const y0 = bell?.position.y ?? 0;

  //: **The three shockwaves are gone**, and so is the one they were cut down
  //: to. A bell ringing out is the clearest thing an expanding ring can mean,
  //: which is exactly why this was the last one to go -- but the bell already
  //: swings, every banner comes down, and the whole island goes to night on
  //: the same beat. It was never the ring carrying the bell.
  //
  //: What stands in for it is the **fire**, which is coming up at this exact
  //: moment anyway: it flares as the bell swings and settles back to the day's
  //: own value afterwards, so nothing about it is a thing that travels.
  //: **The fire, through the layer that owns it.** The bell is nightfall and
  //: the campfire taking over, and both are the size of the island where the
  //: bell itself is a plum on a post. Asked for rather than done by hand: the
  //: cones and the light they throw belong to `island-life`, and a clip that
  //: set them directly would be overwritten by the layer on the next frame or
  //: would have to be undone by a restore that might never run.

  //: **The banners going up with the lapsed offers are gone with the
  //: banners.** A hut has no flag any more -- a flag on this island says which
  //: good is made where, and nothing else -- so the bell is the swing, the
  //: day's stock being eaten, and the night coming down over the whole frame.
  //: Those are three things a viewer can see from any distance; the scrap of
  //: cloth leaving a pole was never one of them.

  c.update = (t) => {
    const swing = win(t, 0, 2.2);
    if (bell) {
      bell.rotation.z = Math.sin(t * 9) * 0.5 * (1 - swing) ** 1.4;
      bell.position.y = y0 + Math.sin(t * 26) * 0.006 * (1 - swing);
    }
    const p = win(t, 0.05, 2.6);
    // Night, drawn down over the island. At a real bell the page's own clock
    // has already put the day here, and `hold` never pulls it back.
    life?.hold(easeInOut(win(t, 0, 2.4)));
    life?.flare(Math.sin(Math.PI * p) ** 0.7 * 0.95);
    eaten.forEach(({ box, y0, turn }, i) => {
      const go = easeIn(win(t, 0.6 + (i % 6) * 0.12, 2.8 + (i % 6) * 0.12));
      box.position.y = y0 - go * 0.34;
      box.rotation.y = turn + go * 2.2;
      box.scale.setScalar(Math.max(0.001, 1 - go));
    });
  };
  return c;
}

/**
 * A new day: **the night lifts and last night's fire goes out.**
 *
 * The mirror of the bell, and for the same reason: a dawn is the light coming
 * back over the whole island, not two banners going up a pole. The fire that
 * burned all night falls with it.
 */
function opened(event, { island, anchors, traders, life }) {
  const c = clip(4.4);
  //: **The night lifts and last night's fire goes out.** The mirror of the
  //: bell and asked for the same way -- see the note there.
  const stock = traders.flatMap((n, hi) => ["a", "b"]
    .map((k) => island.getObjectByName(`hut_${n}_crate_${k}`))
    .filter(Boolean)
    .map((cr, i) => {
      borrow(c, cr);
      return { cr, k: (hi * 2 + i) / Math.max(2, traders.length * 2),
               y0: cr.position.y, r0: cr.rotation.y };
    }));

  //: **No banner runs back up a pole, because there is no pole.** This used to
  //: end with a flag rising at every settlement, which was the oldest way there
  //: is of saying a day has started -- and then the huts lost their flags, so
  //: that a flag on this island means one thing and one thing only. What is
  //: left is the larger half and always was: the night lifting off the whole
  //: frame, the light coming back up on the model, and every trader's crates
  //: coming back out of the ground.

  //: **The dawn used to cross the island from the centre outward**, and that
  //: ring is gone with the rest of them. What a new day looks like is already
  //: on screen and is bigger than any ring: the night lifts off the whole
  //: frame, the light comes back up on the model, and every banner runs back
  //: up its pole. A ring going out from the middle was a fourth thing saying
  //: it, and the one a viewer called distracting.
  //

  c.update = (t) => {
    const out = easeInOut(win(t, 0.2, 2.8));
    //: The night's fire going out takes its light with it, which is the
    //: largest thing on screen at dawn. It **falls to** the new day's value
    //: rather than being pushed under it: the day resets to zero at an
    //: episode boundary, so the curve already says the fire is out and a clip
    //: subtracting from that would animate nothing at all.
    life?.hold(1 - out);
    life?.flare((1 - out) * 0.95);
    stock.forEach(({ cr, k, y0, r0 }) => {
      const drain = easeIn(win(t, 0.1 + k * 0.5, 1.7 + k * 0.5));
      const back = easeOut(win(t, 2.6 + k * 0.4, 4.0 + k * 0.4));
      const sc = Math.max(0.001, 1 - drain + back * drain);
      cr.scale.setScalar(sc);
      cr.position.y = y0 - (1 - sc) * 0.28;
      cr.rotation.y = r0 + drain * 2.4 * (1 - back);
    });
  };
  return c;
}
