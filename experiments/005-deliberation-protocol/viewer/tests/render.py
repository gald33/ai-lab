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


#: The server `serve()` last started, so a check can point it at a fake
#: upstream. Kept here rather than threaded through every call, because only
#: the live check has ever needed it.
_SERVERS: dict[str, object] = {}


def server_for(base: str):
    return _SERVERS[base]


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
    base = f"http://127.0.0.1:{port}"
    _SERVERS[base] = server
    return base, server


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
      // Visible, not merely present: hiding the drawn world leaves its nodes
      // in the DOM, and 'is there an island path' is not the question.
      land: [...document.querySelectorAll('.land')]
        .filter(n => n.getBoundingClientRect().width > 0).length,
      palms: [...document.querySelectorAll('.palm')].map(p => {
        const b = p.getBBox(); return [b.x, b.y, b.width, b.height];
      }),
      cards: [...document.querySelectorAll('.hut .card-bg')].map(c => {
        const b = c.getBoundingClientRect(); return [b.x, b.y, b.width, b.height];
      }),
      palmBoxes: [...document.querySelectorAll('.palm')].map(p => {
        const b = p.getBoundingClientRect(); return [b.x, b.y, b.width, b.height];
      }),
      // Whether there is a model under the page at all. A browser with no
      // WebGL keeps the drawn island, and both have to be checkable.
      modelled: document.querySelector('.app').classList.contains('has-3d'),
      palmCount: [...document.querySelectorAll('.palm')]
        .filter(p => p.getBoundingClientRect().width > 0).length,
    })""")
    if counts["huts"] != expect_traders:
        bad.append(f"{where}: {counts['huts']} huts, expected {expect_traders}")
    want_cells = expect_traders * expect_goods
    if counts["cells"] != want_cells:
        bad.append(f"{where}: {counts['cells']} shelf cells, expected {want_cells}")
    if counts["modelled"]:
        # The island is a model now, and its scenery is in it -- so the drawn
        # world must be gone rather than merely covered up, and the palm-vs-card
        # check below has nothing left to measure. What replaces it is
        # `painted()`: that the model actually drew.
        for ghost, n in (("land", counts["land"]), ("palms", counts["palmCount"])):
            if n:
                bad.append(f"{where}: the model is up and the drawn {ghost} is still "
                           f"there ({n}); two islands on one page")
    else:
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
    bad += empty_slots(page, where)
    return bad


def empty_slots(page, where: str) -> list[str]:
    """A good a trader holds none of has to say so, in words.

    Under Cobb-Douglas one zero is the whole episode, so this is the single
    most decision-relevant thing on a card -- and it was rendered as a blank
    where every other slot had a number, which reads as "not applicable"
    rather than "none". Game 002's episode 2 is exactly that state: T1 holds
    no iron, its utility is 0.000, and nothing on the card said why.

    Checked wherever the page happens to be, so it costs nothing when no slot
    is empty and speaks up at the stop where one is.
    """
    slots = page.evaluate("""() => [...document.querySelectorAll('.hut .cell')]
      .filter(c => c.classList.contains('empty'))
      .map(c => {
        const q = c.querySelector('.qty');
        const zero = c.querySelector('.bar-zero');
        return { good: c.dataset.good, text: q ? q.textContent : null,
                 flagged: q ? q.classList.contains('none') : false,
                 mark: zero ? getComputedStyle(zero).opacity : null };
      })""")
    bad = []
    for s in slots:
        if not (s["text"] or "").strip():
            bad.append(f"{where}: an empty {s['good']} slot shows no quantity at all")
        elif not s["flagged"]:
            bad.append(f"{where}: an empty {s['good']} slot reads {s['text']!r} "
                       f"but is not marked as none")
        if s["mark"] is not None and float(s["mark"]) < 0.5:
            bad.append(f"{where}: an empty {s['good']} slot's zero mark is "
                       f"invisible (opacity {s['mark']})")
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
      // This drives the *drawn* scene in isolation -- the fallback a browser
      // with no WebGL gets -- so the model's class comes off for it. With it on,
      // the scenery is hidden and the palm check has nothing to measure.
      document.querySelector('.app').classList.remove('has-3d');
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

      // The day ends. The bell brings the night; it does not move the sun --
      // the sun is on its own clock and `sky()` carries it down while the
      // bell's light plays. Driven in that order, and the bell is played with
      // the disc deliberately left alone in between, so an animation that
      // reached for it again would show up here.
      const sunY = () => scene.sunNode.getBoundingClientRect().top;
      scene.sky({ ...t.final, phase: 'market', bell_at: null }, null, 0);
      found.sunBefore = sunY();
      scene.play({ kind: 'bell', episode: 1, lapsed: 0 });
      await nap(400);
      found.sunAfterBellOnly = sunY();
      scene.draw({ ...t.final, phase: 'closed' }, t);
      scene.sky({ ...t.final, phase: 'closed' }, null, 0);
      // The night overlay is a CSS transition on `.closed`, which is applied
      // here rather than by the bell -- so it needs its own time to land.
      // Past the end of the 2.4s transition, not part-way into it: a sample
      // taken mid-glide measures how busy the machine is as much as it
      // measures the page, and it is the landed value that is the assertion.
      await nap(2900);
      found.closed = island.classList.contains('closed');
      found.sunSetting = sunY() > found.sunBefore;
      found.nightOpacity = Number(getComputedStyle(
        document.querySelector('.night')).opacity);

      // And a new day. The sun does not slide back across the sky to get
      // there: it is dark at both ends of the night, and rises in the east.
      scene.draw({ ...t.final, phase: 'market' }, t);
      scene.sky({ ...t.final, phase: 'market' }, null, 0);
      scene.play({ kind: 'open', episode: 2, of: 3 });
      await nap(300);
      found.reopened = !island.classList.contains('closed');
      found.dawnDim = Number(getComputedStyle(scene.sunNode).opacity);
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
        bad.append(f"{where}: the sun did not go down when the day closed ({seen})")
    # The point of this change: the bell is the light, not the disc. If playing
    # it moves the sun, something has reached for the sun again.
    if abs(seen["sunAfterBellOnly"] - seen["sunBefore"]) > 1:
        bad.append(f"{where}: playing the bell moved the sun on its own "
                   f"({seen['sunBefore']:.0f} -> {seen['sunAfterBellOnly']:.0f}); "
                   f"the sun keeps its own clock and the bell carries the light")
    if seen["dawnDim"] > 0.35:
        bad.append(f"{where}: a new day started with the sun already at "
                   f"{seen['dawnDim']:.2f} opacity; it should rise out of the sea")
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
      // This drives the *drawn* scene in isolation -- the fallback a browser
      // with no WebGL gets -- so the model's class comes off for it. With it on,
      // the scenery is hidden and the palm check has nothing to measure.
      document.querySelector('.app').classList.remove('has-3d');
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
            # Every replay, not just the first. `boards[0]` meant a newly
            # published game was never rendered by anything until somebody
            # opened it -- which is exactly how the live board's seat names
            # got past this harness and were found by eye instead.
            for board in boards:
                problems += replay(browser, base, board, out)
            for board in boards:
                problems += blame(browser, base, board, out)
            problems += bare(browser, base, boards[0], out)
            problems += mobile(browser, base, boards[0], out)
            problems += fallback(browser, base, boards[0], out)
            problems += living(browser, base, boards[0], out)
            problems += alive(browser, base, boards[0], out)
            problems += turning(browser, base, boards[0], out)
            problems += uncovered(browser, base, boards[0], out)
            problems += island(browser, base, out)
            problems += mechanics(browser, base, out)
            for board in boards:
                problems += daylight(browser, base, board, out)
            problems += vocabulary(browser, base, boards[0])
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
            if name == "end":
                bad += ending(page, reveal, f"{stem}{' still' if motion else ''}")

            suffix = f"-{label}" if label else ""
            page.screenshot(path=str(out / f"{stem}-{name}{suffix}.png"))
        bad += [f"{stem}{' still' if motion else ''}: {e}" for e in errs]
        page.close()
    return bad


#: The two refusals in game 002 that are the same mistake -- a trader promising
#: the same stock to two exchanges at once -- caught in the two different states
#: that mistake can be in when the manager refuses.
#:
#: Episode 2: T2 held 0.1413 bread, offered 0.1 of it in `p4`, then tried to
#: approve `p3`, which asks for 0.1. `p4` is still **open**, so the rope holding
#: the bread is on the square and is the thing to point at.
#:
#: Episode 3: T1 held 0.8868 cloth, offered 0.5 in `p7` and wanted 0.4 for `p6`
#: -- 0.9 of stock it did not have. By the time it approved `p6`, `p7` had
#: **settled**: the cloth is gone rather than committed, there is no rope to
#: blame, and the page must mark the slot and stop there rather than invent a
#: culprit. That distinction is why this case is here at all.
BLAME = {
    "island-game-002b-g1": [
        {"reason": "you have 0.0413 bread uncommitted, not the 0.1000 it asks for",
         "trader": "T2", "good": "bread", "rope": "p4", "innocent": "p3"},
        {"reason": "you have 0.3868 cloth uncommitted, not the 0.4000 it asks for",
         "trader": "T1", "good": "cloth", "rope": None, "innocent": "p6"},
    ],
}


def blame(browser, base: str, board: Path, out: Path) -> list[str]:
    """A refusal points at what caused it.

    The page drew a bare ✗ for every refusal, including the ones whose cause
    -- a rope -- was on the square the whole time. This drives the two real
    refusals from game 002's board and checks that the offer lit is the
    trader's own, and not the one it failed to take.
    """
    stem = board.name[len("board-"):-len(".json")]
    where = f"{stem} blame"
    cases = BLAME.get(stem)
    if not cases:
        return []
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(f"{base}/")
    page.wait_for_timeout(500)
    bad: list[str] = []
    for want in cases:
        # The real board, reduced by the real reducer, drawn by the real scene.
        # The refusal is found among the frames by its text rather than handed
        # in, so this cannot pass against a board that stopped containing it.
        lit = page.evaluate("""async ({want, url}) => {
          const { reduce } = await import('./reducer.js');
          const { Scene } = await import('./scene.js');
          const nap = (ms) => new Promise(r => setTimeout(r, ms));
          const board = await (await fetch(url)).json();
          const t = reduce(board.messages, {});
          const at = t.frames.findIndex(
            (f) => f.event?.kind === 'refused' && f.event.reason === want.reason);
          if (at < 0) return { error: 'that refusal is not on this board any more' };
          document.getElementById('island').replaceChildren();
          const scene = new Scene(document.getElementById('island'), t, null);
          scene.draw(t.frames[at].state, t);
          scene.play(t.frames[at].event);
          await nap(120);
          const on = (sel) => [...document.querySelectorAll(sel)]
            .map(n => n.dataset.pid || n.dataset.good);
          return { ropes: on('.rope.blamed'), cells: on('.cell.blamed'),
                   ropesAll: on('.rope'),
                   badge: document.querySelectorAll('.pop.bad').length };
        }""", {"want": want, "url": f"replays/{board.name}"})
        tag = f"{where} {want['good']}"
        if lit.get("error"):
            bad.append(f"{tag}: {lit['error']}")
            continue
        page.screenshot(path=str(out / f"{stem}-blame-{want['good']}.png"))
        if want["rope"]:
            if want["rope"] not in lit["ropesAll"]:
                bad.append(f"{tag}: {want['rope']} is not open at that refusal "
                           f"({lit['ropesAll']}), so this case proved nothing")
            elif want["rope"] not in lit["ropes"]:
                bad.append(f"{tag}: the refusal did not light {want['rope']}, the "
                           f"offer holding it (lit {lit['ropes']})")
        elif lit["ropes"]:
            # Nothing on the square caused this one -- the goods were spent, not
            # committed -- and a page that lights a rope anyway is telling the
            # reader something untrue about a real board.
            bad.append(f"{tag}: the goods were already spent, not committed, and "
                       f"the page blamed {lit['ropes']} anyway")
        if want["innocent"] in lit["ropes"]:
            bad.append(f"{tag}: lit {want['innocent']}, which is the offer it could "
                       f"not take rather than the reason it could not")
        if want["good"] not in lit["cells"]:
            bad.append(f"{tag}: the {want['good']} slot it came up short in is not "
                       f"marked (marked {lit['cells']})")
        if not lit["badge"]:
            bad.append(f"{tag}: the refusal badge itself stopped being drawn")
    bad += [f"{where}: {e}" for e in errs]
    page.close()
    return bad


#: Phone viewports the page has to work at: a common portrait, a small one,
#: and the same phone turned on its side.
PHONES = [("portrait", 390, 844), ("small", 360, 640), ("landscape", 844, 390),
          #: A phone with the browser's own bars showing, which is what a
          #: shared link actually opens into: the window is a hundred and more
          #: points shorter than the device, and everything the page floats
          #: over the bottom of the island moves up with it.
          ("safari", 393, 660)]

#: The chrome that floats over the island. Any two of these overlapping is the
#: bug this exists to hold shut -- it happened twice while the breakpoints were
#: being written, once because a media block was authored above the rules it
#: meant to override and lost on source order, which no amount of reading the
#: CSS made obvious.
CHROME = ["#transport", ".counts", ".legend", ".at-top-left", ".at-top-right"]


def daylight(browser, base: str, board: Path, out: Path) -> list[str]:
    """The sun marks how far through the episode a frame is.

    An episode is a day. The page used to report how long the board had been
    quiet in a pill -- a number about the replay rather than about the island --
    while the sun sat in one spot from the open to the bell.

    Driven through the page, at frames inside a single episode, so this is the
    sun a viewer actually sees rather than the arc's arithmetic (which
    `scene.test.mjs` checks on its own).
    """
    stem = board.name[len("board-"):-len(".json")]
    where = f"{stem} daylight"
    page = browser.new_page(viewport={"width": 1500, "height": 1000},
                            reduced_motion="reduce")
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(board_url(base, stem))
    page.wait_for_selector(".hut", timeout=10_000)
    page.wait_for_timeout(1200)
    page.evaluate("u => { window.__boardUrl = u; }", f"replays/{board.name}")
    seen = page.evaluate("""async () => {
      const s = document.getElementById('scrub');
      const at = (i) => new Promise(r => {
        s.value = String(i); s.dispatchEvent(new Event('input'));
        setTimeout(() => {
          const b = document.querySelector('.sun').getBoundingClientRect();
          r({ x: b.x + b.width / 2, y: b.y + b.height / 2 });
        }, 90);
      });
      const total = Number(s.max);
      const out = [];
      for (let i = 0; i <= total; i++) out.push(await at(i));
      return { total, spots: out,
               clock: (document.getElementById('clock') || {}).textContent || '' };
    }""")
    # The live shape of the same call: there is no next line yet, so the sun is
    # aimed at the bell over whatever is left of the day. Driven here because a
    # live hub is not available to a test, and the arithmetic is the part that
    # differs -- `until` is the bell rather than the next frame.
    live = page.evaluate("""async () => {
      const { reduce } = await import('./reducer.js');
      const { Scene } = await import('./scene.js');
      const board = await (await fetch(window.__boardUrl)).json();
      const t = reduce(board.messages, {});
      const open = t.frames.find((f) => f.event?.kind === 'open');
      if (!open) return { error: 'no episode opens on this board' };
      document.getElementById('island').replaceChildren();
      const scene = new Scene(document.getElementById('island'), t, null);
      const state = open.state;
      scene.draw(state, t);
      const at = () => scene.sunNode.getBoundingClientRect().x;
      const dawn = at();
      // What index.html does on a live poll, with the bell still ahead.
      scene.sky(state, state.bell_at, 4000);
      await new Promise(r => setTimeout(r, 500));
      return { dawn, later: at(), bell: state.bell_at, secs: state.seconds };
    }""")
    page.close()
    bad = [f"{where}: {e}" for e in errs]
    if live.get("error"):
        bad.append(f"{where}: {live['error']}")
    elif not (live["later"] > live["dawn"] + 1):
        bad.append(f"{where}: aimed at the bell the sun did not move "
                   f"({live['dawn']:.0f} -> {live['later']:.0f}); live would sit still "
                   f"between polls, which is when there is nothing else to watch")
    xs = [round(s["x"], 1) for s in seen["spots"]]
    # It has to actually go somewhere, and westward: the same x at every frame
    # is the sun this change exists to unpark.
    if len(set(xs)) < 4:
        bad.append(f"{where}: the sun stood in {len(set(xs))} place(s) across "
                   f"{seen['total'] + 1} frames -- it is not marking the day")
    backwards = sum(1 for a, b in zip(xs, xs[1:]) if b < a - 1)
    # One step back per episode boundary: dawn puts it back in the east.
    if backwards > 4:
        bad.append(f"{where}: the sun went backwards {backwards} times; it should "
                   f"only reset at an episode boundary")
    if "quiet" in seen["clock"]:
        bad.append(f"{where}: the idle-seconds pill is back: {seen['clock']!r}")
    return bad


def vocabulary(browser, base: str, board: Path) -> list[str]:
    """In the game an episode is called a day.

    The board is not renamed and neither are the metrics: the manager writes
    "episode 1 of 3 is open" in its own words, the transcript shows those words,
    and `eff_episode` is an identifier in the ledger. What is renamed is
    everything the game says in its own voice -- the round state, the chapter
    menu, the closing card.
    """
    stem = board.name[len("board-"):-len(".json")]
    page = browser.new_page(viewport={"width": 1500, "height": 1000},
                            reduced_motion="reduce")
    page.goto(board_url(base, stem))
    page.wait_for_selector(".hut", timeout=10_000)
    page.wait_for_timeout(1000)
    page.evaluate("() => { const s = document.getElementById('scrub');"
                  " s.value = s.max; s.dispatchEvent(new Event('input')); }")
    page.wait_for_timeout(900)
    said = page.evaluate("""() => {
      const of = (sel) => (document.querySelector(sel) || {}).textContent || '';
      return { state: of('#ep'), chapters: of('#chapters'), closing: of('#closing'),
               // The transcript is the board verbatim and keeps the manager's
               // word; this asserts it is still there rather than renamed.
               ticker: of('#ticker') };
    }""")
    page.close()
    bad = []
    for where, text in (("round state", said["state"]), ("chapter menu", said["chapters"]),
                        ("closing card", said["closing"])):
        if "episode" in text.lower():
            bad.append(f"{stem} vocabulary: the {where} still says episode: "
                       f"{text.strip()[:70]!r}")
    if "day" not in said["state"].lower():
        bad.append(f"{stem} vocabulary: the round state does not say day: "
                   f"{said['state'].strip()[:70]!r}")
    if said["ticker"] and "episode" not in said["ticker"].lower():
        bad.append(f"{stem} vocabulary: the transcript stopped quoting the "
                   f"manager's own word for an episode")
    return bad


#: Reading the model's own pixels. Everything the life layer does is in the
#: canvas and none of it is in the DOM, so the alternative was a test handle on
#: the shipped page -- and a check that measures what a viewer sees is better
#: than one that measures what the page exposes to be measured.
SAMPLE = """() => {
  const cv = document.getElementById('stage');
  const s = document.createElement('canvas');
  s.width = 96; s.height = Math.max(1, Math.round(96 * cv.height / cv.width));
  const g = s.getContext('2d');
  g.drawImage(cv, 0, 0, s.width, s.height);
  const px = g.getImageData(0, 0, s.width, s.height).data;
  let lum = 0, warm = 0, lit = 0;
  for (let i = 0; i < px.length; i += 4) {
    if (px[i + 3] < 24) continue;
    lit++;
    lum += (px[i] + px[i + 1] + px[i + 2]) / 3;
    warm += px[i] - px[i + 2];          // red over blue: how warm the light is
  }
  return { lum: lit ? lum / lit : 0, warm: lit ? warm / lit : 0, lit,
           px: [...px.slice(0, 4096)].join(',') };
}"""


def alive(browser, base: str, board: Path, out: Path) -> list[str]:
    """The island moves, holds still when asked to, and keeps the day's time.

    Three things, none of which a single screenshot can show, and all of them
    measured off the canvas rather than through a handle on the page.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []

    def at(page, frac):
        total = int(page.eval_on_selector("#scrub", "e => Number(e.max)"))
        page.evaluate("i => { const s = document.getElementById('scrub');"
                      " s.value = String(i); s.dispatchEvent(new Event('input')); }",
                      round(total * frac))
        # Past the sun's glide and the overlays' 2.4s
        # transitions, so what is sampled is where the page settles
        # rather than how fast this machine happens to be.
        page.wait_for_timeout(2600)

    for still in (False, True):
        page = browser.new_page(viewport={"width": 1200, "height": 800},
                                reduced_motion="reduce" if still else "no-preference")
        page.goto(board_url(base, stem))
        page.wait_for_selector(".hut", timeout=15_000)
        page.wait_for_timeout(1800)
        at(page, 0.55)
        first = page.evaluate(SAMPLE)
        page.wait_for_timeout(700)
        second = page.evaluate(SAMPLE)
        where = f"{stem} alive{' still' if still else ''}"
        if not first["lit"]:
            bad.append(f"{where}: nothing on the canvas to measure")
        elif still and first["px"] != second["px"]:
            bad.append(f"{where}: the island kept moving for somebody who asked "
                       f"for less motion")
        elif not still and first["px"] == second["px"]:
            bad.append(f"{where}: the island did not move between two frames; "
                       f"the life layer is not running")
        if not still:
            # The light against **the page's own sun**, not against a position
            # in the replay. A scrub fraction is not a time of day: a board's
            # events do not fall evenly across its days, so "half way through
            # the messages" can land at dusk on one board and at dawn on the
            # next, and comparing two of them says nothing. The drawn sun is
            # already on the clock, so its height on screen is the reference --
            # and what is asserted is that the model agrees with it: the island
            # is warmer and darker when the sun is low than when it is high.
            #
            # Held loosely. This is a threshold on a rendered picture.
            read = []
            for frac in (0.15, 0.3, 0.45, 0.6, 0.8, 1.0):
                at(page, frac)
                shot = page.evaluate(SAMPLE)
                shot["sun"] = page.evaluate(
                    "() => document.querySelector('.sun').getBoundingClientRect().top")
                read.append(shot)
            page.screenshot(path=str(out / f"{stem}-dusk3d.png"))
            # Warmth *relative to brightness*. Red-minus-blue on its own falls
            # with the light, so a genuinely orange evening scores lower than a
            # bright blue midday simply for being dark -- which measures the
            # dimmer, not the colour. Divided through, it is the tint.
            for r in read:
                r["tint"] = r["warm"] / max(1.0, r["lum"])
            high = min(read, key=lambda r: r["sun"])   # smallest top: sun highest
            low = max(read, key=lambda r: r["sun"])    # largest top: sun lowest
            if high["sun"] == low["sun"]:
                bad.append(f"{where}: the sun never moved across the replay, so "
                           f"nothing checked the light against it")
            elif low["tint"] <= high["tint"] + 0.08:
                bad.append(f"{where}: the island is no warmer with the sun down "
                           f"than with it up (tint {high['tint']:.2f} -> "
                           f"{low['tint']:.2f}); the light is not on the day's clock")
            elif low["lum"] >= high["lum"]:
                bad.append(f"{where}: the island is no darker with the sun down "
                           f"than with it up ({high['lum']:.0f} -> {low['lum']:.0f})")
        page.close()
    return bad


