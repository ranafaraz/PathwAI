"""Search engine: optimality of A*/uniform and budget handling."""

from __future__ import annotations

import pytest

from pathwai.domains import make_domain
from pathwai.search import astar, best_first


@pytest.mark.parametrize("name", ["gridworld", "blocksworld", "delivery"])
def test_astar_matches_uniform_cost_optimum(name):
    # Two optimal searches must agree on cost: A* (heuristic) and Dijkstra (blind).
    domain = make_domain(name, 5)
    a = astar(domain, max_expansions=20000)
    u = best_first(domain, lambda s, g: g, max_expansions=20000)
    assert a.solved and u.solved
    assert a.cost == u.cost


def test_astar_expands_no_more_than_uniform():
    domain = make_domain("delivery", 5)
    a = astar(domain, max_expansions=20000)
    u = best_first(domain, lambda s, g: g, max_expansions=20000)
    assert a.expansions <= u.expansions


def test_zero_budget_does_not_solve_nontrivial_instance():
    domain = make_domain("gridworld", 1)
    out = astar(domain, max_expansions=0)
    assert not out.solved
    assert out.expansions == 0
