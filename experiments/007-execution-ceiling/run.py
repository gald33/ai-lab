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

import plan  # noqa: E402

#: Two cells. `e-bare` is the base instructions, unchanged and identical to
#: every other experiment's control. `e-plan` adds the block *and* the island's
#: own solution, computed per trader by `plan.hook`.
run_v3.ARMS.update({
    "e-bare": (None, False),
    "e-plan": (str(HERE / "stimuli" / "plan"), False),
})
run_v3.PRIVATE_HOOK = plan.hook

if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--out" in argv:
        i = argv.index("--out") + 1
        argv[i] = str((HERE / argv[i]).resolve())
    sys.argv = [sys.argv[0], *argv]
    run_v3.main()
