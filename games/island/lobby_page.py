"""The lobby, as a page a person can look at.

`run_lobby.py --page lobby.html` rewrites this file on every drain, so a
human can see what a board of `OPEN`/`JOIN`/`MANAGE` lines actually means:
which tables are forming, which seats are taken and under which witnessed
keys, what settled, and what lapsed.

**Written, not served.** It is one static file, produced by the process that
already reads the board, and any web server -- or the viewer's own static
roots -- can hand it out. A lobby view that needed a service of its own would
be a second thing to keep alive for a room whose whole state fits on a page.

*Superseded 2026-08-29, and the reasoning above is kept because only half of
it was wrong.* Gal decided the lobby is served by Vercel as static assets that
are **themselves a Switchboard client**, reading the board in the reader's
browser. That is not "a service of its own" -- there is nothing to keep alive,
which is what the paragraph above was actually objecting to -- and it means no
one calls the VM to see the lobby. What makes it allowed is the line below
that has always been true: this page shows only what the board shows, so it is
for humans and is not part of the game, and nothing on it is evidence of
anything. The viewer is the opposite and stays on Pages, where the code a
stranger checks a game with is the code they can read. See `HOSTING.md`, "The
lobby is served by Vercel, and reads the board itself" -- including the
measured obstacle, that the hub allowlists CORS origins and Vercel is not yet
one.

This module stays regardless: a page written to disk is the fallback if that
grant or that host goes away.

It shows only what the board shows. No score, no judgement, and nothing about
a game in progress: the island is the viewer's job and a seed in play is
nobody's.
"""

from __future__ import annotations

import html
import json
import os
import time
from urllib.parse import quote
from pathlib import Path

from .lobby import (Lobby, MAX_FORMING_PER_PEER, MAX_JOINABLE,
                    MAX_TABLES, TABLE_TTL)
from .protocol import EPISODE_SECONDS_ALLOWED, EPISODE_SECONDS_DEFAULT

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

#: How often the page tells a browser to come back, in seconds. **The page is
#: a file, so a reader's copy is only ever as fresh as the last drain that
#: wrote it** -- and a lobby page that has stopped being rewritten looks
#: exactly like one where nothing is happening. Both halves of that are fixed
#: here: the browser reloads on this interval, and the page says out loud how
#: old the copy in front of the reader is (`_age`), so a stale one is visible
#: rather than merely wrong.
PAGE_REFRESH = 15

#: How many refresh intervals may pass before the page calls itself stale. Two
#: missed reloads is a host that has stopped, not a slow one.
STALE_AFTER = PAGE_REFRESH * 3


def live_base() -> str:
    """Where this host serves `--live` from, if it serves it at all.

    **Read at render time, not at import.** As a module constant this was set
    once, by whatever the environment happened to hold when the first import
    ran -- so a host that exported it after the process started, or a test that
    sets it at all, got a page with no watch button and no error to explain
    why. That is the same shape as the missing `--live` in `HOSTING.md`: a
    feature documented by its output and shipped turned off.

    No key travels in the link it builds: the file is a board somebody already
    in the room wrote down, so a spectator reads without holding anything they
    could write with. Unset means no button, which is the honest state for a
    host that is not serving one.
    """
    return os.environ.get("ISLAND_LIVE_BASE", "").rstrip("/")


def live_state(table, live_dir=None) -> str:
    """Is this table playing now, finished, or neither -- `live`, `recording`, `""`.

    **The live file is what knows, and the board is not.** A table settles and
    the board says nothing more about it: the last bell is a thing the manager
    writes into `--live/<table>.json`, as the `finished` block that names the
    copies of the board and the reveal beside it (`live.finish`). So a page
    that reads only the lobby cannot tell a game being played from one that
    ended an hour ago -- and it called both of them *live*, which is a claim
    about right now made from a fact that was true once.

    The process that writes this page is the process that writes those files,
    so the answer is a file read rather than a guess. Reading the block rather
    than testing for the copies beside it is deliberate: `finish` writes the
    copies **before** the pointer, so a poll landing between the two sees a
    game still running, which is the direction that stays honest.

    With no `live_dir` -- `run_lobby --page`, or `run_game` without `--live` --
    there is nothing to read and nothing is claimed: `unknown`. A host serving
    no live directory has nothing to point at either.
    """
    if not live_base() or not table.settled or table.lapsed:
        return ""
    if live_dir is None:
        return "unknown"
    path = Path(live_dir) / f"{table.id}.json"
    try:
        state = json.loads(path.read_text())
    except (OSError, ValueError):
        # No file yet, or a game whose host never wrote one. Either way there
        # is nothing served at the URL a button would point at, so there is no
        # button -- a door onto a 404 is worse than no door.
        return ""
    return "recording" if state.get("finished") else "live"


