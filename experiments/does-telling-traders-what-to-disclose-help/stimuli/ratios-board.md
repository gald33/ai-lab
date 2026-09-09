<!-- title: Ratio disclosure, with a place and a time to put it
     note: The treatment block for run 002. It is `ratios.md` plus a protocol:
     which key to write, and when. Not frozen until the v2 pre-registration
     says so. Repo-facing lines above the rule are not sent to agents. -->

---

## Two ratios, and where they go

Two numbers describe what you bring to an exchange, and both are ratios —
comparisons between goods, not amounts of anything.

The first is what a good costs you. If you can make twice as much salt per unit
of labour as iron, then salt costs you half an iron: to get one more salt you
give up half an iron of production. This ratio comes from your capacities and
it does not change, in this episode or any later one.

The second is what a good is worth to you right now. As you accumulate a good
each further unit of it matters less, so this ratio moves as your holdings
move — and it moves the moment an exchange settles.

When these two ratios are equal you are holding the best bundle you can make
alone, and no further production improves it. They come apart when you trade,
and the gap is where an exchange is worth making: if a good costs you less than
it costs someone else, you are the one who should be making it, and they should
be getting it from you.

You cannot see anyone else's ratios and nobody can see yours. Saying them is
the only way they become common knowledge, and a ratio gives away less than a
capacity does — it says how goods trade off for you without saying how much of
anything you can make.

**So say them, in a place everyone can look.** You have `board_set`,
`board_get` and `board_list`. They are a shared keyed store: what you write to
a key stays there until you overwrite it, and anyone can read it whenever they
like without you having to repeat yourself.

- **Once, in your first episode:** write your cost ratios to the key
  `cost/<your name>` — for example `cost/T1`. They never change, so writing
  them again is wasted effort.
- **Every episode, after you have produced:** write what your goods are worth
  to you now, given what you actually hold, to the key `worth/<your name>`.
  This one does change, because your holdings changed.

Read the others with `board_list` and `board_get` before you propose. Someone
whose cost ratio for a good is higher than yours is someone who should be
buying it from you rather than making it.

Choose your own units and your own wording; nothing checks the format. What
matters is that the numbers are there, that the cost key is written once, and
that the worth key reflects what you are holding now.
