# 005 — deviations from the pre-registration

Written and committed **before the agent run**, in the same spirit as
`PREREGISTRATION.md`: a deviation declared in advance is a design choice, and a
deviation noticed afterwards is a result about the author.

Nothing in `PREREGISTRATION.md` is edited. Everything below is a departure from
it, with the reason, and with what it costs.

## D1 — the round budget is 5 submissions, not 21

The accepted pilot configuration is `n8-k4-s0.15-w2-a0.3-r20`: eight agents,
four goods, twenty talking rounds. The agent run uses **five submissions**
(`r0` before anyone has heard anything, then four rounds of talk-and-resubmit).

Reason: cost and wall-clock. Twenty rounds is `4 cells x 12 worlds x 8 agents x
21 = 8,064` model calls. Five is 1,920, which is about two and a half hours
of wall-clock on this four-core container at eight concurrent calls.

Cost: `budget_exhausted` becomes a much more likely classification, and the
pilot's calibration of "not pinned at the ceiling" (P3) does not transfer. The
classification still runs and is still reported, so a cell that ran out of
rounds is visible rather than silently recorded as disagreement.

## D2 — the primary metric is under-powered, and a paired secondary is
pre-specified here

Coordination rate at `TAU=0.10` remains **the** primary metric and is reported
first. At twelve worlds per cell its Wilson interval is roughly +/-0.27, which
cannot separate 0.40 from 0.60. It is reported anyway, with intervals, because
changing the primary metric after freezing it is the exact move this document
exists to prevent.

**Pre-specified before any cell was run:** the reading is carried by
**minimum dispersion reached**, `min_r D(r)` — continuous, defined on every
world including ones that never coordinate, and **paired by seed** across
cells. Paired on twelve worlds, with the same truth, the same private signals,
the same observation draw and the same hint in all four cells, this has real
power where a twelve-world rate has none.

Comparisons are by exact binomial sign test on paired worlds, the unit being
the world, never the agent-round.

## D3 — the model is Haiku 4.5, and this is a choice about the hypothesis

The lab's standing claim is that conventions matter **especially to newborn
agents thrown at a task**. A protocol that helps a weak deliberator and not a
strong one is a finding, not a failure, and running the cheapest capable model
puts the hypothesis where it is most likely to be visible.

Cost: the result is about Haiku 4.5 and does not transfer upward. A null on a
stronger model would be a separate experiment, and the design does not claim
otherwise.

## D4 — the hint is common, not private

`PREREGISTRATION.md` defers hint distribution to a later experiment and does not
cross it. The `hint` cells therefore have to pick one, and they announce a
single vector to every agent in the world.

The hint is `normalise(exp(log(truth) + N(0, 0.10)))` — informative, closer to
the answer than any private signal (`sigma = 0.15`), and **wrong**, so a
population that simply copies it agrees on something slightly false and pays for
it in metric 2.

Cost: a common hint is itself a coordination device, so `content only` is
expected to score very well, and `both` may ceiling. That is prediction 2 and it
is not evidence about the protocol either way.

## D5 — one retry on a malformed submission

An agent that returns unparseable output is asked once more with the same
prompt. A second failure is a `harness_failure` for that world, excluded from
every rate and counted separately, exactly as the pre-registration requires.

Reason: a JSON slip is a fact about output formatting, not about deliberation,
and the pre-registration already insists that harness faults never enter a rate.

Cost: the retry is invisible in the transcript record unless read for; the retry
count is reported per cell.

## D6 — run 001's calibration cannot be executed at pilot size, and its baseline number was wrong

*Written 2026-08-22, after the pilot, before the main run it affects.*

Two faults in `runs/001-does-the-channel-have-a-job.md`, both in the
calibration gate, both found by running the pilot the gate depends on.

**The baseline was misstated.** The record puts the screen's n=2 talk rate at
"~0.02 talk per trader-episode". It is **0.100** — 30 talk messages over 300
trader-episodes (50 rounds × 2 traders × 3 episodes). The record's number is
wrong by 5×, and it is a pre-registered comparison value, so it is corrected
here rather than edited there.

**The gate is underpowered by construction.** The pilot yields 8
trader-episodes (4 traders × 2 episodes). At the corrected n=2 rate the pilot
expects **0.80** talk messages; under the run's own hypothesis of 3× it expects
**2.40**. The pilot observed **0**, and P(0 | Poisson mean 2.40) = **0.091** —
not decisive at any threshold worth pre-registering. A gate that cannot
separate its two conditions is not a gate, whatever it returns.

