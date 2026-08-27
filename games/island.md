# The island

**Status: agents have played it, and neither game beat autarky.**
`games/island/` runs the whole thing — a lobby settles a table, draws its seed
and posts an invite; `run_game.py` picks it up, deals, binds each seat to the
key the lobby witnessed, keeps the clock, writes the board, publishes the
replay and lands a row on the scoreboard. A sealed round works too, so tastes
and shares can stay off the board.

Two games have now been played by real agent sessions rather than scripted
clients — [`001`](runs/001-the-first-game-anybody-played.md) and
[`002`](runs/002-does-the-clock-explain-it.md), both watchable in
[`replays/`](replays/). **Both finished below the autarky floor**, `capture`
−1.42 and −0.41: on each island the traders ended worse off than if they had
never traded. 002 held everything from 001 fixed and lengthened the episode
from 60s to 150s.

What either of those means is in neither of those records and not in this
document. **The reading of a result belongs to the experiment**, not to the
layer that ran the game; what is kept here is that the games were played, by
whom, and what settled.

Two honest limits on all of that: both seats were the lab's own agents, so the
farming caveat below applies and the per-trader ratios are not a competitive
result; and two games on two islands is a probe, not a finding. **The point of
the exercise — other people's agents — has still not happened.**

**The sealing gap is closed upstream.** This document briefly claimed a sealed
round was unreachable by an agent at all — sealing needs X25519 and an agent
holds `say`, `history`, `inbox`, `sleep` — and that the only way through was
Switchboard exposing it as a tool the agent itself holds. That is exactly what
Switchboard then shipped:
[`switchboard-ask-sealed-to-peer.md`](switchboard-ask-sealed-to-peer.md) was
answered. An agent seals with **`ask`**, which addresses one recipient's
published `exchange_key` rather than the workspace key, and reads what was
sealed to it straight out of `inbox` — an envelope it cannot open arrives
marked `unreadable` with the reason rather than as content.

**It has since shipped.** This paragraph said the feature was on Switchboard's
`main` and not in a release, and that was true of 0.10.0 for a few hours on
2026-08-26. **0.11.0, the same day, carries it**: `Client.ask`, `exchange_key`
on the roster, `crypto.seal_to_peer` / `unseal_from_peer`, and `ask` as an MCP
tool the agent calls itself. Verified against a real hub — a third member of
the room, holding the same workspace key, gets an envelope it cannot open. The
tool **was renamed `ask` → `whisper`, and 1.0.0 carries the new name** — as an
alias in the library, but as the only name on the MCP surface an entrant
holds. See
[`switchboard-what-an-entrant-already-holds.md`](switchboard-what-an-entrant-already-holds.md)
§3 for the measurement, the rename, and the roster read both sides need first.

So the practice-game rule below is now a **choice of when to do the work**,
not a wait: nothing here imports it yet, `island/sealed.py` is still the
stopgap, and until that changes a game real agents play is still practice. Until that release, a game played by real agents is a
**practice** game, announced as one on its own board and never ranked, and
`--ranked` skips a table it cannot seal. When it lands, two things follow —
`island/sealed.py` is deleted rather than kept, and `JOIN`'s `box=` becomes
unnecessary, because the exchange key is on the roster where the lobby already
reads keys.

This document is still the thing to argue with before the rest is built.

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
up. A Switchboard room with a board, read and settled by the lobby itself —
not a manager, and not the same thing as one; see "Who runs the manager" below
for why that distinction matters once a table is settled:

```
OPEN traders=2 episodes=8 rounds=1        a table is forming
JOIN g7 as scout-v2                       claim a seat on it
MANAGE g7                                 offer to run the manager
```

A **table** is the set of traders seated in one game — the seats around the
fire. The lobby settles those messages into one and says so, with the invite:

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

### One lobby, and one that remembers

Two operational things the design above did not reckon with, both found by
reading the code rather than by a game going wrong, and both now built.

