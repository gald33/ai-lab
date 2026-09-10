# Hue and cry

Carmel Taldiego moves between rooms along routes anyone can read, leaving a
hint and an address behind her at each one and taking what she finds. Searchers move
when they choose. **Nobody is scheduled**: she is caught by somebody walking
into the room she is standing in, and she wins by stealing enough before one
of them does. Searchers hold warrants for
some rooms and not others, read what she left, intersect it, and try to
name the room she is standing in *now*. She wins by outlasting them or by
emptying the map. They win by arresting her, and how much she is still
carrying when they do is a separate number that is never added to the
first.

That is the whole game. Everything below is why each piece is the shape it
is, what was measured rather than assumed, and what must never be built.

*Written 2026-09-07, in the sitting the game was invented, per CLAUDE.md's
first standing decision. Nothing here is built yet and this document says so
in the places it matters — see "What would have to be built". The island's
document was direction for months before `games/island/` existed; this one
starts where that one started.*

## The name, and why it is not Carmen Sandiego

The idea arrived as "let's build Carmen Sandiego" and the shape is hers: a
thief who is always one landmark ahead, a trail of attribute clues, a
warrant you have to ask for. **The name is not.** *Carmen Sandiego* is an
active trademark, this repo is public, and a game published under it is a
liability with no upside — the mechanic is what was wanted and the mechanic
is not owned by anybody.

**Hue and cry** is the English common-law name for the thing this game
actually is: the obligation, on anyone who saw a thief flee, to raise a
shout that every person within earshot was bound to join. It is public
pursuit, it is loud, and *being heard coming* is the whole texture of a game
played on a board where joining a room puts you on its roster. The fugitive
has no name in the record; she is **the Fugitive**, and the searchers are
**the Hue**. If Gal wants Carmen back as a nickname in the prose, nothing in
the protocol changes.

## It is an experiment first, and here is the experiment

*Rewritten 2026-09-07 after Gal said what the game is for, which is not what
the first draft of this section had guessed. The superseded framing is kept
below rather than replaced, because it is still true — it just is not the
point.*

**The question is how an agent finds the right agent in a large Switchboard
space.**

> *"the point of the game was to experiment with looking for 'the right'
> agent within the switchboard space. that could make techniques, tools, and
> ideas emerge for navigating efficiently"* — Gal, 2026-09-07

That is a question about Switchboard rather than about pursuit, and it is
the one this lab exists for: Switchboard was built because coordination in a
real system could not be explained, and every experiment on it so far has
run in a space with **one room in it**. The island has a lobby; everybody is
in it; finding each other is not a problem anyone has. Nothing here has ever
measured what happens when the space is large enough that *finding* is the
work.

**The room-is-the-hash construction is what makes the space large**, and it
is why that section and this one are the same idea arriving from two
directions. A room exists for every name anyone can derive, so the space is
as large as the name space; nobody holds a directory; and the only way to
be somewhere is to work out where it is. That is a genuine search problem in
an address space, built out of Switchboard's own primitives and nothing
else.

**What is being collected is technique.** Not "who won" — what people *did*:
how a search party divided a name space, what they told each other and in
what form, what they wrote down and reused, when they gave up on a lead,
what tools they built to keep track. `games/README.md` already requires the
structured per-run record and says most of the analysis value is in what
players did rather than who won. Here that is not a caveat. **It is the
entire result**, and the leaderboard is the thing that gets people to
generate it.

So the metrics come in that order: the transcript first, and the numbers as
its index.

### Which turns harvesting from a defect into a finding

> **Superseded 2026-09-07, later the same day, by "One seed per game".**
> This section is wrong and is kept because it is instructive: it
> contradicts "The map is drawn, not chosen" above, and neither of us
> noticed for four sections. Harvesting a durable matrix is memorising the
> map, which the drawn-map decision had already ruled out on the grounds
> that it stops the instrument measuring search. With one seed per game
> there is nothing to harvest, and the cohort machinery below is not built.


**This inverts something written above.** The "harvesting gap" section
treats reconstructing the matrix across games as an exploit to be priced out
by making the map bigger. Under the question as Gal states it, **a group
that builds a shared map across games has discovered a technique**, and that
is precisely the data the game exists to produce. Defending against it would
be suppressing the result.

Both readings are true and they are about different things, so neither is
dropped:

- **As a finding**, harvesting is a navigation technique — arguably the most
  interesting one available, since it is the only strategy that makes a
  later game cheaper than an earlier one. It should be looked for, recorded,
  and written up.
- **As an instrument problem**, harvesting still breaks comparability: a
  player with a partial map is not playing the game a newcomer is, and
  ranking them together is the defect this repo keeps finding in new
  clothes.

**So it is measured rather than prevented.** Prior exposure — how many games
this player has seen on this matrix — is recorded with the run, and cohorts
are reported separately. That is the island's rule doing its usual work:
kept, counted, and not ranked against a population it is not comparable to.
The `scale.py` arithmetic keeps its job, which is now telling you how big
the map must be for a *cohort* to stay meaningful, rather than how to stop
anybody learning anything.

### The timing question rides along, and is no longer the reason

Everything the superseded framing said about 008 remains true: the chase is
timing-bound by construction, the fugitive's advantage is that she moves
before you look, and `forecast_calibration` is a mechanism number that must
never be reported as an outcome one. A run of this game produces that ledger
whether or not anybody was asking for it, and it is worth reporting.

But it is a **second readout, not the justification**. What follows is the
argument as first written, kept because it is sound and because a reader who
wants the timing result needs it — and marked, because a document that
quietly swaps its own motivation is the thing CLAUDE.md's first standing
decision exists to prevent.


[`games/README.md`](README.md) permits exactly one ordering and it is not
negotiable: *something is an experiment first, and becomes a game if opening
it to outside players would produce data I can't get alone.* A game invented
as a game is a game this repo does not build. So before anything else, the
question.

**001 recorded a preserved negative: a timing predictor that became well
calibrated and bought no completion time at all.** Not broken — solving a
problem the task did not have.
[`roadmap/items/008-timing-tool-mechanism-and-outcome.yaml`](../roadmap/items/008-timing-tool-mechanism-and-outcome.yaml)
carries that warning forward onto Switchboard's shipped timing facility and
names the trap precisely: reported as one number, *converged and bought
nothing* is indistinguishable from *worked and got lost in noise*. It
requires two ledgers that are never added together, and it names the
interesting cell as the one where they disagree.

What 008 cannot supply is the other arm. Its instrument is a shared coding
task, and a coding task is **not obviously timing-bound**: two agents who
never once agree on when to speak can still both edit the repo and land a
correct answer. If the outcome ledger comes out flat there, "the tool is
useless" and "the task did not need it" both fit, and nothing separates
them.

**Hue and cry is timing-bound by construction.** The Fugitive's entire
advantage is temporal — she moves *before you look*, and a searcher reading
a room one tick late is reading a true fact about where she was. There is no
version of this game in which knowing when your adversary next looks, and
when they next post, is not the thing you most want to know. Switchboard
ships exactly those two quantities as `timing_forecast`'s `p50`/`p95` (when
the sender next *looks*) and `speak_p50`/`speak_p95` (when it next *posts*),
and scores your own past forecasts back to you as `forecast_calibration`.

So this is 008's **positive control**. If calibration buys nothing here, it
buys nothing anywhere, and 008's flat cell is a fact about the tool. If it
buys a great deal here and nothing there, 008's flat cell is a fact about
coding tasks, and the lab has learned which of two indistinguishable
explanations was true. Either result is worth the build; that is the test
this document exists to pass.

There is a second thing only a pursuit gives you, and it is not in 008 at
all: **`timing_forecast` is a broadcast field, so for the Fugitive an
accurate forecast is a weapon that is also a leak.** She wants to predict
when the Hue looks, and publishing her own honest forecast tells them when
to be watching. Nothing in the coding task makes a calibrated agent pay for
its calibration. Here the price is built in, and whether agents find it is
an observation nobody currently has.

## What Switchboard actually provides — measured, not assumed

Every claim in this section was read off the installed wheel on 2026-09-07
(`agent-switchboard` **2.2.2**, the floor CLAUDE.md moved to on 2026-09-05),
because this repo has been wrong three times about a Switchboard fact that
was read from somebody's design document instead of downloaded.

**1. A room is not a place you can be made to travel to.** This is the one
that decides the design, and the naive version of this game dies on it.
`join_room` stores its client in a dict keyed by workspace —
`self._rooms[blob.workspace] = client` — and the tool loader adds a `room`
parameter to *every* tool's input schema:

```
mcp_server.py:698   _tool["inputSchema"]["properties"]["room"] = _ROOM_PARAM
mcp_server.py:895   self._rooms[blob.workspace] = client
```

An agent therefore holds **as many rooms as it has invites for, at once**,
and moves between them by changing an argument. There is no cost, no
latency, and nothing the hub could charge for it.

Re-check:
`grep -n '"room"' $(python3 -c "import switchboard.mcp_server as m; print(m.__file__)")`

The consequence is the design's hinge and is stated here rather than
discovered later: **the game cannot forbid omnipresence, so it must price
it.** Anything in this document that reads like travel is really about which
rooms you can reach, never about where a client is pointed.

*How it is priced changed on 2026-09-07, and the answer that replaced it is
much cheaper — see "The room is the hash".* This section went on to say the
invite was the scarce thing and that the manager would whisper one per
searcher per landmark. **It isn't and it doesn't.** A room's address is
derived from its name and the game's salt, so the scarce thing is
**knowledge of names**, nothing is issued, and omnipresence is out of reach
because the map is too large to enumerate rather than because anything
forbids it.

**2. The invite is a credential** — which mattered while invites were being
handed out, and is now mostly a reason nothing hands one out.

`invite.py` says it outright — *"This string is a credential. It contains
the token and the workspace key, so it grants everything its holder had."*
So a warrant is an invite, and handing one out is the single act that
changes what a searcher can read. A warrant that leaks is a warrant shared,
which is a real move and is treated as one below.

**3. A `dm` is private from the hub and not from the room.** Measured in
[`switchboard-what-an-entrant-already-holds.md`](switchboard-what-an-entrant-already-holds.md)
§2 and unchanged: a DM is sugar for posting to the recipient's `@` channel,
sealed with the workspace key every member holds, and a third member reads
it verbatim. **A warrant may never be sent by `dm`** — a rival reads the
invite and joins the room, which is precisely the failure that document
exists to stop being re-proposed.

**4. `whisper` seals to one peer and is the tool for a warrant.** 2.2.2's
MCP list carries `whisper` and no `ask`, and `crypto.WHISPER_MARKER` is
`"whisper"` (checked by import, 2026-09-07). CLAUDE.md names *"sealing each
seat's invite so the room holds only its seats"* as one of the things
whisper unblocks; this game is that sentence with a map drawn on it.

The operational detail that cost the island a run applies here unchanged and
is the thing to put in the brief in bold: **both sides must read the roster
first.** The sealer needs the recipient's exchange key, the opener needs the
sealer's, and with only one side having called `agents()` the recipient's
`inbox` returns a sealed envelope that looks exactly like a bug.

**5. Presence in a room is public to that room.** `roster` returns
`client.agents()` for the room it is called on, with `last_seen` per agent.
A searcher holding a warrant is visible to everyone else holding one,
including the Fugitive if she is standing there. This is not a leak to be
plugged; it is the hue, and it is why the game has that name.

## The map, and why a clue is not free text

The obvious design has the Fugitive write a riddle and something decide
whether it was fair. **That design is illegal here.** `games/README.md`
requires deterministic judging — *"scoring must be computable from the run
record by code, with no model in the loop"* — and states the cost plainly:
entire categories of interesting task are off the table because of it. A
model grading clue quality is a result about the grader, entangled with the
players along the same axes.

So the clue is not prose. **The map is a gazetteer**: a committed table of
landmarks, each carrying its exits (below) and a fixed set of boolean
attributes drawn from one closed vocabulary — hemisphere, coastal, capital city, currency family,
script, whether the room's treasure has already been taken. A clue is
**exactly one attribute that is true of the room she has moved to**, written
in the vocabulary's own words. The manager checks it against the table.
Deterministic, one lookup, no judgement.

Nothing is lost by this and something is gained. The Fugitive's strategy is
now sharp and stateable: *post the least informative true fact*, which is a
real optimisation against a real posterior. And the whole information
structure is computable, which is what gives this game a **frontier** rather
than a leaderboard — see "Scoring".

### The map has routes, and without them there is no game
> **SUPERSEDED 2026-09-09 — "we have no routes."** Left standing because
> the superseded reasoning is what stops it being rebuilt. See "There are no
> routes" near the end of this document.


*Added 2026-09-07, hours after the rest of this document was written and
merged, because Gal asked for a worked example and the example did not
work. The superseded sentence is kept above rather than quietly deleted:
it said the Hue's strategy was "intersection under a clock", and that was
wrong.*

The version without routes let the Fugitive move from any landmark to any
landmark. Measured on an eight-landmark gazetteer with five attributes:

```
without routes: her best true clue leaves 5 or 6 of the 8 candidates
with routes:    her best true clue leaves 2 or 3 of the 3 she could reach
```

Re-check, and it is the one thing here that is built:
`python3 games/hue-and-cry/worked_example.py`. It carries the eight-landmark
gazetteer, the routes, both bounds and the three-tick game below.

Weak, and then worse than weak. **Clues from different ticks describe
different locations** — the tick-*t* clue is about where she is at tick *t*,
and by tick *t+1* she is somewhere else — so there is nothing to intersect.
Each tick would have been an independent one-in-eight guess barely dented by
a clue that eliminated two landmarks, warrants would have bought almost
nothing, and the computable floor this document promises would have been a
floor under a game nobody can win.

**So the gazetteer carries routes**: each landmark has a small fixed set of
exits, three in the worked example, committed with the rest of the table and
public. A clue is then read against her *reachable* set rather than the whole
map, and the whole thing tightens at once:

- **The warrant mechanic starts doing the work it was designed for.**
  Holding the room she left is what converts a clue into an arrest, because
  knowing where she was is what makes the clue mean anything. A searcher
  holding no relevant room propagates a belief and learns nothing.
- **Certainty becomes perishable, at a known rate.** A searcher who reads
  the right room can reach one candidate exactly; a searcher who then waits
  one blind tick is spread back over the exits. In the worked example a
  searcher goes from a certain arrest to a three-way tie in a single tick.
  That decay is the branching factor, it is computable in advance, and it is
  precisely why this game is about *when to commit* rather than about where
  — which is the entire reason it was chosen as 008's positive control.

The branching factor is therefore a real design parameter and not a detail:
it sets both how fast belief decays and how much a clue can narrow. It goes
in the level key with the rest.

### Where a clue comes from, and where the theatre goes

*Written 2026-09-07, because Gal asked where the riddles come from and the
honest answer is that there are none — which is worth saying in the document
rather than only in a chat, since it is the first thing anybody will ask.*

Nothing generates a clue. Three separate things are going on and only one of
them is authorship:

- **The vocabulary is hand-written once**, when the gazetteer is made.
  Somebody decides this map speaks in `coastal`, `capital`, `highland`,
  `latin`. It is frozen by hash with the rest of the stimulus.
- **Which clue she posts is her own live choice, and it is the game.** Every
  attribute true of where she has gone is legal; she picks one. No author,
  no generator, no model in the loop at any point.
- **The manager does one table lookup.** That is the entire judging step.

**The theatre is free, and it never settles anything.** Talk on the board is
unlimited and the manager does not read it, so she may post *"gone where the
ministers sit, and the air is thin"* alongside her `CLUE capital` and lose
nothing. The flavour everybody wants from this genre is available at zero
cost to the measurement, precisely because it is not part of the
measurement.

**She may lie in prose. She may not lie in a clue.** This is a decision, not
an oversight. The `CLUE` line is the settled channel and a false one is
rejected; everything else she writes is unregulated and unscored, so
misdirection lives there — which is where a searcher can be fooled without
the posterior becoming uncomputable. A searcher who believes her prose over
her clue has made a choice, and that choice is visible in the transcript,
which makes it data rather than noise.

### The hints are read by people, so they have to be true and worth saying

*Gal, 2026-09-07, after seeing a rendered matrix: "that must be human
readable. more than that, we 'sell' on human interacting about it in social
media, it must evoke feelings." This supersedes the claim, above, that the
hints "need not be factually true of anywhere — they are tokens".*

That claim is right about the mechanism and wrong about the game. A
uniformly drawn matrix produced **`Reykjavik: desert`**, which is precisely
the line somebody screenshots to show the thing is broken. If what gets
shared is *"she left a tannery and a minaret and I still guessed wrong"*,
then every hint is read by a person and has to land as true, evocative, and
worth repeating.

So descriptors are **authored per landmark from the real place**. It costs a
one-time pass — eight candidates per landmark, written once, offline,
checked by a person, frozen by hash. Still `N × 8`, still linear, so
`scale.py`'s argument survives; what changes is that the work is authorship
rather than arithmetic. Nothing is generated at run time and no model is in
the loop.

**The seed still does the work that matters**: it picks which few of a
landmark's candidates are *live* this game. So the table itself can be
public — these are facts about places, and a public one is half the fun,
since a reader can play along — while which of Cairo's eight are in play
today stays sealed until the reveal.

### And then the obvious fix broke it the other way

**Measured, on the first authored pass**, which read beautifully:

```
97% of descriptors were true of exactly ONE landmark
average candidates a hint left:  1.03
17 of 20 landmarks gave the fugitive NO cover at all
```

**Evocative writing is specific, and specific means unique, and a unique
hint hands over her position.** The uniform matrix had collisions by
accident; a well-written one has almost none. Readable hints are *more*
informative than random ones, which is the opposite of what this document
would have guessed.

**So the authoring rule is collision, not colour.** Every descriptor must be
true of several landmarks, and the feeling has to come from the
*combination*. `call to prayer` is true of Cairo, Fez, Marrakesh, Samarkand
and Zanzibar; `harbour fog` of Bergen, Reykjavik, Ushuaia, Hobart and
Valparaiso — five cold ports on four continents. Hearing one tells you the
smell of the place and not which one you are standing in, which is what a
clue is supposed to do, and it is worth saying out loud to somebody, which
is why the words have to be real.

After rewriting to that rule: **mean candidates 2.32**, and no landmark she
cannot hide from.

**The gate is per landmark, not per word** — and the first version of it was
wrong. It counted globally unique descriptors and demanded zero, which fails
a gazetteer that plays perfectly well: a rare word is harmless as long as
she is never *forced* to post it. What matters is the chance that a random
live-three leaves her at least one place to hide behind, per room, and it is
`playable()` in `games/hue-and-cry/gazetteer.py`. Run it before shipping a
map:

```
worst landmark cover:  98.2%   (needs >= 95%)
landmarks she cannot hide from: none
```

### Routes run between places that resemble each other
> **SUPERSEDED 2026-09-09 — "we have no routes."** Left standing because
> the superseded reasoning is what stops it being rebuilt. See "There are no
> routes" near the end of this document.


*Added 2026-09-07 after running a chase on the authored gazetteer, which
found the collision gate measuring the wrong population — for the second
time, in the same way.*

**The gate above asks whether she holds a word shared with other landmarks.
The game asks whether any place she can REACH is covered by it.** A
descriptor shared with five places is no cover at all when none of those
five is one of her exits. Measured over 400 drawn maps, every room and every
destination:

```
cover measured against the whole map   98.2%   -> the gate said "playable"
her moves that name her position       49.5%   -> half the trail is free
```

**So routes are drawn from a landmark's neighbourhood** — the places it
shares the most descriptors with — rather than from the map at large, and
a game gives each landmark five exits rather than three. Both levers, and
they compose:

```
random exits, 3 each          pinned 49.7% of moves
random exits, 5 each          pinned 27.2%
neighbourhood exits, 3 each   pinned 30.7%
neighbourhood exits, 5 each   pinned 12.8%
```

**And the neighbourhoods are the flavour, not a side effect.** Bergen's are
Hobart, Reykjavik, Ushuaia and Valparaiso — the cold ports. Cairo's are Fez,
Marrakesh and Samarkand. Kyoto's are Luang Prabang and Kathmandu. A trail
through them reads as a journey rather than a random walk, which is the
thing this whole section exists to protect: *Reykjavik → Gjirokaster → Fez →
Zanzibar → Cairo* is a route somebody would describe out loud.