def uncovered(browser, base: str, board: Path, out: Path) -> list[str]:
    """No trader card stands on the island.

    The cards used to hang under their own huts, which put them in the middle
    of the frame -- between them they covered the market, both settlements and
    most of the meadow, which is the picture the page exists to show. They are
    in the frame's margins now, and this is the thing that says so: it reads
    the model's own canvas under each card's rectangle and counts how much of
    what is behind it is island.

    Asked of the pixels rather than of the layout, because "the card is outside
    the island's box" is a statement about two numbers agreeing and this is a
    statement about what a person sees.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    for label, w, h in (("desktop", 1400, 860), ("laptop", 1200, 750),
                        ("wide", 1700, 720), ("phone", 430, 880),
                        # A phone with the browser's own bars showing, which is
                        # what a shared link opens into and where the cards were
                        # found sitting behind the transport.
                        ("safari", 393, 660), ("small", 360, 640),
                        # A phone on its side: the shortest frame there is, and
                        # where a card column has the legend to miss.
                        ("landscape", 844, 390)):
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(board_url(base, stem))
        page.wait_for_selector(".hut", timeout=15_000)
        page.wait_for_timeout(1800)
        if not page.evaluate("() => document.querySelector('.app').classList.contains('has-3d')"):
            page.close()
            continue
        seen = page.evaluate("""() => {
          const cv = document.getElementById('stage');
          const cr = cv.getBoundingClientRect();
          const s = document.createElement('canvas');
          s.width = cv.width; s.height = cv.height;
          const g = s.getContext('2d');
          g.drawImage(cv, 0, 0);
          const sx = cv.width / cr.width, sy = cv.height / cr.height;
          return [...document.querySelectorAll('.hut')].map(hut => {
            const bg = hut.querySelector('.card-bg').getBoundingClientRect();
            const x = Math.max(0, Math.round((bg.x - cr.x) * sx));
            const y = Math.max(0, Math.round((bg.y - cr.y) * sy));
            const bw = Math.min(s.width - x, Math.round(bg.width * sx));
            const bh = Math.min(s.height - y, Math.round(bg.height * sy));
            const name = hut.getAttribute('data-trader');
            if (bw <= 0 || bh <= 0) return { name, over: 0, off: true };
            const px = g.getImageData(x, y, bw, bh).data;
            let on = 0;
            // The island is drawn on a transparent canvas, so anything opaque
            // behind a card *is* the island.
            for (let i = 3; i < px.length; i += 4) if (px[i] > 40) on++;
            return { name, over: on / (bw * bh), off: false };
          });
        }""")
        over = page.evaluate("""(chrome) => {
          const boxes = chrome.map(s => document.querySelector(s))
            .filter(n => n && !n.hidden)
            .map(n => ({ s: n.id ? '#' + n.id : n.className, r: n.getBoundingClientRect() }))
            .filter(b => b.r.width && b.r.height)
            // Grown by a margin, so "the card's last pixel row is not quite
            // under the transport" does not count as clear of it.
            .map(b => ({ s: b.s, r: { x: b.r.x - 10, y: b.r.y - 10,
                                      width: b.r.width + 20, height: b.r.height + 20 } }));
          return [...document.querySelectorAll('.hut')].map(hut => {
            const c = hut.querySelector('.card-bg').getBoundingClientRect();
            const hit = boxes.filter(b => b.r.x < c.x + c.width && b.r.x + b.r.width > c.x
                                       && b.r.y < c.y + c.height && b.r.y + b.r.height > c.y);
            return { name: hut.getAttribute('data-trader'),
                     under: hit.map(b => b.s),
                     // How much of the card is off the bottom of the window,
                     // which is where a card too tall for the frame goes.
                     below: Math.max(0, (c.y + c.height - innerHeight) / c.height) };
          });
        }""", CHROME)
        for r in over:
            if r["under"]:
                bad.append(f"uncovered {label}: {r['name']}'s card is behind "
                           f"{', '.join(r['under'])}")
            if r["below"] > 0.01:
                bad.append(f"uncovered {label}: {r['below'] * 100:.0f}% of "
                           f"{r['name']}'s card is off the bottom of the window")
        for r in seen:
            if r["off"]:
                bad.append(f"uncovered {label}: {r['name']}'s card is off the canvas")
            #: A tenth. Not zero: the island's sea disc is soft-edged and the
            #: margins are only as wide as a card, so a corner of open water
            #: behind one is expected and harmless. Half a card of *island* is
            #: not.
            elif r["over"] > 0.10:
                bad.append(f"uncovered {label}: {r['name']}'s card is standing on "
                           f"the island -- {r['over'] * 100:.0f}% of what is behind "
                           f"it is drawn world")
        page.screenshot(path=str(out / f"{stem}-{label}-cards.png"))
        page.close()
    return bad


#: A stage built off-page, so a check can ask the model questions the page
#: has no reason to expose. The same modules the viewer loads, driven directly.
STAGE = """async ({w, h, n, portrait, goods}) => {
  const THREE = await import('./vendor/three/three.module.js');
  const { Stage } = await import('./stage.js');
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h; document.body.appendChild(cv);
  const st = new Stage(cv, {w, h});
  st.pause();
  st.setDay(0.45);
  const traders = Array.from({length: n}, (_, i) => `T${i + 1}`);
  const mid = {x: w / 2, y: h * (portrait ? 0.5 : 0.46)};
  let spots;
  if (n <= 2) {
    const dx = w * (portrait ? 0 : 0.2), dy = h * (portrait ? 0.19 : 0);
    spots = n === 1 ? [mid]
      : [{x: mid.x - dx, y: mid.y - dy}, {x: mid.x + dx, y: mid.y + dy}];
  } else spots = Array.from({length: n}, (_, i) => {
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return {x: mid.x + Math.cos(a) * w * 0.26, y: mid.y + Math.sin(a) * h * 0.20};
  });
  const made = st.build({traders, goods, seats: spots.map(p => st.groundAt(p.x, p.y))});
  st.pause();
  // What is directly under a point, ignoring anything standing on the ground
  // rather than being it.
  const ray = new THREE.Raycaster(), down = new THREE.Vector3(0, -1, 0);
  const SKIP = /^(settlement_|hut_|trails?$|trail_|tree_|palm_|marker_|site_|smoke_|goat_|gull_|cloud_|leaf_|ripple_|surf_|crate|ring|puff_|dust|labour_|banner_|post$|notice)/;
  const chain = (o) => { const ns = []; for (let k = o; k && k !== made.island; k = k.parent) ns.push(k.name || '?'); return ns; };
  window.__under = (x, z) => {
    ray.set(new THREE.Vector3(x, 8, z), down);
    const hit = ray.intersectObject(made.island, true)
      .filter(h => !chain(h.object).some(nm => SKIP.test(nm)))[0];
    return hit ? hit.object.name : 'nothing';
  };
  window.__st = st;
  window.__made = made;
  return {traders, seats: traders.map(t => [made.anchors[t].x, made.anchors[t].z])};
}"""


def island(browser, base: str, out: Path) -> list[str]:
    """Nothing stands in the sea, and the goats do not run.

    **Both of these were reported by somebody watching, not by a test**, which
    is the argument for this one existing. The seats come from the page in
    screen coordinates and are unprojected onto the island, and how much island
    a screen fraction covers depends on the frame's shape -- so on a wide
    window both settlements landed in the water, and on a narrow one two of
    four landed on the market roof. The goats ran the delivered clip's numbers
    at island scale, which is a metre a second across a meadow six wide, out
    over the beach and off into the sea.

    Asked of the model by raycast rather than of the picture by eye: what is
    under this hut is a question with an exact answer.
    """
    bad: list[str] = []
    #: Where a settlement may stand. Not the beach: a hut on sand is a hut
    #: nobody put there on purpose.
    LAND = {"meadow", "upland", "market_plaza", "ridge"}
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    shapes = [("desktop", 1200, 750, 2, False), ("wide", 1600, 700, 2, False),
              ("tall", 900, 1100, 2, False), ("phone", 430, 780, 2, True),
              ("desktop/4", 1200, 750, 4, False), ("phone/4", 430, 900, 4, True),
              ("desktop/5", 1400, 800, 5, False)]
    for label, w, h, n, portrait in shapes:
        built = page.evaluate(STAGE, {"w": w, "h": h, "n": n, "portrait": portrait,
                                      "goods": ["bread", "cloth", "iron", "salt", "fish"]})
        seats = built["seats"]
        for name, (x, z) in zip(built["traders"], seats):
            under = page.evaluate("([x, z]) => window.__under(x, z)", [x, z])
            if under not in LAND:
                bad.append(f"island {label}: {name}'s settlement stands on "
                           f"{under!r} at ({x:.2f}, {z:.2f})")
        # And not on top of each other: a frame narrow enough collapses the
        # layout's ring, and two huts in one place is one hut with a spare card.
        for i in range(len(seats)):
            for j in range(i + 1, len(seats)):
                d = ((seats[i][0] - seats[j][0]) ** 2 + (seats[i][1] - seats[j][1]) ** 2) ** 0.5
                if d < 1.2:
                    bad.append(f"island {label}: two settlements {d:.2f} apart, "
                               f"which is inside a hut's own width")

    # And the case the layout can actually produce but these shapes happen not
    # to: two seats at the same point. Asked of the model directly, because a
    # viewport that collapses the ring is a moving target and this is the
    # property that has to hold whatever produced it.
    twins = page.evaluate("""async () => {
      const { buildIsland } = await import('./island3d.js');
      const same = [[2.2, 1.1], [2.2, 1.1], [2.21, 1.09]];
      const made = buildIsland({traders: ['A', 'B', 'C'],
                                goods: ['bread', 'cloth'], seats: same});
      return ['A', 'B', 'C'].map(n => [made.anchors[n].x, made.anchors[n].z]);
    }""")
    for i in range(len(twins)):
        for j in range(i + 1, len(twins)):
            d = ((twins[i][0] - twins[j][0]) ** 2 + (twins[i][1] - twins[j][1]) ** 2) ** 0.5
            if d < 1.2:
                bad.append(f"island: three seats at one point built settlements "
                           f"{d:.2f} apart; they were not moved off each other")

    # The herd, over three minutes of its own clock.
    walk = page.evaluate("""() => {
      const st = window.__st, made = window.__made;
      const goats = made.island.children.filter(o => /^goat_/.test(o.name));
      const seen = [], step = 0.25;
      let fastest = 0;
      const last = new Map();
      for (let t = 0; t < 200; t += step) {
        st.life.update(t, st.ctx());
        for (const g of goats) {
          const p = [g.position.x, g.position.z];
          seen.push([g.name, p[0], p[1], window.__under(p[0], p[1])]);
          const was = last.get(g.name);
          if (was) fastest = Math.max(fastest, Math.hypot(p[0] - was[0], p[1] - was[1]) / step);
          last.set(g.name, p);
        }
      }
      return {n: goats.length, fastest,
              off: seen.filter(s => !['meadow', 'upland', 'market_plaza', 'ridge'].includes(s[3]))
                       .slice(0, 3)};
    }""")
    if not walk["n"]:
        bad.append("island: no goats to check")
    if walk["off"]:
        where = ", ".join(f"{g[0]} on {g[3]!r} at ({g[1]:.1f}, {g[2]:.1f})" for g in walk["off"])
        bad.append(f"island: a goat left the grass -- {where}")
    #: Island units a second. A goat is about 0.35 long, so this is roughly a
    #: body length per second -- an outer bound on "ambling", not a target.
    if walk["fastest"] > 0.35:
        bad.append(f"island: the goats move at {walk['fastest']:.2f} units/s, "
                   f"which at this scale is a run, not a graze")
    page.screenshot(path=str(out / "island-model.png"))
    page.close()
    return bad


#: One of each kind the island has a clip for, with enough of a payload that
#: the clip has something to carry.
FIRED = [
    {"kind": "produced", "trader": "T1", "made": {"bread": 0.8, "salt": 0.5}},
    {"kind": "offer", "pid": "p1", "maker": "T1", "taker": "T2",
     "give": {"bread": 0.5}, "want": {"cloth": 0.3}},
    {"kind": "settled", "pid": "p1", "maker": "T1", "taker": "T2",
     "give": {"bread": 0.5}, "want": {"cloth": 0.3}},
    {"kind": "refused", "trader": "T2", "reason": "uncommitted stock"},
    {"kind": "bell", "episode": 1, "lapsed": 2},
    {"kind": "open", "episode": 2, "of": 3},
]


def mechanics(browser, base: str, out: Path) -> list[str]:
    """Every event the island has a clip for actually shows, and then goes.

    Three things, and the first is the one that matters: **a clip that runs but
    cannot be seen is not an animation.** The delivered clips were watched one
    at a time in a frame two units across; the island is eight and half of it
    is behind the cards, so at their own scale the crates were a handful of
    pixels and the rings were hairlines under the market roof. This measures
    the canvas against the same island with nothing happening on it, and asks
    for a share of the frame to have changed.

    The second: it has to end. A clip that leaves a crate standing is a page
    that accumulates litter over a long replay.

    The third: it has to put back what it borrowed. Several of these move the
    island's own nodes -- the hut banners, the crates beside a door -- and
    those are not the clip's to keep.
    """
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 1000, "height": 700})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.on("console", lambda m: errs.append(f"console error: {m.text}")
            if m.type == "error" else None)
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    page.evaluate(STAGE, {"w": 900, "h": 560, "n": 2, "portrait": False,
                          "goods": ["bread", "cloth", "iron", "salt", "fish"]})
    seen = page.evaluate("""({events}) => {
      const st = window.__st;
      const shot = () => {
        st.life.update(3, st.ctx());
        st.renderer.render(st.scene, st.camera);
        const s = document.createElement('canvas');
        s.width = 300; s.height = 187;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, 0, 0, s.width, s.height);
        return g.getImageData(0, 0, s.width, s.height).data;
      };
      const diff = (a, b) => {
        let n = 0;
        for (let i = 0; i < a.length; i += 4)
          if (Math.abs(a[i] - b[i]) + Math.abs(a[i+1] - b[i+1])
              + Math.abs(a[i+2] - b[i+2]) > 18) n++;
        return n / (a.length / 4);
      };
      const bare = shot();
      return events.map((e) => {
        st.clear();
        const c = st.fire(e);
        st.pause();
        if (!c) return {kind: e.kind, clip: false};
        let peak = 0;
        for (let t = 0.1; t <= c.dur; t += 0.1) {
          c.t0 = 0;
          st.step(t);
          peak = Math.max(peak, diff(bare, shot()));
        }
        // Past the end, which is what the stage's own loop does.
        c.t0 = 0;
        st.step(c.dur + 0.5);
        const after = diff(bare, shot());
        return {kind: e.kind, clip: true, peak, after, live: st.clips.length};
      });
    }""", {"events": FIRED})
    for r in seen:
        where = f"mechanics {r['kind']}"
        if not r.get("clip"):
            bad.append(f"{where}: the island has nothing to show for it")
            continue
        #: Share of the frame. Small, because the island is mostly island --
        #: but an order of magnitude above the hairlines this replaced.
        if r["peak"] < 0.004:
            bad.append(f"{where}: only {r['peak'] * 100:.2f}% of the frame ever "
                       f"changed; whatever it did cannot be seen")
        if r["live"]:
            bad.append(f"{where}: {r['live']} clip(s) still running after the end")
        if r["after"] > 0.0005:
            bad.append(f"{where}: {r['after'] * 100:.2f}% of the frame is still "
                       f"changed once it finished; it left something behind")
    # And the case `restore` actually exists for: a clip cut off part-way,
    # which is what a rebuild does to whatever was in flight. Left alone, a
    # bell interrupted mid-swing leaves every settlement's banner hanging in
    # the air over the island for the rest of the round.
    cut = page.evaluate("""() => {
      const st = window.__st;
      const shot = () => {
        st.life.update(3, st.ctx());
        st.renderer.render(st.scene, st.camera);
        const s = document.createElement('canvas');
        s.width = 300; s.height = 187;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, 0, 0, s.width, s.height);
        return g.getImageData(0, 0, s.width, s.height).data;
      };
      const diff = (a, b) => {
        let n = 0;
        for (let i = 0; i < a.length; i += 4)
          if (Math.abs(a[i] - b[i]) + Math.abs(a[i+1] - b[i+1])
              + Math.abs(a[i+2] - b[i+2]) > 18) n++;
        return n / (a.length / 4);
      };
      st.clear();
      const bare = shot();
      const out = [];
      for (const e of [{kind: 'bell', episode: 1, lapsed: 2},
                       {kind: 'open', episode: 2, of: 3}]) {
        const c = st.fire(e);
        st.pause();
        c.t0 = 0;
        st.step(c.dur * 0.5);           // half way through, and then pulled
        st.clear();
        out.push([e.kind, diff(bare, shot())]);
      }
      return out;
    }""")
    for kind, left in cut:
        if left > 0.0005:
            bad.append(f"mechanics {kind}: cut off half way and {left * 100:.2f}% "
                       f"of the frame stayed changed; it kept what it borrowed")

    # A kind the island says nothing about must stay silent rather than throw.
    quiet = page.evaluate("""() => {
      const st = window.__st;
      return [{kind: 'said', author: 'T1'}, {kind: 'tick', left: 30}, {kind: 'over'}]
        .map(e => [e.kind, st.fire(e) === null]);
    }""")
    for kind, silent in quiet:
        if not silent:
            bad.append(f"mechanics {kind}: the island invented something to show")
    bad += [f"mechanics: {e}" for e in errs]
    page.screenshot(path=str(out / "mechanics.png"))
    page.close()
    return bad


def turning(browser, base: str, board: Path, out: Path) -> list[str]:
    """The camera goes round the island, and what points at it goes round too.

    **The cards do not move, and that is the assertion.** They stand in the
    frame's margins now -- they used to hang under their huts, in the middle of
    the picture, covering the market and both settlements -- so a card that
    drifted with the camera would be a card wandering out of its margin.

    What has to keep up is everything drawn *at* a settlement: the pin at the
    end of each card's tether, and the rope between two huts with an offer
    standing between them. Nothing else on the page can tell you whether that
    is happening -- a screenshot shows one instant, and a page that follows and
    a page that does not look identical in it. So: two instants, four seconds
    apart, and what moved between them.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    read = """() => {
      const at = (n) => {
        const m = /translate\\(([-\\d.]+)[ ,]+([-\\d.]+)\\)/.exec(n.getAttribute('transform') || '');
        return m ? [Number(m[1]), Number(m[2])] : null;
      };
      const ends = [...document.querySelectorAll('.rope .rope-line')].map(p => {
        const m = /^M ([-\\d.]+) ([-\\d.]+) Q [-\\d.]+ [-\\d.]+ ([-\\d.]+) ([-\\d.]+)$/
          .exec(p.getAttribute('d'));
        return m ? [[Number(m[1]), Number(m[2])], [Number(m[3]), Number(m[4])]] : null;
      });
      return {
        cards: [...document.querySelectorAll('.hut')].map(at),
        pins: [...document.querySelectorAll('.tether-pin')]
          .map(c => [Number(c.getAttribute('cx')), Number(c.getAttribute('cy'))]),
        ropes: ends,
      };
    }"""

    for still in (False, True):
        page = browser.new_page(viewport={"width": 1200, "height": 800},
                                reduced_motion="reduce" if still else "no-preference")
        page.goto(board_url(base, stem))
        page.wait_for_selector(".hut", timeout=15_000)
        if not page.evaluate("() => document.querySelector('.app').classList.contains('has-3d')"):
            page.close()
            return bad          # no model, nothing to turn
        total = int(page.eval_on_selector("#scrub", "e => Number(e.max)"))
        # Stopped somewhere with an offer standing, because a rope left behind
        # is half of what this checks and a frame with no rope cannot show it.
        for frac in (0.5, 0.78, 0.3, 0.85, 0.55):
            page.evaluate("i => { const s = document.getElementById('scrub');"
                          " s.value = String(i); s.dispatchEvent(new Event('input')); }",
                          round(total * frac))
            page.wait_for_timeout(1200)
            if page.evaluate("() => document.querySelectorAll('.rope .rope-line').length"):
                break
        where = f"{stem} turning{' still' if still else ''}"
        first = page.evaluate(read)
        page.wait_for_timeout(4000)
        second = page.evaluate(read)
        page.screenshot(path=str(out / f"{stem}-turned.png"))

        if None in first["cards"] or not first["cards"]:
            bad.append(f"{where}: a card has no placement to read")
            page.close()
            continue
        if not first["pins"]:
            bad.append(f"{where}: no card is tethered to a settlement")
            page.close()
            continue

        drift = max(abs(a[0] - b[0]) + abs(a[1] - b[1])
                    for a, b in zip(first["cards"], second["cards"]))
        moved = max(abs(a[0] - b[0]) + abs(a[1] - b[1])
                    for a, b in zip(first["pins"], second["pins"]))
        if drift > 0.5:
            bad.append(f"{where}: a card moved {drift:.1f} with the camera; the "
                       f"margins do not turn and neither should what stands in them")
        if still and moved > 0.5:
            bad.append(f"{where}: the island turned under somebody who asked for "
                       f"less motion (a tether moved {moved:.1f})")
        if not still:
            #: In viewBox units, over four seconds of a 150-second revolution.
            #: Small on purpose -- this asks whether the tethers are being moved
            #: at all, not how fast.
            if moved < 2:
                bad.append(f"{where}: the camera turned and the tethers did not "
                           f"follow (the furthest pin moved {moved:.1f})")
            if not second["ropes"]:
                bad.append(f"{where}: no offer stood at any stop, so nothing "
                           f"checked that the ropes are re-laid")
            for ends in second["ropes"]:
                if ends is None:
                    bad.append(f"{where}: a rope is not a plain arc between two seats")
                    continue
                for end in ends:
                    # A rope hangs from the settlements, so its ends sit a fixed
                    # lift above the same points the tethers pin.
                    near = min(abs(end[0] - p[0]) + abs(end[1] - (p[1] - 34))
                               for p in second["pins"])
                    if near > 1:
                        bad.append(f"{where}: a rope ends {near:.0f} from any "
                                   f"settlement; it was left where they used to be")
        page.close()
    return bad


