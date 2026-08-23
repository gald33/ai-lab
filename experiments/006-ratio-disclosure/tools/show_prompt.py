"""Print the prompt a cell actually sends. The assembly gate reads this."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "005-deliberation-protocol"))

import run  # noqa: E402,F401  -- registers this experiment's arms
import run_v3  # noqa: E402

if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "r-ratios"
    print(run_v3.instructions(arm, "You are T1. [private state]", 10))
