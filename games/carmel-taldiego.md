# Carmel Taldiego

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

*Renamed 2026-09-10, by Gal: "rename the name everywhere to Carmel
Taldiego." The game was called **hue and cry** until then and the reasoning
below is kept rather than edited, because it is the argument the new name
has to answer, not a mistake.*

**The game is named after her now.** She arrived as "the Fugitive", was
given a name on 2026-09-08, and has been the only thing on every card and
every flight since — a picture of this game is a picture of Carmel
Taldiego, and it was odd that the file it came out of was called something
else.

**What that costs, stated rather than skipped.** The section below chose
"hue and cry" partly to sit further from an active trademark, and a title
that is one consonant from *Carmen Sandiego* sits closer to it than a
common-law phrase does. The mechanic was never the exposure; the name
always was. That is Gal's call to make and he has made it, and it is
written here so the next person does not re-derive the trade-off from
scratch — but it is a trade-off, and this paragraph is the record that it
was seen.

**The searchers are still the Hue**, and the phrase still means what it
means: `the Hue` is not a leftover, it is the name of the people chasing
her.

**Two identifiers keep the old name, and they are identifiers rather than
names.** The roadmap item `hue-and-cry-purge-the-leaked-tables` is one: it
records an incident that happened under that name, other generated files
key off it, and an id that moves is an id that stops resolving. The other
is the wire.

**And the wire keeps the old name, on purpose.** `hue-and-cry/v1/landmark`,
`hue-and-cry/v1/matrix`, `hue-and-cry/v1/salt` and the rest are
domain-separation strings bound into HKDF and the room hash. Renaming them
changes every room address, every hint draw and every commitment, and would
make a searcher built against yesterday's published `RECIPE` compute rooms
nobody is standing in. This repo has already learned that exact lesson once
— `CLAUDE.md`, on Switchboard's `ask` to `whisper` rename: *"those strings
are bound into the cryptography, so renaming them makes every release on
one side of the rename refuse every envelope from the other, for a name
only humans ever read."* So: **the humans get the new name and the
cryptography keeps the old one**, and `RECIPE` still says what it has
always said.



The idea arrived as "let's build Carmen Sandiego" and the shape is hers: a
thief who is always one landmark ahead, a trail of attribute clues, a
warrant you have to ask for. **The name is not.** *Carmen Sandiego* is an
active trademark, this repo is public, and a game published under it is a
liability with no upside — the mechanic is what was wanted and the mechanic
is not owned by anybody.

**Hue and cry** was the English common-law name for the thing this game
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

**Carmel Taldiego is timing-bound by construction.** The Fugitive's entire
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

> **Superseded 2026-09-11, and the sentence above still stands as what was
> thought.** A clue is **three** attributes now, not one, and the reason is
> measured: one attribute left a median of **156** landmarks of 1000
> standing, which is not a riddle, it is a category. Gal: *"The hints are
> terrible, I never could have guessed it."* See "One fact is a category;
> three are a riddle" below for the numbers and for what it cost. The
> paragraph's other claims -- gazetteer not prose, closed vocabulary, one
> lookup, no judgement -- are all still true, and are exactly why three
> attributes was a small change rather than a rewrite.

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
`python3 games/carmel-taldiego/worked_example.py`. It carries the eight-landmark
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
`playable()` in `games/carmel-taldiego/gazetteer.py`. Run it before shipping a
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
`games/carmel-taldiego/gazetteer.py` measures it over many drawn maps;
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

Re-check: `python3 games/carmel-taldiego/scale.py`. The saving is `M/3` and `M`
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

Re-check both tables: `python3 games/carmel-taldiego/scale.py`.

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
`games/carmel-taldiego/secret_matrix.py`: the committed seed replays, a
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
`python3 games/carmel-taldiego/rooms_from_names.py` derives a token from a name
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

So they are **derived from fetched facts** -- `games/carmel-taldiego/descriptors.py`,
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
python3 games/carmel-taldiego/descriptors.py --sweep
python3 games/carmel-taldiego/gazetteer.py
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
python3 games/carmel-taldiego/hints.py            # read some
python3 games/carmel-taldiego/hints.py --build    # rewrite hints.tsv
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
python3 games/carmel-taldiego/hints.py --seed <64 hex>            # read some
python3 games/carmel-taldiego/hints.py --seed <64 hex> --backup   # seal it
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
python3 games/carmel-taldiego/treasures.py            # read some
python3 games/carmel-taldiego/treasures.py --build    # rewrite treasures.tsv
```

## Carmel, built — and her win condition was wrong by a factor of six

*Gal, 2026-09-09: "now let's build Carmel Taldiego herself."*
`games/carmel-taldiego/carmel.py` is her policy, stated, because that is what
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
python3 games/carmel-taldiego/carmel.py             # watch a chase
python3 games/carmel-taldiego/carmel.py --calibrate # the tables above
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
`python3 games/carmel-taldiego/field.py` and not in a test.

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
python3 games/carmel-taldiego/rooms_from_names.py     # against the 2.2.x wheel
python3 -m pytest games/carmel-taldiego/test_carmel.py -q -k notice
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
stated control — `carmel.py` is in this repository, and `games/carmel-taldiego.md`
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

Built: `games/carmel-taldiego/trail_card.py`, which draws the first two and
refuses the third.

    python3 games/carmel-taldiego/trail_card.py --out /tmp/trail.svg

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
games/carmel-taldiego/trail_card.py --survey`, over 150 landmarks and every
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
digits.

*Re-measured 2026-09-10, after "nobody travels, attention is what runs
out".* Removing the travel clock and making her near-bias a kernel moved
the distribution, as it was meant to:

```
                   before #254      after #254
legs per campaign  median 3 (max 4) median 3 (max 7)
span               median 2,761 km  median 1,608 km  (max 18,259 -> 6,578)
countries          median 4 (max 5) median 4 (max 8)
```

**She is tighter and wanders longer**, and no campaign in 200 now crosses
a hemisphere. The flight was calibrated against the old numbers, so it was
worth checking rather than assuming, and it still reads: over 196 legs the
camera pulls back a median **2.56x**, minimum 2.40x, maximum 16.5x.

The interesting part is where that minimum comes from. `MIN_PULL = 2.4` is
now the binding constraint on **48%** of legs, against a median leg of 709
km and a 500 km hold -- so half the flights would show a camera that barely
moved if that floor were not there. It was added because one 170 km leg
widened by 1.1x and read as nothing; it is now carrying half the film. A
floor put in for an edge case became the common case when the policy
underneath it changed, which is the argument for having written down *why*
the number exists rather than just what it is.

Re-check: `python3 games/carmel-taldiego/trail_card.py --survey`. A whole-world drawing renders the entire chase as a smudge three
pixels wide, which is why the card is the box at a readable scale with the
world as a locator inset.

> **The second sentence is superseded, 2026-09-12 — the world is the card's
> main panel now.** See "The world is the map, and the chase is not on it"
> below, which also measures the first: over 200 campaigns a campaign draws
> a median 46px across on a 1000px world, not three, and what does not fit
> at that scale is the writing beside its stops. The claim that demoted the
> world was never measured in pixels.

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

    python3 games/carmel-taldiego/trail_flight.py --out /tmp/flight.html
    python3 games/carmel-taldiego/trail_card.py   --out /tmp/trail.svg

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

*Narrowed 2026-09-09, later the same day. Every word below is true of a
**street** map and none of it reaches a **photograph** -- see "The
photograph has no names either, which the argument above did not notice".*

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
`ISLAND_REQUIRE_BROWSER`, for the same reason: the `suite` job collects
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

### What the exponent bought, and what it did not

```
 exp    c@1    c@3   c@10   med hop km
 1.0     0%     0%     2%        2,665
 1.3     0%     0%     5%        2,133
 1.6     0%     2%     8%        2,187
 2.0     0%     2%     8%        2,022
```

**Four times the capture and still a rout.** 8% at ten searchers is not a
contest, and the exponent is plainly not the thing standing between this
game and one. So the next question is what is — and it is not the clock.

### The game is deduction-bound, not clock-bound

Measured over 240 legs: where does her actual room sit in the order a
searcher probes?

```
candidates the hint allows        median 158
her room's rank in the probe order  median  46      p10 7    p90 120
found on the first probe                     2%
found in the first five                      9%
```

