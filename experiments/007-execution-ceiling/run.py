"""Experiment 007's entry point. Drives 005's runner as a shared instrument.

    python run.py --arms e-bare e-plan --rounds 12 --episodes 10 \
        --episode-seconds 180 --ack-seconds 30 --ack-by-seconds 20 \
        --agents 4 --out results/001-ceiling
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "005-deliberation-protocol"))

import run_v3  # noqa: E402
from island import manager as island_manager  # noqa: E402

import plan  # noqa: E402

#: Two cells. `e-bare` is the base instructions, unchanged and identical to
#: every other experiment's control. `e-plan` adds the block *and* the island's
#: own solution, computed per trader by `plan.hook`.
run_v3.ARMS.update({
    "e-bare": (None, False),
    "e-plan": (str(HERE / "stimuli" / "plan"), False),
    #: Run 002. Same plan, same private numbers; the block adds the tranching
    #: advice, and the rule below lets it be followed.
    "t-plan": (str(HERE / "stimuli" / "plan"), False),
    "t-tranche": (str(HERE / "stimuli" / "tranche"), False),
    #: Run 004, the ladder. The winning block decomposed: what a trader could
    #: derive alone (hint), how to act with others (protocol, domain-free), and
    #: both. The cheat -- anything needing another trader's private data -- is
    #: gone from all four; see stimuli/decomposed/00-CHEAT-removed.md.
    "l-bare":     (None, False),
    "l-protocol": (str(HERE / "stimuli" / "decomposed" / "01-protocol"), False),
    "l-hint":     (str(HERE / "stimuli" / "decomposed" / "02-hint"), False),
    "l-both":     (str(HERE / "stimuli" / "decomposed" / "both"), False),
})
run_v3.PRIVATE_HOOK = plan.hook

if __name__ == "__main__":
    argv = sys.argv[1:]
    # Splitting labour changes what the manager settles, so it is opt-in per
    # run and recorded (007 D4). It is switched on for the `t-` cells, and on
    # for *both* of them: the tranching advice is the treatment, and a rule
    # only one cell could use would confound the two.
    if any(a.startswith("t-") for a in argv):
        island_manager.SPLIT_LABOUR = True
    if "--out" in argv:
        i = argv.index("--out") + 1
        argv[i] = str((HERE / argv[i]).resolve())
    sys.argv = [sys.argv[0], *argv]
    run_v3.main()
