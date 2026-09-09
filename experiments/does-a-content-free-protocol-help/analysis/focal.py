"""Round-0 focal points: is a cell coordinated before anyone has spoken?

`005-render-precision-fix` exists because v1's two hinted cells were. This is
the check that says so from a record, so that the artifact cannot come back
unnoticed in a later run -- it is the acceptance criterion that item asks to be
named in the next pre-registration, written as code rather than as a sentence.

**Round 0 is the right place to look.** It is the one round in which no agent
has heard anybody: any agreement in it was manufactured by the instrument,
never by deliberation. A cell with a world at exactly zero dispersion at round
0 is not measuring a protocol.

Two numbers per cell, both denominators printed:

- **worlds at zero round-0 dispersion** -- the criterion. Zero of N passes.
- **round-0 submissions equal to the hint as the prompt printed it** -- the
  mechanism, when the criterion fails. It separates "agents happened to agree"
  from "agents copied the one number the instrument handed all of them", which
  are different faults with different fixes.

    python analysis/focal.py results/agents.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiment"))

from agents.market import dispersion, draw_world  # noqa: E402
from agents.prompt import _vector  # noqa: E402


def round0(episode: dict) -> list[list[float]]:
    """What every agent submitted before it had heard anybody."""
    return [a["prices"] for a in episode["transcript"][0]]


def copied_hint(episode: dict, hint: list[float]) -> int:
    """How many round-0 submissions are the hint *as the prompt printed it*.

    Rendered rather than rounded: the agent never saw the hint, it saw a
    string, and the string is what it could copy. Comparing against the
    unrounded hint answers a different question and answers it 0 every time.
    """
    printed = _vector(hint)
    return sum(1 for price in round0(episode) if _vector(price) == printed)


def report(path: Path) -> int:
    """Print the check and return 0 if every cell passes, 1 if any does not."""
    record = json.loads(path.read_text())
    rounds = record.get("config", {}).get("rounds", 5)
    cells: dict[str, list[dict]] = {}
    for episode in record["episodes"]:
        if not episode.get("transcript"):
            continue
        cells.setdefault(episode["cell"], []).append(episode)

    failed = []
    print(f"{path}: round-0 focal-point check\n")
    print(f"{'cell':<14}{'worlds':>7}{'at zero':>9}{'copied hint':>13}")
    for cell, episodes in sorted(cells.items()):
        zero = copies = shown = 0
        for episode in episodes:
            world = draw_world(episode["seed"], rounds)
            submissions = round0(episode)
            if len(submissions) > 1 and dispersion(submissions) == 0.0:
                zero += 1
            copies += copied_hint(episode, world.hint)
            shown += len(submissions)
        print(f"{cell:<14}{len(episodes):>7}{zero:>9}{copies:>9}/{shown:<4}")
        if zero:
            failed.append(cell)

    print()
    if failed:
        print(f"FAIL: {', '.join(failed)} agreed before anyone spoke. "
              f"A cell coordinated at round 0 measures the instrument.")
        return 1
    print("pass: no cell agreed before anyone spoke.")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    return report(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
