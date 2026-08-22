# The roadmap

What is open in this lab, as a graph rather than as prose scattered across six
reports.

The machinery is [`roadmap-core`](https://github.com/gald33/roadmap-core) —
stdlib-only, one SQLite file inside the checkout, no service and no credential.
It is a lab utility, not experiment infrastructure: nothing under
`experiments/` imports it, and no experiment is shaped by it. That is the line
[`tools/README.md`](../tools/README.md) draws, and this stays on the outside of
it.

## Why

Every report here ends in what to attack first, and every experiment README
ends in what is unrun. That is already a backlog — written six times, in six
places, where nothing can say which of those things is *startable now*, which
is waiting on another, and which quietly stopped being true.

An item does not replace a report. The report is the argument; the item is the
one line of it that is still work.

## Using it

```bash
pip install "roadmap-core[files]"
export ROADMAP_SOURCE=local     # the SQLite store, in this checkout

roadmap push        # roadmap/items/*.yaml -> the store
roadmap ready       # what is startable now
roadmap show 005-rerun-at-twenty-one-rounds
roadmap claim 005-display-precision-artifact
roadmap sync        # regenerate ROADMAP.md and ../ARCS.md
```

Reading needs none of that: [`ROADMAP.md`](ROADMAP.md) and
[`../ARCS.md`](../ARCS.md) are generated but committed, so an agent in a
checkout reads the backlog with no install and no network. They are also
therefore files that lie the moment somebody edits an item without running
`sync`, which is what the CI check exists to catch.

`roadmap/roadmap.db` is derived and **not committed** — `push` rebuilds it from
the YAML on first open.

## Rules

**1. Authoring an item is writing `roadmap/items/<id>.yaml`.** There is no
`roadmap new`, deliberately: filing work belongs in a diff somebody reviews.
The `id` must match the filename stem and be kebab-case.

**2. Every item carries `evidence`, and it says two things**: why this is worth
doing, and how you will know it worked. Point at the report or the README
paragraph that made it work — an item whose evidence is a restatement of its
title is an item nobody can retire. Validation fails without it.

**3. Status is the store's, not the file's.** A file's `status` and claim are
honored when the item is first filed and ignored afterwards; a checkout is a
snapshot and cannot assert where an item *is*. `priority` (`now` / `next` /
`later`) is the opposite — a judgement, authored in YAML and reviewed in a
diff.

**4. A finished item is deleted, not archived.** `roadmap prune` removes done
items from the files and the store. The record of what was done is the report
and the commit; a done column is a second, worse copy of both.

**5. Blocking is stated, not implied.** `blocked_on` is for an item that cannot
start until another finishes. Use it for the real dependency — a paid re-run
blocked on the instrument review that decides whether it would buy the same
artifact twice — and not as a ranking.

## Arcs

An **arc** is a long question. Here that is one per experiment, plus
`lab-practice` for how the lab itself is run. Items point at an arc with
`arc: <id>`; arcs live in [`arcs/`](arcs/) and render to
[`../ARCS.md`](../ARCS.md).

An arc's state is derived from its items. Three states may be *declared* —
`closed`, `blocked`, `dark` — and each needs `state_evidence`, because each
says something the items cannot: that somebody checked and the tail is empty,
or that the blocker is outside the graph entirely. `closed` is declared rather
than derived for a reason worth knowing: after `prune`, a finished arc and an
arc nobody ever filed items for are the same empty set.

An arc is not an experiment directory, and closing one does not close the
question — 004 is `closed` because its tail is empty, not because nothing could
reopen it.