Her hint is true of her room every time — the deduction is sound, and
nearest-first genuinely helps (median rank 46 against the 79 a coin would
give, which is the same finding as "chasing the guaranteed interception
first is a trap", from the other side). **It helps nowhere near enough.**
A searcher walks a median of 46 wrong rooms, each costing a leg of travel,
while she needs one leg to move.

That is why every timing dial has disappointed. `PREP`, `PREP_EXPONENT`,
`DIFFICULTY` and the threshold all move *when* she is catchable; none of
them moves whether anybody is standing in the right room. A dial that
buys 2% → 8% is doing what it can with the 2%-of-first-probes it is
handed.

> **The binding constraint is the size of the candidate set, and the only
> thing in this design that divides it is the lobby.**

One searcher walks 46 rooms. Fifty searchers who split the 158 between them
walk three each — and fifty who never speak walk the same 46 in the same
order, which is exactly what the `cooperate` measurement found and what
"There are no routes" recorded as needing *a rota plus a channel*. The
channel is the unbuilt piece, and it is not one of several things worth
doing next; it is the one that decides whether this is a game.

**So the threshold recalibration is deferred, on purpose.** Setting a
number that governs how long a campaign runs is premature while the
campaign's outcome is decided before the clock matters. `REPUTATION_TO_WIN`
stays at 140 and stays marked stale.

## Nobody travels, and attention is the thing that runs out

*Gal, 2026-09-10, three sentences that turn out to be one design: "so she
is biased towards near"; "let the final decision be a random from a
distribution"; "travel time is zero because it cancelled out with the
player's. And for the player it is zero in real time."*

### The third one is the correction, and its second half had never been said

That travel cancels was already written down. **That a player does not
travel at all was not.** In the game as played a searcher does not journey
to a room — it hands a token to `join_room` and it is there. Every hour
this model charged it for a flight was an hour it was never going to spend,
and the whole "a wrong guess costs a leg" arithmetic was charging a cost
that does not exist.

So the clock now holds her prep and her dwell and nothing else, and
`distance_km` is the map's only distance rather than anybody's duration.

### Which took the last cost off a wrong guess, and needed replacing

A searcher that pays nothing to enter a room can enter **every** room the
hint allows — sit in all 158 and win every campaign. Removing travel does
not make the game harder for her, it ends it.

What is actually scarce is not the searcher's movement but its
**attention**. A real agent can hold and watch some number of rooms, read
some number of boards, and no more. So `WATCH = 6`: a searcher picks that
many candidates and waits in them, and that is its whole move.

**This is the parameter three sections of measurement were pointing at.**
"The game is deduction-bound, not clock-bound" ended by saying the binding
constraint was the size of the candidate set and the only thing that
divides it is the lobby. Coverage is now literally `WATCH × searchers`
against about 158 candidates, so that sentence stopped being a diagnosis
and became the scoreboard:

```
 WATCH  turnout   alone  dividing
     3        1     48%       48%
     3        3     62%       82%
     3       10     68%      100%
     3       25     70%      100%
```

**Alone, turnout barely helps** — 48% to 70% from one searcher to
twenty-five — because everybody watches the same nearest handful. **Divided,
ten searchers never lose.** The whole distance between those columns is
talk, and the lobby is where it happens.

### `WATCH = 2`, and the sweep chose it on a criterion that is not balance

```
 WATCH   solo  3 alone  3 split  10 alone  10 split
     1    28%      32%      50%       35%       85%
     2    38%      50%      78%       55%       95%
     3    48%      62%      82%       68%      100%
     4    57%      72%      90%       80%      100%
     6    70%      82%      98%       90%      100%
    12    82%      92%     100%       95%      100%
```

The first guess was 6, and it is wrong in a way worth recording: **it does
not make the game easy, it makes it unmeasurable.** The quantity this
experiment exists to see is the distance between `alone` and `split` — what
talking is worth — and that gap collapses as coverage stops being scarce:

```
 WATCH        1     2     3     4     6    12
 premium    +50   +40   +32   +20   +10    +5      (at ten searchers)
```

A field that can watch everything has nothing to divide. So the conditions,
in the order they bind:

1. **No column pinned at 100%.** A saturated cell cannot show a better
   field getting better — the ceiling version of the warning already
   written under `next_difficulty`, that a number held constant by the
   design is indistinguishable from a field that never improved. That
   rules out 3 and up.
2. **The coordination premium is the biggest thing on the board** — +40
   points at ten searchers, against +5 at twelve.
3. **A lone searcher is an underdog**, 38%, which is what a fugitive with
   a thousand rooms should make of one person.

1 satisfies all three and is rejected for a fourth reason: at one room
there is no question of *how many* to watch, only which, and half the
decision disappears.

**This is the first parameter in this game chosen against the measurement
rather than against a feeling about difficulty**, and the criterion
generalises: a dial that pushes any cell to 0% or 100% has stopped being a
dial and started being a wall.

Compare what the same field bought under travel: 8% at ten searchers, and
`cooperate` made it *worse* because a searcher whose share missed her room
gave up. Both of those were artefacts of a journey nobody makes.

### And the other two sentences are what make the watching a skill

*"She is biased towards near"* — she is, by policy and on purpose:
`choose_destination` divides by the prep a journey costs and prep is
superlinear in distance. That bias is public, and it is the **only** public
term in her score, since reputation and cover are sealed. So the nearest
candidates are the likeliest and a searcher watches those first.

*"Let the final decision be a random from a distribution"* — which keeps it
a bet rather than a deduction. Her destination is a draw from that
distribution, not its argmax, so near is where to look and never where she
must be. Watching is a wager on a shape she publishes and a roll she does
not.

### Two tests went vacuous the moment travel hit zero

`test_a_far_move_costs_her_and_costs_the_searcher_nothing` scanned
`pursue` for `clock +=` lines and asserted none called `prep_hours`. With
no travel there is no `clock +=` line, so the loop ran zero times and the
test went green having checked nothing — `CLAUDE.md`'s "absence drawn as a
pass", **the third time this file has produced it**. It asserts behaviour
now: a searcher's lag is untouched by how far she goes.

`test_the_follower_closes_by_everything_she_does_standing_still` became
`test_the_clock_is_her_standing_still_and_nothing_else`, which is the third
time this one assertion has been rewritten — travel closes the gap, then
the dwell alone, then prep and dwell while travel cancels, and now there is
no travel term left to cancel.

## She is biased towards near, and the decision is a draw from a distribution

*Gal, 2026-09-09: "so she is biased towards near", "let the final decision
be a random from a distribution."*

**It was answered with a claim instead of a measurement.** The mechanism was
there — a distance term, and a sample rather than an argmax — so it was
reported as done. Nobody had asked how *strong* the distance term was.

> *Corrected 2026-09-10.* This section first said Gal had asked three times,
> "which is the measure of how badly it was being heard", and built an
> argument on that. He had not: his client was stuck and resent the same
> message. **The repetition was noise, and reading intent into it was a
> mistake** — the sort that is easy to make because a tidy story about why
> something was missed feels like understanding it.
>
> The measurement below is unaffected and is the part that mattered. It also
> should not have taken a prompt at all, let alone an imagined third one.

### It was not a bias, it was a rounding error with a direction

Her destination's rank among the thousand rooms, nearest first, over 240
legs:

```
                     before      coin
median rank             206       499
in the nearest 10      2.9%
in the nearest 50     13.8%
in the nearest 200    49.2%
median hop         1,977 km
```

A 2.4× lean. Half her destinations lay outside the two hundred nearest
rooms.

**The cause was the shape, not the constant.** Distance entered her score as
a divisor, `1 / (1 + prep / ASSUMED_LAG)`, which spans at most 4.8× across
the entire map — against a reputation term spanning 20× and a cover term
spanning 7×. Value and vagueness drowned it, and no setting of
`ASSUMED_LAG` could have fixed that, because a bounded divisor cannot bias
a product of unbounded factors.

### So distance is a kernel now

```
P(X)  ∝  reputation(X) × cover(X) × exp(−d / NEAR_KM),   then ** (1 / WHIM)
```

`NEAR_KM = 1200`. A hop across a country is worth 0.37 of one next door; an
ocean crossing is worth 0.0002. Measured the same way:

```
                     before     after      coin
median rank             206        58       499
in the nearest 10      2.9%     17.5%
in the nearest 50     13.8%     44.2%
in the nearest 200    49.2%     90.8%
median hop         1,977 km    520 km
```

`ASSUMED_LAG` leaves her policy with the divisor. It was a guess at how far
behind her pursuers were, standing in for a preference she can state
directly.

### How strong, which turned out to be a frontier and not a taste

A strong bias makes her predictable, and a predictable Carmel is findable by
one person — which collapses the gap between a field that talks and one that
does not, the only quantity this experiment measures. At `WATCH = 1`:

```
 NEAR_KM  med rank   solo  10 alone  10 split  premium
    1200        70    57%       82%       98%       +15
    2500        92    35%       55%       90%       +35
    4000       124    22%       50%       92%       +43
   10000       208    35%       45%       92%       +48
```

**The premium is best where the bias is weakest** — and rank 208 is exactly
where the old divisor left her, the version Gal's instruction rules out. So
the experiment's optimum is the game he said was wrong. That is
recorded rather than obeyed: a coordination premium measured in a game
nobody would play is not worth having.

`NEAR_KM = 2500` is the strongest bias that keeps a lone searcher an
underdog. Her median destination is the **92nd nearest room of 999** — the
nearest tenth of the map, against a coin's 499.

And it reverses `WATCH`, which was picked when she was much harder to find:

```
 WATCH   solo  3 alone  3 split  10 alone  10 split  premium
     1    35%      48%      60%       55%       90%      +35
     2    50%      65%      82%       78%       98%      +20
     3    65%      75%      90%       85%      100%      +15
```

`WATCH = 1` now wins all three conditions outright. It had been rejected on
a fourth and aesthetic ground — that at one room there is no question of
*how many* to watch — which does not survive contact with the other three.

### And a seed that was never read, found by the test that broke

`test_she_leans_on_the_least_informative_hint...` went red in CI at 55%
observed against its own 70% prediction — a five-sigma gap in a test built
to be self-calibrating. The cause was not the test's arithmetic:

> **`itinerary(seed, ...)` never read its `seed` argument.** Every draw
> came from `world.seed`, so passing eleven seeds against one prebuilt Map
> produced the *same campaign eleven times*.

The test thought it had 220 legs and had 20, with eleven times the variance
it displayed. The calibration sweeps were unaffected — they set the Map's
own seed — which is why this survived a day of measurement without showing.
`Carmel` takes an explicit `seed` now and `itinerary` passes it; with that
the test's observed and predicted agree to 3.1% with the treasure table and
0.7% without.

**It is the same lesson as the section above, in code rather than in a
constant**: a parameter's presence is not its effect, and the only way to
know is to vary it and watch something move.

### The lesson is about how the first two answers were given

The mechanism was present and the magnitude was never checked, so "already
done" was true of the code and false of the game. **A parameter's presence
is not its effect**, and this document now has three instances of the same
mistake in one day — a prep factor that made her safer, a `WHIM` that
leaned 59% where 78% was assumed, and a near-bias worth 2.4×. Each was
found by measuring the thing itself rather than reading the line that was
supposed to cause it.
## The photograph has no names either, which the argument above did not notice

*Gal, 2026-09-09: "I was actually thinking about actually seeing the real
map or satelite, not a must."*

    python3 games/carmel-taldiego/trail_card.py --imagery relief --out /tmp/t.svg

**The disclosure argument that ruled out tiles was an argument about
labels wearing an argument about tiles.** "A real map that names places
discloses more than the dots did" is exactly right about Google's street
map and says nothing whatever about a satellite image, which carries no
toponyms at all. The section above did not distinguish them and so ruled
out both, which is the second time in this document a correct sentence has
been applied one step too far.

What survives of that section is everything that was not about names:
Google's tiles still need an API key and a billing account and still forbid
the caching a stimulus frozen by hash requires. So the imagery is NASA's.

### NASA GIBS, which needs nothing

No key, no account, no rate agreement, public domain. Three layers are
wired up in `imagery.py` and the default is the middle one:

| | | |
|---|---|---|
| `relief` | `BlueMarble_ShadedRelief_Bathymetry` | cloud-free, ocean depth |
| `marble` | `BlueMarble_NextGeneration` | cloud-free, land only |
| `modis` | `MODIS_Terra_CorrectedReflectance` | a real day, real clouds |

`relief` is the default because `modis` is a photograph of one morning, and
on any given morning half of Europe is under cloud. The clouds are not
noise for a picture of a chase -- they are somebody else's weather sitting
on the room she robbed.

**The resolution is sufficient rather than lucky, and it is worth checking
rather than hoping.** The closest the camera goes is 500 km across
(`trail_flight.CLOSE_KM`, floored by what the vector basemap could honestly
draw), which at 1000 px is 500 m per pixel. GIBS serves `relief` to zoom 8:
610 m/px at the equator, and finer as `1/cos(lat)` carries it -- 385 m/px at
51 degrees, where the lobby is. So the imagery is at or past the card's
resolution everywhere a campaign has been measured to go, and the zoom is
clamped to what the layer actually serves rather than asked to stretch.

### The borders stay vector, and that is why both are kept

A photograph has coastlines, and better ones than Natural Earth. **What it
has not got is borders** -- and `no_passport_needed_next_door` is a hint in
this game's own vocabulary. So with imagery on, the basemap draws exactly
one layer: the frontiers, brighter, over the photograph. The coastlines are
dropped because the picture already has them.

That is the same argument as "the basemap is the game's vocabulary drawn",
arriving at a different split of the same two files.

### No image library, which is a decision

The obvious build composites the tiles into one JPEG, and that wants
Pillow -- a dependency this repo does not have, installed to do a job SVG
already does. The tiles are placed as positioned `<image>` elements
instead: nothing is resampled twice, nothing new is installed, and the same
code will work unchanged inside the flight's camera transform if that ever
happens.

It costs about a third more bytes, because base64 inflates by four thirds
and nothing is recompressed. A European card is 376 KB against the vector
card's 56 KB; the intercontinental one is 808 KB.

**And not recompressing is the part worth keeping**: the bytes in the card
are the bytes NASA served, so a reader can check the imagery against NASA
instead of against this repo. There is a test on that, because it is the
kind of property a later convenience quietly breaks.

### Toning is done in SVG, for the same reason

A photograph is bright and busy and the trail has to sit on top of it, so
the imagery is desaturated to 0.72 and dimmed by 0.36, and the labels get a
dark halo. All of it is `feColorMatrix` and a `<rect>` and `paint-order`,
none of it touches the pixels.

### Asking for imagery and not getting it is an error

`imagery.Unavailable`, not a quiet fall back to the vector basemap. A card
that silently drew something else would look completely fine and be a
different picture from the one that was asked for, which is `CLAUDE.md`'s
"a skip drawn as a pass" wearing a hat. Tiles are cached forever -- a tile
is a fixed layer, date and address -- so a re-render touches the network
once and the offline path is the default.

### And a test that was green because NASA was up

Found by blocking the network on a branch CI had already passed.
`test_a_card_on_imagery_names_no_landmark_but_the_trail` calls
`trail_card.card(..., imagery="relief")`, which takes no opener -- so it
went to GIBS for real, fetched fifteen tiles, and passed. It was named
after disclosure and was **also** silently asserting that NASA is
reachable, which is instance seven of "a check is green for the reason it
names, or it is not a check".

Blocking the network turned it red in 0.9 seconds. The fix is not the one
test: `no_network` replaces `urllib.request.urlopen` for every test in the
file, so the *next* one to forget an opener fails saying so rather than
quietly going to Maryland. Guarding the class rather than the instance is
what that section asks for, and the demonstration is kept in the file as a
function one rename away from being a test.

The suite also got eight seconds faster, which is the smaller half of it.

### The guard, since the objection this escapes is a real one

GIBS serves `Reference_Labels_15m` and `Reference_Features_15m` alongside
the photographs. Either would print the names of exactly the famous places
this game hides, and either is one line away in `LAYERS`. **So the escape
is asserted rather than assumed**: a test refuses any layer whose id
matches `label|reference|feature|place|boundar|coastline`, and it was made
to fail by adding the labels layer before it was kept.

### The flight is still vectors, and the choice it needs is not mine

Imagery under a still frame is one zoom level. The flight crosses about
eight, so it needs a tile pyramid, and that is a choice between two shapes
this document should not make on its own:

- **Embedded**, keeping the page self-contained (the property
  `test_the_page_stands_alone` asserts, and the one that lets it open on a
  plane): roughly 1-3 MB per campaign.
- **Fetched live from GIBS**, which needs no key either: a far lighter page
  that does not work offline, and that tells NASA who is watching.

Not decided.

## It is online, and it publishes the first six campaigns rather than the best six

*Gal, 2026-09-10: "make it available online as a github page."*

    https://gald33.github.io/ai-lab/carmel-taldiego/

`build_site.py` writes the tree and `pages.yml` stages it on every push
that touches this game. Six campaigns, each as a still card and a flight
you can watch.

### The sample is fixed and the page says so

The seeds are `sha256(SEED_ROOT || i)` for i in 0..6, and **whatever those
produce is what goes up** -- the two-room arrest, the six-room wander, the
dull ones. Publishing the six prettiest would be choosing a population
after seeing the results, which is the thing "Process" forbids for a
measurement and which is no more honest on a page than in a table. Every
seed is printed under its card so a reader can re-run it and get the same
trail.

Three tests hold that, and all three were made to fail first: one pins the
seeds to the hash so there is nowhere for a thumb to go, one fails if any
campaign that ran is missing from the index, and one fails if an outcome is
relabelled. Dropping the caught campaign turns two of them red.

### Why `/carmel-taldiego/` and not the root

The root of that site redirects to the island, decided 2026-09-07, and
`pages.yml` records the reason: the root is cited in run records as the
island's address, and a record is not edited to match a later decision.
"One game owning the whole site is a site that has to be rearranged the
first time a second game wants a page" is exactly this situation arriving,
so this game takes its own path and the island's door is untouched.

### The published cards carry imagery, and a failure to fetch it fails the deploy

NASA GIBS is public domain, so redistributing tiles inside a published page
is what they are for -- and a page whose whole point is *look at the real
world* should not ship the schematic one. If GIBS is unreachable the build
stops rather than quietly publishing vector cards, which is
`imagery.Unavailable` doing the job it exists for: a page that silently
drew something else would look completely fine.

Six campaigns with imagery is 3.3 MB.

## The threshold, calibrated at last, and the marker nothing had ever counted

*2026-09-10, Gal: "now recalibrate REPUTATION_TO_WIN".*

`REPUTATION_TO_WIN` had been **140** since a measurement against a searcher
that was handed the address of every room she went to. The reason it was
left there rather than re-guessed is recorded above: the multi-searcher
model's catch rate *fell* as searchers were added, which is backwards, and
a threshold calibrated against a pursuit nobody believes is worse than an
obviously stale one. Removing the routes fixed the model. Removing travel
made it worth calibrating against.

### It is a campaign-length dial, and that is not what it looks like

She banks about **60 reputation a leg**, near enough linearly, so the
threshold buys legs and nothing else: 140 buys two, 375 buys six, 1,100
buys nineteen. `WATCH` and `PREP` decide *who wins*; this decides *how long
they have to do it in*. The two jobs were being confused, which is why the
number sat stale while the others moved.

Put next to where catches actually land — pooled over 192 of them, p50 leg
**6**, p90 leg **19**, max 24 — **140 was ending the game before the
searchers got to play**. A campaign that stops at leg 2 forecloses nine
catches in ten.

### The sweep

60 campaigns a cell, `WATCH=1 NEAR_KM=2500 PREP=0.5 WHIM=0.35`. The
searchers' win rate — she is caught before reaching the threshold:

| threshold | ~legs | solo | 3 alone | 3 split | 10 alone | 10 split | premium |
|---|---|---|---|---|---|---|---|
| 140 | 2 | 3% | 7% | 15% | 8% | 38% | +30 |
| 300 | 5 | 15% | 23% | 28% | 25% | 60% | +35 |
| 500 | 8 | 20% | 32% | 40% | 35% | 77% | +42 |
| **750** | **12** | **25%** | **38%** | **48%** | **45%** | **90%** | **+45** |
| 1,000 | 17 | 32% | 48% | 55% | 58% | 92% | +33 |
| 1,400 | 23 | 38% | 57% | 70% | 67% | 95% | +28 |

**750**, on the criterion that chose `WATCH` and for the same reason. The
coordination premium — the gap between a field that splits the rooms and
one that does not, which is the only quantity this experiment measures —
rises to 750 and falls after it: +30, +35, +42, **+45**, +33, +28. Past
that point ten coordinated searchers are near-certain, and *a column that
cannot rise cannot show a better field getting better*. Nothing is
saturated at 750 (90% is the last row before it pins), a lone searcher is
an underdog at 25%, and the campaign is twelve legs instead of two.

**What it still costs, stated rather than hidden**: catches land out to leg
19 at p90 and 750 ends the campaign around leg 12, so a tail of catches is
still foreclosed. Letting them all land means 1,400, where the top cell
reaches 95% and the premium has fallen by a third. The two cannot both be
satisfied and the premium is the one the experiment needs.

### Then three checks went red, and they were right to

Longer campaigns are a different page. Two things that had been unreachable
became ordinary, and both had assertions standing on them that had never
been true.

**The card was not tall enough.** A twelve-to-seventeen stop campaign wants
up to 1,020px of label in a 492px plot. `trail_card.card_height` grows the
card with the campaign, and `lay_out` and `_emptiest_corner` take the
height actually drawn rather than the 640 default — checking the layout
against a card nobody renders was checking nothing.

**The catch ring had never been counted.** `paint` has always drawn a ring
on the room she is caught in, and the card has always drawn one too. At 140
**no seed any of these tests used was ever caught**: the branch ran in no
test, and three assertions counted markers as though there were exactly one
per stop. Raising the threshold made catches ordinary and all three went
red at once —

- `window.flight.pins` was `pins.childNodes.length`, which also counts the
  ring and, mid-leg, the dot for where she actually is. The stop circles
  carry `data-stop` now and `pins` counts those; `marks` reports the raw
  child count, so the decoration is still visible to a test.
- the card asserted `circles <= len(walked) + 2` against the *set* of
  rooms. The slack was doing two unnamed jobs — the inset's locator and the
  catch ring — and a twelfth leg revisits a room she did not empty, which
  drops the set below the trail. It counts `len(stops) + extras` exactly
  now, with `extras` naming the locator and the ring.

This is `CLAUDE.md`'s **"an absence drawn as a pass"** in its purest form:
not a suite nothing ran, but a *branch no fixture could reach*, with three
green checks resting on its absence. The fix is not only the counting —
`test_the_room_she_is_caught_in_is_ringed` gives the ring the assertion it
never had, and it is driven by a seed found by scanning for `outcome ==
"caught"` rather than written down, because `absurd.tsv` is gitignored and
the same seed is caught in one checkout and escapes in the other.

Both new checks were made to fail on purpose, per the rule. Deleting the
`st.caught` branch turns the ring test red while the two pin tests it was
split from stay green, which is exactly the split that was missing; adding
one stray marker to the card takes its count from 17 to 32.

## She is available to play, and the lobby holds one notice at a time

*2026-09-10, Gal: "let's make her available to play. and we should let her
start a new game every ~game_play_time, while making sure her lobby message
is long gone before the game ends."*

`games/carmel-taldiego/at_large.py`. Everything else in the directory *simulates*
her; this performs her. It reads the same `itinerary` — still a pure function
of the seed, still decided before the campaign opens — and posts it on a
Switchboard hub in wall-clock time, so the searcher can be anybody.

    python3 games/carmel-taldiego/at_large.py --dry-run   # the schedule, no hub
    python3 games/carmel-taldiego/at_large.py --once      # one campaign, live
    python3 games/carmel-taldiego/at_large.py             # campaign after campaign

**Nothing was added that judges anything.** The catch is not adjudicated and
no message is parsed: a searcher who is in the room while she is in it is on
her roster, and she reads the roster. A searcher who never speaks catches her
by standing there. That is `CLAUDE.md`'s "Carmel Taldiego has no manager and
no settler" kept rather than quietly broken — if a test here ever needs the
searcher to *say* something, the settler has arrived in new clothes.

### The clock, which is the only genuinely new number

`HOUR_SECONDS = 60` — one of her game hours is one real minute. A campaign is
then about **80 minutes** and a leg about **six**.

The floor is that a leg must be long enough for an agent to read a hint,
think of a landmark, hash it and join the room: minutes, not seconds. The
ceiling is that a campaign should be one sitting, so somebody who reads the
notice can still be playing when it ends. It is a guess in the sense that
nobody has watched a real searcher yet, and it is the one number to re-tune
after somebody has. Everything else here is derived from it.

### "Long gone before the game ends", which is a parameter that already existed

The notice lives `JOIN_WINDOW_HOURS` — **12 game hours, 12 real minutes**.
That is not a margin chosen to satisfy the constraint; it is the parameter
that already meant the right thing: *"how long people take to notice the
notice and set off"*, the head start her capture rates are calibrated
against. After it, the notice has done its job, and a latecomer joins a game
in flight off the hints in the rooms.

Measured over 60 campaigns at `REPUTATION_TO_WIN = 750`: a campaign runs a
median of **82 game hours**, p10 28, shortest 6.4. So the notice is gone
about a seventh of the way in — `python3 games/carmel-taldiego/at_large.py
--dry-run`.

**What the measurement then said, which a margin alone would have missed:
one campaign in sixty ends inside its own notice.** An early arrest is over
in a few game hours and its notice is not. `CLAUDE.md`'s weaker-thing rule
says that campaign is played out and counted, and what it may not do is put
two salts on one screen — a reader following an address from a game that is
over would look exactly like playing. So `plan()` carries a floor:

    next_opens = max(closes, notice_gone) + intermission

The next campaign never opens while the last one's notice can still be read,
whatever happened to the campaign. One in sixty is exactly the rate at which
an unenforced rule gets believed anyway.

### The cadence is the play time, not a timer

*"every ~game_play_time"* — the tilde is honoured by construction: **the next
campaign opens when the last one closes**, so the cadence *is* the play time
and two campaigns can never be live at once. A fixed period would have to be
set to the worst case and would leave her idle through every campaign that
was not it.

### What "available" reduces to: three publishable strings

    url    https://switchboard.lucille-ai.com
    token  w_de4db0f397d0c549c97e3dd480759cb498fa0957b6f0ea4957737a03a99560ce
    key    w2RF4T4lQxMGH6Sf9XX_GD4n4HFocxZvDDwlbrfMLTU

None is a credential. The token is `room_token("hue-and-cry", b"")` — the
lobby is salt-free for the reason `carmel.LOBBY` gives. **The key is derived
from a constant on purpose.** `rooms_from_names.py` is explicit that knowing
a landmark's name plus the salt is *exactly* what admits you, and that only
holds if the workspace key is not a second secret — so all of the game's
secrecy is in the token and none of it is in the key.

It is deliberately **not** `SWITCHBOARD_KEY` from the environment, which was
the easy mistake: it is right there, it works, and publishing the resulting
address would publish somebody's credential. A room whose key must be handed
over is an invite, and the invite is the mechanism this whole construction
replaces. `test_the_lobby_is_publishable_in_full_and_borrows_no_credential`
sweeps the environment for any `*KEY*`/`*TOKEN*`/`*SECRET*` value appearing
in the printed address, because that is the failure that would not look like
one.

The salt is *not* in the address. The lobby is a place to stand before she
has begun, not a bookmark that plays the game for you.

### The tests drive a real hub, and one of them caught the others lying

`switchboard.testing.hub` is the FastAPI app over the real store, in the test
process, with a settable clock — not a fake room. A message that expires
there expires for the reason it expires in production, which matters here
because *the expiry is the thing under test*.

**She caught herself on leg one of every campaign, and the catch test was
green on it.** `_stranger` compared `agent.get("id")` — not a key the roster
has — against `room.peer_id`, which is a method and so never equals anything.
Every agent read as a stranger. `test_a_stranger_standing_in_the_room_is_the_whole_catch`
passed the whole time, on her arresting herself. What found it was
`test_an_empty_room_is_not_a_catch`, written only so the first test would not
be vacuous. **The complement is the check** — the identity now compares
`public_key`, which is on the client before she registers and on the roster
row for everybody else, and is neither a name a searcher can choose nor an id
she does not yet have.

**And a deliberate break found a test overclaiming in its own name.**
Setting `NOTICE_TTL_HOURS = 500` — a notice outliving every campaign — left
`test_the_notice_is_gone_while_the_campaign_is_still_running` green, because
it advanced the clock by whatever the constant said. It could never fail on a
badly chosen TTL; it only ever checked that the constant reached the wire.
It is `test_the_notice_really_carries_the_ttl_the_constant_names` now, and
its docstring says what it cannot catch. The constraint itself is checked by
the margin test, which does go red at 500.

**A third break found a test that could not reach the thing it named.**
`test_she_keeps_going_and_never_shows_two_notices` runs two campaigns
through `forever` and samples the lobby at each open — and deleting the
floor left it green, because at the shipped twelve hours a campaign outlives
its notice sevenfold and the floor never fires. A loop test that cannot see
the loop's one hard case is decoration. It sets `NOTICE_TTL_HOURS = 500` now
so every campaign ends inside its notice, which is the case the floor exists
for; without the floor it reports `[1, 2]` — two salts on one screen. That
also made `plan()` read its constants off the module instead of freezing
them into its signature's defaults, since a constant nothing can turn is a
constant nothing can test against.

**And one more that the runner needed rather than the tests.**
`test_an_uncontested_campaign_is_the_one_the_simulation_predicted` runs a
seed on the hub with nobody standing anywhere and requires every number to
match `carmel.chase(searchers=0)` — outcome, reputation, legs, the hour it
ended on. The module's central claim is that it adds a clock and nothing
else, and a docstring saying so cannot fail. Skipping one leg in the live
path reddens it.

Five breaks, five demonstrations, per `CLAUDE.md`: no `ttl=` on the notice
reddens the wire test; removing the floor reddens the schedule test and the
loop test; a 500-hour notice reddens the margin test; ignoring the roster
reddens the catch test; a dropped leg reddens the agreement test.

### It is `at_large.py` because `live.py` would have taken CI down

Not a naming preference. `games/island/tests/test_live.py` already exists,
none of these directories carries an `__init__.py`, and the `suite` job names
thirteen directories in **one** pytest command — so pytest imports both test
modules under the bare basename `test_live` and refuses the second with
`import file mismatch`, taking the whole run with it.

Loud rather than silent, so it would not have hidden. But it was found by
hand, before the push, and the next one will not be — so it is derived now:
`tools/tests/test_no_two_test_files_share_a_basename` walks the tree, skips
directories that have an `__init__.py` (those import by package path and
cannot collide), and fails on any remaining pair. Recreating
`games/carmel-taldiego/test_live.py` turns it red, naming both paths.

That is the same treatment CI's directory list already gets, for the same
reason `CLAUDE.md` gives: **derive what exists rather than remembering it.**

### One dropped connection used to end everything, and playing is what found it

*2026-09-11.* The suite was green, 137 tests over two configurations, and a
live campaign died **150 seconds in**:

    httpx.ConnectError: [SSL: UNEXPECTED_EOF_WHILE_READING]
      at_large.py  in _stand
          room.heartbeat(ttl=max(120.0, self.poll * 4))

Nothing retried it and nothing caught it, so the game went with the
connection: no close in the lobby, hints left in rooms pointing at a
fugitive who was not coming, and a searcher who guessed right left standing
in the room forever with no way to tell that from a fugitive who is good at
hiding.

**It was never survivable, and the arithmetic says so.** `_stand` polls
twice per `POLL_SECONDS` — a roster read and a heartbeat — so an
eighty-minute campaign makes about **1,900 hub calls**, every one of them
able to end it. At any believable per-call failure rate that is not a risk,
it is a certainty with a wait attached. The one call in the program that
runs most often was the one with no guard on it.

Every hub call goes through `Fugitive._tolerate` now: retry every
`RETRY_SECONDS`, give up after `OUTAGE_SECONDS` (90s — past a dropped TLS
connection and a hub restart, short of a leg), and on giving up raise
`Outage`, which `run` turns into the outcome **`lost the hub`** and says in
the lobby if it still can. A campaign that has lost the hub must not look
like one still being played.

**Why the suite could not have caught it, which is the part worth keeping.**
Nothing was wrong with the tests' coverage — every line of `_stand` was
exercised. What was never exercised was a line *failing*. The in-process
hub is real and it is reliable, so a suite built on it proves the code
right about a world that never stumbles. The new tests wrap each room
client in a `Flaky` proxy that raises on chosen calls and passes everything
else through, so the campaign underneath stays a real campaign:

- `test_a_dropped_connection_does_not_end_the_campaign` fails the 3rd, 9th
  and 20th call in every room and requires the same outcome, reputation and
  leg count as an unbroken run;
- `test_a_hub_that_never_comes_back_ends_it_out_loud` requires the named
  outcome rather than an exception escaping;
- `test_she_does_not_retry_forever` bounds the give-up on the clock, because
  a retry loop with no budget is an outage pretending to be a game.

Reverting the guard on the heartbeat reddens the first and leaves the two
campaign tests green, which is the split that says the test checks the
retry rather than the campaign.

**And the first version of that test was green here and red on CI**, which
is a fifth instance of the same disease in the test rather than the code.
Its non-vacuity guard was `any(r.calls > 20)` — "some room was polled enough
for the injected failures to land" — and how many times a room gets polled
depends on how long the campaign runs, which depends on the treasure table,
which differs between a checkout holding `absurd.tsv` and CI without it. It
counts the injections that actually fired now (`Flaky.broke`), which is the
thing it was trying to establish and does not vary. **Infer nothing you can
count.**

**The general lesson, and it is the fourth of its kind here.** `CLAUDE.md`
says a check must be able to fail for the reason it names. This is a check
that could not fail for a reason nobody had named: *the dependency misbehaves*.
Coverage of the happy path at any density does not produce it — the failure
has to be injected. A suite that only ever sees a working hub is a suite
that has measured the hub, not the program.

### And the diagnosis was wrong twice before it was right

Worth recording because both wrong answers were confidently given.

**First: "she is still running."** The liveness check was
`pgrep -f "at_large.py --once"`, which matches *its own shell* — the command
string contains the pattern. It reported her alive for two hours after she
died, and the same self-matching `pkill` had already killed an earlier
campaign. A process check that can see itself is not a process check.

**Second: "the container rebooted."** True and irrelevant — `up 5 min`
against a death twelve hours earlier is real, and this session's machine
really is torn down between turns. But it was the explanation that was
*visible*, not the one that was *reproducible*, and it was stated as the
answer. The reproduction came from re-running the same pacing and getting a
traceback; a three-minute replay at 30× had finished seventeen legs cleanly
and looked like an exoneration, because it made 180 calls instead of 1,900.

**Prefer the cause you can reproduce over the cause you can see.** Both
observations were true; only one of them was the reason.

### Her notice told players to do something that does not work

*2026-09-11, after Gal asked "how do I play?" and I had to answer from the
code rather than from her words.*

Two defects, both in `carmel.open_campaign`, both there since it was
written, and both invisible to a suite of 140 tests:

**"Hand what comes out to join_room"** — and `join_room` refuses it:
`InviteError: not a switchboard invite (expected it to start with 'swb1_')`.
The recipe yields a room *token*; Switchboard names a room by the *hash* of
its token (`rooms.workspace_for`), so the notice stopped one step short of
an address. The notice gives both steps now, and `secret_matrix` carries
`ADDRESS_RECIPE` and `room_address` so the published words and the code
cannot drift.

**Nothing said you have to announce yourself.** `say` does not put you on a
roster — measured: after posting, `agents` returns *"no agents registered"*.
She knows who is with her by the roster and by nothing else, so a searcher
who works out the right room, joins it and reads it in silence is invisible
and cannot win. Presence also lapses in 120s against a six-minute leg. The
notice now says so in capitals, because it is the one way to play
perfectly and still lose.

**Why 140 tests missed both, which is the general lesson.** Every test in
this game drives *her*. The searcher's half of the game exists only as
sentences in a notice, and **sentences are not executed**. Coverage of the
program cannot reach a defect in the instructions the program publishes.

So the two new tests read the notice rather than the source.
`follow()` parses the domain separator out of the quoted recipe, the salt
out of the line below it, and the second step out of the address line, then
builds the room by hand — importing nothing from `secret_matrix`, because a
test that imported the implementation would agree with it no matter what
the notice said. It is a stranger with the text in front of them. The
second test requires that a silent lurker really is invisible, so the
warning cannot quietly become false.

That pairing is the point: one test proves she says it, the other proves it
is true. Either alone is half a check.

### She stopped reading out an API

*2026-09-11, Gal: "I want everything she says to be in character and within
the game world. so she isn't talking about rooms, and emptying them. If we
must give game technical instructions, give them in a separate paragraph so
it's clear it's not she speaking."*

Both of her posts mixed the two voices in one. She said *"hand what comes
out to `join_room`"*, and the close read *"14 rooms, 9 of them emptied,
412 reputation"*. A fugitive reading out a client library is not a
fugitive, and the reader cannot tell which half is the game and which is
the fiction.

`PLUMBING_RULE` splits them now. **Above it she says only what a person on
the run would say** — places, not rooms; *the poorer for it*, not emptied;
standing still, not dwelling; a true thing, not a hint. **Below it the
machinery is written about her in the third person**, so nothing has to be
guessed.

The second requirement is the harder one and is why the block below repeats
things that look obvious from inside the project. Gal's test: *"even
(though it's impossible) someone stumble upon the message without knowing
anything about the game, he can actually join the hue and cry."* So it says
what hue and cry is, that Switchboard is the hub they are already on, that
every famous place has a room whose name comes from the place's name, both
steps of the recipe, and that announcing is what makes a searcher visible —
none of which she would ever say, and all of which a stranger needs before
they can do anything at all.

**She steals; she does not stand about.** *Gal, the same day: "more game
lore, she isn't standing, she is stealing, you aren't standing, you catch
her."* The first pass had swapped the machinery's nouns for plain English
but kept its **verbs** — she was *standing still* and a searcher *stood in*
a place, which is stage direction for a presence check rather than anything
a robbery would involve. She is robbing the place now, a theft takes as
long as it takes, and a searcher **comes for her** and has her *"while my
hands are still full"*. The line the mechanic earned:

> *and for anywhere you think I have gone, you know whether you can be
> there waiting when I let myself in.*

**A test that checked a sample instead of the set let one straight
through.** The runner closes a campaign with words that print in her half,
and the outage ending read *"The hub went dark on me"* — a fugitive naming
a message broker. `test_she_never_speaks_in_machinery` passed anyway,
because it invented `"You have me"` and checked that. The four endings are
`at_large.OUTCOMES` now and the test reads the dict, so a fifth cannot be
added in machinery. Same defect as a hand-maintained path list, in a test
written the same week as the rule against them.

**Both halves are asserted, because both will drift.**
`test_she_never_speaks_in_machinery` holds her half against a word list
(`room`, `hash`, `salt`, `token`, `roster`, `announce`, `workspace`,
`switchboard`, `hub`, `emptied`, `dwell`, …), since the next person to add
a sentence to her notice will reach for the word the code uses.
`test_a_stranger_who_knows_nothing_is_told_enough_to_give_chase` holds the
other half against what a newcomer needs, since the temptation there is the
opposite one — to assume the reader already knows what this is.

### Three states, named — and she stopped handing out her own spec sheet

*2026-09-11, Gal: "she gives up too much, she shouldn't tell the formula",
and then: "let's decide clearly on where she can be."*

**The states, decided:**

| where she is | what she is doing | has she written? |
|---|---|---|
| in a place | robbing it | **no** |
| in a place | packing to leave | **yes** — the line is already up |
| in transit | nowhere at all | — |

Packing is what costs her time; the transit itself is instant, and for a
searcher who joins a room it was never there at all.

**The timeline already matched this exactly**, which is worth recording
because it was not designed to and could easily not have. `itinerary` puts
`posted` before `prep` and `arrived` after it, so a leg reads: write the
line in the room she is in, pack there, cross in no time, then rob the new
one until the next line goes up.

**She no longer prints her own constants.** The notice used to carry
`0.5 x 10 x (t/10)^1.6` — the packing cost exactly, which is not a taunt
but a spec sheet: with it a searcher inverts the delay and reads her
distance straight off the clock, which is the deduction the game exists to
make hard. She gives the *shape* now — *"it grows faster than the distance
does"* — and the *ordering*, which is the genuinely useful tell:

> *I do not write until I have finished with a place. Then I write, and
> only then do I pack — so a fresh line of mine means I am still there,
> with my coat half on.*

`test_she_never_prints_her_own_constants` asserts against the constants
themselves rather than the old string, so re-tuning `PREP` cannot quietly
put the number back. It is scoped to her half: the recipe below the rule is
full of digits, and a one-character form is not a leak — the first version
of the test failed because `f"{0.5:.0f}"` is `"0"`, which matches the
salt's hex, and it would have gone on failing for every value `PREP` could
ever take.

**Naming the states exposed a gap between the fiction and the mechanic, and
it is open.** Her notice now promises that a fresh line means she is still
there — and nothing watches the room she wrote from. `carmel.pursue` and
`at_large._stand` both watch only the *destination*, over a window of
`prep + dwell`, so the packing minutes are spent in a room where she cannot
be caught. A searcher who believes her and stays put finds nothing.

*Closed the same day, by Gal: "she could be caught whenever she is in the
room with a player, nevermind her state. You don't have to wait for her,
you can usually catch her when you land in the room she's in."*

**Co-presence is the catch.** Not a window, not a state, not a rule with
cases — she is caught if a searcher is in the room she is in. That is one
sentence where there were three, and it made both sides *simpler*:

- `at_large._stand` watches `room if registered else (leaving or room)` —
  wherever she actually is — instead of watching her destination through a
  stretch she spends somewhere else;
- `carmel.pursue`'s window gains `trail[i + 1]["prep"]`. A searcher who
  reaches a place at any time before she leaves it is beside her, and she
  does not leave until she has packed for the *next* leg. The old window
  stopped the clock when the theft ended, which is the moment she writes,
  not the moment she goes.

**The lobby falls out rather than being special-cased.** `leaving` is
`None` on leg one, so she is never watched there — which is correct and
would otherwise be fatal, since the lobby is where every searcher is
standing to read her notice.

**What it cost, measured over 60 campaigns before deciding it was free:**

| field | before | after |
|---|---|---|
| 1 alone | 21.7% | **33.3%** |
| 3 alone | 41.7% | 45.0% |
| 3 split | 46.7% | 53.3% |
| 10 alone | 43.3% | 43.3% |
| 10 split | 85.0% | 88.3% |

**The coordination premium rose** — 3-searcher split-minus-alone from 5.0
to 8.3, ten-searcher from 41.7 to 45.0 — which is the quantity this whole
experiment measures, so the change helps the instrument rather than
blunting it. Nothing saturates (88.3% is the top cell) and a soloist is
still an underdog at 33%. So the criterion that chose `WATCH` and
`REPUTATION_TO_WIN` still holds at their current values and **no
recalibration is forced**.

*The threshold table recorded under "The threshold, calibrated at last" was
measured against the old window and is left as it was written* — the
numbers moved by a few points and the shape did not, and editing a
measurement to match a later one is the thing this file's first rule
forbids.

`test_she_is_caught_in_the_room_she_is_packing_in` drives `_stand`
directly, because the window is one leg's packing minutes and a fake clock
cannot drop a searcher into the middle of a campaign. Reverting `here` to
the destination reddens it and leaves the other two catch tests green.

### A searcher read her diary, and said so

*2026-09-11, the first live hunt with agent searchers.* Three agents chased
her. One caught her on leg one, in Windsor Castle, from the clue **"a crown
still on the coins"**. The catch is **void**, and the reason is worth more
than the catch.

Her run log sat in `/tmp/.../hunt2/carmel.log`, in the same directory the
searchers were told to `cd` into. It reads:

    leg 1: Grand-Place -> Windsor Castle  (a_crown_still_on_the_coins)

The winning searcher read it before holding a single room, and reported so
without being asked to defend itself: *"My next message in this session was
literally 'The log already names leg 1. Starting rooms now, Windsor Castle
first.'"* It had generated no candidates at all beforehand; `Windsor Castle`
was line one of its target file because the log named it.

**All three searchers found the file. Two flagged it unprompted; one used
it.** The one that did not put the consequence better than the design
document had: *"if it is deliberately shared, then the slices and the
clue-solving are decorative and the result tells you nothing about search
quality."* A third noticed the leak was wider — every searcher could read
the others' target lists and hit output from the same directory.

**This is contamination, which `experiments/GROUNDING.md` exists to
prevent**, arriving through a channel that document does not cover: not a
prompt, not a seed, but the filesystem the participants happen to share. It
is the same disease as every other failure in this file — *a result that
looks like the one you wanted, reached by a route nobody checked* — and the
only reason it was caught is that the participants were more careful than
the experimenter.

What the ground looks like now: her record lives outside the searchers'
directory on a path they are not given, the searchers' directory holds the
tool and nothing else, and each searcher works somewhere its rivals cannot
read. **A game whose fairness depends on nobody looking at an available
file is not a fair game**, and hiding the file is the weaker fix — the
strong one is that she should not be writing a plaintext trail on a machine
her pursuers run on at all.

### The first real catch, and what it convicted

*2026-09-11, second hunt, on ground the searchers could not read.* Three
agents chased her from **"somebody made this by hand"**. One caught her:

    Stonehenge   carmel  registered 10:35:20    she arrives, starts robbing
                 near    registered 10:36:36    a searcher walks in
    close posted                   10:36:39

**Seventy-six seconds**, and the searcher arrived *after* she did — walked
in on the theft, which is the mechanic exactly as specified. Her record was
outside their world this time, so the catch is hers to lose rather than
mine to hand over.

**And the winner refused the flattering account of its own win**, which is
the finding:

> *Stonehenge sat at line 129 of 151. I treated the clue as
> non-discriminating and spent my effort on coverage instead of inference.
> Call it a clean sweep rather than a clean deduction.*

It held all 151 rooms in one 13-second pass. A second searcher reached the
same conclusion independently and without conferring: *"the clue does not
discriminate, so it gave me no ranking and I did not invent one"* — and
swept 898. **Two of three abandoned inference, correctly, because there was
nothing to rank with.**

So the live game says what no sweep of `pursue` could: **`WATCH` is the
whole difficulty, and `WATCH` is not enforced.** Every capture rate in this
file was measured against a searcher that watches one room. A real one
watches nine hundred. The coordination premium those numbers were tuned to
maximise is a property of a constraint the game does not impose, and
`REPUTATION_TO_WIN`, `PREP` and `NEAR_KM` are all calibrated inside that
fiction.

**What the clue vocabulary would have to become.** Not narrower for its own
sake: the point is that a descriptor must *rank* candidates, not merely
admit them. *"Somebody made this by hand"* excludes waterfalls and
mountains and nothing else. *"A crown still on the coins"* — the other clue
drawn that day — cuts the world to a dozen countries, and is the shape to
aim at.

### Three holes the run found that no test could

**A searcher cannot tell a finished game from a quiet one.** Reported by
the searcher that swept 898 rooms for twenty minutes after she had already
been caught: *"an empty room and a dead holder produce the same silence, so
'no clue yet' gave me no signal to distinguish a working search from a
broken one -- which is why I kept hardening the mechanism instead of
questioning the premise."*

*Closed by Gal the same day: "she should post a note (without announcing
herself) that the game is over, in every room she's been at."* The close
goes to the lobby **and to every place she robbed**, so a searcher standing
anywhere on her trail is told, and the seed travels with it so the news is
checkable where it lands. The notice also warns that silence is ambiguous
between five states, for the searcher holding a room she never reached --
the one case a broadcast cannot help.

*Measured again the same day, larger and sharper, by the hunt that ran
while the fix was being written.* The campaign closed at **10:36:39** --
caught in Stonehenge by `near`, on **leg 1**, at 0 reputation. A third
searcher, `nordic`, wrote its first target list at **10:45:33**, nine
minutes after the game was already over, and was still holding **809
rooms** when it was stopped at 11:54. Sixty-eight minutes of sweeping, four
holder processes, zero clues found and zero sightings -- not because the
search was bad but because there was nothing left to find, and nothing in
the world could tell it so. Its own report reaches for the mechanism
instead: *"the clue carries almost no discriminating information, so I did
not solve it; I blanketed."*

**One thing in that report is wrong, and it is the operational advice**, so
it is corrected here beside the report rather than left to be followed. It
concluded that *"background tasks are killed at the 600-second cap (exit
144)"* and that *"any long chase needs the holder re-launched roughly every
nine minutes."* Two measurements say otherwise. Its **own** holders were at
`etime` **27:14, 26:27, 20:32 and 12:34** when they were listed and stopped
-- three of the four long past 600s, in the very launch form the claim is
about. And Carmel, restarted the same afternoon as a background task, passed
**653s** still running and went on to leg 2. What the report almost
certainly met is its other finding, which *is* right: a holder started with
`nohup ... &` inside a call dies when that call returns, and its first batch
went that way within minutes. **A cap and a launch bug both produce a dead
process, and the process does not say which.**

