# Deviations and amendments

Every departure from [`PREREGISTRATION.md`](PREREGISTRATION.md), dated, and
**written before the run it affects**. `PREREGISTRATION.md` points here and
this file did not exist until the first amendment needed it; nothing is
missing from before 2026-09-10.

A pre-registration is never revised in place. Each entry below says what the
frozen document says, what is now done instead, and what measurement moved it.
A threshold moved after seeing a number is not a threshold, so no entry here
moves one — **there is still no threshold in this experiment**, and there will
not be until H0b is authorised and run.

---

## A1 — 2026-09-10 · Rung 1 runs at 4 traders and 3 goods

**Affects:** rungs 1, 2 and 3. None has run.
**From:** run 002, rung 0b (`results/rung0b-curve.json`).

`PREREGISTRATION.md` names no table shape; the design's prose says "2–4
traders" and the game's default is 5 goods. Rung 0b swept all twelve shapes the
game allows and found **six of them cannot read the primary at all**: wherever
goods outnumber traders, the scripted convention arm sits at a zero-period
share of 1.000 for every δ including zero, because full specialisation covers
at most `traders` goods and Cobb-Douglas zeroes every agent on the rest.

The widest-reading shape is **4 traders × 3 goods** (span 0.678 in `sharpen`,
0.493 in `flatten`), and that is the cell. See README correction C4.

**What this does not claim.** The degeneracy is a property of the *scripted*
trader. NPC seats at 4 traders and 5 goods return a zero-episode share of about
0.13–0.19, not 1.0 (run 002, rung 0a), and model agents are not scripted
traders either. The shape is chosen because it is the one where the scripted
tier can calibrate, not because 5 goods is known to break the model tier.

## A2 — 2026-09-10 · The δ ladder runs on `flatten`

**Affects:** rung 3. It has not run.
**From:** run 002, rung 0b.

H3 predicts a cliff, and the frozen text does not say which perturbation
direction the δ ladder uses. Rung 0b shows the two are not interchangeable at
this table shape: `sharpen` moves the primary 0.227 → 0.525 between δ = 0 and
δ = 0.05 — a realised error of **0.021** — and then crawls to 0.905 across the
remaining seven rungs. `flatten` spreads 0.227 → 0.720 over the whole range.

So `sharpen` is a cliff detector with almost no resolution above its own first
step, and `flatten` is the ladder. Both are still reported; δ\* is estimated on
`flatten`.

**This is not H3 being confirmed.** H3 is a claim about *model* agents holding
a *shared* convention, and the scripted tier has no beliefs about other agents
at all — CS − CP is not measurable there at any δ. What rung 0b establishes is
that the content axis exists and which direction can resolve it.

## A3 — 2026-09-10 · H0a is not expected to return zero, and the reason is the wall clock

**Affects:** H0a, and the reading of every later "the harness contributes
nothing" claim.
**From:** run 002, rung 0a, and its serial control.

`PREFLIGHT.md` gate 2 said *"Expect exactly zero, and that is a pass … anything
above zero here is a defect to find, not a noise budget to spend"*, on run 001's
finding that NPC policies are deterministic given their seed. **That does not
hold at four seats.** Replicates of one identical cell differ, including at
`--workers 1`, which is the serial path run 001 itself measured:

| | seed 1 | seed 2 |
|---|---|---|
| replicate 1 | `capture` −0.2796, 12 settled | −0.5423, 9 settled |
| replicate 2 | `capture` −0.2836, 10 settled | −0.5295, 11 settled |

`results/rung0a-serial-control.json`, 4 traders × 2 episodes × 45s, workers 1.

The policies are deterministic; the **island is a wall clock**, and how many
moves land inside an episode is not. That is the island's design and not a
defect — `CLAUDE.md`: the bell rings anyway and the episode closes on the
clock. So H0a returns a real number rather than a zero, and it is a *harness*
number: still not the agent-sampling variance a threshold needs, and still not
a substitute for H0b.

Run 001's byte-identical result was measured at **two** seats, and is not
retracted for the cell it was measured in.
