# the legacy root

`https://gald33.github.io/ai-lab/` — not the front door. That is
`https://island.lucille-ai.com/`, decided by Gal 2026-09-07, and the landing
page lives in [`games/island/lobby-web/`](../games/island/lobby-web/) where
Vercel deploys it.

What is left here is the half of this page that was never about the landing
page: **the hop that older records depend on**.

| file | what it is |
|---|---|
| `index.html` | the hop, and a line saying where the door went |
| `tests/` | driven in a browser, per `CLAUDE.md` |

`.github/workflows/pages.yml` copies `index.html` to the site root. Its
stylesheet is `island/tokens.css`, staged by the same job, so there is nothing
else to copy.

## The thing that is easy to break

**The redirect contract.** Anything arriving with a `?` or a `#` hops into
`island/` **on this origin**, carrying itself. `games/runs/001` and `002` cite
this root as where a finished game's replay outlives its Switchboard room, and
a live feed arrives as `?invite=…` on exactly those links — and the replay each
one names is a file here, not on the main door. Only a bare visit is sent
onward. `tests/test_landing.py` drives every one of those shapes in a browser.
Do not "simplify" the hop away, and do not let the bare-visit redirect swallow
the query one.

The card tags here name the main door on purpose: a legacy link that is still
posted should render the card of the page it will actually land on.

## Working on it

    python -m pytest site/tests -q                    # skips without a browser
    ISLAND_REQUIRE_BROWSER=1 python -m pytest site/tests -q   # what CI runs

The landing page's own checks moved with it:

    ISLAND_REQUIRE_BROWSER=1 python -m pytest games/island/tests/test_front_door.py -q