So the calibration gate as written is **not passed and not failed: it is
unexecutable at the size specified**, and recording it as a pass would be the
exact failure `GROUNDING.md` warns about.

The pilot's other job was done: at 4 traders all four sessions started and
acknowledged (4/4), 28 exchanges settled across 2 episodes, 4 refusals, no
harness failure, and the clock proved survivable. That is what a pilot is for
and it is reported as such. Its efficiency numbers are not evidence.

**What changes:** the calibration is not carried at pilot size. Either it is
re-run at ~5 rounds of n=4 (about 60 trader-episodes: 6 expected under the
null against 18 under the hypothesis, which does separate them), or it is
folded into the main run, whose n=4 cell yields 144 trader-episodes and 14.4
expected under the null. Folding it in is defensible only because the counter
is already known to count — the screen recorded 30 messages with it, so it is
not pinned at zero by construction — and because the run's abandonment
condition ("talk stays near zero at n=4") does not require the instrument to
move, only to count. The 3× hypothesis does require power, and only the main
run has it.

Cost of folding it in: if the main run returns zero talk in both cells, the
abandonment conclusion is available but the 3× hypothesis is untested rather
than rejected, and the record must say so.

## D7 — run 002 aborted: the self-scheduling loop does not survive a long round

*Written 2026-08-22, after the run it describes, before any run that follows.*

Run 002 asked for one round of thirty episodes. It was stopped by hand at
episode 10. All four sessions had already ended themselves — T1 and T2 after
episode 3, T3 after episode 4, T4 after episode 8 — so 22 of the 30 episodes
had no trader in them.

**None of them failed.** No runtime error, no turn cap reached (it had been
raised to `40 × episodes` for exactly this run), no harness fault. Each ended
its session while claiming to have arranged to continue: "I've scheduled a loop
to maintain my trading strategy", "I'll continue this pattern through the
remaining 27 episodes when the wakeup fires", "The system is maintaining my
active status while I manage tokens efficiently". Two gave token economy as the
reason. No such schedule exists: a `claude -p` session ends when the model
stops calling tools, and nothing brings it back.

**This is not a new instruction gap.** The per-round text already says it, in
these words: "Nobody will prompt you, ever. Nothing will wake you up… if you
stop acting you have left the island for good", and "Never finish a reply
without having called `checkin` or `say`." The agents were told plainly and
stopped anyway.

What changed is the arithmetic. `checkin`'s `wait` is capped at **25 seconds**
by the MCP server. A ten-minute round — every round run before this one — needs
about **24** calls to stay awake for. A ninety-two-minute round needs about
**220**. The design asks an agent to spend two hundred turns doing nothing but
staying present, and at that price it rationalises its way out.

**Classification.** Neither "harness failure" nor "the agent chose silence"
fits, and forcing it into either would misreport it. The sessions ended by
their own action, which is behaviour; but the environment makes that ending
irreversible and requires 220 self-scheduled calls to avoid, which is a
property of the runtime and the clock. It is recorded here as a **feasibility
failure of the round length**, and run records should classify it that way
rather than folding it into either existing bucket.

**What it costs.** Any result about long rounds. The trajectory question run
002 was opened to answer — does anything converge given enough episodes — is
unanswered, and the thirty-episode design cannot answer it as written.

**What may not be done about it.** Adding anything that prompts, calls or wakes
an agent. That is the forbidden thing in the repo-root `CLAUDE.md`, it has been
built twice already, and a long round is not a reason to build it a third time.

**What may.** Shortening the episode so thirty of them fit in a wall clock the
loop survives — thirty episodes of 45s is 22 minutes and about 54 checkins,
inside the range that has always worked. That is a different run with a
different clock, and it needs its own record.

## D7a — correction to D7: the loop was not exhausted, and the arithmetic was not the cause

*Written 2026-08-22, same day as D7, before any run that follows.*

D7 says a ninety-two-minute round needs about 220 `checkin` calls and that "at
that price the agents rationalise their way out". The second half is not
supported by the record and is withdrawn.

**They never approached 220.** T1's last act was at 11:57:54, roughly **seven
minutes** into the episodes, at **episode 3 of 30** — on the order of 25–30
calls. That is the same number every previous round used: three episodes plus
the acknowledgement window is eleven minutes, and agents have always survived
it. T1 stopped almost exactly where a normal round would have ended. T4 ran to
episode 8 and wrote 66 board messages, three times T1's span, so there is no
ceiling being hit either.

