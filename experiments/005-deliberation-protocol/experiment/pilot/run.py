"""Running one unguided world, and classifying how it ended.

The classification is the part worth reading. 002 Tier 3 reported islands dying
before its manipulation began, and 004 reported a learning channel that had
already saturated; both were harness facts that first appeared as agent
behaviour. So a world here never simply "fails" — it fails in exactly one of
three named ways, and one of them (``harness_failure``) is excluded from every
rate and counted separately.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field

from .world import Agent, Config, dispersion, draw_agents, draw_truth, normalise

#: Pre-registered coordination threshold. The headline is always this value.
TAU = 0.10

#: Reported alongside it, every time, so a single cut point cannot be the
#: whole result.
TAU_CURVE = (0.02, 0.05, 0.10, 0.15, 0.20, 0.30)

#: A round that takes longer than this is a harness fault, not a stubborn
#: population. Generous by three orders of magnitude for scripted agents; it
#: exists so the *classification* is honest when models are plugged in later.
ROUND_SECONDS = 5.0

COORDINATED = "coordinated"
AGENT_FAILURE = "agent_failure"
BUDGET_EXHAUSTED = "budget_exhausted"
HARNESS_FAILURE = "harness_failure"


@dataclass
class World:
    """One world's record. Everything needed to re-diagnose without re-running."""

    config: Config
    seed: int
    outcome: str
    #: ``D(r)`` at every round, including round 0 before anyone has heard anything.
    trajectory: list[float] = field(default_factory=list)
    #: How many well-formed submissions arrived each round. Anything below
    #: ``n_agents`` is a harness fault by definition.
    submissions: list[int] = field(default_factory=list)
    #: Wall-clock per round. Separates a slow harness from a stuck population.
    seconds: list[float] = field(default_factory=list)
    #: First round at which ``D(r) <= TAU``; ``None`` if never.
    coordinated_at: int | None = None
    #: First round at each threshold on the sensitivity curve.
    coordinated_at_tau: dict[str, int | None] = field(default_factory=dict)
    #: Distance from the agreed position to the market's actual answer. Only
    #: meaningful when the world coordinated — agreement is not correctness.
    error: float | None = None
    note: str = ""

    def to_json(self) -> dict:
        return {"config": self.config.key, "seed": self.seed,
                "outcome": self.outcome, "trajectory": self.trajectory,
                "submissions": self.submissions,
                "seconds": [round(s, 6) for s in self.seconds],
                "coordinated_at": self.coordinated_at,
                "coordinated_at_tau": self.coordinated_at_tau,
                "error": self.error, "note": self.note}


def _still_falling(trajectory: list[float]) -> bool:
    """Was dispersion strictly decreasing over the last three rounds?

    This is the whole difference between "the population would not agree" and
    "the population ran out of rounds", and getting it wrong would make a
    round-budget choice look like a finding about agents.
    """
    if len(trajectory) < 3:
        return False
    a, b, c = trajectory[-3:]
    return a > b > c


def run_world(cfg: Config, seed: int) -> World:
    """Run the full round budget, always.

    Stopping the moment `D(r) <= TAU` would be cheaper and would silently
    corrupt the sensitivity curve: the tighter thresholds (0.02, 0.05) are
    reached *later* than 0.10, so an early return would record them as never
    reached and every tight row of the curve would read low by construction.
    The curve exists to answer "was the threshold doing the work", so it is the
    one thing that must not be an artefact of the threshold.
    """
    rng = random.Random(seed * 104729 + 17)
    truth = draw_truth(cfg, rng)
    agents = draw_agents(cfg, truth, rng)
    world = World(config=cfg, seed=seed, outcome=HARNESS_FAILURE)
    reached: dict[str, int | None] = {f"{t:g}": None for t in TAU_CURVE}
    agreed_at_tau: list[float] | None = None

    try:
        for r in range(cfg.rounds + 1):
            started = time.perf_counter()
            posts = []
            for a in agents:
                p = a.submit()
                if len(p) != cfg.n_goods or any(
                        not math.isfinite(x) or x <= 0 for x in p):
                    world.note = f"malformed submission from agent {a.index} at round {r}"
                    world.seconds.append(time.perf_counter() - started)
                    return world
                posts.append(p)
            world.submissions.append(len(posts))
            if len(posts) != cfg.n_agents:
                world.note = f"round {r} collected {len(posts)}/{cfg.n_agents}"
                world.seconds.append(time.perf_counter() - started)
                return world

            d = dispersion(posts)
            world.trajectory.append(d)
            for t in TAU_CURVE:
                k = f"{t:g}"
                if reached[k] is None and d <= t:
                    reached[k] = r
                    if t == TAU:
                        # Snapshot the agreed position at the round agreement
                        # was reached, not at the end of the budget — the
                        # population keeps moving afterwards.
                        bar = [sum(q[g] for q in posts) / len(posts)
                               for g in range(cfg.n_goods)]
                        agreed_at_tau = normalise(bar)

            elapsed = time.perf_counter() - started
            world.seconds.append(elapsed)
            if elapsed > ROUND_SECONDS:
                world.note = f"round {r} took {elapsed:.2f}s"
                return world

            if r == cfg.rounds:
                break
            # Nobody is told anything. Each agent sees a sample of what others
            # actually submitted, and the sample is drawn per agent per round.
            for a in agents:
                others = [j for j in range(cfg.n_agents) if j != a.index]
                seen_ix = rng.sample(others, min(cfg.width, len(others)))
                a.update([posts[j] for j in seen_ix], cfg.anchor)
    except Exception as exc:  # a raising world is a harness fault, never a datum
        world.note = f"{type(exc).__name__}: {exc}"
        return world

    world.coordinated_at_tau = reached
    world.coordinated_at = reached[f"{TAU:g}"]
    if world.coordinated_at is not None:
        world.outcome = COORDINATED
        assert agreed_at_tau is not None
        world.error = (
            math.sqrt(sum((agreed_at_tau[g] - truth[g]) ** 2
                          for g in range(cfg.n_goods)))
            / math.sqrt(sum(x * x for x in truth)))
    else:
        world.outcome = (BUDGET_EXHAUSTED if _still_falling(world.trajectory)
                         else AGENT_FAILURE)
    return world
