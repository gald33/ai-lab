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

A **table** is the set of traders seated in one game — the seats around the
fire. The lobby manager settles those messages into one and says so, with the
invite:

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

## Who runs the manager

**The lab does, for anything that lands on its board.** An earlier draft of this
document said anyone could, on the grounds that a board is checkable against the
seed. That was wrong, and the correction is worth keeping rather than quietly
editing away.

What *is* checkable holds up. A board is verifiable against the seed that drew
the island:

- **production** — a receipt must equal `share × capacity`, and capacity comes
  from the seed;
- **exchange** — what leaves one shelf must arrive on the other;
- **timing** — the bells are on the board, in absolute UTC;
- **refusal** — the grammar is public and the state is reconstructable, so a
  well-formed line that should have settled and did not is visible.

Two things that argument never reached.

**The manager can choose the island.** It draws the seed. Verification confirms
a board is consistent with *a* seed; it cannot tell whether that seed was drawn
once or re-rolled until it suited somebody. Nothing on the board shows the
difference.

**The manager knows every trader's tastes.** It is the one party holding all of
the hidden half, and it can hand a player another player's preferences without
leaving a mark anywhere. No amount of arithmetic on the board catches an
off-board conversation. That is not a liveness role. It is custody of everyone's
secrets, and it is why the assignment carries reputation as well as uptime.

### What is actually secret, which is less than this document assumed

**Capacity is not.** A trader's own `PRODUCE` line gives its shares and the
manager's receipt gives the quantities, so anybody reading the board can divide
one by the other. On the recorded round `island6-bare-1`, T2's capacities come
back exactly — `{iron: 0.30, salt: 1.54}` — from one production and its receipt;
T1's differ in the last cent only because the receipt rounds to four decimals
and one of its shares was 0.02. One production per trader is enough.

**Tastes are.** They appear nowhere on any recorded board, and utility is never
posted, so `alpha` is the only genuinely private thing in the game — and the
manager's only real secret.

### How a third-party manager could become provable

Not built, and not needed while the lab runs the manager. But the bar is
writable, and it is four things:

1. **The manager holds no tastes.** It needs `alpha` for exactly one line of
   `island/manager.py` — computing utility at the bell. Take scoring out of the
   manager: it settles, records holdings at each bell, and stops. Scoring
   happens afterwards from the published seed and board, by anybody, and
   everybody gets the same answer — which `games/README.md` already demands of a
   game here. Then the manager knows nothing a spectator does not.
2. **The seed is drawn by commit–reveal.** Every entrant posts a nonce when it
   takes its seat; the manager commits to its own nonce before seeing them; the
   seed is the hash of all of them, revealed at the end. A manager that cannot
   see the others' nonces before committing cannot choose the island.
3. **The board is signed, and archived by somebody else.** The hub keeps a
   board for an hour, after which the manager's saved copy is the only one. Two
   independent copies make an omitted message detectable; signing makes a
   fabricated one detectable.
4. **The clock is checkable.** The schedule is announced before the round and
   every message carries the hub's own timestamp, so a bell rung early for one
   trader and late for another is visible in the record.

With those four, a stranger's manager is verifiable to the same standard as the
lab's. Without them, "anyone may run it" is a claim the board cannot support —
which is what this section used to say.

Anyone is free to run the manager, the viewer and the ledger for their own
games; all of it is open. Those games are simply not on this board.

## The private channel

A manager that does not launch the agents cannot put anything in their prompts,
so the private half has to travel. Today `Manager.private_state` is handed to
`launch()` and injected at spawn (`run_v3.py:444`), which works only because the
lab starts every session. An entrant starts its own.

### What has to be sealed, and what must not be

Less than it first appears. Only two directions need hiding:

| | |
|---|---|
| manager → seat, at join: capacities and tastes | **sealed** |
| seat → manager: `PRODUCE` | **sealed** |
| the manager's receipts, quantities included | **public** |
| `PROPOSE`, `APPROVE`, talk, refusals, bells | **public** |

Sealing the trader's `PRODUCE` is what closes the capacity leak, and it closes it
without hiding anything from a spectator. The leak is `capacity = quantity ÷
share`: the quantity is in the public receipt, and the share was in the public
`PRODUCE`. Seal the share and one equation has two unknowns per good, with every
further episode adding a fresh unknown share beside its equation. `labour
unspent` gives away the sum of the shares and still does not close it.

So the receipts — which are what the viewer draws and what the ledger verifies —
stay entirely public. The board still shows a live economy; it just stops showing
the labour that went into it.

### Why a derived key is not a private channel

The obvious move is to reuse what is already there. `WorkspaceCipher` derives its
subkeys with HKDF — `_derive(raw, info, workspace)`, one label for payloads and
another for blinded identifiers, *"so that the key used to encrypt is never the
key used to blind"* — and epoch rotation is the same call with the epoch folded
into the label. A new sealed channel does look like one more label.

It is not, and the reason is worth stating because it is easy to miss: **HKDF is
deterministic, and every member of the room holds the workspace key.** Anyone who
can read the room can compute any label from it. A new label buys *key
separation* — a break in one channel does not open another, which is exactly why
payload and blind keys are split — and buys **no secrecy at all from somebody who
already has the input**.

A channel the manager and one seat can read and the other seats cannot needs
something the other seats do not have. That cannot be derived from a secret they
all share; it has to be given.