**What the sessions actually say** is that each was reasoning about the
announced span, not about running out of anything: "the remaining 28 episodes…
minimizing the cognitive overhead of monitoring and responding to every
proposal" (T1), "through the remaining 27 episodes when the wakeup fires" (T2),
"I'll maintain this through episode 30" (T3). T4 computed the round's end time
correctly and stopped regardless.

**Three candidates remain, and D7 named none of them.**

1. *Anticipation of the count.* Told thirty episodes up front, they treat
   twenty-seven more repetitions as something to delegate rather than perform.
2. *Strategy convergence.* The screen's clearest finding was that good rounds
   lock a pattern in early and replay it unchanged. By episode 3 these traders
   had theirs. "I've scheduled a loop to maintain my trading strategy" is an
   agent trying to say *keep doing this*, which the runtime cannot express —
   the behaviour the design rewards is the one it has no way to represent.
3. *Wall-clock fatigue.* The timings do not support it.

**What this costs the proposed fix.** D7 ends by offering thirty episodes at
45s as the available remedy. That holds the count at thirty and only shrinks
the clock, so if (1) or (2) is driving this the agents quit at episode 3 again,
two minutes in, and the run buys nothing. It does separate (3) from the others:
quitting near episode 10 would mean duration, quitting near episode 3 would
mean duration was never the mechanism. That is worth knowing and is worth one
round, but it must be run for that question and not as a repaired trajectory
probe.

**Standing.** The classification in D7 — a feasibility failure of the round
length, neither harness fault nor an agent choosing silence — still holds. Only
the stated cause is withdrawn.

## D8 — run 003 hides the round's length from one cell, and gives another a hint

*Written 2026-08-22, before the run it affects.*

Run 003 is a manipulation check on whether a long round is impossible for these
agents or impossible as this harness presents it. Two of its three cells depart
from the frozen setup, and both departures are recorded here rather than made
quietly.

**`persist-nocount` withholds the episode count.** The frozen per-round text
says "This round is N episodes long"; the manager's schedule says "N episodes,
Xs each"; every episode opens with "episode k of N". In this cell all three are
replaced: the instructions say only that the manager will announce what is
scheduled next and will say when the round is over, the schedule names no
total, and episodes are announced five at a time. Nothing else changes.

This is a **timing** change, which the standing decisions permit the system to
make — it alters what the manager announces and when, not what any agent should
produce, offer or accept. It is a deviation because it edits text that was
frozen, not because it crosses that line. Two offline gates check the count is
absent from the instructions, the schedule and the announcements, and that the
other two cells still state it.

**`persist-improve` adds a domain instruction.** `stimuli/persist/improve.md`
tells traders to treat each episode as an attempt to beat their last. That is a
hint in 005's sense — the thing the experiment otherwise holds fixed — and it
is legitimate here only because this run is a ceiling test. The file says so in
its own header. **Nothing measured in that cell may be cited as evidence about
deliberation protocols**, and it is not frozen.

**The confound, stated in advance.** "Improve on your last episode" implies
more episodes are coming, so `persist-improve` carries part of
`persist-nocount`'s mechanism. The fourth cell that would separate them was
dropped to save four sessions. If `improve` sustains and `nocount` does not,
the finding is that *a reason to continue* matters — not which reason.

**Cost if this is wrong.** If the hidden horizon leaks anywhere unchecked, the
cell measures nothing and the run's central comparison is void. That is why the
leak is gated offline and the board is searched for the count afterwards.

## D9 — run 004 has the manager announce the time remaining

*Written 2026-08-22, before the run it affects.*

In `idle-tick` the manager posts one line every 30 seconds inside an open
episode: "Ns remain in this episode." Nothing else about the cell differs from
`idle-long`.

**Why it is not the forbidden thing.** The standing decisions permit the system
to enforce timing and forbid it to drive: the manager "never tells an agent to
do anything and never asks an agent for anything". A tick is addressed to
nobody, names only the clock, and requests nothing; an agent may ignore every
one of them. It is the same kind of line as "episode 3 is open for 180s", which
the manager already posts, at a higher frequency. Two offline gates check that
only the one arm ticks and that the wording contains no agent name and no verb
asking for an action.

