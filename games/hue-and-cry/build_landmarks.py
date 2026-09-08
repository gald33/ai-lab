"""Rebuild `landmarks.tsv` from Wikidata.

A data file nobody can regenerate is a data file nobody can check, and this
one carries three hand corrections that would otherwise live only in a
commit message. Running this reproduces the thousand exactly:

    python3 games/hue-and-cry/build_landmarks.py --out games/hue-and-cry/landmarks.tsv

It needs the network (Wikidata's query service) and takes a couple of
minutes. It is not run by CI; `landmarks.py` reads the committed file.

WHY THE QUERIES LOOK LIKE THIS. The obvious query -- walk `wdt:P31/wdt:P279*`
down from "tourist attraction" or "landmark" -- times out on the public
endpoint every time, because the subclass closure under those is enormous.
Three narrow queries that each return in seconds beat one that returns
nothing:

- UNESCO sites are one direct statement, `wdt:P1435 wd:Q9259`.
- Fame has no property, so the iconic set is a `VALUES` list of labels.
- The features are direct `wdt:P31` on six concrete types.
"""

import argparse
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "hue-and-cry-gazetteer/1.0 (https://github.com/gald33/ai-lab)"
RETRIES = 5

UNESCO = """
SELECT ?name ?cc ?coord ?sl WHERE {
  ?item wdt:P1435 wd:Q9259 ; wdt:P625 ?coord ; rdfs:label ?name .
  OPTIONAL { ?item wdt:P17 ?c . ?c rdfs:label ?cc . FILTER(lang(?cc)="en") }
  ?item wikibase:sitelinks ?sl .
  FILTER(lang(?name)="en")
}
"""

# No property in Wikidata means "famous", so these are named. The list is the
# editorial decision in this file: places with a story rather than a citation.
ICONIC_NAMES = """
Eiffel Tower
Dead Sea
Area 51
Stonehenge
Uluru
Taj Mahal
Great Wall of China
Machu Picchu
Colosseum
Petra
Christ the Redeemer
Angkor Wat
Chichen Itza
Statue of Liberty
Golden Gate Bridge
Mount Rushmore
Times Square
Empire State Building
Alcatraz Island
Hollywood Sign
White House
Pentagon
Roswell
Bermuda Triangle
Loch Ness
Nazca Lines
Easter Island
Galápagos Islands
Mount Everest
K2
Matterhorn
Mount Fuji
Mount Kilimanjaro
Denali
Table Mountain
Grand Canyon
Niagara Falls
Victoria Falls
Yellowstone National Park
Yosemite National Park
Old Faithful
Devils Tower
Salar de Uyuni
Atacama Desert
Sahara
Gobi Desert
Okavango Delta
Serengeti
Amazon rainforest
Great Blue Hole
Mariana Trench
Krakatoa
Mount Vesuvius
Eyjafjallajökull
Pompeii
Persepolis
Babylon
Palmyra
Samarkand
Timbuktu
Lhasa
Forbidden City
Hagia Sophia
Blue Mosque
Kaaba
Western Wall
Mount Athos
Sagrada Família
Brandenburg Gate
Berlin Wall
Red Square
Big Ben
Tower Bridge
Tower of London
Buckingham Palace
Sydney Opera House
Burj Khalifa
Acropolis of Athens
Göbekli Tepe
Newgrange
Skara Brae
Carnac stones
Lascaux
Banaue Rice Terraces
Ha Long Bay
Chernobyl Nuclear Power Plant
Fukushima Daiichi Nuclear Power Plant
Three Mile Island
Bikini Atoll
Guantanamo Bay Naval Base
Cheyenne Mountain Complex
Svalbard Global Seed Vault
Great Barrier Reef
Mount Sinai
Angel Falls
Iguazu Falls
Lake Baikal
"""

FEATURES = {  # label -> Wikidata class
    "mountain": "Q8502", "lake": "Q23397", "waterfall": "Q34038",
    "castle": "Q23413", "canyon": "Q150784", "desert": "Q8514",
}

FEATURE_Q = """
SELECT ?name ?cc ?coord ?sl WHERE {
  ?item wdt:P31 wd:%s ; wdt:P625 ?coord ; rdfs:label ?name ;
        wikibase:sitelinks ?sl .
  OPTIONAL { ?item wdt:P17 ?c . ?c rdfs:label ?cc . FILTER(lang(?cc)="en") }
  FILTER(lang(?name)="en") FILTER(?sl > 25)
}
"""