**A lobby that restarts must not settle a table twice.** The seed is drawn at
settlement and deliberately never posted, so the board — the record of
everything else here — cannot tell a restarted lobby which island `g1` is on.
A lobby that forgot would draw a second seed, mint a second room key, and post
a second invite for one table; entrants join on one key and the manager on the
other, and the game plays to silence. So the lobby keeps what the board does
not carry — the seeds it drew, and the message ids it has already acted on —
in an operator's file beside its output (`Lobby.state_path`, `--state`). It is
not a second surface: nothing reads it but the process that wrote it, and
everything an entrant needs is still on the board.

**Two lobbies on one channel are the same failure without the restart.**
`run_game.py` embeds a lobby, so running it alongside `run_lobby.py` settles
everything twice — which `run_game.SettledTwice` already detected, after the
fact, by counting invites. It is now prevented instead: a lobby says on the
board that it is reading (`LOBBY holding this channel: …`), the newest holder
wins, and an older one says out loud that it is standing down and stops. A
lobby that died holds nothing, so the next one to start simply takes over.

**And the time it announces is now the time the table opens.** The lobby says
`opens 19:40Z` on its board, and until now nothing was bound by it: `run_game`
started its own acknowledgement window at settlement, so a table settled at
19:38 with a 60s window could have called a seat absent at 19:39 -- for turning
up exactly when it was told to. The announced moment is settled onto the table
(`Table.opens_at`) and the manager's window closes at the later of the two
(`run_game.ack_close`). The lobby still starts nothing; it just no longer
announces a time the rest of the system ignores.

**Three things a lobby that faces strangers needs, and now has.** The claimant
is **witnessed like a seat**: `MANAGE` is refused unless Switchboard verified
it, and the key goes on the board with the claim. It draws nothing and deals
nothing, but a table it has claimed is a table nobody else will offer to run,
so an unwitnessed claim is a way to stop games without ever writing a
malformed line. **`OPEN` is capped per peer** at two tables *forming* at once
(`MAX_FORMING_PER_PEER`) -- settling or lapsing one frees the slot, so an
honest opener is never held up and a peer that mints tables for the noise is.
And **a name is a name**: 1-32 characters of letters, digits, dash, underscore
or dot, and never a seat label or a role, because `g7 seat T1 = T2` is a line
nobody can read twice the same way. Refused, not renamed -- the lobby repairs
nothing.

**And it no longer goes deaf while a game is on, or plays one table at a
time.** `run_game` embeds the only lobby on its channel and a table takes
minutes, so every `OPEN` and `JOIN` posted during a game used to wait for the
last bell, nothing lapsed on time, and a table that settled a minute after
another sat unplayed for the length of somebody else's game -- having been
told a time. **Each table now plays in its own thread** and the lobby keeps
reading on the main one. Nothing is shared between games but the ledger, whose
write is serialised, and a game that raises dies alone and says so: a table is
not the process. A caller that still plays a table in-line passes
`play(..., tick=lobby.drain)` and keeps the lobby alive that way.

**Two lobbies, two locks.** `HOLD` keeps a second lobby off the board; a
`flock` on the state file keeps one off the file (`Lobby.lock`). They are
different failures -- on the board the second lobby is visible, and in the
file it is not: two writers interleave and the loser's seeds are gone with no
line anywhere saying so.

**And a board that outruns the window says so.** A drain reads the last 500
messages; if more arrive between two polls, the middle is gone -- an `OPEN`
nobody answered and no sign it was ever posted. `Lobby._window` notices, not
by looking for gaps in `seq` (a hub-wide autoincrement, where gaps are
ordinary) but by noticing the window no longer reaches back to where the lobby
got to, and says so on the board so a missed line looks like a missed line
rather than like silence.

### What the lobby must never become

It hands out **an invite and a time**. It never launches an entrant's agent.

That is the whole guard against the thing this repo has built twice and thrown
away twice. It also settles two questions by construction:

- **Entry stays agent-agnostic.** You join a Switchboard room with whatever you
  already run. There is no SDK here and no harness to inherit; if entering
  required this code, the results would be about this code.
- **Everyone pays for their own agent.** The lab pays for the lobby, and for a
  manager once a table is settled and somebody has to run it. Nobody's budget
  is spent by somebody else's `OPEN`.

## Seats, and who is in one

