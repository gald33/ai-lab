"""Running one round: k episodes on one island, with memory across them.

A **round** is the unit that resets context. Inside it, `k` episodes share the
same island -- the same abilities, the same tastes, the same traders -- and each
episode resets item stocks, labour and open offers. What carries between
episodes is what each agent has been told and what it has seen happen, which is
the whole learning channel and the reason a round has more than one episode.

Each agent therefore carries a private history that is appended to on every turn
and handed back to it in the next prompt. It is the agent's own record: what it
did, what the world answered, and what it heard. It is never the world's state,
and it is never another agent's history.
"""

from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .prompt import stimulus, turn as build_turn
from .runner import AgentFault, TransportFault, Turn, ask
from .world import ActionError, FLOOR, MARKET, PRODUCTION, World

SCORED, AGENT_FAILURE, HARNESS_FAILURE = "scored", "agent_failure", "harness_failure"

#: Turns each agent gets in each stage. Talk stages get one; the market gets
#: two so an offer can be answered inside the episode it was made in.
TURNS = {FLOOR: 1, PRODUCTION: 1, MARKET: 2}


@dataclass
class Round:
    cell: str
    seed: int
    outcome: str = SCORED
    note: str = ""
    #: One row of per-agent utilities per closed episode.
    trajectory: list[list[float]] = field(default_factory=list)
    transcript: list[dict] = field(default_factory=list)
    retries: int = 0
    transport_retries: int = 0
    refused: int = 0
    seconds: float = 0.0
    #: Longest history any agent carried, and whether anyone's was trimmed.
    history_chars_max: int = 0
    history_trimmed: bool = False

    def to_json(self) -> dict:
        return {"cell": self.cell, "seed": self.seed, "outcome": self.outcome,
                "note": self.note, "trajectory": self.trajectory,
                "retries": self.retries,
                "transport_retries": self.transport_retries,
                "refused": self.refused, "seconds": round(self.seconds, 1),
                "history_chars_max": self.history_chars_max,
                "history_trimmed": self.history_trimmed,
                "transcript": self.transcript}


def _apply(world: World, name: str, actions: list[dict]) -> list[str]:
    """Execute an agent's actions in order, reporting each outcome verbatim.

    A refused call is reported back and counted, never silently dropped and
    never repaired: the agent asked for something the world does not allow, and
    knowing that is part of the task.
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
                out.append("read: messages are delivered to you automatically; "
                           "everything new is in this prompt")
            elif call == "pending":
                out.append(f"pending: {world.pending(name)}")
            elif call == "state":
                out.append("state: your private state is in this prompt, "
                           "under 'Your private state'")
            else:
                out.append(f"REFUSED: no such call {call!r}")
        except ActionError as exc:
            out.append(f"REFUSED ({call}): {exc}")
    return out


def _entry(episode: int, stage: str, inbox: list[dict], actions: list[dict],
           results: list[str]) -> str:
    """One line-group of an agent's private record of the round."""
    lines = [f"**Episode {episode + 1}, {stage}**"]
    for m in inbox:
        where = "board" if m["public"] else "direct"
        lines.append(f"  heard ({where}) from {m['from']}: {m['text'].strip()}")
    for a, r in zip(actions, results):
        detail = a.get("text") or a.get("plan") or a.get("offer_id") or ""
        lines.append(f"  you {a.get('call')} {detail} -> {r}")
    if len(actions) > len(results):
        for a in actions[len(results):]:
            lines.append(f"  you {a.get('call')} -> (no result recorded)")
    return "\n".join(lines)


def run_round(*, island, cell: str, seed: int, episodes: int, cwd: str,
              concurrency: int = 8) -> Round:
    world = World(island=island, episodes=episodes)
    rec = Round(cell=cell, seed=seed)
    # Built once per round and sent as a system prompt on every call, because
    # it does not vary and the runtime caches that channel.
    system = stimulus(cell, episodes)
    names = sorted(world.traders)
    rng = random.Random(seed * 7919 + 13)
    results: dict[str, list[str]] = {n: [] for n in names}
    history: dict[str, list[str]] = {n: [] for n in names}
    started = time.perf_counter()

    try:
        for _ in range(episodes):
            for stage, count in TURNS.items():
                world.open(stage)
                for _ in range(count):
                    order = list(names)
                    rng.shuffle(order)
                    inboxes, prompts = {}, {}
                    for n in order:
                        inboxes[n] = world.read(n)
                        prompts[n] = build_turn(
                            cell=cell, state=world.state(n), inbox=inboxes[n],
                            pending=world.pending(n), results=results[n],
                            episodes=episodes, history=history[n])
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        futures = {n: pool.submit(ask, prompts[n], cwd, system)
                                   for n in order}
                        replies: dict[str, Turn] = {n: f.result()
                                                    for n, f in futures.items()}
                    for n in order:
                        r = replies[n]
                        rec.retries += int(r.retried)
                        rec.transport_retries += r.transport_retries
                        out = _apply(world, n, r.actions)
                        rec.refused += sum(1 for o in out
                                           if o.startswith("REFUSED"))
                        results[n] = out
                        history[n].append(_entry(world.episode, stage,
                                                 inboxes[n], r.actions, out))
                        rec.transcript.append(
                            {"episode": world.episode, "stage": stage,
                             "agent": n, "actions": r.actions, "results": out})
            rec.trajectory.append(world.close_episode())
    except (AgentFault, TransportFault, Exception) as exc:  # noqa: BLE001
        rec.outcome = HARNESS_FAILURE
        rec.note = f"{type(exc).__name__}: {exc}"
        rec.seconds = time.perf_counter() - started
        return rec

    rec.seconds = time.perf_counter() - started
    rec.history_chars_max = max(sum(len(e) for e in h) for h in history.values())
    from .prompt import HISTORY_CHARS
    rec.history_trimmed = rec.history_chars_max > HISTORY_CHARS
    return rec
