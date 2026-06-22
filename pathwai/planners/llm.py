"""Open-loop LLM agent: greedily follow the proposer, no backtracking.

This is the naive "let the model just pick the next step" baseline. At each state
it ranks applicable actions by ``step_cost + proposer.cost_to_go(successor)`` and
takes the best one the verifier allows (legal and not already visited). With no
ability to backtrack, a single bad suggestion can strand it in a dead-end -- which
is exactly what happens often enough to expose why search matters.
"""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.planners.base import Planner
from pathwai.proposers.base import Proposer
from pathwai.types import PlanResult
from pathwai.verify import Verifier


class OpenLoopLLMPlanner(Planner):
    name = "llm"

    def __init__(self, proposer: Proposer, max_steps: int = 500) -> None:
        self.proposer = proposer
        self.max_steps = max_steps

    def plan(self, domain: Domain, optimal_cost: float | None = None) -> PlanResult:
        state = domain.initial_state()
        verifier = Verifier()
        verifier.visit(state)
        plan = []
        cost = 0.0

        for _ in range(self.max_steps):
            if domain.goal_test(state):
                break
            # Rank legal actions whose successor is unexplored.
            candidates = []
            for action in domain.actions(state):
                nxt = domain.result(state, action)
                if not verifier.is_progress(nxt):
                    continue
                score = domain.step_cost(state, action) + self.proposer.cost_to_go(domain, nxt)
                candidates.append((score, action, nxt))
            if not candidates:
                break  # dead-end: every move loops back. No backtracking -> stuck.
            candidates.sort(key=lambda t: t[0])
            _, action, nxt = candidates[0]
            cost += domain.step_cost(state, action)
            plan.append(action)
            verifier.visit(nxt)
            state = nxt

        solved = domain.goal_test(state)
        return PlanResult(
            domain=domain.name,
            planner=self.name,
            solved=solved,
            plan=plan if solved else [],
            cost=cost if solved else 0.0,
            optimal_cost=optimal_cost,
            expansions=len(plan),
            invalid_proposals=verifier.rejections,
        )