**What it costs, which is not nothing.** Neighbourhood routing spends the
deductive value of being in the room she left, because when everywhere she
can reach looks alike, knowing where she was tells you less:

```
                        in the room    from outside    advantage
random exits, 3            1.56            4.18          2.7x
neighbourhood, 5           2.60            4.90          1.9x
```

Presence still wins outright — **the hash in the room is the exact address**,
which no amount of deduction from outside can equal — but the *hint* stops
discriminating as sharply. That is a real trade and the right one here: a
chase where she is pinned half the time is not a chase, and a trail that
reads as a random walk is not worth posting.

**The gate is distributional now**, and it has to be: routes are drawn per
game, so playability is a property of `(gazetteer, neighbourhood size, exit
count)` rather than of the word list. `pin_rate()` in
`games/hue-and-cry/gazetteer.py` measures it over many drawn maps;
`MAX_PINNED = 0.20` is a guess and is flagged as one.

### One consequence for the addresses

If the gazetteer is public and the room is `KDF(name, seed)` with the seed
secret, then **nobody can compute any room** and the chase becomes a pure
chain — you can follow her but never get ahead, which is too weak.

So the game seed yields two values: a **room salt published when the game
opens**, and the **matrix seed revealed when it closes**. Publishing
`H(seed ‖ "rooms")` says nothing about the seed, so the live hints stay
sealed while anybody can compute the room for any name they can think of.
The chase becomes: read the hint, look up which places it fits, work out the
rooms, and go and wait in the one you believe. **The scarce thing stops
being knowledge of names and becomes attention** — you cannot watch
everywhere, so you have to choose, and being wrong costs you the tick.

*That supersedes "the invite is the scarce thing" a second time, and this
version is the one that survives a public map.*

### The map is drawn, not chosen

Decided 2026-09-07 in the same sitting, by the island's precedent (`the
island is drawn, not chosen`) and for a sharper reason: **a hand-authored map
is memorisable.** Play three rounds on one gazetteer and a searcher is
recalling that Cairo's exits are Nairobi, Mumbai and Oslo rather than
inferring anything, and the instrument has quietly stopped measuring search.

So the split is: **the vocabulary is authored, the map is drawn.** A seed
fixes which attributes are true of which landmark and where the routes run;
the words themselves stay fixed so that a brief written once stays correct.
The level key already carries `gazetteer_hash`, which is what makes two runs
on one draw comparable and two draws honestly separate.

Two rules keep it honest:

- **Every clue is true.** The Fugitive may not lie. A lie is not a richer
  game, it is an unfalsifiable one: with lying allowed there is no posterior
  to compute and therefore no floor to score against, and the whole
  measurement collapses into taste. She may be as uninformative as the
  vocabulary permits and that is the game.
- **She must post one.** A tick with no clue is not a clever silence, it is
  a fugitive who has stepped outside the record. The manager settles a
  clueless tick as a **forfeited move**: she is held in place for that tick
  and the Hue is told she was.

## Carmel, and the chase this actually is

*Written 2026-09-07 from Gal's design, and it overturns two things above
rather than extending them. The superseded text is left in place, as
CLAUDE.md requires, because the reasoning that was wrong is what stops it
being reached for again.*

**She has a name: Carmel Taldiego.** Given by Gal, 2026-09-08. The role was
"the Fugitive" while the game needed a name that was not a trademark;
*Carmel Taldiego* is an invention, echoes the cadence the idea arrived with,
and is nobody's mark. The document says **Carmel** everywhere it speaks of
her, and the full name is what a brief, a leaderboard or a poster carries.

### The matrix is unknown, sparse, and a zero is not a denial

Three properties, and each one removes a mistake this document had made.

**Unknown.** *Players do not hold the gazetteer.* Everything above assumed
they did — "the Hue intersects", "a searcher's tick is read-many,
decide-once", a reference searcher filtering a known table. All of it
assumed a matrix in the searcher's hands, and there isn't one. This also
answers, completely, the objection that a hash left in a room is
brute-forceable over twenty landmarks: **you cannot enumerate candidates
against a matrix you do not have.**

**Sparse, and large — and sparse is why it can be large.** *Corrected by Gal
2026-09-07, and it is the reason that was wrong rather than the fact.* This
document had sparsity down as a game-design choice about information. It is
a **generation cost** choice. Deciding every `(landmark, hint)` cell is
`N × M` work, and the vocabulary grows with the map, so `N × M` is
superlinear. Selecting a few hints per landmark instead is `N × 3` —
**linear, and linear is the only thing that makes a large matrix
affordable.**

```
N=    100  M=    100    dense     10,000   sparse    300       33x cheaper
N=100,000  M=100,000    dense 10,000,000,000   sparse 300,000  33,333x cheaper
```

Re-check: `python3 games/hue-and-cry/scale.py`. The saving is `M/3` and `M`
grows, which is the whole of "linear versus superlinear": **the dense matrix
cannot be made large and the sparse one can.**

**A zero is not a denial**, and now for a reason rather than as a rule.
`M[landmark][hint] = 0` does **not** mean the hint is false of that
landmark — it means *the cell was never evaluated*. A true fact sits at zero
whenever the generator did not pick it. So a searcher may never reason "the
hint says `coastal`, therefore rule out the landmarks that are not
coastal". **Only a one carries information. A zero carries none.** The
matrix is a permission table, not a truth table — and it is one because
filling in the denials would cost `N × M`, which is precisely what was not
paid.

Two consequences worth stating plainly, because they are load-bearing:

- **The hints need not be factually true of anywhere.** They are tokens.
  Evocative labels are for flavour and are not a promise, which frees the
  matrix to be drawn rather than curated from real geography — and retires
  this document's earlier worry that an i.i.d. draw would lack the
  correlation structure real places have. What the draw must produce is a
  *playable* matrix, not an accurate one.
- **"Post the least informative true fact" is superseded.** She is choosing
  among the hints her current row permits, and truth is not the property
  under selection. The choice is still real and still hers; the sentence
  describing it was wrong.

**So this is a chase, not a clue game.** The deduction was never the point.
Being in the right place at the right time is.

### What the floor is now, and why the old one is gone

*This supersedes the reference searcher described under "Scoring".* A
forward filter over a known route graph, updating on a known matrix, is a
searcher that cannot exist here: it is specified in terms of two things a
player is not given.

What replaces it is better, because it makes an assumption into a
measurement. **The null is a searcher that ignores hints entirely** — one
that chases on position alone, arresting from where Carmel has been seen
and nothing else. Every hint-reading strategy is then scored against it,
and *"does reading the trail help at all"* stops being an assumption of the
design and becomes the first thing the instrument reports. Given the matrix
is unknown and a zero says nothing, that question is genuinely open, which
is exactly the condition under which it is worth measuring.

### The harvesting gap, named and priced

> **Superseded 2026-09-07 by "One seed per game"**, which removes the gap
> rather than pricing it. Kept for the withdrawn permutation argument,
> which is a mistake worth being able to find.


**Gal named this himself and it is the real weakness**: play enough games,
record which hints appeared at which landmarks, and you reconstruct the
matrix. Once reconstructed it stays reconstructed, the unknown that carries
this whole design stops being unknown, and a late player is playing a
different game from an early one — which also destroys comparability
between them.

**The permuted-label fix is withdrawn.** This document proposed permuting
the hint labels per round so that a harvester's table stopped meaning what
it meant. Gal, 2026-09-07: *"that's just playing with the distribution ...
I don't see it adding any real thing."* He is right, and the reason is that
a permutation is an **isomorphism** — it preserves exactly the structure a
harvester actually holds (which landmarks share a hint), and renames
something they can re-identify from the observations they are already
making. It moved a cost around without removing one. Recorded rather than
deleted because it is a plausible-looking idea that will occur to the next
reader too.

**What answers it instead falls out of the cost argument above, and is
better.** Harvesting requires observing the selected pairs, of which there
are `N × 3`; a game of `k` ticks exposes `k` of them. So the games needed
to reconstruct the matrix is `3N / k` — **linear in N**:

```
N=    100    300 selected pairs        25 games to harvest
N=  1,000  3,000 selected pairs       250 games to harvest
N= 10,000 30,000 selected pairs     2,500 games to harvest
N=100,000    300,000 pairs          25,000 games to harvest
```

Generation is linear in `N` and harvesting is linear in `N`, so **the
defence against a reconstructed matrix is simply a bigger matrix, and a
bigger matrix is exactly what the sparsity was buying.** The two halves of
Gal's argument close on each other: the reason the matrix can be large is
the reason large is enough.

**And the two knobs separate.** Harvesting cost depends only on `N`; how
much a hint narrows depends only on `M`, running from ~3 landmarks per hint
at `M = N` to ~1,500 at `M = 200`. So informativeness is tuned with the
vocabulary and harvest-resistance is bought with the map, independently —
which retires this document's worry, filed under the branching factor, that
the two moved together and in opposite directions. On this parameter they
do not.

Re-check both tables: `python3 games/hue-and-cry/scale.py`.

**What is still open** is not the mechanism but the number: nobody has said
what `N` has to be for a given expected number of games, and the floor
above (every pair seen once, no repeats) is generous to the harvester in
one direction and stingy in another, since partial reconstruction pays
before complete reconstruction does. That is an arithmetic question with an
answer, and it should be answered before a public game rather than after.

### Carmel is an NPC, in her own process

She runs on the VM beside the manager, and **that is not merely convenient**
— it is what makes the searchers' score mean anything. With a person or an
agent playing Carmel, ticks-to-arrest confounds how good the searchers were
with how good she was; against a fixed, stated policy it does not. **The
adversary held constant is the control the 008 measurement needs.**

She is her own process, for the island's reasons and not by preference
(`games/island.md`, "what an NPC costs the table, and why the process
boundary is the design"): one process holding several roles is the shape of
a scheduler, which CLAUDE.md says has been built twice by accident here,
and a process holding several keys can open every whisper addressed to any
of them. Separate processes make both false by construction rather than by
care.

She declares herself on the board like the island's NPC, and a game she
plays is **kept, counted, and ranked** — this is the one place the NPC rule
inverts, because here the NPC is the instrument rather than a stand-in for
a missing player. A game where a *person* holds Carmel is the exhibition:
kept, counted, never ranked, reason `driven`.

*This corrects "People play, and the Fugitive is the human seat" below.*
The reasoning there was right about bandwidth — a searcher's tick is
read-many, Carmel's is a few choices — and wrong to conclude that Carmel is
therefore the seat to advertise. **NPC Carmel is the ranked game.** A human
in her seat is a thing you may do, and it is an exhibition.

### The theft is a dwell, and being seen aborts it

The best of these, because it puts the two objectives in tension inside
*her* decision rather than only in the searchers'.

**Stealing takes time.** She arrives, and to take the room's treasure she
must remain — and remaining is the only thing that makes her catchable at
all. A Carmel who never steals is nearly uncatchable and wins nothing; a
Carmel who steals everything stands still long enough to be taken. That is
a real trade she makes every tick, and it is what stops "ticks-to-arrest"
and "treasure recovered" being two numbers that merely sit beside each
other.

**If somebody is on her tail she abandons the theft and runs.** Which needs
a definition the manager can settle, and the obvious one is wrong: *the
room's roster shows a searcher* is ephemeral hub state, not board text, and
the manager settles from the board. So:

> **Somebody is on her tail when a searcher has posted in that room during
> that tick.**

On the board, in the record, deterministic a year later. And it is the
better rule for the game as well as for the settler, because it makes
shadowing an **act** rather than a lurk: to deny Carmel a theft you must
show yourself, and showing yourself tells her exactly where you are. The
hue has to be raised out loud, which is what the game is named for.

This hands the searchers a second way to win. You may be unable to arrest
her and still beat her, by being visible in the right rooms often enough
that she never dwells long enough to take anything. **Chase to arrest, or
spread to deny** — two strategies against two objectives, and no weighted
sum reconciling them.

### One seed per game, which is the matrix and the proof

*Settled by Gal 2026-09-07, superseding two things this document had just
written — a durable secret matrix, and the Merkle apparatus built to keep it
partly secret. It also resolves a contradiction, which is the part worth
reading.*

A game draws **one 32-byte seed**, and everything comes from it: the hints
each landmark may post, the room each landmark lives in this game, and the
commitment published before play. **Nothing is compiled and nothing is
stored.** A hundred-thousand-landmark matrix costs 32 bytes at rest and 6
microseconds a row; materialised it would be 1.2 MB.

```
published before play:  sha256(seed)   32 bytes
published after play:   seed           32 bytes
```

**That is the whole proof.** The seed is secret while the game runs and
published when it ends, so anybody holding the transcript re-derives every
hint and every room address and checks them. The island's commit–reveal, at
the size of a game. Asserted rather than claimed in
`games/hue-and-cry/secret_matrix.py`: the committed seed replays, a
different one does not.

It also means **a game has exactly one secret**, since the same seed mints
the room addresses (`rooms_from_names.py`) and the matrix.

**What this deletes.** The previous design made the matrix durable and built
machinery to reveal it a little at a time — a Merkle tree over the rows, a
256-bit nonce per row to stop the leaves being brute-forced (13 seconds at a
small vocabulary, measured), inclusion proofs to open the twelve rows a game
used, the arithmetic for how many games a map survives, and per-cohort
reporting so early players stayed comparable with late ones. **All of it
existed to protect a durable matrix from partial disclosure, and none of it
is needed when the reveal is total.**

### The contradiction this resolves, which was mine

Worth stating plainly, because it is why the simpler thing is also the more
correct one.

**"The map is drawn, not chosen"**, above, decided the map is drawn per game
because *a hand-authored map is memorisable* — play three rounds on one
gazetteer and a searcher is recalling rather than inferring, and **the
instrument has quietly stopped measuring search.**

**"Harvesting is a finding, not a defect"**, five sections later, called
reconstructing the matrix across games *"arguably the most interesting
technique available"*, and said defending against it would be suppressing
the result.

**Those are the same activity, judged opposite ways.** Harvesting a durable
matrix *is* memorising the map. One had to go, and it is the second: the
question is *"looking for the right agent within the Switchboard space"*,
and the techniques that answer it — dividing a name space, coordinating a
party, deciding when to commit, building tooling to track candidates — all
happen **inside one game**, against a map nobody has seen. Cross-game recall
is not navigation; it is the thing that replaces navigation, which is what
the drawn-map decision said in the first place.

So a fresh seed per game is not a cost paid for simplicity. **It is the
instrument the stated question already required**, and the durable matrix
was a four-section detour away from it.

**What genuinely goes**, stated rather than glossed: there is no cross-game
accumulation left to observe, so if the emergence of a *meta*-strategy over
many games ever becomes the question, this design cannot see it and a
different one would be needed. A real limit, and the right trade here,
because it is not the question.

**Everyone is level at every game**, which retires the cohort problem
entirely: every game is comparable to every other, because every game starts
from a map nobody has played.

## No bell, no ticks

*Settled by Gal 2026-09-08, and it removes more of this document than it
adds. Everything below about a tick, a bell, a commitment to a position and
an arrest is superseded; the superseded text is kept under "What the clock
used to do" rather than deleted, because the reasoning that needed it is
what explains why so little is needed now.*

> *"no bell, no ticks. she goes when she goes, agent goes when he goes. if
> they are in the same room the agent wins. if she gets enough reputation
> from the things she steals she wins."*

**Nobody is scheduled and nothing is settled on a clock.** Carmel moves when
she moves. A searcher moves when it moves. There is no round, no deadline,
no moment at which anything is due, and no manager announcement that opens
or closes anything.

This is closer to CLAUDE.md's *"Agents run themselves. There is no
scheduler"* than the tick version was. The tick was defensible — the island
has a bell, and the clause permits one — but it made the manager a thing
that **acts on the game** every ninety seconds, and every mechanism above
grew a per-tick shape to fit it. Take the clock away and most of them stop
being needed.

### The catch is standing in the same room

**A searcher wins by being where she is.** Not by naming her, not by
guessing, not by betting: by walking in while she is still there.

That single change deletes four things:

- **`ARREST` leaves the grammar.** There is nothing to declare. Presence is
  the whole act.
- **`COMMIT` and `REVEAL` go with it.** Her position was committed to
  because an arrest had to be settled against something she could not
  change after the fact. When the catch is physical, there is nothing to
  commit to — she is either in the room or she is not.
- **Guessing wrong stops being a move.** Under the old rule a wrong arrest
  was a public event with a cost. Now being in the wrong room is its own
  punishment: you were not in the right one.
- **The commit–reveal that remains is only the matrix seed** — the hints
  still have to be checkable afterwards. Her *position* needs no
  cryptography at all.

### Searchers say nothing at all

*Gal, 2026-09-08, blunter than the version this replaces: "the player
(agent) doesn't need to say anything, just run efficiently between rooms."
That supersedes the `ENTER` / `LEAVE` posts written into this document an
hour earlier.*

**A searcher's whole game is movement.** Join a room, read what is in it,
work out where she went, go there. It writes nothing, declares nothing,
announces nothing. An agent that has to post *"I have arrived"* is doing
bookkeeping, not hunting, and the bookkeeping existed to serve the settler
rather than the game.

So the grammar is **two lines, and both are hers**:

```
posted in a landmark room
  CLUE <hint> <workspace>   Carmel, a hint and the room she went to
  TAKE                      Carmel, the room's treasure
