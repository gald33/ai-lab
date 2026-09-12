"""The trail, flown: close on each room, wide while she is in the air.

    python3 games/carmel-taldiego/trail_flight.py --out /tmp/flight.html

Gal, 2026-09-09: *"zoom in when arrive and animate zoom out in flight"*.
That is the oldest move in the genre and it is not decoration here -- it is
the only way to draw this trail honestly at one scale. A campaign spans a
couple of thousand kilometres (`trail_card.py --survey`) and a room is a
building, so a still card has to choose: wide enough for the journey, or
close enough for the place. The flight refuses the choice by moving.

WHAT THE CAMERA DOES, AND WHY IT IS THAT AND NOT A PAN.

    hold    at a room, ~500 km across, long enough to read what she said
    flight  eases out to fit both ends, crosses, eases back in

The zoom curve is `sin(pi * t)` in **log** space: zero at both ends, one at
the middle. Log, because a camera's zoom reads as geometric -- halving the
scale looks like the same move whether you are at a continent or a valley,
and a linear ramp spends four fifths of the flight looking at nothing.

It never zooms *in* during a flight: where two rooms are close enough that
fitting them is tighter than the hold, the wide point is clamped to the
hold. Without that, a 170 km leg (Rhine Falls to Wieskirche is one) played
as a lurch forward and back.

**500 km is the closest this may honestly go.** The basemap is Natural
Earth 1:50m, which is drawn for viewing at about that scale; at 50 km it
would be a smooth wrong coastline stated confidently, which is worse than a
coarse one. There is nothing to see closer in anyway -- the map has no
labels, on purpose (`build_basemap.py`), so a room's surroundings *are* its
coast and its border, and those are exactly what the hint vocabulary talks
about.

IT OPENS ON THE WORLD AND ENDS BACK OUT AT IT. Gal, 2026-09-11: *"I want a
world map"*, and the next day, *"do the flight too"*. The still card answers
that with two panels, the world and the box enlarged; a film has the move
the card does not, which is to start wide and come back.

    globe   the whole world, and a box round the corner she stays in
    fade    a dissolve, not a zoom
    ... the holds and the flights, as before ...
    fade    back out
    globe   the same box, with the whole trail drawn in it

**The dissolve is what makes the shots affordable**, and it is a real
argument rather than a stylistic one. A camera that zoomed continuously
from the world to a valley would be *looking at* the world on the way, so
the page would have to carry the whole basemap -- 45,548 points against the
corridor's couple of thousand -- and the two schemes for avoiding that were
built and deleted (`basemap.near`, and `games/carmel-taldiego.md`, "Two
schemes to make the page lighter"). Their objection was that any zoom close
enough to be honest still needs the detailed layer, so a crushed one pops
when it is swapped in. A dissolve between two shots makes no claim about
the ground in between: there is no zoom at which both layers are on screen,
so the world shot can be the coarse layer (1,958 points, 4% of the map) and
the flight the detailed one, and neither is ever a lie about the other.
`test_the_flight_itself_never_sits_at_world_scale` is what keeps that true.

**The opening shot shows the box and not the trail.** Where, not what: the
trail has not happened yet, and a film that opens on its own ending is not
a film. On the way out the same box holds all of it.

THE SAME REFUSALS AS THE STILL CARD, AND ONE MORE THAT MOTION ADDS.
It draws no exits and names no landmark but the trail's own -- see
`trail_card.py` and `games/carmel-taldiego.md`, "Three maps". Motion adds a
way to leak that a still cannot: a camera that pulls back far enough, or
lingers, can show a searcher the neighbourhood to look in. So the basemap
carries no place names at any zoom, and the geometry embedded in the page
is clipped to what the flight actually visits -- a reader who opens the
source finds coastlines, not a gazetteer.

CLAUDE.md: "A page's behaviour is checked in a browser, or it is not
checked". Everything above is behaviour, so `test_trail_flight.py` drives
a real Chromium and watches it happen; nothing here is asserted from
markup. `window.flight` exists so those tests can read the camera -- a
small deliberate surface, documented rather than smuggled, because the
alternative is asserting on a transform string and hoping.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import basemap as BM  # noqa: E402
import carmel as C  # noqa: E402
from trail_card import INK, kept  # noqa: E402

#: The stage, in CSS pixels. The page scales it to fit the window.
WIDTH, HEIGHT = 1000, 640

#: World-pixel units the geometry is emitted in. Big enough that three
#: decimals is sub-pixel at the closest zoom, small enough to read.
WORLD = 8192

#: How wide the camera is when it is sitting on a room, in kilometres.
#: Floored by what 1:50m data can honestly draw -- see the module head.
CLOSE_KM = 500.0

#: The earth, for turning kilometres into Mercator units.
EQUATOR_KM = 40075.017

#: Milliseconds: how long she stands in a room, and the shortest and
#: longest a leg may take however far it is.
HOLD_MS = 1900
FLIGHT_MIN_MS, FLIGHT_MAX_MS = 1700, 3800

#: The kilometres at which a leg earns the longest flight.
FLIGHT_FULL_KM = 6000.0

#: Padding around the two ends of a leg at its widest, and around the whole
#: trail in the closing shot.
LEG_PAD, FINAL_PAD = 0.55, 0.35

#: The camera pulls back by at least this factor on every leg, even one
#: that would fit inside the hold. MEASURED, AND THE REASON IT EXISTS: with
#: `wide` set purely by what fits, a 170 km leg (Rhine Falls to Wieskirche)
#: widened by 1.1x, which on screen is nothing -- the camera slid sideways
#: and the journey did not read as a journey. A campaign's median leg is
#: about 1,500 km against a 500 km hold, so most legs pull back on their
#: own; this is the floor under the short ones.
MIN_PULL = 2.4

#: The opening and closing world shots, and the dissolve between each and
#: the flight, in milliseconds.
#:
#: **They are cuts and not zooms, and that is the whole reason they are
#: affordable.** A camera that zoomed continuously from the world to a
#: valley would be *looking at* the world on the way, so the page would have
#: to carry all 45,548 points of the basemap instead of the corridor's
#: couple of thousand -- and the two schemes for avoiding that were built
#: and deleted (`basemap.near`, and "Two schemes to make the page lighter").
#: A dissolve between two shots makes no claim about the ground in between,
#: so the world shot can be drawn from the coarse layer (1,958 points) and
#: the flight from the detailed one, with no zoom at which they disagree.
GLOBE_MS, FADE_MS = 1700, 520


def close_scale(lat: float) -> float:
    """Pixels per Mercator unit that put `CLOSE_KM` across the stage.

    Mercator's scale grows as 1/cos(lat), so a fixed number of units is a
    different number of kilometres in Bergen than in Zanzibar. Holding the
    *kilometres* constant is what makes two rooms look like the same kind
    of place, which is the whole job of the hold.
    """
    km_per_unit = EQUATOR_KM * math.cos(math.radians(lat))
    return WIDTH / max(CLOSE_KM / km_per_unit, 1e-9)


def fit_scale(points: list[tuple[float, float]], pad: float) -> float:
    """Pixels per unit that hold every projected point, with padding."""
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    half_x = max((max(xs) - min(xs)) / 2, 1e-6) * (1 + pad)
    half_y = max((max(ys) - min(ys)) / 2, 1e-6) * (1 + pad)
    return min(WIDTH / (2 * half_x), HEIGHT / (2 * half_y))


def unwrap(xs: list[float]) -> list[float]:
    out = [xs[0]]
    for x in xs[1:]:
        out.append(min((x + turn for turn in (-1.0, 0.0, 1.0)),
                       key=lambda c, p=out[-1]: abs(c - p)))
    return out


def plan(result: dict, world: C.Map, start: str) -> dict:
    """Everything the page needs: the stops, the legs, and the geometry.

    Computed here rather than in the browser so the page has no arithmetic
    of its own to get wrong, and so the geometry can be clipped to the
    flight before it is ever written down.
    """
    legs = result["moves"]
    names = [start] + [leg["to"] for leg in legs]
    places = [world.places[name] for name in names]
    emptied = kept(result)
    caught_at = len(legs) if result["outcome"] == "caught" else None

    # projected, and unwrapped so a trail across the date line is short
    projected = [BM.mercator(p["lat"], p["lon"]) for p in places]
    xs = unwrap([x for x, _ in projected])
    stops_xy = [(x, y) for x, (_, y) in zip(xs, projected)]

    stops = []
    for i, (name, place, (x, y)) in enumerate(zip(names, places, stops_xy)):
        leg = legs[i - 1] if i else None
        stole = (i - 1) in emptied if i else False
        if not leg:
            took = ""
        elif stole:
            took = world.treasure[name]["treasure"]
        elif i == caught_at:
            took = f'caught taking {world.treasure[name]["treasure"]}'
        else:
            took = "nothing taken"
        stops.append({
            "name": name, "x": x, "y": y,
            "scale": close_scale(place["lat"]),
            "said": leg["details"][0].replace("_", " ") if leg else "",
            "took": took, "stole": stole, "caught": i == caught_at,
            "lobby": i == 0,
        })

    flights = []
    for i, (a, b) in enumerate(zip(places, places[1:])):
        line = BM.great_circle((a["lat"], a["lon"]), (b["lat"], b["lon"]))
        pts = [BM.mercator(lat, lon) for lat, lon in line]
        # keep the arc in the same turn of the world as its two ends
        shift = stops_xy[i][0] - pts[0][0]
        pts = [(x + shift, y) for x, y in pts]
        km = C.travel_hours(a, b) * C.TRAVEL_KMH
        wide = min(stops[i]["scale"] / MIN_PULL,
                   stops[i + 1]["scale"] / MIN_PULL,
                   fit_scale([stops_xy[i], stops_xy[i + 1]], LEG_PAD))
        flights.append({
            "path": [[round(x * WORLD, 2), round(y * WORLD, 2)]
                     for x, y in pts],
            "centres": [[x, y] for x, y in pts],
            "wide": wide,
            "km": round(km),
            "ms": round(FLIGHT_MIN_MS + (FLIGHT_MAX_MS - FLIGHT_MIN_MS)
                        * min(km / FLIGHT_FULL_KM, 1.0)),
            "kept": i in emptied,
        })

    # the closing shot, and the clip box: everything the camera ever sees
    final = fit_scale(stops_xy, FINAL_PAD)
    boxes = [(x - WIDTH / 2 / s, y - HEIGHT / 2 / s,
              x + WIDTH / 2 / s, y + HEIGHT / 2 / s)
             for (x, y), s in ((xy, st["scale"])
                               for xy, st in zip(stops_xy, stops))]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(y for _, y in stops_xy) + max(y for _, y in stops_xy)) / 2
    boxes.append((cx - WIDTH / 2 / final, cy - HEIGHT / 2 / final,
                  cx + WIDTH / 2 / final, cy + HEIGHT / 2 / final))
    for flight in flights:
        for x, y in flight["centres"]:
            boxes.append((x - WIDTH / 2 / flight["wide"],
                          y - HEIGHT / 2 / flight["wide"],
                          x + WIDTH / 2 / flight["wide"],
                          y + HEIGHT / 2 / flight["wide"]))
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
           max(b[2] for b in boxes), max(b[3] for b in boxes))

    # Everything the camera ever sees, cut to that. Two cleverer schemes
    # were tried here and deleted -- `basemap.near` carries the
    # measurements and why neither paid.
    cut = BM.near(box, margin=0.01)
    geometry = {
        key: [[[round(x * WORLD, 2), round(y * WORLD, 2)] for x, y in shape]
              for shape in shapes]
        for key, shapes in cut.items()
    }

    return {
        "stops": stops, "flights": flights,
        "final": {"x": cx, "y": cy, "scale": final},
        "geometry": geometry,
        "globe": globe(stops_xy, xs, places),
        "outcome": result["outcome"],
        "reputation": result["reputation"],
        "hours": round(result["hours"]),
        "emptied": len(emptied),
        "world": WORLD, "w": WIDTH, "h": HEIGHT,
        "hold": HOLD_MS, "globeMs": GLOBE_MS, "fadeMs": FADE_MS,
    }


def globe(stops_xy: list[tuple[float, float]], xs: list[float],
          places: list[dict]) -> dict:
    """The two world shots: the whole planet, the box she stayed inside, and
    on the way out the trail she left in it.

    Gal, 2026-09-11: *"I want a world map"*, and 2026-09-12: *"do the flight
    too"*. The still card answers it with two panels; a film has the other
    move available, which is to open on the world and end back out at it.

    **The coarse layer, not the detailed one.** At one turn of the world
    across 1000px the fine coastline is sub-pixel, and the shots are cuts
    rather than the ends of one long zoom (`GLOBE_MS`), so there is no zoom
    at which the two layers are visible together and disagree -- which is
    exactly the objection that killed the level-of-detail scheme.

    **The campaign is moved into the map's turn, not the map into hers.**
    `unwrap` may leave a trail's x outside [0, 1] so that a leg across the
    date line is short; the world shot rolls the whole campaign back by
    whole turns. Rolling the *map* instead would put the seam somewhere new
    on every card, and a world map with the Pacific split down the middle of
    one campaign and the Atlantic down the next reads as two different
    worlds.
    """
    turn = round(0.5 - (min(xs) + max(xs)) / 2)
    rolled = [(x + turn, y) for x, y in stops_xy]

    # One turn of the world is the stage's width. The stage is shorter than
    # it is wide, so that band is about 75 degrees north and south -- which
    # holds all but one of the map's landmarks; a stop outside it pulls the
    # camera back rather than off the top.
    scale = WIDTH
    reach = max(abs(y - 0.5) for _, y in rolled) + 0.02
    if reach > HEIGHT / 2 / scale:
        scale = HEIGHT / 2 / reach

    pad = 12 / scale
    x0, x1 = min(x for x, _ in rolled) - pad, max(x for x, _ in rolled) + pad
    y0, y1 = min(y for _, y in rolled) - pad, max(y for _, y in rolled) + pad
    span = max((C.travel_hours(a, b) * C.TRAVEL_KMH
                for a in places for b in places), default=0.0)

    def units(points):
        return [[round(x * WORLD, 2), round(y * WORLD, 2)] for x, y in points]

    return {
        "coarse": [units([BM.mercator(lat, lon) for lon, lat in shape])
                   for shape in BM.load()["land_coarse"]],
        "x": 0.5, "y": 0.5, "scale": scale,
        "stops": units(rolled),
        "trail": [units([(x + turn, y) for x, y in
                         (BM.mercator(lat, lon) for lat, lon in
                          BM.great_circle((a["lat"], a["lon"]),
                                          (b["lat"], b["lon"])))])
                  for a, b in zip(places, places[1:])],
        "frame": [round(x0 * WORLD, 2), round(y0 * WORLD, 2),
                  round((x1 - x0) * WORLD, 2), round((y1 - y0) * WORLD, 2)],
        "hair": round(WORLD / scale, 3),
        "span": f"{span:,.0f} KM ACROSS, ON A WORLD 40,075 KM AROUND",
    }


PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { color-scheme: dark; }
  html, body { margin: 0; height: 100%; background: __GROUND__;
               color: __TEXT__; font-family: Georgia, "Times New Roman", serif; }
  #stage { position: relative; width: 100%; max-width: __W__px; margin: 0 auto; }
  svg { display: block; width: 100%; height: auto; background: __SEA__; }
  .chrome { position: absolute; left: 0; right: 0; pointer-events: none; }
  #head { top: 0; padding: 18px 22px 24px;
          background: linear-gradient(__GROUND__ 55%, transparent); }
  #head h1 { margin: 0; font-size: clamp(19px, 3vw, 30px); font-weight: normal; }
  #head p { margin: 4px 0 0; font-size: clamp(11px, 1.5vw, 15px); color: __DIM__; }
  #foot { bottom: 0; padding: 26px 22px 16px; display: flex; gap: 14px;
          align-items: flex-end; justify-content: space-between;
          background: linear-gradient(transparent, __GROUND__ 55%); }
  #say { min-height: 62px; }
  #where { font-size: clamp(14px, 2.2vw, 20px); }
  #said { color: __DIM__; font-size: clamp(11px, 1.5vw, 14px); }
  #took { color: __DIM__; font-size: clamp(11px, 1.5vw, 14px); font-style: italic; }
  #took.stole { color: __THEFT__; }
  #scale { color: __DIM__; font-size: 11px; letter-spacing: 1.2px;
           white-space: nowrap; }
  #play { pointer-events: auto; background: none; color: __TEXT__;
          border: 1px solid __RULE__; border-radius: 3px; padding: 5px 12px;
          font: inherit; font-size: 12px; cursor: pointer; }
  #play:hover { border-color: __LINE__; }
  #credit { position: absolute; right: 10px; top: 10px; font-size: 10px;
            color: __DIM__; opacity: 0.55; pointer-events: none; }
</style>
<div id="stage">
  <svg id="map" viewBox="0 0 __W__ __H__" aria-label="__TITLE__">
    <g id="camera"></g>
    <g id="globe"></g>
    <g id="pins"></g>
  </svg>
  <div class="chrome" id="head">
    <h1>Carmel Taldiego, __OUTCOME__</h1>
    <p>__SUBTITLE__</p>
  </div>
  <div class="chrome" id="foot">
    <div id="say">
      <div id="where"></div>
      <div id="said"></div>
      <div id="took"></div>
    </div>
    <div style="text-align:right">
      <div id="scale"></div>
      <button id="play">pause</button>
    </div>
  </div>
  <div id="credit">basemap: Natural Earth (public domain)</div>
</div>
<script type="application/json" id="data">__DATA__</script>
<script>
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("data").textContent);
  var camera = document.getElementById("camera");
  var pins = document.getElementById("pins");
  var NS = "http://www.w3.org/2000/svg";

  // --- the basemap, drawn once; the camera is a transform on top of it ---
  function shape(points, close) {
    var d = "", i;
    for (i = 0; i < points.length; i++) {
      d += (i ? "L" : "M") + points[i][0] + "," + points[i][1];
    }
    return d + (close ? "Z" : "");
  }
  function add(parent, name, attrs) {
    var el = document.createElementNS(NS, name), k;
    for (k in attrs) { el.setAttribute(k, attrs[k]); }
    parent.appendChild(el);
    return el;
  }
  D.geometry.land.forEach(function (s) {
    add(camera, "path", { d: shape(s, true), fill: "__LAND__" });
  });
  D.geometry.lakes.forEach(function (s) {
    add(camera, "path", { d: shape(s, true), fill: "__SEA__" });
  });
  D.geometry.borders.forEach(function (s) {
    add(camera, "path", { d: shape(s, false), fill: "none",
      stroke: "__BORDER__", "stroke-width": 0.8, opacity: 0.75,
      "vector-effect": "non-scaling-stroke" });
  });
  var trail = add(camera, "path", { d: "", fill: "none", stroke: "__LINE__",
    "stroke-width": 2.4, "stroke-linecap": "round", "stroke-linejoin": "round",
    "vector-effect": "non-scaling-stroke" });

  // --- the world, drawn once and shown at both ends ---------------------
  var globe = document.getElementById("globe");
  D.globe.coarse.forEach(function (s) {
    add(globe, "path", { d: shape(s, true), fill: "__LAND__" });
  });
  var globeTrail = add(globe, "path", {
    d: D.globe.trail.map(function (leg) { return shape(leg, false); }).join(""),
    fill: "none", stroke: "__LINE__", "stroke-width": 1.4, opacity: 0,
    "stroke-linecap": "round", "vector-effect": "non-scaling-stroke" });
  var globeFrame = add(globe, "rect", {
    x: D.globe.frame[0], y: D.globe.frame[1],
    width: D.globe.frame[2], height: D.globe.frame[3], fill: "none",
    stroke: "__DIM__", opacity: 0.75, "stroke-width": 1,
    "vector-effect": "non-scaling-stroke" });
  globe.style.opacity = 0;

  // --- the timeline -----------------------------------------------------
  var segments = [], total = 0, i;
  segments.push({ kind: "globe", when: "open", ms: D.globeMs });
  segments.push({ kind: "fade", into: "map", ms: D.fadeMs });
  for (i = 0; i < D.stops.length; i++) {
    segments.push({ kind: "hold", stop: i, ms: D.hold });
    if (i < D.flights.length) {
      segments.push({ kind: "flight", leg: i, ms: D.flights[i].ms });
    }
  }
  segments.push({ kind: "pull", ms: 1500 });
  segments.push({ kind: "rest", ms: 2600 });
  segments.push({ kind: "fade", into: "globe", ms: D.fadeMs });
  segments.push({ kind: "globe", when: "close", ms: D.globeMs + 900 });
  segments.forEach(function (s) { s.at = total; total += s.ms; });

  function lerp(a, b, t) { return a + (b - a) * t; }
  function glide(a, b, t) { return Math.exp(lerp(Math.log(a), Math.log(b), t)); }
  function ease(t) { return t * t * (3 - 2 * t); }

  // The frame the world shots dissolve out of and back into: the first
  // hold at one end, the closing shot at the other. The camera underneath
  // is already where it will be, so the dissolve is a dissolve and not a
  // move -- nothing behind the fade is pretending to travel.
  function held(i) {
    var st = D.stops[i];
    return { x: st.x, y: st.y, scale: st.scale, phase: "hold",
             stop: i, arrived: i, leg: -1, progress: 0 };
  }
  function settled() {
    return { x: D.final.x, y: D.final.y, scale: D.final.scale, phase: "rest",
             stop: D.stops.length - 1, arrived: D.stops.length - 1,
             leg: -1, progress: 0 };
  }

  function frame(clock) {
    var s = segments[segments.length - 1], k;
    for (k = 0; k < segments.length; k++) {
      if (clock < segments[k].at + segments[k].ms) { s = segments[k]; break; }
    }
    var t = Math.min(Math.max((clock - s.at) / s.ms, 0), 1);
    if (s.kind === "globe") {
      var under = s.when === "open" ? held(0) : settled();
      under.globe = 1;
      under.opening = s.when === "open";
      under.phase = "globe";
      return under;
    }
    if (s.kind === "fade") {
      var to = s.into === "map";
      var base = to ? held(0) : settled();
      base.globe = to ? 1 - ease(t) : ease(t);
      base.opening = to;
      return base;
    }
    if (s.kind === "hold") {
      return held(s.stop);
    }
    if (s.kind === "flight") {
      var f = D.flights[s.leg], a = D.stops[s.leg], b = D.stops[s.leg + 1];
      var e = ease(t);
      var at = f.centres[Math.min(Math.round(e * (f.centres.length - 1)),
                                  f.centres.length - 1)];
      // out and back in, in log space, so both ends are exactly the hold
      var near = glide(a.scale, b.scale, e);
      return { x: at[0], y: at[1],
               scale: glide(near, f.wide, Math.sin(Math.PI * t)),
               phase: "flight", stop: s.leg + 1, arrived: s.leg,
               leg: s.leg, progress: e, km: f.km, globe: 0 };
    }
    var last = D.stops[D.stops.length - 1];
    var e2 = s.kind === "pull" ? ease(t) : 1;
    return { x: lerp(last.x, D.final.x, e2), y: lerp(last.y, D.final.y, e2),
             scale: glide(last.scale, D.final.scale, e2), phase: "rest",
             stop: D.stops.length - 1, arrived: D.stops.length - 1,
             leg: -1, progress: 0, globe: 0 };
  }

  // --- drawing ----------------------------------------------------------
  function screen(x, y, f) {
    return [D.w / 2 + (x - f.x) * f.scale, D.h / 2 + (y - f.y) * f.scale];
  }
  function screenGlobe(point) {
    return [D.w / 2 + (point[0] / D.world - D.globe.x) * D.globe.scale,
            D.h / 2 + (point[1] / D.world - D.globe.y) * D.globe.scale];
  }
  var where = document.getElementById("where");
  var said = document.getElementById("said");
  var took = document.getElementById("took");
  var scaleLabel = document.getElementById("scale");

  function drawn(f) {
    var d = "", j, n, pts, upto;
    for (j = 0; j < D.flights.length; j++) {
      if (f.leg >= 0 && j > f.leg) { break; }
      if (f.leg < 0 && j > f.arrived - 1) { break; }
      pts = D.flights[j].path;
      upto = (j === f.leg) ? Math.max(1, Math.round(f.progress * (pts.length - 1)))
                           : pts.length - 1;
      for (n = 0; n <= upto; n++) {
        d += (n ? "L" : "M") + pts[n][0] + "," + pts[n][1];
      }
    }
    return d;
  }

  function paint(f) {
    var over = f.globe || 0;
    camera.style.opacity = 1 - over;
    globe.style.opacity = over;
    if (over > 0) {
      globe.setAttribute("transform",
        "translate(" + (D.w / 2) + "," + (D.h / 2) + ") scale("
        + (D.globe.scale / D.world) + ") translate("
        + (-D.globe.x * D.world) + "," + (-D.globe.y * D.world) + ")");
      // The opening shot says where, not what: the box she stayed inside,
      // and nothing of the trail she is about to leave in it. On the way
      // out the same box holds the whole thing.
      globeTrail.setAttribute("opacity", f.opening ? 0 : 1);
    }
    camera.setAttribute("transform",
      "translate(" + (D.w / 2) + "," + (D.h / 2) + ") scale("
      + (f.scale / D.world) + ") translate(" + (-f.x * D.world) + ","
      + (-f.y * D.world) + ")");
    trail.setAttribute("d", drawn(f));

    while (pins.firstChild) { pins.removeChild(pins.firstChild); }
    if (over >= 0.5) {
      // On the world, her stops are drawn where the globe camera puts them
      // -- and only on the way out, since the opening shot has not happened
      // yet. `data-stop` is kept so the pin count still means what every
      // test that reads it thinks it means.
      if (!f.opening) {
        for (var g = 0; g < D.globe.stops.length; g++) {
          var gp = screenGlobe(D.globe.stops[g]);
          if (D.stops[g].caught) {
            add(pins, "circle", { cx: gp[0], cy: gp[1], r: 7, fill: "none",
              stroke: "__THEFT__", "stroke-width": 1.4 });
          }
          add(pins, "circle", { cx: gp[0], cy: gp[1], r: 2.6,
            fill: D.stops[g].stole ? "__THEFT__" : "__STOP__",
            "data-stop": g });
        }
      }
      where.textContent = f.opening ? "the world" : "the whole chase";
      said.textContent = f.opening ? "she is somewhere in the box"
                                   : D.globe.span;
      took.textContent = "";
      took.className = "";
      scaleLabel.textContent = Math.round(D.w / D.globe.scale * 40075)
        .toLocaleString() + " KM ACROSS";
      window.flight = { clock: clock, scale: D.globe.scale, x: D.globe.x,
        y: D.globe.y, phase: "globe", globe: over, opening: !!f.opening,
        stop: f.stop, leg: -1, progress: 0,
        trail: trail.getAttribute("d").length,
        pins: pins.querySelectorAll("[data-stop]").length,
        marks: pins.childNodes.length, done: clock >= total - 1 };
      return;
    }
    for (var j = 0; j <= f.arrived; j++) {
      var st = D.stops[j], at = screen(st.x, st.y, f);
      if (st.caught) {
        add(pins, "circle", { cx: at[0], cy: at[1], r: 12, fill: "none",
          stroke: "__THEFT__", "stroke-width": 1.6 });
      }
      // `data-stop` is what makes the count checkable. The group also
      // holds a ring on the room she was caught in and, mid-leg, a dot for
      // where she actually is, so `childNodes.length` is not the number of
      // rooms reached and a test that read it as one went red the day
      // catches became common (`carmel-taldiego.md`, "The catch ring that
      // nothing had ever counted").
      add(pins, "circle", { cx: at[0], cy: at[1], r: j ? 6 : 5,
        fill: st.stole ? "__THEFT__" : "__SEA__", stroke: "__STOP__",
        "stroke-width": 2, "data-stop": j });
    }
    if (f.phase === "flight") {
      // where she actually is. The camera centres on her, so this is
      // always mid-stage -- but without it the leading edge of the line is
      // the only thing moving and it reads as a line being drawn rather
      // than as somebody travelling.
      var pts = D.flights[f.leg].path;
      var n = Math.max(1, Math.round(f.progress * (pts.length - 1)));
      var at = screen(pts[n][0] / D.world, pts[n][1] / D.world, f);
      add(pins, "circle", { cx: at[0], cy: at[1], r: 4.5,
        fill: "__LINE__", stroke: "__SEA__", "stroke-width": 1.5 });
    }
    var here = D.stops[f.phase === "flight" ? f.arrived : f.stop];
    if (f.phase === "flight") {
      where.textContent = "in the air — " + f.km.toLocaleString() + " km";
      said.textContent = "to " + D.stops[f.leg + 1].name;
      took.textContent = "";
      took.className = "";
    } else {
      where.textContent = (f.stop) + ". " + here.name
        + (here.lobby ? "  — the lobby" : "");
      said.textContent = here.said ? "\\u201c" + here.said + "\\u201d" : "";
      took.textContent = here.took;
      took.className = here.stole ? "stole" : "";
    }
    var km = Math.round(D.w / f.scale * 40075
      * Math.cos(Math.atan(Math.sinh(Math.PI * (1 - 2 * f.y)))));
    scaleLabel.textContent = km.toLocaleString() + " KM ACROSS";
    window.flight = { clock: clock, scale: f.scale, x: f.x, y: f.y,
      phase: f.phase, globe: over, stop: f.stop, leg: f.leg,
      progress: f.progress,
      trail: trail.getAttribute("d").length,
      pins: pins.querySelectorAll("[data-stop]").length,
      marks: pins.childNodes.length,
      done: clock >= total - 1 };
  }

  // --- the clock --------------------------------------------------------
  var clock = 0, last = null, running = true;
  var button = document.getElementById("play");
  var still = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function tick(now) {
    if (last !== null && running) { clock = Math.min(clock + (now - last), total - 1); }
    last = now;
    paint(frame(clock));
    if (clock >= total - 1) { running = false; button.textContent = "replay"; }
    requestAnimationFrame(tick);
  }

  // A test surface, and the reason it exists rather than the tests
  // sleeping: the flight is about twenty seconds long, and asserting that
  // the camera pulls back at the middle of the second leg by waiting for
  // it is both slow and a race. `seek` moves the clock and repaints; it
  // changes nothing about how the page plays for a reader.
  window.seekFlight = function (ms) {
    clock = Math.min(Math.max(ms, 0), total - 1);
    running = false;
    button.textContent = "play";
    paint(frame(clock));
    return window.flight;
  };
  window.flightPlan = { total: total, segments: segments };

  button.addEventListener("click", function () {
    if (clock >= total - 1) { clock = 0; }
    running = !running;
    button.textContent = running ? "pause" : "play";
  });

  if (still) {
    // A reader who has asked for no motion gets the whole trail at once --
    // the closing shot, which is the frame everything else builds to.
    running = false;
    clock = total - 1;
    button.textContent = "play";
    paint(frame(clock));
    window.flight.reduced = true;
  } else {
    requestAnimationFrame(tick);
  }
}());
</script>
"""


