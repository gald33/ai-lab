"""A transcript in, a settled outcome out. No hub, no network, no model.

This is the piece `games/hue-and-cry.md` has been calling for since the
document began -- *"a pure function from a board transcript to a settled
outcome: were the clues true, did she move along a route she had, did the
commitments open, was the arrest right, what was taken"* -- and the reason
it is the first thing to build: **it makes this design's central claim,
deterministic judging, something you can run instead of something the
document asserts.**

    python3 games/hue-and-cry/settle.py        # settle a demonstration game

Everything it needs is the transcript and the seed she published at the end.
It talks to nothing, costs nothing, and gives the same answer a year later.

WHAT IT REFUSES TO DO
=====================

**It never repairs a line.** A malformed `CLUE` is rejected with a reason and
does not move her; it is not read as the plausible line it nearly was.
CLAUDE.md forbids that in the same sentence it forbids inventing a
production plan, and the temptation here is real, because a rejected clue is
usually a typo rather than a cheat.

**It never asks anybody what happened.** Self-reports are not evidence, with
one exception the design argues for at length and which is implemented as
stated: her report of her own capture is conclusive, because it ends the
game against her and nobody lies in that direction.

THE GRAMMAR IS LARGER THAN THE DOCUMENT SAYS, AND THAT IS A FINDING
===================================================================

`games/hue-and-cry.md`, "The grammar", says: *"The manager recognises two
formatted lines and nothing else"*, listing `CLUE` and `TAKE`. But
"Which makes the adversary the referee" then requires her to publish a
commitment before, publish the seed after, report her own capture, and
refute a searcher's claim of one -- and "No seed, no win" makes the reveal
load-bearing on the outcome.

Those are five more lines. **Writing the settler is what turned that from a
sentence into a contradiction**, which is the argument for writing settlers
early. Resolved by taking the document's *reasoning* over its summary, since
every one of the five is argued for somewhere and the "two lines" claim is
only asserted:

    in the lobby
      COMMIT <hex>              hers, before: what she will play
      OPEN <workspace>          hers: a campaign, and where it starts
      SEED <hex>                hers, after: the reveal. No seed, no win.

    in a landmark room
      CLUE <hint> <workspace>   hers: a hint and where she went
      TAKE                      hers: the room's treasure
      CAUGHT                    hers: conclusive, and ends it
      CLAIM                     a searcher's: refutable
      REFUTE                    hers: answers a CLAIM

`CLAIM` is the one line a searcher may post, and it does not break
*"searchers say nothing at all"*: that section is a claim about the optimal
strategy -- nothing they say helps them -- rather than a prohibition. A
claim that is refuted leaves both statements in the record, said out loud
once, and **costs the game its ranking**, which is CLAUDE.md's rule for the
weaker thing applied to a disputed capture.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import carmel as C  # noqa: E402
import treasures as T  # noqa: E402
from descriptors import all_descriptors  # noqa: E402
from gazetteer import kinship  # noqa: E402
from secret_matrix import _prf, hints_for, replays, token_for  # noqa: E402

LOBBY = C.LOBBY


class Line:
    """One record on a board: which room, who wrote it, what it said.

    `who` is a signing key in the real thing. Here it is any hashable, and
    the only thing settlement asks of it is whether it is hers.
    """

    __slots__ = ("room", "who", "text")

    def __init__(self, room: str, who: str, text: str):
        self.room, self.who, self.text = room, who, text

    def __repr__(self) -> str:
        return f"Line({self.room!r}, {self.who!r}, {self.text!r})"


def settle(transcript: list[Line], her: str,
           threshold: int = C.REPUTATION_TO_WIN) -> dict:
    """Read the board, decide the game.

    Returns the outcome, what she took, and a verdict on every line that
    claimed to settle something -- including the rejected ones and why,
    because a settler that silently drops what it could not parse is a
    settler nobody can audit.
    """
    world = None
    verdicts: list[dict] = []
    commit = seed = None
    at = None                       # where she is, once OPEN names it
    taken: list[dict] = []
    caught = False
    claims: list[Line] = []
    refuted: list[Line] = []

    def reject(line: str, why: str) -> None:
        verdicts.append({"line": line, "ok": False, "why": why})

    def accept(line: str, what: str) -> None:
        verdicts.append({"line": line, "ok": True, "why": what})

    for line in transcript:
        parts = line.text.split()
        if not parts:
            continue
        verb, args = parts[0], parts[1:]

        if verb not in ("COMMIT", "OPEN", "SEED", "CLUE", "TAKE", "CAUGHT",
                        "CLAIM", "REFUTE"):
            continue                # talk, and talk settles nothing

        mine = line.who == her
        if verb == "CLAIM":
            if mine:
                reject(line.text, "a claim of capture is a searcher's line")
            else:
                claims.append(line)
            continue
        if not mine:
            reject(line.text, f"{verb} is hers and this is not her key")
            continue

        if verb == "COMMIT":
            if len(args) != 1:
                reject(line.text, "COMMIT takes one digest")
            elif line.room != LOBBY:
                reject(line.text, "COMMIT belongs in the lobby")
            elif commit is not None:
                reject(line.text, "already committed")
            else:
                commit = args[0]
                accept(line.text, "committed")

        elif verb == "SEED":
            if len(args) != 1:
                reject(line.text, "SEED takes one value")
            elif line.room != LOBBY:
                reject(line.text, "SEED belongs in the lobby")
            elif commit is None:
                reject(line.text, "a seed with nothing committed to")
            else:
                try:
                    candidate = bytes.fromhex(args[0])
                except ValueError:
                    reject(line.text, "SEED is not hex")
                    continue
                if not replays(candidate, commit):
                    reject(line.text, "the seed does not open the commitment")
                else:
                    seed = candidate
                    world = C.Map(seed)
                    accept(line.text, "the commitment opens")

        elif verb == "OPEN":
            if len(args) != 1:
                reject(line.text, "OPEN takes one workspace")
            elif line.room != LOBBY:
                reject(line.text, "OPEN belongs in the lobby")
            elif at is not None:
                reject(line.text, "a campaign is already open")
            else:
                at = args[0]        # a token; resolved once the seed is out
                accept(line.text, "campaign open")

        elif verb == "CLUE":
            if len(args) != 2:
                reject(line.text, "CLUE takes a hint and a workspace")
            else:
                taken.append({"kind": "clue", "room": line.room,
                              "hint": args[0], "to": args[1],
                              "text": line.text})

        elif verb == "TAKE":
            if args:
                reject(line.text, "TAKE takes nothing")
            else:
                taken.append({"kind": "take", "room": line.room,
                              "text": line.text})

        elif verb == "CAUGHT":
            caught = True
            accept(line.text, "her own capture, which is conclusive")

        elif verb == "REFUTE":
            refuted.append(line)
            accept(line.text, "refutes a claim of capture")

    # --- everything above is parsing. Nothing below can run without the seed.
    if seed is None:
        return {"outcome": "she loses", "why": "no seed, no win",
                "reputation": 0, "verdicts": verdicts, "ranked": True,
                "moves": [], "disputed": bool(claims and refuted)}

    rooms = {token_for(seed, name): name for name in world.descriptors}
    here = rooms.get(at)
    if here is None:
        return {"outcome": "she loses", "why": "no campaign was opened",
                "reputation": 0, "verdicts": verdicts, "ranked": True,
                "moves": [], "disputed": False}

    reputation = 0
    emptied: set[str] = set()
    moves = [here]
    for record in taken:
        if rooms.get(token_for(seed, here)) is None:
            break
        if record["kind"] == "clue":
            if record["room"] != token_for(seed, here):
                reject(record["text"],
                       "posted somewhere she was not standing")
                continue
            destination = rooms.get(record["to"])
            if destination is None:
                reject(record["text"], "the address is not a room this game")
                continue
            if destination not in _exits(world, here):
                reject(record["text"],
                       f"{here} has no route to {destination}")
                continue
            if record["hint"] not in _live(world, destination):
                reject(record["text"],
                       "the hint is not live at where she went")
                continue
            accept(record["text"], f"{here} -> {destination}")
            here = destination
            moves.append(here)
        else:
            if record["room"] != token_for(seed, here):
                reject(record["text"], "a theft where she was not standing")
                continue
            if here in emptied:
                reject(record["text"], "already emptied")
                continue
            prize = world.treasure[here]
            emptied.add(here)
            reputation += prize["reputation"]
            accept(record["text"],
                   f"took {prize['reputation']} at {here}")

    disputed = bool(claims and refuted)
    unrefuted = bool(claims and not refuted)
    if caught:
        outcome, why = "caught", "she reported it herself"
    elif unrefuted:
        outcome, why = "caught", "a searcher claimed it and she did not refute"
    elif reputation >= threshold:
        outcome, why = "she wins", f"{reputation} reputation"
    else:
        outcome, why = "unfinished", "no capture and the threshold not reached"

    return {"outcome": outcome, "why": why, "reputation": reputation,
            "verdicts": verdicts, "moves": moves, "disputed": disputed,
            # A disputed capture is kept and counted and never ranked, which
            # is CLAUDE.md's rule for the weaker thing.
            "ranked": not disputed}


def _exits(world: C.Map, landmark: str) -> list[str]:
    return world.exits(landmark)


def _live(world: C.Map, landmark: str) -> list[str]:
    words = world.descriptors[landmark]
    return [words[i] for i in hints_for(world.seed, landmark, len(words))]


def demonstration(seed: bytes, start: str, world: C.Map,
                  moves: int = 6) -> list[Line]:
    """A transcript of a game she played honestly, so the settler has
    something real to settle. Built from her own policy, not by hand."""
    from secret_matrix import commitment

    trail = C.itinerary(seed, start, world, moves)
    out = [Line(LOBBY, "carmel", f"COMMIT {commitment(seed)}"),
           Line(LOBBY, "carmel", f"OPEN {token_for(seed, start)}")]
    for leg in trail:
        out.append(Line(token_for(seed, leg["from"]), "carmel",
                        f"CLUE {leg['hint']} {token_for(seed, leg['to'])}"))
        if leg["dwell"]:
            out.append(Line(token_for(seed, leg["to"]), "carmel", "TAKE"))
    out.append(Line(LOBBY, "carmel", f"SEED {seed.hex()}"))
    return out


def main() -> None:
    import os

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", help="64 hex characters; random if omitted")
    args = ap.parse_args()
    seed = bytes.fromhex(args.seed) if args.seed else os.urandom(32)

    world = C.Map(seed)
    transcript = demonstration(seed, "Stonehenge", world)
    result = settle(transcript, her="carmel")

    print(f"{len(transcript)} lines on the board\n")
    for v in result["verdicts"]:
        mark = "ok  " if v["ok"] else "NO  "
        print(f"  {mark}{v['line'][:52]:<54}{v['why']}")
    print(f"\n  {result['outcome']} -- {result['why']}")
    print(f"  {len(result['moves'])} rooms, {result['reputation']} reputation,"
          f" ranked: {result['ranked']}")

    print("\n  and the same transcript with one line tampered with:")
    bad = list(transcript)
    for i, line in enumerate(bad):
        if line.text.startswith("CLUE"):
            verb, hint, where = line.text.split()
            bad[i] = Line(line.room, "carmel", f"CLUE far_from_the_equator {where}")
            break
    spoiled = settle(bad, her="carmel")
    for v in spoiled["verdicts"]:
        if not v["ok"]:
            print(f"  NO  {v['line'][:52]:<54}{v['why']}")
    print(f"  {spoiled['outcome']}, {spoiled['reputation']} reputation"
          f" (was {result['reputation']})")


if __name__ == "__main__":
    main()