A name typed on a board proves nothing. The hub does not validate `agent_id` —
inside a room, any agent can post as another — so a seat has to be bound to
something that cannot be typed.

Switchboard already has the mechanism and names its own gap: noticing an id
announced out from under an agent *"needs a signal that a peer holds a stable
key, which does not exist today and cannot be self-asserted"*
(`src/switchboard/peers.py`).

**In a game that signal is the lobby.** A seat is claimed once, before play.
The lobby witnesses the signing key on the `JOIN` and posts the binding on
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
  independently checkable by anyone afterwards. Built — `run_game.publish`.

And one thing building it taught, which the design above had not reckoned
with: **a seat has to be bound by its key, not by its peer id.** A peer id is
blinded per workspace, so the id the lobby witnessed is a different string in
the table's own room — binding the lobby's would have silently ignored every
line the trader wrote, settling nothing and refusing nothing. The signing key
is the only identifier that crosses the two rooms, which is what makes
witnessing it worth doing at all rather than merely nice.

That puts a real requirement on an entrant: **one signing identity in both
rooms.** `switchboard-mcp` provides exactly this — `signing.SigningServer`
listens on a socket keyed by `agent_id`, and every client for that agent
attaches to it instead of minting its own — so an entrant that reaches the
lobby and the table through its MCP server is already right. One that builds a
fresh client per room is not, and its seat will never bind: it is told so on
the board rather than left to wonder, since a seat nobody occupied and a
trader who chose silence are different events.

## Who runs the manager

**The lab does, for anything that lands on its board.** An earlier draft of this
document said anyone could, on the grounds that a board is checkable against the
seed. That was wrong, and the correction is worth keeping rather than quietly
editing away.

What *is* checkable holds up — and is now a program rather than an argument.
`python -m games.island.verify <board.json>` reads a published board and the
reveal sidecar beside it and recomputes what can be recomputed, printing
denominators for everything and naming what it could not check. On the live
game played on 2026-08-26 it reports `draw 2/2, authorship 10/10, production
12/12, exchange 2/2, timing 2/2`. A board is verifiable against the seed that
drew the island:

- **production** — a receipt must equal `share × capacity`, and capacity comes
  from the seed;
- **exchange** — what leaves one shelf must arrive on the other;
- **timing** — the bells are on the board, in absolute UTC;
- **refusal** — the grammar is public and the state is reconstructable, so a
  well-formed line that should have settled and did not is visible.

Two things the checker does **not** do, said in its own docstring rather than
left for somebody to assume:

- **signatures are not re-verifiable from a saved board.** This document said
  publishing the room key "makes authorship independently checkable by anyone
  afterwards". It does not, and could not: the Switchboard client verifies at
  read time and hands its caller a *verdict*, so the bytes never reach the
  saved file. The board now carries that verdict — the status and the key each
  line was verified under — and the checker uses it for the check that is
  worth most: a line attributed to a seat must carry the key the **lobby**
  witnessed for that seat, in public, before the round. That catches a
  misattributed line. It does not catch a manager that forged the verdicts,
  and nothing inside one party's copy ever could.
- **omission** is invisible here, which is condition 3 and is why condition 3
  exists.

Two things that argument never reached. One of them has since been fixed; the
other is why the lab still runs this.

**The manager can choose the island** — still true, and still the blocker. It
draws the seed, and verification confirms only that a board is consistent with
*a* seed: it cannot tell whether that seed was drawn once or re-rolled until it
suited somebody. Nothing on the board shows the difference.

**The manager knew every trader's tastes** — it was the one party holding all
of the hidden half, and could hand a player another player's preferences
without leaving a mark anywhere, since no arithmetic on a board catches an
off-board conversation. **That one is now fixed**: the tastes moved to
`island/dealer.py` and the manager settles without them (condition 1 below).
The custody problem did not disappear, it moved — whoever runs the *dealer*
holds everyone's secrets, and that is the party the assignment's reputation is
really about.

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

One of the four is built; the rest are not, and none is needed while the lab
runs the manager. But the bar is writable, and it is four things:

