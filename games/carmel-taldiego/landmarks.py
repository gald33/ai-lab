"""The thousand places Carmel can be, with coordinates that are really theirs.

Step one of building the gazetteer for real (Gal, 2026-09-08: "1) create 1000
landmarks"). The twenty in `gazetteer.py` were a demonstration; these are the
map.

HOW THEY WERE CHOSEN, and this reverses an earlier answer that is left here
because the reasoning is the correction. The first thousand were **cities**,
taken from GeoNames by population: every national capital, then a fill capped
at six per country so nowhere could crowd the map. It gave excellent spread
and it was the wrong map. Gal, the same day:

    "but you should choose landmarks, and don't base them on how many per
    area or country. pick 1000 known or interesting landmarks. The Eifel
    tower, Dead sea, Area 51, Stonehenge. Then the game is interesting and
    you have something to say about every one of them."

That last clause is the whole requirement, and population cannot satisfy it.
Step two of this build writes three hint sentences for every landmark, and a
hint is a report, a sighting, a rumour -- a sentence a person reads and feels
something about. There is nothing to say about the 700th largest city that
anybody would want to read, and there is something to say about every one of
Area 51, the Dead Sea, Stonehenge and Uluru. **Spread is a property you can
optimise for and interest is not**, so interest was chosen first and the
spread checked afterwards: 162 countries, latitude -54.6 to +78.2,
longitude -172.9 to +175.6. Enough.

WHERE THEY COME FROM, because a coordinate written from memory is a
coordinate nobody can check. Every row is from Wikidata (CC0), by three
queries in `build_landmarks.py`, and the `source` column records which one:

- **`unesco`** (848) -- `?item wdt:P1435 wd:Q9259`, the UNESCO World Heritage
  Sites, of which 1,875 have coordinates. A list of the places the world
  agreed were worth keeping is very close to a list of places worth being
  chased through.
- **`iconic`** (95) -- named directly, by label lookup, because no property
  in Wikidata means "famous": Area 51, the Bermuda Triangle, Loch Ness,
  Roswell, Chernobyl, the Svalbard Global Seed Vault, the Hollywood Sign.
  These are the ones with a story rather than a citation.
- **`feature`** (57) -- lakes, deserts, canyons, waterfalls, mountains and
  castles by `wdt:P31`, twelve of each by sitelinks. A quota per type and
  not one threshold across all six, because the threshold that admits a
  reasonable number of castles admits four hundred lakes. This is where
  Neuschwanstein, the Namib, Tiger Leaping Gorge and the Valley of Geysers
  come from.

`sitelinks` is the number of Wikipedia language editions with an article on
the place. It is a fame proxy and a rough one -- it reads Tower Bridge as
better known than the Tower of London, and returns 0 for Denali -- so it
orders the file and decides nothing else.

`qid` is the Wikidata item, and it is in the file because the name is not an
identifier. Asking Wikidata for "Eiffel Tower" returns four things, three of
them in the United States; asking for Q243 returns the tower. Step three
wants elevation, age and type for every landmark, and every one of those
lookups is exact with a Q-number and a guess without one.

ONE LANDMARK PER PLACE, at a kilometre. The raw selection had 27 pairs
closer than that: the Dome of the Rock, Al-Aqsa and the Western Wall inside
200 metres of each other; "Basilica and Expiatory Church of the Holy Family"
and "Sagrada Família"; Chichen Itza and the Temple of Kukulcan. Two rooms
that near are one room under two names, and the game cannot have them --
the landmark hashes to the room, so one place would hold two rooms whose
hints are interchangeable, and **travel between them is free**, which is the
one cost the design leans on. The better-known name was kept and the pool
backfilled to a thousand.

Eight rows are corrected by hand in `build_landmarks.py`, which reports
each as fired or stale so a correction cannot outlive the defect it was
for: the Pentagon and Three Mile Island had coordinates in Brussels and in
New Hampshire, and five countries were defunct (the Berlin Wall in East
Germany) or merely the first of several (the Amazon in France).

    python3 games/carmel-taldiego/landmarks.py           # read the committed file
    python3 games/carmel-taldiego/build_landmarks.py \
        --out games/carmel-taldiego/landmarks.tsv        # rebuild it from Wikidata
"""

from pathlib import Path

DATA = Path(__file__).with_name("landmarks.tsv")


def load() -> list[dict]:
    """Every landmark, as {name, country, lat, lon, source, sitelinks, qid}."""
    out = []
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, cc, lat, lon, source, sitelinks, qid = line.split("\t")
        out.append({"name": name, "country": cc, "lat": float(lat),
                    "lon": float(lon), "source": source,
                    "sitelinks": int(sitelinks), "qid": qid})
    return out


def main() -> None:
    places = load()
    countries = {p["country"] for p in places}
    lats = [p["lat"] for p in places]
    lons = [p["lon"] for p in places]

    print(f"{len(places):,} landmarks across {len(countries)} countries")
    print(f"  latitude  {min(lats):+.1f} .. {max(lats):+.1f}")
    print(f"  longitude {min(lons):+.1f} .. {max(lons):+.1f}")
    for source in ("unesco", "iconic", "feature"):
        n = sum(1 for p in places if p["source"] == source)
        print(f"  {source:<8} {n}")

    print("\n  the ones the map was rebuilt for:")
    wanted = ["Eiffel Tower", "Dead Sea", "Area 51", "Stonehenge",
              "Uluru", "Bermuda Triangle", "Svalbard Global Seed Vault"]
    by_name = {p["name"]: p for p in places}
    for name in wanted:
        p = by_name[name]
        print(f"    {p['name']:<28} {p['lat']:+7.2f} {p['lon']:+8.2f}"
              f"  {p['country']}")

    print("\n  the far corners:")
    edges = (sorted(places, key=lambda p: p["lat"])[:2]
             + sorted(places, key=lambda p: -p["lat"])[:2])
    for p in edges:
        print(f"    {p['name']:<28} {p['lat']:+7.2f} {p['lon']:+8.2f}"
              f"  {p['country']}")


if __name__ == "__main__":
    main()
