"""Fetch the facts a hint can be written from, into `facts.tsv` and
`countries.tsv`.

    python3 games/carmel-taldiego/build_facts.py

Same shape as `build_landmarks.py` and for the same reason: the network is
here, not in the game. It needs a minute or two and is not run by CI.

WHY THERE ARE FACTS AT ALL. A hint is a sentence somebody reads and
believes, and this document's oldest scar is a uniformly drawn matrix that
produced **`Reykjavik: desert`** -- the line somebody screenshots to show
the thing is broken. Every descriptor a landmark carries has to be *true of
that landmark*, so it has to come from somewhere checkable. It comes from
here.

WHAT IS FETCHED, and each is chosen because it is (a) checkable and (b)
shared by many landmarks, which is the collision the chase needs:

- **per landmark** -- `P31` types, `P2044` elevation, `P571` founding year,
  `P206` the body of water it stands on, `P1174` annual visitors. Only the
  types are near-universal (991 of 1000); elevation is on 238 and founding
  on 391, which is why the vocabulary leans on types and coordinates and
  treats the rest as bonus.
- **per country** -- `P30` continent, `P38` currency, `P37` official
  language, `P1622` which side of the road, `P31 = Q123480` landlocked.
  `P282` writing system was tried first and is on only 59 of 162 countries;
  script is derived from the language instead, in `descriptors.py`.

Landmarks are looked up by `qid`, never by label -- see `landmarks.py` on
why the name is not an identifier. Countries are looked up by label, which
is safe only because the label came from Wikidata in the first place.
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from landmarks import load  # noqa: E402

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "hue-and-cry-gazetteer/1.0 (https://github.com/gald33/ai-lab)"
RETRIES = 5
CHUNK = 120

# `build_landmarks.py` shortens one country for readability, and the short
# form is a different Wikidata item -- "China"@en labels the historical
# state, not the one with a side of the road. Ask under the label Wikidata
# uses; file under the label the hints will read.
COUNTRY_ALIAS = {"China": "People's Republic of China"}

LANDMARK_Q = """
SELECT ?item ?p31L ?elev ?inception ?waterL ?visitors ?tzL ?critL ?listed WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item wdt:P2614 ?c . ?c rdfs:label ?critL . FILTER(lang(?critL)="en") }
  OPTIONAL { ?item p:P1435/pq:P580 ?listed }
  OPTIONAL { ?item wdt:P31 ?p31 . ?p31 rdfs:label ?p31L . FILTER(lang(?p31L)="en") }
  OPTIONAL { ?item wdt:P421 ?tz . ?tz rdfs:label ?tzL . FILTER(lang(?tzL)="en") }
  # psn: is the SI-normalised value. `wdt:P2044` serves the raw number with
  # the unit thrown away, so Area 51's 4463 feet arrived as 4463 metres and
  # a desert airbase was reported as thinner air than Lhasa.
  OPTIONAL { ?item p:P2044/psn:P2044 ?ev . ?ev wikibase:quantityAmount ?elev }
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P206 ?w . ?w rdfs:label ?waterL . FILTER(lang(?waterL)="en") }
  OPTIONAL { ?item wdt:P1174 ?visitors }
}
"""

COUNTRY_Q = """
SELECT ?cL ?contL ?curL ?langL ?driveL ?landlocked ?orgL ?govL ?tzL WHERE {
  VALUES ?cL { %s }
  ?c rdfs:label ?cL .
  OPTIONAL { ?c wdt:P463 ?o . ?o rdfs:label ?orgL . FILTER(lang(?orgL)="en") }
  OPTIONAL { ?c wdt:P122 ?g . ?g rdfs:label ?govL . FILTER(lang(?govL)="en") }
  OPTIONAL { ?c wdt:P421 ?tz . ?tz rdfs:label ?tzL . FILTER(lang(?tzL)="en") }
  OPTIONAL { ?c wdt:P30 ?co . ?co rdfs:label ?contL . FILTER(lang(?contL)="en") }
  OPTIONAL { ?c wdt:P38 ?cu . ?cu rdfs:label ?curL . FILTER(lang(?curL)="en") }
  OPTIONAL { ?c wdt:P37 ?l . ?l rdfs:label ?langL . FILTER(lang(?langL)="en") }
  OPTIONAL { ?c wdt:P1622 ?d . ?d rdfs:label ?driveL . FILTER(lang(?driveL)="en") }
  OPTIONAL { ?c wdt:P31 ?t . BIND(IF(?t = wd:Q123480, true, ?undef) AS ?landlocked) }
}
"""


def query(sparql: str) -> list[dict]:
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": sparql})
    req = urllib.request.Request(
        url, headers={"Accept": "application/sparql-results+json",
                      "User-Agent": UA})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)["results"]["bindings"]
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError) as e:
            if attempt == RETRIES - 1:
                raise
            wait = 2 ** attempt * 5
            print(f"    {e}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)


def number(x) -> str:
    try:
        return f"{float(x):g}"
    except (TypeError, ValueError):
        return ""


def founding_year(stamp: str) -> str:
    """Wikidata dates are ISO-ish and can be BCE, where the leading minus is
    the whole point: Stonehenge's -3000 must not become 3000."""
    m = re.match(r"(-?\d{1,6})", stamp or "")
    return m.group(1) if m else ""


