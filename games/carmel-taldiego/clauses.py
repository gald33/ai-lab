"""What a witness saw, for each descriptor. The authorship in this game.

`descriptors.py` says what is true of a landmark in the vocabulary's own
words -- `a_dug_site`, `traffic_keeps_left`. Nobody would repeat those. This
file is where the feeling comes from: for each descriptor, several things a
person could have noticed that are true **whenever that descriptor is
true**, and which name no particular place.

THE RULE EVERY CLAUSE HAS TO PASS. Not "is this evocative" -- that is easy
and it is how this game was broken once already, with an authored pass that
read beautifully and measured 1.03 candidates per hint. The rule is:

    Would this be true of EVERY landmark that carries the descriptor?

So `south_of_the_line` cannot say the water went down the drain backwards,
because it does not; it says Orion was standing on his head, which he is.
`inside_the_tropics` cannot say she had no shadow at noon, because that
happens on two days a year; it says the day and the night were much the same
length, which they are. `a_crown_still_on_the_coins` cannot say a queen's
head, because most of those monarchies have kings.

And the second rule, which is the one this file exists to serve: a clause
must **name nothing**. No country, no landmark, no language, no city. A
hint that identifies the room is not a hint.

Where a descriptor is institutional rather than sensory -- membership of the
Organisation of Islamic Cooperation is not a smell -- the clause reaches for
what a traveller would actually have noticed about being there, and where
there is no such thing, it says the institutional fact plainly rather than
inventing a sensory one. A dull true clause beats a vivid false one.
"""