def watchable(table, live_dir=None) -> bool:
    """Is there a board a spectator could be pointed at, running or finished?"""
    return bool(live_state(table, live_dir))


#: What each state's button says and looks like. **The label is the claim**:
#: "live" says a game is being played right now, and saying it over a game that
#: ended is the page telling a spectator something it has not checked.
_WATCH = {
    "live": ("&#9654;&nbsp; Watch this game live",
             "watching a game in progress &mdash; the board updates as it is written"),
    "recording": ("&#9654;&nbsp; Watch the recording",
                  "this game has finished &mdash; its scores and replay are on the page"),
    "unknown": ("&#9654;&nbsp; Watch this game",
                "this host does not say whether the game is still running"),
}


def watch_link(table, live_dir=None) -> str:
    """The viewer, pointed at this table's board. Empty if none is served.

    **A button, and the loudest thing on the table.** It was a `&middot;`-
    separated link at the tail of the "managed by" line, which is the one place
    on the page a reader scanning for *something to look at* does not read --
    and a game in progress that nobody finds the door to is the whole failure
    the viewer exists to prevent. A table that can be watched now says so at
    the top of its own section.

    A running game gets the fire colour and the word *live*; a finished one
    gets the quieter surface and the word *recording*. One URL serves both --
    the live file is the archive (`HOSTING.md`) -- so the difference is what
    the page is willing to claim about it, not where it points.
    """
    state = live_state(table, live_dir)
    if not state:
        return ""
    label, note = _WATCH[state]
    src = f"{live_base()}/{table.id}.json"
    return (f'<p class=watch><a class="watchbtn {state}" '
            f'href="{html.escape(VIEWER)}?live='
            f'{html.escape(quote(src, safe=""))}">{label}</a> '
            f'<span class=watchnote>{note}</span></p>')


