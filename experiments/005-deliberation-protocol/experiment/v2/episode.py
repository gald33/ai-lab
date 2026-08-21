"""Running one world for one cell, and classifying how it ended.

The stage order is the design's: an open floor where only talk is possible, a
production stage where labour is committed, a market, then the bell. Talk is
open in every stage except the bell; production is not, which is what makes
conversation before the production stage worth something different from
conversation after it.

Agents within a stage act in a **seeded rotation** rather than a fixed order,
so no trader is permanently first to see the board. The rotation is drawn from
the world seed and is therefore identical across cells -- part of what makes
the comparison paired.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .prompt import turn as build_turn
from .runner import AgentFault, TransportFault, Turn, ask
from .world import ActionError, FLOOR, MARKET, PRODUCTION, World

SCORED, AGENT_FAILURE, HARNESS_FAILURE = "scored", "agent_failure", "harness_failure"

#: Turns each agent gets in each stage. Talk stages get one; the market gets
#: two so that an offer can be answered within the period it was made.
TURNS = {FLOOR: 1, PRODUCTION: 1, MARKET: 2}


@dataclass
class Episode:
    cell: str
    seed: int
    outcome: str = SCORED
    note: str = ""
    trajectory: list[list[float]] = field(default_factory=list)
    transcript: list[dict] = field(default_factory=list)
    retries: int = 0
    transport_retries: int = 0
    refused: int = 0
    seconds: float = 0.0

    def to_json(self) -> dict:
        return {"cell": self.cell, "seed": self.seed, "outcome": self.outcome,
                "note": self.note, "trajectory": self.trajectory,
                "retries": self.retries,
                "transport_retries": self.transport_retries,
                "refused": self.refused,
                "seconds": round(self.seconds, 1),
                "transcript": self.transcript}


def _apply(world: World, name: str, actions: list[dict]) -> list[str]:
    """Execute an agent's actions in order, reporting each outcome verbatim.

    A refused call is reported back to the agent and counted. It is never
    silently dropped and never repaired: the agent asked for something the
    world does not allow, and knowing that is part of the task.
    """
    out = []
    for a in actions:
        call = a.get("call")
        try:
            if call == "post":
                world.post(name, a.get("text", ""))
                out.append("posted to the board")
            elif call == "message":
                world.message(name, a.get("to", ""), a.get("text", ""))
                out.append(f"message delivered to {a.get('to')}")
            elif call == "produce":
                r = world.produce(name, a.get("plan", {}))
                out.append(f"produced {r['produced']}, "
                           f"{r['labour_unspent']} labour unspent")
            elif call == "offer":
                r = world.offer(name, a.get("to", ""), a.get("give", {}),
                                a.get("want", {}))
                out.append(f"offer {r['offer_id']} made to {a.get('to')}")
            elif call == "accept":
                world.accept(name, a.get("offer_id", ""))
                out.append(f"accepted {a.get('offer_id')} — the trade executed")
            elif call == "decline":
                world.decline(name, a.get("offer_id", ""))
                out.append(f"declined {a.get('offer_id')}")
            elif call == "cancel":
                world.cancel(name, a.get("offer_id", ""))
                out.append(f"cancelled {a.get('offer_id')}")
            elif call == "read":
                # The base block advertises `read()` as part of the surface, so
                # refusing it was the harness contradicting its own
                # description. Delivery is automatic -- the next prompt carries
                # the inbox -- and saying so is more honest than a refusal that
                # reads as "you may not do that".
                out.append("read: messages are delivered to you automatically; "
                           "everything new is in this prompt")
            elif call == "pending":
                out.append(f"pending: {world.pending(name)}")
            elif call == "state":
                # Also advertised, also delivered automatically: the prompt
                # already carries this agent's private state every turn.
                out.append("state: your private state is in this prompt, "
                           "under 'Your private state'")
            else:
                out.append(f"REFUSED: no such call {call!r}")
        except ActionError as exc:
            out.append(f"REFUSED ({call}): {exc}")
    return out


def run_episode(*, island, cell: str, seed: int, periods: int, cwd: str,
                concurrency: int = 8) -> Episode:
    world = World(island=island, periods=periods)
    ep = Episode(cell=cell, seed=seed)
    names = sorted(world.traders)
    rng = random.Random(seed * 7919 + 13)
    results: dict[str, list[str]] = {n: [] for n in names}
    started = time.perf_counter()

    try:
        for _ in range(periods):
            for stage, count in TURNS.items():
                world.open(stage)
                for _ in range(count):
                    order = list(names)
                    rng.shuffle(order)
                    prompts = {}
                    for n in order:
                        prompts[n] = build_turn(
                            cell=cell, state=world.state(n),
                            inbox=world.read(n), pending=world.pending(n),
                            results=results[n], periods=periods)
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        futures = {n: pool.submit(ask, prompts[n], cwd)
                                   for n in order}
                        replies: dict[str, Turn] = {}
                        for n, f in futures.items():
                            replies[n] = f.result()
                    for n in order:
                        r = replies[n]
                        ep.retries += int(r.retried)
                        ep.transport_retries += r.transport_retries
                        out = _apply(world, n, r.actions)
                        ep.refused += sum(1 for o in out if o.startswith("REFUSED"))
                        results[n] = out
                        ep.transcript.append(
                            {"period": world.period, "stage": stage,
                             "agent": n, "actions": r.actions, "results": out})
            ep.trajectory.append(world.close_period())
    except (AgentFault, TransportFault, Exception) as exc:  # noqa: BLE001
        ep.outcome = HARNESS_FAILURE
        ep.note = f"{type(exc).__name__}: {exc}"
        ep.seconds = time.perf_counter() - started
        return ep

    ep.seconds = time.perf_counter() - started
    ep.world = world  # type: ignore[attr-defined]
    return ep
