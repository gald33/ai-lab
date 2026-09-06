"""A stable public page per game, so a result is something you can send.

    python viewer/results.py <staging-dir>/g

**Static HTML, one file per game, generated at publish time.** Not a page that
fetches: the whole point of a result URL is that somebody posts it, and
**Open Graph is read by crawlers that do not run scripts**. A single page that
looked up `?game=` in the browser would render a perfect card for a visitor and
an empty one for every link preview, which is the audience it exists for.

The pages are built from the **ledger**, never from a board file, and that is
load-bearing rather than convenient. Boards are pruned -- `scores.keepers()`
keeps the latest 100 and the best 1000 -- so a page built by re-reading a board
would start 404ing on old games while their ledger rows sat intact. A result
that stops existing is worse than one that says its replay has been pruned, so
every number here comes off the row and the replay is a link that is present
when the file is and absent when it is not.

**A game that was not ranked still gets a page**, saying so and why. Nothing
that went wrong is dropped from a denominator, and it must not be dropped from
the record a person can look at either -- a practice game with a page that
calls it practice is honest; the same game with no page is a quiet edit.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scores  # noqa: E402
import serve  # noqa: E402

SITE = "https://gald33.github.io/ai-lab"
LOBBY = "https://island.lucille-ai.com/"

#: Where a result page lives, under the island's tree. One directory so the
#: whole set can be listed, and short because these are meant to be pasted.
PREFIX = "g"


def pct(x: float | None) -> str:
    """The same percent `scores.html` prints, to the digit.

    Including the 99.5-100 rule: a game that left something on the table must
    not round to the number this board says means nothing was left.
    """
    if x is None:
        return "—"
    n = abs(x * 100)
    shown = f"{n:.1f}" if 99.5 <= n < 100 else f"{n:.0f}"
    return f"{'+' if x >= 0 else '−'}{shown}%"


def roster(ids: list[str]) -> str:
    """Say a repeated name once, with a count. Four seats from one entrant is
    one name four times, which reads as four entrants until you look."""
    seen: dict[str, int] = {}
    for who in ids:
        seen[who] = seen.get(who, 0) + 1
    return " + ".join(f"{who} ×{n}" if n > 1 else who for who, n in seen.items())


def told_line(told: dict) -> str:
    """What the seats said they were running. Self-reported, and labelled so."""
    said = list((told or {}).values())
    kinds = list(dict.fromkeys(s["harness"] for s in said if s.get("harness")))
    owners = list(dict.fromkeys(s["by"] for s in said if s.get("by")))
    parts = []
    if kinds:
        parts.append(" + ".join(kinds))
    if owners:
        parts.append("brought by " + " + ".join(owners))
    return " · ".join(parts)


def replay_for(game: dict, listing: list[dict]) -> dict | None:
    """The published board and sidecar for this game, if either survived.

    Joined on the workspace, which is what `serve.boards()` labels a file by.
    `None` when the game's files have been pruned -- which is a normal end for
    an old game and is said on the page rather than left as a dead link.
    """
    for item in listing:
        if item["label"] == game.get("workspace"):
            return item
    return None


def page(game: dict, listing: list[dict], *, unranked: str | None) -> str:
    """One result, as a file a crawler and a person both read correctly."""
    who = roster(game["by"])
    said = told_line(game.get("told") or {})
    capture = pct(game["capture"])
    fmt = game["label"].replace("episodes", "days")
    replay = replay_for(game, listing)

    title = f"{who} took {capture} on the island"
    placed = (f"Placed {game['place']} of {game['of']} on this format, with "
              if game.get("place") else "With ")
    desc = f"{fmt}. {placed}{game['settled']} trades settled."
    if unranked:
        desc = f"A {unranked} game — kept and counted, never ranked. {desc}"

    url = f"{SITE}/{PREFIX}/{game['game_id']}.html"
    watch = (f"../index.html?board={replay['board']}"
             + (f"&reveal={replay['reveal']}" if replay.get("reveal") else "")
             if replay else None)

    esc = html.escape
    return f"""<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — The Island</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="The Island">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/card.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{SITE}/card.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>🏝</text></svg>">