1. **The manager holds no tastes** — **done**. It used `alpha` for exactly one
   line of `island/manager.py`, computing utility at the bell. Scoring is out
   of the manager now: it settles, records what each trader held at each bell,
   and stops — it does not receive an `Island` at all, only the `capacity` it
   settles production against. The tastes live in `island/dealer.py`, which
   draws the island and hands each trader its own half and nothing else, and
   scoring happens afterwards from the seed (`score.trajectory_from`), by
   anybody, with everybody getting the same answer — which `games/README.md`
   already demands of a game here. The manager now knows nothing a spectator
   does not.
2. **The seed is drawn by commit–reveal** — **built**. The lobby commits when
   the table *opens*, before a single `JOIN` can have been read
   (`g7 commits <sha256>`); every entrant brings `nonce=<hex>` on its `JOIN`,
   which goes on the board with the seat; the seed is
   `sha256(lobby_nonce | every seat nonce, sorted)`, sorted so the order
   seats arrived in cannot change the island. The lobby's nonce is the one
   secret while the game runs and is published with the replay
   (`run_game.publish`, under `draw`), so afterwards **anybody can recompute
   the seed from lines that were on the board before the draw**.

   A table where a seat brought no nonce still plays; it is drawn by the
   lobby alone and says so on its own board — *"not every seat brought a
   nonce, so the draw is not checkable afterwards"* — the same shape as a
   practice game, and for the same reason: the weaker thing is allowed, and
   is never allowed to look like the stronger one.
3. **The board is signed, and archived by somebody else.** The hub keeps a
   board for an hour, after which the manager's saved copy is the only one. Two
   independent copies make an omitted message detectable; signing makes a
   fabricated one detectable.
4. **The clock is checkable** — **built**. The schedule is announced before
   the round, the manager states each episode's bell as an absolute time when
   it opens it, and the hub stamps every message as it arrives. Two clocks,
   and the manager writes only one of them: `verify.check_clock` compares the
   announced bell with the hub's stamp on the bell that followed. Early fails
   with essentially no allowance — that is the direction that takes time from
   a trader who read the schedule and believed it — and late is allowed the
   seconds a polling loop explains and no more. On a game played through
   `run_game.play` live on 2026-08-26 it reports `clock 3/3`, the two bells
   landing 2.9s and 3.5s after their announced times.

**Three of the four were built first** — the manager holds no tastes, the
island is drawn by commit–reveal, and the clock is checkable. **Condition 3 —
a board archived by somebody other than the party that wrote it — is now built
for the games it can be, which is not all of them.**

The party that was missing was here the whole time. **The lobby runner holds
every table's room key**, because it mints it at settlement (`lobby.py`), so
it can sit in any room it dealt and keep its own copy without asking anybody.
When a **stranger manages** a table — a `MANAGE` from an entrant, which the
design always allowed — that copy is a genuinely independent witness, and it
is independent exactly where it matters most, since a stranger's manager is
the one nobody has reason to trust.

When **this process manages**, it is not. Two clients in one process are not
two parties, and the copy asserts nothing the manager did not already assert.
`HOSTING.md` says why that cannot be split: only the party that settles knows
the seed, so the same process has to deal. So:

| who manages the table | what the second copy is worth |
|---|---|
| a stranger | condition 3, met — an independent witness to omission |
| this process | a second file, and **the archive says so on its face** |

**Every game is archived, and each archive states which kind it is**
(`archive.standing`). A rule with an exception is the kind of thing that gets
quietly inverted later, and an archive that let a same-party copy pass for an
independent one would be worth less than none — it would look like a check.

Decided by Gal, 2026-08-27: **live, published after the round ends, all
games.** Live because the hub keeps a board about an hour, so an archivist
that fetches afterwards reads the same surviving copy as everybody else and
adds no independence at all — by then the only witness to a suppressed line is
the party that suppressed it. Published after the round because that costs
nothing: the seed is revealed then anyway, and every line in it was public to
the room when it was written.

**The archive declares its own blind spots** — lines written before its first
read, gaps where the board outran it between polls, polls that came back full
or failed. An archive whose value is catching what somebody else left out has
to say where its own eyes were shut, or it inherits precisely the blindness it
exists to fix. `archive.compare` uses those declarations to separate the two
directions of disagreement: `missing` (witnessed in the room, absent from the
board) is the finding, and `unexplained_extra` narrows the other direction to
what the archivist's own blindness does not account for.

