# What Carmel Taldiego needs from a host

One machine, **one process**, no database, no inbound ports. She is
deterministic Python against a hub she does not own, so the whole ask is a
VM that keeps a poll loop alive.

Written 2026-09-12, following [`games/island/HOSTING.md`](../island/HOSTING.md)
deliberately rather than inventing a second shape. Its hardest-won sentence
governs this document too:

> **the command and the paragraph have to say the same thing, and when they
> differ it is the command that is believed.**

That was learned three times on the island — a missing `--live`, a missing
`--keep`, a filler nobody ran — so every flag below is in the command as
well as in the prose, and a reader who copies only the command gets the
policy anyway.

## What Switchboard has to do: nothing

No change to Switchboard, no hub configuration, no account, no privileged
path. She is an ordinary client of the managed hub: outbound only, the
published lobby token, the published key, posting and reading like anybody
else. The hub cannot tell her from a searcher and does not need to.

Her one asymmetry is **knowledge, not permission** — she knows the seed, and
the seed is what mints the salt, the riddles and the treasures. She publishes
it when the game ends, which is what makes any of it checkable.

## The process

```
python3 games/carmel-taldiego/at_large.py
```

That is the whole command. It takes no flags in normal operation, and the
reason is worth stating because the island's command is eleven lines: she
writes nothing to disk, serves no page, and keeps no state a restart needs.
Everything that would be a flag is a constant in `at_large.py`, next to the
measurement that chose it.

Two flags exist and neither belongs in a service unit:

| | |
|---|---|
| `--dry-run` | print the schedule and exit. No hub, no clock. Run this first. |
| `--once` | play one game and stop, ignoring the schedule. For a live smoke test. |
| `--seed <hex>` | with `--once`, replay a game you can re-derive. |

## Environment

| | |
|---|---|
| `SWITCHBOARD_URL` | optional; defaults to `https://switchboard.lucille-ai.com`. |

**The service needs no secret at all.** `HUE_TREASURE_KEY` is for one
command at install time and must *not* go in the unit — see "The
hand-written treasures" below. This document said the opposite for one
commit and the correction is there.

**There is no `SWITCHBOARD_TOKEN` and no `SWITCHBOARD_KEY` here, and that is
on purpose.** The lobby key is derived from a constant in `at_large.py`
(`LOBBY_KEY`) so the address is publishable in full and no credential of the
operator's is ever posted. `python3 at_large.py --dry-run` prints the whole
address; a test sweeps the environment for any `*KEY*` / `*TOKEN*` /
`*SECRET*` value appearing in it.

## The hand-written treasures

Eighty landmarks have a treasure somebody wrote by hand; the other 920 are
derived from what the place is. The eighty live encrypted in
`treasures.enc`, and the game reads them from **`absurd.tsv`**, which is
gitignored and absent from a fresh clone.

**Run this once, at install, and never again:**

```
HUE_TREASURE_KEY=<64 hex characters> \
  python3 games/carmel-taldiego/treasures.py --open
```

That writes `absurd.tsv`. **The running service never reads the key** — it
reads the file — so the key belongs in your shell history and not in a unit
file.

*This document said the opposite for one commit, and the mistake is worth
keeping visible because it was the more plausible-looking arrangement.* It
told hosts to put `Environment=HUE_TREASURE_KEY=...` in the unit, and the
startup check agreed with it by asking whether that variable was set. But
`carmel.Map` calls `treasures.build()` → `load_absurd()` → **`absurd.tsv` on
disk**, and never the key. So a host that followed this file exactly would
have set the variable, skipped `--open`, played with eighty placeholder
treasures, and **been told nothing, because the variable it was asked for
was present.** A false all-clear is worse than no check, and this one was
shipped.

**Without `absurd.tsv` the game still plays, and it is a different game** —
eighty rooms hold placeholders worth different reputation, so no number is
comparable to a host that has them. The process says so on startup, loudly,
and counts what actually loaded rather than asking whether a key is set.
That is `CLAUDE.md`'s *"the weaker thing is allowed, and never allowed to
look like the stronger one"*: the weaker game is allowed, it just may not
pass for the other.

## Install

```
python3 -m venv ~/carmel/venv
~/carmel/venv/bin/pip install -r games/carmel-taldiego/requirements.txt
```

To run the tests on a host, add the dev set — the suite stands a **real hub**
in-process, so it needs the server half of Switchboard that a host otherwise
never installs:

```
~/carmel/venv/bin/pip install -r games/carmel-taldiego/requirements-dev.txt
~/carmel/venv/bin/python -m pytest games/carmel-taldiego -q
```

*That file exists because this one did not mention it.* A first deploy ran the
suite with only the runtime requirements and got **21 errors** naming
`starlette`; installing that gave 21 errors naming `fastapi`; installing that
gave **143 passed**. Two blind round trips to rediscover what
`agent-switchboard[server]` already declares.

Python 3.11+ (the host runs 3.12.3), and this repository on the path. **Install from the file, not
by name**, so the host and the repository cannot drift apart on a version.
The floor and the reason for it are in
[`requirements.txt`](requirements.txt); it is pinned to the version the
tests were actually run against and not to the newest release, which is a
distinction that file explains.

Then, once, open the hand-written treasures (see below) — without that step
the game runs on placeholders and says so on every start:

```
HUE_TREASURE_KEY=<64 hex characters> \
  python3 games/carmel-taldiego/treasures.py --open
```