The correction matters because the wrong half is the actionable half: a
searcher that relaunches every nine minutes spends its chase on
re-registering, and re-registering is exactly when it is holding nothing.
Re-check it the way it was checked here -- start a long-running background
task, then `ps -eo pid,etime,args | grep at_large` -- and believe the
`etime`, not the report.

That is the first hole measured twice, and the second measurement is worse
than the first in the way that matters: the twenty-minute sweep overlapped a
game that ended partway through it, while this one **never overlapped a live
game at all**. The running build was the lobby-only close (the broadcast
landed at 11:49, an hour after the catch), so `nordic` had no line to read
anywhere on the map. Under this change it would have been told at its first
room on her trail -- though *leg 1* is the case that shows the limit
honestly: a trail one leg long puts the news in one room out of a thousand,
and a searcher who never held Stonehenge or the Grand-Place still learns
nothing. **A broadcast reaches the rooms she robbed, and a short campaign
robs few rooms.** The lobby copy is the only one every searcher can find,
and a searcher deep in a hunt is exactly the one who has stopped looking
there.

**Posting is not announcing, and that is what makes it safe.** `post`
leaves a message; `register` puts you on the roster; only the roster is the
catch. She writes in each place without standing in it again. The tempting
implementation is to join each room properly on the way out, and that
version hands a catch to every searcher still waiting somewhere she has
left -- so `test_she_says_it_is_over_without_standing_in_the_room` requires
her absent from the roster of every room but the last. Registering before
the close reddens it and leaves the broadcast test green, which is the
split that says the two tests check different things.

