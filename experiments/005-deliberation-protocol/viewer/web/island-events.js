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
import { M, GRASS_Y, goodMat, seatMat, onMeadow } from "./island3d.js";

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

//: Everything a clip spawns is bigger than the delivered clip drew it.
//: The clips were watched one at a time in a frame about two units across;
//: the island is eight, and half of it is behind the traders' cards. A crate
//: the size the diorama used is four pixels on a phone -- present, but not
//: something a spectator would ever notice crossing the ground.
const PROP = 1.7;

/**
 * A flat ring on the ground, for a pulse, a shock or a seal.
 *
 * Fat on purpose. A ring is the cheapest thing on the island that covers real
 * area, and a hairline one at a third opacity -- which is what the diorama
 * used -- is a few dozen pixels nobody will ever catch.
 */
function ring(material, radius = 0.3, y = 0.05) {
  return mesh(new THREE.TorusGeometry(radius, 0.1, 8, 56), material,
    "ring", [0, y, 0], [Math.PI / 2, 0, 0]);
}

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
  return { root: new THREE.Group(), dur, mine: [], update() {} };
}

/** A material this clip owns, and will dispose with itself. */
function own(c, material) {
  c.mine.push(material);
  return material;
}

//: The market's plaza, and how far its roof reaches. Anything a clip lays on
//: the ground at the centre starts outside this, because a ring that begins
//: under the roof is a ring nobody sees begin.
const MARKET = new THREE.Vector3(0.45, GRASS_Y, 0.55);
const MARKET_R = 1.45;

/**
 * A spot beside a settlement, on the grass.
 *
 * Along the hut's own side rather than on the line to the market: a prop set
 * out toward the middle from a hut two and a half units out lands *on the
 * market*, which is where the first cut of this put every offer and every
 * refusal -- under the plaza roof, invisible.
 */
function beside(home, side = 1.15, out = 0.25) {
  const away = new THREE.Vector3(MARKET.x - home.x, 0, MARKET.z - home.z).normalize();
  const x = home.x + -away.z * side + away.x * out;
  const z = home.z + away.x * side + away.z * out;
  const [cx, cz] = onMeadow(x, z, 0.35);
  return { at: new THREE.Vector3(cx, GRASS_Y, cz), face: Math.atan2(away.x, away.z) };
}

/**
 * The event, staged on the island -- or `null` if this is not one the island
 * has anything to say about.
 *
 * @param {object} event  a reduced board event: `kind`, and whatever that kind
 *                        carries (`trader`, `made`, `maker`, `taker`, ...)
 * @param {object} world  `{ island, anchors, traders, goods }` from the build
 */
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
 * Production: the site works, and what it made walks home.
 *
 * The site's own parts are animated in place -- the fields ripen and are cut,
 * the racks fill, the quarry cart runs, the pans dry -- because they are
 * already standing where that good is made. What the clip adds is the yield:
 * a crate per good produced, which rises at the site and crosses the island to
 * the settlement that produced it.
 */
