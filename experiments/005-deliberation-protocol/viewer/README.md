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

**No number it computed itself.** `eff_round` and the per-episode series are the
manager's, read from the recorded round. A page that recomputed the metric would
be a second implementation of it, and the two would drift.

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

## The two feeds

**Live** reads the Switchboard viewer's `api/state`, never the hub. That is the
whole architecture: the viewer holds the token, the key and the read cursors, so
this page inherits its safety properties — it cannot post, cannot register, and
cannot advance any agent's cursor. `serve.py` forwards `api/state` so the two
share an origin, which they must: `api/state` sends no CORS headers, so a page
served from anywhere else cannot read it at all.

**Replay** reads a saved board — `results/**/board-*.json`, `{seq, at, author,
body}` — and its sidecar if one exists. Transport, scrubbing, episode chapters,
1×/4×/16×. Silence is compressed (a 60s gap between two messages is not 60s of
still picture) and the pause is labelled rather than hidden.

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
node --test "viewer/tests/*.test.mjs"
```

Nine tests. The ones that matter: a self-report moves nothing, a line that is
nearly a receipt is not repaired into one, and **every saved board parses with
nothing left over** — which is what will fail if `island/manager.py` or
`run_v3.py` is reworded, rather than the island quietly emptying.

## Files

| | |
|---|---|
| `web/reducer.js` | board text → a scrubbable timeline. Pure, and the only place the manager's wording is known |
| `web/scene.js` | the island, drawn from a state |
| `web/feeds.js` | the two feeds, and the replay clock |
| `web/index.html` | the page: HUD, ticker, transport, the hidden half |
| `serve.py` | static files, the board list, and the `api/state` forward |
| `reveal.py` | the hidden half, after the fact, with `--check` |

## Notes on the drawing

Goods hold a **fixed position** on every shelf and always wear their glyph, so
identity is never colour alone. The palette is the four dark categorical slots,
validated against this page's own surface (`#171d21`): worst adjacent CVD ΔE 8.4,
worst normal-vision ΔE 19.8, all ≥3:1 on the surface. Those gates pass for
*adjacent* pairs, which is the pairlist a fixed-order shelf is read on; they do
not pass all-pairs, which is exactly why position and glyph do the identifying
and colour only reinforces it.

One committed dark look: this is an island at dusk, and a light mode would be a
different picture rather than the same one lit differently. Every animation is
skipped under `prefers-reduced-motion`.
