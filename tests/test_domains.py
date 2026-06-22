"""Domain correctness, including the admissibility of every heuristic.

Admissibility (heuristic never overestimates the true cost-to-go) is the property
that makes the A* baseline a valid optimum. We check it along each optimal plan:
at every state, h(s) must not exceed the remaining optimal cost.
"""

from __future__ import annotations

import pytest

from pathwai.domains import DOMAINS, make_domain
from pathwai.planners.classical import OptimalPlanner

SEEDS = range(8)


def _replay(domain, plan):
    state = domain.initial_state()
    for action in plan:
        assert action in domain.actions(state), f"illegal action {action}"
        state = domain.result(state, action)
    return state


@pytest.mark.parametrize("name", DOMAINS)
@pytest.mark.parametrize("seed", SEEDS)
def test_instances_are_solvable_and_plans_valid(name, seed):
    domain = make_domain(name, seed)
    res = OptimalPlanner().plan(domain)
    assert res.solved
    final = _replay(domain, res.plan)
    assert domain.goal_test(final)
    # Plan cost equals number of unit-cost steps.
    assert res.cost == pytest.approx(len(res.plan))


@pytest.mark.parametrize("name", DOMAINS)
@pytest.mark.parametrize("seed", SEEDS)
def test_heuristic_is_admissible_along_optimal_path(name, seed):
    domain = make_domain(name, seed)
    res = OptimalPlanner().plan(domain)
    state = domain.initial_state()
    g = 0.0
    for action in res.plan:
        remaining = res.cost - g
        assert domain.heuristic(state) <= remaining + 1e-9, "heuristic overestimates"
        g += domain.step_cost(state, action)
        state = domain.result(state, action)
    # Heuristic is zero exactly at the goal.
    assert domain.heuristic(state) == 0.0


@pytest.mark.parametrize("name", DOMAINS)
def test_actions_are_all_applicable(name):
    domain = make_domain(name, 3)
    state = domain.initial_state()
    for action in domain.actions(state):
        # result() must not raise for any advertised action.
        domain.result(state, action)


def test_unknown_domain_raises():
    with pytest.raises(ValueError):
        make_domain("nope", 0)
