"""One world, one cell: the round loop, and the classification of how it ended.

The loop is deliberately dull. What is worth attention is that every failure is
sorted into exactly one of the four pre-registered outcomes, and that
``harness_failure`` is a real category rather than a shrug — 002 reported
islands that died before its manipulation began, and 004 reported a channel
that had already saturated, and both first appeared as agent behaviour.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .market import (N_AGENTS, World, dispersion, distance)
from .prompt import build
from .runner import AgentFault, Reply, ask

TAU = 0.10
TAU_CURVE = (0.02, 0.05, 0.10, 0.15, 0.20, 0.30)

COORDINATED = "coordinated"
AGENT_FAILURE = "agent_failure"
BUDGET_EXHAUSTED = "budget_exhausted"
HARNESS_FAILURE = "harness_failure"


@dataclass
class Episode:
    cell: str
    seed: int
    outcome: str
    trajectory: list[float] = field(default_factory=list)
    submissions: list[int] = field(default_factory=list)
    seconds: list[float] = field(default_factory=list)
    coordinated_at: int | None = None
    coordinated_at_tau: dict[str, int | None] = field(default_factory=dict)
    #: ``min_r D(r)`` — the paired secondary reading declared in DEVIATIONS.md.
    min_dispersion: float | None = None
    #: Distance from the agreed position to the truth, at the round agreement
    #: was reached. Agreement is not correctness and this is where that shows.
    error: float | None = None
    #: Distance from the population mean at the final round to the truth,
    #: defined on every episode including ones that never agreed.
    final_error: float | None = None
    retries: int = 0
    transcript: list[list[dict]] = field(default_factory=list)
    note: str = ""

    def to_json(self) -> dict:
        return {"cell": self.cell, "seed": self.seed, "outcome": self.outcome,
                "trajectory": [round(x, 6) for x in self.trajectory],
                "submissions": self.submissions,
                "seconds": [round(s, 3) for s in self.seconds],
                "coordinated_at": self.coordinated_at,
                "coordinated_at_tau": self.coordinated_at_tau,
                "min_dispersion": self.min_dispersion,
                "error": self.error, "final_error": self.final_error,
                "retries": self.retries, "note": self.note,
                "transcript": self.transcript}


def _still_falling(trajectory: list[float]) -> bool:
    if len(trajectory) < 3:
        return False
    a, b, c = trajectory[-3:]
    return a > b > c


def run_episode(world: World, *, cell: str, stimulus: str, use_hint: bool,
                rounds: int, cwd: str, workers: int = 8) -> Episode:
    """Run one world in one cell. Never repairs a reply, never invents a price."""
    ep = Episode(cell=cell, seed=world.seed, outcome=HARNESS_FAILURE)
    reached: dict[str, int | None] = {f"{t:g}": None for t in TAU_CURVE}
    agreed: list[float] | None = None
    heard: list[list[tuple[int, str, list[float]]]] = [[] for _ in range(N_AGENTS)]
    posts: list[list[float]] = []

    for r in range(rounds + 1):
        started = time.perf_counter()
        prompts = [build(stimulus=stimulus,
                         hint=world.hint if use_hint else None,
                         signal=world.signals[i], heard=heard[i],
                         round_index=r, rounds=rounds)
                   for i in range(N_AGENTS)]
        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                replies: list[Reply] = list(pool.map(
                    lambda p: ask(p, cwd), prompts))
        except Exception as exc:
            ep.note = f"round {r}: {type(exc).__name__}: {exc}"
            ep.seconds.append(time.perf_counter() - started)
            return ep

        ep.retries += sum(1 for x in replies if x.retried)
        posts = [x.prices for x in replies]
        ep.submissions.append(len(posts))
        ep.seconds.append(time.perf_counter() - started)
        ep.transcript.append([
            {"agent": i, "message": x.message,
             "prices": [round(v, 6) for v in x.prices]}
            for i, x in enumerate(replies)])

        d = dispersion(posts)
        ep.trajectory.append(d)
        for t in TAU_CURVE:
            k = f"{t:g}"
            if reached[k] is None and d <= t:
                reached[k] = r
                if t == TAU:
                    bar = [sum(q[g] for q in posts) / len(posts)
                           for g in range(len(world.truth))]
                    agreed = [x / bar[0] for x in bar]

        if r == rounds:
            break
        # Nobody is told anything. Each agent is passed what a fixed, seeded
        # sample of the others actually submitted and actually said.
        heard = [[(j, replies[j].message, posts[j]) for j in world.seen[r][i]]
                 for i in range(N_AGENTS)]

    ep.coordinated_at_tau = reached
    ep.coordinated_at = reached[f"{TAU:g}"]
    ep.min_dispersion = min(ep.trajectory)
    bar = [sum(q[g] for q in posts) / len(posts) for g in range(len(world.truth))]
    ep.final_error = distance([x / bar[0] for x in bar], world.truth)
    if ep.coordinated_at is not None:
        ep.outcome = COORDINATED
        assert agreed is not None
        ep.error = distance(agreed, world.truth)
    else:
        ep.outcome = (BUDGET_EXHAUSTED if _still_falling(ep.trajectory)
                      else AGENT_FAILURE)
    return ep
