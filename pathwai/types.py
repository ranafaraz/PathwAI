"""Core value types shared across domains, search, and planners.

States are any *hashable* value (domains use tuples of immutable data) so the
search frontier can keep a closed set cheaply. Actions carry a name plus a
hashable argument tuple and stringify into a human-readable label for the LLM
prompt and the CLI trace.
"""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any

# A domain state: any hashable, immutable value (domains use nested tuples).
State = Hashable


@dataclass(frozen=True)
class Action:
    """A single, fully-grounded domain action.

    ``name`` is the operator (e.g. ``move``); ``args`` are its grounded
    arguments. Frozen + hashable so plans and proposer caches can use it.
    """

    name: str
    args: tuple[Any, ...] = ()
    label: str = ""

    def __str__(self) -> str:
        if self.label:
            return self.label
        arg = ", ".join(str(a) for a in self.args)
        return f"{self.name}({arg})" if arg else self.name


@dataclass
class PlanResult:
    """Outcome of running one planner on one domain instance.

    The headline portfolio metrics derive from this: ``solved`` (did we reach
    the goal under budget), ``optimality_ratio`` (plan cost vs. the A* optimum),
    and ``expansions`` (search effort -- the efficiency axis).
    """

    domain: str
    planner: str
    solved: bool
    plan: list[Action] = field(default_factory=list)
    cost: float = 0.0
    optimal_cost: float | None = None
    expansions: int = 0
    invalid_proposals: int = 0
    replans: int = 0

    @property
    def steps(self) -> int:
        return len(self.plan)

    @property
    def optimality_ratio(self) -> float | None:
        """Plan cost / optimal cost. ``1.0`` is optimal; ``None`` if unsolved or
        no optimum is known. An unsolved instance has no meaningful ratio."""
        if not self.solved or self.optimal_cost is None or self.optimal_cost <= 0:
            return None
        return self.cost / self.optimal_cost

    def as_dict(self) -> dict[str, Any]:
        ratio = self.optimality_ratio
        return {
            "domain": self.domain,
            "planner": self.planner,
            "solved": self.solved,
            "steps": self.steps,
            "cost": round(self.cost, 3),
            "optimal_cost": self.optimal_cost,
            "optimality_ratio": None if ratio is None else round(ratio, 3),
            "expansions": self.expansions,
            "invalid_proposals": self.invalid_proposals,
            "replans": self.replans,
        }
