"""The preflight gate, against the failure it exists to catch.

This is a test about a test, which is usually a smell and is not one here:
the gate is what stands between a spent run and a run of silence, and it was
**passing a hub that was not there** until this was written. A gate nobody
points at a broken thing is a reassurance.
"""

from __future__ import annotations

import json

from island import toolchain


def test_a_jsonrpc_error_object_is_a_failure():
    """The exact shape an unreachable hub produces, and the exact shape the
    first version of this gate missed: `id` is present and the text says
    "internal error", which is what the gate searched for -- inside a
    *result* it never looks at, so the search never matched."""
    out = json.dumps({"jsonrpc": "2.0", "id": 2,
                      "error": {"code": -32603,
                                "message": "internal error (see stderr)"}})

    verdict = toolchain._verdict(out)

    assert verdict is not None
    assert "internal error" in verdict


def test_a_result_flagged_is_error_is_a_failure():
    out = json.dumps({"jsonrpc": "2.0", "id": 2,
                      "result": {"isError": True,
                                 "content": [{"type": "text", "text": "nope"}]}})

    assert toolchain._verdict(out) is not None


def test_no_answer_at_all_is_a_failure():
    """The server never started, which is different from it starting and
    failing -- and is worth saying differently."""
    verdict = toolchain._verdict('{"jsonrpc": "2.0", "id": 1, "result": {}}')

    assert verdict is not None
    assert "did not start" in verdict


def test_a_good_answer_passes():
    out = "\n".join([
        json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2,
                    "result": {"content": [{"type": "text", "text": "[]"}]}}),
    ])

    assert toolchain._verdict(out) is None


def test_noise_around_the_json_does_not_confuse_it():
    """Servers log. A line that is not JSON is not an answer either way."""
    out = "\n".join([
        "starting up, reading config",
        json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"content": []}}),
        "shutting down",
    ])

    assert toolchain._verdict(out) is None


def test_the_probe_is_a_tool_that_needs_the_hub():
    """`whoami` answers out of local config, so it passes whether or not
    anything is listening. That is how the first version came to be useless,
    and it is worth pinning rather than remembering."""
    assert toolchain._PROBE != "whoami"
