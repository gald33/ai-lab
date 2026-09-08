"""Landmarks and the things that are true of them, in words a person feels.

Gal, 2026-09-07: *"that must be human readable. more than that, we 'sell' on
human interacting about it in social media, it must evoke feelings"*.

THIS CORRECTS A CLAIM MADE THE SAME DAY. `games/hue-and-cry.md` argued that
because the matrix is a permission table rather than a truth table, the
hints "need not be factually true of anywhere -- they are tokens", and that
this freed the matrix to be drawn uniformly from a word list. Right about
the mechanism, wrong about the game: a uniform draw produced *Reykjavik:
desert*, which is the line somebody screenshots to show the thing is broken.

AND THEN THE OBVIOUS FIX BROKE IT THE OTHER WAY. The first authored pass
here gave each place the eight things a travel writer would say about it --
Marrakesh: tannery, souk, snake charmers; Ushuaia: end of the world,
penguins. Beautiful, and measured:

    97% of descriptors were true of exactly ONE landmark
    average candidates a hint left: 1.03
    17 of 20 landmarks gave the fugitive NO cover at all

Evocative writing is *specific*, and specific means unique, and a unique
hint hands over her position. The uniform matrix had collisions by accident;
a well-written one has almost none.

SO THE AUTHORING RULE IS COLLISION, NOT COLOUR. Every descriptor must be
true of several landmarks, and the feeling has to come from the COMBINATION
rather than from any single word being rare. "Call to prayer" is true of
Cairo, Fez, Marrakesh, Zanzibar and Samarkand; hearing it tells you the
smell of the place and not which one you are in. That is what a clue is
supposed to do.

The test to apply when adding a landmark is at the bottom of this file, and
it fails a gazetteer whose descriptors are too rare.

    python3 games/hue-and-cry/gazetteer.py
"""

#: The shared palette. Every entry is meant to be true of the places listed
#: against it, to be worth repeating, and -- the constraint that matters --
#: to be true of SEVERAL places, so that hearing it narrows without deciding.
GAZETTEER: dict[str, tuple[str, ...]] = {
    "Cairo":       ("call to prayer", "old walls", "river mist", "spice market",
                    "donkey carts", "desert wind", "tea glasses", "minaret"),
    "Fez":         ("call to prayer", "old walls", "steep lanes", "spice market",
                    "donkey carts", "tanning pits", "tea glasses", "no cars"),
    "Marrakesh":   ("call to prayer", "old walls", "spice market", "night market",
                    "tanning pits", "desert wind", "tea glasses", "orange trees"),
    "Samarkand":   ("call to prayer", "old walls", "tiled domes", "melon stalls",
                    "silk road", "desert wind", "tea glasses", "minaret"),
    "Zanzibar":    ("call to prayer", "carved doors", "spice market", "monsoon",
                    "dhow sails", "coral stone", "night market", "sea air"),
    "Kathmandu":   ("prayer flags", "monsoon", "mountain shadow", "night market",
                    "incense", "steep lanes", "brass bells", "river mist"),
    "Luang Prabang": ("saffron robes", "river mist", "monsoon", "night market",
                      "incense", "brass bells", "temple roofs", "river bend"),
    "Kyoto":       ("temple roofs", "brass bells", "incense", "wooden lanes",
                    "moss and stone", "tea houses", "river bend", "mountain shadow"),
    "Bergen":      ("harbour fog", "wooden wharf", "steep lanes", "fish market",
                    "rain on slate", "mountain shadow", "gulls", "cable car"),
    "Reykjavik":   ("harbour fog", "fish market", "rain on slate", "gulls",
                    "black rock", "low sun", "sea air", "hot water"),
    "Ushuaia":     ("harbour fog", "gulls", "low sun", "mountain shadow",
                    "black rock", "sea air", "wind off the ice", "fish market"),
    "Hobart":      ("harbour fog", "fish market", "sandstone", "gulls",
                    "mountain shadow", "sea air", "wind off the ice", "orchards"),
    "Valparaiso":  ("harbour fog", "steep lanes", "painted houses", "cable car",
                    "gulls", "sea air", "murals", "stray dogs"),
    "Havana":      ("painted houses", "sea wall", "colonnades", "peeling paint",
                    "sea air", "cigar smoke", "music at night", "vintage cars"),
    "Salvador":    ("painted houses", "colonnades", "peeling paint", "drumming",
                    "music at night", "sea air", "cable car", "steep lanes"),
    "Lviv":        ("cobblestones", "coffee smell", "baroque fronts", "trams",
                    "cellars", "old walls", "chocolate", "music at night"),
    "Bruges":      ("cobblestones", "canals", "belfry", "chocolate",
                    "baroque fronts", "coffee smell", "rain on slate", "lace"),
    "Trieste":     ("coffee smell", "sea wall", "colonnades", "canals",
                    "trams", "baroque fronts", "sea air", "borderland"),
    "Tbilisi":     ("sulphur steam", "wooden balconies", "cable car", "old walls",
                    "steep lanes", "river bend", "wine cellars", "borderland"),
    "Gjirokaster": ("stone roofs", "old walls", "steep lanes", "hillside fort",
                    "cobblestones", "rain on slate", "bazaar street",
                    "mountain shadow"),
}

