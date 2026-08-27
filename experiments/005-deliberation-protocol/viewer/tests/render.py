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
import math
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
      //: The whole drawn world, not one class of it. `.shallows` was left out
      //: of the stylesheet's hide rule and drew a pale ring over the model for
      //: as long as there has been a model, because this asked about `.land`
      //: alone -- one member of the group it belongs to.
      ghosts: Object.fromEntries(['land', 'wet', 'square', 'water', 'sea-fill', 'surf', 'shallows',
         'grain-fill', 'fire', 'firelight', 'hut-shadow', 'roof',
         'roof-thatch', 'wall', 'window', 'door', 'hut-rim']
        .map(c => [c, [...document.querySelectorAll('.' + c)]
          .filter(n => n.getBoundingClientRect().width > 0
                    && getComputedStyle(n).display !== 'none').length])
        .filter(([, n]) => n)),
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
        ghosts = dict(counts["ghosts"], palms=counts["palmCount"])
        for ghost, n in sorted(ghosts.items()):
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
    read = """() => [...document.querySelectorAll('.hut .cell')]
      .filter(c => c.classList.contains('empty'))
      .map(c => {
        const q = c.querySelector('.qty');
        const zero = c.querySelector('.bar-zero');
        return { good: c.dataset.good, text: q ? q.textContent : null,
                 flagged: q ? q.classList.contains('none') : false,
                 mark: zero ? getComputedStyle(zero).opacity : null };
      })"""
    slots = page.evaluate(read)
    #: The mark fades in over 0.3s, and this reads the *computed* opacity --
    #: so a sample taken while the transition is still running is a number
    #: about how loaded the machine is. It flaked exactly that way: three
    #: slots at opacity 0 in one run and none in the next, on the same commit.
    #:
    #: Waited out rather than loosened. A transition that has finished does
    #: not go back down, so a second read after longer than its own duration
    #: is the settled value, and a mark that is genuinely never shown is still
    #: at zero when it arrives.
    if any(s["mark"] is not None and float(s["mark"]) < 0.5 for s in slots):
        page.wait_for_timeout(500)
        slots = page.evaluate(read)
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
            for board in boards:
                problems += overhead(browser, base, board, out)
            problems += bare(browser, base, boards[0], out)
            problems += mobile(browser, base, boards[0], out)
            problems += focusing(browser, base, boards[0], out)
            problems += fallback(browser, base, boards[0], out)
            problems += living(browser, base, boards[0], out)
            problems += alive(browser, base, boards[0], out)
            problems += turning(browser, base, boards[0], out)
            problems += uncovered(browser, base, boards[0], out)
            problems += afloat(browser, base, boards[0], out)
            problems += nightfall(browser, base, out)
            problems += clockwork(browser, base, out)
            for board in boards:
                problems += travelling(browser, base, board, out)
            problems += stock(browser, base, out)
            problems += carrying(browser, base, out)
            problems += island(browser, base, out)
            problems += whose(browser, base, out)
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


#: Freeze a bubble half way up and read where it is.
#:
#: Frozen because it lives 1.3 to 1.5 seconds and a click through the driver
#: costs most of that: measured live, the first reading came back at t=1400 of
#: 1500 with the thing already faded to two per cent, which is a check that
#: passes or fails on how busy the machine is. `currentTime` puts it at the top
#: of its rise, where a viewer sees it.
OVERHEAD = """(want) => {
  for (const a of document.getAnimations()) {
    const n = a.effect?.target;
    if (n && n.classList && n.classList.contains('pop')) { a.pause(); a.currentTime = 500; }
  }
  //: Read off the SVG's own transform list rather than by parsing the
  //: attribute. A regex over `translate(x y)` is one backslash away from
  //: matching nothing and returning whatever the fallback was, which is how
  //: the first cut of this passed against a deliberately broken page.
  const spot = (n) => {
    const m = n && n.transform && n.transform.baseVal.consolidate();
    return m ? [m.matrix.e, m.matrix.f] : null;
  };
  const at = document.querySelector('.pop-at');
  if (!at) return { error: 'no bubble was drawn at all' };
  const who = at.getAttribute('data-trader');
  const here = spot(at);
  if (!here) return { error: 'the bubble is not placed by a transform' };
  const pin = document.querySelector(`.tether[data-trader="${who}"] .tether-pin`);
  const hut = document.querySelector(`.hut[data-trader="${who}"]`);
  return {
    who, at: here,
    kinds: [...document.querySelectorAll('.pop')].map(n => n.getAttribute('class')),
    pin: pin ? [+pin.getAttribute('cx'), +pin.getAttribute('cy')] : null,
    card: spot(hut),
    cross: !!document.querySelector('.pop-cross'),
    dots: document.querySelectorAll('.pop-dot').length,
    want,
  };
}"""


def overhead(browser, base: str, board: Path, out: Path) -> list[str]:
    """A refusal and a remark are drawn over the settlement, not over the card.

    **Reported by eye.** They are things a *trader* did, and the trader on this
    page is the hut standing on the island -- the card is the ledger beside it,
    out in the frame's margin. The bubbles were placed at `seats`, which is the
    card once there is a model, so the one picture that says "this one just
    spoke" appeared a third of a frame away from the thing that spoke.

    Two statements. The bubble opens over the settlement, and it is **still**
    over it a second later: the camera goes right round the island every
    hundred and fifty seconds, so a bubble pinned once at the moment it opened
    drifts off the roof it belongs to while it is still on screen.

    Measured against the tether pin, which is where the page itself thinks the
    settlement is, and against the card's own transform -- so this fails both
    ways round: a bubble at the card is far from the pin, and a check that read
    the wrong node would find them equal.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(board_url(base, stem))
    page.wait_for_selector(".hut", timeout=15_000)
    page.wait_for_timeout(1800)
    if not page.evaluate("() => document.querySelector('.app')"
                         ".classList.contains('has-3d')"):
        page.close()
        return []
    marks = """async (url) => {
      const { reduce } = await import('./reducer.js');
      const t = reduce((await (await fetch(url)).json()).messages, {});
      const out = {};
      t.frames.forEach((f, k) => {
        if (f.event?.kind === 'refused' && out.bad === undefined) out.bad = k;
        if (f.event?.kind === 'said' && !f.event.attempt && out.talk === undefined) {
          out.talk = k;
        }
      });
      return out;
    }"""
    found = page.evaluate(marks, f"replays/{board.name}")
    #: **A remark is not on either replay this repo keeps**, and the talk
    #: bubble is half of what this exists to check. The page serves every tree
    #: `serve.py:ROOTS` names, so the listing is asked for a board that does
    #: have one and it is opened for that half. Whether that found anything is
    #: printed either way: a check that quietly examined one of the two kinds
    #: and said nothing would read as having examined both.
    def elsewhere():
        """The first board this page serves that has a plain remark on it."""
        return page.evaluate("""async (m) => {
          const list = await (await fetch('api/boards', {cache: 'no-store'})).json();
          const look = new Function('url', 'return (' + m + ')(url)');
          for (const b of (list.boards || []).slice(0, 60)) {
            try {
              const at = await look(b.board);
              if (at.talk !== undefined) return { board: b.board, at: at.talk };
            } catch { /* a board this page cannot read is not this check's business */ }
          }
          return null;
        }""", marks)

    #: The refusal first, on the board this was opened with, and only then the
    #: search for a remark -- which navigates. The other way round left the
    #: refusal being looked for on a board that does not contain it, and the
    #: check reported no bubble at all rather than the wrong board.
    for kind in ("bad", "talk"):
        at = found.get(kind)
        where = f"{stem} overhead {kind}"
        if at is None and kind == "talk":
            other = elsewhere()
            if other:
                page.goto(f"{base}/?board={other['board']}")
                page.wait_for_selector(".hut", timeout=15_000)
                page.wait_for_timeout(1800)
                at = other["at"]
                print(f"NOTE {where}: driven from {other['board']}")
        if at is None:
            # Said out loud rather than skipped in silence: no board this page
            # can see has a frame of that kind.
            print(f"NOTE {where}: no board served here has one; not checked")
            continue
        page.evaluate("""(i) => { const s = document.getElementById('scrub');
          s.value = String(i); s.dispatchEvent(new Event('input')); }""", at - 1)
        page.wait_for_timeout(900)
        page.click("#fwd")
        page.wait_for_timeout(250)
        seen = page.evaluate(OVERHEAD, kind)
        if seen.get("error"):
            bad.append(f"{where}: {seen['error']}")
            continue
        if seen["pin"] is None or seen["card"] is None:
            bad.append(f"{where}: no pin or card for {seen['who']} to measure against")
            continue
        near = math.dist(seen["at"], seen["pin"])
        far = math.dist(seen["at"], seen["card"])
        #: In viewBox units, where the island is about 700 across. A bubble is
        #: hung *at* the settlement and rises from there, so the anchor should
        #: be on the pin and not merely nearer to it than to the card.
        if near > 3:
            bad.append(f"{where}: the bubble is {near:.0f} from {seen['who']}'s "
                       f"settlement and {far:.0f} from its card; it is not "
                       f"drawn over the hut")
        elif far < 60:
            bad.append(f"{where}: {seen['who']}'s settlement and card are only "
                       f"{far:.0f} apart, so this frame cannot tell them apart")
        # The right mark for the right thing: a cross for a refusal, and for a
        # remark three dots that say a trader spoke without saying what.
        if kind == "bad" and not seen["cross"]:
            bad.append(f"{where}: a refusal drew no cross")
        if kind == "talk" and seen["dots"] < 3:
            bad.append(f"{where}: a remark drew {seen['dots']} dot(s), not three")
        # And it goes with the settlement as the camera turns.
        page.wait_for_timeout(1400)
        moved = page.evaluate(OVERHEAD, kind)
        if moved.get("error") or moved["pin"] is None:
            bad.append(f"{where}: the bubble was gone before the camera moved")
            continue
        drift = math.dist(moved["at"], moved["pin"])
        turned = math.dist(moved["pin"], seen["pin"])
        if turned < 1:
            bad.append(f"{where}: the camera did not move ({turned:.1f}), so "
                       f"nothing checked that the bubble follows")
        elif drift > 3:
            bad.append(f"{where}: the settlement moved {turned:.0f} and the "
                       f"bubble stayed behind ({drift:.0f} off it)")
    page.screenshot(path=str(out / f"overhead-{stem}.png"))
    page.close()
    return bad + [f"{stem} overhead: {e}" for e in errs]



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


#: What counts as *island* in a canvas that is now sea from edge to edge.
#:
#: This used to be "any opaque pixel": the model drew on a transparent canvas
#: and the only thing on it was the island and a disc of water a little wider
#: than its shore, so opacity and island were the same question. The sea now
#: runs to the corners of the frame -- open water rather than a void was asked
#: for, and it is what a spectator gets -- and under the old rule every pixel
#: on the page is island, which makes "the card is standing on the island" true
#: of every card and the check worthless.
#:
#: So it is asked by colour, of the two things the island is actually made of.
#: The water is the only strongly blue surface a spectator sees a lot of
#: (`sea` #36718f, `sea_deep` #244a63, and both stay blue under every hour's
#: light because the fill is the sea's own colour); grass, sand, rock, thatch
#: and surf are all warm or neutral. A blue *crate* is read as water, which
#: only ever makes this more forgiving, never less.
#:
#: A card over open sea is fine and always was -- the cards live in the frame's
#: margins, and the margins are water. What is not fine is a card over the
#: land, which is the picture the page exists to show.
LAND_JS = """
  const LAND = (px, i) => px[i + 3] > 40
    && !(px[i + 2] > px[i] + 16 && px[i + 2] > px[i + 1] + 4);
