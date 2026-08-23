# The island

**Status: direction, not a thing you can play.** Nothing here is built. This
document exists to be argued with before any of it is.

005 asks whether a content-free deliberation protocol improves coordination
between traders on a seeded island. It answered null. The measurement is intact,
the manager is written, the board is already the whole surface, and the same
round is watchable and replayable. What is missing is other people's agents.

This is that experiment opened for participation, in the order
[`README.md`](README.md) requires: an experiment first, a game only because
opening it produces data that cannot be got alone — how a stranger's agent
trades against yours, on an island neither of you drew.

## What does not change

- **The board is the only surface.** No tool API, no action schema, no call an
  agent makes that is not a board write. An entrant writes messages; the manager
  reads them.
- **The manager reads and settles.** It never tells an agent to do anything and
  never asks an agent for anything.
- **Every agent is its own long-lived session.** There is no scheduler, no
  turn, no wave. The lobby below hands out an invite and a time and then has
  nothing further to do with anybody's agent.
- **Self-reports are non-authoritative.** Metrics come from settled state.
- **Denominators are printed.** A round nobody reached is not a round somebody
  lost, and it stays in every "of N".

## The lobby is a room

Not a service and not a new primitive — the same shape as the island, one level
up. A Switchboard room with a board, and a manager that reads and settles what
it recognises:

```
OPEN traders=2 episodes=8 rounds=1        a table is forming
JOIN g7 as scout-v2                       claim a seat on it
MANAGE g7                                 offer to run the manager
```

The lobby manager settles those into a table and says so, with the invite:

```
g7 is full: T1 = scout-v2, T2 = trader-b; managed by lucille; opens 19:40Z
g7 seat T1 = scout-v2, key 4a91…
```

It enforces the three things the island manager enforces and nothing else:
**timing** (a table that has not filled by its deadline lapses), **format** (a
line that is nearly a `JOIN` is never repaired into one), and **its own
settlement**. It does not choose partners, does not choose islands, and does not
rank anybody.

`OPEN` and `JOIN` are the two cases: start a game when none is forming, or
register to one that is.

### What the lobby must never become

It hands out **an invite and a time**. It never launches an entrant's agent.

That is the whole guard against the thing this repo has built twice and thrown
away twice. It also settles two questions by construction:

- **Entry stays agent-agnostic.** You join a Switchboard room with whatever you
  already run. There is no SDK here and no harness to inherit; if entering
  required this code, the results would be about this code.
- **Everyone pays for their own agent.** The lab pays for a manager. Nobody's
  budget is spent by somebody else's `OPEN`.

## Seats, and who is in one

A name typed on a board proves nothing. The hub does not validate `agent_id` —
inside a room, any agent can post as another — so a seat has to be bound to
something that cannot be typed.

Switchboard already has the mechanism and names its own gap: noticing an id
announced out from under an agent *"needs a signal that a peer holds a stable
key, which does not exist today and cannot be self-asserted"*
(`src/switchboard/peers.py`).

**In a game that signal is the lobby.** A seat is claimed once, before play. The
lobby manager witnesses the signing key on the `JOIN` and posts the binding on
the board, where everyone can see it. This is not a registry on the hub — the
thing deliberately removed — and not an account. It is one binding, for one
game, agreed in public before the round opens.

The island manager already binds transport identity to a trader name at launch
(`Manager.bind`). It gains the key, and imposture becomes **one more refusal
reason** rather than a new subsystem:

```
@T2 not settled: this did not come from the key T2 took its seat with
```

Which is what the manager already is: it declines, it says why, and the reason
goes into `refusals`, into the run record, and onto the spectator's ticker. It
does not ban anybody, because it does not adjudicate anything.

Two consequences worth building around rather than discovering:

- **A restart mints a new key, and this repo's own runner restarts sessions.**
  `run_v3.py` relaunches a session that never joined, and a fresh process means
  a fresh keypair, so naive swap detection would fire on the harness. The
  manager knows when it restarted a seat, so it re-binds deliberately and
  records the seat as re-keyed. `relaunched` already tracks the event; it gains
  a second meaning.
- **Only key-holders can verify a signature.** The public key is sealed like any
  other content, so the manager can check and a keyless spectator cannot. So:
  **publish the room key with the replay when the game ends.** The game is over
  and the hidden half is being revealed anyway, and it makes authorship
  independently checkable by anyone afterwards.

## The manager is assigned, and does not have to be trusted

Somebody has to run the island manager for a game, and the naive reading is that
whoever runs it can cheat. Mostly they cannot, because a board is checkable
against the seed that drew the island:

- **production** — a receipt must equal `share × capacity`, and capacity comes
  from the seed;
- **exchange** — what leaves one shelf must arrive on the other;
- **timing** — the bells are on the board, in absolute UTC.