#: A stage built off-page, so a check can ask the model questions the page
#: has no reason to expose. The same modules the viewer loads, driven directly.
STAGE = """async ({w, h, n, portrait, goods}) => {
  const THREE = await import('./vendor/three/three.module.js');
  const { Stage } = await import('./stage.js');
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h; document.body.appendChild(cv);
  const st = new Stage(cv, {w, h});
  st.pause();
  st.setDay(0.45);
  const traders = Array.from({length: n}, (_, i) => `T${i + 1}`);
  const mid = {x: w / 2, y: h * (portrait ? 0.5 : 0.46)};
  let spots;
  if (n <= 2) {
    const dx = w * (portrait ? 0 : 0.2), dy = h * (portrait ? 0.19 : 0);
    spots = n === 1 ? [mid]
      : [{x: mid.x - dx, y: mid.y - dy}, {x: mid.x + dx, y: mid.y + dy}];
  } else spots = Array.from({length: n}, (_, i) => {
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return {x: mid.x + Math.cos(a) * w * 0.26, y: mid.y + Math.sin(a) * h * 0.20};
  });
  const made = st.build({traders, goods, seats: spots.map(p => st.groundAt(p.x, p.y))});
  st.pause();
  // What is directly under a point, ignoring anything standing on the ground
  // rather than being it.
  const ray = new THREE.Raycaster(), down = new THREE.Vector3(0, -1, 0);
  const SKIP = /^(settlement_|hut_|trails?$|trail_|tree_|palm_|marker_|site_|smoke_|goat_|gull_|cloud_|leaf_|ripple_|surf_|crate|ring|puff_|dust|labour_|banner_|post$|notice)/;
  const chain = (o) => { const ns = []; for (let k = o; k && k !== made.island; k = k.parent) ns.push(k.name || '?'); return ns; };
  window.__under = (x, z) => {
    ray.set(new THREE.Vector3(x, 8, z), down);
    const hit = ray.intersectObject(made.island, true)
      .filter(h => !chain(h.object).some(nm => SKIP.test(nm)))[0];
    return hit ? hit.object.name : 'nothing';
  };
  window.__st = st;
  window.__made = made;
  return {traders, seats: traders.map(t => [made.anchors[t].x, made.anchors[t].z])};
}"""


