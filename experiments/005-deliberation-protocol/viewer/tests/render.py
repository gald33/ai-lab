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
STOPS = [("open", 0.0), ("mid", 0.55), ("late", 0.78), ("dusk", 0.92), ("end", 1.0)]


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


#: A refusal reason from a real board. The island must not print it.
REASON = "you have 0.0000 bread uncommitted, not 0.1500"


def motion(page, where: str) -> list[str]:
    """That the event animations run, and that they say the right things.

    A screenshot cannot see any of this. Production had no picture at all
    before -- `state.made` sat in the reducer and nothing drew it -- and the
    island used to print the manager's refusal text across the sand, which is
    the regression the `no reason text` assertion holds shut.

    Driven the way `index.html:paint` drives it: `draw()` then `play()`, in that
    order, because night is a state `draw()` sets and only the passage is played.
    """
    bad = []
    seen = page.evaluate("""async (reason) => {
      const scene = window.__probe, t = window.__timeline;
      const nap = (ms) => new Promise(r => setTimeout(r, ms));
      const island = document.getElementById('island');
      const watch = (cls) => document.querySelectorAll('.flights ' + cls).length;
      const found = {};

      scene.play({ kind: 'produced', trader: scene.traders[0],
                   made: { [scene.goods[0]]: 1.25 }, unspent: 0 });
      await nap(150);
      found.sheaf = watch('.sheaf');
      found.popOnProduce = watch('.pop');

      scene.play({ kind: 'refused', trader: scene.traders[0], reason });
      await nap(150);
      found.bad = watch('.pop.bad');
      found.cross = watch('.pop-cross');
      found.svgText = [...island.querySelectorAll('text')].map(n => n.textContent).join(' ');
      found.titled = [...island.querySelectorAll('.pop.bad title')]
        .some(n => n.textContent === reason);

      scene.play({ kind: 'said', author: scene.traders[0], attempt: false });
      await nap(150);
      found.talk = watch('.pop.talk');
      scene.play({ kind: 'said', author: scene.traders[0], attempt: true });
      await nap(150);
      found.talkAfterAttempt = watch('.pop.talk');

      scene.play({ kind: 'settled', pid: 'p1', maker: scene.traders[0],
                   taker: scene.traders[1] || scene.traders[0],
                   give: { [scene.goods[0]]: .5 }, want: { [scene.goods[1]]: .25 } });
      await nap(300);
      found.parcel = watch('.parcel');

      // The day ends. `draw()` carries the state; `play()` carries the passage.
      const sunAt = () => scene.sunNode.getBoundingClientRect().top;
      found.sunBefore = sunAt();
      scene.draw({ ...t.final, phase: 'closed' }, t);
      scene.play({ kind: 'bell', episode: 1, lapsed: 0 });
      await nap(900);
      found.closed = island.classList.contains('closed');
      found.sunSetting = sunAt() > found.sunBefore;
      found.nightOpacity = Number(getComputedStyle(
        document.querySelector('.night')).opacity);

      // And a new episode is a new day.
      scene.draw({ ...t.final, phase: 'market' }, t);
      scene.play({ kind: 'open', episode: 2, of: 3 });
      await nap(300);
      found.reopened = !island.classList.contains('closed');
      return found;
    }""", REASON)

    for key, want in (("sheaf", 1), ("parcel", 2), ("bad", 1), ("cross", 1), ("talk", 1)):
        if seen[key] < want:
            bad.append(f"{where}: {seen[key]} .{key} node(s) during play, expected >= {want}")
    # The whole point of the symbols: the island shows *that* it refused, not
    # the sentence the manager wrote.
    for fragment in ("uncommitted", "0.1500", "you have"):
        if fragment in seen["svgText"]:
            bad.append(f"{where}: the refusal reason is printed on the island "
                       f"({fragment!r} found in its text)")
    if not seen["titled"]:
        bad.append(f"{where}: the refusal badge lost the reason as its title")
    if seen["popOnProduce"]:
        bad.append(f"{where}: production still captions itself "
                   f"({seen['popOnProduce']} bubble(s)); the rising goods say it")
    if seen["talkAfterAttempt"] != seen["talk"]:
        bad.append(f"{where}: an attempt drew a bubble; its receipt is the tell")
    if not seen["closed"] or seen["nightOpacity"] <= 0.05:
        bad.append(f"{where}: the bell did not bring night ({seen})")
    if not seen["sunSetting"]:
        bad.append(f"{where}: the sun did not go down at the bell ({seen})")
    if not seen["reopened"]:
        bad.append(f"{where}: a new episode did not bring the day back")
    return bad


