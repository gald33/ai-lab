"""The lobby's grammar in isolation, no hub needed."""

from __future__ import annotations

import pytest

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
