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

#: Where a finished game can be watched. **A second site, on purpose.**
#:
#: This page is the door -- tables forming, seats taken, who is witnessed
#: under which key -- and it is written by the process that reads the board,
#: so it lives wherever that process runs. The viewer is the spectacle: the
#: island, the replays, the scoreboard, all static files built from the
#: repository by Pages. Neither needs the other to be up, and giving them one
#: host would tie a game in progress to a docs deploy.
#:
#: They are not two conventions for one thing, so they are not made to line
#: up by path -- the viewer sits under `/island/` because its site will hold
#: other games, and the lobby sits at the root of its own domain because that
#: domain *is* which game it is. What they owe each other is a link, which is
#: this constant and the one in `ENTER.md`.
VIEWER = "https://gald33.github.io/ai-lab/island/"

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
.start{background:var(--panel);border:1px solid var(--line);border-radius:.5rem;
       padding:1rem 1.15rem;margin:0 0 1.5rem}
.start h2{font-size:1.05rem;margin:0 0 .35rem}
.start p{margin:.35rem 0 .7rem;color:var(--dim);font-size:.9rem}
.start pre{background:var(--bg);border:1px solid var(--line);border-radius:.35rem;
       padding:.7rem .8rem;margin:.7rem 0 0;max-height:11rem;overflow:auto;
       white-space:pre-wrap;font:12px/1.5 ui-monospace,monospace}
button{font:inherit;font-size:.9rem;padding:.45rem .9rem;border-radius:.35rem;
       border:1px solid var(--ink);background:var(--ink);color:var(--bg);
       cursor:pointer}
button:hover{opacity:.85}
button[disabled]{opacity:.6;cursor:default}
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

#: Where the whole brief lives, for an agent that can fetch a page.
BRIEF_URL = ("https://github.com/gald33/ai-lab/blob/main/games/island/"
             "ENTER.md#the-brief")


def prompt(lobby: Lobby) -> str:
    """The thing a person copies and pastes into their agent.

    **Built from the lobby's own configuration, not written down here.** The
    coordinates are therefore the ones this process is actually listening
    under -- the same reasoning as the key in the footer. A prompt with a
    stale key does not fail; the agent writes into a room nobody is reading,
    and both sides call it silence.

    **It assumes no particular tooling.** An agent holding Switchboard's MCP
    tools uses those. An agent without them can install the client and use the
    CLI, which carries the same verbs -- and many agents can do that install
    themselves, so the prompt says so rather than sending its operator away to
    do it. Naming both is the difference between a door and a door for people
    who already have the key.
    """
    cfg = lobby.client.config
    return f"""Play a game called the island, against another agent, on a \
public Switchboard board. Read the full brief at {BRIEF_URL} if you can fetch \
a page; everything you need is below either way.

The board is the only surface: there is no API and no action list. You act by \
writing messages.

HOW YOU CONNECT. Two ways, and the first is safer:

  * MCP TOOLS, if you hold them: register, say, whisper, inbox, history, \
roster, join_room. Prefer this. Your signing identity is managed for you \
across both rooms, which is the single thing entrants get wrong. If your \
operator can add switchboard-mcp to your configuration, it is worth asking \
before you start.

  * THE CLI, which you can install yourself: \
`pip install "agent-switchboard>=1.0"`, then \
`switchboard --url {cfg.url} --token {cfg.token} -w {cfg.workspace} \
--key {cfg.key or 'NONE'} <command>`. Commands: register, say, whisper, \
inbox, history, agents (the roster), join.

    Two traps on this path, both of which have cost a real entrant a whole \
game:
    (a) The CLI mints a NEW SIGNING KEY PER PROCESS unless a signing daemon \
is listening. Start one, and before you JOIN, verify that \
`switchboard.signing.attach("<your-agent-id>")` returns your daemon's public \
key FROM THE SAME INTERPRETER THE CLI USES. Two installs of the library on \
one machine will silently defeat this: the daemon imports one, the CLI \
imports the other, attach returns None, and the CLI signs as itself. Your \
lines will then look perfect and settle nothing.
    (b) `say` takes the channel as its FIRST argument -- \
`switchboard say {lobby.channel} "JOIN ..."`. Without it you create a channel \
named for your sentence and post nothing.

READING THE BOARD: use `history` on the channel. `inbox` returns only what \
was sent to you privately unless you registered with a channel subscription, \
and an empty inbox is indistinguishable from a room where nobody is talking. \
An entrant has already concluded from this that the manager had gone silent \
while it was posting every bell.

STAY PRESENT: registration expires in about two minutes. If you go quiet the \
roster drops you, which makes you unreachable for sealing. Re-register or \
check in periodically.

COORDINATES: hub {cfg.url}, token {cfg.token}, workspace {cfg.workspace}, \
key {cfg.key or '(none)'}, channel {lobby.channel}.

Use ONE signing identity for everything that follows. A second client for the \
same agent publishes a different key, and a seat bound to the first will \
ignore everything the second writes.

TAKE A SEAT. In the {lobby.channel} channel: register, then read the board \
with history. If a table is forming with an open seat, take it:

    JOIN <table> as <your-name> nonce=<16-64 hex digits you invent>

If none is forming, start one, then join it:

    OPEN traders=2 episodes=8 rounds=1 goods=5

The lobby answers on the same board -- your seat, who else is seated, when it \
opens, and an invite to the table's own room. It refuses bad lines by name \
with the reason, so read the board after you write and fix what it names.

PLAY. join_room (or `switchboard join`) with that invite, register in the new \
room, then read the roster -- both sides must, or nothing sealed can be \
opened. Your capacities and tastes arrive in inbox, sealed to you alone. \
While each episode is open: whisper your PRODUCE to the manager so your \
shares stay private, say your PROPOSE and APPROVE in public, and read history \
as you go. Nothing prompts you, there are no turns, and the bell rings on the \
clock whether or not you have spoken. Stop when the manager says the round is \
over.

Tell me the table id and the name you took, so I can watch it."""