LOOKUP = """
SELECT ?name ?cc ?coord ?sl WHERE {
  VALUES ?name { %s }
  ?item rdfs:label ?name ; wdt:P625 ?coord ; wikibase:sitelinks ?sl .
  OPTIONAL { ?item wdt:P17 ?c . ?c rdfs:label ?cc . FILTER(lang(?cc)="en") }
}
"""

# --- Corrections, each of which the build reports as fired or stale.
#
# There used to be a DROP set here, holding "Ayers Rock" (which came back a
# hill in New Zealand), "Nasca" (a comune in Italy) and "Altamira" (a city in
# Pará). None of them was Wikidata's fault. The name list above was being
# read with `.split()`, which splits on whitespace, so "Nazca Lines" was
# asked for as "Nazca" and "Lines" and the label lookup obligingly found
# something. Fixing the split emptied the set. The lesson is the one the
# stale report exists to surface: **a correction is a claim about the world,
# and a correction that stops firing may mean the world was never wrong.**
COORD_FIX = {
    "Pentagon": (38.8709, -77.0563, "United States"),
    "Three Mile Island": (40.1533, -76.7247, "United States"),
}
COUNTRY_FIX = {
    "Berlin Wall": "Germany",        # Wikidata says East Germany, which has none
    "Amazon rainforest": "Brazil",   # spans nine; the query returned France
    "Serengeti": "Tanzania",         # the coordinate is in Tanzania, not Kenya
    "Mount Everest": "Nepal",        # the border; Nepal is the approach
    "Matterhorn": "Switzerland",
    "Nahal Me'arot Nature Reserve": "Israel",  # Wikidata has no P17 on it
}
RENAME = {"Blue Mosque": "Blue Mosque of Mazar-i-Sharif"}
COUNTRY_NAMES = {"People's Republic of China": "China"}

# Two rooms nearer than this are one place under two names: their hints are
# interchangeable and travel between them is free, which is the one cost the
# chase leans on.
MIN_KM = 1.0
TOTAL = 1000
FEATURE_QUOTA = 12  # per type, most-linked first
# Sitelinks order the iconic set into the map; below this a "famous" name is
# usually a mis-resolved item rather than an obscure landmark.
PREFER = {"Tower of London"}
RANK = {"iconic": 0, "feature": 1, "unesco": 2}


def query(sparql: str) -> list[dict]:
    """Ask the query service, in JSON.

    Not CSV and not TSV, and the difference is not cosmetic: Wikidata's TSV
    writes a label as `"Eiffel Tower"@en`, quote marks and language tag and
    all, so every consumer grows a strip-the-tag helper and gets it subtly
    wrong -- this one did, and reported every landmark missing. JSON has one
    unambiguous `value` per binding and nothing to strip.
    """
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": sparql})
    req = urllib.request.Request(
        url, headers={"Accept": "application/sparql-results+json",
                      "User-Agent": UA})
    # The public endpoint returns 502 and 429 under load, and the eighth
    # query failing four minutes in throws away the seven that worked.
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = json.load(r)
            break
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if attempt == RETRIES - 1:
                raise
            wait = 2 ** attempt * 5
            print(f"    {e}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    return [{k: b["value"] for k, b in row.items()}
            for row in body["results"]["bindings"]]


def point(coord: str) -> tuple[float, float] | None:
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", coord or "")
    return (float(m.group(2)), float(m.group(1))) if m else None


def collect(rows: list[dict], source: str, into: dict) -> None:
    """Keep the best row per name -- Wikidata returns one per country.

    The tiebreak is alphabetical and that matters more than it looks. Lake
    Tanganyika touches four countries and Titicaca two, each row carrying
    the same sitelink count, so "keep the first" keeps whichever row the
    endpoint happened to serve first and **a rebuild produces a different
    file** -- which makes the reproducibility this script exists for a
    thing you cannot check. Alphabetical is arbitrary; being arbitrary the
    same way every time is the whole point.
    """
    for row in rows:
        name, p = row.get("name"), point(row.get("coord", ""))
        if not name or not p:
            continue
        sl, cc = int(row.get("sl") or 0), row.get("cc") or ""
        prev = into.get(name)
        if prev and (prev["sl"], prev["cc"]) <= (sl, cc) and prev["sl"] >= sl:
            continue
        if prev and prev["sl"] > sl:
            continue
        into[name] = {"lat": p[0], "lon": p[1], "cc": cc,
                      "sl": sl, "src": source}