def production(page, where: str) -> list[str]:
    """That the goods cause the shelf, rather than racing it.

    The regression: `paint()` calls `draw()` then `play()`, `draw()` grew the
    bar on a 0.55s CSS transition, and a sheaf flew for 1.5s. So the shelf had
    finished filling a second before anything landed on it, and nothing on
    screen connected the flying glyph to the bar that grew.
    """
    seen = page.evaluate("""async () => {
      const scene = window.__probe, t = window.__timeline;
      const nap = (ms) => new Promise(r => setTimeout(r, ms));
      const who = scene.traders[0], good = scene.goods[0];
      const bar = () => {
        const el = scene.bars[who][good].bar;
        const m = /scaleY\(([\d.]+)\)/.exec(el.style.transform || '');
        return m ? Number(m[1]) : null;
      };
      // The computed value, not the attribute: the wheel is animated through
      // the Web Animations API, which overrides the presentation attribute
      // without ever rewriting it.
      const wheel = () => getComputedStyle(scene.labels[who].wheel).strokeDasharray;

      // Empty the shelf, then fill it the way a frame does: draw the new state
      // first, then play the event that explains it.
      const bare = { ...t.final, stocks: { ...t.final.stocks, [who]: {} },
                     labour: { ...t.final.labour, [who]: null } };
      scene.draw(bare, t); await nap(650);
      const before = bar();

      const made = { [good]: 1.4 };
      const after = { ...t.final,
                      stocks: { ...t.final.stocks, [who]: made },
                      labour: { ...t.final.labour, [who]: 0 } };
      scene.draw(after, t);
      scene.play({ kind: 'produced', trader: who, made, unspent: 0 });

      await nap(120);
      const early = bar();
      const working = document.querySelector(`.hut[data-trader="${who}"]`)
                        .classList.contains('working');

      // A live board repaints while the goods are still in the air. The shelf
      // has to stay held through that, or the next poll fills it early and the
      // arriving sheaf lands on a bar that already grew.
      await nap(300);
      scene.draw(after, t);
      await nap(200);
      const redrawn = bar();
      const flying = document.querySelectorAll('.flights .sheaf').length;

      // Past where the old CSS transition would have finished (0.5s). If the
      // wheel is already at its final value here, nothing is animating it and
      // the labour went in one silent step.
      const wheelLate = wheel();
      await nap(3200);
      const settled = bar();
      const wheelDone = wheel();
      return { before, early, redrawn, settled, flying, working,
               wheelLate, wheelDone };
    }""")
    bad = []
    if seen["settled"] is None or seen["settled"] <= (seen["before"] or 0) + 0.05:
        bad.append(f"{where}: the shelf never took the goods ({seen})")
    # The one that matters: partway through the flight the bar is still low.
    if seen["early"] is None or seen["early"] > (seen["settled"] or 1) * 0.5:
        bad.append(f"{where}: the shelf filled before the goods landed "
                   f"(bar was {seen['early']} of {seen['settled']} while still "
                   f"in flight) — {seen}")
    if seen["redrawn"] is None or seen["redrawn"] > (seen["settled"] or 1) * 0.5:
        bad.append(f"{where}: a repaint during the flight filled the shelf early "
                   f"(bar {seen['redrawn']} of {seen['settled']}) — {seen}")
    if not seen["flying"]:
        bad.append(f"{where}: nothing was in flight during production ({seen})")
    if not seen["working"]:
        bad.append(f"{where}: the hut did not work before its goods appeared")
    if seen["wheelLate"] == seen["wheelDone"]:
        bad.append(f"{where}: the labour went in one step — the wheel had already "
                   f"finished at {seen['wheelLate']!r} while goods were still "
                   "in flight")
    return bad


def palms(page, where: str) -> list[str]:
    """The trunk stands still while the crown moves.

    The sway used to be on the whole palm group, so the trunk and its shadow
    slid about with the fronds -- a tree walking rather than a tree in wind.
    Sampled over a second of animation, because at any one instant both are
    simply somewhere.
    """
    spread = page.evaluate("""async () => {
      const nap = (ms) => new Promise(r => setTimeout(r, ms));
      const of = (sel) => [...document.querySelectorAll(sel)]
        .map(n => n.getBoundingClientRect().left);
      const trunks = [], crowns = [];
      for (let i = 0; i < 12; i++) {
        trunks.push(of('.palm .trunk')); crowns.push(of('.palm .crown'));
        await nap(90);
      }
      const range = (rows) => rows[0].map((_, c) => {
        const col = rows.map(r => r[c]);
        return Math.max(...col) - Math.min(...col);
      });
      return { trunk: Math.max(...range(trunks)), crown: Math.max(...range(crowns)) };
    }""")
    bad = []
    if spread["trunk"] > 0.6:
        bad.append(f"{where}: the trunk moves with the fronds "
                   f"(drifts {spread['trunk']:.2f}px); only the leaves should")
    if spread["crown"] < 0.6:
        bad.append(f"{where}: the crown does not stir ({spread['crown']:.2f}px)")
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
            page.screenshot(path=str(out / f"{stem}-{name}{suffix}.png"))
        bad += [f"{stem}{' still' if motion else ''}: {e}" for e in errs]
        page.close()
    return bad


def ring(browser, base: str, out: Path) -> list[str]:
    """Four traders over five goods, neither of which any saved replay has --
    and where the events are driven.

    Doubles as the motion check: a scene here is reachable from the page, so
    `motion()` can play a receipt at it and watch what appears.
    """
    # Five, because the island has five now and no saved replay does. The
    # fifth slot is also where the palette used to draw a good in exactly the
    # colour of the utility bar beneath it.
    goods = ["bread", "cloth", "iron", "salt", "fish"]
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
      const t = reduce(rows, { manager: 'manager' });
      window.__timeline = t;
      window.__probe = new Scene(document.getElementById('island'), t, null);
      window.__probe.draw(t.final, t);
    }""", {"rows": synthetic(4, goods)})
    page.wait_for_timeout(700)
    bad = check(page, 4, len(goods), "ring/4")
    page.screenshot(path=str(out / "ring-4.png"))
    bad += production(page, "ring/4")
    bad += palms(page, "ring/4")
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
