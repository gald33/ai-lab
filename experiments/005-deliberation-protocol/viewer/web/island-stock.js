// The goods, standing on the island.
//
// **Nothing pops or vanishes except when it is created or consumed.** Until
// now every good on this island was a clip prop: a crate appeared when a
// production receipt arrived, crossed to the hut, and shrank out of existence
// three seconds later. The island held nothing between events, so a trader's
// stock existed only on its card and the ground told you nothing.
//
// This is the other half. Every trader has a **yard** beside its hut, and what
// it holds stands there as boxes. A production *creates* boxes at the site
// that made them and they walk home. A settled exchange *moves the same boxes*
// along the offer's own line and they stack in the other trader's yard. The
// bell *consumes* them. Those three are the only times the count changes, and
// each of them is a thing that happened on the board.
//
// The one cut that is not an animation is a **scrub**: jump to the middle of a
// replay and the island has to be what the board says it is at that frame,
// with no journey to show. `rest()` is that cut, and it is the only path that
// puts a box down without one.
//
// ## How many boxes is a holding
//
// A box is a unit of the round's own largest holding of that good, so six of
// them is the most anybody ever had. **Not capacity** -- which is what a first
// reading of this asks for -- because capacity is private to a trader and the
// page never has it live, and a denominator that exists in a replay and not on
// a live board would make a box mean two different things. The round's biggest
// settled holding is available in both, comes from settled state rather than
// from anything an agent said, and is the same rule the card's own shelf scale
// already uses.
//
// Any non-zero holding is at least one box: a trader with a little of
// something has some of it, and rounding that to an empty yard would say it
// has none.

import * as THREE from "./vendor/three/three.module.js";
import { GOOD_COLOURS, onMeadow } from "./island3d.js";
//: What a good looks like when the island draws one, from the module the site
//: flags read too: a crate in a yard and the flag over the site that made it
//: are the same claim and must wear the same mark.
import { face } from "./good-face.js";

//: A box's side, in island units. A hut is about 0.8 across at the scale the
//: island draws it, so this is a crate a person could lift and a stack of six
//: is a yard rather than a second building.
const BOX = 0.13;
//: The most boxes one good's pile ever shows. Six is two layers of a 2x2 and a
//: bit -- enough that a big holding reads as bigger, few enough that a yard
//: stays a yard.
const MOST = 6;
//: How far the pile stands off the hut, and how far apart two goods' piles are.
//: `OUT` clears the hut: its roof reaches half a unit out from the middle of
//: it, so a yard any closer stacks crates through the thatch. It was set
//: against the banner pole as well, which the hut no longer has -- kept as it
//: is, because a yard tight against the wall reads as part of the building.
const OUT = 0.86, PITCH = 0.3;

/**
 * Where the yard stands, and which way it runs.
 *
 * Behind the hut as seen from the fire: the door faces the middle of the
 * island because that is where a settlement with one fire in front of it
 * looks, and a stack of crates across the front would cover the door, which
 * is now painted in the trader's own colour and is half of what says whose
 * hut this is.
 */
function yardAt(home, centre, ground) {
  const away = new THREE.Vector3(home.x - centre.x, 0, home.z - centre.z);
  if (!away.lengthSq()) away.set(1, 0, 0);
  away.normalize();
  const flank = new THREE.Vector3(-away.z, 0, away.x);
  //: **Behind the hut if there is a behind.** A settlement sits on an annulus
  //: that reaches most of the way to the meadow's rim, so for some seats the
  //: ground behind it is sea -- and `onMeadow`, which is what keeps a yard on
  //: the grass, then pulls the whole thing back on top of the hut it was meant
  //: to stand beside. Found by a check counting boxes inside huts.
  //:
  //: So the bearings are tried in order of preference and the first one with
  //: room wins: behind, then either flank, then in front. Only a hut with no
  //: room on any side falls through, and there is nowhere better to put it.
  const tries = [away, flank, flank.clone().negate(), away.clone().negate()];
  let best = null;
  for (const dir of tries) {
    const [x, z] = onMeadow(home.x + dir.x * OUT, home.z + dir.z * OUT, 0.75);
    const room = Math.hypot(x - home.x, z - home.z);
    if (!best || room > best.room) best = { x, z, dir, room };
    if (room > OUT * 0.86) break;
  }
  const { x, z, dir } = best;
  return { at: new THREE.Vector3(x, ground(x, z), z),
           side: new THREE.Vector3(-dir.z, 0, dir.x), away: dir };
}

/**
 * The goods a round ever put in one pair of hands, per good.
 *
 * One pass over the whole timeline, like the card's shelf scale: a ceiling
 * recomputed per frame would make a box mean something different from one
 * message to the next, and a stock that never moved would grow as its
 * neighbours shrank.
 */
export function ceilings(timeline) {
  const top = {};
  for (const good of timeline.goods) top[good] = 0;
  for (const frame of timeline.frames) {
    for (const t of timeline.traders) {
      for (const good of timeline.goods) {
        top[good] = Math.max(top[good], frame.state.stocks?.[t]?.[good] || 0);
      }
    }
  }
  return top;
}

/**
 * The standing stock: a yard of boxes beside every hut.
 *
 * @param {THREE.Group} island
 * @param {object} world  `{ traders, goods, anchors, ground }` from the build
 */
