// What a good looks like when the island draws one.
//
// **One texture, used by everything that has to say which good it is.** A crate
// standing in a trader's yard and the flag over the site that makes that good
// are the same claim, and until this existed they were made two different ways:
// the crate carried a colour and a symbol, and the flag carried a colour and
// nothing at all. A flag that only has its colour is asking a viewer to tell
// pink from purple across an island eight units wide, which is precisely what
// the palette does not promise -- it clears *adjacent* pairs, not all pairs,
// and that is the whole reason a good carries a glyph anywhere.
//
// It lives in its own file rather than in `island3d.js` because the glyph table
// is `scene.js`'s, and the model must not import the drawing layer. Nothing
// here imports the model either -- the colour arrives as an argument -- so
// there is no cycle in any direction.

import * as THREE from "./vendor/three/three.module.js";
//: The page's one list of what a good is marked with. A second copy would be a
//: second answer to "what is bread" the first time somebody added a good.
import { GLYPH } from "./scene.js";

//: Built once per good and shared. A texture is a canvas and an upload; one per
//: crate would be six per trader per good.
const cache = new Map();

/**
 * A face for a good: its colour, with its own symbol on it.
 *
 * The same two marks the legend and the card's shelf use, so a crate on the
 * ground, a flag over a site and a bar on a card are recognisably one good.
 *
 * @param {string} good    the good's name, for its glyph
 * @param {number} colour  `0xrrggbb`, from `GOOD_COLOURS` -- which is the
 *   stylesheet's palette, because that is the one the contrast and dichromacy
 *   gates are run against
 * @param {boolean} lip    a dark border, so a stack of crates reads as separate
 *   boxes rather than one painted block. A flag is a single surface and does
 *   not want one.
 */
export function face(good, colour, { lip = true } = {}) {
  const key = `${good}:${colour}:${lip}`;
  if (cache.has(key)) return cache.get(key);
  //: **`null` where there is no document to draw on.** A texture is a canvas,
  //: and the island is built headless by checks that ask it geometry questions
  //: -- where a hut stands, how high the ground is -- and never render a pixel.
  //: A model that cannot be constructed without a browser is a model those
  //: checks cannot ask. The caller falls back to the flat colour, which is
  //: what a face is under its mark anyway.
  if (typeof document === "undefined") return null;
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const g = c.getContext("2d");
  g.fillStyle = `#${colour.toString(16).padStart(6, "0")}`;
  g.fillRect(0, 0, 128, 128);
  if (lip) {
    g.strokeStyle = "rgba(0,0,0,0.28)";
    g.lineWidth = 8;
    g.strokeRect(4, 4, 120, 120);
  }
  //: **Always something.** A good the glyph table has never heard of -- the
  //: eighth one somebody adds -- would otherwise get a plain coloured square,
  //: and colour alone does not identify. The card's shelf already falls back to
  //: the same mark for the same reason.
  g.font = "76px serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillStyle = "rgba(255,255,255,0.92)";
  g.fillText(GLYPH[good] || "▪", 64, 70);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  cache.set(key, tex);
  return tex;
}
