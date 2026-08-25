"""Render the island in a real browser, and say what came back.

    python viewer/tests/render.py                  # check, and write PNGs
    python viewer/tests/render.py --out /tmp/after # somewhere else

`scene.js` had no test of any kind, which is how a page breaks quietly: the
suites all pass, the SVG renders half of nothing, and the first person to find
out is somebody watching a replay. This is the cheapest thing that would have
caught that -- load the page the way a spectator does, and assert what is on it.

It is deliberately **not** a pixel-diff. The PNGs are for a person to look at;
what is asserted is structural and would survive any amount of restyling:

* the page raises nothing -- no console error, no unhandled rejection;
* one hut per trader, one shelf cell per good per trader;
* the scenery lands nowhere near the cards (the bug this exists to hold shut);
* it survives a board with more than two traders, which no saved replay has,
  so the ring layout would otherwise be drawn for the first time in front of
  whoever first plays a four-hander.

Skips rather than fails when Playwright or Chromium is absent: this must not
become something a checkout has to install before the free suites run.
"""

from __future__ import annotations

import argparse
import contextlib
import http.server
import json
import socket
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE.parent
REPO = VIEWER.parents[2]
REPLAYS = REPO / "games" / "replays"

#: Where the replay is stepped to. Chosen for what is on screen, not evenly:
#: the open shows an empty island, the middle shows production and an open
#: offer, and the end shows the bell's aftermath.
STOPS = [("open", 0.0), ("mid", 0.55), ("late", 0.78), ("end", 1.0)]


def serve(replays: Path) -> tuple[str, http.server.ThreadingHTTPServer]:
    """The viewer's own server, on a port the OS picks.

    The page's own server, not a static one: `api/boards` is a route, and a
    harness that served the files some other way would be checking a page
    nobody visits.
    """
    sys.path.insert(0, str(VIEWER))
    import serve as viewer_serve  # noqa: PLC0415 - after the path insert

    viewer_serve.ROOTS["replays"] = replays
    viewer_serve._listing = (0.0, [])  # noqa: SLF001 - the module's own cache
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = viewer_serve.Server(("127.0.0.1", port), viewer_serve.Handler)
    server.upstream = None
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}", server


def board_url(base: str, stem: str) -> str:
    return (f"{base}/?board=replays/board-{stem}.json"
            f"&reveal=replays/reveal-{stem}.json")


def synthetic(n: int, goods: list[str]) -> list[dict]:
    """A board with `n` traders, so the ring layout is drawn at least once.

    Every replay on disk is two traders. `layout(n)` has a whole other branch
    for more, and nothing had ever rendered it.
    """
    names = [f"T{i + 1}" for i in range(n)]
    rows = [{"seq": 1, "author": "manager", "body":
             f"Schedule for this round. {n} traders: {', '.join(names)}. "
             "1 episodes, 60s each."}]
    rows.append({"seq": 2, "author": "manager",
                 "body": "episode 1 of 1 is open; the bell is at 00:00:00Z (60s)."})
    for i, name in enumerate(names):
        made = {g: round(0.4 + 0.2 * ((i + j) % 3), 4) for j, g in enumerate(goods)}
        # A receipt is a Python repr on the real board -- single quotes, which is
        # what `reducer.bundle` parses. `json.dumps` here would be a fixture that
        # cannot happen, and it would test nothing.
        body = ", ".join(f"'{g}': {q}" for g, q in made.items())
        rows.append({"seq": 3 + i, "author": "manager",
                     "body": f"@{name} produced {{{body}}}; 0.0 labour unspent"})
    return rows


def check(page, expect_traders: int, expect_goods: int, where: str) -> list[str]:
    """Structure, not pixels. Anything here failing is a page a person cannot read."""
    bad = []
    counts = page.evaluate("""() => ({
      huts: document.querySelectorAll('.hut').length,
      cells: document.querySelectorAll('.hut .cell').length,
      land: document.querySelectorAll('.land').length,
      palms: [...document.querySelectorAll('.palm')].map(p => {
        const b = p.getBBox(); return [b.x, b.y, b.width, b.height];
      }),
      cards: [...document.querySelectorAll('.hut .card-bg')].map(c => {
        const b = c.getBoundingClientRect(); return [b.x, b.y, b.width, b.height];
      }),
      palmBoxes: [...document.querySelectorAll('.palm')].map(p => {
        const b = p.getBoundingClientRect(); return [b.x, b.y, b.width, b.height];
      }),
    })""")
    if counts["huts"] != expect_traders:
        bad.append(f"{where}: {counts['huts']} huts, expected {expect_traders}")
    want_cells = expect_traders * expect_goods
    if counts["cells"] != want_cells:
        bad.append(f"{where}: {counts['cells']} shelf cells, expected {want_cells}")
    if counts["land"] != 1:
        bad.append(f"{where}: {counts['land']} land paths, expected 1")
    # The bug this file exists to hold shut: scenery drawn on top of the only
    # part of the picture carrying information.
    for pb in counts["palmBoxes"]:
        for cb in counts["cards"]:
            if (pb[0] < cb[0] + cb[2] and pb[0] + pb[2] > cb[0]
                    and pb[1] < cb[1] + cb[3] and pb[1] + pb[3] > cb[1]):
                bad.append(f"{where}: a palm overlaps a trader card "
                           f"(palm {[round(v) for v in pb]}, card {[round(v) for v in cb]})")
    return bad


