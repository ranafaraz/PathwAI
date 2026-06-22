"""Orchestration: solve one instance with one planner, scored against the optimum.

Every run first computes the ground-truth optimal cost with A*, then hands it to
the chosen planner purely for reporting (the planner never sees the optimal plan).
This is what makes the optimality ratio meaningful: the denominator is provably
the best possible, not another heuristic's guess.
"""

from __future__ import annotations

from pathwai.config import Settings
from pathwai.domains import Domain, make_domain
from pathwai.planners import get_planner
from pathwai.planners.classical import OptimalPlanner
from pathwai.types import PlanResult


def optimal_cost_of(domain: Domain, max_expansions: int) -> float | None:
    res = OptimalPlanner(max_expansions=max_expansions).plan(domain)
    return res.cost if res.solved else None


def solve_instance(domain: Domain, cfg: Settings, planner_name: str | None = None) -> PlanResult:
    """Solve ``domain`` with the named planner, reporting against the A* optimum."""
    opt = optimal_cost_of(domain, cfg.max_expansions)
    planner = get_planner(cfg, planner_name)
    return planner.plan(domain, optimal_cost=opt)


def solve(cfg: Settings) -> PlanResult:
    """Build the configured domain instance and solve it with the configured planner."""
    domain = make_domain(cfg.domain, cfg.seed)
    return solve_instance(domain, cfg, cfg.planner)