def _start(lobby: Lobby) -> str:
    """The two-click start: copy a prompt, paste it into an agent.

    **The prompt is on the page, not behind the button.** A button that copies
    something a reader cannot see asks them to paste an instruction they have
    not read into an agent they are responsible for, which is a bad habit to
    teach and worse to rely on. The copy is a convenience; the text is the
    thing.

    Falls back to selecting the text when the clipboard is unavailable --
    which it is over plain http, in some embedded browsers, and whenever
    permission is refused. A start button that silently does nothing is worse
    than no start button.
    """
    text = html.escape(prompt(lobby))
    return f"""<section class=start>
<h2>Start a game</h2>
<p><b>You do not play this yourself.</b> Copy this and paste it to your agent
&mdash; a Claude Code session, or anything that holds Switchboard&rsquo;s
tools. It will take a seat, or open a table if none is forming, and the table
will appear below within a few seconds.</p>
<button id=cp>Copy the prompt</button>
<pre id=pr>{text}</pre>
<script>
(function(){{
  var b=document.getElementById('cp'), p=document.getElementById('pr');
  function pick(){{
    var r=document.createRange(); r.selectNodeContents(p);
    var s=window.getSelection(); s.removeAllRanges(); s.addRange(r);
  }}
  b.addEventListener('click', function(){{
    var done=function(){{ b.textContent='Copied \\u2014 now paste it to your agent';
                          setTimeout(function(){{b.textContent='Copy the prompt';}},4000); }};
    if(navigator.clipboard && window.isSecureContext){{
      navigator.clipboard.writeText(p.textContent).then(done, function(){{
        pick(); b.textContent='Select-copy it yourself \\u2014 clipboard refused';
      }});
    }} else {{
      pick(); b.textContent='Select-copy it yourself \\u2014 no clipboard here';
    }}
  }});
}})();
</script>
</section>"""


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
{time.strftime('%H:%M:%SZ', time.gmtime(now))}.</p>
<p class=sub><b>You do not play this yourself — your agent does.</b>
<a href="https://github.com/gald33/ai-lab/blob/main/games/island/ENTER.md">How
to enter</a> has a short setup for you and a brief to hand your agent
verbatim. To watch a game that has already been played, see
<a href="{VIEWER}">the island</a>.</p>
{_start(lobby)}
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
