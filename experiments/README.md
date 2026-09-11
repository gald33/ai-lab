# The experiments, and what each one asks

**An experiment is named by its question.** The directory name is the question,
so a directory listing is a list of what this lab has asked. Nothing here is
numbered.

| experiment | the question it asks | status |
|---|---|---|
| [`is-coordination-less-to-reason-about`](is-coordination-less-to-reason-about/) | Does coordination improve because agents reason harder about each other, or because good primitives leave them less to reason about? | run, not published |
| [`which-part-of-a-convention-works`](which-part-of-a-convention-works/) | Does a shared convention for talking about value make a group better off — and is it the words, the machinery, or the disposition that does the work? | Tier 1 a result; Tier 3 designed, calibrated, unrun |
| [`which-promotion-rule-beats-luck`](which-promotion-rule-beats-luck/) | When candidate solutions compete and the winner is promoted automatically, which rule converges on the *good* solution rather than the *lucky* one? | Tier 1 complete |
| [`is-ruin-the-convention-or-the-commitment`](is-ruin-the-convention-or-the-commitment/) | Is the ruin a fact about the convention, or about a world where a production commitment can never be taken back? | run and reported |
| [`does-a-content-free-protocol-help`](does-a-content-free-protocol-help/) | Does a content-free deliberation protocol improve coordination between traders? | run; null |
| [`does-telling-traders-what-to-disclose-help`](does-telling-traders-what-to-disclose-help/) | Does telling traders what to disclose improve coordination? | run; unresolved |
| [`do-they-take-a-handed-over-answer`](do-they-take-a-handed-over-answer/) | If the answer is handed to them, do they take it — and what survives when it is taken away? | run; open tail |
| [`can-an-agent-hold-availability`](can-an-agent-hold-availability/) | Can an agent hold availability across time, and what is actually holding it? | probes only |
| [`how-wrong-can-a-shared-convention-be`](how-wrong-can-a-shared-convention-be/) | How wrong may a convention be and still be worth holding, purely because everyone holds it? | **designed, nothing run** |

Each directory carries its own `CLAUDE.md`, which is the only
experiment-specific grounding an agent working on it should read. The rule, and
why it is a rule, is in [`GROUNDING.md`](GROUNDING.md).

`tools/ground.py <fragment>` prints exactly one experiment's grounding bundle.
Any distinctive part of the question finds it — `ground.py ruin`, `ground.py
promotion`, `ground.py handed-over`. An ambiguous fragment is an error rather
than a first match.

## The numbers, retired

Every experiment used to be `NNN-slug`, and the numbers are cited about 1,200
times across `reports/` and the run records. **Those documents are not being
rewritten.** They are the record of what was thought at the time, and editing
them to say something else is the thing this lab's first standing decision
forbids. So the map lives here instead, and it is permanent.

| retired number | the experiment it was |
|---|---|
| 001 | `is-coordination-less-to-reason-about` |
| 002 | `which-part-of-a-convention-works` |
| 003 | `which-promotion-rule-beats-luck` |
| 004 | `is-ruin-the-convention-or-the-commitment` |
| 005 | `does-a-content-free-protocol-help` |
| **006** | **two experiments** — `can-an-agent-hold-availability` *and* `does-telling-traders-what-to-disclose-help` |
| 007 | `do-they-take-a-handed-over-answer` |
| 008 | never a directory — the `shared-coding-tasks` arc, still unbuilt |

The same map is in `tools/ground.py` as `RETIRED_NUMBERS`, so `ground.py 004`
still works and prints the name it is now. `tools/tests/test_ground.py` fails if
an entry stops resolving.

### Why the number went, in one line each

- **It was never unique.** There were two `006` directories, `006-agent-standby`
  and `006-ratio-disclosure`. A duplicate identifier is not an identifier, and
  it had been that way for weeks without anyone noticing — which is the
  measurement, not the anecdote.
- **It was ambiguous three ways.** `002` meant experiment 002, run 002 inside
  some experiment, and game g2. All three shapes appear in this repo, often on
  the same page.
- **It was the only thing standing between two naming systems.** Seven of the
  eight directory slugs were already byte-identical to an arc `id:` in
  `roadmap/arcs/`. The number was the sole difference.
- **Nobody could remember what it meant.** Which is the whole point, and the
  reason the replacement is the question rather than a tidier slug.

## Numbers that look alike across experiments

Three figures in this directory share digits, mean different things, and belong
to different experiments. Collected here because the reader who conflates them
is by definition reading across experiments, and no single experiment's
documents can warn them.

| figure | what it is | where it is defined |
|---|---|---|
| **0.229** | run-mean sd of **captured gain** — instrument noise | `do-they-take-a-handed-over-answer/PREREGISTRATION-v3.md`, "What forced a new endpoint" |
| **1.029** | per-seed sd of the same endpoint across runs (often rounded to 1.03) | same table |
| **−0.229** | a **median paired difference** on 5 seeds — a treatment effect, not noise | `does-telling-traders-what-to-disclose-help/runs/001-does-saying-the-ratios-help.md` |

The first two are the same quantity at two denominators. The third is a
different kind of number entirely and merely resembles the first.

Related, and the reason that table exists at all: the run-level variance
finding is `does-telling-traders-what-to-disclose-help/FINDING-run-level-variance.md`
(sd 0.322 pooled against 0.175 within a run) — a third experiment again, and
one of the two that shared the retired number `006`.

## The rule for a new experiment

Name the directory after the **question**, never the answer or the mechanism.

- `does-a-content-free-protocol-help` — a question. Still true after the answer
  came back null: it was asked.
- ~~`content-free-protocols-dont-help`~~ — an answer. Half of these will be
  wrong, and the ones that are wrong will be wrong in the filename.
- ~~`deliberation-protocol`~~ — a mechanism. It names the apparatus, which is
  what the reader is trying to look past.

Lowercase, hyphenated, reads as a question without the question mark. Keep it
short enough to type a fragment of.
