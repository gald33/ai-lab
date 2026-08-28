"""A live game, readable by a spectator who is not in the room.

**This needs nothing from Switchboard, which is a correction.** `games/island.md`
concluded that watching a live game required a read-only invite, because an
invite is a read-write credential and a spectator link would hand out the
ability to post. The credential half of that is still true. The conclusion
drawn from it was not: *reading a room requires no credential at all if
somebody who already holds one does the reading.*

The manager is in the room and reads it every drain. So it writes what it read
to a file, and the viewer -- which already takes `?live=<url>` and polls it
with a plain `fetch` -- reads that. No invite leaves the host, nothing a
spectator holds can write, and no Switchboard feature is required.

**Only the channel, never the private half.** A trader's capacities, tastes
and plans travel sealed to one peer and are delivered to that peer's own
channel; they are not on the board and so are not here. That is not a
redaction step to be maintained -- it is a property of where the two kinds of
message live, which is why this file does not have to be careful. What a
spectator sees is exactly the board, which is exactly what the traders see.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

#: What the viewer's `rowsFromState` reads. Kept to that shape deliberately:
#: it is the same contract Switchboard's own browser room-reader returns, so a
#: page can take either source without knowing which it got.
def snapshot(client, channel: str, *, limit: int = 300,
             names: dict[str, str] | None = None) -> dict:
    """The channel as the viewer wants it: `{messages: [...]}`.

    Read fresh from the hub rather than accumulated, so a spectator sees the
    board as it stands and not one process's memory of it.

    **`names` is the manager's alias, and without it a live game is drawn
    silent.** A hub names a line by the room's agent id -- `scout-v2` -- while
    the schedule seats `T1..Tn` and every receipt is written in those seat
    names. The viewer takes its cast from the schedule, so an author it has
    never heard of is not one of the traders: `reducer.js` reads those lines as
    the manager's, they classify as `unknown`, and nothing is drawn. The whole
    visible symptom is that **nobody talks during a live game and everybody
    talks in the replay** -- which is exactly where the two differ, because
    `run_game.save_board` has always mapped peer to seat through this same
    alias and this did not.

    So the seat name goes in `from.name`, which is the field
    `rowsFromState` already prefers, and the raw id stays in `from.id`: a
    spectator's file loses nothing, and the live board finally names its
    authors the way the recording of it does.

    The mapping is given whole rather than assembled here -- the manager's own
    id included, if the caller wants it named -- because this module knows
    about a board and a file and deliberately nothing about seats.
    """
    rows = sorted(client.history(channel, limit=limit),
                  key=lambda r: r.get("seq", 0))
    seats = dict(names or {})

    def who(peer: str) -> dict:
        seat = seats.get(peer)
        return {"id": peer, **({"name": seat} if seat else {})}

    return {
        "channel": channel,
        "messages": [{"seq": m.get("seq"),
                      "created_at": m.get("created_at"),
                      "channel": channel,
                      "from": who(str(m.get("from") or "?")),
                      "body": m.get("body")}
                     for m in rows if isinstance(m.get("body"), str)],
    }


def write(client, channel: str, path: Path, *, limit: int = 300,
          names: dict[str, str] | None = None) -> Path:
    """Replace the spectator's file atomically, so nobody reads half a board."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(
        snapshot(client, channel, limit=limit, names=names)) + "\n")
    tmp.replace(path)
    return path


#: The archive's own listing, beside the games it lists. A spectator's page
#: reads this to know which finished games are watchable, so a game becomes a
#: recording by being written here rather than by anybody copying it anywhere.
INDEX = "index.json"


def _remember(directory: Path, label: str, copies: dict, standing: dict | None,
              facets: dict | None, when: str) -> None:
    """Add this game to the live directory's index, or replace its entry.

    **The live directory is the archive.** Nothing here is ever pruned (see
    `HOSTING.md`, "all games are saved forever"), so the file a spectator was
    polling while the game ran is the file that keeps its replay afterwards --
    and the only thing standing between "a game ended" and "a recording anybody
    can watch" was a listing. This is that listing.

    Keyed by label and rewritten whole, so re-finishing a game replaces its row
    rather than doubling it, and newest first because with many games kept the
    interesting one is the one that just ended.
    """
    index = directory / INDEX
    try:
        rows = json.loads(index.read_text()).get("games", [])
    except (OSError, ValueError):
        rows = []
    rows = [r for r in rows if r.get("label") != label]
    rows.append({"label": label, "finished_at": when, "kept": True,
                 "board": copies["board"], "reveal": copies["reveal"],
                 "live": f"{label}.json",
                 **({"standing": standing} if standing else {}),
                 **({"facets": facets} if facets else {})})
    rows.sort(key=lambda r: r.get("finished_at") or "", reverse=True)
    tmp = index.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"games": rows}, indent=1) + "\n")
    tmp.replace(index)