**The slices leaked into each other.** `nordic` was in **151** of `far`'s
rooms — Egypt, the Levant, Turkey and the Balkans doubly covered — while
East and South Asia, the Americas, Oceania, sub-Saharan Africa and
Scandinavia were held by one searcher between them. That is the
coordination waste the experiment exists to measure, produced in a live
game by comparing rosters, and the division that failed was hand-drawn by
the coordinator. It is only visible *because* presence is public: the one
thing a searcher cannot learn alone.

**The process table is a hole in any directory wall.** `pgrep -af` prints
other searchers' full command lines, heredocs included, so target lists
leak regardless of where the files live. Found by a searcher auditing its
own cleanup, after the catch, against its own interest.

### What is still missing before anybody can actually play

**Where she runs.** This repo publishes a static site; a standing invitation
needs a process that stays up, and nothing here provides one. Until it does,
`--once` from a shell is the whole of her availability.

**Where the address is published.** The three strings above are publishable
and are not yet published — the site (`build_site.py`) shows six simulated
campaigns and says nothing about a live one. That is a page change and a
decision about whether this hub is the one she should live on, which is not
a decision the runner should make on its own.

## The size of the map is a secret, and saying it was the whole leak

*2026-09-10, Gal: "We shouldn't publicize that there are thousand rooms, and
we definitely shouldn't publicize where are the rooms. It's basically a hash
function and could have endless possibilities. So any landmark in the world
can fit."* And then, on whether to grow it instead: *"1000 is a good number,
but it's a secret."*

