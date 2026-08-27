// A colour per seat, for any number of seats.
//
// **Six of them were named, and the seventh trader wore the first one's
// colour.** `SEAT_COLOURS[i % 6]` is what both the island and the SVG layer
// did, and a table is not capped at six anywhere -- `dealer.draw` takes an
// agent count and the lobby seats whoever turns up. Two huts in one colour is
// worse than no colour at all: a colour that repeats is not a quiet failure,
// it is a wrong answer to "whose is that?".
//
// So a seat's colour is a function of **which seat and how many there are**.
// Up to six it is the hand-picked list below, unchanged -- those are on the
// island today, they are what `tokens.css` names, and they have been looked at.
// Past six the whole ring is generated: `n` hues evenly spaced in OKLCH around
// the band the named six sit in, stepping lightness as they go, so every seat
// is as far from every other as a table of that size allows.
//
// **The ring is a property of the round, not of the trader.** With seven at the
// table nobody wears one of the six; they wear one of seven. A trader's colour
// is fixed for as long as the table is, which is as long as the question
// "whose is that?" is being asked, and a round is where the seats are fixed.
//
// Nothing here is a promise that eleven seats are eleven tellable-apart
// colours. They cannot be: the wheel is finite, and the goods are on it too.
// This is the same bargain the goods make -- position and a glyph identify a
// good, and colour is what makes it findable -- and it is why an offer's pill
// carries `maker→taker` in text beside the colour. What the ring does promise,
// and `test_palette.py` measures out to sixteen seats, is that no two seats are
// the *same* colour and each is legible on the surface it is drawn on.

//: The named six. Hand-picked, on the island since it was modelled, and the
//: same list as `--seat-1..6` in `tokens.css` -- which is where the palette's
//: gates are run, so a colour that exists only here has passed nothing.
//: `test_palette.py` compares the two.
export const NAMED = ["#e8a13d", "#6fc2a0", "#c98bd8",
                      "#d9694f", "#86a8e0", "#d3c463"];

const clamp01 = (v) => Math.max(0, Math.min(1, v));
const toLinear = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const toSrgb = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);

/**
 * sRGB hex to OKLab. Ottosson's matrices, applied in linear light.
 *
 * OKLab rather than HSL because the ring's lightness is a quantity it sets
 * deliberately, and HSL's L is not a lightness anybody sees: a ring at constant
 * HSL lightness has a yellow that glares and a blue that vanishes, so neither
 * holding it nor stepping it would mean anything.
 */
function oklab(hex) {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => toLinear(parseInt(h.slice(i, i + 2), 16) / 255));
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
          1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
          0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
}

/** OKLab back to sRGB, and whether it landed inside the gamut. */
function srgb([L, A, B]) {
  const l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3;
  const m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3;
  const s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3;
  const rgb = [+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
               -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
               -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s];
  return { rgb, inside: rgb.every((c) => c >= -0.001 && c <= 1.001) };
}

const hex = (rgb) => "#" + rgb.map(
  (c) => Math.round(clamp01(toSrgb(clamp01(c))) * 255).toString(16).padStart(2, "0")).join("");

/**
 * One point of the ring: a hue, at the band the named six sit in.
 *
 * **Chroma is walked down until the colour is one sRGB can print**, rather
 * than each channel being clipped where it overflows. Clipping a channel moves
 * the hue -- a saturated blue past the gamut clips to purple -- and a ring
 * whose points slide toward whichever corner they overflowed is no longer
 * evenly spaced, which was the whole point of generating it.
 */
function atHue(h, L, C) {
  for (let c = C; c > 0.004; c *= 0.97) {
    const rad = h * Math.PI / 180;
    const out = srgb([L, c * Math.cos(rad), c * Math.sin(rad)]);
    if (out.inside) return hex(out.rgb);
  }
  return hex(srgb([L, 0, 0]).rgb);
}

//: The band the named six occupy, taken from them rather than chosen: mean
//: lightness and mean chroma, and the first seat's hue as where the ring
//: starts. So a generated ring is the same *kind* of colour as the six a
//: viewer sees on a smaller table -- warm, mid-light, not fully saturated --
//: and it moves if somebody ever repaints those six.
const BAND = (() => {
  const lab = NAMED.map(oklab);
  const mean = (f) => lab.reduce((t, v) => t + f(v), 0) / lab.length;
  const [, a0, b0] = lab[0];
  return { L: mean(([L]) => L),
           C: mean(([, a, b]) => Math.hypot(a, b)),
           h0: (Math.atan2(b0, a0) * 180 / Math.PI + 360) % 360 };
})();

//: **Hue alone is one colour to a dichromat, so the ring steps its lightness
//: too.** Evenly spaced hues at a fixed lightness looked right and measured
//: terribly: at ten seats the closest pair was CVD ΔE **0.3** -- the same
//: colour to a red-green dichromat -- because red-green vision keeps roughly
//: one chromatic axis and a hue circle folds onto it. Lightness survives every
//: dichromacy, so seats cycle through four levels spanning 0.20 of OKLab L as
//: the hue goes round. Measured, at four levels and that span: worst pair
//: **5.1** at seven seats, **3.2** at eight, **2.8** at ten, **3.8** at twelve,
//: and every colour at least 4.7:1 on the panel. For comparison the hand-picked
//: six measure **2.1** -- so past six a viewer is not being given something
//: worse, and the six stay because they are what is on the island today.
//:
//:     python3 viewer/palette.py seats 6 7 8 10 12 16
const STEPS = 4;
const SPAN = 0.20;

/** Every seat's colour at a table of `n`, as `#rrggbb`, in seat order. */
export function seatRing(n) {
  const seats = Math.max(1, n | 0);
  if (seats <= NAMED.length) return NAMED.slice(0, seats);
  return Array.from({ length: seats }, (_, i) =>
    atHue(BAND.h0 + i * 360 / seats,
          BAND.L + SPAN * ((i % STEPS) / (STEPS - 1) - 0.5),
          BAND.C));
}

/**
 * Seat `i` of `n`, as `#rrggbb`.
 *
 * `n` is not optional and does not default: the whole defect this replaces was
 * a colour picked from the seat alone, and a caller that does not know how many
 * seats there are cannot ask this question. It is cheap -- the ring is six
 * cube roots and `n` conversions, computed when a scene is built, not per
 * frame -- and callers that draw many seats should ask for `seatRing(n)` once.
 */
export const seatColour = (i, n) => seatRing(n)[((i % n) + n) % n];

/** The same colour as a hex integer, for three.js. */
export const seatInt = (i, n) => parseInt(seatColour(i, n).slice(1), 16);
