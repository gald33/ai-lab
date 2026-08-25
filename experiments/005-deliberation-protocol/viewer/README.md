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
| a rope across the square | an open proposal, with what it offers for what |
| goods in flight | a settled exchange, both directions at once |
| a red card outline | holding some goods and none of another — a zero episode |
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
and `games/replays/` to `https://gald33.github.io/ai-lab/` on every push to
`main` that touches this directory or a published replay. The staged site's
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
