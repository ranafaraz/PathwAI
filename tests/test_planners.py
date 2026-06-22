"""Planner behaviour: completeness, optimality, and the core comparison."""

from __future__ import annotations

import pytest

from pathwai.config import Settings
from pathwai.domains import DOMAINS, make_domain
from pathwai.pipeline import solve_instance
from pathwai.planners import PLANNERS, get_planner


def _cfg(domain, backend="stub"):
    cfg = Settings.from_env()
    cfg.domain = domain
    cfg.proposer_backend = backend
    return cfg


@pytest.mark.parametrize("name", DOMAINS)
def test_optimal_planner_is_optimal(name):
    domain = make_domain(name, 4)
    res = solve_instance(domain, _cfg(name), "optimal")
    assert res.solved
    assert res.optimality_ratio == pytest.approx(1.0)


@pytest.mark.parametrize("name", DOMAINS)
def test_llm_search_solves_and_is_near_optimal(name):
    # Across several seeds the search+verifier agent must always solve and stay
    # close to optimal -- this is the product claim.
    for seed in range(10):
        domain = make_domain(name, seed)
        res = solve_instance(domain, _cfg(name), "llm_search")
        assert res.solved, f"{name} seed {seed} unsolved"
        assert res.optimality_ratio <= 1.30
        assert res.invalid_proposals == 0  # a correct search returns a clean plan


def test_search_beats_open_loop_on_aggregate():
    # The whole point: search+verifier rescues the same noisy proposer the
    # open-loop agent fails with.
    llm_solved = ls_solved = total = 0
    for name in DOMAINS:
        for seed in range(12):
            domain = make_domain(name, seed)
            total += 1
            if solve_instance(domain, _cfg(name), "llm").solved:
                llm_solved += 1
            if solve_instance(domain, _cfg(name), "llm_search").solved:
                ls_solved += 1
    assert ls_solved == total
    assert llm_solved < ls_solved


def test_guidance_reduces_expansions_vs_uniform():
    domain = make_domain("delivery", 5)
    uni = solve_instance(domain, _cfg("delivery"), "uniform")
    lls = solve_instance(domain, _cfg("delivery"), "llm_search")
    assert lls.expansions < uni.expansions


def test_unknown_planner_raises():
    with pytest.raises(ValueError):
        get_planner(_cfg("gridworld"), "bogus")


def test_all_planner_names_build():
    cfg = _cfg("gridworld")
    for name in PLANNERS:
        assert get_planner(cfg, name) is not None