def island(browser, base: str, out: Path) -> list[str]:
    """Nothing stands in the sea, and the goats do not run.

    **Both of these were reported by somebody watching, not by a test**, which
    is the argument for this one existing. The seats come from the page in
    screen coordinates and are unprojected onto the island, and how much island
    a screen fraction covers depends on the frame's shape -- so on a wide
    window both settlements landed in the water, and on a narrow one two of
    four landed on the market roof. The goats ran the delivered clip's numbers
    at island scale, which is a metre a second across a meadow six wide, out
    over the beach and off into the sea.

    Asked of the model by raycast rather than of the picture by eye: what is
    under this hut is a question with an exact answer.
    """
    bad: list[str] = []
    #: Where a settlement may stand. Not the beach: a hut on sand is a hut
    #: nobody put there on purpose.
    LAND = {"meadow", "upland", "market_plaza", "ridge"}
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    shapes = [("desktop", 1200, 750, 2, False), ("wide", 1600, 700, 2, False),
              ("tall", 900, 1100, 2, False), ("phone", 430, 780, 2, True),
              ("desktop/4", 1200, 750, 4, False), ("phone/4", 430, 900, 4, True),
              ("desktop/5", 1400, 800, 5, False)]
    for label, w, h, n, portrait in shapes:
        built = page.evaluate(STAGE, {"w": w, "h": h, "n": n, "portrait": portrait,
                                      "goods": ["bread", "cloth", "iron", "salt", "fish"]})
        seats = built["seats"]
        for name, (x, z) in zip(built["traders"], seats):
            under = page.evaluate("([x, z]) => window.__under(x, z)", [x, z])
            if under not in LAND:
                bad.append(f"island {label}: {name}'s settlement stands on "
                           f"{under!r} at ({x:.2f}, {z:.2f})")
        # And not on top of each other: a frame narrow enough collapses the
        # layout's ring, and two huts in one place is one hut with a spare card.
        for i in range(len(seats)):
            for j in range(i + 1, len(seats)):
                d = ((seats[i][0] - seats[j][0]) ** 2 + (seats[i][1] - seats[j][1]) ** 2) ** 0.5
                if d < 1.2:
                    bad.append(f"island {label}: two settlements {d:.2f} apart, "
                               f"which is inside a hut's own width")

    # And the case the layout can actually produce but these shapes happen not
    # to: two seats at the same point. Asked of the model directly, because a
    # viewport that collapses the ring is a moving target and this is the
    # property that has to hold whatever produced it.
    twins = page.evaluate("""async () => {
      const { buildIsland } = await import('./island3d.js');
      const same = [[2.2, 1.1], [2.2, 1.1], [2.21, 1.09]];
      const made = buildIsland({traders: ['A', 'B', 'C'],
                                goods: ['bread', 'cloth'], seats: same});
      return ['A', 'B', 'C'].map(n => [made.anchors[n].x, made.anchors[n].z]);
    }""")
    for i in range(len(twins)):
        for j in range(i + 1, len(twins)):
            d = ((twins[i][0] - twins[j][0]) ** 2 + (twins[i][1] - twins[j][1]) ** 2) ** 0.5
            if d < 1.2:
                bad.append(f"island: three seats at one point built settlements "
                           f"{d:.2f} apart; they were not moved off each other")

    # The herd, over three minutes of its own clock.
    walk = page.evaluate("""() => {
      const st = window.__st, made = window.__made;
      const goats = made.island.children.filter(o => /^goat_/.test(o.name));
      const seen = [], step = 0.25;
      let fastest = 0;
      const last = new Map();
      for (let t = 0; t < 200; t += step) {
        st.life.update(t, st.ctx());
        for (const g of goats) {
          const p = [g.position.x, g.position.z];
          seen.push([g.name, p[0], p[1], window.__under(p[0], p[1])]);
          const was = last.get(g.name);
          if (was) fastest = Math.max(fastest, Math.hypot(p[0] - was[0], p[1] - was[1]) / step);
          last.set(g.name, p);
        }
      }
      return {n: goats.length, fastest,
              off: seen.filter(s => !['meadow', 'upland', 'market_plaza', 'ridge'].includes(s[3]))
                       .slice(0, 3)};
    }""")
    if not walk["n"]:
        bad.append("island: no goats to check")
    if walk["off"]:
        where = ", ".join(f"{g[0]} on {g[3]!r} at ({g[1]:.1f}, {g[2]:.1f})" for g in walk["off"])
        bad.append(f"island: a goat left the grass -- {where}")
    #: Island units a second. A goat is about 0.35 long, so this is roughly a
    #: body length per second -- an outer bound on "ambling", not a target.
    if walk["fastest"] > 0.35:
        bad.append(f"island: the goats move at {walk['fastest']:.2f} units/s, "
                   f"which at this scale is a run, not a graze")
    page.screenshot(path=str(out / "island-model.png"))
    page.close()
    return bad


