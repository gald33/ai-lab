"""The three cells assemble to base plus exactly their own block."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "005-deliberation-protocol"))

import run  # noqa: E402,F401  -- registers the arms
import run_v3  # noqa: E402


def prompt(arm):
    return run_v3.instructions(arm, "PRIVATE", 10)


def test_bare_carries_neither_block():
    text = prompt("r-bare")
    assert "## Two ratios" not in text
    assert "## Two habits" not in text


def test_each_treated_cell_carries_only_its_own_block():
    assert "## Two ratios" in prompt("r-ratios")
    assert "## Two habits" not in prompt("r-ratios")
    assert "## Two habits" in prompt("r-placebo")
    assert "## Two ratios" not in prompt("r-placebo")


def test_the_treated_cells_are_length_matched():
    """Within 5%: a difference in length is a difference in treatment."""
    a, b = len(prompt("r-ratios").split()), len(prompt("r-placebo").split())
    assert abs(a - b) / a < 0.05


def test_every_cell_is_base_plus_its_block_and_nothing_else():
    base = prompt("r-bare")
    for arm, heading in (("r-ratios", "## Two ratios"),
                         ("r-placebo", "## Two habits")):
        text = prompt(arm)
        # Every heading of the bare prompt survives, in order, in the treated
        # one -- the block is added, never a replacement for something.
        for line in (ln for ln in base.splitlines() if ln.startswith("## ")):
            assert line in text
        assert text.count(heading) == 1
