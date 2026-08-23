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

import { utilityOf } from "./utility.js";

const NS = "http://www.w3.org/2000/svg";

export const GLYPH = {
  bread: "🍞", cloth: "🧵", iron: "⛏", salt: "🧂",
  fish: "🐟", grain: "🌾", timber: "🪵",
};

const SLOT = ["--good-1", "--good-2", "--good-3", "--good-4",
              "--good-5", "--good-6", "--good-7"];

const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

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

const W = 1000, H = 560;
const CX = W / 2, CY = H / 2 + 10;

/** Where each hut stands. Two traders face each other; more ring the island. */
function seats(n) {
  if (n === 2) return [{ x: 210, y: CY - 14 }, { x: W - 210, y: CY - 14 }];
  const r = n <= 4 ? 250 : 275;
  return Array.from({ length: n }, (_, i) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    return { x: CX + r * Math.cos(a) * 1.35, y: CY + r * Math.sin(a) * 0.78 };
  });
}

const CARD_W = 168, BAR_W = 22, BAR_MAX = 40;
//: The shelf's floor, in card coordinates. Bars stand on it, labels hang below.
const BASE = 92;
//: Taller only where there is a utility to put in it. A live card must not
//: carry an empty score row: a blank number reads as a number that failed,
//: rather than as one nobody on this island is allowed to know.
const CARD_H = 116, CARD_H_SCORED = 138;

export class Scene {
  constructor(root, timeline, reveal = null) {
    this.root = root;
    this.timeline = timeline;
    this.traders = timeline.traders;
    this.goods = timeline.goods;
    // Present only in a replay. Everything utility on this island hangs off it,
    // and there is deliberately no path that fills it in live.
    this.reveal = reveal;
    this.cardH = reveal ? CARD_H_SCORED : CARD_H;
    this.utilityTop = this.utilityScale();
    this.seats = {};
    this.bars = {};
    this.labels = {};
    this.build();
  }

