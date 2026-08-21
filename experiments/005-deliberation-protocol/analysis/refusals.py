"""What the harness refused, and what agents spent their turns on.

A refused call is the one place where the world and the agent disagree, so the
shape of the refusals says which of the two is at fault. Two readings this is
built to tell apart:

* **The agent misused the surface** -- offering goods it does not hold, naming
  a trader that does not exist, accepting an offer made to somebody else. That
  is agent behaviour and belongs in the result.
* **The clock refused them** -- a call that would have been fine one stage
  earlier or later. Each agent gets one turn in the production stage, so an
  agent that spends it talking produces nothing for the whole period. If most
  refusals are stage refusals, the finding is about the design's clock rather
  than about the agents, and the clock is mine to change.

    python analysis/refusals.py results/v2_pilot.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

STAGE = re.compile(r"belongs to the (\w+) stage; the (\w+) stage is open")


def bucket(text: str) -> str:
    m = STAGE.search(text)
    if m:
        return f"clock: {m.group(1)} call during {m.group(2)}"
    for probe, label in (
            ("already produced", "clock: produced twice in one period"),
            ("shares sum to", "budget: over the labour budget"),
            ("free,", "escrow: goods not free"),
            ("no such trader", "surface: unknown trader"),
            ("no such good", "surface: unknown good"),
            ("no such offer", "surface: unknown offer"),
            ("not offered to you", "surface: not your offer"),
            ("already", "surface: offer already settled"),
            ("no such call", "surface: unknown call"),
            ("cannot trade with yourself", "surface: self-dealing"),
            ("cannot message yourself", "surface: self-dealing"),
            ("needs text", "surface: empty message"),
            ("cannot be empty", "surface: empty bundle"),
            ("must be positive", "surface: non-positive quantity"),
            ("not a number", "surface: non-numeric"),
            ("negative", "surface: negative share"),
    ):
        if probe in text:
            return label
    return "other"


def main(path: str) -> None:
    data = json.loads(open(path).read())
    calls: Counter[str] = Counter()
    by_stage: Counter[str] = Counter()
    refusals: Counter[str] = Counter()
    produced_in_episode: Counter[tuple[int, int]] = Counter()
    turns = 0
    examples: dict[str, str] = {}

    for ep in data["rounds"]:
        for row in ep.get("transcript", []):
            turns += 1
            for a in row["actions"]:
                calls[str(a.get("call"))] += 1
                by_stage[f"{row['stage']}/{a.get('call')}"] += 1
            for r in row["results"]:
                if r.startswith("REFUSED"):
                    b = bucket(r)
                    refusals[b] += 1
                    examples.setdefault(b, r)
            if row["stage"] == "production":
                for a, r in zip(row["actions"], row["results"]):
                    if a.get("call") == "produce" and not r.startswith("REFUSED"):
                        produced_in_episode[(ep["seed"], row["episode"])] += 1

    print(f"{turns} agent-turns, {sum(calls.values())} calls, "
          f"{sum(refusals.values())} refused "
          f"({sum(refusals.values()) / max(1, sum(calls.values())):.0%})\n")

    print("calls attempted")
    for name, n in calls.most_common():
        print(f"  {name:10s} {n:5d}")

    print("\nrefusals by cause")
    for name, n in refusals.most_common():
        print(f"  {n:5d}  {name}")
        print(f"         e.g. {examples[name][:100]}")

    print("\ntraders who actually produced, per (seed, episode)")
    agents = data["agents"]
    missed = [k for k, v in produced_in_episode.items() if v < agents]
    for seed, episode in sorted(produced_in_episode):
        n = produced_in_episode[(seed, episode)]
        flag = "" if n == agents else "   <-- not everyone worked"
        print(f"  seed {seed} episode {episode}: {n}/{agents}{flag}")
    if missed:
        print(f"\n{len(missed)} of {len(produced_in_episode)} episodes had at "
              f"least one trader produce nothing.\nWith one production turn per "
              f"episode, a trader that talks instead of working\nhas no second "
              f"chance -- which is a property of the clock, not of the world.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/v2_pilot.json")
