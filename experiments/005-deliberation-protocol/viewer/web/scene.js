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

const NS = "http://www.w3.org/2000/svg";

export const GLYPH = {
  bread: "🍞", cloth: "🧵", iron: "⛏", salt: "🧂",
  fish: "🐟", grain: "🌾", timber: "🪵",
};

const SLOT = ["--good-1", "--good-2", "--good-3", "--good-4",
              "--good-5", "--good-6", "--good-7"];

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
export const DWELL = {
  settled: 2100,   // parcels cross, stagger, and land
  produced: 2600,  // the hut works, then a sheaf per good lands on the shelf
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
export function layout(n, portrait = false) {
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
    return {
      w, h: bottom + 120, cx: w / 2, ly, ry: (bottom - sky) / 2, rx: w / 2 - 34, seats,
      // Beside the column rather than in it: a fire between two stacked huts
      // would sit underneath a card.
      fire: { x: w / 2, y: bottom + 46 },
    };
  }
  if (n <= 2) {
    const g = { w: BASE_W, h: BASE_H, cx: BASE_W / 2, ly: 298, rx: 452, ry: 188 };
    const seats = n === 2
      ? [{ x: 250, y: 238 }, { x: BASE_W - 250, y: 238 }]
      : [{ x: g.cx, y: 238 }];
    return { ...g, seats, fire: { x: g.cx, y: g.ly + 52 } };
  }
  const w = 268 * n + 300;
  const g = { w, h: 620, cx: w / 2, ly: 320, rx: w / 2 - 44, ry: 200 };
  const step = (w - 420) / (n - 1);
  return {
    ...g,
    seats: Array.from({ length: n }, (_, i) => ({ x: 210 + i * step, y: 232 })),
    // In front of the huts rather than between them: with a line of traders
    // there is no between.
    fire: { x: g.cx, y: g.ly + 150 },
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

const CARD_W = 196, BAR_W = 26, BAR_MAX = 52;
//: The shelf's floor, in card coordinates. Bars stand on it, labels hang below.
const BASE = 104;
//: Taller only where there is a utility to put in it. A live card must not
//: carry an empty score row: a blank number reads as a number that failed,
//: rather than as one nobody on this island is allowed to know.
const CARD_H = 140, CARD_H_SCORED = 186;
//: The card hangs below the seat, clear of the hut rather than pasted onto it.
const CARD_TOP = 22;

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
  constructor(root, timeline, reveal = null, portrait = false) {
    this.root = root;
    this.timeline = timeline;
    this.traders = timeline.traders;
    this.goods = timeline.goods;
    // Present only in a replay. Everything utility on this island hangs off it,
    // and there is deliberately no path that fills it in live.
    this.reveal = reveal;
    this.cardH = reveal ? CARD_H_SCORED : CARD_H;
    this.portrait = portrait;
    this.geo = layout(this.traders.length, portrait);
    this.utilityTop = this.utilityScale();
    this.seats = {};
    this.bars = {};
    this.labels = {};
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
  reflow(portrait) {
    if (portrait === this.portrait) return false;
    this.portrait = portrait;
    this.geo = layout(this.traders.length, portrait);
    // Rebuilt from the new geometry rather than carried over: every one of
    // these is keyed to nodes `build()` is about to throw away.
    this.seats = {};
    this.bars = {};
    this.labels = {};
    this.top = undefined;
    this.shown = new Map();
    this.build();
    return true;
  }

  build() {
    const svg = this.root;
    const g = this.geo;
    svg.setAttribute("viewBox", `0 0 ${g.w} ${g.h}`);
    svg.replaceChildren();
    svg.append(this.defs());

    svg.append(el("rect", { x: 0, y: 0, width: g.w, height: g.h, fill: "url(#sea)" }));
    // Behind the water, so it sets *into* the sea rather than on top of it.
    svg.append(this.sun());
    svg.append(this.water());
    svg.append(this.land());

    g.seats.forEach((seat, i) => { this.seats[this.traders[i]] = seat; });
    svg.append(this.square());
    svg.append(this.scenery());

    this.ropes = el("g", { class: "ropes" });
    svg.append(this.ropes);

    const huts = el("g", { class: "huts" });
    this.traders.forEach((name) => huts.append(this.hut(name, this.seats[name])));
    svg.append(huts);

    this.flights = el("g", { class: "flights" });
    svg.append(this.flights);

    // Dusk rather than a black rectangle: the bell is the most dramatic thing
    // that happens in an episode and it was being drawn as a power cut.
    // The colour the light turns as the sun goes, then the dark it leaves.
    // Both opacities are CSS, keyed off `.closed`: a state, not a pulse, so
    // scrubbing to a closed frame lands in the dark with no event played.
    svg.append(el("rect", { x: 0, y: 0, width: g.w, height: g.h, class: "sky-burn" }));
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

  /** Where the sun stands, this far through the episode. */
  sunPoint(p) {
    return sunAt(this.geo, p);
  }

  /**
   * How far through its episode this frame is, by the board's own clock.
   *
   * `null` when the board has not said -- before the first episode, after the
   * round, or on a board whose schedule line this page could not read. The
   * caller leaves the sun where it is rather than putting it at dawn, because
   * "we do not know the time" is not the same as "it is morning".
   */
  dayProgress(state) {
    if (!state?.bell_at || !state.seconds || !state.at) return null;
    const bell = Date.parse(state.bell_at);
    const span = state.seconds * 1000;
    const now = Date.parse(state.at);
    if (!Number.isFinite(bell) || !Number.isFinite(now) || span <= 0) return null;
    return Math.max(0, Math.min(1, (now - (bell - span)) / span));
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
    const from = this.sunP ?? 0;
    let to;
    if (closed) {
      // The bell does not move the sun. It was already almost down when the
      // bell rang and it goes on down; the bell's own animation is the light
      // going and the fire coming up, and that runs alongside.
      to = SET;
    } else {
      const now = this.dayProgress(state);
      if (now === null) return;   // no clock on this board: leave it where it is
      to = until === null ? now
        : Math.max(now, this.dayProgress({ ...state, at: until }) ?? now);
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
    const first = seatList[0], last = seatList[seatList.length - 1];
    g.append(el("path", {
      class: "track",
      d: `M ${first.x} ${geo.fire.y - 34} Q ${geo.cx} ${geo.fire.y + 74} ` +
         `${last.x} ${geo.fire.y - 34}`,
    }));
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

    const card = el("g", { class: "card" });
    card.append(el("rect", { class: "card-shadow", x: -CARD_W / 2 + 3, y: CARD_TOP + 5,
                             width: CARD_W, height: this.cardH, rx: 13 }));
    card.append(el("rect", { class: "card-bg", x: -CARD_W / 2, y: CARD_TOP,
                             width: CARD_W, height: this.cardH, rx: 13 }));
    // Clamped, with the whole of it on hover. A seat is `T1` on a saved board,
    // but live an author is a peer id and an entrant picks its own name -- so
    // this has to survive `ai-lab:claude/island-economy-game-wrapper-pcm5s6`,
    // which is a real name that really appeared and really ran off the island.
    const label = el("text", { x: -CARD_W / 2 + 13, y: CARD_TOP + 25,
                               class: "card-name" }, shortName(name));
    label.append(el("title", {}, name));
    card.append(label);

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

    if (this.reveal) {
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
      const wheel = this.labels[name];
      const arc = 2 * Math.PI * 12;
      const used = spent === null ? 0 : Math.max(0, Math.min(1, 1 - spent));
      wheel.wheel.setAttribute("stroke-dasharray", `${(used * arc).toFixed(2)} ${arc}`);
      wheel.wheelText.textContent = spent === null ? "—" : `${Math.round(used * 100)}`;
      if (this.reveal) {
        // After the bell the shelf is empty and a live reading would say zero,
        // which is true and useless: what the episode was worth is what it
        // closed holding. Hold that until the next episode opens.
        const u = utilityOf(this.reveal, name, shelf);
        const label = this.labels[name];
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
      if (p.status !== "lapsed" || !was.has(p.pid)) continue;
      this.fray(p, was.get(p.pid));
    }
    this.shown = placed;
    // Kept so a refusal played straight after this paint can find what was
    // open at the moment it happened.
    this.state = state;
    this.root.classList.toggle("closed", closed);
  }

  /** One rope, going slack and fading, after the bell took the offer with it. */
  fray(p, fan) {
    const node = this.rope(p, fan);
    node.classList.add("lapsing");
    this.flights.append(node);
    const anim = node.animate(
      [{ opacity: 1 }, { opacity: 0.55, offset: .3 }, { opacity: 0 }],
      { duration: still() ? 1 : 1100, easing: "ease-in" });
    anim.finished.then(() => node.remove(), () => node.remove());
  }

  rope(p, fan = 0) {
    const a = this.seats[p.maker], b = this.seats[p.taker];
    if (!a || !b) return el("g");
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2 - 118 - fan * 44;
    const g = el("g", { class: "rope", "data-pid": p.pid });
    g.append(el("path", { class: "rope-shadow",
                          d: `M ${a.x} ${a.y - 84} Q ${mx} ${my} ${b.x} ${b.y - 84}` }));
    g.append(el("path", { class: "rope-line",
                          d: `M ${a.x} ${a.y - 84} Q ${mx} ${my} ${b.x} ${b.y - 84}` }));
    const chip = el("g", { class: "rope-chip", transform: `translate(${mx} ${my + 20})` });
    const text = `${bundleText(p.give)} → ${bundleText(p.want)}`;
    const width = Math.max(104, text.length * 8.4);
    chip.append(el("rect", { x: -width / 2, y: -16, width, height: 32, rx: 16,
                             class: "chip-bg" }));
    chip.append(el("text", { x: 0, y: 5, class: "chip-text" }, text));
    chip.append(el("text", { x: 0, y: 28, class: "chip-pid" }, `${p.pid} · ${p.maker}→${p.taker}`));
    g.append(chip);
    return g;
  }

  // --- what an event looks like ---------------------------------------------

  play(event) {
    switch (event.kind) {
      case "settled": return this.flight(event);
      case "produced": return this.produce(event);
      // A symbol, and the reason kept as the badge's title rather than printed
      // over the sand. What the manager wrote is in the ticker; the island says
      // *that* it refused, and whose.
      case "refused":
        this.blame(event.trader, event.reason);
        return this.mark(event.trader, "bad", event.reason);
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
   * Somebody did something, said as a shape.
   *
   * The island used to print the manager's refusal text across the sand, which
   * is unreadable at that size and is already in the ticker underneath. And it
   * drew nothing at all when a trader merely spoke -- so a board where two
   * agents talked and settled nothing looked identical to one where nobody
   * turned up.
   */
  mark(who, kind, title = "") {
    const seat = this.seats[who];
    if (!seat) return;
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
    this.flights.append(g);
    const anim = g.animate([
      { transform: `translate(${seat.x}px, ${seat.y - 100}px) scale(.6)`, opacity: 0 },
      { transform: `translate(${seat.x}px, ${seat.y - 126}px) scale(1)`, opacity: 1,
        offset: 0.18 },
      { transform: `translate(${seat.x}px, ${seat.y - 134}px) scale(1)`, opacity: 1,
        offset: 0.72 },
      { transform: `translate(${seat.x}px, ${seat.y - 162}px) scale(.9)`, opacity: 0 },
    ], { duration: still() ? 1 : DWELL[kind === "bad" ? "refused" : "said"],
         easing: "ease-out" });
    anim.finished.then(() => g.remove(), () => g.remove());
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
    const span = still() ? 1 : DWELL.produced - 300;
    const each = still() ? 0 : Math.min(520, (span - 900) / Math.max(1, made.length));

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

    made.forEach(([good, qty], i) => {
      const slot = this.bars[e.trader]?.[good];
      if (!slot) return;
      // Hold this slot at what it held before, and let the goods fill it. The
      // arriving sheaf is what makes the bar grow -- before, the two were
      // unrelated and the bar won the race by a second.
      slot.holding = true;
      this.setBar(slot, slot.was.qty, slot.was.free);
      const delay = still() ? 0 : i * each;
      const flight = still() ? 1 : Math.max(700, span - i * each - 120);

      const sheaf = el("g", { class: "sheaf" });
      sheaf.append(el("circle", { class: "sheaf-puff", r: 15 }));
      sheaf.append(el("text", { y: 0, class: "sheaf-glyph" }, GLYPH[good] || "▪"));
      sheaf.append(el("text", { y: 16, class: "sheaf-qty" }, qty.toFixed(2)));
      this.flights.append(sheaf);

      // Sized by how much of it there is, on the shelf's own scale -- so a big
      // haul is a big thing crossing the card. Not by labour share: that is
      // `qty / capacity`, and a capacity is private, so live the page has no
      // way to know it and must not pretend otherwise.
      const size = 0.62 + 0.55 * Math.min(1, qty / (this.top || 1));
      const x = seat.x + slot.x, to = seat.y + CARD_TOP + BASE - 10;
      const anim = sheaf.animate([
        { transform: `translate(${seat.x}px, ${seat.y - 12}px) scale(.35)`, opacity: 0 },
        { transform: `translate(${seat.x}px, ${seat.y - 30}px) scale(${size})`,
          opacity: 1, offset: .22 },
        { transform: `translate(${(seat.x + x) / 2}px, ${seat.y - 6}px) scale(${size})`,
          opacity: 1, offset: .55 },
        { transform: `translate(${x}px, ${to}px) scale(${size * .8})`, opacity: 1 },
      ], { duration: flight, delay, easing: "cubic-bezier(.3,.7,.35,1)",
           fill: "backwards" });

      anim.finished.then(() => {
        // It landed. *Now* the shelf has it.
        sheaf.remove();
        slot.holding = false;
        this.setBar(slot, slot.now.qty, slot.now.free);
        slot.cell.classList.add("grew");
        setTimeout(() => slot.cell.classList.remove("grew"), 700);
      }, () => {
        // Scrubbed away mid-flight: put the shelf where the state says it is
        // rather than leaving it held at a value nothing is coming to fill.
        sheaf.remove();
        slot.holding = false;
        this.setBar(slot, slot.now.qty, slot.now.free);
      });
    });

    setTimeout(() => hut?.classList.remove("working"), still() ? 1 : span);
  }

  /** Goods crossing the square. The only moment a trade is visible as motion. */
  flight(e) {
    const a = this.seats[e.maker], b = this.seats[e.taker];
    if (!a || !b) return;
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

export const NAME_MAX = 14;

/** A name the card can hold. The full one goes in a `<title>`. */
export function shortName(name, max = NAME_MAX) {
  const text = String(name ?? "");
  if (text.length <= max) return text;
  // Keep the tail: a peer id or a branch name differs at the end, and three
  // cards all reading `ai-lab:claude/…` would name nobody.
  return `…${text.slice(-(max - 1))}`;
}

