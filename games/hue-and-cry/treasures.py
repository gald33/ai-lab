"""What she takes, what it is worth, and how long standing still costs her.

Step three (Gal, 2026-09-08: "add coordinates, treasures, and other
stats"), and the steer that shapes it: *"the treasure can be absurdly
impossible to steal like Carmen likes in some places"*.

    python3 games/hue-and-cry/treasures.py            # read some
    python3 games/hue-and-cry/treasures.py --build    # rewrite treasures.tsv

THE JOKE IS LOAD-BEARING. "Absurdly impossible to steal" could have been
flavour text. Instead it is the mechanic, because the theft is a **dwell**:
she must stand still to take a thing, and standing still is the only reason
she is catchable at all. So the impossible ones are worth the most and take
the longest, and going after one is a bet that nobody reads the room in
time. Taking the sound of the bells at a cathedral is nine hours of
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
`games/hue-and-cry.md`, "Routes run between places that resemble each
other"). Re-check with `python3 games/hue-and-cry/treasures.py`.

WHY THE NAMES MAY SAY WHERE SHE IS, when a hint may not. A treasure is not
a clue. It is written on the room's own board at setup and settles into the
record when a `TAKE` is recognised, so a searcher who can read the treasure
is already standing in the room and has won. The hint is the thing that
must name nothing.
"""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from descriptors import all_descriptors  # noqa: E402
from landmarks import load as load_landmarks  # noqa: E402

DATA = Path(__file__).with_name("treasures.tsv")

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


#: Hand-written, and the reason this file is not entirely arithmetic. If a
#: place is famous enough that a person has a picture of it in their head,
#: the thing she takes should be the thing in the picture -- and it should
#: be the one thing that could not possibly be carried away.
ABSURD = {
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    "Vatican City": "the keys",
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    "Sydney Opera House": "the sails",
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    "Lake Baikal": "the depth",
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    # (redacted)
    "Blue Mosque of Mazar-i-Sharif": "the blue",
    "Lhasa": "the altitude",
    # (redacted)
}

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


def build() -> list[dict]:
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
        absurd = name in ABSURD
        if absurd:
            what = ABSURD[name]
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


def write(rows, out) -> None:
    out.write("# What she takes at each landmark, what it is worth, and the\n"
              "# hours of standing still it costs her. Written by\n"
              "# treasures.py; the impossible ones are hand-authored there.\n"
              "# landmark\ttreasure\treputation\tdwell_hours\tabsurd\n")
    for r in rows:
        assert "\t" not in r["treasure"]
        out.write(f"{r['landmark']}\t{r['treasure']}\t{r['reputation']}"
                  f"\t{r['dwell']}\t{'1' if r['absurd'] else '0'}\n")


def load() -> list[dict]:
    out = []
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
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
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()

    if args.build:
        rows = build()
        with open(DATA, "w", encoding="utf-8") as fh:
            write(rows, fh)
        print(f"{len(rows):,} treasures, {sum(r['absurd'] for r in rows)}"
              " of them impossible")
        return

    rows = load()
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
