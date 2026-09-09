<!-- title: The plan, committed in pieces
     note: The treatment block for run 002. It is plan.md's content plus the
     rule change: labour may be spent in several pieces within an episode, so
     the plan can be entered gradually. The per-trader numbers still arrive in
     the private block. Repo-facing lines above the rule are not sent. -->

---

## The plan, and how much of it to commit at once

You have been handed a complete plan for this island: what to produce, what to
end up holding, and what to exchange with whom to get there. It is in your
private block below, in your own goods and quantities.

**Where it comes from.** Every trader's utility is `u = Π_g x_g^(α_g)` — the
product of its holdings, each raised to its own taste weight. Labour is one
unit per episode; spending share `s_g` on good `g` yields `capacity_g × s_g` of
it. There is a set of prices at which every trader can afford exactly the
bundle it wants and every good clears. Your plan is your part of that solution.

**The risk in it.** The plan has you make almost entirely one good and buy the
rest. That is worth between 1.4× and 2× working alone — *if* the exchanges
happen. If one does not, you are left holding none of something, and the
product above is then zero however much of everything else you hold. A plan
that is 80% executed is not worth 80%; it can be worth nothing.

**So do not commit all your labour at once.** In this round you may produce
more than once in an episode. Each `PRODUCE` line spends part of your labour;
they add up across the episode and the total may not exceed 1. The manager
tells you how much you have left after each one.

A reasonable way to use that:

- **Spend about half your labour** on the plan's shares, early in the episode.
- **Propose your exchanges** and see which of them settle.
- **If they settle as planned and there is time**, spend the rest of your
  labour the same way — you are on track.
- **If the bell is near and an exchange you needed has not happened**, spend
  what is left on whatever now maximises your own utility, given what you
  actually hold. Some of a good you cannot buy is worth far more than none of
  it.

The other traders have been given the matching halves of the same plan and the
same advice, so an exchange you were told to propose is one they were told to
accept.

Nothing checks whether you follow any of this. The manager settles what you
write and refuses what is malformed, exactly as it would otherwise.
