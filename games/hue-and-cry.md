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

```
100  11h  Vatican City    the keys
  5   1h  Cheyenne Mountain Complex   the signboard at the gate
```

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

## What would have to be built, in order

Nothing here exists yet. The order is chosen so that the piece most likely
to be wrong is the piece built first, which is why the island built its
grammar before its pages.

1. **The gazetteer and the settler.** A committed table of attributes *and
   exits*, and a pure function from a board transcript to a settled outcome:
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
