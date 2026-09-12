"""What she takes, what it is worth, and how long standing still costs her.

Step three (Gal, 2026-09-08: "add coordinates, treasures, and other
stats"), and the steer that shapes it: *"the treasure can be absurdly
impossible to steal like Carmen likes in some places"*.

    python3 games/carmel-taldiego/treasures.py            # read some
    python3 games/carmel-taldiego/treasures.py --open     # unseal, to edit them
    python3 games/carmel-taldiego/treasures.py --seal     # re-encrypt

WHY THIS IS SEALED
==================

*Gal, 2026-09-09, after the same mistake was found in the hint layer:
"seal the treasures too".*

This table maps each landmark to what she takes there, so publishing it
does what the committed `hints.tsv` did: any public line naming what was
taken names the room. **Encrypting `treasures.tsv` would not have been
enough**, because the eighty hand-written ones were a dict in this file's
source, keyed by landmark -- the leak for the best eighty was the code, not
the data file.

And they cannot be published as an unordered list either, the way
`clauses.py` publishes the hint bank. A hint clause is written to name
nothing; **a hand-written treasure names its place implicitly**. Each one
is about a specific landmark and reads like it, so an unordered list is a
puzzle with eighty answers and no difficulty. There is no form of that
prose that is both readable and safe, which is why it goes behind the key
whole -- and this docstring names none of them for the same reason.

WHAT STAYS PUBLIC, and it is most of the reasoning. The scoring parameters,
the dwell rule, the generic per-descriptor bank, and the balance finding
below are all here in the open. What is behind the key is only the mapping:
which landmark, which treasure.

WHAT IT COSTS. A fresh clone cannot rebuild the eighty, and the tests
cannot check them. `build()` therefore returns a complete table without
them -- 920 derived treasures and 80 placeholders -- so the invariants and
the balance check still run in CI with no secret present. That is a real
loss of coverage on the best writing in the repository, and it is the price
of the mapping not being readable.

THE JOKE IS LOAD-BEARING. "Absurdly impossible to steal" could have been
flavour text. Instead it is the mechanic, because the theft is a **dwell**:
she must stand still to take a thing, and standing still is the only reason
she is catchable at all. So the impossible ones are worth the most and take
the longest, and going after one is a bet that nobody reads the room in
time.

**"the only reason she is catchable" was superseded on 2026-09-10** and the
sentence above is left standing because the economics it explains are still
the economics. The catch rule is Gal's: *sharing a room with her is the
win*, however she came to be in it and whatever she is doing there -- see
`carmel.chase`, which carries the decision and why the old pair of rules
was unplayable. What survives here is that a long theft is a long time in
one room, so the impossible treasures are still the risky ones; what does
not survive is "only".
 Taking the sound of the bells at a cathedral is nine hours of
standing where a searcher can find her; taking a fistful of gravel from a
minor site is one.

THE TENSION IS IN THE DATA AND WAS NOT PUT THERE. Reputation tracks fame --
sitelinks, the number of Wikipedia language editions -- and fame turns out
to run *against* cover:

    correlation(cover, sitelinks) = -0.260

A famous landmark carries rarer descriptors, so the rooms worth the most
are the rooms where her hint hides her least. Nobody designed that; it
falls out of a map of real places, which is the second time real geography
has supplied a balance this game would otherwise have had to fake (see
`games/carmel-taldiego.md`, "Routes run between places that resemble each
other"). Re-check with `python3 games/carmel-taldiego/treasures.py`.

WHY THE NAMES MAY SAY WHERE SHE IS, when a hint may not. A treasure is not
a clue. It is written on the room's own board at setup and settles into the
record when a `TAKE` is recognised, so a searcher who can read the treasure
is already standing in the room and has won.

That argument is sound and it is exactly what made the file feel safe to
commit. It is also conditional -- it holds *while* a treasure is only ever
readable in its own room -- and a committed table does not care about the
condition. The lesson from the hint matrix, restated: **the reasoning that
makes a secret safe to hold is not a reason to publish it.**
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from descriptors import all_descriptors  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402

ABSURD_HEADER = (
    "# The hand-written treasures, one per place famous enough that a\n"
    "# person has a picture of it in their head. THIS FILE IS THE GAME\n"
    "# SECRET and is gitignored: the prose names the place implicitly --\n"
    "# mapping cannot be published even as an unordered list: each line\n"
    "# reads like the place it belongs to.\n"
    "# Only games/carmel-taldiego/treasures.enc may be committed.\n"
    "# landmark\ttreasure\n")

#: Reputation runs 5..80 by fame rank, and an impossible treasure adds 20 on
#: top and is floored at ABSURD_FLOOR -- so the ceiling is reserved for them
#: and the ordering inside the top is preserved. A multiplier was tried
#: first and piled seventy treasures onto the cap, which is the same as not
#: scoring them; then the plain bonus put Denali's impossible theft at 25,
#: below the average ordinary one, because Wikidata records Denali as
#: having no sitelinks at all. Taking a mountain's name away is not a
#: small job however obscure the ranking thinks the mountain is.
#:
#: Guesses, all three, and flagged as such: what settles them is whether a
#: Carmel who only ever takes the cheap thing can still win, and that needs
#: the settler and the reference searcher, neither of which exists.
MIN_REPUTATION, MAX_REPUTATION = 5, 80
ABSURD_BONUS = 20
ABSURD_FLOOR = 60

#: Hours of standing still, which is the whole cost. One hour per twelve
#: points, so the cheapest theft is quick and the Eiffel Tower is most of a
#: working day in one place.
def dwell_for(reputation: int, absurd: bool) -> int:
    return max(1, round(reputation / 12) + (3 if absurd else 0))


#: Where the hand-written treasures live when they are unsealed. Gitignored,
#: and the seal is the only form of them that may be committed.
ABSURD_SOURCE = Path(__file__).with_name("absurd.tsv")

#: The sealed table -- the whole mapping, every landmark to what she takes
#: there. See `WHY THIS IS SEALED` at the top of the file.
SEALED = Path(__file__).with_name("treasures.enc")

#: The key lives with the person running the game, never in the repository.
KEY_ENV = "HUE_TREASURE_KEY"


def load_absurd(path: Path = ABSURD_SOURCE) -> dict:
    """The hand-written treasures, if this checkout has them unsealed.

    Absent on a fresh clone, and that is the point: `--open` with the key
    puts them back. Everything else in this file works without them, which
    is what lets the tests and the balance check run in CI with no secret.
    """
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        landmark, treasure = line.split("\t")
        out[landmark] = treasure
    return out


#: For everywhere else, the thing she took is drawn from what the place is.
#: Several per descriptor so a thousand landmarks do not all lose a plaque.
BY_DESCRIPTOR = {
    "a_dug_site": ["everything in trench four, crated and gone",
                   "the finds tray, and the labels with it",
                   "the site notebook, which was worse than the finds"],
    "a_ruined_city": ["the last standing lintel",
                      "the street plan, and now nobody can say where anything was",
                      "the doorway everyone photographs"],
    "a_living_city": ["one day's takings from the whole quarter",
                      "the hands off the station clock",
                      "the name off every street sign in the district"],
    "an_old_quarter": ["the shutters, from every window on one street",
                       "the door of the oldest house in it",
                       "the cobbles, and they were numbered"],
    "a_church_or_cathedral": ["the sound of the bells",
                              "the rose window, in one piece",
                              "the reliquary, and what was in it"],
    "a_monastery": ["the library's oldest book",
                    "the bell that keeps the hours",
                    "the recipe, which was the only secret they had"],
    "a_temple_or_pagoda": ["the topmost finial",
                           "the incense, and the smell went with it",
                           "the bell rope and the bell"],
    "a_castle": ["the portcullis",
                 "the keys to a gate that has not been locked in centuries",
                 "the banner off the keep"],
    "walls_and_gates": ["one gate, hinges and all",
                        "the stretch of wall the postcards use",
                        "the watchman's horn"],
    "royal_rooms": ["the state bed",
                    "the chandelier, lowered and walked out",
                    "one portrait, and it was the good one"],
    "graves": ["the effigy off the tomb",
               "the grave goods, all of them",
               "the inscription, chiselled out entire"],
    "glass_cases": ["the third case from the left, and the card beside it",
                    "the exhibit everyone comes for",
                    "the catalogue, which named things no longer there"],
    "a_garden": ["every seed in the seed store",
                 "the oldest tree in it, roots and all",
                 "the plan the whole thing was laid out from"],
    "worked_land": ["a season's harvest, standing",
                    "the terrace walls, stone by stone",
                    "the water rights"],
    "a_national_park": ["the boundary stones",
                        "the ranger's log for forty years",
                        "the view from the overlook"],
    "a_reserve": ["the breeding pair", "the count, so nobody knows what is left",
                  "the tags off every animal in it"],
    "a_mountain": ["the summit cairn", "the last hundred metres of it",
                   "the snow line"],
    "deep_cut": ["the echo", "the bridge across it", "the river at the bottom"],
    "underground": ["the deepest chamber", "the dark",
                    "the paintings off the wall"],
    "standing_water": ["the far shore", "the reflection", "the depth of it"],
    "water_at_its_feet": ["every boat tied up that night",
                          "the harbour light", "the tide"],
    "ringed_by_water": ["the only jetty", "the causeway",
                        "the boat, and then there was no way off"],
    "at_sea_level": ["the sea wall", "the flood markers", "the horizon"],
    "a_span_or_a_channel": ["the keystone", "the lock gates",
                            "the span, and both banks are still there"],
    "machine_age": ["the great wheel", "the last working engine",
                    "the drawings the whole place was built from"],
    "dry_country": ["the well", "the only shade for a day's walk",
                    "the map of where the water is"],
    "thin_air": ["the oxygen", "the last shelter below the summit",
                 "the weather station"],
    "a_ruin_default": ["the plaque"],
}

FALLBACK = ["the visitors' book", "the plaque, and the screws it was on",
            "one day's takings", "the keys to everything",
            "the oldest thing on the site", "the signboard at the gate"]


def _pick(options, landmark, salt=b"treasure"):
    n = int.from_bytes(
        hashlib.sha256(salt + b"\0" + landmark.encode()).digest()[:8], "big")
    return options[n % len(options)]


def build(absurd_map: dict | None = None) -> list[dict]:
    """Every landmark's treasure. Without the hand-written ones this still
    returns a complete table -- 920 derived treasures and 80 placeholders --
    so a checkout with no key can still be tested and balanced."""
    absurd_map = load_absurd() if absurd_map is None else absurd_map
    places = load_landmarks()
    per = all_descriptors()

    # Reputation by fame RANK rather than by raw sitelinks, because the raw
    # number is a bad scale and a worse tail. Four rows are under eight and
    # every one of them is a recording error rather than an obscure place:
    # Denali and the Galapagos have 0, Three Mile Island 4, the Pentagon 7.
    # Rank does not repair that -- it puts them at the bottom in order --
    # so all four are named in ABSURD, which is both the honest fix and the
    # right one, since each of them is exactly the sort of place Carmel
    # would take something ridiculous from.
    order = sorted(places, key=lambda p: (p["sitelinks"], p["name"]))
    rank = {p["name"]: i for i, p in enumerate(order)}
    span = MAX_REPUTATION - MIN_REPUTATION

    rows = []
    for p in places:
        name = p["name"]
        absurd = name in absurd_map
        if absurd:
            what = absurd_map[name]
        else:
            banks = [BY_DESCRIPTOR[d] for d in sorted(per[name])
                     if d in BY_DESCRIPTOR]
            what = _pick(banks[0] if banks else FALLBACK, name) if banks \
                else _pick(FALLBACK, name)
        base = MIN_REPUTATION + round(span * rank[name] / (len(order) - 1))
        reputation = (max(base + ABSURD_BONUS, ABSURD_FLOOR)
                      if absurd else base)
        rows.append({"landmark": name, "treasure": what,
                     "reputation": reputation, "absurd": absurd,
                     "dwell": dwell_for(reputation, absurd)})
    return rows


def _key() -> bytes:
    raw = os.environ.get(KEY_ENV)
    if not raw:
        raise SystemExit(
            f"set {KEY_ENV} to the 64-hex-character treasure key. It is not"
            " in the repository and it is not derivable from anything that"
            " is -- that is the whole point of it.")
    key = bytes.fromhex(raw)
    if len(key) != 32:
        raise SystemExit(f"{KEY_ENV} must be 32 bytes as 64 hex characters")
    return key


def _serialise(rows) -> bytes:
    body = "\n".join(
        "\t".join([r["landmark"], r["treasure"], str(r["reputation"]),
                    str(r["dwell"]), "1" if r["absurd"] else "0"])
        for r in rows)
    return body.encode("utf-8")


def seal(rows, path: Path = SEALED) -> int:
    """AES-256-GCM, nonce prepended. The bytes are the only form of this
    table that may exist in the repository."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    nonce = os.urandom(12)
    path.write_bytes(nonce + AESGCM(_key()).encrypt(nonce, _serialise(rows),
                                                    None))
    return len(rows)


