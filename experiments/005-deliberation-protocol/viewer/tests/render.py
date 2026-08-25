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
            # Every replay, not just the first. `boards[0]` meant a newly
            # published game was never rendered by anything until somebody
            # opened it -- which is exactly how the live board's seat names
            # got past this harness and were found by eye instead.
            for board in boards:
                problems += replay(browser, base, board, out)
            for board in boards:
                problems += blame(browser, base, board, out)
            problems += bare(browser, base, boards[0], out)
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

    Four of the eight refusals across games 001 and 002 are one trader
    approving goods its own open offer already holds. The page drew a bare ✗
    for all of them while the cause -- a rope -- was on the square the whole
    time. This drives the real refusal from game 002's board and checks that
    the offer lit is the trader's own, and not the one it failed to take.
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