def motion(page, where: str) -> list[str]:
    """That the event animations actually run, which a screenshot cannot say.

    Production had no picture at all before this -- `state.made` sat in the
    reducer and nothing drew it -- so "the parcels still fly" is not enough to
    check. Play the events directly and watch for the nodes they create.
    """
    bad = []
    seen = page.evaluate("""async () => {
      const scene = window.__probe;
      const found = {};
      const watch = (cls) => document.querySelectorAll('.flights ' + cls).length;
      scene.play({ kind: 'produced', trader: scene.traders[0],
                   made: { [scene.goods[0]]: 1.25 }, unspent: 0 });
      await new Promise(r => setTimeout(r, 120));
      found.sheaf = watch('.sheaf');
      found.pop = watch('.pop');
      scene.play({ kind: 'settled', pid: 'p1', maker: scene.traders[0],
                   taker: scene.traders[1] || scene.traders[0],
                   give: { [scene.goods[0]]: .5 }, want: { [scene.goods[1]]: .25 } });
      await new Promise(r => setTimeout(r, 260));
      found.parcel = watch('.parcel');
      scene.play({ kind: 'bell', episode: 1, lapsed: 0 });
      await new Promise(r => setTimeout(r, 120));
      found.dusk = document.getElementById('island').classList.contains('dusk');
      found.night = Number(document.querySelector('.night').getAnimations().length);
      return found;
    }""")
    for key, want in (("sheaf", 1), ("pop", 1), ("parcel", 2)):
        if seen[key] < want:
            bad.append(f"{where}: {seen[key]} .{key} node(s) during play, expected >= {want}")
    if not seen["dusk"] or not seen["night"]:
        bad.append(f"{where}: the bell did not bring dusk ({seen})")
    return bad


def run(out: Path, headed: bool = False) -> int:
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError:
        print("SKIP: playwright is not installed")
        return 0
    chrome = next((p for p in Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome")),
                  None)
    boards = sorted(REPLAYS.glob("board-*.json"))
    if not boards:
        print(f"SKIP: no replays under {REPLAYS}")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    base, server = serve(REPLAYS)
    problems: list[str] = []
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    executable_path=str(chrome) if chrome else None, headless=not headed)
            except Exception as exc:  # noqa: BLE001 - any launch failure is a skip
                print(f"SKIP: no chromium to drive ({exc})".split("\nCall log")[0])
                return 0
            problems += replay(browser, base, boards[0], out)
            problems += ring(browser, base, out)
            browser.close()
    finally:
        server.shutdown()

    for line in problems:
        print(f"FAIL {line}")
    print(f"\n{len(problems)} problem(s); PNGs in {out}")
    return 1 if problems else 0


def replay(browser, base: str, board: Path, out: Path) -> list[str]:
    stem = board.name[len("board-"):-len(".json")]
    reveal = json.loads((REPLAYS / f"reveal-{stem}.json").read_text())
    goods = len(reveal["goods"])
    traders = len(reveal["traders"])
    bad: list[str] = []
    for label, motion in (("", False), ("still", True)):
        page = browser.new_page(viewport={"width": 1500, "height": 1000},
                                reduced_motion="reduce" if motion else "no-preference")
        errs: list[str] = []
        page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
                if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.goto(board_url(base, stem))
        page.wait_for_selector(".hut", timeout=10_000)
        page.wait_for_timeout(1800)
        total = int(page.eval_on_selector("#scrub", "e => Number(e.max)"))
        for name, at in STOPS:
            page.evaluate(
                "i => { const s = document.getElementById('scrub');"
                " s.value = String(i); s.dispatchEvent(new Event('input')); }",
                round(total * at))
            page.wait_for_timeout(900)
            bad += check(page, traders, goods, f"{stem} @{name}{' still' if motion else ''}")
            suffix = f"-{label}" if label else ""
            page.locator(".stage").screenshot(path=str(out / f"{stem}-{name}{suffix}.png"))
        bad += [f"{stem}{' still' if motion else ''}: {e}" for e in errs]
        page.close()
    return bad


def ring(browser, base: str, out: Path) -> list[str]:
    """Four traders, which no saved replay has -- and where the events are driven.

    Doubles as the motion check: a scene here is reachable from the page, so
    `motion()` can play a receipt at it and watch what appears.
    """
    goods = ["bread", "cloth", "iron", "salt"]
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    page.evaluate("""async ({rows}) => {
      const { reduce } = await import('./reducer.js');
      const { Scene } = await import('./scene.js');
      window.__probe = new Scene(document.getElementById('island'),
                                 reduce(rows, { manager: 'manager' }), null);
      const t = reduce(rows, { manager: 'manager' });
      window.__probe.draw(t.final, t);
    }""", {"rows": synthetic(4, goods)})
    page.wait_for_timeout(700)
    bad = check(page, 4, len(goods), "ring/4")
    page.locator(".stage").screenshot(path=str(out / "ring-4.png"))
    bad += motion(page, "ring/4")
    bad += [f"ring/4: {e}" for e in errs]
    page.close()
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("/tmp/island-shots"))
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args(argv)
    with contextlib.suppress(KeyboardInterrupt):
        return run(args.out.resolve(), args.headed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
