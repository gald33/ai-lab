# The island — a spectator's view

A game surface over a 005 round. It changes nothing about the experiment: it
reads, it never writes, and it never reaches a hub.

```bash
switchboard-viewer                 # in the checkout that coordinates (for live)
python viewer/serve.py             # → http://127.0.0.1:8790
```

Replays need nothing running but `serve.py`. Live needs the Switchboard viewer
too, and reads it rather than the hub.

![the island, mid-trade](docs/island.png)

## What it draws, and what it refuses to

**Only what the manager said.** A trader writing `PRODUCE bread=0.5` has
attempted something; the shelf changes when `@T1 produced {'bread': 0.44}` comes
back. Self-reports are not authoritative in the experiment and they are not
authoritative here — attempts show in the ticker, receipts move the island.

**Not tastes, not capacities — not live.** They are private to each trader and
never appear on the board. A spectator page that drew all four hut interiors
during a round would know more than any player does, and what it showed would no
longer be the game the traders are playing. So the live page shows stocks,
offers, trades, refusals and the bell, and says out loud that the rest is
hidden. The hidden half is regenerated from the round's seed **afterwards**, by
[`reveal.py`](reveal.py), and appears only in a replay.

**Nothing it does not recognise.** A manager line that does not parse is counted
and shown as text, never repaired into a plausible receipt. If the manager's
wording changes, the page goes quiet about that line and says so — the same rule
the manager itself follows about malformed messages.

**No metric it computed itself.** `eff_round`, the per-episode efficiencies and
every trader's utility trajectory are the manager's, read from the recorded
round. A page that recomputed the metric would be a second implementation of it,
and the two would drift.

The one number the page does derive is the **card's utility while an episode is
running**, because no such number exists in the record — the manager scores at
the bell, not continuously. It is Cobb-Douglas over the revealed tastes and the
rebuilt shelf, and `audit()` puts it against the recorded trajectory at every
bell in the exact code path that draws the island. Agreement is reported in the
rail; disagreement says the *drawing* is wrong, not the score.

| on screen | what it is |
|---|---|
| a hut and its card | one trader; the card is the only part carrying information |
| four bars, fixed order | stock, from production and settled trades |
| the pale part of a bar | promised to an open offer, so not offerable again |
| the labour wheel | share of this episode's labour spent, from the receipt |
| a pill sliding down a rope | an offer being carried from the trader who made it to the trader it is addressed to |
| a pill waiting over a hut | an open proposal, with what it offers for what, standing on the trader who has to answer it |
| a stack of pills on one hut | every open offer that trader has to answer, oldest at the bottom |
| a pill blinking green, then gone | the offer settled |
| a pill blinking red | the manager would not settle it; the offer is still open |
| a rope blurring and coming apart | the bell took the offer with it, unanswered |
| goods in flight | a settled exchange, both directions at once |
| a card washed dark red | holding some goods and none of another — a zero episode |
| nightfall | the bell: proposals lapse, stocks and labour are eaten |
| the pink bar | replay only — what the shelf is worth to the trader who owns it |
| the tick on it | what autarky would have given them: the line worth beating |

## The three feeds

**Live via a local viewer** reads the Switchboard viewer's `api/state`, never
the hub. The viewer holds the token, the key and the read cursors, so this page
inherits its safety properties — it cannot post, cannot register, and cannot
advance any agent's cursor. `serve.py` forwards `api/state` so the two share an
origin, which they must: `api/state` sends no CORS headers, so a page served
from anywhere else cannot read it at all.

**Live from the hub** reads a room the same way the *published* Switchboard
viewer does — sealed content opened in the browser, nothing trusted with a
key but the tab it was typed into. `feeds.js` imports `snapshot()` straight
from `https://gald33.github.io/switchboard/switchboard-room.js` rather than
reimplementing it, which is also why it works cross-origin: that file is
published with `Access-Control-Allow-Origin: *`. Point it at a room with
`?workspace=…&key=…` (defaulting `hub` to the managed hub) or one string —
`?invite=swb1_…` — the way an invite is meant to arrive. Neither is ever put
in a link this page hands out itself: a workspace and key are read-write
credentials, and advertising them in a spectator link would be handing out
write access along with the view (see `games/island.md`, "An invite is a
read-write credential" — open, not yet closed).

**Replay** reads a saved board — `board-*.json`, `{seq, at, author, body}` —
and its sidecar if one exists. Boards come from every tree named in
`serve.py:ROOTS`, each served under its own URL prefix: `results/` is this
experiment's, `replays/` is `games/replays`, where a finished game's board is
kept on purpose so it has a link after its Switchboard room is gone. The page
never learns which tree a board came from. Transport, scrubbing, episode chapters,
1×/4×/16×. Silence is compressed (a 60s gap between two messages is not 60s of
still picture) and the pause is labelled rather than hidden.

## The island is a model

The scene used to draw the island: a wobbled ellipse, palms placed to miss the
cards, a hut per trader as a roof and a wall. It is a **three.js model** now,
rendered to a canvas behind the page — terrain, a market at the centre, a
settlement per seat, a site per good, a dock and boats. Ported from a design
delivered as `island.html`; `island3d.js` holds the geometry and `stage.js`
puts it under the scene.

Two things about it are worth knowing before changing either.

**The camera is orthographic, and that is not a style choice.** The cards,
ropes and sun are SVG drawn in viewBox coordinates. Under perspective, the map
from the island's ground to those coordinates depends on the viewport's aspect,
so a hut and the card belonging to it drift apart when the window changes
shape. Orthographic makes that map affine and viewport-independent, which is
what lets a settlement stand exactly beneath its own card.

**The settlements are placed on the screen and dropped onto the ground.**
`seatSpots()` decides where traders go in the frame, `Stage.groundAt()` turns
each into a point on the island, and the card goes back at `toViewBox()` of the
hut. Placing them on a ring in island coordinates was tried first and put both
huts on nearly the same pixel — the ring's axis and the camera's happened to
line up. A spectator does not care which compass point a hut is on.

**Without WebGL the page draws the island as it always did.** `.has-3d` is set
only once a model is actually up, so the drawn world is hidden exactly when it
has been replaced. `tests/render.py:fallback` takes WebGL away and checks the
drawn island comes back — that path is not otherwise exercised, and its failure
looks like a replay that will not load.

three.js is **vendored**, not fetched: see [`web/vendor/three/`](web/vendor/three/).

## A day, not an episode

**In the game an episode is called a day** — the round state, the chapter menu,
the closing card, the scoreboard's levels. It is a presentation name: the
manager still writes "episode" on the board, so the transcript quotes it that
way, and `eff_episode` keeps its name in the metric panel because that is what
the ledger records. Renaming either would change what agents read or what the
numbers are called. `tests/render.py:vocabulary` holds the line in both
directions — the game's own voice says day, and the transcript still says
episode.

## The shadows tell the time

**With a model up, the disc is hidden and the island's own shadows say what
hour it is.** A drawn sun over a lit island is the picture saying it twice, and
the drawing was the half that could disagree — it crossed the sky while the
model's key light cast nothing at all, so the island had a sun in it and no
shadow under anything. The key casts now (`shadowMap`, an orthographic shadow
camera six units either way, which is the island and none of the sea), and
`.has-3d .sun` takes the disc away.

**The light's angle is reckoned from the camera, not from the island**, because
the camera goes right round the island every 150 seconds. A key at a fixed world
bearing would hold its shadow due north-west all day and let the camera sweep it
across the frame — so the shadow a person reads would be telling them the
bearing rather than the hour. `Stage.ctx()` passes `turn` along with `day`, and
`island-life.js` adds it straight back into the light's azimuth, which cancels
the revolution. What is left is the day: over one shoulder and long at the open,
behind the viewer and high at midday where the shadows are shortest, over the
far shoulder and long again by the bell.

**A cloud's shadow goes with the light.** The clouds cross the meadow on their
own loop and drop a dark patch under themselves, and that patch used to be the
same darkness at the bell as at midday — while the key had swung almost to the
horizon and every other shadow on the island had gone long and soft, so the one
hard dark patch left on screen was the only thing still claiming it was noon.
It now fades out with the sun and comes back with it, on `sin(π·day)` rather
than on `day`, because "the sun is up" and "it is late" are not the same curve:
the sun is up at dawn too, and casts almost nothing.

The disc is hidden with `visibility`, not `display`. It is still the clock the
**fallback** island has — the one drawn in SVG when there is no WebGL — so it
stays where it stands and both paths remain one path with one arc in it.
`daylight` and `alive` read the day off its position, which is what a viewer of
the fallback reads it off too.

### The model's light travels too

**The glide belongs to both suns, not just the drawn one.** `sky()` is handed
where the day is now and where it will be when the next line lands, and it
animates the disc across the gap so a silence looks long. The stage got only
the first of those — `setDay` was called once per board event with the
instantaneous fraction — so the island's shadows stepped to wherever the last
event fell and froze there. On a 3D board that is the *only* clock a viewer
has, because `.has-3d .sun` hides the disc that would have shown the rest of
the day.

Reported by eye against `island-game-001d-g1`: shadows walking to the middle of
the day and stopping while the board went on producing and trading. The board is
not at fault — every line on it settles before its bell — and the middle is
simply where that day's last event falls (0.38, 0.84 and 0.69 of the three
days). `setDay(day, until, ms)` now takes the same two ends of the same journey
and `Stage.dayNow()` reads the light off it per frame. It never travels
backwards, for the same reason the disc does not: a new day is a jump, not a
rewind.

### A hold is a level of night, not an hour

A clip that wants the island dark says so with `life.hold(v)`, and that value
used to *be* the day for as long as the clip ran. The day owns the key's
bearing as well as its brightness, so the dawn clip — which holds a night
lifting from `1` to `0` over four and a half seconds — dragged the sun
backwards through a whole day and swept every shadow across the island at the
moment a new day **opened**. Reported by eye as shadows crossing the island at
the start of a day, in the dark.

The hold is spent on the light *level* now — how bright, how warm, how high the
fire — and the bearing stays on the page's clock. The bell loses nothing: the
day is already at dusk when it rings, so the shadow is where the hold would have
put it anyway. The dawn gains what the drawn disc always had — a jump, made
under cover of the night still being drawn over it.

### The arc it keeps

An episode is a day, so the day is readable from the sky. The sun crosses on an
arc from the open to the bell, and during a replay it keeps travelling while a
frame is held on screen — so a stretch where nobody acted *looks* long, in the
one part of the page that is about the island rather than about the player.

It replaces a pill that read `quiet 41s`: a number about the replay, next to a
sun parked in one spot for the whole episode.

**Nothing else moves the sun.** The bell brings the night and lights the fire;
it does not touch the disc. The sun was already almost down when the bell rang
and it goes on down past the horizon on the same clock, so an event animation
starts at its own moment and runs alongside rather than taking the day over and
restarting it. The one discontinuity is the night itself — the sun sets in the
west and the next day rises in the east — and it is invisible because the disc
is at zero opacity at both ends of it: a day begins with the sun still out of
sight and it comes up out of the sea.

The arc is bounded by the island rather than by a constant. It rises and sets
beyond the island's width, where there is only water, and clears the island's
topmost point at noon — the sun is drawn *behind* the land so it can set behind
it, so an arc dipping below that edge would take it through the island at
midday. `scene.test.mjs` holds both properties at every trader count and in both
orientations.

**The bell had no date.** The manager writes *"the bell is at 12:42:27Z"*, which
`Date.parse` cannot read, so everything comparing it to a clock got `NaN` and
quietly did nothing — the live countdown read "bell due" from the first second
of every episode. The date now comes from the timestamp of the line that
announced it, and a bell earlier in the day than its own announcement is
tomorrow's.

