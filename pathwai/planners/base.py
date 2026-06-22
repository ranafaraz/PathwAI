"""The :class:`Planner` contract: turn a domain instance into a :class:`PlanResult`.

Every planner -- classical or LLM-guided -- takes the same domain and returns the
same result type, so the eval harness can score them on one set of axes
(solved / optimality / expansions). ``optimal_cost`` is injected by the caller
(computed once by the optimal planner) so each result can report its optimality
ratio without re-running A*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pathwai.domains.base import Domain
from pathwai.types import PlanResult


class Planner(ABC):
    name: str = "planner"

    @abstractmethod
    def plan(self, domain: Domain, optimal_cost: float | None = None) -> PlanResult:
        """Produce a plan for ``domain`` (``optimal_cost`` is for reporting only)."""
