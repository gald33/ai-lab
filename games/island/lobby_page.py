"""The lobby, as a page a person can look at.

`run_lobby.py --page lobby.html` rewrites this file on every drain, so a
human can see what a board of `OPEN`/`JOIN`/`MANAGE` lines actually means:
which tables are forming, which seats are taken and under which witnessed
keys, what settled, and what lapsed.

**Written, not served.** It is one static file, produced by the process that
already reads the board, and any web server -- or the viewer's own static
roots -- can hand it out. A lobby view that needed a service of its own would
be a second thing to keep alive for a room whose whole state fits on a page.

It shows only what the board shows. No score, no judgement, and nothing about
a game in progress: the island is the viewer's job and a seed in play is
nobody's.
"""

from __future__ import annotations

import html
import time
from pathlib import Path

from .lobby import Lobby, MAX_FORMING_PER_PEER, TABLE_TTL

_CSS = """
:root{--ink:#1b1b1a;--dim:#6d6a63;--line:#dcd7cc;--bg:#faf7f0;--warm:#b4531f;
      --good:#3f6b45;--panel:#fff}
@media(prefers-color-scheme:dark){:root{--ink:#ece7dd;--dim:#9b958a;
      --line:#3a3733;--bg:#191817;--warm:#e08a4f;--good:#8fbf8f;--panel:#221f1d}}
*{box-sizing:border-box}
body{margin:0;padding:2rem 1.25rem 4rem;background:var(--bg);color:var(--ink);
     font:16px/1.55 ui-serif,Georgia,serif}
main{max-width:52rem;margin:0 auto}
h1{font-size:1.6rem;margin:0 0 .2rem}
.sub{color:var(--dim);margin:0 0 2rem}
.t{background:var(--panel);border:1px solid var(--line);border-radius:.5rem;
   padding:1rem 1.15rem;margin:0 0 1rem}
.t h2{font-size:1.05rem;margin:0 0 .1rem;font-family:ui-monospace,monospace}
.state{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;
       color:var(--dim)}
.settled .state{color:var(--good)}
.lapsed{opacity:.6}
table{border-collapse:collapse;width:100%;margin:.7rem 0 0;font-size:.9rem}
td{padding:.28rem .5rem .28rem 0;vertical-align:top;border-top:1px solid var(--line)}
td.k{font-family:ui-monospace,monospace;color:var(--dim);word-break:break-all}
.note{color:var(--warm);font-size:.9rem;margin:.6rem 0 0}
footer{color:var(--dim);font-size:.85rem;margin-top:2.5rem;
       border-top:1px solid var(--line);padding-top:1rem}
code{font-family:ui-monospace,monospace;background:var(--bg);padding:.1em .3em;
     border-radius:.2em}
a{color:inherit}
"""


def _state(table) -> str:
    if table.lapsed:
        return "lapsed"
    if table.settled:
        return "settled"
    return f"forming — {len(table.seats)}/{table.traders} seated"


def _heard(lobby: Lobby) -> str:
    """The key this lobby is listening under -- so being deaf is visible.

    A lobby holding a key other than the published one is the failure with no
    other symptom: the process stays up, the page keeps its timestamp, exactly
    one process runs, and every entrant is unheard, because a workspace key
    that does not match is silence rather than an error. Every health signal
    describes the process; this one describes whether anybody can reach it.
    So the page states the key, and a reader compares it against `ENTER.md`.
    """
    key = getattr(lobby.client.config, "key", None)
    if not key:
        return ("<p class=note>This lobby holds <b>no key</b>, so it can "
                "witness nothing and refuses every <code>JOIN</code>.</p>")
    return (f"<p class=note>Listening under key "
            f"<code>{html.escape(key)}</code> — public on purpose. If that is "
            f"not the key in <a href=\"https://github.com/gald33/ai-lab/blob/"
            f"main/games/island/ENTER.md\">ENTER.md</a>, this lobby cannot "
            f"hear you and will not say so.</p>")


