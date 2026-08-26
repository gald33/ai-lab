/**
 * The island, rendered. A WebGL canvas behind the scene's own drawing.
 *
 * The design this comes from was a page of its own: a 3D stage with orbit
 * controls, and every number beside it written into the HTML by hand. This is
 * the half of it that belongs in the viewer -- the island as a model -- put
 * under the page that already knows what happened on it.
 *
 * **Orthographic, and framed to the scene's own viewBox.** A perspective camera
 * would have been the obvious port, and it is the wrong one here: the cards,
 * ropes and sun are SVG drawn in viewBox coordinates, and under perspective the
 * map from the ground to those coordinates changes with the window's aspect, so
 * a hut and the card belonging to it would drift apart on resize. Orthographic
 * makes ground-to-viewBox an **affine map that does not depend on the viewport
 * at all**, which is what lets `groundAt()` place a settlement exactly beneath
 * a card the scene has already positioned.
 *
 * The tilt is what makes it read as a model rather than a plan.
 */

import * as THREE from "./vendor/three/three.module.js";
import { buildIsland } from "./island3d.js";
import { enliven } from "./island-life.js";
import { stageEvent } from "./island-events.js";

//: How much island the frame holds, in island units, measured on the short
//: side of the viewBox.
//:
//: Not the sea disc's 4.95, which was the first guess and put the settlements
//: in the water: the scene lays its cards out across the frame, and a frame
//: wide enough to hold the whole sea maps those card positions to ground points
//: beyond the shore. This is set so that the seats the scene chooses land on
//: the meadow, which costs the corners of the sea and gains an island you are
//: standing on rather than looking at from orbit.
const EXTENT = 4.35;

//: Looking down and along, from over the trader's shoulder rather than a
//: satellite. **Lower than it was** (0.86): the flatter the camera sits, the
//: more the island reads as a plan of itself, and the less a turn of the
//: camera shows. At this angle the huts have sides, the shore has depth, and
//: the rotation below has something to reveal. Raise it back toward 0.9 for a
//: more overhead view.
const TILT = 0.68;

//: Where the camera starts, and how long it takes to go round once. Slow on
//: purpose: this is a place being watched, not a turntable, and a spectator
//: reading a card should never feel hurried by the ground moving under it.
const TURN = -0.62, TURN_SECONDS = 150;

