"""The verifier: the guardrail that turns a fallible proposer into a safe agent.

An LLM proposer can suggest an action that is illegal, or walk the agent in
circles. The verifier rejects both: it confirms each action is actually
applicable in the current state and refuses to revisit a state already seen on
this trajectory. It is what lets the LLM-guided search recover from bad
suggestions instead of executing them blindly -- and it is shared by the
open-loop agent (where it is the *only* safety net) and the replanning loop.
"""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.types import Action, State


class Verifier:
    def __init__(self) -> None:
        self.visited: set[State] = set()
        self.rejections = 0

    def is_legal(self, domain: Domain, state: State, action: Action) -> bool:
        """True iff ``action`` is applicable in ``state`` per the domain model."""
        legal = action in domain.actions(state)
        if not legal:
            self.rejections += 1
        return legal

    def is_progress(self, next_state: State) -> bool:
        """True iff moving to ``next_state`` does not revisit an explored state."""
        ok = next_state not in self.visited
        if not ok:
            self.rejections += 1
        return ok

    def visit(self, state: State) -> None:
        self.visited.add(state)