def page(result: dict, world: C.Map, seed: bytes, start: str) -> str:
    data = plan(result, world, start)
    took = data["emptied"]
    subtitle = (f'{len(data["flights"])} rooms, {took} of them emptied, '
                f'{data["reputation"]} reputation, {data["hours"]} hours')
    swaps = {
        "__TITLE__": f'Carmel Taldiego, {result["outcome"]}',
        "__OUTCOME__": result["outcome"],
        "__SUBTITLE__": subtitle,
        "__DATA__": json.dumps(data, separators=(",", ":")),
        "__W__": str(WIDTH), "__H__": str(HEIGHT),
        "__GROUND__": INK["ground"], "__SEA__": INK["sea"],
        "__LAND__": INK["land"], "__BORDER__": INK["border"],
        "__LINE__": INK["line"], "__STOP__": INK["stop"],
        "__TEXT__": INK["text"], "__DIM__": INK["dim"],
        "__THEFT__": INK["theft"], "__RULE__": INK["rule"],
    }
    out = PAGE
    for token, value in swaps.items():
        out = out.replace(token, value)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", help="hex; omitted means a fresh one")
    ap.add_argument("--out", default="flight.html")
    ap.add_argument("--searchers", type=int, default=2)
    args = ap.parse_args()

    seed = bytes.fromhex(args.seed) if args.seed else os.urandom(32)
    world = C.Map(seed)
    result = C.chase(seed, C.LOBBY_LANDMARK, searchers=args.searchers,
                     world=world)
    Path(args.out).write_text(page(result, world, seed, C.LOBBY_LANDMARK),
                              encoding="utf-8")
    print(f"{result['outcome']}: {len(result['moves'])} rooms,"
          f" {result['reputation']} reputation")
    print(f"wrote {args.out}   seed {seed.hex()}")


if __name__ == "__main__":
    main()