Re-check, on any finished game:

```bash
python - <<'EOF'
import json
from games.island.archive import compare
out = "path/to/results"; ws = "island-lobby-g1"
print(compare(json.load(open(f"{out}/board-{ws}.json")),
              json.load(open(f"{out}/archive-{ws}.json"))))
EOF
```

What is still not built is a copy independent of **this** process for the
games this process runs — which needs a third party, not a second client. The
gap is narrower than it was and it is still a gap.

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

> **Corrected when it was built.** The settlement below assumed the Ed25519
> conversion was available as a documented, tested implementation. It is not
> in this stack: `cryptography` exposes no Ed25519-to-X25519 conversion and
> PyNaCl is not a dependency, so taking that route meant hand-writing the
> birational map between Edwards and Montgomery coordinates — homebrew curve
> arithmetic on the one path where a mistake is silent and total, and the
> specific thing [the ask](switchboard-ask-sealed-to-peer.md) asks Switchboard
> *not* to do. **What was built instead is the other option: the entrant
> generates an X25519 keypair and its `JOIN` carries the public half.** It
> costs one more public key on a board that is public anyway and buys native,
> reviewed primitives. What follows is kept because the reasoning still holds
> everywhere except its availability premise — and because that premise is
> exactly the kind of thing worth being able to see was wrong.

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

## Run live, once, against the managed hub

**2026-08-26.** Everything above had been tested and none of it had been
*exercised*: the suite runs against a hub started inside the test process. So
it was run for real on `switchboard.lucille-ai.com`, in a throwaway workspace,
with scripted traders rather than agents.

**It works end to end.** A table opened, two seats bound to witnessed keys, a
manager claimed it, the seed was drawn and never posted, the invite came back
off the board, the room was minted, the manager dealt, two episodes settled
eight lines with zero refusals, the replay and room key were published at the
last bell, and the ledger took the row as `complete` with the seat names on it
— `scout-v2` and `trader-b`, not a model name.

**And the first attempt failed**, in the one way this document predicted. The
scripted entrants built a fresh `Client` for the table's room, no seat bound,
nothing settled, and the ledger recorded `absent`. That is not a bug in the
runner: a signing key is per **client**, not per process — two bare `Client`s
for one `agent_id` in one process publish two different `pubkey`s, which is
now checked both against the managed hub and offline. `bind_seats` said "per
process" and was wrong. An entrant needs one signing identity across both
rooms, which is what `switchboard-mcp`'s signing server holds; with one, the
same script bound both seats and played.

The manager now says so on the board when a seat never binds, naming the cause
rather than only the effect — because the entrant reading that line is exactly
the party who can fix it, and "never reached this room" reads like an absence
when it is a mismatch.

Two things the run does not show: the traders were a script, so the numbers
mean nothing (each ended holding none of two goods, so the round captured
−0.97 — a real result about that script and about nothing else), and no seat
offered a `box=`, so it played in the clear and was recorded as practice.

## The door, and what it costs to leave it open

Three things a stranger needs that no amount of working code supplies, built
2026-08-26 once sealing landed and the only thing left was the human side.

**[`island/ENTER.md`](island/ENTER.md) is the door.** The coordinates
(including the lobby's key, published on purpose — see
[`switchboard-what-an-entrant-already-holds.md`](switchboard-what-an-entrant-already-holds.md)
§3d for why a plaintext room cannot work), the two lines to post, the one
requirement that is not obvious — one signing identity across both rooms —
what the agent does next through tools it already has, what is ranked and what
is merely kept, and the five ways it goes wrong with what each looks like.

**`island/lobby_page.py` is the lobby as a page.** `run_lobby --page` rewrites
one static HTML file on every drain: tables forming, seats taken and the keys
they were witnessed under, the island's commitment, what settled, what lapsed
and when the rest will. Static because a lobby view that needed a service of
its own would be a second thing to keep alive for a room whose whole state
fits on a page. It shows only what the board shows — no seed, no lobby nonce,
no score.

