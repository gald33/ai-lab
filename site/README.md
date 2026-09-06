# the front door

`https://gald33.github.io/ai-lab/` — what somebody sees who has just been told
"bring your own agent, there's a high score waiting to be broken".

The reasoning is in [`games/island.md`](../games/island.md), under **"The score
nobody could beat"** and **"The front door is a page, not a redirect"**. What is
here is the shape of the directory.

| file | what it is |
|---|---|
| `index.html` | the landing page, and the redirect the old root used to be |
| `landing.css` | its stylesheet; palette from `island/tokens.css` |
| `landing.js` | the score to beat, read off `island/api/scores` |
| `card.html` | the social card, as a page |
| `make_card.py` | renders `card.html` to `card.png` at 1200×630 |
| `card.png` | what a posted link renders as. Generated, not drawn |
| `tests/` | driven in a browser, per `CLAUDE.md` |

`.github/workflows/pages.yml` copies the first three plus `card.png` to the
site root. Everything else here is source.

## The two things that are easy to break

**The redirect contract.** A bare visit gets the landing page; anything with a
`?` or a `#` still hops into `island/` carrying it. `games/runs/001` and `002`
cite the root as where a finished game's replay lives, and a live feed arrives
as `?invite=…` on exactly those links. `tests/test_landing.py` drives every one
of those shapes in a browser. Do not "simplify" the hop away.

**The card is static.** A crawler does not run scripts, so nothing fetched can
appear in the Open Graph tags — the score included. If the card should ever
quote a live number, that needs a rendering step at publish time, not a script
on the page.

## Working on it

    python -m pytest site/tests -q                    # skips without a browser
    ISLAND_REQUIRE_BROWSER=1 python -m pytest site/tests -q   # what CI runs

    python site/make_card.py            # re-render the card after editing it
    python site/make_card.py --check    # is the committed PNG still the source's?

To look at it, serve the repo root with `island/` in place — the page fetches
`island/api/scores`, which a `file://` page cannot do:

    python -m http.server 8080
