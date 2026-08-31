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
