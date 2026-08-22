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