#: The lobby, wearing the island's own palette.
#:
#: **A copy of `viewer/web/tokens.css`, on purpose.** The viewer is committed
#: to one look -- "an island at dusk", and its tokens file says a light mode
#: would be a different picture rather than the same one lit differently -- and
#: the lobby is the door into that. It was a warm cream serif page with a
#: dark-mode media query, which is a second look for one game: a spectator who
#: came from the island arrived somewhere that did not resemble it, and the
#: page's own dark mode meant it did not even resemble itself.
#:
#: It is duplicated rather than linked because these are **two hosts** (see
#: `VIEWER`): the lobby is one static file written by this process wherever it
#: runs, and a stylesheet fetched from the Pages site would make the door
#: depend on a docs deploy being up -- the coupling the two-sites decision
#: exists to refuse. So the values are copied, and copied *whole*: only the
#: scenery tokens, which encode nothing and are held to no contrast gate.
#: **Nothing categorical is copied** -- no good, trader or metric colour lives
#: here, because nothing on this page encodes one, and a categorical token
#: loose on a page with no legend is how a reader starts looking for meaning
#: in the furniture.
_CSS = """
:root{color-scheme:dark;
  --sea-near:#1d3242;--sea-mid:#132532;--sea-far:#070d12;
  --panel:#171d21;--panel-2:#1e262b;--line:#2b353b;
  --ink:#f2f4f4;--ink-2:#b6c0c4;--muted:#8b9599;
  --fire:#ffb648;--sand:#c9a86a;--sand-lit:#ddbe83;--surf:#cfe6ef;
  --frond:#55803f;--sky-set:#d9603a}
*{box-sizing:border-box}
body{margin:0;padding:2rem 1.25rem 4rem;color:var(--ink);
     background:var(--sea-far);
     background-image:linear-gradient(180deg,var(--sea-mid) 0,var(--sea-far) 34rem);
     background-repeat:no-repeat;
     font:16px/1.55 ui-serif,Georgia,serif}
main{max-width:52rem;margin:0 auto}
h1{font-size:1.6rem;margin:0 0 .2rem;color:var(--sand-lit);
   letter-spacing:.01em}
.sub{color:var(--ink-2);margin:0 0 2rem}
.t{background:var(--panel);border:1px solid var(--line);border-radius:.5rem;
   padding:1rem 1.15rem;margin:0 0 1rem}
.t h2{font-size:1.05rem;margin:0 0 .1rem;font-family:ui-monospace,monospace;
      color:var(--surf)}
.state{display:inline-block;font-size:.72rem;text-transform:uppercase;
       letter-spacing:.07em;color:var(--muted);border:1px solid var(--line);
       border-radius:1em;padding:.1rem .6rem;margin:.15rem 0 0}
.settled .state{color:var(--frond);border-color:var(--frond)}
.forming .state{color:var(--sand);border-color:var(--sand)}
.lapsed{opacity:.55}
.t.live{border-color:var(--fire);box-shadow:0 0 0 1px var(--fire) inset,
        0 0 1.6rem -.6rem var(--fire)}
.watch{margin:.8rem 0 .2rem}
a.watchbtn{display:inline-block;text-decoration:none;font-size:.95rem;
       font-weight:700;padding:.5rem 1.1rem;border-radius:.35rem;
       border:1px solid var(--line);background:var(--panel-2);color:var(--ink)}
a.watchbtn.live{background:var(--fire);border-color:var(--fire);
       color:var(--sea-far)}
a.watchbtn.recording{border-color:var(--surf);color:var(--surf)}
a.watchbtn:hover{filter:brightness(1.12)}
.watchnote{color:var(--muted);font-size:.8rem;margin-left:.5rem}
.age{color:var(--muted);font-size:.85rem}
.cd{font-variant-numeric:tabular-nums}
.cd.soon{color:var(--sky-set);font-weight:700}
.cd.now{color:var(--ink);font-weight:700}
.age.stale{color:var(--sky-set);font-weight:700}
table{border-collapse:collapse;width:100%;margin:.7rem 0 0;font-size:.9rem}
td{padding:.28rem .5rem .28rem 0;vertical-align:top;border-top:1px solid var(--line)}
td.k{font-family:ui-monospace,monospace;color:var(--muted);word-break:break-all}
.note{color:var(--ink-2);font-size:.9rem;margin:.6rem 0 0}
.note b{color:var(--sand-lit)}
footer{color:var(--muted);font-size:.85rem;margin-top:2.5rem;
       border-top:1px solid var(--line);padding-top:1rem}
code{font-family:ui-monospace,monospace;background:var(--sea-far);
     color:var(--sand-lit);padding:.1em .3em;border-radius:.2em}
a{color:var(--surf)}
.start{background:var(--panel);border:1px solid var(--line);border-radius:.5rem;
       padding:1rem 1.15rem;margin:0 0 1.5rem}
.start h2{font-size:1.05rem;margin:0 0 .35rem;color:var(--sand-lit)}
.start p{margin:.35rem 0 .7rem;color:var(--ink-2);font-size:.9rem}
.start pre{background:var(--sea-far);border:1px solid var(--line);
       border-radius:.35rem;color:var(--ink-2);
       padding:.7rem .8rem;margin:.7rem 0 0;max-height:11rem;overflow:auto;
       white-space:pre-wrap;font:12px/1.5 ui-monospace,monospace}
button{font:inherit;font-size:.9rem;padding:.45rem .9rem;border-radius:.35rem;
       border:1px solid var(--sand);background:var(--sand);
       color:var(--sea-far);cursor:pointer;font-weight:700}
button:hover{filter:brightness(1.12)}
button[disabled]{opacity:.6;cursor:default}
.levers{display:flex;flex-wrap:wrap;gap:.5rem .9rem;align-items:flex-end;
       margin:.8rem 0 0;padding:.75rem .85rem;background:var(--sea-far);
       border:1px solid var(--line);border-radius:.35rem}
.levers .lh{flex:1 0 100%;margin:0 0 .2rem;font-size:.82rem;color:var(--ink-2)}
.levers label{display:flex;flex-direction:column;gap:.2rem;font-size:.72rem;
       letter-spacing:.03em;text-transform:uppercase;color:var(--ink-2)}
.levers select{font:inherit;font-size:.85rem;padding:.3rem .4rem;
       border-radius:.3rem;border:1px solid var(--line);
       background:var(--panel);color:var(--ink)}
.levers select:focus-visible{outline:2px solid var(--sand);outline-offset:1px}
#ol{color:var(--sand-lit);font-weight:700}
"""


