"""What the CI workflows are allowed to be, asserted rather than eyeballed.

Three of `CLAUDE.md`'s entries are the same disease: a check that was green for
a reason unrelated to what it was checking -- a ticker emitted above the rows it
looked for, `viewer/tests` missing from a path list, page tests skipped behind
somebody else's red render. A `paths:` filter is the newest way to catch it,
and the quietest: **a filter naming a directory that does not exist never
fires, and a job that never fires is reported as neither passed nor failed.**

So the filter's paths are checked against the filesystem. That is the assertion
that would have caught the rename in this very PR had the filter existed before
it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def load(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text())


def triggers(doc: dict) -> dict:
    """A workflow's `on:` block.

    YAML 1.1 reads a bare `on` as the boolean true, which is why this is a
    function and not `doc["on"]` -- and why the test suite reads these files
    with a parser rather than a regex.
    """
    return doc.get("on", doc.get(True))


def every_workflow():
    return sorted(p.name for p in WORKFLOWS.glob("*.yml"))


# --- the drawing gate ----------------------------------------------------

def test_the_drawing_jobs_are_gated_on_paths():
    """Two browsers at ~16 minutes each must not run on a roadmap-only diff."""
    on = triggers(load("drawing.yml"))
    for event in ("pull_request", "push"):
        assert on[event].get("paths"), f"drawing.yml {event} has no paths filter"


def test_the_drawing_gate_names_paths_that_exist():
    """A filter naming a stale path never fires, and a job that never fires
    reports nothing at all -- the quietest version of a gate that checks
    nothing. This is the assertion a directory rename has to survive."""
    on = triggers(load("drawing.yml"))
    for pattern in on["pull_request"]["paths"]:
        top = pattern.split("/**")[0].split("/*")[0]
        assert (ROOT / top).exists(), (
            f"drawing.yml gates on {pattern!r}, but {top!r} is not in the "
            f"checkout -- this filter can never fire")


def test_the_gate_covers_the_harness_that_runs_the_check():
    """If `render.py` itself changes and the filter does not cover it, the
    check does not run on the change to the check."""
    doc = load("drawing.yml")
    on = triggers(doc)
    commands = " ".join(
        step.get("run", "")
        for job in doc["jobs"].values() for step in job["steps"])
    assert "render.py" in commands
    harness = "experiments/does-a-content-free-protocol-help/viewer"
    assert any(p.startswith(harness) for p in on["pull_request"]["paths"]), (
        "the drawing jobs run render.py but the gate does not cover the tree "
        "it lives in")


# --- across every workflow -----------------------------------------------

def test_no_job_name_is_defined_twice():
    """Splitting a job out of one workflow into another must move it, not copy
    it: two jobs of one name run the same work twice and report it once."""
    seen: dict[str, str] = {}
    for name in every_workflow():
        for job in (load(name).get("jobs") or {}):
            assert job not in seen, (
                f"job {job!r} is defined in both {seen[job]} and {name}")
            seen[job] = name


@pytest.mark.parametrize("name", every_workflow())
def test_every_workflow_parses_and_has_jobs(name):
    doc = load(name)
    assert triggers(doc), f"{name} has no `on:` block"
    assert doc.get("jobs"), f"{name} defines no jobs"


def test_every_pytest_directory_named_in_ci_exists():
    """The `viewer/tests` omission, and then `tools/tests`, both got in by a
    hand-maintained list drifting from the tree. A named directory that is not
    there is a test suite nothing runs."""
    missing = []
    for name in every_workflow():
        doc = load(name)
        for job_name, job in (doc.get("jobs") or {}).items():
            for step in job["steps"]:
                run = step.get("run", "")
                if "pytest" not in run:
                    continue
                for word in run.split():
                    if "/" in word and not word.startswith("-"):
                        if not (ROOT / word).exists():
                            missing.append(f"{name}:{job_name} -> {word}")
    assert not missing, "CI names paths that are not in the checkout: " + \
        ", ".join(missing)


def test_the_tools_tests_are_actually_run_by_ci():
    """They were not, when they were added. This file is one of them, so an
    omission here silences the check that would have reported it."""
    runs = " ".join(
        step.get("run", "")
        for name in every_workflow()
        for job in (load(name).get("jobs") or {}).values()
        for step in job["steps"])
    assert "tools/tests" in runs, (
        "nothing in .github/workflows runs tools/tests, so these assertions "
        "are green only on somebody's laptop")
