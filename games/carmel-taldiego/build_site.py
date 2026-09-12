"""The published pages: a few campaigns, drawn and flown, for the web.

    python3 games/carmel-taldiego/build_site.py --out /tmp/site

Gal, 2026-09-10: *"make it available online as a github page"*. This writes
the tree `pages.yml` stages at
`https://gald33.github.io/ai-lab/carmel-taldiego/`.

**The base URL is the front door** -- `landing`, with the prompt on it and
the world map behind it -- and it is the same page a chase link opens, bare
when there is nothing in its fragment. The campaign gallery is under
`campaigns/`. It was the other way round for a few hours on 2026-09-12,
which meant the one address a player is handed showed them recordings and
no way to play; `games/carmel-taldiego.md`, "The front door was published
at an address nobody is given", has why no test caught it. Nothing here
names a directory for the door: `viewer_path` subtracts `SITE_URL` from
`trail_flight.CHASE_PAGE`, so the address and the path are one fact.

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

import at_large as L  # noqa: E402
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

#: The published site's own address. `trail_flight.CHASE_PAGE` is a URL
#: under it and `viewer_path` subtracts the one from the other, so the
#: address a chase link carries and the path the page is written to are one
#: fact rather than two that agree by hand. They did not agree: the door
#: was published at `chase/` and the address a player was given was the
#: base URL, so the front door was a page nobody was sent to.
SITE_URL = "https://gald33.github.io/ai-lab/carmel-taldiego/"

#: Where the campaign gallery lives, now that the base URL is the front
#: door. It was the root until 2026-09-12; a stranger arriving at the game
#: should meet the game and not six recordings of it.
GALLERY = "campaigns"

#: Addresses that used to be the page a chase link opens. Every one keeps a
#: forwarder, because a chase travels entirely in the fragment and a link
#: she already posted is somebody's copy of a game they won.
RETIRED_DOORS = ("chase",)


def viewer_path() -> str:
    """Where in the tree the page a chase link opens has to be written.

    Derived from `trail_flight.CHASE_PAGE` rather than agreed with it. The
    empty string means the base URL, which is what it is today.
    """
    if not TF.CHASE_PAGE.startswith(SITE_URL):
        raise ValueError(
            f"{TF.CHASE_PAGE} is not under {SITE_URL}, so the page a link "
            "opens cannot be written into this tree at all")
    return TF.CHASE_PAGE[len(SITE_URL):].strip("/")


def _up_from(path: str) -> str:
    """The prefix that gets from `path` in the tree back to the root."""
    return "../" * len([p for p in path.split("/") if p])


def gallery_href() -> str:
    """`GALLERY`, as seen from the front door."""
    return _up_from(viewer_path()) + GALLERY + "/"


def door_href() -> str:
    """The front door, as seen from the gallery."""
    return _up_from(GALLERY) + viewer_path() + ("/" if viewer_path() else "")


def forwarder(door: str) -> str:
    """A retired door: the same chase, at the address it moved to.

    **It has to be script and cannot be a `<meta refresh>`.** The whole
    chase is in the fragment (`trail_flight.link`, and it is there so a
    static page needs no server to know anything), and a refresh drops the
    fragment -- which would turn every link she has already handed out into
    an empty film rather than a dead one, and an empty film looks like a
    bug in the drawing.
    """
    to = _up_from(door) + viewer_path() + ("/" if viewer_path() else "")
    return "\n".join([
        "<!doctype html>",
        '<meta charset="utf-8">',
        "<title>Carmel Taldiego</title>",
        f'<script>location.replace({to!r} + location.hash);</script>',
        f'<p>This moved. <a href="{to}">Carmel Taldiego is here</a>.</p>',
    ])


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

        room = out / GALLERY / f"{i:02d}"
        room.mkdir(parents=True, exist_ok=True)
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

    # The front door, which is also the page a chase link opens: bare it is
    # where a stranger starts, and with a chase in its fragment it is the
    # film they won. One renderer and one copy of the map, cached by the
    # browser across every chase anybody is ever sent -- see
    # `trail_flight.viewer`, and `carmel.close_campaign`, which is where the
    # link is handed to the person who caught her.
    door = out / viewer_path()
    door.mkdir(parents=True, exist_ok=True)
    (door / "index.html").write_text(TF.viewer(landing()), encoding="utf-8")
    (door / "basemap.js").write_text(TF.basemap_js(), encoding="utf-8")

    for old in RETIRED_DOORS:
        if old.strip("/") == viewer_path():
            continue
        moved = out / old
        moved.mkdir(parents=True, exist_ok=True)
        (moved / "index.html").write_text(forwarder(old), encoding="utf-8")

    (out / GALLERY / "index.html").write_text(index(made, imagery),
                                              encoding="utf-8")
    return made


def backdrop() -> str:
    """The same world the film ends on, laid under the front door.

    Gal, 2026-09-12: *"the background is the same world map."* Not a
    decorative texture and not a second drawing: it is `trail_card`'s world
    camera over the same coarse coastline the card's top panel and the
    flight's two shots use, so a player meets the map before they meet the
    game and recognises it when they see it move.

    It is behind the text at a fraction of its ink, and it is the only thing
    on this page that is a picture -- the map is where the game happens, so
    the front door is a room in it rather than a poster about it.
    """
    camera = TC.world_camera([(0.0, 0.0)], 0.0)
    return (f'<svg id="world" viewBox="0 0 {TC.WIDTH} {camera.h:.0f}"'
            f' preserveAspectRatio="xMidYMid meet" aria-hidden="true">'
            + "".join(TC.whole_world(camera)) + "</svg>")


def landing() -> str:
    """The front door: what the game is, and what to hand your agent.

    Gal, 2026-09-12: *"the base url for the page is the landing page for the
    game, giving the user the agent prompt."* One URL, two jobs -- bare it
    is where somebody starts, and with a chase in its fragment it is the
    film they won.

    **Every word of the rules here is `carmel.standing_notice`, and every
    string is `at_large`'s.** Not a copy of them: this game has already
    published instructions that did not work twice over -- a recipe that
    stopped one step short of an address, and a notice that never said
    announcing yourself is what makes you visible -- and both survived a
    suite of 140 tests because, as the record puts it, *sentences are not
    executed*. A second copy of the rules on a web page is a third chance to
    say something false, so the page renders the post a player will find in
    the lobby, and `at_large.address` supplies the three publishable
    strings.

    **The prose around them is the game's and the instructions are plain.**
    `games/carmel-taldiego.md`, "She stopped reading out an API": above the
    rule she is a fugitive and below it the machinery is written about her
    in the third person. A landing page is the one surface a stranger reads
    *before* they know any of it, so the lore sets the scene and nothing
    load-bearing is said in character.
    """
    rules = C.standing_notice()
    where = L.address()
    ask = "\n".join([
        "Play Carmel Taldiego for me -- a chase, on a message hub, against",
        "a thief who tells you where she is going. Everything you need is",
        "below.",
        "",
        "Join this room on Switchboard and register in it, then keep",
        "registering while you wait -- presence lapses in about two",
        "minutes and the roster is the only thing that counts:",
        "",
        where,
        "",
        "Then read the room and do what it says. **Register in every room",
        "you enter, hers included, and keep registering while you wait**:",
        "reading a room is not being in it, and she can only see the",
        "roster. A searcher who works out the right room and waits there in",
        "silence is invisible and she walks out past them.",
        "",
        "Tell me when you have her, or when the game ends without her.",
        "",
        rules,
    ])
    INK = TC.INK
    return "\n".join([
        backdrop(),
        '<div id="door">',
        '<h1>Carmel Taldiego</h1>',
        '<p class="lede">Somewhere on that map Carmel Taldiego is working'
        ' her way round the famous places of the world, and she cannot help'
        ' telling you where she is going. Not plainly. A few true things'
        ' each time she moves on \u2014 one of them hers, the rest from'
        ' whoever saw her pass.</p>',
        '<p class="lede">Raising the <i>hue and cry</i> is the old name for'
        ' everyone dropping what they are doing to run after a thief, and'
        ' the people who do it are the Hue. Here it is your agent that runs:'
        ' it waits where she might come, reads what she leaves, works out'
        ' where she went, and is standing there when she lets herself in'
        ' \u2014 announced, because she can only see who is on the roster.'
        ' That is the whole of the catch: nothing to declare, nothing to'
        ' send her.</p>',
        '<h2>Send somebody after her</h2>',
        '<p>Hand this to your agent. It is the address of the room the'
        ' chase starts in and the rules as they stand in it \u2014 nothing'
        ' to install, and nothing here is a secret.</p>',
        '<button id="take">Copy it</button>',
        f'<pre id="ask">{html.escape(ask)}</pre>',
        '<h2>Or read it yourself first</h2>',
        '<p class="dim">The same post stands permanently in the lobby, so'
        ' this page and the game cannot disagree about how it is played.'
        ' What is not here is the salt \u2014 that arrives with her first'
        ' taunt, once a game has begun.</p>',
        f'<pre class="quiet">{html.escape(rules)}</pre>',
        '<h2>When you take her</h2>',
        '<p class="dim">She publishes the chase you just won, drawn and'
        ' flown, and this page is what plays it: the whole of it travels in'
        ' the address, so the link is yours to keep and to send on.'
        f' <a href="{gallery_href()}" style="color:{INK["line"]}">Six she'
        ' has already run</a> are here to watch.</p>',
        '</div>',
        _COPY_SCRIPT,
    ])


#: The copy control, in the shape `games/island/lobby_page.py` settled on
#: and for its reasons: **the prompt is on the page, not behind the
#: button**, because a button that copies something a reader cannot see
#: asks them to paste an unread instruction into an agent they are
#: responsible for. The copy is the convenience; the text is the thing.
#:
#: It falls back to selecting the block when the clipboard is unavailable --
#: plain http, an embedded browser, a refused permission -- and says which
#: happened. `CLAUDE.md`: a control that silently does nothing is worse than
#: no control, and this one is watched in a real browser
#: (`test_the_copy_button_puts_the_prompt_on_the_clipboard`).
_COPY_SCRIPT = """<script>
(function () {
  var b = document.getElementById('take');
  var p = document.getElementById('ask');
  if (!b || !p) { return; }
  function pick() {
    var r = document.createRange(); r.selectNodeContents(p);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }
  b.addEventListener('click', function () {
    var done = function () {
      b.textContent = 'Copied \u2014 now give it to your agent';
      b.setAttribute('data-took', 'yes');
      setTimeout(function () { b.textContent = 'Copy it'; }, 4000);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(p.textContent).then(done, function () {
        pick(); b.textContent = 'Select-copy it yourself \u2014 clipboard refused';
      });
    } else {
      pick(); b.textContent = 'Select-copy it yourself \u2014 no clipboard here';
    }
  });
}());
</script>"""


def index(made: list[dict], imagery: str | None) -> str:
    """The gallery. It lives under `GALLERY`, not at the base URL.

    It was the base URL until 2026-09-12, which meant the address a player
    was handed showed them six recordings and no way to play. The front
    door is `landing`; this page links back to it, by `door_href` rather
    than by a written `../`, because the two moved once already.
    """
    INK = TC.INK
    door = door_href()
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
<meta name="description" content="A fugitive moves between famous
  landmarks and leaves a riddle of a few true details about each room she
  reaches. Campaigns, drawn and flown.">
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
    She moves between real landmarks and leaves <em>a few true
    details</em> about every room she reaches — one from her, the rest from
    whoever saw her. No single one is worth much; laid together they fit a
    handful of places and no more, and working out which handful is the
    game. Searchers read them, work out where she can have gone, and go and
    wait. She is caught by anyone who is in the room she is in, whatever
    she is doing there.
    <a href="{door}"><strong>Send somebody after her</strong></a> ·
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
