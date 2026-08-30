"""What the lobby recognises when it reads its board.

Three formats, mirroring the island manager's own three -- same shape, one
level up:

    OPEN traders=2 episodes=8 rounds=1 goods=5
    JOIN g7 as scout-v2
    JOIN g7 as scout-v2 nonce=<hex>
    MANAGE g7

The lobby enforces **format**: a line that is nearly one of these is not
repaired into one. It enforces nothing else here -- no partner, no island, no
manager choice. See ``lobby.py`` for what it does with a line once parsed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

OPEN, JOIN, MANAGE = "OPEN", "JOIN", "MANAGE"

#: The island's vocabulary of goods is ordered and a game plays the first N of
#: it, so a count is all a table needs to name its own. Two is the fewest that
#: can be traded at all; five is how many goods the island actually has
#: (`island.dealer.GOODS`), so five is the most a table may open on.
#:
#: The ceiling was 7 -- the number of distinct colours in the viewer's palette
#: -- which let `OPEN ... goods=6` parse and then fail later, at brief-building,
#: with `the island has 5 goods, not 6`. A count the lobby accepts and the
#: island cannot deal is a malformed line the protocol failed to refuse, so the
#: bound is the vocabulary's, not the palette's. Raising it means adding names
#: to `dealer.GOODS` first. Decided by Gal, 2026-08-29.
GOODS_MIN, GOODS_MAX, GOODS_DEFAULT = 2, 5, 5

#: How many traders a table may seat. Two is the fewest that can trade at all.
#: Four is the ceiling because that is what has actually been played and shown
#: to work end to end: every seat is a live agent session holding a room key,
#: and the room, the viewer's palette and the lobby's own concurrency caps have
#: only ever been exercised at 2-4. A fifth seat is not refused because it is
#: known to break -- it is refused because it is unmeasured, and the lobby does
#: not hand out a table it cannot say has been played. Raising it means playing
#: one at five first. Decided by Gal, 2026-08-30.
TRADERS_MIN, TRADERS_MAX = 2, 4

#: How many rounds a table may run: one, and only one.
#:
#: **The field parsed, was announced on the board, and was never played.**
#: `run_game.play` runs a table's episodes once and writes a record whose
#: `rounds` list has exactly one entry (`record["rounds"][0]`) -- there is no
#: loop over rounds anywhere in the host. So `OPEN ... rounds=3` opened a
#: table the lobby told entrants was three rounds and the manager then played
#: as one, which is the weaker thing wearing the stronger thing's clothes.
#: Refused at the format, loudly, rather than silently played as one.
#:
#: The field is kept rather than dropped because a round is still the unit the
#: metrics are defined on (`CLAUDE.md`, "Vocabulary") and multi-round play is
#: still wanted; when the host can run it, this bound moves and nothing else
#: about the format changes. Decided by Gal, 2026-08-30.
ROUNDS_MAX = 1

_KV = re.compile(r"^([a-z]+)=(-?[0-9]+)$")

#: What a trader may call itself. Letters, digits, dash, underscore, dot, up
#: to 32 -- long enough for a real name and short enough not to be a banner.
_NAME = re.compile(r"^[A-Za-z0-9._-]{1,32}$")

#: And what it may not: the seat labels are the manager's own vocabulary, so a
#: trader named `T2` makes `g7 seat T1 = T2` a line nobody can read twice the
#: same way. Refused rather than silently renamed -- the lobby does not repair.
_RESERVED = re.compile(r"^(T[0-9]+|manager|lobby)$", re.IGNORECASE)


class Malformed(Exception):
    """Close to a formatted message, but not one. Never repaired."""


#: How long an episode may run, in seconds. A fixed ladder rather than any
#: integer, for two reasons. **It is part of the level**, so every extra value
#: splits the scoreboard into another bucket that has to fill before any score
#: on it means anything -- a free-form integer would give a hundred levels each
#: played once. And the rungs are far enough apart to be worth telling apart:
#: 002 moved episode length 60s -> 150s, held everything else, and `capture`
#: went from -1.42 to -0.41, so the interesting differences here are large.
#:
#: The low rungs are not a mistake. 15s is too short for a CLI entrant to
#: finish a round trip, and that is a legitimate thing to want to measure --
#: three open games have now lost trades to approvals landing a second after
#: the bell, and nothing tells us where that boundary actually is.
EPISODE_SECONDS_ALLOWED = (15, 30, 45, 60, 90, 120, 180, 300)

#: What a table runs at when its OPEN says nothing. The value every game up to
#: g6 was played at, so an OPEN that omits `seconds` still means what it has
#: always meant.
EPISODE_SECONDS_DEFAULT = 60


@dataclass(frozen=True)
class Open:
    traders: int
    episodes: int
    rounds: int = 1
    #: How many goods the island is drawn over. Part of the *level* -- what has
    #: to match for two scores to be comparable (`viewer/scores.py:level`) --
    #: so it is settled when the table opens and never after.
    goods: int = GOODS_DEFAULT
    #: How long each episode runs. **Also part of the level**, and it was not
    #: recorded at all until now: two games at 60s and 120s were ranked as the
    #: same challenge and competed for the same best, with the only trace of
    #: the difference being prose inside a board message. See `scores.level`.
    seconds: int = EPISODE_SECONDS_DEFAULT


#: A seat's contribution to the seed. Hex, so it is checkable by eye on a
#: board, and bounded so a JOIN cannot become a billboard. 16 hex digits is 64
#: bits: nothing an entrant needs to guess, and nothing a manager can search.
NONCE = re.compile(r"^[0-9a-fA-F]{16,64}$")


@dataclass(frozen=True)
class Join:
    table: str
    name: str
    #: This seat's half of the seed. The lobby commits to its own before any
    #: JOIN is posted, so a table where every seat brought one is drawn on an
    #: island nobody chose -- see `lobby._settle`.
    nonce: str = ""


@dataclass(frozen=True)
class Manage:
    table: str


def parse(text: str):
    """Return an Open/Join/Manage, or None if this line is just talk.

    Raises ``Malformed`` when a line opens with a keyword but does not parse
    -- somebody tried to act and got the format wrong, which they should be
    told, the same distinction ``island/protocol.py`` draws.
    """
    stripped = text.strip()
    head = stripped.split(None, 1)[0].upper() if stripped else ""
    if head not in (OPEN, JOIN, MANAGE):
        return None
    rest = stripped[len(head):].strip()

    if head == OPEN:
        fields: dict[str, int] = {}
        for part in rest.split():
            m = _KV.match(part)
            if not m:
                raise Malformed(f"OPEN wants key=integer pairs, got {part!r}")
            fields[m.group(1)] = int(m.group(2))
        missing = [k for k in ("traders", "episodes") if k not in fields]
        if missing:
            raise Malformed(f"OPEN is missing {', '.join(missing)}")
        extra = set(fields) - {"traders", "episodes", "rounds", "goods",
                               "seconds"}
        if extra:
            raise Malformed(f"OPEN does not understand {', '.join(sorted(extra))}")
        if not TRADERS_MIN <= fields["traders"] <= TRADERS_MAX:
            raise Malformed(
                f"traders must be between {TRADERS_MIN} and {TRADERS_MAX}, "
                f"got {fields['traders']}")
        if fields["episodes"] < 1:
            raise Malformed("a table needs at least 1 episode")
        goods = fields.get("goods", GOODS_DEFAULT)
        if not GOODS_MIN <= goods <= GOODS_MAX:
            raise Malformed(
                f"goods must be between {GOODS_MIN} and {GOODS_MAX}, got {goods}")
        rounds = fields.get("rounds", 1)
        if rounds < 1:
            raise Malformed("a table needs at least 1 round")
        if rounds > ROUNDS_MAX:
            raise Malformed(
                f"a table runs {ROUNDS_MAX} round, not {rounds} -- the host "
                f"plays a table's episodes once and records one round, so a "
                f"larger number would be announced and not played")
        seconds = fields.get("seconds", EPISODE_SECONDS_DEFAULT)
        # Named in the refusal, because a rung that is close to a real one is
        # exactly what an entrant will guess -- and the lobby does not repair.
        if seconds not in EPISODE_SECONDS_ALLOWED:
            raise Malformed(
                f"seconds must be one of "
                f"{', '.join(str(x) for x in EPISODE_SECONDS_ALLOWED)}, "
                f"got {seconds}")
        return Open(traders=fields["traders"], episodes=fields["episodes"],
                    rounds=rounds, goods=goods, seconds=seconds)

    if head == JOIN:
        parts = rest.split()
        nonce = ""
        while len(parts) > 3 and "=" in parts[-1]:
            field, _, value = parts[-1].partition("=")
            field = field.lower()
            if field == "box":
                # Removed 2026-08-26, when the sealing tool (now `whisper`)
                # reached a release. A seat used
                # to carry its own X25519 key here for the manager to seal to;
                # the key is now the entrant's published `exchange_key`, read
                # off the room's roster. Refused rather than ignored, because
                # an entrant still sending one believes something about this
                # game that is no longer true.
                raise Malformed(
                    "JOIN no longer takes box= -- your exchange key is on the "
                    "roster when you register, and that is what the manager "
                    "seals to. Drop it and JOIN again")
            if field == "nonce":
                if not NONCE.match(value):
                    raise Malformed(
                        "JOIN's nonce= wants 16-64 hex digits -- it is this "
                        "seat's half of the seed, and the board has to be able "
                        "to show it was not chosen after the fact")
                nonce = value
            else:
                raise Malformed(f"JOIN does not understand {field!r}")
            parts = parts[:-1]
        if len(parts) != 3 or parts[1].lower() != "as":
            raise Malformed("JOIN wants '<table> as <name>', optionally "
                            "followed by nonce=<hex>")
        table, _, name = parts
        if not _NAME.match(name):
            raise Malformed(
                "a trader name is 1-32 characters of letters, digits, dash, "
                f"underscore or dot -- {name!r} is not")
        if _RESERVED.match(name):
            raise Malformed(
                f"{name!r} is the manager's own vocabulary -- a seat label, "
                f"or one of the two roles. Pick a name that is yours")
        return Join(table=table, name=name, nonce=nonce)

    if head == MANAGE:
        parts = rest.split()
        if len(parts) != 1:
            raise Malformed("MANAGE wants exactly one table id")
        return Manage(table=parts[0])