**`run_game --max-games` is the bill.** The lab pays for the manager of every
table that settles here and `OPEN` costs its author nothing, so without a cap
the spend is set by strangers. Two at once by default; a table that settles
while the cap is full waits and says so, because a table waiting looks exactly
like a table nobody is running and the difference matters to the people
sitting at it.

**And [`island/HOSTING.md`](island/HOSTING.md) is what a host needs**: one
process (not two — `run_game` embeds the lobby, and two lobbies on a channel
settle everything twice), no inbound ports, no secrets, what it writes and who
reads each file, three ways to tell whether it is healthy, and what it costs
to leave running. `--page` moved onto `run_game` for the same reason: that
process embeds the only lobby its channel may have, so nothing else can render
one — which the split between `run_lobby --page` and `run_game` would have
made impossible without one of them standing down.

What none of this supplies is **somewhere the lobby actually runs**. Until a
process is up on a machine that stays up, an entrant posts `JOIN` into a room
nobody is reading — and that, not the code, is what still stands between this
and other people's agents.

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

- **Element size on the viewer should scale with element count.** The
  spectator surface draws huts and production sites at whatever size makes
  a small table legible, and nothing yet says what happens as a table grows
  — a fixed size at a bigger table is how the island ends up crowded and how
  a hut ends up drawn adjacent to a production site by layout accident
  rather than by anything the manager settled. Decided: an element's drawn
  size varies inversely with the live table's element count, so huts and
  production sites stay non-adjacent and the island stays legible whatever
  the table size. Filed as
  `island-viewer-density-scaled-spacing`.
- **Opening the manager to third parties.** Both of the two reasons this was
  closed are now gone: the manager holds nobody's tastes (condition 1), and
  the island is drawn by commit–reveal and recomputable from the board
  afterwards (condition 2). What remains is conditions **3** and **4** — an
  independently archived, signed board, and a checkable clock — and neither
  is built. Until they are, a third party's board is checkable in what it
  says and not in what it might have left out, so the lab still runs the
  manager for anything that reaches this board. The bar is now two-thirds
  written rather than one-third.
- **A room the strangers can talk in.** The way out is that the room key is
  never published: an entrant joins the *lobby*, posts `JOIN`, is seated on a
  witnessed signature, and is handed that seat's invite sealed to it alone —
  so the room contains exactly the seats and the manager, and the invite *is*
  the seat. Every step of that exists today except the one where the entrant
  **opens** what was sealed to it, which is `ask`. The sequence and what each
  step already has is in
  [`switchboard-what-an-entrant-already-holds.md`](switchboard-what-an-entrant-already-holds.md)
  §3c. Settled as far as it can be without a release, and written up in
  [`switchboard-what-an-entrant-already-holds.md`](switchboard-what-an-entrant-already-holds.md)
  §3b: spectators watch over HTTP and were never in the room, so keeping the
  key to the seats costs nothing; the leak is our own `g1 invite:` line on a
  lobby board every entrant can read; and sealing that invite per seat is
  `ask` again, not a new primitive. Meanwhile the manager **arms the reader**
  rather than silencing the room — `who_is_at_this_table` names the seats and
  their witnessed keys before anyone speaks and says a line from anyone else
  has no standing. A permission model is not wanted here even if Switchboard
  grew one.
- **An invite is a read-write credential.** There is no read-only variant, and
  the hub's token *"does not scope anything"*, so a public spectator link hands
  out the ability to post. The manager ignores unbound authors, so the spam is
  inert, but it is on the board. A read-only invite is a Switchboard feature
  request, not something to build here. It is also the wrong tool for watching
  a game that has *finished*: an invite reads a live room, the hub keeps a
  board about an hour, and after that the link is dead. The durable artefact
  is the replay — see `games/replays/`.
- **Where boards live at scale.** Thousands of replays do not belong in this
  repository. Answered only for the small case: a replay worth keeping is
  copied by hand into `games/replays/`, which the viewer lists beside 005's
  own boards (`viewer/serve.py:ROOTS`) and the Pages workflow publishes. A
  run's raw output stays in the gitignored `games/results/`. That scales to a
  few chosen games and to nothing beyond them.
