"""The thousand places Carmel can be, with coordinates that are really theirs.

Step one of building the gazetteer for real (Gal, 2026-09-08: "1) create 1000
landmarks"). The twenty in `gazetteer.py` were a demonstration; these are the
map.

WHERE THEY COME FROM, because a coordinate written from memory is a
coordinate nobody can check. `landmarks.tsv` is derived from GeoNames'
`cities15000` dump -- 34,134 settlements above 15,000 people, with surveyed
latitude and longitude -- rather than authored here. GeoNames is licensed
CC BY 4.0; the attribution is in `landmarks.tsv` and this docstring is the
other half of it.

    https://download.geonames.org/export/dump/cities15000.zip

HOW THE THOUSAND WERE CHOSEN, and it is not "the thousand biggest". Taking
the largest cities gives a map that is four fifths Asian megacity, where
every route is short and every place is a capital of somewhere. The game
needs spread -- distance is a cost now, and clusters have to form -- so:

1. **Every national capital first** (GeoNames feature code `PPLC`): 241 of
   them, which buys world coverage in one move.
2. **Fill to a thousand by population, capped at six per country**, so no
   country can crowd the map. India and the United States get six each, the
   same as Latvia.

What that produces, and it is worth reading as game design rather than as
statistics: latitude −54 to +78, longitude −176 to +179, 244 countries, and
a long tail of places that are the whole reason to do this properly --
**Grytviken**, an abandoned whaling station on South Georgia; **Plymouth**,
the capital of Montserrat that a volcano buried, population 0;
**Adamstown** on Pitcairn, population 46; **Longyearbyen** on Svalbard;
**Port-aux-Français** on Kerguelen, population 45.

Those are the rooms worth being caught in.

    python3 games/hue-and-cry/landmarks.py
"""

from pathlib import Path

DATA = Path(__file__).with_name("landmarks.tsv")


def load() -> list[dict]:
    """Every landmark, as {name, country, lat, lon, population}."""
    out = []
    for line in DATA.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        name, cc, lat, lon, pop = line.split("\t")
        out.append({"name": name, "country": cc, "lat": float(lat),
                    "lon": float(lon), "population": int(pop)})
    return out


def main() -> None:
    places = load()
    countries = {p["country"] for p in places}
    lats = [p["lat"] for p in places]
    lons = [p["lon"] for p in places]

    print(f"{len(places):,} landmarks across {len(countries)} countries")
    print(f"  latitude  {min(lats):+.0f} .. {max(lats):+.0f}")
    print(f"  longitude {min(lons):+.0f} .. {max(lons):+.0f}")
    print(f"  population {min(p['population'] for p in places):,}"
          f" .. {max(p['population'] for p in places):,}")

    print("\n  the far corners, which are the point:")
    for p in sorted(places, key=lambda p: p["lat"])[:3]:
        print(f"    {p['name']:<22} {p['country']}  {p['lat']:+7.2f}"
              f" {p['lon']:+8.2f}   pop {p['population']:,}")
    for p in sorted(places, key=lambda p: -p["lat"])[:2]:
        print(f"    {p['name']:<22} {p['country']}  {p['lat']:+7.2f}"
              f" {p['lon']:+8.2f}   pop {p['population']:,}")

    print("\n  and the smallest rooms on the map:")
    for p in sorted(places, key=lambda p: p["population"])[:5]:
        print(f"    {p['name']:<22} {p['country']}  pop {p['population']:,}")


if __name__ == "__main__":
    main()