#: One of each kind the island has a clip for, with enough of a payload that
#: the clip has something to carry.
FIRED = [
    {"kind": "produced", "trader": "T1", "made": {"bread": 0.8, "salt": 0.5}},
    {"kind": "offer", "pid": "p1", "maker": "T1", "taker": "T2",
     "give": {"bread": 0.5}, "want": {"cloth": 0.3}},
    {"kind": "settled", "pid": "p1", "maker": "T1", "taker": "T2",
     "give": {"bread": 0.5}, "want": {"cloth": 0.3}},
    {"kind": "refused", "trader": "T2", "reason": "uncommitted stock"},
    {"kind": "bell", "episode": 1, "lapsed": 2},
    {"kind": "open", "episode": 2, "of": 3},
]


def mechanics(browser, base: str, out: Path) -> list[str]:
    """Every event the island has a clip for actually shows, and then goes.

    Three things, and the first is the one that matters: **a clip that runs but
    cannot be seen is not an animation.** The delivered clips were watched one
    at a time in a frame two units across; the island is eight and half of it
    is behind the cards, so at their own scale the crates were a handful of
    pixels and the rings were hairlines under the market roof. This measures
    the canvas against the same island with nothing happening on it, and asks
    for a share of the frame to have changed.

    The second: it has to end. A clip that leaves a crate standing is a page
    that accumulates litter over a long replay.

    The third: it has to put back what it borrowed. Several of these move the
    island's own nodes -- the hut banners, the crates beside a door -- and
    those are not the clip's to keep.
    """
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 1000, "height": 700})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.on("console", lambda m: errs.append(f"console error: {m.text}")
            if m.type == "error" else None)
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    page.evaluate(STAGE, {"w": 900, "h": 560, "n": 2, "portrait": False,
                          "goods": ["bread", "cloth", "iron", "salt", "fish"]})
    seen = page.evaluate("""({events}) => {
      const st = window.__st;
      const shot = () => {
        st.life.update(3, st.ctx());
        st.renderer.render(st.scene, st.camera);
        const s = document.createElement('canvas');
        s.width = 300; s.height = 187;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, 0, 0, s.width, s.height);
        return g.getImageData(0, 0, s.width, s.height).data;
      };
      const diff = (a, b) => {
        let n = 0;
        for (let i = 0; i < a.length; i += 4)
          if (Math.abs(a[i] - b[i]) + Math.abs(a[i+1] - b[i+1])
              + Math.abs(a[i+2] - b[i+2]) > 18) n++;
        return n / (a.length / 4);
      };
      const bare = shot();
      return events.map((e) => {
        st.clear();
        const c = st.fire(e);
        st.pause();
        if (!c) return {kind: e.kind, clip: false};
        let peak = 0;
        for (let t = 0.1; t <= c.dur; t += 0.1) {
          c.t0 = 0;
          st.step(t);
          peak = Math.max(peak, diff(bare, shot()));
        }
        // Past the end, which is what the stage's own loop does.
        c.t0 = 0;
        st.step(c.dur + 0.5);
        const after = diff(bare, shot());
        return {kind: e.kind, clip: true, peak, after, live: st.clips.length};
      });
    }""", {"events": FIRED})
    for r in seen:
        where = f"mechanics {r['kind']}"
        if not r.get("clip"):
            bad.append(f"{where}: the island has nothing to show for it")
            continue
        #: Share of the frame. Small, because the island is mostly island --
        #: but an order of magnitude above the hairlines this replaced.
        if r["peak"] < 0.004:
            bad.append(f"{where}: only {r['peak'] * 100:.2f}% of the frame ever "
                       f"changed; whatever it did cannot be seen")
        if r["live"]:
            bad.append(f"{where}: {r['live']} clip(s) still running after the end")
        if r["after"] > 0.0005:
            bad.append(f"{where}: {r['after'] * 100:.2f}% of the frame is still "
                       f"changed once it finished; it left something behind")
    # And the case `restore` actually exists for: a clip cut off part-way,
    # which is what a rebuild does to whatever was in flight. Left alone, a
    # bell interrupted mid-swing leaves every settlement's banner hanging in
    # the air over the island for the rest of the round.
    cut = page.evaluate("""() => {
      const st = window.__st;
      const shot = () => {
        st.life.update(3, st.ctx());
        st.renderer.render(st.scene, st.camera);
        const s = document.createElement('canvas');
        s.width = 300; s.height = 187;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, 0, 0, s.width, s.height);
        return g.getImageData(0, 0, s.width, s.height).data;
      };
      const diff = (a, b) => {
        let n = 0;
        for (let i = 0; i < a.length; i += 4)
          if (Math.abs(a[i] - b[i]) + Math.abs(a[i+1] - b[i+1])
              + Math.abs(a[i+2] - b[i+2]) > 18) n++;
        return n / (a.length / 4);
      };
      st.clear();
      const bare = shot();
      const out = [];
      for (const e of [{kind: 'bell', episode: 1, lapsed: 2},
                       {kind: 'open', episode: 2, of: 3}]) {
        const c = st.fire(e);
        st.pause();
        c.t0 = 0;
        st.step(c.dur * 0.5);           // half way through, and then pulled
        st.clear();
        out.push([e.kind, diff(bare, shot())]);
      }
      return out;
    }""")
    for kind, left in cut:
        if left > 0.0005:
            bad.append(f"mechanics {kind}: cut off half way and {left * 100:.2f}% "
                       f"of the frame stayed changed; it kept what it borrowed")

    # A kind the island says nothing about must stay silent rather than throw.
    quiet = page.evaluate("""() => {
      const st = window.__st;
      return [{kind: 'said', author: 'T1'}, {kind: 'tick', left: 30}, {kind: 'over'}]
        .map(e => [e.kind, st.fire(e) === null]);
    }""")
    for kind, silent in quiet:
        if not silent:
            bad.append(f"mechanics {kind}: the island invented something to show")
    bad += [f"mechanics: {e}" for e in errs]
    page.screenshot(path=str(out / "mechanics.png"))
    page.close()
    return bad