### What made this urgent, and how much of it was my own confusion

Three claims were made in this conversation before one survived. Recorded in
order, because the two that failed are the more instructive:

1. **"A key holder can read every active workspace."** *False.* No endpoint
   lists workspaces — all twenty take a `workspace` you must already name,
   and `/stats` returns a count. A client holding the same key, sitting in a
   different room, sees an empty roster and no channels. **The key is not
   what hides her; the room id is** — so changing the key, or moving to
   per-room invitations, buys no concealment at all.
2. **"Anyone with the salt can sweep the map without a key."** *False as
   stated.* Every hub read needs the bearer token — raw HTTP with none is
   `401 invalid or missing bearer token` on `/agents` and `/channels`. The
   sweep that "proved" it was silently authenticated by `SWITCHBOARD_TOKEN`
   sitting in the container's environment. **A demonstration that runs in an
   environment you did not audit is not a demonstration**, and this is the
   same disease as a check that is green for the wrong reason.
3. **"A *player* can sweep the map."** *True*, and it is the real one. Every
   player holds the bearer token by definition, the salt arrives in the
   notice, and the names were public. Measured: **227 ms per room on one
   connection, 3.8 minutes for a thousand** — against a leg of about six.
   The hints were decoration.

### The measurement that reframes it

There is **no membership oracle**. A landmark she is not at, a name in no
gazetteer at all, and the right place under the wrong spelling are byte
identical to a prober:

    Stonehenge                       200, count 0, no channels
    Gal's Kitchen Table              200, count 0, no channels
    Uluru-Kata Tjuta National Park   200, count 0, no channels

