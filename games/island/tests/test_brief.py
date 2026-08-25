"""The rules an entrant hands its agent, for however many goods it is playing.

    python -m pytest games/island/tests/test_brief.py -q

005's frozen stimulus counts the goods in prose -- "Four goods exist", the
utility product written out good by good, "the other three". A five-good game
briefed from it verbatim tells every trader it is playing a different island
from the one the manager is dealing, and the trader has no way to notice.

The load-bearing test is `test_four_goods_is_the_frozen_text_exactly`. It is
what makes the whole change inert for a four-good game: game 001's replay is
scored against a brief this must still reproduce byte for byte.
"""

from __future__ import annotations

import pytest

from games.island import brief as B


def line(text: str, needle: str) -> str:
    found = [ln for ln in text.splitlines() if needle in ln]
    assert found, f"no line containing {needle!r}"
    return found[0]


def test_four_goods_is_the_frozen_text_exactly() -> None:
    # Not "close to" and not "equivalent": the same bytes. A four-good game
    # reads what game 001 read, and that is checkable rather than asserted.
    assert B.brief(B.FROZEN_GOODS) == B.body(B.BASE.read_text())


def test_five_goods_says_five_everywhere_it_counts() -> None:
    five = B.brief(B.FROZEN_GOODS + ("fish",))
    assert line(five, "goods exist") == (
        "Five goods exist: **bread**, **cloth**, **iron**, **salt** and **fish**.")
    assert line(five, "^a_") == (
        "bread^a_bread × cloth^a_cloth × iron^a_iron × salt^a_salt × fish^a_fish")
    assert "however much of the other four you have" in five


def test_nothing_else_moves() -> None:
    # Exactly three sentences count the goods. "Exactly three shapes of line"
    # and "all three lines settle" are about PRODUCE/PROPOSE/APPROVE, and the
    # worked examples name goods that are still goods -- so they must survive.
    four = B.brief(B.FROZEN_GOODS).splitlines()
    five = B.brief(B.FROZEN_GOODS + ("fish",)).splitlines()
    assert len(four) == len(five)
    assert sum(1 for a, b in zip(four, five) if a != b) == 3
    for keep in ("Exactly three shapes of line", "all three lines settle",
                 "PRODUCE bread=0.5 iron=0.5"):
        assert any(keep in ln for ln in five), f"{keep!r} was rewritten"


def test_a_rewrite_that_finds_nothing_raises() -> None:
    """The dangerous failure, made loud.

    A silent no-op hands a trader a brief promising four goods while the
    manager deals five. Nothing downstream can catch that -- the agent simply
    plays the wrong island -- so it has to fail here.
    """
    moved = B.BASE.parent / "nothing-like-the-stimulus.md"
    try:
        moved.write_text("# T\n\nThis file counts no goods at all.\n")
        with pytest.raises(B.BriefError, match="goods sentence"):
            B.brief(B.FROZEN_GOODS + ("fish",), source=moved)
    finally:
        moved.unlink(missing_ok=True)


def test_the_island_has_fish_and_the_brief_can_name_it() -> None:
    assert "fish" in B.vocabulary()
    assert B.goods_for(5)[-1] == "fish"
    assert B.goods_for(4) == B.FROZEN_GOODS


@pytest.mark.parametrize("count", [1, 0, 99])
def test_a_count_the_island_cannot_deal_is_refused(count: int) -> None:
    if count == 1:
        # One good is dealable but not a game; the brief still renders, and it
        # is `protocol.GOODS_MIN` that refuses it. Kept apart on purpose.
        assert B.goods_for(1) == ("bread",)
        return
    with pytest.raises(B.BriefError):
        B.goods_for(count)


def test_the_frozen_stimulus_is_never_written_to() -> None:
    before = B.BASE.read_bytes()
    B.brief(B.FROZEN_GOODS + ("fish",))
    assert B.BASE.read_bytes() == before
