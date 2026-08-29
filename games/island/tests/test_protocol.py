"""The lobby's grammar in isolation, no hub needed."""

from __future__ import annotations

import pytest

from games.island import protocol
from games.island.protocol import Join, Malformed, Manage, Open, parse


def test_open_parses_traders_episodes_rounds():
    assert parse("OPEN traders=2 episodes=8 rounds=3") == Open(2, 8, 3)


def test_open_defaults_rounds_to_one():
    assert parse("OPEN traders=2 episodes=8") == Open(2, 8, 1)


def test_join_parses_table_and_name():
    assert parse("JOIN g7 as scout-v2") == Join("g7", "scout-v2")


def test_manage_parses_a_table_id():
    assert parse("MANAGE g7") == Manage("g7")


def test_an_unrecognised_line_is_talk():
    assert parse("good luck everyone") is None
    assert parse("") is None


@pytest.mark.parametrize("line,fragment", [
    ("OPEN traders=1 episodes=8", "at least 2 traders"),
    ("OPEN traders=2 episodes=0", "at least 1 episode"),
    ("OPEN traders=2 episodes=8 rounds=0", "at least 1 round"),
    ("OPEN traders=2", "missing"),
    ("OPEN traders=2 episodes=8 players=2", "does not understand"),
    ("OPEN traders=two episodes=8", "key=integer"),
    ("JOIN g7", "'<table> as <name>'"),
    ("JOIN g7 scout-v2", "'<table> as <name>'"),
    ("JOIN g7 as", "'<table> as <name>'"),
    ("MANAGE", "exactly one table id"),
    ("MANAGE g7 g8", "exactly one table id"),
])
def test_a_near_miss_is_refused_and_never_repaired(line, fragment):
    with pytest.raises(Malformed, match=fragment):
        parse(line)


def test_a_name_that_is_a_seat_label_is_refused_not_renamed():
    """`g7 seat T1 = T2` is a line nobody can read twice the same way."""
    with pytest.raises(Malformed) as exc:
        parse("JOIN g7 as T2")

    assert "vocabulary" in str(exc.value)


def test_a_name_that_is_a_banner_is_refused():
    with pytest.raises(Malformed):
        parse("JOIN g7 as " + "x" * 33)
    with pytest.raises(Malformed):
        parse("JOIN g7 as scout/v2")


def test_an_ordinary_name_still_parses():
    assert parse("JOIN g7 as scout-v2.1").name == "scout-v2.1"


def test_join_carries_a_nonce():
    assert parse("JOIN g7 as scout-v2 nonce=0123456789ABCDEF").nonce == "0123456789ABCDEF"
    assert parse("JOIN g7 as scout-v2").nonce == ""


def test_a_join_still_offering_box_is_told_it_is_gone():
    """Refused rather than ignored: an entrant still sending one believes
    something about this game that stopped being true when sealing shipped."""
    with pytest.raises(Malformed) as exc:
        parse("JOIN g7 as scout-v2 box=abc")

    assert "no longer takes box=" in str(exc.value)
    assert "roster" in str(exc.value)


def test_a_nonce_that_is_not_hex_is_refused_not_accepted_as_one():
    """A nonce is the seat's half of the seed: the board has to be able to
    show it, so it has to be something a reader can check by eye."""
    for bad in ("nonce=zzzz", "nonce=abc", "nonce=" + "a" * 65, "nonce="):
        with pytest.raises(Malformed):
            parse(f"JOIN g7 as scout-v2 {bad}")


def test_an_unknown_field_on_a_join_is_refused():
    with pytest.raises(Malformed) as exc:
        parse("JOIN g7 as scout-v2 seat=1")

    assert "does not understand" in str(exc.value)


# --- episode length is part of the format -------------------------------


def test_open_takes_a_seconds_from_the_ladder():
    a = parse("OPEN traders=2 episodes=3 rounds=3 goods=5 seconds=120")
    assert a.seconds == 120


def test_open_without_seconds_is_the_sixty_every_game_so_far_was_played_at():
    """The default is not a fresh choice -- it is what g1..g6 actually ran."""
    assert parse("OPEN traders=2 episodes=8").seconds == 60
    assert protocol.EPISODE_SECONDS_DEFAULT == 60


def test_a_seconds_off_the_ladder_is_refused_and_the_ladder_is_named():
    """**A rung near a real one is exactly what an entrant guesses.**

    So the refusal lists them rather than saying only that this one is wrong;
    the lobby does not repair, so the reason has to carry the fix.
    """
    with pytest.raises(Malformed) as e:
        parse("OPEN traders=2 episodes=8 seconds=100")
    for rung in protocol.EPISODE_SECONDS_ALLOWED:
        assert str(rung) in str(e.value)


def test_the_ladder_is_the_one_that_was_asked_for():
    assert protocol.EPISODE_SECONDS_ALLOWED == (15, 30, 45, 60, 90, 120, 180, 300)


# --- a table may not open on goods the island does not have -------------


def test_the_goods_ceiling_is_the_islands_vocabulary():
    """Five is what `island.dealer.GOODS` holds, so five is the most.

    The ceiling used to be the palette's seven, which let `goods=6` parse and
    fail later at brief-building. The bound belongs to the vocabulary.
    """
    from games.island.brief import vocabulary  # noqa: PLC0415

    assert protocol.GOODS_MAX == len(vocabulary()) == 5


def test_more_goods_than_the_island_has_is_refused_at_the_line():
    with pytest.raises(Malformed) as e:
        parse("OPEN traders=2 episodes=8 goods=6")
    assert "goods must be between 2 and 5" in str(e.value)


def test_five_goods_is_still_a_table_that_opens():
    assert parse("OPEN traders=2 episodes=8 goods=5").goods == 5
