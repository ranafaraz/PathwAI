"""Classical baselines: optimal A*, uninformed uniform-cost, and greedy best-first.

These bracket the LLM-guided agent. ``optimal`` (A* with the admissible heuristic)
defines the best achievable plan and the optimality denominator. ``uniform``
(Dijkstra) is also optimal but heuristic-blind -- its expansion count is the
"search without guidance" cost the agent must beat. ``greedy`` (best-first on the
heuristic alone) is fast but suboptimal, the classic speed-for-quality trade.
"""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.planners.base import Planner
from pathwai.search import best_first
from pathwai.types import PlanResult


class _SearchPlanner(Planner):
    """Shared wrapper: run ``best_first`` with this planner's priority function."""

    def __init__(self, max_expansions: int = 5000) -> None:
        self.max_expansions = max_expansions

    def _priority(self, domain: Domain):  # pragma: no cover - overridden
        raise NotImplementedError

    def plan(self, domain: Domain, optimal_cost: float | None = None) -> PlanResult:
        outcome = best_first(domain, self._priority(domain), self.max_expansions)
        return PlanResult(
            domain=domain.name,
            planner=self.name,
            solved=outcome.solved,
            plan=outcome.plan,
            cost=outcome.cost if outcome.solved else 0.0,
            optimal_cost=optimal_cost,
            expansions=outcome.expansions,
        )


class OptimalPlanner(_SearchPlanner):
    name = "optimal"

    def _priority(self, domain: Domain):
        return lambda s, g: g + domain.heuristic(s)


class UniformCostPlanner(_SearchPlanner):
    name = "uniform"

    def _priority(self, domain: Domain):
        return lambda s, g: g


class GreedyPlanner(_SearchPlanner):
    name = "greedy"

    def _priority(self, domain: Domain):
        return lambda s, g: domain.heuristic(s)