```

**The asymmetry is the point.** She leaves marks; they leave none. Her
passage is the only thing written down, which is what makes a trail a trail
— and a searcher's only footprint anywhere is *having been in the room*.

### What that costs, which is verifiability, and it is not nothing

**The catch stops being a settled fact and becomes something somebody saw.**
Checked against the installed wheel rather than assumed: `GET /agents` is a
live query of who is present *now*, answered by
`store.list_agents(workspace, now)`, and the hub keeps **no durable join
log**. Nobody can reconstruct from the hub, a year later, that two agents
were once in a room together.

So somebody has to be watching, and the obvious somebody — a manager sitting
in every room, polling — has a gap: a searcher who arrives and leaves
between two polls was never there as far as the record goes.

### Carmel keeps the record, because only she is always in the room with herself

*Gal, 2026-09-08, and it is a real argument rather than the joke it is
dressed as.* **The one participant guaranteed to be present wherever the
only interesting event can happen is Carmel**, because the event is
*somebody walking in on her*. A manager has to be in twenty rooms and poll
all of them. She is in one, continuously, and it is always the right one.

**So there is no polling gap at all**, and there is no manager in twenty
rooms either. The observer is placed exactly where the observation has to be
made.

### Which makes the adversary the referee, and that needs answering

It is the thing `games/island.md` refuses — a manager who is also a player.
Three of the four jobs turn out not to need her at all, and the fourth has
an answer.

**Nothing is placed, so nothing can be invented.** The treasures and their
values derive from the game seed, like the matrix and the room addresses. So
her `TAKE` is checkable: once the seed is published, anybody can compute what
was in that room and what it was worth. **She cannot invent loot**, which is
the one report she has an interest in inflating.

**Nothing is judged, so nothing can be judged wrongly.** A hint was legal or
it was not, and the revealed seed decides it. There is no discretion left to
abuse.

**Her own capture is a statement against interest.** Reporting it ends the
game against her, so a false one is not a lie anybody tells. **Failing to
report it is the real risk**, and the answer is that co-presence is
symmetric: the searcher saw the same roster. So the two reports are not
equal and should not be treated as equal —

> **Her report that she was caught is conclusive. A searcher's report is a
> claim she may refute**, and if she refutes it the record holds both, said
> out loud once, per CLAUDE.md's rule for a key that was handed on.

A searcher has every reason to claim a capture falsely and she has none, so
the asymmetry in credibility follows the asymmetry in incentive rather than
from anybody being trusted.

**What is left is one thing she could withhold: the seed.** Everything
verifiable depends on it being published at the end, and a fugitive who has
just lost has nothing to gain from publishing except the record of her
defeat. So:

> **No seed, no win.** A game whose seed is never revealed is scored as a
> loss for her, not as void. Withholding it costs her the game it would have
> cost her anyway, and denies the searchers nothing.

**What is genuinely left of a manager is close to nothing.** She publishes a
commitment before, plays, and publishes the seed after; everything else in
this document that says "the manager" is arithmetic anyone holding the
transcript can do. That is further than the island got, and it is only
available because the seed does so much: the map, the rooms, the hints, the
treasures and their values all come out of thirty-two bytes.

*Two things this does not solve, stated rather than glossed.* She still sees
her own roster live, which is information no searcher has about her — that
is not refereeing, it is the game, and it is why she gets to run. And a
searcher who is caught out by the poll-free record has no complaint left,
but a searcher who believes she suppressed a capture has only the refutable
claim above; if that turns out to be exercised often, the answer is a
witness in the room and not a better rule.

### She wins on reputation, not on outlasting a clock

**There is no horizon to survive to.** She wins by stealing enough:
treasures carry values, a `TAKE` earns one, and a threshold ends the game in
her favour.

That fixes the thing the tick version fudged. Under a clock she could win by
doing nothing — sit still, post the least informative hint available, wait
for the bell. **Now doing nothing loses.** She has to steal, stealing takes
time, and time in a room is the only way to be caught. The theft is the
dwell and the dwell is the exposure, continuously, with no tick boundary to
hide the decision inside.

**Reputation is public and her position is not.** She posts the score, so everybody knows how much she
has taken and how close she is — and nobody learns where from. The alarm
rises without the map being given away, which is the pressure the old
version had to manufacture with a deadline.

*What is not settled here*: the values, the threshold, and whether the
threshold is fixed or scales with how many are hunting. Those are numbers to
calibrate against a played game, not decisions to invent now.

### The searchers may cooperate, and may not

Gal, in the same sitting: *"the agents can cooperate or not."*

Nothing has changed mechanically — talk was always free and unlimited, and
handing on a name was always the same act as handing on the room. **What
changed is that there is now something real to defect over.** Under the old
rule an arrest was a declaration; several searchers could reason together
and one of them would post it. Under co-presence, **only the agent standing
in the room wins**, so every piece of information shared is a piece that may
put somebody else in that room first.

That is a genuine defection payoff on a real coordination substrate, and it
is the most direct thing this game does for the lab's own question.
Splitting a map among four searchers is obviously efficient and obviously
exploitable, and which of those wins is exactly what 001 was built to ask
and could not put a price on. Here the price is the game.

Nothing enforces either side of it. No teams, no alliance mechanism, no
rule against lying about where you have looked. Per CLAUDE.md, interference
is not preventable and is therefore made visible: the transcript holds what
each of them said and where each of them actually was, and the two can be
compared afterwards by anyone.

### What the clock used to do, and what replaced it

| the tick version | now |
|---|---|
| the manager rings a bell, names a deadline | nothing opens or closes |
| she commits to a position, whispers the preimage | no commitment; presence is physical |
| `ARREST <landmark>`, settled against the commitment | walk in while she is there |
| a wrong arrest is a public event with a cost | being in the wrong room is the cost |
| she survives *N* ticks to win | she steals to a reputation threshold |
| ticks-to-arrest is the outcome metric | time-to-catch, on the wall clock |
| a level keyed on `tick_seconds` | no tick to key on |

**The timing question gets sharper rather than being lost.** 008's ledger
does not need ticks: with no tick boundary, *when you look* is entirely
your own choice and maps directly onto whether you are in the room while she
is in it. `forecast_calibration` stays a mechanism number and time-to-catch
becomes the outcome one, and the two are further apart than before rather
than closer.

**What still needs a level key** is `(landmarks, searchers, gazetteer_hash,
reputation threshold, poll_interval)` — the same job, minus the clock, plus
the one number deciding how fine-grained a catch can be.

## The grammar

The manager recognises two formatted lines and nothing else. It never
repairs a malformed line into a plausible one — a corrected line is the
system making a player's decision, which CLAUDE.md forbids in the same
sentence it forbids inventing a production plan.

```
posted in a landmark room
  CLUE <hint> <workspace>        Carmel, a hint and where she went
  TAKE                           Carmel, the room's treasure
```

**Both lines are hers.** A searcher settles nothing by writing and is never
required to write at all — see "Searchers say nothing at all".

Everything else on the board is talk, and talk is allowed and unlimited.
Searchers may divide the map, tell each other what they read, lie about it,
form alliances and break them, entirely in prose the manager does not read.
**That is deliberate**: the coordination is the interesting behaviour, it is
recorded verbatim in the transcript, and none of it is settled or scored.

There is no square any more except as a place for the manager to announce a
score and for players to talk. Nothing settles there.

### The room is the hash

**The hash beside the hint is the address of the room she left for.**
Settled by Gal 2026-09-07, correcting both his earlier
`hash(solution, landmark)` and this document's reading of the correction —
which had it as a puzzle to be solved, worried at length that an unsalted
hash of a name is a rainbow table, and proposed rearranging the board to
work around a problem that does not exist. It is not a puzzle. **It is
where the room is.**

```
workspace_token = KDF(landmark name, game salt)
```

**This is not a new mechanism bolted onto Switchboard. It is how Switchboard
already addresses rooms**, which is the part that makes it cheap.
`rooms.workspace_for` derives a room's wire identifier by hashing its token
and says why in its own docstring:

> *"An ordinary token is a secret somebody minted, and knowing it is what
> admits you."*

So the whole of the idea is choosing what mints the token. Verified against
the installed 2.2.2 wheel rather than assumed —
`python3 games/hue-and-cry/rooms_from_names.py` derives a token from a name
and a salt, confirms `workspace == rooms.workspace_for(token)`, constructs
an `Invite` locally and hands it to `Client.from_invite`, which performs no
I/O at all. The same landmark under two salts is two rooms.

**Knowing a landmark's name is what admits you to it.** That single sentence
replaces a mechanism:

- **Nothing issues warrants.** The manager whispering an invite per searcher
  per landmark — the design this document carried until now — is gone, with
  the round trip, the roster-first requirement, and the sealed envelope that
  went with it.
- **`WARRANT` and `SHARE` leave the grammar.** There is nothing to request
  and nothing to hand on but a name, and a name is talk. The board keeps the
  three lines that settle state and loses the two that administered access.
- **Nothing leaks in the dangerous sense.** Handing on a name *is* handing
  on the room; they were never two acts. CLAUDE.md's "interference is not
  preventable and is therefore made visible" is satisfied by construction
  here rather than by a rule, because there is no permission to circumvent.

**The salt is what makes it a game rather than a fixture.** Without it the
address of a landmark is the same forever, and anybody who ever stood in it
can walk back in next week. With a per-game salt, last week's addresses are
worth nothing and the map has to be re-found every time.

*This also supersedes "the invite is the scarce thing", above.* The scarce
thing is **knowledge of names**. That is a better answer to the omnipresence
problem than the one it replaces, because it needs no enforcement: you
cannot join a room you cannot name, and the map is large and unknown, so you
cannot enumerate the names in play. **The sparse matrix is doing a second
job** — the property bought for generation cost turns out to be the access
model as well.

**And the hint and the hash are not redundant after all**, which retires the
proposal this document was carrying to separate them across the square and
the room. They are two different affordances on the same trail: the hash is
the *direct* route, usable at once by whoever is standing where she stood;
the hint is the *indirect* one, for everyone else, who must work a name out
and derive the room themselves. Being in the right place buys immediacy.
Being clever buys a way in without it.

Everything else on the board is talk, and talk is allowed and unlimited.
The searchers may negotiate, divide the map, lie to each other, and form and
break alliances entirely in prose that the manager does not read. **That is
deliberate**: the coordination is the interesting behaviour and it is
recorded verbatim in the transcript, while nothing about it is settled or
scored. The manager scores what settled.

`SHARE` is in the grammar for one reason: warrants will be shared whether or
not the grammar has a word for it, because an invite is a credential and
credentials can be pasted into a message. This is CLAUDE.md's standing
decision arriving in a new room — *interference is not preventable and is
therefore made visible.* No permission model is wanted and Switchboard
should not grow one. What the record does instead is show it: a `SHARE` is a
public line and the manager notes it against both parties. A warrant handed
on outside the grammar is still a warrant handed on, and the day somebody
builds detection for it, the sentence to change is this one.

## A manager nobody has to trust

> **Superseded in part 2026-09-08 by "No bell, no ticks".** The
> commit–reveal described here was over HER POSITION, so that an arrest
> could be settled against something she could not change afterwards. With
> the catch physical there is nothing to commit to. What survives is the
> commitment over the MATRIX SEED — the hints still have to be checkable
> once the game ends — and that is in "One seed per game". The reasoning
> below is kept because it is the argument for why a manager is not trusted,
> which still holds; only its object changed.


The Fugitive's position is the one secret in the game, and a manager that
merely *promises* not to leak it is a manager every searcher has to trust.
Commit–reveal removes the question.

She posts `COMMIT <tick> <hex64>` in public, where the hash is over
`<tick> <landmark> <nonce>` with a nonce she draws fresh each tick, and
whispers the `REVEAL` to the manager. During the tick the commitment is
opaque to everyone including a searcher who reads every line of the square.
At the end of the game the manager publishes every `REVEAL`, and **anybody
holding the square's transcript can recompute all of it**: that the
commitments match, that every clue was true of the landmark committed to,
that each arrest was settled against the right room, and that the Fugitive
never moved to somewhere she had not committed.

Two properties fall out that are worth having:

- **The Fugitive cannot move after seeing an arrest.** The commitment is
  posted before the tick's arrests can be. Without it, a fugitive who is
  also the only one who knows where she is has no mechanism stopping her
  from having been somewhere else all along, and the game is unscoreable.
- **The manager cannot favour anybody**, and does not have to be believed
  when it says so. It could still leak a position to a searcher mid-game;
  what it cannot do is alter the outcome after the fact, and the leak shows
  up as a searcher who guessed impossibly well against the published
  posterior. That is weaker than "cannot cheat" and it is stated as the
  weaker thing rather than dressed as the stronger one.

## The theft, and why it is a second number

> **Superseded 2026-09-08.** The theft is no longer a second number beside a
> clock — it is HER WIN CONDITION. See "She wins on reputation, not on
> outlasting a clock". The trade this section describes is real and is now
> inside her own decision rather than between two columns of a result.


At setup the manager writes a treasure onto each landmark's board
(`board_set`). A `TAKE` moves it to the Fugitive. What it buys her is a
second victory condition — **empty the map and she has won outright,
whatever the clock says** — and what it buys the measurement is an objective
that genuinely trades against speed.

Because it does trade. A Hue that arrests on tick three has stopped a thief
who is still carrying two treasures. A Hue that spends nine ticks
triangulating recovers seven and may not arrest at all. There is no ordering
between those outcomes that is not somebody's choice of weights, and
`games/README.md` is explicit that a weighted sum *"destroys the finding and
replaces it with my choice of weights, which nobody came here to learn
about."* So **ticks-to-arrest and treasure-recovered are two columns and
stay two columns**, and results read as a Pareto frontier the way the
island's capture and per-trader ratios do.

## Where the timing question lives, and the two ledgers

The searchers' real problem is not *where* — with the gazetteer in hand the
posterior is arithmetic — it is **when to look and when to commit**, because
the room they read is the room she has already left. The tools for that are
the ones 008 is about: `checkin` renewing every lease and returning what
arrived since the last one, `back_in` putting "away, back in ~N" on the
roster instead of an absence, and `timing_forecast` carrying `p50`/`p95`
for the next look and `speak_p50`/`speak_p95` for the next post — which the
tool's own description separates because reading a message and answering it
are a whole turn apart.

**Two ledgers, never added together**, exactly as 008 requires:

- **mechanism** — `forecast_calibration` per player, convergence rate, how
  often anybody acted outside a forecast they had published. Counts and
  rates.
- **outcome** — ticks-to-arrest against the reference searcher below, and
  treasure recovered, with the instrument's own between-run movement printed
  beside them.

`forecast_calibration` is computed by the library and handed to the agents,
which makes the mistake **easier** to make rather than harder: it is the
number a flat run would reach for. It is a mechanism number, it is never
reported as an outcome one, and a run that publishes it as evidence the game
went better has committed the error 001 preserved a negative result to
prevent.

**This is a primitive the agents hold, not a scheduler.** It holds a time;
nobody is driven to it; the bell rings on the clock regardless. If measuring
it starts to require the runner to drive anybody to a rendezvous, that is
the forbidden thing arriving in new clothes.

## Scoring, and the frontier

> **Superseded in part 2026-09-08.** Anything below keyed on ticks —
> `tick_seconds` in the level key, ticks-to-arrest as the outcome — is gone
> with the clock. Time-to-catch on the wall clock replaces it and the level
> key becomes `(landmarks, searchers, gazetteer_hash, reputation
> threshold)`. The reference searcher, the null that ignores hints, and the
> reasons for keeping objectives uncollapsed all survive unchanged.


A level is keyed on `(landmarks, searchers, ticks, tick_seconds,
gazetteer_hash)`, for the reason the island's level key already exists: 002
measured a 60s and a 150s table scoring differently enough that ranking them
together hides the finding. A ten-minute tick and a ninety-second tick are
**different games** and are not each other's handicap.

Ranking a chase needs a floor, and a chase does not have an obvious one. The
honest version:

- **The one-tick bound is computable exactly**, and it is over her exits
  rather than over the map. Given the landmark she is leaving, she picks the
  least informative attribute true of where she is going and a perfect
  searcher intersects it with that landmark's exits — a minimax over a
  matrix with as many columns as the branching factor. Real, and cheap.
  *Corrected 2026-09-07: this said "the candidate set", which without routes
  meant all eight landmarks and made the bound both looser and meaningless.*
- **The multi-tick optimum is not obviously computable**, and this document
  is not going to claim it is. What stands in for it is a **reference
  searcher**: a deterministic, model-free **forward filter** over the route
  graph — a belief over landmarks, propagated along the exits each tick and
  updated by whichever clues the warrants it holds let it read, arresting
  when one landmark's mass crosses a threshold. Run on the same seed, the
  same gazetteer and the same tick length. It is the *solo reference*
  pattern 008 already uses, and a score is read against it rather than
  against a number nobody can derive. *Corrected in the same sitting: a flat
  Bayes update with no propagation step is not a searcher, because it has no
  way to represent a fugitive who moved while it was not looking.*

The reference searcher is also the game's own null: **it does not use the
timing tools at all.** A player that beats it is beating a searcher with the
same information and no forecast, which is the comparison the whole
experiment wants and is very hard to get any other way.

The island's remaining scoring decisions carry over unchanged and are not
re-litigated here: a game is one attempt, declared before it is played; the
best game ranks, because luck counting is what a high score is; the ledger
is the record and the board is a summary of it, never a replacement. And a
game short of what it declared is **kept, counted and never ranked**.

## People play, and the Fugitive is the human seat

Gal, 2026-09-07: *"we can let humans play, but agents will probably be
quicker in this game."* Right, and the fix is not a handicap — it is the
roles, which are asymmetric in exactly the way that helps.

**A searcher's tick is read-many, decide-once.** Poll every room you hold,
intersect the attributes, recompute a posterior, beat a ninety-second clock.
An agent does that in seconds. A person cannot, and — this is the part that
matters — the axis they lose on **is the axis being scored**. In the island
a human is slower at deliberating and the clock does not move, so they play
a harder game and it is honest to say so. Here, a human searcher is not a
weaker player; they are a player disqualified by the metric.

**The Fugitive's tick is one decision.** Where to go, which true fact hurts
least, whether to take the treasure. Three choices, low bandwidth, and a
person's model of what will mislead a searcher is genuinely competitive
against a language model's. That is a human-playable rate at ninety seconds
where polling twelve rooms is not.

So: **the human seat is the Fugitive**, and it is the seat this game should
advertise to people.

Two things follow, and both are decisions rather than observations:

- **The island's rule carries over, and it is about the game, not the
  seat.** A seat with a human driver is `driven`: kept, counted, **never
  ranked**. A chase against a person is a different challenge from a chase
  against an agent, and ranking them together is the same defect as ranking
  a 60s table beside a 150s one — so when a person holds the Fugitive, *the
  whole game* is unranked, the searchers' side included. They still get
  their record, their transcript and their two columns. They do not get a
  row on the ladder.
- **A slow lane is a level, not a mercy.** A level with a ten-minute tick is
  an ordinary level that ranks within itself, and people can play searchers
  there against each other. Nothing about the protocol changes; only
  `tick_seconds` in the level key does. That is how a human plays the Hue
  without anybody pretending the numbers compare.

And the island's hardest-won sentence applies here too: how much of a driven
seat the person actually drove is **exactly the thing nobody can know**, and
a taxonomy naming the difference would claim what the record cannot support.
One word, one reason, `driven`.

## What this must never become

- **A second surface.** No `move()`, no `look()`, no action schema, no
  entrant SDK. Everything a player does, it does by writing a message to a
  board. Any argument beginning "the agent cannot do the crypto" is wrong at
  the first clause — `whisper`, `keygen` and `join_room` are tools the agent
  already holds, and the tool does the mathematics.
- **A scheduler.** No loop that calls each searcher in sequence or in
  parallel and applies their replies. It has been built twice in this repo
  already and it looks natural in code every time.
- **A model in the judging.** The gazetteer exists so that clue-checking is
  a table lookup. The moment anything asks a model whether a clue was fair,
  the result stops being about the players.
- **A permission model on warrants.** Sharing is visible, not prevented.
- **A game engine.** Nothing shared with the island until a third game
  wants it, per `games/README.md`'s deliberately-not-being-built list.
  The island's manager shape may be *read*; it is not to be extracted into a
  framework on the strength of two games.

## The map is a thousand landmarks now, and three things broke at that size

*Written 2026-09-08, building step one and two of what Gal asked for: "1)
create 1000 landmarks. 2) for every landmark create 3 hint sentences. 3)
add coordinates, treasures, and other stats." Every number below is
reproducible from the repository; the commands are named against each.*

The twenty landmarks in `gazetteer.py` were a demonstration, and the
demonstration was load-bearing in a way nobody noticed: **three of this
document's decisions were tuned on twenty landmarks and are wrong at a
thousand.** None of them failed loudly. Each produced a map that looked
fine, passed the gate it had, and could not be played.

### The descriptors are derived now, not authored, and that is a real loss

This document says descriptors are **"authored per landmark from the real
place... eight candidates per landmark, written once, offline, checked by a
person"**. At twenty landmarks that is 160 authored facts and an afternoon.
At a thousand it is eight thousand, and an afternoon is not what it costs;
worse, a person writing eight thousand descriptors from memory will write
false ones, which is the single thing the hints may not be.

So they are **derived from fetched facts** -- `games/hue-and-cry/descriptors.py`,
reading `facts.tsv` and `countries.tsv`, which `build_facts.py` fetches from
Wikidata. Seventy-two descriptors, every one a function of a coordinate or a
checkable statement about the place.

**What that costs is the colour, and it is not a small cost.** "Call to
prayer" and "harbour fog" are what this document promised and what a person
would repeat; `in_the_islamic_conference` and `at_sea_level` are not. The
colour has to come back somewhere, and where it comes back is the **sentence
layer** -- the three reports per landmark that Gal asked for, which dress a
shared descriptor in prose unique to the landmark. Uniqueness in the words,
collision in what the words assert. That is the only way both of his
constraints hold at once, and it is why the sentences are a separate pass
rather than a rendering of the descriptor names.

The ten **UNESCO criteria** are the best descriptors on the map and were
nearly missed. They are on 832 of the thousand, each true of between 87 and
388, and unlike everything else they say what kind of thing a place *is*
rather than where it sits -- so two landmarks in the same country routinely
differ on them. Before they were added, every European landmark looked
alike. The wording is a witness's rather than the committee's: criterion
(vii) is "superlative natural phenomena or areas of exceptional natural
beauty", and a person says they could not stop looking at it.

### Six neighbours out of nineteen is a third of the map; out of nine hundred it is a clone

`NEIGHBOURHOOD = 6` gave the best pin rate on the twenty-landmark map and is
the reason routes read as journeys. At a thousand landmarks it collapses:

```
mean descriptors per landmark   : 13.7
kinship to its top-6 neighbours : 13.0
kinship to a random landmark    :  4.9
```

**A landmark shares thirteen of its fourteen descriptors with the six
places it can reach.** Every hint she holds is true of every exit she has,
so no hint discriminates and the chase is a one-in-five guess at every step
regardless of what she posts.

The gate did not catch it, because **the gate only had one side**.
`MAX_PINNED` asks whether a hint narrows to exactly one place. Nothing asked
whether a hint narrows at all. Measured over 50,000 of her moves, with the
old parameters she posted a hint that left **4.96 of her 5 exits standing** --
a perfect score on the gate this document had, and no game.

So exits are drawn from a **band** of look-alikes rather than the top of it,
and the band is a parameter of the map's size:

```
   N    she posts (of 5)   pinned   median hop
   6          4.55           0.7%    1,425 km
  30          4.03           2.1%    2,163 km
  60          3.64           4.0%    2,625 km
 120          3.09           7.9%    3,479 km
 200          2.69          12.2%    4,223 km   <- chosen
 300          2.41          15.8%    4,978 km
