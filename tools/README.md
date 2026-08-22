# Tools

Nearly empty on purpose.

Shared utilities move here when a **second** experiment needs them — not in
anticipation of one. Until then, each experiment keeps its own code next to its
own results, where it can be read alongside the thing it produced.

The failure mode this avoids is a shared framework that quietly becomes the
thing under test: experiments shaped to fit the harness, and results that are
partly about the harness rather than the question.

## `ground.py`

    tools/ground.py 004                        # the grounding for exactly one experiment
    tools/ground.py 004 --paths                # just the paths
    tools/ground.py 004 --preflight            # just the gates, before spending
    tools/ground.py 004 --new-run "<name>"     # open a run record from the template

Prints the standing decisions, [`experiments/GROUNDING.md`](../experiments/GROUNDING.md),
and one experiment's own `CLAUDE.md` and `PREFLIGHT.md` — and nothing from any
other experiment. It reads and copies; it runs nothing and is not part of any
experiment's code path, so it cannot become the thing under test.

That includes the gates: `--preflight` prints an experiment's smoke,
calibration and pilot commands, and you run them yourself. A shared gate runner
would end up shaping experiments to fit it, which is the failure mode this
directory exists to avoid.