"""


#: Reading the model's own pixels. Everything the life layer does is in the
#: canvas and none of it is in the DOM, so the alternative was a test handle on
#: the shipped page -- and a check that measures what a viewer sees is better
#: than one that measures what the page exposes to be measured.
#:
#: **The land, not the water.** This used to average every opaque pixel, which
#: was the island and the disc of sea a little wider than its shore. The sea
#: now runs to the corners of the frame, and it is the one surface on the page
#: that goes *bluer* as the sun sets -- the fill is the sea's own colour and
#: dusk turns it indigo -- so an average over the whole canvas is mostly water
#: fighting the thing being measured, and the island's warming at dusk came out
#: as no change at all. `LAND_JS` is the same classifier the card checks use.
SAMPLE = """() => {""" + LAND_JS + """
  const cv = document.getElementById('stage');
  const s = document.createElement('canvas');
  s.width = 96; s.height = Math.max(1, Math.round(96 * cv.height / cv.width));
  const g = s.getContext('2d');
  g.drawImage(cv, 0, 0, s.width, s.height);
  const px = g.getImageData(0, 0, s.width, s.height).data;
  let lum = 0, warm = 0, lit = 0;
  for (let i = 0; i < px.length; i += 4) {
    if (!LAND(px, i)) continue;
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


#: How far the letterbox band may be from the water inside the frame, per
#: channel, before it reads as a seam.
#:
#: **Measured, not inherited.** It was 12, carried over from when the band was
#: painted by a clear colour and could plausibly be a stop out. The band is the
#: same mesh under the same lights now, and the shipped gap is *exactly zero* on
#: both shapes that have one -- rgb(32,63,82) against rgb(32,63,82). Twelve was
#: loose enough to pass a deliberately mis-tinted band: tinting the backdrop
#: pass 30% brighter gives rgb(37,72,93), a gap of 11, which is a visible line
#: down the side of the screen and was being called clean.
SEAM = 4


def afloat(browser, base: str, board: Path, out: Path) -> list[str]:
    """The frame is water to its edges -- there is no void round the island.

    The renderer draws into the letterboxed rectangle the `<svg>` fits its
    viewBox into, and for a long time the bands beside or above that rectangle
    were simply not drawn: the page's dark backing showed through them, and on
    any window whose shape did not match the viewBox's, the island sat in a
    hole with a strip of it above and below. Reported by eye, twice -- once as
    "the whole background beyond the island should just be the sea", and once
    as a frozen bar across the top with clouds cut in half in it, which was the
    same band keeping a strip of an older frame because a scissored clear only
    clears inside the scissor.

    Both are the same fact and this is the fact: **no pixel of the canvas is
    unpainted.** Measured in five shapes, because the band only exists when
    the canvas and the viewBox disagree and a square window has none.

    **Two of the five are phones, and they are here because the void came back
    a third time through the shape nothing measured.** The sea is a disc 32
    units across, which covered every frame this had ever been pointed at --
    all three of them desktop-shaped, where the island's box is most of the
    frame. A phone in portrait is not: the box is a fraction of a tall frame,
    so the frustum is `8.7 * geo.h / D` island units deep, which on a 393x660
    window is 29 and at a card focus 36. Past 16 there was nothing to draw and
    the corners came back black -- and the alpha rule could not see it, because
    a corner cleared to black is painted. The colour rule is what catches it,
    and is why the corners are compared against the frame's own water rather
    than only counted.

    Two colour rules on top of that, and they are different questions.

    **Every corner is sea.** Not "is painted" -- a corner cleared to black is
    painted, which is how the void got past the alpha rule -- but *is water*, by
    the same classifier the rest of the suite reads land with. The corners and
    not the edge midpoints: the island is a disc inscribed in the frame's short
    side, so nothing is ever drawn in a corner, while a cloud crossing the
    island sits on the top edge on a tall window, which is weather.

    **And where there is a letterbox band, it is the same water as the frame.**
    That is the seam a band painted from a second copy of the day's arithmetic
    showed, drifting half a stop at noon. It is asked *at the band*, which is
    the only place the seam can be: this used to compare the corners against a
    point 2% in at half height and call it open water, which stopped being true
    the moment a phone could draw the island the full width of the frame -- the
    point landed on the shore shelf and the check failed on a page that was
    correct. Where the canvas and the viewBox are the same shape there is no
    band and nothing to compare, and this says so rather than passing quietly.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    #: The shapes with no letterbox band, so that "all of them" can be caught.
    bands: list[str] = []
    for label, w, h in (("wide", 1600, 700), ("tall", 820, 1100), ("desktop", 1300, 860),
                        ("phone", 393, 660), ("phone-tall", 390, 844)):
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(board_url(base, stem))
        page.wait_for_selector(".hut", timeout=15_000)
        page.wait_for_timeout(2000)
        if not page.evaluate("() => document.querySelector('.app')"
                             ".classList.contains('has-3d')"):
            page.close()
            continue
        seen = page.evaluate("""() => {""" + LAND_JS + """
          const cv = document.getElementById('stage');
          const s = document.createElement('canvas');
          s.width = cv.width; s.height = cv.height;
          s.getContext('2d').drawImage(cv, 0, 0);
          const g = s.getContext('2d');
          const px = g.getImageData(0, 0, s.width, s.height).data;
          let clear = 0;
          for (let i = 3; i < px.length; i += 4) if (px[i] < 250) clear++;
          //: **The corners, and the median of a block of each.**
          //:
          //: A single sample at the top-middle of the frame caught a *cloud*
          //: -- they fly at four and a half units and cross the island, so on
          //: a tall window one sits on the frame's own top edge, which is not
          //: a seam and not a fault. The corners are the one place nothing is
          //: ever drawn: the island is a disc inscribed in the short side, so
          //: it cannot reach them at any aspect, and neither can the weather
          //: that crosses it. A median over a block shrugs off a stray pixel.
          const block = (fx, fy) => {
            const n = 12;
            const x = Math.round((s.width - n) * fx), y = Math.round((s.height - n) * fy);
            const d = g.getImageData(x, y, n, n).data;
            const chan = (k) => {
              const v = [];
              for (let i = 0; i < d.length; i += 4) v.push(d[i + k]);
              v.sort((a, b) => a - b);
              return v[v.length >> 1];
            };
            return [chan(0), chan(1), chan(2)];
          };
          //: Water, by the classifier the rest of the suite reads land with.
          //: Black is *land* to it -- blue is what it excludes -- which is
          //: exactly why a corner cleared to black fails this and passed the
          //: alpha rule above.
          const wet = (c) => !LAND([c[0], c[1], c[2], 255], 0);
          //: The letterbox band, if the canvas and the viewBox disagree about
          //: their shape. Computed from the two of them rather than read off
          //: the stage, which a real replay page does not expose.
          const vb = document.getElementById('island').getAttribute('viewBox')
            .split(/\s+/).map(Number);
          const k = Math.min(s.width / vb[2], s.height / vb[3]);
          const side = (s.width - vb[2] * k) / 2, cap = (s.height - vb[3] * k) / 2;
          let band = null;
          if (side >= 8) {
            band = { out: block(0, 0.5),
                     in: [Math.round(side + 6), Math.round(s.height / 2) - 6] };
          } else if (cap >= 8) {
            band = { out: block(0.5, 0), in: [Math.round(s.width / 2) - 6,
                                              Math.round(cap + 6)] };
          }
          if (band) {
            const d = g.getImageData(band.in[0], band.in[1], 12, 12).data;
            const chan = (kk) => { const v = [];
              for (let i = 0; i < d.length; i += 4) v.push(d[i + kk]);
              v.sort((a, b) => a - b); return v[v.length >> 1]; };
            band.inside = [chan(0), chan(1), chan(2)];
          }
          const corners = [block(0, 0), block(1, 0), block(0, 1), block(1, 1)];
          return { clear, total: px.length / 4, corners, band,
                   dry: corners.map(wet) };
        }""")
        page.close()
        if seen["clear"]:
            bad.append(f"afloat {label}: {seen['clear']} of {seen['total']} pixels "
                       f"are unpainted; the island is standing in a void")
        for k, ok in enumerate(seen["dry"]):
            if not ok:
                e = seen["corners"][k]
                bad.append(f"afloat {label}: corner {k} is rgb({e[0]},{e[1]},"
                           f"{e[2]}), which is not sea; the frame runs out of "
                           f"water before it runs out of frame")
        b = seen["band"]
        if b:
            gap = max(abs(b["out"][i] - b["inside"][i]) for i in range(3))
            if gap > SEAM:
                bad.append(f"afloat {label}: the letterbox band is rgb("
                           f"{b['out'][0]},{b['out'][1]},{b['out'][2]}) against "
                           f"the frame's own water rgb({b['inside'][0]},"
                           f"{b['inside'][1]},{b['inside'][2]}); the join shows")
        else:
            bands.append(label)
    #: Said rather than passed over. The seam rule only has something to look at
    #: where the canvas and the viewBox disagree about their shape, and a suite
    #: in which that is true of *every* shape has stopped asking the question.
    if len(bands) == 5:
        bad.append(f"afloat: no shape measured has a letterbox band "
                   f"({', '.join(bands)}); the seam rule looked at nothing")
    return bad


def nightfall(browser, base: str, out: Path) -> list[str]:
    """A new round does not open in the last round's dark.

    The key, the ambient and the fill belong to the stage and outlive the
    island, so a round watched to its bell leaves them at dusk. `day` is
    `null` on a board whose schedule line the page cannot read, and the rule
    for `null` is to leave the light alone -- not knowing the hour is not the
    same as it being dawn. Between them: a second replay that played from its
    first frame to its last in the previous round's night.

    Reported by eye as "daylight hasn't changed" on a second replay. The rule
    is kept, and narrowed: an island that has *never* been told the hour gets
    the middle of the day, and only one that has been told holds what it was
    told.
    """
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 900, "height": 600})
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    page.evaluate(STAGE, {"w": 900, "h": 600, "n": 2, "portrait": False,
                          "goods": ["bread", "cloth", "iron", "salt"]})
    seen = page.evaluate("""(goods) => {
      const st = window.__st;
      const lum = () => {
        st.render();
        const s = document.createElement('canvas');
        s.width = 90; s.height = 60;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, 0, 0, 90, 60);
        const px = g.getImageData(0, 0, 90, 60).data;
        let sum = 0;
        for (let i = 0; i < px.length; i += 4) sum += (px[i] + px[i+1] + px[i+2]) / 3;
        return sum / (px.length / 4);
      };
      // A round played to its bell.
      st.setDay(1);
      st.life.update(1, st.ctx());
      const dusk = lum();
      // The next round, on a board whose clock this page cannot read.
      st.build({ traders: ['T1', 'T2'], goods });
      st.setDay(null);
      st.life.update(2, st.ctx());
      const next = lum();
      // And the round after that, whose clock it can: the hold still holds.
      st.setDay(1);
      st.life.update(3, st.ctx());
      const told = lum();
      st.setDay(null);
      st.life.update(4, st.ctx());
      return { dusk, next, told, held: lum() };
    }""", ["bread", "cloth", "iron", "salt"])
    page.close()
    if not (seen["next"] > seen["dusk"] + 12):
        bad.append(f"nightfall: a new round opened at {seen['next']:.0f} against "
                   f"the last one's dusk at {seen['dusk']:.0f}; it inherited the "
                   f"night it was built on top of")
    if abs(seen["held"] - seen["told"]) > 4:
        bad.append(f"nightfall: an island that was told the hour did not hold it "
                   f"when the clock went quiet ({seen['told']:.0f} -> "
                   f"{seen['held']:.0f}); a dropped poll should not move the sun")
    return bad



def uncovered(browser, base: str, board: Path, out: Path) -> list[str]:
    """Nothing the page floats stands on the island -- no card, and no pill.

    The chrome half was reported by eye, twice. The pills stack into four rows
    on a phone because there is no width to put them side by side, and all four
    sat over the island's top edge: the round's state, the counts and the goods
    key, across the shore and the hill. The layout reserves a band for them now
    (`--chrome-top` in the stylesheet, spent by `cardPlan`), and this is what
    says the band is the right size -- measured off the model's own pixels
    rather than off the two numbers agreeing, because a band that matches a
    stylesheet it no longer describes agrees with itself.

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
        seen = page.evaluate("""() => {""" + LAND_JS + """
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
            for (let i = 0; i < px.length; i += 4) if (LAND(px, i)) on++;
            return { name, over: on / (bw * bh), off: false };
          });
        }""")
        pills = page.evaluate("""(chrome) => {""" + LAND_JS + """
          const cv = document.getElementById('stage');
          const cr = cv.getBoundingClientRect();
          const s = document.createElement('canvas');
          s.width = cv.width; s.height = cv.height;
          s.getContext('2d').drawImage(cv, 0, 0);
          const g = s.getContext('2d');
          const sx = cv.width / cr.width, sy = cv.height / cr.height;
          // What the island covers of the canvas, to divide by: a pill over a
          // tenth of a *frame* means nothing, and a pill over a tenth of the
          // island means the island is being hidden. Counted at the same
          // sampling as the pills so the two are the same measurement.
          let world = 0;
          {
            const px = g.getImageData(0, 0, s.width, s.height).data;
            for (let i = 0; i < px.length; i += 4) if (LAND(px, i)) world++;
          }
          return { world, pills: chrome.map(sel => {
            const n = document.querySelector(sel);
            if (!n || n.hidden) return null;
            const r = n.getBoundingClientRect();
            const x = Math.max(0, Math.round((r.x - cr.x) * sx));
            const y = Math.max(0, Math.round((r.y - cr.y) * sy));
            const bw = Math.min(s.width - x, Math.round(r.width * sx));
            const bh = Math.min(s.height - y, Math.round(r.height * sy));
            if (bw <= 0 || bh <= 0) return null;
            const px = g.getImageData(x, y, bw, bh).data;
            let on = 0;
            for (let i = 0; i < px.length; i += 4) if (LAND(px, i)) on++;
            return { sel, on };
          }).filter(Boolean) };
        }""", CHROME)
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
        #: A fortieth of the island, per pill. Not zero: the sea disc is
        #: soft-edged and a pill in a corner catches the outermost ring of it,
        #: and on a desktop the legend sits in the bottom corner where there is
        #: open water. A pill over more of the island than that is standing on
        #: the land the page exists to show.
        for r in pills["pills"]:
            share = r["on"] / max(1, pills["world"])
            if share > 0.025:
                bad.append(f"uncovered {label}: {r['sel']} covers "
                           f"{share * 100:.0f}% of the drawn island")
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


#: Does the offer's dashed line actually travel, and which way.
ROPE_DASH = """async () => {
  const pick = () => document.querySelector('.rope .rope-line');
  const line = pick();
  if (!line) return {has: false};
  const g = line.closest('.rope');
  const label = g.querySelector('.chip-pid')?.textContent || '';
  const maker = (label.split('\u00b7').pop() || '').split('\u2192')[0].trim();
  const nums = (line.getAttribute('d') || '').match(/-?[\d.]+/g)?.map(Number) || [];
  // Each tether's group carries its trader; the pin inside it is where that
  // settlement is drawn this frame.
  const dot = document.querySelector(`.tether[data-trader="${maker}"] .tether-pin`);
  const pin = dot ? [+dot.getAttribute('cx'), +dot.getAttribute('cy')] : null;
  const off = () => parseFloat(getComputedStyle(pick()).strokeDashoffset) || 0;
  //: **The animation's own clock, not the dash offset.** `stroke-dashoffset`
  //: is a *painted* value: Chromium throttles the paint when the machine is
  //: busy, so on a loaded box the offset crawled 0.31 in six hundred
  //: milliseconds against a floor of 0.5 and the check failed for being run
  //: alongside the rest of the suite. `currentTime` tracks the document
  //: timeline instead, so it advances whether or not a frame was drawn -- and
  //: it still catches the bug this exists for, because a rope rebuilt under
  //: its own animation gets a *fresh* animation whose clock starts at zero.
  const clock = () => pick()?.getAnimations()[0]?.currentTime ?? null;
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const before = off();
  const t0 = clock();
  let rebuilt = 0;
  for (let k = 0; k < 6; k++) {
    await new Promise(r => setTimeout(r, 100));
    if (pick() !== line) rebuilt++;
  }
  const after = off();
  const t1 = clock();
  return {has: true, before, after, rebuilt, t0, t1,
          moved: t0 !== null && t1 !== null && t1 - t0 > 200,
          fromMaker: pin ? dist(nums.slice(0, 2), pin) < dist(nums.slice(-2), pin) : null};
}"""


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
            # **The offer's line crawls toward the trader it is addressed to.**
            #
            # Two things have to hold and neither shows in a screenshot. The
            # dashes are a CSS animation, so the rope has to be the *same node*
            # from one frame to the next -- `follow` runs on every frame the
            # camera turns and used to rebuild every rope, which restarted the
            # animation sixty times a second and left the line sitting still.
            # And the path has to be written from the maker to the taker,
            # because a negative dash offset advances along it.
            dash = page.evaluate(ROPE_DASH)
            if dash and dash.get("has"):
                if not dash["moved"]:
                    bad.append(f"{where}: the offer's crawl did not advance in "
                               f"600ms (its own clock went {dash['t0']} -> "
                               f"{dash['t1']}, the offset {dash['before']:.2f} "
                               f"-> {dash['after']:.2f}); the line is being "
                               f"rebuilt under its own animation")
                if dash["rebuilt"]:
                    bad.append(f"{where}: the offer's rope was replaced "
                               f"{dash['rebuilt']} time(s) while the camera "
                               f"turned; a fresh node restarts the crawl")
                if dash["fromMaker"] is False:
                    bad.append(f"{where}: the rope is drawn from the taker to "
                               f"the maker, so its dashes crawl back toward the "
                               f"trader making the offer")
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
  const { layout } = await import('./scene.js');
  // The same bands the page reserves, read the same way the page reads them.
  // A stage built without them frames the island where nothing on the real
  // page ever frames it, and every question asked of it is then about a
  // layout nobody sees.
  const css = getComputedStyle(document.documentElement);
  const band = (nm) => Math.min(0.35, (parseFloat(css.getPropertyValue(nm)) || 0) / h);
  const chrome = { top: band('--chrome-top'), foot: band('--chrome-foot') };
  const geo = layout(n, portrait, portrait ? Math.floor(w / h * 100) / 100 : w / h,
                     chrome);
  const st = new Stage(cv, geo);
  st.pause();
  const traders = Array.from({length: n}, (_, i) => `T${i + 1}`);
  const made = st.build({traders, goods});
  st.pause();
  //: **After the build, which is the order the page does it in.** `build()`
  //: forgets the hour on purpose -- a new round must not open in the last
  //: one's dark -- and it lights the island once before returning, so a day
  //: set before it is thrown away and the still shots come out at whatever
  //: `island-life` gives an island nobody has told the time to.
  st.setDay(0.45);
  st.life.update(0, st.ctx());
  // What is directly under a point, ignoring anything standing on the ground
  // rather than being it.
  const ray = new THREE.Raycaster(), down = new THREE.Vector3(0, -1, 0);
  const SKIP = /^(settlement_|hut_|trails?$|trail_|tree_|palm_|marker_|site_|smoke_|goat_|gull_|cloud_|leaf_|ripple_|surf_|crate|ring|puff_|labour_)/;
  const chain = (o) => { const ns = []; for (let k = o; k && k !== made.island; k = k.parent) ns.push(k.name || '?'); return ns; };
  window.__under = (x, z) => {
    ray.set(new THREE.Vector3(x, 8, z), down);
    const hit = ray.intersectObject(made.island, true)
      .filter(h => !chain(h.object).some(nm => SKIP.test(nm)))[0];
    return hit ? hit.object.name : 'nothing';
  };
  window.__st = st;
  window.__made = made;
  // Where the island's own silhouette lands in the scene's coordinates.
  //
  // Everything but the weather: clouds, gulls and falling leaves are over the
  // island rather than part of it, and one of them at the top of the frame is
  // not the island being cut. Everything else counts, and the trees do most of
  // the work -- the camera is tilted, so a tree on the far shore projects well
  // above the water it stands beside.
  //
  // Its actual vertices, not a bounding box round them: the box's top corner
  // is where the tallest tree's height meets the widest sea's radius, and
  // nothing is there. Sampled every few vertices, which is plenty for a
  // silhouette made of hundreds.
  //
  // **At every bearing, not the one it was built at.** The camera goes round
  // the island, and the silhouette is a different shape from each side -- the
  // hill is on one side of it and the dock on another. Measured at the bearing
  // it happens to start from, the island looks clear of the frame and then
  // rises out of it a minute later.
  //: `sea` is excluded with the weather, and for the same reason: **it is not
  //: the island.** It used to be the outermost thing the model drew -- a disc
  //: of water a little wider than the shore -- so its edge was a fair stand-in
  //: for the island's own outline. It is sixteen units across now, wider than
  //: any frame this page has, because open water to the edge of the picture is
  //: what a spectator asked for instead of a void. Left in, it makes the
  //: "silhouette" the whole canvas and every question below unanswerable.
  //: What is left is the coast: shallows, surf, shelf, beach, and the land.
  //: **`swell` and the dolphins go with it, for the same reason.** The swell
  //: is the sea's own surface -- seventeen units of it, wider than any frame
  //: -- and a pod passing out in the open water is no more the island's
  //: outline than a gull over it is. Left in, they put the "silhouette" at the
  //: edge of the picture and every question below is unanswerable again: the
  //: check reported the island drawn under the chrome on four frame shapes,
  //: measuring water.
  const WEATHER = /^(cloud_|gull_|leaf_|smoke_|puff_|dolphin_|sea$|swell$)/;
  const meshes = [];
  for (const part of made.island.children) {
    if (WEATHER.test(part.name)) continue;
    part.updateWorldMatrix(true, true);
    part.traverse((node) => {
      if (node.geometry && node.geometry.attributes.position) meshes.push(node);
    });
  }
  const v = new THREE.Vector3();
  const was = st.turn;
  let top = Infinity, bottom = -Infinity;
  for (let k = 0; k < 12; k++) {
    st.aim(was + (k / 12) * Math.PI * 2);
    for (const node of meshes) {
      const pos = node.geometry.attributes.position;
      for (let i = 0; i < pos.count; i += 7) {
        v.fromBufferAttribute(pos, i).applyMatrix4(node.matrixWorld);
        const p = st.toViewBox(v);
        if (p.y < top) top = p.y;
        if (p.y > bottom) bottom = p.y;
      }
    }
  }
  st.aim(was);
  //: **Every mesh that casts a shadow, against the box the shadow camera
  //: covers.** A caster wider than that box has its shadow map clipped by the
  //: frustum's own edge, which is a straight line laid across whatever it
  //: falls on -- and a *flat* caster that wide is worse still, because from a
  //: light forty-five degrees up its far side is nearer the light than the
  //: island is, so it wins the texels the island needs and shadows it. That is
  //: what the sea disc was doing: a dark rectangle on the meadow, crawling as
  //: the light swung, reported by eye and traced here.
  const shadowBox = { ...st.key.shadow.camera };
  const casters = [];
  {
    const b = new THREE.Box3();
    made.island.traverse((n) => {
      if (!n.isMesh || !n.castShadow) return;
      b.setFromObject(n);
      const reach = Math.max(Math.abs(b.min.x), Math.abs(b.max.x),
                             Math.abs(b.min.z), Math.abs(b.max.z));
      casters.push({ name: n.name, reach: +reach.toFixed(2) });
    });
  }

  // Where each of the island's big horizontal surfaces starts and stops, so a
  // check can ask whether two of them share a plane. Names, not everything:
  // these are the ones that overlap each other across the whole coast.
  const decks = {};
  for (const nm of ['sea', 'shallows', 'shore_shelf', 'beach', 'meadow', 'upland']) {
    const o = made.island.getObjectByName(nm);
    if (!o) continue;
    const b = new THREE.Box3().setFromObject(o);
    decks[nm] = [b.min.y, b.max.y];
  }
  // How far each good's flag clears the ground directly beneath it.
  //
  // The parts of a site are built at offsets from the site's origin and only
  // the origin was ever asked how high the island is there, so on a slope they
  // went into it -- reported as three flags drawn inside the hill with their
  // poles showing. Two of them measure 3 and 5 hundredths under, which is
  // enough: a flag is 0.16 tall, so a twentieth of a unit takes a third of it
  // into the grass and the rest reads as lying on the slope.
  //
  // A ray from the camera to the flag was tried instead and taken out again:
  // it could not be made to fail. Even with a flag genuinely under the ground
  // its top half still catches the ray first, so the check that reads like the
  // complaint answers yes to everything, and 600 raycasts a shape bought
  // nothing this line does not.
  //: **Every part of every site, against the ground under it.** The flags
  //: below are one part of one kind; this is all of them, and it is a
  //: different question -- not "does this stand a little into the slope" but
  //: "is the whole of it underneath the island". The quarry's three terraces
  //: were built at -0.08, -0.24 and -0.40 from the site's origin, which is
  //: what cutting a quarry means and which on a grass hill means three slabs
  //: of rock nobody can see. Reported as the quarry being inside the hill.
  //:
  //: The *top* of the part, not its bottom: a thing may stand into the slope
  //: -- the salt pans are bedded a little into the sand -- and still be there
  //: to look at. A part whose highest point is under the ground is not.
  const sunk = [];
  {
    const b = new THREE.Box3(), mid = new THREE.Vector3();
    for (const site of made.island.children.filter((n) => /^site_/.test(n.name))) {
      site.updateMatrixWorld(true);
      for (const part of site.children) {
        b.setFromObject(part);
        b.getCenter(mid);
        sunk.push({ site: site.name, part: part.name,
                    clear: +(b.max.y - made.ground(mid.x, mid.z)).toFixed(3) });
      }
    }
  }

  const flags = {};
  const flagFace = {};
  for (const good of goods) {
    const f = made.island.getObjectByName(`marker_${good}_flag`);
    if (!f) continue;
    const box = new THREE.Box3().setFromObject(f);
    const mid = box.getCenter(new THREE.Vector3());
    flags[good] = box.min.y - made.ground(mid.x, mid.z);
    // And what the flag is painted with. It carried only the good's colour,
    // which asks a viewer to tell pink from purple across an island eight
    // units wide -- the palette clears adjacent pairs and not all pairs, which
    // is the whole reason a good has a glyph. Read the same way a crate's face
    // is read, because it is now the same texture.
    const img = f.material.map?.image;
    if (!img) { flagFace[good] = {hex: null, mark: 0}; continue; }
    const sc = document.createElement('canvas');
    sc.width = img.width; sc.height = img.height;
    sc.getContext('2d').drawImage(img, 0, 0);
    const g2 = sc.getContext('2d');
    const px = g2.getImageData(0, 0, sc.width, sc.height).data;
    const at = (x, y) => { const i = (y * sc.width + x) * 4;
                           return [px[i], px[i + 1], px[i + 2]]; };
    const base = at(Math.round(sc.width * 0.5), Math.round(sc.height * 0.1));
    let marked = 0, seen = 0;
    for (let y = sc.height * 0.25; y < sc.height * 0.85; y += 2) {
      for (let x = sc.width * 0.25; x < sc.width * 0.75; x += 2) {
        const cc = at(Math.round(x), Math.round(y));
        seen++;
        if (Math.abs(cc[0] - base[0]) + Math.abs(cc[1] - base[1])
            + Math.abs(cc[2] - base[2]) > 40) marked++;
      }
    }
    flagFace[good] = {
      hex: '#' + base.map(v => v.toString(16).padStart(2, '0')).join(''),
      mark: +(marked / Math.max(1, seen)).toFixed(3)};
  }
  //: **The horizontal footprint of every settlement and every site.** Not a
  //: radius from the anchor: a salt pan is a long thing and a hut is a round
  //: one, and a circle round either of them is a different claim from the
  //: ground it actually covers. Two boxes that do not overlap is the exact
  //: statement of "these are not drawn against each other", and it is the
  //: thing a spectator reported seeing on a crowded table.
  const foot = [];
  {
    const b = new THREE.Box3();
    for (const nm of [...traders.map(t => `settlement_${t}`),
                      ...goods.map(g => `site_${g}`)]) {
      const o = made.island.getObjectByName(nm);
      if (!o) continue;
      b.setFromObject(o);
      foot.push({ name: nm, box: [b.min.x, b.min.z, b.max.x, b.max.z].map(v => +v.toFixed(3)) });
    }
  }

  //: Where the trail's stones lie, with the radius each is drawn at. A step
  //: is a flat sand disc, and a flat sand disc inside a hut's footprint is the
  //: thing the campfire's clearing was removed for -- see `island3d.js`.
  //: In world coordinates, like the boxes above, and with the radius carried
  //: through whatever the island itself is scaled to. Local numbers compared
  //: against world boxes is a check that passes for the wrong reason.
  const steps = made.island.getObjectByName('trails').children.map(o => {
    const w = o.getWorldPosition(new THREE.Vector3());
    return [+w.x.toFixed(3), +w.z.toFixed(3), +(0.11 * made.island.scale.x).toFixed(3)];
  });

  // Everything the island places on purpose, by name, so a check can ask
  // whether any two of them are standing in the same spot.
  const sited = Object.fromEntries(Object.entries(made.anchors)
    .map(([k, v]) => [k, [v.x, v.z]]));
  return {traders, decks, sited, flags, flagFace, casters, foot, sunk, steps,
          //: The meadow's own area, to say what "crowded" is a share of.
          meadow: Math.PI * 3.2 * 3.2,
          shadowReach: Math.min(shadowBox.right, shadowBox.top,
                                -shadowBox.left, -shadowBox.bottom),
          seats: traders.map(t => [made.anchors[t].x, made.anchors[t].z]),
          geo: {w: geo.w, h: geo.h}, portrait,
          card0: geo.cards.length ? geo.cards[0].y : null,
          // The band the *stylesheet* declares, in this frame's units -- not
          // where the layout put the island's box. Read off `islandBox.y` it
          // would be the layout agreeing with itself, and a layout that
          // ignored the declaration entirely would pass.
          band: Math.round(geo.h * chrome.top),
          shoreTop: top, shoreBottom: bottom};
}"""


#: A stage driven directly, so a check can ask the island what is standing on
#: it for a set of holdings it chose. The same modules the page loads.
STOCK = """async ({goods, cases}) => {
  const THREE = await import('./vendor/three/three.module.js');
  const { Stage } = await import('./stage.js');
  const { layout, CARRY, carriedBy } = await import('./scene.js');
  const cv = document.createElement('canvas');
  cv.width = 1200; cv.height = 750; document.body.appendChild(cv);
  const st = new Stage(cv, layout(2, false, 1.6, {top: 0, foot: 0}));
  st.pause();
  const traders = ['T1', 'T2'];
  const made = st.build({traders, goods});
  st.pause();
  const out = [];
  for (const c of cases) {
    st.showStock(c.stocks, c.event ?? null);
    const boxes = [];
    st.stock.root.traverse(o => { if (o.isMesh) boxes.push(o); });
    // Where every box actually stands, and how far each is above the ground
    // beneath it: a crate floating over the grass or sunk into it is the same
    // defect the flags had, and this is a hundred more chances to have it.
    made.island.updateMatrixWorld(true);
    // A box stands on the ground or squarely on the box under it, and nowhere
    // in between: the clearance is a whole number of box heights or the pile
    // is floating.
    const off = boxes.map(b => {
      const w = b.getWorldPosition(new THREE.Vector3());
      const h = w.y - made.ground(w.x, w.z) - 0.065;
      return +(h - Math.round(h / 0.1326) * 0.1326).toFixed(3);
    });
    // Nothing standing in a hut, and no two yards in each other.
    let clash = null;
    for (const b of boxes) {
      const w = b.getWorldPosition(new THREE.Vector3());
      for (const t of traders) {
        const h = made.anchors[t];
        if (Math.hypot(w.x - h.x, w.z - h.z) < 0.5) clash = `${b.name} inside ${t}'s hut`;
      }
      if (Math.hypot(w.x, w.z) > 3.3) clash = `${b.name} off the meadow`;
    }
    // What a box is actually painted with: the colour of its face, and how
    // much of that face is not the flat colour -- which is the mark. A crate
    // is a cube with one texture on all six sides, so this is what a viewer
    // sees whichever way it is turned.
    const faces = {};
    for (const b of boxes) {
      const good = b.name.replace(/^box_/, "");
      if (faces[good] || !b.material.map?.image) continue;
      const img = b.material.map.image;
      const sc = document.createElement("canvas");
      sc.width = img.width; sc.height = img.height;
      const g2 = sc.getContext("2d");
      g2.drawImage(img, 0, 0);
      const px = g2.getImageData(0, 0, sc.width, sc.height).data;
      // The flat colour, read off the middle of an edge: away from the lip
      // drawn round the border and away from the mark in the centre.
      const at = (x, y) => { const i = (y * sc.width + x) * 4;
                             return [px[i], px[i + 1], px[i + 2]]; };
      const base = at(Math.round(sc.width * 0.5), Math.round(sc.height * 0.12));
      let marked = 0, seen = 0;
      // The middle half of the face, which is where a mark is drawn and where
      // the border lip is not.
      for (let y = sc.height * 0.25; y < sc.height * 0.85; y += 2) {
        for (let x = sc.width * 0.25; x < sc.width * 0.75; x += 2) {
          const c = at(Math.round(x), Math.round(y));
          seen++;
          if (Math.abs(c[0] - base[0]) + Math.abs(c[1] - base[1])
              + Math.abs(c[2] - base[2]) > 40) marked++;
        }
      }
      faces[good] = { hex: "#" + base.map(v => v.toString(16).padStart(2, "0")).join(""),
                      mark: +(marked / Math.max(1, seen)).toFixed(3) };
    }
    out.push({tally: st.stock.tally(), n: boxes.length, clash, faces,
              low: off.length ? Math.min(...off) : 0,
              high: off.length ? Math.max(...off) : 0});
  }
  return out;
}"""


#: An exchange driven frame by frame off-page, so a check can watch where every
#: box is at every moment of it rather than at the two ends.
CARRY = """async ({goods, give, want, hold}) => {
  const THREE = await import('./vendor/three/three.module.js');
  const { Stage } = await import('./stage.js');
  const { layout, CARRY, carriedBy } = await import('./scene.js');
  const cv = document.createElement('canvas');
  cv.width = 1200; cv.height = 750; document.body.appendChild(cv);
  const st = new Stage(cv, layout(2, false, 1.6, {top: 0, foot: 0}));
  st.pause();
  const traders = ['T1', 'T2'];
  st.build({traders, goods});
  st.pause();
  // Both sides holding plenty, so there is something to send either way.
  const before = {T1: Object.fromEntries(goods.map(g => [g, hold])),
                  T2: Object.fromEntries(goods.map(g => [g, hold]))};
  st.showStock(before);
  const was = [];
  st.stock.root.traverse(o => { if (o.isMesh) was.push(o); });
  const home = new Map(was.map(o => [o, o.getWorldPosition(new THREE.Vector3())]));
  // What the board says after the exchange, and **only the traded goods move**.
  // A fixture that changed every holding would have the yards reconciling
  // goods no clip is carrying, which is the scrub cut doing its job and not
  // this check's question.
  const after = {T1: {...before.T1}, T2: {...before.T2}};
  for (const [g, q] of Object.entries(give)) { after.T1[g] -= q; after.T2[g] += q; }
  for (const [g, q] of Object.entries(want)) { after.T2[g] -= q; after.T1[g] += q; }
  const event = {kind: 'settled', pid: 'p1', maker: 'T1', taker: 'T2', give, want, after};
  st.showStock(event.after, event);
  const c = st.fire(event);
  if (!c) return {error: 'the exchange staged no clip at all'};
  //: Which boxes carry which good, so the moment *that good* comes to rest can
  //: be compared against the moment its symbols are told to leave. By name,
  //: which is what a box is called after the good inside it.
  const of = {};
  for (const o of was) for (const g of goods) if (o.name.includes(g)) (of[g] ||= []).push(o);
  const place = (o) => { const p = o.getWorldPosition(new THREE.Vector3());
    return `${p.x.toFixed(4)},${p.y.toFixed(4)},${p.z.toFixed(4)}`; };
  const seen = {}, stops = {};
  for (let t = 0; t <= c.dur + 0.2; t += 0.02) {
    c.update(t);
    for (const [g, ms] of Object.entries(of)) {
      const now = ms.map(place).join('|');
      if (seen[g] !== undefined && now !== seen[g]) stops[g] = Math.round(t * 1000);
      seen[g] = now;
    }
  }
  //: What `hands()` schedules the symbols at, from the page's own table.
  const cue = {};
  Object.keys(give).forEach((g, i) => { cue[g] = carriedBy(i, false); });
  Object.keys(want).forEach((g, i) => { cue[g] = carriedBy(i, true); });
  c.restore();
  c.update(0);

  // Every tenth of a second of it: is any box that existed before the clip
  // started invisible, or standing somewhere it did not walk to?
  const trail = [];
  for (let t = 0; t <= c.dur; t += 0.1) {
    c.update(t);
    const shot = [];
    for (const o of was) {
      const p = o.getWorldPosition(new THREE.Vector3());
      shot.push({name: o.name, vis: o.visible && o.parent !== null,
                 x: +p.x.toFixed(3), y: +p.y.toFixed(3), z: +p.z.toFixed(3)});
    }
    trail.push({t: +t.toFixed(1), shot});
  }
  c.restore();
  return {n: was.length, trail, stops, cue, rest: CARRY.rest,
          home: was.map(o => {const p = home.get(o);
                              return [+p.x.toFixed(3), +p.y.toFixed(3), +p.z.toFixed(3)];})};
}"""


def carrying(browser, base: str, out: Path) -> list[str]:
    """A box that changes hands walks there; it does not blink out and back.

    **Reported by eye, and it was doing exactly that.** The clip hid each box
    until its own leg of the exchange began, so for the first second the goods
    were gone from the maker's yard and then appeared in mid-air on their way
    to the taker's. That is the one thing the standing-stock layer exists to
    stop, and no check would have caught it: the yards agree with the board at
    both ends of the animation, and the counts never lie. It is only wrong
    *while it is moving*.

    So this drives an exchange a tenth of a second at a time and watches every
    box that existed before it started: none may go invisible, and none may
    move further in one step than a box can travel.

    **And the symbols wait for them.** Also reported by eye: the item symbols
    left the arriving boxes for the gaining card before the boxes had touched
    down. The two engines were keeping separate copies of the same schedule --
    three.js in seconds off its clip clock, SVG in milliseconds off a `CROSS`
    constant -- and the copies had drifted apart by half a second, so a bar
    filled from goods that were still in the air. They read one table now
    (`scene.js:CARRY`), and this measures the thing the table claims: for
    **each good**, the moment its own boxes stop moving against the moment
    `hands()` is told to send its symbols up.

    Bounded on both sides, and tightly. Early is the defect. The gap is
    `CARRY.rest` by construction -- the last box of *any* good lands at exactly
    `carriedBy(i) - rest`, whether that good came to one box or six -- so late
    by more than a beat means the two schedules have drifted apart again, and a
    table could otherwise be made to pass by holding the symbols for a second
    after the island had gone still.
    """
    goods = ["bread", "cloth", "iron", "salt"]
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    #: **A bundle of several boxes per good, not one.** It used to hold 0.8 of
    #: everything and move 0.4, which at `BOX` = 0.465 is a single box changing
    #: hands per good -- and a single box is the one case where `CARRY.spread`
    #: does nothing at all, so the rule that says the boxes of one good leave
    #: across a fixed window could not be made to fail. Six boxes each, five of
    #: them moving.
    seen = page.evaluate(CARRY, {"goods": goods, "hold": 2.8,
                                 "give": {"bread": 2.4, "cloth": 2.4},
                                 "want": {"iron": 2.4}})
    page.close()
    bad = [f"carrying: {e}" for e in errs]
    if seen.get("error"):
        return bad + [f"carrying: {seen['error']}"]
    if not seen["n"]:
        return bad + ["carrying: nothing was standing on the island to carry"]
    # Nothing blinks.
    for step in seen["trail"]:
        for box in step["shot"]:
            if not box["vis"]:
                bad.append(f"carrying: a {box['name']} standing before the "
                           f"exchange is invisible at t={step['t']}s; it "
                           f"vanished from the ground instead of walking")
                break
        if bad and "invisible" in bad[-1]:
            break
    # And nothing teleports.
    #
    # **Against its own journey, not against a fixed distance.** A box crosses
    # the island in about a second and a half, and how far that is depends on
    # where the two yards happen to sit -- a real carry between the widest pair
    # of settlements steps a whole unit in a tenth of a second at the fastest
    # part of its arc, which is most of a fixed threshold and none of a
    # relative one. A teleport is the *whole* journey in one step.
    #: **By position in the shot, not by name.** Six boxes of bread are all
    #: called `box_bread`, so a dictionary keyed by name collapses them and
    #: compares a box that crossed the island against a journey belonging to
    #: one that never left the yard. Every shot lists the same boxes in the
    #: same order, so the index is the identity.
    # The symbols leave after their own boxes are down -- and not long after.
    for good, cue in sorted(seen["cue"].items()):
        stops = seen["stops"].get(good)
        if stops is None:
            bad.append(f"carrying: no box of {good} moved at all, so there is "
                       f"nothing for its symbols to have waited for")
            continue
        if cue < stops:
            bad.append(f"carrying: {good}'s symbols are sent to the card at "
                       f"{cue}ms and its boxes are still moving at {stops}ms; "
                       f"the bar fills from goods that are in the air")
        elif cue - stops > seen["rest"] + 60:
            bad.append(f"carrying: {good}'s boxes come to rest at {stops}ms and "
                       f"its symbols are not sent until {cue}ms, {cue - stops}ms "
                       f"later; the two schedules have drifted apart")
    at = lambda b: (b["x"], b["y"], b["z"])
    trips = [math.dist(at(f), at(l))
             for f, l in zip(seen["trail"][0]["shot"], seen["trail"][-1]["shot"])]
    for a, b in zip(seen["trail"], seen["trail"][1:]):
        for i, (was, now) in enumerate(zip(a["shot"], b["shot"])):
            jump = math.dist(at(was), at(now))
            trip = trips[i]
            # A box that changed hands: no step may be most of the journey.
            # A box that stayed where it was: it may settle, and no more.
            limit = trip * 0.45 if trip > 0.5 else 0.35
            if jump > limit:
                bad.append(f"carrying: a {now['name']} moved {jump:.2f} in a "
                           f"tenth of a second between t={a['t']}s and "
                           f"t={b['t']}s, on a {trip:.2f} journey; it was put "
                           f"down somewhere rather than carried there")
                return bad
    return bad


#: What one box on the island is worth, in the goods' own units.
#:
#: The page's `island-stock.js:UNIT`, restated here because a check that read
#: the number out of the module it is checking would agree with itself. The
#: derivation -- the ninetieth percentile of `barter.economy`'s capacity draw,
#: over six boxes -- is `tests/test_box_unit.py`, which computes it from
#: `draw_island` rather than from either copy.
BOX = 2.788 / 6


def stock(browser, base: str, out: Path) -> list[str]:
    """What is standing on the island is what the board says is held.

    **Goods stopped being clip props.** A crate used to appear at a site,
    cross the island and shrink out of existence at the hut, so between one
    receipt and the next the ground held nothing at all. Every trader has a
    yard now and what it holds stands in it, which means the island can be
    *wrong* in a way it could not be before -- a box left behind after a trade,
    a pile that did not grow when a receipt arrived, a stack floating over the
    grass.

    Asked of the model directly with holdings this check chose, because the
    interesting cases (a trader holding one good, holding none, holding more
    than six boxes can show) are not all on any board on disk.
    """
    goods = ["bread", "cloth", "iron", "salt"]
    #: A box is a fixed quantity on every board -- a sixth of the ninetieth
    #: percentile of the capacity draw -- so these are quantities in the goods'
    #: own units and the counts they have to come out as. Written as multiples
    #: of the unit rather than as literals, so the two cannot drift apart
    #: silently if the distribution is ever re-derived.
    cases = [
        {"name": "nobody has anything", "stocks": {"T1": {}, "T2": {}},
         "want": {"T1": {g: 0 for g in goods}, "T2": {g: 0 for g in goods}}},
        {"name": "one good each",
         "stocks": {"T1": {"bread": 6 * BOX}, "T2": {"salt": 2 * BOX}},
         "want": {"T1": {"bread": 6, "cloth": 0, "iron": 0, "salt": 0},
                  "T2": {"bread": 0, "cloth": 0, "iron": 0, "salt": 2}}},
        {"name": "a crumb is still a box",
         "stocks": {"T1": {"iron": 0.001}, "T2": {}},
         "want": {"T1": {"bread": 0, "cloth": 0, "iron": 1, "salt": 0},
                  "T2": {g: 0 for g in goods}}},
        {"name": "more than six boxes can show",
         "stocks": {"T1": {"cloth": 99}, "T2": {}},
         "want": {"T1": {"bread": 0, "cloth": 6, "iron": 0, "salt": 0},
                  "T2": {g: 0 for g in goods}}},
        {"name": "back to nothing", "stocks": {"T1": {}, "T2": {}},
         "want": {"T1": {g: 0 for g in goods}, "T2": {g: 0 for g in goods}}},
        # The bell is eating the lot, and eating it is the animation: the yards
        # are left exactly as they were for the clip to empty. So this follows
        # a case that put goods on the ground, and asks that they are still
        # there after a paint whose board says everybody holds nothing.
        {"name": "before the bell",
         "stocks": {"T1": {"bread": 6 * BOX}, "T2": {"salt": 2 * BOX}},
         "want": {"T1": {"bread": 6, "cloth": 0, "iron": 0, "salt": 0},
                  "T2": {"bread": 0, "cloth": 0, "iron": 0, "salt": 2}}},
        {"name": "the bell leaves the clip to it",
         "stocks": {"T1": {}, "T2": {}}, "event": {"kind": "bell"},
         "want": {"T1": {"bread": 6, "cloth": 0, "iron": 0, "salt": 0},
                  "T2": {"bread": 0, "cloth": 0, "iron": 0, "salt": 2}}},
    ]
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    seen = page.evaluate(STOCK, {"goods": goods,
                                 "cases": [{"stocks": c["stocks"],
                                            "event": c.get("event")} for c in cases]})
    # What the stylesheet says a good is, read off the page serving it.
    css = page.evaluate("""(gs) => {
      const s = getComputedStyle(document.documentElement);
      const hex = (v) => {
        const m = v.trim().match(/^#([0-9a-f]{6})$/i);
        return m ? '#' + m[1].toLowerCase() : v.trim();
      };
      return Object.fromEntries(gs.map((g, i) =>
        [g, hex(s.getPropertyValue('--good-' + (i + 1)))]));
    }""", goods)

    page.screenshot(path=str(out / "island-stock.png"))
    page.close()
    bad = [f"stock: {e}" for e in errs]
    for case, got in zip(cases, seen):
        where = f"stock {case['name']!r}"
        if case.get("event", {}).get("kind") == "bell" and not got["n"]:
            bad.append(f"{where}: the yards were emptied by the paint; the "
                       f"bell's own clip had nothing left to eat")
        for name, want in case["want"].items():
            if got["tally"].get(name) != want:
                bad.append(f"{where}: {name} holds {got['tally'].get(name)}, "
                           f"the board says {want}")
        if got["clash"]:
            bad.append(f"{where}: {got['clash']}")
        for good, face in (got.get("faces") or {}).items():
            # The colour a box is painted, against the colour the card paints
            # the bar counting it. These had drifted from the fifth good on and
            # nothing compared them -- one list is CSS and the other is hex
            # integers for three.js. `test_palette.py` compares the two
            # sources; this compares the pixels a viewer sees.
            if face["hex"] != css.get(good):
                bad.append(f"{where}: a {good} box is painted {face['hex']} and "
                           f"its bar is {css.get(good)}; one good, two colours")
            #: A tenth of the face. The marks are drawn at 76px in a 128px
            #: square, so one that rendered at all covers far more than this; a
            #: face with none is a plain coloured cube, and colour alone does
            #: not identify a good -- which is the whole reason the card's
            #: shelf carries a glyph too.
            if face["mark"] < 0.1:
                bad.append(f"{where}: a {good} box carries no mark "
                           f"({face['mark']:.0%} of its face); it is a coloured "
                           f"cube and nothing else")
        #: Every box sitting on the ground under it, to within a hair. Half a
        #: box is 0.065, so this is the same question the flags answer.
        if got["n"] and not -0.04 <= got["low"] <= got["high"] <= 0.04:
            bad.append(f"{where}: boxes stand between {got['low']:+.3f} and "
                       f"{got['high']:+.3f} off the ground beneath them")
    return bad


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
    #:
    #: `hearth_ground` was here for the sand clearing the fire used to sit in,
    #: which was removed as a yellow circle that said nothing the fire had not
    #: (island3d.js). That ground is plain `meadow` now, so the name is gone
    #: from both lists rather than left as a surface nothing can return.
    LAND = {"meadow", "upland", "ridge"}
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    shapes = [("desktop", 1200, 750, 2, False), ("wide", 1600, 700, 2, False),
              ("tall", 900, 1100, 2, False), ("phone", 430, 780, 2, True),
              ("desktop/4", 1200, 750, 4, False), ("phone/4", 430, 900, 4, True),
              ("desktop/5", 1400, 800, 5, False),
              # The frames a shared link opens into on a phone: the browser's
              # own bars take a hundred points and more off the window, and
              # everything the layout reserved is worth less of it.
              ("safari", 393, 660, 2, True), ("small", 360, 640, 2, True),
              ("safari/3", 393, 660, 3, True),
              # The crowded end. Eight traders and five goods is thirteen
              # things on an island six units of grass across, and it is the
              # shape nothing was ever drawn at: the props were sized by eye at
              # a table half that and stayed constant as it grew.
              ("crowd/8", 1400, 820, 8, False), ("crowd/7", 1200, 750, 7, False),
              ("crowd/6", 1200, 750, 6, False)]
    for label, w, h, n, portrait in shapes:
        # The window is put into the shape being asked about before the stage
        # is built, because the stage reads the chrome's bands off the page's
        # own stylesheet and those are declared inside a media query. Asked at
        # a desktop viewport they come back as zero -- which is a frame nobody
        # has, and every question about the band is then a question about a
        # band of nothing. (Found by neutering: a layout that ignored the
        # declaration outright still passed this.)
        page.set_viewport_size({"width": w, "height": h})
        built = page.evaluate(STAGE, {"w": w, "h": h, "n": n, "portrait": portrait,
                                      "goods": ["bread", "cloth", "iron", "salt", "fish"]})
        seats = built["seats"]
        # The island cut across its own shore by the top of the frame.
        #
        # Asked of the model rather than of the picture: the topmost drawn pixel
        # cannot tell the island's shore from a cloud sitting over it, and with
        # motion stilled the clouds sit wherever they started. This projects the
        # sea's own disc and asks where its edge lands.
        #
        # Only in portrait. A frame wider than it is tall has no room to give
        # the sea, and there the cut falls in open water where nothing reads it;
        # in portrait the island was sliced flat with the land going over the
        # edge, which is what a phone showing the browser's bars looked like.
        # And the dead band under it. The island is a disc under a tilted
        # camera, so it is not as tall as it is wide, and the layout starts the
        # cards where it actually ends rather than where its square box does --
        # from two numbers that were measured off the model. This is what keeps
        # them honest: change the tilt or the sea and the band opens back up
        # here, on a phone, where every unit of it is island the reader lost.
        if portrait and built["card0"] is not None:
            gap = built["card0"] - built["shoreBottom"]
            if not 0 <= gap <= 48:
                bad.append(f"island {label}: {gap:.0f} between the island's foot "
                           f"and the first card; the layout and the model "
                           f"disagree about how tall the island is")
        #: **Below the band the chrome reserved**, not merely inside the
        #: frame. The frame's own top row stopped being the thing to clear the
        #: moment the layout admitted that four rows of pills stand across it:
        #: an island that starts at the frame's first row starts underneath the
        #: goods key. This is the same number the stylesheet declares, arriving
        #: through the layout, so the two cannot drift apart without failing.
        if portrait and built["shoreTop"] < built["band"]:
            bad.append(f"island {label}: the island's silhouette reaches "
                       f"{built['shoreTop']:.0f} in the frame at its worst bearing, "
                       f"above the band the chrome has at {built['band']:.0f}; "
                       f"it is drawn under the pills")
        #: **No part of a site is buried in the island.**
        #:
        #: Reported by eye as the quarry being inside the hill, and it was: its
        #: three terraces are what makes it a quarry, they were cut downward
        #: from the site's own origin, and on a grass hill that put all three
        #: of them under the grass -- the first's top face exactly at it, the
        #: third a third of a unit below. What showed was a flag, a cart and
        #: two lumps of spoil.
        #:
        #: `follow` is not a defence against this and cannot be: it walks each
        #: part down onto the ground *under it*, which corrects for the slope
        #: across a site -- a hundredth of a unit -- and says nothing about a
        #: part built below its own origin.
        #:
        #: Measured at the part's **top**, against zero and not against a
        #: margin. A thing may stand into the slope and still be there to look
        #: at -- the salt pans are bedded into the sand and their beds clear by
        #: two hundredths at the biggest tables -- so any floor generous enough
        #: to be a "margin" fails them, and the quarry did not need one: its
        #: terraces were flush, a sixth under and a third under. Buried means
        #: buried. The hair above zero is for the flush case, which is a part
        #: whose top face is exactly the ground and is just as invisible.
        for part in built["sunk"]:
            if part["clear"] <= 0.005:
                bad.append(f"island {label}: {part['site']}'s {part['part']} "
                           f"tops out at {part['clear']:+.3f} against the "
                           f"ground beneath it; it is drawn inside the island")
        #: **Nothing casts a shadow from outside the shadow camera's box.**
        #:
        #: Reported by eye as a dark, soft-edged rectangle sitting on the
        #: meadow and flickering rather than sitting still. It was the sea:
        #: `add()` gives every mesh `castShadow`, and the water is a flat disc
        #: sixteen units across against a shadow camera six units either way.
        #: Two things go wrong at once. The frustum clips the map, so its own
        #: edge is a straight line laid across whatever it falls on; and from a
        #: light forty-five degrees up the disc's far side is *nearer the
        #: light* than the island is, so the water wins the texels the land
        #: needs and the land is compared against the water's depth and comes
        #: out shadowed. The rectangle crawled as the light swung, which is
        #: what read as flicker.
        #:
        #: Asked of the model rather than of the picture: "is this caster
        #: inside the box that can hold its shadow" has an exact answer, where
        #: "is there a rectangle on the grass" is a question about pixels that
        #: only fails once somebody has already seen it.
        for c in built["casters"]:
            if c["reach"] > built["shadowReach"]:
                bad.append(f"island {label}: {c['name']} casts a shadow and "
                           f"reaches {c['reach']} from the middle, past the "
                           f"{built['shadowReach']} the shadow camera covers; "
                           f"the frustum's edge is drawn across the island")
        #: **No two things the island places are drawn against each other**,
        #: and the island does not fill up as the table grows.
        #:
        #: Both halves of one report: a fixed element size at a growing table
        #: is how a hut ends up rendered adjacent to a production site, which
        #: is a layout accident and not a fact the manager settled. The props
        #: shrink with the count now (`room` in `island3d.js`, area-preserving,
        #: so twice as many things each about seven-tenths the size cover the
        #: same grass), settlements and sites are dealt onto one schedule of
        #: bearings so the angular pitch shrinks with them, and what is built
        #: is then measured and settled.
        #:
        #: Measured as the ground the props actually cover, not as a radius
        #: from the anchor: a hut carries crates beside its door and a site
        #: carries a flag on a pole, so both boxes sit off to one side of the
        #: point any placement rule was satisfied at. That is exactly the gap
        #: this found -- a hut cleared the bread field by the rule and still
        #: overlapped it by a tenth of a unit.
        feet = built["foot"]
        for k, one in enumerate(feet):
            for two in feet[k + 1:]:
                a, b = one["box"], two["box"]
                gap = max(max(a[0] - b[2], b[0] - a[2]),
                          max(a[1] - b[3], b[1] - a[3]))
                if gap <= 0:
                    bad.append(f"island {label}: {one['name']} and {two['name']} "
                               f"overlap by {-gap:.2f} on the ground; they are "
                               f"drawn against each other")
        #: And no stone of the trail lies under anything the trail runs to.
        #: The steps were laid at eighths of the way out, so the last one fell
        #: short by a fraction of the distance rather than by the size of what
        #: it was walking to -- and under a settlement on the near ring that is
        #: a sand disc lying inside the hut. Reported by eye, as a yellow disc
        #: below a hut, which is the same complaint that took the campfire's
        #: clearing off the island one commit earlier. Measured against the
        #: drawn footprint for the same reason the pair check above is: a hut
        #: is its roof, not its anchor.
        for sx, sz, sr in built.get("steps") or []:
            for one in feet:
                a = one["box"]
                gap = max(max(a[0] - (sx + sr), (sx - sr) - a[2]),
                          max(a[1] - (sz + sr), (sz - sr) - a[3]))
                if gap <= 0:
                    bad.append(f"island {label}: a trail step at "
                               f"({sx:.2f}, {sz:.2f}) lies inside "
                               f"{one['name']} by {-gap:.2f}; it is a sand "
                               f"disc drawn under a prop")
        covered = sum((f["box"][2] - f["box"][0]) * (f["box"][3] - f["box"][1])
                      for f in feet)
        #: A share, not an area: what "crowded" means is how much of the grass
        #: is taken, and the whole point of the size rule is that this number
        #: stays put as the table grows. It sits at 36-39% from two traders and
        #: four goods up to eight and five.
        if feet and covered > 0.48 * built["meadow"]:
            bad.append(f"island {label}: settlements and sites cover "
                       f"{covered / built['meadow']:.0%} of the meadow; the "
                       f"island is drawn full")
        # Two horizontal faces at exactly one height, both of them wide enough
        # to cover the coast, is z-fighting -- and z-fighting only shows while
        # the camera moves, so a still screenshot cannot catch it and nothing
        # here could. It was reported as blue flickering round the island: the
        # deep sea's top face and the shore shelf's underside were both at
        # y=0. Asked of the model, where it is a question about two numbers.
        decks = built["decks"]
        planes = [(nm, y) for nm, span in decks.items() for y in span]
        for i, (an, ay) in enumerate(planes):
            for bn, by in planes[i + 1:]:
                if an == bn or abs(ay - by) > 0.008:
                    continue
                bad.append(f"island {label}: {an} and {bn} both have a face at "
                           f"y={ay:.3f}; two flat surfaces on one plane fight "
                           f"for every pixel where they overlap")
        # And nothing the island placed on purpose stands in anything else it
        # placed on purpose. The settlements were separated from each other and
        # from nothing else -- the good sites are laid on their own ring at
        # their own radii, so a hut could come down on the salt pans, which is
        # what "elements are drawn on top of one another" looked like from a
        # seat. A market stall is about 0.9 across and a hut about 0.8, so a
        # metre between centres is two of them not touching.
        # A flag is a sign, and a sign inside a hill signs nothing. Asked of the
        # model at the flag's own position rather than its site's, which is
        # exactly the distinction the bug turned on.
        # A flag names the good its site makes, and a colour alone does not
        # name it: the palette clears adjacent pairs, not all pairs. Same
        # texture as the crates in a trader's yard, and read the same way.
        for good, seen_face in (built.get("flagFace") or {}).items():
            if seen_face["mark"] < 0.1:
                bad.append(f"island {label}: {good}'s site flag carries no mark "
                           f"({seen_face['mark']:.0%} of its face); it is a "
                           f"coloured rectangle and nothing else")
        for good, clear in built["flags"].items():
            if clear < -0.02:
                bad.append(f"island {label}: {good}'s flag is {-clear:.2f} below "
                           f"the ground under it; it is drawn inside the hill")
        sited = built["sited"]
        names = sorted(sited)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                gap = math.dist(sited[a], sited[b])
                if gap < 1.0:
                    bad.append(f"island {label}: {a} and {b} are {gap:.2f} apart; "
                               f"they are drawn standing in each other")
        for name, (x, z) in zip(built["traders"], seats):
            under = page.evaluate("([x, z]) => window.__under(x, z)", [x, z])
            if under not in LAND:
                bad.append(f"island {label}: {name}'s settlement stands on "
                           f"{under!r} at ({x:.2f}, {z:.2f})")
        #: **"Two settlements at least 1.2 apart" is gone**, and the footprint
        #: test above replaces it. It was the right question -- a frame narrow
        #: enough collapses the layout's ring, and two huts in one place is one
        #: hut with a spare card -- asked against a constant, from when a hut
        #: was always the same size. A hut is drawn smaller at a bigger table
        #: now, so 1.2 between their middles is a different amount of daylight
        #: at four traders and at eight, and the rule failed a seven-trader
        #: island whose huts had a tenth of a unit of grass between them. The
        #: replacement measures the grass rather than the middles, which is
        #: what the question was always about.

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
              off: seen.filter(s => !['meadow', 'upland', 'ridge'].includes(s[3]))
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
#: What everybody is holding when these events happen.
#:
#: **A settlement moves goods that exist and the bell eats goods that exist.**
#: This harness used to fire both at an island whose yards were empty, which is
#: a state no board can be in: the clips had nothing to carry and nothing to
#: consume, and what they were measured on was whatever else they happened to
#: do. Each event below carries the holdings before it and after it, so it is
#: fired at the island it would really happen on, and what it left behind is
#: measured against the island it should really leave.
#: A day's work, in the goods' own units.
#:
#: **Scaled up when a box stopped being round-relative.** These numbers were
#: chosen when six boxes meant the round's own biggest pile, so 0.8 of a good
#: was five crates. A box is a fixed quantity now -- a sixth of the ninetieth
#: percentile of the capacity draw, `BOX` above -- and 0.8 is one crate and a
#: bit, which is not "the day's work standing in the yard" and is not what the
#: events below say they are showing. Same shape, same trades, at a size that
#: is a good day on a real board: the largest pile ever settled on any board on
#: disk is 5.91 and the median round's biggest is 0.75.
HOLDING = {"T1": {"bread": 2.24, "cloth": 0.56, "salt": 1.4},
           "T2": {"cloth": 1.68, "iron": 1.12}}
EMPTY = {"T1": {}, "T2": {}}

FIRED = [
    # Nothing made yet, and then the day's work is standing in the yard.
    {"kind": "produced", "trader": "T1", "made": {"bread": 2.24, "salt": 1.4},
     "pre": {"T1": {"cloth": 0.56}, "T2": {"cloth": 1.68, "iron": 1.12}},
     "post": HOLDING},
    {"kind": "offer", "pid": "p1", "maker": "T1", "taker": "T2",
     "give": {"bread": 1.4}, "want": {"cloth": 0.84},
     "pre": HOLDING, "post": HOLDING},
    {"kind": "settled", "pid": "p1", "maker": "T1", "taker": "T2",
     "give": {"bread": 1.4}, "want": {"cloth": 0.84},
     "pre": HOLDING,
     "after": {"T1": {"bread": 0.84, "cloth": 1.4, "salt": 1.4},
               "T2": {"bread": 1.4, "cloth": 0.84, "iron": 1.12}},
     "post": {"T1": {"bread": 0.84, "cloth": 1.4, "salt": 1.4},
              "T2": {"bread": 1.4, "cloth": 0.84, "iron": 1.12}}},
    {"kind": "refused", "trader": "T2", "reason": "uncommitted stock",
     "pre": HOLDING, "post": HOLDING},
    # The bell eats everything held, which is the one place a good may vanish.
    {"kind": "bell", "episode": 1, "lapsed": 2, "pre": HOLDING, "post": EMPTY},
    {"kind": "open", "episode": 2, "of": 3, "pre": EMPTY, "post": EMPTY},
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
    #: **The handover, asserted.** An offer and a refusal are let off the
    #: island's own floor because their picture is drawn over the canvas
    #: instead -- so the checks that hold *those* to their job have to still be
    #: in the suite, or the two events go quiet everywhere at once and nothing
    #: says so. Read out of this file's own source, which is where `run` says
    #: what it runs.
    here = Path(__file__).read_text()
    for kind, carrier in (("an offer", "turning"), ("a refusal", "overhead")):
        if f"problems += {carrier}(" not in here:
            bad.append(f"mechanics: {kind} is excused the island's floor "
                       f"because `{carrier}` carries it, and `{carrier}` is no "
                       f"longer run")
    page = browser.new_page(viewport={"width": 1000, "height": 700})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.on("console", lambda m: errs.append(f"console error: {m.text}")
            if m.type == "error" else None)
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    page.evaluate(STAGE, {"w": 900, "h": 560, "n": 2, "portrait": False,
                          "goods": ["bread", "cloth", "iron", "salt", "fish"]})
    seen = page.evaluate("""({events, holding}) => {
      const st = window.__st;
      //: **The clip, then the ambient layer, then draw** -- the order the
      //: stage's own loop runs in. This used to advance the life layer inside
      //: `shot`, which is after everything, so a clip asking the island for a
      //: brighter fire was spent before the pixels were read and the bell
      //: measured as not happening at all. The layer is advanced at one fixed
      //: moment so the ambient motion is the same in every shot and only the
      //: clip differs.
      //: **Only the rectangle the island is drawn into.**
      //:
      //: The renderer letterboxes: it draws into the rect the `<svg>` fits its
      //: viewBox into and the bands beside it are a separate pass. Those bands
      //: used to be transparent, so "opaque" and "inside the frame" were the
      //: same question and the denominator below could be counted off the
      //: alpha channel. They are open water now -- a spectator asked not to
      //: have a void round the island -- and counting alpha made the
      //: denominator the whole canvas, which cut every clip's measured share
      //: by the ratio of the two and failed the smallest one. Cropping to the
      //: frame gives back exactly the old denominator, and the bands cannot
      //: contribute to a difference either.
      const r = st.renderer.getPixelRatio();
      const [vx, vyGL, vw, vh] = st.view;
      // WebGL counts from the bottom of the canvas; a 2D context from the top.
      const src = [vx * r, st.canvas.height - (vyGL + vh) * r, vw * r, vh * r];
      const shot = () => {
        st.renderer.render(st.scene, st.camera);
        const s = document.createElement('canvas');
        s.width = 300; s.height = 187;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, ...src, 0, 0, s.width, s.height);
        return g.getImageData(0, 0, s.width, s.height).data;
      };
      // Changed pixels as a share of the *island's* own, not of the frame's.
      // How much of the frame is island is a layout decision -- the cards took
      // the margins and it halved -- and a clip does not become less visible
      // because the page put something else beside the island.
      let ground = 0;
      const diff = (a, b) => {
        let n = 0;
        for (let i = 0; i < a.length; i += 4)
          if (Math.abs(a[i] - b[i]) + Math.abs(a[i+1] - b[i+1])
              + Math.abs(a[i+2] - b[i+2]) > 18) n++;
        return n / Math.max(1, ground);
      };
      st.life.update(3, st.ctx());
      st.stock.rest(holding);
      const lit = shot();
      //: Every pixel of the crop is the island's frame, which is what this
      //: counted before the water reached the edge of the canvas.
      ground = lit.length / 4;
      return events.map((e) => {
        // The island with this event's own goods standing on it and nothing
        // happening -- which is what its clip has to be visible *against*.
        st.clear();
        st.life.update(3, st.ctx());
        st.stock.rest(e.pre ?? holding);
        const bare = shot();
        st.clear();
        // Put the island back to what everybody holds *before* this one: a
        // clip that carries goods needs goods to carry, and the one before it
        // may have moved or eaten them.
        st.stock.rest(e.pre ?? holding);
        st.showStock(e.pre ?? holding, e);
        const c = st.fire(e);
        st.pause();
        if (!c) return {kind: e.kind, clip: false};
        let peak = 0;
        for (let t = 0.1; t <= c.dur; t += 0.1) {
          c.t0 = 0;
          st.step(t);
          st.life.update(3, st.ctx());
          peak = Math.max(peak, diff(bare, shot()));
        }
        // Past the end, which is what the stage's own loop does.
        c.t0 = 0;
        st.step(c.dur + 0.5);
        st.life.update(3, st.ctx());
        const done = shot();
        // **What it left behind, against what the event legitimately changed.**
        // Goods are permanent now: a settlement really does move boxes from
        // one yard to the other and the bell really does eat them, so
        // comparing the finished island with the island *before* the event
        // reports the feature as litter. The baseline is the island rested at
        // the holdings the board says come next, with no clip involved -- so
        // what is measured is only the difference a clip made and did not put
        // back.
        st.clear();
        st.life.update(3, st.ctx());
        st.stock.rest(e.post ?? holding);
        const settled = shot();
        const after = diff(settled, done);
        return {kind: e.kind, clip: true, peak, after, live: st.clips.length};
      });
    }""", {"events": FIRED, "holding": HOLDING})
    #: **A refusal has no clip at all any more, and is not asked for one.**
    #: What it had on the island was a post beside the hut with a notice
    #: tearing in two on it, and every post and flag on this island bar a
    #: production site's marker was cut on 2026-08-27. Its whole picture is
    #: the bubble over the hut and the red outline round the card, which
    #: `overhead` below is what holds to the job -- so this asks that check
    #: exists rather than asking the island to move. Any other event with
    #: nothing to show is still a failure.
    ISLAND_SAYS_NOTHING = {"refused"}
    for r in seen:
        where = f"mechanics {r['kind']}"
        if not r.get("clip"):
            if r["kind"] not in ISLAND_SAYS_NOTHING:
                bad.append(f"{where}: the island has nothing to show for it")
            continue
        #: Share of the island. Small, because most of an island is ground --
        #: but an order of magnitude above the hairlines this replaced.
        #:
        #: **Two events are not carried by the island and are not asked to
        #: be.** An offer's picture is the rope across the frame, labelled with
        #: what is on the table and crawling toward the trader it is addressed
        #: to; a refusal's is the bubble over the hut with a cross in it. Both
        #: are SVG over the canvas, which this cannot see -- it drives a bare
        #: stage with no scene on it.
        #:
        #: That is a **decision**, not a threshold being relaxed to fit: the
        #: lamp on the offer's post and the red disc under the refusal were the
        #: last two ground-lights on the island and both were cut on report;
        #: the posts themselves went after them, with every other post and flag
        #: bar a production site's marker. Measured before and after -- an
        #: offer went 1.75% -> 0.36% and a refusal 3.20% -> 0.27% -- so the
        #: island's own share of them is small on purpose. An offer is still
        #: required to do something there: the crates it is putting on the
        #: table lift off the maker's pile, an order of magnitude above
        #: nothing. A refusal is not; see `ISLAND_SAYS_NOTHING` above.
        #:
        #: `carries` names who does hold each of them to its job, and the
        #: assertion below is that those checks are still in the suite. Without
        #: it this is an exemption; with it, it is a handover.
        carries = {"offer": "turning", "refused": "overhead"}
        floor = 0.002 if r["kind"] in carries else 0.012
        if r["peak"] < floor:
            bad.append(f"{where}: only {r['peak'] * 100:.2f}% of the island ever "
                       f"changed, under {floor * 100:.1f}%; whatever it did "
                       f"cannot be seen")
        if r["live"]:
            bad.append(f"{where}: {r['live']} clip(s) still running after the end")
        if r["after"] > 0.0015:
            bad.append(f"{where}: {r['after'] * 100:.2f}% of the island is still "
                       f"changed once it finished; it left something behind")
    # And the case `restore` actually exists for: a clip cut off part-way,
    # which is what a rebuild does to whatever was in flight. Left alone, a
    # bell interrupted mid-swing leaves every settlement's banner hanging in
    # the air over the island for the rest of the round.
    cut = page.evaluate("""(holding) => {
      const st = window.__st;
      //: **The clip, then the ambient layer, then draw** -- the order the
      //: stage's own loop runs in. This used to advance the life layer inside
      //: `shot`, which is after everything, so a clip asking the island for a
      //: brighter fire was spent before the pixels were read and the bell
      //: measured as not happening at all. The layer is advanced at one fixed
      //: moment so the ambient motion is the same in every shot and only the
      //: clip differs.
      //: **Only the rectangle the island is drawn into.**
      //:
      //: The renderer letterboxes: it draws into the rect the `<svg>` fits its
      //: viewBox into and the bands beside it are a separate pass. Those bands
      //: used to be transparent, so "opaque" and "inside the frame" were the
      //: same question and the denominator below could be counted off the
      //: alpha channel. They are open water now -- a spectator asked not to
      //: have a void round the island -- and counting alpha made the
      //: denominator the whole canvas, which cut every clip's measured share
      //: by the ratio of the two and failed the smallest one. Cropping to the
      //: frame gives back exactly the old denominator, and the bands cannot
      //: contribute to a difference either.
      const r = st.renderer.getPixelRatio();
      const [vx, vyGL, vw, vh] = st.view;
      // WebGL counts from the bottom of the canvas; a 2D context from the top.
      const src = [vx * r, st.canvas.height - (vyGL + vh) * r, vw * r, vh * r];
      const shot = () => {
        st.renderer.render(st.scene, st.camera);
        const s = document.createElement('canvas');
        s.width = 300; s.height = 187;
        const g = s.getContext('2d');
        g.drawImage(st.canvas, ...src, 0, 0, s.width, s.height);
        return g.getImageData(0, 0, s.width, s.height).data;
      };
      let ground = 0;
      const diff = (a, b) => {
        let n = 0;
        for (let i = 0; i < a.length; i += 4)
          if (Math.abs(a[i] - b[i]) + Math.abs(a[i+1] - b[i+1])
              + Math.abs(a[i+2] - b[i+2]) > 18) n++;
        return n / Math.max(1, ground);
      };
      st.clear();
      st.life.update(3, st.ctx());
      st.stock.rest(holding);
      const lit = shot();
      //: Every pixel of the crop is the island's frame, which is what this
      //: counted before the water reached the edge of the canvas.
      ground = lit.length / 4;
      const out = [];
      // The bell eats what is held; a dawn happens on an island holding
      // nothing. Both are the state their clip really runs in.
      for (const e of [{kind: 'bell', episode: 1, lapsed: 2,
                        pre: holding, post: {T1: {}, T2: {}}},
                       {kind: 'open', episode: 2, of: 3,
                        pre: {T1: {}, T2: {}}, post: {T1: {}, T2: {}}}]) {
        st.clear();
        st.stock.rest(e.pre);
        const c = st.fire(e);
        st.pause();
        c.t0 = 0;
        st.step(c.dur * 0.5);           // half way through, and then pulled
        st.life.update(3, st.ctx());
        st.clear();
        st.life.update(3, st.ctx());
        const cutShot = shot();
        // **Against the island the event should leave**, not the one before
        // it: goods are permanent now, so a bell cut off half way still ate
        // what was held and comparing with the pre-bell island reports that
        // as litter.
        st.stock.rest(e.post);
        st.life.update(3, st.ctx());
        out.push([e.kind, diff(shot(), cutShot)]);
      }
      return out;
    }""", HOLDING)
    for kind, left in cut:
        if left > 0.0015:
            bad.append(f"mechanics {kind}: cut off half way and {left * 100:.2f}% "
                       f"of the island stayed changed; it kept what it borrowed")

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
        seen = page.evaluate("""(chrome) => {""" + LAND_JS + """
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
          //
          // **The land, and not the water.** This counted every pixel with any
          // alpha, which was the island back when the canvas was transparent
          // around it. The sea runs to the corners of the frame now, so that
          // classifier returned the whole canvas: on a 393x660 phone it made
          // the island 393x464 and its share of its own band 2.30, and every
          // island-size assertion below had been passing on arithmetic that
          // could not fail. `LAND_JS` is the classifier `uncovered` and the
          // card checks already use, and it puts the same island at 198x187.
          const cv = document.getElementById('stage');
          let drawn = null, span = null, drawnBox = null;
          if (document.querySelector('.app').classList.contains('has-3d') && cv) {
            const cr = cv.getBoundingClientRect();
            const s = document.createElement('canvas');
            s.width = 200; s.height = Math.max(1, Math.round(200 * cr.height / cr.width));
            const g = s.getContext('2d');
            g.drawImage(cv, 0, 0, s.width, s.height);
            const px = g.getImageData(0, 0, s.width, s.height).data;
            let lit = 0, x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1;
            for (let y = 0; y < s.height; y++) {
              let row = 0;
              for (let x = 0; x < s.width; x++) {
                if (!LAND(px, (y * s.width + x) * 4)) continue;
                row++;
                if (x < x0) x0 = x; if (x > x1) x1 = x;
                if (y < y0) y0 = y; if (y > y1) y1 = y;
              }
              lit += row;
            }
            drawn = lit / (s.width * s.height);
            if (lit) {
              // How big the island actually draws, in the window's own pixels.
              drawnBox = { x: cr.x + x0 / s.width * cr.width,
                           y: cr.y + y0 / s.height * cr.height,
                           w: (x1 - x0 + 1) / s.width * cr.width,
                           h: (y1 - y0 + 1) / s.height * cr.height };
              span = Math.max(drawnBox.w, drawnBox.h) / Math.min(innerWidth, innerHeight);
            }
          }
          // The band the island was given: from the bottom of the chrome's own
          // reservation to the top of the first card. Read off the stylesheet
          // and the cards rather than off the layout, so this is the room a
          // person sees rather than the room the code meant to leave.
          const css = getComputedStyle(document.documentElement);
          const chromeTop = parseFloat(css.getPropertyValue('--chrome-top')) || 0;
          const cards = [...document.querySelectorAll('.card-bg')]
            .map(n => n.getBoundingClientRect()).filter(r => r.width && r.height);
          const cardTop = cards.length ? Math.min(...cards.map(r => r.y)) : innerHeight;
          return {
            scrollW: document.documentElement.scrollWidth, winW: innerWidth,
            winH: innerHeight, boxes: chrome.map(box).filter(Boolean),
            land: lb ? { w: lb.width, h: lb.height } : null, drawn, span,
            box: drawnBox,
            chromeTop, cardTop,
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
        # **Against the band the island was given, not against the window.**
        # Its share of the screen was the right question while the island had
        # the whole frame. It stopped being one when the cards took the margins
        # and the chrome took a reserved strip at either end: on a 393x660
        # phone -- a shared link opened with the browser's own bars showing --
        # the pills and one row of cards are near half the height between them,
        # so the island is small there *by arithmetic*, and a threshold on the
        # window would be a threshold on the phone rather than on the layout.
        #
        # What it asks instead is whether the island took what was left, which
        # is the thing that can actually go wrong: the defect this was written
        # for is dead sky above the island and dead sea below it inside its own
        # band, and that is exactly what fails here.
        if seen["drawn"] is not None and not seen["drawn"]:
            bad.append(f"{where}: the model drew nothing at all")
        elif seen["box"]:
            band = seen["cardTop"] - seen["chromeTop"]
            fill = seen["box"]["h"] / band if band > 0 else 0
            if band <= 0:
                bad.append(f"{where}: the cards start at {seen['cardTop']:.0f} and "
                           f"the chrome's band ends at {seen['chromeTop']:.0f}; "
                           f"there is no island band at all")
            elif fill < 0.85:
                bad.append(f"{where}: the island fills {fill:.0%} of the "
                           f"{band:.0f}px band between the chrome and the cards; "
                           f"the rest is dead sky and dead sea")
            #: A drawn island narrower than this has stopped being the picture
            #: whatever the arithmetic says, and the answer then is to take
            #: room back off the chrome rather than to move this number.
            elif seen["box"]["w"] < 0.45 * seen["winW"]:
                bad.append(f"{where}: the island draws {seen['box']['w']:.0f}px "
                           f"wide in a {seen['winW']}px window")

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


#: What a tap moves the layout by, at the least. Not the measured numbers --
#: those are 39% for the island and 19% for the cards on a 393x660 frame, and a
#: threshold set at a measurement is a threshold that fails on a font change.
#: This is "a viewer can see that something happened", which is the claim.
FOCUS_GAIN = 1.12

#: How much of its full-size self a mark on the glance card has to keep.
#:
#: **A ratio and not a floor.** This was an absolute 7 device pixels, and a
#: neuter that deleted the rule holding the trader's name up could not be made
#: to fail: 15 units at 0.58 on a 390pt window still paints a 7.5px box, so a
#: name shrunk with the card cleared the floor by half a pixel. The claim the
#: stylesheet actually makes is that what survives is drawn *at the size it
#: always was* -- declared `1/0.58` larger inside a group about to be scaled by
#: 0.58 -- so that is what is measured, against the same mark on the same card
#: at even focus. It also cannot go stale: change a font size and this follows.
FOCUS_KEPT = 0.85

#: The marks a glance card must not print at all, because at its scale they are
#: numbers nobody can read: 4.6 device pixels for a shelf's quantities at 0.55.
FOCUS_DROPPED = (".qty", ".wheel-text", ".score-value")

#: How much of the window's width the island must draw across once a viewer has
#: asked for it. **The claim is "screen wide"** and it is met to 98% on all
#: three portrait phones -- not 100%, because the frame is `520` units and the
#: island's box lands a few short of it after the band is divided. Set below the
#: measurement with room, and far enough above the 50% it draws at `even` that
#: it is a different claim and not a restatement.
FOCUS_WIDE = 0.90


def focusing(browser, base: str, board: Path, out: Path) -> list[str]:
    """A phone gives the screen to whichever of the two the viewer tapped.

    The island and a card per trader do not both fit on a phone held upright.
    At `even` on a 393x660 frame -- a shared link opened with the browser's own
    bars showing -- the island draws 198px wide in a 393px window and a card
    147px, and neither is comfortable. There is no arrangement that fixes it:
    the room is not there. So the viewer says which one they are looking at.

    Four things, and the last two are the ones that would rot quietly:

    * a tap on the island grows the island and shrinks the cards;
    * a tap on a card does the reverse;
    * a second tap on the same thing puts the frame back **exactly** where it
      was -- a toggle that drifts is a toggle nobody dares press twice;
    * the small card has stopped printing what it cannot draw. At 0.55 a
      shelf's quantities are 4.6 device pixels and its captions 4.0, so they go
      and what stays is declared larger to land at the size it always was. This
      re-measures every surviving mark in **device pixels**, because the whole
      claim is about what an eye can resolve and a unit in a viewBox is not
      that.

    And two more that came with "screen wide":

    * **the island actually reaches the frame.** The room for that could not
      come from the cards -- the arithmetic is in the stylesheet beside the
      rule that spends it -- so it comes off the chrome, which stands two of
      its four rows down at this focus. A card small enough to buy the last
      15% does not exist, so a check that only watched the cards would have
      called a 70% island a pass.
    * **and the chrome that stayed is still clear of it.** That is the whole
      risk of the row above: a band declared shorter than the pills left
      standing in it puts them back on the island, which is the defect
      `uncovered` exists for and which was reported by eye twice. Counted the
      same way it counts -- model pixels behind each pill, not boxes.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 393, "height": 660}, is_mobile=True,
                            has_touch=True, reduced_motion="reduce")
    errs: list[str] = []
    page.on("console", lambda m: errs.append(f"console {m.type}: {m.text}")
            if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(board_url(base, stem))
    page.wait_for_selector(".hut", timeout=15_000)
    page.wait_for_timeout(1400)

    #: The island's own pixels and the cards' boxes, in one read. The island is
    #: measured off the canvas with `LAND_JS` for the reason `mobile` now is:
    #: the sea fills the frame, so anything with alpha is the whole canvas.
    look = """() => {""" + LAND_JS + """
      const cv = document.getElementById('stage');
      const cr = cv.getBoundingClientRect();
      const s = document.createElement('canvas');
      s.width = 200; s.height = Math.max(1, Math.round(200 * cr.height / cr.width));
      const g = s.getContext('2d');
      g.drawImage(cv, 0, 0, s.width, s.height);
      const px = g.getImageData(0, 0, s.width, s.height).data;
      let x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, lit = 0;
      for (let y = 0; y < s.height; y++) for (let x = 0; x < s.width; x++) {
        const i = (y * s.width + x) * 4;
        if (!LAND(px, i)) continue;
        lit++;
        if (x < x0) x0 = x; if (x > x1) x1 = x;
        if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
      //: Model pixels behind each piece of chrome still standing, the way
      //: `uncovered` counts them: a box test would call the transport guilty
      //: the moment the island is drawn the full width of the frame.
      const sx = s.width / cr.width, sy = s.height / cr.height;
      const pills = CHROME.map((sel) => {
        const n = document.querySelector(sel);
        if (!n || n.hidden || !n.offsetParent) return null;
        const r = n.getBoundingClientRect();
        const bx = Math.max(0, Math.round((r.x - cr.x) * sx));
        const by = Math.max(0, Math.round((r.y - cr.y) * sy));
        const bw = Math.min(s.width - bx, Math.round(r.width * sx));
        const bh = Math.min(s.height - by, Math.round(r.height * sy));
        if (bw <= 0 || bh <= 0) return null;
        const q = document.createElement('canvas').getContext('2d');
        let on = 0;
        const d = g.getImageData(bx, by, bw, bh).data;
        for (let i = 0; i < d.length; i += 4) if (LAND(d, i)) on++;
        return { sel, on };
      }).filter(Boolean);
      const cards = [...document.querySelectorAll('.card-bg')]
        .map((n) => n.getBoundingClientRect()).filter((r) => r.width);
      //: Every mark still drawn on the first card, by how tall it actually
      //: paints. `getBBox` would answer in viewBox units, which is the one
      //: unit this question is not asked in.
      const card = document.querySelector('.card');
      const marks = {};
      for (const sel of ['.card-name', '.qty', '.glyph', '.score-value',
                         '.score .card-sub', '.wheel-text']) {
        const n = card && card.querySelector(sel);
        const r = n && n.getBoundingClientRect();
        marks[sel] = !n ? null : (r.width && r.height ? r.height : 0);
      }
      return {
        island: lit ? { w: (x1 - x0 + 1) / s.width * cr.width,
                        h: (y1 - y0 + 1) / s.height * cr.height } : null,
        lit, pills, win: innerWidth,
        cardW: cards.length ? Math.max(...cards.map((r) => r.width)) : 0,
        mini: !!document.querySelector('.card.mini'),
        marks, viewBox: document.getElementById('island').getAttribute('viewBox'),
        note: document.getElementById('focus-note').textContent.trim(),
        said: !!document.querySelector('#focus-note.on'),
      };
    }"""
    look = look.replace("() => {", "(CHROME) => {", 1)
    at_card = """() => { const n = document.querySelector('.card-bg');
      const b = n.getBoundingClientRect();
      return [b.x + b.width / 2, b.y + b.height / 2]; }"""

    def read(tag: str):
        page.screenshot(path=str(out / f"{stem}-focus-{tag}.png"), full_page=False)
        return page.evaluate(look, CHROME)

    def tap(where: str):
        if where == "island":
            seen = page.evaluate(look, CHROME)
            page.mouse.click(393 / 2, seen["island"]["h"] / 2 + 200)
        else:
            page.mouse.click(*page.evaluate(at_card))
        page.wait_for_timeout(800)

    even = read("even")
    if not even["island"]:
        page.close()
        return [f"{stem} @focus: the model drew nothing at all"]

    # The island's turn.
    tap("island")
    isle = read("island")
    grew = isle["island"]["w"] / even["island"]["w"]
    shrank = isle["cardW"] / even["cardW"] if even["cardW"] else 1
    #: The island is capped at the frame's own width -- past that its shore is
    #: cropped, because the land spans exactly its box -- so on a tall phone it
    #: is already as large as it goes and only the cards can move. Which of the
    #: two moved is the frame's business; that *something* did is the claim.
    if grew < FOCUS_GAIN and shrank > 1 / FOCUS_GAIN:
        bad.append(f"{stem} @focus: tapping the island left it at "
                   f"{isle['island']['w']:.0f}px (was {even['island']['w']:.0f}) "
                   f"and the cards at {isle['cardW']:.0f}px "
                   f"(was {even['cardW']:.0f}); the tap did not give it the "
                   f"screen")
    if isle["cardW"] > even["cardW"]:
        bad.append(f"{stem} @focus: tapping the island *grew* the cards, "
                   f"{even['cardW']:.0f}px to {isle['cardW']:.0f}px")
    if not isle["mini"]:
        bad.append(f"{stem} @focus: the island's focus drew a full card at "
                   f"{isle['cardW']:.0f}px rather than a glance card")
    if not isle["said"] or "island" not in isle["note"]:
        bad.append(f"{stem} @focus: nothing on the page said what the tap did "
                   f"(the caption reads {isle['note']!r})")
    # Screen wide, which the cards alone could never have bought.
    if isle["island"]["w"] < FOCUS_WIDE * isle["win"]:
        bad.append(f"{stem} @focus: the island the viewer asked for draws "
                   f"{isle['island']['w']:.0f}px in a {isle['win']}px window, "
                   f"{isle['island']['w'] / isle['win']:.0%} of it")
    # And the chrome left standing is still clear of it. Same rule and same
    # fraction as `uncovered`: a fortieth of the drawn island, per pill.
    for r in isle["pills"]:
        share = r["on"] / max(1, isle["lit"])
        if share > 0.025:
            bad.append(f"{stem} @focus: {r['sel']} covers {share:.0%} of the "
                       f"island the viewer just asked for; the band the chrome "
                       f"declares is shorter than the chrome standing in it")
    # A number too small to read is worse than no number, so it must be gone --
    # and what stays has to be the size it was, not a shrunk copy of it.
    for sel, height in isle["marks"].items():
        was = even["marks"].get(sel)
        if height is None or was is None:
            continue
        if sel in FOCUS_DROPPED:
            if height:
                bad.append(f"{stem} @focus: the glance card still prints {sel} "
                           f"at {height:.1f}px, which is a number nobody can read")
            continue
        if not height:
            bad.append(f"{stem} @focus: the glance card dropped {sel}, which is "
                       f"not one of the marks it may drop")
        elif was and height < FOCUS_KEPT * was:
            bad.append(f"{stem} @focus: {sel} draws {height:.1f}px tall on the "
                       f"glance card against {was:.1f}px at even focus; it was "
                       f"shrunk with the card rather than kept at its own size")

    # And back. A toggle that does not return is a toggle nobody presses twice.
    tap("island")
    back = read("back")
    if back["viewBox"] != even["viewBox"] or abs(back["cardW"] - even["cardW"]) > 1:
        bad.append(f"{stem} @focus: tapping the island again came back to "
                   f"{back['viewBox']!r} at {back['cardW']:.0f}px, not to "
                   f"{even['viewBox']!r} at {even['cardW']:.0f}px")

    # The cards' turn.
    tap("card")
    held = read("cards")
    if held["cardW"] / even["cardW"] < FOCUS_GAIN:
        bad.append(f"{stem} @focus: tapping a card took it from "
                   f"{even['cardW']:.0f}px to {held['cardW']:.0f}px")
    if held["island"]["w"] >= even["island"]["w"]:
        bad.append(f"{stem} @focus: tapping a card left the island at "
                   f"{held['island']['w']:.0f}px (was {even['island']['w']:.0f}); "
                   f"the room came from nowhere")
    if held["mini"]:
        bad.append(f"{stem} @focus: the card the viewer asked for is drawn as a "
                   f"glance card")

    #: Landscape has margins down the sides and the cards stand in them, so
    #: there is nothing there for a tap to re-divide, and the gesture is gated
    #: off rather than left to rebuild a frame it cannot improve.
    #:
    #: **Asked of the caption, not only of the frame.** `layout` ignores the
    #: focus in landscape, so a tap that got through the gate would rebuild the
    #: scene -- throwing away every animation in flight -- and arrive at exactly
    #: the same viewBox. Neutered by deleting the gate, a check that only
    #: compared frames could not be made to fail; the caption is the one thing
    #: that says a tap was taken.
    page.set_viewport_size({"width": 660, "height": 393})
    page.wait_for_timeout(700)
    wide = page.evaluate(look, CHROME)
    page.mouse.click(*page.evaluate(at_card))
    page.wait_for_timeout(700)
    after = page.evaluate(look, CHROME)
    if after["viewBox"] != wide["viewBox"] or abs(after["cardW"] - wide["cardW"]) > 1:
        bad.append(f"{stem} @focus: a tap on a landscape phone moved the frame "
                   f"from {wide['viewBox']!r} to {after['viewBox']!r}")
    if after["said"]:
        bad.append(f"{stem} @focus: a tap on a landscape phone was taken -- the "
                   f"caption reads {after['note']!r} -- and rebuilt the scene "
                   f"for a layout that ignores the focus")

    bad += [f"{stem} @focus: {e}" for e in errs]
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


#: Played, not scrubbed: a scrub paints with nothing ahead of it, and the
#: journey being measured is the one between two board events.
TRAVEL = """async () => {
  const nap = (ms) => new Promise(r => setTimeout(r, ms));
  if (!window.__island) return { error: 'the page never handed over a stage' };
  document.getElementById('play').click();
  // Somewhere in the first stretch of the board there is a gap between two
  // lines, and the island should be crossing it rather than waiting at the
  // last one. Poll for a glide in flight and measure while it runs.
  for (let i = 0; i < 120; i++) {
    const st = window.__island;
    if (st && st.glide) {
      const first = st.dayNow();
      await nap(250);
      const second = st.dayNow();
      document.getElementById('play').click();
      return { first, second };
    }
    await nap(100);
  }
  document.getElementById('play').click();
  return { error: 'no day ever travelled between two board events' };
}"""


def clockwork(browser, base: str, out: Path) -> list[str]:
    """The three ways the island's clock read wrong to a spectator.

    Reported against `island-game-001d-g1`: shadows sweeping the island at the
    *start* of a day, shadows reaching the middle of the day and stopping while
    the board went on trading, and the campfire alight through production and
    settlement. None of the three is in the record -- that board settles
    everything before its bell -- so all three were the drawing.

    Each is measured off the stage's own objects rather than off a screenshot,
    because what is asserted here is where the light *is*, and a picture can
    only say how bright it came out.
    """
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 900, "height": 600})
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    page.evaluate(STAGE, {"w": 900, "h": 600, "n": 2, "portrait": False,
                          "goods": ["bread", "cloth", "iron", "salt"]})
    seen = page.evaluate("""async () => {
      const st = window.__st;
      const nap = (ms) => new Promise(r => setTimeout(r, ms));
      const bearing = () => {
        const p = st.key.position;
        return Math.atan2(p.x, p.z);
      };
      const flame = () => {
        let f = null;
        st.island.traverse((o) => {
          if (!f && o.material && o.material.emissiveIntensity !== undefined
              && /flame/.test(o.name || '')) f = o;
        });
        return f ? f.material.emissiveIntensity : null;
      };
      // A bell, and then the dawn that follows it: the clip holds a night that
      // lifts from 1 to 0 while the page's own clock says the new day has
      // barely started.
      st.setDay(1);
      st.life.update(0, st.ctx());
      const dusk = bearing();
      st.setDay(0.02);
      st.life.hold(1);
      st.life.update(0.1, st.ctx());
      const dark = bearing();
      st.life.hold(0.5);
      st.life.update(0.2, st.ctx());
      const half = bearing();
      st.life.update(0.3, st.ctx());
      const dawn = bearing();

      // The fire, against the day the page is on.
      st.setDay(0.6);
      st.life.update(1, st.ctx());
      const midday = flame();
      st.setDay(1);
      st.life.update(2, st.ctx());
      const bell = flame();

      // The glide: told where the day is and where it will be when the next
      // line lands, the light has to cover the ground between.
      //: Two seconds, and the two reads are taken by the clock rather than by
      //: the naps: a headless browser under load runs a 200ms timer late, and
      //: a glide short enough to have finished by the time the nap returns
      //: measures the timer, not the light.
      st.setDay(0.2, 0.8, 2000);
      const t0 = performance.now();
      const before = st.dayNow();
      await nap(700);
      const midAt = (performance.now() - t0) / 2000;
      const during = st.dayNow();
      await nap(2000);
      const after = st.dayNow();
      // And a day set with nowhere to go stays put.
      st.setDay(0.3);
      await nap(120);
      const still = st.dayNow();
      return { dusk, dark, half, dawn, midday, bell,
               before, during, after, midAt, still };
    }""")
    page.close()

    # 1. The dawn's hold is a night, not an hour: it must not move the shadows.
    #    The bearing belongs to the clock, so it lands on the new day's hour the
    #    moment the page says so -- under cover of the night the clip is still
    #    drawing -- and stays there while the night lifts.
    swing = max(abs(seen["half"] - seen["dark"]), abs(seen["dawn"] - seen["dark"]))
    if swing > 0.05:
        bad.append(f"clockwork: the light swung {swing:.2f} rad while the night "
                   f"lifted; a hold is moving the sun, not just the dark")
    if abs(seen["dark"] - seen["dusk"]) < 0.5:
        bad.append(f"clockwork: a new day did not move the light off the last "
                   f"one's dusk ({seen['dusk']:.2f} -> {seen['dark']:.2f})")

    # 2. The fire is the bell. Banked at midday, up at the bell.
    if seen["midday"] is None or seen["bell"] is None:
        bad.append("clockwork: no flame on the island to measure")
    else:
        if seen["midday"] > 0.5:
            bad.append(f"clockwork: the campfire is alight at midday "
                       f"({seen['midday']:.2f}), while the island is still "
                       f"producing and settling")
        if seen["bell"] < seen["midday"] * 2:
            bad.append(f"clockwork: the campfire does not come up by the bell "
                       f"({seen['midday']:.2f} -> {seen['bell']:.2f})")

    # 3. The day travels over a silence instead of freezing at the last event.
    # Where the light should have got to by the time the middle read was taken,
    # measured off the same clock the glide runs on rather than off the nap.
    want = 0.2 + 0.6 * min(1.0, seen["midAt"])
    if not seen["before"] < seen["during"] <= seen["after"]:
        bad.append(f"clockwork: the island's day did not travel between two "
                   f"board events ({seen['before']:.2f}, {seen['during']:.2f}, "
                   f"{seen['after']:.2f}); the shadows are frozen at whatever "
                   f"the last line said")
    elif abs(seen["during"] - want) > 0.05:
        bad.append(f"clockwork: the day is not on the glide's own clock "
                   f"({seen['during']:.2f} at {seen['midAt']:.2f} of the way "
                   f"through, wanting {want:.2f})")
    if abs(seen["after"] - 0.8) > 0.02:
        bad.append(f"clockwork: the day overran where the next line lands "
                   f"({seen['after']:.2f} against 0.80)")
    if abs(seen["still"] - 0.3) > 1e-6:
        bad.append(f"clockwork: a day with nowhere to go drifted "
                   f"({seen['still']:.4f} against 0.30)")
    return bad


def travelling(browser, base: str, board: Path, out: Path) -> list[str]:
    """And the page hands the island both ends of that journey.

    `clockwork` drives the stage directly, so it holds the glide shut without
    ever asking whether the page uses it -- and the whole bug was in the
    wiring: `setDay` was called with the day and nothing else while `sky` was
    given the day *and* where it would be by the next line. So this one plays a
    real replay and watches the island's own clock move between two board
    events.
    """
    stem = board.name[len("board-"):-len(".json")]
    bad: list[str] = []
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    page.goto(board_url(base, stem))
    page.wait_for_selector(".hut", timeout=15_000)
    page.wait_for_timeout(1200)
    seen = page.evaluate(TRAVEL)
    page.close()
    if seen.get("error"):
        bad.append(f"{stem} travelling: {seen['error']}")
    elif not seen["second"] > seen["first"]:
        bad.append(f"{stem} travelling: the island's day stood still through a "
                   f"glide ({seen['first']:.3f} -> {seen['second']:.3f})")
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


WHOSE = """async ({w, h, n, goods, turns}) => {
  const THREE = await import('./vendor/three/three.module.js');
  const { Stage } = await import('./stage.js');
  const { layout } = await import('./scene.js');
  const { SEAT_COLOURS } = await import('./island3d.js');
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h; document.body.appendChild(cv);
  const st = new Stage(cv, layout(n, false, w / h, {top: 0, foot: 0}));
  st.pause();
  const traders = Array.from({length: n}, (_, i) => `T${i + 1}`);
  const made = st.build({traders, goods});
  st.pause(); st.setDay(0.45); st.life.update(0, st.ctx());

  const ray = new THREE.Raycaster();
  //: A mesh's *unoccluded* screen area. Points on its own surface, each
  //: raycast from the camera: a point counts only when nothing else in the
  //: scene stands between. This is the whole question -- the band that could
  //: not be seen was drawn, lit, and in the frame, and every check that asked
  //: whether it existed passed.
  const seen = (mesh, cam) => {
    const pos = mesh.geometry.attributes.position;
    const step = Math.max(1, Math.floor(pos.count / 200));
    let shown = 0, total = 0;
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (let i = 0; i < pos.count; i += step) {
      const p = new THREE.Vector3().fromBufferAttribute(pos, i);
      mesh.localToWorld(p);
      total++;
      const dir = p.clone().sub(cam.position);
      const far = dir.length();
      ray.set(cam.position, dir.normalize());
      const hit = ray.intersectObject(made.island, true)[0];
      if (!hit || (hit.object !== mesh && hit.distance < far - 0.02)) continue;
      shown++;
      const s = p.clone().project(cam);
      const sx = (s.x + 1) / 2 * w, sy = (1 - s.y) / 2 * h;
      x0 = Math.min(x0, sx); x1 = Math.max(x1, sx);
      y0 = Math.min(y0, sy); y1 = Math.max(y1, sy);
    }
    return {shown, total, w: shown ? x1 - x0 : 0, h: shown ? y1 - y0 : 0};
  };

  const out = [];
  for (const spin of turns) {
    //: Round the island, because the accents are on a hut that faces the fire
    //: and the camera does not stay behind it. `spin` is the same turn the
    //: page's own camera makes with time. `aim` is what the page calls.
    st.aim(spin);
    st.camera.updateMatrixWorld(true);
    made.island.updateMatrixWorld(true);
    const at = {spin, huts: []};
    traders.forEach((t, i) => {
      const row = {trader: t,
                   colour: '#' + SEAT_COLOURS[i % SEAT_COLOURS.length].toString(16).padStart(6, '0')};
      for (const part of ['door', 'band', 'finial']) {
        const m = made.island.getObjectByName(`hut_${t}_${part}`);
        row[part] = m ? seen(m, st.camera) : null;
      }
      at.huts.push(row);
    });
    out.push(at);
  }
  return out;
}
"""


def whose(browser, base: str, out: Path) -> list[str]:
    """A hut says whose it is, to a camera that is actually looking at it.

    **The band was drawn where nothing could see it, and every check passed.**
    Reported by eye -- *"I don't see the door and band"* -- of an accent that
    had been in the model for weeks with a comment claiming it was "visible
    from any bearing the camera swings to". It was: the failure was in
    elevation, not bearing. The roof is a cone of radius 0.52 whose rim sits at
    y = 0.42, and the band was a ring of radius 0.40 at y = 0.41, so the only
    camera that could ever have seen it was one standing under the eaves. This
    island is watched from above. Measured before the fix: **0 of 148 sample
    points**, on both huts, at every bearing.

    Existence is not visibility, which is why nothing here counts meshes. Each
    accent's own surface is sampled and each sample raycast from the camera; a
    point counts only when the accent is the first thing the ray meets.
    """
    page = browser.new_page(viewport={"width": 1200, "height": 800})
    errs: list[str] = []
    page.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))
    page.goto(f"{base}/")
    page.wait_for_timeout(600)
    turns = [0, 2.5, 5.0, 7.5]
    rounds = page.evaluate(WHOSE, {"w": 1200, "h": 800, "n": 3, "turns": turns,
                                   "goods": ["bread", "cloth", "iron", "salt"]})
    page.screenshot(path=str(out / "island-whose.png"))
    page.close()
    bad = [f"whose: {e}" for e in errs]

    #: What a spectator has to be able to see. The band is the one held to a
    #: size, because it is the accent that has to work from every bearing: the
    #: door faces the fire and goes edge-on as the camera comes round, which is
    #: exactly why the colour is not left to the door alone. 24 pixels is
    #: roughly the width of a good's chip in the legend.
    BAND_PX = 24
    for at in rounds:
        for hut in at["huts"]:
            where = f"whose {hut['trader']} at spin {at['spin']}"
            band = hut["band"]
            if band is None:
                bad.append(f"{where}: the hut has no band at all")
                continue
            if not band["shown"]:
                bad.append(f"{where}: none of the band's {band['total']} points "
                           f"is unoccluded -- the colour is drawn where nothing "
                           f"can see it")
            elif band["w"] < BAND_PX:
                bad.append(f"{where}: the band shows {band['w']:.0f}px across, "
                           f"under the {BAND_PX}px floor")
            seen_any = [k for k in ("door", "band", "finial")
                        if hut[k] and hut[k]["shown"]]
            if len(seen_any) < 2:
                bad.append(f"{where}: only {seen_any or 'nothing'} of the hut's "
                           f"accents can be seen; one mark is one occlusion "
                           f"from a hut that says nothing")
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