def living(browser, base: str, board: Path, out: Path) -> list[str]:
    """The live path, driven.

    Everything else here replays a saved board. **Live is a different code
    path** -- rows arrive from a poll, there is no sidecar, no transport and no
    player -- and until now nothing exercised it: the island was rebuilt
    underneath it and the only thing that would have caught a break was
    somebody opening a game while it ran.

    A fake upstream stands in for the hub, because a real room lives about an
    hour and a test cannot have one.
    """
    rows = json.loads(board.read_text())["messages"][:34]   # mid-round
    state = {"hub": {"url": "test://hub", "workspace": "island-live-test"},
             "agents": [], "messages": [dict(m, channel="island") for m in rows]}

    class Upstream(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps(state).encode()
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    up = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=up.serve_forever, daemon=True).start()
    was, server_for(base).upstream = server_for(base).upstream, \
        f"http://127.0.0.1:{up.server_address[1]}"
    page = browser.new_page(viewport={"width": 1400, "height": 900},
                            reduced_motion="reduce")
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    try:
        page.goto(f"{base}/?live=api/state")
        page.wait_for_selector(".hut", timeout=15_000)
        page.wait_for_timeout(2200)
        seen = page.evaluate("""() => ({
          huts: document.querySelectorAll('.hut').length,
          cells: document.querySelectorAll('.hut .cell').length,
          modelled: document.querySelector('.app').classList.contains('has-3d'),
          where: (document.getElementById('where') || {}).textContent || '',
          // Live has no sidecar, so there is no score and the rail says why
          // rather than showing a blank one.
          locked: !!document.querySelector('#reveal-body.locked'),
          transport: getComputedStyle(document.getElementById('transport')).display,
        })""")
        page.screenshot(path=str(out / "live.png"))
    finally:
        page.close()
        server_for(base).upstream = was
        up.shutdown()

    where = "live"
    bad = [f"{where}: {e}" for e in errs]
    if seen["huts"] != 2 or not seen["cells"]:
        bad.append(f"{where}: {seen['huts']} huts and {seen['cells']} shelf cells "
                   f"from a poll; the board arrived and nothing drew it")
    if not seen["modelled"]:
        bad.append(f"{where}: no island under a live board")
    if "live" not in seen["where"]:
        bad.append(f"{where}: the page does not say it is live: {seen['where']!r}")
    if not seen["locked"]:
        bad.append(f"{where}: the hidden half is not locked; live has no sidecar "
                   f"and must not imply a score")
    if seen["transport"] != "none":
        bad.append(f"{where}: the replay transport is showing on a live board")
    return bad


