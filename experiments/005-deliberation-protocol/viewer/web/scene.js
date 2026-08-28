// The island, drawn.
//
// Every number on this screen came out of a manager receipt. Nothing here
// computes an outcome, nothing here knows a taste or a capacity, and nothing
// here writes anywhere. It is a painting of `reducer.js`'s state.
//
// Colour never carries identity on its own: goods sit in a fixed order on every
// shelf, and a parcel in flight wears its glyph and its quantity. The palette
// passes the adjacent-pair gates for four series; it does not pass all-pairs,
// which is exactly why position and glyph do the identifying.
//
// The scenery is generated rather than hand-drawn: one wobbled ellipse gives
// the coast, and the surf and the wet sand are the same ring at other scales.
// Three hand-written paths would have to be kept in sync by eye, and would
// drift the first time the island changed size.

import { utilityOf } from "./utility.js";
//: Whose an offer is, in the seat's own colour -- the same colour the island
//: paints that trader's hut and boat with, so a pill sliding off a roof wears
//: the colour of the roof it left. It takes the seat *count* as well as the
//: seat: past six the ring is generated, and six colours handed round a table
//: of seven puts two huts in one colour.
import { seatRing } from "./seats.js";

const NS = "http://www.w3.org/2000/svg";

//: Iron's pickaxe is U+26CF, which is a *text* codepoint by default: without
//: the variation selector it renders as a black monochrome glyph and vanishes
//: into the agent card's dark background. The trailing U+FE0F asks for the
//: colour emoji, like every other good here already gets by default.
export const GLYPH = {
  bread: "🍞", cloth: "🧵", iron: "⛏️", salt: "🧂",
  fish: "🐟", grain: "🌾", timber: "🪵",
};

const SLOT = ["--good-1", "--good-2", "--good-3", "--good-4",
              "--good-5", "--good-6", "--good-7"];

//: How long the pill takes to travel the rope, in ms, and how long the rope
//: then takes to go. The fade is CSS (`.rope.delivered`), and this only has to
//: outlast it so a rope is not still fading when its pill is asked to move.
const SLIDE = 1100;
//: How quickly a pill closes the gap to where it belongs, as the time constant
//: of an exponential ease: about 95% of the way there in three of these. Short
//: enough that a re-stacked pile has settled before a viewer looks for it, long
//: enough to read as a move rather than a jump.
const GLIDE = 110;
//: The longest gap that counts as animation: one frame on a slow machine. See
//: `glideTo` -- without this a pill that has been sitting still teleports the
//: first time its target moves.
const GLIDE_CAP = 48;

const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * How long each event needs on screen, in ms.
 *
 * It lives here because it mirrors the durations in `play()` below, and a copy
 * of it anywhere else would drift the first time one of those changed.
 * `feeds.js` reads it to decide how long to hold a frame: an animation that
 * takes a second is worth nothing if the next six events start during it, and
 * at the default 4x the player was stepping every 35ms.
 *
 * A kind that is not here is a frame with nothing to watch, and is not held.
 */
/**
 * The exchange's middle leg, in milliseconds from the moment the frame paints:
 * when a bundle's boxes set off across the island, and when they are standing
 * in the new owner's yard.
 *
 * **One schedule, read by both engines.** The boxes are three.js and the
 * symbols that fly off them are SVG, and the two were keeping separate copies
 * of the same choreography in different units -- `island-events.js` in seconds
 * off its own clip clock, `hands()` in milliseconds off a `CROSS` constant.
 * They disagreed, and the disagreement was visible: the symbols left for the
 * gaining card **30ms before the boxes touched down** and a full half-second
 * before they had finished settling onto the pile, so a card filled from goods
 * that were still in the air. Reported by eye.
 *
 * `island-events.js` imports this and divides by a thousand. That is the same
 * arrangement `feeds.js` already has with `DWELL` -- the durations are named
 * once, where the animation that spends them is written, and everything that
 * has to keep step with them reads them rather than mirroring them.
 */
export const CARRY = {
  off: 850,      // the boxes set off, the losing card having emptied into them
  step: 300,     // and the next good's boxes follow this much later
  spread: 240,   // one good's boxes leave across this window, however many
  cross: 1500,   // over the island
  land: 420,     // and the hop onto the new owner's pile
  rest: 160,     // a beat standing there before the symbols rise off them
  back: 200,     // the return bundle sets off this much after the first
};

/**
 * When the `i`-th good of a bundle is certainly standing in the new yard.
 *
 * **Exact, and that is the point.** The boxes of one good are spread across
 * `CARRY.spread` however many there are -- `k / (n - 1)` of it, and a lone box
 * takes the whole of it -- so the *last* box of a good always leaves at
 * `spread`, whether that good came to one box or six. The card's symbols do
 * not know how many boxes a quantity came to, and counting them would put the
 * stock's arithmetic inside the drawing.
 *
 * `CARRY.rest` is why this is not the landing itself. Cued at the instant the
 * last box stopped, the symbol left on the same frame the hop finished, which
 * reads as the two being one motion rather than one following the other.
 */
export const carriedBy = (i, back = false) =>
  (back ? CARRY.back : 0) + CARRY.off + i * CARRY.step + CARRY.spread
  + CARRY.cross + CARRY.land + CARRY.rest;

/**
 * The other journey a good makes: **out of the site that made it, home.**
 *
 * The same arrangement as `CARRY`, for the same reason. Production had no
 * shared table at all: `island-events.js` flew its crates off hard-coded
 * seconds -- 0.9 and 0.3 apart, 1.9 across, landing at 2.4 -- while
 * `scene.js:produce` filled the shelf off `DWELL.produced` minus 300, and the
 * two had never been the same schedule. The symbols left the yard inside the
 * first second and the crates were still walking home at two and a half, so
 * the card filled from goods that had not arrived yet. **The exact defect
 * `CARRY` was written to end, at the other event.** Reported by eye, twice --
 * once as the trades looking right and production not.
 *
 * So a production is three legs like an exchange, and the last one is the same
 * motion: the crate is made at the site, it walks home, it lands, it opens,
 * and the symbol rises out of it into the bar.
 */
export const MAKE = {
  work: 900,     // the site works before anything comes out of it
  step: 300,     // and the next good's crates are made this much later
  spread: 240,   // one good's crates leave across this window, however many
  fly: 1900,     // across the island, from the site to the yard
  land: 600,     // the hop onto the pile
  rest: 160,     // a beat standing there before the lid comes up
};

/** When the `i`-th good of a receipt is certainly standing in its yard. */
export const madeBy = (i) =>
  MAKE.work + i * MAKE.step + MAKE.spread + MAKE.fly + MAKE.land + MAKE.rest;

//: The arriving boxes emptying into the gaining card: the third leg.
//: Exported for the same reason `CARRY` is -- the boxes hold their lids open
//: for exactly as long as the symbols are climbing out of them, and a second
//: copy of this number in `island-events.js` is the drift this file already
//: had once.
export const IN_LEG = 820;

export const DWELL = {
  //: Three legs now, not one: the losing card empties into its own boxes, the
  //: boxes cross the island, and the arriving boxes fill the gaining card. It
  //: was 2100 when the whole exchange was parcels crossing the square.
  //:
  //: **The floor, for one good each way.** A real bundle is measured by
  //: `dwellFor`, which knows how many goods are in it: holding every exchange
  //: for the worst case a board allows -- seven goods, 7.6s -- would spend that
  //: on every two-good trade as well.
  settled: carriedBy(0, true) + IN_LEG,
  //: The floor, for a receipt of one good: the site works, the crate walks
  //: home and lands, and the symbol rises off it. `dwellFor` measures a wider
  //: receipt, exactly as it does a wider bundle.
  produced: madeBy(0) + IN_LEG,
  refused: 1500,   // one badge, rising
  said: 1300,      // one bubble, rising
  bell: 3600,      // the sun goes down. Not a thing to hurry
  open: 2400,      // and comes back up
  over: 2400,
  fault: 2400,
};

/**
 * The floor for one event, honouring a viewer who asked for less motion.
 *
 * Nothing moves for them, so holding the frame would be making them wait for a
 * still picture -- `play()` collapses every animation to 1ms for the same
 * reason.
 *
 * Takes the event rather than its kind because one kind draws two things. A
 * `said` that is an **attempt** -- `PROPOSE to=T1 give=...` -- gets no bubble:
 * what it attempted shows as the receipt or the refusal that follows, and
 * drawing both would say it twice. So it gets no dwell either; holding a frame
 * that draws nothing is just waiting.
 */
export function dwellFor(event, isStill = false) {
  if (isStill || !event) return 0;
  if (event.kind === "said" && event.attempt) return 0;
  //: Measured off the bundle rather than taken off the table: the last leg of
  //: an exchange starts when the last of its boxes has landed, and that is
  //: `CARRY.step` later for every good in it.
  //: A receipt is measured the same way an exchange is: its last crate lands
  //: `MAKE.step` later for every good in it, and the symbol leaves from there.
  if (event.kind === "produced") {
    const n = Object.values(event.made || {}).filter((q) => q > 1e-9).length;
    return Math.max(DWELL.produced, madeBy(Math.max(0, n - 1)) + IN_LEG);
  }
  if (event.kind === "settled") {
    const wide = (b) => Object.values(b || {}).filter((q) => q > 1e-9).length;
    return Math.max(DWELL.settled, ...[[wide(event.give), false],
                                       [wide(event.want), true]]
      .filter(([n]) => n > 0)
      .map(([n, back]) => carriedBy(n - 1, back) + IN_LEG));
  }
  return DWELL[event.kind] || 0;
}

