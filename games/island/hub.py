"""What to do when the hub blinks.

**A hub that is redeploying is not a hub that is gone**, and the difference
is the whole of this module. `island-lobby` crashed at 11:55:28 on 2026-08-28
and was caught by `Restart=always` (`NRestarts=2`): the managed hub's own
redeploy answered a poll with a Cloudflare 502, `Client.history` raised, and
`run_lobby`'s loop -- which had no `except` around its drain -- fell out of
`main` and exited 1. It was idle, so nothing was lost. Had a table been live,
the round would have died of somebody else's deploy, and `Restart=always`
would have brought back a process that reads `--state`, sees the table as one
it already settled, and does not resume it.

So the rule this module encodes: **a poll that fails for a reason that is
about the transport, not about the request, is retried rather than fatal.**
Everything else still propagates on the first try -- a 400, a 403, a line the
lobby cannot read -- because those do not get better by waiting and a runner
that retried them would hide a defect behind a backoff.

The budget is deliberately finite. A hub that has been unreachable for two
minutes is not blinking, and at that point exiting is right again: systemd
restarts a lobby that reads its state back, which is a better place to be
than a process looping forever against a hub that has moved.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

import httpx
from switchboard.client import SwitchboardError

T = TypeVar("T")

#: Statuses that say "ask again", not "you asked wrongly". 502/503/504 are the
#: shapes a redeploy behind Cloudflare takes; 500 is here because the managed
#: hub returns one while its store reconnects; 408/429 are the hub or the edge
#: asking for a slower caller.
BLIP_STATUS = frozenset({408, 429, 500, 502, 503, 504})

BUDGET = 120.0        #: seconds a single call may spend being retried
FIRST_WAIT = 1.0      #: seconds before the first retry, doubling from there
MAX_WAIT = 15.0       #: ceiling on the backoff, so a long budget still polls


def is_blip(exc: BaseException) -> bool:
    """Is this the hub being briefly unavailable, rather than a real answer?

    Two cases, and nothing else counts. A `httpx.TransportError` -- the
    request never got an answer at all: connection refused mid-restart, a DNS
    blip, a read timeout. And a `SwitchboardError` carrying one of
    `BLIP_STATUS`, which is a hub (or an edge in front of one) that answered
    with "not now".

    Note what is *not* here: `LeaseHeld`, `UnknownPeerExchangeKey`, and every
    4xx that is not 408/429. A retry loop that swallowed those would turn a
    bug into a hang.
    """
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, SwitchboardError) and exc.status in BLIP_STATUS


def through_blips(work: Callable[[], T], what: str, *, budget: float = BUDGET,
                  sleep: Callable[[float], None] = time.sleep,
                  now: Callable[[], float] = time.monotonic) -> T:
    """Run `work`, retrying it while the hub is only blinking.

    Says every retry out loud on stdout -- a lobby that quietly absorbed a
    ninety-second outage would look, in its own log, exactly like a lobby
    nothing happened to, and the next person reading that log is trying to
    explain a gap.

    `sleep` and `now` are injectable so a test can prove the backoff without
    spending it.
    """
    deadline = now() + budget
    wait = FIRST_WAIT
    while True:
        try:
            return work()
        except Exception as exc:      # noqa: BLE001 -- re-raised unless a blip
            if not is_blip(exc) or now() >= deadline:
                raise
            pause = max(0.0, min(wait, deadline - now()))
            print(f"{what}: hub blinked, retrying in {pause:.0f}s: {exc!r}",
                  flush=True)
            sleep(pause)
            wait = min(wait * 2, MAX_WAIT)