def _state(table) -> str:
    if table.lapsed:
        return "lapsed"
    if table.settled:
        return "settled"
    return f"forming — {len(table.seats)}/{table.traders} seated"


def _waiting_for(table) -> str:
    """What a forming table is still short of, named rather than inferred.

    "forming — 1/2 seated" says how far along it is and not what would move
    it, and the two things it can be waiting for are different jobs for
    different people: an empty seat wants another entrant, a missing manager
    wants somebody to post one line. A reader who cannot tell which is being
    asked of them does neither.
    """
    wants = []
    empty = table.traders - len(table.seats)
    if empty > 0:
        wants.append(f"{empty} more entrant{'s' if empty != 1 else ''} to sit down")
    if not table.manager:
        wants.append("somebody to offer to manage it")
    if not wants:
        return ""
    return "Waiting for " + " and ".join(wants) + "."


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

def _age(now: float) -> str:
    """When this copy was written, and how old it has since become.

    **A static page is stale the moment after it is written, and says so.**
    The timestamp alone did not help: it is in UTC, the reader is not, and a
    page frozen an hour ago carries a perfectly plausible-looking time. So the
    page also counts up from its own write in the reader's browser and turns
    the counter warm past `STALE_AFTER` — three refresh intervals, so two
    missed reloads. By then the host has stopped rewriting the file, and a
    lobby that has stopped being rewritten is indistinguishable from a lobby
    where nothing is happening.

    It counts from the *server's* clock, so a badly skewed browser clock can
    read the page as stale when it is not. That is the direction to be wrong
    in: the other one hides a dead host.

    With no script at all, the timestamp and the meta-refresh still stand.
    """
    return (f"<span class=age id=age data-at='{int(now)}'>"
            f"read {time.strftime('%H:%M:%SZ', time.gmtime(now))}, "
            f"refreshing every {PAGE_REFRESH}s</span>"
            f"<script>(function(){{"
            f"var e=document.getElementById('age'),t=+e.dataset.at;"
            f"function tick(){{"
            f"var a=Math.max(0,Math.round(Date.now()/1000-t));"
            f"var s=a<{STALE_AFTER};"
            f"e.className='age'+(s?'':' stale');"
            f"e.textContent=s?'read '+a+'s ago, refreshing every {PAGE_REFRESH}s'"
            f":'STALE — this page has not been rewritten for '+a+'s. "
            f"The lobby behind it may have stopped.';}}"
            f"tick();setInterval(tick,1000);}})();</script>")


#: Inside this many seconds a countdown is worth looking at rather than
#: reading past: about the time it takes to start an agent and have it reach
#: the room. Purely presentational -- nothing in the game turns on it.
SOON = 120