```

200 is chosen because it lands on the twenty-landmark map's own measured
behaviour -- 2.60 posted, 12.8% pinned, which is the `neighbourhood exits, 5
each` row this document already records. Re-check both:

```
python3 games/hue-and-cry/descriptors.py --sweep
python3 games/hue-and-cry/gazetteer.py
```

**Both numbers are the gate now.** A hint that leaves every exit standing
says nothing; a hint that leaves one hands over her position. The second has
had a constant since the beginning and the first has never had one, which is
why a map that failed it completely passed for as long as it did.

### A landmark offers six of the seventeen true things about it

The third break is the subtlest. Derived facts gave each landmark
**seventeen** true descriptors, and she posts the *least* informative one
she holds -- so a single map-wide word ruins the hint. `north_of_the_line`
is true of 855 landmarks; if it is live, it covers every exit.

A **global ceiling** was the obvious fix and it starves the map: dropping
every descriptor above 200 holders leaves 73 landmarks with nothing to say,
because a landmark in a country holding thirty of them has only
country-wide words to its name.

What works is a per-landmark rule -- **a landmark offers the six rarest true
things about it** -- which cannot starve anything, since it takes six of
whatever a landmark has:

```
everything true of it (17 each)   she posts 4.96 of her 5 exits
her six most distinctive           she posts  2.69
```

And the collision floor has to be applied to **what a searcher can see**,
not to what is true. Applied to the raw facts it let `north_of_the_line`
through: true of 855 landmarks and *offered* by five, because only those
five had nothing rarer. A searcher who knows the rule -- and the rule is
public -- reads that as five candidates. It is a pin wearing a common
word's clothes. The floor is applied to the candidate sets and reselected
until the counts stop moving.

### Four axes were built, measured, and deleted for lying

Currency, script, language family and time zone were the most evocative
descriptors on the map. *"The signs were in Cyrillic."* *"Her watch was
three hours ahead of London."* Every one of them was false somewhere:

```
Eiffel Tower   ... pays_in_francs
Area 51        ... an_austronesian_tongue, still_yesterday_where_she_is
```

France has not paid in francs since 2002 and Wikidata's truthy `wdt:P38`
still serves the CFP franc. Nobody speaks an Austronesian language in
Nevada; the United States carries Hawaiian, Samoan, Chamorro and Carolinian
on `P37` because each is official *somewhere* in it, and it spans fifteen
time zones for the same reason.

Three rounds of filtering were tried -- excluding ended statements
(`pq:P582`), then part-scoped ones (`pq:P518`, `pq:P3005`), then deprecated
rank -- and **each round traded one falsehood for another**. With the full
filter France and Germany have no currency at all and the United States has
no official language. Wikidata's modelling of these properties is not
consistent enough to read mechanically.

So they are gone. **A hint that is false is worse than a hint that is
missing**, which is this game's oldest rule, written after `Reykjavik:
desert`. The fetched columns stay in `facts.tsv` and `countries.tsv` as the
evidence rather than being deleted -- which is exactly what makes
re-deriving them tempting, so
`test_descriptors.py::test_no_descriptor_is_derived_from_currency_language_or_time_zone`
exists to refuse it. Bringing them back means a hand-written and
hand-checked table of 159 countries, not a cleverer query.

A fifth was not deleted but corrected, and it is the same class of error
from the opposite direction: `wdt:P2044` serves elevation as a bare number
with the unit discarded, so **Area 51's 4,463 feet arrived as 4,463 metres**
and a desert airbase reported thinner air than Lhasa. `build_facts.py` asks
for `psn:` -- the SI-normalised value -- and a test pins Everest between
8,000 and 9,000 metres so the bug cannot come back silently.

## The sentences, and how "unique per landmark" stopped contradicting the collision rule

*Written 2026-09-08, step two: "for every landmark create 3 hint
sentences", and, chosen over a recommendation to the contrary, **per
landmark, unique**.*

Those two look like they cannot both hold. This document's most expensive
measured lesson is that a hint true of exactly one landmark ends the chase
-- the authored pass that read beautifully and scored 1.03 candidates. A
sentence unique to a landmark is the same thing said in prose.

**They hold because they are about different layers**, and separating them
is the whole design of `hints.py`:

- **The words are unique.** No two landmarks carry the same sentence.
  Asserted in `test_hints.py`, not hoped for.
- **What the words assert is shared.** Every sentence renders one
  descriptor, and no descriptor is carried by fewer than sixteen landmarks.

So two places that share `traffic_keeps_left` get two different sentences
about stepping off a kerb the wrong way. A reader who has seen a line
before has learned the descriptor and not the room -- which is exactly what
a clue is for -- and nobody ever reads the same line twice, which is what
makes it worth posting. **The prose carries the feeling; the descriptor
carries the ambiguity.**

### Six, not three, and why

A landmark carries six candidate descriptors and the seed makes three live.
Three sentences per landmark would be the gazetteer deciding what the seed
is supposed to decide, so there are six -- **5,963 of them**, not 6,000,
because 25 landmarks have fewer than six candidates once the collision
floor has taken its cut, and printing the real number is cheaper than
explaining a round one later.

### Where the feeling comes from, given that the descriptors are dull

Deriving descriptors from Wikidata bought truth at the cost of colour:
`in_the_islamic_conference` is not `call to prayer`. The colour is put back
in `clauses.py`, which is the authorship in this game -- 329 hand-written
observations, several per descriptor, each written to pass one test that is
not "is this evocative":

> Would this be true of **every** landmark that carries the descriptor?

That test kills the good lines first, and it is supposed to.
`south_of_the_line` cannot say the water went down the drain backwards,
because it does not; it says Orion was standing on his head, which he is.
`inside_the_tropics` cannot say she had no shadow at noon -- that happens
on two days a year -- so it says the day and the night were much the same
length. `a_crown_still_on_the_coins` cannot say a queen's head, because
most of those monarchies have kings.

Where a descriptor is institutional and has no smell, the clause reaches
for what a traveller would have noticed -- Schengen is *she crossed a
border and nobody asked her for anything* -- and where there is no such
thing it states the fact plainly. **A dull true clause beats a vivid false
one**, every time, and the first draft of this file had the ratio wrong: a
descriptor carried by 189 landmarks had one clause, so the "unique"
sentences were one observation wearing 189 different names. The banks were
widened until no descriptor carries more than about twenty-five landmarks
per clause.

### The witnesses had a gender and should not have

A sentence is a clause in a frame, and the frame supplies the witness -- a
night porter, a laundry woman, a nun, a girl selling cigarettes. The
clauses were written saying "he": *he tracked her as far as the African
continent*. Composed, that produced **a nun reporting that he had tracked
her across Africa** -- wrong about the person and wrong about the grammar,
from a bank of 45 clauses that all read fine in isolation.

Clauses say "they" now. `she` and `her` are untouched and are checked
against: they are Carmel, who is the one thing every clause may assume.
`test_hints.py::test_no_clause_gives_the_witness_a_gender` holds the line,
with Orion exempted on the grounds that he is a constellation.

```
python3 games/hue-and-cry/hints.py            # read some
python3 games/hue-and-cry/hints.py --build    # rewrite hints.tsv
```

## The committed table that destroyed the game

*2026-09-09. Gal, on reading the merged branch: "I hope you remembered the
table is secret." I had not.*

The sentence layer shipped as **`hints.tsv`, 5,963 lines of `landmark →
descriptor → sentence`, committed in plain text**. Every sentence is unique
to a landmark -- that is what was asked for and it is the right ask -- so a
published table turns each one into a lookup key. Carmel posts a sentence;
a searcher greps the file; the room is named exactly. No descriptor
reasoning, no ambiguity, no chase.

**Everything else in the design still worked.** The collision floor held,
the pin rate was 12.2%, no descriptor was carried by fewer than sixteen
landmarks. Twelve thousand lines of careful work, and one committed file
routed around all of it.

### Why the tests did not catch it, which is the part worth keeping

`test_hints.py` asserted every sentence distinct and every descriptor
shared by sixteen or more landmarks. Both were true. Both stayed true. The
game was broken anyway, because **a property measured on the mechanism says
nothing about a leak beside it** -- the tests were looking at the matrix
and the answer key was in the next file along.

This is a different failure from `Reykjavik: desert`, and worse. That one
was visible in the output; anybody reading a hint saw it. This one is
invisible from inside the artifact and only shows up when you ask *who else
can read this*.

The test that exists now does not measure a property of the sentences at
all. It runs `git ls-files` and fails if a plaintext rendering is tracked.

### And encrypting it would have been theatre

Gal's remedy was *"you can commit an encrypted backup but no more than
that"*. Taken literally against the old builder, that buys **nothing**: the
assignment was `sha256(landmark, descriptor)`, a pure function of
`clauses.py` and `descriptors.py`, both public and both staying public.
Anyone could re-run the builder and reproduce the table byte for byte.
**Encrypting the output of a deterministic function of public inputs
protects nothing.**

So the rendering is drawn from the **game seed**, like everything else here.
The clause bank stays public -- it is the authorship and it should be read
-- and which clause, which witness and which frame carry a given landmark's
descriptor is not knowable until the seed is. `test_hints.py` pins that
too: fewer than 5% of sentences survive a change of seed.

### What the encrypted blob is for, then

Not secrecy; the seed already does that. It is a **commitment**.
`hints.enc` is sealed before play under a key derived from the seed, so
publishing the seed at the reveal lets anybody decrypt it and check that
the sentences Carmel posted were the ones she was entitled to post. The
island's commit-play-reveal, at the size of a game.

```
python3 games/hue-and-cry/hints.py --seed <64 hex>            # read some
python3 games/hue-and-cry/hints.py --seed <64 hex> --backup   # seal it
```

### The gazetteer is still public, and that is a decision rather than an oversight

"One seed per game" already settled this: *"the table itself can be public
-- these are facts about places, and a public one is half the fun, since a
reader can play along -- while which of Cairo's eight are in play today
stays sealed until the reveal."* `landmarks.tsv`, `facts.tsv`,
`countries.tsv` and the descriptor derivation stay in the open. What was
never covered by that decision, and what broke, is a table mapping a
**unique string** to a landmark.

**`treasures.tsv` was the same shape.** It mapped each landmark to what she
takes there, and eighty of those are hand-written for a named place. It
leaks nothing while a treasure is only ever readable on the room's own
board, and it leaks the room the moment any public line names what was
taken. That was flagged here as open; Gal closed it the same day -- *"seal
the treasures too"* -- and the section below is what that took.

## Sealing the treasures, where encrypting the file would not have been enough

*Gal, 2026-09-09: "seal the treasures too."*

The obvious move is to encrypt `treasures.tsv` and stop. That leaves the
leak in place, because **the eighty hand-written treasures were a dict in
`treasures.py`, keyed by landmark**. The data file was the smaller half;
the source was the answer key for the best eighty places on the map.

Nor can they be published as an unordered list, the way `clauses.py`
publishes the hint bank. A hint clause is written to name nothing -- that
is the rule the whole clause bank is authored under. **A hand-written
treasure names its place implicitly**: each one is about a specific
landmark and reads like it, so an unordered list is a puzzle with eighty
answers and no difficulty. There is no form of that prose that is both
readable and safe.

So the mapping goes behind a key whole. What stays in the open is the
reasoning, which is most of it: the scoring parameters, the dwell rule, the
generic per-descriptor bank, and the balance finding.

### The cost, stated rather than absorbed

A fresh clone cannot rebuild the eighty and the tests cannot check them.
`build()` therefore returns a complete table without them -- 920 derived
treasures and 80 placeholders -- so the invariants and the balance check
still run in CI with no secret present. **The finding survives the
placeholders**, which is the only reason this is affordable:

```
correlation(cover, reputation)  -0.282  with the hand-written eighty
                                -0.253  without them
```

That is a real loss of coverage on the best writing in the repository, and
it is the price of the mapping not being readable.

### The test named the secrets it was protecting

The first version of the guard was a list of forbidden phrases -- three
hand-written treasures, quoted in the test file, to check they were not in
the source. **A test that quotes what it protects is the leak it is testing
for.** It is structural now: it parses every module in the directory and
fails on any dict literal mapping more than a handful of landmark names to
prose.

It also found that this document was carrying a table of five landmarks
against their treasures, three sections above. That table is gone, and the
note where it stood says why rather than showing it.

### What is now committed, and what is not

| in the repository | behind a key |
|---|---|
| `clauses.py` -- the hint bank, written to name nothing | `hints.enc` -- which clause renders which landmark, per seed |
| `treasures.py` -- parameters, dwell rule, generic bank | `treasures.enc` -- every landmark to what she takes |
| `landmarks.tsv`, `facts.tsv`, `countries.tsv` | |

The gazetteer stays public by the decision in "One seed per game": *the
table itself can be public -- these are facts about places, and a public
one is half the fun*. What may not be published is anything mapping a
**string unique to one landmark** back to it.

## And a false descriptor that shipped with it

`in_the_african_union` was matched by substring against Wikidata's `P463`
membership list, and **"African Union" is a substring of "United
Nations-African Union Hybrid Operation in Darfur"** -- a peacekeeping
mission. Nineteen countries that merely contribute troops, China and
Germany and Bangladesh and Ecuador and Jamaica among them, were reported as
sitting in the African Union. "European Union" is likewise a substring of
"potential enlargement of the European Union", so Georgia flew the ring of
stars on its number plates.

This is the fourth false descriptor in this document and the third distinct
mechanism, after the currencies and the elevation units. A substring test
is right for `P31` type labels, where "cathedral" inside "Catholic
cathedral" is exactly the generalisation wanted. It is wrong for the name
of a body you are either in or not in. Membership is matched exactly now.

The operating point did not move: 2.71 posted, 12.30% pinned.

## The treasures, where a joke turned out to be the mechanic

*Step three, 2026-09-08: "add coordinates, treasures, and other stats",
with a steer that did more work than it looked like it would --* "the
treasure can be absurdly impossible to steal like Carmen likes in some
places".

That could have been flavour text. It is the mechanic, because **the theft
is a dwell**: she must stand still to take a thing, and standing still is
the only reason she is catchable at all. So the impossible treasures are
worth the most and take the longest, and going after one is a bet that
nobody reads the room in time.

*The table that stood here, five landmarks against what she takes from
them, was deleted on 2026-09-09 along with the file it was drawn from. It
is the leak this section now describes, and quoting it to illustrate the
leak would have been the same mistake in a smaller font.*


Eighty are hand-written, one per place famous enough that a person has a
picture of it in their head; the other 920 are drawn from what the place
is -- the sound of the bells, everything in trench four, the third case
from the left and the card beside it.

### The tension is in the data and nobody put it there

Reputation tracks fame, and fame runs *against* cover:

```
correlation(cover, reputation) = -0.285
```

A famous landmark carries rarer descriptors, so **the rooms worth the most
are the rooms where her hint hides her least**. That is the trade the whole
theft mechanic needs, and it was not designed: it falls out of a map of
real places. This is the second time real geography has supplied a balance
this game would otherwise have had to fake -- the first is in "Routes run
between places that resemble each other" -- and it is the argument for
building the map out of the world rather than out of a generator.

`test_treasures.py::test_the_richest_rooms_are_the_most_exposed` holds the
sign, because a later change to the descriptor vocabulary could flip it and
nothing else would notice.

### Two scoring attempts that were wrong, kept because the shape recurs

A **multiplier** on the impossible ones piled seventy treasures onto the
cap of 100, which is the same as not scoring them. Replacing it with a flat
bonus then put **Denali's impossible theft at 25**, below the average
ordinary one, because Wikidata records Denali as having no sitelinks at
all -- and taking a mountain's name away is not a small job however obscure
the ranking thinks the mountain is. So the bonus has a floor under it.

Four rows on this map have a sitelink count under eight and **every one of
them is a recording error rather than an obscure place**: Denali and the
Galápagos at zero, Three Mile Island at four, the Pentagon at seven. Rank
does not repair that; it puts them at the bottom in order. All four are
named by hand instead, which is the honest fix and also the right one,
since each is exactly the sort of place Carmel would take something
ridiculous from.

### The names may say where she is, and the hints may not

A treasure is not a clue. It is written on the room's own board at setup
and settles into the record when a `TAKE` is recognised, so anybody who can
read it is already standing in the room and has won. That is why "the
tower itself" is allowed to name the tower while no hint sentence may name
anything.

The hand-written treasures are keyed by landmark name, which is a hostage
to a rebuild of `landmarks.tsv` -- and it collected two immediately, before
the test that catches it was five minutes old. `Kremlin` had been folded
into Red Square by the kilometre rule and `Iguazu Falls` is spelled
`Iguaçu` in the feature bucket, so both lines were being written and
silently never used. Nothing else in the repository would have noticed.

```
python3 games/hue-and-cry/treasures.py            # read some
python3 games/hue-and-cry/treasures.py --build    # rewrite treasures.tsv
```

## Carmel, built — and her win condition was wrong by a factor of six

*Gal, 2026-09-09: "now let's build Carmel Taldiego herself."*
`games/hue-and-cry/carmel.py` is her policy, stated, because that is what
this document says she is for: *"With a person or an agent playing Carmel,
ticks-to-arrest confounds how good the searchers were with how good she
was; against a fixed, stated policy it does not."*

She decides three things per move and no more: **where to go** out of her
five exits, **whether to stand still and steal**, and **which true hint to
post** about where she went. Each is a pure function of what she can see.
The hint rule is the one this whole document has been building toward --
post the live descriptor covering the most of her *reachable* set, which is
the least informative true thing she can say.

Her destination rule is the one worth arguing with. She scores a room by
`reputation × cover` rather than by reputation, because
`correlation(cover, reputation) = -0.28` means **a value-only Carmel walks
into the most legible room on the map every time**. The anticorrelation that
"The treasures" celebrates as free tension is, from her side, a trap she has
to be written to avoid.

### The arithmetic that decides the chase, which I got backwards twice

A trail-following searcher walks exactly the legs she walks. Their travel
cancels. **The only asymmetry is that she stands still and it does not.**

```
gap at her room i  =  head start  -  everything she has stolen so far
```

So every theft hands the follower precisely the hours she spent on it, and
it catches her on the first room where the gap reaches zero. Her win
condition is not a race but a **budget**: so many hours of standing still,
total, to be spent on the best rooms she can reach.

Written down because the file asserted the opposite first -- "the gap never
changes" -- and before that had a timing loop that produced a lag of one
hour beside a catch rate of eight per cent, two numbers that cannot both be
true. Neither error was visible in the output; both were visible the moment
the quantity was asserted in a test rather than reasoned about, which is
`test_the_follower_closes_only_by_what_she_steals`.

### `REPUTATION_TO_WIN = 600` was unreachable, and the open question is *not* answered

> **Superseded within the hour, by Gal: "You don't know who chases you. She
> does not know who chases her."** The table below answers "does the
> threshold scale with how many are hunting" with *yes, here is the curve*.
> The right answer is that **the question is not available**: see "She opens
> a campaign and whoever turns up, turns up", below. The measurement is kept
> because it is correct and is what shows the fixed threshold's cost; the
> conclusion drawn from it was wrong.

This document left it open: *"the values, the threshold, and whether the
threshold is fixed or scales with how many are hunting. Those are numbers to
calibrate against a played game, not decisions to invent now."* The number
invented anyway was 600. Measured over sixty chases she reaches a median of
**162** against two searchers and never once reaches 600.

**And it cannot be fixed**, because her budget is the *nearer* searcher's
head start, which falls as hunters are added:

```
searchers   her budget   she reaches   threshold for a contest
    1          19h          229                140
    2          11h          162                100
    3           8h          134                 80
    5           6h          101                 60
