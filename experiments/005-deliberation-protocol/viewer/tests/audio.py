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

MEASURE = """
async ([secs, good, day, closed]) => {
  const { Ambience } = await import('./island-ambience.js');
  const ctx = new OfflineAudioContext(1, 44100 * secs, 44100);
  let fake = 0;
  Object.defineProperty(ctx, 'currentTime', { get: () => fake });
  const a = new Ambience(ctx, ctx.destination);
  a.start();
  a.setDay(day, closed);
  if (good) a.working(good);
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
  // The work window is the first six seconds (WORK_MS is 6.5); the bed alone
  // is what is left once the site has faded.
  return { work: rms(0.5, 6), bed: rms(8, secs), peak };
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

            control = page.evaluate(MEASURE, [SECONDS, None, 0.5, False])
            night = page.evaluate(MEASURE, [SECONDS, None, 0.5, True])
            rows = [("bed", control), ("bed at night", night)]
            for good in [*goods(), "nothing-has-a-site-called-this"]:
                rows.append((good, page.evaluate(MEASURE, [SECONDS, good, 0.5, False])))

            ratio = control["work"] / control["bed"]
            for name, r in rows:
                if args.verbose:
                    print(f"{name:32} work {r['work']:.4f}  bed {r['bed']:.4f}  "
                          f"peak {r['peak'] * MASTER:.3f}")
                if r["peak"] * MASTER >= 0.99:
                    problems.append(f"{name} clips at the master gain "
                                    f"({r['peak'] * MASTER:.2f})")
                if r["bed"] < 0.004:
                    problems.append(f"{name}: the bed is silent ({r['bed']:.4f})")
            if control["bed"] > 0.08:
                problems.append(f"the bed is loud for a background ({control['bed']:.3f})")
            if night["bed"] <= 0.004:
                problems.append("the sea stopped at night")
            for name, r in rows[2:]:
                heard = (r["work"] / r["bed"]) / ratio
                if args.verbose:
                    print(f"{name:32} x{heard:.2f} over the bed")
                if heard < FLOOR:
                    problems.append(f"{name} at work cannot be heard over the bed "
                                    f"(x{heard:.2f}, floor x{FLOOR})")
            browser.close()
    finally:
        server.shutdown()

    for line in problems:
        print(f"FAIL: {line}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