def forget(directory: Path, label: str) -> list[Path]:
    """Delete a game's copies, and leave a row saying it was played.

    Retention keeps the latest and the best, which means **a game can be
    evicted by a later, better game**: a link handed out today stops working on
    a day nobody touched that game, for a reason that has nothing to do with
    it. Raised by the host operator, 2026-08-28, as the thing that makes merit
    retention worse than an expiry date -- an expiry can at least be stated in
    advance.

    So the files go and the row stays, with `kept: false` and the date it went.
    A page that asks for an evicted game gets an index that says *this game was
    played and is no longer kept*, which is a different sentence from a 404 and
    from silence. The row is small; the board and reveal were the bulk.
    """
    index = directory / INDEX
    try:
        state = json.loads(index.read_text())
    except (OSError, ValueError):
        return []
    rows = state.get("games", [])
    row = next((r for r in rows if r.get("label") == label), None)
    if row is None or row.get("kept") is False:
        return []

    gone: list[Path] = []
    for name in (row.get("board"), row.get("reveal"), row.get("live")):
        if not name:
            continue
        path = directory / name
        if path.exists():
            path.unlink()
            gone.append(path)
    row["kept"] = False
    row["dropped_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for key in ("board", "reveal", "live"):
        row.pop(key, None)
    tmp = index.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"games": rows}, indent=1) + "\n")
    tmp.replace(index)
    return gone


def finish(path: Path, *, board: Path, reveal: Path,
           standing: dict | None = None, facets: dict | None = None) -> dict:
    """Say on the spectator's own file that the game is over, and where to read it.

    A live round shows no score, and cannot: utility needs a taste and tastes
    are never on the board. So the moment a spectator most wants -- *how did
    they do?* -- is exactly the moment the live file stops being able to
    answer, and until now the answer lived only in `--out`, which is not
    served, under a filename nobody watching was given.

    This is the handover. At the last bell the seed is disclosed anyway
    (`run_game.publish`), so the two files that disclose it are copied beside
    the live one and the live file grows a `finished` block pointing at them.
    A page polling the board sees the game end, reads the reveal, and can show
    the scores and the replay of what it just watched.

    **The copy happens before the pointer.** A poll that lands in between must
    see a game still running, never a pointer at a file that is not there yet.

    Nothing here is published a moment earlier than `--out` publishes it: the
    same rule ("a seed still in play is not replayable by anyone") is what
    decides *when* this is called, and the caller is the last bell.

    `standing` is the game's **official** score and place, and it is passed in
    rather than worked out here: it comes from `viewer/scores.py:standing`,
    reading the ledger this game has just been written into. One ranking rule,
    in the file that owns it. A page that did its own arithmetic on the reveal
    would be a second scoring surface, and two official scores for one game is
    worse than a slower one.
    """
    stem = path.name.split(".")[0]
    copies = {}
    for kind, src in (("board", board), ("reveal", reveal)):
        dst = path.parent / f"{kind}-{stem}.json"
        tmp = dst.with_suffix(".json.tmp")
        tmp.write_bytes(src.read_bytes())
        tmp.replace(dst)
        copies[kind] = dst.name

    state = json.loads(path.read_text()) if path.exists() else {}
    state["finished"] = dict(copies)
    if standing is not None:
        state["finished"]["standing"] = standing
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state) + "\n")
    tmp.replace(path)

    # Last, and only once the game is genuinely readable: the index is what a
    # page believes. A row pointing at files that are not there yet would be
    # the same mistake as a pointer written before its copies, one level up.
    _remember(path.parent, stem, copies, standing, facets,
              datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return copies
