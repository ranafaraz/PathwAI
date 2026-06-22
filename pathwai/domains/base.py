"""The :class:`Domain` contract every planning environment implements.

A domain is a deterministic search problem with a *grounded* successor function.
Crucially it also exposes ``heuristic`` (an admissible lower bound used by the
optimal A* baseline) and ``render`` (a natural-language view handed to the LLM
proposer). Keeping both on the domain lets every planner -- classical or
LLM-guided -- run against the exact same problem definition.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pathwai.types import Action, State


class Domain(ABC):
    """A deterministic, fully-observable planning problem."""

    name: str = "domain"

    @abstractmethod
    def initial_state(self) -> State:
        """The start state."""

    @abstractmethod
    def goal_test(self, state: State) -> bool:
        """True iff ``state`` satisfies the goal."""

    @abstractmethod
    def actions(self, state: State) -> list[Action]:
        """All actions *applicable* in ``state`` (never illegal ones)."""

    @abstractmethod
    def result(self, state: State, action: Action) -> State:
        """The deterministic successor of applying ``action`` in ``state``."""

    @abstractmethod
    def heuristic(self, state: State) -> float:
        """An **admissible** lower bound on cost-to-go (0 at the goal).

        Admissibility is what makes the A* baseline provably optimal; it is
        unit-tested per domain. The stub proposer perturbs this value, so a
        broken heuristic would quietly corrupt the LLM guidance too.
        """

    @abstractmethod
    def render(self, state: State) -> str:
        """A compact human/LLM-readable view of ``state`` (for prompts + CLI)."""

    def step_cost(self, state: State, action: Action) -> float:
        """Cost of one action. Unit cost unless a domain overrides it."""
        return 1.0