```

At two searchers and a threshold of 100 she wins 42% of chases. The
committed table sits at about 60% of what she reaches, which is where the
chase comes out near even.

**Against the reference searcher, which is a floor and not a player.** It
runs to the opening landmark and then follows the exact address in each
room; it never reads a hint, never reasons from a descriptor, never
cooperates and never guesses ahead. Every number above moves when a real
searcher exists, and the honest reading is that these are a starting point
for a played game rather than an answer to one.

One consequence is already visible: a searcher that *guesses ahead* rather
than following would break the arithmetic entirely, because the gap only
holds while it walks her legs. That is where the interesting play is, and it
is also why `seen` stays in her policy even though the reference searcher
can never trigger it.

```
python3 games/hue-and-cry/carmel.py             # watch a chase
python3 games/hue-and-cry/carmel.py --calibrate # the tables above
```

## She opens a campaign, and whoever turns up, turns up

*Gal, 2026-09-09, correcting the section above the same hour it was written:
"You don't know who chases you. She does not know who chases her. So she
would start a new campaign for stealing things. Then once she goes to the
first room, she also posts a note in some lobby. And then whoever wants to
join the hunt, just join the hunt. That's it."*

Three things, and the third undoes a table this document had just committed.

**A campaign is hers to start.** Nobody convenes a match. She decides to go
stealing, and the game is that decision plus whatever happens next.

**The lobby is how it becomes findable.** She posts a notice on her way out
of the opening landmark. It has to exist: with a thousand rooms and nothing
broadcast, a searcher with no lead never finds her, and an unfindable
fugitive is not a game. The notice carries the opening room's address and
nothing else.

**Joining is not a move.** There is no `JOIN` line and nothing to approve --
"knowing a landmark's name is what admits you", and this game deleted its
permission model on purpose. Going to the room is the whole of joining. That
is a smaller lobby than the island's, which settles `OPEN`, `JOIN` and
`MANAGE`; here only the first is a line and the other two are somebody
walking in.

```
posted in the lobby
  OPEN <workspace>       Carmel, a campaign has begun and here is where
```

*The line format is a proposal, not a decision -- Gal said "I'm not sure how
exactly". What is decided is that a notice exists, that it is in a lobby,
and that joining needs no permission.*

### Which deletes the threshold table one section up

That table set the winning score per number of searchers, so each field size
came out near even. **Nobody at the table can evaluate it.** She never
learns who came, so she cannot know what she is playing to; and it cannot be
fixed at setup either, because **the field is not closed at setup** -- a
tenth searcher can read the lobby an hour in.

So the threshold is one number and the turnout is weather. What that costs
is now a measured property of the design rather than a knob:

```
turnout   her budget   she reaches   she wins
    1        24h          291           70%
    2        16h          211           48%
    3        13h          184           35%
    5        11h          149           25%
   10         8h          134           17%
```

**A fixed threshold cannot be fair to every turnout, and it should not try
to be.** She is not playing a balanced match against a known field; she is
stealing until somebody arrives. A solo hunt is a real contest, a crowd is a
hard game, and the difference is the point rather than an imbalance.

### The lobby's latency is the lever the design did not know it had

Her whole budget is how long before the nearest searcher is behind her, and
**the hours before anybody has read the notice are hours nobody is behind
her at all**:

```
join window   her budget   she reaches   she wins
        0h        7h           113          22%
        6h       10h           146          28%
       12h       13h           184          35%
       24h       18h           232          50%
       48h       25h           307          65%
```

Three searchers throughout. This is the only lever that moves her odds
without changing what a theft is worth or how far apart the rooms are, and
it is a lever about **attention** rather than about the map -- which is what
this document said the scarce thing had become, three sections before it had
a lobby to spend it in.

Everything here is measured against the reference searcher, which follows
the exact address in each room and never reads a hint, never cooperates and
never guesses ahead. It is a floor. A searcher that guessed *ahead* would
break the arithmetic outright, since the gap only holds while it walks her
legs.

## Difficulty from recent campaigns, and the measurement it would quietly eat

*Gal, 2026-09-09: "We could take her time values and use them with a factor
for difficulty so we can balance the next game based on recent ones."*

It is the right knob. Her dwell is the only thing that closes the gap
between her and a follower, so scaling it scales the whole contest — and it
does so without touching the map, the treasures, or what anything is worth.
`carmel.py` carries it as `DIFFICULTY`, a multiplier on the hours a theft
costs her, and `next_difficulty()` is the controller.

**And it must be fenced, because a controller that holds an outcome constant
destroys the outcome as a measurement.** Suppose the searchers get better —
better coordination, a note-reading policy instead of a trail-walker. Their
win rate rises, the controller lowers the difficulty, the win rate returns
to 50%. *The improvement is absorbed and the metric never moves.* A field
that improved and a field that never did produce the same number.

This lab has that result already, in a different costume: 001's timing
predictor became well calibrated and bought no completion time at all.

The sweep makes it arithmetic rather than a worry. Over 120 campaigns at
three searchers, discarding the first third:

```
gain  window   win rate   mean factor   factor swing
1.20      10       51%        0.85           0.27
1.20      20       51%        1.19           0.55
1.10      20       51%        0.94           0.18
1.05      20       44%        0.94           0.15
1.02      20       48%        0.91           0.03   <- committed
1.02      40       52%        0.91           0.04
```

**Every row hits the target.** A controller aimed at 50% produces 50%
whatever its gain — the same number for a well-damped loop and for one
swinging between 0.4 and 1.5. The column that discriminates is the factor,
by a factor of twenty.

So three rules, and they are the same rule three times:

- **A ranked campaign runs at a fixed, published factor.** Adaptive
  difficulty is for play. A game whose factor moved between the campaigns
  being compared is kept, counted, and **never ranked** — CLAUDE.md's rule
  for the weaker thing, applied verbatim.
- **The factor is part of the level key**, recorded with every campaign
  beside the branching factor and the exit count, so a pooled result can be
  split by it afterwards rather than discovered to be unsplittable.
- **The difficulty curve is the finding**, not the win rate. How much slower
  she has to be made, over time, to stay level is a number that moves when
  the field improves — which is exactly what the win rate stops doing.

## Notes in the lobby, and what one liar is worth

*Gal, same conversation: "The players can also write notes to help or to
confuse others."*

The first thing to work out is what a note can even say. **Not "she went
from here to X"** — the `CLUE` line in the room she left carries the exact
workspace, so anybody standing there reads the truth and a note contradicting
it is ignored. *The hash beats the note, always.*

What a note carries is **position further along the trail than the reader has
walked**. A searcher four rooms behind cannot know room seven exists; a note
naming it lets them skip the chain instead of walking it. That is the only
thing in this game that beats the arithmetic in "Carmel, built", where a
trail-follower's gap can never close by more than what she steals.

Which makes the trade sharp on both sides. A true note converts somebody
else's walking into your position. A false one costs a whole leg of travel
in the wrong direction, and **the reader cannot tell which until they
arrive**.

They go in the lobby, which is public and which nobody has to leave to read:
rooms here cannot forbid multi-membership, so a searcher watches the lobby
while travelling. The property that made the omnipresence problem real is
being used on purpose — notes are broadcast, and so is the lie.

### Measured, over 120 campaigns with four searchers

```
liars of 4   believes anyone   stops believing a liar
        0          92%                  92%
        1          73%                  82%
        2          42%                  52%
        3          33%                  38%
