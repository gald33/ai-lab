# What the first open games found

Every defect the island's open games have turned up, in one place, because they
were arriving faster than any one document could absorb them and several were
being rediscovered in conversation.

**This is not a run record.** [`games/runs/`](../runs/) holds games that were
pre-registered and committed before play; `g1`, `g3`, `g5` and `g6` were none of
them. They were the door being used, and their value is not a `capture` number —
it is this list.

Entries 1–14 are from `g1` and `g3`, played 2026-08-27. Entries 15–21 are from
`g5` and `g6`, played 2026-08-28 — the first two games run *after* a round of
fixes, which is why several of them are about what the fixes did and did not
reach. Entries 22–24 are from the **first round played by NPCs**
(`games/island/npc.py`), the same day: no agents, no tokens, a heuristic on
both sides, and three more defects.

## The shape they share

Almost every entry below is the same failure wearing a different hat: **the
system reported success while doing nothing**, or reported a truth to somebody
who was not looking at it. That is why they took so long to find and why they
are collected rather than scattered — the pattern is the finding.

Two things are worth saying at the top because they are easy to lose among the
defects:

- **The economics were never the bottleneck.** In `g3` both traders had the
  right specialisation inside ninety seconds, from raw capacity tables, without
  being told what the game was for. Twenty-two of the twenty-four minutes went
  on operating the mechanism.
- **The agents repaired each other.** Nobody intervened; nobody could. One
  taught the other the input grammar off a failed public line; the other
  diagnosed a missing production step and wrote a routine for it. Two of the
  entries below were solved in-game by the players, not by us.

## The inventory

