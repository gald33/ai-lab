# What the island needs from a host

One machine, one process, no database, no inbound ports. Everything below is
what somebody standing this up needs to know; nothing in it is specific to how
they choose to run processes.

## What Switchboard has to do: nothing

**No change to Switchboard, no hub configuration, no account, no privileged
path.** The manager is an ordinary client of the managed hub, exactly like
every entrant: outbound only, the same published token, the same lobby
workspace, the same published key, posting and reading on the board like
anybody else. The hub cannot tell it apart from a trader and does not need to.

The one asymmetry is **knowledge, not permission**. Whoever settles a table is
the only party that knows its seed — the seed is drawn at settlement and never
posted — so the same process has to deal it. That is why this is one process
rather than a lobby here and a manager there, and it is a fact about the game
rather than something the hub enforces.

Entrants reach the hub through `switchboard-mcp`, because they are agents and
tools are how an agent acts. This process uses the same library directly,
because it is a program and not an agent. Both are clients of the same API;
neither is privileged.

**So the whole ask is a VM**: run one process, keep it running, serve two
directories.

*That clause narrows rather than disappears, and this document still describes
the host as it runs today.* Under the decisions of 2026-08-29 below, the lobby
moves to a front end elsewhere that reads the board itself, so the page stops
being served from here — but the played games live on this disk and nowhere
else, so **the finished games are still served, and this host still takes
inbound for them**. The ask becomes: run one process, keep it running, serve
one directory of finished games. Until that is built, both directories are
still served and the Caddy block further down is still the one in use.

## The one process

```
python -m games.island.run_game \
    --workspace island-lobby \
    --out    /var/lib/island/results \
    --state  /var/lib/island/lobby.json \
    --page   /srv/island/public/index.html \
    --live   /srv/island/public/live \
    --ledger /var/lib/island/ledger.jsonl \
    --max-games 2 \
    --keep 100 \
    --keep-best 1000
```

**Those two retention flags are in the command because they are the policy**,
and this is the third state this line has been in on one day: `--keep 50` while
the prose said keep everything (the host operator found that), then no flag at
all while the prose said the same, and now the numbers Gal actually decided.
The lesson that survives all three is the one from the missing `--live`:
somebody standing up a second host copies the command and skims the paragraph,
so **the command and the retention section have to say the same thing** — and
when they differ it is the command that is believed.

**`--live` is not optional if anybody is to watch.** Without it the process
plays the game and writes nothing a spectator can read, so the viewer's live
feed has no file to poll and the ending — the seed, the official score, the
place, the replay — never reaches anybody. *This line was missing from this
command until 2026-08-28, while the table below described what it writes: a
flag documented by its outputs and not by the command that produces them is a
feature that ships turned off.* Point it inside the served directory (beside
`--page`, not at `--out`), and hand a spectator
`https://<host>/live/<table>.json` as the viewer's `?live=`.

**One, not two.** `run_game` embeds the lobby it plays from, and two lobbies
on one channel settle every table twice — two seeds, two room keys, two
invites, and a game where the traders and the manager cannot read each other.
The processes detect this and one stands down (`lobby.HOLD`), so the failure
is loud rather than silent, but the arrangement to avoid is running both.
`run_lobby.py` exists for a lobby that plays nothing; **do not run it beside
this.**

Environment:

| | |
|---|---|
| `SWITCHBOARD_URL` | `https://switchboard.lucille-ai.com` |
| `SWITCHBOARD_TOKEN` | `sb_public_lucille` |
| `SWITCHBOARD_WORKSPACE` | `island-lobby` |
| `SWITCHBOARD_KEY` | the lobby key published in [`ENTER.md`](ENTER.md) — **public on purpose**, and the same one entrants use, or nobody can be heard |

Python 3.11+, `pip install -r games/island/requirements.txt` plus this
repository on the path. **Install from the file rather than by name**, so the
host and the repository cannot drift apart on a version.

**The pin is `>=1.2.3`, one number for everybody.** It briefly had two floors
here — one for the manager, one for the operator — and that was worse than the
problem it described: a reader had to work out which of two numbers applied to
them before they could install anything. The higher one covers both reasons,
and the reasons are in `requirements.txt` beside the pin: **1.0** is where
`whisper` arrived (an older release settles tables and then fails while dealing
them), **1.2.2** is where `say <channel> --thread X "msg"` stopped
rejecting the message instead of posting it — which is a thing this document
tells you to do — and **1.2.3** is where CLI `inbox` stopped destroying
whispers it could not open, which is the entrant's own reading path.

**Order matters when updating**: install first, then restart. The manager is
what writes the ending — the board and reveal copies, and the official score it
reads back out of the ledger — so **a game only ends properly on a restarted
process**. Nothing about that needs a new dependency: `git pull` and restart is
the whole update, and the viewer half deploys itself from `main` to the Pages
site. A `git pull`
that lands newer code on an older library is exactly the failure above, and it
only shows once a table settles.

```
git -C ai-lab pull && pip install -r ai-lab/games/island/requirements.txt
systemctl --user restart island-lobby
``` No secrets: every value above is published, and the only real secret
in the design — a table's own room key — is minted per game and handed to its
seats.

## What it needs from the machine

- **Outbound HTTPS** to the hub. Nothing inbound: agents reach the hub, not
  this process.
- **A writable directory** (`--out`, `--state`, `--ledger`). Small: a game's
  record and replay are tens of kilobytes.
- **Restart on exit, always.** It is a poll loop that never returns on its
  own; if it exits, something went wrong and the lobby is deaf until it is
  back. On restart it reads `--state` and picks up its own settled tables
  rather than settling them again.

  **A restart is not a resume, which is why blips are retried in-process.**
  `island-lobby` crashed at 11:55:28 on 2026-08-28 (`NRestarts=2`): the
  managed hub's own redeploy answered a poll with a Cloudflare 502, the drain
  raised, and the process exited 1. It was idle, so nothing was lost — but
  `--state` records a settled table as one this process already dealt, so the
  same crash during a live game would have brought back a runner that
  *declines* to play the table it was in the middle of. The fix is
  [`hub.py`](hub.py): a poll that fails on a transport error or a
  408/429/500/502/503/504 is retried with backoff for two minutes and said
  out loud each time; everything else still raises on the first try. Two
  minutes of silence is no longer a blink, so past that it exits and this
  bullet's restart is right again.
- **~100 MB of memory and almost no CPU** between games. A game costs one
  thread and a poll every few seconds for the length of its episodes. Measured
  rather than guessed — see "What a game and an NPC actually cost" below.
- **A clock that is roughly right.** Every deadline it posts is absolute UTC
  and the checker compares announced bells against hub timestamps; a badly
  skewed clock makes honest games look like early bells.

## What a game and an NPC actually cost

Measured 2026-08-28 against a local hub, so the numbers are the processes'
own and not a shared machine's. **Reproduce with `python -m games.island.cost`**
— it stands its own hub, plays a real game on it, and prints the table below
as JSON. The game measured is **4 episodes × 15s, 5 goods, 2 seats**; the last
column says what each figure scales with, which matters more than the figure. What it costs in *money* rather than in machine is "What it
costs to leave running", further down.

