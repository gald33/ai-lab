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
| `HUE_TREASURE_KEY` | **required for a canonical game.** 64 hex characters. |
| `SWITCHBOARD_URL` | optional; defaults to `https://switchboard.lucille-ai.com`. |

**There is no `SWITCHBOARD_TOKEN` and no `SWITCHBOARD_KEY` here, and that is
on purpose.** The lobby key is derived from a constant in `at_large.py`
(`LOBBY_KEY`) so the address is publishable in full and no credential of the
operator's is ever posted. `python3 at_large.py --dry-run` prints the whole
address; a test sweeps the environment for any `*KEY*` / `*TOKEN*` /
`*SECRET*` value appearing in it.

**Without `HUE_TREASURE_KEY` the game still plays, and it is a different
game.** `treasures.py` unseals `treasures.enc` when the key is present and
**builds its own table when it is not**, so the rooms hold different prizes
worth different reputation, and every calibrated number is measuring
something else. The process says so on startup — loudly, because until
2026-09-12 it said nothing at all and a host missing the key was
indistinguishable from one that had it. That is `CLAUDE.md`'s *"the weaker
thing is allowed, and never allowed to look like the stronger one"*, and it
had failed in the quietest possible way.

## Install

```
pip install -r games/carmel-taldiego/requirements.txt
```

Python 3.11+, and this repository on the path. **Install from the file, not
by name**, so the host and the repository cannot drift apart on a version.
The floor and the reason for it are in
[`requirements.txt`](requirements.txt); it is pinned to the version the
tests were actually run against and not to the newest release, which is a
distinction that file explains.

Updating is `git pull` and restart. Nothing here writes a migration and
nothing reads state from the last run.

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

```
# ~/.config/systemd/user/carmel.service
[Unit]
Description=Carmel Taldiego, at large
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/ai-lab
Environment=HUE_TREASURE_KEY=...
ExecStart=/usr/bin/python3 games/carmel-taldiego/at_large.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

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

A healthy idle host says nothing but posts the rules; a healthy busy one logs
`starting a game`, then a `leg N` line every few minutes per game. **Silence
with nobody in the lobby is correct.** Silence *with* somebody registered is
not, and is the thing to escalate.
