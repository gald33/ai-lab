"""The island's sound, rendered offline in a real browser and measured.

    python viewer/tests/audio.py            # check
    python viewer/tests/audio.py --verbose  # and print the table

Sound cannot be checked by ear in CI and should not be checked by ear here
either -- "it sounds about right" is how the sites ended up inaudible in the
first version of this. What *can* be asserted is the thing that was actually
wrong: how loud each part is against the rest, and whether the sum clips.

An `OfflineAudioContext` renders the real `island-ambience.js` faster than
real time and hands back the samples, so this is the bed itself being
measured, not a model of it. The clock is faked forward so the whole span is
scheduled before the render runs -- the scheduler works a beat ahead of
`ctx.currentTime`, and without that only its first window would be in the
buffer.

Skips rather than fails when Playwright or Chromium is absent, like
`render.py`: this must not become something a checkout has to install.

What it holds:

* **The bed is there and is quiet.** Silence would pass any "no error" check.
* **Nothing clips**, at the master gain the page actually applies.
* **Every good's site can be heard working**, against the bed alone as the
  control. This is the measurement that changed the design: at the first
  `WORK_GAIN` a whole site at work moved the mix by 7%, and salt by nothing.
"""

from __future__ import annotations

import argparse
import http.server
import socket
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent

#: The master gain `island-sound.js` puts between all of this and the speakers.
#: Kept here so the clipping check is against what a listener hears, not what
#: the bed renders on its own.
MASTER = 0.32

#: A site at work has to be at least this much louder than the bed alone over
#: the same window. Not a taste: 1.0 is inaudible and was shipped once.
FLOOR = 1.35

SECONDS = 12

#: The seeds every measurement is taken on. Each is a different draw of when
#: the gulls call and where the strikes fall; a site clears the floor on the
#: *worst* of them or it does not clear it. Three, because a site that fails
#: one seed in three is a site whose margin is the scheduler's luck.
SEEDS = (1, 7, 12345)

#: Every accent voice, rendered alone and measured by zero-crossing rate --
#: a fair pitch proxy for signals this simple, and it needs no FFT.
#:
#: The rule it holds is the island's own: **the bell is the top of the
#: register.** It is the one voice the design lets sit over everything, the
#: day ending being the loudest fact on the board -- so nothing else may ring
#: above it. `settled` did, at ~1019Hz against the bell's ~539, and since a
#: settlement plays while goods cross the ground between two huts, what a
#: spectator heard was a box in the air pitched above the end of the day. It
#: was reported by ear before it was ever measured.
VOICE_PITCH = """
async () => {
  const { VOICES } = await import('./island-sound.js');
  const out = {};
  for (const name of Object.keys(VOICES)) {
    const ctx = new OfflineAudioContext(1, 44100 * 3, 44100);
    VOICES[name](ctx, ctx.destination, 0);
    const d = (await ctx.startRendering()).getChannelData(0);
    let cross = 0, last = 0, voiced = 0, peak = 0;
    for (let i = 1; i < d.length; i++) {
      peak = Math.max(peak, Math.abs(d[i]));
      if (Math.abs(d[i]) < 1e-4) continue;
      voiced++;
      const sign = d[i] > 0 ? 1 : -1;
      if (last && sign !== last) cross++;
      last = sign;
    }
    out[name] = { pitch: voiced ? cross / 2 / (voiced / 44100) : 0, peak };
  }
  return out;
}
"""

