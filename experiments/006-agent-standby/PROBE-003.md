# 006 — probe 003: does the container survive an hour of nobody holding it?

*Written before arming. `PROBE-002.md` is not edited; its confound is why this
exists and its rung 3 was deliberately left unarmed.*

## The one question

Probes 001 and 002 armed a timer inside the container and watched it fire. The
confound found at the end of 002 is that **the timer may be what kept the
container alive** — it runs as a task this harness tracks, and a session with a
tracked task in flight is plausibly not idle at all. Two rungs at 0s late is
what that looks like from outside, and nothing in either separates it from the
reading they were recorded under.

There is also no way to climb past it with a longer timer, because an alarm
inside a container needs a process to hold it. "An agent-held alarm" and "a
process the agent is paying to keep running" are one object. So the question
worth an hour is not about alarms at all:

> **With nothing running, does the container the agent lives in still exist an
> hour later?**

If it does, an in-container alarm *could* have survived it, and the open
question becomes what a quiet wake costs. If it does not, nothing inside the
old container survived, no amount of process-holding fixes that, and "the agent
keeps its own clock" is false on this substrate for a reason that is structural
rather than incidental.

## Method

**Hold nothing.** No background task, no timer, no poll. That is the whole
design and the only thing that makes it different from 002.

1. **Fingerprint, taken 20:41:43Z** — recorded here so the comparison cannot be
   quietly re-specified afterwards:

   ```
   boot_id=f1d1fbec-ce11-44b6-b0af-9915b69de759
   hostname=vm
   uptime=1897.26 (seconds, at fingerprint time)
   pid1_start=1787289509
   ```

   A copy sits in the session's scratchpad, which is itself part of the test:
   a fresh container has no such file.

2. **One server trigger, due 21:47Z** — about 65 minutes out. It is the only
   thing armed, and it is the reader, not the subject. Whether *it* fires is
   already known from 002; what it is for is to bring the agent back to look.

3. **On the wake, compare.** Same `boot_id` and a `uptime` about 3,900s larger
   → the same container, still running, with nobody holding it. A different
   `boot_id`, or a missing scratchpad file, or an `uptime` that restarted →
   this is a new container and the old one is gone.

## Pre-registered readings

- **Same container** → this substrate keeps a session's container alive across
  an idle hour. An agent-held alarm is *possible* here; the arc's question
  becomes cost, and the honest next number is what a quiet wake is worth
  against ~30 wasted turns a month.
- **Fresh container** → availability cannot be held by anything inside the
  agent. It is lent by the runtime, and `agent-standby`'s central claim is
  false on this substrate. That is the arc's outcome 2, and it retires the
  design rather than leaving it looking shippable.
- **Same container but the scratchpad is gone** → recorded as its own case,
  not folded into either. It would mean the process survived and its storage
  did not, which is a different and worse promise than either reading above.
- **Ambiguous or contaminated** → see below. Reported as a failed probe, in
  the denominator.

## Contamination, named in advance again

This session watches `gald33/ai-lab#54`. A comment, a review or a merge wakes
it, and a session that runs a turn is a container being kept alive by that
turn. **Any wake before 21:47Z marks this probe contaminated and it is re-run**
— including a message from the operator, which is the likeliest of the three.

The subscription stays on. Dropping a watch to protect a measurement makes the
measurement about the person taking it.

## Contaminated once, before it began — and re-armed

The first arming was contaminated within three minutes by an operator message
(a request to see the lobby running), which is exactly the case the section
above named as likeliest. Per that section it is **re-run rather than kept**,
and the count below says 2 armings for 1 probe.

Re-fingerprinted **20:43:09Z**, same container as the first arming — `boot_id`
unchanged, `uptime` 1982.85s:

```
boot_id=f1d1fbec-ce11-44b6-b0af-9915b69de759
hostname=vm
uptime=1982.85 (seconds, at re-fingerprint time)
pid1_start=1787289509
```

The reader stays where it was, **21:47Z**, which is now about 64 minutes out.
The clock that matters is the gap since the last thing to touch the session,
not the gap since the file was written.

## Contaminated twice, and the design corrected rather than re-armed again

A second operator message arrived at 20:48Z, five minutes into the second
arming. Two contaminations out of two says something the probe should have
been built for from the start: **an interactive session cannot hold a quiet
hour**, and re-arming into one is just buying the same contamination again.

So the reader moves, and the reading rule changes with it:

- **the reader is a long one** — six hours out, not sixty-five minutes. It
  will land after this session has stopped being used, whenever that is,
  rather than betting on a gap inside it;
- **the measurement is taken at read time from two things that are both still
  observable then** — the container's identity (`boot_id`, `uptime`,
  the scratchpad file) and **the gap since the last thing that touched this
  session**. Neither needs the gap to have been planned in advance;
- **so an interruption no longer ruins it.** Every message simply resets the
  clock the read will measure against. If the reader finds a gap over an hour,
  the reading holds; if it finds twenty minutes, it says twenty minutes and
  the probe is re-read later rather than thrown away.

That is strictly better than what was armed at 20:41Z, and the reason it was
not built this way first is worth keeping: the design assumed the quiet was
something to arrange, when it was something to *observe*.

## Denominators

Probes armed: 3 (two contaminated by operator messages; the third is a
corrected design, not a third attempt at the same one). Read: to be filled in. This section is appended to, never
rewritten.

## Outcome

*(appended after the read — empty until then)*