function produced(event, { island, anchors, traders, goods }) {
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
    // A ring on the ground where the work happened. The site's own parts move,
    // but a rack or a field plot is small and half behind a tree: this is what
    // says *here*, and it is the cheapest area on the island.
    const glow = own(c, clone(goodMat(good, goods.indexOf(good)),
      { transparent: true, opacity: 0 }));
    const mark = ring(glow, 0.75);
    mark.position.set(from.x, from.y + 0.08, from.z);
    c.root.add(mark);
    works.push((t) => {
      const p = win(t, 0.1, 2.4);
      mark.scale.set(0.6 + easeOut(p) * 0.9, 0.6 + easeOut(p) * 0.9, 1);
      glow.opacity = 0.75 * Math.sin(Math.PI * p) ** 0.8;
    });
    // Bigger the more was made, but only a little: this says which good and
    // roughly how much, and a crate the size of a hut would say neither.
    const size = (0.16 + Math.min(0.9, qty) * 0.09) * PROP;
    const box = crate(own(c, goodMat(good, goods.indexOf(good))), size);
    c.root.add(box);
    legs.push({ box, wake: trail(c, goodMat(good, goods.indexOf(good))),
                from: from.clone().setY(from.y + 0.25), to: home.clone().setY(GRASS_Y + 0.2) });
  }
  if (!legs.length) return null;

  const dustMat = own(c, clone(M.sand, { transparent: true, opacity: 0 }));
  const dust = mesh(new THREE.CircleGeometry(0.22 * PROP, 20), dustMat, "dust",
    [home.x, GRASS_Y + 0.03, home.z], [-Math.PI / 2, 0, 0]);
  c.root.add(dust);

  c.update = (t) => {
    for (const w of works) w(t);
    legs.forEach(({ box, wake, from, to }, i) => {
      const t0 = 0.9 + i * 0.35;
      const pop = easeOut(win(t, t0 - 0.6, t0));
      const p = easeInOut(win(t, t0, t0 + 1.9));
      box.visible = pop > 0.01;
      box.scale.setScalar(pop);
      box.position.lerpVectors(from, to, p);
      box.position.y += Math.sin(p * Math.PI) * 0.75;
      box.rotation.set(p * 4.2, p * 3.1, p * 1.8);
      wake(from, to, p, 0.75);
      const land = win(t, t0 + 1.8, t0 + 2.3);
      if (land > 0) {
        box.position.y = GRASS_Y + 0.1 + Math.abs(Math.sin(land * Math.PI * 2)) * 0.14 * (1 - land);
        dustMat.opacity = Math.max(dustMat.opacity, 0.4 * (1 - land));
        dust.scale.setScalar(1 + land * 1.5);
      }
      const gone = win(t, t0 + 2.6, t0 + 3.2);
      if (gone > 0) box.scale.setScalar(pop * (1 - gone));
    });
    if (t < 0.9) dustMat.opacity = 0;
  };
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
      p.material = own(c, p.material.clone());
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
    const cloths = part(/_cloth$/).map((p, i) => ({ p, i, y0: p.position.y, s0: p.scale.y }));
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
    const spoil = part(/^quarry_spoil_/).map((s, i) => ({ s, i, y0: s.position.y }));
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
      b.material = own(c, b.material.clone());
      return { b, k: i / 4, y0: b.position.y, s0: b.scale.y };
    });
    const heap = named("salt_heap");
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
    return [(t) => nets.forEach((n, i) => {
      const haul = win(t, 0.2 + i * 0.3, 2.4);
      n.rotation.x = Math.sin(t * 2.6 + i) * 0.22 * haul;
      n.scale.y = 1 + Math.sin(t * 3.1 + i * 2) * 0.08 * haul;
    })];
  }
  // The plainly-built works: the kiln runs and the shed shakes with it.
  const kiln = named("works_kiln"), shed = named("works_shed");
  return [(t) => {
    const run = win(t, 0.2, 3.0) * (1 - win(t, 3.0, 3.8));
    if (kiln) kiln.scale.set(1 + Math.sin(t * 12) * 0.03 * run, 1, 1 + Math.sin(t * 12) * 0.03 * run);
    if (shed) shed.rotation.z = Math.sin(t * 17) * 0.012 * run;
  }];
}

/** An offer: a post goes up beside the maker's hut and a notice unrolls on it. */
function offered(event, { anchors, traders }) {
  const home = anchors[event.maker];
  if (!home) return null;
  const c = clip(3.0);
  const spot = beside(home);
  const post = bannerPost(own(c, seatMat(event.maker, traders.indexOf(event.maker))));
  post.position.copy(spot.at);
  post.rotation.y = spot.face;
  c.root.add(post);

  const scrollMat = own(c, clone(M.cloth));
  const scroll = mesh(new THREE.BoxGeometry(0.03, 0.5, 0.56), scrollMat, "notice", [0, 0.95, 0.28]);
  post.add(scroll);

  const pulseMat = own(c, clone(M.glass, { transparent: true, opacity: 0.5 }));
  const pulse = ring(pulseMat, 0.42);
  pulse.position.set(post.position.x, GRASS_Y + 0.05, post.position.z);
  c.root.add(pulse);

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
    const p = win(t, 0.8, 2.8);
    pulse.scale.set(1 + easeOut(p) * 1.9, 1 + easeOut(p) * 1.9, 1);
    pulseMat.opacity = 0.8 * (1 - p ** 2);
    // Taken down at the end rather than left standing: the rope on the card is
    // what says an offer is still open, and two things saying it disagree the
    // moment one of them is a second behind.
    const down = win(t, 2.6, 3.0);
    post.scale.y = Math.max(0.02, rise) * (1 - down);
  };
  return c;
}