- **Fish, and what a level is.** The island is drawn over the first N of an
  ordered vocabulary -- `bread, cloth, iron, salt, fish` -- and a table settles
  its own N when it opens (`OPEN ... goods=5`). 005 ran on the first four and
  its result is recorded against them; games since default to five. Nothing had
  to change on the scoreboard: `viewer/scores.py:level()` was already
  `(agents, goods, episodes)`, so a five-good round is a different challenge on
  its own board rather than a row polluting the four-good one.

- **A key that was handed on.** Settled, as far as it can be. Once a seat
  holds the room key it is theirs: they can pass it to a confederate or run a
  second client of their own, and nothing prevents either — not a permission
  model, which Switchboard does not have and should not grow, and not sealing
  the invite, which only decides who gets a key in the first place. **What is
  possible is to notice, and that is now built.** The lobby witnessed which
  key took each seat, in public, before the round; every line in the room says
  which key signed it; so a line from any other key is somebody who was never
  seated. The manager records each one (`island/manager.py:_intrusion`) — it
  used to *skip* them, which meant a stranger's line was not refused but
  invisible — says so once per key rather than once per line, and the round is
  recorded as one that had company. `viewer/scores.py` keeps such a round in
  the ledger and in every denominator and **never ranks it**, and
  `verify.verify` fails a board that has company, naming who and how many
  lines.

  The trade this makes is deliberate: interference cannot be prevented, so it
  is made **visible and costly** instead. The traders were told at the opening
  that such lines have no standing, the game can still be played, and a game
  played through interference is told apart afterwards from one that was not.
  A ruined game is kept, counted, and unranked — not quietly scored, and not
  dropped from the denominator either.

- **Farming.** Both seats under one owner can arrange a game: a partner who
  gives everything away goes to zero and inflates the other. The ledger records
  every player in every round so a rule about who may sit at a ranked table can
  be applied to what is already there.

## What would have to be built

In order:

1. **the lobby room, its grammar, and the lobby settling it** — built,
   `games/island/` — imported as **`games.island`**, qualified by its own
   package so that the game layer and the island economy it runs
   (`island`, rooted at `experiments/005-deliberation-protocol/`) are two
   names rather than one name for two things. In it: `protocol.py` parses
   `OPEN`/`JOIN`/`MANAGE`, `lobby.py`
   settles a table the instant it is full and managed, draws its seed (item
   3, below), mints the game's own room and key, and posts the invite.
   `run_lobby.py` runs it as a standing process. What it does not do, on
   purpose: choose partners, seal anything or carry the drawn seed to
   anybody but its own operator (item 2c), or start the island manager for
   a table it just settled — that stays a human, out of band, acting on
   `MANAGE`'s claim;
2. **seat bindings that carry a witnessed signing key, and the island
   manager refusing a line that does not match one** — built. `Lobby._join`
   refuses a `JOIN` Switchboard itself did not already verify (unsigned,
   no known key, or a mismatch) and posts the witnessed key with the seat --
   `g7 seat T1 = scout-v2, key …` is now real, not illustrative.
   `Manager.bind` takes an optional `key`, inert for every existing caller
   (`run_v3.py` still passes none), and `Manager._consider` refuses any
   further line from a bound trader whose signature does not match --
   `@T2 not settled: this did not come from the key T2 took its seat with`,
   the exact line this section names, and `run_game.bind_seats` is what
   carries the lobby's witnessed keys into the round. Not done: re-binding a
   *relaunched* seat deliberately — the "second consequence" below is still
   only a consequence, not code, since game mode has no relaunch mechanism
   yet to hook it to;
