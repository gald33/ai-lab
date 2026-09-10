"""Gates on the rung-0 runner's arithmetic and on its two refusals.

The game-playing half needs a hub and a clock and is exercised by running it;
what is tested here is everything that decides *what number comes out*, because
that number becomes this experiment's thresholds and a wrong one is not
visible downstream -- it just makes every later comparison pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "experiment"))

import noise  # noqa: E402


def game(**over):
    base = {"zero_episode_share": 0.25, "capture": 0.5,
            "above_autarky_share": 0.5, "eff_round": 0.6,
            "seed": 1, "settled": 4}
    return {**base, **over}


# --- the endpoints, off a ledger row ------------------------------------

def test_the_primary_is_a_share_of_trader_episodes_not_of_traders():
    """2 traders x 4 episodes = 8 slots; 3 zeros is 3/8, not 3/2."""
    row = {"eff_round": 0.5, "autarky_floor": 0.0,
           "zero_episodes": {"T1": 1, "T2": 2}, "ratios": {}}
    assert noise.endpoints_from(row, 4)["zero_episode_share"] == 3 / 8


def test_above_autarky_counts_only_ratios_strictly_above_one():
    row = {"eff_round": 0.5, "autarky_floor": 0.0, "zero_episodes": {},
           "ratios": {"T1": 1.4, "T2": 1.0, "T3": 0.2, "T4": None}}
    assert noise.endpoints_from(row, 4)["above_autarky_share"] == 1 / 4


def test_a_row_with_no_traders_yields_none_rather_than_dividing_by_zero():
    row = {"eff_round": None, "autarky_floor": None,
           "zero_episodes": {}, "ratios": {}}
    got = noise.endpoints_from(row, 4)
    assert got["zero_episode_share"] is None
    assert got["above_autarky_share"] is None


# --- the summary --------------------------------------------------------

def test_between_replicate_sd_is_the_sd_of_replicate_means():
    """Not the sd of every game pooled -- those are different numbers, and
    conflating them is how a threshold gets chosen against the wrong one."""
    reps = [[game(zero_episode_share=0.0), game(zero_episode_share=0.4)],
            [game(zero_episode_share=0.2), game(zero_episode_share=0.2)]]
    summary = noise.between_replicate_sd(reps)["zero_episode_share"]
    assert summary["replicate_means"] == [0.2, 0.2]
    assert summary["between_replicate_sd"] == 0.0
    # pooled, the same games do move
    assert summary["per_game_sd"] > 0
    assert summary["games"] == 4


def test_a_missing_endpoint_shrinks_its_own_denominator_only():
    reps = [[game(), game(capture=None)]]
    summary = noise.between_replicate_sd(reps)
    assert summary["capture"]["games"] == 1
    assert summary["zero_episode_share"]["games"] == 2


# --- the two refusals ---------------------------------------------------

def test_a_bounded_endpoint_on_a_bound_in_every_game_is_pinned():
    """Found by running the real thing at 15s: every game settled nothing,
    every share sat at a bound, and the reported sd was 0.0000 -- which reads
    as the most precise instrument this lab has ever had."""
    reps = [[game(zero_episode_share=1.0, above_autarky_share=0.0)],
            [game(zero_episode_share=1.0, above_autarky_share=0.0)]]
    assert noise.pinned(reps) == ["above_autarky_share", "zero_episode_share"]


def test_an_endpoint_that_moves_off_a_bound_is_not_pinned():
    reps = [[game(zero_episode_share=1.0, above_autarky_share=0.5)],
            [game(zero_episode_share=0.25, above_autarky_share=0.5)]]
    assert "zero_episode_share" not in noise.pinned(reps)


def test_an_unbounded_endpoint_is_never_called_pinned():
    """`capture` and `eff_round` have no bound to sit on, so the check must
    not be applied to them -- a constant capture is a different problem."""
    reps = [[game(capture=0.0, eff_round=0.0)]] * 2
    assert "capture" not in noise.pinned(reps)
    assert "eff_round" not in noise.pinned(reps)


def test_games_that_settled_nothing_are_counted_not_dropped():
    reps = [[game(settled=0), game(settled=3)], [game(settled=0)]]
    assert noise.dead(reps) == 2


def test_a_game_missing_its_settled_count_reads_as_dead_rather_than_alive():
    """Absent must not be optimistic: the whole class of defect this island
    keeps finding is the system reporting success while doing nothing."""
    assert noise.dead([[{"settled": None}]]) == 1


def test_replicates_that_returned_the_same_numbers_are_named_as_such():
    """The other road to a meaningless 0.0000, and the one NPCs actually take:
    heuristics are deterministic given their seed, so two replicates come back
    byte-identical and the sd is 0 because nothing varied."""
    reps = [[game()], [game()]]
    assert noise.identical(reps) is True


def test_replicates_that_differ_anywhere_are_not_identical():
    reps = [[game()], [game(eff_round=0.61)]]
    assert noise.identical(reps) is False


def test_one_replicate_cannot_be_identical_to_anything():
    assert noise.identical([[game()]]) is False


# --- the pool, and the summary that had never run -----------------------

def _fake_game(job):
    """Stands in for a whole game. Deterministic in the seed, like an NPC one."""
    return {"replicate": job.replicate, "seed": job.seed, "settled": 4,
            "zero_episode_share": 0.25 + 0.01 * job.seed, "capture": 0.5,
            "above_autarky_share": 0.5, "eff_round": 0.6}


def test_the_plan_is_seed_major_so_replicates_of_one_seed_run_together():
    """The order is part of the measurement -- see `plan()`. With workers equal
    to the replicate count, seed-major puts a seed's replicates in flight at
    once, so they contend for the machine identically."""
    jobs = noise.plan(3, [7, 8], noise.Cell(), vary_npc_seed=False)
    assert [(j.seed, j.replicate) for j in jobs] == [
        (7, 0), (7, 1), (7, 2), (8, 0), (8, 1), (8, 2)]


def test_varying_the_policy_seed_changes_it_per_replicate_and_not_per_seed():
    same = noise.plan(2, [1], noise.Cell(), vary_npc_seed=False)
    varied = noise.plan(2, [1], noise.Cell(), vary_npc_seed=True)
    assert len({j.npc_seed for j in same}) == 1
    assert len({j.npc_seed for j in varied}) == 2


def test_results_are_keyed_back_to_their_job_not_kept_in_finish_order():
    """A summary whose value depended on which game finished first would be the
    `overhead` render check's disease: a verdict riding on something the check
    does not control."""
    import concurrent.futures as cf
    jobs = noise.plan(2, [3, 1, 2], noise.Cell(), vary_npc_seed=False)
    results, failures = noise.play_all(
        jobs, workers=4, run=_fake_game, pool=cf.ThreadPoolExecutor,
        log=lambda *a, **k: None)
    assert not failures
    grouped = noise.by_replicate(results, 2)
    assert [[g["seed"] for g in games] for games in grouped] == [[1, 2, 3]] * 2


def test_a_game_that_raises_is_counted_as_a_harness_failure_not_dropped():
    def explode(job):
        if job.seed == 2:
            raise RuntimeError("the lobby settled without posting an invite")
        return _fake_game(job)

    jobs = noise.plan(1, [1, 2, 3], noise.Cell(), vary_npc_seed=False)
    results, failures = noise.play_all(jobs, workers=1, run=explode,
                                       log=lambda *a, **k: None)
    assert len(results) == 2 and len(failures) == 1
    assert failures[0]["seed"] == 2


def test_the_pool_path_really_crosses_a_process_boundary():
    """`workers > 1` is a *process* pool, and the thing that can break at that
    boundary is pickling. Asserted with a real one rather than inferred from
    the thread-pool test above, which shares an interpreter and would pass
    whether or not a `Job` could be sent anywhere."""
    import os
    import pickle
    from concurrent.futures import ProcessPoolExecutor

    job = noise.plan(1, [5], noise.Cell(traders=2), vary_npc_seed=False)[0]
    assert pickle.loads(pickle.dumps(job)) == job

    with ProcessPoolExecutor(max_workers=2) as pool:
        pids = set(pool.map(_elsewhere, [1, 2, 3, 4]))
    assert pids and os.getpid() not in pids


def _elsewhere(_):
    import os
    return os.getpid()


def test_main_runs_to_the_end_and_writes_its_record(tmp_path, monkeypatch,
                                                    capsys):
    """The regression for the bug that made every one of run 001's guards dead.

    `main()` bound a local named `identical`, which shadowed the module
    function of that name, so the line that calls it raised UnboundLocalError --
    every time, from the moment the guard was added. Everything above tested the
    functions; nothing ran `main()`, so a guard added *because* a run had misled
    somebody had itself never executed once.
    """
    monkeypatch.setattr(noise, "run_job", _fake_game)
    out = tmp_path / "record.json"
    code = noise.main(["--replicates", "3", "--games", "4", "--workers", "1",
                       "--json", str(out)])
    assert code == 0
    printed = capsys.readouterr().out
    assert "every complete replicate played the same seeds: True" in printed
    assert "EVERY REPLICATE RETURNED THE SAME NUMBERS." in printed

    import json
    record = json.loads(out.read_text())
    assert record["attempted"] == 12 and record["played"] == 12
    assert record["every_replicate_identical"] is True
    assert record["seeds_identical_across_replicates"] is True
    assert record["workers"] == 1
    assert record["summary"]["zero_episode_share"]["between_replicate_sd"] == 0.0


def test_main_refuses_a_pinned_run_with_a_non_zero_exit(tmp_path, monkeypatch):
    """`pinned()` is the run-001 guard proper. It has now been seen to fire
    through `main()`, which is the only path that ever calls it."""
    def floored(job):
        return {**_fake_game(job), "zero_episode_share": 1.0,
                "above_autarky_share": 0.0}

    monkeypatch.setattr(noise, "run_job", floored)
    assert noise.main(["--replicates", "2", "--games", "2",
                       "--workers", "1"]) == 1


def test_a_pinned_run_says_whether_it_is_the_clock_or_the_seats(monkeypatch,
                                                                capsys):
    """Same 0.0000, same refusal, two different faults and two remedies.

    Run 001 pinned because no NPC finished a round trip in 15s -- the clock.
    Run 002 pinned `above_autarky_share` at zero with every game settling --
    the seats, which no longer episode length can fix. The message told the
    reader to lengthen the episode in both cases.
    """
    def dead_game(job):
        return {**_fake_game(job), "settled": 0, "zero_episode_share": 1.0,
                "above_autarky_share": 0.0}

    monkeypatch.setattr(noise, "run_job", dead_game)
    assert noise.main(["--replicates", "2", "--games", "2",
                       "--workers", "1"]) == 1
    assert "That is the clock" in capsys.readouterr().out

    def settled_but_pinned(job):
        return {**_fake_game(job), "settled": 6, "above_autarky_share": 0.0}

    monkeypatch.setattr(noise, "run_job", settled_but_pinned)
    assert noise.main(["--replicates", "2", "--games", "2",
                       "--workers", "1"]) == 1
    printed = capsys.readouterr().out
    assert "seat population: these seats never" in printed
    assert "That is the clock" not in printed


# --- the collision concurrency found ------------------------------------

def test_two_games_running_at_once_do_not_share_a_signing_socket(tmp_path):
    """The defect the first concurrent rung-0 run raised, asserted directly.

    `signing.socket_path()` hashes the **agent id and nothing else**, and every
    game here seats `t1`..`t4`. Eight games at once were binding four sockets
    between them: one raised `no AF_UNIX signer available on this platform`,
    and the ones that did not raise were free to reach a neighbour's signer and
    sign as somebody the lobby never witnessed.
    """
    import os
    from switchboard import signing

    with noise.signer_namespace(tmp_path / "one"):
        first = signing.socket_path("t1")
    with noise.signer_namespace(tmp_path / "two"):
        second = signing.socket_path("t1")

    assert first != second
    assert (tmp_path / "one") in first.parents
    assert (tmp_path / "two") in second.parents

    # And without the namespace they are the same path, which is the bug.
    os.environ.pop("XDG_RUNTIME_DIR", None)
    assert signing.socket_path("t1") == signing.socket_path("t1")


def test_the_namespace_is_put_back_however_it_leaves(tmp_path, monkeypatch):
    """A game that raises must not leave the next game pointed at its own
    deleted temporary directory."""
    import os

    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    try:
        with noise.signer_namespace(tmp_path):
            raise RuntimeError("the lobby settled without posting an invite")
    except RuntimeError:
        pass
    assert os.environ["XDG_RUNTIME_DIR"] == "/run/user/1000"

    monkeypatch.delenv("XDG_RUNTIME_DIR")
    with noise.signer_namespace(tmp_path):
        assert os.environ["XDG_RUNTIME_DIR"] == str(tmp_path)
    assert "XDG_RUNTIME_DIR" not in os.environ
