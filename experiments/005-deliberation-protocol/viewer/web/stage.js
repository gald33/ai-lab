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
//: satellite. Shallow enough that the huts have sides and the shore has depth.
const TILT = 0.86, TURN = -0.62;

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
    // The cost is nil here because this renders on demand, not per frame.
    this.renderer = new THREE.WebGLRenderer({
      canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
    this.renderer.setClearColor(0x000000, 0);
    this.scene = new THREE.Scene();

    // Framed on the island, in the viewBox's aspect. Both halves of the page
    // are then looking at the same rectangle.
    const aspect = geo.w / geo.h;
    const half = EXTENT;
    this.camera = new THREE.OrthographicCamera(
      -half * aspect, half * aspect, half, -half, -50, 100);
    this.camera.position.set(
      Math.sin(TURN) * 10 * Math.cos(TILT), Math.sin(TILT) * 10,
      Math.cos(TURN) * 10 * Math.cos(TILT));
    this.camera.lookAt(0, 0, 0);
    this.camera.updateMatrixWorld();

    // Daylight: a warm key with the sun's own colour, a cool fill from the sea
    // side, and enough ambient that the shaded faces are still readable. The
    // key is kept as `this.key` because the sun is on a clock and this should
    // eventually move with it.
    this.scene.add(new THREE.AmbientLight(0xbcd2dd, 1.15));
    this.key = new THREE.DirectionalLight(0xffd9a8, 2.1);
    this.key.position.set(4, 7, 3);
    this.scene.add(this.key);
    const fill = new THREE.DirectionalLight(0x6fa6c8, 0.75);
    fill.position.set(-5, 3, -4);
    this.scene.add(fill);

    this.island = null;
    this.anchors = {};
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
    const made = buildIsland({ traders, goods, seats });
    this.island = made.island;
    this.anchors = made.anchors;
    this.ground = made.ground;
    this.scene.add(this.island);
    this.render();
    return made;
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

  /** The canvas follows its box; the framing does not move. */
  resize() {
    const box = this.canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(box.width)), h = Math.max(1, Math.round(box.height));
    this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    this.renderer.setSize(w, h, false);
    this.render();
  }

  /**
   * Re-frame for a viewBox of a different shape -- which is what a rotated
   * phone is, since the scene stacks its huts in a column there and its
   * viewBox goes tall with them.
   */
  reframe(geo) {
    this.geo = geo;
    const aspect = geo.w / geo.h;
    Object.assign(this.camera, {
      left: -EXTENT * aspect, right: EXTENT * aspect, top: EXTENT, bottom: -EXTENT });
    this.camera.updateProjectionMatrix();
    this.resize();
  }

  render() {
    if (this.island) this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    if (this.island) dispose(this.island);
    this.renderer.dispose();
  }
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