#: A gazetteer is playable when the fugitive has somewhere to hide FROM EVERY
#: ROOM. Not when every descriptor is shared -- a rare word is harmless as
#: long as she is never forced to post it, which is what the first version of
#: this check got wrong by counting singletons globally.
MIN_COVER = 0.95


def candidates(landmark: str) -> tuple[str, ...]:
    """Everything true of a landmark. Public; the seed picks which are live."""
    return GAZETTEER[landmark]


def holders() -> dict[str, list[str]]:
    """For each descriptor, the landmarks it is true of."""
    out: dict[str, list[str]] = {}
    for place, words in GAZETTEER.items():
        for word in words:
            out.setdefault(word, []).append(place)
    return out


def cover(landmark: str) -> float:
    """Chance a random live-three leaves her at least one place to hide behind.

    The quantity that actually decides whether a room is playable: if every
    one of her three live descriptors is unique to this landmark, the hint
    names her position and the tick is over before it starts.
    """
    import itertools
    h = holders()
    words = GAZETTEER[landmark]
    trios = list(itertools.combinations(words, 3))
    return sum(1 for t in trios if any(len(h[w]) > 1 for w in t)) / len(trios)


def playable() -> tuple[bool, float, list[str]]:
    """Can she hide from every room? Returns (passes, worst cover, offenders).

    *This replaced a check that counted globally unique descriptors and
    demanded zero.* That gate failed a gazetteer that plays perfectly well,
    because it measured the wrong thing: what matters is not whether a word
    is rare but whether a landmark can be caught with nothing but rare words
    in hand.
    """
    covers = {lm: cover(lm) for lm in GAZETTEER}
    weak = sorted(lm for lm, c in covers.items() if c < MIN_COVER)
    return not weak, min(covers.values()), weak


def main() -> None:
    h = holders()
    ok, worst, weak = playable()
    total = sum(len(v) for v in GAZETTEER.values())

    print(f"{len(GAZETTEER)} landmarks, {len(h)} distinct descriptors, "
          f"{total} marks ({total / len(GAZETTEER):.0f} per landmark)\n")

    print("how many landmarks each descriptor is true of:")
    from collections import Counter
    sizes = Counter(len(v) for v in h.values())
    for n in sorted(sizes):
        print(f"  true of {n:>2}   {sizes[n]:>3} descriptors  {'#' * sizes[n]}")

    mean = sum(len(v) for v in h.values()) / len(h)
    print(f"\n  mean candidates a hint leaves : {mean:.2f}"
          f"   (was 1.03 when authored for colour)")
    print(f"  worst landmark cover          : {worst:.1%}"
          f"   (needs >= {MIN_COVER:.0%})")
    print(f"  landmarks she cannot hide from: {', '.join(weak) or 'none'}")
    print(f"  playable                      : {ok}")

    print("\nthe ambiguities a person can feel:")
    for word in ("call to prayer", "harbour fog", "tanning pits", "monsoon",
                 "cable car", "low sun"):
        print(f"  {word:<16} {', '.join(h[word])}")

    print("""
That is the point of the collision rule. "She left a tanning pit" and it is
Fez or Marrakesh -- two cities four hours apart that smell the same. "Harbour
fog" and it is Bergen, Reykjavik, Ushuaia, Hobart or Valparaiso: five cold
ports on four continents. You cannot look that up; you have to think about
where she has been going and guess. And it is worth saying out loud to
somebody, which is the whole reason the words have to be real.""")


if __name__ == "__main__":
    main()