MEASURE = """
async ([secs, good, day, closed, seed]) => {
  const { Ambience } = await import('./island-ambience.js');
  const ctx = new OfflineAudioContext(1, 44100 * secs, 44100);
  let fake = 0;
  Object.defineProperty(ctx, 'currentTime', { get: () => fake });
  // Seeded, because everything intermittent here is scheduled at random and
  // an unseeded check reports the dice: sites sit near the floor and one run
  // in six failed on a different one each time. `Ambience` takes the rng for
  // exactly this. The spread is not thrown away -- the caller runs several
  // seeds and judges the worst.
  let x = seed >>> 0;
  const rng = () => {
    x = (x + 0x6D2B79F5) >>> 0;
    let r = Math.imul(x ^ (x >>> 15), 1 | x);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
  const a = new Ambience(ctx, ctx.destination, { rng });
  a.start();
  a.setDay(day, closed);
  if (good === '@sunrise') a.sunrise(); else if (good) a.working(good);
  for (let t = 0; t < secs; t += 0.4) { fake = t; a.pump(); }
  fake = 0;
  const d = (await ctx.startRendering()).getChannelData(0);
  const rms = (from, to) => {
    let sum = 0;
    const a0 = Math.floor(from * 44100), a1 = Math.min(d.length, Math.floor(to * 44100));
    for (let i = a0; i < a1; i++) sum += d[i] * d[i];
    return Math.sqrt(sum / (a1 - a0));
  };
  let peak = 0;
  for (let i = 0; i < d.length; i++) peak = Math.max(peak, Math.abs(d[i]));
  // How much of the work window lives above roughly 4kHz, as a one-pole
  // difference. This is the thing RMS is blind to: a square-wave click and a
  // struck body can measure the same loudness and one of them is a headache.
  const bright = (from, to) => {
    const a0 = Math.floor(from * 44100), a1 = Math.min(d.length, Math.floor(to * 44100));
    let sum = 0, all = 0, prev = d[a0] || 0;
    for (let i = a0; i < a1; i++) {
      const hp = d[i] - prev;                 // ~+6dB/oct above the corner
      prev = d[i];
      sum += hp * hp;
      all += d[i] * d[i];
    }
    return all ? Math.sqrt(sum / all) : 0;
  };
  // The work window is the first six seconds (WORK_MS is 6.5); the bed alone
  // is what is left once the site has faded.
  return { work: rms(0.5, 6), bed: rms(8, secs), peak,
           bright: bright(0.5, 6), bedBright: bright(8, secs),
           // The two halves of a gesture, for anything that has to *grow*.
           early: rms(0.3, 2.2), late: rms(3.2, 5.6),
           earlyBright: bright(0.3, 2.2), lateBright: bright(3.2, 5.6) };
}
"""


class Files(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(VIEWER / "web"), **k)

    def log_message(self, *a):  # noqa: A002 - quiet
        pass