def landmark_facts(places: list[dict]) -> dict:
    out = {p["qid"]: {"types": set(), "water": set(), "tz": set(),
                      "crit": set()} for p in places}
    qids = [p["qid"] for p in places]
    for i in range(0, len(qids), CHUNK):
        chunk = qids[i:i + CHUNK]
        for b in query(LANDMARK_Q % " ".join("wd:" + q for q in chunk)):
            d = out[b["item"]["value"].rsplit("/", 1)[-1]]
            if "p31L" in b:
                d["types"].add(b["p31L"]["value"])
            if "waterL" in b:
                d["water"].add(b["waterL"]["value"])
            if "tzL" in b:
                d["tz"].add(b["tzL"]["value"])
            if "critL" in b:
                d["crit"].add(b["critL"]["value"])
            if "listed" in b:
                d.setdefault("listed", b["listed"]["value"])
            if "elev" in b:
                # Everest carries five: 8848, 8848.86, 8850, 8844.43 and a
                # converted 8848.36. Any is fine for a band; take the least
                # so the number is never overstated.
                v = float(b["elev"]["value"])
                d["elev"] = v if "elev" not in d else min(d["elev"], v)
            for key in ("inception", "visitors"):
                if key in b:
                    d.setdefault(key, b[key]["value"])
        print(f"  landmarks {i + len(chunk)}/{len(qids)}", file=sys.stderr)
    return out


def country_facts(names: list[str]) -> dict:
    fields = ("continent", "currency", "language", "drive", "org", "gov", "tz")
    out = defaultdict(lambda: {f: set() for f in fields} | {"landlocked": False})
    ask = {COUNTRY_ALIAS.get(n, n): n for n in names}
    labels = sorted(ask)
    for i in range(0, len(labels), 60):
        chunk = labels[i:i + 60]
        values = " ".join('"%s"@en' % n.replace('"', "") for n in chunk)
        for b in query(COUNTRY_Q % values):
            label = b["cL"]["value"]
            if label not in ask:
                continue
            d = out[ask[label]]
            for field, var in zip(fields, ("contL", "curL", "langL", "driveL",
                                           "orgL", "govL", "tzL")):
                if var in b:
                    d[field].add(b[var]["value"])
            if "landlocked" in b:
                d["landlocked"] = True
        print(f"  countries {i + len(chunk)}/{len(labels)}", file=sys.stderr)
    return out


def write_landmarks(facts: dict, places: list[dict], out) -> None:
    out.write(
        "# Per-landmark facts from Wikidata (CC0), fetched by build_facts.py.\n"
        "# types is |-separated P31 labels. elev metres (P2044), founded year\n"
        "# (P571, negative is BCE), water is P206 labels, visitors is P1174,\n"
        "# tz is P421 time zone labels, crit is P2614 World Heritage\n"
        "# criteria, listed is the P1435 inscription year (qualifier P580).\n"
        "# qid\ttypes\telev\tfounded\twater\tvisitors\ttz\tcrit\tlisted\n")
    for p in places:
        v = facts[p["qid"]]
        out.write("\t".join([
            p["qid"], "|".join(sorted(v["types"])), number(v.get("elev")),
            founding_year(v.get("inception", "")), "|".join(sorted(v["water"])),
            number(v.get("visitors")), "|".join(sorted(v["tz"])),
            "|".join(sorted(v["crit"])),
            founding_year(v.get("listed", ""))]) + "\n")


def write_countries(facts: dict, out) -> None:
    out.write(
        "# Per-country facts from Wikidata (CC0), fetched by build_facts.py.\n"
        "# continent P30, currency P38, language P37, drive P1622,\n"
        "# landlocked P31 = Q123480, org P463 memberships, gov P122 basic\n"
        "# form of government, tz P421 time zones.\n"
        "# country\tcontinent\tcurrency\tlanguage\tdrive\tlandlocked"
        "\torg\tgov\ttz\n")
    for name in sorted(facts):
        d = facts[name]
        out.write("\t".join([
            name, "|".join(sorted(d["continent"])),
            "|".join(sorted(d["currency"])), "|".join(sorted(d["language"])),
            "|".join(sorted(d["drive"])), "1" if d["landlocked"] else "0",
            "|".join(sorted(d["org"])), "|".join(sorted(d["gov"])),
            "|".join(sorted(d["tz"])),
        ]) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--facts", default=str(Path(__file__).with_name("facts.tsv")))
    ap.add_argument("--countries",
                    default=str(Path(__file__).with_name("countries.tsv")))
    args = ap.parse_args()

    places = load()
    lf = landmark_facts(places)
    with open(args.facts, "w", encoding="utf-8") as fh:
        write_landmarks(lf, places, fh)

    names = sorted({p["country"] for p in places})
    cf = country_facts(names)
    missing = [n for n in names if n not in cf]
    if missing:
        print(f"  NO COUNTRY DATA: {', '.join(missing)}", file=sys.stderr)
    with open(args.countries, "w", encoding="utf-8") as fh:
        write_countries(cf, fh)
    print(f"  wrote {len(lf)} landmarks, {len(cf)} countries", file=sys.stderr)


if __name__ == "__main__":
    main()
