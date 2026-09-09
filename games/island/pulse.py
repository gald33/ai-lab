"""Did the launch work? Counted from the record, with no tracker anywhere.

    python -m games.island.pulse
    python -m games.island.pulse --json

**Nothing here is a page view**, and that is the design rather than a
limitation. The brief that asked for this wanted landing visitors, brief
copies, lobby joins, games started, games completed, unique entrants and repeat
attempts. Six of those seven are already written down somewhere this repo
controls -- a `JOIN` is a line on a board, a finished game is a ledger row, and
a repeat attempt is the same entrant appearing twice in that file. Only "how
many people looked at the page" needs a tracker, and it is the least
interesting of the seven.

So this counts what is already recorded, and says plainly what it cannot see.
That is not a privacy compromise dressed up as a feature: a script on the
landing page would have to be loaded by every reader, and what it would buy is
one number that does not answer the question the launch is actually asking,
which is **did anybody's agent play, and did anybody come back**.

What it reads:

- **the ledger** -- games completed, who played, on what, how often, and
  whether anybody played twice. `viewer/scores.py` owns it;
- **the live hub** -- whether the lobby is up, and what is on its board right
  now. Read-only, through the same catch-up endpoint the viewer uses, without
  registering or advancing a cursor. `--offline` skips it;
- **the record host** -- every game it has published, against every game the
  committed ledger knows. **This is the check that found the launch's worst
  defect** and the reason it is here: on 2026-09-06 the host had scored games
  through that day and the committed ledger's newest was 2026-08-29, so the
  published scoreboard was eight days stale and every game ever played on the
  open table was missing from it. A visitor saw a board whose newest game
  predated the launch. Nothing said so, because the ledger is a file somebody
  commits and a file nobody commits looks exactly like a game nobody played.

What it cannot see, and says so rather than leaving a blank:

- how many people opened a page;
- how many copied the brief;
- how many pasted it into an agent and got no further.

The gap between "briefs copied" and "JOINs on the board" is the one number
that would genuinely help, and it is the one that needs the tracker. It is
deliberately not here yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ISLAND = Path(__file__).resolve().parents[2] / "experiments" / "does-a-content-free-protocol-help"
sys.path.insert(0, str(_ISLAND / "viewer"))

import scores  # noqa: E402

#: The published coordinates. Same four as `ENTER.md`, and the key protects
#: nothing -- see that document. Read-only use only, here.
HUB = "https://switchboard.lucille-ai.com"
TOKEN = "sb_public_lucille"
WORKSPACE = "island-lobby"
KEY = "Z822U5v1WFyeOEJUeLchMgLED-VgI_0chD4OjmRxej0"
CHANNEL = "lobby"

#: Where the host publishes a finished game. `HOSTING.md` names it, and the
#: viewer already reads `reveal-<room>.json` off it at the end of a watched
#: game.
RECORD = "https://record.lucille-ai.com/games"

#: The lab's own entrants, so "did a stranger play" can be asked separately
#: from "did anybody play". Not a filter -- nothing is dropped -- just a label,
#: and it is a prefix list rather than a name list because a baseline is
#: allowed to be run more than once.
OURS = ("npc-", "baseline-", "t-one", "t-two", "trader-b", "claude-haiku",
        "scout-v2")


def ours(who: str) -> bool:
    return any(who.startswith(p) for p in OURS)


def from_the_ledger(rows: list[dict] | None = None) -> dict:
    """Everything the record already knows, which is most of it."""
    rows = rows if rows is not None else scores.load()
    played = scores.games(rows)
    ranked = [g for g in played if scores.is_ranked(g)]

    # A game a stranger could have opened -- the format the door hands out.
    on_open = [g for g in played
               if g.get("level") and tuple(g["level"]) == scores.OPEN_TABLE]

    # Who played, and how often. **The interesting product number is the
    # repeat**: somebody who played, disliked their score, changed something
    # and came back. It is knowable from names alone and needs no tracker.
    appearances: Counter[str] = Counter()
    first_seen: dict[str, str] = {}
    for game in sorted(played, key=lambda g: g.get("played_at") or ""):
        for who in set(game["players"].values()):
            appearances[who] += 1
            first_seen.setdefault(who, game.get("played_at") or "")

    strangers = {w: n for w, n in appearances.items() if not ours(w)}
    repeats = {w: n for w, n in strangers.items() if n > 1}

    # What kinds of agent turned up, off the labels a JOIN carried. Absent for
    # every game played before the labels existed, which is most of them.
    harnesses: Counter[str] = Counter()
    owners: Counter[str] = Counter()
    for game in played:
        for said in (game.get("told") or {}).values():
            if said.get("harness"):
                harnesses[said["harness"]] += 1
            if said.get("by"):
                owners[said["by"]] += 1

    week = datetime.now(timezone.utc) - timedelta(days=7)
    recent = [g for g in played
              if (g.get("played_at") or "") >= week.isoformat()]

    return {
        "games_completed": len(played),
        "games_ranked": len(ranked),
        "games_on_the_open_table": len(on_open),
        "open_table_held": bool([g for g in on_open if scores.is_ranked(g)]),
        "games_last_7_days": len(recent),
        "entrants_all": len(appearances),
        "entrants_not_ours": len(strangers),
        # The one worth watching.
        "entrants_who_came_back": len(repeats),
        "repeat_attempts": {w: n for w, n in sorted(
            repeats.items(), key=lambda kv: -kv[1])},
        "harnesses_declared": dict(harnesses.most_common()),
        "owners_declared": dict(owners.most_common()),
        "ledger_rows": len(rows),
    }


def from_the_hub() -> dict:
    """Is the door open, and is anything happening at it?

    Read-only and unregistered, the way the viewer and the lobby page read: no
    presence is announced and no cursor is advanced, so running this cannot
    look like an entrant and cannot consume anybody's message.
    """
    try:
        from switchboard import Client
        from switchboard.config import ClientConfig
    except ImportError:
        return {"reachable": False, "why": "no switchboard client installed"}

    client = Client(ClientConfig(url=HUB, url_source="explicit", token=TOKEN,
                                 workspace=WORKSPACE, key=KEY),
                    agent_id="pulse-readonly")
    try:
        agents = client.agents()
        stats = client.stats()
        board = client.history(CHANNEL, limit=200)
    except Exception as exc:                               # noqa: BLE001
        return {"reachable": False, "why": f"{type(exc).__name__}: {exc}"}

    present = {a.get("name") for a in agents if not a.get("stale")}
    lines = [str(m.get("text") or m.get("body") or "") for m in board]
    return {
        "reachable": True,
        # The two processes that have to be alive for anybody to get in. The
        # page being up says nothing about this: the lobby is a separate
        # process, and a served page with a dead lobby looks exactly like a
        # quiet one.
        "lobby_running": "lobby" in present,
        # `or ""` and not `.get("task", "")`: the hub sends the key with a
        # null value for an agent that registered without a task, and a
        # default only applies to a missing key. On 2026-09-08 one such agent
        # joined the room and `pulse` stopped running entirely --
        # AttributeError on None -- which is the one tool that reports whether
        # the ledger has drifted. The idiom two lines up already had this
        # right; this line did not.
        "runner_running": any((a.get("task") or "").startswith("running tables")
                              for a in agents if not a.get("stale")),
        "on_the_roster": sorted(n for n in present if n),
        # The hub keeps a room about an hour, so these are "right now" and not
        # "ever". A zero here is not a zero since launch.
        "messages_retained": stats.get("messages"),
        "opens_on_the_board": sum(1 for x in lines if x.startswith("OPEN")),
        "joins_on_the_board": sum(1 for x in lines if x.startswith("JOIN")),
        "board_lines": len(lines),
    }


def _fetch_index() -> list[dict]:
    """The host's own list of published games.

    Split out so the comparison above can be tested without reaching the
    network -- and so the two reasons this call is fussy stay in one place.

    A named agent and, where one is configured, the environment's CA bundle.
    Bare `urlopen` got a flat 403 here while `curl` on the same URL got 200:
    the default `Python-urllib/3.x` user agent is refused by what sits in
    front of the host. Worth the lines, because a 403 read as "the host is
    down" is the same class of mistake as everything else this file exists to
    catch -- a silent nothing wearing the clothes of a real answer.
    """
    import os
    import ssl
    import urllib.request

    bundle = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    context = ssl.create_default_context(cafile=bundle) if bundle else None
    request = urllib.request.Request(f"{RECORD}/index.json",
                                     headers={"User-Agent": "island-pulse"})
    with urllib.request.urlopen(request, timeout=30, context=context) as fh:
        index = json.load(fh)
    return index if isinstance(index, list) else (
        index.get("games") or index.get("rows") or [])


def against_the_record_host(rows: list[dict] | None = None) -> dict:
    """Games the host has published, against games the ledger has recorded.

    **The ledger is committed by hand**, so it goes stale silently: the host
    scores a game, publishes its board and reveal, and the board a visitor
    reads knows nothing about it until somebody runs `git add`. There is no
    error anywhere in that, which is what makes it worth a check -- a stale
    scoreboard and an unplayed game look identical from outside.

    This only ever *reports*. It deliberately does not reconstruct the missing
    rows: a reveal carries the seed and the trajectory but not `arm`, `npcs`,
    `hands` or `company`, and those are exactly the fields that decide whether
    a game ranks. Rebuilding them by guess would put a practice game in a
    ranked game's clothes, which is the one thing this repo will not do. The
    host already computed them correctly; the fix is to commit its ledger.
    """
    rows = rows if rows is not None else scores.load()
    known = {r.get("workspace") for r in rows}
    # A named agent and, where one is configured, the environment's CA bundle.
    # Bare `urlopen` got a flat 403 here while `curl` on the same URL got 200:
    # the default `Python-urllib/3.x` user agent is refused by what sits in
    # front of the host. Worth the two lines, because a 403 read as "the host
    # is down" is the same class of mistake as everything else this file
    # exists to catch -- a silent nothing that looks like a real answer.
    try:
        published = _fetch_index()
    except Exception as exc:                               # noqa: BLE001
        return {"reachable": False, "why": f"{type(exc).__name__}: {exc}"}
    missing = []
    for item in published:
        standing = item.get("standing") or {}
        workspace = standing.get("workspace") or item.get("workspace")
        if workspace and workspace not in known:
            missing.append({
                "label": item.get("label"),
                "workspace": workspace,
                "finished_at": item.get("finished_at"),
                "capture": standing.get("capture"),
                "level": standing.get("level"),
                "ranked": standing.get("ranked"),
            })
    newest_here = max((r.get("played_at") or "" for r in rows), default="")
    newest_there = max((i.get("finished_at") or "" for i in published), default="")
    return {
        "reachable": True,
        "published": len(published),
        "missing_from_the_ledger": missing,
        "newest_in_the_ledger": newest_here[:19],
        "newest_on_the_host": newest_there[:19],
    }


#: Said out loud rather than left as an absent key. A blank in a report reads
#: as a zero, and these are not zeroes -- they are things nothing here measures.
BLIND = [
    "page views (landing, scoreboard, result pages)",
    "briefs copied from the lobby",
    "agents that were handed a brief and never reached the board",
]


def report(data: dict) -> str:
    led, hub = data["ledger"], data["hub"]
    out = ["THE ISLAND -- pulse", ""]
    out.append("Played (from the ledger, which is the record)")
    out.append(f"  games completed         {led['games_completed']}")
    out.append(f"  of those, ranked        {led['games_ranked']}")
    out.append(f"  on the open table       {led['games_on_the_open_table']}"
               f"  ({'held' if led['open_table_held'] else 'UNHELD'})")
    out.append(f"  in the last 7 days      {led['games_last_7_days']}")
    out.append("")
    out.append("Who")
    out.append(f"  entrants, all           {led['entrants_all']}")
    out.append(f"  entrants, not ours      {led['entrants_not_ours']}")
    out.append(f"  came back for another   {led['entrants_who_came_back']}")
    for who, n in list(led["repeat_attempts"].items())[:8]:
        out.append(f"      {who:<24} {n} games")
    if led["harnesses_declared"]:
        out.append("  harnesses declared      "
                   + ", ".join(f"{k} x{v}" for k, v
                               in led["harnesses_declared"].items()))
    out.append("")
    out.append("The door (right now -- the hub keeps a room about an hour)")
    if not hub.get("reachable"):
        out.append(f"  UNREACHABLE: {hub.get('why')}")
    else:
        out.append(f"  lobby process           "
                   f"{'up' if hub['lobby_running'] else 'DOWN'}")
        out.append(f"  table runner            "
                   f"{'up' if hub['runner_running'] else 'DOWN'}")
        out.append(f"  lines on the board      {hub['board_lines']}"
                   f"  ({hub['opens_on_the_board']} OPEN, "
                   f"{hub['joins_on_the_board']} JOIN)")
    out.append("")
    out.append("The published board, against what the host has actually scored")
    rec = data.get("record") or {}
    if not rec.get("reachable"):
        out.append(f"  UNREACHABLE: {rec.get('why')}")
    else:
        missing = rec["missing_from_the_ledger"]
        out.append(f"  games published by the host   {rec['published']}")
        out.append(f"  newest in the ledger          {rec['newest_in_the_ledger']}")
        out.append(f"  newest on the host            {rec['newest_on_the_host']}")
        if missing:
            out.append(f"  MISSING FROM THE LEDGER       {len(missing)}"
                       f"  -- the published board does not know about these")
            for m in missing[:10]:
                cap = ("     -" if m["capture"] is None
                       else f"{m['capture']:>6.2f}")
                out.append(f"      {str(m['label']):5} {str(m['finished_at'])[:19]}"
                           f" {str(m['level']):14} {cap}"
                           f"  ranked={m['ranked']}")
            out.append("  The host computed these correctly. Commit its "
                       "ledger; do not rebuild them from the reveals.")
        else:
            out.append("  nothing missing -- the board is current")
    out.append("")
    out.append("Not measured here, and not zero:")
    out.extend(f"  - {x}" for x in BLIND)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Did the launch work?")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    ap.add_argument("--offline", action="store_true",
                    help="the ledger only; do not reach the hub")
    args = ap.parse_args(argv)

    data = {"ledger": from_the_ledger(),
            "hub": {"reachable": False, "why": "not asked"} if args.offline
            else from_the_hub(),
            "record": {"reachable": False, "why": "not asked"} if args.offline
            else against_the_record_host()}
    print(json.dumps(data, indent=1) if args.json else report(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