## On a phone

The page is a link you hand somebody, and most people open a link on a phone.

The island's viewBox is wide, so upright it used to fit to width and sit as a
thin band — **16% of the screen** — with dead sky above and dead sea below,
and the trader cards at about a third of a readable size. In portrait the huts
**stack in a column** and the viewBox goes tall with them; nothing else about
the scene changes, because everything is positioned from `seats`, `ly`, `rx`,
`ry` and `fire`, and `fits()` holds the geometry honest either way. Rotating
rebuilds it through the same `build()` — one construction path, run again.

The floating chrome re-stacks rather than being dropped: the title gives way to
the picker and the tab, the counters and the legend take rows of their own, and
the transport gives the scrub a full-width row so it is long enough to drag.
Controls get a 40px minimum under `pointer: coarse` — a tablet is neither
narrow nor short and is still touched.

### The chrome has a band, and the island stays out of it

Re-stacked, the pills are **four rows deep**, and they floated over the picture:
the round's state, the counts and the goods key all lay across the island's top
edge, over the shore and the hill. Reported by eye, twice.

The stylesheet declares what they come to — `--chrome-top: 162px`,
`--chrome-foot: 146px`, beside the rules that put them there, because that is
the one place that knows how tall four rows of pills are. `chromeBands()` turns
them into fractions of the window's height and `cardPlan` reserves them. What is
left is the island's, and **the island is the term that gives**: the cards carry
every number on the page and shrinking them is how this view was unreadable to
begin with.

That reservation rests on the portrait frame being **the window's own shape**.
A viewBox of any other shape is fitted inside the window with `meet` and
*centred* in whichever direction is slack, so a band at the top of the viewBox
would land somewhere in the middle of the window and reserve the wrong strip.
So `layout` sizes its own height from the aspect, and `frameAspect` rounds
portrait to hundredths and **downwards** — erring tall leaves the slack across
the width, where it is a few pixels of sea, instead of down the height, where it
would be split above and below and move every band.

The arithmetic is honest about what it costs. On a 393×660 window — a shared
link opened with the browser's own bars showing — the chrome and one row of
cards are near half the height between them, and the island is drawn small. That
is the deliberate side of the trade: it was bigger before because it was drawn
underneath the pills. So the size check no longer asks for a share of the
*screen*; it asks whether the island filled **the band it was given**, which is
the defect the check was written for — dead sky above it and dead sea below.
`island()` re-measures the silhouette off the model's own vertices at twelve
bearings and fails if it climbs into the chrome's band; `uncovered()` counts the
model's pixels behind every pill.

`tests/render.py` drives seven viewports and checks what a screenshot cannot:
that nothing scrolls sideways, that **no two pieces of chrome overlap**, that
the island fills the band between the chrome and the cards, that every control
is a fingertip tall, that rotating actually turns the island, and — in
`focusing` — that a tap re-divides the frame and a second tap puts it back. The overlap check exists
because that bug happened twice while these breakpoints were written — once
because a media block was authored above the rules it meant to override and
lost on source order, which no amount of reading the CSS made obvious.

### The viewer says which of the two gets the screen

The section above ends by conceding that on a 393×660 phone the island is drawn
small and calling it the deliberate side of a trade. It is, and it is still not
comfortable. **Neither of them is.** At `even` on that frame the island draws
198px wide in a 393px window and a card 147px, with its quantities at 8.3 device
pixels. There is no arrangement that fixes that: the room is not there.

So it stops being the layout's call. **A tap on the island gives it the screen;
a tap on a card gives it to the cards; a second tap on the same thing gives it
back.** The whole mechanism is one number — `FOCUS` in `scene.js` scales the
cards, and `cardPlan` already sizes the island as the *residual* of the band the
chrome left, so the island moves by construction and there is nothing else to
move.

Measured on 393×660, two traders:

| focus | card scale | card, drawn | island, drawn | of the window |
|---|---|---|---|---|
| `island` | 0.55 | 81 × 46px | **385px** | 98% |
| `even` | 1.00 | 147 × 139px | 198px | 50% |
| `cards` | 1.19 | **174px** | 165px | 42% |

**The asymmetry is the frame's, not a choice.** The cards run out of *width*
long before the island runs out of *height*: two to a row on a 520-unit frame
allows `1.19×`, while the height freed by taking the island all the way down to
`ISLAND_TINY` would allow `1.63×`. A card focus that shrank the island further
would buy nothing at all.

Two things fall out of that arithmetic and are worth stating, because both look
like bugs from the outside:

- **The island is capped at the frame's own width.** The land spans exactly its
  box, so a box wider than the frame is an island with its shore cropped. On a
  *tall* phone — 390×844, a browser with no bars showing — the island is already
  at that cap at `even`, and tapping it only clears the cards away. That is the
  honest answer, not a dead tap.
- **The frame's height is settled before the focus is**, off the card the layout
  would have drawn had nobody chosen. A focus that moved `H` would change the
  frame's *shape*, and the shape is the whole reason the chrome's bands land
  where the chrome is — so a tap on a card would have walked the pills back over
  the island. A tap re-divides the band; it never resizes it.

#### Screen wide, and where the room came from

The first version of this reached **70%** of the window and called it a gain,
which it was. It was not what was asked for. And no card is small enough to
close the gap: on a 393×660 window the island needs 452 units of an 881-unit
frame to be 520 across, the gap to the cards takes 16, and the two chrome bands
leave 469 — so the cards would have to be **one unit tall**. Shrinking them
further was never going to do it.

The room has to come off the chrome or not at all, which is what the size check
had been saying all along: *"the answer then is to take room back off the chrome
rather than to move this number."* So at the island's focus two of the four
stacked rows stand down — the counters, and the goods key — and `--chrome-top`
drops from 162px to 96px. What stays is the controls and the round's own state,
which is a caption on the island rather than a tally beside it.

**The goods key is the real cost**, because it is what names the colours of the
boxes standing in the yards. It is paid because the glance card carries the same
glyphs on its own shelf, and because one tap brings both rows back.

The card gave up its **score row** at the same time, and the earlier reasoning
for keeping it is left in `CARD_H_GLANCE` because it was not wrong: the utility
is the one number a round is scored on, and a bare figure under a shelf is worse
than a named one. What changed is what the tap is *for*. 186 units of card is 74
more than the shelf needs, and those 74 units are band the island cannot have
while a number nobody tapped for is standing in it.

Together: **98% of the window on all three portrait phones**, from 50%.

The glance card's surviving type is now `calc(15px / var(--card-scale))` rather
than a literal `26px` paired with a literal `0.58`. Two constants that had to
agree, one edit apart from a name that shrinks with its card.

`focusing` gained the two checks that guard this: that the island **actually
reaches the frame** — a check watching only the cards would have called 70% a
pass — and that the chrome left standing is still clear of the island, counted
in model pixels behind each pill the way `uncovered` counts them. The second is
the risk the first one creates: a band declared shorter than the pills left in
it puts them back on the island, which is the defect reported by eye twice.

The block of island-then-cards is now **centred** in the band rather than pinned
to its top. Slack dumped below the last card is invisible, and on a tall phone —
where the island cannot grow — that is all a tap would have produced.

#### 0.58 of a card is not a card

The viewBox is 520 across, so on a 390pt window a unit is 0.75 device pixels and
0.58 of one is 0.44. That puts a shelf's quantities at **4.8 pixels** and its
`labour` and `utility` captions at 4.2. A number too small to read is worse than
no number, because the page still looks like it is telling you something.

So the small card stops being a shrunk card and becomes a **glance card**. What
goes is everything that was a number at that size — the per-good quantities, the
labour caption, the dial's own reading. What stays is drawn at the size it
always was, by being declared `1/0.58` larger inside a group about to be scaled
by 0.58: the trader's name at 13px, the goods' glyphs at 12px, the utility at
10px, and the bars, which are shapes and survive being small. That is the same
rule as everywhere else here — the weaker thing is allowed, and is never allowed
to look like the stronger one.

`focusing()` in `tests/render.py` drives the taps on a real phone viewport and
re-measures all of it: that a tap moves the layout at all, that it moves it the
right way, that a second tap returns the frame **exactly** — a toggle that
drifts is one nobody presses twice — that the glance card prints no quantity at
all, that every mark it *does* print is still **the size it is at even focus**,
and that the same tap on a landscape phone does nothing, because there the cards
stand in margins and are not competing with anything.

Ten neuters, and **two of them found the check rather than the code**:

- The legibility rule was an absolute *7 device pixels*. Deleting the stylesheet
  rule that holds the trader's name up could not be made to fail it — 15 units
  at 0.58 on a 390pt window still paints a 7.5px box. It measures each mark
  against the same mark on the same card at even focus instead, which is what
  the stylesheet actually claims and which cannot go stale when a font size
  moves.
- The landscape rule compared viewBoxes. But `layout` ignores the focus in
  landscape, so a tap that got past the gate would rebuild the scene — throwing
  away every animation in flight — and land on exactly the same viewBox. Deleting
  the gate failed nothing. It reads the caption too now, which is the one thing
  that says a tap was taken.

#### A check that could not fail