export class Stage {
  /**
   * @param {HTMLCanvasElement} canvas  sits behind the scene's `<svg>`
   * @param {{w:number,h:number}} geo   the scene's viewBox, which this frames
   */
  constructor(canvas, geo) {
    this.canvas = canvas;
    this.geo = geo;
    // `preserveDrawingBuffer` so the canvas can be read back after a render.
    // Nothing in the page needs that; the harness does -- it is how a check
    // can say the island actually drew rather than that a canvas exists.
    // It costs a little now that this renders every frame; a check that can
    // read the picture back is worth more than that.
    this.renderer = new THREE.WebGLRenderer({
      canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    this.renderer.setClearColor(0x000000, 0);
    this.scene = new THREE.Scene();

    // Framed into the box the page left for it, which is no longer the whole
    // frame: the trader cards stand in the margins now, and the island is what
    // is between them.
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -50, 100);
    this.frame(geo.islandBox ?? { x: 0, y: 0, w: geo.w, h: geo.h });
    this.turn = TURN;
    this.aim(TURN);

    // Daylight: a warm key with the sun's own colour, a cool fill from the sea
    // side, and enough ambient that the shaded faces are still readable. The
    // key is kept as `this.key` because the sun is on the page's clock and the
    // light goes round with it -- see `island-life.js`, which owns the day.
    this.ambient = new THREE.AmbientLight(0xbcd2dd, 1.15);
    this.scene.add(this.ambient);
    this.key = new THREE.DirectionalLight(0xffd9a8, 2.1);
    this.key.position.set(4, 7, 3);
    this.scene.add(this.key);
    // The fill is kept too, and for the same reason: at dusk the key comes in
    // almost horizontally and lights nothing the camera can see, so whatever
    // else is in the rig is what the island's colour *is* by then. A cool fill
    // left at full strength makes a sunset read blue.
    this.fill = new THREE.DirectionalLight(0x6fa6c8, 0.75);
    this.fill.position.set(-5, 3, -4);
    this.scene.add(this.fill);

    this.island = null;
    this.anchors = {};
    this.life = null;
    this.world = null;
    //: Clips in flight. More than one at a time on purpose: a production and
    //: an offer a second apart are two things that happened, and holding the
    //: second until the first finished would be the page inventing an order
    //: the board did not have.
    this.clips = [];
    this.day = null;
    //: The pending animation-frame handle. Named for what it is: `frame` was
    //: taken by the framing below, and a rAF id stored under it made the
    //: method vanish behind an integer.
    this.raf = null;
    this.t0 = 0;
    // Somebody who asked for less motion gets a still island: everything the
    // loop does is atmosphere, and none of it carries a fact.
    this.still = matchMedia?.("(prefers-reduced-motion: reduce)")?.matches ?? false;
    // A hidden tab should not be animating an island nobody is looking at.
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) this.pause(); else this.play();
    });
    this.resize();
  }

  /**
   * Build the island for this round. Cheap enough to redo when the round
   * changes; not something to do on a resize, which is why the camera is the
   * part that does not depend on the viewport.
   */
  build({ traders, goods, seats }) {
    if (this.island) {
      this.scene.remove(this.island);
      dispose(this.island);
    }
    this.clear();
    const made = buildIsland({ traders, goods, seats });
    this.island = made.island;
    this.anchors = made.anchors;
    this.ground = made.ground;
    this.world = { island: made.island, anchors: made.anchors,
                   ground: made.ground, traders, goods };
    this.life = enliven(this.island, { ground: made.ground });
    this.scene.add(this.island);
    // Placed at t=0 before anything is shown, so a still island is an island
    // at a moment rather than one with its gulls at the origin.
    this.life.update(0, this.ctx());
    this.render();
    this.play();
    return made;
  }

  /**
   * Put the island inside a rectangle of the scene's viewBox.
   *
   * The camera still renders across the whole canvas -- what changes is the
   * frustum, widened and pushed off-centre so that the island lands where the
   * box is. Doing it here rather than by moving the canvas keeps `toViewBox()`
   * and `groundAt()` correct without either of them knowing about the box:
   * they project through this camera and map the result to the whole viewBox,
   * which is exactly what the renderer does.
   */
  frame(box) {
    this.box = box;
    //: viewBox units per island unit, set so the island fits the box's short
    //: side -- the same rule the whole-frame version used, on a smaller frame.
    const s = Math.min(box.w, box.h) / (2 * EXTENT);
    const cx = box.x + box.w / 2, cy = box.y + box.h / 2;
    Object.assign(this.camera, {
      left: -cx / s, right: -cx / s + this.geo.w / s,
      top: cy / s, bottom: cy / s - this.geo.h / s,
    });
    this.camera.updateProjectionMatrix();
  }

  /**
   * Point the camera from a given bearing. The island stays where it is and
   * the camera goes round it, which is what keeps the settlements' ground
   * positions -- and so the trails and sites between them -- fixed.
   */
  aim(turn) {
    this.turn = turn;
    this.camera.position.set(
      Math.sin(turn) * 10 * Math.cos(TILT), Math.sin(TILT) * 10,
      Math.cos(turn) * 10 * Math.cos(TILT));
    this.camera.lookAt(0, 0, 0);
    this.camera.updateMatrixWorld();
  }

  /**
   * Where a point on the island lands in the scene's viewBox.
   *
   * The scene draws in viewBox units and knows nothing about the model, so
   * everything crossing between them crosses here.
   */
  toViewBox(world) {
    const v = world.clone().project(this.camera);
    return { x: (v.x * 0.5 + 0.5) * this.geo.w, y: (1 - (v.y * 0.5 + 0.5)) * this.geo.h };
  }

  /**
   * The other direction: a point in the scene's viewBox, dropped onto the
   * island's ground. This is what puts a hut under a card -- the scene decides
   * where a trader's card goes, and the settlement is placed to match rather
   * than the other way round.
   */
  groundAt(x, y, height = 0.70) {
    const ndc = new THREE.Vector3((x / this.geo.w) * 2 - 1, 1 - (y / this.geo.h) * 2, -1);
    ndc.unproject(this.camera);
    const dir = new THREE.Vector3(0, 0, -1).applyQuaternion(this.camera.quaternion);
    // Orthographic: every ray is the view direction, so this is one division
    // rather than a raycast.
    const t = (height - ndc.y) / dir.y;
    return [ndc.x + dir.x * t, ndc.z + dir.z * t];
  }

  /**
   * The canvas follows its box, and the model is drawn into the same rectangle
   * the drawing is.
   *
   * **The `<svg>` letterboxes and the canvas does not.** Both cover the page,
   * but the SVG fits its viewBox inside that box with `meet`, so on a window
   * wider than the viewBox it leaves bars at the sides -- while the canvas
   * filled the lot and the camera, built at the viewBox's aspect, was stretched
   * across it. The two halves of the page were describing differently-shaped
   * islands, which stayed invisible only while the cards sat on top of the
   * huts and moved with them. Now that the cards stand in the margins, an
   * island stretched into those margins is an island under the cards.
   *
   * So the renderer is given the same rectangle: the viewBox's aspect, fitted
   * and centred, with everything outside it scissored away.
   */
  resize() {
    const box = this.canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(box.width)), h = Math.max(1, Math.round(box.height));
    this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    this.renderer.setSize(w, h, false);
    const k = Math.min(w / this.geo.w, h / this.geo.h);
    const vw = this.geo.w * k, vh = this.geo.h * k;
    const vx = (w - vw) / 2, vy = (h - vh) / 2;
    // WebGL counts from the bottom; the page counts from the top.
    this.renderer.setViewport(vx, h - vy - vh, vw, vh);
    this.renderer.setScissor(vx, h - vy - vh, vw, vh);
    this.renderer.setScissorTest(true);
    this.render();
  }

  /**
   * Re-frame for a viewBox of a different shape -- which is what a rotated
   * phone is, since the scene stacks its huts in a column there and its
   * viewBox goes tall with them.
   */
  reframe(geo) {
    this.geo = geo;
    this.frame(geo.islandBox ?? { x: 0, y: 0, w: geo.w, h: geo.h });
    this.resize();
  }

  /**
   * How far through its day the island is.
   *
   * Set by the page from the same clock the drawn sun crosses on. `null` when
   * the board has not said -- before the round, or on a board whose schedule
   * this page could not read -- and the light then holds where it is rather
   * than snapping to dawn.
   */
  setDay(day) {
    this.day = day;
    if (this.still) { this.life?.update(0, this.ctx()); this.render(); }
  }

  /**
   * Something happened on the board; show it on the island.
   *
   * Silently does nothing for an event the island has no clip for, and for a
   * reader who asked for less motion. The page calls this for every event it
   * paints, so "not everything is worth animating" has to be cheap.
   */
  fire(event) {
    if (!this.world || this.still) return null;
    const c = stageEvent(event, this.world);
    if (!c) return null;
    c.t0 = null;
    this.island.add(c.root);
    this.clips.push(c);
    this.play();
    return c;
  }

  /** Advance every clip in flight, and retire the ones that have run. */
  step(t) {
    for (let i = this.clips.length - 1; i >= 0; i--) {
      const c = this.clips[i];
      c.t0 ??= t;
      const age = t - c.t0;
      c.update(age);
      if (age < c.dur) continue;
      // A clip that moved the island's own nodes puts them back; one that only
      // added its own props just goes.
      c.restore?.();
      this.island.remove(c.root);
      disposeClip(c);
      this.clips.splice(i, 1);
    }
  }

  /** Every clip in flight, gone -- the island under them is being rebuilt. */
  clear() {
    for (const c of this.clips) {
      c.restore?.();
      this.island?.remove(c.root);
      disposeClip(c);
    }
    this.clips = [];
  }

  ctx() {
    return { day: this.day, key: this.key, ambient: this.ambient, fill: this.fill };
  }

  play() {
    if (this.raf !== null || this.still || !this.life || document.hidden) return;
    const tick = (now) => {
      this.t0 ||= now;
      const t = (now - this.t0) / 1000;
      this.aim(TURN + (t / TURN_SECONDS) * Math.PI * 2);
      this.life.update(t, this.ctx());
      this.step(t);
      this.renderer.render(this.scene, this.camera);
      // The camera moved, so every settlement is somewhere else on screen and
      // the cards have to go with them. This is the whole reason the page hands
      // the stage a callback rather than the stage knowing about the scene.
      this.onFrame?.(this);
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  pause() {
    if (this.raf !== null) cancelAnimationFrame(this.raf);
    this.raf = null;
  }

  render() {
    if (this.island) this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    this.pause();
    this.clear();
    if (this.island) dispose(this.island);
    this.renderer.dispose();
  }
}

/**
 * A finished clip, given back.
 *
 * Only what the clip made: its geometries, and the materials it cloned for
 * itself. The model's own materials are shared across the island and disposing
 * one here would take a face off every mesh using it.
 */
function disposeClip(c) {
  c.root.traverse((n) => n.geometry?.dispose());
  for (const m of c.mine) m.dispose?.();
}

/** Give the GPU back what a rebuilt island stopped using. */
function dispose(root) {
  root.traverse((n) => {
    if (n.geometry) n.geometry.dispose();
    // Materials are shared across the model by design, so they are disposed
    // once each rather than once per mesh that reaches them.
    const mats = Array.isArray(n.material) ? n.material : n.material ? [n.material] : [];
    for (const m of mats) m.dispose?.();
  });
}
