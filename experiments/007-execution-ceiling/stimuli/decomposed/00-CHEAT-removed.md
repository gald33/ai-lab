<!-- title: What comes out — the cheat
     note: NOT a stimulus. This is the part of run 001's winning treatment that
     no legitimate experiment may hand over, listed so the removal is explicit
     and auditable rather than implied. -->

# What must come out of the winning block

**The test.** Anything a trader could not have obtained from its own private
block, or earned by talking to the others. If it required the manager's global
view or another trader's capacities and tastes, it is a cheat.

## Removed from `plan.md`

| what | why it is a cheat |
|---|---|
| *"There is a set of prices at which every trader can afford exactly the bundle it wants and every good clears. Your plan is your part of that solution."* | The equilibrium is computed from all four traders' private data. Naming it as an existing solved object hands over the answer's existence. |
| *"On this island that is worth between 1.4× and 2× your solo result"* | The size of the prize is a property of the whole island, unknowable to one trader. |
| *"The other traders have been given the matching halves of the same plan, so an exchange you were told to propose is one they were told to accept."* | Guarantees coordination exogenously. It replaces the thing under study — reaching agreement — with an assurance. |
| *"Produce the shares your plan names… Propose the exchanges your plan names, to the traders it names, in the quantities it names."* | Instructions to execute numbers the trader did not derive. |

## Removed from the private block entirely

Everything `plan.py` computes: the labour shares, the end holdings, the named
counterparties and quantities, the supporting prices, and the multiple of
autarky. **All of it comes from `walras()` over the full island.**

A trader keeps only what it always had: its own capacities, its own tastes, its
own holdings.

## What this costs, stated plainly

Run 001's result — production compliance 214/214, and four replicates all above
the control — was obtained **with** these. Removing them is expected to cost
most of it. That is the point: the ladder measures how much.
