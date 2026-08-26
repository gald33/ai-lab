# ARCS.md — what's in flight, at arc level

<!-- GENERATED FILE — DO NOT EDIT BY HAND. Regenerate with `roadmap sync`. Edit roadmap/arcs/*.yaml instead. -->

The narrative layer above `roadmap/ROADMAP.md`: *why* each theme is still open. Work items live in the roadmap graph and are listed per arc below; the prose here is the arc's own, and is the one place a multi-PR theme gets explained rather than enumerated. For when this was last regenerated ask git — `git log -1 --format=%cI -- ARCS.md` — because nothing here derives from the clock or from a graph-wide total, so two branches editing different arcs merge cleanly.

## Legend

| State | Meaning |
|---|---|
| 🟠 open | Open tail — unfinished items, or a stated unresolved decision. |
| 🔵 blocked | Nothing startable — every unfinished item is blocked, or the blocker is outside the graph and was declared. |
| 🟡 dark | Code merged, flag off **in prod env**. Declared, never derived. |
| 🟢 closed | Tail is empty and somebody said so. Declared, never derived. |

`dark`, `closed` and `blocked` may be **declared** by a human with dated evidence, because each is about something the items cannot show: an environment flag, a closure whose finished items `prune` has deleted, or a blocker outside the graph entirely. `blocked` is *also* derived when every unfinished item is itself blocked. `open` is never declared — it is the fallback every check fires on, so stating it would only silence them.

## 🟠 Open

### 🟠 006 — can an agent hold availability across time, and what is actually holding it?

`agent-standby` · 1 item(s), 1 startable

`https://github.com/gald33/Lucille/blob/main/docs/architecture/agent-standby.md`

Built in Lucille, and it does not work in the only environment it has been
tried in. That is the arc: the mechanism exists, one half of it is verified
against a live system, and the other half — the part that makes it more than
a data structure — has never once fired.

The question came the way this repo's questions are supposed to. Lucille's
agents coordinate through a hub whose records all expire in minutes, which
answers "who is working right now" and cannot answer "who is on call". A
standby layer was built for the second question: an agent writes down when it
will next be awake, and keeps its own alarm rather than letting anything
outside it hold the schedule. The hub side works. The alarm has not rung yet,
and until it does the interesting claim is untested.

What makes it worth an arc rather than a bug is that the failure is
informative in a way the design predicted about itself. Standby working and
standby being dead produce the *same* observable — silence — which is why the
design writes down a next-wake time at all, and that detector is the half that
has now fired twice on a real absence. So the arc splits cleanly: a promise
with a timestamp is verifiably enough to detect a dead agent, and whether
anything can keep such a promise is open.

The second half is where the real question is. "The agent keeps its own clock"
sounds like a property of the agent and is not — it is a property of whatever
process the agent happens to be running inside. Move the same agent to a
different harness and the claim changes truth value with nothing about the
agent having changed. Working out what the substrate actually has to provide,
and whether availability is a thing an agent can hold at all or only something
its runtime can lend it, is the arc.

| item | status | priority |
|---|---|---|
| `006-standby-alarm-has-never-rung` | ready | next |

### 🟠 005 — does a content-free deliberation protocol help agents coordinate?

`deliberation-protocol` · 7 item(s), 3 startable

`experiments/005-deliberation-protocol/README.md` · `reports/2026-08-21-005-deliberation-protocol.md`

Four cells run with agents; the headline is a null. The protocol moved
nothing on top of a matched placebo, and nothing at all on top of a common
hint (12/12 ties). The arc stays open because the report's own first threat
to validity says the null is most likely a design choice: five rounds is not
the twenty-one the pilot accepted, and the protocol is a procedure over
rounds. The tail is the instrument review the report named, and then the
re-run that would make the null a result about protocols rather than about
five rounds of Haiku.

| item | status | priority |
|---|---|---|
| `005-display-precision-artifact` | done | now |
| `005-render-precision-fix` | ready | now |
| `005-rerun-at-twenty-one-rounds` | blocked | now |
| `005-word-cap-fits-the-protocol` | done | now |
| `005-episodes-to-threshold` | ready | next |
| `005-transport-retry-audit` | done | next |
| `005-paired-statistic-choice` | ready | later |

### 🟠 007 — if the answer is handed over, do they take it, and what survives when it is taken away?

`execution-ceiling` · 2 item(s), 2 startable

`experiments/007-execution-ceiling/README.md` · `reports/2026-08-24-hypothesis-ledger.md`

Opened to answer a feasibility question the earlier nulls could not: is a
good outcome reachable on this island at all? Handed the competitive
equilibrium, traders produced it 214/214 and four independent replicates all
beat the control — so yes, and the earlier nulls were not measuring an
impossible task.

It then turned into a measuring instrument's own post-mortem. Replicating one
cell four times with nothing varied gave a between-run sd of 1.03 on captured
gain, against pre-registered thresholds of 0.10–0.15. Every paired difference
this lab had reported was inside its own noise.

The arc's tail is what survives that. Two things do: counts of whether agents
did a thing at all, which are lopsided enough that noise cannot turn them
over, and the plan-versus-control difference, which is the only one replicated
four times. The open work is finishing that comparison honestly and deciding
whether the ruin reduction from the decomposed blocks is real or is the
control moving under it.

| item | status | priority |
|---|---|---|
| `007-replicate-the-control` | ready | next |
| `007-third-pass-on-ruin` | ready | next |

### 🟠 How the lab itself is run — process, records, and the tools that hold them

`lab-practice` · 2 item(s), 0 startable

`CLAUDE.md` · `CONTRIBUTING.md` · `reports/README.md`

Not an experiment. This arc holds work on the lab's own practice: the
standing decisions in CLAUDE.md, how runs are pre-registered and reported,
and the small amount of tooling that survives the tools/README.md rule (a
utility moves in when a second experiment needs it, not in anticipation).

| item | status | priority |
|---|---|---|
| `lab-roadmap-adoption` | verifying | now |
| `lab-roadmap-core-0-2-0` | blocked | next |

## 🟢 Closed

### 🟢 002 — words, machinery, or disposition: which part of a value convention works?

`barter-conventions` · 0 item(s), 0 startable

**Declared `closed`.** Closed by decision on 2026-08-22 to focus the lab on 005. The tail was
WITHDRAWN, not finished: `002-tier3-run` was deleted unstarted. Tier 1 stands
as a result; Tier 2's numbers stay recorded as measuring the harness; Tier 3
stays designed, calibrated and unrun.

`experiments/002-barter-conventions/README.md` · `reports/2026-08-20-002-tier3-calibration.md`

Tier 1 is a result. Tier 2 is mid-flight with the harness still moving under
it, so most of its numbers measure the harness. Tier 3 is designed,
calibrated and unrun — and now closed in that state rather than run. The
calibration report is what a re-opening would start from.

### 🟢 003 — which promotion rule converges on the good solution rather than the lucky one?

`promotion-rules` · 0 item(s), 0 startable

**Declared `closed`.** Closed by decision on 2026-08-22 to focus the lab on 005. The tail was
WITHDRAWN, not finished: `003-tier2-design` was deleted unstarted, so the
question the experiment is actually about — a promoter choosing among
solutions a model wrote — stays unasked. Tier 1, the scripted tier, is
complete and reported and unaffected.

`experiments/003-promotion-rules/README.md` · `reports/2026-08-20-003-promotion-rules.md`

Tier 1, the scripted tier, is complete and reported. Tier 2 — the same
promoter over real instincts — is neither designed nor run, and is now closed
in that state. The open question is recorded in the experiment README, not in
an item.

### 🟢 004 — is 002's ruin about the convention, or about irrecoverable commitment?

`stock-and-flow` · 0 item(s), 0 startable

**Declared `closed`.** Run and reported: experiments/004-stock-and-flow/README.md carries results,
and reports/2026-08-20-004-stock-and-flow.md is the write-up. No unfinished
items are filed against it as of 2026-08-22. Declared rather than derived
because an arc with no items and a finished arc are the same empty set.

`experiments/004-stock-and-flow/README.md` · `reports/2026-08-20-004-stock-and-flow.md`

Answered: whether ruin survives per-period consumption decides whether 002's
finding is about conventions or about a world where a production commitment
can never be taken back.

### 🟢 001 — is coordination better reasoning, or less to reason about?

`switchboard-coordination` · 0 item(s), 0 startable

**Declared `closed`.** Closed by decision on 2026-08-22 to focus the lab on 005. The tail was
WITHDRAWN, not finished: `001-publish-results` was deleted unstarted, so the
run's data stays uncleaned and its analysis unwritten. The experiment
directory's own status line — run, not published, nothing below is a result —
remains the accurate description, and closing the arc does not turn it into
one.

`experiments/001-switchboard-coordination/README.md`

Run, not published, and now closed with that still true. The design and the
one preserved negative result are in the experiment directory; the numbers
are not, and no longer have an item saying they will be. Reopening means
filing the analysis item again, not re-running anything.