def _countdown(left: float, *, key: str, prefix: str, at: str = "",
               after: str = "") -> str:
    """A number of seconds, ticking down in the reader's browser.

    **It counts down from the server's number, not towards the server's
    clock**, and that is the whole of the design. The obvious version puts the
    absolute instant in the page and has the browser subtract `Date.now()`;
    that reads a browser whose clock is a few minutes fast as "opened 3m ago"
    for a table that has not opened, and one running slow as "opens in 3m" for
    a table already playing. A lobby that tells a reader the game has started
    when it has not is worse than a lobby that says nothing.

    So the page carries how long was left *when it was written*, and the
    script subtracts only time it has measured itself since the script ran.
    That depends on no absolute clock at all, and the error it can accumulate
    is bounded by `PAGE_REFRESH`, because the next rewrite replaces the
    number. `_age` reasons the other way round on purpose -- it is measuring
    the page's own staleness, where trusting the reader's clock is what makes
    a dead host visible.

    `at` is the absolute UTC time, kept beside it so a reader with no script
    still has the one thing they need, and so two people comparing pages have
    a fixed point to compare. `after` is what to say once it reaches zero.

    `key` names the countdown across reloads, so the meta-refresh does not
    make it jump -- see `_TICKER`.
    """
    left = max(0.0, left)
    shown = f"{prefix} {_span(left)}" + (f" ({at})" if at else "")
    return (f"<span class=cd data-key='{html.escape(key)}' data-left='{left:.0f}' "
            f"data-prefix='{html.escape(prefix)}' "
            f"data-at='{html.escape(at)}' data-after='{html.escape(after)}'>"
            f"{html.escape(shown)}</span>")


def _span(seconds: float) -> str:
    """Seconds as a person reads them. Minutes only once there are minutes:
    "in 90s" is a clearer thing to wait out than "in 1m 30s"."""
    seconds = int(max(0.0, seconds))
    if seconds < 60:
        return f"in {seconds}s"
    return f"in {seconds // 60}m {seconds % 60:02d}s"


#: How far the number the server wrote may sit from the one this browser has
#: been counting before the browser gives up its own count and takes the
#: server's. A page is written at most `PAGE_REFRESH` before it is read, so
#: anything inside a couple of intervals is that staleness and nothing else;
#: past it, the schedule itself moved and the reader should be told.
RESYNC = PAGE_REFRESH * 2

#: One script for every countdown on the page. It runs once, measures its own
#: elapsed time, and never reads a wall clock -- see `_countdown`.
#:
#: **It also carries each countdown across the meta-refresh.** Within one load
#: the number ticked; every `PAGE_REFRESH` the page was replaced by one written
#: up to an interval earlier, and the countdown jumped back to it -- so what a
#: reader watched was a second hand that lurched backwards every fifteenth
#: second. The deadline was never wrong; the counting between reloads was.
#:
#: So the first load of each countdown records, in `sessionStorage`, what was
#: left and the `Date.now()` it read that at, and later loads count from that
#: record instead of from the freshly-written number. Both readings come from
#: one browser's clock, so a skewed clock cancels: this is still measuring
#: elapsed time and still never comparing a browser to a server. When the two
#: disagree by more than `RESYNC` the record is thrown away and the server's
#: number wins, because that is no longer page staleness -- the schedule moved.
#: With `sessionStorage` unavailable every branch falls back to the server's
#: number, which is what the page did before.
#:
#: **It goes last in the page, after the tables, and that is load-bearing.**
#: It ran once at parse time and took its elements with one
#: `querySelectorAll('.cd')` -- so while it sat above the table rows it
#: matched nothing, `els` was empty, and every countdown on the page simply
#: showed the number the server wrote and never moved. Both fixes above were
#: in it and working; nobody was calling them.
#:
#: *The lesson is about the tests, not the script.* Every test here asserted
#: on the rendered markup -- that the span carried `data-key`, that the script
#: said `sessionStorage`, that the resync bound was in it -- and all of them
#: passed against a page whose countdowns were frozen, because each fragment
#: was present and only their **order** was wrong. A test that reads markup
#: cannot see a script that runs too early. So the test beneath this one loads
#: the page in a real browser and watches the number change, which is the only
#: thing that was ever being claimed.
_TICKER = f"""<script>(function(){{
var t0=Date.now(),els=[].slice.call(document.querySelectorAll('.cd'));
function store(k,v){{try{{sessionStorage.setItem(k,v);}}catch(_){{}}}}
els.forEach(function(e){{
  var k='cd:'+(e.dataset.key||e.dataset.prefix),srv=+e.dataset.left,base=srv,saw=null;
  try{{saw=JSON.parse(sessionStorage.getItem(k));}}catch(_){{}}
  if(saw&&isFinite(saw.left)&&isFinite(saw.t)){{
    var carried=saw.left-(t0-saw.t)/1000;
    if(Math.abs(carried-srv)<={RESYNC}) base=carried;
    else store(k,JSON.stringify({{left:srv,t:t0}}));
  }} else store(k,JSON.stringify({{left:srv,t:t0}}));
  e.dataset.base=base;}});
function span(s){{s=Math.max(0,Math.round(s));
  return s<60?'in '+s+'s':'in '+Math.floor(s/60)+'m '+('0'+(s%60)).slice(-2)+'s';}}
function tick(){{
  var gone=(Date.now()-t0)/1000;
  els.forEach(function(e){{
    var left=+e.dataset.base-gone;
    if(left<=0){{e.className='cd now';e.textContent=e.dataset.after;return;}}
    e.className='cd'+(left<={SOON}?' soon':'');
    e.textContent=e.dataset.prefix+' '+span(left)
      +(e.dataset.at?' ('+e.dataset.at+')':'');}});}}
tick();setInterval(tick,1000);}})();</script>"""


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
    open_suggestion = open_line()
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
`pip install "agent-switchboard>=1.2.3"`, then \
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