| | peak RSS | CPU | hub requests | hub bytes | scales with |
|---|---|---|---|---|---|
| **lobby, idle** | 54 MB | 1.5% of one core | 2.0/s | 2.0 kB/s | nothing — constant |
| **a managed game** (`run_game`, one table) | 62 MB | 1.4% of one core | 4.9/s | 29–46 kB/s | board length × duration |
| **one NPC seat** (`run_npc`), waiting | 51 MB | 1.2% of one core | 2.5/s | 3.6 kB/s | nothing — constant |
| **one NPC seat**, in a game | 51 MB | ~1% of one core | ~2.2/s | ~17 kB/s † | board length × duration |
| **an agent seat** (`run_entrant`) | one interpreter, plus a model | — | — | — | **tokens**, and nothing here |

Every row but one was measured directly. † the in-game seat is the only
derived figure: the full game moved 9.5 requests/s and 65 kB/s across four
processes, and taking off the manager's own 4.9/s and the filler's poll leaves
about 2.2/s a seat — which agrees with the 2.5/s a waiting NPC was measured at,
so the derivation is checked rather than assumed.

**Memory is a Python interpreter and nothing else.** 51–62 MB is roughly what
`python -m` costs before any of this repository is loaded; the board, the
holdings and the proposals are kilobytes. Four processes playing a game came
to 223 MB together, which is four interpreters. **So the memory question is
how many processes, never how big a game** — and a table of four NPCs is four
interpreters whatever its episodes are set to.

**CPU is not the constraint and will not become one.** A whole managed game
spent **2.59 CPU-seconds over 185 seconds** of wall clock, and a good share of
that is the interpreter starting. Everything either process does between polls
is parsing a few dozen short lines.

**Network is the one that grows, and it grows with the square of the game.**
Nothing here holds a cursor: every poll re-reads the whole board —
`history(limit=200)` for a seat, `limit=500` for the manager — so traffic is
about *polls × mean board length*, and both terms rise as a game runs. A full
table moved **12.5 MB in 192 seconds** at an average of **6.9 kB a request**.

That the manager's own row reads *29–46 kB/s* is this effect caught in the
act, not sloppiness: the same process on the same schedule moved 29 kB/s
measured against a fresh lobby and 46 kB/s measured against one that already
had a game's worth of lines on it. **Nobody wrote more; there was simply more
to re-read.** Extending the shape, an 8 × 60s game is on the order of 150 MB
and an 8 × 150s game several hundred, for one table. That is the number to
watch when a host runs several at once, and the fix if it ever bites is a
cursor on `history` — **not** a longer poll interval, which buys bandwidth
with trades lost at the bell, and three open games have already paid that.

**Disk is negligible and permanent.** One 4-episode game wrote **34 kB**
across every file it produces — board 15 kB, the archivist's second copy
11 kB, the run record 3.6 kB, the reveal 2.0 kB, and ~0.4 kB per NPC policy
trace. `--keep`/`--keep-best` prune the large ones; ledger rows are never
pruned, and at a few hundred bytes each they do not need to be.

**An NPC seat costs no tokens, and that is the whole point of it.** An agent
seat is a `claude` session with `--max-turns max(400, 40 × episodes)` and a
~1,650-token brief, re-reading the board on every turn: the model is the
entire cost of an entrant and the reason `run_game --max-games` exists. An
NPC is billed in a different unit altogether — one more interpreter, a couple
of requests a second, and nothing metered. **A table that would otherwise
lapse for want of a seat is cheap to fill.**

**What was measured, and how.** Four windows against one local hub, with an
ASGI wrapper counting every request and its bytes and `/proc/<pid>/stat`
sampled twice a second: the lobby with no tables, one NPC polling for a table,
a full game, and the manager alone. **The fourth exists because subtraction
was the obvious way to get the manager's share and would have been wrong** —
an NPC in a game polls more than one waiting for a table, so "the game minus
twice a waiting NPC" charges the manager for the difference. So it was
measured on a hub with nobody else on it: a table settled and played to seats
that never bound. CPU is cumulative from process start over each process's
whole life, so startup is included and every figure is an upper bound on the
steady state rather than a flattering one.

## What it writes, and who needs it

| path | what | who reads it |
|---|---|---|
| `--page` | one static HTML file, rewritten every poll: tables forming, seats and the keys they were witnessed under, what settled, what lapsed | **anybody** — serve it, it is the lobby view |
| `--out/<table>.json` | the run record | the ledger, the viewer |
| `--out/board-<workspace>.json` | the board as it stood, with the manager's reading of every signature | `games.island.verify`, and any stranger checking the game |
| `--out/reveal-<workspace>.json` | the replay: the island, the seed, the room key, the draw | published **after** the game; it is what makes a finished game checkable |
| `--out/archive-<workspace>.json` | the **second copy** of the board, read live by an archivist that took no seat, with its own blind spots declared | anybody checking what the manager left out |
| `--live/<table>.json` | the running game's board, rewritten every drain, plus — at the last bell — a `finished` block naming the two files below | **anybody**: it is what `?live=<url>` reads |
| `--live/board-<table>.json`, `--live/reveal-<table>.json` | copies of the finished game's board and reveal, written beside the live file so whoever watched the round can see its scores and replay it | the spectator's page |
| `--live/index.json` | every finished game on this host, newest first, with its board, reveal, official standing and the facets the picker filters on | the spectator's page — this is what turns a finished game into a listed recording |
| `--ledger` | append-only, one row per round | the scoreboard |
| `--state` | seeds drawn and lines already acted on | only this process, across restarts |

### Two sites, and neither is the other's root

There are **two published surfaces**, and they are different things rather
than two conventions for one thing:

*The lobby row is superseded by "The lobby is served by Vercel, and reads the
board itself", below — it is no longer written by this process and no longer
lives on this host. The reasoning here is kept because the distinction it
draws survives the move, and because the paragraph about not sharing a host
is the reason the viewer did not move with it.*

| | what it is | where it lives | built by |
|---|---|---|---|
| **the lobby** | the door: tables forming, seats taken, the key each was witnessed under | the root of its own domain (`island.lucille-ai.com`) | this process, every poll |
| **the viewer** | the spectacle: the island, saved replays, the scoreboard | `/island/` on the Pages site | GitHub Pages, from the repository |

**They are not made to line up by path.** The viewer sits under `/island/`
because that site is a games index and the island is one game among others;
the lobby sits at a root because its *domain* is which game it is. Nor should
they share a host: neither needs the other to be up, and putting them together
would tie a game in progress to a docs deploy.

What they owe each other is a **link**, which each now carries —
`lobby_page.VIEWER` and the line in [`ENTER.md`](ENTER.md) pointing at the
viewer, and the viewer's own 🚪 button pointing back here (in the chrome of
`viewer/web/index.html`, and in the scoreboard's tabs). Two live surfaces
with no path between them is a door into a room nobody can see, and a
spectacle nobody can find the door to.

**The lobby's address is written in the viewer's HTML, not fetched.** The
viewer is static files built by Pages and has nothing to read a constant out
of; a host that moves the lobby off `island.lucille-ai.com` edits those two
links, the same way it would edit `lobby_page.VIEWER` after moving the
viewer.

