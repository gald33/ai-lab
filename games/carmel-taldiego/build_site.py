"""The published pages: a few campaigns, drawn and flown, for the web.

    python3 games/carmel-taldiego/build_site.py --out /tmp/site

Gal, 2026-09-10: *"make it available online as a github page"*. This writes
the tree `pages.yml` stages at
`https://gald33.github.io/ai-lab/carmel-taldiego/`.

**THE FIRST N CAMPAIGNS, NEVER THE BEST N.** The seeds are
`sha256(SEED_ROOT || i)` for i in 0..N, and whatever those produce is what
goes up -- the short ones, the ones where she is caught in two rooms, the
dull ones. Picking the pretty campaigns would make the page a highlight
reel, which is a claim about the distribution that the distribution does
not support, and this lab has a rule about choosing a population after
seeing the results (`CLAUDE.md`, "Never drop failed runs from a
denominator"). The page says the seeds out loud so anybody can re-run them
and get the same trails.

**Why it lives at `/carmel-taldiego/` and not at the root.** The root of
that site redirects to the island (`site/index.html`, Gal 2026-09-07, and
`pages.yml` explains why: the root is cited in run records as the island's
address). One game owning the root is what that decision already refused,
so this one takes a path of its own. Nothing here changes the island's
door.

**Imagery is on for the published cards**, and off by default here so the
tests need no network. NASA GIBS is public domain, so redistributing the
tiles inside a published page is exactly what it is for -- and a page whose
whole point is "look at the real world" should not ship the schematic one.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import trail_card as TC  # noqa: E402
import trail_flight as TF  # noqa: E402

#: Fixed, so the published campaigns are the same ones every deploy and a
#: reader can reproduce any of them from the seed printed on its card.
SEED_ROOT = b"carmel-taldiego/pages/v1"

#: How many go up. Six is enough to show the spread -- caught and clear,
#: two rooms and seven -- without the page becoming a scroll.
CAMPAIGNS = 6

SEARCHERS = 2


def seeds(count: int = CAMPAIGNS, root: bytes = SEED_ROOT) -> list[bytes]:
    return [hashlib.sha256(root + i.to_bytes(4, "big")).digest()
            for i in range(count)]


def build(out: Path, imagery: str | None = "relief",
          count: int = CAMPAIGNS) -> list[dict]:
    """Write the tree and return what went into it."""
    out.mkdir(parents=True, exist_ok=True)
    base = C.Map(bytes(32))
    made = []

    for i, seed in enumerate(seeds(count), start=1):
        world = C.Map(seed)
        world.descriptors, world.places, world.treasure = (
            base.descriptors, base.places, base.treasure)
        result = C.chase(seed, C.LOBBY_LANDMARK, searchers=SEARCHERS,
                         world=world)

        room = out / f"{i:02d}"
        room.mkdir(exist_ok=True)
        (room / "card.svg").write_text(
            TC.card(result, world, seed, C.LOBBY_LANDMARK, imagery=imagery),
            encoding="utf-8")
        (room / "flight.html").write_text(
            TF.page(result, world, seed, C.LOBBY_LANDMARK), encoding="utf-8")

        legs = result["moves"]
        made.append({
            "n": i, "seed": seed.hex(), "dir": f"{i:02d}",
            "outcome": result["outcome"],
            "rooms": len(legs),
            "emptied": len(TC.kept(result)),
            "reputation": result["reputation"],
            "hours": round(result["hours"]),
            "last": legs[-1]["to"] if legs else C.LOBBY_LANDMARK,
        })

    (out / "index.html").write_text(index(made, imagery), encoding="utf-8")
    return made


def index(made: list[dict], imagery: str | None) -> str:
    INK = TC.INK
    rows = []
    for m in made:
        rows.append(f"""
  <li class="campaign">
    <a class="shot" href="{m['dir']}/flight.html">
      <img src="{m['dir']}/card.svg" width="1000" height="640"
           alt="Carmel Taldiego, {html.escape(m['outcome'])}: {m['rooms']} rooms,
                ending at {html.escape(m['last'])}" loading="lazy">
    </a>
    <div class="meta">
      <span class="outcome {'caught' if m['outcome'] == 'caught' else 'won'}"
        >{html.escape(m['outcome'])}</span>
      <span>{m['rooms']} rooms, {m['emptied']} emptied</span>
      <span>{m['reputation']} reputation</span>
      <span>{m['hours']} hours</span>
      <a href="{m['dir']}/flight.html">watch the flight →</a>
      <code>{m['seed']}</code>
    </div>
  </li>""")

    return f"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Carmel Taldiego</title>
<meta name="description" content="A fugitive moves between a thousand
  landmarks and posts one true thing about each room she reaches. Six
  campaigns, drawn and flown.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'
  viewBox='0 0 16 16'><text y='14' font-size='14'>&#128506;</text></svg>">
<style>
  :root {{ color-scheme: dark; }}
  html, body {{ margin: 0; background: {INK['ground']}; color: {INK['text']};
                font-family: Georgia, "Times New Roman", serif; }}
  .wrap {{ max-width: 1000px; margin: 0 auto; padding: 40px 20px 80px; }}
  h1 {{ font-size: clamp(28px, 6vw, 46px); font-weight: normal; margin: 0 0 6px; }}
  .sub {{ color: {INK['dim']}; font-size: clamp(14px, 2vw, 17px);
          margin: 0 0 28px; max-width: 62ch; line-height: 1.55; }}
  .sub a {{ color: {INK['line']}; }}
  ul {{ list-style: none; margin: 0; padding: 0; }}
  .campaign {{ margin: 0 0 44px; }}
  .shot {{ display: block; }}
  .shot img {{ width: 100%; height: auto; display: block;
               border: 1px solid {INK['rule']}; }}
  .meta {{ display: flex; flex-wrap: wrap; gap: 14px; align-items: baseline;
           padding: 10px 2px 0; font-size: 13px; color: {INK['dim']}; }}
  .outcome {{ font-size: 15px; }}
  .won {{ color: {INK['stop']}; }}
  .caught {{ color: {INK['theft']}; }}
  .meta a {{ color: {INK['line']}; text-decoration: none; }}
  .meta a:hover {{ text-decoration: underline; }}
  .meta code {{ font-size: 10px; color: {INK['rule']}; word-break: break-all; }}
  footer {{ color: {INK['dim']}; font-size: 12px; border-top: 1px solid
            {INK['rule']}; padding-top: 16px; line-height: 1.7; }}
  footer a {{ color: {INK['line']}; }}
</style>
<div class="wrap">
  <h1>Carmel Taldiego</h1>
  <p class="sub">
    She moves between a thousand real landmarks and posts <em>one true
    thing</em> about every room she reaches — the least informative true
    thing she can say. Searchers read it, work out where she can have gone,
    and go and wait. She is only catchable while she is standing still
    stealing something.
    <a href="https://github.com/gald33/ai-lab/blob/main/games/carmel-taldiego.md">How
    it works</a> ·
    <a href="https://github.com/gald33/ai-lab/tree/main/games/carmel-taldiego">Source</a>
  </p>
  <ul>{''.join(rows)}
  </ul>
  <footer>
    <p>These are the <strong>first six</strong> campaigns from a fixed seed
    root — not the best six. Whatever they produced is what is here, because
    picking the good ones would be a claim about the distribution that the
    distribution does not support. Every seed is printed above; re-run one
    with
    <code>python3 games/carmel-taldiego/trail_card.py --seed &lt;seed&gt;</code>.</p>
    <p>Basemap: Natural Earth (public domain).{
      " Imagery: NASA GIBS / Blue Marble (public domain)." if imagery else ""
    } No place names on either, on purpose — the map must not name the
    candidates.</p>
  </footer>
</div>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="directory to write")
    ap.add_argument("--imagery", nargs="?", const="relief", default=None,
                    metavar="LAYER",
                    help="NASA GIBS layer under the cards (default: none, "
                         "which needs no network)")
    ap.add_argument("--campaigns", type=int, default=CAMPAIGNS)
    ap.add_argument("--clean", action="store_true",
                    help="empty the output directory first")
    args = ap.parse_args()

    out = Path(args.out)
    if args.clean and out.exists():
        shutil.rmtree(out)
    made = build(out, imagery=args.imagery, count=args.campaigns)

    for m in made:
        print(f"  {m['n']:2}. {m['outcome']:>9}  {m['rooms']} rooms,"
              f" {m['emptied']} emptied, {m['reputation']:>4} rep,"
              f" ends {m['last'][:30]}")
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"\nwrote {out}  {len(made)} campaigns, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
