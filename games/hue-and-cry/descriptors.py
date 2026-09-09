"""What is true of a landmark, in words a witness could have used.

A hint is one descriptor, dressed as a sentence. This module is the
descriptor half: it reads `landmarks.tsv`, `facts.tsv` and `countries.tsv`
and returns, for every landmark, the set of things a person standing there
could truthfully say about it.

    python3 games/hue-and-cry/descriptors.py

TWO RULES, AND THEY PULL AGAINST EACH OTHER. Both are already paid for in
`games/hue-and-cry.md` and neither is negotiable:

1. **Every descriptor must be true of its landmark.** The scar is
   `Reykjavik: desert` from a uniformly drawn matrix -- the line somebody
   screenshots to show the game is broken. So nothing here is invented:
   every descriptor is a function of a fetched fact or a coordinate.
2. **Every descriptor must be true of MANY landmarks.** The other scar is
   the authored pass that read beautifully and measured 97% singletons,
   1.03 candidates, 17 of 20 landmarks with no cover at all. *Evocative
   writing is specific, and specific hands over her position.* The feeling
   has to come from the combination, not the word.

Rule 2 is why this vocabulary is deliberately coarse. `sacred_ground` covers
a cathedral, a stupa and a Sufi shrine; that is the point, not a
shortcoming. A descriptor true of one landmark is a descriptor that ends the
chase, so `rarest()` prints the tail and the tests hold a floor under it.

WHERE EACH ONE COMES FROM. Three sources, in decreasing coverage:

- **Coordinates** (1000/1000) -- hemisphere, latitude band. Never missing,
  so these are the backstop that stops a landmark having nothing to say.
- **Country** (1000/1000) -- continent, which side of the road, landlocked,
  currency family, script. Script is derived from the official language
  because Wikidata's `P282` is on 59 countries of 162 and its `P37` is on
  158; a fact you have for a sixth of the map is not a fact you can build a
  vocabulary on.
- **The landmark itself** (types 991, elevation 238, founding 391) -- what
  kind of place it is, how high, how old, whether it stands on water.

The type table is matched on substrings of Wikidata's `P31` labels, which
is crude and is the right crudeness: `P31` gives "Catholic cathedral",
"minor basilica" and "Hindu temple" for what one witness would call a place
of worship, and enumerating that tail exactly would be a worse job than
matching "cathedral", "basilica" and "temple".
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from landmarks import load  # noqa: E402

FACTS = Path(__file__).with_name("facts.tsv")
COUNTRIES = Path(__file__).with_name("countries.tsv")

# Substrings of Wikidata P31 labels. Order is irrelevant; a landmark takes
# every group it matches, and most take two or three.
TYPES = {
    # Places of worship, split four ways rather than one, because
    # `sacred_ground` over eighty landmarks was a word that covered every
    # exit she had and therefore told a searcher nothing.
    "a_church_or_cathedral": ["church", "cathedral", "basilica", "chapel",
                              "minster", "collegiate"],
    "a_mosque_or_madrasa": ["mosque", "madrasa", "masjid", "musalla"],
    "a_temple_or_pagoda": ["temple", "pagoda", "stupa", "shrine", "torii"],
    "a_monastery": ["monastery", "abbey", "convent", "priory", "cloister",
                    "friary", "lavra"],

    # What a dig looks like, and what a ruin looks like, are different
    # sights and a witness would say so.
    "a_dug_site": ["archaeological", "excavation", "tell ", "midden"],
    "a_ruined_city": ["ancient city", "ruin", "abandoned", "ghost town",
                      "lost city", "oppidum"],
    "standing_stones": ["megalith", "dolmen", "menhir", "stone circle",
                        "petroglyph", "rock art", "cairn", "runestone"],

    "walls_and_gates": ["fortification", "citadel", "city wall", "stronghold",
                        "fort", "bastion", "defensive", "rampart"],
    "a_castle": ["castle", "keep", "tower house"],
    "royal_rooms": ["palace", "château", "chateau", "residence", "villa",
                    "manor", "stately home", "court"],

    "underground": ["cave", "catacomb", "crypt", "tunnel", "grotto",
                    "cenote"],
    "a_working_face": ["mine", "quarry", "colliery", "pit head"],

    "a_national_park": ["national park"],
    "a_reserve": ["nature reserve", "protected area", "biosphere",
                  "wildlife", "natural park", "game reserve",
                  "natural reserve", "conservation"],

    "a_mountain": ["mountain", "peak", "massif", "summit", "hill",
                   "plateau", "ridge"],
    "a_volcano": ["volcano", "caldera", "crater", "lava"],
    "deep_cut": ["canyon", "valley", "gorge", "ravine", "fjord"],
    "standing_water": ["lake", "reservoir", "lagoon", "pond", "sea"],
    "falling_water": ["waterfall", "cascade", "geyser", "hot spring",
                      "spring"],
    "dry_country": ["desert", "dune", "oasis", "salt flat", "salt pan",
                    "badland"],
    "ringed_by_water": ["island", "archipelago", "atoll", "reef", "islet",
                        "peninsula", "cay"],
    "forest_dark": ["forest", "rainforest", "jungle", "woodland", "taiga"],
    "wide_water": ["river", "delta", "estuary", "wetland", "marsh", "swamp",
                   "floodplain"],

    "a_living_city": ["urban area", "city", "town", "human settlement",
                      "municipality", "borough", "capital"],
    "an_old_quarter": ["old town", "historic centre", "historic center",
                       "historic district", "architectural ensemble",
                       "group of structures"],

    "machine_age": ["factory", "industrial", "railway", "canal",
                    "power plant", "mill", "furnace", "shipyard", "foundry",
                    "manufactur"],
    "a_span_or_a_channel": ["bridge", "aqueduct", "dam", "viaduct", "lock",
                            "lighthouse", "harbour", "port"],
    "an_instrument": ["observatory", "telescope", "laboratory", "station"],

    "glass_cases": ["museum", "gallery", "library", "archive"],
    "a_garden": ["garden", "park", "arboretum", "botanical"],
    "worked_land": ["cultural landscape", "vineyard", "terrace", "plantation",
                    "agricultur", "estate", "orchard", "pasture", "field"],
    "graves": ["necropolis", "tomb", "cemetery", "mausoleum", "burial",
               "barrow", "tumulus", "grave", "sepulchre", "pyramid"],
}

# WHAT USED TO BE HERE, AND THE MEASUREMENT THAT REMOVED IT.
#
# Four axes were built and then deleted: currency, script, language family
# and time zone. They were the most evocative descriptors on the map --
# "the signs were in Cyrillic", "her watch was three hours ahead of London"
# -- and they were wrong.
#
# The tell was in a sample of six landmarks' descriptors:
#
#     Eiffel Tower   ... pays_in_francs
#     Area 51        ... an_austronesian_tongue, still_yesterday_where_she_is
#
# France has not paid in francs since 2002; Wikidata's truthy `wdt:P38`
# still serves the CFP franc. Nobody speaks an Austronesian language in
# Nevada; the United States carries Hawaiian, Samoan, Chamorro and
# Carolinian on `P37` because they are official *somewhere* in it, and it
# spans fifteen time zones for the same reason.
#
# Three rounds of filtering were tried -- excluding ended statements
# (`pq:P582`), then part-scoped ones (`pq:P518`, `pq:P3005`), then
# deprecated rank. Each round traded one falsehood for another: with the
# full filter, France and Germany have no currency at all and the United
# States has no official language. Wikidata's modelling of these properties
# is not consistent enough to read mechanically, and **a hint that is false
# is worse than a hint that is missing** -- which is this game's oldest
# rule, written after `Reykjavik: desert`.
#
# So they are gone, and the fetched columns are kept in `facts.tsv` and
# `countries.tsv` as the evidence rather than deleted. Bringing them back
# means a hand-written and hand-checked table of 159 countries, not a
# cleverer query. Do not re-derive them from `P37`, `P38` or `P421`.

# Memberships that some countries have and others do not. The universal
# ones -- the UN, Interpol, UNESCO, the Universal Postal Union -- are on
# 148 to 154 of 159 countries and are therefore worthless as hints, which
# is the ceiling problem in miniature: a fact true of everywhere narrows
# nothing. These sit between 17 and 43.
ORGS = {
    "flies_the_ring_of_stars": ["European Union"],
    "no_passport_needed_next_door": ["Schengen Area"],
    "the_old_empire_in_common": ["Commonwealth of Nations"],
    "under_the_atlantic_treaty": ["NATO"],
    "in_the_arab_league": ["Arab League"],
    "in_the_african_union": ["African Union"],
    "in_the_american_states": ["Organization of American States"],
    "in_the_council_of_europe": ["Council of Europe"],
    # Both names are the same body; Wikidata records either.
    "french_is_spoken_at_the_top": ["Francophonie",
                                    "Organisation internationale de la Francophonie"],
    "in_the_islamic_conference": ["Organisation of Islamic Cooperation"],
    "one_of_the_twenty": ["G20"],
}

GOVERNMENT = {
    "a_crown_still_on_the_coins": ["monarchy"],
    "a_republic": ["republic"],
    "a_federation_of_states": ["federal", "federation"],
    "a_prime_minister_not_a_president": ["parliamentary"],
    "a_president_who_governs": ["presidential"],
}

# Language families, which are what a witness hears rather than what they
# read. Derived from P37 for the same reason the script table is: P37 is on
# 158 countries of 159.
LANGUAGE_FAMILY = {
    "a_romance_tongue": ["spanish", "french", "portuguese", "italian",
                         "romanian", "catalan", "galician", "moldovan"],
    "a_germanic_tongue": ["english", "german", "dutch", "swedish",
                          "norwegian", "danish", "icelandic", "afrikaans",
                          "luxembourgish", "faroese", "frisian"],
    "a_slavic_tongue": ["russian", "polish", "czech", "slovak", "ukrainian",
                        "bulgarian", "serbian", "croatian", "slovene",
                        "macedonian", "belarusian", "bosnian", "montenegrin"],
    "a_turkic_tongue": ["turkish", "azerbaijani", "kazakh", "kyrgyz",
                        "turkmen", "uzbek", "tatar", "uyghur"],
    "a_semitic_tongue": ["arabic", "hebrew", "amharic", "tigrinya",
                         "maltese", "aramaic"],
    "a_bantu_tongue": ["swahili", "zulu", "xhosa", "shona", "kinyarwanda",
                       "kirundi", "chichewa", "sotho", "tswana", "lingala",
                       "kikongo", "luganda", "ndebele", "swati", "venda"],
    "an_indic_tongue": ["hindi", "bengali", "nepali", "sinhala", "urdu",
                        "marathi", "gujarati", "punjabi", "assamese",
                        "odia", "divehi", "dzongkha"],
    "an_austronesian_tongue": ["malay", "indonesian", "tagalog", "filipino",
                               "javanese", "malagasy", "samoan", "fijian",
                               "tongan", "maori", "chamorro", "marshallese",
                               "palauan", "nauruan", "tetum", "hawaiian"],
    "a_creole_is_spoken": ["creole", "papiamento", "bislama", "tok pisin",
                           "sango", "seychellois", "krio"],
}


#: A descriptor OFFERED by fewer than this many landmarks ends the chase
#: when she is forced to post it, so it is dropped and named in the report.
#:
#: 16 rather than a rounder 20 because 20 leaves the Negev with two
#: candidates and the seed needs three to make live. Swept, and the choice
#: costs nothing either way -- 20 gives 2.73 posted and 11.6% pinned, 16
#: gives 2.69 and 12.3%, 8 gives 2.68 and 12.3%. What the floor protects
#: against is the tail, not the average, and the tail is where a landmark
#: runs out of things to say.
MIN_SHARED = 16

#: How many descriptors a landmark actually offers, out of everything true
#: of it. THE PARAMETER THAT MAKES THE MAP PLAYABLE, and it is not in the
#: twenty-landmark gazetteer because at twenty landmarks it was not needed.
#:
#: A thousand landmarks derived seventeen true descriptors each, and she
#: posts the *least* informative one she holds, so a single map-wide word
#: -- `north_of_the_line` is true of 855 -- covers every exit she has and
#: the hint says nothing. Measured, over 50,000 of her moves:
#:
#:     everything true of it (17 each)   she posts 4.96 of her 5 exits
#:     her six most distinctive           she posts 2.83
#:
#: A global ceiling was tried first and starves the map: dropping every
#: descriptor above 200 holders leaves 73 landmarks with nothing to say,
#: because a landmark in a country that holds thirty of them has only
#: country-wide words. The per-landmark rule cannot starve anything -- it
#: takes the six rarest of whatever a landmark has -- and lands on the
#: twenty-landmark map's own operating point.
CANDIDATES = 6

#: How wide the band of look-alikes is that a game draws her five exits
#: from. `gazetteer.py` uses 6 and that is right for its twenty landmarks;
#: at a thousand the six most similar are near-clones -- a landmark shares
#: 13.0 of its 13.7 raw descriptors with them -- so every hint covered every
#: exit and none of them discriminated. Swept, six trials each over every
#: landmark and every exit (50,000 of her moves per row):
#:
#:       N    she posts   pinned   median hop
#:       6      4.55       0.7%     1,425 km
#:      30      4.02       2.5%     2,163 km
#:      60      3.61       4.3%     2,625 km
#:     120      3.11       7.6%     3,479 km
#:     200      2.71      11.8%     4,223 km      <- here
#:     300      2.40      16.2%     4,978 km
#:     999      1.95      27.1%     6,982 km
#:
#: 200 is chosen because it lands on the twenty-landmark map's own measured
#: behaviour -- 2.60 posted and 12.8% pinned, which is the number
#: `games/hue-and-cry.md` records for `neighbourhood exits, 5 each`. Both
#: numbers matter and they pull opposite ways: a hint that leaves all five
#: exits standing says nothing, and one that leaves a single exit hands over
#: her position. Reproduce with `python3 games/hue-and-cry/descriptors.py
#: --sweep`.
#: SUPERSEDED IN PLAY, 2026-09-09 ("we have no routes"): the band this
#: sized no longer exists, and `sweep` below is the record of how it was
#: chosen rather than a live parameter. `MIN_SHARED` and `CANDIDATES` are
#: not superseded and matter more -- a descriptor true of too few places is
#: now identifying against the whole map, not merely against five exits.
NEIGHBOURHOOD = 200


def _rows(path: Path) -> list[list[str]]:
    return [line.split("\t")
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]


def facts() -> dict:
    out = {}
    for qid, types, elev, founded, water, visitors, tz, crit, listed in _rows(FACTS):
        out[qid] = {
            "types": [t for t in types.split("|") if t],
            "elev": float(elev) if elev else None,
            "founded": int(founded) if founded else None,
            "water": [w for w in water.split("|") if w],
            "visitors": float(visitors) if visitors else None,
            "crit": [c for c in crit.split("|") if c],
            "listed": int(listed) if listed.strip() else None,
        }
    return out


def countries() -> dict:
    out = {}
    for name, cont, cur, lang, drive, landlocked, org, gov, tz in _rows(COUNTRIES):
        out[name] = {
            "continent": [c for c in cont.split("|") if c],
            "currency": [c for c in cur.split("|") if c],
            "language": [x for x in lang.split("|") if x],
            "drive": [d for d in drive.split("|") if d],
            "landlocked": landlocked == "1",
            "org": [o for o in org.split("|") if o],
            "gov": [g for g in gov.split("|") if g],
            "tz": [z for z in tz.split("|") if z],
        }
    return out


# The ten World Heritage criteria, which are the best descriptors on this
# map and were nearly missed. They are on 832 of the 1000, each true of
# between 87 and 388, and -- the part that matters -- they say what kind of
# thing a place *is* rather than where it sits, so two landmarks in the same
# country routinely differ on them. Everything before them was geography and
# governance, which is why every European landmark looked alike.
#
# The wording is a witness's, not UNESCO's. The committee says criterion
# (vii) is "superlative natural phenomena or areas of exceptional natural
# beauty"; a person says they could not stop looking at it.
CRITERIA = {
    "(i)": "somebody_made_this_by_hand",
    "(ii)": "two_traditions_met_here",
    "(iii)": "the_last_of_its_people",
    "(iv)": "a_kind_of_building_at_its_best",
    "(v)": "worked_the_same_way_for_centuries",
    "(vi)": "something_famous_happened_here",
    "(vii)": "you_cannot_stop_looking_at_it",
    "(viii)": "the_earth_showing_its_workings",
    "(ix)": "living_things_doing_what_they_do",
    "(x)": "the_last_animals_of_their_kind",
}


def _by_word(table: dict, haystack: str) -> set:
    return {key for key, words in table.items()
            if any(w in haystack for w in words)}


def _by_name(table: dict, names: list[str]) -> set:
    """Exact membership, not a substring search.

    `ORGS` was matched with `_by_word` and it was wrong in a way that is
    worth keeping written down, because it is the same failure as
    `Reykjavik: desert` arriving through a different door. "African Union"
    is a substring of **"United Nations-African Union Hybrid Operation in
    Darfur"**, a peacekeeping mission, so 19 countries that merely
    contribute troops -- China, Germany, Bangladesh, Ecuador, Jamaica --
    were reported as sitting in the African Union. "European Union" is a
    substring of "potential enlargement of the European Union", so Georgia
    flew the ring of stars on its number plates.

    A substring test is fine for `P31` type labels, where "cathedral"
    inside "Catholic cathedral" is exactly the generalisation wanted. It is
    wrong for the name of a body you are either in or not in.
    """
    have = set(names)
    return {key for key, wanted in table.items()
            if any(w in have for w in wanted)}


def describe(place: dict, fact: dict, country: dict) -> set:
    """Everything truthfully sayable about one landmark."""
    out = _by_word(TYPES, " | ".join(fact["types"]).lower())

    lat, lon = place["lat"], place["lon"]
    out.add("north_of_the_line" if lat >= 0 else "south_of_the_line")
    if abs(lat) < 23.5:
        out.add("inside_the_tropics")
    if abs(lat) > 45:
        out.add("far_from_the_equator")
    if lat > 55:
        out.add("long_dark_winter")
    out.add("east_of_greenwich" if lon >= 0 else "west_of_greenwich")

    for continent in country["continent"]:
        out.add("in_" + continent.lower().replace(" ", "_"))
    if country["landlocked"]:
        out.add("no_coast_in_this_country")
    if "left" in country["drive"]:
        out.add("traffic_keeps_left")
    out |= _by_name(ORGS, country["org"])
    out |= _by_word(GOVERNMENT, " | ".join(country["gov"]).lower())

    if fact["elev"] is not None:
        if fact["elev"] > 1500:
            out.add("thin_air")
        # Bounded below as well as above: the Dead Sea is 441 metres down,
        # and "at sea level" is not a true thing to say about it.
        if -50 <= fact["elev"] < 20:
            out.add("at_sea_level")
        if fact["elev"] < -50:
            out.add("below_the_sea_outside")
    if fact["water"]:
        out.add("water_at_its_feet")
    if fact["founded"] is not None:
        if fact["founded"] < 500:
            out.add("older_than_the_records")
        elif fact["founded"] < 1500:
            out.add("standing_before_the_maps")
        elif fact["founded"] > 1900:
            out.add("within_living_memory")
    if fact["visitors"] is not None and fact["visitors"] > 500_000:
        out.add("thick_with_visitors")

    for c in fact["crit"]:
        if c in CRITERIA:
            out.add(CRITERIA[c])
    if fact["listed"] is not None:
        # P1435 is heritage designation of any kind, not the World Heritage
        # list: the Eiffel Tower's 1964 is its monument historique. So the
        # wording says protected, which is true of every one of them.
        if fact["listed"] < 1985:
            out.add("guarded_since_before_the_tourists")
        elif fact["listed"] < 1995:
            out.add("protected_in_the_eighties_or_nineties")
        elif fact["listed"] < 2008:
            out.add("protected_around_the_millennium")
        else:
            out.add("protected_only_recently")
    return out


def raw_descriptors() -> dict:
    """{landmark name -> set of descriptors}, before the collision floor."""
    f, c = facts(), countries()
    return {p["name"]: describe(p, f[p["qid"]], c[p["country"]])
            for p in load()}


def below_floor(raw: dict | None = None) -> list[tuple[str, int]]:
    raw = raw if raw is not None else raw_descriptors()
    counts = Counter(d for s in raw.values() for d in s)
    return sorted(((d, n) for d, n in counts.items() if n < MIN_SHARED),
                  key=lambda kv: kv[1])


def all_descriptors() -> dict:
    """{landmark name -> its candidate descriptors}, as the game uses them.

    The seed picks three of these to be live in a given game; this is the
    pool it picks from, and it is the six *rarest* true things about the
    landmark rather than everything true of it. See `CANDIDATES`.
    """
    raw = raw_descriptors()
    counts = Counter(d for s in raw.values() for d in s)

    # The floor has to hold on what a searcher can SEE, which is the
    # candidate sets and not the raw truth. Applied once, before selection,
    # it let `north_of_the_line` through: true of 855 landmarks, and offered
    # by five, because only those five had nothing rarer. A searcher who
    # knows the rule -- and the rule is public -- reads that as five
    # candidates, which is a pin wearing a common word's clothes.
    #
    # So drop and reselect until the counts stop moving. It converges in a
    # handful of passes and the bound is there to say so rather than to be
    # reached.
    banned: set[str] = set()
    for _ in range(20):
        chosen = {name: sorted((s - banned),
                               key=lambda d: (counts[d], d))[:CANDIDATES]
                  for name, s in raw.items()}
        offered = Counter(d for v in chosen.values() for d in v)
        thin = {d for d, n in offered.items() if n < MIN_SHARED}
        if not thin:
            return {name: set(v) for name, v in chosen.items()}
        banned |= thin
    raise RuntimeError("the collision floor did not settle")


def rarest(n: int = 12) -> list[tuple[str, int]]:
    """The tail, because a descriptor true of one landmark ends the chase."""
    counts = Counter(d for s in all_descriptors().values() for d in s)
    return counts.most_common()[: -n - 1: -1]


def sweep(bands=(6, 30, 60, 120, NEIGHBOURHOOD, 300), trials: int = 2) -> None:
    """The two numbers that decide whether this map plays, over N."""
    import gazetteer

    gaz = {k: sorted(v) for k, v in all_descriptors().items()}
    places = list(gaz)
    ranked = {p: [x for _, x in
                  sorted((-gazetteer.kinship(p, x, gaz), x)
                         for x in places if x != p)]
              for p in places}
    print(f"\n{'N':>5}{'she posts (of 5)':>19}{'pinned':>9}")
    for n in bands:
        rate, posted = _measure(gaz, ranked, n, trials)
        print(f"{n:>5}{posted:>19.2f}{rate:>9.2%}")


def _measure(gaz, ranked, n, trials, exits=5):
    import hashlib
    import hmac
    import os

    def draw(seed, tag, pool, key, count):
        out, i = [], 0
        while len(out) < count and i < 400:
            digest = hmac.new(seed, tag + b"\0" + key.encode() + bytes([i]),
                              hashlib.sha256).digest()
            pick = pool[int.from_bytes(digest[:8], "big") % len(pool)]
            if pick not in out:
                out.append(pick)
            i += 1
        return out

    total = pinned = posted = 0
    for _ in range(trials):
        seed = os.urandom(32)
        for here in ranked:
            reachable = draw(seed, b"exit", ranked[here][:n], here, exits)
            for destination in reachable:
                live = draw(seed, b"live", gaz[destination], destination, 3)
                sizes = [len([x for x in reachable if w in gaz[x]])
                         for w in live]
                total += 1
                pinned += max(sizes) == 1
                posted += max(sizes)
    return pinned / total, posted / total


def main() -> None:
    per = all_descriptors()
    counts = Counter(d for s in per.values() for d in s)
    print(f"{len(counts)} descriptors over {len(per)} landmarks\n")
    for key, n in counts.most_common():
        print(f"  {n:4}  {key}")

    sizes = Counter(len(s) for s in per.values())
    print("\n  descriptors per landmark:", dict(sorted(sizes.items())))
    thin = sorted(n for n, s in per.items() if len(s) < 3)
    print(f"  fewer than three: {len(thin)}"
          + (f"  {thin[:5]}" if thin else ""))

    dropped = below_floor()
    print(f"\n  dropped below the floor of {MIN_SHARED}:")
    for key, n in dropped:
        print(f"    {n:4}  {key}")
    print("\n  the thinnest that survived:")
    for key, n in rarest(6):
        print(f"    {n:4}  {key}")


if __name__ == "__main__":
    if "--sweep" in sys.argv:
        sweep()
    else:
        main()
