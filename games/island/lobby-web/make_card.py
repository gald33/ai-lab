"""Render `card.html` to `card.png`, the image a posted link renders as.

    python games/island/lobby-web/make_card.py

Committed as a PNG because that is what Open Graph consumers fetch -- most of
them will not rasterise an SVG, and several will not follow a redirect -- but
**generated, not drawn by hand**, so the next person to want different words on
it edits `card.html` and re-runs this rather than opening an image editor and
guessing at the font.

`--check` re-renders to a temporary file and compares, so CI can say the
committed PNG is the one the current `card.html` produces. That check is
deliberately not wired into any deploy job: a font substitution on a different
runner would fail it for a reason nobody can act on, and the card being one
revision behind its source is not worth a red deploy. It is here for the person
changing the card.

It lives beside the page that declares it because Vercel's root directory is
`games/island/lobby-web` with "include files outside the root directory" off,
so `card.png` has to be a file in here to exist at `/card.png` at all.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CARD = HERE / "card.html"
OUT = HERE / "card.png"

#: What every Open Graph consumer expects, and what `index.html` declares. A
#: card rendered at another size is letterboxed or cropped by the consumer.
SIZE = (1200, 630)


def render(target: pathlib.Path) -> None:
    from playwright.sync_api import sync_playwright

    chrome = next((p for p in pathlib.Path("/opt/pw-browsers").glob("chromium*")
                   if p.is_file()), None)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=str(chrome) if chrome else None)
        page = browser.new_page(viewport={"width": SIZE[0], "height": SIZE[1]},
                                device_scale_factor=1)
        page.goto(CARD.as_uri())
        # Web fonts are not used, but the SVG and the gradient still need a
        # frame to paint before the shot is taken.
        page.wait_for_timeout(300)
        page.screenshot(path=str(target))
        browser.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed card is not what card.html renders")
    args = ap.parse_args(argv)

    if not args.check:
        render(OUT)
        print(f"wrote {OUT.relative_to(HERE.parent)} ({OUT.stat().st_size} bytes)")
        return 0

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        fresh = pathlib.Path(tmp) / "card.png"
        render(fresh)
        if not OUT.is_file():
            print("no card.png committed; run without --check", file=sys.stderr)
            return 1
        if fresh.read_bytes() != OUT.read_bytes():
            print("card.png is not what card.html renders; re-run "
                  "`python games/island/lobby-web/make_card.py`",
                  file=sys.stderr)
            return 1
    print("card.png matches card.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