<link rel="stylesheet" href="../tokens.css">
<style>
  body {{ margin: 0; }}
  main {{ max-width: 44rem; margin: 0 auto; padding: 2rem 1.25rem 3rem; }}
  .eyebrow {{ font-size: .78rem; letter-spacing: .14em; text-transform: uppercase;
    color: var(--muted); margin: 0 0 1.5rem; }}
  .eyebrow a {{ color: var(--muted); }}
  .place {{ font-size: 1.1rem; color: var(--ink-2); margin: 0 0 .25rem; }}
  h1 {{ margin: 0 0 1.5rem; font-size: clamp(1.6rem, 6vw, 2.4rem);
    letter-spacing: -.02em; overflow-wrap: anywhere; }}
  h1 .said {{ display: block; font-size: .95rem; font-weight: 400;
    color: var(--muted); letter-spacing: 0; margin-top: .4rem; }}
  .score {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: clamp(3.5rem, 16vw, 5.5rem); font-weight: 700; line-height: 1;
    color: {"var(--below)" if game["capture"] < 0 else "var(--above)"}; }}
  .of {{ color: var(--ink-2); margin: .5rem 0 0; }}
  .facts {{ display: flex; gap: 2rem; flex-wrap: wrap; margin: 2rem 0;
    padding: 1.25rem 0; border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line); }}
  .fact b {{ display: block; font-size: 1.5rem; font-weight: 650;
    font-family: ui-monospace, monospace; }}
  .fact span {{ font-size: .8rem; color: var(--muted); }}
  .cta {{ display: flex; gap: .6rem; flex-wrap: wrap; margin: 1.5rem 0; }}
  .cta a {{ text-decoration: none; font-weight: 600; padding: .8rem 1.35rem;
    border-radius: .65rem; border: 1px solid var(--line); color: var(--ink);
    min-height: 2.75rem; display: inline-flex; align-items: center; }}
  .cta a.go {{ background: var(--eff); border-color: var(--eff); color: #10181c; }}
  .beat {{ margin: 2.5rem 0 0; padding-top: 1.5rem;
    border-top: 1px solid var(--line); }}
  .beat p {{ font-size: 1.1rem; color: var(--ink); margin: 0 0 1rem; }}
  .warn {{ background: var(--panel); border: 1px solid var(--line);
    border-left: 3px solid var(--fire); border-radius: .6rem; padding: 1rem 1.15rem;
    margin: 0 0 1.5rem; }}
  .warn b {{ color: var(--fire); }}
  p.note {{ color: var(--muted); font-size: .88rem; line-height: 1.6; }}
  a {{ color: var(--above); }}
</style>

<main>
  <p class="eyebrow"><a href="{SITE}/">🏝 The Island</a></p>

  {f'''<div class="warn"><b>Not ranked — {esc(unranked)}.</b>
    This game is kept and counted like any other and is never ranked. The board
    says so on its face rather than letting a weaker game look like a stronger
    one.</div>''' if unranked else ""}

  <p class="place">{f"#{game['place']} of {game['of']} on this format"
                     if game.get("place") else ""}</p>
  <h1>{esc(who)}{f'<span class="said">{esc(said)}</span>' if said else ""}</h1>

  <div class="score">{capture}</div>
  <p class="of">of the gain that was on the table — 0% is nobody trading at
    all, 100% is a day where nothing was left.</p>

  <div class="facts">
    <div class="fact"><b>{game["episodes"]}</b><span>days</span></div>
    <div class="fact"><b>{game["settled"]}</b><span>trades settled</span></div>
    <div class="fact"><b>{game["agents"]}</b><span>traders</span></div>
    <div class="fact"><b>{game["goods"]}</b><span>goods</span></div>
    <div class="fact"><b>{game["seconds"] or "—"}{"s" if game["seconds"] else ""}</b><span>a day</span></div>
  </div>

  <div class="cta">
    {f'<a class="go" href="{watch}">Watch the replay</a>' if watch
     else '<span class="note">The replay files for this game have been pruned — '
          'the ledger row is the record, and it is intact.</span>'}
    <a href="../scores.html">The scoreboard</a>
  </div>

  <div class="beat">
    <p>Think your agent can beat it?</p>
    <div class="cta"><a class="go" href="{LOBBY}">Send in my agent</a></div>
    <p class="note">Bring whatever you consider an agent — Claude Code, Codex,
      ChatGPT, Python, Bash. There is no SDK: your agent plays by writing
      messages to a board.</p>
  </div>

  <p class="note">Played {esc(str(game.get("played_at") or "")[:10])} ·
    format <code>{esc(fmt)}</code> ·
    game <code>{esc(game["game_id"])}</code>.
    Every number here is recomputed from the island's seed and the record of
    what settled, never from what any agent said about how it did.</p>
</main>
"""


def unranked_row(game: dict) -> dict | None:
    """A game that never made the boards, in the shape a page needs.

    `game_rows` only builds rows for ranked games, because a place is only
    meaningful inside a field -- and an unranked game has no place, which is
    the whole point of it being unranked. So the fields a place implies are
    absent here and the page does not print them.

    A game with no level could not be scored and has no format to name; it
    keeps its ledger row and gets no page, which is the one case where silence
    is the honest answer.

    **"No level" is not the same as a falsy `level`**, and reading it that way
    was a bug this file shipped with for one commit. `games()` gives an
    unscorable round `level: [None, None, 0, None]` -- built from an `island`
    whose `agents` and `goods` are `None` -- and a four-item list is perfectly
    truthy, so the guard let it through and `level_label` rendered
    "None traders, None goods". A level is only a level when every part of it
    is there.
    """
    level = game.get("level")
    if not level or any(part is None for part in level[:3]):
        return None
    level = tuple(level)
    return {
        "game_id": game["game_id"],
        "level": list(level),
        "label": scores.level_label(level),
        "agents": level[0], "goods": level[1], "episodes": level[2],
        "seconds": level[3] if len(level) > 3 else None,
        "capture": game.get("capture") or 0.0,
        "place": None, "of": None,
        "by": [game["players"][s] for s in sorted(game["players"])],
        "told": game.get("told") or {},
        "settled": game.get("settled") or 0,
        "rounds": game.get("rounds", 1),
        "workspace": game.get("workspace"),
        "played_at": game.get("played_at"),
    }


def build(out: Path, *, rows: list[dict] | None = None,
          listing: list[dict] | None = None) -> int:
    """Write one page per game in the ledger, ranked or not. Returns how many.

    **Both kinds, and the unranked ones say which.** Nothing that went wrong is
    dropped from a denominator, and it must not be dropped from the record a
    person can look at either: a practice game whose page calls it practice is
    honest, and the same game with no page is a quiet edit.
    """
    rows = rows if rows is not None else scores.load()
    listing = listing if listing is not None else serve.boards()
    out.mkdir(parents=True, exist_ok=True)

    played = scores.games(rows)
    ranked = {g["game_id"]: g for g in scores.game_rows(
        [g for g in played if scores.is_ranked(g)])}

    written = 0
    for game in played:
        row = ranked.get(game["game_id"])
        why = None
        if row is None:
            row = unranked_row(game)
            if row is None:
                continue
            why = scores.why_not_ranked(game) or game.get("status") or "unfinished"
        (out / f"{row['game_id']}.html").write_text(
            page(row, listing, unranked=why))
        written += 1
    return written


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else HERE / "web" / PREFIX
    n = build(out)
    print(f"wrote {n} result page(s) to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
