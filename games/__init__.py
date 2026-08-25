"""Experiments opened for participation -- see `games/README.md`.

A package, rather than a bare directory, so each game inside it is reached by
a qualified name: `games.island` is the island game's lobby and runner, and
`island` (rooted at `experiments/005-deliberation-protocol/`) is the island
economy it runs. Both are about the island and both would otherwise be a
top-level package called `island`, which is one name for two things and
resolves to whichever imported first.
"""