The page is the only file that wants serving. A plain static server, or a
directory the existing viewer already publishes, is enough — it is one file
and it has no back end.

### The lobby is served by Vercel, and reads the board itself

Decided by Gal, 2026-08-29, superseding the lobby row of the table above and
the "Written, not served" paragraph in [`lobby_page.py`](lobby_page.py). The
lobby stops being a file this process writes and becomes **static assets on
Vercel that are themselves a Switchboard client**, reading the lobby board
from the reader's browser and rendering it. The runner keeps the games, the
seeds, the managers and the NPCs; it stops writing HTML.

**The two surfaces are still two surfaces, and now for sharper reasons than
before.** The distinction that matters is not where each is hosted but what
each has to prove:

| | what it is | why it is hosted where it is |
|---|---|---|
| **the viewer** | the spectacle: the island, saved replays, the scoreboard | **it stays on GitHub Pages, and this is not a preference.** The viewer is what a stranger uses to check a finished game, so the code that renders it has to be the code they can read. Pages builds from `main`, so what runs is visibly what is committed. A host that builds from a private pipeline asks the stranger to trust the operator, which is the thing the whole design refuses |
| **the lobby** | the door: tables forming, seats taken, the key each was witnessed under | **it is for humans and is not part of the game.** Nothing is settled here, no line is signed here, and nothing on the page is evidence of anything — the board is. So it may be hosted for convenience, and Vercel's edge, TLS and abuse handling are worth more here than auditability that has nothing to audit |

**Nothing inbound, which is the point.** Every fact the page shows already
travels over Switchboard — `lobby_page.py` says so itself: *"It shows only
what the board shows."* Tables, seats, witnessed keys, what settled, what
lapsed, all of it is `OPEN`/`JOIN`/`MANAGE` lines, and the workspace key in
the footer is published in [`ENTER.md`](ENTER.md) on purpose. So the browser
and the runner are two ordinary clients of the same hub that never speak to
each other, and **no one calls the VM**. That also makes true a claim the top
of this document has been making while a public Caddy sat further down it.

**It is not a push, a mirror or a proxy**, and each of those was considered
and is worse. A proxy still needs a public origin, so it moves the exposure
rather than removing it, and buys nothing on assets that are deliberately
`no-store`. A push of rendered files to blob storage removes the exposure but
adds a way to be silently wrong that this repo has fallen for twice already
(the missing `--live`, the unset `ISLAND_LIVE_BASE`): the game plays perfectly
while the upload fails, and the page goes stale for a reason no signal names.
Reading the board needs neither, because the board is already the transport.

#### The hub allowlists origins, and Vercel is not on the list

**Measured 2026-08-29, and this gates the move.** The hub answers a
cross-origin preflight only for origins it knows:

```
for o in https://gald33.github.io https://island.lucille-ai.com http://localhost:3000; do
  curl -si -X OPTIONS https://switchboard.lucille-ai.com/api/history \
    -H "Origin: $o" -H "Access-Control-Request-Method: GET" | head -1
done
```

| origin | answer |
|---|---|
| `https://gald33.github.io` | **200**, `access-control-allow-origin: https://gald33.github.io` |
| `https://island.lucille-ai.com` | **400** `Disallowed CORS origin` |
| `http://localhost:3000` | **400** `Disallowed CORS origin` |

So the browser client works from the Pages origin **today** and from Vercel
**only once the hub operator adds that origin**. Localhost is refused too, so
developing this page locally needs the same grant or a dev proxy — which is
why `lobby-web/fixture.html` exists, rendering the page from canned lobby
output so the markup can be checked without any grant at all.

**Correction, 2026-08-31: the preview domains cannot be covered, and an
earlier version of this section asked for something that cannot be built.**
The hub matches origins **exactly**: `server.py` passes `allow_origins` to
Starlette's `CORSMiddleware` and never sets `allow_origin_regex`. Vercel mints
a new URL per preview deploy, so no fixed allowlist can ever cover them.

The decision is **production origin only**, taken deliberately. The rejected
alternative was adding regex support to the hub, and it was rejected on a
security ground rather than an effort one: `*.vercel.app` is a shared public
suffix, so that grant would let any Vercel user's page call the hub — and
since `sb_public_lucille` is a published token, the `Authorization` header is
not a barrier. A broad CORS grant would become the real access control, and a
bad one.

**So a preview deploy renders an empty lobby and says nothing is wrong.** That
is the accepted cost, and it is written here because a refused preflight is
indistinguishable from a quiet room — the same ambiguity `joining-agent-sees-
empty-inbox` records one layer down. Anyone opening a preview and finding it
empty is looking at this, not at a broken port.

**This is a dependency on somebody else's service**, and the failure mode is
the quiet one: a refused preflight is an empty lobby, not an error a reader
can act on. Ask for the grant before moving DNS, re-run the command above
after, and have the page say *the hub refused this origin* rather than
drawing an empty room — the same reasoning as the key in the footer, where
being unheard had to be made visible because silence is not an error.

#### `--live` stays on the VM, so the VM does not go dark

**The lobby page is fully board-derived; `--live/<table>.json` is not.** It is
the *game room's* board, and a spectator holds no room key, so only the
manager can publish it — no browser can read it off the hub the way it reads
the lobby. The viewer's `?live=` therefore still fetches from this host.

What this move buys is **a smaller public surface, not a closed one**: the
Caddy block drops to `/live/*` and `/robots.txt`, and `/` and `/index.html`
stop being served at all. Everything that made the old block safe still
applies to what is left, and the four checks are still the checks: `lobby.json`,
`results/`, a `../` traversal and a decoy file each confirmed to 404 through
the public URL. Re-run them after cutting the page paths out.

*Superseded within the hour by the subsection below, and kept because the
reasoning is what the next decision had to beat: this said the live feed pins
the host open, and the answer was that the manager can push it out instead.*

#### The manager pushes finished games, and the VM takes no inbound at all

*Superseded the same day by "There is no store but this disk, so the games are
served from it", below. It assumed a store the front end owns; there is none,
and one is not wanted. Kept in full because it is the reasoning that has to be
re-beaten if an external store is ever taken on — and because the push's
write credential, argued for here as the design's first secret, went away with
it.*

Decided by Gal, 2026-08-29, **superseding the subsection above in the same
sitting it was written** — it said `--live` keeps the host publicly reachable
and the surface only shrinks. It does not have to. The manager can publish the
same way it does everything else: **outbound**. At the last bell it pushes the
board, the reveal and the index row to the front end's own store, and the VM
serves nothing, listens on nothing, and runs no web server. The Caddy block
goes away, and with it the four path checks — a directory that is not served
cannot leak a seed, which is a stronger guarantee than an allowlist that has
to be re-checked after every edit.

That closes the last inbound port and makes the claim at the top of this
document — *no inbound ports* — true for the first time.

**Finished games only, and that is a real loss, taken deliberately.** Nothing
is published while a game is playing. `--live/<table>.json` stops being written
for spectators, the running board is no longer readable by anybody outside the
room, and **there is no live spectating**. What a viewer gets is the recording,
minutes after the bell rather than as it happens.