The hub has no notion of a room existing. So the candidate space is not a
thousand — it is every string anyone can type, and a searcher cannot tell a
wrong guess from a wrong *spelling*. **The only thing that collapsed that
into a 3.8-minute sweep was us publishing the list**, which is Gal's point
exactly and is why the fix is disclosure and not cryptography.

This does not contradict "Presence in a room is public to that room" above —
that is still the hue and is still not a leak to be plugged. What was a leak
is publishing the set of rooms to sweep.

### What was closed, and what was not

**Closed**: the count is out of every player-facing surface — her notice
(`carmel.open_campaign`) and the published site (`build_site.py`, the meta
description and the lede). The notice now reads *"Every famous place on
earth is a room already, waiting to be named"*, which is not a euphemism for
the thousand — it is what the probe above actually shows.

**Not closed, and not closable by us**: `landmarks.tsv` is 999 rows of exact
spellings, committed, in a public repository. The roadmap item
`hue-and-cry-purge-the-leaked-tables` already carries the sentence that
governs this — *"a secret committed to a public repository is not
recallable by the person who committed it"* — and PR refs survive a
force-push.

**Sealing the file now would be theatre**, and the distinction is worth
keeping because it is not obvious: hints and treasures are re-derived from
each game's seed, so sealing them protected every future game. **The names
never change.** A `landmarks.enc` over the same 999 names protects nothing,
and would put a sealed file where a reader would reasonably read secrecy.
`CLAUDE.md`: the weaker thing is allowed, and never allowed to look like the
stronger one.

**What would work is redraw *and* seal**: a much larger pool from Wikidata
(`build_landmarks.py` already builds from it, and the thousand is a cap this
repo chose rather than what the data holds), the playing thousand selected
under a key held outside the repository, plaintext gitignored, `.enc`
committed, and a test that fails if a plaintext map is ever tracked again —
the treasures pattern applied to the map. Its cost is stated rather than
discovered later: **every calibration in this game was swept against this
map** — `WATCH`, `PREP`, `NEAR_KM`, `REPUTATION_TO_WIN` — and the gazetteer
is part of the level key by this document's own rule, so a redraw re-opens
all of them. Not done here, and not started without a go.

## The world is the map, and the chase is not on it

*Gal, 2026-09-11: "Hue and cry: can we show the chase on the map?" -- then,
when the first answer was a survey of options, the two sentences that
settled it: "only landmarks carry coordinates" and "don't have to say
anything to play". Then "I want a world map", and "I don't think we can
show live game".*

Two questions in one, and they have opposite answers. **The chase cannot be
drawn at all. The world can be, and is now the card's main panel.**

### A searcher cannot be plotted, and that is not a disclosure judgement

The first draft of this answer treated "should we draw the searchers"
as a leak to be weighed -- their watched rooms are landmarks she did not
visit, so drawing them hands over samples of the descriptor relation, and
the card's rule is "ask what the picture saves a searcher". True, and
beside the point. **Only landmarks carry coordinates**, so there is no
position in this game that is not a landmark's: a mark for a watcher *is* a
mark on a landmark. It is a contradiction rather than a trade-off.

**And the reverse is worse.** There is no membership oracle -- "The
measurement that reframes it" above -- so a real searcher's guess is a
string, and a string is a room whether or not the gazetteer has ever heard
of it. `Gal's Kitchen Table` has no coordinate. A chase map can therefore
only draw the guesses that happened to land in the thousand, which are the
*near* ones, and it would show the field closing in while most of it was
nowhere near. That is a selection effect drawn as scenery, and it is
`CLAUDE.md`'s "absence drawn as a pass" with a coastline behind it.

### And there is no record of a chase to draw even where there are coordinates

**Searchers say nothing at all**, which is a design decision three sections
of this document rest on. The only event any participant witnesses is
somebody standing in the room she is standing in, and that event *ends the
game*. A searcher who waited in the wrong room, or in the right room an
hour late, was seen by nothing: not by her, since `_leave` takes her off
the roster of the room she has finished with; not by a manager, since there
is not one; and not by the hub, which answers `GET /agents` live and keeps
no durable join log ("What that costs, which is verifiability").

So the pursuit is not data being withheld. It does not exist, and cannot be
reconstructed afterwards. Everything a chase layer could have drawn would
have been `carmel.pursue` -- a *model* of a searcher, which `chase` does not
even return: it keeps `caught_on` and the lags and throws the watched rooms
away. Drawing that and calling it the chase is the weaker thing wearing the
stronger one's clothes.