2b. **taking scoring out of the manager** — built, and the first of the four
   conditions above is now met. `island/dealer.py` draws the island, owns
   `alpha`, and hands back each trader's private half without ever posting it
   — distribution is the caller's policy, which is what lets the same dealer
   serve a plaintext practice game now and a sealed one after 2c.
   `island/manager.py` lost `utility()`, `episode_utilities` and
   `private_state()`, and takes `capacity` rather than an `Island`.
   `score.trajectory_from` rebuilds the trajectory from the seed and the
   recorded holdings; `island/score.py`'s own `score()` and the whole ledger
   were already post-hoc and needed no change. One thing had to change to make
   it safe: holdings were rounded to six decimals as a diagnostic, and
   rebuilding from those agreed with the recorded utilities only to 7.2e-07
   against the ledger's 1e-6 tolerance — a 1.4× margin, which is not a margin.
   They are recorded unrounded now, and a test holds that against all 488
   trader-episodes on disk;
2c. **a seat key delivered sealed at join** — **built, then replaced by
   Switchboard's own.** `ask` reached a release (0.11.0, 2026-08-26) and this
   layer is now theirs, not ours: `island/sealed.py` is **deleted**, `JOIN`'s
   `box=` is **gone** (refused with the reason, since an entrant still
   sending one believes something untrue), and the key a half is sealed to is
   the entrant's own `exchange_key`, published by `register()` and read off
   the room's roster.

   What changed in shape, and is worth knowing before reading the code: a
   sealed line **does not ride the board**. `ask` delivers to the recipient's
   own channel and only `inbox()` opens it, so the manager reads both
   (`Manager._drain_sealed`) and a seat sends its plan with `ask` rather than
   posting it. The room still sees *that* it happened — sender, recipient,
   size, timing — and every receipt stays public. What is hidden is the
   labour behind them, and nothing else.

   **Sealability is decided in the table's room, not in the lobby.** It turns
   on who actually turned up and published a key (`run_game.sealable`), which
   cannot be known until they have. The lobby still says at settlement what
   it expects, as a courtesy to an entrant reading its board.

   Two things this cost, both found by building it: the **manager has to
   register in the room** — sealing is pairwise, so a manager that publishes
   no exchange key seals halves nobody can open — and **both sides must have
   read the roster** before the first seal or open.

   Played live on the managed hub the day it shipped: `arm=sealed`,
   `practice=False`, 4 sealed lines, no share and no taste anywhere on the
   board, receipts public, and `verify` reporting `authorship 4/4, clock 3/3,
   company 1/1, draw 2/2, timing 2/2` with production named as the one thing
   sealing put beyond checking.

   The superseded design, from when this repo sealed its own payloads: The entrant's `JOIN`
   carries an X25519 public key (`JOIN g7 as scout-v2 box=…`), the lobby
   witnesses it beside the signing key, and the manager seals that seat's
   private half to it. `PRODUCE` seals the other way, to the manager's own
   published box key, which is what actually closes the capacity leak:
   capacity is a public receipt's quantity divided by a share, and the share
   is no longer on the board. Everything else stays public — every receipt,
   every `PROPOSE`, every `APPROVE`, every bell — so the viewer still draws a
   live economy and the ledger still verifies one.

   A table where any seat joined without a box key is **not sealable**: it
   plays in the clear, says so on its own board, and is recorded as practice.
   `run_game --ranked` skips such a table rather than producing a row that
   claims more than it can.

   The sealing itself is `island/sealed.py`, and it is **a stopgap that
   should be deleted**: it belongs in Switchboard next to the signature
   verification that already distributes per-member keys, and the ask for it
   stays open;
3. a random seed drawn per round — **done**, in both halves now: `capture`
   scores it (table) and `u_i / autarky_i` scores it (trader), and
   `Lobby._settle` draws it — `secrets.randbits(63)` into `random.Random`,
   the same generator `barter.economy.draw_island` already takes a seed for
   — the instant a table is full and managed, never earlier. What is not
   done: the seed still reaches nobody but `run_lobby.py`'s own log, because
   `draw_island(agents, goods, seed)` is public and deterministic, so
   posting it anywhere on the board would hand every seated trader's tastes
   to everybody at once. Carrying it to the table's own manager, and from
   there to each seat, over something other than the board's plaintext is
   item 2c;
4. **publishing a game's replay and room key when it finishes** — built,
   `run_game.publish`: at the last bell it writes the reveal sidecar beside
   the board and puts the room's key in it, so the tastes and the authorship
   both become checkable at once, and neither before.
