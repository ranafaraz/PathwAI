"""LLM + search + verifier: the hero planner.

It uses the proposer's cost-to-go as the heuristic in a best-first search
(``priority = g + proposer.cost_to_go``). The search's closed set is the verifier
in action -- it can abandon a misleading suggestion and explore an alternative,
something the open-loop agent cannot. The result: near-optimal plans even with a
noisy proposer, while expanding far fewer nodes than uninformed search because
the guidance focuses the frontier toward the goal.

It also supports ``replan`` from an arbitrary state, which the robustness eval
uses to recover after the environment changes mid-execution.
"""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.planners.base import Planner
from pathwai.proposers.base import Proposer
from pathwai.search import best_first
from pathwai.types import PlanResult
from pathwai.verify import Verifier


class LLMSearchPlanner(Planner):
    name = "llm_search"

    def __init__(self, proposer: Proposer, max_expansions: int = 5000) -> None:
        self.proposer = proposer
        self.max_expansions = max_expansions

    def _priority(self, domain: Domain):
        return lambda s, g: g + self.proposer.cost_to_go(domain, s)

    def plan(self, domain: Domain, optimal_cost: float | None = None) -> PlanResult:
        outcome = best_first(domain, self._priority(domain), self.max_expansions)
        invalid = 0
        if outcome.solved:
            invalid = self._audit(domain, outcome.plan)
        return PlanResult(
            domain=domain.name,
            planner=self.name,
            solved=outcome.solved,
            plan=outcome.plan,
            cost=outcome.cost if outcome.solved else 0.0,
            optimal_cost=optimal_cost,
            expansions=outcome.expansions,
            invalid_proposals=invalid,
        )

    def _audit(self, domain: Domain, plan) -> int:
        """Replay the plan through the verifier; a correct search yields zero
        rejections. This is a defensive check that the returned plan is sound."""
        verifier = Verifier()
        state = domain.initial_state()
        for action in plan:
            if not verifier.is_legal(domain, state, action):
                break
            state = domain.result(state, action)
        return verifier.rejections
