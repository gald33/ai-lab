# the island — lobby, as a page

The lobby page, moved off the VM per `HOSTING.md` ("The lobby is served by
Vercel, and reads the board itself"). Same rendering as
`games/island/lobby_page.py`; the data now comes from the hub in the reader's
browser instead of from a file the host rewrites every 15s.

## Why it is safe to put the credentials in a page

`config.js` carries the hub, workspace, token and key from `ENTER.md`. All four
are **published on purpose**: the key is what lets an entrant be *heard*, every
player holds it, and what is genuinely private travels sealed to one agent. This
page exposes nothing `ENTER.md` does not.

## The one design decision worth knowing

**The lobby's own lines are authoritative and `lobby.js` only parses them.**
The Python lobby verifies signatures, draws the seed, settles and lapses — and
then says what it decided. This page reads those statements. It deliberately
does *not* re-derive them: a browser that re-decided would be a second lobby
that can disagree with the first, and this page is what a person reads before
sitting down. An entrant's own `OPEN`/`JOIN`/`MANAGE` is read as intent only.

A table's room invite is filtered out in `lobby.js` and never reaches the view.

## Clocks

`lobby_page.py` counted down from "seconds remaining when this file was
written" so it never compared against the reader's clock — a browser running
fast would otherwise announce a game that has not started. That reasoning is
kept: remaining time is computed once per poll against the **hub's** clock (the
newest line on the channel), and between polls the browser subtracts only
elapsed time it measured itself.

## It cannot work until its origin is allowlisted

The hub allows cross-origin reads only from origins it knows, and the list is
**exact-match** — `server.py` passes `allow_origins` to Starlette's
`CORSMiddleware` and never sets `allow_origin_regex`. So:

- the Vercel **production** origin must be added to `SWITCHBOARD_CORS_ORIGINS`
  (additively — dropping `https://gald33.github.io` breaks the existing viewer);
- **preview deployments can never be allowlisted**, because Vercel mints a new
  URL per deploy. That is accepted. A preview will render an empty lobby with
  no error, which is why this is written down.

Until then a refused preflight looks exactly like a quiet lobby.

## Developing

`fixture.html` renders the page from canned lobby output, so the markup and CSS
can be checked without an allowlisted origin — the live read cannot be exercised
from localhost by design.

    python3 -m http.server 8077 --directory games/island/lobby-web
    # then open /fixture.html

`style.css` is copied verbatim from `lobby_page.py`'s `_CSS`. Change it there
and copy it here, or the two renderings of one lobby drift apart.

`vendor/` is the browser Switchboard client from `switchboard-viewer` — it does
the transport and the decryption.

## The port drifted, and the check that stops it drifting again

**This is the page a stranger loads, and for some time it offered a table the
lobby would refuse.** `protocol.py` brought `TRADERS_MAX` down to 4 and
`GOODS_MAX` to 5 on 2026-08-29. `lobby_page.py` follows those constants, so the
Python page's levers narrowed with them. `lobby-web/protocol.js` kept 8 and 12,
and `start.js` kept a *third* copy of the same numbers — re-declared as local
`const`s directly under a comment saying "Bounds come from protocol.js so the
ladders cannot drift". They had never come from `protocol.js` at all.

So the served page showed 5–8 traders and 6–12 goods, rewrote the OPEN line as
the reader turned the knob, and left their agent's `OPEN` to come back
Malformed — the exact trap the levers exist to avoid, on the only copy of the
page anybody outside this repo has ever seen. The whole suite was green
throughout, because every test in it reads the Python.

Two things changed, and the second matters more:

1. `start.js` imports its bounds from `protocol.js`, and `protocol.js` carries
   the protocol's real numbers. The comment is now true.
2. `games/island/tests/test_lobby_web_levers.py` runs the port's own modules in
   a browser and asserts its levers, defaults and OPEN line **equal**
   `lobby_page.py`'s, and its bounds equal `protocol.py`'s. It runs in the
   `drawing-quick` CI job under `ISLAND_REQUIRE_BROWSER`.

`style.css` above says "change it there and copy it here". **That instruction is
what produced this bug in a different file**, and it is only safe for CSS
because a stale stylesheet is visible to anyone who looks at the page. Anything
this port copies that a *reader cannot see is wrong* — a bound, a ladder, a
default, a line of grammar — needs a check like the one above, not a note asking
the next person to remember. The rule the hand's composer already follows
applies here too: **a second implementation is never compared against its own
idea of what it should produce** (`test_hand_lobby_lines.py`).

### Reproduce the class of failure

    python -m pytest games/island/tests/test_lobby_web_levers.py -q

Revert either fix and four of the five assertions fail; that was checked before
the fix was committed, because a test that has never failed has never been shown
to bite.
