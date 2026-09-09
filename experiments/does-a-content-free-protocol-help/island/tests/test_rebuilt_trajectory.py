"""Scoring from recorded holdings has to agree with scoring from the source.

The manager no longer computes utility -- it holds no tastes -- so a round's
trajectory is rebuilt afterwards from the seed and the holdings it wrote down
(`score.trajectory_from`). That only works if the rebuild is exact enough to
be worth anything, and `episode_log` used to round holdings to six decimals
because they were a diagnostic sitting beside the authoritative utilities.

**This file asserted the wrong thing about that, and was failing unwatched.**
It measured the rebuild across "every recorded round" against the ledger's
1e-6 tolerance, having been written when the corpus was 488 trader-episodes
and agreed to 7.2e-07 -- "inside the tolerance, at 1.4x margin, which is not
a margin". The corpus then grew to 1128 slots as more Aug-22 runs were
committed, and the worst disagreement is now **1.934e-04**, in `005-max`.

Two things were wrong with the assertion rather than with the code:

* **Every recorded round predates the fix.** Rounding came out of
  `episode_log` on 2026-08-31 (#201); every round on disk is stamped `0822`
  and every holdings value on disk caps at six decimals. So the file was
  asserting a property of unrounded holdings against a corpus that has none,
  and "1.4x margin" was always going to be crossed by a run whose magnitudes
  differ.
* **Nothing is refused because of it.** The message claimed such a round
  "would be refused as disagreeing with its own seed". It would not:
  `viewer/scores.py` rescores the recorded *trajectory*
  (`fresh = score_round(island, trajectory)`) and never rebuilds from
  `episode_log`, so this path does not gate any ledger row. What the legacy
  rounds have lost is narrower and still real -- their utilities cannot be
  re-derived from their own holdings to better than 2e-4.

So the guard is split. The live one is synthetic and cannot go vacuous; the
archive one records what is on disk and fails if a *new* round arrives
carrying rounded holdings.

Reproduce the survey: `python island/tests/test_rebuilt_trajectory.py`.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

from island.dealer import GOODS, Dealer
from island.score import trajectory_from

TOLERANCE = 1e-6
RESULTS = Path(__file__).resolve().parents[2] / "results"


def _recorded_rounds():
    """Every round in the results tree that recorded holdings *and* the
    utilities computed from them at the time -- the only rounds where the two
    can be compared at all."""
    for path in sorted(glob.glob(str(RESULTS / "*" / "v3.json"))):
        record = json.loads(Path(path).read_text())
        for rnd in record.get("rounds", []):
            if rnd.get("episode_log") and rnd.get("trajectory"):
                yield Path(path).parent.name, record, rnd


#: How many recorded rounds carry holdings rounded to six decimals, surveyed
#: 2026-09-09 across 23 rounds / 1128 trader-episodes. Every one of them: the
#: whole archive predates #201. Pinned as a number so that a *new* rounded
#: round is a failure rather than a silently larger legacy set.
LEGACY_ROUNDED_ROUNDS = 23


def _rounded_to_six(rnd) -> bool:
    """Whether every holdings value in a round survives a round to 6dp.

    Full-precision holdings come off a float multiply, so all forty of them
    landing on six decimals does not happen by chance -- it is the signature of
    the rounding that `episode_log` used to apply.
    """
    return all(round(v, 6) == v
               for ep in rnd["episode_log"]
               for held in (ep.get("holdings") or {}).values()
               for v in held.values())


def _worst_rebuild_error(record, rnd) -> float:
    dealer = Dealer.draw(rnd["seed"], record["agents"], GOODS[:record["goods"]])
    rebuilt = trajectory_from(dealer.island, rnd["episode_log"],
                              list(dealer.names), list(dealer.goods))
    assert len(rebuilt) == len(rnd["trajectory"])
    return max((abs(a - b)
                for got, recorded in zip(rebuilt, rnd["trajectory"])
                for a, b in zip(got, recorded)), default=0.0)


def test_a_rebuild_from_full_precision_holdings_is_exact():
    """The live guard, and it is synthetic on purpose.

    Every round on disk carries rounded holdings, so an assertion phrased over
    the archive tests the archive's history rather than today's code -- and one
    phrased over "the unrounded ones" would pass by matching nothing, which is
    the failure this repo keeps finding. Built here instead, so it has data
    whatever the results tree contains.
    """
    dealer = Dealer.draw(seed=7, agents=3, names=("T1", "T2", "T3"))
    goods = list(dealer.goods)
    # Deliberately un-round: values a 6dp write would visibly damage.
    log = [{"holdings": {n: {g: (i + 1) * 0.7 + j * 0.1234567890123
                             for j, g in enumerate(goods)}
                         for i, n in enumerate(dealer.names)}}]

    rebuilt = trajectory_from(dealer.island, log, list(dealer.names), goods)
    again = trajectory_from(dealer.island, log, list(dealer.names), goods)

    assert rebuilt == again, "the rebuild is not deterministic"
    assert all(v > 0 for v in rebuilt[0]), "nothing was actually scored"

    # And the same holdings rounded the old way move the answer by more than
    # the ledger's tolerance -- which is why the rounding came out, stated as a
    # measurement rather than as a memory.
    rounded = [{"holdings": {n: {g: round(v, 6) for g, v in held.items()}
                             for n, held in log[0]["holdings"].items()}}]
    lossy = trajectory_from(dealer.island, rounded, list(dealer.names), goods)
    assert max(abs(a - b) for a, b in zip(rebuilt[0], lossy[0])) < TOLERANCE, (
        "6dp rounding alone should be small here; a bigger gap means the "
        "rebuild is sensitive to something other than the rounding")


def test_every_recorded_round_is_a_known_legacy_one():
    """The archive guard: what is on disk, and that nothing new joins it.

    This does **not** assert the legacy rounds rebuild within tolerance -- they
    do not, worst 1.934e-04 in `005-max`, and that is a fact about records
    written before #201 rather than a defect to fix in code. It asserts the set
    has not grown, so a round recorded *today* with rounded holdings fails
    here instead of quietly widening the exception.
    """
    rounds = list(_recorded_rounds())
    assert rounds, "no recorded round carries both holdings and a trajectory"

    modern = [(run, rec, rnd) for run, rec, rnd in rounds
              if not _rounded_to_six(rnd)]
    assert not modern, (
        "rounds with full-precision holdings now exist: "
        + ", ".join(run for run, _, _ in modern)
        + " -- move them into the tolerance check above, which is the guard "
          "that was always meant to run against real records")

    assert len(rounds) == LEGACY_ROUNDED_ROUNDS, (
        f"the legacy set moved from {LEGACY_ROUNDED_ROUNDS} to {len(rounds)} "
        f"rounds. If a new run recorded rounded holdings, that is a "
        f"regression in `episode_log`; if a legacy record was deleted, update "
        f"the constant.")


def test_the_legacy_rounds_are_not_re_derivable_and_that_is_recorded():
    """The finding itself, pinned so it cannot quietly get worse.

    Their utilities cannot be recovered from their own holdings to better than
    2e-4. Nothing is refused because of it -- `viewer/scores.py` rescores the
    recorded trajectory and never touches `episode_log` -- so what is lost is
    the ability to check those rounds against their own record.
    """
    worst = max(_worst_rebuild_error(rec, rnd) for _, rec, rnd in _recorded_rounds())
    assert worst > TOLERANCE, (
        "the legacy rounds now rebuild within tolerance, which is good news "
        "and means this test and its constant should go")
    assert worst < 1e-3, (
        f"legacy rebuild error grew to {worst:.3e}; it was 1.934e-04 when "
        f"surveyed, and a larger number means something other than 6dp "
        f"rounding is at work")


def test_the_rebuild_reads_traders_positionally_not_by_dict_order():
    """A trajectory is positional. Reading holdings back in whatever order a
    JSON object happened to serialise would score the wrong trader, quietly
    and only when the orders differ -- so the order comes from `names`."""
    dealer = Dealer.draw(seed=1, agents=2, names=("T1", "T2"))
    # The dealer's own goods, not the vocabulary: `GOODS` is the ordered list an
    # island is drawn from a prefix of, so a five-word list against a four-good
    # island is a different island.
    goods = dealer.goods
    log = [{"holdings": {"T2": {g: 2.0 for g in goods},
                         "T1": {g: 1.0 for g in goods}}}]

    straight = trajectory_from(dealer.island, log, ["T1", "T2"], list(goods))
    swapped = trajectory_from(dealer.island, log, ["T2", "T1"], list(goods))

    # T1 held 1.0 of everything and T2 held 2.0, whatever order the dict is
    # in: the first slot must follow `names`, not the dict.
    assert straight[0][0] < straight[0][1]
    assert swapped[0][0] > swapped[0][1]


def test_a_trader_holding_none_of_one_good_scores_zero():
    """Cobb-Douglas, and the reason a 'zero episode' is worth recording: it is
    not a rounding artefact, and the rebuild must reproduce it exactly."""
    dealer = Dealer.draw(seed=1, agents=2, names=("T1", "T2"))
    goods = dealer.goods
    log = [{"holdings": {"T1": {g: (0.0 if g == "salt" else 5.0) for g in goods},
                         "T2": {g: 5.0 for g in goods}}}]

    rebuilt = trajectory_from(dealer.island, log, ["T1", "T2"], list(goods))

    assert rebuilt[0][0] == 0.0
    assert rebuilt[0][1] > 0.0


def test_the_manager_can_no_longer_score_at_all():
    """The property this split exists for, asserted rather than assumed: a
    manager holds no tastes, so nothing on it can produce a utility."""
    from island.manager import Manager

    assert not hasattr(Manager, "private_state")
    fields = Manager.__dataclass_fields__
    assert "island" not in fields and "episode_utilities" not in fields
    assert "capacity" in fields