  build() {
    const svg = this.root;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.replaceChildren();

    const defs = el("defs");
    defs.append(el("radialGradient", { id: "sea", cx: "50%", cy: "45%", r: "75%" }, [
      el("stop", { offset: "0%", "stop-color": "var(--sea-near)" }),
      el("stop", { offset: "100%", "stop-color": "var(--sea-far)" }),
    ]));
    defs.append(el("radialGradient", { id: "glow", cx: "50%", cy: "50%", r: "50%" }, [
      el("stop", { offset: "0%", "stop-color": "var(--fire)", "stop-opacity": "0.55" }),
      el("stop", { offset: "100%", "stop-color": "var(--fire)", "stop-opacity": "0" }),
    ]));
    svg.append(defs);

    svg.append(el("rect", { x: 0, y: 0, width: W, height: H, fill: "url(#sea)" }));

    // Water, moving slowly enough to be scenery rather than information.
    const water = el("g", { class: "water", "aria-hidden": "true" });
    for (let i = 0; i < 7; i++) {
      const y = 70 + i * 78;
      water.append(el("path", {
        d: `M -60 ${y} q 60 -12 120 0 t 120 0 t 120 0 t 120 0 t 120 0 t 120 0 t 120 0 t 120 0 t 120 0`,
        class: "wave", style: `animation-delay: ${-i * 1.7}s`,
      }));
    }
    svg.append(water);

    // The island itself. One hand-written blob: a circle reads as a logo.
    // Sized so the trader cards sit on sand with a little shore to spare: the
    // island is the frame for the information, not a landscape in its own right.
    svg.append(el("path", {
      class: "land",
      d: `M ${CX - 392} ${CY + 10}
          C ${CX - 392} ${CY - 96} ${CX - 250} ${CY - 142} ${CX - 118} ${CY - 128}
          C ${CX - 38} ${CY - 120} ${CX + 40} ${CY - 142} ${CX + 142} ${CY - 132}
          C ${CX + 282} ${CY - 120} ${CX + 392} ${CY - 70} ${CX + 392} ${CY + 12}
          C ${CX + 392} ${CY + 102} ${CX + 250} ${CY + 158} ${CX} ${CY + 158}
          C ${CX - 250} ${CY + 158} ${CX - 392} ${CY + 100} ${CX - 392} ${CY + 10} Z`,
    }));
    svg.append(el("ellipse", {
      class: "square", cx: CX, cy: CY + 26, rx: 118, ry: 52,
    }));

    // The fire in the middle of the square: the only thing on screen that is
    // pure decoration, and the thing that makes an idle board look inhabited.
    svg.append(el("circle", { cx: CX, cy: CY + 18, r: 90, fill: "url(#glow)", class: "firelight" }));
    const fire = el("g", { class: "fire", transform: `translate(${CX} ${CY + 26})` });
    fire.append(el("path", { class: "log", d: "M -22 6 L 22 -2" }));
    fire.append(el("path", { class: "log", d: "M -22 -2 L 22 6" }));
    fire.append(el("path", { class: "flame", d: "M 0 -30 c 12 12 16 22 0 30 c -16 -8 -12 -18 0 -30 z" }));
    svg.append(fire);

    // A place rather than a blank: a worn path between the huts, and planting
    // where nothing informative goes.
    seats(this.traders.length).forEach((seat, i) => { this.seats[this.traders[i]] = seat; });
    const scenery = el("g", { class: "scenery", "aria-hidden": "true" });
    scenery.append(el("path", {
      class: "track", d: `M 150 ${CY + 14} Q ${CX} ${CY + 104} ${W - 150} ${CY + 14}`,
    }));
    const clear = (x, y) => Object.values(this.seats)
      .every((s) => Math.hypot(s.x - x, s.y - y) > 170);
    for (const [x, y, k] of [[CX - 148, CY + 132, 1], [CX + 162, CY + 134, .92],
                             [CX - 26, CY - 104, .8], [CX + 134, CY - 98, .7],
                             [CX - 268, CY + 108, .8], [CX + 272, CY + 104, .86]]
                             .filter(([x, y]) => clear(x, y))) {
      const palm = el("g", { class: "palm", transform: `translate(${x} ${y}) scale(${k})` });
      palm.append(el("path", { class: "trunk", d: "M 0 0 q -5 -18 2 -34" }));
      for (const a of [-54, -18, 18, 54]) {
        palm.append(el("path", {
          class: "frond", transform: `rotate(${a} 2 -34)`,
          d: "M 2 -34 q 17 -9 27 -2 q -15 7 -27 2 z",
        }));
      }
      scenery.append(palm);
    }
    svg.append(scenery);

    this.ropes = el("g", { class: "ropes" });
    svg.append(this.ropes);

    const huts = el("g", { class: "huts" });
    this.traders.forEach((name) => huts.append(this.hut(name, this.seats[name])));
    svg.append(huts);

    this.flights = el("g", { class: "flights" });
    svg.append(this.flights);

    this.night = el("rect", {
      x: 0, y: 0, width: W, height: H, class: "night", opacity: 0,
    });
    svg.append(this.night);

    this.banner = el("g", { class: "banner", opacity: 0 });
    this.banner.append(el("text", { x: CX, y: 84, class: "banner-text" }, ""));
    svg.append(this.banner);
  }