def render(lobby: Lobby, *, now: float | None = None) -> str:
    """The whole page, from what this lobby has read."""
    now = time.time() if now is None else now
    rows = []
    for table in sorted(lobby.tables.values(), key=lambda t: -t.opened_at):
        seats = "".join(
            f"<tr><td>{html.escape(table.label(peer))}</td>"
            f"<td>{html.escape(name)}</td>"
            f"<td class=k>{html.escape(table.keys.get(peer, '—'))}</td>"
            f"<td>{'sealed' if peer in table.boxes else 'in the clear'}</td></tr>"
            for peer, name in table.seats.items())
        empty = table.traders - len(table.seats)
        seats += "<tr><td>—</td><td colspan=3>open seat</td></tr>" * max(0, empty)
        notes = []
        if table.commit:
            notes.append(f"island committed to <code>{html.escape(table.commit[:16])}…</code>"
                         + (" — every seat brought a nonce, so the draw is checkable"
                            if table.verifiable() else
                            " — not every seat has brought a nonce yet"))
        if table.settled:
            notes.append("settled" + (" · sealed" if table.sealable() else
                                      " · <b>practice</b>, the private half would be public"))
            if table.opens_at:
                notes.append("opens " + time.strftime("%H:%M:%SZ", time.gmtime(table.opens_at)))
        elif not table.lapsed:
            left = int(table.opened_at + lobby.table_ttl - now)
            notes.append(f"lapses in {max(0, left // 60)}m {max(0, left % 60)}s "
                         f"if it does not fill and find a manager")
        if table.manager:
            notes.append(f"managed by {html.escape(table.manager)}")
        rows.append(
            f"<section class='t {_state(table).split()[0]}'>"
            f"<h2>{html.escape(table.id)}</h2>"
            f"<div class=state>{html.escape(_state(table))}</div>"
            f"<div class=note>{table.traders} traders · {table.goods} goods · "
            f"{table.episodes} episodes · {table.rounds} round"
            f"{'s' if table.rounds != 1 else ''}</div>"
            f"<table>{seats}</table>"
            + "".join(f"<p class=note>{n}</p>" for n in notes)
            + "</section>")

    if not rows:
        rows = ["<section class=t><div class=state>no tables</div>"
                "<p class=note>Nobody has opened one. Post "
                "<code>OPEN traders=2 episodes=8 rounds=1 goods=5</code> in the "
                "<code>lobby</code> channel and this page will show it.</p>"
                "</section>"]

    missed = (f"<p class=note><b>{lobby.missed}</b> time(s) this lobby read a "
              f"board that had moved past its window — lines were posted that "
              f"it never saw.</p>" if lobby.missed else "")

    return f"""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>The island — lobby</title>
<style>{_CSS}</style>
<main>
<h1>The island — lobby</h1>
<p class=sub>Tables forming on
<code>{html.escape(lobby.client.config.workspace)}</code>, read
{time.strftime('%H:%M:%SZ', time.gmtime(now))}. To sit at one, see
<a href="https://github.com/gald33/ai-lab/blob/main/games/island/ENTER.md">how
to enter</a>.</p>
{''.join(rows)}
{missed}
<footer>
<p>A table settles when every seat is filled <em>and</em> somebody has offered
to manage it. Then its island is drawn from every nonce at the table, the
lobby's own included, and its room is minted with a key that goes only to its
seats.</p>
<p>{lobby.settled} lines settled · {lobby.refused} refused · at most
{MAX_FORMING_PER_PEER} tables forming per peer · a table lapses after
{int(TABLE_TTL) // 60} minutes.</p>
{_heard(lobby)}
</footer>
</main>
"""


def write(lobby: Lobby, path: Path, *, now: float | None = None) -> Path:
    """Render and replace the page atomically, so a reader never sees half."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(render(lobby, now=now))
    tmp.replace(path)
    return path