def haversine(a: dict, b: dict) -> float:
    la1, lo1, la2, lo2 = map(
        math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    return 6371 * 2 * math.asin(math.sqrt(
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


def build() -> dict:
    unesco: dict = {}
    collect(query(UNESCO), "unesco", unesco)
    print(f"  unesco   {len(unesco)}", file=sys.stderr)

    names = [n.strip() for n in ICONIC_NAMES.splitlines() if n.strip()]
    values = " ".join(f'"{n}"@en' for n in names)
    iconic: dict = {}
    collect(query(LOOKUP % values), "iconic", iconic)
    print(f"  iconic   {len(iconic)}", file=sys.stderr)

    # A quota per type, not one sitelinks threshold across all six: the
    # threshold that admits a reasonable number of castles admits four
    # hundred lakes, and the map wants some of each.
    feature: dict = {}
    for qid in FEATURES.values():
        got: dict = {}
        collect(query(FEATURE_Q % qid), "feature", got)
        best = sorted(got.items(), key=lambda kv: -kv[1]["sl"])[:FEATURE_QUOTA]
        feature.update(best)
    print(f"  feature  {len(feature)}", file=sys.stderr)

    chosen = dict(unesco)
    chosen.update(feature)
    chosen.update(iconic)  # a name in two buckets is the more interesting one

    # Report which corrections fired. A correction that stops firing is one
    # Wikidata has fixed, and leaving it in the file pretends to a defect
    # that is no longer there.
    fired, idle = 0, []
    for name, (lat, lon, cc) in COORD_FIX.items():
        if name in chosen:
            chosen[name].update(lat=lat, lon=lon, cc=cc)
            fired += 1
        else:
            idle.append(name)
    for name, cc in COUNTRY_FIX.items():
        if name in chosen:
            chosen[name]["cc"] = cc
            fired += 1
        else:
            idle.append(name)
    for old, new in RENAME.items():
        if old in chosen:
            chosen[new] = chosen.pop(old)
            fired += 1
        else:
            idle.append(old)
    print(f"  fixed    {fired} corrections applied", file=sys.stderr)
    if idle:
        print(f"  STALE    no longer needed: {', '.join(sorted(idle))}",
              file=sys.stderr)

    def order(item):
        name, v = item
        return (0 if name in PREFER else 1, RANK[v["src"]], -v["sl"], len(name))

    kept, folded = {}, []
    for name, v in sorted(chosen.items(), key=order):
        if v["src"] == "unesco" and len(kept) >= TOTAL:
            continue  # the tail is backfill; take it after the icons
        near = next((n for n, w in kept.items() if haversine(v, w) < MIN_KM),
                    None)
        if near:
            folded.append((name, near))
            continue
        kept[name] = v
    print(f"  folded   {len(folded)} same-place duplicates", file=sys.stderr)

    for v in kept.values():
        v["cc"] = COUNTRY_NAMES.get(v["cc"], v["cc"])

    # A hint says where she was seen, so a blank country is a sentence that
    # cannot be written. Wikidata leaves P17 off a handful of sites; say so
    # rather than shipping the blank, since the test downstream only knows
    # that one got through, not which rebuild let it.
    blank = sorted(n for n, v in kept.items() if not v["cc"])
    if blank:
        print(f"  NO COUNTRY  add to COUNTRY_FIX: {', '.join(blank)}",
              file=sys.stderr)
    return kept


def write(kept: dict, out) -> None:
    out.write("# 1,000 known or interesting landmarks, from Wikidata (CC0) --\n"
              "# UNESCO World Heritage Sites (wdt:P1435 wd:Q9259), named icons,"
              " and\n# natural features. Selection and use:"
              " games/hue-and-cry/landmarks.py\n"
              "# name\tcountry\tlat\tlon\tsource\tsitelinks\n")
    rows = sorted(kept.items(), key=lambda kv: (-kv[1]["sl"], kv[0]))
    for name, v in rows:
        assert "\t" not in name, name
        out.write(f"{name}\t{v['cc']}\t{v['lat']:.5f}\t{v['lon']:.5f}"
                  f"\t{v['src']}\t{v['sl']}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", help="write TSV here (default: stdout)")
    args = ap.parse_args()

    kept = build()
    print(f"  total    {len(kept)}", file=sys.stderr)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            write(kept, fh)
    else:
        write(kept, sys.stdout)


if __name__ == "__main__":
    main()