def fallback(browser, base: str, board: Path, out: Path) -> list[str]:
    """A browser with no WebGL still gets an island.

    The model is the island now, and a page that cannot build one must not show
    an empty sea: the drawn world is still there and comes back. Checked by
    taking WebGL away rather than by trusting the `try` around the build --
    that is the one path no ordinary run exercises, and the failure it guards
    against looks exactly like a replay that would not load.
    """
    stem = board.name[len("board-"):-len(".json")]
    page = browser.new_page(viewport={"width": 1500, "height": 1000},
                            reduced_motion="reduce")
    page.add_init_script("""HTMLCanvasElement.prototype.getContext = new Proxy(
        HTMLCanvasElement.prototype.getContext,
        { apply: (f, t, a) => /webgl/i.test(a[0]) ? null : Reflect.apply(f, t, a) });""")
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(board_url(base, stem))
    page.wait_for_selector(".hut", timeout=15_000)
    page.wait_for_timeout(1400)
    seen = page.evaluate("""() => ({
      modelled: document.querySelector('.app').classList.contains('has-3d'),
      hidden: document.getElementById('stage').hidden,
      land: [...document.querySelectorAll('.land')]
        .filter(n => n.getBoundingClientRect().width > 0).length,
      huts: document.querySelectorAll('.hut').length,
      cells: document.querySelectorAll('.hut .cell').length,
    })""")
    page.screenshot(path=str(out / f"{stem}-no-webgl.png"))
    page.close()
    where = f"{stem} no-webgl"
    bad = [f"{where}: {e}" for e in errs]
    if seen["modelled"]:
        bad.append(f"{where}: the page claims a model it could not build")
    if not seen["hidden"]:
        bad.append(f"{where}: an empty canvas was left over the page")
    if seen["land"] != 1:
        bad.append(f"{where}: {seen['land']} drawn island(s); the fallback is not there")
    if not seen["huts"] or not seen["cells"]:
        bad.append(f"{where}: {seen['huts']} huts and {seen['cells']} shelf cells "
                   f"-- the replay itself stopped drawing")
    return bad