def serve() -> tuple[str, http.server.ThreadingHTTPServer]:
    """Static files are enough: nothing here reads a board."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Files)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}", server


def goods() -> list[str]:
    """Every good the island can draw, read off `scene.js` rather than listed."""
    text = (VIEWER / "web" / "scene.js").read_text()
    block = text.split("export const GLYPH = {", 1)[1].split("}", 1)[0]
    return [part.split(":")[0].strip() for part in block.split(",") if ":" in part]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verbose", action="store_true", help="print the levels")
    args = ap.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        print("SKIP: playwright is not installed")
        return 0

    chrome = next((p for p in Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")),
                  None)
    base, server = serve()
    problems: list[str] = []
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(executable_path=str(chrome) if chrome else None)
            except Exception as exc:  # noqa: BLE001 - any launch failure is a skip
                print(f"SKIP: no chromium to drive ({exc})".split("\nCall log")[0])
                return 0
            page = browser.new_page()
            page.goto(f"{base}/index.html")

            def take(good, day=0.5, closed=False):
                """Every seed, worst first on whatever the caller is judging."""
                return [page.evaluate(MEASURE, [SECONDS, good, day, closed, seed])
                        for seed in SEEDS]

            controls = take(None)
            nights = take(None, closed=True)
            sunrises = take("@sunrise", day=0.06)
            control, night, sunrise = controls[0], nights[0], sunrises[0]
            rows = [("bed", control), ("bed at night", night)]
            works: dict[str, list[dict]] = {}
            for good in [*goods(), "nothing-has-a-site-called-this"]:
                works[good] = take(good)
                rows.append((good, works[good][0]))

            ratio = control["work"] / control["bed"]
            for name, r in rows:
                if args.verbose:
                    print(f"{name:32} work {r['work']:.4f}  bed {r['bed']:.4f}  "
                          f"peak {r['peak'] * MASTER:.3f}  bright {r['bright']:.3f}"
                          f" / {r['bedBright']:.3f}")
                if r["peak"] * MASTER >= 0.99:
                    problems.append(f"{name} clips at the master gain "
                                    f"({r['peak'] * MASTER:.2f})")
                if r.get("bright", 0) > 4 * max(r.get("bedBright", 0), 1e-6):
                    problems.append(f"{name} is harsh next to the bed it sits in "
                                    f"(bright {r['bright']:.2f} against {r['bedBright']:.2f})")
                if r["bed"] < 0.004:
                    problems.append(f"{name}: the bed is silent ({r['bed']:.4f})")
            if control["bed"] > 0.08:
                problems.append(f"the bed is loud for a background ({control['bed']:.3f})")
            if min(n["bed"] for n in nights) <= 0.004:
                problems.append("the sea stopped at night")
            # Night is a hearth: the fire is the loudest thing left, so the bed
            # is *louder* than by day and *darker* than by day. Asked for in
            # those words, and this is what those words mean in numbers.
            if min(n["bed"] for n in nights) <= max(c["bed"] for c in controls) * 1.1:
                problems.append(f"night is not a fireplace: it is no louder than "
                                f"the day ({night['bed']:.4f} against {control['bed']:.4f})")
            if max(n["bedBright"] for n in nights) >= min(c["bedBright"] for c in controls):
                problems.append(f"night is not a fireplace: it is no warmer than the "
                                f"day (bright {night['bedBright']:.3f} against "
                                f"{control['bedBright']:.3f})")
            # The sunrise has to *rise*: louder at its middle than at its start,
            # and brighter with it, which is the thing that reads as light
            # rather than as volume.
            # Measured against itself, not against another hour: the open
            # fires at dawn, when the bed is quiet anyway, so comparing it to
            # midday would credit the sunrise for the hour it happens in.
            if args.verbose:
                print(f"{'sunrise':32} early {sunrise['early']:.4f} -> "
                      f"late {sunrise['late']:.4f}   bright "
                      f"{sunrise['earlyBright']:.3f} -> {sunrise['lateBright']:.3f}"
                      f"   (bed after {sunrise['bed']:.4f})")
            if min(s["late"] / s["early"] for s in sunrises) <= 1.3:
                problems.append(f"the sun did not come up: no swell "
                                f"({sunrise['early']:.4f} to {sunrise['late']:.4f})")
            if min(s["work"] / s["bed"] for s in sunrises) <= 1.4:
                problems.append(f"the sunrise is not heard over the bed it rises into "
                                f"({sunrise['work']:.4f} against {sunrise['bed']:.4f})")
            # Brightening is what reads as light rather than as volume: the
            # lowpass opens across the swell, so the second half must carry
            # more of its energy up top than the first.
            if min(s["lateBright"] / s["earlyBright"] for s in sunrises) <= 1.15:
                problems.append(f"the sunrise grows without brightening "
                                f"({sunrise['earlyBright']:.3f} to "
                                f"{sunrise['lateBright']:.3f})")
            # And a ceiling on it, under the same rule the sites live by. The
            # shine is the brightest thing on this island by design, which is
            # exactly why it needs a bound: bright is not the same as sharp,
            # and the quarry already proved how easily one becomes the other.
            worst = max(s["bright"] / max(s["bedBright"], 1e-6) for s in sunrises)
            if worst > 2.5:
                problems.append(f"the sunrise is piercing rather than bright "
                                f"(x{worst:.2f} the bed's brightness)")
            for name, runs in works.items():
                heards = [(r["work"] / r["bed"])
                          / (c["work"] / c["bed"])
                          for r, c in zip(runs, controls)]
                worst = min(heards)
                if args.verbose:
                    spread = " ".join(f"{h:.2f}" for h in heards)
                    print(f"{name:32} x{worst:.2f} over the bed   (seeds: {spread})")
                if worst < FLOOR:
                    problems.append(f"{name} at work cannot be heard over the bed "
                                    f"(x{worst:.2f} on its worst seed, floor x{FLOOR})")
            voices = page.evaluate(VOICE_PITCH)
            bell = voices.get("bell", {}).get("pitch", 0)
            for name, v in sorted(voices.items(), key=lambda kv: -kv[1]["pitch"]):
                if args.verbose:
                    print(f"{('voice: ' + name):32} ~{v['pitch']:.0f} Hz  "
                          f"peak {v['peak'] * MASTER:.3f}")
                if v["peak"] * MASTER >= 0.99:
                    problems.append(f"the {name} voice clips ({v['peak'] * MASTER:.2f})")
            if not bell:
                problems.append("the bell voice made no sound at all")
            for name, v in voices.items():
                if name != "bell" and v["pitch"] > bell:
                    problems.append(
                        f"the {name} voice rings above the bell "
                        f"(~{v['pitch']:.0f}Hz against ~{bell:.0f}Hz): the bell is the "
                        f"one voice this island lets sit over everything")
            browser.close()
    finally:
        server.shutdown()

    for line in problems:
        print(f"FAIL: {line}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
