"""Random proposer: an uninformative guidance ablation.

It returns a deterministic value that is *uncorrelated* with the true
cost-to-go. Swapping the stub for this is PathwAI's "null test": with no useful
guidance, the open-loop agent collapses, while the search+verifier agent still
solves every instance but pays for it in vastly more node expansions. That gap
isolates how much of the agent's performance comes from guidance vs. from search.
"""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.proposers.base import Proposer, stable_unit
from pathwai.types import State


class RandomProposer(Proposer):
    name = "random"

    def __init__(self, scale: float = 20.0, seed: int = 0) -> None:
        self.scale = scale
        self.seed = seed

    def cost_to_go(self, domain: Domain, state: State) -> float:
        if domain.goal_test(state):
            return 0.0
        return stable_unit(("rand", self.seed, domain.name, state)) * self.scale