def unseal(path: Path = SEALED) -> list[dict]:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    raw = path.read_bytes()
    plain = AESGCM(_key()).decrypt(raw[:12], raw[12:], None)
    out = []
    for line in plain.decode("utf-8").splitlines():
        landmark, treasure, reputation, dwell, absurd = line.split("\t")
        out.append({"landmark": landmark, "treasure": treasure,
                    "reputation": int(reputation), "dwell": int(dwell),
                    "absurd": absurd == "1"})
    return out


def cover() -> dict:
    """Mean number of landmarks sharing each descriptor a landmark offers --
    how much room its hint gives her to hide in."""
    from collections import Counter
    per = all_descriptors()
    counts = Counter(d for s in per.values() for d in s)
    return {n: sum(counts[d] for d in s) / len(s) for n, s in per.items()}


def correlation(xs, ys) -> float:
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs)
           * sum((b - my) ** 2 for b in ys)) ** 0.5
    return num / den


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seal", action="store_true",
                    help=f"build and encrypt into {SEALED.name}")
    ap.add_argument("--open", action="store_true",
                    help=f"decrypt the hand-written ones into"
                         f" {ABSURD_SOURCE.name}")
    args = ap.parse_args()

    if args.seal:
        rows = build()
        n = sum(r["absurd"] for r in rows)
        if n == 0:
            raise SystemExit(
                f"{ABSURD_SOURCE.name} is missing, so there is nothing"
                " hand-written to seal. Run --open first.")
        seal(rows)
        print(f"{len(rows):,} treasures sealed into {SEALED.name},"
              f" {n} of them impossible")
        return

    if args.open:
        rows = unseal()
        with open(ABSURD_SOURCE, "w", encoding="utf-8") as fh:
            fh.write(ABSURD_HEADER)
            for r in rows:
                if r["absurd"]:
                    fh.write(f"{r['landmark']}\t{r['treasure']}\n")
        print(f"{sum(r['absurd'] for r in rows)} hand-written treasures"
              f" written to {ABSURD_SOURCE.name} (gitignored)")
        return

    rows = unseal() if SEALED.exists() and os.environ.get(KEY_ENV) else build()
    c = cover()
    print(f"{len(rows):,} treasures, {sum(r['absurd'] for r in rows)}"
          " impossible\n")
    print("  the richest rooms, which are also the most exposed:")
    for r in sorted(rows, key=lambda r: -r["reputation"])[:8]:
        print(f"    {r['reputation']:3}  {r['dwell']}h  {r['landmark']}"
              f" -- {r['treasure']}")
    print("\n  and the cheap ones, where she can stand about:")
    for r in sorted(rows, key=lambda r: r["reputation"])[:4]:
        print(f"    {r['reputation']:3}  {r['dwell']}h  {r['landmark']}"
              f" -- {r['treasure']}")

    rep = [r["reputation"] for r in rows]
    cov = [c[r["landmark"]] for r in rows]
    print(f"\n  correlation(cover, reputation) = "
          f"{correlation(cov, rep):+.3f}")
    print("  Negative is the whole point: the rooms worth the most are the"
          "\n  rooms where her hint hides her least, and nobody arranged it.")


if __name__ == "__main__":
    main()