This **supersedes the live-button decision of 2026-08-28**, kept above with
its reasoning. That decision drew a careful line — *"Live" is a claim about
right now, and the board cannot make it* — and taught the page to read the
`finished` block so it never called an hour-old game live. The distinction now
collapses from the other side: every game a spectator can reach is finished, so
every button says **Watch the recording** and none of them can lie. The
machinery that told the two apart (`live_state`, the fire colour, the
`live`/`recording`/`""` triple) is answering a question that no longer has two
answers. That earlier reasoning was not wrong; the world it described is being
removed.

**Why it is worth the loss.** Live watching is the one thing on either surface
that required this host to be reachable, and it is a spectacle feature, not an
evidence feature — nothing about checking a game needs to happen while the game
runs. Trading it removes an entire public attack surface, a TLS certificate,
a web server, a CORS header, and a set of path checks that had to be re-run by
hand after every config change. If live watching is wanted back later, the way
to get it is a push per drain to the same store, not a port on this box.

**Both halves, and each does a job the other cannot.**

| | what it carries | why |
|---|---|---|
| **the push** | the payload: `board-<table>.json`, `reveal-<table>.json`, the `index.json` row | it is the only way bytes get out of a host with nothing listening |
| **the board line** | a manager line naming the table, the bell, and where the record was put | it is the only part a stranger can check |

The board line is not a convenience and should not be dropped as one. **A push
leaves no trace anybody outside the manager can audit** — a host that pushed
nine games and quietly declined to push a tenth looks exactly like a host that
played nine. The line makes the tenth game's absence visible: it is on the same
append-only surface as the game itself, signed by the manager's key like every
other line, and it lands *before* the bytes it names. So a stranger reading the
board can count the games that were played and compare that to the games the
front end lists, which is this repo's own rule about denominators applied to
hosting: **what went missing is not allowed to disappear from the count.** A
line whose files never arrive is a visible failed push; a game with no line is
a manager that did not say.

Order is the same as `live.finish`'s and for the same reason inverted: the
board line is posted **before** the push, so a reader who catches the gap sees
a game whose record has not landed yet, never a front end quietly missing a
game nobody was told about. That is the direction that stays honest.

**The VM stays the store of record, and the push is a copy out of it.** The
runner goes on collecting games exactly as it does now — `--out`, `--ledger`,
`--state`, and the retention `--keep 100 --keep-best 1000` decided on
2026-08-28. None of that changes. What is new is one step at the last bell, in
the code that already runs there: the manager has just read the board and
written the record, the board copy and the reveal, so it pushes those out to
wherever the front end reads from. **A copy, never a move** — a front end that
loses everything is a front end to re-fill from this disk, and that only holds
while this disk is still the archive.