**Why it is still a deviation.** It changes what an idle `checkin(wait=25)`
returns — content instead of a timeout — and that is precisely the mechanism
under test. A reader should be able to see that the manipulation works *through*
the agent's waiting behaviour, and decide for themselves whether that is a
timing change or a nudge. It is recorded here so that judgement is available
rather than buried.

**Named risk.** Six ticks per 180s episode add to a board that carried about 37
messages per episode at four traders. If an agent's cost of reading history
rises enough to change its behaviour, the cell has moved two things at once.
Message counts per cell are reported for that reason.

## D10 — run 004 relaunches a session that never joined, once

*Written 2026-08-22, after two false starts of run 004 and before the run
proper.*

Run 004 was launched twice and stopped twice without collecting data. Both
times a session exited within the first minute having never posted to the
board, and both times it changed the population of one cell.

The shape is identical in every instance seen so far. The session addresses the
operator instead of calling a tool — "Ready when you approve the Switchboard
access", "What would you like me to do?" — and exits. It is not a harness
failure: the tools are allowed and its neighbours in the same cell use them in
the same second. It is not the behaviour the persistence runs measure either,
which is a trader who acted and then stopped. It is a session that never
started, at a rate of roughly one in ten launches.

**Why it cannot be left alone.** In the first false start it removed a trader
from `idle-long`, the reference cell, leaving three traders against four. A
quieter board is exactly the manipulation under test, so the confound pushed
the reference cell toward the result the hypothesis predicts. In the second it
hit `idle-tick` and pushed the other way. Either way one cell is measuring a
different population, and the difference is the size of the effect.

**What the harness now does.** During the acknowledgement window only, a
session that has exited and whose trader has never appeared on the board is
relaunched **once**. The manager says so on the channel, the abandoned log is
kept as `session-abandoned.log`, and the relaunched traders are recorded per
round as `relaunched`.

**Why this is not the forbidden thing.** The runner already starts sessions;
this starts one again after it failed to join. Nothing prompts, calls or wakes
a live agent, and the rescue stops the moment the first episode opens — after
that, a session that stops has taken part, and its stopping is data rather than
a fault. `spoke` is the discriminator, and it is gated offline.

**What it costs.** A relaunched trader joins late, with less of the
acknowledgement window than its neighbours. That is recorded per round rather
than corrected, and a cell whose result depends on a relaunched trader should
be read with that in view.

## D11 — run 005's treatment is deliberately impure

*Written 2026-08-22, before the run it affects.*

`stimuli/max/talk.md` mixes what 005 was built to separate. It encourages
talking, disclosing needs and capabilities, asking, naming a rate rather than
only goods, improving an offer rather than taking the first, and choosing
production with intended trades in mind. Protocol and hint at once, and more
besides.

That is the point rather than a compromise. Four runs have gone into why
sessions stop and none into whether text changes anything, and the cheapest way
to find out is to try the strongest text available before spending on a design
that separates ingredients. If a text this strong moves neither talk nor
efficiency, the 2×2 has nothing to decompose and that is worth knowing for
forty sessions.

**What may not be claimed from it.** Nothing about deliberation protocols
specifically, nothing about hints specifically, and nothing about which
ingredient did any work. A positive result licenses a decomposition run; it is
not itself evidence for any component.

**The manipulation check is part of the design, not a nicety.** If talk does not
rise in the treated cell, the text did not take, and a null then says nothing
about what the text describes. Talk per trader-episode is reported beside the
primary metric and never in place of it.

**Not frozen.** The file carries that in its own header, alongside the
statement that no result from it may be reported as evidence about protocols.

## D12 — run 006 adds an implication, not a fact, and holds the timing fix constant

*Written 2026-08-22, before the run it affects.*

`stimuli/probe/constant.md` states no fact the base instructions do not already
carry. The base says "Your capacities and tastes are the same in every episode
of this round, and so is everyone else's". The block draws the consequence:
that knowledge about a trader keeps its value, that early episodes buy
information and later ones should spend it, and that a poor rate reflects costs
that do not move.

It is a **domain instruction** and a run using it may not be cited as evidence
about deliberation protocols. It is not frozen, and its own header says so.

**Two changes were in flight and are deliberately not conflated.** PR #23
replaced relative countdowns with absolute UTC deadlines. Both cells of run 006
carry that fix, so it is constant between them and cannot explain a difference
between the cells. Separately, `probe-bare` re-measures run 005's control under
the fix, on the same three islands, which is the only way to see what the fix
itself did — a weaker across-run comparison, reported as one.