Found while writing the above. `mobile()` measured the island by counting canvas
pixels with any alpha — which was the island back when the canvas was
transparent around it. [The sea reaches the edge of the frame](#the-sea-reaches-the-edge-of-the-frame)
ended that, and the classifier was never revisited: it had been returning the
whole canvas ever since.

| phone | what it measured | the island |
|---|---|---|
| 390×844 | 390×811, 2.22 of its band | 382×363, 0.99 |
| 393×660 | 393×464, 2.30 of its band | 198×187, 0.93 |

Every island-size assertion in that check — fills its band, wide enough to be
the picture — had been passing on arithmetic that could not fail. It uses
`LAND_JS` now, the classifier `uncovered()` and the card checks already share,
and it passes on the real numbers.

Shown, not assumed: pinning the island to `ISLAND_TINY` and running `mobile`
both ways, the fixed classifier fails **all three** portrait viewports with true
figures (29%, 47%, 49% of their bands); the old one fails **one**, and by
accident — the cards had moved up, so the band shrank until the whole canvas
stopped covering it.

## The fire at the centre

**The market had no purpose.** A roofed stall with six posts and a plaza stood
in the middle of the island because a barter game sounds like it should have
one — but nothing on the board ever happens there. A trade is struck between
two traders and settled by the manager; nobody walks to a stall. So the biggest
building on the island was a label for a thing that does not exist.

A fire is what the middle of this island is actually for. It is the point every
settlement faces and every trail runs to, it is the one thing with something to
say at the bell — it comes up as the light goes — and the drawn island the
model replaced had a campfire there all along. The bell keeps its post beside
it: the bell is the island's clock, and it was only hanging in the stall
because the stall was there.

**It is a fire, not a plaza.** It inherited the market's footprint when it
replaced it — a two-unit sand disc with a wide ring of ash in it, on an island
whose huts are eight-tenths of a unit across — so the thing meant to be a
campfire read as the largest structure on the island, which is the complaint
the market got. Reported by eye. The clearing is about a hut and a half wide
now and the hearth inside it is something four people could sit round.

### The fire is the bell

**So it does not light at lunchtime.** The flames rose from `day` 0.52 and stood
at full by 0.82 — from just past midday, and full while the island was still
producing and still settling trades. Reported by eye against
`island-game-001d-g1`, where day 2's activity runs 0.49 → 0.84 and day 3's
0.64 → 0.69: a spectator watched the campfire burn through a working afternoon.

This page's own glossary says the bell **is** nightfall and the campfire taking
over. A fire lit halfway through the day says the day is ending when it is not,
which is the one thing the fire is on screen to say. It rises from 0.86 and is
full at the bell itself, where the bell clip's hold and flare carry it the rest
of the way; the fireflies keep their place a little behind it, from 0.92.
Decided by Gal, 2026-08-27.

It is still banked all day — the embers are a floor under the flames, not a
curve — and still comes up a little before the light has quite gone, which is
what the last stretch of the day buys. What changed is how much of the day
counts as "before the light has quite gone": an eighth of it, not half.

**Fireflies** come out over the meadow once the light has gone, a little behind
the fire, which is banked before dusk and built up as it arrives. They are
nothing at midday on purpose: a bright drifting dot in daylight already means a
good in flight on this island. They are also **kept clear of the fire** — they
were seeded on a ring about the island's centre, which the fire is very nearly
at, so the densest part of the swarm hung in the smoke, and beside small warm
flames a firefly is not a firefly, it is a spark coming off the fire.

## The sea reaches the edge of the frame

The renderer letterboxes: it draws into the rectangle the `<svg>` fits its
viewBox into, because that mapping is what puts a hut under its card. Two
separate reports came out of the bands beside and above that rectangle.

**The island stood in a void.** The sea was a disc a little wider than the
shore, and everything past it was the page's own dark backing. The disc was
widened to sixteen units, and the bands are painted by a **first pass** that
draws the sea alone, through the same camera, at a viewport the full width of
the canvas — so what lands in them is open water. Two passes rather than a
clear colour chosen to look like water: it is the same mesh under the same
lights, so it goes down with the day and through every colour the sea passes
through without a second copy of that arithmetic being kept in step. The first
attempt did keep one and it was half a stop out at noon.

**A frozen bar across the top, with clouds cut in half in it.** A scissored
clear only clears inside the scissor, so the moment the rectangle changed shape
— a resize, a phone rotating, a second round with a different number of traders
— a strip of the previous frame was stranded outside the new one and nothing
ever drew there again. The clear runs with the scissor off now. The animation
loop was also calling the renderer directly and so skipping the clear
altogether; it goes through `render()` like everything else.

### And then a third time, through the shape nothing measured

**The corners came back black on a phone.** Reported as "the sea could fill the
whole background", which is the same sentence as the first report and was the
same defect underneath — with a different cause.

The first pass draws the sea *disc*, and a disc has an edge. Sixteen units of
radius covered every frame this had ever been pointed at, and all three were
desktop-shaped, where the island's box is most of the frame. A phone in portrait
is not: the box is a fraction of a tall frame, so the frustum runs
`8.7 × geo.h / D` island units deep — **29 on a 393×660 window**, 36 at a card
focus. Past 16 there was nothing to draw.

`stage.js:flood()` sizes the disc to the frustum instead of assuming. A
horizontal disc of radius `R` under an orthographic camera at elevation `TILT`
projects to an ellipse with semi-axes `R` across and `R·sin(TILT)` down, so a
frustum corner at `(x, y)` is covered when `hypot(x, y / sin TILT) ≤ R`. It
takes the furthest corner and scales the mesh to reach it, which carries the sea
along with any change to the tilt, the frame, or the island's box.

`afloat` measures **five** shapes now, two of them phones, and asks three
questions instead of two:

- **no unpainted pixel anywhere on the canvas** — which could not have caught
  this: a corner cleared to black is painted;
- **every corner is sea** — by the same classifier the rest of the suite reads
  land with, which calls black *land*, and so fails on it;
- **and where there is a letterbox band, it is the same water as the frame.**
  That is the seam a band painted from a second copy of the day's arithmetic
  showed. It is asked **at the band** now, which is the only place the seam can
  be. It used to compare the corners against a point 2% in at half height and
  call that open water — which stopped being true the moment a phone could draw
  the island the full width of the frame, and the check failed on a correct
  page, sampling the shore shelf.

The seam's tolerance came down from 12 per channel to **4**, and that too was
measured rather than inherited: the shipped gap is *exactly zero* on both shapes
that have a band, while a backdrop pass mis-tinted 30% brighter gives a gap of
11 — a visible line down the side of the screen, which twelve was calling clean.
Two of five shapes have a band, and `afloat` now fails if *none* of them does,
because a seam rule with nothing to look at is a rule that has stopped asking.

## Flags say which good is made where, and nothing else

Every settlement used to fly one too, so a four-trader seven-good island carried
eleven flags and a flag stopped meaning anything — it was just what the skyline
was made of. Reported by eye. A hut still has to say whose it is, so the
trader's colour moved **onto the hut**: the door it faces the fire with, and a
painted band under the eaves that is visible from any bearing the camera swings
to. That is more of the colour than the banner ever showed, on a shape a viewer
is already looking at.

**The band was drawn where nothing could see it** (2026-08-27). Reported by
eye — *"I don't see the door and band"* — of an accent that had been in the
model for weeks under a comment claiming it was "visible from any bearing the
camera swings to". The bearings were never the problem; the elevation was. The
roof is a cone of radius 0.52 whose rim sits at y = 0.42, and the band was a
ring of radius 0.40 at y = 0.41 — wholly inside the overhang, so the only
camera that could ever have seen it is one standing below the eaves, and this
island is watched from above. Measured: **0 of 148 sample points unoccluded**,
on every hut, at every bearing.

The band is on the **roof** now, where the camera is already looking: a ring
hugging the cone's own slope between y = 0.47 and y = 0.55, its radii the
cone's radius at those heights (`r = 0.52 (0.84 − y) / 0.42`) plus 0.006 to
keep it off the surface it lies on, open-ended so it is a stripe and not a lid.
It measures **38–40 of 50 points and about 69px across** on a 1200×800 frame.
The finial takes the colour as well — it is the highest thing on the hut and
the last to be occluded by anything — and the door went from 0.14 × 0.24 to
0.19 × 0.28, having been about five pixels across.

`render.py:whose` is the check, and it asks about *visibility*, not existence:
each accent's own surface is sampled and every sample raycast from the camera,
counting a point only when the accent is the first thing the ray meets, at four
bearings. Every check the old band passed was a check that it existed. Neutered
against the old geometry, it reports 0 of 148 at all four bearings.

**The drawn hut and the card wore none of it** (2026-08-27). That colour lived
only in the model: `SEAT_COLOURS` in `island3d.js`, painted on the door and the
band. The SVG hut — which is what a page with no model behind it draws, and
what a viewer sees before three.js is up — had a brown door and a thatch rim
like every other hut, and the card hanging under it was a dark rectangle with a
name on it, identical for all six. So the one place a trader is named for the
whole episode said whose it was in text alone.

Now the settlement group carries `--seat` (set once, in `scene.js`, from the
trader's index) and the hut and its card both inherit it: the drawn hut's door
and roof rim, the card's border, and a rule down the card's inside edge — kept
on the glance card, where it is the cheapest mark that says whose card this is.
The stripe is inset rather than laid on the card's own border, which is rounded
at 13 and would show a straight stripe overhanging both corners. Starvation
still outranks identity: a starved card's border goes back to `--critical`.

`--seat-1..6` are in `tokens.css`, and were the same list as `SEAT_COLOURS` in
`island3d.js` — not a coincidence to be trusted, since the goods drifted in
exactly this way, so `test_palette.py` compared the two.

**Superseded the same day, and by the defect both lists shared:** each picked
its colour with `% 6`, so a seventh trader's hut, card and offers all wore the
first trader's colour. There is one list now — `web/seats.js`, which answers for
any seat count and which both layers import — and the accent set on the
settlement group comes from it rather than from `var(--seat-N)`. The stylesheet
still names the six, because that is where the palette's gates are run. See "A
seat's colour is a function of the seat *and how many seats there are*" below.

The bell and the new day used to run those banners down and back up their poles.
Both keep the larger half they always had — nightfall over the whole frame, the
fire taking over, the night lifting, every trader's crates draining and coming
back — and neither needs a scrap of cloth on a stick to say it.

The offer and the refusal used to raise a **post with a notice on it** beside
the maker's hut. **Both posts are gone (2026-08-27, Gal)**, and with them the
last post or flag on this island that is not a production site's marker. A flag
here says which good is made where; nothing else says anything with a post or a
scrap of cloth.

Neither event loses its picture, because neither was carried by the post. An
offer is **the rope** across the frame — labelled with what is on the table, its
dashes crawling toward the trader it is addressed to — and, on the island
itself, the crates the maker is offering lifting off its own pile and settling
back, since an offer is a proposal and nothing has moved yet. A refusal is the
**bubble over the hut** with a cross in it — and, where the manager named a
cause, the slot it came up short in and the offer holding what it needed, lit
together (`blame()`). It has nothing of its own on the island at all: `render.py:overhead` is
what holds it to that job, and `mechanics` names it as the one event the island
is not asked to show. Measured on the way here — a refusal was 3.20% of the
island's frame with its ground disc and 0.27% with only the post, so what was
dropped is the smaller half of something already carried elsewhere.

**The offer's lift is bigger than it was, because it is now the whole of the
offer on the island.** It was 0.42 of a unit with a twelfth of a scale on it —
tuned when it was the third thing an offer did, behind a post and a notice — and
with those gone `mechanics` measured the whole event at **0.17%** of the
island's frame, under its own 0.2% floor. That is the check saying a viewer
could not see it, and it was caught by the browser suite after the change was
merged rather than before it: the run that would have said so was written off as
an environment failure on a flaky first load. It is a crate held up over the
yard now — twice the height, a third again the size, every box up together
rather than stepped a tenth of a second apart — and the suite passes with no
floor moved.

### The water casts no shadow

Reported by eye: a dark, soft-edged **rectangle** sitting on the meadow,
flickering rather than sitting still.

It was the sea. `island3d.js:add()` gives every mesh `castShadow`, and the
water is a flat disc sixteen units across against a shadow camera six units
either way. Two things go wrong at once. The frustum clips the shadow map, so
its own edge is a straight line laid across whatever it falls on; and from a
light forty-five degrees up the disc's **far side is nearer the light than the
island is**, so the water wins the texels the land needs, the land is compared
against the water's depth, and it comes out shadowed. The patch crawled as the
light swung through the day, which is what read as flicker.

Widening the disc from five units to sixteen — so the frame ends in open water
rather than a void — made it obvious. It did not cause it.

Water casting a shadow is meaningless in any case, and nothing on this island
stands far enough out to sea to throw one onto deep water, so the disc neither
casts nor receives now. The shallows, the shelf and the beach still do both,
which is where the coast's own shadows are.

`render.py:island` asks the model rather than the picture: **every mesh that
casts must fit inside the box the shadow camera covers.** "Is this caster
inside the box that can hold its shadow" has an exact answer, where "is there a
rectangle on the grass" is a question about pixels that only fails once
somebody has already seen it. Neutered, it reports the sea at 16 against a
reach of 6, in every frame shape.

### An element is smaller when there are more of them

A fixed element size at a growing table is how an island reads as crowded and
how a hut ends up drawn against a production site — a layout accident, not a
fact the manager settled. The props were sized by eye at a small table and
stayed constant as it grew; at eight traders and five goods, settlements and
sites covered **62%** of the meadow and overlapped.

Three things, and they are one rule seen from three sides:

**Size.** `room = √(REF / crowd)`, clamped to 0.72–1.1, where `crowd` is
traders plus goods and `REF` is 8 — the table the current sizes were tuned at,
so nothing moves on an island already drawn. The rule is area-preserving: twice
as many things, each about seven-tenths the size, covering the same grass. It
holds: the footprint share is 36–39% from two traders and four goods up to
eight and five, where it used to run to 62%.

**Bearing.** Settlements and sites used to be laid on two independent rings,
and the comment said "a ring the settlements are not on", which was not true —
a dry site sits at 2.15 and a settlement may stand anywhere from 2.15 out to
the grass's edge. Which bearings collided came down to how the two counts
happened to divide the circle. There is one schedule now, `crowd` slots wide,
dealt alternately between the two kinds. **The angular pitch is the density
rule**: `2π/crowd`, the same arithmetic that shrinks the props, applied to the
ground they stand on.

**Then measure.** Any placement rule works on anchors, and what a spectator
reads as "these two are drawn against each other" is the ground the props
actually cover — which is not centred on the anchor, because a hut carries
crates beside its door and a site carries a flag on a pole. A hut cleared the
bread field by the rule and still overlapped it by a tenth of a unit. So the
props are built and *then* the footprints are measured, and any overlapping
pair is separated along whichever axis is cheaper. A settlement moves freely; a
site moves only along its own ring, because its radius is what it means — salt
is worked on the wet shelf, iron is cut out of the upland.

Two consequences worth naming. `spaced()` no longer moves seats only around the
island: a seat caught between the hill and a site on its own bearing had the
push taken straight back off it by the clamp, so it relaxes in two dimensions
and lets `homeSite` put it back on the grass. And `follow()` — which walks a
site's parts down onto the slope under each of them — now runs *after* the
settling rather than during the build, because it reads the ground once and
adding the slope twice is what running it before a move would do.

`render.py:island` measures footprints at six through eight traders as well as
the shapes it already had, and asks two things: no two of them overlap, and
together they cover no more than 48% of the meadow. The old "two settlements at
least 1.2 apart" is gone — the right question asked against a constant, from
when a hut was always the same size. Neutered to a constant size, the new one
reports 51%, 56% and 62% and two overlaps.

### An offer is delivered, and then it waits on the trader it is addressed to

**Decided by Gal, 2026-08-27.** The rope was the whole picture of an offer: a
line between two huts with a label hanging at its midpoint, its dashes crawling
toward the taker. Two things it did not say, and both are the offer's content.

**Whose it is.** The label named the maker in 10px monospace beside the pid,
and that is the only place on the frame an offer said who made it — a spectator
reading the square had to read text to answer the first question they have. The
pill now wears the **maker's seat colour**, as its border and as a dot inside
it: the same colour the island paints that trader's hut and boat, so a pill
leaving a roof is the colour of the roof it left.

The seats are held to **byte-distinctness** from every good and metric rather
than to the series' contrast floors. A seat is never the only thing saying
whose an offer is — the pill carries `maker→taker` in text under it — so it is
not asked to be tellable apart at a glance the way two bars on one shelf are.
What it must not be is the *same colour* as something that already means a good
or a score on the same frame.

### A seat's colour is a function of the seat *and how many seats there are*

`SEAT_COLOURS[i % 6]` is what the island did, and a table is not capped at six
anywhere — `dealer.draw` takes an agent count and the lobby seats whoever turns
up. **At seven, the seventh trader wore the first trader's colour**: on the
hut, on the boat, and on every offer either of them made. A repeated colour is
not a quiet degradation, it is a wrong answer to the one question a colour on
this island is asked.

`web/seats.js` owns it now, and both layers import it — the island for its huts
and boats, the SVG layer for its pills, so there is one list rather than a
CSS one and a three.js one drifting apart the way the goods did. Up to six
seats it is the hand-picked six, unchanged, which are also `--seat-1..6` in
`tokens.css` where the gates are run. Past six the **whole ring is generated**:
`n` hues evenly spaced in OKLCH around the band those six sit in.

**The ring belongs to the round, not to the trader.** With seven at the table
nobody wears one of the six; they wear one of seven. That is fine because the
question a seat colour answers — *whose is that?* — is only ever asked within a
table, and a round is where the table is fixed.

**Hue alone is one colour to a dichromat, which is why the ring steps its
lightness too.** Evenly spaced hues at fixed lightness looked right and
measured terribly: at ten seats the closest pair was CVD ΔE **0.3**, because
red-green vision keeps roughly one chromatic axis and a hue circle folds onto
it. Lightness survives every dichromacy, so seats cycle four levels spanning
0.20 of OKLab L as the hue goes round:

| seats | closest pair (worst CVD) | closest pair (normal) | dimmest on the panel |
|---|---|---|---|
| 6, hand-picked | 2.1 | 17.1 | 4.93:1 |
| 7 | 5.1 | 19.9 | 4.87:1 |
| 8 | 3.2 | 17.0 | 4.91:1 |
| 10 | 2.8 | 14.7 | 4.70:1 |
| 12 | 3.8 | 12.6 | 4.75:1 |
| 16 | 1.1 | 10.1 | 4.73:1 |

```
python3 viewer/palette.py seats 6 7 8 10 12 16
```

Two things that table says, and both are written into the gates rather than
left as a reading. **The hand-picked six do not clear the series' adjacent
floor and never did** — `--seat-2` and `--seat-5` are ΔE 2.1 apart under
deuteranopia — so `test_palette.py` holds seats to **2.0**, which is a
regression gate at what the palette measures today and not a standard anybody
would design to. And **past twelve, colour stops carrying a seat at all**: 1.1
at sixteen, 0.0 at twenty-four, two seats one colour to a dichromat and
distinct only in bytes. That is the eye and the gamut, not the generator, and
no palette fixes it. What is asserted at every size is what remains true: **no
two seats share a colour, and every seat is legible on the surface it is drawn
on.** Past that, the name in text beside the colour is what identifies a
trader — the same bargain the goods make with their glyphs.

**Where it is going.** The rope's direction was carried only by the crawl of
its dashes, which is a thing a viewer has to already know to read. The pill now
**slides the rope**, from the maker's hut to the taker's, and then the **rope
fades** and the pill **stays over the taker** until that trader answers it or
the bell takes it away. An offer is a thing waiting on somebody, and it now
looks like one: the line was the *delivery*, and once the delivery has happened
a line across the picture is saying something already said.

Three details that are the design, not the implementation:

* **The pill rides the rope's own curve**, sampled from the same quadratic the
  path is drawn as, and it is driven by a per-frame loop rather than by a CSS
  or WAAPI animation. The camera turns the island continuously, so keyframes
  sampled when the offer opened would walk a path that is no longer where the
  huts are. `scene.js:ride`.
* **The slide's clock is kept by pid, not by node.** `follow()` and `paint()`
  both throw the rope nodes away — on every camera frame when the set of open
  offers changes — and a slide restarted by a rebuild is a pill that never
  arrives. Kept in `scene.travel` and dropped when the offer stops being open,
  which is also what lets a viewer scrub backwards and watch it delivered
  again. This is the same defect the dashes' crawl had, and it is the reason
  `render.py:turning` reads the animation's own clock.
* **The faded rope is still in the DOM, at its own two settlements.** That is
  what `turning` reads to check the ropes are re-laid as the camera goes round,
  and the crawl still runs under the fade. A blamed offer — a refusal for goods
  the trader has already promised away — brings its rope back at full opacity,
  because that refusal is a statement about *which* line on the square is the
  problem and it cannot make it invisibly.

A viewer who asked for less motion gets the pill arrived and the rope gone at
once: the picture is where the offer is standing, not the travelling.

### There are no ground marks left, and now no lights either

**The last two are gone (2026-08-27).** The lamp on an offer's post and the red
disc under a refusal outlived the ring purge — one because it replaced a ring,
the other because it was called a flash rather than a ring. Cut on the same
reading: a light on the grass is not a thing that happened, it is a caption for
one.

The cost was measured before the cut, not discovered after it. An offer changed
**1.75%** of the island's frame with its lamp and **0.36%** without; a refusal
**3.20%** with its disc and **0.27%** without. Doubling the notice instead of
the lamp gets 0.61%, so nothing standing on the post buys it back — the light
on the ground *was* the change.

That is fine, because neither event was ever carried by the island:

* an **offer** is the **rope** — a line across the frame from the maker to the
  taker, labelled with what is on the table, its dashes crawling toward the
  trader it is addressed to;
* a **refusal** is the **bubble over the hut** with a cross in it, and the red
  outline round the trader's card.

Both are SVG over the canvas. So `mechanics` — which drives a bare stage with
no scene on it, and cannot see either — lets those two off its 1.2% floor and
holds them to a real but small one instead: something has to happen on the
island, a post rising and a notice unrolling, a post shaking and a notice
tearing in two.

**That is a handover, not an exemption, and the difference is asserted.**
`mechanics` reads this file's own source and fails if `turning` (the rope) or
`overhead` (the bubble) has stopped being run — otherwise the day somebody
deletes one, the event goes quiet everywhere at once and nothing says so.
Neutered — `turning` dropped from `run` — it reports exactly that.

### There are no ground marks left

There was a ring under every event. Reported as shockwaves, they became a patch
of light in the same places instead — and that was reported too, and by then the
reading was the right one. **A coloured disc on the grass is not a thing that
happened, it is a caption for one**, and the island already shows what happened:
goods are made and carried by boxes that stand there afterwards, and the bell is
the fire coming up and the light going. A ring said none of it and covered the
ground that did.

What each clip carries itself now:

| clip | what a viewer sees |
|---|---|
| a production | the site works, and boxes are made there and hop home |
| an offer | a post and a notice beside the maker's hut, the crates it offers lifting off the pile — and **the rope**, which is the picture |
| a settlement | the boxes cross the island, and the fire flares once |
| a refusal | the post shakes and the notice tears, and **a bubble over the hut with a cross in it** |
| a remark | **a bubble over the hut, with three dots in it** |
| the bell | **nightfall**, and the campfire taking over |
| a new day | **the night lifting**, and last night's fire going out |

### The offer's crawl is measured on its own clock

`stroke-dashoffset` is a **painted** value, and Chromium throttles the paint
when the machine is busy: run alongside the rest of the suite, the offer's
dashes crawled 0.31 in six hundred milliseconds against a floor of 0.5, and
`turning` failed for being run in company. Run alone it passed. That is a check
whose answer depends on the load.

It reads the animation's `currentTime` now, which tracks the document timeline
and advances whether or not a frame was drawn. It still catches the bug it
exists for — a rope rebuilt under its own animation gets a *fresh* animation
whose clock starts at zero — and neutered (ropes replaced every frame) it
reports the clock at 0 → 0 alongside six replacements.

### A crate on this island is a good, and nothing else is

Asked by name — *"what are the brown boxes?"* — which is the question a shape
gets when it looks like something it is not.

Two of them stood by every hut's door, and one at the generic works site. They
are scenery from before goods stood on the island at all: a hut with some things
outside it. They became a lie the moment a trader's holdings became **crates in
a yard beside that same hut**. A brown cube with no colour and no glyph, next to
a stack of coloured ones that each say what they are, is a good a viewer cannot
identify.

The door crates are gone. The works site's crate is a barrel — it is only drawn
for a sixth good and no table has been that wide, which is exactly why it would
still have been a crate when one was.

The same rule as the flags: **a shape on this island means one thing.** A flag
says which good is made where; a crate says a quantity of a good somebody holds.

The quarry's cart was the third of them — a 0.2 timber cube, reported as not
recognisable, and it was a crate in everything but name. It is a cart now: a
tipped body, two stone wheels and a shaft, and half again the size it was. A
cart is a quarter of a unit long on an island eight across — about twenty pixels
on a laptop — so what makes it readable at that size is its silhouette and the
contrast of the wheels against the body, not its parts.

### A bubble belongs over the hut

The two things a trader does that leave no goods behind — refusing an offer, and
simply speaking — are drawn as a speech bubble: a cross for the refusal, and for
a remark **three dots and nothing else**, because the island's job is to say
*that* somebody spoke, not what they said. What they said is in the ticker, and
printing the manager's sentence across the sand was the thing this replaced.

They were hung at `seats`, which is the **card** once there is a model. So the
one picture that says "this one just spoke" appeared out in the frame's margin,
a third of a frame from the thing that spoke, and read as chrome rather than as
the island. They hang at `pins` now — where the model put the settlement.

Two groups, not one. The outer holds the *place* and is moved by `follow()` on
every frame the camera turns; the inner holds the *rise* and is what the
animation drives. One group doing both would have the animation's transform
overwrite the position sixty times a second, and the bubble would sit where the
hut was at the moment it opened — which matters, because a bubble lives about a
second and a half and the camera covers a few pixels of its revolution in that
time.

`render.py:overhead` drives a real refusal on the real page and asks that the
bubble opens on the settlement, is still on it a second later, and carries the
right mark. It **freezes the bubble half way up** before measuring: it lives
1300–1500ms and a click through the driver costs most of that, so measured live
the first reading came back with the thing already faded to two per cent — a
check that would pass or fail on how busy the machine is.

Neither replay this repo keeps has a plain remark on it, so the talk half is
driven from the first board the page serves that does have one, and which board
that was is printed. Both halves fail when the bubbles are put back over the
card.

### The huts have no lanterns

Each hut carried a small emissive sphere by its door, brightened as the day went
on the argument that it was the one thing on the island brighter at dusk than at
noon. **Cut as unnecessary (2026-08-26).** The campfire already carries
nightfall, and a warm dot per hut says nothing the fire has not — while a small
bright dot on this island already means a good in flight, which is the same
reason the fireflies are held a clearing's width off the fire.

That line used to end "the material stays, for an offer's lit notice, which is a
mark that fires once for a reason rather than a light that is simply on." **The
offer's lamp is gone too (2026-08-27)** — see *"no ground marks left, and now no
lights either"* — so there is no lantern anywhere on this island.

`M.glass` survived that cut, unused, on the argument that the next thing which
genuinely glows should be this colour and that deleting it is how a palette
drifts. **It is deleted now (2026-08-27, Gal)**, with the last of the posts and
the notice it was kept for: a palette entry nothing draws is not a palette, it
is a note, and the note is the one in `island3d.js` — it was `0xffd79a` at
roughness 0.4, emissive `0xffb45e`.

### One face per good, wherever the island draws one

A crate standing in a trader's yard and the flag over the site that *makes*
that good are the same claim, and they were made two different ways: the crate
carried a colour and a symbol, the flag carried a colour and nothing at all.
A flag with only its colour asks a viewer to tell pink from purple across an
island eight units wide, which is exactly what the palette does not promise —
it clears **adjacent** pairs, not all pairs, and that is the whole reason a good
carries a glyph anywhere.

[`good-face.js`](web/good-face.js) is the one texture both read. It lives in its
own file because the glyph table belongs to `scene.js` and the model must not
import the drawing layer; nothing in it imports the model either, since the
colour arrives as an argument, so there is no cycle in either direction.

It returns `null` where there is no `document`. The island is built headless by
checks that ask it geometry questions — where a hut stands, how high the ground
is — and never render a pixel, and a model that cannot be constructed without a
browser is a model those checks cannot ask. The caller falls back to the flat
colour, which is what a face is under its mark anyway.

`island()` reads each flag's own texture and fails below a tenth of the face
covered. Against the shipped flags it reports **50**.

### A clip asks the island; it does not reach into it

The bell is not a bell swinging. It is the light going and the fire coming up —
both the size of the island, where the bell itself is a plum on a post. Dawn is
the mirror. Neither of those is a prop a clip can own, so a clip **asks**
`island-life` for them: `flare` for the fire, `hold` for the light.

Both are **contributions for one frame**, spent by the layer that reads them.
A clip that ends, is cut off half way, or is thrown away with the island under
it stops contributing by saying nothing — there is no state left holding the
island at midnight because a restore did not run. That was the first shape of
this and it left the island dark after every bell.

Two orderings fall out of that and both were wrong before:

* the stage steps its **clips first**, then the ambient layer, then draws —
  a contribution has to be set before the layer that spends it, and the other
  way round applied everything a frame late;
* a clip that has run out is **not advanced one last time**. `step()` used to
  call `update()` past a clip's duration and retire it in the same pass, which
  was harmless while a clip only touched props it owned and not harmless once
  one could set nightfall: the bell's final call darkened a frame with no bell
  in it. What a clip leaves behind for good is `settle`'s job.

### The offer's line travels

The dashes crawl from the trader making the offer toward the one it is
addressed to — the path is written maker-to-taker and a negative dash offset
advances along it, so a line built the other way round would animate the goods
flowing backwards.

They were not moving at all. `follow()` runs on every frame the camera turns,
and it rebuilt every rope node each time; **a fresh node restarts its CSS
animation**, so the crawl was reset sixty times a second and the line sat
still. Ropes are moved in place now and rebuilt only when the set of offers
changes. `turning()` holds both halves: the node has to survive the camera
turning, and the path has to start at the maker's end.

### The border is whose, and nothing else

**A card's border is its seat's colour, at the weight an offer's pill wears
it** (2026-08-27, Gal's ask). It was a half-opacity hairline with the colour
that said whose card this was living on a rule *inside* it instead — so a card
in the margin and a pill over a hut, which are the two places the same trader
appears at once, wore the same colour at two different strengths. They match
now, and the inside rule is gone: with the border carrying it at full weight, a
second stripe of the same colour is the same fact twice.

That leaves the border with one job, which is why the other thing on it had to
move. **Starvation floods the card instead of outlining it.** A red border said
"this is the trader in trouble" by ceasing to say *which* trader it was —
identity and alarm competing for one line, and the alarm winning. Holding some
of something and none of another is a state the whole card is in, so the whole
card carries it: the fill goes dark red and the shadow under it picks up the
same colour. The shelf cell that is empty keeps its own red ring and red zero,
which is the part that says which good.

### What became of an offer, said on the offer

An offer left the square three ways and the square said nothing about which.
It vanished at the bell, it vanished when it settled, and a refusal put a cross
over a hut while the rope it was about carried on crawling. All three are now
said on the rope and the pill themselves (2026-08-27, Gal's ask):

* **The bell dissolves it.** A lapsed rope used to fade its opacity, which read
  as the page dropping the offer rather than the bell taking it. `fray()` blurs
  and lifts the group while `@keyframes scatter` pulls its dashes open into
  specks.
* **A refusal blinks it red.** `refuse()` finds the offer the manager was
  answering — the manager names the proposal in three of its four approval
  refusals, and in the fourth it names the good, where the offer is the open one
  addressed to that trader asking for it. Marked on the **live** rope, since a
  refusal does not close the offer, and a red copy laid over the orange original
  would blink to the wrong colour between flashes.
* **A settlement blinks it green.** A settled offer is out of `this.ropes` by
  the time `play()` runs, because `paint()` draws only open offers — so the
  green copy is spawned from `paint()`, beside the lapsed one.

The colour is the answer and stays under `prefers-reduced-motion`; only the
blinking goes.

### The pile on a hut is the queue that hut has to answer

**The pills stack by taker, and the ropes fan by pair. Those are two different
numbers**, and using one for both was the bug. Fanning the arcs keeps two
offers between the *same* two huts off one curve, which is what `fan` is for —
but three traders offering the same hut all sit at fan 0, so their pills landed
on that one roof on top of each other. Which is exactly where a spectator
counts what a trader has been asked, and the count was unreadable there.

`stacking()` numbers the open offers by taker in the order they were made, and
the arrived pill rises one pill-and-a-gap per place in the pile, oldest at the
bottom. Two details it needs:

* **The frame before is kept** (`wasStack`). A pill on its way out is drawn
  *after* its offer stopped being open, so `fray` and `verdict` build their copy
  from a proposal the current map no longer carries — without the old height it
  would drop to the roof before dissolving.
* **A changed pile is changed offers.** `follow()`'s reuse check compares pair
  fans and the count, and one offer lapsing as another opens leaves both
  identical. `aimRope()` re-reads the stack every frame, so the reused branch is
  correct either way.
* **The pile stops at a ceiling and compresses instead of growing through it.**
  A pile that grew freely put its top pills off the top of the picture, which is
  the one place a spectator counting what a trader has been asked cannot count
  them; overlapping pills can still be counted. So every pill knows how tall its
  own pile is, and the spacing is the smaller of a pill-and-a-gap and what the
  room allows.

**The ceiling is measured off the drawing, not derived from the layout**, and
the first version got this wrong by deriving it: a frame whose shape is not the
window's is fitted inside it with `meet` and *centred*, so in landscape there is
real picture above `y = 0` — a sixth of a 1500×1000 window at the frame this
draws — and a ceiling taken from `islandBox.y` squeezed piles of three that had
room to stand at full spacing. What actually cuts a pill off is the `svg`'s own
box, which clips, and the floating chrome, which is opaque and stands on top.
Both are on the page, so `ceiling()` asks them. Measured on a 1500×1000 window:
six offers on one hut stand 34.6 units apart against a 38 maximum, the top one
115 units above the frame's own top edge and inside the window with a pill's
height to spare.

### The pill says whose without writing it down

The pill carried a grey `p2 · T1→T4` under it. **Gone (2026-08-27, Gal)**: the
pid is the manager's word for the ledger, and the arrow repeated what the pill's
own colour and the rope it hangs from already say — whose offer this is, and
which hut it is addressed to. It survives as `data-pid`, `data-maker` and
`data-taker` on the rope's group, which is where a name nobody reads belongs;
`render.py:turning` reads the maker from there rather than off a label.

### The sea moves, and there are dolphins in it

The open water was a flat disc: one colour, perfectly still, with every moving
thing in the picture crowded into the two surf rings at the shore. The further
from the coast a pixel was, the more plainly it was a painted floor.

**The swell** is that disc's surface. `island-life.js` lays a ring of geometry
over it, from just under the shallows out past anything the camera frames, and
displaces it with three sine trains crossing at different bearings and speeds.
The normals are recomputed each frame, which is the part that matters: without
it the crests are lit as though the sheet were flat and the whole thing is a
blue disc with a bumpy outline. Lit rather than tinted, so it goes gold at dusk
because the light does, and nobody keeps a second copy of that arithmetic.

The deep disc stayed, and **moved down**. Its top used to sit at `-0.04`, and
the swell's troughs reach a tenth of a unit below the still water line, so
every trough cut into it and the sea got a ring of intersection lines. It is
the colour behind the swell now; it only has to be below the lowest trough.

**The dolphins are occasional, and that is the design.** A pod circling the
island all day is scenery and stops being seen by the second minute. A pass is
a chord across the open water lasting thirteen seconds out of every fifty-two,
on a bearing taken from the cycle number — so it is different each time round
and still reproducible — and between passes the pod is not in the scene. They
porpoise: the pitch follows the slope of the arc rather than being animated
apart from it, so a dolphin never enters the water nose up.

Two things had to be got right and neither is guessable from the code that
draws them.

**A dolphin is built along `+x`, so its yaw is `-bearing`.** The gulls' own
`-a + PI/2` is the tangent to a circle, and borrowing it here swam the whole
pod broadside, nose to the camera, for a full pass.

**They belong to the backdrop pass, not the framed one.** `Stage.render()`
draws the sea across the whole canvas on layer `WATER` and then the island
again, scissored to its own rectangle. Anything on layer 0 alone stops existing
outside that rectangle: the swell ended at the edge of the box with flat water
beyond it, and a pod passing wide was cut off mid-leap at a line down the
frame. `stage.js` enables `WATER` on the swell and on each dolphin — and on
their child meshes, because layers are per object and are not inherited, so
marking the group alone renders nothing at all.

Neither is caught by a structural check; both were found by looking, with
`python viewer/tests/render.py --out /tmp/after` and a browser on
`viewer/serve.py`.

## The goods stand on the island

**Nothing pops or vanishes except when it is created or consumed.**

Every good used to be a clip prop. A crate appeared when a production receipt
arrived, crossed the island, and shrank out of existence at the hut three
seconds later; a settled exchange conjured crates at one settlement and
dissolved them at the other. So the ground held nothing between events — a
trader's stock existed only as a bar on its card — and what the island showed
was goods being destroyed and re-created rather than changing hands.

[`island-stock.js`](web/island-stock.js) is the other half. Every trader has a
**yard** beside its hut and what it holds stands there as boxes, each wearing
the good's colour and the good's own symbol — the same two marks the legend and
the card's shelf use, because colour alone does not identify.

| what happens on the board | what the island does |
|---|---|
| a production receipt | boxes are **made** at the site that made them and hop home to the yard |
| a settled exchange | **the same boxes** leave one yard, fly the offer's line, and stack in the other |
| the bell | what was held is **eaten**, and the boxes go down into the ground |

Those three are the only times a count changes, and each is a thing the manager
settled. The one cut that is not an animation is a **scrub**: jump into the
middle of a replay and the island has to be what the board says at that frame
with no journey to show. `rest()` is that cut and it is the only path that puts
a box down without one.

### How many boxes is a holding

**A box is a fixed quantity, and it is the same one on every board.**

It was a sixth of the round's own largest settled holding of that good, so six
boxes was whatever the biggest pile turned out to be. That reads well in a
replay and is wrong twice over. A denominator taken from how a round *ended* is
not known while it is running, so a live board had no scale at all and every
non-zero holding was a single box; and even in a replay it made a box mean a
different quantity on every board, so two rounds side by side could not be
compared by looking at them.

The scale comes from the **distribution**, which the design fixes and which is
therefore known before a single message is posted. `barter.economy`'s
`draw_island` gives every trader a capacity per good of `exp(0.8 · N(0,1))` —
lognormal, `spread = 0.8`, the same for every island this game has ever drawn.
Six boxes is its **ninetieth percentile, 2.79**: a pile at the top of what one
trader can make of one thing. A box is a sixth of that, `UNIT ≈ 0.465`.

The ninetieth and not the median, which was the other candidate: the largest
pile ever settled on any board on disk is 5.91 and the median round's biggest
is 0.75, so a median-sized cap (0.167 a box) puts a full yard under both and
says nothing. At `0.465` the median round's biggest pile draws two boxes, the
upper quartile three, the ninetieth four, and only the genuine extremes
saturate at six. Any non-zero holding is still at least one box — a trader with
a little of something has some of it.

`tests/test_box_unit.py` re-derives the quantile from `draw_island` itself, so
a change to `spread` — or to the shape of the draw — fails there rather than
silently rescaling every yard on the island. The number is a literal in three
places (the page, the checks, and that test's own constant) because JavaScript
cannot import a Python module; the test is what stops the three drifting.

Two things moved with it. A crate is a little larger (0.15 island units, from
0.13), because a box is worth about three times what it was and there are one
to three of them in a yard now rather than five or six. And `render.py`'s
event fixture was scaled up: its quantities were chosen when 0.8 of a good was
five crates, and the events it fires say they are showing "the day's work
standing in the yard", which 0.8 no longer is.

### The three legs of an exchange

A good is in exactly one place at every moment, and no bar changes until
something arrives to change it:

1. the **losing** bar empties and its symbols fall to its own boxes (820ms);
2. the boxes cross the island (1500ms) — the only thing that moves between the
   two settlements;
3. the symbols rise off the arriving boxes and the **gaining** bar fills as
   they land (900ms).

With a model up the card layer draws no parcel across the square at all. The
boxes are already crossing; a parcel would be the page saying it twice, and the
two would disagree the first time one was a frame behind.

### Three things reported by watching it

* **A traded box vanished and reappeared.** The clip hid each box until its own
  leg of the exchange began, so for the first 850ms the goods were gone from
  the maker's yard and then appeared in mid-air on the way to the taker's —
  the one thing this whole layer exists to stop. No check would have caught it:
  the yards agree with the board at *both ends* of the animation and the counts
  never lie. It is only wrong while it is moving. `render.py:carrying` drives an
  exchange a tenth of a second at a time and watches every box that existed
  before it started — none may go invisible, none may move further in one step
  than a box can travel.
* **The island's palette and the card's had drifted.** From the fifth good on —
  and five goods is the table default since fish — the stylesheet said pink,
  green, purple and `GOOD_COLOURS` said purple, pink, cyan, so a crate standing
  in a yard was a different colour from the bar counting it and the chip naming
  it. Nothing compared them because one list is CSS and the other is hex
  integers for three.js. The stylesheet is the source: its colours are the ones
  `palette.py` runs the contrast and dichromacy gates against, so a colour that
  exists only in the model has passed nothing. `test_palette.py` compares the
  two lists; `render.py:stock` compares the **pixels** a box is painted against
  the computed `--good-N`.
* **A box could carry no mark.** A good absent from the glyph table got a plain
  coloured cube, while the card's shelf already fell back to `▪` for the same
  case. Colour alone does not identify — the palette clears adjacent pairs, not
  all pairs, which is exactly why goods carry a glyph. The check reads a box's
  own texture and fails below a tenth of the face covered.

### A second replay played in the first one's night

Reported by eye: *"first replay was fine, second replay showed many bugs —
daylight hasn't changed."*

The key, the ambient and the fill belong to the **stage** and outlive the
island, so a round watched to its bell leaves them at dusk. `day` is the page's,
set on every paint, and it is `null` on a board whose schedule line the page
cannot read — and the rule for `null` is to leave the light where it is, because
not knowing the hour is not the same as it being dawn. Between them: a second
round that played from its first frame to its last in the previous round's dark.

The rule is kept and narrowed. `Stage.build()` forgets the hour, so a new island
is **untold**; `island-life.js` gives an untold island the middle of the day, and
only an island that has been told the hour holds what it was told. Both halves
are needed and both are neutered in `render.py:nightfall`, which drives a stage
to a bell, builds the next round on top of it, and asks for daylight — and then
asks a *told* island to hold its hour when the clock goes quiet, so the fix
cannot be "always daylight".

A second thing fell out of chasing it: **the animation loop asked for its next
frame last**, so one exception anywhere in it meant no frame was ever requested
again and the island froze exactly as it stood — sun, clouds and camera — with
the canvas still showing the last thing drawn. It asks first now, and a frame
that throws says so once instead of sixty times a second.

### What a check can catch that could not exist before

The island can now be *wrong* in ways it could not be as a prop layer: a box
left behind after a trade, a pile that did not grow when a receipt arrived, a
stack floating over the grass. `render.py:stock` drives a stage directly with
holdings it chooses — a trader holding nothing, holding a crumb, holding more
than six boxes can show — and compares the yards against the board. It found a
real placement bug on its first run: a settlement sits on an annulus reaching
most of the way to the meadow's rim, so for some seats the ground *behind* the
hut is sea, and the clamp that keeps a yard on the grass pulled the whole thing
back on top of the hut it was meant to stand beside. A yard picks the first
bearing with room now — behind, then either flank, then in front.

## The symbols wait for the boxes

The exchange is three legs, and they run in order:

1. the **losing** bar unfills and its symbols fall to its own pile;
2. the boxes cross the island;
3. the symbols rise off the **arriving** boxes and the gaining bar fills.

Leg 3 was starting **30ms before the boxes touched down**, and 590ms before
they had finished settling onto the new owner's pile — so a bar filled from
goods that were still in the air. Reported by eye.

The cause is the shape of the thing: the boxes are three.js and the symbols are
SVG, and the two engines were keeping **separate copies of the same
choreography in different units** — `island-events.js` in seconds off its clip
clock, `hands()` in milliseconds off a `CROSS` constant. They had drifted apart,
and nothing could have noticed, because neither one was wrong about itself.

`scene.js:CARRY` is the one table now, and `island-events.js` imports it and
divides by a thousand. It is the same arrangement `feeds.js` already has with
`DWELL`: the durations are named once, where the animation that spends them is
written.

| | ms |
|---|---|
| `off` | the boxes set off, the losing card having emptied into them |
| `step` | and the next good's boxes follow this much later |
| `spread` | one good's boxes leave across this window, however many |
| `cross` | over the island |
| `land` | and the hop onto the new owner's pile |
| `rest` | a beat standing there before the symbols rise off them |
| `back` | the return bundle sets off this much after the first |

**`spread` is what makes the cue computable.** The boxes of one good used to
leave a fixed 120ms apart, so a good that came to six boxes was 600ms slower off
the ground than one that came to one — and the card's symbols, which do not know
how many boxes a quantity came to, had no landing time to follow. Spread across
a fixed window at `k / (n - 1)` of it, the *last* box of a good always leaves at
`spread`; a lone box takes the whole window rather than none of it, so that is
true of every good and not only of the crowded ones. `carriedBy(i, back)` is
then exact, and both engines compute it.

`DWELL.settled` stopped being a literal. `dwellFor` measures the bundle it is
given — a two-good exchange runs 300ms longer than a one-good one — because
holding every trade for the worst case a board allows (seven goods, 7.6s) would
spend that on every two-good trade as well.

`carrying()` measures the claim rather than the table: for **each good**, the
moment its own boxes stop moving against the moment `hands()` is told to send
its symbols. Bounded on both sides — early is the defect, and later than a beat
means the two schedules have drifted apart again.

Its fixture had to change to say anything. It held 0.8 of everything and moved
0.4, which at `BOX` = 0.465 is a **single box** changing hands per good — and a
single box is the one case where `spread` does nothing at all, so the rule it
exists for could not be made to fail. Six boxes each now, five of them moving.

## Utilities and efficiency

Both need tastes, so both are replay-only, and the live page says so rather than
showing an empty score.

On the island, each card carries the trader's utility — rising as they produce
and trade, held at the episode's closing value through the bell rather than
dropping to zero with the emptied shelf, because what the episode was worth is
what it closed holding.

When the round is over, a **closing card** says what it came to, over the
island rather than behind a drawer: whether anybody beat playing alone, and
each trader's total as a multiple of what they would have had never trading —
the number the ledger scores a trader on. Its figures are derived from the
sidecar's trajectory and autarky utilities, and reproduce the ledger's own
exactly; a board with no sidecar gets the card saying so instead of numbers.

**`capture` and `eff_round` are deliberately not on it.** Both are measured
against the island's frontier, the page has no frontier and cannot derive one
from a trajectory, and a results screen guessing at the headline number is
worse than one that leaves it out. They are in the rail and on the scoreboard.

In the rail (the ▤ drawer, shut until asked for):

- **`eff_round`** as the headline, with the autarky floor marked on its meter.
  Accumulated utility against the frontier of the total — the primary.
- **Efficiency per episode**, with the floor as a reference line, and the
  standing warning that it is a coverage measure and not welfare: one trader at
  zero puts the whole vector maximally far from the frontier however well the
  others did.
- **Utility by trader** — each trader's per-episode series with their autarky
  level as the reference, and the accumulated total beside their name. That
  total is the object `eff_round` is scored on, which is why a trader ruined in
  one episode and fed in the rest still shows a positive round.
- **Diagnostics** the medians hide: the `eff_round` bracket, gains at the median
  and worst trader, how many ended below autarky, how many trader-episodes were
  zero, and the first episode that beat the floor.

## Deploying

`.github/workflows/pages.yml`, at the repo root, publishes `web/`, `results/`
and `games/replays/` to `https://gald33.github.io/ai-lab/island/` on every push
to `main` that touches this directory or a published replay. **Under
`island/`, because the island is one game and the root is a games index** — a
game that owns the whole site is a site to be rearranged the moment a second
one wants a page. The tree moves whole and nothing in `web/` changes, since it
all fetches by relative path. The root redirects there, carrying `?` and `#`
across, so the links written down before this move — `games/runs/001` and
`002` each cite the root as where their replay outlives its room — still
resolve. The staged site's
directory names are `serve.py:ROOTS`' prefixes, which is what `api/boards`
names — so the copy and the listing cannot disagree about where a board is. Same origin switchboard's own published viewer uses
— a different path under `gald33.github.io`, not a different origin — so the
managed hub's existing `SWITCHBOARD_CORS_ORIGINS` already covers this page
for the hub-direct live feed with no change on that side.

`web/` fetches `api/boards` and `api/scores` as relative paths, which
`serve.py` answers from a running process; a static host has none, so the
workflow runs `freeze_static.py` to compute the same two answers once and
write them to disk under those paths before publishing. Nothing in `web/`
changes because of it — replay and the scoreboard read exactly what they
always did.

One manual step, once per repo, unavoidably: *Settings → Pages → Build and
deployment → Source: GitHub Actions*. The workflow's own token cannot flip it
— that needs admin — so the first run fails at `configure-pages` with a bare
`Not Found` until it is set by hand. Re-run afterwards.

## The scoreboard

A round that is over should still be worth something, so every finished round is
recorded and the boards are read back out of that record.

```bash
python viewer/scores.py --ingest results/*/v3.json    # add finished rounds
python viewer/scores.py --table                       # the boards
python viewer/scores.py --verify                      # recompute every row
```

![the scoreboard](docs/scoreboard.png)

**A game is one attempt, and may be more than one round.** A *round* is what the
manager runs — `k` episodes on one island — and that vocabulary does not move. A
*game* is the unit somebody enters: one round, or several played as a single
attempt. A one-round game is a legitimate format and its score is that round; a
several-round game scores the **median** of its rounds, so within a declared
format the luck evens out, while a lucky game still tops the board.

The rounds in a game have to be declared as one **before they are played**, or
the median is worthless: ten rounds played and the best three called "a game"
afterwards is cherry-picking with a statistic on top. A game short of the rounds
it declared is kept, counted, and not ranked — abandoning the rounds that went
badly is the cheapest way to launder a median. The runner is what stamps the
game, at launch, next to where it binds identities; nothing an agent says about
which game it is in can be believed.

Until joining exists nothing declares a game, so every recorded round is a
one-round game and the boards read exactly as they did before this existed.

**Two scores, because two things are being played.**

*The table's.* **`capture`** — how much of the gains actually on this island got
taken, with autarky at 0.0 and the frontier at 1.0. It belongs to the whole set
of traders rather than to any one of them.

Not raw `eff_round`: two islands are not equally hard, so ranking on raw
efficiency ranks the draw. Among the rounds recorded here, a 0.734 against a
floor of 0.823 sits fourth on a raw board while those traders ended up
substantially worse off than never trading. `barter.economy.capture` already
makes this argument and this uses it. Negative is not clamped.

*A trader's.* `u_i / autarky_i` — what they ended with as a multiple of what they
would have had **alone**. Raw Cobb-Douglas utilities are not comparable between
traders, so "T1 got more than T2" means nothing; "T1 ended at 1.4× what it would
have had alone" means something, and those ratios are comparable, being pure
numbers against a per-trader baseline. That argument is
`barter.economy.gains`'s, and this reuses it rather than restating it. **1.00× is
the line**: below it, trading left them worse off than never trading.

**The format is the level** — traders, goods, episodes. Not the seed: the island
is drawn per round, so a seed is a roll rather than a level, and `capture` is
what puts two rolls on one scale. Four traders still face a different frontier
from two, and thirty episodes is still more room to learn than three.

**A player is ranked on their best game.** A lucky island, or a partner who
happened to want what you could make, still counts — that is what a high score
is, and a board that averages it away is a statistics table wearing a trophy.
Inside a game of several rounds the median has already taken the luck out to
whatever degree that format asked for. The median across games, the worst, and
the game and round counts sit beside the best, so a top score that was one game
is visible as one.

### What the ledger will not do

- **Believe anybody.** Every figure is recomputed from the run record and the
  round's seed: the island is redrawn, autarky is resolved, and a row whose
  recorded `eff_round` disagrees with what its seed produces is refused rather
  than written down. No agent's account of how it did is read anywhere.
- **Lose a round.** `scores/ledger.jsonl` is append-only and a round's id is a
  hash of its own content, so re-ingesting cannot duplicate it and re-running
  cannot quietly replace it.
- **Drop a failure from a denominator.** A round nobody reached is not a round
  somebody lost: it is recorded, kept out of the ranking, and still counted in
  every "of N". Rounds that ran before the manager kept a list of who reached
  the board are marked as having unrecorded attendance rather than assumed fine.
- **Need this file to be believed.** Each row carries its seed, its trajectory
  and the digest of the board it came from, so anybody can re-derive it without
  trusting the ledger.
- **Confuse a schema change with tampering.** Rows carry the version they were
  built under. When `digest` moved from hashing a board's bytes to hashing its
  contents, every stored digest became unreproducible at once, and an
  unversioned ledger reported that as ten boards having changed. A row built by
  an older version is re-ingestable, and `--verify` says so instead.
- **Serve a ranking nobody asked for any more.** The derived boards are keyed on
  the ledger *and* on the version of the rule that read it, because a ranking
  that changes while the record does not is exactly when a cache keyed only on
  the record keeps answering with the old order.

### Keeping many rounds

Three different things scale differently, and only one of them was a problem.

**Watching a replay does not care how many there are.** A replay is two files —
the board and its sidecar, about 17 KiB — and you fetch the one you are
watching. That is the same work at ten rounds and at ten thousand.

**Reading the boards did care.** Parsing the whole ledger and recomputing the
leaderboards on every request is a page that gets slower every time somebody
plays: measured on one machine at 72,000 rounds, 4.6 s to parse plus 0.9 s to
compute, for a 16 KiB answer that does not grow. So the ledger stays the record
and the page reads `scores/boards.json`, derived and rewritten when rounds are
added — **0.2 ms**, whatever the ledger holds. The cache carries the stamp of
the parts it was built from; a stale or damaged one is rebuilt rather than
trusted, so deleting it only ever costs one recomputation. `--refresh` forces it.

Ingest checks `scores/index.json` — round ids and nothing else — instead of
re-reading every round to ask whether it has seen this one.

**Storage grows with what you keep.** A board is mostly the manager saying
similar things, so it packs about sevenfold:

```bash
python viewer/scores.py --pack     # 109 KiB → 19 KiB across ten boards
```

Each is read back and compared before the original is removed. Afterwards the
board is a `.json.gz`, and nothing else changes: `serve.py` answers a request
for the unpacked name with `Content-Encoding: gzip`, so saved links keep
working and the page never learns; every reader here — `scores.py`,
`tests/board.mjs`, the tests — accepts either name; and the digest a ledger row
carries is of the board's *contents*, so packing does not make `--verify` claim
the board has changed.

The ledger itself is line-oriented and append-only, so old parts can be rolled
off and gzipped — `ledger-2026-08.jsonl.gz` beside `ledger.jsonl` — and are read
back with it.

What is **not** solved: where thousands of boards live. Forty megabytes of
replays does not belong in a git repository, and that decision belongs with the
joining mechanics rather than ahead of them.

### Known, and open until joining exists

A player is currently whatever the run record called the model. Real entrants
need identities bound by the runner at launch — the same place `Manager.bind`
binds a Switchboard peer to a trader name — never claimed on the board, because
a name an agent types is a self-report.

And the trader board is farmable by anyone running both seats: a partner who
gives everything away goes to zero and inflates the other's ratio. Ranking on
the best game makes that cheaper — one arranged game is enough, and a one-round
game is one round — so the rule about who may sit at a *ranked* table matters
more, not less. It belongs with
the joining mechanics; until then the ledger records every player in every round
so such a rule can be applied to what is already there.

## The sidecar

```bash
python viewer/reveal.py --seed 1 --agents 2 --goods 4 \
    --result results/v3/v3.json --workspace island6-bare-1 \
    --check results/v3/board-island6-bare-1.json \
    -o results/v3/reveal-island6-bare-1.json
```

`--check` is the honest test of the whole wrapper: it replays the board through
the same reducer the page uses, rebuilds each trader's holdings from the
receipts, and compares the resulting utilities against the trajectory the
manager scored. All ten saved boards agree to **6.8e-05 or better**.

They do not agree exactly, and cannot: `Manager._produce` writes `round(qty, 4)`
into its receipt while keeping full precision internally. A spectator rebuilding
stocks from receipts is accurate to ~1e-4 in quantity and ~2e-5 in utility and no
better. That is a property of the record, not a fault in the reader — and it is
the reason the replay shows the *recorded* score rather than its own.

## Tests

```bash
node --test "viewer/tests/*.test.mjs"            # the page: 48
python -m pytest viewer/tests/ -q                # the ledger and the roots: 104
python viewer/tests/render.py                    # the drawing, in a real browser
```

The ones that matter: a self-report moves nothing, a line that is
nearly a receipt is not repaired into one, **every saved board parses with
nothing left over** — which is what will fail if `island/manager.py` or
`run_v3.py` is reworded, rather than the island quietly emptying — and **every
board with a sidecar reproduces the manager's scored trajectory** through the
page's own reducer and utility code.

On the pacing: **an eventful frame is held until its animation has played**,
at every speed. Before that, `feeds.js` stepped every `MIN_STEP / speed` --
35ms at the default `4x` -- while a parcel took a second to cross the square,
so a busy stretch played six animations on top of each other and read as a
flicker. `scene.js:DWELL` names how long each event needs and `feeds.js` reads
it, so the floor cannot drift from the durations it mirrors. Speed still
compresses the silence between events; it no longer compresses the events, so
`16x` is not sixteen times faster on a busy board. That is deliberate.

On the drawing: the geometry is pure arithmetic and is checked as such --
every card and hut **fits on the canvas** and **no two cards overlap** at one
through eight traders, and **scenery lands on neither a card nor the fire**.
That last one is a bug that shipped: placement used to test a circle around the
seat while a card is a tall box hanging *below* it, so palms rendered on top of
the shelves. `render.py` covers what arithmetic cannot -- it loads a replay in
Chromium, asserts the page raises nothing and has one hut per trader and one
shelf cell per good, plays a receipt at the scene to confirm the **event
animations actually run**, and renders a four-trader board, which no saved
replay is. It **skips** when Playwright or Chromium is absent, so a checkout
never has to install a browser to run the free suites.

**The island's clock is checked on the light, not on a screenshot.**
`render.py:clockwork` drives a stage through a bell and the dawn after it, a
midday and a bell, and a day told where it is going, and reads the key light's
bearing, a flame's emissive level and `Stage.dayNow()` straight off the stage.
All three were reported by eye against `island-game-001d-g1` and none of them
is a brightness: a picture can say how bright a frame came out, not where the
sun is standing. What it holds shut: a hold does not move the bearing, the fire
is dark at midday and up at the bell, and the day travels between two board
events instead of freezing at the last line.

`clockwork` drives the stage directly, which would hold the glide shut without
ever asking whether the page uses it — and the wiring was the whole bug, so
`travelling` plays a real replay and watches `window.__island` cross a gap
between two lines. Both were confirmed against the behaviour they describe
before it was fixed: the bearing check reports the 2.16-radian sweep, the fire
check reports it alight at midday, and `travelling` reports a day that never
travelled at all.

**Measured on the land, not on the canvas.** Several of these checks used to
ask "is this pixel opaque?" and mean "is this the island?", which was true while
the model drew on a transparent canvas with a disc of water a little wider than
the shore. The sea reaches the frame's edge now, so opacity answers *yes*
everywhere and those questions stopped being questions. Two answers, depending
on what is being asked: `uncovered` and `alive` classify by colour — water is
the only strongly blue surface a spectator sees much of, and it stays blue under
every hour's light because the fill is the sea's own colour — and `mechanics`
crops its shots to the rectangle the island is drawn into, which is exactly the
denominator it had before. A card over open sea was always fine; the cards live
in the margins and the margins are water.

That sweep missed one, and `mobile` went on measuring the island by alpha for
long enough to make every island-size assertion in it vacuous — it was reporting
the island as 2.3 times the band it was given, because it was reporting the
whole canvas. Found while adding `focusing`, and written up
[above](#a-check-that-could-not-fail). The lesson is not "grep harder": it is
that a check whose numbers nobody looks at can pass for weeks on a question it
has stopped asking.

And on the live side: `rowsFromState` against `tests/fixtures/snapshot-sample.json`,
a real snapshot from a real hub rather than a shape assumed by hand — this is
what fails if either Switchboard viewer ever changed the fields it hands this
page, instead of the live view quietly going blank. Regenerated the same way
`switchboard`'s own `tests/test_web_snapshot.py` builds one, captured once
rather than reimplemented here.

On the ledger side: every round in every run record is re-scored from its seed
and has to come out equal to what the manager recorded — including the
per-trader ratios, which are checked against the gains it wrote down at the
time — plus the refusals: a record that disagrees with its seed, a re-ingest
that would duplicate, an edited row, and a denominator that drops a failure.

## Files

| | |
|---|---|
| `web/reducer.js` | board text → a scrubbable timeline. Pure, and the only place the manager's wording is known |
| `web/scene.js` | the island, drawn from a state |
| `web/utility.js` | Cobb-Douglas, and the audit against the recorded score. Cannot run live |
| `web/feeds.js` | the three feeds, and the replay clock |
| `web/index.html` | the page: the island, and the chrome floating over it |
| `serve.py` | static files, the board list, the scores API, and the `api/state` forward |
| `freeze_static.py` | writes `api/boards` and `api/scores` as files, for a static deploy |
| `scores.py` | the ledger: recording finished rounds and reading the boards out |
| `web/scores.html` | the scoreboard |
| `web/tokens.css` | the palette, shared by both pages |
| `scores/ledger.jsonl` | every recorded round, append-only. `ledger-*.jsonl.gz` parts are read with it |
| `scores/boards.json` | the leaderboards, derived; rebuilt whenever it falls behind the record |
| `scores/index.json` | round ids, so ingest need not re-read every round |
| `tests/board.mjs` | reading a saved board, packed or not |
| `palette.py` | the contrast and colour-blindness gates `tokens.css` describes |
| `tests/test_palette.py` | those gates, run — including that the comment matches the palette |
| `tests/scene.test.mjs` | the island's geometry — seats, cards, coastline, scenery placement |
| `tests/render.py` | the drawing itself, in a real browser; skips without one |
| `tests/live.test.mjs` | `rowsFromState` against a real snapshot, not an assumed shape |
| `tests/fixtures/snapshot-sample.json` | that snapshot — a real hub, captured once |
| `reveal.py` | the hidden half, after the fact, with `--check` |

## Notes on the drawing

**The island is the page.** Not a panel in a dashboard with a picture in it:
the scene fills the window and everything else floats over it — the title and
the round's state top-left, the counters top-right, the transport along the
bottom, the legend in the corner. The two panels that used to sit beside it are
**drawers, shut until asked for**: `▤` for the hidden half and who has spoken,
`☰` for the board's full transcript. `Esc` shuts both; `Space` plays. Chrome
steps aside when a drawer opens rather than being buried by it — a drawer that
covers the control which shuts it is a trap.

**The palette is checked, not claimed.** `tokens.css` used to carry its
contrast and CVD numbers in a comment that nothing recomputed, and two of them
were wrong: `--util` was *byte-identical* to `--good-5`, and `--eff` sat at CVD
ΔE **1.6** from `--good-1` — so the headline metric and the bread bar were
already one colour to a red-green dichromat, at four goods, while the comment
said 16.0. `palette.py` implements the gates (WCAG contrast, CIEDE2000, Viénot
dichromacy) and `tests/test_palette.py` runs them, including a test that the
numbers written in the stylesheet are the numbers it actually has. The metrics
are cyan and gold now, which is what the series leaves free.

**Watched, then fixed.** Five things about the drawing were reported by
somebody looking at it and by nothing else, and each is worth the note because
none of them is a defect a still screenshot shows.

* **The greens were olive.** `grass` and `grass_dark` sat around a hue of 100°
  — a third of the way to yellow before any light touched them — under a key
  that is warm all day and frankly orange by the bell, so the island read as a
  yellow one. Moved to 120–130°, which is a leaf. The warmth in the picture is
  the light's now, and it still goes gold at dusk because the light does.
* **Blue flickered round the coast.** The deep sea's top face and the shore
  shelf's underside were both at exactly `y=0` — two coplanar surfaces fighting
  for every pixel where they overlap, which is the whole coast. Z-fighting only
  shows while the camera moves, so no still frame could catch it and nothing in
  the suite could either. `island()` now asks the *model* whether two of its big
  horizontal surfaces share a plane, which is a question about two numbers.
* **The water was a circle and the island is not.** The surf ring was a torus,
  so it ran along the sand on one bearing and sat half a unit out to sea on the
  next. Surf and shallows follow the shore's own silhouette now — the same
  wobble the land is extruded from.
* **The island was crowded, and things stood inside each other.** Every prop was
  built about a third again its drawn size, and the planting's keep-out list
  held what the island had placed on purpose and nothing else — so two trees a
  tenth of a unit apart shared a trunk. The scales came down together (shrinking
  one only makes the rest look bigger) and every tree planted joins the keep-out
  list. Taken down twice: a fifth off was still reported as crowded, and the
  props stand at about three-quarters of what the model shipped with.

  The second half of that was worse and no screenshot showed it. **The
  settlements were separated from each other and from nothing else** — the good
  sites are laid on their own ring at their own radii and nothing compared the
  two, so a hut came down 0.63 units from the fish site, well inside it.
  `spaced()` takes fixed obstacles now, and `island()` asks whether *any* two
  things the island placed on purpose are within a metre of each other; against
  the old placement it reports 25.
* **Three flags were drawn inside the mountain.** A site is placed by its
  origin and its parts are not: the group asks the island how high it is at one
  point and everything inside it inherits that one answer, which is right on
  the flat and wrong on a slope. The iron site stands at radius 1.7, a hair
  outside the upland's own 1.55, so the offsets its parts are built at carried
  them into the side of the hill — the flags by a twentieth of a unit, which is
  a third of a flag, and the quarry's own spoil by six tenths. `follow()` adds
  the terrain under each part on top of the height it was *designed* at, so a
  salt pan still sits a little into the sand and a quarry terrace is still cut
  into the rock.

  A ray from the camera to each flag was tried as the check, because that reads
  like the complaint, and it was **taken out again: it could not be made to
  fail.** A flag is 0.16 tall, so even one genuinely under the ground catches
  the ray on its top half — the check answers yes to everything, and 600
  raycasts a frame shape bought nothing that measuring the clearance beneath
  the flag does not.

* **And the quarry was inside the hill.** Reported by eye, and the line above —
  "a quarry terrace is still cut into the rock" — is the assumption that hid
  it. `follow()` corrects for the *slope across a site*, which on this island
  is a hundredth of a unit. It says nothing about a part built below its own
  origin, and the quarry's three terraces were built at −0.08, −0.24 and −0.40:
  the first's top face exactly at the grass, the third a third of a unit under
  it. What showed was a flag, a cart and two lumps of spoil.

  Cutting downward is what a quarry *is*, and on a grass hill it is three slabs
  of rock nobody can see. A hillside quarry seen from below is a stepped rock
  face, so that is what it is: three ledges standing on the ground, each
  stepping back uphill and up. The cut faces are what says stone.

  `render.py:island` now measures **every part of every site** against the
  ground under it — the flags were one part of one kind — and at the part's
  **top**, against zero rather than a margin. A thing may stand into the slope
  and still be there to look at: the salt pans are bedded into the sand and
  clear by two hundredths at the biggest tables, so any floor generous enough
  to be a margin fails them, and the quarry never needed one. Neutered back to
  cutting downward it reports all three terraces, in every frame shape.

* **The shockwaves are gone.** Five clips fired expanding rings, and a
  production of four goods put four up at once with an offer's and a bell's
  arriving on top at 4×. Cut to three first, then to none: the second report
  said simply that they were too distracting to read past. What replaced them
  is a **patch of light lying on the ground** at the place the thing happened —
  the same area a ring covered, all of it at once, and it never moves, so
  several at once read as several places rather than as a pile. `mechanics()`
  is what kept this honest: the three clips that lost a ring fell straight
  through its visibility floor, which said out loud that the ring had been the
  only thing carrying them.

* **A pale ellipse circled the island, and rode over it.** Reported by eye, and
  it was not in the model at all: `.shallows` is the *drawn* island's outer
  glow — a 26px stroke of the SVG coastline at 4.5% opacity, which is what
  stands in for scattered light in the shallows on a browser with no WebGL.
  When the model loads, `.has-3d` hides the drawn world, and that rule listed
  `.land`, `.wet`, `.surf`, `.water`, `.sea-fill` and the hut's parts — but not
  `.shallows`, and not `.grain-fill` either. So a 2D coastline kept drawing
  over the 3D scene at the 2D island's size and place, which are not the
  model's: it sat out to sea on one bearing and up over the sand on the next.
  The same shape the surf ring used to have, arrived at from the other side.
  Both classes are in the hide rule now. The check that would have caught it is
  the one `check()` already does for `.land` — *visible*, not merely present —
  and it was asked about one class out of the group it belongs to.

**One mark per good.** The legend's glyph rides *on* its colour rather than
beside it, because that is the chip that appears on a shelf and on a parcel in
flight; two marks side by side are a pairing the reader has to learn.

**An episode is a day.** It opens, it runs, a bell closes it and everything
held is consumed -- so the sun rises when an episode opens and goes down behind
the island at the bell, and the campfire is the brightest thing left. Night is
a *state* (`.island.closed`), not a flash: scrub to a closed frame and it is
dark, with no event needing to have been played to put it there. The fire is
drawn above the dark on purpose -- where it used to sit, dusk fell on it too
and the campfire got dimmer as the day ended.

**Nothing anybody said is printed on the island.** A refusal is a ✗ badge with
the manager's reason as its `<title>`; a trader speaking is a speech bubble;
production is the goods themselves lifting onto the shelf. The words are in the
ticker underneath, where they are readable. An **attempt** draws nothing at
all -- what it attempted arrives as the receipt or the refusal, and drawing
both would say it twice.

Goods hold a **fixed position** on every shelf and always wear their glyph, so
identity is never colour alone. The palette is the four dark categorical slots,
validated against this page's own surface (`#171d21`): worst adjacent CVD ΔE 8.4,
worst normal-vision ΔE 19.8, all ≥3:1 on the surface. Those gates pass for
*adjacent* pairs, which is the pairlist a fixed-order shelf is read on; they do
not pass all-pairs, which is exactly why position and glyph do the identifying
and colour only reinforces it.

Metrics wear two hues of their own — violet for efficiency, magenta for utility
— kept off the goods palette so a score can never be mistaken for a stock. Both
clear the all-pairs gates against the same surface (CVD ΔE 16.0, normal-vision
19.7).

One committed dark look: this is an island at dusk, and a light mode would be a
different picture rather than the same one lit differently. Every animation is
skipped under `prefers-reduced-motion`.
