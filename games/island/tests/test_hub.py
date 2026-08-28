"""A hub that blinks must not end a process that is holding a table.

The case these are written from: `island-lobby` crashed at 11:55:28 on
2026-08-28 because the managed hub's own redeploy answered a poll with a
Cloudflare 502 and `run_lobby`'s loop had no retry around its drain.
"""

from __future__ import annotations

import httpx
import pytest
from switchboard.client import LeaseHeld, SwitchboardError

from games.island import hub


def cloudflare_502() -> SwitchboardError:
    """What `Client._raise_for` builds out of an HTML error page: no JSON to
    read, so the whole body lands in `detail` and the status is all there is
    to classify on."""
    response = httpx.Response(502, text="<html>error code: 502</html>",
                              request=httpx.Request("GET", "https://hub/history"))
    with pytest.raises(SwitchboardError) as caught:
        from switchboard.client import _raise_for
        _raise_for(response)
    return caught.value


def test_cloudflare_502_is_a_blip():
    assert hub.is_blip(cloudflare_502())


@pytest.mark.parametrize("exc", [
    httpx.ConnectError("connection refused"),
    httpx.ReadTimeout("timed out"),
    SwitchboardError("gateway timeout", status=504),
    SwitchboardError("too many requests", status=429),
])
def test_transport_and_not_now_are_blips(exc):
    assert hub.is_blip(exc)


@pytest.mark.parametrize("exc", [
    SwitchboardError("no such channel", status=404),
    SwitchboardError("forbidden", status=403),
    LeaseHeld("held", status=409, payload={"holder": "someone"}),
    ValueError("a line the lobby could not read"),
])
def test_real_answers_are_not_blips(exc):
    """A retry loop that swallowed these would turn a bug into a hang."""
    assert not hub.is_blip(exc)


def test_retries_through_a_redeploy_and_returns():
    clock = [0.0]
    slept: list[float] = []
    calls = []

    def work():
        calls.append(len(calls))
        if len(calls) < 4:
            raise cloudflare_502()
        return "drained"

    def sleep(seconds):
        slept.append(seconds)
        clock[0] += seconds

    assert hub.through_blips(work, "drain", sleep=sleep,
                             now=lambda: clock[0]) == "drained"
    assert slept == [1.0, 2.0, 4.0]


def test_gives_up_once_the_hub_is_not_blinking_any_more():
    """Past the budget it raises, and systemd restarts a lobby that reads its
    own state back -- better than looping forever against a hub that moved."""
    clock = [0.0]

    def sleep(seconds):
        clock[0] += seconds

    with pytest.raises(SwitchboardError):
        hub.through_blips(lambda: (_ for _ in ()).throw(cloudflare_502()),
                          "drain", budget=10.0, sleep=sleep,
                          now=lambda: clock[0])
    assert clock[0] <= 10.0


def test_a_real_error_raises_on_the_first_try():
    calls = []

    def work():
        calls.append(1)
        raise SwitchboardError("forbidden", status=403)

    with pytest.raises(SwitchboardError):
        hub.through_blips(work, "drain", sleep=lambda s: None)
    assert calls == [1]