function el(name, attrs = {}, children = []) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    node.setAttribute(k, String(v));
  }
  for (const c of [].concat(children)) {
    node.append(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

//: Two traders is the shape every board on disk has, and the one the canvas is
//: proportioned for. More is allowed by the rules and has never been drawn.
const BASE_W = 1000, BASE_H = 560;

/**
 * A coast that does not read as a logo.
 *
 * Fixed wobble rather than random: the same board must draw the same island
 * on every reload, and a shape that shifts under a scrub bar is a distraction
 * dressed up as texture.
 */
const WOBBLE = [1.000, 0.988, 1.012, 0.994, 1.018, 0.986, 1.008, 0.978, 1.014,
                0.992, 1.020, 0.984, 1.006, 0.990, 1.016, 0.982, 1.010, 0.996,
                1.018, 0.988, 1.004, 0.980, 1.014, 0.994];

export function coast(g, k = 1) {
  const n = WOBBLE.length;
  return Array.from({ length: n }, (_, i) => {
    const a = (i / n) * 2 * Math.PI;
    return [g.cx + g.rx * k * WOBBLE[i] * Math.cos(a),
            g.ly + g.ry * k * WOBBLE[i] * Math.sin(a)];
  });
}

/** A closed Catmull-Rom through the points, as cubics. Smooth, and it loops. */
export function closedPath(pts, tension = 0.5) {
  const n = pts.length;
  const at = (i) => pts[(i % n + n) % n];
  let d = `M ${at(0)[0].toFixed(1)} ${at(0)[1].toFixed(1)}`;
  for (let i = 0; i < n; i++) {
    const [p0, p1, p2, p3] = [at(i - 1), at(i), at(i + 1), at(i + 2)];
    const c1 = [p1[0] + (p2[0] - p0[0]) * tension / 3,
                p1[1] + (p2[1] - p0[1]) * tension / 3];
    const c2 = [p2[0] - (p3[0] - p1[0]) * tension / 3,
                p2[1] - (p3[1] - p1[1]) * tension / 3];
    d += ` C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)}` +
         ` ${c2[0].toFixed(1)} ${c2[1].toFixed(1)}` +
         ` ${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
  }
  return `${d} Z`;
}

/**
 * The whole scene's geometry, from one number: how many traders.
 *
 * Two face each other across the fire, which is what every board on disk is.
 * More stand in a line along the shore with the square in front of them, and
 * the canvas gets wider rather than more crowded -- the page scales the SVG to
 * its column, so a wide viewBox is a smaller picture and not a broken one.
 *
 * They used to ring the island. A ring cannot work here and never did: a card
 * hangs below its hut, so a seat at the bottom of the ring puts its card off
 * the canvas and a seat at the top puts it over the fire. It had simply never
 * been rendered -- every replay is two traders.
 */
/**
 * Where everything stands, for however many traders and whichever way up.
 *
 * A phone in portrait is about 0.46 wide-to-tall and the island's viewBox was
 * 1.79, so the whole scene fitted to width and sat as a thin band with dead sky
 * above and dead sea below -- the trader cards, which are the only part
 * carrying information, rendered at about a third of a readable size.
 *
 * A row of huts is what will not fit. So in portrait they go in a **column**
 * instead, and the viewBox goes tall with them; nothing else about the scene
 * changes, because everything is positioned from `seats`, `ly`, `rx`, `ry` and
 * `fire`. `fits()` is what holds the geometry honest either way.
 */
/**
 * Where the trader cards go, and what is left for the island.
 *
 * **The cards were standing on the island.** Each one hung under its own hut,
 * and a hut is in the middle of the frame because that is where an island is,
 * so between them two cards covered the market, both settlements and most of
 * the meadow -- the picture the page exists to show. They are moved out to the
 * frame's own margins and tied back to their huts with a line.
 *
 * Landscape has margins down the sides; portrait has none worth the name, so
 * the island takes a band across the top and the cards a grid beneath it.
 * Either way this returns the card positions and the box the island is then
 * framed into, and the two do not overlap by construction.
 */
//: Island units across the frame the stage fits the island into. The same
//: number as `EXTENT * 2` in `stage.js`, which cannot be imported here because
//: it brings three.js with it.
const ISLAND_ACROSS = 8.7;

//: How far the island reaches above and below its own centre once drawn, in
//: multiples of the scale it is framed at.
//:
//: **It is not as tall as it is wide.** It is a disc under a tilted camera, so
//: its width is the sea's full diameter and its height is that diameter
//: foreshortened -- and only its top is given back, by the trees and the hill
//: standing on it. A square band round it reserves a sixth of its own height
//: with nothing in it, which on a phone is space the island could have had.
//:
//: Measured off the model rather than derived from the tilt, and `island()`
//: re-measures it every run against the card below it, so a change to the
//: camera or the sea cannot leave these behind.
//: **Re-measured when the lagoon was widened.** `ISLAND_DOWN` was 3.21 for a
//: shallows of 4.62; at 5.45 the island's drawn foot is 4.00 below its middle,
//: and leaving the old number behind is exactly what `island()` fails on --
//: it read the island's foot ten points *below* the first card on a phone.
//: `ISLAND_UP` measures 4.07 now and is left at 4.27: over-reserving above
//: costs a little room and under-reserving puts the island under the chrome,
//: so the two errors are not worth the same.
const ISLAND_UP = 4.27, ISLAND_DOWN = 4.00;

//: Where the island's lowest drawn point falls inside a square box of side
//: `D`, as a fraction of `D`. The stage fits the island to the box's short
//: side, so the island is `D` wide and centred in it, and its foot is
//: `D/2 + ISLAND_DOWN * D / ISLAND_ACROSS` down from the box's top.
//:
//: The top is the mirror of it -- `0.5 - ISLAND_UP / ISLAND_ACROSS`, which is
//: within a hundredth of zero, so the island starts where its box does.
const ISLAND_FOOT = 0.5 + ISLAND_DOWN / ISLAND_ACROSS;
const ISLAND_TOP = 0.5 - ISLAND_UP / ISLAND_ACROSS;

//: The smallest island worth drawing, in viewBox units of box side. A frame
//: with no room left after its chrome and its cards gets a small island rather
//: than a negative one.
const ISLAND_MIN = 200;

//: And the smallest it goes once somebody has *asked* for the cards. The floor
//: above is what the layout imposes on a viewer who chose nothing; this is what
//: a viewer gets who tapped a card, which is a different question and deserves
//: a different answer. Still an island and not a strip: below about this the
//: huts stop being distinguishable from the trees.
const ISLAND_TINY = 116;

//: The widest a card goes with two of them to a row. The columns are centred on
//: `0.265w` and `0.735w`, so cards of width `W` leave `0.47w - W` between them;
//: this keeps twelve units of that as a gutter.
//:
//: **This, and not the island, is what caps the cards.** Measured: on a 393pt
//: portrait frame it allows `1.19x`, while the height freed by taking the
//: island all the way down to `ISLAND_TINY` would allow `1.63x`. So a card
//: focus that shrank the island further would buy nothing at all -- the frame
//: is 520 units wide whatever the island does.
const CARD_WIDEST = (w) => 0.47 * w - 12;

/**
 * What one tap is worth, on a phone held upright.
 *
 * The island and the cards are competing for one screen and the viewer is the
 * only one who knows which of them they are looking at. So they get to say, and
 * this is the whole of the mechanism: **a card scale, and a floor under the
 * island.** `cardPlan` already sizes the island as the *residual* of the band
 * the chrome left, so scaling the cards moves the island by construction and
 * there is nothing else to move.
 *
 * `card: null` means "as large as the frame allows", solved below.
 *
 * Measured on a 393x660 portrait frame -- a shared link opened with the
 * browser's own bars showing -- with two traders:
 *
 * | focus | card | island, drawn | of the window |
 * |---|---|---|---|
 * | `even` | 1.00 | 198px | 50% |
 * | `island` | 0.58 | 276px | 70% |
 * | `cards` | 1.19 | 166px | 42% |
 *
 * The asymmetry is real and is the frame's, not a choice: the island gains 39%
 * and the cards 19%, because the cards run out of *width* long before the
 * island runs out of *height*.
 */
const FOCUS = {
  even: { card: 1, floor: ISLAND_MIN },
  //: `mini`, because 0.58 of a card is not a card. Measured on a 390pt window:
  //: the viewBox is 520 across, so a unit is 0.75 device pixels and 0.58 of one
  //: is 0.44 -- which puts a shelf's quantities at **4.8 pixels** and its
  //: `labour` and `utility` captions at 4.2. A number too small to read is
  //: worse than no number, because it still looks like the page is telling you
  //: something. So the small card stops being a shrunk card and becomes a
  //: glance card: whose it is, the coloured bars, and what the shelf came to.
  //: The rules are in the stylesheet, on `.card.mini`.
  island: { card: 0.55, floor: ISLAND_MIN, mini: true },
  cards: { card: null, floor: ISLAND_TINY },
};

/** The focus names, in the order a tap cycles them. */
export const FOCUSES = Object.keys(FOCUS);

function cardPlan(n, w, h, cardH, portrait, frame, focus = "even") {
  const gap = 14;
  const pitch = CARD_TOP + cardH + gap;
  if (portrait) {
    // Two to a row: a card is 196 of the 520 a portrait frame is wide, so two
    // fit beside each other with a gutter and three do not.
    const rows = Math.ceil(n / 2);
    //: **The frame's height is settled before the focus is**, off the card the
    //: layout would have drawn had nobody chosen. A focus that moved `H` would
    //: change the frame's *shape*, and the shape is what makes the chrome's
    //: bands land where the chrome is -- so a tap on a card would have walked
    //: the pills back over the island. A tap re-divides this band; it never
    //: resizes it.
    const cardsEven = rows * pitch;
    //: **The frame is the window's own shape**, so the viewBox does not
    //: letterbox and a band measured in units is the same band in pixels.
    //:
    //: That equality is the whole reason the chrome's band can be reserved
    //: at all. A viewBox of some other shape fits inside the window with `meet`
    //: and is *centred* in whichever direction is slack, so a band at the top
    //: of the viewBox lands somewhere in the middle of the window and reserves
    //: the wrong strip. `frameAspect` rounds down in portrait for the same
    //: reason: erring tall leaves the slack across the width, where a few
    //: pixels of sea cost nothing, instead of down the height, where they
    //: would move every band.
    //: A floor under the frame, for when the cards alone are most of the
    //: window. Three traders on a 393x660 phone is two rows of them, and the
    //: chrome's bands take a further 47% of the height: the island's box came
    //: out at nothing and the frame grew past the window's shape to hold the
    //: cards -- at which point the bands, taken as fractions of a frame that
    //: had grown, no longer landed where the chrome is and the island was back
    //: under the pills. Solved for instead: whatever height leaves the island
    //: its minimum once the chrome and the cards have theirs. The frame is
    //: then taller than the window and the slack falls across the *width*,
    //: which is the direction this has been spending slack in all along.
    const floorH = Math.ceil((ISLAND_MIN * ISLAND_FOOT + 16 + cardsEven)
                             / Math.max(0.2, 1 - frame.top - frame.foot));
    const H = Math.max(720, Math.round(w / frame.aspect), floorH);
    //: The chrome's two bands, in units. Declared in the stylesheet next to
    //: the rules that put the chrome there, and arriving here as fractions of
    //: the window's height so that this does not need to know how many pixels
    //: tall the window is.
    const above = Math.round(H * frame.top);
    const below = Math.round(H * frame.foot);
    //: What is left is the island's, and it takes all of it. The cards are
    //: fixed -- they carry every number on the page and shrinking them is how
    //: the phone view was unreadable to begin with -- so the island is the
    //: term that gives.
    //:
    //: On a tall phone that leaves the island the full width of the frame. On
    //: a short one -- 393 by 660, which is what a shared link opens into with
    //: the browser's own bars showing -- the chrome and one row of cards are
    //: near half the height between them and the island is drawn small. That
    //: is the trade, and it is the deliberate side of it: the island was
    //: bigger before because it was drawn *underneath* the chrome.
    //:
    //: **Which of the two gives is now the viewer's to say.** `FOCUS` scales
    //: the cards; the island is still the residual and still takes all of it.
    const band = H - above - below;
    const want = FOCUS[focus] ?? FOCUS.even;
    //: A glance card is a shorter card, not only a smaller one -- see
    //: `CARD_H_GLANCE`. The height is settled here rather than by the scene so
    //: that the band this reserves and the box the scene draws are one number.
    const tall = want.mini ? CARD_H_GLANCE : cardH;
    const pitchAt = (s) => s * (CARD_TOP + tall) + gap;
    //: The largest card that still leaves the island the floor this focus put
    //: under it. Never below 1: a viewer who asked for the cards is not told
    //: that the answer is smaller cards.
    const byHeight = ((band - 16 - want.floor * ISLAND_FOOT) / rows - gap)
                     / (CARD_TOP + tall);
    const scale = want.card
      ?? Math.max(1, Math.min(CARD_WIDEST(w) / CARD_W, byHeight));
    const cardsH = Math.round(rows * pitchAt(scale));
    const room = band - cardsH - 16;
    const D = Math.max(want.floor, Math.min(w, Math.floor(room / ISLAND_FOOT)));
    //: **The block sits in the middle of the band, not at the top of it.**
    //: The island is capped at the frame's own width -- past that its shore
    //: would be cropped, since the land spans exactly its box -- so on a tall
    //: phone it is already as big as it can be and every unit the cards give
    //: back is slack. Dumped below the last card that slack is invisible, and
    //: a tap on the island would have looked like a tap that did nothing.
    //: Shared above and below, it is the island getting the room.
    const used = Math.round(ISLAND_FOOT * D) + 16 + cardsH;
    const top = above + Math.max(0, Math.round((band - used) / 2));
    //: Where the island actually stops, which is above where its box does.
    //: Kept separate from where the cards start, so that a check comparing the
    //: two is asking a question rather than restating one number twice.
    const islandFoot = top + Math.round(ISLAND_FOOT * D);
    const foot = islandFoot + 16;
    return {
      cards: Array.from({ length: n }, (_, i) => {
        const row = Math.floor(i / 2);
        // A row with one card in it sits in the middle rather than off to a side.
        const alone = i === n - 1 && n % 2 === 1;
        return { x: alone ? w / 2 : (i % 2 ? w * 0.735 : w * 0.265),
                 y: foot + row * pitchAt(scale) };
      }),
      islandBox: { x: Math.round((w - D) / 2), y: top, w: D, h: D },
      //: Where the island starts drawing, a hair below its box's own top.
      islandTop: top + Math.round(ISLAND_TOP * D),
      islandFoot,
      cardScale: scale,
      cardMini: !!want.mini,
      //: Only when this branch has an opinion. A live board draws a shorter
      //: card than the layout plans for -- `CARD_H` against `CARD_H_SCORED` --
      //: and overriding that here would grow every live card by 46 units.
      cardH: want.mini ? CARD_H_GLANCE : null,
      //: The window's height, or more if the cards need it. Any slack falls
      //: past the last card, below the transport's own band, where it is sea.
      h: Math.max(H, foot + cardsH + below),
    };
  }
  //: A column's width, from the card's own: the margin is as wide as what
  //: stands in it and no wider, because every unit of it is island.
  const col = CARD_W / 2 + 22;
  const perSide = Math.ceil(n / 2);
  const cards = Array.from({ length: n }, (_, i) => {
    const right = i >= perSide;
    const k = right ? i - perSide : i;
    const of = right ? n - perSide : perSide;
    const block = of * pitch - gap;
    return { x: right ? w - col : col, y: (h - block) / 2 + k * pitch };
  });
  //: Landscape has margins down the sides and the cards stand in them, so
  //: nothing here is competing for the same pixels and there is nothing for a
  //: focus to re-divide. `cardScale` is declared anyway rather than left
  //: undefined, so the scene has one number to read either way up.
  return { cards, islandBox: { x: col * 2, y: 0, w: w - col * 4, h }, h,
           cardScale: 1, cardMini: false, cardH: null };
}

/**
 * The viewBox's width, never narrower than the layout's own but widened to a
 * window that is wider still.
 *
 * A fixed-width viewBox letterboxes inside a window of a different shape, and
 * the bars are dead pixels: on a landscape phone -- 844 by 390 -- the island
 * had a quarter of the screen and the rest was black. Widening spends them on
 * the island, which is the only thing between the two card columns.
 *
 * It only ever widens. Narrowing would spend them the other way, on the cards,
 * and there is no window where that is the trade to make.
 */
const widen = (base, h, aspect) =>
  aspect ? Math.max(base, Math.round(Math.min(h * aspect, h * 3.4))) : base;

/**
 * @param {number} n        how many traders
 * @param {boolean} portrait  which way up the frame is
 * @param {?number} aspect  the window's shape, wide over tall
 * @param {?{top:number, foot:number}} chrome  the bands the floating chrome
 *   stands on, as fractions of the window's height. Read off the stylesheet by
 *   the page; **zero here means the island is drawn under the pills**, which
 *   is what it did before these existed.
 * @param {string} focus  which of the island and the cards the viewer asked
 *   for -- `"even"`, `"island"` or `"cards"`. Portrait only; see `FOCUS`.
 */
export function layout(n, portrait = false, aspect = null, chrome = null,
                       focus = "even") {
  if (portrait) {
    // One seat above another, far enough apart for a hut above each card. The
    // pitch is the seat's own extent -- hut, card and a gap -- rather than a
    // number chosen to look right at one count of traders.
    const w = 520;
    const pitch = 84 + CARD_TOP + CARD_H_SCORED + 54;
    // Sky, and enough of it for a sun to cross. The island used to run from 40
    // to 900 of a 940 viewBox, which left the sun a strip to sit in and nowhere
    // to travel; the huts start far enough down that the island's top edge is
    // above them and there is still weather over it.
    const sky = 150;
    const first = sky + 104;
    const seats = Array.from({ length: n }, (_, i) => ({ x: w / 2, y: first + i * pitch }));
    const bottom = first + pitch * (n - 1) + CARD_TOP + CARD_H_SCORED + 60;
    const ly = (sky + bottom) / 2;
    const plan = cardPlan(n, w, bottom + 120, CARD_H_SCORED, true,
                          // A phone held upright, for a caller that did not say.
                          { aspect: aspect ?? 0.46,
                            top: chrome?.top ?? 0, foot: chrome?.foot ?? 0 },
                          focus);
    return {
      w, h: plan.h, cx: w / 2, ly, ry: (bottom - sky) / 2, rx: w / 2 - 34, seats,
      // Beside the column rather than in it: a fire between two stacked huts
      // would sit underneath a card.
      fire: { x: w / 2, y: bottom + 46 },
      ...plan,
    };
  }
  if (n <= 2) {
    const w = widen(BASE_W, BASE_H, aspect);
    const g = { w, h: BASE_H, cx: w / 2, ly: 298, rx: w / 2 - 48, ry: 188 };
    const seats = n === 2
      ? [{ x: w * 0.25, y: 238 }, { x: w * 0.75, y: 238 }]
      : [{ x: g.cx, y: 238 }];
    return { ...g, seats, fire: { x: g.cx, y: g.ly + 52 },
             ...cardPlan(n, g.w, g.h, CARD_H_SCORED, false) };
  }
  // Tall enough for the longer of the two card columns. A frame that only
  // ever held one card per side ran the third off the bottom at five traders.
  const h = Math.max(620, Math.ceil(n / 2) * (CARD_TOP + CARD_H_SCORED + 14) + 40);
  const w = widen(268 * n + 300, h, aspect);
  const g = { w, h, cx: w / 2, ly: h / 2 + 10, rx: w / 2 - 44, ry: h / 3 };
  const step = (w - 420) / (n - 1);
  return {
    ...g,
    seats: Array.from({ length: n }, (_, i) => ({ x: 210 + i * step, y: 232 })),
    // In front of the huts rather than between them: with a line of traders
    // there is no between.
    fire: { x: g.cx, y: g.ly + 150 },
    ...cardPlan(n, w, h, CARD_H_SCORED, false),
  };
}

/**
 * Where the sun stands at a given point in the episode, 0 at the open and 1 at
 * the bell.
 *
 * **An episode is a day, so the day should be readable from the sky.** The page
 * used to say how long it had been quiet in a pill -- "quiet 41s" -- which is a
 * number about the replay rather than about the island, and it left the sun
 * parked in one spot for the whole episode with nothing marking the hours.
 *
 * The arc is bounded by the island rather than by a constant. It rises and sets
 * beyond the island's width, where there is only water, and its apex clears the
 * island's topmost point -- the sun is drawn *behind* the land so that it can
 * set behind it, which also means an arc that dipped below that edge would take
 * the sun through the island at noon.
 */
//: Past the bell, where the sun goes on down. The day does not stop at the
//: horizon and neither does the disc: it keeps its own clock, and the bell's
//: animation is the light going, not the sun being moved.
export const SET = 1.28;

export function sunAt(g, p) {
  const top = g.ly - g.ry;
  // Just clear of the island at noon, and low but still over water at either
  // end, where the island is not wide enough to be in the way.
  const apex = top * 0.34;
  const rest = top * 0.9;
  const day = Math.max(0, Math.min(1, p));
  const x = g.cx + g.rx * 1.02 * (2 * day - 1);
  const y = rest - (rest - apex) * Math.sin(Math.PI * day);
  if (p <= 1) {
    // It comes up out of the sea rather than appearing already in it, which is
    // also what makes a new day readable: the previous one set in the west and
    // this one arrives in the east with nothing travelling backwards between.
    return { x, y, dim: Math.max(0, Math.min(1, p / 0.06)) };
  }
  const sinking = Math.max(0, Math.min(1, (p - 1) / (SET - 1)));
  return {
    x: x + g.rx * 0.16 * sinking,
    // Behind the island, which works because the sun is drawn before the water
    // and the land.
    y: y + (g.ly - 24 - y) * sinking,
    dim: 1 - sinking,
  };
}

/**
 * How far the day is into its own colour, 0 through the middle of it and 1 at
 * the open and at the bell.
 *
 * **The page has no horizon and is not getting one.** Considered and declined:
 * the model's camera is a fixed tilt looking down, `Stage.flood()` exists
 * specifically to guarantee water reaches every corner of the frustum, and the
 * ground-to-viewBox map that puts a hut under its card is affine only while
 * that tilt does not move. A sun on the water would have been a matte painted
 * over the letterbox bands claiming a distance the geometry does not have. So
 * the dawn and the dusk are carried by *light* instead -- the burn over the
 * drawn island, and the key, ambient and fill over the modelled one -- and
 * this is the one curve both of them read, so the two halves of the page
 * cannot disagree about how far through the day the colour is.
 *
 * Flat across the middle rather than linear from noon: a straight ramp spreads
 * the warmth over the whole morning, which reads as an island that is orange
 * all day and never as one that is orange *now*. Zero for the middle 52% of
 * the day and all of it in the last quarter at each end.
 *
 * Past the bell it stays at 1. The day does not stop at the horizon -- see
 * `SET` above, which is the disc's own overshoot on the same clock.
 */
export function burnAt(p) {
  const d = Math.abs(2 * Math.max(0, Math.min(1, p)) - 1);
  return Math.max(0, Math.min(1, (d - 0.52) / 0.48));
}

const CARD_W = 196, BAR_W = 26, BAR_MAX = 52;
//: The shelf's floor, in card coordinates. Bars stand on it, labels hang below.
const BASE = 104;
//: Taller only where there is a utility to put in it. A live card must not
//: carry an empty score row: a blank number reads as a number that failed,
//: rather than as one nobody on this island is allowed to know.
const CARD_H = 140, CARD_H_SCORED = 186;
//: And what is left of one when a viewer has given the screen to the island: a
//: name, a labour dial and the shelf, ending just under the glyphs that name
//: the goods. **The score row goes with the height.**
//:
//: It was kept at first, and the reasoning is left here because it was not
//: wrong: the utility is the one number the round is scored on, and a shelf
//: with a bare number under it is worse than one with a named number. What
//: changed is what the tap is *for*. A viewer who tapped the island asked for
//: the island, and 186 units of card is 74 more than the shelf needs -- 74
//: units of band that the island cannot have while a number nobody tapped for
//: is standing in it. One tap brings the whole card back.
const CARD_H_GLANCE = 112;
//: The card hangs below the seat, clear of the hut rather than pasted onto it.
const CARD_TOP = 22;
//: How far above a settlement a bubble floats, in viewBox units. The model
//: draws a hut a little under a unit tall and the island's short side is 8.7
//: units across the frame, so this is about a hut and a half -- clear of the
//: roof, and close enough that it reads as belonging to it.
const POP_UP = 74;

/** A name safe to put in a selector: live, a seat is a raw peer id. */
const cssName = (s) => (window.CSS?.escape ? CSS.escape(s) : String(s));

/**
 * Where a line leaving a card should leave it: the point on the card's own
 * edge nearest whatever it is pointing at. A leader that starts inside the
 * card it belongs to reads as a scratch across it.
 */
export function edgeToward(box, to) {
  const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
  const dx = to.x - cx, dy = to.y - cy;
  if (!dx && !dy) return { x: cx, y: cy };
  // How far along the centre-to-target ray the box's own edge is.
  const t = Math.min(dx ? (box.w / 2) / Math.abs(dx) : Infinity,
                     dy ? (box.h / 2) / Math.abs(dy) : Infinity);
  return { x: cx + dx * t, y: cy + dy * t };
}

/** The box a trader's card occupies, in scene coordinates. */
export function cardBox(seat, cardH = CARD_H_SCORED) {
  return { x: seat.x - CARD_W / 2, y: seat.y + CARD_TOP, w: CARD_W, h: cardH };
}

/** Room for a card, and for the hut above it, at every seat. */
export function fits(g, cardH = CARD_H_SCORED) {
  return g.seats.every((s) => s.y - 84 > 0 && s.y + CARD_TOP + cardH < g.h
                              && s.x - CARD_W / 2 > 0 && s.x + CARD_W / 2 < g.w);
}

/**
 * What a palm actually covers, relative to where it is planted.
 *
 * Its anchor is the foot of the trunk, but it spreads up and to the right --
 * fronds to about x+38, crown to y-50 -- and the sway swings that a couple of
 * units further. Written down because the placement test needs the footprint,
 * not the anchor.
 */
export const PALM_BOX = { dx: -20, dy: -60, w: 68, h: 74 };

const boxesOverlap = (a, b) =>
  a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;

/**
 * Scenery that does not land on the data.
 *
 * Twice wrong before. First it tested `hypot(seat - point) > 170` -- a circle
 * around the seat -- while a card is a tall box hanging *below* it, so palms
 * rendered on top of the shelves. Then it tested the palm's **anchor** against
 * a padded card box, which is the same mistake from the other side: a palm
 * planted just clear of the card still reaches 38 units to the right, so it
 * landed on the shelf anyway.
 *
 * Both things have extent. Test box against box.
 */
export function placeScenery(seatList, candidates, cardH = CARD_H_SCORED, pad = 10,
                             keepOff = [], foot = PALM_BOX) {
  const boxes = seatList.map((s) => cardBox(s, cardH)).concat(keepOff)
    .map((b) => ({ x: b.x - pad, y: b.y - pad, w: b.w + pad * 2, h: b.h + pad * 2 }));
  return candidates.filter(([x, y]) => !boxes.some((b) =>
    boxesOverlap({ x: x + foot.dx, y: y + foot.dy, w: foot.w, h: foot.h }, b)));
}

export class Scene {
  constructor(root, timeline, reveal = null, portrait = false, placed = null,
              aspect = null, chrome = null, focus = "even") {
    this.root = root;
    this.timeline = timeline;
    this.traders = timeline.traders;
    this.goods = timeline.goods;
    // Present only in a replay. Everything utility on this island hangs off it,
    // and there is deliberately no path that fills it in live.
    this.reveal = reveal;
    this.cardH = reveal ? CARD_H_SCORED : CARD_H;
    this.portrait = portrait;
    this.aspect = aspect;
    //: The bands the page's floating chrome stands on. Kept so that a reflow
    //: can tell a window that only changed shape from one whose chrome now
    //: takes a different share of it -- a phone's pill rows are a fixed number
    //: of pixels, so a shorter window is a bigger band at the same aspect.
    this.chrome = chrome;
    //: Which offers a refusal is currently blinking, and until when. The ropes
    //: are rebuilt from scratch on every paint (`paint()` calls
    //: `replaceChildren`), so a class put on one by `refuse()` is gone by the
    //: next frame -- which did not show while the bubble over the hut was
    //: carrying the message, and is the whole indicator now. Held here and
    //: re-applied by `rope()` for as long as the mark is meant to be up.
    this.noUntil = new Map();
    //: Which of the island and the cards this viewer asked for. Portrait only:
    //: landscape has margins for the cards and the two are not competing.
    this.focus = focus;
    this.geo = layout(this.traders.length, portrait, aspect, chrome, focus);
    // Where the settlements actually are, when there is a model underneath.
    // The island decides where its own huts stand; the cards stand in the
    // frame's margins and a line ties each one back, which is why this arrives
    // from outside instead of from `layout`.
    this.placed = placed?.length === this.traders.length ? placed : null;
    this.utilityTop = this.utilityScale();
    //: Whether there is a model of the island under this drawing. With one, the
    //: cards stand out in the frame's margins and a line ties each back to its
    //: settlement; without one, the drawing is the island and a card hangs
    //: under its own drawn hut as it always did.
    this.modelled = placed !== null;
    this.seats = {};
    //: Where each settlement is on screen. The same as its card's seat when
    //: there is no model; from the stage, every frame, when there is.
    this.pins = {};
    //: `trader:good` to a viewBox point: where that pile of boxes is drawn.
    //: Empty without a model, and the card's own seat stands in for it.
    this.yards = {};
    this.bars = {};
    this.labels = {};
    //: When each open offer's pill started down its rope, by pid. Kept across
    //: rebuilds -- `follow()` and `paint()` both throw the rope nodes away and
    //: a pill that restarted its slide on every camera frame would never
    //: arrive -- and pruned in `paint()` when the offer stops being open, so
    //: scrubbing back over a proposal plays it again.
    this.travel = new Map();
    //: Where each pill actually *is*, as against where the geometry says it
    //: belongs. Kept by pid for the same reason the clock is: the rope's node
    //: is thrown away and rebuilt whenever the set of offers changes.
    this.spot = new Map();
    this.build();
  }

  /**
   * Turn the island the other way up, when the window did.
   *
   * `build()` already replaces everything it drew, so this is a rebuild rather
   * than a second code path -- there is one way the scene is constructed, and a
   * rotated phone goes through it again. Returns whether anything changed, so
   * the page can skip a repaint on a resize that did not cross the boundary
   * (every scroll on mobile Safari fires one).
   */
  reflow(portrait, aspect = this.aspect, chrome = this.chrome,
         focus = this.focus) {
    const same = (a, b) => (a?.top ?? 0) === (b?.top ?? 0)
                        && (a?.foot ?? 0) === (b?.foot ?? 0);
    if (portrait === this.portrait && aspect === this.aspect
        && focus === this.focus && same(chrome, this.chrome)) return false;
    this.portrait = portrait;
    this.aspect = aspect;
    this.chrome = chrome;
    this.focus = focus;
    this.geo = layout(this.traders.length, portrait, aspect, chrome, focus);
    // The layout's own seats, for now. A caller with an island underneath
    // follows this with `replace()`, because the settlements have to be put
    // back on a frame of the new shape before the cards can find them.
    // Rebuilt from the new geometry rather than carried over: every one of
    // these is keyed to nodes `build()` is about to throw away.
    this.seats = {};
    this.pins = {};
    this.bars = {};
    this.labels = {};
    this.top = undefined;
    this.shown = new Map();
    this.build();
    return true;
  }

  /**
   * The camera turned; what points at the island follows it.
   *
   * The cards do not move -- they stand in the margins, which do not turn.
   * What has to keep up is everything drawn *at* a settlement: the line tying
   * each card to its own hut, and the rope between two huts with an offer
   * standing between them.
   *
   * Cheaper than `replace()` on purpose, because this runs every frame.
   */
  follow(placed, yards = null) {
    if (placed?.length !== this.traders.length || !this.state) return;
    this.traders.forEach((name, i) => { this.pins[name] = placed[i]; });
    //: Where each trader's pile of each good stands, in this frame's viewBox.
    //: A symbol crossing between a box on the island and a bar on the card has
    //: to start or end somewhere real, and the island is a canvas the SVG
    //: layer cannot see into.
    if (yards) this.yards = yards;
    //: Any bubble in the air goes with the settlement it belongs to. It is a
    //: second or three long and the camera covers about a fiftieth of its
    //: revolution in that time -- a few pixels, which is exactly enough for a
    //: bubble pinned at the start to drift off the roof it is meant to be over.
    for (const node of this.flights?.querySelectorAll(".pop-at") ?? []) {
      const p = this.pins[node.getAttribute("data-trader")];
      if (p) node.setAttribute("transform", `translate(${p.x} ${p.y})`);
    }
    this.layTethers();
    const open = this.state.proposals.filter((p) => p.status === "open");
    const rank = new Map();
    this.stack = this.stacking(open);
    const want = new Map();
    for (const p of open) {
      const pair = [p.maker, p.taker].sort().join("~");
      const i = rank.get(pair) || 0;
      rank.set(pair, i + 1);
      want.set(p.pid, i);
    }
    //: **Only rebuilt when the offers change.** This runs on every frame the
    //: camera turns, which is every frame, and it used to replace every rope
    //: node each time -- and a fresh node restarts its CSS animation, so the
    //: dashes crawling toward the trader an offer is addressed to were reset
    //: sixty times a second and the line sat still. The same ropes are now
    //: moved to where the settlements went; new ones are built once.
    //: The height of the pile a pill sits in is part of how the rope is drawn,
    //: so a changed pile counts as changed offers even when every pair fan and
    //: the count are the same -- which is what one offer lapsing as another
    //: opens looks like. `aimRope` re-reads `this.stack`, so the reused branch
    //: is right either way; this only decides whether the nodes are kept.
    const same = this.shown.size === want.size
      && [...want].every(([pid, fan]) => this.shown.get(pid) === fan);
    if (same) {
      for (const p of open) {
        const node = this.ropes.querySelector(`.rope[data-pid="${p.pid}"]`);
        if (node) this.aimRope(node, p, want.get(p.pid));
      }
    } else {
      this.ropes.replaceChildren(...open.map((p) => this.rope(p, want.get(p.pid))));
      this.shown = want;
    }
  }

  /**
   * A mark on each settlement, saying which trader's it is.
   *
   * **There was a dashed line from here to the trader's card**, on the
   * argument that a card out in the margin has stopped saying whose it is.
   * Four traders make four of those lines, and they cross the whole picture
   * and each other -- reported as clutter over the island the page exists to
   * show. What says whose a settlement is, on the island, is the coloured
   * banner already flying over it; the card says whose it is by being labelled.
   *
   * The mark stays because it is what a rope hangs from and what the goods
   * fly between, and because a settlement with nothing on it is a hut.
   * Re-laid every frame because the island turns under it.
   *
   * **Drawn stroke removed (2026-08-26).** The circle read as a gray ring
   * left sitting on every hut whether or not a card even pointed there --
   * a leftover mark from the line above, once that line was cut, rather
   * than something its own endpoint needed. The `.tether-pin` element still
   * carries the settlement's own point (`index.html` draws it stroke:none),
   * because `viewer/tests/render.py`'s turning check reads it to confirm the
   * mark follows the island as the camera turns.
   */
  layTethers() {
    if (!this.tethers) return;
    if (!this.modelled) { this.tethers.replaceChildren(); return; }
    this.tethers.replaceChildren(...this.traders.flatMap((name) => {
      const pin = this.pins[name];
      if (!pin) return [];
      const g = el("g", { class: "tether", "data-trader": name });
      g.append(el("circle", { class: "tether-pin", cx: pin.x, cy: pin.y, r: 5.5 }));
      return [g];
    }));
  }

  /** Take new settlement positions -- the island was reframed under us. */
  replace(placed) {
    if (placed?.length !== this.traders.length) return;
    this.placed = placed;
    this.seats = {};
    this.pins = {};
    this.bars = {};
    this.labels = {};
    this.top = undefined;
    this.shown = new Map();
    this.build();
  }

  build() {
    const svg = this.root;
    const g = this.geo;
    svg.setAttribute("viewBox", `0 0 ${g.w} ${g.h}`);
    svg.replaceChildren();
    svg.append(this.defs());

    svg.append(el("rect", { class: "sea-fill", x: 0, y: 0, width: g.w, height: g.h,
                            fill: "url(#sea)" }));
    // Behind the water, so it sets *into* the sea rather than on top of it.
    svg.append(this.sun());
    svg.append(this.water());
    //: **The sunset is on the water, and under the land.**
    //:
    //: It used to be the last rect on the stack, over the whole frame, so a
    //: dawn or a bell put a soft-light wash across the meadow, the sand, the
    //: huts and the cards alike. Reported by eye as the island looking tinted.
    //: A wash over everything is not what a low sun does to a landscape: it
    //: lights the faces turned towards it and leaves the rest, and the one
    //: surface that really does go the colour of the sky is the water, which
    //: is reflecting it.
    //:
    //: So the rect is drawn here, after the sea and before the land, and the
    //: z-order is the whole mechanism -- the sea takes the colour and nothing
    //: standing on the island is touched by it. The model does the same thing
    //: a different way, because with a canvas underneath the SVG this ordering
    //: buys nothing: see `island-life.js`, which tints the sea's own material.
    svg.append(el("rect", { x: 0, y: 0, width: g.w, height: g.h, class: "sky-burn" }));
    svg.append(this.land());

    // The cards go where the layout put them; the settlements go where the
    // model says, or -- with no model -- under their own drawn huts.
    const cards = this.modelled && g.cards ? g.cards : g.seats;
    cards.forEach((seat, i) => { this.seats[this.traders[i]] = seat; });
    (this.placed ?? g.seats).forEach((p, i) => { this.pins[this.traders[i]] = p; });
    svg.append(this.square());
    svg.append(this.scenery());

    // Under the ropes and the huts both: a line to a card is the quietest thing
    // on the island and must never draw over what it points at.
    this.tethers = el("g", { class: "tethers" });
    svg.append(this.tethers);

    this.ropes = el("g", { class: "ropes" });
    svg.append(this.ropes);

    const huts = el("g", { class: "huts" });
    this.traders.forEach((name) => huts.append(this.hut(name, this.seats[name])));
    svg.append(huts);
    this.layTethers();

    this.flights = el("g", { class: "flights" });
    svg.append(this.flights);
    //: Anything waiting to be drawn belongs to the layer it was scheduled on.
    //: `gen` says which; a symbol whose generation has gone is a symbol for a
    //: board nobody is looking at any more.
    this.gen = (this.gen ?? 0) + 1;
    this.unpend_();

    // Dusk rather than a black rectangle: the bell is the most dramatic thing
    // that happens in an episode and it was being drawn as a power cut.
    // The colour the light turns as the sun goes, then the dark it leaves.
    // Both opacities are CSS, keyed off `.closed`: a state, not a pulse, so
    // scrubbing to a closed frame lands in the dark with no event played.
    svg.append(el("rect", { x: 0, y: 0, width: g.w, height: g.h, class: "night",
                            fill: "url(#dusk)" }));
    svg.append(this.campfire());
    svg.append(el("rect", { x: 0, y: 0, width: g.w, height: g.h, class: "vignette",
                            fill: "url(#vignette)" }));

    this.banner = el("g", { class: "banner", opacity: 0 });
    this.banner.append(el("rect", { class: "banner-bg", x: g.cx - 200, y: 42,
                                    width: 400, height: 46, rx: 23 }));
    this.banner.append(el("text", { x: g.cx, y: 72, class: "banner-text" }, ""));
    svg.append(this.banner);
  }

  defs() {
    const defs = el("defs");
    defs.append(el("radialGradient", { id: "sea", cx: "50%", cy: "42%", r: "78%" }, [
      el("stop", { offset: "0%", "stop-color": "var(--sea-near)" }),
      el("stop", { offset: "60%", "stop-color": "var(--sea-mid)" }),
      el("stop", { offset: "100%", "stop-color": "var(--sea-far)" }),
    ]));
    // The sand is lit from the square, so the gradient's bright end sits where
    // the fire is rather than at the top of the shape.
    defs.append(el("radialGradient", { id: "sand", cx: "50%", cy: "58%", r: "68%" }, [
      el("stop", { offset: "0%", "stop-color": "var(--sand-lit)" }),
      el("stop", { offset: "65%", "stop-color": "var(--sand)" }),
      el("stop", { offset: "100%", "stop-color": "var(--sand-dark)" }),
    ]));
    defs.append(el("radialGradient", { id: "glow", cx: "50%", cy: "50%", r: "50%" }, [
      el("stop", { offset: "0%", "stop-color": "var(--fire)", "stop-opacity": "0.5" }),
      el("stop", { offset: "55%", "stop-color": "var(--fire)", "stop-opacity": "0.14" }),
      el("stop", { offset: "100%", "stop-color": "var(--fire)", "stop-opacity": "0" }),
    ]));
    defs.append(el("radialGradient", { id: "sun", cx: "50%", cy: "50%", r: "50%" }, [
      el("stop", { offset: "0%", "stop-color": "var(--sun-core)" }),
      el("stop", { offset: "55%", "stop-color": "var(--sun)" }),
      el("stop", { offset: "100%", "stop-color": "var(--sun)", "stop-opacity": "0" }),
    ]));
    defs.append(el("radialGradient", { id: "vignette", cx: "50%", cy: "48%", r: "72%" }, [
      el("stop", { offset: "55%", "stop-color": "#000", "stop-opacity": "0" }),
      el("stop", { offset: "100%", "stop-color": "#000", "stop-opacity": "0.5" }),
    ]));
    defs.append(el("linearGradient", { id: "dusk", x1: "0", y1: "0", x2: "0", y2: "1" }, [
      el("stop", { offset: "0%", "stop-color": "#05202f" }),
      el("stop", { offset: "100%", "stop-color": "#020a10" }),
    ]));
    // Sand grain. Sparse on purpose: texture that competes with a bar chart is
    // not texture, it is noise on top of the only information here.
    const grain = el("pattern", { id: "grain", width: 38, height: 38,
                                  patternUnits: "userSpaceOnUse" });
    for (const [x, y, r] of [[5, 9, .9], [21, 3, .6], [13, 21, .8], [30, 16, .55],
                             [2, 27, .7], [25, 30, .85], [34, 6, .6], [9, 33, .5],
                             [18, 12, .45], [31, 25, .7]]) {
      grain.append(el("circle", { cx: x, cy: y, r, class: "grain-dot" }));
    }
    defs.append(grain);
    // Thatch, for the roofs. Same argument as the grain: barely there.
    const thatch = el("pattern", { id: "thatch", width: 8, height: 6,
                                   patternUnits: "userSpaceOnUse" });
    thatch.append(el("path", { d: "M 0 6 q 4 -6 8 0", class: "thatch-line" }));
    defs.append(thatch);
    return defs;
  }

  /**
   * What the cards are drawn at, which is 1 unless a viewer asked otherwise.
   *
   * Only with a model behind the page: without one the cards hang under their
   * own drawn huts at `geo.seats` rather than standing in the frame's margins
   * at `geo.cards`, so scaling them would move a card off the hut it belongs
   * to and the layout's own plan is not being used anyway.
   */
  cardScale() {
    return this.modelled ? (this.geo.cardScale ?? 1) : 1;
  }

  /** How tall a card's own box is: the layout's, when it has an opinion. */
  cardBoxH() {
    return (this.modelled && this.geo.cardH) || this.cardH;
  }

  /**
   * Where one good's bar stands, in scene coordinates.
   *
   * The bar's own `x` and the shelf's `BASE` are **card** coordinates, and the
   * card is a scaled group, so the two are not the same thing any more. This is
   * the one place the conversion happens: every symbol that flies between a
   * pile on the island and the bar counting it starts or ends here.
   */
  barAt(seat, slot) {
    const s = this.cardScale();
    return { x: seat.x + slot.x * s, y: seat.y + (CARD_TOP + BASE - 10) * s };
  }

  /**
   * What a tap at a point in the frame is a tap on: `"cards"`, `"island"`, or
   * `null` for the sea around them.
   *
   * The page asks, because the page owns the gesture; this owns the geometry
   * and is the only thing that knows where either of them ended up. A card is
   * tested first: the two boxes do not overlap by construction, but a tap near
   * the edge of one should land on the thing that was drawn there.
   */
  tapped(x, y) {
    const s = this.cardScale();
    const seats = this.modelled && this.geo.cards ? this.geo.cards : this.geo.seats;
    const inside = (b) => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h;
    for (const seat of seats ?? []) {
      if (inside({ x: seat.x - (CARD_W / 2) * s, y: seat.y + CARD_TOP * s,
                   w: CARD_W * s, h: this.cardH * s })) return "cards";
    }
    return this.geo.islandBox && inside(this.geo.islandBox) ? "island" : null;
  }

  /** Where the sun stands, this far through the episode. */
  sunPoint(p) {
    return sunAt(this.geo, p);
  }

  /**
   * How far through its episode this frame is, by the board's own clock.
   *
   * `null` when the board has not said -- after the round, or on a board whose
   * schedule line this page could not read. The caller leaves the sun where it
   * is rather than putting it at dawn, because "we do not know the time" is not
   * the same as "it is morning".
   *
   * **Before the first day opens is not one of those cases.** The round has
   * not started, so the island is at dawn and nowhere else -- and an untold
   * island is lit at noon by `island-life`, which meant the opening frames
   * stood in full daylight and the first day then began in the dark of the
   * dawn clip. Day, night, day, before anything had happened. The wait for the
   * first line is morning now, and the first day just rolls on from it.
   */
  dayProgress(state) {
    if (state?.phase === "before" || state?.phase === "ack") return 0;
    if (!state?.bell_at || !state.seconds || !state.at) return null;
    const bell = Date.parse(state.bell_at);
    const span = state.seconds * 1000;
    const now = Date.parse(state.at);
    if (!Number.isFinite(bell) || !Number.isFinite(now) || span <= 0) return null;
    return Math.max(0, Math.min(1, (now - (bell - span)) / span));
  }

  /**
   * How far through its day this frame will be by the time the next line
   * lands -- the far end of the sun's travel over a silence.
   *
   * `until` is when the next event is, or `null` when there is no next event
   * to wait for. Never behind `dayProgress`: the sun does not travel back.
   */
  dayAhead(state, until = null) {
    const now = this.dayProgress(state);
    if (now === null || until === null) return now;
    return Math.max(now, this.dayProgress({ ...state, at: until }) ?? now);
  }

  /** Put the sun at a point in the day, with no journey. */
  placeSun(p) {
    if (!this.sunNode) return;
    const { x, y, dim } = this.sunPoint(p);
    this.sunNode.style.transform = `translate(${x}px, ${y}px) scale(1)`;
    this.sunNode.style.opacity = String(dim);
    this.sunP = p;
  }

  /**
   * The sun's travel between one frame and the next.
   *
   * This is where the replay's compression becomes visible. A quiet stretch on
   * the board is held on screen for a moment, and over that moment the sun
   * covers the whole of the time nobody acted -- so a long silence *looks*
   * long, in the one place on the page that is about the island rather than
   * about the player.
   */
  sky(state, until = null, ms = 0) {
    if (!this.sunNode) return;
    const closed = state.phase === "closed" || state.phase === "over";
    //: The sky's colour is on the same clock as the disc, and is set here for
    //: both paths -- the burn reads it in the stylesheet, and `island-life`
    //: reads `burnAt` itself for the model's lights. Left alone when the board
    //: has no clock, exactly as the disc is: not knowing the hour is not the
    //: same as it being noon, and a frame that guessed would put the island
    //: back in full daylight between two evening events.
    const at = closed ? 1 : this.dayAhead(state, until);
    if (at !== null) {
      this.root?.style.setProperty("--burn", String(burnAt(at)));
      //: Which end of the day this is. The two are not one colour -- see
      //: `--sky-rise` in the tokens -- and a single orange at both ends made
      //: the morning read as a second evening.
      this.root?.style.setProperty("--burn-hue",
                                   at < 0.5 ? "var(--sky-rise)" : "var(--sky-set)");
    }
    const from = this.sunP ?? 0;
    let to;
    if (closed) {
      // The bell does not move the sun. It was already almost down when the
      // bell rang and it goes on down; the bell's own animation is the light
      // going and the fire coming up, and that runs alongside.
      to = SET;
    } else {
      to = this.dayAhead(state, until);
      if (to === null) return;   // no clock on this board: leave it where it is
    }
    // Never travel backwards across the sky. A new day begins in the east and
    // the night between is a jump nobody watches: the disc is at zero opacity
    // at both ends of it, so the next day rises out of the sea.
    if (to < from || !(ms > 0) || still()) { this.placeSun(to); return; }
    const a = this.sunPoint(from), b = this.sunPoint(to);
    this.sunP = to;
    this.sunNode.animate([
      { transform: `translate(${a.x}px, ${a.y}px) scale(1)`, opacity: a.dim },
      { transform: `translate(${b.x}px, ${b.y}px) scale(1)`, opacity: b.dim },
    ], { duration: ms, easing: "linear", fill: "forwards" });
  }

  /**
   * The sun, which the island did not have.
   *
   * Without one the bell had nothing to set: it was an overlay pulsing and
   * going back to full daylight, which reads as a flicker rather than as the
   * end of a day. An episode *is* a day here -- it opens, it runs, a bell
   * closes it and everything held is consumed -- so it should look like one.
   *
   * High in the band the huts face, which is the only part of this stylised
   * view that reads as distance. It travels down and out of it at the bell.
   */
  sun() {
    const g = this.geo;
    const wrap = el("g", { class: "sun-wrap", "aria-hidden": "true" });
    const dawn = sunAt(g, 0);
    const sun = el("g", { class: "sun",
                          transform: `translate(${dawn.x} ${dawn.y})` });
    sun.append(el("circle", { class: "sun-halo", r: 74, fill: "url(#sun)" }));
    sun.append(el("circle", { class: "sun-disc", r: 21 }));
    wrap.append(sun);
    this.sunNode = sun;
    return wrap;
  }

  /**
   * Three bands, three speeds. One band reads as wallpaper; the parallax is
   * what makes it water. Each translates by exactly one wavelength, so the
   * loop has no seam to catch the eye.
   */
  water() {
    const g = this.geo;
    const w = el("g", { class: "water", "aria-hidden": "true" });
    const reps = Math.ceil((g.w + 480) / 240) + 1;
    const band = (cls, ys, dy) => {
      const layer = el("g", { class: `wave-band ${cls}` });
      ys.forEach((y, i) => {
        layer.append(el("path", {
          class: "wave",
          d: `M -240 ${y} ` + `q 60 ${-dy} 120 0 t 120 0 `.repeat(reps),
          style: `animation-delay: ${-i * 2.3}s`,
        }));
      });
      return layer;
    };
    const near = g.ly + g.ry;
    w.append(band("far", [26, 58, 90, 122], 7));
    w.append(band("mid", [g.ly - g.ry - 40, near + 34, near + 66], 10));
    w.append(band("near", [g.h - 26, g.h + 6], 13));
    return w;
  }

  land() {
    const geo = this.geo;
    const g = el("g", { class: "island-body" });
    // Surf first, so the shore sits on top of it and the foam reads as being
    // *under* the beach rather than drawn over it.
    g.append(el("path", { class: "shallows", d: closedPath(coast(geo, 1.04)) }));
    g.append(el("path", { class: "surf surf-2", d: closedPath(coast(geo, 1.014)) }));
    g.append(el("path", { class: "surf surf-1", d: closedPath(coast(geo, 1.004)) }));
    g.append(el("path", { class: "land", d: closedPath(coast(geo, 1)) }));
    g.append(el("path", { class: "grain-fill", d: closedPath(coast(geo, 0.997)) }));
    // Stroked, not filled. Filled, it is a pale disc over the whole island and
    // the sand gradient underneath stops existing.
    g.append(el("path", { class: "wet", d: closedPath(coast(geo, 0.978)) }));
    return g;
  }

  /** The square, the fire, and the light it throws. */
  square() {
    const { x: fx, y: fy } = this.geo.fire;
    const g = el("g", { class: "square-group" });
    g.append(el("ellipse", { class: "square", cx: fx, cy: fy, rx: 132, ry: 54 }));
    return g;
  }

  /**
   * The fire, drawn **above** the night overlay.
   *
   * Where it used to sit, dusk fell on it like everything else and the
   * campfire got *dimmer* as the day ended -- which is backwards. It is the
   * one thing that should be brighter once the sun has gone, so it is the one
   * thing the dark is not allowed to cover.
   */
  campfire() {
    const { x: fx, y: fy } = this.geo.fire;
    const g = el("g", { class: "fire-layer" });
    g.append(el("circle", { cx: fx, cy: fy - 8, r: 132, fill: "url(#glow)",
                            class: "firelight" }));
    const fire = el("g", { class: "fire", transform: `translate(${fx} ${fy})` });
    fire.append(el("path", { class: "log", d: "M -26 7 L 26 -2" }));
    fire.append(el("path", { class: "log", d: "M -26 -2 L 26 7" }));
    fire.append(el("ellipse", { class: "embers", cx: 0, cy: 4, rx: 20, ry: 6 }));
    // Three flames on their own clocks. One flame that changes opacity reads as
    // a light bulb with a fault; three that move against each other read as
    // burning.
    [[0, -36, 1, 0], [-11, -26, .72, -.55], [12, -28, .78, -1.1]].forEach(
      ([dx, top, k, delay]) => {
        fire.append(el("path", {
          class: "flame",
          d: `M ${dx} ${top} c ${12 * k} ${12 * k} ${16 * k} ${22 * k} 0 ${30 * k}` +
             ` c ${-16 * k} ${-8 * k} ${-12 * k} ${-18 * k} 0 ${-30 * k} z`,
          style: `animation-delay: ${delay}s`,
        }));
      });
    for (const [dx, delay] of [[-6, 0], [7, -1.9], [1, -3.4]]) {
      fire.append(el("circle", { class: "ember", cx: dx, cy: -34, r: 1.8,
                                 style: `animation-delay: ${delay}s` }));
    }
    g.append(fire);
    return g;
  }

  /** A place rather than a blank: a worn path between the huts, and planting. */
  scenery() {
    const geo = this.geo;
    const g = el("g", { class: "scenery", "aria-hidden": "true" });
    const seatList = Object.values(this.seats);
    // A track is worn between huts, so an island with nobody on it has none --
    // and reaching for the first seat's `x` there threw, which is what an empty
    // live room used to show instead of a board.
    const first = seatList[0], last = seatList[seatList.length - 1];
    if (first) {
      g.append(el("path", {
        class: "track",
        d: `M ${first.x} ${geo.fire.y - 34} Q ${geo.cx} ${geo.fire.y + 74} ` +
           `${last.x} ${geo.fire.y - 34}`,
      }));
    }
    // Along the shore, where nothing informative goes. Kept as fractions of the
    // island so a wider canvas plants more of it rather than stretching six.
    const ring = [[-.90, -.34], [.91, -.30], [-.74, .56], [.76, .58],
                  [-.30, -.76], [.32, -.74], [-.14, .84], [.18, .86],
                  [-.55, .78], [.58, .76], [-.96, .16], [.97, .12],
                  [-.44, -.68], [.46, -.66], [-.02, -.80], [.04, .88]];
    const candidates = ring.map(([u, v]) => [geo.cx + u * geo.rx * .84,
                                             geo.ly + v * geo.ry * .84]);
    // The square is where everybody meets and the fire is in it. A palm growing
    // out of the fire is the same class of mistake as one growing out of a card.
    const square = { x: geo.fire.x - 148, y: geo.fire.y - 74, w: 296, h: 128 };
    placeScenery(seatList, candidates, this.cardH, 10, [square]).forEach(([x, y], i) => {
      const k = 0.98 + ((i * 7) % 4) * 0.13;
      const palm = el("g", { class: "palm", transform: `translate(${x} ${y}) scale(${k})`,
                             style: `animation-delay: ${-i * 1.3}s` });
      palm.append(el("ellipse", { class: "palm-shadow", cx: 3, cy: 3, rx: 15, ry: 4 }));
      palm.append(el("path", { class: "trunk", d: "M 0 0 q -7 -22 3 -42" }));
      // Its own group, turning about the top of the trunk. The sway used to be
      // on the whole palm, so the trunk and its shadow slid about with it --
      // which is a tree walking, not a tree in wind.
      const crown = el("g", { class: "crown" });
      [[-72, .9], [-38, 1], [-4, .95], [30, 1], [64, .88]].forEach(([a, sc], j) => {
        crown.append(el("path", {
          class: "frond", transform: `rotate(${a} 3 -42) scale(${sc})`,
          d: "M 3 -42 q 20 -11 32 -3 q -12 5 -19 6 q -8 1 -13 -3 z",
        }));
      });
      crown.append(el("circle", { class: "coconut", cx: 4, cy: -40, r: 2.6 }));
      palm.append(crown);
      g.append(palm);
    });
    return g;
  }

  hut(name, seat) {
    const g = el("g", { class: "hut", transform: `translate(${seat.x} ${seat.y})`,
                        "data-trader": name });
    //: **Whose hut, and whose card.** The model already paints a trader's
    //: colour on its door and the band under its roof; the drawn hut and the
    //: card hanging under it carried none of it, so with the island turned to
    //: cards a viewer had identical dark rectangles and a name to read on each.
    //: The accent is set once on the settlement group and inherited by both,
    //: which is what keeps the hut and the card that belongs to it wearing one
    //: colour.
    //:
    //: **From the ring, not from `--seat-${(i % 6) + 1}`.** The stylesheet
    //: names six and a table is not capped at six, so that wrapped the seventh
    //: trader's hut and card onto the first trader's colour -- the same defect
    //: the island had, in a second place. `seats.js` answers for any count, and
    //: the island is asked the same question, so the two still agree.
    g.style.setProperty("--seat", this.seatColour(name));
    // The dwelling, then the card. The hut says whose this is; the card is the
    // only part carrying information, and it gets a dark ground of its own --
    // a number written straight onto sand cannot be read at any size.
    g.append(el("ellipse", { class: "hut-shadow", cx: 6, cy: 12, rx: 52, ry: 10 }));
    g.append(el("path", { class: "roof", d: "M -50 -34 L 0 -80 L 50 -34 Z" }));
    g.append(el("path", { class: "roof-thatch", d: "M -50 -34 L 0 -80 L 50 -34 Z" }));
    g.append(el("rect", { class: "wall", x: -38, y: -34, width: 76, height: 46, rx: 3 }));
    // Lit while this trader has spoken, dark while they have not: the building
    // carries "nobody is home", so the state is not only a whole-hut fade.
    g.append(el("rect", { class: "window", x: -30, y: -26, width: 15, height: 13, rx: 2 }));
    g.append(el("rect", { class: "door", x: -8, y: -14, width: 20, height: 26, rx: 2 }));
    g.append(el("path", { class: "hut-rim", d: "M -50 -34 L 0 -80 L 50 -34" }));

    //: **The card scales; the hut does not.** In portrait the two are competing
    //: for one screen and a tap says which of them wins (see `FOCUS`), and the
    //: card is the term that moves because the island is sized as the residual.
    //: Applied to the card's own group rather than to the whole settlement, so
    //: that a drawn hut -- the fallback with no model behind the page -- is
    //: never scaled by a number chosen for the thing hanging under it.
    const card = el("g", {
      class: this.cardScale() !== 1 && this.geo.cardMini ? "card mini" : "card" });
    if (this.cardScale() !== 1) {
      card.setAttribute("transform", `scale(${this.cardScale()})`);
      //: The scale, handed to the stylesheet. A glance card holds its marks at
      //: the size they are on a full card by declaring them `1/scale` larger
      //: inside a group about to be scaled by `scale` -- and that only works
      //: while the two numbers agree. They were a literal `26px` against a
      //: literal `0.58`, which is one edit away from a name that shrinks with
      //: its card and a check that has to be told the new number.
      card.style.setProperty("--card-scale", String(this.cardScale()));
    }
    const tall = this.cardBoxH();
    card.append(el("rect", { class: "card-shadow", x: -CARD_W / 2 + 3, y: CARD_TOP + 5,
                             width: CARD_W, height: tall, rx: 13 }));
    card.append(el("rect", { class: "card-bg", x: -CARD_W / 2, y: CARD_TOP,
                             width: CARD_W, height: tall, rx: 13 }));
    // Clamped, with the whole of it on hover. A seat is `T1` on a saved board,
    // but live an author is a peer id and an entrant picks its own name -- so
    // this has to survive `ai-lab:claude/island-economy-game-wrapper-pcm5s6`,
    // which is a real name that really appeared and really ran off the island.
    const label = el("text", { x: -CARD_W / 2 + 13, y: CARD_TOP + 25,
                               class: "card-name" }, shortName(name));
    label.append(el("title", {}, name));
    card.append(label);

    //: **No rule down the inside edge any more.** It existed because the card's
    //: own border was a half-opacity hairline and could not carry the seat's
    //: colour; the border wears it at full weight now, the way an offer's pill
    //: does, so a second stripe of the same colour is the same fact twice.

    // Labour: filled by what this trader spent this episode, and empty until a
    // production receipt says otherwise -- nobody has told this page anything
    // about their labour before then.
    const wheel = el("g", { class: "wheel",
                            transform: `translate(${CARD_W / 2 - 24} ${CARD_TOP + 19})` });
    wheel.append(el("circle", { r: 12, class: "wheel-track" }));
    wheel.append(el("circle", { r: 12, class: "wheel-fill",
                                "stroke-dasharray": "0 76", transform: "rotate(-90)" }));
    wheel.append(el("text", { y: 3.5, class: "wheel-text" }, "—"));
    card.append(wheel);
    card.append(el("text", { x: CARD_W / 2 - 43, y: CARD_TOP + 23, class: "card-sub",
                             "text-anchor": "end" }, "labour"));
    this.labels[name] = { wheel: wheel.querySelector(".wheel-fill"),
                          wheelText: wheel.querySelector(".wheel-text"),
                          card: card.querySelector(".card-bg") };

    // The shelf: goods in the manager's own order, always, so the position is
    // learned once and no legend has to be consulted again.
    this.bars[name] = {};
    const inner = CARD_W - 26;
    const step = inner / this.goods.length;
    this.goods.forEach((good, i) => {
      const cx = -CARD_W / 2 + 13 + i * step + step / 2;
      const x = cx - BAR_W / 2;
      const cell = el("g", { class: "cell", "data-good": good,
                             style: `--c: var(${SLOT[i % SLOT.length]})` });
      cell.append(el("rect", { class: "bar-track", x, y: BASE - BAR_MAX,
                               width: BAR_W, height: BAR_MAX, rx: 4 }));
      const bar = el("rect", { class: "bar", x, y: BASE - BAR_MAX,
                               width: BAR_W, height: BAR_MAX, rx: 4 });
      // Promised, not gone: the manager will not settle a second offer over the
      // same goods, so a shelf that hides commitment shows stock that cannot
      // actually be offered.
      const held = el("rect", { class: "bar-held", x, y: BASE - BAR_MAX,
                                width: BAR_W, height: BAR_MAX, rx: 4 });
      cell.append(bar, held);
      // An empty slot has to say empty. A dark trough reads as "small", and the
      // difference between small and none is the whole of Cobb-Douglas.
      //
      // This was a rule along the base of the trough, which is the one shape it
      // must not be: a short bar is *also* a rule along the base of the trough.
      // On game 002's episode 2 the trader holding no iron was less conspicuous
      // than the one holding 0.06 bread beside it, while its utility read 0.000
      // and nothing on the card said why. An outline around the whole empty
      // trough cannot be mistaken for a quantity.
      cell.append(el("rect", { class: "bar-zero", x: x + 0.75, y: BASE - BAR_MAX + 0.75,
                               width: BAR_W - 1.5, height: BAR_MAX - 1.5, rx: 4 }));
      cell.append(el("text", { x: cx, y: BASE + 17, class: "glyph" }, GLYPH[good] || "▪"));
      cell.append(el("text", { x: cx, y: BASE + 31, class: "qty" }, ""));
      card.append(cell);
      this.bars[name][good] = { cell, bar, held, qty: cell.querySelector(".qty"), x: cx };
    });
    card.append(el("line", { class: "plank", x1: -CARD_W / 2 + 9, y1: BASE + 2,
                             x2: CARD_W / 2 - 9, y2: BASE + 2 }));

    if (this.reveal && !this.geo.cardMini) {
      // What this shelf is worth to the trader who owns it. Computed here from
      // the revealed tastes and the receipts -- the manager's own scored
      // trajectory is in the rail, and `audit()` holds the two together.
      const row = el("g", { class: "score", transform: `translate(0 ${BASE + 52})` });
      const w = CARD_W - 26;
      row.append(el("text", { x: -CARD_W / 2 + 13, y: 0, class: "card-sub" }, "utility"));
      row.append(el("text", { x: CARD_W / 2 - 13, y: 0, class: "score-value",
                              "text-anchor": "end" }, "—"));
      row.append(el("rect", { class: "score-track", x: -w / 2, y: 6, width: w,
                              height: 7, rx: 3.5 }));
      row.append(el("rect", { class: "score-fill", x: -w / 2, y: 6, width: w,
                              height: 7, rx: 3.5 }));
      // Where autarky would have put them: the line worth beating, and the one
      // a round can finish below.
      const auto = this.reveal.autarky_utility?.[name];
      if (auto !== undefined && this.utilityTop > 0) {
        const at = -w / 2 + w * Math.min(1, auto / this.utilityTop);
        row.append(el("rect", { class: "score-floor", x: at - 1, y: 2, width: 2, height: 15 }));
        // Clamped: autarky can be the top of the scale (it was, for T1 in game
        // 001), which puts the tick hard against the card's right edge and the
        // label half outside it.
        row.append(el("text", { x: Math.max(-w / 2 + 16, Math.min(w / 2 - 16, at)), y: 27,
                                class: "score-floor-tag" }, "alone"));
      }
      card.append(row);
      this.labels[name].score = row.querySelector(".score-fill");
      this.labels[name].scoreText = row.querySelector(".score-value");
    }

    g.append(card);
    return g;
  }

  /**
   * One utility scale for the whole round, like the shelf's.
   *
   * Taken from the manager's recorded trajectory where there is one, so the bar
   * is measured against what actually happened rather than against whatever the
   * replay has reached so far.
   */
  utilityScale() {
    if (!this.reveal) return 0;
    let top = 0;
    for (const row of this.reveal.round?.trajectory || []) {
      for (const u of row) top = Math.max(top, u);
    }
    for (const u of Object.values(this.reveal.autarky_utility || {})) top = Math.max(top, u);
    return top || 1;
  }

  /**
   * One height scale for the whole round, not one per frame.
   *
   * A scale recomputed each frame makes a bar mean something different from one
   * message to the next: a stock that never moved would grow as its neighbours
   * shrank. The tallest stock anybody ever holds sets the ceiling once.
   */
  scale(timeline) {
    let top = 0.6;
    for (const frame of timeline.frames) {
      for (const t of this.traders) {
        for (const g of this.goods) top = Math.max(top, frame.state.stocks[t]?.[g] || 0);
      }
    }
    return top;
  }

  /** One slot's two bars, at a stock and a free-to-offer part. */
  setBar(b, qty, free, top = this.top) {
    b.bar.style.transform = `scaleY(${Math.min(1, qty / top)})`;
    b.held.style.transform = `scaleY(${Math.min(1, free / top)})`;
  }

  draw(state, timeline) {
    // Cached: the ceiling is a property of the round, and on a live board it
    // only ever rises, so recomputing it per paint would be the frame-local
    // scale this deliberately avoids.
    if (this.top === undefined || timeline.frames.length !== this.scaledAt) {
      this.top = this.scale(timeline);
      this.scaledAt = timeline.frames.length;
    }
    const top = this.top;
    // After the bell the shelf is empty and a live reading says zero for every
    // good, which is true and useless -- and it made the card contradict
    // itself, because the utility beneath already held the closing basket.
    // Game 002's last frame read `UTILITY 0.208` over four zeros. What the
    // episode was worth is what it closed holding, so the shelf holds it too,
    // until the next episode opens.
    const closed = state.phase === "closed" || state.phase === "over";
    const last = state.episodes_closed[state.episodes_closed.length - 1];
    // Before the round starts nobody has produced, so every slot is empty and
    // none of it means anything yet. The zero mark is a finding about play, and
    // there has not been any -- eight red troughs on the opening frame say the
    // island is on fire when it has not been lit.
    const started = state.phase !== "before" && state.phase !== "ack";
    for (const name of this.traders) {
      const promised = (good) => timeline.committed(state, name, good);
      const shelf = closed && last ? last.holdings[name] : state.stocks[name];
      // A trader that has not produced yet holds none of everything, which is
      // trivially true and says nothing. The zero mark is for a trader that
      // spent its labour and still ended up with none of something -- the
      // Cobb-Douglas hazard -- so it waits for the labour to be spent, or for
      // the bell, which is when a zero is final whatever was spent.
      const spentLabour = closed || state.labour[name] !== null;
      for (const good of this.goods) {
        const qty = shelf?.[good] || 0;
        const b = this.bars[name][good];
        const free = Math.max(0, qty - promised(good));
        // What this slot looked like *before* this frame, kept so `produce()`
        // can put it back. `paint()` calls `draw()` and then `play()`, so by
        // the time production is animated the shelf has already been filled
        // by it -- which is why the goods used to arrive at a bar that had
        // finished growing half a second earlier.
        b.was = b.now ?? { qty: 0, free: 0 };
        b.now = { qty, free };
        if (!b.holding) this.setBar(b, qty, free, top);
        // Two decimals is what a reader can hold. The receipts carry four and
        // the page must not imply more precision than they do.
        // Zero is a number and gets written as one. Blank reads as "not
        // applicable"; `0.00` in the critical colour reads as "none, and that
        // is the problem". `<0.01` keeps a rounded-down holding from printing
        // the same "0.00" as an actual zero.
        b.qty.textContent = qty <= 1e-9 ? "0.00"
          : qty < 0.005 ? "<0.01" : qty.toFixed(2);
        const none = started && spentLabour && qty <= 1e-9;
        b.qty.classList.toggle("none", none);
        b.cell.classList.toggle("empty", none);
      }
      const spent = state.labour[name];
      // Named for what it holds -- every writable node on this card -- rather
      // than for the first one that was needed. The score row below reads off
      // the same object and shadowed it with a second `const label`, which is
      // how a guard written against `label` came to be a ReferenceError.
      const label = this.labels[name];
      const arc = 2 * Math.PI * 12;
      const used = spent === null ? 0 : Math.max(0, Math.min(1, 1 - spent));
      label.wheel.setAttribute("stroke-dasharray", `${(used * arc).toFixed(2)} ${arc}`);
      label.wheelText.textContent = spent === null ? "—" : `${Math.round(used * 100)}`;
      // `label.score` and not `this.reveal`: a glance card has no score row to
      // write into, and the card is what decides that, not the board.
      if (this.reveal && label.score) {
        // After the bell the shelf is empty and a live reading would say zero,
        // which is true and useless: what the episode was worth is what it
        // closed holding. Hold that until the next episode opens.
        const u = utilityOf(this.reveal, name, shelf);
        const w = CARD_W - 26;
        label.score.setAttribute("width",
          (w * Math.max(0, Math.min(1, (u || 0) / this.utilityTop))).toFixed(2));
        label.scoreText.textContent = u === null ? "—" : u.toFixed(3);
        // Zero before anybody has produced is not a failed episode, for the
        // same reason an empty shelf is not a starved one: there has been no
        // play yet. The critical colour waits for there to be some.
        label.scoreText.classList.toggle("zero",
          started && spentLabour && u !== null && u <= 1e-12);
      }
      const hut = this.root.querySelector(`.hut[data-trader="${name}"]`);
      hut.classList.toggle("quiet", !state.spoke.includes(name));
      const held = this.goods.map((g) => state.stocks[name]?.[g] || 0);
      // Ruin, in the sense the metric cares about: something on the shelf, and
      // nothing at all of something else. Cobb-Douglas puts that at zero.
      hut.classList.toggle("starved",
        held.some((q) => q > 1e-12) && held.some((q) => q <= 1e-12));
    }
    // Offers between the same two huts would otherwise land on one curve and
    // hide each other -- and "how many are open" is exactly what a spectator is
    // reading the square for. Fan them by pair.
    const open = state.proposals.filter((p) => p.status === "open");
    this.stack = this.stacking(open);
    const rank = new Map();
    const placed = new Map();
    this.ropes.replaceChildren(...open.map((p) => {
      const pair = [p.maker, p.taker].sort().join("~");
      const i = rank.get(pair) || 0;
      rank.set(pair, i + 1);
      placed.set(p.pid, i);
      return this.rope(p, i);
    }));
    // A rope that lapsed used to vanish between two paints, and how many offers
    // died unanswered is exactly what a spectator is counting. Fray it on the
    // way out instead -- but only when it was on screen a moment ago, so
    // scrubbing backwards over an old bell does not replay somebody else's.
    const was = this.shown || new Map();
    for (const p of state.proposals) {
      if (!was.has(p.pid)) continue;
      if (p.status === "lapsed") this.fray(p, was.get(p.pid));
      // The rope of a settled offer is gone from `this.ropes` by the time
      // `play()` runs -- only open offers are drawn -- so the answer an offer
      // got is said here, on a copy, or it is not said at all.
      else if (p.status === "settled") this.verdict(p, was.get(p.pid), "approved");
    }
    this.shown = placed;
    //: A pill's clock lives as long as its offer is open. Dropping it when the
    //: offer closes is what lets a viewer scrub backwards over a proposal and
    //: watch it travel again -- and stops the map growing for the whole round.
    for (const pid of [...this.travel.keys()]) {
      if (!placed.has(pid)) this.travel.delete(pid);
    }
    //: Dropped one paint later than the clock would allow, because `fray` and
    //: `verdict` draw a copy of an offer that has just stopped being open and
    //: it has to leave from where the pill actually was.
    for (const pid of [...this.spot.keys()]) {
      if (!placed.has(pid) && !this.wasStack?.has(pid)) this.spot.delete(pid);
    }
    // Kept so a refusal played straight after this paint can find what was
    // open at the moment it happened.
    this.state = state;
    this.root.classList.toggle("closed", closed);
  }

  /** One rope, dissolving, after the bell took the offer with it. */
  fray(p, fan) {
    //: Arrived, not travelling: a rope only lapses after its pill has landed,
    //: and a pill that started its slide again on the way out would leave the
    //: hut it had been waiting over.
    const node = this.rope(p, fan, 1);
    node.classList.add("lapsing");
    this.flights.append(node);
    //: **Dissolved, not switched off.** A plain fade read as the page dropping
    //: the offer; an offer the bell took is a thing that came apart. So it
    //: blurs, lifts and loses colour on the way out, and `.rope.lapsing` in
    //: index.html scatters its dashes at the same time.
    const anim = node.animate([
      { opacity: 1, filter: "blur(0px)", transform: "translateY(0) scale(1)" },
      { opacity: .5, filter: "blur(1.5px)",
        transform: "translateY(-6px) scale(1.015)", offset: .45 },
      { opacity: 0, filter: "blur(6px)", transform: "translateY(-18px) scale(1.04)" },
    ], { duration: still() ? 1 : 1300, easing: "ease-in", fill: "forwards" });
    anim.finished.then(() => node.remove(), () => node.remove());
  }

  /**
   * The answer an offer got, blinked on the rope itself.
   *
   * Green for approved, on a copy in `flights`: a settled offer is off the
   * square by the time this runs, since `paint()` draws only open ones. A
   * refusal leaves its offer open, so `refuse()` marks the live rope instead
   * and shares these classes.
   *
   * The colour is the content, so under `prefers-reduced-motion` the copy is
   * still drawn in that colour; only the blinking goes (`index.html`).
   */
  verdict(p, fan, kind) {
    const node = this.rope(p, fan, 1);
    node.classList.add("answered", kind);
    this.flights.append(node);
    const anim = node.animate(
      [{ opacity: 1 }, { opacity: 1, offset: .72 }, { opacity: 0 }],
      { duration: still() ? 1 : 1400, easing: "ease-out", fill: "forwards" });
    anim.finished.then(() => node.remove(), () => node.remove());
  }

  /**
   * Where a rope hangs, given who is at each end and how many share the pair.
   *
   * **Drawn from the maker to the taker, and that direction is the content.**
   * The dashes crawl along the path, so a line built the other way round would
   * animate goods flowing to the trader who is offering them.
   */
  ropePath(p, fan) {
    const a = this.pins[p.maker], b = this.pins[p.taker];
    if (!a || !b) return null;
    const lift = this.modelled ? 34 : 84;
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2 - lift - 64 - fan * 44;
    //: **The arc is fanned by pair and the pill is stacked by taker**, which
    //: are two different numbers. Fanning the arcs keeps two offers between the
    //: *same* two huts off one curve; but three traders offering the same hut
    //: all sit at fan 0, and their pills landed on that one roof on top of each
    //: other -- exactly where a spectator counts what a trader has to answer.
    return { d: `M ${a.x} ${a.y - lift} Q ${mx} ${my} ${b.x} ${b.y - lift}`,
             mx, my, a, b, lift, fan,
             top: this.ceiling(),
             stack: this.stack?.get(p.pid) ?? this.wasStack?.get(p.pid)
                    ?? { i: fan, of: fan + 1 } };
  }

  /**
   * The height a pile of pills is not allowed through, in viewBox units.
   *
   * **Measured off the drawing rather than derived from the layout**, because
   * the answer is not a property of the viewBox: a frame whose shape is not the
   * window's is fitted inside it with `meet` and centred, so in landscape there
   * is real picture above `y = 0` -- a third of a 1500x1000 window, at the
   * frame this draws -- and a ceiling taken from the layout alone squeezed
   * piles that had room to stand. What actually cuts a pill off is the `svg`'s
   * own box, which clips, and the floating chrome, which is opaque and sits on
   * top; both are on the page and can simply be asked.
   *
   * Falls back to the top of the island's own band, which is what the layout
   * knows on its own, if the drawing has no size yet.
   */
  ceiling() {
    const box = this.root?.viewBox?.baseVal;
    const r = this.root?.getBoundingClientRect();
    if (!box?.height || !r?.height || !r?.width) {
      return (this.geo?.islandBox?.y ?? 0) + PILL_H;
    }
    const scale = Math.min(r.width / box.width, r.height / box.height);
    if (!(scale > 0)) return (this.geo?.islandBox?.y ?? 0) + PILL_H;
    //: Where the top of the window falls, in the units this is drawn in --
    //: negative wherever the frame is letterboxed.
    const top = box.y - (r.height - box.height * scale) / 2 / scale;
    const chrome = parseFloat(getComputedStyle(document.documentElement)
      .getPropertyValue("--chrome-top")) || 0;
    //: A whole pill clear of it, not half: half puts the topmost pill's edge
    //: flush against the window's, which reads as cut off whether or not it is.
    return top + chrome / scale + PILL_H;
  }

  /**
   * How high each arrived pill sits on the hut it is waiting over.
   *
   * By **taker**, and in the order the offers were made, so the pile on a hut
   * is the queue that hut has to answer, oldest at the bottom. Kept as a map on
   * the scene rather than passed down because `ropePath` is reached from four
   * places -- `paint`, `follow`, `fray` and `verdict` -- and only one of them
   * knows what else is open.
   */
  stacking(open) {
    //: The frame before is kept because a pill on its way out is drawn *after*
    //: the offer stopped being open: `fray` and `verdict` build their copy from
    //: a proposal this map no longer carries, and it has to leave the pile from
    //: the height it was sitting at rather than dropping to the roof first.
    this.wasStack = this.stack;
    return stacking(open);
  }

  /**
   * The seat's colour, for whoever is named.
   *
   * A trader's index in `traders` is the same index the island picks its hut's
   * colour by, and it is given the same seat count, so an offer's pill is the
   * colour of the hut that made it however many huts there are.
   *
   * The ring is built once per scene rather than once per pill: it is `n`
   * colour conversions, and `paint()` draws every open offer.
   */
  seatColour(name) {
    this.ring ??= seatRing(this.traders.length);
    const i = this.traders.indexOf(name);
    return this.ring[i < 0 ? 0 : i];
  }

  /**
   * How far down its rope an offer's pill has got: 0 at the maker, 1 arrived.
   *
   * The clock starts the first time the pill is drawn and is kept by pid, not
   * by node -- the rope is rebuilt whenever the set of open offers changes and
   * on every reflow, and a slide restarted by a rebuild is a pill that never
   * lands. A viewer who asked for less motion gets it arrived.
   */
  progress(pid, force = null) {
    if (force !== null) return force;
    if (still()) return 1;
    let t0 = this.travel.get(pid);
    if (t0 === undefined) { t0 = performance.now(); this.travel.set(pid, t0); }
    return Math.max(0, Math.min(1, (performance.now() - t0) / SLIDE));
  }

  /**
   * The pill's drawn position: never the target, always on its way to it.
   *
   * **A pill only ever flies.** Everything that moves one used to move it by
   * setting a new place: a pill below it in the pile lapsing and the ones above
   * dropping a slot, a pile compressing as it grew, a pair's fan changing when
   * a second offer between the same two huts closed -- and, every single time,
   * the arrival itself, because the end of the rope and the resting spot over
   * the hut are two different points and the pill jumped between them.
   *
   * So the target is followed rather than taken. The drawn point eases toward
   * wherever the geometry says it should be, at a rate that does not depend on
   * how often this is called, and the loop in `ride()` keeps running while any
   * pill is still catching up.
   *
   * A viewer who asked for less motion gets the target, arrived.
   */
  glide(pid, target) {
    if (still()) return target;
    const now = performance.now();
    const was = this.spot.get(pid);
    if (!was) { this.spot.set(pid, { ...target, at: now }); return target; }
    //: Time-based, not per-frame: a 120Hz screen must not settle the pill twice
    //: as fast as a 60Hz one.
    //:
    //: **Clamped to one slow frame**, and that clamp is the whole thing
    //: working. A settled pill is not being glided -- the loop in `ride()` has
    //: stopped -- so when its pile changes under it, the gap since the last
    //: step is however long it sat there, and an unclamped ease covers the
    //: whole distance in that first step. Measured: the drop of a slot when the
    //: pill below it settles moved 38 units in one frame, which is the jump
    //: this exists to remove, wearing an ease. Idle time is not animation time.
    const { x, y } = glideTo(was, target, now - was.at);
    const near = Math.hypot(target.x - x, target.y - y) < 0.35;
    const spot = near ? { ...target, at: now } : { x, y, at: now };
    this.spot.set(pid, spot);
    //: Still moving, so the loop has to keep going -- the pill may have arrived
    //: at the end of its rope a second ago and still be rising into the pile.
    if (!near) { this.settling = true; this.ride(); }
    return spot;
  }

  /**
   * Where the pill sits, given how far along it is.
   *
   * On the way: the point at `t` of the same quadratic the rope is drawn as, so
   * the pill rides the line rather than crossing the frame beside it. Arrived:
   * over the *taker's* hut, which is the whole content of the picture -- an
   * offer that has been delivered is a thing waiting on the trader it is
   * addressed to, and it stays there until that trader answers it or the bell
   * takes it away.
   */
  chipAt(at, prog) {
    if (prog >= 1) {
      const foot = at.b.y - at.lift - 58;
      //: One pill-and-a-gap apart -- so a hut with three waiting on it reads as
      //: a pile of three rather than one pill with something behind it --
      //: **until the pile would leave the frame**, and then as far apart as
      //: what is left allows. A pile that grew freely put its top pills off the
      //: top of the picture, where a spectator counting what a trader has been
      //: asked cannot count them at all; overlapping pills can still be counted.
      const room = Math.max(0, foot - at.top);
      const step = Math.min(PILL_STEP, room / Math.max(1, at.stack.of - 1));
      return { x: at.b.x, y: foot - at.stack.i * step };
    }
    // Ease out: it leaves the maker's roof quickly and settles onto the
    // taker's, rather than arriving at full speed and stopping dead.
    const t = 1 - (1 - prog) * (1 - prog);
    const ax = at.a.x, ay = at.a.y - at.lift, bx = at.b.x, by = at.b.y - at.lift;
    const k = 1 - t;
    return { x: k * k * ax + 2 * k * t * at.mx + t * t * bx,
             y: k * k * ay + 2 * k * t * at.my + t * t * by + 20 };
  }

  /**
   * Keep every pill still in flight moving, frame by frame.
   *
   * Its own loop rather than a CSS or WAAPI animation, because the rope moves
   * under the pill: the camera turns the island continuously, so a set of
   * keyframes sampled when the offer opened would walk a path that is no
   * longer where the huts are. One loop for all of them, stopped as soon as the
   * last one lands.
   */
  ride() {
    if (this.riding) return;
    this.riding = true;
    const step = () => {
      let flying = false;
      //: Set by `glide` for any pill that has not caught its target yet, and
      //: cleared here so it is asked afresh every frame. A pill can be still
      //: travelling, still settling, or both.
      this.settling = false;
      for (const p of this.state?.proposals ?? []) {
        if (p.status !== "open") continue;
        const node = this.ropes?.querySelector(`.rope[data-pid="${p.pid}"]`);
        if (!node) continue;
        if (this.progress(p.pid) < 1) flying = true;
        this.aimRope(node, p, this.shown?.get(p.pid) ?? 0);
      }
      if (flying || this.settling) requestAnimationFrame(step);
      else this.riding = false;
    };
    requestAnimationFrame(step);
  }

  /**
   * Move a rope already on screen to where its settlements are now.
   *
   * **In place, because the dashes are an animation.** `follow` runs on every
   * frame the camera turns -- which is every frame -- and it used to rebuild
   * every rope from scratch each time. A fresh node restarts its CSS
   * animation, so the crawl was reset sixty times a second and the line sat
   * perfectly still: an offer that is supposed to show goods heading for the
   * trader they are offered to showed a static dashed line instead.
   */
  aimRope(g, p, fan, force = null) {
    const at = this.ropePath(p, fan);
    if (!at) return;
    for (const path of g.querySelectorAll(".rope-shadow, .rope-line")) {
      path.setAttribute("d", at.d);
    }
    const prog = this.progress(p.pid, force);
    // Arrived: the rope has said what it had to say -- who sent this to whom --
    // and goes, leaving the offer standing over the trader it is addressed to.
    g.classList.toggle("delivered", prog >= 1);
    const spot = this.glide(p.pid, this.chipAt(at, prog));
    g.querySelector(".rope-chip")?.setAttribute(
      "transform", `translate(${spot.x.toFixed(2)} ${spot.y.toFixed(2)})`);
  }

  rope(p, fan = 0, force = null) {
    // Between the *settlements*, not the cards. An offer is a thing happening
    // on the island between two huts; drawn between two cards in the margins it
    // would be a line across the whole frame, over everything, saying nothing
    // about where it is happening.
    const at = this.ropePath(p, fan);
    if (!at) return el("g");
    const { d } = at;
    //: The maker's colour, on the group, so everything in the pill can wear it
    //: and `.rope.lapsing` can still take it back with a plain rule.
    const g = el("g", { class: "rope", "data-pid": p.pid,
                        "data-maker": p.maker, "data-taker": p.taker,
                        style: `--seat: ${this.seatColour(p.maker)}` });
    g.append(el("path", { class: "rope-shadow", d }));
    g.append(el("path", { class: "rope-line", d }));
    const prog = this.progress(p.pid, force);
    //: Through the glide, so a rope rebuilt under a pill -- which is what a
    //: changed set of offers does to all of them -- puts the new node's pill
    //: back where the old one had got to, rather than at the target.
    const spot = this.glide(p.pid, this.chipAt(at, prog));
    const chip = el("g", { class: "rope-chip",
                           transform: `translate(${spot.x.toFixed(2)} ${spot.y.toFixed(2)})` });
    const text = `${bundleText(p.give)} → ${bundleText(p.want)}`;
    const width = Math.max(104, text.length * 8.4);
    chip.append(el("rect", { x: -width / 2, y: -16, width, height: 32, rx: 16,
                             class: "chip-bg" }));
    //: A dot of the maker's colour inside the pill as well as around it. The
    //: border alone is two pixels of colour at the size this is drawn, and the
    //: palette does not clear all-pairs at that width -- the dot is the part a
    //: viewer can actually match to a roof.
    chip.append(el("circle", { class: "chip-seat", cx: -width / 2 + 13, cy: -0.5, r: 4.5 }));
    chip.append(el("text", { x: 7, y: 5, class: "chip-text" }, text));
    //: **No `p2 · T1→T4` under the pill.** The pid is a manager's word for the
    //: ledger, and the arrow repeated what the pill's colour and the rope it
    //: hangs from already say: whose offer this is, and which hut it is
    //: addressed to. It is on the group as `data-pid`/`data-maker` for
    //: `viewer/tests/render.py`, which is where a name nobody reads belongs.
    g.append(chip);
    if (prog >= 1) g.classList.add("delivered");
    else this.ride();
    //: A rope rebuilt while its refusal is still on screen is re-marked here,
    //: or the blink would last one frame.
    if ((this.noUntil.get(p.pid) || 0) > performance.now()) this.markNo(g);
    return g;
  }

  /**
   * The red answer, on one rope: the classes and the ✗ that rides its pill.
   *
   * Marked on the **live** rope rather than on a copy, since a refusal does not
   * close the offer and a red copy laid over the orange original would blink to
   * the wrong colour between flashes.
   */
  markNo(g, reason = "") {
    g.classList.add("answered", "refused");
    const chip = g.querySelector(".rope-chip");
    if (!chip || chip.querySelector(".chip-no")) return;
    const bg = chip.querySelector(".chip-bg");
    const x = Number(bg?.getAttribute("width") || 104) / 2 + 13;
    const no = el("g", { class: "chip-no", transform: `translate(${x} 0)` });
    const why = reason || this.noWhy || "";
    if (why) no.append(el("title", {}, why));
    no.append(el("path", { class: "chip-cross", d: "M -6 -6 L 6 6 M 6 -6 L -6 6" }));
    chip.append(no);
  }

  // --- what an event looks like ---------------------------------------------

  play(event) {
    switch (event.kind) {
      case "settled": return this.flight(event);
      case "produced": return this.produce(event);
      // A symbol, and the reason kept as the badge's title rather than printed
      // over the sand. What the manager wrote is in the ticker; the island says
      // *that* it refused, and whose.
      case "refused": {
        this.blame(event.trader, event.reason);
        //: The red blink on the offer *is* the refusal (Gal, 2026-08-28). The
        //: bubble over the hut said the same thing a second time, further from
        //: the square than the thing it was about, so it is kept only for the
        //: refusals that have no rope to blink -- a refusal at proposal time is
        //: about an offer that does not exist yet, and something must still say
        //: it happened.
        const blinked = this.refuse(event.trader, event.reason);
        return blinked ? undefined : this.mark(event.trader, "bad", event.reason);
      }
      // An attempt draws nothing: what it attempted arrives as the receipt or
      // the refusal, and drawing both says it twice.
      case "said": return event.attempt ? undefined : this.mark(event.author, "talk");
      case "bell": return this.bell(event);
      case "open": return this.dawn(event);
      case "over": return this.banner_("the round is over");
      case "fault": return this.banner_("harness fault");
      default: return undefined;
    }
  }

  /**
   * Why the manager refused, pointed at rather than described.
   *
   * The refusal text is already in the ticker and on the badge's tooltip. What
   * it cannot do there is say *which* rope on the square is the problem, and
   * that is the whole content of a refusal for goods an offer of the trader's
   * own has already promised away. So light the slot it came up short in and
   * the offer that is holding it, together, for as long as the badge is up.
   *
   * Marked, not moved: the highlight stays under `prefers-reduced-motion`
   * because it carries information. Reduced motion means less movement, not
   * less to read.
   */
  blame(who, reason = "") {
    const held = [];
    const short = SHORT.exec(reason);
    if (short) {
      const good = short[2];
      const cell = this.bars[who]?.[good]?.cell;
      if (cell) held.push(cell);
      for (const p of culprits(this.state?.proposals, who, good)) {
        const rope = this.ropes.querySelector(`.rope[data-pid="${p.pid}"]`);
        if (rope) held.push(rope);
      }
    }
    const theirs = NOT_YOURS.exec(reason);
    if (theirs) {
      // Not the trader's own slot at fault -- the offer simply belongs to
      // somebody else, so the only thing worth pointing at is the rope.
      const rope = this.ropes.querySelector(`.rope[data-pid="${theirs[1]}"]`);
      if (rope) held.push(rope);
    }
    if (!held.length) return;
    for (const node of held) node.classList.add("blamed");
    // Cleared on a timer rather than on the badge's animation, because the
    // badge is gone in 1ms under reduced motion and the reader still needs it.
    clearTimeout(this.blameTimer);
    this.blameTimer = setTimeout(() => {
      for (const node of held) node.classList.remove("blamed");
    }, DWELL.refused);
  }

  /**
   * The offer a refusal was about, blinked red.
   *
   * `blame()` says which *stock* the trader came up short in; this says which
   * offer the manager would not settle -- the one thing a spectator watching
   * the square is looking for. It is the whole indicator: the badge over the
   * hut is drawn only when this finds nothing, so this returns whether it did.
   * Only offers the manager itself
   * named, or the offer it was answering: a refusal at proposal time is about
   * an offer that does not exist yet, and there is nothing on the square to
   * blink.
   */
  refuse(who, reason = "") {
    const pids = refused(this.state?.proposals, who, reason).map((p) => p.pid);
    if (!pids.length) return false;
    //: An ✗ on the pill as well as the colour: red alone is a colour a viewer
    //: reads as "an answer", and the cross is *which* answer. It carries the
    //: manager's reason as its `<title>`, which is where the badge kept it.
    this.noWhy = reason;
    const until = performance.now() + DWELL.refused;
    for (const pid of pids) {
      this.noUntil.set(pid, until);
      const rope = this.ropes.querySelector(`.rope[data-pid="${pid}"]`);
      if (rope) this.markNo(rope, reason);
    }
    //: On a timer, as `blame()` is, and for the same reason: under reduced
    //: motion there is no animation to hang the clean-up off, and the reader
    //: still needs the colour for as long as the mark is meant to be up.
    clearTimeout(this.refuseTimer);
    this.refuseTimer = setTimeout(() => {
      for (const pid of pids) {
        this.noUntil.delete(pid);
        const rope = this.ropes.querySelector(`.rope[data-pid="${pid}"]`);
        if (!rope) continue;
        rope.classList.remove("answered", "refused");
        rope.querySelector(".chip-no")?.remove();
      }
    }, DWELL.refused);
    return true;
  }

  /**
   * Somebody did something, said as a shape.
   *
   * The island used to print the manager's refusal text across the sand, which
   * is unreadable at that size and is already in the ticker underneath. And it
   * drew nothing at all when a trader merely spoke -- so a board where two
   * agents talked and settled nothing looked identical to one where nobody
   * turned up.
   */
  mark(who, kind, title = "") {
    //: **Over the hut, not over the card.** A refusal and a remark are things a
    //: *trader* did, and the trader on this page is the settlement standing on
    //: the island -- the card is the ledger beside it, out in the frame's
    //: margin. The bubbles were drawn above the card, so the one picture that
    //: says "this one just spoke" appeared a third of a frame away from the
    //: thing that spoke, and read as chrome rather than as the island.
    //:
    //: `pins` is where the model put the settlement, refreshed every frame by
    //: `follow`; `seats` is the card, and is the fallback for a browser with no
    //: model, where the two are the same place anyway.
    const at = this.pins[who] ?? this.seats[who];
    if (!at) return;
    //: Two groups. The outer one holds the *place* and is moved by `follow` as
    //: the camera goes round; the inner one holds the *rise* and is animated.
    //: One group doing both would have the animation's transform overwrite the
    //: position every frame, and the bubble would sit where the hut was when
    //: it opened.
    const anchor = el("g", { class: "pop-at", "data-trader": who,
                             transform: `translate(${at.x} ${at.y})` });
    const g = el("g", { class: `pop ${kind}` });
    if (title) g.append(el("title", {}, title));
    g.append(el("path", { class: "pop-bubble",
                          d: "M -21 -17 h 42 a 9 9 0 0 1 9 9 v 15 a 9 9 0 0 1 -9 9 " +
                             "h -14 l -7 8 l -7 -8 h -14 a 9 9 0 0 1 -9 -9 v -15 " +
                             "a 9 9 0 0 1 9 -9 z" }));
    if (kind === "bad") {
      g.append(el("path", { class: "pop-cross", d: "M -7 -7 L 7 7 M 7 -7 L -7 7" }));
    } else {
      [-9, 0, 9].forEach((dx, i) => g.append(el("circle", {
        class: "pop-dot", cx: dx, cy: 0, r: 2.6,
        style: `animation-delay: ${i * 0.16}s`,
      })));
    }
    anchor.append(g);
    this.flights.append(anchor);
    //: Purely vertical, and relative to the anchor. `POP_UP` clears the roof of
    //: the hut it belongs to at the scale the model draws one.
    const anim = g.animate([
      { transform: `translate(0px, ${-POP_UP + 22}px) scale(.6)`, opacity: 0 },
      { transform: `translate(0px, ${-POP_UP}px) scale(1)`, opacity: 1,
        offset: 0.18 },
      { transform: `translate(0px, ${-POP_UP - 8}px) scale(1)`, opacity: 1,
        offset: 0.72 },
      { transform: `translate(0px, ${-POP_UP - 36}px) scale(.9)`, opacity: 0 },
    ], { duration: still() ? 1 : DWELL[kind === "bad" ? "refused" : "said"],
         easing: "ease-out" });
    anim.finished.then(() => anchor.remove(), () => anchor.remove());
  }

  /**
   * Production, which used to have no picture at all.
   *
   * `state.made` has been in the reducer since it was written and nothing drew
   * it, so the one thing a trader does entirely on its own was a text bubble
   * reading "produced". Lift what was made out of the hut and onto its slot.
   */
  produce(e) {
    const seat = this.seats[e.trader];
    if (!seat) return;
    const made = Object.entries(e.made || {}).filter(([, q]) => q > 1e-9);
    if (!made.length) return;

    // The hut works before anything comes out of it. Production is the one
    // thing a trader does entirely alone, and it used to have no beginning --
    // goods simply appeared in the air above the shelf.
    const hut = this.root.querySelector(`.hut[data-trader="${e.trader}"]`);
    hut?.classList.add("working");
    const wheel = this.labels[e.trader];
    //: The wheel fills while the site works and the crates cross, which is the
    //: labour being spent -- it is finished by the time the first crate is in
    //: the yard, and the symbols are what happens after that.
    const span = still() ? 1 : madeBy(0) - MAKE.rest;

    // The labour goes as the goods come. One unit divided across the shelf is
    // the entire decision a trader makes here, and the wheel filling silently
    // in the corner said none of it.
    if (!still() && wheel?.wheel) {
      const arc = 2 * Math.PI * 12;
      const to = wheel.wheel.getAttribute("stroke-dasharray");
      wheel.wheel.animate(
        [{ strokeDasharray: `0 ${arc}` }, { strokeDasharray: to }],
        { duration: span, easing: "cubic-bezier(.4,0,.3,1)" });
    }

    //: **The same last leg as an exchange's.** A production used to fill the
    //: shelf off its own clock: the symbols left the yard inside the first
    //: second while the crates were still walking home at two and a half, so a
    //: bar filled from goods that had not arrived. Reported by eye, as the
    //: trades looking right and production not.
    //:
    //: It is `hand(..., "in", ...)` now -- the identical motion, on the
    //: identical schedule shape: `madeBy(i)` is when that good's crate is
    //: certainly standing in the yard, and `IN_LEG` is the rise off it. Which
    //: means the fix that made an exchange's symbols leave from the crate --
    //: built at the moment they fly, not cued three seconds earlier against an
    //: island that then turns -- is the same code here and cannot drift from
    //: it. A production's crates land *open* now, because there is finally
    //: something coming out of them.
    made.forEach(([good, qty], i) => {
      this.hand(e.trader, good, qty, "in", still() ? 2 : madeBy(i),
                still() ? 1 : IN_LEG);
    });

    setTimeout(() => hut?.classList.remove("working"), still() ? 1 : span);
  }

  /** Goods crossing the square. The only moment a trade is visible as motion. */
  flight(e) {
    const a = this.seats[e.maker], b = this.seats[e.taker];
    if (!a || !b) return;
    //: **With a model, the goods cross the island and not the card layer.**
    //: The boxes themselves come off one trader's pile, fly the offer's line
    //: and stack in the other's, so a parcel drawn across the square as well
    //: would be the page saying it twice -- and the two would disagree the
    //: first time one of them was a frame behind.
    //:
    //: What the cards do instead is the two ends of that journey: the bar that
    //: is losing empties *into* its own boxes, and the bar that is gaining
    //: fills *from* the boxes arriving. A symbol never crosses the square; it
    //: only ever goes between a pile and the card that counts it.
    if (Object.keys(this.yards).length) return this.hands(e);
    const send = (from, to, bundle, cls) => {
      // Staggered: a three-good bundle sent all at once is one blur, and how
      // much crossed the square is the thing a spectator is here for.
      Object.entries(bundle).forEach(([good, qty], i) => {
        const parcel = el("g", { class: `parcel ${cls}` });
        parcel.append(el("circle", { r: 3, class: "parcel-trail" }));
        parcel.append(el("circle", { r: 17, class: "parcel-bg",
                                     style: `--c: var(${SLOT[this.goods.indexOf(good) % SLOT.length]})` }));
        parcel.append(el("text", { y: 5, class: "parcel-glyph" }, GLYPH[good] || "▪"));
        parcel.append(el("text", { y: 32, class: "parcel-qty" }, qty.toFixed(2)));
        this.flights.append(parcel);
        const lift = -96;
        const frames = [
          { transform: `translate(${from.x}px, ${from.y - 42}px) scale(.55) rotate(0deg)`,
            opacity: 0 },
          { transform: `translate(${from.x * .72 + to.x * .28}px, ` +
                       `${(from.y + to.y) / 2 + lift * .8}px) scale(1) rotate(-7deg)`,
            opacity: 1, offset: .28 },
          { transform: `translate(${(from.x + to.x) / 2}px, ` +
                       `${(from.y + to.y) / 2 + lift}px) scale(1.05) rotate(0deg)`,
            opacity: 1, offset: .55 },
          { transform: `translate(${to.x}px, ${to.y - 42}px) scale(.62) rotate(8deg)`,
            opacity: 0 },
        ];
        const anim = parcel.animate(frames, {
          duration: still() ? 1 : 1700, delay: still() ? 0 : i * 230,
          easing: "cubic-bezier(.4,0,.2,1)", fill: "backwards",
        });
        anim.finished.then(() => parcel.remove(), () => parcel.remove());
      });
    };
    send(a, b, e.give, "out");
    send(b, a, e.want, "back");
    const rope = this.ropes.querySelector(`.rope[data-pid="${e.pid}"]`);
    if (rope) rope.classList.add("settling");
  }

  /**
   * The bell: the sun goes down, the fire comes up, and it stays dark.
   *
   * It was a black rectangle flashed over the picture and then full daylight
   * again. Two things were wrong with that. It read as the page breaking
   * rather than as the day ending -- and it was a *pulse*, so a spectator who
   * scrubbed to a closed frame saw noon.
   *
   * Night is a state now: `draw()` puts `.closed` on the root and the CSS holds
   * dusk there, so scrubbing lands in the dark without any event being played.
   * This method only plays the passage.
   */
  /**
   * A settled exchange, on the cards: what each side loses and what it gains.
   *
   * Three legs in sequence, and the middle one is not drawn here at all.
   *
   * 1. The **losing** bar unfills and its symbols fly down to its own pile,
   *    which is where the boxes are waiting to be sent.
   * 2. The boxes cross the island. That is `island-events.js` and it is the
   *    only thing that moves between the two settlements.
   * 3. The symbols fly off the arriving boxes up to the **gaining** bar, and
   *    the bar fills as they land.
   *
   * So a good is in exactly one place at every moment of the exchange, and no
   * bar changes until something has arrived to change it.
   */
  /** Drop anything scheduled and not yet drawn. */
  unpend_() {
    for (const id of this.pending ?? []) clearTimeout(id);
    this.pending = [];
  }

  hands(e) {
    //: The exchange on screen is this one. A symbol still waiting to leave a
    //: crate for the last one would arrive at a bar that has moved on.
    this.unpend_();
    //: The losing card has to be empty before its boxes leave, so this ends a
    //: beat short of `CARRY.off` rather than running up against it.
    const OUT = still() ? 1 : CARRY.off - 40;
    const IN = still() ? 1 : IN_LEG;
    const move = (owner, taker, bundle, back) => {
      Object.entries(bundle || {}).filter(([, q]) => q > 1e-9)
        .forEach(([good, qty], i) => {
          const out = still() ? 0 : (back ? CARRY.back : 0) + i * CARRY.step;
          this.hand(owner, good, qty, "out", out, OUT);
          //: **After the boxes are standing in the yard, not while they fly.**
          //: This used to be `delay + OUT + CROSS` against a `CROSS` of 1500,
          //: which put it 30ms before the boxes touched down and 530ms before
          //: they had finished settling -- the gaining bar filled from goods
          //: that were still in the air.
          this.hand(taker, good, qty, "in", still() ? 2 : carriedBy(i, back), IN);
        });
    };
    move(e.maker, e.taker, e.give, false);
    move(e.taker, e.maker, e.want, true);
    const rope = this.ropes.querySelector(`.rope[data-pid="${e.pid}"]`);
    if (rope) rope.classList.add("settling");
  }

  /**
   * One symbol between a trader's card and that trader's own pile of one good.
   *
   * `"out"` is losing it: the bar empties first and the symbol falls to the
   * boxes, which are about to be carried off. `"in"` is gaining it: the symbol
   * rises off the boxes that just landed and the bar fills when it arrives.
   * The bar is only ever changed by something reaching it.
   */
  hand(name, good, qty, way, delay, span) {
    const seat = this.seats[name], slot = this.bars[name]?.[good];
    if (!seat || !slot) return;
    // Held at what it was until the symbol lands, the same way `produce()`
    // holds a shelf: a bar that moved on its own would win the race and the
    // symbol would arrive at a bar that had already finished changing.
    slot.holding = true;
    if (way === "in") this.setBar(slot, slot.was.qty, slot.was.free);
    //: **Where the crate is when the symbol leaves it, not where it was when
    //: the exchange began.** A gaining bar is cued 3.4s after the losing one --
    //: leg 1, the crossing, the landing, `CARRY.rest` -- and the island turns
    //: the whole time. Baked at cue time, the flight's first keyframe was
    //: **55px off the crate it was supposed to come out of**, measured on a
    //: 1400px page: far enough that the symbol rose out of open grass. The
    //: rope and the overhead bubbles are re-pinned every frame for exactly
    //: this reason; a WAAPI keyframe cannot be, so the symbol is *built* at
    //: the moment it flies and reads the yard then. The camera moves a few
    //: pixels across the flight itself, which is the drift a bubble already
    //: lives with.
    const gen = this.gen;
    if (delay > 1) {
      (this.pending ??= []).push(setTimeout(() => {
        if (gen === this.gen) this.fly_(name, good, qty, way, span, seat, slot);
      }, delay));
      return;
    }
    this.fly_(name, good, qty, way, span, seat, slot);
  }

  /** The symbol itself, built at the instant it leaves. */
  fly_(name, good, qty, way, span, seat, slot) {
    const yard = this.yards[`${name}:${good}`] ?? { x: seat.x, y: seat.y - 12 };
    const { x, y: at } = this.barAt(seat, slot);
    const mark = el("g", { class: `sheaf ${way}` });
    mark.append(el("circle", { class: "sheaf-puff", r: 13 }));
    mark.append(el("text", { y: 0, class: "sheaf-glyph" }, GLYPH[good] || "▪"));
    mark.append(el("text", { y: 16, class: "sheaf-qty" }, qty.toFixed(2)));
    this.flights.append(mark);

    const size = 0.6 + 0.5 * Math.min(1, qty / (this.top || 1));
    const A = way === "out" ? { x, y: at } : yard;
    const B = way === "out" ? yard : { x, y: at };
    //: **It is visible at the crate.** Both ends used to start at `opacity: 0`
    //: and reach 1 at three tenths of the way across, which -- with the lid
    //: open underneath it -- meant the one moment the symbol is supposed to be
    //: read as coming *out of the box* was the moment it could not be seen at
    //: all: it faded up a third of the way to the card, in open air. Reported
    //: by eye, as "the items do not come out of the boxes".
    //:
    //: So the fade is a beat at the crate end and nothing more: small in the
    //: mouth of the box, up to full size clear of it by a tenth of the flight.
    //: `out` is the same motion run the other way -- it shrinks back into the
    //: crate rather than snapping out at full size on top of it.
    const anim = mark.animate([
      { transform: `translate(${A.x}px, ${A.y}px) scale(${size * (way === "in" ? .34 : .8)})`,
        opacity: way === "in" ? 0 : 1 },
      //: Out of the mouth and standing above it, before it has gone anywhere.
      //: This is the frame that says where the goods came from.
      { transform: `translate(${A.x * .96 + B.x * .04}px, ` +
                   `${A.y * .96 + B.y * .04 - (way === "in" ? 15 : 6)}px) ` +
                   `scale(${size * (way === "in" ? .85 : .95)})`,
        opacity: 1, offset: .1 },
      { transform: `translate(${A.x * .7 + B.x * .3}px, ` +
                   `${(A.y + B.y) / 2 - 34}px) scale(${size})`, opacity: 1, offset: .42 },
      { transform: `translate(${B.x}px, ${B.y}px) ` +
                   `scale(${size * (way === "out" ? .38 : .8)})`,
        opacity: way === "out" ? 0.85 : 1 },
    ], { duration: span, easing: "cubic-bezier(.35,.65,.3,1)", fill: "backwards" });

    const done = () => {
      mark.remove();
      slot.holding = false;
      this.setBar(slot, slot.now.qty, slot.now.free);
      if (way === "in") {
        slot.cell.classList.add("grew");
        setTimeout(() => slot.cell.classList.remove("grew"), 700);
      }
    };
    // Scrubbed away mid-flight lands in the same place: the shelf is what the
    // board says, not what an animation was on its way to making it.
    anim.finished.then(done, done);
    // Losing is the one that empties as the symbol *leaves*, so the bar is
    // already down by the time the boxes are carried off the island.
    if (way === "out") setTimeout(done, still() ? 1 : span * 0.35);
  }

  /**
   * The bell: the light goes and the fire comes up.
   *
   * It does not touch the sun. The sun keeps its own clock -- it was already
   * almost down when the bell rang, and `sky()` carries it the rest of the way
   * while this plays. An animation that seized the disc made the day stop and
   * start again instead of running through.
   */
  bell(e) {
    this.banner_(`sundown — day ${e.episode} closed` +
                 (e.lapsed ? ` · ${e.lapsed} lapsed` : ""));
  }

  /** A new day. The sun rises out of the sea on its own, by the clock. */
  dawn(e) {
    this.banner_(`day ${e.episode}${e.of ? ` of ${e.of}` : ""}`);
  }


  banner_(text) {
    const node = this.banner.querySelector(".banner-text");
    node.textContent = text;
    const anim = this.banner.animate([
      { opacity: 0, transform: "translateY(-14px)" },
      { opacity: 1, transform: "translateY(0)", offset: 0.18 },
      { opacity: 1, transform: "translateY(0)", offset: 0.74 },
      { opacity: 0, transform: "translateY(-8px)" },
    ], { duration: still() ? 1 : 2600, easing: "cubic-bezier(.2,.9,.3,1)" });
    anim.finished.catch(() => {});
  }
}

export function bundleText(bundle) {
  return Object.entries(bundle)
    .map(([g, q]) => `${GLYPH[g] || ""}${trim(q)}`)
    .join(" ");
}

const trim = (q) => String(Math.round(q * 1000) / 1000);

//: How many characters of a name the card has room for beside its labour
//: wheel, at `.card-name`'s size. Measured against the drawing rather than
//: guessed: `CARD_W` less the padding and the wheel, over the width of a
//: monospace digit at 15px.
/**
 * The manager's two refusals that have a picture, and the shapes it says them in.
 *
 * Both drew a bare ✗: the page said that a refusal happened and never what
 * caused it, while for one of them the cause was sitting on screen the whole
 * time as a rope. Which refusals matter and what they say about how these
 * agents play is not this file's to decide -- it draws what the manager said.
 *
 * Matched against the manager's wording rather than re-derived, because the
 * manager's arithmetic is the authority on why it refused. A reason that does
 * not match either shape still gets its badge and its tooltip; nothing is
 * guessed at.
 */
export const SHORT = /you have ([\d.]+) (\w+) uncommitted, not the ([\d.]+)/;
export const NOT_YOURS = /^(p\d+) was not addressed to you/;

/** Which of a trader's own open offers is holding the good it came up short on. */
export function culprits(proposals, who, good) {
  return (proposals || []).filter(
    (p) => p.status === "open" && p.maker === who && (p.give?.[good] || 0) > 0);
}

/**
 * Which offers on the square a refusal is about.
 *
 * The manager names the proposal in three of its four approval refusals
 * (`no such proposal 'p3'`, `p3 is already settled`, `p3 was not addressed to
 * you`); the fourth -- coming up short on what an offer asks for -- names the
 * good instead, and the offer is then the open one addressed to this trader
 * that asks for it. A pid the board never carried matches nothing, which is
 * the right answer for `no such proposal`.
 */
export function refused(proposals, who, reason = "") {
  const open = (proposals || []).filter((p) => p.status === "open");
  const named = /\b(p\d+)\b/.exec(reason);
  if (named) return open.filter((p) => p.pid === named[1]);
  const asks = ASKS.exec(reason);
  if (asks) {
    return open.filter((p) => p.taker === who && (p.want?.[asks[2]] || 0) > 0);
  }
  return [];
}

//: The one approval refusal that names a good rather than a proposal.
export const ASKS = /you have ([\d.]+) (\w+) uncommitted, not the ([\d.]+) it asks for/;

/**
 * How high each arrived pill sits on the hut it is waiting over: by taker, in
 * the order the offers were made, oldest at the bottom of the pile.
 */
export function stacking(open) {
  const high = new Map(), at = new Map();
  for (const p of open || []) {
    const n = high.get(p.taker) || 0;
    high.set(p.taker, n + 1);
    at.set(p.pid, { i: n });
  }
  //: **How many are in this pile, on every member of it.** The pile has to fit
  //: between the hut and the top of the frame, so a pill cannot be placed
  //: knowing only its own place in the queue -- the fifth of five and the fifth
  //: of nine sit at different heights.
  for (const p of open || []) at.get(p.pid).of = high.get(p.taker);
  return at;
}

//: The pill's own height, and how far apart two of them stand in a pile: the
//: height plus a gap, so a stack of them reads as separate things.
/**
 * One step of a pill toward where it belongs, `ms` of animation later.
 *
 * Exponential, so it leaves quickly and settles rather than stopping dead, and
 * driven by elapsed time so a 120Hz screen does not settle it twice as fast as
 * a 60Hz one.
 *
 * **The clamp is the part that matters.** A settled pill is not being stepped
 * at all -- `ride()` has stopped -- so when its pile changes under it the gap
 * since the last step is however long it sat there, and an unclamped ease
 * covers the whole distance in one frame: a jump wearing an ease, which is
 * what this was measured doing before the clamp went in. Idle time is not
 * animation time.
 */
export function glideTo(was, target, ms, tau = GLIDE, cap = GLIDE_CAP) {
  const k = 1 - Math.exp(-Math.min(Math.max(0, ms), cap) / tau);
  return { x: was.x + (target.x - was.x) * k,
           y: was.y + (target.y - was.y) * k };
}

export const PILL_H = 32;
export const PILL_STEP = 38;

export const NAME_MAX = 14;

/** A name the card can hold. The full one goes in a `<title>`. */
export function shortName(name, max = NAME_MAX) {
  const text = String(name ?? "");
  if (text.length <= max) return text;
  // Keep the tail: a peer id or a branch name differs at the end, and three
  // cards all reading `ai-lab:claude/…` would name nobody.
  return `…${text.slice(-(max - 1))}`;
}

