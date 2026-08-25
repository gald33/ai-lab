"""Print the prompt a cell sends, including the private plan. The assembly gate."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "005-deliberation-protocol"))
sys.path.insert(0, str(HERE.parent / "002-barter-conventions" / "experiment"))

import run  # noqa: E402,F401  -- registers the arms and the hook
import run_v3  # noqa: E402
from barter.economy import draw_island  # noqa: E402

if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "e-plan"
    island = draw_island(4, 4, seed=1)
    private = f"You are T1. [capacities and tastes]"
    extra = run_v3.PRIVATE_HOOK(arm, "T1", island, 0)
    print(run_v3.instructions(arm, private + ("\n\n" + extra if extra else ""), 10))