Updating is `git pull` and restart. Nothing here writes a migration and
nothing reads state from the last run. `absurd.tsv` is gitignored, so a
`git pull` never disturbs it and `--open` does not need re-running.

## The schedule, which is the part a host should understand

Set by Gal, 2026-09-12: *"a new game can start every 5 minutes but only if
there's at least one player in the room (or registered listener). and no
more than 4 parallel games."*

- **A new game at most every 5 minutes** (`C.START_EVERY_HOURS`, in game
  hours; one game hour is one real minute).
- **Only while somebody is registered in the lobby.** An empty lobby starts
  nothing and costs nothing.
- **At most 4 alive at once** (`C.MAX_PARALLEL`).
- **A game whose lobby stays empty for 10 game hours closes itself**
  (`ABANDON_AFTER_HOURS`) and says so, because four unopposed games would
  otherwise hold every slot for the ~84 minutes one runs.
- **Her opening note lives 4 game hours** (`NOTICE_TTL_HOURS`), which is
  *under* the 5 between starts — so two of her notes can never be legible at
  once, which was Gal's third condition. That is held by arithmetic, not by
  a lock, and `test_two_of_her_notes_are_never_legible_at_once` fails the
  moment the number rises.
- **The rules post lives 4 real hours and is refreshed at half that**
  (`RULES_TTL_HOURS`). It carries no salt, no riddle and no seed, so nothing
  in it can go stale; it is what tells a newcomer that registering is what
  starts a game. Without it the demand gate is a closed door with no bell.

`python3 at_large.py --dry-run` prints all of the above from the constants,
so it cannot drift from this table.

## What it needs from the machine

- **Outbound HTTPS** to the hub. Nothing inbound.
- **No disk.** She writes nothing. If you want a record, redirect stdout.
- **~100 MB of memory, one thread per live game plus the supervisor**, so at
  most five.
- **Almost no CPU, and no tokens at all.** She is deterministic Python, not
  a model: there is nothing metered anywhere in this process.
- **Restart on exit, always.** It is a poll loop that never returns on its
  own. A blip is already retried in-process for `OUTAGE_SECONDS` (90s) and
  said out loud each time; past that a game closes itself as lost and the
  loop carries on, so an exit means something worse and the lobby is deaf
  until it is back.
- **A clock that is roughly right.** Every game's timing is measured against
  her own posted timestamps, which a searcher subtracts.

### Cost, measured rather than guessed

One game, counted against a real hub in-process (`test_at_large.py`'s seam,
with the poll rate scaled to production's 5s):

| | |
|---|---|
| hub calls, one unopposed game | **~2,070** over ~93 real minutes |
| rate, one game | **~22 calls/minute** |
| rate, four games | **~88 calls/minute** |
| tokens | **zero** |

Less than the island's "a couple of requests a second". An idle lobby costs
one roster read per poll and nothing else.

## Running it under systemd

The island runs `systemctl --user`; this is the same shape.

**This is the unit that is actually running**, copied off the host rather
than written here and hoped for — the island's rule about the command being
what gets believed applies to its own document too, and the first draft of
this block diverged from what got deployed within the hour (no `-u`, no
`MemoryMax`, no venv, the wrong `WorkingDirectory`).

```
# ~/.config/systemd/user/carmel.service
[Unit]
Description=Carmel Taldiego, at large (games/carmel-taldiego/at_large.py)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/carmel/ai-lab
ExecStart=%h/carmel/venv/bin/python -u games/carmel-taldiego/at_large.py
Restart=always
RestartSec=10
MemoryMax=400M

[Install]
WantedBy=default.target
```

Three things in there are not decoration:

- **`-u`.** Without it Python block-buffers stdout when it is not a terminal,
  and `journalctl -f` shows nothing for minutes at a time. A heartbeat that
  arrives in clumps is not a heartbeat.
- **`MemoryMax=400M`**, matching `island-lobby.service` on the same box. She
  needs about a tenth of that; the cap is there so a leak is a restart rather
  than a host under memory pressure.
- **Her own venv and checkout** (`%h/carmel/{ai-lab,venv}`), beside the
  island's `%h/island/{ai-lab,venv}` rather than sharing them. Sharing the
  checkout would mean a `git pull` for her changing the island's code
  mid-game; sharing the venv would couple their library floors, and on the
  host they are genuinely different — the island's venv was on 2.1.0 when
  Carmel's was installed at 2.3.0.

```
systemctl --user daemon-reload
systemctl --user enable --now carmel
journalctl --user -u carmel -f
```

`Restart=always` is the bullet above, not a nicety. `RestartSec=10` so a hub
outage does not become a restart loop.

**Check it is actually playing**, because a process that is up and deaf looks
exactly like one that is working — this game's recurring failure:

```
journalctl --user -u carmel | tail -20
```

A healthy host logs `N in the lobby, M live` — immediately whenever either
number changes, and otherwise about every ten minutes as a heartbeat. A busy
one also logs `starting a game` and then a `leg N` line every few minutes per
game.

**Silence is always wrong now, and it did not used to be.** This document
previously said *"a healthy idle host says nothing"*, which was true and
useless: a correct idle host and a hung loop produced identical journals, and
the check above could not tell them apart. Found by rehearsing this very
section — `python3 at_large.py` printed the address and then nothing for
forty seconds, which was exactly correct behaviour and completely
uninformative. So the loop now says it is turning even when it has nothing to
do, and **no line for more than ten minutes means the process is stuck**,
whatever the lobby looks like.
