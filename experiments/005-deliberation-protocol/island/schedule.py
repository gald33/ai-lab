"""What the manager posts about time, and how it writes a deadline.

Lifted out of `run_v3.py` unchanged so that a second runner -- the game's --
announces a round in exactly the same words. The wording is not cosmetic: it
is what an agent reads to decide when to act, and `viewer/web/reducer.js`
matches it to draw the board at all, so two runners phrasing it differently
would be two different experiments and one broken spectator page.

`ACK_SECONDS` and `EPISODE_SECONDS` are parameters here rather than the module
globals they are in `run_v3.py`, which rebinds them from its own command line.
Same numbers, same text; the caller says which.
"""

from __future__ import annotations

import time

#: How long the acknowledgement window runs before episode 1 opens regardless.
ACK_SECONDS = 120
#: How long a trader has to acknowledge, counted from the same start as
#: `ACK_SECONDS`. Shorter than the window when a round wants the acknowledgement
#: in before the episode opens rather than at the moment it does.
ACK_BY_SECONDS = ACK_SECONDS
#: How long an episode stays open.
EPISODE_SECONDS = 60


def stamp(ts: float) -> str:
    """A deadline as an absolute UTC clock time.

    A deadline stated as "in 120s" is only true at the instant it is posted.
    An agent that reads the schedule ninety seconds after the manager wrote it
    -- which is ordinary, since nobody is prompted and a session may spend its
    first turns starting up -- reads "in 120s" and plans against a window that
    has already mostly gone. Run 005 has a trader acknowledging with "Episode 1
    in 120s" when episode 1 was about thirty seconds away.

    So every deadline the manager posts is an absolute time. Every Switchboard
    tool result carries the current time as `now` in the same form, so a
    reader can tell how long it has left however late it arrives.
    """
    return time.strftime("%H:%M:%SZ", time.gmtime(ts))


def schedule_text(episodes: int, names: tuple[str, ...], *, hide: bool = False,
                  opens_at: float | None = None,
                  episode_seconds: int = EPISODE_SECONDS,
                  ack_seconds: int = ACK_SECONDS,
                  ack_by_seconds: int | None = None) -> str:
    opens = opens_at if opens_at is not None else time.time() + ack_seconds
    # Stated absolutely, like every other deadline on this board: a countdown
    # is what a trader misreads when it reads the message late.
    ack_by = opens - (ack_seconds - (ack_by_seconds
                                     if ack_by_seconds is not None else ack_seconds))
    span = (f"Episodes are {episode_seconds}s each; the next few are announced "
            f"as they come." if hide
            else f"{episodes} episodes, {episode_seconds}s each.")
    return (f"Schedule for this round. {len(names)} traders: "
            f"{', '.join(names)}. {span} "
            f"Within an episode there are no stages: PRODUCE, PROPOSE and "
            f"APPROVE all settle for as long as the episode is open. At the "
            f"bell open proposals lapse and everything held is consumed. "
            f"Acknowledge with a line beginning ACK, by {stamp(ack_by)}. "
            f"Every time on this board is absolute UTC, and every tool result "
            f"carries the current time as `now`: read the deadline against "
            f"that, not against when this message was written. "
            f"Episode 1 opens at {stamp(opens)} "
            f"whether or not everyone has.")
