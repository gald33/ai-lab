"""The gate that lets `render.py` be a required check.

`render.py` needs a browser and a minute, so it is not imported for its
checks here -- only for `verdict`, which is pure and is the part that decides
whether a run is a pass. That decision is the whole reason CI can run the
suite at all, so it gets tests of its own: a list of known failures nobody
verifies is a list that quietly swallows a real regression.

**Against a fixture list, not against the live one.** These were written when
`KNOWN_FAILURES` held two entries and they read it directly, which made them
tests of whatever happened to be listed rather than of the mechanism: fixing
both entries -- which is what the list is *for* -- turned all six red at once,
with nothing broken. The mechanism is what needs holding shut, so the fixture
below is what the rules are exercised on, and the live list gets the one test
it deserves: that whatever is in it is well formed. Today it is empty, and an
empty list is a pass here.
"""

from __future__ import annotations

import contextlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _render():
    spec = importlib.util.spec_from_file_location("render", HERE / "render.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


render = _render()

#: Two entries shaped like the two this list was opened with -- a board and a
#: check, a date, and a reason -- so the rules below are exercised on something
#: that cannot change under them.
FIXTURE = {
    "some-board @safari 393x660": (
        "2026-08-29", "A layout failure that is not this branch's fault, "
                      "described at enough length to be retired by somebody "
                      "else later."),
    "some-board alive": (
        "2026-08-29", "A lighting failure that is not this branch's fault, "
                      "described at enough length to be retired by somebody "
                      "else later."),
}
KEYS = list(FIXTURE)


@contextlib.contextmanager
def listed(entries):
    """Run `verdict` against a list of known failures of our own choosing."""
    was = render.KNOWN_FAILURES
    render.KNOWN_FAILURES = entries
    try:
        yield
    finally:
        render.KNOWN_FAILURES = was


def test_every_live_known_failure_carries_a_date_and_a_reason():
    """An entry with no reason is an entry nobody can ever retire.

    An empty list is the intended state and passes: the entries this gate was
    opened with have been fixed, and the rules are tested on `FIXTURE` below.
    """
    for key, entry in render.KNOWN_FAILURES.items():
        since, why = entry
        assert len(since) == 10 and since[4] == since[7] == "-", (
            f"{key} is dated {since!r}, which is not a date")
        assert len(why) > 40, f"{key} has no reason worth reading: {why!r}"


def test_a_clean_run_against_an_empty_list_is_a_pass():
    """Which is what green looks like once the debts are paid."""
    with listed({}):
        code, out = render.verdict([])
    assert code == 0
    assert not [line for line in out if line.startswith("FAIL")]


def test_nothing_is_tolerated_when_nothing_is_listed():
    with listed({}):
        code, out = render.verdict(["some-board cards: two cards overlap"])
    assert code == 1
    assert any(line == "FAIL some-board cards: two cards overlap" for line in out)


def test_exactly_the_known_failures_is_a_pass():
    with listed(FIXTURE):
        code, out = render.verdict([f"{k}: some measured number" for k in KEYS])
    assert code == 0
    # And it says so out loud, so a reader of the log knows what was tolerated
    # rather than finding a silent green.
    assert any(line.startswith("KNOWN") for line in out)


def test_anything_unlisted_fails_the_run():
    """The property the whole mechanism exists to keep."""
    with listed(FIXTURE):
        code, out = render.verdict(
            [f"{KEYS[0]}: measured", "some-board cards: two cards overlap"])
    assert code == 1
    assert any(line == "FAIL some-board cards: two cards overlap" for line in out)


def test_a_known_failure_that_stops_failing_also_fails_the_run():
    """Otherwise the list rots: entries outlive the bugs and nobody notices."""
    with listed(FIXTURE):
        code, out = render.verdict([f"{KEYS[0]}: measured"])
    assert code == 1
    assert any(KEYS[1] in line and "no longer failing" in line for line in out)


def test_a_clean_run_against_a_stale_list_is_not_a_pass():
    with listed(FIXTURE):
        code, out = render.verdict([])
    assert code == 1
    assert sum(1 for line in out if line.startswith("FAIL")) == len(KEYS)


def test_a_known_key_matches_on_the_stable_half_only():
    """The half after the colon carries measured numbers that move each run."""
    with listed(FIXTURE):
        a, _ = render.verdict([f"{KEYS[0]}: tint 0.41 -> 0.35", f"{KEYS[1]}: x"])
        b, _ = render.verdict([f"{KEYS[0]}: tint 0.42 -> 0.34", f"{KEYS[1]}: y"])
        assert a == b == 0
        # But a different board with the same check is not the same failure.
        code, _ = render.verdict(
            [f"other-board {KEYS[0].split(' ', 1)[1]}: x"] + [f"{k}: x" for k in KEYS])
    assert code == 1


#: The suite is enumerated in exactly one place -- `render.checks` -- and split
#: across CI jobs by group. Both of those are ways for a check to stop running
#: while the ticks stay green, which is the same failure `--require` exists to
#: prevent, so both get a test.
WORKFLOW = HERE.parents[3] / ".github" / "workflows" / "tests.yml"


def _plan():
    """The whole suite, named, without a browser.

    `checks` only *builds* the calls; nothing is driven until one is invoked,
    so a `None` browser and two made-up boards are enough to ask what the
    suite contains.
    """
    return render.checks(None, "http://127.0.0.1:0",
                         [Path("board-one.json"), Path("board-two.json")],
                         Path("/tmp/unused"))


def test_every_check_is_in_a_group_and_named_once():
    plan = _plan()
    assert plan, "the suite enumerates no check at all"
    for group, name, _ in plan:
        assert group in render.GROUPS, f"{name} is in group {group!r}"
    names = [name for _, name, _ in plan]
    assert len(names) == len(set(names)), "two checks share a name"


def test_the_groups_partition_the_suite():
    """A check in neither group is a check nobody runs, drawn as a pass."""
    plan = _plan()
    covered = {name for group in render.GROUPS
               for _, name, _ in render.select(plan, group, None)}
    assert covered == {name for _, name, _ in plan}
    # And no check is in two groups, which would pay for it twice.
    assert sum(len(render.select(plan, g, None)) for g in render.GROUPS) == len(plan)


def test_the_workflow_runs_every_group():
    """The split is only safe while CI carries both halves of it.

    Read off `tests.yml` rather than asserted about the code alone, because
    the way this goes wrong is a group added here and not there -- and that
    failure is silent in exactly the way a skip is.
    """
    text = WORKFLOW.read_text()
    for group in render.GROUPS:
        assert f"--group {group}" in text, (
            f"no CI job runs `--group {group}`, so those checks run nowhere")
    # And each of those jobs still refuses to pass having checked nothing.
    assert text.count("--require") >= len(render.GROUPS)


def test_a_selection_that_matches_nothing_is_empty_rather_than_everything():
    """Which is what lets `run` fail it, instead of quietly running the lot."""
    plan = _plan()
    assert render.select(plan, None, ["no-such-check"]) == []
    assert len(render.select(plan, None, None)) == len(plan)


def test_a_name_selects_every_board_that_check_runs_on():
    plan = _plan()
    picked = [name for _, name, _ in render.select(plan, None, ["replay"])]
    assert picked == ["replay/one", "replay/two"]
    assert [n for _, n, _ in render.select(plan, None, ["replay/one"])] == ["replay/one"]


def test_the_carriers_mechanics_leans_on_are_in_the_suite():
    """`mechanics` excuses two events the island's floor because these carry them.

    It says so itself, at the cost of a browser and twenty minutes. Said here
    too, for nothing, because this is the failure it exists to catch and there
    is no reason to wait for a rendered island to hear about it.
    """
    for carrier in ("turning", "overhead"):
        assert carrier in render.enumerated()
