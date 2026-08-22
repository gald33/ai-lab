# Contributing

This is a personal lab, not a project looking for maintainers. That said, a few
kinds of contribution are genuinely useful.

## Most useful

**Tell me an experiment is wrong.** A confounder I didn't name, a control that
doesn't control what I claimed, a metric that measures the harness. Open an
issue with the specific step in the design and what it lets through. This is
worth more to me than anything else on this page.

**Propose an experiment.** Use the
[new experiment](.github/ISSUE_TEMPLATE/new-experiment.md) issue template. The
part that matters is the question and what result would change your mind — not
the implementation.

**Take something off the roadmap.** [roadmap/ROADMAP.md](roadmap/ROADMAP.md)
lists what is open and what is startable now, with the evidence that put each
item there. An item under `now` is one somebody would otherwise be doing.

**Report a reproduction that disagrees.** If you run something here and get a
different answer, that's a result. Include your model versions, run count, and
raw records.

## Less useful right now

Pull requests adding infrastructure — a docs site, a shared experiment
framework, test scaffolding. These are deliberately absent
([tools/](tools/README.md) explains why), and a PR adding one will probably be
declined for reasons that have nothing to do with its quality.

## Games

Nothing is playable yet, so there's nothing to submit a run to.
[games/](games/README.md) describes what a game here would have to preserve; if
you think one of those constraints is wrong, that's an issue worth opening.

## Style

Experiments follow [templates/experiment/](templates/experiment/README.md),
loosely. It's a set of prompts, not a schema — a section with nothing under it
should be deleted rather than filled with hedging.

The one part that isn't loose is grounding: every run whose result is kept has
a record written before it runs, an experiment's grounding does not travel to
another experiment, and nothing is spent until that experiment's smoke,
calibration and pilot gates have a recorded result on the current commit.
[experiments/GROUNDING.md](experiments/GROUNDING.md) says why and how.