STAY PRESENT, and ask for it once rather than nursing it: registration \
defaults to about two minutes, but `register`/`announce` takes a TTL and \
honours it up to 3600s -- so ask for one that covers your whole game and stop \
worrying about it. Above 3600 it is CLAMPED SILENTLY, with the same success \
line, so do not believe a larger number. Pass a `back_in` too: past your TTL \
the roster keeps your row as `away` for that long, still carrying your key, \
so a peer can still seal to you. Note that announcing REPLACES your presence \
rather than extending it -- a short TTL announced later overwrites a long one \
announced earlier. If you go quiet with no TTL left you drop off the roster, \
which makes you unreachable for sealing.

COORDINATES: hub {cfg.url}, token {cfg.token}, workspace {cfg.workspace}, \
key {cfg.key or '(none)'}, channel {lobby.channel}.

Use ONE signing identity for everything that follows. A second client for the \
same agent publishes a different key, and a seat bound to the first will \
ignore everything the second writes.

TAKE A SEAT. In the {lobby.channel} channel: register, then read the board \
with history. If a table is forming with an open seat, take it:

    JOIN <table> as <your-name> nonce=<16-64 hex digits you invent>

If none is forming, start one, then join it:

    {open_suggestion}

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


#: What the levers start on, and what the prompt suggests when nobody touches
#: them. `seconds` is spelled out rather than left to the default so that the
#: knob is discoverable: an entrant that reads the line learns the field exists,
#: which is how `kelp` came to try `seconds=120` before it was a field at all.
OPEN_DEFAULTS = {"traders": 2, "episodes": 8, "rounds": 1, "goods": 5,
                 "seconds": EPISODE_SECONDS_DEFAULT}

#: The knobs, in the order they read on the page. Each is (field, label, values)
#: -- every one a fixed list, because every distinct value is another level for
#: the scoreboard to fill, and a free-form box would produce a hundred formats
#: played once each.
LEVERS = (
    ("traders", "traders", (2, 3, 4)),
    ("episodes", "episodes per round", (1, 2, 3, 4, 5, 6, 8, 10, 12)),
    ("rounds", "rounds", (1, 2, 3, 5)),
    ("goods", "goods", (2, 3, 4, 5, 6, 7, 8)),
    ("seconds", "seconds per episode", EPISODE_SECONDS_ALLOWED),
)

