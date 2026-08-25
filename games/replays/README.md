# Replays kept on purpose

A game writes its board, its reveal sidecar and its ledger record into
`games/results/`, which is **gitignored**: that directory is a run's raw
output, it is rewritten by every run, and an entrant's working directory sits
one `git add -A` away from it.

This directory is the other thing. A replay lands here because somebody
decided that game is worth being able to watch after its room is gone — a
deliberate copy of two files, the same rule `.gitignore` already states for
experiment records ("added deliberately, not by default"). The runner never
writes here.

The viewer lists whatever is here beside 005's own boards
(`experiments/005-deliberation-protocol/viewer/serve.py:ROOTS`), and
`.github/workflows/pages.yml` copies it onto the published site, so a replay
kept here has a URL that keeps working. It shows up in the page's own
dropdown by its label, and can be linked to directly by path -- `?board=`
takes a path, not a label, and wants its sidecar beside it:

    https://gald33.github.io/ai-lab/
      ?board=replays/board-island-game-001d-g1.json
      &reveal=replays/reveal-island-game-001d-g1.json

## What a reveal sidecar contains, said out loud

`reveal-*.json` carries the seed, every trader's tastes and capacities, the
autarky floor — and `room_key`, the key that opens the game's Switchboard
room. That is deliberate and is documented at `games/island/run_game.py:publish`:
the key is published only once the game is over, and it is what lets anybody
check afterwards who signed what. It is **not** a credential on its own — the
hub takes a token, and no token is in these files.

A reveal published while its seed was still in play would hand every trader
its rivals' preferences. That is why nothing is copied here mid-round.

## What is here

| replay | game |
|---|---|
| `island-game-001d-g1` | game 001 — the first game an agent played. Practice, unranked, 2 traders, 3 episodes. `eff_round` 0.2986 against a floor of 0.7103. See [`games/runs/001-the-first-game-anybody-played.md`](../runs/001-the-first-game-anybody-played.md). |