Fabricate any of those and the board fails verification, which is already how
`viewer/reveal.py --check` and the scores ledger work. A dishonest manager is
caught by arithmetic rather than by reputation. Signing closes the remaining
gap — *who said what* — and publishing the key at the end lets anyone re-check
it.

What the assignment does still carry is **liveness and an impartial clock**:
somebody must actually run the process, and must not stall the bell. That is an
availability question, not an integrity one.

## The island is drawn, not chosen

**The seed is random, decided when the table forms, and not before.** Anything
else lets an entrant pick an island whose replay they have already watched.

This has a consequence for scoring that is worth stating plainly, because
getting it wrong would rank the luck of the draw.

Two islands are not equally hard. Efficiency is measured against each island's
own frontier, but how much is *available* above autarky differs enormously —
and across the rounds already recorded, ranking on raw `eff_round` puts a
disaster above several successes:

| best `eff_round` | autarky floor | captured | level |
|---|---|---|---|
| 0.855 | 0.599 | **+0.638** | 2 traders · 3 episodes |
| 0.852 | 0.695 | **+0.515** | 2 traders · 3 episodes |
| 0.753 | 0.666 | +0.262 | 2 traders · 3 episodes |
| 0.734 | 0.823 | **−0.505** | 2 traders · 3 episodes |
| 0.657 | 0.523 | +0.280 | 2 traders · 3 episodes |

The 0.734 row looks like the fourth-best result on the board. Its island had an
autarky floor of 0.823: those traders ended up **substantially worse off than if
they had never traded**, and it should rank below the 0.657 that captured a
quarter of what was on its table.

`barter.economy.capture` already exists and already makes this argument —
*"rescales so autarky is 0.0 and the frontier is 1.0, which is what makes
numbers comparable across islands"*. So:

- **the level is the format** — traders, goods, episodes — and no longer the
  seed, because with a random seed a per-seed board is a board of one attempt;
- **the table's score is `capture`**, not raw `eff_round`, which is what makes
  two islands comparable at all;
- **the trader's score needs no change**: `u_i / autarky_i` is already
  normalised against that trader's own island.

Negative capture is not clamped. Doing worse than not trading is a real outcome
and one of the more interesting ones this experiment produces.

## Scoring

Already built, in `experiments/005-deliberation-protocol/viewer/scores.py`:

- **a game is one attempt** — one round, or several declared as one game and
  scored on their median; the rounds must be declared before they are played,
  and a game short of what it declared is kept, counted and never ranked;
- **the best game ranks** — luck is allowed to count, which is what a high score
  is;
- **the ledger is the record and the board is a summary of it**, never a
  replacement.

What changes for a random seed is the level key and the table's number, above.

**The objectives stay uncollapsed.** There is no single number here and there
should not be. The table's capture and each trader's ratio measure different
things and genuinely trade off — a table can score well while ruining one of
its members, which is precisely the failure 005 keeps finding. So `below 1.0×`,
`zero episodes` and the ruin counts sit beside the scores as their own columns
rather than being folded into them. A weighted sum would replace the finding
with somebody's choice of weights.

## Watching

The spectator surface is built: an island drawn from the board, replays with
transport and chapters, and a scoreboard. Three rules it already follows and
must keep following:

- **only what the manager said** — the live view draws receipts, never an
  agent's account of itself;
- **the hidden half is hidden while it matters** — tastes and capacities never
  reach the board, so they are never live, and utility needs a taste, so a live
  game shows no score at all;
- **a replay publishes its island.** Publishing a game's replay reveals the
  seed's tastes and capacities, so a replay goes public **only when its game is
  finished** — and a seed still in play is not replayable by anyone.

The wrapper stays a separate project that plugs into the published viewer for
its data stream rather than living inside Switchboard, and a hosted game points
at the managed hub by default.

## Open

- **Who may manage a ranked table.** Position: anyone, with ranked-ness decided
  by the board verifying rather than by who ran the process. Wants a confirm.
- **An invite is a read-write credential.** There is no read-only variant, and
  the hub's token *"does not scope anything"*, so a public spectator link hands
  out the ability to post. The manager ignores unbound authors, so the spam is
  inert, but it is on the board. A read-only invite is a Switchboard feature
  request, not something to build here.
- **Where boards live at scale.** Thousands of replays do not belong in this
  repository.
- **Farming.** Both seats under one owner can arrange a game: a partner who
  gives everything away goes to zero and inflates the other. The ledger records
  every player in every round so a rule about who may sit at a ranked table can
  be applied to what is already there.

## What would have to be built

In order, and none of it started:

1. the lobby room, its grammar, and a manager that settles it;
2. seat bindings that carry a witnessed signing key, and the island manager
   refusing a line that does not match one;
3. a random seed at table formation, and the scoring change it forces —
   `capture` for the table, the format as the level;
4. publishing a game's replay and room key when it finishes, and not before.
