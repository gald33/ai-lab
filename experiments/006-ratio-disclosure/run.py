"""Experiment 006's entry point. It drives 005's runner as a shared instrument.

**The runner is code, not grounding.** `run_v3.py` starts the sessions, runs
the clock, reads the board and settles; nothing in it decides anything about
this experiment. 005's design documents, pre-registration and stopping rule are
not read here and do not apply here — the same rule 005 follows for importing
002's `barter.economy`.

What this file owns: the three cells, and the stimuli they are built from.

    python run.py --arms r-bare r-placebo r-ratios --rounds 5 \
        --episodes 10 --episode-seconds 180 --agents 4 --out results/001-first
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / "005-deliberation-protocol"
sys.path.insert(0, str(RUNNER))

import run_v3  # noqa: E402

#: Three cells, differing only in what is appended to the base instructions.
#: `r-placebo` is length- and register-matched to `r-ratios` and carries nothing
#: about goods, costs, worth or exchange. It is here because run 005 of the
#: previous experiment found that *adding text at all* cost something: without
#: a matched placebo, a difference between `r-bare` and `r-ratios` cannot be
#: told from the price of being handed a paragraph.
run_v3.ARMS.update({
    "r-bare":    (None, False),
    "r-placebo": (str(HERE / "stimuli" / "placebo"), False),
    "r-ratios":  (str(HERE / "stimuli" / "ratios"), False),
})

if __name__ == "__main__":
    # `--out` is made absolute so results land in this experiment's tree and
    # not in the runner's.
    argv = sys.argv[1:]
    if "--out" in argv:
        i = argv.index("--out") + 1
        argv[i] = str((HERE / argv[i]).resolve())
    sys.argv = [sys.argv[0], *argv]
    run_v3.main()