/** A settlement: the goods actually cross the island, both ways. */
function settled(event, { anchors, goods }) {
  const a = anchors[event.maker], b = anchors[event.taker];
  if (!a || !b) return null;
  const c = clip(4.2);
  const from = a.clone().setY(GRASS_Y + 0.45), to = b.clone().setY(GRASS_Y + 0.45);

  const legs = [];
  const push = (bundle, src, dst, base) => {
    Object.entries(bundle || {}).filter(([, q]) => q > 1e-9)
      .forEach(([good, q], i) => {
        const box = crate(own(c, goodMat(good, goods.indexOf(good))),
          (0.15 + Math.min(0.9, q) * 0.08) * PROP);
        c.root.add(box);
        legs.push({ box, wake: trail(c, goodMat(good, goods.indexOf(good))),
                    a: src, b: dst, t0: base + i * 0.3 });
      });
  };
  push(event.give, from, to, 0.25);
  push(event.want, to, from, 0.55);
  if (!legs.length) return null;

  const dustMat = own(c, clone(M.sand, { transparent: true, opacity: 0 }));
  const dust = legs.map((l) => {
    const d = mesh(new THREE.CircleGeometry(0.18 * PROP, 20), own(c, dustMat.clone()), "dust",
      [l.b.x, GRASS_Y + 0.03, l.b.z], [-Math.PI / 2, 0, 0]);
    c.root.add(d);
    return d;
  });

  // The seal goes down where the deal was struck, which on this island is the
  // market -- not at either hut, because it belongs to neither of them.
  const sealMat = own(c, clone(M.glass, { transparent: true, opacity: 0.6 }));
  const seal = ring(sealMat, MARKET_R);
  seal.position.set(MARKET.x, GRASS_Y + 0.08, MARKET.z);
  c.root.add(seal);

  c.update = (t) => {
    legs.forEach((l, i) => {
      const p = easeInOut(win(t, l.t0, l.t0 + 1.6));
      l.box.visible = t > l.t0 - 0.01;
      l.box.position.lerpVectors(l.a, l.b, p);
      l.box.position.y = GRASS_Y + 0.45 + Math.sin(p * Math.PI) * 0.85;
      l.box.rotation.set(p * 5, p * 3.4, p * 2);
      l.wake(l.a, l.b, p, 0.85);
      const land = win(t, l.t0 + 1.5, l.t0 + 2.0);
      if (land > 0) {
        l.box.position.y = GRASS_Y + 0.2
          + Math.abs(Math.sin(land * Math.PI * 2)) * 0.14 * (1 - land);
        dust[i].material.opacity = 0.42 * (1 - land);
        dust[i].scale.setScalar(1 + land * 1.6);
      } else dust[i].material.opacity = 0;
      const gone = win(t, l.t0 + 2.4, l.t0 + 3.0);
      if (gone > 0) l.box.scale.setScalar(1 - gone);
    });
    const s = win(t, 2.0, 3.8);
    seal.scale.set(1 + easeOut(s) * 1.2, 1 + easeOut(s) * 1.2, 1);
    sealMat.opacity = 0.85 * (1 - s ** 2);
  };
  return c;
}

/** A refusal: the notice is torn up where it was posted. */
function refused(event, { anchors, traders }) {
  const home = anchors[event.trader];
  if (!home) return null;
  const c = clip(3.0);
  const spot = beside(home);
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
    [post.position.x, GRASS_Y + 0.04, post.position.z]);
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

