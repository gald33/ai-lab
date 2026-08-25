"""Scoring from recorded holdings has to agree with scoring from the source.

The manager no longer computes utility -- it holds no tastes -- so a round's
trajectory is rebuilt afterwards from the seed and the holdings it wrote down
(`score.trajectory_from`). That only works if the rebuild is exact enough for
the ledger, which refuses a row whose recorded `eff_round` disagrees with what
its seed produces by more than `viewer/scores.py:TOLERANCE` (1e-6).

It is exact enough now and it was *nearly* not. `episode_log` used to round
holdings to six decimals, because they were a diagnostic sitting beside the
authoritative utilities. Measured across every recorded round that carries
both -- 488 trader-episodes -- rebuilding from those six-decimal holdings
agreed to 7.2e-07: inside the tolerance, at 1.4x margin, which is not a
margin. Holdings are the record now and are kept unrounded; this is the guard
on that staying true.
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


def test_rebuilding_from_recorded_holdings_matches_what_was_scored():
    """The whole basis of taking scoring out of the manager, against every
    round on disk that can check it."""
    worst, compared, rounds = 0.0, 0, 0
    for _, record, rnd in _recorded_rounds():
        rounds += 1
        dealer = Dealer.draw(rnd["seed"], record["agents"],
                             GOODS[:record["goods"]])
        rebuilt = trajectory_from(dealer.island, rnd["episode_log"],
                                  list(dealer.names), list(dealer.goods))
        assert len(rebuilt) == len(rnd["trajectory"])
        for got, recorded in zip(rebuilt, rnd["trajectory"]):
            for a, b in zip(got, recorded):
                worst = max(worst, abs(a - b))
                compared += 1

    assert rounds, "no recorded round carries both holdings and a trajectory"
    assert compared >= 488, f"expected the known corpus, compared {compared}"
    assert worst < TOLERANCE, (
        f"rebuilt utilities differ from the recorded ones by {worst:.3e}, "
        f"over the ledger's {TOLERANCE:.0e} tolerance -- a round rebuilt this "
        f"way would be refused as disagreeing with its own seed")


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