export function standing(island, { traders, goods, anchors, ground }) {
  const root = new THREE.Group();
  root.name = "yards";
  island.add(root);

  const geo = new THREE.BoxGeometry(BOX, BOX, BOX);
  const mats = {};
  const yards = {};
  goods.forEach((good, i) => {
    const colour = GOOD_COLOURS[i % GOOD_COLOURS.length];
    const mark = face(good, colour);
    mats[good] = new THREE.MeshStandardMaterial(
      mark ? { map: mark, roughness: 0.85 } : { color: colour, roughness: 0.85 });
  });
  for (const t of traders) {
    if (!anchors[t]) continue;
    yards[t] = { ...yardAt(anchors[t], anchors.fire, ground), held: {} };
    for (const good of goods) yards[t].held[good] = [];
  }

  //: Raised by the page from the timeline. Zero until then, which makes every
  //: non-zero holding one box -- the honest reading when nothing has said how
  //: big a big holding is on this island.
  let top = Object.fromEntries(goods.map((g) => [g, 0]));

  /** Where the k-th box of a good stands in a trader's yard. */
  const slot = (t, good, k) => {
    const y = yards[t];
    const lane = goods.indexOf(good) - (goods.length - 1) / 2;
    const row = Math.floor(k / 2) % 2, col = k % 2, tier = Math.floor(k / 4);
    const p = y.at.clone()
      .addScaledVector(y.side, lane * PITCH + (col - 0.5) * (BOX * 1.08))
      .addScaledVector(y.away, (row - 0.5) * (BOX * 1.08));
    p.y = ground(p.x, p.z, y.at.y) + BOX / 2 + tier * BOX * 1.02;
    return p;
  };

  const box = (good) => {
    const m = new THREE.Mesh(geo, mats[good]);
    m.name = `box_${good}`;
    m.castShadow = true;
    m.receiveShadow = true;
    root.add(m);
    return m;
  };

  /** How many boxes a quantity of a good is worth. */
  const want = (good, qty) => {
    if (!(qty > 1e-9)) return 0;
    const unit = top[good] > 1e-9 ? top[good] / MOST : qty;
    return Math.max(1, Math.min(MOST, Math.round(qty / unit)));
  };

  /** Put a trader's pile of one good back in its slots. */
  const tidy = (t, good) => {
    yards[t].held[good].forEach((m, k) => {
      m.position.copy(slot(t, good, k));
      m.rotation.set(0, 0, 0);
      m.scale.setScalar(1);
    });
  };

  return {
    root,
    slot,
    /** The round's ceiling per good, from the page's timeline. */
    ceil(next) {
      top = { ...top, ...next };
    },
    count: (t, good) => yards[t]?.held[good].length ?? 0,
    want,

    /**
     * The island is what the board says it is at this frame, with no journey.
     *
     * The cut, and the only way a box is put down or taken away without one.
     * `keep` names the (trader, good) pairs a clip is animating right now, so
     * that a settlement in flight is not snapped to its destination under the
     * boxes crossing to it. `"all"` is the bell, which is eating the lot.
     */
    rest(stocks, keep = null) {
      if (keep === "all") return;
      for (const t of traders) {
        const y = yards[t];
        if (!y) continue;
        for (const good of goods) {
          if (keep?.has(`${t}:${good}`)) continue;
          const pile = y.held[good];
          const n = want(good, stocks?.[t]?.[good] || 0);
          while (pile.length > n) root.remove(pile.pop());
          while (pile.length < n) pile.push(box(good));
          tidy(t, good);
        }
      }
    },

    /**
     * New boxes, made where the good is made. Handed back loose -- the clip
     * flies them home and calls `put` when they land.
     */
    mint(good, n, at) {
      return Array.from({ length: n }, () => {
        const m = box(good);
        m.position.copy(at);
        return m;
      });
    },

    /** Take boxes off the top of a pile, to be flown somewhere. */
    take(t, good, n) {
      const pile = yards[t]?.held[good];
      if (!pile) return [];
      return pile.splice(Math.max(0, pile.length - n), n);
    },

    /** Boxes arrive in a yard and take the next free slots. */
    put(t, good, boxes) {
      const pile = yards[t]?.held[good];
      if (!pile) return boxes.map(() => null);
      const at = boxes.map((m, i) => slot(t, good, pile.length + i));
      pile.push(...boxes);
      return at;
    },

    /** Where a pile's next box would land, without adding one. */
    next: (t, good, i = 0) => slot(t, good, (yards[t]?.held[good].length ?? 0) + i),

    /**
     * What is standing in every yard, by trader and good.
     *
     * The island's own answer to "what is on the ground", which is the thing a
     * check has to compare against the board. Read-only and cheap.
     */
    tally: () => Object.fromEntries(traders.filter((t) => yards[t]).map((t) =>
      [t, Object.fromEntries(goods.map((g) => [g, yards[t].held[g].length]))])),

    /** Every box in a trader's yard, for a clip that consumes the lot. */
    all: (t) => goods.flatMap((good) => yards[t]?.held[good] ?? []),

    /** The bell: what was held is eaten. Boxes go because they are consumed. */
    clear(t) {
      for (const good of goods) {
        const pile = yards[t]?.held[good];
        if (!pile) continue;
        while (pile.length) root.remove(pile.pop());
      }
    },

    dispose() {
      island.remove(root);
      geo.dispose();
      for (const m of Object.values(mats)) m.dispose();
    },
  };
}