  hut(name, seat) {
    const g = el("g", { class: "hut", transform: `translate(${seat.x} ${seat.y})`,
                        "data-trader": name });
    // The dwelling, then the card. The hut says whose this is; the card is the
    // only part carrying information, and it gets a dark ground of its own --
    // a number written straight onto sand cannot be read at any size.
    g.append(el("path", { class: "roof", d: "M -46 -34 L 0 -76 L 46 -34 Z" }));
    g.append(el("rect", { class: "wall", x: -36, y: -34, width: 72, height: 44, rx: 3 }));
    g.append(el("rect", { class: "door", x: -10, y: -14, width: 20, height: 24, rx: 2 }));

    const card = el("g", { class: "card" });
    card.append(el("rect", { class: "card-bg", x: -CARD_W / 2, y: 14,
                             width: CARD_W, height: this.cardH, rx: 11 }));
    card.append(el("text", { x: -CARD_W / 2 + 12, y: 36, class: "card-name" }, name));

    // Labour: filled by what this trader spent this episode, and empty until a
    // production receipt says otherwise -- nobody has told this page anything
    // about their labour before then.
    const wheel = el("g", { class: "wheel", transform: `translate(${CARD_W / 2 - 22} 30)` });
    wheel.append(el("circle", { r: 11, class: "wheel-track" }));
    wheel.append(el("circle", { r: 11, class: "wheel-fill",
                                "stroke-dasharray": "0 70", transform: "rotate(-90)" }));
    wheel.append(el("text", { y: 3.5, class: "wheel-text" }, "—"));
    card.append(wheel);
    card.append(el("text", { x: CARD_W / 2 - 40, y: 34, class: "card-sub",
                             "text-anchor": "end" }, "labour"));
    this.labels[name] = { wheel: wheel.querySelector(".wheel-fill"),
                          wheelText: wheel.querySelector(".wheel-text"),
                          card: card.querySelector(".card-bg") };

    // The shelf: goods in the manager's own order, always, so the position is
    // learned once and no legend has to be consulted again.
    this.bars[name] = {};
    const inner = CARD_W - 24;
    const step = inner / this.goods.length;
    this.goods.forEach((good, i) => {
      const cx = -CARD_W / 2 + 12 + i * step + step / 2;
      const x = cx - BAR_W / 2;
      const cell = el("g", { class: "cell", "data-good": good,
                             style: `--c: var(${SLOT[i % SLOT.length]})` });
      cell.append(el("rect", { class: "bar-track", x, y: BASE - BAR_MAX,
                               width: BAR_W, height: BAR_MAX, rx: 3 }));
      const bar = el("rect", { class: "bar", x, y: BASE - BAR_MAX,
                               width: BAR_W, height: BAR_MAX, rx: 3 });
      // Promised, not gone: the manager will not settle a second offer over the
      // same goods, so a shelf that hides commitment shows stock that cannot
      // actually be offered.
      const held = el("rect", { class: "bar-held", x, y: BASE - BAR_MAX,
                                width: BAR_W, height: BAR_MAX, rx: 3 });
      cell.append(bar, held);
      cell.append(el("text", { x: cx, y: BASE + 16, class: "glyph" }, GLYPH[good] || "▪"));
      cell.append(el("text", { x: cx, y: BASE + 29, class: "qty" }, ""));
      card.append(cell);
      this.bars[name][good] = { bar, held, qty: cell.querySelector(".qty"), x: cx };
    });
    card.append(el("line", { class: "plank", x1: -CARD_W / 2 + 8, y1: BASE + 1.5,
                             x2: CARD_W / 2 - 8, y2: BASE + 1.5 }));

    if (this.reveal) {
      // What this shelf is worth to the trader who owns it. Computed here from
      // the revealed tastes and the receipts -- the manager's own scored
      // trajectory is in the rail, and `audit()` holds the two together.
      const row = el("g", { class: "score", transform: `translate(0 ${BASE + 44})` });
      const w = CARD_W - 24;
      row.append(el("text", { x: -CARD_W / 2 + 12, y: 0, class: "card-sub" }, "utility"));
      row.append(el("text", { x: CARD_W / 2 - 12, y: 0, class: "score-value",
                              "text-anchor": "end" }, "—"));
      row.append(el("rect", { class: "score-track", x: -w / 2, y: 5, width: w,
                              height: 6, rx: 3 }));
      row.append(el("rect", { class: "score-fill", x: -w / 2, y: 5, width: w,
                              height: 6, rx: 3 }));
      // Where autarky would have put them: the line worth beating, and the one
      // a round can finish below.
      const auto = this.reveal.autarky_utility?.[name];
      if (auto !== undefined && this.utilityTop > 0) {
        row.append(el("rect", {
          class: "score-floor", x: -w / 2 + w * Math.min(1, auto / this.utilityTop) - 1,
          y: 2, width: 2, height: 12,
        }, []));
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

  draw(state, timeline) {
    // Cached: the ceiling is a property of the round, and on a live board it
    // only ever rises, so recomputing it per paint would be the frame-local
    // scale this deliberately avoids.
    if (this.top === undefined || timeline.frames.length !== this.scaledAt) {
      this.top = this.scale(timeline);
      this.scaledAt = timeline.frames.length;
    }
    const top = this.top;
    for (const name of this.traders) {
      const promised = (good) => timeline.committed(state, name, good);
      for (const good of this.goods) {
        const qty = state.stocks[name]?.[good] || 0;
        const b = this.bars[name][good];
        const free = Math.max(0, qty - promised(good));
        b.bar.style.transform = `scaleY(${Math.min(1, qty / top)})`;
        b.held.style.transform = `scaleY(${Math.min(1, free / top)})`;
        // Two decimals is what a reader can hold. The receipts carry four and
        // the page must not imply more precision than they do.
        b.qty.textContent = qty > 1e-9 ? qty.toFixed(2) : "";
        b.qty.classList.toggle("none", qty <= 1e-9);
      }
      const spent = state.labour[name];
      const wheel = this.labels[name];
      const arc = 2 * Math.PI * 11;
      const used = spent === null ? 0 : Math.max(0, Math.min(1, 1 - spent));
      wheel.wheel.setAttribute("stroke-dasharray", `${(used * arc).toFixed(2)} ${arc}`);
      wheel.wheelText.textContent = spent === null ? "—" : `${Math.round(used * 100)}`;
      if (this.reveal) {
        // After the bell the shelf is empty and a live reading would say zero,
        // which is true and useless: what the episode was worth is what it
        // closed holding. Hold that until the next episode opens.
        const closed = state.phase === "closed" || state.phase === "over";
        const last = state.episodes_closed[state.episodes_closed.length - 1];
        const held = closed && last ? last.holdings[name] : state.stocks[name];
        const u = utilityOf(this.reveal, name, held);
        const label = this.labels[name];
        const w = CARD_W - 24;
        label.score.setAttribute("width",
          (w * Math.max(0, Math.min(1, (u || 0) / this.utilityTop))).toFixed(2));
        label.scoreText.textContent = u === null ? "—" : u.toFixed(3);
        label.scoreText.classList.toggle("zero", u !== null && u <= 1e-12);
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
    this.ropes.replaceChildren(...open.map((p) => {
      const pair = [p.maker, p.taker].sort().join("~");
      const i = rank.get(pair) || 0;
      rank.set(pair, i + 1);
      return this.rope(p, i);
    }));
    this.root.classList.toggle("closed", state.phase === "closed" || state.phase === "over");
  }

  rope(p, fan = 0) {
    const a = this.seats[p.maker], b = this.seats[p.taker];
    if (!a || !b) return el("g");
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2 - 78 - fan * 56;
    const g = el("g", { class: "rope", "data-pid": p.pid });
    g.append(el("path", { class: "rope-line", d: `M ${a.x} ${a.y - 40} Q ${mx} ${my} ${b.x} ${b.y - 40}` }));
    const chip = el("g", { class: "rope-chip", transform: `translate(${mx} ${my + 18})` });
    const text = `${bundleText(p.give)} → ${bundleText(p.want)}`;
    const width = Math.max(96, text.length * 8.2);
    chip.append(el("rect", { x: -width / 2, y: -15, width, height: 30, rx: 15, class: "chip-bg" }));
    chip.append(el("text", { x: 0, y: 5, class: "chip-text" }, text));
    chip.append(el("text", { x: 0, y: 26, class: "chip-pid" }, `${p.pid} · ${p.maker}→${p.taker}`));
    g.append(chip);
    return g;
  }

  // --- what an event looks like ---------------------------------------------

  play(event) {
    switch (event.kind) {
      case "settled": return this.flight(event);
      case "produced": return this.pop(event.trader, "produced", "good");
      case "refused": return this.pop(event.trader, `✗ ${short(event.reason)}`, "bad");
      case "bell": return this.bell(event);
      case "open": return this.banner_(`episode ${event.episode}${event.of ? ` of ${event.of}` : ""}`);
      case "over": return this.banner_("the round is over");
      case "fault": return this.banner_("harness fault");
      default: return undefined;
    }
  }

  /** Goods crossing the square. The only moment a trade is visible as motion. */
  flight(e) {
    const a = this.seats[e.maker], b = this.seats[e.taker];
    if (!a || !b) return;
    const send = (from, to, bundle, cls) => {
      for (const [good, qty] of Object.entries(bundle)) {
        const parcel = el("g", { class: `parcel ${cls}` });
        parcel.append(el("circle", { r: 16, class: "parcel-bg",
                                     style: `--c: var(${SLOT[this.goods.indexOf(good) % SLOT.length]})` }));
        parcel.append(el("text", { y: 5, class: "parcel-glyph" }, GLYPH[good] || "▪"));
        parcel.append(el("text", { y: 30, class: "parcel-qty" }, qty.toFixed(2)));
        this.flights.append(parcel);
        const lift = -70;
        const frames = [
          { transform: `translate(${from.x}px, ${from.y - 40}px)`, opacity: 0 },
          { transform: `translate(${(from.x + to.x) / 2}px, ${(from.y + to.y) / 2 + lift}px)`, opacity: 1 },
          { transform: `translate(${to.x}px, ${to.y - 40}px)`, opacity: 0 },
        ];
        const anim = parcel.animate(frames, {
          duration: still() ? 1 : 900, easing: "cubic-bezier(.4,0,.2,1)",
        });
        anim.finished.then(() => parcel.remove(), () => parcel.remove());
      }
    };
    send(a, b, e.give, "out");
    send(b, a, e.want, "back");
    const rope = this.ropes.querySelector(`.rope[data-pid="${e.pid}"]`);
    if (rope) rope.classList.add("settling");
  }

  pop(trader, text, kind) {
    const seat = this.seats[trader];
    if (!seat) return;
    const g = el("g", { class: `pop ${kind}` });
    const width = Math.max(84, String(text).length * 7.4);
    g.append(el("rect", { x: -width / 2, y: -14, width, height: 26, rx: 13, class: "pop-bg" }));
    g.append(el("text", { y: 4, class: "pop-text" }, String(text)));
    this.flights.append(g);
    const anim = g.animate([
      { transform: `translate(${seat.x}px, ${seat.y - 100}px)`, opacity: 0 },
      { transform: `translate(${seat.x}px, ${seat.y - 128}px)`, opacity: 1, offset: 0.25 },
      { transform: `translate(${seat.x}px, ${seat.y - 150}px)`, opacity: 0 },
    ], { duration: still() ? 1 : 1800, easing: "ease-out" });
    anim.finished.then(() => g.remove(), () => g.remove());
  }

  bell(e) {
    this.banner_(`bell — episode ${e.episode} closed` +
                 (e.lapsed ? ` · ${e.lapsed} lapsed` : ""));
    const anim = this.night.animate(
      [{ opacity: 0 }, { opacity: 0.62 }, { opacity: 0 }],
      { duration: still() ? 1 : 1600, easing: "ease-in-out" });
    anim.finished.catch(() => {});
  }

  banner_(text) {
    const node = this.banner.querySelector(".banner-text");
    node.textContent = text;
    const anim = this.banner.animate(
      [{ opacity: 0 }, { opacity: 1, offset: 0.2 }, { opacity: 1, offset: 0.75 }, { opacity: 0 }],
      { duration: still() ? 1 : 2200 });
    anim.finished.catch(() => {});
  }
}

export function bundleText(bundle) {
  return Object.entries(bundle)
    .map(([g, q]) => `${GLYPH[g] || ""}${trim(q)}`)
    .join(" ");
}

const trim = (q) => String(Math.round(q * 1000) / 1000);

const short = (s) => (s.length > 34 ? s.slice(0, 32) + "…" : s);