#: Descriptor -> the things a witness could have noticed. Every entry is
#: written to be true of every landmark carrying that descriptor.
CLAUSES = {
    # --- where on the earth ------------------------------------------
    "far_from_the_equator": [
        "her shadow never got short, not even at midday",
        "the sun crossed low and went along the sky rather than over it",
        "the seasons there are the four proper ones, and they said so twice",
        "the light came in sideways all afternoon",
        "she had bought a coat, and she is not a woman who feels the cold",
        "the difference between the longest day and the shortest is most of a working day",
        "the trees had a proper autumn about them",
    ],
    "inside_the_tropics": [
        "the day and the night were much the same length",
        "the heat came straight down rather than across",
        "dusk lasted about twenty minutes and then it was night",
        "there was no season to speak of, only wet and less wet",
        "the fans were running in every room they went into",
    ],
    "south_of_the_line": [
        "Orion was standing on his head",
        "the moon was the wrong way up",
        "the sun went round the north side of the sky",
        "it was the wrong month entirely for the weather she was dressed for",
        "the year was running backwards to ours, summer where we have winter",
    ],
    "north_of_the_line": [
        "the sun kept to the south all day",
        "they found the Plough without looking for it",
        "the seasons were ours, the same months and the same weather",
    ],
    "west_of_greenwich": [
        "she was west of us and the whole day was behind",
        "the wire came in hours after it was sent",
        "they cabled at their breakfast and it reached us at our supper",
        "her morning had not started when ours was finishing",
    ],
    "long_dark_winter": [
        "in December they get about four hours of daylight, and she knew it",
        "the summer nights up there never go properly dark",
        "everyone they spoke to talked about the light as though it were money",
        "the sun did its whole business between breakfast and tea",
    ],
    "in_africa": [
        "the postmark on the envelope was African",
        "they tracked her as far as the African continent and lost her there",
        "the stamps she bought were African and they kept one",
        "her ticket had been issued at a desk in Africa",
        "the wire came through an African exchange",
        "the money that changed hands was African money",
        "the manifest had her going out on an African route and not coming back",
        "she is somewhere on the African continent, and that is as much as anyone will say",
    ],
    "in_asia": [
        "the postmark was Asian",
        "her ticket was issued somewhere in Asia",
        "the wire routed through an Asian exchange",
        "they traced her as far as the Asian continent and no further",
        "the money in her hand was Asian money",
        "the manifest put her on an Asian route",
    ],
    "in_north_america": [
        "the postmark was North American",
        "her ticket was issued somewhere in North America",
        "the wire routed through a North American exchange",
        "they followed her as far as North America and there it stops",
        "the notes in her hand were North American",
        "the manifest put her on a North American route",
        "she is on the North American continent and nobody will narrow it further",
    ],
    "in_south_america": [
        "the postmark was South American",
        "her ticket was bought at a South American counter",
        "the wire came up through South America",
        "they lost her somewhere on the South American continent",
        "the notes she paid with were South American",
        "the manifest had her on a South American routing",
    ],
    "in_oceania": [
        "the postmark came from out in Oceania",
        "her ticket was issued at one of the island desks",
        "the wire took a day to come in and it came from Oceania",
        "they lost her out among the Pacific routings",
        "the manifest had her going out over the ocean and not coming back",
    ],
    "in_eurasia": [
        "the routing was through the middle of the Eurasian landmass",
        "they traced her into the interior of Eurasia and lost her",
        "the postmark was from deep in the Eurasian continent",
    ],

    # --- what kind of country ----------------------------------------
    "traffic_keeps_left": [
        "she stepped off the kerb the wrong way and a taxi swore at her",
        "the traffic came at her from the side she was not watching",
        "they had to be told twice which way to look before crossing",
        "the driver sat on the side she keeps her handbag",
        "the roundabouts went round the wrong way and they were ill by lunchtime",
    ],
    "no_coast_in_this_country": [
        "there is no sea in that country at all, and she chose it for that",
        "the nearest port was a border crossing and two days away",
        "nothing on any menu had come out of the water that morning",
        "not one road out of it ended at a harbour",
        "the country has no navy and no reason for one",
    ],
    "a_crown_still_on_the_coins": [
        "there was a monarch's head on the change in her hand",
        "the country still keeps a crown, whatever else it has changed",
        "the stamps they were sold had a sovereign on them",
        "somebody's portrait was on the money and it was not a president's",
        "the oath the officials swear is to a person, not a document",
        "there is a palace there that is not a museum",
    ],
    "a_republic": [
        "there has been no crown there for a long time",
        "the money had no monarch on it, only a building and a date",
    ],
    "a_federation_of_states": [
        "the law changed under her when she crossed a line inside the country",
        "it is a country made of smaller countries and they do not agree",
        "their papers were checked twice by two different sorts of official",
        "the police at one end of the road answered to somebody different from the police at the other",
        "there were two sets of taxes on the same receipt",
    ],
    "a_president_who_governs": [
        "the president there does the governing himself",
        "the man on the office wall runs the country and is not decoration",
        "there was one portrait in every room and it was the same man",
        "the officials all deferred upward to a single office",
        "the news at seven was about what the president had decided that day",
        "the country has a president who signs things and means it",
    ],
    "a_prime_minister_not_a_president": [
        "the head of state was not the one who governs",
        "the person who runs that country is answerable to a chamber, daily",
        "there were two figures on the office wall and only one of them decides",
        "the government fell while they were there and the country did not notice",
        "questions get shouted at the man in charge once a week, in public",
    ],
    "flies_the_ring_of_stars": [
        "there was a circle of gold stars on the number plates",
        "the flag beside the official one had a ring of stars on it",
        "the queue at the airport had a lane she was entitled to use",
    ],
    "no_passport_needed_next_door": [
        "she crossed a border and nobody asked her for anything",
        "there was a booth at the frontier and no one was sitting in it",
        "the road out of the country had no barrier across it",
        "the frontier post had been turned into a cafe",
        "they watched her walk into another country between one field and the next",
        "there is no check on that border and there has not been for years",
    ],
    "the_old_empire_in_common": [
        "the plugs were the three-pin sort and the paperwork was familiar",
        "the courts there still argue from the same old cases we do",
        "there was a game being played on a green with a bat in it",
        "the road markings were laid out the way ours are",
        "the forms they filled in were laid out exactly like the forms at home",
        "the country still sends a team to the same games we do",
    ],
    "under_the_atlantic_treaty": [
        "there were aircraft overhead in the markings of an alliance",
    ],
    "in_the_african_union": [
        "the country sits in the African Union and the flag was up for it",
        "there was a Union pennant beside the national one on the ministry",
        "the number plates carried the continental band",
        "her papers were of a kind the Union countries accept from one another",
        "a summit of the Union was being advertised on every hoarding",
    ],
    "in_the_american_states": [
        "the country sits in the assembly of the American states",
        "the flags outside the ministry included the one for the hemisphere's assembly",
        "her visa was of the kind the American states issue one another",
        "there was a poster for a hemispheric conference in the post office",
        "the country belongs to the organisation of the Americas and the paperwork shows it",
    ],
    "in_the_arab_league": [
        "the newspapers on the stand were in the script of the League",
        "the country sits with the Arab League and the holidays follow it",
        "the League's pennant was flying beside the national flag",
        "the official forms came in two languages and one of them was Arabic",
    ],
    "in_the_islamic_conference": [
        "the working week ended on a Friday",
        "the country sits in the Islamic conference and keeps its calendar",
        "the public holidays followed a calendar that is not ours",
        "the year on the newspaper was not the year on their watch",
        "the banks shut at midday on a day our banks are busy",
        "the conference's emblem was on the ministry gate",
    ],
    "in_the_council_of_europe": [
        "there was a court in Strasbourg she could have appealed to",
    ],
    "french_is_spoken_at_the_top": [
        "the official who stamped their form did it in French",
        "the ministry letterhead was in French, whatever the street was in",
        "the paperwork was French even where the conversation was not",
        "the courts there run in French and so does the civil service",
        "the diplomatic notes go out in French",
    ],
    "one_of_the_twenty": [
        "it is one of the twenty economies that get a seat at the top table",
        "the financial pages there are read abroad, which is the whole tell",
        "the country is big enough that its interest rate is somebody else's problem",
        "there was a police cordon for a summit of the twenty largest",
    ],

    # --- what kind of place ------------------------------------------
    "a_dug_site": [
        "there were open trenches with string and numbered pegs across them",
        "the ground was cut into squares and roped off",
        "somebody was sieving dirt into a barrow, very slowly",
        "she stepped over a grid of pegs as though she knew the way through",
        "there were students on their knees with trowels and small brushes",
        "everything coming out of the ground was going into labelled trays",
        "the site hut had a plan of the dig pinned up and a kettle",
    ],
    "a_ruined_city": [
        "there were streets with no roofs left on them",
        "there were doorways standing with no walls either side",
        "the place had been a town once and nobody has lived in it since",
        "grass was growing up through what had plainly been a floor",
    ],
    "a_living_city": [
        "there were people going to work around her, thousands of them",
        "she was lost in a crowd that had somewhere else to be",
        "the trams were full and nobody looked at her twice",
        "it is a working town and she could be any of forty thousand women in it",
        "the shops were open and the traffic was bad",
        "there were schoolchildren, and offices, and a rush hour she used",
        "they lost her in it within four minutes, which tells you the size of it",
    ],
    "an_old_quarter": [
        "the streets were too narrow for a car and older than any of them",
        "the whole quarter is kept as it was, by law, down to the shutters",
        "she went into a lane that had not been straightened in four hundred years",
        "the buildings leaned over the street and met it at the top",
        "you cannot change a window there without asking somebody",
    ],
    "a_church_or_cathedral": [
        "there were bells, and they set their watch by them",
        "she went in under a cross and came out without her coat",
        "the roof inside was higher than anything outside it",
    ],
    "a_monastery": [
        "the men who live there do not talk much and keep hours by a bell",
        "there was a community living behind a wall on a rule and a timetable",
    ],
    "a_temple_or_pagoda": [
        "shoes came off at the step and hers were among them",
        "there was incense on everything, including the man who saw her",
    ],
    "a_castle": [
        "there was a keep with arrow slits and a stair going the wrong way round",
        "somebody built it to be hard to get into, and it still is",
    ],
    "walls_and_gates": [
        "the town has a wall round it and gates that still shut",
        "she came in through an arch built to be defended",
        "there were ramparts, and a walk along the top of them",
    ],
    "royal_rooms": [
        "the rooms were too big for anybody to have lived comfortably in them",
        "there was a state bed with a rope across it",
        "somebody grand had this built to be looked at, and it was",
    ],
    "graves": [
        "the whole place is somebody's grave, and a grand one",
        "there were tombs in rows and she walked between them",
        "they were standing on the dead and everybody there knew it",
    ],
    "glass_cases": [
        "there were things in cases with small cards beside them",
        "she bought a ticket and a bag was taken off her at the door",
        "a guard was watching her from the corner of a room full of exhibits",
    ],
    "a_garden": [
        "the planting was laid out by somebody with a plan and a budget",
        "there were gravel paths and a man with a rake",
        "everything green in it had been put there on purpose",
        "somebody had decided where every tree in it would stand, a long time ago",
        "it is kept, and keeping it is somebody's whole job",
    ],
    "worked_land": [
        "the fields were worked in a pattern older than the fences",
        "it is farmed ground, and the way it is farmed is the point",
        "there were terraces cut into a slope by hand, long ago",
    ],
    "a_national_park": [
        "there was a gate, a fee, and a warden who wrote their name down",
        "the whole of it is a national park and she needed a permit",
        "there were rangers, and a hut, and a book you sign going in",
        "the boundary was on the map in green and enforced",
    ],
    "a_reserve": [
        "the land is protected and there were signs saying what not to do",
        "it is kept for what lives in it rather than for anybody visiting",
        "there were more rules on the noticeboard than there were visitors",
        "they were asked to keep to the track and given a reason",
    ],
    "a_mountain": [
        "they had to look up a long way to see the top of it",
        "the weather at the top was a different day from the weather below",
        "she was carrying boots and using them",
    ],
    "deep_cut": [
        "the ground opened up and went down further than they liked",
        "there was a rim, and a very long way below it a river",
    ],
    "underground": [
        "she went in under the rock and did not come out for an hour",
        "it was cold in there in a way that had nothing to do with the season",
        "the air came up out of the ground and smelled of stone",
    ],
    "standing_water": [
        "there was water without a current, and a long way across it",
        "the far shore was a line you had to squint at",
    ],
    "water_at_its_feet": [
        "the place stands on water and the water is half of it",
        "there were boats tied up within sight of where she stood",
        "you could hear water from wherever they stood in it",
        "the whole thing is arranged around a shore",
        "there was a jetty, and things arrived at it",
    ],
    "ringed_by_water": [
        "she had to take a boat, and the boat took its time",
        "there was water on every side of it and no bridge",
        "the last part of the journey could only be done by sea",
    ],
    "at_sea_level": [
        "the sea was at the same height as the street",
        "there was salt on the windows a mile inland",
    ],
    "a_span_or_a_channel": [
        "somebody had thrown a structure across a gap that wanted crossing",
        "the water was going where engineers had told it to",
    ],
    "machine_age": [
        "the buildings were made to hold machinery and they still smell of it",
        "there was iron everywhere, and it was working iron, not ornament",
    ],
    "dry_country": [
        "there was no water for a very long way in any direction",
        "the ground had not been rained on in living memory",
        "everything they ate there had been carried in",
    ],
    "thin_air": [
        "the climb left them wheezing, and they are not an old person",
        "the kettle boiled and the tea was still not properly hot",
        "she was walking slowly and she does not walk slowly",
    ],

    # --- what happened here ------------------------------------------
    "somebody_made_this_by_hand": [
        "whatever it is, a person made it, and made it better than they had to",
        "the work in it was done by hand and it shows at arm's length",
        "you could see the tool marks if you got close, and they did",
        "it is the sort of thing people travel to look at because of the making",
        "somebody spent a life on it and the life is visible",
        "there is no machine that could have done that and there was none",
    ],
    "two_traditions_met_here": [
        "two ways of building had run into each other and the join showed",
        "the place is a seam between two traditions and neither one won",
        "the arches were of one people and the tilework of another",
        "somebody conquered somebody there and then they built together",
    ],
    "the_last_of_its_people": [
        "the people who made it are gone and this is the evidence of them",
    ],
    "a_kind_of_building_at_its_best": [
        "if you wanted to show somebody what that kind of building should be,"
        " it is this",
    ],
    "worked_the_same_way_for_centuries": [
        "they still do it there the way it has always been done",
        "the way of life and the place it is lived in are the same thing",
        "the tools in the shed were the same shape as the tools in the museum",
        "nobody there was doing anything their grandparents could not have done",
        "the pattern of the work has outlasted three governments",
    ],
    "something_famous_happened_here": [
        "something happened there that everyone has heard of",
        "the place is famous for an event rather than for the look of it",
        "half the postcards on the rack showed a date rather than a view",
        "the guide spent their whole talk on one afternoon in the place's history",
        "people go there for what happened, and they stand about looking at nothing much",
        "there was a plaque, and the plaque was the reason anyone came",
        "the name of it turns up in songs, and not because of the scenery",
    ],
    "you_cannot_stop_looking_at_it": [
        "they said they stopped walking when they saw it and could not say why",
        "it is the sort of view people go a long way to stand in front of",
        "everybody there was standing still and facing the same direction",
        "the postcards do not do it justice, and everybody says so, and they are right",
        "she stood and looked at it for a quarter of an hour, which is not like her",
        "the place is on the list for being beautiful and nothing else",
    ],
    "the_earth_showing_its_workings": [
        "the rock there is laid open and you can read it like pages",
        "the ground is doing something the ground does not usually do",
        "there are layers in the cliff and each one is an age",
        "the place is protected for the geology, which is a way of saying it is very old",
    ],
    "living_things_doing_what_they_do": [
        "the place is kept for a process rather than a thing -- a migration, a spawning, a slow return",
        "something living happens there on a scale that needs the whole valley",
        "they were told to come back in the right month to see the point of it",
        "the wardens talk about it as a timetable rather than a place",
        "it is protected for what happens there every year, not for what stands there",
    ],
    "the_last_animals_of_their_kind": [
        "there are animals there that are nowhere else, and not many of them",
        "the wardens count what lives there, and the number is small",
        "there is a species in that valley and no other valley",
        "the whole protection of it is for the sake of things that are nearly gone",
        "they were told not to leave the path because of what nests beside it",
        "the guides talk in numbers, and the numbers are two figures",
    ],

    # --- how old, how protected --------------------------------------
    "older_than_the_records": [
        "it was old before anyone there could write it down",
        "nobody knows who built it, only roughly when",
        "it predates every record of the people who now live around it",
    ],
    "standing_before_the_maps": [
        "it was standing before any of our maps had that coast right",
        "it is medieval, and it has been there longer than the country has",
        "the stonework is of a period when nobody signed their work",
        "it has outlasted the language its builders wrote in",
    ],
    "within_living_memory": [
        "it is new enough that somebody alive watched it go up",
        "the whole thing is younger than the oldest person they spoke to",
        "there are people in the town who remember the building of it",
        "it is modern, whatever the postcards imply",
        "the photographs of its construction are photographs, not engravings",
    ],
    "guarded_since_before_the_tourists": [
        "it has been on a protected list since before any of this was fashionable",
        "the preservation order on it is older than the coach parties",
        "the file goes back further than anyone still working there",
        "it was being looked after before most countries had a word for it",
        "the oldest sign on the gate is enamel and half illegible",
        "protection came early, which is why there is anything left to protect",
    ],
    "protected_in_the_eighties_or_nineties": [
        "it went on the protected list at about the time they were born",
        "the plaque is of that period when everything was set in a particular sans-serif",
        "the preservation order is about forty years old and the paperwork is typed",
        "the file on it starts in the eighties and the earlier pages are missing",
        "there is a commemorative photograph on the office wall and the haircuts date it",
        "the fence round it has been there long enough to rust properly",
        "the listing predates the internet and the office still keeps it on cards",
        "the oldest warden there was hired when it was listed and is nearly retired",
        "the guidebook their father used already calls it protected",
    ],
    "protected_around_the_millennium": [
        "the brass plaque by the gate had a date on it from about a quarter-century back",
        "the listing paperwork they were shown was signed the year the century turned",
        "the preservation notice was younger than the man standing under it",
        "the guidebooks printed before the millennium do not mention it being protected",
        "the fence round it went up at about the time everyone was worrying about computers",
        "the protection order on it dates from around the turn of the century",
        "the warden's post there was created about twenty-five years ago and they are only the second to hold it",
        "there is a photograph in the office of the ceremony, and the clothes in it are of that decade",
        "the signage was of a style nobody has ordered since the early two thousands",
        "it has been officially looked after for about a generation, no longer",
        "the oldest permit in the file was issued a little before they were born",
    ],
    "protected_only_recently": [
        "the signs at the entrance still looked new and the paint had not run",
        "it was listed recently enough that the old guidebooks call it nothing in particular",
        "the protection on it is younger than the argument about whether it deserved it",
        "the warden had been in post since it was listed, and that was not long",
        "the plaque was so new they could still read every letter of it",
        "the fence was recent, the posts were not yet weathered, and it was all official",
        "half the people who live near it can remember when it was not protected at all",
        "the paperwork protecting it is more recent than her passport",
        "there was scaffolding up and a notice explaining a restoration that had only just been funded",
        "the listing is new enough that the locals still argue about the parking",
    ],
    "thick_with_visitors": [
        "she went through a turnstile behind a coach party and was gone",
        "there were more people there than anywhere she has been this month",
        "the queue was an hour long and she stood in all of it",
    ],
}