def mobile(browser, base: str, board: Path, out: Path) -> list[str]:
    """That the page works on a phone, which is where a shared link gets opened.

    Three things, none of which a desktop screenshot can show:

    * nothing scrolls sideways;
    * no two pieces of floating chrome sit on top of each other;
    * in portrait the island is not a thin band. The scene's viewBox is wide,
      so it used to fit to width and leave the trader cards -- the only part
      carrying information -- at about a third of a readable size, with dead
      sky above and dead sea below.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    for tag, w, h in PHONES:
        page = browser.new_page(viewport={"width": w, "height": h}, is_mobile=True,
                                has_touch=True, reduced_motion="reduce")
        errs: list[str] = []
        page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
                if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
        page.goto(board_url(base, stem))
        page.wait_for_selector(".hut", timeout=15_000)
        page.wait_for_timeout(1400)
        seen = page.evaluate("""(chrome) => {
          const box = (s) => { const n = document.querySelector(s);
            if (!n || n.hidden) return null;
            const r = n.getBoundingClientRect();
            return r.width && r.height ? { s, x: r.x, y: r.y, w: r.width, h: r.height } : null; };
          const land = document.querySelector('.land');
          const lb = land && land.getBoundingClientRect();
          // With a model up, the island is pixels rather than a path, so its
          // share of the screen is counted rather than measured off a box.
          // This also catches the render that produced nothing at all, which a
          // bounding box cannot: a canvas of the right size, and empty.
          const cv = document.getElementById('stage');
          let drawn = null, span = null;
          if (document.querySelector('.app').classList.contains('has-3d') && cv) {
            const cr = cv.getBoundingClientRect();
            const s = document.createElement('canvas');
            s.width = 200; s.height = Math.max(1, Math.round(200 * cr.height / cr.width));
            const g = s.getContext('2d');
            g.drawImage(cv, 0, 0, s.width, s.height);
            const px = g.getImageData(0, 0, s.width, s.height).data;
            let lit = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1;
            for (let y = 0; y < s.height; y++) for (let x = 0; x < s.width; x++) {
              if (px[(y * s.width + x) * 4 + 3] <= 24) continue;
              lit++;
              if (x < x0) x0 = x; if (x > x1) x1 = x;
              if (y < y0) y0 = y; if (y > y1) y1 = y;
            }
            drawn = lit / (s.width * s.height);
            if (lit) {
              // How big the island actually draws, against the shorter side of
              // the window -- which is the side it is fitted to.
              const bw = (x1 - x0 + 1) / s.width * cr.width;
              const bh = (y1 - y0 + 1) / s.height * cr.height;
              span = Math.max(bw, bh) / Math.min(innerWidth, innerHeight);
            }
          }
          return {
            scrollW: document.documentElement.scrollWidth, winW: innerWidth,
            winH: innerHeight, boxes: chrome.map(box).filter(Boolean),
            land: lb ? { w: lb.width, h: lb.height } : null, drawn, span,
            taps: [...document.querySelectorAll('button, select, .tab')]
              .filter(n => n.offsetParent !== null)
              .map(n => { const r = n.getBoundingClientRect();
                          return [n.id || n.textContent.trim().slice(0, 8), r.height]; })
              .filter(([, hh]) => hh < 34),
          };
        }""", CHROME)
        page.screenshot(path=str(out / f"{stem}-{tag}.png"), full_page=False)
        where = f"{stem} @{tag} {w}x{h}"

        if seen["scrollW"] > seen["winW"] + 1:
            bad.append(f"{where}: the page scrolls sideways "
                       f"({seen['scrollW']}px of content in {seen['winW']}px)")
        boxes = seen["boxes"]
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"]
                        and a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"]):
                    bad.append(f"{where}: {a['s']} and {b['s']} overlap")
        # Fitted to width in a tall window, the island was a thin band with dead
        # sky above and dead sea below.
        #
        # Measured as *how big the island draws*, not as its share of the
        # screen's area. Area was the right proxy while the island had the whole
        # frame; now that the cards stand in the margins and the transport has
        # its own room, a phone spends a third of its height on things that are
        # not island by design, and area cannot tell that apart from the band
        # this exists to catch. The span can: a band is a third of the short
        # side, and an island is most of it.
        if seen["drawn"] is not None and not seen["drawn"]:
            bad.append(f"{where}: the model drew nothing at all")
        elif seen["span"] is not None and seen["span"] < 0.72:
            bad.append(f"{where}: the island draws at {seen['span']:.0%} of the "
                       f"screen's short side; the picture is the page and this "
                       f"is a band in it")
        elif seen["drawn"] is None and seen["land"]:
            # No model: the drawn island is a path, and its own box is the size.
            share = max(seen["land"]["w"], seen["land"]["h"]) / min(seen["winW"], seen["winH"])
            if share < 0.72:
                bad.append(f"{where}: the drawn island is {share:.0%} of the "
                           f"screen's short side")
        for name, height in seen["taps"]:
            bad.append(f"{where}: {name!r} is {height:.0f}px tall, under a fingertip")
        if tag == "portrait":
            # Turning the phone rebuilds the island the other way up. Untested,
            # this is the kind of thing that silently keeps the tall viewBox in
            # landscape and looks fine in every screenshot taken upright.
            before = page.get_attribute("#island", "viewBox")
            page.set_viewport_size({"width": h, "height": w})
            page.wait_for_timeout(700)
            after = page.get_attribute("#island", "viewBox")
            tall = lambda v: (lambda a: a[2] < a[3])([float(x) for x in v.split()])
            if before == after:
                bad.append(f"{where}: rotating the phone left the viewBox at "
                           f"{after!r} -- the island did not turn with it")
            elif not (tall(before) and not tall(after)):
                bad.append(f"{where}: rotated from {before!r} to {after!r}, which is "
                           f"not tall-then-wide")
            elif not page.query_selector(".hut .cell"):
                bad.append(f"{where}: the island came back from a rotation empty")
        bad += [f"{where}: {e}" for e in errs]
        page.close()
    return bad


def bare(browser, base: str, board: Path, out: Path) -> list[str]:
    """A board opened with no reveal sidecar still reaches its ending.

    Live, there is no sidecar at all -- tastes are private and the seed is not
    posted -- so every utility on the closing card is unavailable. The card has
    to say that rather than throw, print `NaN`, or claim nobody beat autarky on
    the strength of numbers it does not have.
    """
    stem = board.name[len("board-"):-len(".json")]
    page = browser.new_page(viewport={"width": 1500, "height": 1000},
                            reduced_motion="reduce")
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(f"{base}/?board=replays/board-{stem}.json")   # no &reveal=
    page.wait_for_selector(".hut", timeout=10_000)
    total = int(page.eval_on_selector("#scrub", "e => Number(e.max)"))
    page.evaluate("i => { const s = document.getElementById('scrub');"
                  " s.value = String(i); s.dispatchEvent(new Event('input')); }", total)
    page.wait_for_timeout(1200)
    shown = page.evaluate("""() => {
      const box = document.getElementById('closing');
      if (!box || box.hidden) return null;
      return { verdict: box.querySelector('.verdict').textContent,
               rows: box.querySelectorAll('.ratio').length,
               body: box.textContent };
    }""")
    page.screenshot(path=str(out / f"{stem}-end-no-sidecar.png"))
    bad = [f"{stem} bare: {e}" for e in errs]
    if shown is None:
        bad.append(f"{stem} bare: no ending shown on a board without a sidecar")
    else:
        if "sidecar" not in shown["verdict"]:
            bad.append(f"{stem} bare: the card does not say why it has no numbers: "
                       f"{shown['verdict'].strip()!r}")
        if shown["rows"]:
            bad.append(f"{stem} bare: {shown['rows']} scored row(s) with no sidecar "
                       f"to score from")
        for junk in ("NaN", "undefined", "Infinity"):
            if junk in shown["body"]:
                bad.append(f"{stem} bare: the card prints {junk}")
    page.close()
    return bad


def ending(page, reveal, where: str) -> list[str]:
    """The round has an ending, and it says the right thing.

    A replay used to stop rather than finish: three episodes played, the sun
    went down, and what any of it came to sat behind a drawer. The numbers on
    the card are the ledger's own -- what each trader ended with as a multiple
    of never having traded -- so they are checkable here against the sidecar
    rather than taken on the page's word.
    """
    bad: list[str] = []
    shown = page.evaluate("""() => {
      const box = document.getElementById('closing');
      if (!box || box.hidden) return null;
      return { verdict: box.querySelector('.verdict').textContent.trim(),
               traffic: box.querySelector('#closing-traffic').textContent.trim(),
               rows: [...box.querySelectorAll('.ratio')].map(r => ({
                 text: (r.querySelector('.num') || {}).textContent || '',
                 under: r.classList.contains('under') })) };
    }""")
    if shown is None:
        return [f"{where}: the round ended and nothing said what it came to"]

    traj = reveal.get("round", {}).get("trajectory") or []
    alone = reveal.get("autarky_utility") or {}
    want = []
    for i, name in enumerate(sorted(alone)):
        total = sum(row[i] for row in traj)
        floor = len(traj) * alone[name]
        want.append(total / floor if floor else None)
    if len(shown["rows"]) != len(want):
        bad.append(f"{where}: {len(shown['rows'])} traders on the closing card, "
                   f"expected {len(want)}")
    for row, ratio in zip(shown["rows"], want):
        if ratio is None:
            continue
        # The number the ledger scores a trader on, to the digits shown.
        if f"{ratio:.2f}" not in row["text"]:
            bad.append(f"{where}: closing card shows {row['text']!r}, "
                       f"expected {ratio:.2f}x")
        # Below 1.00x is worse than never trading, and must read as such.
        if (ratio < 1) != row["under"]:
            bad.append(f"{where}: {ratio:.2f}x is marked "
                       f"{'under' if row['under'] else 'fine'}, which is backwards")
    if want and all(r is not None and r < 1 for r in want) \
            and "beat playing alone" not in shown["verdict"]:
        bad.append(f"{where}: every trader finished below autarky and the card "
                   f"does not say so: {shown['verdict']!r}")
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
