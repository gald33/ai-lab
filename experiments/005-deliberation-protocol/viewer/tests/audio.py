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
import base64
import http.server
import socket
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent

#: **Nothing here multiplies by the master gain any more.** It used to, as a
#: stand-in for the real chain, and the stand-in was the bug: the page's gain
#: was 0.32 under a compressor squashing everything above -14dB at 8:1, this
#: file modelled only the 0.32, and nobody measured the pair. Renders now go
#: through `outputChain()` itself, so every number below is what leaves the
#: page.
#:
#: The band the bed has to leave the page in, **anchored to two configurations
#: a listener actually judged** rather than to anybody's idea of what a bed
#: should measure:
#:
#: | heard | bed RMS out |
#: |---|---|
#: | `BED` 0.5, reported as "I can't hear any of it" | 0.009 |
#: | `BED` 1.15, reported as "now I do hear everything" | 0.021 |
#:
#: The floor sits between them. That is the whole of its justification, and it
#: is a better one than a round number: every threshold in this file that was
#: chosen by taste has been wrong at least once, and these two numbers are the
#: only ones here that a pair of ears has ruled on directly.
#:
#: The ceiling is still the old rule -- a spectator who notices the sea rather
#: than the island is hearing too much of it -- and has never been tested by
#: anybody's ear, which is worth knowing when it starts failing.
OUTPUT = (0.015, 0.09)

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
  const { VOICES, outputChain } = await import('./island-sound.js');
  const out = {};
  for (const name of Object.keys(VOICES)) {
    const ctx = new OfflineAudioContext(1, 44100 * 3, 44100);
    const chain = outputChain(ctx);
    VOICES[name](ctx, chain.accent, 0);
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

#: The same render, handed back as a WAV instead of as numbers.
#:
#: **This is the check that has actually caught things.** Every complaint that
#: mattered -- the sites inaudible, the quarry harsh, the box in the air too
#: high, the whole world too quiet -- was heard by a person first and measured
#: afterwards. So the harness that lets a person hear it belongs in the
#: repository beside the one that measures it, rather than being rebuilt from
#: memory each time somebody says "it sounds wrong".
#:
#: **No longer boosted.** These went out at 3.2x while the page's own chain was
#: 20dB down, so the files sounded right and the page did not -- the boost was
#: hiding the very thing it was meant to reveal. A WAV from here is now exactly
#: what the page plays.
LOUD = 1.0

WAV = """
async ([secs, good, day, closed, seed, master, loud]) => {
  const render = window.__islandRender;
  const d = await render([secs, good, day, closed, seed], true);
  const n = d.length, buf = new ArrayBuffer(44 + n * 2), v = new DataView(buf);
  const put = (o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  put(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); put(8, 'WAVEfmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, 44100, true); v.setUint32(28, 88200, true);
  v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  put(36, 'data'); v.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) {
    const x = Math.max(-1, Math.min(1, d[i] * master * loud));
    v.setInt16(44 + i * 2, x * 32767, true);
  }
  let s = ''; const b = new Uint8Array(buf);
  for (let i = 0; i < b.length; i += 8192) s += String.fromCharCode(...b.subarray(i, i + 8192));
  return btoa(s);
}
"""

RENDER = """
() => { window.__islandRender = async ([secs, good, day, closed, seed], raw) => {
  const { Ambience } = await import('./island-ambience.js');
  const { outputChain } = await import('./island-sound.js');
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
  //: Through the page's own master gain and limiter, not straight at the
  //: destination. Measuring the island before that chain is measuring
  //: something no listener hears -- which is exactly how a page nobody could
  //: hear passed every check in this file.
  const chain = outputChain(ctx);
  const a = new Ambience(ctx, chain.master, { rng });
  a.start();
  a.setDay(day, closed);
  if (good === '@sunrise') a.sunrise(); else if (good) a.working(good);
  for (let t = 0; t < secs; t += 0.4) { fake = t; a.pump(); }
  fake = 0;
  const d = (await ctx.startRendering()).getChannelData(0);
  if (raw) return Array.from(d);
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
}; }
"""

MEASURE = "async (args) => window.__islandRender(args, false)"


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
    ap.add_argument("--wav", metavar="DIR", type=Path,
                    help="also write the bed, the night, the sunrise and each "
                         "site at work as WAVs, to listen to")
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
            page.evaluate(RENDER)

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
                          f"peak {r['peak']:.3f}  bright {r['bright']:.3f}"
                          f" / {r['bedBright']:.3f}")
                if r["peak"] >= 0.99:
                    problems.append(f"{name} clips on the way out ({r['peak']:.2f})")
                if r.get("bright", 0) > 4 * max(r.get("bedBright", 0), 1e-6):
                    problems.append(f"{name} is harsh next to the bed it sits in "
                                    f"(bright {r['bright']:.2f} against {r['bedBright']:.2f})")
                if r["bed"] < 0.004:
                    problems.append(f"{name}: the bed is silent ({r['bed']:.4f})")
            # The bed lives in a band, and both walls were found by ear.
            #
            # The floor: at BED = 0.5 the whole world peaked at 0.051 after the
            # master gain while one settlement chimed at 0.107 -- reported as
            # the day, the night and the sunrise all being barely there, and
            # nothing here could see it, because every check until now compared
            # the island to itself. The ceiling is the older rule: a spectator
            # who notices the sea rather than the island is hearing too much
            # of it.
            day = max(c["bed"] for c in controls)
            quiet = min(c["bed"] for c in controls)
            if day > OUTPUT[1]:
                problems.append(f"the bed is loud for a background ({day:.3f})")
            if quiet < OUTPUT[0]:
                problems.append(f"the bed is barely there ({quiet:.3f}, floor "
                                f"{OUTPUT[0]}): this is what leaves the page, and a "
                                f"listener has to be able to hear it")
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
                          f"peak {v['peak']:.3f}")
                if v["peak"] >= 0.99:
                    problems.append(f"the {name} voice clips ({v['peak']:.2f})")
            if not bell:
                problems.append("the bell voice made no sound at all")
            # And the same rule stated against the accents rather than in the
            # abstract: the world may be quieter than the loudest voice on it,
            # but not a fraction of it. This is the comparison whose absence
            # let the island sit at a third of one chime.
            loudest = max(v["peak"] for v in voices.values())
            floor = max(c["peak"] for c in controls)
            if args.verbose:
                print(f"{'bed against the loudest voice':32} "
                      f"{floor:.3f} against {loudest:.3f}")
            if floor < loudest * 0.6:
                problems.append(f"the bed is dwarfed by the accents over it "
                                f"(the world peaks at {floor:.3f}, one voice at "
                                f"{loudest:.3f})")
            for name, v in voices.items():
                if name != "bell" and v["pitch"] > bell:
                    problems.append(
                        f"the {name} voice rings above the bell "
                        f"(~{v['pitch']:.0f}Hz against ~{bell:.0f}Hz): the bell is the "
                        f"one voice this island lets sit over everything")
            if args.wav:
                args.wav.mkdir(parents=True, exist_ok=True)
                takes = [("bed-day", None, 0.5, False, 12),
                         ("bed-night", None, 0.5, True, 12),
                         ("sunrise", "@sunrise", 0.06, False, 12)]
                takes += [(f"site-{g}", g, 0.5, False, 10) for g in goods()]
                for name, good, day_, closed_, secs in takes:
                    raw = page.evaluate(WAV, [secs, good, day_, closed_, SEEDS[0],
                                              1.0, LOUD])
                    out = args.wav / f"{name}.wav"
                    out.write_bytes(base64.b64decode(raw))
                    print(f"wrote {out}")
            browser.close()
    finally:
        server.shutdown()

    for line in problems:
        print(f"FAIL: {line}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