/** The bell: the market's own bell rings, and the island hears it. */
function belled(event, { island, anchors, traders }) {
  const c = clip(4.2);
  const bell = island.getObjectByName("market_bell");
  const y0 = bell?.position.y ?? 0;

  const shockMat = own(c, clone(M.surf, { transparent: true, opacity: 0.55 }));
  const shocks = [0, 1, 2].map(() => {
    const s = ring(own(c, shockMat.clone()), MARKET_R);
    s.position.set(MARKET.x, GRASS_Y + 0.09, MARKET.z);
    c.root.add(s);
    return s;
  });

  // Every settlement's own banner goes up and away with the offers that
  // lapsed. Restored at the end -- these are the island's, not the clip's.
  const flags = traders.map((n) => island.getObjectByName(`hut_${n}_banner`))
    .filter(Boolean).map((b) => ({ b, y0: b.position.y, r0: b.rotation.y }));

  c.update = (t) => {
    const swing = win(t, 0, 2.2);
    if (bell) {
      bell.rotation.z = Math.sin(t * 9) * 0.5 * (1 - swing) ** 1.4;
      bell.position.y = y0 + Math.sin(t * 26) * 0.006 * (1 - swing);
    }
    shocks.forEach((s, i) => {
      const p = win(t, 0.05 + i * 0.34, 2.6 + i * 0.34);
      s.scale.set(1 + easeOut(p) * 1.55, 1 + easeOut(p) * 1.55, 1);
      s.material.opacity = 0.85 * (1 - p ** 2);
    });
    flags.forEach(({ b, y0: by, r0 }, i) => {
      const ev = easeIn(win(t, 1.4 + i * 0.18, 3.4 + i * 0.18));
      const back = easeOut(win(t, 3.5, 4.2));
      b.position.y = by + (ev * 0.9) * (1 - back);
      b.rotation.y = r0 + ev * 3.2 * (1 - back);
    });
  };
  c.restore = () => {
    if (bell) { bell.rotation.z = 0; bell.position.y = y0; }
    flags.forEach(({ b, y0: by, r0 }) => { b.position.y = by; b.rotation.y = r0; });
  };
  return c;
}

/** A new day: last day's stock goes, and the flags run back up. */
function opened(event, { island, anchors, traders }) {
  const c = clip(4.4);
  const stock = traders.flatMap((n, hi) => ["a", "b"]
    .map((k) => island.getObjectByName(`hut_${n}_crate_${k}`))
    .filter(Boolean)
    .map((cr, i) => ({ cr, k: (hi * 2 + i) / Math.max(2, traders.length * 2),
                       y0: cr.position.y, r0: cr.rotation.y })));

  // The banners run back up their own poles. A floating bar over each hut was
  // the first cut of this and it read as two planks in the sky: the island has
  // a flag on a pole at every settlement already, and a flag going up is the
  // oldest way there is of saying a day has started.
  const flags = traders.map((n) => island.getObjectByName(`hut_${n}_banner`))
    .filter(Boolean).map((b) => ({ b, y0: b.position.y }));

  // And the day itself, crossing the island from the market outward. This is
  // the part that is actually large enough to notice at a glance.
  const dawnMat = own(c, clone(M.glass, { transparent: true, opacity: 0 }));
  const sweep = ring(dawnMat, MARKET_R);
  sweep.position.set(MARKET.x, GRASS_Y + 0.09, MARKET.z);
  c.root.add(sweep);

  c.update = (t) => {
    const d = win(t, 0.1, 2.4);
    sweep.scale.set(1 + easeOut(d) * 1.55, 1 + easeOut(d) * 1.55, 1);
    dawnMat.opacity = 0.8 * (1 - d ** 2);
    stock.forEach(({ cr, k, y0, r0 }) => {
      const drain = easeIn(win(t, 0.1 + k * 0.5, 1.7 + k * 0.5));
      const back = easeOut(win(t, 2.6 + k * 0.4, 4.0 + k * 0.4));
      const sc = Math.max(0.001, 1 - drain + back * drain);
      cr.scale.setScalar(sc);
      cr.position.y = y0 - (1 - sc) * 0.28;
      cr.rotation.y = r0 + drain * 2.4 * (1 - back);
    });
    flags.forEach(({ b, y0 }, i) => {
      // Down while the day's stock drains, then up.
      const down = easeInOut(win(t, 0.2 + i * 0.15, 1.4 + i * 0.15));
      const up = easeOut(win(t, 2.2 + i * 0.25, 3.8 + i * 0.25));
      b.position.y = y0 - 0.62 * (down - up);
      b.rotation.y = Math.sin(t * 4.4) * 0.2 * up * (1 - win(t, 3.8, 4.4));
    });
  };
  // Put back what was borrowed, exactly: the huts' crates are built at an
  // angle each, and a restore that squared them up would leave the island
  // slightly rearranged after every new day.
  c.restore = () => {
    stock.forEach(({ cr, y0, r0 }) => {
      cr.scale.setScalar(1);
      cr.position.y = y0;
      cr.rotation.y = r0;
    });
    flags.forEach(({ b, y0 }) => { b.position.y = y0; b.rotation.y = 0; });
  };
  return c;
}