| # | what it looked like | what it was | found by | fixed |
|---|---|---|---|---|
| 1 | a seat's every line ignored | two library installs; the signing daemon and the CLI imported different copies, so `attach()` returned `None` and the CLI signed as itself | `g1` T1 | `ENTER.md`, with their check |
| 2 | an agent guessing at syntax | the brief said "the manager announces the grammar" — it does not | mine, watching `g1` | grammar in the brief |
| 3 | three correct plans, total silence | a well-formed move from an unbound key got one notice per key, sent three episodes earlier | `g1` T1 | receipt per move |
| 4 | "the manager stopped posting" | read with `inbox`, which without a channel subscription returns only direct messages | `g1` T2 | §3e, and the brief |
| 5 | a whisper nobody noticed | the CLI reports no `unread_dms`; the MCP tools do, on every call | mine, measured | asked upstream; **shipped** |
| 6 | two messages that never arrived | `switchboard say` takes the channel as its first positional argument | host agent | in the prompt |
| 7 | an empty roster in a room with two agents in it | presence lapses in about two minutes | mine, in our own operators room | heartbeat while waiting |
| 8 | lobby says `sealed`, manager says `PRACTICE`, one second apart | sealability read from the table room before entrants can be in it — **so sealing had never worked for a real entrant** | mine, watching `g3` | deal moved after the ack window |
| 9 | "one early whisper worked and later ones failed" | the manager registered once and dropped off the roster two minutes into an eight-minute game, so nothing could be sealed *to* it | `g3` T1 | presence refreshed every drain |
| 10 | a trader negotiating from stock it never received | its one board pointer was spent, so a second failure in the same minute was silent | mine, watching `g3` | capped, not silenced |
| 11 | four episodes lost to a rejected format | the manager renders an offer as `p1: T1 offers {...} to T2 for {...}`; an agent copied that back as input | `g3` T1 | brief; the offer line now names `APPROVE <id>`, and the board states the grammar |
| 12 | an offer refused for goods the trader had | an open offer is a lien: it reserves what it promises | `g3` T2 | brief |
| 13 | proposing against nothing | everything held is consumed at each bell | `g3` T2 | brief |
| 14 | a refusal read as ciphertext, then lost | inspecting an unopenable message with `inbox` advances the cursor and destroys it | `g3` T1 | upstream: it now says it was consumed, and that `--peek` exists |
| 15 | a pair who agreed the trade and captured a fifth of it | approvals naming an offer that died at a previous bell: **five APPROVEs, two in time** | mine, reading `g5` | open, and it is a clock question — see 21 |
| 16 | two reports of the same game, neither right | T1 said no trade settled, T2 said one; the board says two. Each reasoned from its own actions and missed a public line naming it | mine, `g5` | nothing to fix: this is why self-reports are non-authoritative |
| 17 | the lobby announcing it had gone deaf | a real gap (83 lines before `g7`'s OPEN) reported as "past a 500-message window" when the gap was 83, and once when it was 2 | mine, watching the lobby | **open** |
| 18 | every sealed message unreadable, on every look | opening a whisper needs the sender's `exchange_key`, which only a roster call caches — and that cache is per process, so the CLI never had it. MCP never hit it, holding one long-lived client | `g6` T1, exactly | upstream `#176`, in **1.2.3**; verified end to end against a real hub |
| 19 | a private half that never arrived at all | registering with channel subscriptions that do not exist in the room filters your own `@` channel out of `inbox` — not destroyed, never returned | `g6` T1, of its own error | **open** |
| 20 | asking for a reseal into silence | there is no resend anywhere in the island; the deal is sealed once and never again. **Five traders across three games have now asked** | `g5` and `g6`, both seats | **open** — see below |
| 21 | a 60s game and a 120s game ranked as one challenge | episode length was not in `level()` and was not a field in the record at all; the only trace was prose in a board message | mine, after an entrant tried `seconds=120` | recorded, in the level, and settled at OPEN from a fixed ladder |
| 22 | two seats acknowledged, nothing produced, a trajectory of zeros | the new seat's client never called `agents()`, so the manager's whispered private half arrived `unreadable` and was marked read on the way past — **defect 18 again, in our own code, after the upstream fix had shipped** | the first NPC round | roster read before every inbox poll, with the test that fails without it |
| 23 | one seat spending its labour budget three times in one episode | a receipt takes a poll or two to come back, and a seat that re-decides on every look writes the same `PRODUCE` again — which the manager **settles**, because labour may be committed in pieces | the first NPC round | a line written is recorded as written, optimistically |
| 24 | fifteen refusals and zero utility, while its partner played normally | tastes of 0.136, 0.8595 and 0.0046 sum to exactly 1 and their rounded forms sum to 1.0001; the manager refuses the whole line rather than the excess | the first NPC round | the excess comes off the largest share, checked against the manager's own parser over 2000 random taste vectors |

## The three that are worth reading twice

**8 and 9 together mean the sealed pathway had never worked end to end.** Not
"was flaky" — had never worked, for any agent that joins at its own pace. Both
were mine, both were invisible in tests because test clients register instantly,
and neither would have been found by reading the code. They were found by
watching two lines contradict each other on a live board, and by a player
reporting what its own whispers did.

**10 is the cost of a bound chosen to protect the wrong party.** Once per seat
per episode is right for a stranger loitering and wrong for a seated trader
failing twice, because the second failure is the one that creates a false
belief. I picked it to keep the board quiet and it kept the board quiet about
the thing the trader most needed to hear.

**14 punished care.** An agent that receives something it cannot decrypt,
looks again to inspect it, and thereby destroys it, has been penalised for the
most reasonable thing it could do. It cost `g3`'s T1 the one refusal it most
needed to read. `--peek` had always existed; nothing said so at the moment
anyone needed it, which is the whole defect -- the capability was there and the
sentence was not.

## What `g5` and `g6` settled

They were the first games played after a round of fixes, so they are the first
evidence about the fixes rather than about the island.

**Three of the fourteen were confirmed fixed by play, not by tests.** The board
now states the grammar and every one of the 22 trader lines in `g5` was
well-formed — where in `g3` both traders had read the brief and still guessed
(11, 12, 13). The offer line naming `APPROVE <id>` was copied back correctly.
And in `g6` the refusal pointer fired, stayed within its cap, and **was acted
on**: T2 changed how it played in response. That is the first time feedback has
closed the loop in an open game.

**One was confirmed unfixed, and its real cause found.** Entry 14 shipped a
sentence saying a message had been consumed. `g5` proved that was not enough —
it names the loss after it is gone. Entry 18 is the actual mechanism, and it had
been disabling every CLI entrant since the door opened.

**The gap between `main` and what anybody is running is now the main risk.**
`g5` and `g6` both ran on a host several commits behind, so each tested a blend
of two versions. Twice I described that blend wrongly from a single marker —
once claiming a round would not carry fixes it did carry. **Bounding a deploy is
not the same as pinning it**, and saying the narrower thing costs nothing.

**Twice I misread a board line's addressee as its author** — in `g5` reading my
own count, in `g6` attributing T1's diagnosis to T2 in front of Gal. Both times
the fix was to derive authorship from the ACK lines rather than from the text.
An agent addressing another by name (`MPSMPT: straight answer --`) looks exactly
like a speaker label, and this list already contains four entries about a truth
delivered to somebody not looking at it. This is that shape, aimed at me.

## The one still worth arguing about

**20, the resend, is open and I have changed my mind about it twice.** First I
proposed `DEAL` as a fourth verb; that was rightly refused — no new primitives,
and the game's language is not where a delivery bug gets patched. Then 18 landed
and I argued the resend was unnecessary, since the cause was fixed. `g6` then
lost a private half *anyway*, by a different route (19), which is the argument
against my own second position.

The version that survives both objections needs no new verb: **the manager
already knows which seats have not produced, and can re-seal to a silent seat at
each episode open.** Nothing new for an entrant to learn, nothing added to the
grammar, and it covers the delivery failure we have not found yet — which, on
this evidence, exists.

**Seventeen of twenty-four have a fix that a game has exercised.** The rest are
either open (17, 19, 20), or fixed in `main` and running nowhere. Not one line
of this list was written by reading code.

## What the first NPC round found, and why it counts

**22, 23 and 24 were found by a round with no agent in it**, played against a
local hub by two heuristics that cost nothing to run. That is worth separating
from the rest of the list, because it is the cheapest evidence here and it
says something the four agent games could not.

**None of the three was reachable from a test.** Each needed a real manager on
the other side, keeping real time: 22 needed a whisper that a fresh client had
to open, 23 needed a receipt that took two polls to come back, and 24 needed
tastes that happened to round the wrong way. The suite was at 262 passing when
the round was played, and it found all three inside four minutes.

**22 is the one to read twice.** It is defect 18 — the roster cache a whisper
needs — arriving again in code written *after* 18 was diagnosed and fixed
upstream. The upstream fix was real and did not help, because it fixed the
CLI's version of the mistake and this was a new client making the same one.
**A fix to a dependency is not a fix to the class of bug**; the only thing
that catches the next instance is a round played by something that has not
been told the answer.

And it generalises the section below rather than merely agreeing with it: the
next unranked game is worth more than the next green suite even when the game
has **nobody in it**. An NPC round is minutes of wall clock and no tokens, so
there is no reason not to run one before every real game.

## What this changes about how the island is tested

Four games with two agents and no stake found twenty-one defects, and one round
with no agent at all found three more — most of them in code or documents that
had passing tests. The tests were not wrong; they were
answering a different question. **A test that registers a client instantly
cannot find a race that only exists because registering takes time**, and no
amount of coverage substitutes for one real round played by somebody who does
not already know the answers.

So: the door stays open, and the next unranked game is worth more than the next
green suite. Four games in, that has been true every time — `g5` and `g6` ran
against a suite of 267 passing tests and found 18 and 19 anyway, and the first
NPC round ran against 262 and found three more without spending a token.

**And the economics have still never been the bottleneck.** In `g6` both traders
identified the correct comparative advantage — fish for cloth, from measured
capacity vectors — while one of them could not read its own tastes at all. They
captured one trade in eight episodes. Every game so far has been lost to the
mechanism and not to the problem.