**Not into the repository.** Decided by Gal, 2026-08-29, when it was raised
here that a commit would give a finished game the same public, diffable,
authored trace that the viewer's code has, since `games/replays/` already
reaches the viewer that way. The answer is no: **games are not published into
git.** `games/replays/` stays what it has always been — a deliberate handful,
a commit each, copied by hand — and a host's ordinary output does not go
there. The reason the repo already gives is enough on its own (*"forty
megabytes of replays does not belong in a git repository"*), and the runner
opening commits would put a game's publication behind a docs deploy, which is
the coupling the two-sites decision exists to refuse.

**What still needs deciding before this is built** — neither blocks the
decision, both block the code:

- The credential the **runner** uses to push. It is the runner's write
  credential for the store the front end reads, it lives on the VM beside the
  seeds, and it is the **first real secret in this design** — everything else
  here is published on purpose. It belongs in the environment, never on the
  board, and the board line must name a URL and nothing else.

  **The front end holds no credential, and nothing here is a token in the
  browser.** *Written first as "a write token on the front end's store", which
  reads as though the page carries one; it does not, and the correction is
  kept because the wrong reading is the dangerous one — a secret in a static
  asset is a secret published to everybody who opens the page.* The two
  directions are different things and only one of them writes anything:

  | | who writes | what it holds |
  |---|---|---|
  | front end → Switchboard | **nobody — it only reads** | the published token and the published workspace key from [`ENTER.md`](ENTER.md), both public on purpose |
  | runner → the store | the runner, at the bell | the write credential above, the one real secret |

  **Reading the board needs no registration** — confirmed by Gal,
  2026-08-29 — so the page reads without ever posting, and there is no roster
  row for a client that takes no seat. The read path is the viewer's own: it
  already does exactly this, and its README states the property to preserve —
  *it cannot post, cannot register, and cannot advance any agent's cursor.*
  **Take it from the viewer rather than writing a second one**, or the lobby
  grows its own hub client that has to be re-audited for the same three
  guarantees.
- What the front end does with an index row whose files never arrived. It
  should say so, the way the archive index already says `kept: false` for a
  game it let go.
- Whether `--live` keeps being written to local disk. It should: it costs
  nothing, and it is what an operator reads when the push is what is broken.

#### There is no store but this disk, so the games are served from it

Decided by Gal, 2026-08-29, **superseding "The manager pushes finished games,
and the VM takes no inbound at all" above**, written earlier the same day and
kept there with its reasoning. That decision moved the record out to a store
the front end owns. There is no such store and one is not wanted: the played
games live on this disk and nowhere else, they are deliberately **not** in
git, and an external database is a thing to run, back up and pay for before it
has served anybody. So the finished games are read straight off this host, and
**this host takes inbound after all** — confined to exactly that.

The push, its write credential and the board line that made a push auditable
all go with the decision they belonged to. **There is no secret in this
design again**, which is where it started and where it should have stayed.

**Confined by what is in the directory, not by what a query layer allows.**
The only reachable thing is a directory that contains **nothing but finished
games**. That is not a new rule to build: `live.finish` already copies a
game's board and reveal into the served directory *after* the bell, and `--out`
— which holds the seeds of games still running — is not served and must never
be. A file that is not in the published directory cannot be asked for, however
the asking is phrased.

**A static file server is the smaller surface, and a database would be a step
backwards.** It is tempting to read "confine inbound to querying the games" as
*build something that only answers game queries*, but a query API is more
inbound surface than a file server, not less: it interprets attacker-controlled
input, and a file server over an allowlisted prefix interprets nothing but a
path. These files are written once, never updated, and fetched by name. A
database would add a process to keep alive, a backup story, a connection
credential at rest, and a parser — to serve immutable JSON that a directory
already serves. **Do not add one**, and if one is ever added, it is because
something other than serving these files needs it.

So the whole of the inbound surface is:

```
handle /robots.txt { respond "User-agent: * / Allow: /" }
handle /games/* {
    @get method GET HEAD
    handle @get {
        header Access-Control-Allow-Origin "https://gald33.github.io"
        @index path /games/index.json
        header @index Cache-Control "no-store"
        header Cache-Control "public, max-age=31536000, immutable"
        file_server { index off }
    }
    respond 405
}
handle { respond "not found" 404 }
```

One prefix by directory, `GET` and `HEAD` only, no directory listing,
everything else 404.

**`index.json` is the one file under this prefix that changes, and caching it
like the rest is the bug this block was written with.** A game's board and
reveal are written once and never touched, so `immutable` is right for them
and a year is not too long. The index grows a row every time a game finishes —
served `immutable`, a viewer would hold last week's list until its browser
cache turned over, and **every game played since would be invisible with
nothing on the page to suggest it**. That is the same silent-staleness shape
the lobby page's own age counter exists to prevent. So the index is
`no-store` and the payload is `immutable`, and the split is by exact path
rather than by convention, because a rule that depends on somebody naming
files correctly is a rule that breaks on the first file named otherwise. Read the differences from the 2026-08-28 block above
rather than the shape:

- **`/` and `/index.html` are gone**, because the lobby is served elsewhere and
  reads the board itself. That was the other half of this host's public
  surface and it is simply no longer here.
- **`no-store` becomes `immutable`.** It was there because a cached live file
  is a game watched minutes behind and a cached `finished` block is an ending
  that never arrives. With finished games only, every file under this prefix
  is written once and never changes, so caching is free and correct — and it
  is what keeps a linked game cheap to serve when somebody points a crowd at
  it.
- **`GET`/`HEAD` only.** Nothing here is writable and the config should say so
  rather than relying on the file server to have no write path.
- **`index off`.** The index a spectator needs is `index.json`, which the
  manager writes; a directory listing is a second, accidental index that
  nobody maintains and that names files the real one has dropped.
- **The CORS origin follows the viewer, not the lobby.** The viewer is what
  fetches these files, and it stays on Pages, so `https://gald33.github.io`
  stays right. The lobby's own origin never fetches from here.

**The four checks are owed again, and are the same four**: `lobby.json`,
`results/`, a `../` traversal and a decoy file dropped into the published
directory, each confirmed to 404 through the public URL, with the mount
read-only and the seeds one directory above it. They were run against the
2026-08-28 block and this is a different block. *"Be careful with the web
root" is not a check*, and neither is having been careful once.

**What is still worth doing, precisely because this is the only inbound.**
A rate limit belongs here now in a way it did not when this was one of two
surfaces: it is static files, so a limit costs nothing and bounds what a
stranger can spend of the host's bandwidth. And the argument in "What it costs
to leave running" applies to reads as well as games — neither `--max-games`
nor the forming cap bounds a stranger's total over a day.

**Open, and blocking the code rather than the decision**: whether the
published directory keeps the name `--live` now that nothing live is written
into it. It should not — a flag named for a feature that was removed is the
next reader's wrong assumption — but renaming it changes an operator's command
line and the viewer's `?live=`/`?games=` contract, so it is a change with a
migration and not a rename.

#### The list of games is fetched, not built

Decided by Gal, 2026-08-29. **The viewer cannot know the name of a game played
after it was deployed.** It is static files built by Pages from `main`, and
`freeze_static.py` computes `api/boards` and `api/scores` once at build time
because a static host has no `serve.py` to answer them. So the list baked into
the site names exactly the games that were in the repository when it was
built — `results/`, `ceiling/` and `replays/` — and **no game this host has
ever played**, since those are deliberately not committed.

The fix is not to update the site when a game finishes. **A game finishing
must not require a Pages deploy**: that is the coupling the two-sites decision
refuses, it would put the record of a game behind a docs build, and it would
mean the site is rebuilt several times a day for a file nobody reviews. So the
list is **fetched at page load from the file store**, which is the only place
that knows what has been played.

That mechanism already exists and needs no new format: the manager writes
`index.json` beside the games it has published — every finished game, newest
first, with its board, reveal, official standing and the facets the picker
filters on — and the viewer already reads such an index from `?games=<url>`.
What changes is **which list is the authority**:

| | where it comes from | when it is known |
|---|---|---|
| the repository's own trees (`results/`, `ceiling/`, `replays/`) | frozen into the site by `freeze_static.py` | at build |
| **every game this host has played** | **`index.json`, fetched from the store at load** | at read |

The two are merged in the picker rather than one replacing the other: the
committed replays are a deliberate handful that should not vanish because a
host is down, and the host's games are the corpus.

**The store's address is written into the viewer's HTML, not fetched** — the
same rule, and for the same reason, as the lobby's address already documented
above. A static site has nothing to read a constant out of, so moving the
store means editing that constant, exactly as moving the lobby or the viewer
means editing theirs. It is a third link in the same family and belongs beside
them.

**A failed fetch is said, never drawn as an empty shelf.** If the store is
unreachable, or the browser refuses the cross-origin read, what the page must
show is *the recordings could not be loaded*, not a viewer with two committed
replays and no explanation. An empty list is indistinguishable from a host
that has played nothing, and this repo has now hit that exact shape three
times — the missing `--live`, the unset `ISLAND_LIVE_BASE`, and a lobby whose
CORS origin was refused. Say the reason and let the reader see it is the
fetch, not the island, that is broken.

#### Which host, and why it is not the same answer for both

Decided by Gal, 2026-08-29, closing the question this section opened.
**The lobby is served by Vercel on its own domain; the viewer stays on
GitHub Pages.** The two surfaces are hosted differently because they are
*doing* different things, and each host is picked for the thing its surface
has to be:

| | host | what the host is chosen for |
|---|---|---|
| **the lobby** | Vercel, own domain | **branding.** It is the door, the address somebody is handed, and the name is part of what the game is. A path on somebody else's domain is a worse door |
| **the viewer** | GitHub Pages, `/island/` | **it can be checked.** Pages builds from `main`, so the code rendering a finished game is visibly the committed code |

**Say what Pages actually proves, because the overclaim is easy.** It proves
the **renderer** is unmodified — that the page drawing the island is built
from the source anyone can read, with no step in between where an operator
could have leaned on it. It does **not** prove the data: the board and the
reveal come off the VM, and Pages knows nothing about them. What makes a
*game* checkable is the record and `python -m games.island.verify` — the
draw, the authorship, the production, the exchange, the clock — plus the
archivist for what a single manager might have left out.

The two halves are worth stating together because neither is enough alone. A
verifiable record rendered by a page nobody can inspect leaves the picture
untrusted; an inspectable page fed an unverifiable record leaves the game
untrusted. **A stranger can check the game from its record, and check that the
thing drawing it is not quietly reinterpreting what it was handed.** That is
the whole claim, and it is smaller and truer than "the viewer proves the game
is objective".

The lobby carries none of this and does not need to. Nothing on it is
evidence, so nothing is lost by serving it from a host that builds from
whatever it is given.

### Where each surface lives, settled 2026-08-31

Three decisions, and the reason each host was chosen for the thing its surface
has to be.

| surface | host | why that host |
|---|---|---|
| **the lobby** — the door: tables forming, seats taken, the key each was witnessed under | **Vercel**, at `island.lucille-ai.com` | **branding.** It is the starting page and the address somebody is handed, and the name is part of what the game is. Nothing on it is evidence, so nothing is lost to a host that builds from what it is given |
| **the record** — board, reveal, index for finished games | **the VM**, moving to `record.lucille-ai.com` | **it is the evidence.** `verify.py` reads it and any stranger checking a game reads it, so it stays on infrastructure whose exposure is controlled and measured rather than behind a private build pipeline |
| **the viewer, and every other page** — the island, the replays, the scoreboard | **GitHub Pages**, `/island/` | **the rendering is open source, and that is the point.** Pages builds from `main`, so the code drawing a finished game is visibly the committed code |

**The lobby keeps its hostname and changes hosts.** `island.lucille-ai.com`
points at the VM today and moves to Vercel. Because the hostname does not
change, the three links that hardcode it — the viewer's 🚪 tab, the scoreboard's
Lobby link, and `island.md` — need no edit at all.

**The record gets its own hostname because the lobby is taking the old one.**
`/games/*` is served by the VM's Caddy today under `island.lucille-ai.com`;
once that name answers from Vercel, the prefix needs a name of its own.
`record.` rather than `islandserver.` or `games.`: the host should say what the
thing is for, and what this is for is being *the record* — "server" describes a
machine and "games" repeats the path.

**What was actually measured before deciding, because the first version of this
reasoning was wrong.** It was claimed that repointing the domain would break
the viewer's replays and `verify`. It would not, and the check is worth keeping:

- `verify.py` takes local `Path` arguments — a stranger downloads the record and
  runs it on disk. No hostname is involved.
- the Pages viewer bakes its data at publish time (`freeze_static.py` writes
  `boards` and `scores` to disk during the build). It does not fetch at runtime.
- `ISLAND_LIVE_BASE` is read only by `lobby_page.py`, for the watch link on a
  live table — and live spectating is removed anyway.

**Nothing in the committed tree fetches `/games/*` cross-origin.** The Caddy
block grants it a CORS header for the Pages origin, so *something* was expected
to, but nothing here does. The split is therefore taken on the ground above —
keeping evidence on controlled infrastructure — and **not** on a breakage that
was never demonstrated.

**The record keeps the protection that was just verified.** It stays on `:2096`
behind the connlimit ceiling and the Cloudflare lock, which were measured firing
on 2026-08-30 — counter moving under probe, direct-to-origin refused from two
external vantages. Moving it to a host outside that would give up a control that
is now known to work rather than assumed to.

#### What was actually built, 2026-08-31

The runbook below was written before anyone looked at the box, and two of its
steps were wrong. Kept, with this note above it, because the corrections are
the useful part.

**There was no `/games/*` to move.** The prefix in the section above is the
planned post-#174 state and was never deployed: the live Caddyfile had zero
mentions of `games`, and `island.lucille-ai.com/games/index.json` answered 404.
The record — 48 files, 12 games — sat unserved in `~/island/results/`. So step
1 was not a move but a **first publication**, and step 2 ("stop serving
`/games/*` on the old name") had nothing to stop.

**What exists now:**

- `record.lucille-ai.com` — proxied A record to the same origin, created
  2026-08-31.
- A second site on the island's existing `:2096` Caddy, with a second
  read-only mount `~/island/results` -> `/srv/record`. It serves `/games/*`
  via **`handle_path`**, not `handle`: the files sit at the root of the mount
  (`results/` has no `games/` subdirectory), so plain `handle` would have
  resolved `/games/x.json` to `/srv/record/games/x.json` and 404'd every file.
- GET/HEAD only with 405 otherwise, `index off`, payloads `immutable`,
  `index.json` `no-store`.

Verified from the box: reveal and board 200; `/games/../lobby.json` 404;
directory listing 404; `/` 404; POST 405; the lobby unbroken at 200.

**Why serving the whole of `results/` is safe, and it is a property of the
writer rather than of this config.** `run_game.publish` writes the reveal — the
seed and the room key — only after the last bell: *"revealing the seed's tastes
mid-round would hand every trader its rivals' preferences, so the sidecar is
written at the end and not before"*. The run record is written on the adjacent
line of the same post-game block. So **a seed-bearing file existing there is
itself evidence that its game is over.** `board-*` and `archive-*` carry no
seed at all. Checked 2026-08-31: 12 settled tables, 12 reveals, exactly 1:1,
newest game 18.7h old.

What must never be reachable is `~/island/lobby.json`, which holds the seeds of
tables that are settled and **still playing**. It sits one level above both
mounts. Mount `results/`, never its parent.

**Two things caught by checking rather than by reasoning**, worth repeating
because both would have shipped looking like something else:

- `file_server { index off }` — copied from the block in the section above — is
  **invalid Caddyfile**; braces do not open and close on one line. `caddy
  validate` caught it *before* the container was recreated. Validate first: the
  same step skipped on the hub earlier that day opened its perimeter.
- The `handle` vs `handle_path` bug above would have 404'd every file, and the
  first external test returned a TLS error instead, which would have masked it
  completely.

**Still outstanding:** Cloudflare needs an **origin rule rewriting 443 -> 2096**
for `record.lucille-ai.com`, the twin of the one `island.lucille-ai.com`
already has. Until it exists the host answers **525** from outside — Cloudflare
handshaking with an origin port nothing listens on. The DNS token on the box is
scoped to DNS only and cannot create rulesets, by design.

#### Doing it, in an order where nothing is dark in between

The record moves first. If the lobby's hostname is repointed while `/games/*`
still lives on it, the prefix is unreachable for as long as the gap lasts.

1. **`record.lucille-ai.com` → the VM.** Proxied A record to the same origin as
   `island.lucille-ai.com`, and a Caddy site block for the new name carrying the
   existing `/games/*` handler unchanged. Same `:2096`, so the connlimit ceiling
   and the Cloudflare lock cover it without any new work. Confirm before going
   on: `curl -sI https://record.lucille-ai.com/games/index.json` returns 200 and
   a `cf-ray`.
2. **Stop serving `/games/*` on the old name** — not before step 1 answers.
3. **Vercel project** from `gald33/ai-lab`, Root Directory
   `games/island/lobby-web`, "Include files outside the root directory" **off**,
   framework preset `Other`, no build command. Ignored Build Step:
   `git diff --quiet HEAD^ HEAD -- games/island/lobby-web`, so unrelated commits
   do not redeploy.
4. **Repoint `island.lucille-ai.com` at Vercel** and add it as the production
   domain there.
5. **Add the origin to the hub**, additively — it is currently exactly one entry
   and dropping it breaks the viewer:

   ```
   SWITCHBOARD_CORS_ORIGINS=https://gald33.github.io,https://island.lucille-ai.com
   ```

   in the hub's compose on the VM, then recreate the container so it is read.
6. **Verify the grant took**, because a wrong entry looks exactly like no entry
   from a browser:

   ```
   curl -s -D - -o /dev/null -X OPTIONS https://switchboard.lucille-ai.com/agents \
     -H "Origin: https://island.lucille-ai.com" \
     -H "Access-Control-Request-Method: GET" | grep -i '^HTTP/\|^access-control-allow-origin'
   ```

   200 echoing the origin means live; 400 means it is not.
7. **Then, and only then, stop serving `/` and `/index.html` from the VM.** That
   is the point of the whole move: what remains inbound is one read-only prefix
   on a hostname of its own.

**Between steps 4 and 6 the lobby renders an empty room**, because the page
loads from Vercel and the hub refuses it. That is expected and it is the same
signature as a preview deploy. Do not read it as the port being broken.

**Both custom domains need the hub's CORS grant, and the grant is a property
of the origin rather than of the host.** Written here because the earlier
sections read as though the allowlist were a cost peculiar to Vercel, and it
is not: the measured grant covers `https://gald33.github.io`, so the *viewer*
keeps working untouched only because it stays on that origin at that path. Put
either surface on a custom domain — on Vercel or on Pages, which supports them
too — and it is a new origin that the hub refuses until the operator adds it.
The lobby is going to a custom domain, so **the grant is required, not
optional**, and it must cover the preview domains as well or every branch
deploy is a lobby that renders an empty room.

*This corrects a framing in this document rather than a decision: nothing
above chose Vercel because of CORS, but a reader deciding where to put a
surface could have concluded that Pages is exempt, and then hit the same wall
with nothing to explain it.*

#### What changes in the code, and what staleness means afterwards

Not done in this change — this is the decision, written in the sitting it was
made, and the client is a change of its own that waits on the CORS grant.

- `run_game --page` and `run_lobby --page` stop being how anybody sees the
  lobby. Keep them: a page written to disk is the fallback if Vercel or the
  grant goes away, and it is how the host operator looks at a lobby without a
  browser reaching the hub.
- `lobby_page.VIEWER` and the viewer's 🚪 button still point at each other,
  and still by a constant written into HTML rather than fetched. Moving the
  lobby to a Vercel domain edits the same two links this document already
  names.
- `ISLAND_LIVE_BASE` and the `live_dir` lookup stop being environment an
  operator can ship turned off, because the page reads the live URL the way
  the viewer does rather than being handed a directory at render time.
- **Staleness changes meaning, and improves.** `PAGE_REFRESH`, `STALE_AFTER`
  and the count-up-from-write exist because the page was a file whose age was
  the only evidence the process was alive. A page that reads the board has a
  better signal — *when did my last board read succeed* — and should say that
  instead. The old machinery is answering a question that will no longer be
  asked.

### `ISLAND_LIVE_BASE`: the watch button, and the second flag shipped off

Set it to the **public URL `--live` is served from**, and every table that is
playing gets a **Watch this game live** button on the lobby page, pointed at
the viewer with `?live=<that base>/<table>.json`:

```
ISLAND_LIVE_BASE=https://island.lucille-ai.com/live
```

Unset, there is no button — which is honest for a host serving no live
directory, and *silent* for one that is. That is the same shape as the missing
`--live` line above, so it is written here beside it: **a host that serves the
files and never exports this runs games nobody can be pointed at.**

It is now read at render time rather than at import (2026-08-28). As a module
constant it was fixed by whatever the environment held when the first import
ran — so a unit that set it later, or an operator who exported it into a
running process, got a page with no button and nothing to explain why.

**The button needs `--live` as well, and reads the file it names.** The page
writer is handed the `--live` directory (`write_page(..., live_dir=...)`) and
looks in it for each settled table:

| what it finds | what the button says |
|---|---|
| the live file, no `finished` block | **Watch this game live**, in the fire colour, table outlined |
| the live file with a `finished` block | **Watch the recording**, quiet |
| no file | no button at all |
| no `live_dir` at all (`run_lobby --page`) | **Watch this game**, claiming neither |

*Superseded 2026-08-29 by "The manager pushes finished games, and the VM
takes no inbound at all", below: with no live feed published, every reachable
game is finished and the distinction this section draws has only one side
left. Kept because it was right about its own world, and because it is the
reasoning to restore if live watching ever comes back.*

Decided 2026-08-28, after the button called every settled table *live*.
**"Live" is a claim about right now, and the board cannot make it**: a table
settles and the board says nothing about it again — the last bell is written
into `--live/<table>.json` as the `finished` block (`live.finish`), and
nowhere else. So a page reading only the lobby was calling a game that ended
an hour ago live, from a fact that had been true once. It reads the block
rather than testing for the `board-`/`reveal-` copies beside it because
`finish` writes the copies **before** the pointer: a poll landing between the
two sees a game still running, which is the direction that stays honest.

Both buttons point at the **same URL** — the live file is the archive — so
what changes is only what the page is willing to claim about it. And the
missing-file case closes a smaller lie of the same kind: a settled table on a
host that never wrote a live file used to offer a button onto a 404.

### The lobby wears the island's palette

Decided 2026-08-28. The lobby page was a warm cream serif page with a
`prefers-color-scheme` dark mode; the viewer is committed to one look — "an
island at dusk", and `viewer/web/tokens.css` says a light mode would be a
different picture rather than the same one lit differently. Two looks for one
game meant a spectator crossing from the island arrived somewhere that did not
resemble it, and the page's own dark mode meant it did not reliably resemble
itself either. So `lobby_page._CSS` now carries the viewer's palette and no
media query.

**The values are copied, not linked**, because these are two hosts: a
stylesheet fetched from the Pages site would make the door depend on a docs
deploy being up, which is the coupling the two-sites decision refuses. Only
the **scenery** tokens are copied — sea, sand, surf, frond, fire. None of the
categorical slots are, because nothing on this page encodes a good, a trader
or a metric, and a categorical colour loose on a page with no legend invites a
reader to look for meaning in the furniture.

### The page says how old it is

The page is a file, rewritten every poll, so a reader's copy is only ever as
fresh as the last drain — and **a lobby page that has stopped being rewritten
looks exactly like a lobby where nothing is happening.** So it now carries a
`meta refresh` on `lobby_page.PAGE_REFRESH` (15s) *and* counts up from its own
write in the reader's browser, turning warm and saying `STALE` past three
intervals. A timestamp alone did not do this job: it is UTC, the reader is
not, and an hour-old page carries a perfectly plausible-looking time.

The count is against the *server's* clock, so a badly skewed browser clock can
call a live page stale. That is the direction to be wrong in; the other one
hides a dead host.

`--live` is served and `--out` is not, which is why the handover copies
rather than links: `--out` holds the seeds of games that are **still
running**, and serving it would publish them. A copy under `--live` is a
finished game only, put there by the same call that publishes the sidecar.
**The live directory is the archive.** A game does not get copied anywhere to
become watchable: it ends, its board and reveal land beside the live file
nobody stopped polling, and `index.json` lists it. The viewer reads that index
— `?games=<url>`, or automatically from the directory of whatever `?live=` was
pointed at — so the URL a spectator watched a game on is the URL its recording
lives at afterwards. `games/replays/` in the repository is a different thing
and stays that way: a handful of games kept in git *deliberately*, with a
commit behind each, rather than everything this host has ever played.

**Retention is `--keep 100 --keep-best 1000`**, decided by Gal 2026-08-28,
superseding the paragraph below it. A game survives if it is among the latest
100 played **or** among the best 1000; the ledger row survives either way, so
what is at stake is whether a game can still be watched. `--keep-best` needs
`--ledger`, because a game's score lives in the record of every game rather
than in its own file, and a ledger that cannot be read prunes nothing.

When a game is let go, its copies under `--live` go with it and the archive
index keeps a row saying it was played (`kept: false`, with the date). The
viewer reads that row and says so. **Do not add a timer over the live
directory**: eviction happens in the runner, where the ranking rule already
lives, or it happens in two places that will disagree.

*Superseded, kept for its reasoning:*

**Nothing under `--live` is ever pruned, and `--keep` should stay unset.**
Decided by Gal, 2026-08-28: *all games are saved forever*. A spectator link,
once handed out, keeps working — and pruning a live copy breaks the link
silently, because the `finished` block goes on naming files that are no longer
there. The host operator asked for pruning to be wired into the runner rather
than left to a timer on the box, on the sound ground that a retention policy
split across two repositories is one nobody can find; the policy turned out to
be *keep everything*, which is why it is written here rather than built. **Do
not add a timer over the live directory.**

The bill for that is small and measured: after one game, `results` is 108K and
the live directory is 28K (host operator, 2026-08-28), so a thousand games is
about 25MB. If a disk ever does fill, suspect something else first — the one
incident so far, 87% to 91% overnight, was a Docker build cache and not the
island.

**Point `--page` into a directory of its own**, not at the state directory.
Everything else in the table above is either private while a game is running
(`--state` holds seeds already drawn) or published only after it ends
(`--out`), so a web root that contains them publishes a live game's seeds. A
directory holding nothing but the page is a mistake that cannot be made; the
running host does this, mounting `~/island/public/` with the state files one
level up, and refuses any path but `/` and `/index.html` besides.

**The live directory also needs `Access-Control-Allow-Origin`.** The viewer is
published on GitHub Pages and fetches the live file from *this* host, so the
request is cross-origin and the browser refuses it without the header — and
what a spectator sees when it is missing is an empty island and a failed poll,
not an error that names its own cause. Raised by the host operator, 2026-08-28,
who had already worked it out and shipped it; nothing here said so.

**Which means the live directory has to be let through that refusal.** A host
serving only `/` and `/index.html` serves no spectator anything, whatever
`--live` writes. Allow `/live/` under the same root — it is the one other
place a spectator reads from, it holds only what was on the board plus games
that are already over, and it is the same argument as the page: published on
purpose, private things one level up. Serve it `Cache-Control: no-store` too;
a cached live file is a game a spectator watches minutes behind, and a cached
`finished` block is an ending that never arrives.

The running host does all of this in Caddy, and this is the actual block rather
than a description of one (host operator, 2026-08-28):

```
handle /robots.txt { respond "User-agent: * / Allow: /" }
handle /live/* {
    header Access-Control-Allow-Origin "https://gald33.github.io"
    header Cache-Control "no-store"
    file_server
}
@page path / /index.html
handle @page { header Cache-Control "no-store"; file_server }
handle { respond "not found" 404 }
```

Two paths by name, one prefix by directory, everything else 404. What makes
that safe is not the shape of the config but the checks that were run against
it: `lobby.json`, `results/`, a `../` traversal and a decoy file dropped into
the public directory were each confirmed to 404 through the public URL, the
mount is read-only, and the seeds live one directory *above* what is mounted.
Re-run those four checks after any change to this block — "be careful with the
web root" is not a check.

## Saying something in the room, and knowing it arrived

Anything an operator or an agent posts to a Switchboard room — a note to the
other side, a status line, a question — is worth sending the way
[`switchboard-a-post-that-printed-is-not-a-post-that-landed.md`](../switchboard-a-post-that-printed-is-not-a-post-that-landed.md)
describes: **body before options, body in a file, and read the channel back.**
`posted #45995 to coord` means a request succeeded, not that anybody can read
what you meant to say.

## Whether it is healthy

- **The page's timestamp**: it is rewritten every poll (a few seconds), so a
  page more than a minute old means the process is not polling. **Serve it
  `Cache-Control: no-store`** — a cached copy makes this check, and the key
  check below, report stale truth to everyone but the origin. **This stopped
  being only a freshness question when the page grew a start block**: the
  prompt on it carries the key an entrant will use, so a cached page does not
  merely look stale, it hands somebody a key that no longer opens anything.
  Raised by the host operator, 2026-08-27. The file is
  replaced by atomic rename, so no lock, retry or read-repair is needed.
- **`LOBBY holding this channel: <token>`** on the lobby board, posted at
  startup. **This is not a count of processes, and reading it as one is a
  mistake this document used to make.** Every restart posts another line with
  a fresh token, so two lines fifteen minutes apart from the same agent id are
  one process that restarted, not two processes running. What a second *live*
  holder actually looks like is the other process saying **`stands down`** on
  the board — that line, not the count of holder lines, is the symptom. The
  reliable check is the machine's own: exactly one `run_game` process. A
  `pgrep -f run_game` matches its own command line and reports two, so count
  with `ps -eo args | grep -c "[p]ython -m games.island.run_game"`.
- **The key on the page's own footer.** The page states the key the process
  is listening under. A lobby holding any other key is **the failure with no
  other symptom**: the unit stays `active`, the page keeps a fresh timestamp,
  exactly one process runs, and every entrant is unheard — a workspace key
  that does not match is silence, not an error. All three signals above
  describe this process; only this one describes whether anybody can reach it.
  Compare the footer against [`ENTER.md`](ENTER.md). **Rotating the key means
  changing both in the same change**, and a host that hardcodes the key in a
  unit file has a third place to change.
- **`lines were posted here that this lobby never read`** on the board means
  the board outran the read window between two polls. It is said out loud
  rather than passing as quiet, and it means the poll interval is too long
  for how busy the room is.

## What it writes forever, and what to do about it

The board and the replay of a finished game are the durable artefacts — the
hub keeps a board about an hour, after which this copy is the only one — so
`--out` grows by one record, one board and one reveal per game, tens of
kilobytes each. `--ledger` grows by one row per round and is small, and
`viewer/scores.py:parts` already reads a rolled-off `ledger-2026-08.jsonl.gz`
beside the live file, so rotating it by month is supported and needs nothing
new here.

`--keep N` prunes finished games' raw output, oldest first, once they are in
the ledger: **the ledger row survives, so the game is still counted and still
in every denominator** — what goes is the board and reveal files it points at.
It is a count of most-recent and has no notion of rank.

**A replay worth keeping is also copied by hand into `games/replays/`** and
lives in git, one commit each, exactly as it did before any of this ran.
Pruning `--out` never touches those, and neither does anything else here:
that directory is a deliberate handful, not a mirror of what a host holds.

## What it costs to leave running

**Money, not machine** — for CPU, memory and bandwidth see "What a game and an
NPC actually cost" above; the two are different bills and only this one grows
with strangers.

The lab pays for the manager of every table that settles, and `OPEN` costs its
author nothing — so the bill is bounded by `--max-games` (how many run at
once) and by the lobby's own cap of two tables *forming* per peer. Neither
bounds a determined stranger's total over a day; if that becomes real, the cap
to add is per-day and it belongs in the lobby, not here.

## What this host is not

It is not a manager anybody has to trust. The seed is drawn by commit–reveal
from every seat's nonce and is recomputable from the board afterwards; the
private half is sealed by Switchboard to each seat; every line says which key
signed it; and `python -m games.island.verify <board.json>` re-checks the draw,
the authorship, the production, the exchange and the clock. What a single host
still cannot prove is what it **left out** — that needs a second party in the
room, and there now is one. The lobby runner mints every table's room key, so
it archives every game it deals: `archive-<workspace>.json`, read live and
published with the reveal. For a table a **stranger** manages that copy is an
independent witness and is condition 3 met; for a table **this process**
manages it is a second file, because two clients in one process are not two
parties — and each archive says which it is rather than leaving a reader to
assume. See `games/island.md`.
