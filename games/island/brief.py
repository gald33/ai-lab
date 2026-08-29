"""The rules of the island, for however many goods this game is played with.

`run_entrant` used to hand an agent 005's frozen base stimulus verbatim, which
was right while the island had exactly the four goods that document names. It
says so in prose -- "Four goods exist: **bread**, **cloth**, **iron** and
**salt**", the utility product written out good by good, and "however much of
the other three you have" -- so a five-good game handed out a brief that
contradicted the island it was about to play.

The fix is deliberately *not* a copy of the prose with the goods templated out.
There would then be two statements of the rules, 005's and the game's, free to
drift apart by paraphrase -- which is the thing `run_entrant`'s own comment says
it is avoiding by reading the frozen file in the first place. Instead this
**rewrites the three goods-dependent sentences inside 005's text**. There is one
copy of the rules; this adjusts the arithmetic in them.

Two properties hold it honest:

* at the four goods 005 froze, every rewrite is the identity, so the brief is
  byte-identical to what game 001 was played with;
* every rewrite **must match**. A substitution that silently found nothing would
  hand a trader a brief promising four goods while the manager deals five, and
  the trader would have no way to know. So a miss raises.

005's file is never written to. `tools/check_stimuli.py` still guards it.
"""

from __future__ import annotations

import re
from pathlib import Path

_ISLAND = Path(__file__).resolve().parents[2] / "experiments" / "005-deliberation-protocol"

#: The rules, frozen, in the experiment that wrote them. Read, never written.
BASE = _ISLAND / "stimuli" / "v3" / "base.md"

#: The goods that document is written about. A rewrite against exactly these is
#: the identity, which is what makes a four-good game provably unchanged.
FROZEN_GOODS = ("bread", "cloth", "iron", "salt")


def vocabulary() -> tuple[str, ...]:
    """The island's goods, in order, read from the one place that defines them.

    Imported rather than restated: a second list here would be free to drift
    from the one the dealer draws over, and a brief naming goods the island
    does not have is the failure this module exists to prevent.
    """
    import sys  # noqa: PLC0415 - only needed for the path this reaches through

    if str(_ISLAND) not in sys.path:
        sys.path.insert(0, str(_ISLAND))
    from island.dealer import GOODS  # noqa: PLC0415

    return GOODS


def goods_for(count: int) -> tuple[str, ...]:
    """The first `count` goods. A game is drawn over a prefix of the list."""
    words = vocabulary()
    if not 1 <= count <= len(words):
        raise BriefError(f"the island has {len(words)} goods, not {count}")
    return words[:count]

#: Spelled the way the frozen text spells four. An island with more goods than
#: this has bigger problems than its brief.
COUNT = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
         7: "Seven"}
LOWER = {n: w.lower() for n, w in COUNT.items()}


class BriefError(RuntimeError):
    """A rewrite found nothing to rewrite, so the brief cannot be trusted."""


def english(names: tuple[str, ...] | list[str], bold: bool = True) -> str:
    """`a, b and c`, the way the frozen text lists its goods."""
    marked = [f"**{n}**" if bold else n for n in names]
    if len(marked) == 1:
        return marked[0]
    return f"{', '.join(marked[:-1])} and {marked[-1]}"


def _sub(text: str, pattern: str, replacement: str, what: str) -> str:
    # The replacement is a literal, passed as a function so `re` cannot read a
    # backslash or a `\g` in a good's name as a reference into the match.
    out, n = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.MULTILINE)
    if n != 1:
        raise BriefError(
            f"the brief's {what} did not match, so it would still describe "
            f"{len(FROZEN_GOODS)} goods. The frozen stimulus has changed shape; "
            f"fix this rewrite rather than shipping a brief that lies.")
    return out


def body(text: str) -> str:
    """A stimulus without its repo-facing title and note.

    The same trimming `run_v3.py` does, and for the same reason: the heading and
    the italic note under it are addressed to whoever maintains the file, not to
    the trader, and `check_stimuli.py` hashes the body without them.
    """
    keep = [ln for ln in text.splitlines()
            if not ln.startswith("# ") and not ln.startswith("*")]
    return "\n".join(keep).strip()


def brief(goods: tuple[str, ...] | list[str], source: Path = BASE) -> str:
    """The island's rules, stated for `goods`.

    Three sentences in the frozen text count the goods: the one that names them,
    the utility product, and the one that says how many others are left. Nothing
    else does -- "exactly four shapes of line" and "all four lines settle" count
    the commands (PRODUCE, PROPOSE, APPROVE, DECLINE), and the worked examples
    name goods that are still goods.
    """
    goods = tuple(goods)
    if len(goods) not in COUNT:
        raise BriefError(f"no brief for {len(goods)} goods")
    text = body(source.read_text())
    if goods == FROZEN_GOODS:
        # The identity. Said out loud rather than left to fall out of three
        # rewrites that happen to be no-ops, so a four-good game is provably
        # reading exactly what game 001 read.
        return text

    text = _sub(text,
                r"^\w+ goods exist: .*$",
                f"{COUNT[len(goods)]} goods exist: {english(goods)}.",
                "goods sentence")
    text = _sub(text,
                r"^" + re.escape(FROZEN_GOODS[0]) + r"\^a_.*$",
                " × ".join(f"{g}^a_{g}" for g in goods),
                "utility product")
    text = _sub(text,
                r"however much of the other \w+ you have",
                f"however much of the other {LOWER[len(goods) - 1]} you have",
                "count of the remaining goods")
    return text