**Cost if the separation fails.** If anything other than the deadline format
differs between run 005 and this run, comparison 1 measures that instead. A1
names it and the commits are diffable.

## D13 — The hub 502'd fifteen minutes into run 006, and the run died with it

**Written after the abort, before the relaunch. 2026-08-22.**

Run 006 launched at 18:22 UTC and stopped at 18:36. Preflight was green and the
sessions were live; what failed was the hub's gateway, which answered one of
the manager's `history` reads with a Cloudflare **502 Bad gateway**. That
exception propagated out of `drain()`, out of `wait_until()`, out of the thread
pool, and killed the process — taking all six rounds, not the one round whose
read had failed. Nine agent sessions were left orphaned and were killed by
hand. The hub answered 200 again minutes later.

**This is a harness failure, classified as one, and it produced no data.** No
round record was written; nothing from the 18:22 attempt is scored, cited, or
counted in any denominator. Run 006's numbers come entirely from the relaunch.

**The fix.** `Manager._history_with_retry` retries a transient read — no status
or 5xx — four times at 2/4/8s. A read is safe to repeat: history is refetched
whole and deduplicated by message id, so a retry cannot double-count or lose a
message. A hub that is still refusing after the last attempt still raises: a
manager that cannot read the board cannot score it, and swallowing that would
fabricate an empty episode. Writes are **not** retried — a repeated `say` would
duplicate an announcement on the board.

Retries are counted in `drain_errors` and written into every round record, so a
run that limped is distinguishable from one that did not.

**Why this is not a design change.** It touches timing and transport only. No
price, role, trade or production decision is affected, and no malformed message
becomes a well-formed one. The relaunch is the same specification, the same
seeds and the same stimuli as the aborted attempt, under a new run stamp.

## D14 — A solo trader is given text that speaks of other traders

**Written before run 007. 2026-08-22.**

Run 007 puts one trader on a board with no counterparties, to measure what an
agent alone reaches against the autarky optimum every earlier run has scored
against. The base instructions are handed to it **unchanged** — they still
describe other traders, proposing and approving.

**Why not write a solo variant.** Two reasons, and the second is the binding
one. First, the point of the run is to measure the same agent under the same
instructions with the population removed; rewriting the text would change two
things at once and the number would no longer speak to runs 003–006. Second,
run 006 closed the question of whether added or altered instruction text helps,
and it closed it in the negative — composing a new block here would be exactly
the move that run's stopping rule forbids.

**The cost.** A trader may spend episodes waiting for counterparties who do not
exist, and produce less than it otherwise would. That is named as A3 in the run
record: if it happens, it is reported as this impurity biting, not as an agent
failing to allocate labour. The roster is what tells the trader it is alone;
the manager does not announce it, because announcing it would be the system
making a decision the agents should read off the board themselves.

**What is not affected.** Nothing about production settlement changes: same
parser, same budget rule, same refusals (A4). The island is still drawn at four
agents, so the trader's capacities, tastes and autarky optimum are the ones it
had in runs 005 and 006 (A2).

## D15 — A secondary measure added to run 007 after it opened

**Written 2026-08-22, while run 007 was in its first wave and before any of its
data had been read.**

Run 007's record was committed with solo capture as its primary and a list of
secondaries that did not include the MRS/MRT gap. The gap was added afterwards,
and this records that honestly rather than letting the record read as though it
had been planned.

**What was added.** For each production act, the per-good log gap between the
payoff ratio `(α_g/x_g)/(α_0/x_0)` and the cost ratio `capacity_0/capacity_g`.

**Why it is not a new hypothesis.** The two ratios are equal exactly when an
agent produced its own optimum — the tangency condition, verified in
`tests/test_solo_floor.py`. So the gap is arithmetically implied by the primary:
it is zero precisely when solo capture is 1, and it carries direction where
capture carries only magnitude. It cannot turn a negative primary into a
positive finding, and no threshold is attached to it.

**Why the timing is safe.** It was written before any of run 007's boards were
read, and its behaviour is fixed by tests on synthetic bundles rather than on
the run's data. The hypothesis and the threshold in the record are untouched.

**Where it came from.** The owner asked what the payoff ratio adds to the cost
ratio; the answer — that at the optimum it adds nothing, and away from the
optimum it names the direction — is the measure. It is also written up in
`PROPOSAL-ratio-disclosure.md`, which belongs to a later experiment.