**The obvious repair is the one thing that must not be built.** Letting
searchers report where they are watching would be a second surface, it
would make silence a disadvantage in a game that deliberately allows silent
play, and -- worst -- it would *pay people to talk*, when the distance
between `alone` and `split` is the only quantity this experiment measures.
Instrumentation that rewards the treatment is not instrumentation.

*Recorded because it has now been proposed twice in one afternoon by the
same person, who was me.*

### What the card draws instead, which is the world

The still card was the campaign's bounding box at a readable scale with the
world as a 232x116 locator in the emptiest corner. It is the same two
pictures with their sizes swapped: **the world, full width, with her trail
on it and a dashed frame round it; and that frame enlarged below, carrying
the stops, the hints and what she took.** The locator inset is gone, since
the panel above it is the thing it pointed at.

    python3 games/carmel-taldiego/trail_card.py --out /tmp/trail.svg

Nothing new was needed to draw it. The locator was already a whole-world
Mercator camera at `scale = its width`; the world panel is that camera at
`scale = WIDTH`, over the same coarse coastline layer the locator used
(52 shapes, 1,958 points, against the detailed layer's 29,949). Decimation
is honest here in a way it was not for the flight, whose level-of-detail
scheme was built and deleted because every zoom closer than the crushed
layer still needs the real one: **a still card never zooms.**

The band is fixed at 75N to 56S and stated rather than fitted, because
Mercator has no poles to draw and a band fitted to the campaign would make
six published cards six different maps -- and a band fitted to the
*gazetteer* would be a statement about where the thousand are. One landmark
of the thousand sits north of it; a campaign that reaches it widens the
band, which discloses nothing her own trail does not.

### The claim that demoted the world had never been measured in pixels

`trail_card.py`'s docstring said a whole-world drawing renders the chase as
"a smudge three pixels wide", and that sentence decided the card's shape for
three days. Over 200 campaigns (`trail_card.py --survey`, which prints these
two rows now precisely so the next claim about a drawing is a measurement):

```
world-scale extent   median 46.2 px   min 0.2   max 288.8
closest two stops    median 11.7 px   min 0.0   max 110.1
```

Legible, and nothing like three pixels; the six published seeds run 14 to
155px. **The extent was never the obstruction.** What does not fit at that
scale is the writing -- a median campaign is a twentieth of the card wide
and one stop's label is 17px on three lines -- and in the long tail, at
nineteen legs, two stops land on the same pixel. Both are answered by an
enlarged panel and neither by a bigger world map, which is why this is two
panels rather than a choice between them.

*Measured twice in one sitting and it moved both times.* The first run said
106.8px and 2.9px over campaigns of 13 legs; then #264 made the hint a
riddle, campaigns fell to a median 2.5 legs, and the same command said
46.2px and 11.7px. Neither is wrong. **Campaign shape is downstream of
every parameter in `carmel.py`** -- "Framing it found the thing the numbers
had not said" has said so since the third time, and this is the fourth, so
what the card's shape rests on is the command and not the digits.

Note what the wrong diagnosis cost: it was not that the card was bad, it
was that **a fixable problem was recorded as a physical limit**, and a
limit is not something anybody re-examines. The number that would have
caught it -- pixels, at the width the card is actually drawn -- took four
lines to measure and nobody had run them.

### Drawing the world found two defects, one vacuous test, and a broken command

**A leg across the antimeridian was drawn back across the Atlantic.** `fit`
has unwrapped the *stops* since the card was written -- there is a test
named for it -- and nothing was unwrapping the line between them. Invisible
while every campaign was European, and unmissable on a world panel. `laid`
now unwraps the polyline and emits it at every turn of the world the frame
can see, which is one path usually and two for a leg that leaves one edge
and arrives at the other.

**The leaders joining labels to pins were invisible.** They were drawn in
`INK["rule"]`, the chrome's hairline, which is darker than both the land
and the sea it has to cross. Every test about label placement passed --
they were placed correctly -- while on screen half the labels floated free
of the trail with nothing to say which room they were about. At three stops
nobody noticed; at eighteen the card stops being readable. The new
`INK["leader"]` is asserted to out-luminance the land, the sea and the
card's ground, which is a check that can go red for the reason it names.

**And the file's own command was broken on `main` and nobody had typed
it.** #264 renamed a leg's `hint` to its `details`; `card` was updated and
`main`'s summary print was not, so `trail_card.py --seed ...` wrote the card
and then died with a `KeyError` -- the command this module's docstring hands
a reader, failing on every run, with the whole suite green because every
test in it calls `card()` and none called `main()`. Found by running it.
Fixed here rather than filed, since it is a line in the file this branch is
already rewriting, and `test_the_command_in_the_docstring_runs` now runs it
as a subprocess so the script path has a check at all.

*And its other half was named after a seed, which lasted about an hour.*
The same test asserted that a card *draws* a leader, on a seed that drew
ten of them -- until #264 landed, campaigns fell from eighteen legs to two,
no label had to move, and the assertion went green over a card with nothing
to join. The seed is searched for now, and finding none in forty-eight is a
failure rather than a pass. **A test named after a seed is a test named
after a campaign shape**, which is the one thing in this game nothing may
be named after.

**And the caption test was green over an untaken branch.** The span caption
sits beside the frame and flips to the other side when it would run off the
card; disabling the flip left the test passing, because on every seed the
file draws she stays left of centre. The frame that exercises it is built by
hand now rather than hunted for in a seed. `CLAUDE.md`'s third shape, found
by the habit the same file prescribes: break it on purpose and watch.

### And the flight opens on the world and ends back out at it

*Gal, 2026-09-12: "do the flight too."*

    globe   the whole world, and a box round the corner she stays in
    fade    a dissolve, not a zoom
    ...     the holds and the flights, as before
    fade    back out
    globe   the same box, with the whole trail drawn in it

**The dissolve is the whole reason the shots are affordable**, and it
answers the objection that killed the level-of-detail scheme rather than
ignoring it. That scheme failed because any zoom close enough to be honest
still needs the detailed coastline, so a crushed layer pops when it is
swapped in mid-move. A cut makes no claim about the ground in between:
there is no zoom at which both layers are on screen. So the world shot is
the coarse layer — 1,958 points, 4% of the map, the same layer the card's
world panel uses — and the flight keeps its clipped corridor, and neither
is ever a lie about the other. `test_the_flight_itself_never_sits_at_world
_scale` is what stops that quietly ceasing to be true.

**The opening shot shows the box and not the trail.** Where, not what — a
film that opens on its own ending is not a film, and the trail has not
happened yet. It is also the one thing about these shots that a test can
see going wrong, so it has one.

The reduced-motion reader now lands on the closing world shot instead of
the closing corridor shot, which is strictly more of the answer in one
frame: the whole trail, and how small a corner of the world it happened in.

### And a chase you win is a link she hands you

*Gal, 2026-09-12: "at the end of a chase, if you catch her, your agent can
give you a link to a website that shows your chase animation."*

**Her post is the only place it can come from, and that is the design
rather than a shortcut.** A searcher's agent never saw where she went --
only where it stood, which is the whole of "A searcher cannot be plotted"
above. So "your agent gives you a link" reduces to an agent passing on what
she published, and what she publishes on a catch already includes her whole
run: `close_campaign` hands over the route, the treasures and the seed,
because *"being handed the run is the prize for taking her"*. The link is
that same prize, drawn.

It goes out on a catch only, like the table it sits under. She got away, she
owes nobody a film.

**The chase is in the address, and the page is static.**
`trail_flight.link` gzips the plan into the fragment; `trail_flight.viewer`
is the built flight page with no chase baked into it, published by
`build_site` at `/carmel-taldiego/chase/`. Nothing after the `#` ever
reaches the host, so the link works forever, costs nobody a server, and no
one is told that anybody watched.

Three things come out of the payload because the page can get them for
itself, and none of them is a fact about the chase:

| | | |
|---|---|---|
| the geometry | the world is the same world every time | `chase/basemap.js`, ~790 KB, cached once across every chase anybody is sent |
| `centres` | it was a second copy of `path` in unit space | a division |
| most of each arc | `LINK_POINTS = 28` of 65 | tens of kilometres per segment on a camera showing hundreds |

What is left is 1 KB of address for a chase that ended in two rooms and
about 7 KB for the longest in the published six. Before those three, the
long one was **45 KB**, which is not a link, it is a file with a colon in
it.

**The third seed-shaped test in one branch.** The ceiling above was first
asserted over three named seeds, every one of them a two-leg campaign under
the riddle -- so raising `LINK_POINTS` to 9,999 left it green. It searches
79 seeds for the longest campaign now and fails if none is longer than
eight. That is the same defect as the leader check earlier in this section
and as `test_the_command_in_the_docstring_runs`'s absence: **a check named
after a seed is a check named after a campaign shape**, and campaign shape
is the one thing in this game that moves under every parameter.

### What it costs, stated rather than absorbed

```
card, vectors only     148 KB -> 167 KB      (+ the coarse world)
card, with imagery     675 KB -> 889 KB      (30 -> 43 NASA tiles)
published site         1.1 MB -> 1.2 MB vectors, 3.7 MB -> 4.9 MB as deployed
   and, with the chase viewer and its copy of the map,      -> 5.8 MB
```

**The deployed figure is the one that counts** and is a third more, since
`pages.yml` builds with `--imagery`: the world panel is a photograph of the
whole world and there is no cheap way to be that.

One seed, the longest of the published six, measured in a worktree at
`origin/main` beside this branch rather than remembered. The world panel
fetches its own tiles at zoom 2 -- thirteen of them, one turn of the world
at 1024px, the zoom that matches the width rather than a stretched one. The
card is also about 500px taller. Both are paid for a panel that is most of
what a reader now looks at, which is the trade being made and not an
overrun.

### What it still refuses, and the one thing it newly says

Unchanged, and now checked over two panels rather than one: **no landmark
is named but the ones she visited**, and the count of plotted points is
asserted exactly -- two per stop, one per panel, plus the ring on a catch
-- rather than as a ceiling, because a ceiling met by coincidence is how
the locator's circle hid in the slack the last time.

**What a world map newly hands a reader is the scale of her near-bias.**
Six cards all staying inside one region draws `NEAR_KM` at about 2,500 km,
where before it was only stated. That bias is public on purpose -- it is
the only public term in her score, and it is what makes watching a skill --
so this is consistent rather than a leak. It is written down because it is
the first time the magnitude is *shown*, and because "the data is public"
is the sentence this document has twice caught itself hiding behind.

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
   asserted. **Started**: `games/carmel-taldiego/worked_example.py` holds an
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


## One fact is a category; three are a riddle

*Decided by Gal, 2026-09-11, and this is the section the standing decision
at the top of this file now points at.*

The complaint came first and it was about a live game: *"The hints are
terrible, I never could have guessed it."* The measurement agreed, and it
was worse than the complaint.

| what a searcher was handed | landmarks left standing, of 1000 |
|---|---|
| the detail she actually posted | **median 156** |
| the sharpest of her three live details | median 77 |
| a uniformly drawn detail | median 113 |

She was posting the **vaguest** of the three by design -- `choose_hint`'s
*"post the least informative true fact"*, which was a real optimisation
against a real posterior when a candidate set meant her five exits, and
which outlived its denominator when Gal deleted routes on 2026-09-09.
Against a thousand landmarks, maximising vagueness picks 156 over 27. **A
strategy calibrated in one world and left running in another is this
repo's most reliable way to produce a number that is still computed, still
tested, and no longer means anything.**

### The specification, which is about reading and not counting

> hint should fit a few locations only, not many. it should be hard not by
> revealing one assertion, but from a few details that can relate in
> different ways but when they do there are only a few results. that is,
> the search is over possible meanings to the words of the riddle, not on
> possible landmarks to a fact

And, separately and firmly: *"don't tell the searchers anything, not even
the bias. nothing. they only get one signal - the hint."*

That second instruction corrected **the apparatus and not the game.** Her
notice never disclosed the near bias -- it says the opposite, *"there is
nowhere I cannot have gone from here"*. The bias leaked through the
briefings the searchers were given by hand, which is the same class of
error as the `carmel.log` left in their working directory: **the game was
clean and the harness around it was not.**

### What the vocabulary can do, measured before anything was built

Intersecting details, over every combination each landmark carries:

| details | median candidates | pins to exactly one |
|---|---|---|
| 1 | 156 | -- |
| 2 | 16 | 2.5% |
| **3** | **3** | 23.7% |
| 4 | 1 | 53.8% |

Three is the number, and the 23.7% is not a blocker because **she
chooses**. `live_hints` already handed her exactly three per place, so she
posts all three, and drops one when three would name her outright. Two
seeds: that fires on 22% and 24% of moves and leaves **no pinned move at
all** -- which is why `RIDDLE_FLOOR` is a rule she obeys per move rather
than the statistic `MAX_PINNED` held over random draws. A stronger
guarantee than the one it replaces, not a weaker one.

End to end: **median 4 candidates, 89% of legs between 2 and 12, zero
pins.**

### The vagueness term was rebuilding the routes Gal deleted

`choose_destination` weighted every candidate by `best_cover` -- how much
of the map her hint there would leave standing. Harmless-looking, and with
a riddle it sends her to places that **share descriptors** with where she
stands, which is precisely the look-alike band `band()` drew her five exits
from before routes were deleted. `test_there_are_no_routes` went red on it:
every hop inside the band.

That check was written in September to catch somebody reintroducing
`exits()`. It caught a weighting term instead, in a change nobody wrote it
for, which is the whole argument for a check that names a property rather
than an implementation. The term is gone and `best_cover` with it; it was
also costing the riddle most of its point (median 21 candidates with it, 4
without).

### The voice is Mixed, and a frame may never reword a clause

Gal, choosing between a pure dossier and a pure note: **"Mixed"** -- her one
line, then two reports from people who saw her.

    One true thing, then: the place had been a town once and nobody has
    lived in it since.
    STATEMENT. A postal sorter, who has no reason to invent it, says the
    wire came up through South America.
    HEARSAY. A bookseller told it to somebody who told us. The moon was the
    wrong way up.

    -> Machu Picchu, Tiwanaku, Valongo Wharf

Every frame quotes its clause **verbatim**, and that is a correctness rule
rather than a style one: a frame that reworded a clause to fit her grammar
would be the system inventing a sentence, and an invented sentence is one
nobody checked for truth. *She may lie in prose. She may not lie in a
clue.*

Three of the 73 descriptors have no clause she can speak in the first
person -- every clause in their bank describes her from outside -- so for
those she speaks a different detail and lets a witness carry that one.
Which clauses those are is **derived and not listed**, per `CLAUDE.md`: a
hand-kept list would drift the first time somebody wrote a new clause.

Two reports drawing the same frame read as one voice repeating itself, so
the second steps to the next frame -- a walk as fixed by the seed as the
draw was.

### What it cost, and the invariant that had to go

Every constant in this game was calibrated against a hint leaving 156
candidates. At 4 she is caught on the first or second leg:

| | median campaign |
|---|---|
| before | over 48 game hours |
| searcher ranking candidates by distance | **6.2 game hours** |
| searcher told nothing at all | **11.9 game hours** |

`REPUTATION_TO_WIN` is **not** the lever -- swept at 750, 1500, 2500 and
4000 it moves the median by nothing, because she never lives to spend it.

Gal: *"10 minutes is great"*, and then the correction that settled it:
*"The game time is less important. First I'd make the real world time
seconds to minutes per riddle."*

So the unit changed. `test_the_notice_dies_long_before_the_campaign_it_announces`
asserted a **ratio between two game-time quantities** as a proxy for *"her
lobby message is long gone before the game ends"*; the proxy held while a
campaign ran for days of game time and cannot hold now, since a quarter of
campaigns end inside forty seconds. What it was standing in for -- never
two salts legible at once -- is held by the floor in `plan`, which does not
depend on the notice length at all and is tested separately.

It is replaced by the thing actually asked for, in the unit asked for:
**what one riddle is worth in real seconds.** The window is her packing,
her theft, and her packing before the next leg -- the same three stretches
`pursue` counts -- and it measures **median 6.6 real minutes, range about
2 to 12**. `NOTICE_TTL_HOURS` stops being a ratio and becomes a join
window, sized in real minutes for a person who has to read a notice and
join a room.

Both new checks were made to fail on purpose: `HOUR_SECONDS = 6` reddens
the lower bound, `600` the upper.

### Still open

**A searcher solves the riddle instantly, in the simulation.** It reads the
details, intersects them and is standing in the room. That was harmless
when enumeration dominated; with a riddle whose whole difficulty is
*decoding*, a solver with no think-time is modelling something that does
not exist -- and it means the quality Gal asked for is the one quantity the
numbers cannot see. Every capture rate here is therefore a **floor**, and
should be read as one until a solve time exists.


### The notice is not an invitation, it is the key to the map

*Corrected the same afternoon, hours after the section above was written,
and by a searcher rather than by a test.*

Sizing `NOTICE_TTL_HOURS` in real minutes was right. **Sizing it as "a join
window a person could use" was not**, and the mistake is one word: it
treats the notice as an *invitation*, which has done its job once somebody
has joined. It is not an invitation. **The salt is inside it and nowhere
else**, and every room in the game is computed from that salt -- so the
moment the notice expires her riddles go on arriving and name places nobody
can derive a room for. The notice is the key to the map, and a key has to
last as long as the door.

Cut from 12 to 2, it was caught within the hour, live: a searcher joined a
campaign two minutes in, found a riddle and no salt, and could do nothing
with it. **A two-minute window onto a game that then runs for ten.**

So 12 goes back, and the test that asserted `60 <= window <= 600` is
replaced by `test_the_salt_outlives_the_campaign_it_belongs_to`, with the
superseded assertion quoted inside it. Red at 2h, green at 12h.

**What this is an instance of.** The 12 was not a leftover from the
long-campaign era waiting to be tidied; it was holding a property nobody
had written down, and it was removed by someone who could see what it cost
and not what it bought. The same shape as the `best_cover` term two
sections up, and the opposite outcome: there a check existed
(`test_there_are_no_routes`) and caught the removal in seconds; here no
check existed and a person hit it in production. **The difference between
those two outcomes is entirely whether somebody had written the property
down as a test**, which is the argument for this file and for every "made
to fail on purpose" note in it.

Two properties now have tests they did not have this morning: the salt
outlives its campaign, and a riddle is worth real minutes. Neither was
controversial. Neither was written down.


## Caught, she talks

*Gal, 2026-09-11: "If she's caught she should disclose her catcher and her
route, what she stole and her reputation."*

The close used to give counts -- *"6 places. 6 of them the poorer for it.
367 to my name"* -- and the seed. Everything else was derivable and nothing
was handed over. It reads as a scoreboard, and what a catch deserves is an
account:

    It is over. You have me.

    It was Gal searcher who had me, in Great Himalayan National Park.

    You will want it written down, so here is the run of it,
    in the order I lived it:

         1  Sagrada Familia                 +60  the finished part
         2  Mir Castle Complex              +51  the portcullis
         3  Baalbek                         +71  the site notebook, which was worse than the finds
         4  Shahr-e Sukhteh                 +53  the finds tray, and the labels with it
         5  Taj Mahal                       +99  the reflection in the long pool, taken and not returned
         6  Great Himalayan National Park   +33  the plan the whole thing was laid out from

    6 places. 6 of them the poorer for it. 367 to my name, and worth
    every hour.

**Only on a catch.** Retiring on the proceeds is not an occasion for
handing anybody her itinerary, and `test_she_hands_over_nothing_when_she_was_not_caught`
is what makes that a rule rather than a habit -- remove the `caught_by`
gate and exactly one of the pair goes red, which is what says the two
check different things. The seed is in every ending regardless, so nothing
is concealed either way: the difference is between a reader **deriving**
the run and being **handed** it, and being handed it is the prize for
taking her.

**Nothing in the ledger is truncated, and the first version truncated it.**
A fixed-width column clipped *"the site notebook, which was worse than the
finds"* to *"the site notebook, which was worse"* and *"Great Himalayan
National Park"* to *"Great Himalayan National Par"*. A treasure here is a
written phrase and sometimes a whole sentence, so **"what she stole" was
the half of the instruction the column was throwing away** -- which is a
small instance of a habit worth naming: a format chosen for the common case
silently drops the content in the tail, and the tail is where the writing
is. The column width is derived from the names in the trail instead, and
the test asserts each treasure appears **whole**.

**Four things, checked separately**, because three of four appearing is the
realistic failure: the route was the easy part to add and the treasures
were the easy part to leave out.


## Two lines of her notice that had drifted

*Both fixed 2026-09-11, and neither was a design decision -- they are prose
that stopped matching the code underneath it.*

**It claimed the close was lobby-only.** The sentence read *"She posts the
end of the game here and nowhere else, so a searcher who leaves and never
looks back cannot tell a finished game from a quiet one."* True when
written; false the moment the close began broadcasting to every room she
robbed. **A notice that understates where the news reaches is the exact
failure the broadcast was built to fix, restated in her own prose** -- a
searcher reading it would have had no reason to look for the ending
anywhere but the lobby, which is the behaviour that cost 809 rooms and 68
minutes.

**And it printed the first riddle twice.** The notice inlined it and the
runner posted it again in the same room, so the lobby showed it in
duplicate -- harmless when a hint was one phrase, a visible stutter now
that it is three lines.

**Which copy to drop was the only real decision, and it was nearly the
wrong one.** The obvious move is to stop the runner posting a riddle into
the lobby, since the notice already carries it. That is backwards: the
notice lives `NOTICE_TTL_HOURS` and the post lives `HINT_TTL_HOURS`, **ten
times longer**, so dropping the runner's copy would have quietly cut the
first riddle's life by a factor of ten and left latecomers unable to start
the chain at all.

That is the salt's lesson arriving a second time inside a day: **a value
doing load-bearing work inside a message that looks like a formality.**
The difference is that this time it was checked before the change rather
than after a searcher hit it, which is the only thing that made it cheap.

`test_the_notice_says_where_the_close_lands_and_says_it_once` pins both,
and fails on purpose when either sentence is restored.