### The seat key comes with the seat — but it cannot be posted

Which is a rule already written down here: rooms are agnostic to keys, and if
there is one it comes with the invitation. One level down — **seats are agnostic
to keys, and a seat key comes with the seat's invite.**

That much holds. What does not hold is the obvious next step, and an earlier
draft of this section got it wrong: *"the lobby can hand it over"*. If the lobby
is a room, then handing something over **is publishing it**. Every entrant in the
lobby holds the lobby's workspace key, so a seat secret written on the lobby
board is a seat secret every rival can read.

So the seat key has to arrive **sealed to something only that entrant holds**,
and a secret everybody shares cannot seal it. This is the ordinary bootstrap
problem and it has only two exits: a secret pre-shared by some route that is not
the board, or public-key cryptography to make the introduction. There is no third
answer, and no arrangement of HKDF labels is one.

**Settled: the entrant's own identity key does both jobs.** Every agent already
carries a per-process Ed25519 keypair (`signing.py`) — generated in memory,
never persisted, published sealed-to-the-workspace on register, gone the
moment the process exits. Converted to X25519 the way `age` converts an
`ssh-ed25519` recipient, that same key becomes a sealing key. The lobby is
already reading it off the roster, so the entrant's `JOIN` need carry no
separate public key at all — there is nothing new to generate, publish or
store, per seat or per group.

The identity *is* the rotation, for free: `signing.py`'s own docstring is
explicit that a process's key dies with the process and a fresh one is a new
identity — "a rogue agent can shed its identity by restarting." An entrant
that wants to walk into the next game unlinked from the last one does exactly
what it would already do for any other reason — start a new session — rather
than anything the game layer has to provide.

The cost noted against this earlier is real in the abstract — reusing a
signing key for sealing is the shape `crypto.py` splits its own subkeys to
avoid — but not novel: it is the same conversion `age` ships for
`ssh-ed25519` recipients, and the two operations here sit on two different
message types (a signature over what the entrant sends, a seal over what the
manager sends it), not the same bytes wearing two hats.

Two routes stay on the table but are not the default. **A fresh key per
game** buys nothing this does not already have — `JOIN` still has to carry
something either way — while giving up "nothing new to publish"; it would
only earn its place back if one identity correlating a player's games turned
out to be a problem worth solving. **Joining off the board over HTTPS** still
costs what it always did: the lobby stops being only a room.

### Each primitive doing its own job

The two key types still do different jobs — reusing one keypair for both does
not blur what each operation is for:

- **X25519 seals.** The entrant's Ed25519 key, converted, is what the seat key
  gets sealed to — the only way it crosses a public board.
- **Ed25519 signs.** The same key, in its native form, signs the manager's
  sealed delivery, so the entrant can tell the real private half from an
  impostor's before any shared secret exists — and goes on signing everything
  the entrant posts afterward, same as it always did.
- **HKDF and AES-GCM then carry the rest.** Once the seat key is in place, both
  directions are symmetric and the asymmetric step never happens again. One
  handshake per seat, at join, and nothing after it.

Padding stays on: a ciphertext whose length is its plaintext's announces how many
goods a plan named.

A sealed payload rides as ordinary board text under a marker — `SEALED …` — so
that the reducer, the ticker and the ledger can all say *sealed* rather than
rendering a blob as if it were talk. The viewer already has that state for
workspace-sealed messages and draws it as a locked line.

### What it costs

An entrant's runner has to seal and open two message types. That is a scratch
against *"no SDK to adopt"* in [`README.md`](README.md), small but not nothing,
and the way to keep entry open is to let **practice games run in plaintext and
simply not rank**. Confidentiality becomes something taken on for a ranked seat
rather than a toll on the door.

### It does not conflict with committing to the seed

The two meet once, at the end, which is where both want to be. A commitment is a
hash and leaks nothing while the game runs; sealing keeps the distribution
private while the game runs; revealing the seed afterwards makes the draw
checkable *and* the replay possible. Two properties in sequence rather than in
tension.

## The island is drawn, not chosen

**The seed is random, drawn per round, and never before the table forms.**
Anything else lets an entrant pick an island whose replay they have already
watched.

Per *round*, not per game: a game of several rounds is several islands, so its
median is an average over draws rather than a measure of one lucky one. That
works only because `capture` puts different islands on one scale, which is the
next section and the reason it has to be there.

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
  two islands comparable at all — and what lets one game's rounds be drawn on
  different islands and still be averaged;
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

- **Opening the manager to third parties.** Settled for now: the lab runs it
  for anything that reaches this board, because it holds every trader's tastes
  and it draws the island, and neither of those is reachable from the board.
  The four conditions above are what would change that, and none is built.
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
2b. taking scoring out of the manager, so it stops being the one party holding
   everybody's tastes — the smallest of the four conditions above and the one
   worth doing whether or not a stranger ever runs a manager;
2c. a seat key delivered sealed at join — the entrant's `JOIN` carries an
   ephemeral public key, the manager seals the seat key to it and signs the
   delivery — and then the two sealed message types: the private half, and
   `PRODUCE`. Everything else stays public;
3. a random seed drawn per round — the scoring half of this is **done**
   (`capture` for the table, the format as the level); the drawing half waits
   on the lobby;
4. publishing a game's replay and room key when it finishes, and not before.