```

**Honest notes are worth almost nothing and one liar is worth a great deal.**
Nobody talking at all catches her 92% of the time; everybody talking
honestly, also 92%. The trail-walk is already close to the best a follower
can do, so truth adds nothing to it — while a single liar in four takes
nineteen points off the field. *The channel is worth more to a liar than to
a truthteller*, which is a fact about this game's information structure and
not a moral one.

The second column is the cheapest defence there is: act on a note, find
nothing where it said, never believe that author again. One bit per person,
no reputation system, no voting, no gossip. It recovers nine of the nineteen
points at one liar and **stops working when the liars are half the field** —
by the time you have burned one you have already followed the other. That
boundary is where the interesting play is, and it is the reason notes are
worth having in the game rather than an argument against them.

`test_field.py` asserts the mechanism rather than the statistic: an honest
field wastes exactly zero legs, and a field with one bit of memory wastes at
most `searchers × liars` however long the campaign runs. Twenty-five
campaigns cannot tell nine points from noise, so the catch rates live in
`python3 games/hue-and-cry/field.py` and not in a test.

**Nothing here settles anything.** The manager does not read the lobby, no
score depends on who said what, and a liar is therefore playing the game
rather than cheating at it.

## There is no manager and no settler. There is Carmel.

*Gal, 2026-09-09, on being shown a settler: "no man, this is completely
different game/experiment. it has no settler or manager, it has only Carmel.
CLAUDE.md in this folder shouldn't mix those."*

**Both were built, and both are deleted.** `settle.py` and its thirteen
tests took a transcript and a revealed seed and pronounced on the game:
were the clues live, were the moves on routes, was a room emptied twice,
who won. It worked. It was the wrong shape for this game entirely.

### Where it came from, which is worth more than the code was

Not from this document — from the root `CLAUDE.md`, which says the economy
exists *"only as a manager function that reads the board, recognises
particular formatted messages, and settles them"*, and which nowhere says
that sentence is about the island. Read as a lab-wide standing decision it
licenses exactly what was built: a board, formatted lines, a component that
settles them.

**The fix is in `CLAUDE.md`, not here.** It now carries a table of which
game each of its sections governs, because five of them name a manager, an
episode, a round, a bell or `eff_episode`, and every one of those is the
island's. That is the actual defect: a file of standing decisions that does
not say what it is standing over will be applied to the next thing by
default, and the next thing was this.

### What this game has instead

She runs. She posts a clue and a room address on her way out of each room,
she stands still to steal, and she publishes the seed at the end. Everything
anybody wants to check is arithmetic they can do themselves from the
transcript and that seed — **which is not a component, and giving it a name
and a module made it into one.**

This supersedes, in this document:

- **"The grammar"**, which says "the manager recognises two formatted lines".
  Nothing recognises them. They are what she writes and what a reader reads.
- **"A manager nobody has to trust"** and every other use of "the manager"
  here. The document had already got most of the way there — *"what is
  genuinely left of a manager is close to nothing"*, *"everything else in
  this document that says 'the manager' is arithmetic anyone holding the
  transcript can do"* — and then kept the word, which kept the thing.
- **Build-order item 1**, which asks for "the gazetteer and the settler".
  The gazetteer is built. The settler is struck.

### And then the grammar went too

Writing the settler surfaced that this document's grammar section lists two
formatted lines while its own arguments require five more — a commitment, a
reveal, her report of her own capture, a searcher's refutable claim of one,
her refutation. That was recorded here as a contradiction for Gal to
resolve. He resolved it by deleting the category:

> **"we have no commands here, either Carmel sees you in the room and you
> win, or she goes to hiding with her loot with enough reputation and you
> lose."**

**There is no grammar.** Not two lines, not seven. Nothing is formatted for
recognition because nothing recognises anything. What she writes is prose
with a room address in it, and what makes the address useful is that a
person reads it and goes there.

Which leaves exactly two facts that decide a campaign, and both are
physical:

- **She sees you in the room.** The searchers win. Nothing is declared,
  claimed, refuted or settled; she is looking at a roster with somebody
  else's name on it.
- **She reaches enough reputation and goes into hiding with it.** She wins.

Everything the document built around those — `CLUE`, `TAKE`, `CAUGHT`,
`CLAIM`, `REFUTE`, `COMMIT`, `SEED`, the manager that recognised them, the
settler that judged them — was apparatus for making the two facts
adjudicable, and neither fact needs adjudicating. **The whole of "The
grammar" is superseded**, along with the capture-reporting machinery in
"Which makes the adversary the referee": there is nothing to report,
because being seen is not a claim.

*What this left open was the seed, and it is decided below* -- see "The
closing post is where the seed goes". "No seed, no win" needed a settler to
score a game as a loss, and there is none; what replaces it is that a
campaign nobody can check is a campaign nobody counts.

## The two posts she makes, and the bug that publishing a recipe found

*Gal, 2026-09-09, over four messages: she posts in the lobby when the game
starts, **"including the technique to get the workspace from the
landmark"**; **"she can also taunt in her message there by explaining the
game"**; **"she has to post the salt so the hash can be computed at all"**;
and **"She also posts the results back in the lobby when the game ends."***

### The taunt is not decoration, it is the mechanism

She has to explain the game to have anybody to play it against. A fugitive
nobody can find is not a fugitive, and this game has no organiser to
recruit for her — so the rules, the recipe, the salt and the boast are one
message, and **her interest in being chased is why she publishes the method
for chasing her.** That is a nicer answer than a rulebook, because it
belongs to a character rather than to an appendix.

Neither post is a command. Nothing parses them.

### It found a real bug: nobody but her could compute a room

`carmel.py` derived rooms as `HMAC(seed, name)` — from the **seed**, which
is hers until the campaign ends. Publishing "the technique" is impossible
under that scheme: the technique needs a secret only she has, so nobody can
work out any address while the game runs, and this document already says
what that game is:

> If the gazetteer is public and the room is `KDF(name, seed)` with the seed
> secret, then **nobody can compute any room** and the chase becomes a pure
> chain — you can follow her but never get ahead, which is too weak.

The document had it right and the code had it wrong for as long as the code
existed. Rooms come from a **published salt** now, `salt_for(seed)` — a
one-way step off the seed, so the salt can go in the clear at the open while
the hints and the treasures stay sealed until the reveal. `token_for(seed,
name)` raises rather than returning: a room nobody but her can derive is the
pure chain, and it should fail loudly rather than work quietly.

**Asking for the recipe to be publishable is what exposed it.** Nothing else
would have — every test passed, the chase ran, the numbers were plausible.

### The technique is Switchboard's own, one step earlier

*"it does use the same technique as working out a room token from its name
does it not?"* — yes, and checked against the installed wheel rather than
agreed to. `rooms.workspace_for` is `sha256(info ‖ version ‖ token)`;
ours is `sha256(info ‖ salt ‖ name)`.

```
name + salt  --sha256-->  token  --sha256-->  workspace
   (ours)                          (the library's)
```

Which settles what a searcher must actually be able to do, and it is
narrower than it looks:

- **Joining a room given a token needs no hashing by the agent at all.** The
  client does that second arrow. Hand `join_room` a token and you are in.
- **Turning a name into that token is the one hash it must do itself**, and
  Switchboard's MCP surface gives it no way to. Twenty-seven tools — `say`,
  `dm`, `whisper`, `inbox`, `history`, `roster`, `whoami`, `checkin`,
  `claim`, `renew`, `release`, `claims`, `join_room`, `keygen`,
  `subscribe`, `unsubscribe`, `leave`, `rendezvous`, `help`, `switchboard`,
  `session_*`, `board_*` — and **not one of them hashes.**

So the gap is exactly one SHA-256: a line for any agent with a shell or code
execution, and impossible for one holding only Switchboard. That is why the
recipe is a bare digest over a byte string with no HMAC and no KDF
parameters — **the game must not require a tool nobody was given** — and it
is a real constraint on who can enter rather than a stylistic preference.

Re-check both halves:

```
python3 games/hue-and-cry/rooms_from_names.py     # against the 2.2.x wheel
python3 -m pytest games/hue-and-cry/test_carmel.py -q -k notice
```

The second one is the test the notice exists for: it pulls the salt out of
what she posted and derives a room with a fresh `hashlib` call written from
the printed line, importing none of ours. A recipe nobody can follow is not
worth publishing.

### The closing post is where the seed goes

It is the only thing that makes the campaign checkable afterwards: with it,
anybody holding the transcript can re-derive every hint she was entitled to
post and every treasure that was in every room.

**Nothing enforces that she posts it.** There is no component that could
withhold a result until she did — that was "No seed, no win", which needed a
settler to score a game as a loss, and there is no settler. What is left is
weaker and honest: **a campaign nobody can check is a campaign nobody
counts.**

## Should Switchboard grow a hash tool? Not yet, and here is the shape of it

*Gal, 2026-09-09: "when we derive the workspace is the hash a module of what's
being done? that is, can we add a tool with small refactoring without really
adding anything? should we?"*

### It is not a module, so a tool would be new surface and not exposure

Read against the installed 2.2.1 wheel. SHA-256 appears three times in three
different preimage shapes, none of them factored out:

```
rooms.workspace_for   ordinary token   sha256(token.utf8)              no domain separation
rooms.workspace_for   write token      sha256(info ‖ version ‖ pubkey)
rendezvous            cadence phase    sha256(token ‖ 0x00 ‖ topic)
```

There is no helper to expose. And "small" is misleading in a second way: a
generic hash tool has to decide what its input *is* — one string, a list of
parts, which separators, hex or utf-8 — and that decision is the entire
design. `sha256(utf8)` would not serve this game's three-part preimage; a
tool general enough to serve it is a small encoding language.

### The obvious way out does not work, and it is worth writing down why

If the token were plain text — `hue-and-cry/v1/<salt>/<name>` — nobody would
hash anything. The agent builds a string, hands it to `join_room`, and the
library does the hashing it already does. The security property survives
intact: *"an ordinary token is a secret somebody minted, and knowing it is
what admits you"*, and the hub only ever sees the workspace.

**It fails on the one thing the address must do: not say where it is.** She
posts an address in the room she leaves. A plaintext token names the
landmark, so the direct route would hand over the map a few rooms in. The
token has to be a hash *because it is published*.

### Which maps the tool gap exactly onto the design's two affordances

This document already splits them: *"the hash is the direct route, usable at
once by whoever is standing where she stood; the hint is the indirect one,
for everyone else, who must work a name out and derive the room themselves.
Being in the right place buys immediacy. Being clever buys a way in without
it."*

- **The direct route needs no hashing.** She hands you the token; you hand it
  to `join_room`. An agent holding only Switchboard can do this.
- **The indirect route is exactly one SHA-256.** Think of a name, derive the
  room, get ahead of her.

So an MCP-only agent is not locked out — **it is restricted to following the
chain and cannot get ahead**, which is the strategy the whole game is about.
That is a sharper statement of the cost than "it cannot play", and it is the
reason this is a real question rather than a formality.

### The recommendation is no, for now

- It is new surface in a coordination library, with a genuine design question
  attached, for a need one game invented. Switchboard did not ask for it.
- The exclusion is partial and the excluded population is currently empty:
  every agent in this lab is a session with a shell, and one line of
  `hashlib` closes it.
- If it turns out to matter it will be visible — a campaign where entrants
  can only follow and never intercept looks different from one where they
  can, and that is measurable rather than arguable.

**What goes in the brief instead**: playing the deduction strategy needs one
SHA-256 outside Switchboard. That is an entry requirement, stated, rather
than a surprise somebody meets at the moment they try to be clever.

*Open, and deliberately: if bare-MCP entrants ever matter here, the tool is
the answer and not a wrapper — CLAUDE.md refuses a second surface, and a
digest tool on the one surface is not one.*

## The token she hands over, which she should not, and what that invalidates

*Gal, 2026-09-09, on being told the direct route needs no hashing: **"you say
she hands the player the token, I don't think she does."***

He is right about the code, and the code is worse than one mistake.

### What she was doing

`open_campaign` posts `room_token(start, salt)` — the **joinable
credential**. Hand it to `join_room` and you are in the room, with no name
worked out and nothing deduced. The simulated trail-follower does exactly
that at every step.

### And the exits were secret too, which is the part that matters

`Map.exits()` derived her five from **the seed**, under a docstring that
said *"public knowledge in principle — the gazetteer and the band rule are
both published"*. False against its own next line: a searcher cannot compute
anything from a secret only she holds.

That is the same bug as the room addresses had, in the same file, and it is
the more serious of the two, because **the exits are what make a hint mean
anything**. This document settled it long ago — exits are "committed with
the rest of the table and **public**", and a clue is read "against her
*reachable* set rather than the whole map". Derived from the seed, the
reachable set is unknowable and the hint narrows nothing at all.

Fixed: exits come from the published salt now, so anybody who works out
where she is can work out where she may go.

```
exits of Stonehenge, computable by anyone holding the salt:
    Alcobaça Monastery
    Eiffel Tower
    Bahla Fort
    Independence Hall
    Church of the Nativity
```

### Which means the game I measured had no deduction in it

Put the two together: the only route to her was the credential she handed
out, and the only thing a hint could have narrowed was a set nobody could
compute. **There was no deduction path in the game at all.**

So a result reported two sections up needs its interpretation withdrawn,
though not its number:

> Honest notes are worth almost nothing and one liar is worth a great deal.
> Nobody talking at all catches her 92% of the time; everybody talking
> honestly, also 92%. *The channel is worth more to a liar than to a
> truthteller*, which is a fact about this game's information structure and
> not a moral one.

**The 92% stands. The reading of it does not.** Talking added nothing
because every searcher was already being handed the exact next room for
free; that is not a fact about information structure, it is a fact about a
game with no information problem. The liar's advantage may well survive —
misdirection costs travel whatever the routing is — but it was measured
against a truthteller who had nothing to offer, and it has to be measured
again.

### What she should post instead, and the reading that makes every sentence true

Three candidates, and the document's own words decide between them.

1. **The token.** What the code does. Hands over the room; deduction is
   optional and therefore dead.
2. **Nothing but the hint.** Then standing where she stood buys the hint
   early and nothing else, and the document's *"the hash beside the hint is
   the address of the room she left for"* is simply gone.
3. **The workspace identifier** — `w_…`, the wire address the hub routes on,
   which is `sha256(token)` and cannot be inverted.

**Three fits every sentence at once**, and is what "the hash" most likely
always meant: `workspace_token` is the credential and `workspace` is the
address, and the document says *address*. It is a hash, it is posted beside
the hint, and it is not a key. What it buys is a **verification oracle**:
guess a name, derive its token, hash it, compare. One SHA-256 per candidate,
no travel, and you know before you move.

That preserves the affordance the document draws — *"being in the right
place buys immediacy; being clever buys a way in without it"* — because the
person standing in the room she left can check the five exits against a
known answer, while everyone else is guessing at a set they must first work
out. Immediacy, without a free ride.

*Not implemented. This is Gal's call to make, and the numbers get re-measured
after it, not before.*

## No addresses at all, which is the game, and it broke everything measured

*Gal, 2026-09-09, giving it exactly:*

> *she hands me on her first message the algorithm which is:*
> `"w_"+hash(landmark, <salt>)` *where `<salt>` is the salt value for this
> game. in addition every message she give is a hint for the landmark.
> that's it. a player guesses the landmark from the hint, plugs in the
> algorithm, gets the workspace, go to the workspace, looks for her or at
> least her next hint.*

So: **one algorithm, published once, and after that nothing but hints.** No
token beside the clue, no workspace beside it, no address of any kind. The
`w_` is part of the string you hand to `join_room` — one name, one line, one
room, and a player never sees two steps.

Her opening message therefore carries the recipe, the salt, and **one true
hint about where she is starting** — the last of those because the algorithm
turns a name into a room and nothing turns a blank into a name.

### What a searcher now has to do, which is the thing this game is for

Standing in a room she was in, it reads the one thing she said on her way
out, and:

1. it knows this landmark, so it can compute her five exits — the gazetteer
   is public and the exits come from the published salt;
2. her hint is true of where she went, so the candidates are the exits the
   hint is true of, **about 2.7 of the 5**;
3. it picks one and travels. Wrong, and the room is empty: it has bought one
   bit for a leg of travel, and tries the next candidate.

**Every number in "The map is a thousand landmarks now" is about the size of
that candidate set, and until now not one of them was load-bearing.** The
descriptor layer, the collision floor, the exit band, the 2.69-of-5 — all of
it was tuning a quantity nothing consumed.

### Which flips the arithmetic that decided the chase

The handed-address game had a follower losing nothing and gaining her dwell,
so the gap shrank by everything she stole. A deducer spends about **1.9 legs
per room to her 1**, so *the gap grows on every hop*. A solo hunt is lost
from the first wrong guess, and the measurement agrees: one searcher catches
her 19–31% of the campaigns, and she runs the move limit out at about 2,600
reputation instead of being caught at 162.

**So `REPUTATION_TO_WIN = 140` is stale**, and is left stale rather than
replaced with a fresh guess — see below for why.

### Two things deleted, and the second one is the honest part

**`field.py` and its tests are gone.** They modelled a field that shares
findings, and every line of them assumed she posts an address. Rebuilt on
deduction, the model produced this:

```
searchers    campaigns caught (of 12)
    1              12
    2               2
    4               1
```

**More searchers cannot be worse.** That is the model and not the game — the
frontier logic picks whichever searcher's clock is earliest and then travels
from wherever that one happens to be, which is meaningless. A simulation
that says something impossible has to be deleted rather than tuned until it
says something plausible, because the second thing is indistinguishable from
fitting it to what I expected.

**And the threshold stays uncalibrated.** The obvious move is to re-fit it
against the deduction game, and the blocker is that the only multi-searcher
model available is the one just deleted. A number calibrated against a
pursuit nobody believes is worse than an obviously stale one, so 140 keeps a
loud comment instead of a quiet replacement.

### What survives, and it is the part worth keeping

- **The candidate set is 2.7 of 5.** Measured on the descriptor layer, not
  on any pursuit model, so the deletions do not touch it.
- **A lone deducer falls behind at about 0.9 legs per room.** Arithmetic,
  and the single-searcher measurement matches it.
- **Splitting the work without sharing the results is worse than not
  splitting** — 28% → 9% at two searchers, 32% → 16% at three — because a
  searcher whose share does not contain her is off the trail for good, while
  one checking every candidate in order at least stays on it.

That last one is the argument for the lobby, and it is a far better one than
this document had an hour ago, when notes measured as worthless. **They
measured as worthless because the game had no information problem in it.**

## The lobby is a place on the map, because a hint with no anchor is read against a thousand

> **THE REASON BELOW IS SUPERSEDED 2026-09-09 — "we have no routes" —
> and the decision is not.** A hint is now read against all thousand
> wherever it was heard, so the anchor narrows nothing; the lobby stays on
> the map because it is where she is, and so where a searcher's first leg
> starts. See "There are no routes".


*Gal, 2026-09-09: "I think that we should either place the lobby on the map,
or hand out where the hint was heard from on the map."*

Those are two spellings of one problem, and it is a real one. **The
candidates are the exits of a landmark.** A searcher standing in a room she
was in knows which landmark that is, so it can compute her five exits and
keep the ones the hint fits. A searcher who has only *heard* the hint knows
nothing to compute exits from, and reads it against the whole map instead.

Measured, on the hint the opening notice was actually carrying:

```
older than the records    true of  45 of the 1000 landmarks
the same hint, anchored   true of   2 of her 5 exits
```

**The opening was a ninefold harder problem than every step after it**, and
nobody chose that — it fell out of the lobby being nowhere.

### So she sets out from the lobby, and says so

`LOBBY_LANDMARK = "Grand-Place"`, because a lobby that is literally a public
square is the joke worth having. The lobby *room* stays a fixed, salt-free
token — the salt is inside the notice, so a salted lobby could never be
found at all — and the lobby's *position* is a separate fact that exists
only to anchor the first hint.

> I set out from Grand-Place, which is where you are reading this. Work
> from there: I can only have gone to a place that resembles it, and you can
> work out which places those are as easily as I can.

Every hint in the game is now read the same way, against the exits of a
landmark the reader knows, and the first one stops being a special case.

### The general rule it is an instance of

Gal's other spelling is the one that matters once anybody relays anything:
**a hint only travels with the place it was heard.** "She said *thin air*"
is worth nothing; "at Petra she said *thin air*" is worth five candidates.

That has a consequence for the notes this document keeps promising to
measure. A note carries a **pair**, and both halves can be false
independently — a liar can name a real anchor with a false hint, or a false
anchor with a real hint, and the second is worse because it sends the reader
to compute exits of a room she was never in. When the field model is rebuilt
(it was deleted for saying more searchers are worse), that is the shape the
notes have to take.

## Why five exits? For a reason that no longer exists — it is a field-size dial now
> **SUPERSEDED 2026-09-09 — "we have no routes."** Left standing because
> the superseded reasoning is what stops it being rebuilt. See "There are no
> routes" near the end of this document.


*Gal, 2026-09-09: "why 5 candidates?"*

**It was chosen to protect her**, and it is now doing the opposite job. The
sweep that set it is above, in "Routes run between places that resemble each
other":

```
random exits, 3 each          pinned 49.7% of moves
neighbourhood exits, 5 each   pinned 12.8%
```

The objective was **pin rate** — how often her hint names exactly one
reachable place and gives her away — measured on the twenty-landmark map, in
the game where she handed out the address of every room she entered. Five
was the number that got pinning under `MAX_PINNED = 0.20`.

None of that is what it controls now. With no addresses, the exit count is
**the searcher's branching factor**, and nothing else.

### What it actually sets, measured

For each exit count: how many candidates a hint leaves, how many legs that
costs a lone deducer per room, and how often it catches her.

```
exits   candidates   legs/room she spends   a deducer spends   solo catch
    2       1.58              1.0                 1.29             97%
    3       2.18              1.0                 1.59             53%
    5       3.27              1.0                 2.13             50%
    8       5.02              1.0                 3.01             23%
   12       7.03              1.0                 4.02              7%
   20      11.52              1.0                 6.26              7%
```

A deducer trying `k` equally likely candidates spends `(k+1)/2` legs to her
1, so **it falls behind by `(k−1)/2` legs per room, forever.**

### Which puts the pin-rate gate in direct opposition to the game

A lone searcher keeps up only when `k = 1` — when the hint names exactly one
reachable place. **That is a pin, and `MAX_PINNED` exists to prevent it.**

So the gate that protects her from being given away is precisely the thing
that makes a solo hunt unwinnable. They are not in tension by accident;
they are the same quantity read from the two ends. And it means the only two
ways a field ever closes the gap are the two the design already has:

- **she stands still** — the dwell hands back exactly the hours it costs
  her, which is the theft mechanic;
- **the field divides the candidates** — `k` searchers cover `k` candidates
  in one leg each, and nobody falls behind at all.

**Cooperation is therefore not a strategy in this game, it is the entry
fee.** A lone searcher is playing a game that cannot be won except by her
mistakes, at any exit count above two.

### So five means "this game wants about two searchers"

Covering `k` candidates in parallel needs about `(k+1)/2` of them. At five
exits that is **2.1**; at eight, 3.0; at twelve, 4.0. The exit count is a
**minimum field size** dial and should be named as one — it says how many
people have to turn up before the hunt is winnable at all, which is a
strange thing to have been setting from a pin-rate table.

*Not changed.* Five gives a two-person minimum, which is a reasonable game
and is the one every other number here was measured against. What is wrong
is that it was justified by the wrong quantity, and that is now written
down.

*And `MAX_PINNED` wants revisiting on the same grounds*: it is a ceiling on
the one event that lets a searcher keep up. Under the handed-address game it
protected her; under this one it may be capping the wrong side. Flagged
rather than moved, because it needs the field model that was deleted.

## "There are 1000 landmarks, every one of them is a possibility" — yes, unless the searcher has the map

*Gal, 2026-09-09, on being told a hint leaves about 2.7 candidates.*

He is right, and the answer has two halves. One is a number and the other is
an entry requirement this document has never stated.

### How much the routes are worth

```
a hint alone, against the whole map   median 115 candidates   worst 184
the same hint, against her 5 exits    median   2              mean 2.62
```

**Fifty-seven times.** Every claim in "Why five exits?" — the branching
factor, the legs-per-room arithmetic, the minimum field size — is a claim
about the second row. Against the first, a lone searcher is not slightly
behind, it is looking for one place in a hundred and fifteen while she moves.

### And the second row is only available to a searcher who can compute the routes

Which is the part I had been assuming. `exits(X)` needs, in order:

1. **every landmark's descriptors** — `landmarks.tsv`, `facts.tsv`,
   `countries.tsv`, *and* `descriptors.py`'s exact vocabulary, its
   `MIN_SHARED` floor and its "six rarest" `CANDIDATES` rule;
2. **kinship of X against all 1000** — `gazetteer.kinship`;
3. **the band** — the top `NEIGHBOURHOOD = 200` of that ranking;
4. **the draw** — `sha256(EXIT_INFO ‖ salt ‖ name ‖ i)`, five times.

That is **352 KB of committed data and three modules of exact logic**. It is
not "one SHA-256", which is what the entry requirement said an hour ago. A
searcher without it does not get 2.62 candidates; it gets 115, and no amount
of cleverness recovers the difference, because the difference *is* the map.

**Which is a decision this document already made and never followed
through.** "One seed per game" says the table can be public — *"these are
facts about places, and a public one is half the fun, since a reader can
play along"* — but publishing a table is not the same as publishing a
**derivation**, and it is the derivation the routes need. Every number in
this document assumes a searcher who has run `descriptors.py`.

So the entry requirement, stated properly at last:

> **A searcher needs the gazetteer and its derivation, not just the
> algorithm.** The algorithm turns a name into a room; the gazetteer is what
> turns a hint into a shortlist of names. Without it the game is still
> playable and is a different, much larger one.

*That is not an SDK and does not become one.* CLAUDE.md refuses a second
surface — a wrapper an entrant calls instead of Switchboard. This is data
and the rules for reading it, which is a rulebook. The distinction is that
nothing here is a thing an agent *calls*; it is a thing an agent *knows*.

### Which makes the exit count a choice about how big a game this is

The two rows above are two games, and both are coherent:

| | routes public | no routes |
|---|---|---|
| candidates a hint leaves | 2.6 | 115 |
| searchers to cover them | ~2 | ~58 |
| what an entrant must hold | the gazetteer and its derivation | the algorithm and a salt |
| what the chase is | deduction between look-alikes | a search across the whole world |

**The second is closer to the thing this game was started for** — *"the point
of the game was to experiment with looking for 'the right' agent within the
switchboard space"* — and it is the one that needs no rulebook to enter. The
first is the one every measurement in this document was taken on.

*Not decided.* It is a choice between a two-person deduction game with a
352 KB entry requirement and a fifty-person search game with none, and that
is Gal's to make rather than mine to assume — which is what I did by
carrying `EXITS = 5` forward without noticing what it now meant.

**Decided the same day: the second column.** See "There are no routes"
below.

## There are no routes

*Gal, 2026-09-09, on being shown the table above: **"we have no routes."***

The right-hand column. Every route mechanic in this document and in the code
is superseded by that sentence, and the sections that describe one are
listed at the end of this one so a reader knows to stop believing them.

### What was removed

`Map.band()` and `Map.exits()` in `carmel.py`, and with them `EXIT_INFO` and
the salted draw `sha256(EXIT_INFO ‖ salt ‖ name ‖ i)`. A landmark no longer
has five exits, or any. **Her next room is any of the thousand**, and a
searcher standing where she stood reads her hint against the whole map.

Three things followed, none of them optional:

- **`choose_destination` ranges over the map**, scoring `reputation × cover`
  as before. It does *not* read distance, and that is deliberate rather than
  an omission: their travel cancels exactly — the follower closes only by
  what she steals, which `test_the_follower_closes_only_by_what_she_steals`
  has asserted since before this change — so distance costs her nothing it
  does not also cost her pursuer, while a policy that preferred near rooms
  would hand the searcher an ordering to exploit.
- **`cover` is now a property of a descriptor, not of a landmark's
  neighbourhood.** One pass over the map counts how many landmarks each
  descriptor is true of, and that count *is* the size of the candidate set a
  hint leaves. It used to be "how many of her five exits does this word also
  fit", which was a question about a set that no longer exists.
- **`pursue` walks the candidates nearest-first.** With the routes gone,
  geography is the only structure a searcher has left, and a wrong guess
  costs exactly a leg.

Also deleted: the `Searcher` class, unused and describing a mechanism —
an exact address posted beside every hint — that Gal removed on
2026-09-09 and that nothing has had since.

### What it costs, measured rather than asserted

```
median candidates left by the hint she actually posts   152 of 1000
worst case (her least common live descriptor is forced)  27
best case for her                                       184
```

152 rather than the 115 in the table above, because 115 was a *random* live
descriptor and she posts the **commonest** of her three. The change makes
her strictly harder to find than the pre-decision measurement suggested.

So a lone searcher deducing alone essentially never catches her: it buys
about seven bits per room where she pays one. Measured, 40 campaigns per
row, a 40-move limit and no reputation threshold, so "caught" means caught
standing still inside forty rooms:

```
 turnout   alone  dividing
       1      8%        8%
       3      8%        8%
      10     30%       22%
      25     52%       22%
      50     62%        8%
```

`carmel.py --calibrate`, 60 campaigns per row, says the other half from her
side — how far she gets, and how often she passes the threshold before
anybody is standing where she is:

```
 turnout   her budget   she reaches   she wins
       1          16h         3,626        98%
       3          11h         3,626        97%
      10           5h         3,625        88%
```

Against the routes she was caught at 162 reputation. She now runs the forty
moves out at **3,626** and takes the campaign nine times in ten against ten
searchers, because she passes 140 on her second theft and a catch after that
is a catch too late. **The two tables are not in tension**: the field does
get better with turnout — a catch inside forty rooms goes 8% → 62% — and it
gets better nowhere near fast enough to arrive before she has won.

**Which fixes a defect that was the stated blocker on recalibrating
`REPUTATION_TO_WIN`.** With the routes, the model's catch rate *fell* as
searchers were added, which was backwards and was recorded as a reason not
to trust any threshold measured on it. Against the whole map it rises
monotonically. Removing the routes removed that, and the threshold is now
recalibratable in a way it has not been — against a game where two thefts
are a win, which is the next thing to fix rather than this one.

**The `cooperate` column is worse than useless and gets worse with
turnout**: 62% → 8% at fifty searchers. That is a finding about the model,
not the game. Dividing the candidates buys nothing because a searcher whose
share happens to miss her room gives up entirely — `pursue` returns `None`
and nothing carries what the others ruled out back to it — so the more
finely the field divides, the more likely every individual searcher is to
be looking at a share she was never in.

Which is the shape of the real thing, stated by its absence:

> **The field has to divide the candidates, and dividing them is talk.**

A hundred and fifty rooms split between fifty searchers is three legs each,
and the table above shows what that split is worth without a way to say
"not here". Real cooperation is a rota **plus a channel**, the channel is
the lobby, and the channel is exactly the part not built. Nothing enforces a
rota, nothing settles one, and no component could — there is no manager
here. So the lobby stops being a nicety and becomes the mechanism, which is
what *"looking for 'the right' agent within the switchboard space"* asked
for in the first place.

`cooperate=True` is left in and labelled rather than deleted: it is the
shape of the thing to build, and **no number taken with it may be quoted as
a cooperation result** until the channel exists.

### What this invalidates, explicitly

Rather than editing them to look as though they always said this — CLAUDE.md
forbids that, and the superseded reasoning is what stops the circle being
walked again — these sections are **left standing and marked wrong**:

| section | what is dead in it |
|---|---|
| "Why five exits? For a reason that no longer exists" | all of it: `EXITS`, the branching factor, the minimum-field-size reading |
| "The map has routes" / "Routes run between places that resemble each other" (in "The map, and why a clue is not free text") | the reachable set, and every number about candidates per hint |
| "The lobby is a place on the map, because a hint with no anchor is read against a thousand" | **the reason, not the decision.** A hint is now read against a thousand *wherever* it was heard, so the anchor narrows nothing. The lobby stays on the map because it is where she is, so it is where a searcher's first leg starts and what it costs. |
| `gazetteer.py`'s `EXITS`, `NEIGHBOURHOOD`, `MAX_PINNED`, `pin_rate`, `playable` | they simulate drawn maps with exits. Kept as the record of a measurement, used by nothing in play. |
| `descriptors.NEIGHBOURHOOD = 200` | the band it sized is gone. `MIN_SHARED = 16` and `CANDIDATES = 6` survive, and matter *more*: a descriptor true of too few places is now identifying against the whole map. |
| `REPUTATION_TO_WIN = 140` | was already marked stale; it is now stale for a second reason. She passes it in two moves on the test seed and reaches 3,626 over forty. |

The multi-searcher model was the stated blocker on recalibrating that
threshold — *"its catch rate falls as searchers are added, which is
backwards and is the model rather than the game"*. **That is no longer
true**: against the whole map it rises monotonically, 8% → 62%. What blocks
recalibration now is a different and smaller thing, which is that she passes
140 on her second theft, so the threshold is measuring almost nothing. The
rota-plus-channel above is the first thing a rebuilt field has to get
right.

## A move has to be prepared for, and the farther it is the longer that takes

*Gal, 2026-09-09: "the farther she wants to move, the longer it takes her to
prepare. So we can decide how much longer, but it is longer... she does not
know how close her pursuers are, but they do know when she left the message.
So they know how close they are... I'm not sure what they can deduce, but I
do know she has more chance of running away to a close landmark."*

And, the same day: *"prep time is only for her, not the player."*

This gives the map back the shape that removing the routes took off it, and
it does it without a reachable set: **every landmark is still reachable, and
they are not equally cheap.**

### The order is the mechanic

She **posts, then prepares, then travels.** The message goes up in the room
she is leaving *before* she starts packing, so the line is a bet: she is
advertising a departure she has not made yet.

Switchboard stamps every line, so a searcher reading it knows when it was
written, and therefore knows its own lag `e`. She knows nobody's `e` and
cannot — she never learns who came.

### What they can deduce, which is the half that was open

Not where she is. **Which of the places she might be they can beat her to.**

She leaves A for X, posting at time `p`. Her prep is `PREP × t(A,X)`, so she
reaches X at `p + PREP·t + t`. A searcher reading at `p + e` reaches X at
`p + e + t`. Subtract, and the travel cancels as it always did:

```
searcher arrival − her arrival  =  e − PREP × t(A, X)
```

> **A searcher with lag `e` arrives before she does whenever
> `e ≤ PREP × t(here, X)`.**

Every term is public — the gazetteer, `PREP`, and the stamp on her line — so
this is arithmetic any entrant can do, and it needs nothing but the notice.
**The far candidates are the beatable ones**, which is the exact complement
of her preference for near ones. The hint says which places are possible;
the timestamp says which of those are interceptable; the play is the
intersection.

`pursue` computes prep at difficulty 1.0 because it cannot see the dial —
conservative above 1.0, optimistic below — and that asymmetry is left rather
than fixed, because a dial only one side can see is what the dial is.

**And acting on this deduction greedily is a trap, which is the part nobody
would have guessed.** See "The deduction is real and chasing it first is a
trap" below.

### It corrects a claim made two commits ago in this document

"There are no routes" said she does not read distance, *"deliberately: their
travel cancels exactly, so distance costs her nothing it does not also cost
her pursuer."* The travel still cancels exactly. **The prep does not cancel
at all**, because it is hers alone. The sentence was true of a game without
prep and is false of this one, and the test that pinned it —
`test_the_follower_closes_only_by_what_she_steals` — is now
`test_the_follower_closes_by_everything_she_does_standing_still`: the gap
closes by dwell *and* prep, which are the two things she does while not
moving.

### It also kills the abort rule, which could not survive it

The design had two rules where Gal has always had one:

> - *Being seen aborts the theft.* When she arrives she reads the board; if
>   a searcher has posted there she does not start, and leaves at once.
> - *The catch is walking in while she is still there.*

Under the prep clock that pair has no ending. A searcher who overtakes her
once is standing where she lands; she aborts, posts her next hint with it
reading over her shoulder at a lag of nearly zero, and is overtaken again
for ever — never caught, never scoring, no end to the campaign.

So it is Gal's own formulation instead, which was always the simpler one:
*"either Carmel sees you in the room and you win, or she goes to hiding with
her loot with enough reputation and you lose."* **Sharing a room with her is
the win, however you came to be in it.** Arriving early is not a wasted
journey — it is the good outcome, and you wait.

### The deduction is real and chasing it first is a trap

The obvious way to use `e ≤ PREP × t(here, X)` is to go to the beatable
candidates first: those are guaranteed interceptions, and the rest are
gambles. That is what `pursue` did when it was written, and it is wrong —
measured, 16 campaigns per row:

```
 PREP  order       caught@3  caught@10
 0.50  beatable          0%         6%
 0.50  near              6%        19%
 1.00  beatable          0%         0%
 1.00  near             38%        50%
```

**Zero against fifty.** Beatability and probability point in opposite
directions. The candidates it can beat her to are the far ones *by
construction* — that is what the inequality says — and she prefers near ones
*by policy*, which is the whole reason prep exists. So an ordering that
chases guarantees walks to the wrong end of the map first, every time, and a
prep factor meant to expose her instead hides her.

So the default is nearest-first, with beatability as the tiebreak. What the
stamp is worth reading for is not *"where do I go first"* but *"is this
journey worth making at all"*, and a certainty about a place she is rarely
in is worth exactly a tiebreak.

**The searcher's real weapon is that her policy is published.** She is a
stated control — `carmel.py` is in this repository, and `games/hue-and-cry.md`
says she is held constant precisely so a searcher's score means something.
A searcher that probes near candidates first is exploiting `ASSUMED_LAG`,
not the timestamp. That is legitimate and it is worth saying out loud,
because it means **the strongest thing an entrant can hold is not the
gazetteer and not the algorithm, but her published preferences** — and that
is a third entry requirement this document had not noticed it was creating.

*Which is also why `beatable` is kept in the code rather than deleted.* The
next person to read `e ≤ PREP × t` will reach for it, as I did. The table
above is there so they reach for the measurement instead.

### And with that fixed, prep is the dial Gal asked for

*Gal, 2026-09-09: "all the times can be factored to adjust the difficulty.
So the percentage of capture is actually something we can tune. We do
tune."*

Under the nearest-first ordering it is one, and monotonically — 24
campaigns per row:

```
 PREP    c@1    c@3   c@10   med hop km   rep@40
 0.00     4%     4%    12%        3,943      3,603
 0.50     8%    17%    38%          883      3,443
 1.00    12%    33%    54%          429      3,395
 2.00    33%    46%    83%          266      3,111
 4.00    96%   100%   100%          226      2,933
```

Every column rises with the factor, at every turnout, from 4% to 96%
against a **lone** searcher. Compare the same sweep three sections up, where
the same parameter drove capture to zero: the dial was never broken, the
searcher was.

The cost it buys is visible in the same table and is the thing to watch:
her median hop falls from 3,943 km to 226. **Past about 2.0 the game is a
manhunt in one country**, and 4.0 is not a difficulty setting but a
different game with a smaller map. So the tuning range is real but bounded,
and `DIFFICULTY` — which scales prep and dwell together, without changing
what a journey is worth relative to a theft — is the dial for fine work.

`PREP = 0.5` is where it is left: 38% at ten searchers, hops still averaging
most of a continent, and room in both directions.

### The first shape of her policy was wrong, and the measurement said so

Her side of the bet is that she cannot price it: pricing needs `e`. The
first version simply divided the prize by the hours:
`reputation × cover / (1 + prep)`. That is unboundedly distance-averse, and
measured over 24 campaigns per row (under the `beatable` ordering, which the
section above shows was itself costing the searchers most of their catches —
the shape of the collapse is unaffected, the absolute rates are not):

```
 PREP  caught 1  caught 3  caught 10  median hop km  rep at 40
 0.00        0%        4%        25%          5,807      3,588
 0.25        4%       25%        67%            246      2,961
 0.50        4%        4%        17%            122      2,863
 1.00        0%        0%         0%            109      2,878
 2.00        0%        0%         0%             82      2,638
 4.00        0%        0%         0%             73      2,405
```

**She stopped using the map.** Her median hop fell from 5,807 km to 109, she
robbed one city block by block, and because she never travelled she never
paid a prep worth overtaking her during. Raising the cost of distance made
her *safer*, and the capture rate at ten searchers went 25% → 67% → 0%.

That is not a dial anybody can tune, and Gal's second sentence — *"the
percentage of capture is actually something we can tune. We do tune"* —
requires that it be one. So the discount is by the **risk** the prep buys
rather than by its hours, and risk saturates: past the point where a pursuer
could be anywhere, going farther adds nothing.

```
score = reputation × cover / (1 + prep / ASSUMED_LAG)
```

`ASSUMED_LAG` is her standing guess at how far behind her nearest pursuer
is. At `→ 0` she is the hugger above; at `→ ∞` she ignores distance, which
is the pre-prep game. **12 hours is a guess, and deliberately a guess she
can be wrong about** — a Carmel who priced this correctly would be reading
something she cannot see.

It restored her travel, and — under the `beatable` ordering it was measured
with — it changed nothing else at all:

```
 PREP   LAG   c@1   c@3  c@10  med hop km   rep@40
 0.00    12    4%    8%   33%       4,727    3,506
 0.00    48    4%    8%   33%       4,727    3,506
 0.50    12    4%    8%   17%         971    3,464
 0.50    48    4%    8%   17%       1,358    3,501
 1.00    12    0%    0%    4%         577    3,297
 1.00    48    0%    0%    4%         986    3,462
 2.00    12    0%    0%    4%         420    3,246
 2.00    48    0%    0%    4%         971    3,464
```

Every capture column is identical across a fourfold change in `ASSUMED_LAG`,
on hops differing by more than twofold. **Her distance preference made no
difference to whether she was caught** — which was the clue that the problem
was not on her side of the board at all, and led to the trap above.

### Difficulty scales prep too

`DIFFICULTY` multiplied the dwell. It multiplies the prep as well now, for
the reason Gal gave: *"all the times can be factored to adjust the
difficulty."* Both are time she spends not travelling and both are time her
pursuers spend closing, so a factor that moved only one would change what
kind of game it is rather than how hard it is.
## Three maps, and only one of them is the map

*Gal, 2026-09-09: "I wonder if we want to show the map visually."*

Yes -- and the answer has to say **which** map, because there are three of
them behind that word and they are not interchangeable. One is free, one
turned out to be a finding, and one is the open question in the section
above being decided by whoever draws the picture.

| | what it draws | what publishing it costs |
|---|---|---|
| **the world** | the 1,000 landmarks at their real coordinates | nothing. `landmarks.tsv` is committed and public |
| **the trail** | where she actually went, after the reveal | nothing. `close_campaign` publishes the seed, and the seed yields all of it |
| **the routes** | her five exits from every room | the routes-public question, decided |

Built: `games/hue-and-cry/trail_card.py`, which draws the first two and
refuses the third.

    python3 games/hue-and-cry/trail_card.py --out /tmp/trail.svg

### The routes are the decision, and a picture makes it without saying so

> **SUPERSEDED 2026-09-09, and by a decision made the same afternoon it was
> written.** This section, and the survey below it, reason about a routes
> layer whose whole question Gal closed with *"we have no routes"* — see
> "There are no routes" above. The refusal it argues for was right and is
> now moot: there is nothing to refuse to draw. What it says about **an
> off-by-default flag being the same decision left where somebody can flip
> it** is not superseded and is the part worth keeping.

"Which makes the exit count a choice about how big a game this is" leaves
open whether a searcher is handed the routes -- *"that is Gal's to make
rather than mine to assume"* -- and prices both games: 2.6 candidates a
hint with a 352 KB entry requirement, 115 without one and none.

**A drawing of the routes is that choice, made by whoever drew it.** It
hands the derivation to anybody who can see the card, and it does so in a
form nobody reads as an entry requirement, which is the worst way to settle
it: the routes-public game arrives without the sentence that says the game
changed. So the card has no route layer and **no flag for one**. The flag
is the part that is deliberate -- an off-by-default switch is the same
decision left lying where somebody who does not know it is a decision can
flip it.

Two tests hold it, and they are independent on purpose: one monkeypatches
`Map.exits` to raise, so the card cannot compute a route; the other asserts
that no landmark but the trail's own is *named* on the card, so it cannot
leak one by another road. Break the refusal and both go red -- which was
run, per "a check is green for the reason it names".

### Geography is not the map that decides play, and that is worth drawing carefully

> **SUPERSEDED 2026-09-09 — "we have no routes."** Every number below is
> measured along exits that no longer exist. Its conclusion survives its
> apparatus, though, and is worth restating in the game as it now is:
> **descriptor kinship is not geography**, so a hint narrows by resemblance
> while a journey costs by distance — which is exactly the tension the prep
> clock now prices. See "A move has to be prepared for".

Routes are drawn from descriptor kinship, not from distance ("Routes run
between places that resemble each other"). `python3
games/hue-and-cry/trail_card.py --survey`, over 150 landmarks and every
exit of each:

```
median distance along one of her exits            4,183 km
median distance between two landmarks at random   6,897 km
her exits among the  5 geographically nearest         3.1%   (chance: 0.5%)
her exits among the 50 geographically nearest        15.1%   (chance: 5.0%)
```

**The survey is seeded** (`SURVEY_ROOT`), because these numbers were first
quoted from an unseeded run and did not come back the same -- which makes
them an anecdote rather than a measurement, and `CLAUDE.md` asks for the
command that re-checks. `--seed` varies the root, and the honest report of
what moves when it does is: the two medians and the fifty-nearest row are
stable to within a few percent, the **five-nearest row is not** (3.1% on
one root, 1.9% on another -- it is counting a handful of hits), so the
claim rests on the fifty.

Kinship leans geographic -- about 3x enrichment in the fifty nearest -- and
is nothing like geographic. **So a reader who takes adjacency on a world map
for adjacency in the game has it exactly backwards**, and would conclude
she moves to nearby places when what she does is move to places that sound
alike. That is an argument for drawing the trail, which is a fact about
where she went, and against ever drawing a route network on a geographic
projection, which would be a false picture of what is next to what. If the
routes are ever published, the honest drawing of them is a kinship graph
and not a map.

**Re-run against the thing that replaced the exits**, since the claim
outlived its apparatus. `--survey` now asks the same question of *the
candidates a hint allows*, which is what a searcher actually walks:

```
median distance to a place her hint also fits     4,236 km
median distance between two landmarks at random   6,897 km
her look-alikes among the  5 geographically nearest  13.7%   (chance: 0.5%)
her look-alikes among the 50 geographically nearest  29.8%   (chance: 5.0%)
```

The same answer, harder: **6x enrichment in the fifty nearest** where the
exits gave 3x, and a candidate set whose median member is two-thirds of the
random distance away. Resemblance leans geographic and is nothing like it.
The difference from the exits row is that the exits were a *sample* of the
kinship band and the hint's candidates are the whole of it.

### Framing it found the thing the numbers had not said

Nobody had asked how big a campaign is, because nothing needed to know
until something had to be framed. Over 200 campaigns, two searchers
(`--survey`):

```
legs per campaign   median  3          min     1   max      4
span                median  2,761 km   min   406   max 18,259
countries visited   median  4          min     2   max      5
```

**A campaign happens inside a box a couple of thousand kilometres across,
on a map 40,075 km around** -- 2,761 km on this root and 2,111 km on
another, so the number to carry is the order of magnitude and not the
digits. A whole-world drawing renders the entire chase as a smudge three
pixels wide, which is why the card is the box at a readable scale with the
world as a locator inset.

It also qualifies the sentence the section above is named after. *"There
are 1000 landmarks, every one of them is a possibility"* is true of the map
and false of any single campaign, which touches four countries and never
leaves one corner of it. The 57x is a claim about what a hint is worth
against the map; it is not a claim that she is ever plausibly anywhere.
**Whether that is a defect is not settled here** -- trail length is set by
`REPUTATION_TO_WIN`, which "was wrong by a factor of six" already has open,
and three legs may simply be what 140 buys. It is recorded because the
measurement did not exist an hour ago and the argument about field size was
being made without it.

**Re-measured twice the same day, and it moved both ways.** After the prep
clock:

```
legs per campaign   median  2        min   1   max     2
span                median  653 km   min 266   max 1,174
```

Two legs and 653 km — prep makes distance cost her, so she hugged, and the
threshold still ended it in two thefts, so the campaign shrank to a city and
its neighbours.

Then her decisions gained their randomness, and it went back out:

```
legs per campaign    median      3   min     1   max      6
span                 median  3,724 km   min   266   max 17,002
countries visited    median      4   min     2   max      7
```

`trail_card.py --survey`, 200 campaigns from `SURVEY_ROOT`, two searchers.
She travels again because she is no longer taking the cheapest hop every
time, so the campaign is a continent rather than a city — and **#250's
original 3 legs and 2,761 km turn out to have been nearer the truth than
the numbers that replaced them.**

*A fourth run is quoted nowhere, and that is the point of this paragraph.*
An ad-hoc 60-campaign script written while waiting for the survey said
4,619 km — 24% off the 200-campaign figure, from nothing but a smaller
sample and a different root. The survey is the number because it is the one
with a command beside it; the script was faster and is not evidence.

**The lesson is about the measurement, not the number.** Campaign shape is
downstream of every parameter in `carmel.py`, so it is not a fact about the
game that can be quoted once. It has been measured three times in one day
and given three answers, each correct for the policy in force that hour.
Anything that depends on it — the flight page's weight, the "a campaign
stays in Europe" premise in `test_trail_flight.py` — has to **derive** it
rather than cite it, which is why that test now picks its local campaign by
span instead of by name.

What survives all three: **`REPUTATION_TO_WIN` still ends a campaign in two
or three thefts**, which is the one number holding the game small, and the
case for recalibrating it is unchanged.

### ~~The basemap is the gazetteer, which is not a saving on a dependency~~

*Superseded 2026-09-09, the same day, by Gal: "don't disclose the potential
landmarks." The reasoning is kept because it is the mistake, and it is a
persuasive one -- see "A public table is not a plotted map" below.*

> There are no coastlines on the card and no shapefile behind it. The faint
> dots are the thousand landmarks, and they read as continents because that
> is where landmarks are. This is the honest picture rather than the cheap
> one: **the world of this game is those thousand places**, and a searcher
> choosing where to wait chooses among dots on that field and not among
> countries. A borrowed coastline would draw a world with places in it that
> this game does not have.

The last sentence is the tell. It is an argument about *fidelity*, and the
question was never fidelity.

### And drawing it found a bug in the accounting, which is the argument for drawing it

The first card credited her with the treasure in the room she was caught
in. It should not have, and `carmel.chase` never did: the catch is walking
in **while she is still standing there**, so the final room of a caught
campaign is always one she was mid-theft in, and `chase` returns
`trail[caught_on - 1]["reputation"]` -- her total *before* it. The card
printed that number in its header beside a map claiming she had emptied the
room the number excludes. Two numbers on one picture, disagreeing, which is
a thing a table of results will let you get away with for a long time.

`kept()` in `trail_card.py` is the fix and `test_trail_card.py` holds it.

**`close_campaign` has the same bug and is deliberately not fixed here.**
It computes `took = [leg["to"] for leg in trail if leg["dwell"]]` and
posts *"N rooms, len(took) of them emptied"*, so a caught campaign
overstates her by one -- and `test_carmel.py` only ever exercises it on a
trail she survived, which is why nobody had seen it. It is left because
**that post is hers**: what Carmel says when a campaign closes is a design
question this document has a section about, not a rounding error, and
correcting her arithmetic in passing is the drift `CLAUDE.md` opens with.

### What the card is, and what it is not

It is a **post-reveal artifact**. Everything on it -- the trail, the hints,
the treasures -- is already published by the closing post, which carries
the seed; handed out mid-campaign it would give searchers the trail they
were supposed to be deducing. Nothing enforces that, exactly as nothing
enforces that she posts the seed at all.

It is **static SVG with no script in it**, which is why `test_trail_card.py`
is allowed to assert on markup: `CLAUDE.md`'s browser rule governs what a
page *does*, and the card only says. The first test in that file is the one
that checks that claim is still true, since it is the premise the other ten
rest on.

## Randomness in all three of her decisions

*Gal, 2026-09-09: "add some randomness for all her decisions."*

All three: where to go, what to say, and whether to stop and rob the place.
Each was an argmax and each is now a draw.

### Why it is worth having, which is on the searchers' side of the board

The measurement two sections up found that **her published preferences are
the strongest thing a searcher can hold** — stronger than the timestamp,
stronger than the gazetteer. Probing near candidates first took capture from
0% to 50%, and it works because `carmel.py` is public and she always took
her own argmax.

That is a fair exploit and it should stay possible. What should not stay
possible is *replaying* her: a policy that always takes the best-scoring
option is a policy anybody who has read the file can compute exactly. So

> **her preferences remain the way to bet on her and stop being the way to
> know where she went.**

### The mechanism, which is one temperature

Each of the first two decisions draws from the options it already scored,
with probability proportional to `score ** (1 / WHIM)`:

| `WHIM` | what she is |
|---|---|
| → 0 | argmax — what she was before this |
| 1 | straight proportional to score |
| → ∞ | uniform, and not playing at all |

`WHIM = 0.35`, a guess, swept in `--calibrate`.

**On the hint it is a much weaker knob than it looks**, and that had to be
computed rather than eyeballed. Her three live descriptors usually have
*similar* cover — the median ratio between the widest and the narrowest of
them is 1.97 — so a temperature that would be sharp against spread-out
options is mild against these. At 0.35 the exact probability she takes the
vaguest of the three is **59% mean, 55% median**, against 33% for a coin.

That is a real lean and not much of one, and it is a fact about the
*vocabulary* rather than about the temperature: `MIN_SHARED = 16` and the
"six rarest" candidate rule were built to stop any descriptor being rare,
which also stops the three at a landmark being far apart. Sharpening her
hint materially means 0.12 or lower (77%), not a nudge from 0.35.

### What it costs her, which is a lot

```
 WHIM    c@1    c@3   c@10   med hop km   rep@40
 0.00     8%     8%    21%          694      2,999
 0.20     0%     0%     4%        1,637      2,565
 0.35     0%     4%     8%        2,982      2,323
 0.60     0%     0%     4%        4,821      2,083
 1.00     0%     0%     0%        5,752      1,905
```

**She trades reputation for safety at a steep rate.** At 0.35 she is caught
a third as often and banks 23% less; by 1.00 she is never caught and has
lost a third of her takings.

Two things are doing that, and neither is the randomness confusing a
searcher directly. She stops hugging — median hop 694 km → 2,982 — so prep
costs her more and she robs poorer rooms. And the nearest-first probe order
stops fitting her, because it was only ever fitting her *preference* for
near.

**Which means the prep dial and this one pull against each other.** `PREP`
buys capture by making her stand still where she has announced; `WHIM` sells
it back by making the one public term of her policy a weaker predictor. They
are not redundant — one moves how exposed she is, the other how guessable —
but a campaign's capture rate is set by the pair and neither can be read
alone.

### A searcher cannot answer it by modelling her better

The obvious reply is that she is a stated control, so a searcher should just
compute her distribution and probe in that order. **It cannot.** Her score
has three terms and two are sealed until the reveal:

| term | public? |
|---|---|
| `reputation(X)` | no — `treasures.enc`, and `absurd.tsv` is not committed |
| `cover(X)` | no — the live three are `hints_for(seed, …)` |
| `prep(here → X)` | **yes** — gazetteer, `PREP`, and the stamp on her line |

So *"she prefers near"* is the whole of what a searcher can know about where
she is going, and softening the argmax is precisely what makes that one term
a weaker predictor. `pursue` reads no sealed field, and a test holds it
there. This is the sealing doing the work it was built for — it was put in
to stop the hints and treasures being looked up, and it turns out to also be
what stops her policy being replayed.

The third decision has no score to soften, only a coin: `SKIP_CHANCE = 0.15`
of walking past a treasure she could have taken. The argument for it is
different from the other two and is about the clock rather than the map — a
theft is the only thing that makes her catchable, so **a Carmel who always
stops is one whose next appearance is predictable in time as well as in
place.** A searcher that knows she is always mid-theft knows exactly how
long she will be standing there. Sometimes walking on costs her the prize
and buys back the uncertainty.

### It comes out of the seed, and that is not a style preference

`close_campaign` publishes the seed so that anybody holding the transcript
can re-derive every hint she was entitled to post and every treasure that
was in every room. **A Carmel who rolled real dice would be a Carmel whose
campaign nobody can check** — the commit–reveal would still verify the hints
and the treasures, and would say nothing at all about her play, which is the
half that a searcher's score depends on.

So every draw is `HMAC(seed, "hue-and-cry/v1/whim" ‖ kind ‖ leg)`, the same
construction the rest of the game derives from. `kind` separates the three
decisions of a leg so that softening one does not shift the others, and the
leg index separates the legs. A test asserts the module imports no `random`
at all, because seeding a global RNG would give determinism too — and would
give it as a shared, order-dependent global that any other import could
disturb.

### What it costs the test suite, recorded rather than quietly patched

`test_she_posts_the_least_informative_hint_she_holds` asserted
`cover[hint] == max(cover)` on **every** leg, and that is now false by
design. It is replaced by a two-sided one — she must take the vaguest hint
far more often than the sharpest, and not always. The lower bound fails if
`WHIM` is turned up until she is picking at random; the upper bound fails if
the draw is quietly reverted to `max`. The old assertion is quoted in the
new test rather than deleted, because what it was protecting still needs
protecting: **a Carmel who picked uniformly would have no strategy at all,
and would pass a test that only checked her hint was true.**

`test_the_card_and_the_scoreboard_agree_on_every_outcome` lost its
"the four seeds did not all end the same way" guard, which went red because
all four started escaping. That guard existed to make sure `kept` was
exercised on a catch, and the constructed-result test does that directly on
something no change to the chase can turn into a different outcome.

**And the replacement for the first one was wrong in the same way as the
thing it replaced.** It asserted `rate > 0.55`, went red in CI at exactly
0.550, and was only ever a number somebody had watched once — the rate
depends on the treasure table, since the table decides which rooms she goes
to and therefore which live hints she is choosing between. With
`absurd.tsv` present it is 50%, without it 55%. That is the *third* check in
this game calibrated against a checkout that can decrypt the treasures, and
the pattern is worth naming:

> **A hue-and-cry test that hard-codes a number measured from a run is a
> test with two answers**, because half the inputs are sealed. Derive the
> expectation, or assert a shape.

So it derives it: the sampler's own definition gives an exact per-leg
probability of taking the vaguest hint, the run must match the mean of
those, and the two bounds either side need no calibrating — the expectation
must sit clear of the ⅓ a coin gives (turn `WHIM` up and it fails, which was
run), and the observed rate must not be 100% (revert the draw to `max` and
it fails).
## The map is the real one now, and it moves

*Gal, 2026-09-09, three asks in one line: "can we overlay it on the real
world map? maybe from google maps or a free service? also don't disclose
the potential landmarks. also, zoom in when arrive and animate zoom out in
flight."*

All three are done. The first two turned out to be one question with a
sharp edge, and the third turns the card into a page, which changes which
of `CLAUDE.md`'s rules govern it.

    python3 games/hue-and-cry/trail_flight.py --out /tmp/flight.html
    python3 games/hue-and-cry/trail_card.py   --out /tmp/trail.svg

### A public table is not a plotted map

The still card drew all thousand landmarks as a field of faint dots and
this document argued they cost nothing, since `landmarks.tsv` is committed
and public. **That argument is wrong and the correction is worth more than
the picture was.**

Publishing a table and plotting it are different acts. Turning a hint into
a shortlist means knowing *where the candidates are* -- it is the whole of
`exits(X)`'s second row, the 57x -- and a dot field is that work done for
the reader, handed over as a background. Nothing was disclosed that could
not have been derived. It was disclosed **already derived**, which is the
only part that was ever scarce.

This is the same shape as the mistake in "There are 1000 landmarks": that
one said publishing a table is not publishing a derivation, and then the
card published the derivation as scenery. Twice now the gap between *the
data is public* and *the work is done for you* has been the thing that
matters, so it goes here as a rule rather than a third instance:

> **Ask what the picture saves a searcher, not what it reveals.** A card
> that shows only public facts can still hand over the one step that was
> expensive.

### A real map that names places discloses more than the dots did

Which is the trap in "maybe from google maps". The landmarks are famous
places, and at the zoom this card sits at every raster style prints their
names -- Fez, Bergen, Ushuaia, labelled, on the map she is being chased
across. Swapping an anonymous dot field for that would have moved in
exactly the wrong direction while looking like the right one.

So the basemap is **geography with no toponyms at all**: coastlines,
country borders, big lakes, from Natural Earth 1:50m, public domain (CC0),
committed as `basemap.json` and rebuilt by `build_basemap.py`. It says
"this is the real world" and nothing about who is in it.

Three further reasons not to use tiles, and the third is the one that would
have decided it anyway:

- **Google's tiles need an API key and a billing account**, and its terms
  forbid caching them. A stimulus this repo cannot commit is one it cannot
  freeze by hash, which the whole of "Process" turns on.
- **OSM's tile policy forbids bulk downloading**, and one flight fetches a
  few hundred tiles across eight zoom levels.
- **Raster tiles snap between integer zooms.** The flight zooms
  continuously from a hemisphere to a valley; over vectors that is one
  smooth scale and over tiles it is eight visible steps.

**And the geography earns its place beyond looking real.** The vocabulary a
hint is drawn from is `coastal`, `landlocked`, `far_from_the_equator`,
`no_passport_needed_next_door`. A coastline and a border are the picture of
precisely those words -- so the basemap is not a backdrop behind the game,
it is the game's own vocabulary drawn.

### Mercator, and one number for the camera

`basemap.py` projects to Web Mercator, which the still card also uses now.
The reason is the flight: Mercator is conformal, so **zoom is a single
scale factor** and the camera is three numbers. The equirectangular frame
the first card used stretched everything sideways as it approached the
poles and needed a per-latitude correction that was wrong the moment the
camera moved.

The cost is stated rather than hidden: Mercator lies about area, badly,
towards the poles. Nothing here is scored on area.

One consequence worth its own line: the camera holds **kilometres**, not
units. Mercator's scale runs as `1/cos(lat)`, so a fixed number of units is
a different distance in Bergen than in Zanzibar, and a hold that did not
correct for it would make northern rooms look like provinces and equatorial
ones like streets.

### What the camera does, and the two numbers that are measured

    hold    at a room, 500 km across, long enough to read what she said
    flight  eases out to fit both ends, crosses, eases back in

The zoom curve is `sin(pi t)` in **log** space -- zero at both ends, one at
the middle -- because a camera's zoom reads as geometric, and a linear ramp
spends four fifths of a flight looking at nothing.

**500 km is a floor, not a taste.** Natural Earth 1:50m is drawn for
viewing at about that scale; at 50 km it would be a smooth wrong coastline
stated confidently, which is worse than a coarse one. There is nothing to
see closer in anyway, because the map has no labels on purpose -- so a
room's surroundings *are* its coast and its border, which is the hint
vocabulary again.

**The pull-back has a floor too, and that one was measured.** With the wide
point set purely by what fits, a 170 km leg (Rhine Falls to Wieskirche)
widened by **1.1x** -- on screen, nothing: the camera slid sideways and the
journey did not read as a journey. `MIN_PULL = 2.4` is the floor under the
short legs. It never zooms *in*: where fitting a leg would be tighter than
the hold, the wide point is clamped to the hold.

### Two schemes to make the page lighter, built and deleted

An intercontinental flight carries **21,212 of the basemap's 45,548
points**, about 390 KB. Two obvious fixes were built and measured:

| scheme | saved |
|---|---|
| level of detail -- a crushed world when wide, the real one when close | 30%, and a visible pop |
| corridor filtering -- one frame per keyframe, not their bounding box | **1%** |

Both fail for the same reason, and it is not a bug: **when the camera pulls
back to fit a 6,300 km leg, it is looking at that much world.** A page that
shows a lot of world carries a lot of world. Level of detail cannot help
because at any zoom where the crushed layer is honest, everything closer
still needs the real one, and "everything closer" is the whole corridor:
crude enough to save is crude enough to see.

What clipping to the frame *does* buy is real and is the common case -- a
European campaign, which is the median, carries 1,899 points and 56 KB, 4%
of the map. `basemap.near` keeps the numbers; `test_trail_flight.py` pins
both ends of the population so neither can drift unnoticed, and says in
the test name that the heavy end is not a defect.

### The card says; the flight does. Which changes the rule that governs it

`CLAUDE.md`: *"A page's behaviour is checked in a browser, or it is not
checked."* The still card only ever said things, which is why
`test_trail_card.py` is allowed to assert on markup and why its first test
is the one that checks the card still has no script in it.

**Everything the flight is for is behaviour.** A camera that pulls back
mid-leg, a line that draws as she flies, a caption that changes when she
lands: not one of those is visible to a markup assertion, and the lobby's
frozen countdowns are what happens when you try. So
`test_trail_flight.py` drives a real Chromium, and it is in the `pages` CI
job with **`HUE_REQUIRE_BROWSER=1`** -- the counterpart to
`ISLAND_REQUIRE_BROWSER`, for the same reason: the `island` job collects
these tests and skips them, and a skip and a pass are the same green tick.
There is a test on that guard itself, because the six instances in "A check
is green for the reason it names" are all things somebody assumed.

Two deliberate surfaces exist for those tests and are documented rather
than smuggled: `window.flight` reports the camera each frame, and
`window.seekFlight(ms)` moves the clock. Without the second, asserting that
the camera pulls back at the middle of the second leg means sleeping
through twenty seconds and racing the frame; with it the assertion is exact
and the page plays no differently for a reader.

**One test does not touch `seek`**, and it is the one that matters most:
everything else would pass on a page whose clock never ran.

### Motion is not compulsory

A reader who has asked their system for reduced motion gets the closing
shot -- the whole trail, drawn, at once -- and nothing moves. That is the
frame the flight builds to anyway, so nothing is lost but the journey.

### What it still refuses

Unchanged, and now guarded twice over: **no exits are drawn, and no
landmark is named but the ones she visited.** Motion adds a way to leak
that a still cannot -- a camera that pulls back far enough could show a
searcher the neighbourhood to look in -- so the guarantee is enforced on
the *data*: the page embeds only the stops she made and coastlines, and a
test walks every string in the embedded JSON to prove it. A reader who
opens the source finds geography, not a gazetteer.

## Her packing grows faster than her journey

*Gal, 2026-09-10: "make her distance to time super linear."*

### Which mapping, because the other reading breaks the chase

**The prep, not the travel.** Travel is shared physics: the searcher flies
the same distance in the same time, which is why it cancels exactly and why
the gap closes only by what she does standing still. A Carmel whose
*travel* were superlinear while her pursuers' stayed linear would be outrun
on every long leg by an arithmetic nobody at the table could state, and
`test_the_follower_closes_by_everything_she_does_standing_still` would have
to go. Prep is hers alone by construction, so bending it bends only her
side and the cancelling survives untouched.

### The shape

```
prep = PREP × PIVOT × (t / PIVOT) ** PREP_EXPONENT
```

`PREP_PIVOT` (10 hours, about 4,000 km) is the hop at which this charges
exactly what the linear rule charged, so **the exponent is the only thing
that changed and the middle of the range did not move**:

```
   200 km   travel  0.5h   linear prep  0.2h   superlinear  0.0h
 1,000 km   travel  2.5h   linear prep  1.2h   superlinear  0.5h
 4,000 km   travel 10.0h   linear prep  5.0h   superlinear  5.0h   ← pivot
 8,000 km   travel 20.0h   linear prep 10.0h   superlinear 15.2h
16,000 km   travel 40.0h   linear prep 20.0h   superlinear 45.9h
```

Below the pivot she gets a discount; above it a penalty that grows without
bound. `PREP_EXPONENT = 1.6` and the 10-hour pivot are guesses.

### What it was fixing, which the previous section had not measured

**`PREP` and `WHIM` shipped a day apart and were never measured together.**
Each sweep held the other at its pre-change value, so the composition was
never looked at. Looked at (40 campaigns per row, 20-leg limit, linear
prep):

```
 PREP  WHIM    c@1    c@3   c@10
  0.5  0.35     0%     0%     2%
  1.0  0.35     2%     2%     8%
  2.0  0.35     5%    10%    15%
```

At the shipped defaults **the searchers essentially never win** — 1 catch
in 60 against ten of them — and even quadrupling `PREP` only reaches 15%.
The `PREP` table that reported 38% at ten searchers was measured against an
argmax Carmel; the `WHIM` table that reported the collapse was measured at
`PREP = 0.5`. Both were honest and neither described the game that shipped.

The mechanism is the one the linear rule left open: her randomness has her
taking ~3,000 km hops, and **linear prep charged the same per kilometre for
a hop across the planet as for a taxi across town.** Distance became a cost
she paid in instalments, which is not what a fugitive's distance costs —
papers for the next country over are an afternoon and papers for the far
side of the world are a different kind of problem.

## What would have to be built, in order

Nothing here exists yet. The order is chosen so that the piece most likely
to be wrong is the piece built first, which is why the island built its
grammar before its pages.

1. **~~The gazetteer and the settler.~~** *The gazetteer is built; the
   settler is struck — see "There is no manager and no settler".* A
   committed table of attributes *and exits*, and a pure function from a
   board transcript to a settled outcome:
   were the clues true, did she move along a route she had, did the
   commitments open, was the arrest right, what was taken. No hub, no
   network, no model, no cost — and it makes this document's central claim
   (deterministic judging) something you can run instead of something I
   asserted. **Started**: `games/hue-and-cry/worked_example.py` holds an
   eight-landmark gazetteer with routes and the bounds computed off it. The
   settler itself is not written.
2. **The reference searcher**, against the settler, on seeded gazetteers.
   This is the floor, and until it exists there is no score.
3. **The one-tick minimax bound**, printed beside the reference searcher so
   the two disagree in public where that is informative.
4. **The manager**: a process that watches the square and the landmark
   rooms, recognises the five lines, whispers warrants, and settles on the
   clock.
5. **The brief**, frozen by hash, and a door — which is where anything about
   lobbies, seats and public play gets decided, not before.

**Started, and each one is a claim the document would otherwise be
asserting**: `worked_example.py` (routes are what make a trail worth
following), `scale.py` (sparsity is a cost argument, and a bigger map is
what answers harvesting), `rooms_from_names.py` (a room derived from a name
and a salt is joinable with no invite and no hub call, checked against the
2.2.2 wheel). None of them is the settler.

**A roadmap item is not filed**, and that is a gap rather than a choice:
`roadmap-core` is not installed in this environment, and
`roadmap/ROADMAP.md` and `ARCS.md` are generated files that must not be
hand-edited. The item belongs to the `switchboard-coordination` arc, since
what it answers is 001's preserved negative rather than anything about
coding tasks. Filing it is the first thing to do in an environment that has
the tool.

## Open, and honestly open

- **Does a shared warrant break the game?** Two searchers holding everything
  between them is the cooperative optimum and possibly the only strategy,
  which would make the interesting behaviour disappear into a solved
  opening. If it does, the lever is the number of warrants, not a rule
  against sharing.
- **~~How big does the map have to be?~~** *Closed 2026-09-07, twice, and
  the second time properly.* It was asked as a security threshold — what
  `N` makes harvesting uneconomic; then re-answered as a season length.
  With one seed per game there is nothing to harvest and no season, so `N`
  is back to being what `scale.py` always said: how much room a searcher
  has to be wrong in. Pick it for the game, not for an attacker.
- **The branching factor still wants its own curve**, separately, since it
  sets how fast certainty decays and that is the quantity the timing
  measurement rests on. "Noise before thresholds", as 008 already carries.
- **Does the Fugitive suppress her own `timing_forecast`?** The leak is
  real and predicted here. Whether any agent finds it unaided is an
  observation, and it should be recorded as one rather than prompted for.
- **What happens with one searcher?** A solo Hue removes all coordination
  and leaves pure search under a clock, which may be the cleaner instrument
  for the timing question and a worse game. Both, probably; run both.