#: Where a reader's lever choices wait out the reload.
#:
#: **The page reloads every `PAGE_REFRESH`, and a reload puts every `<select>`
#: back on its `selected` default.** So a reader who set traders=4 watched the
#: knobs snap back to 2 a few seconds later, and the OPEN line above them with
#: it -- and the worse half is silent: the reader has already read the line
#: they wanted, so what they copy afterwards is the default one, and the table
#: their agent opens is not the table they asked for.
#:
#: Same fix and same store as the countdowns, which had the same problem in a
#: different shape: carry it in `sessionStorage`, per tab. A restored value is
#: checked against the options actually on the page before it is applied,
#: because the ladders here move (`EPISODE_SECONDS_ALLOWED` has) and a
#: yesterday's value the lobby now refuses is exactly the trap the levers exist
#: to avoid -- a page that shows a value and a lobby that will not take it.
LEVERS_KEY = "island:levers"


def open_line(**over) -> str:
    """The OPEN an entrant should send, as one string in one place."""
    v = {**OPEN_DEFAULTS, **over}
    return ("OPEN " + " ".join(f"{k}={v[k]}"
            for k in ("traders", "episodes", "rounds", "goods", "seconds")))


def _levers() -> str:
    """The knobs, which rewrite the OPEN line in the prompt above them.

    **Advisory, and the board is still the only surface.** Nothing here talks
    to the lobby: it edits the text a human is about to hand their agent, and
    the agent still writes the OPEN itself. That is the whole point -- the
    page cannot open a table, and adding a way for it to would be a second
    surface, which this repo refuses.

    Fixed lists rather than free-form boxes because every distinct value is
    another level on the scoreboard, and a level played once tells nobody
    anything.
    """
    rows = []
    for field, label, values in LEVERS:
        opts = "".join(
            f"<option value={v}{' selected' if v == OPEN_DEFAULTS[field] else ''}>{v}</option>"
            for v in values)
        rows.append(
            f"<label>{html.escape(label)}"
            f"<select data-f={field}>{opts}</select></label>")
    return ("<div class=levers><p class=lh>Adjust what your agent will ask "
            "for &mdash; the line above updates as you choose. Your agent "
            "still sends it.</p>" + "".join(rows) + "</div>")


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
    # The OPEN line is wrapped so the levers can rewrite just that span. The
    # copy button reads `textContent` off the whole block, so whatever the
    # levers last wrote is what gets copied -- there is no second copy of the
    # prompt to keep in step.
    text = html.escape(prompt(lobby))
    line = html.escape(open_line())
    if line in text:
        text = text.replace(line, f"<span id=ol>{line}</span>", 1)
    return f"""<section class=start>
<h2>Start a game</h2>
<p><b>You do not play this yourself.</b> Copy this and paste it to your agent
&mdash; a Claude Code session, or anything that holds Switchboard&rsquo;s
tools. It will take a seat, or open a table if none is forming, and the table
will appear below within a few seconds.</p>
<button id=cp>Copy the prompt</button>
<pre id=pr>{text}</pre>
{_levers()}
<script>
(function(){{
  var b=document.getElementById('cp'), p=document.getElementById('pr');
  var ol=document.getElementById('ol');
  var sel=[].slice.call(document.querySelectorAll('.levers select'));
  function redraw(){{
    if(!ol) return;
    ol.textContent='OPEN '+sel.map(function(s){{
      return s.getAttribute('data-f')+'='+s.value; }}).join(' ');
  }}
  function save(){{
    try{{ var o={{}};
      sel.forEach(function(s){{ o[s.getAttribute('data-f')]=s.value; }});
      sessionStorage.setItem({LEVERS_KEY!r}, JSON.stringify(o));
    }}catch(e){{}}
  }}
  function restore(){{
    try{{ var o=JSON.parse(sessionStorage.getItem({LEVERS_KEY!r})||'{{}}');
      sel.forEach(function(s){{
        var v=o[s.getAttribute('data-f')];
        var ok=[].some.call(s.options,function(c){{ return c.value===v; }});
        if(ok) s.value=v;
      }});
    }}catch(e){{}}
  }}
  sel.forEach(function(s){{
    s.addEventListener('change', function(){{ save(); redraw(); }}); }});
  restore();
  redraw();
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


def render(lobby: Lobby, *, now: float | None = None,
           live_dir: Path | None = None) -> str:
    """The whole page, from what this lobby has read.

    `live_dir` is the `--live` directory this host writes, if it writes one:
    the lobby says a table settled, and only that directory says whether the
    game is still being played. See `live_state`.
    """
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
                # The one time on this page a reader is actually waiting for.
                # It was a bare `opens 19:40:00Z` -- correct, in a timezone the
                # reader is not in, on a page that had already been sitting in
                # their browser for some fraction of a refresh interval.
                notes.append(_countdown(
                    table.opens_at - now, key=f"{table.id}:opens", prefix="opens",
                    at=time.strftime("%H:%M:%SZ", time.gmtime(table.opens_at)),
                    after="the game has started"))
        elif not table.lapsed:
            left = table.opened_at + lobby.table_ttl - now
            waiting = _waiting_for(table)
            if waiting:
                notes.append(f"<b>{waiting}</b>")
            notes.append(_countdown(
                left, key=f"{table.id}:lapses", prefix="lapses",
                after="lapsed, unless somebody took the last seat just now")
                + " if it does not fill and find a manager")
        if table.manager:
            notes.append(f"managed by {html.escape(table.manager)}")
        watching = live_state(table, live_dir)
        classes = "t " + _state(table).split()[0] + (" live" if watching == "live" else "")
        rows.append(
            f"<section class='{classes}'>"
            f"<h2>{html.escape(table.id)}</h2>"
            f"<div class=state>{html.escape(_state(table))}</div>"
            + watch_link(table, live_dir)
            + f"<div class=note>{table.traders} traders · {table.goods} goods · "
            f"{table.episodes} episodes · {table.rounds} round"
            f"{'s' if table.rounds != 1 else ''}</div>"
            f"<table>{seats}</table>"
            + "".join(f"<p class=note>{n}</p>" for n in notes)
            + "</section>")

    if not rows:
        rows = ["<section class=t><div class=state>no tables</div>"
                "<p class=note><b>Nobody has opened one.</b> The prompt above "
                "opens one for you &mdash; or, by hand, post "
                f"<code>{html.escape(open_line())}</code> in the "
                "<code>lobby</code> channel and this page will show it within "
                "seconds.</p>"
                "</section>"]

    missed = (f"<p class=note><b>{lobby.missed}</b> time(s) this lobby read a "
              f"board that had moved past its window — lines were posted that "
              f"it never saw.</p>" if lobby.missed else "")

    states = [live_state(t, live_dir) for t in lobby.tables.values()]
    live_now = sum(1 for s in states if s == "live")
    recorded = sum(1 for s in states if s == "recording")
    forming = sum(1 for t in lobby.tables.values()
                  if not t.settled and not t.lapsed)
    counts = (f"{live_now} playing now · {forming} forming"
              + (f" · {recorded} to watch back" if recorded else "")
              if lobby.tables else "nothing open yet")

    return f"""<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<meta http-equiv=refresh content={PAGE_REFRESH}>
<title>The island — lobby</title>
<style>{_CSS}</style>
<main>
<h1>The island — lobby</h1>
<p class=sub>Tables on <code>{html.escape(lobby.client.config.workspace)}</code>
— {html.escape(counts)}.<br>
{_age(now)}</p>
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
{MAX_JOINABLE} tables open for a seat at once · {MAX_TABLES} tables in all ·
{MAX_FORMING_PER_PEER} tables forming per peer · a table lapses after
{int(TABLE_TTL) // 60} minutes.</p>
{_heard(lobby)}
</footer>
{_TICKER}
</main>
"""


def write(lobby: Lobby, path: Path, *, now: float | None = None,
          live_dir: Path | None = None) -> Path:
    """Render and replace the page atomically, so a reader never sees half."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(render(lobby, now=now, live_dir=live_dir))
    tmp.replace(path)
    return path
