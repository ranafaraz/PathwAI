"""Offline stub proposer: a deterministic but *noisy* heuristic oracle.

This is the default backend that keeps CI green with no model. It returns the
domain's true cost-to-go perturbed by a reproducible, state-dependent error --
modelling an LLM that is informative but imperfect. The noise is calibrated
(``stub_noise``) so that an open-loop agent that blindly follows it stumbles into
detours and dead-ends, while the search+verifier agent using the same signal
recovers near-optimal plans. That contrast is the product.
"""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.proposers.base import Proposer, stable_unit
from pathwai.types import State


class StubProposer(Proposer):
    name = "stub"

    def __init__(self, noise: float = 0.55, seed: int = 0) -> None:
        self.noise = noise
        self.seed = seed

    def cost_to_go(self, domain: Domain, state: State) -> float:
        h = domain.heuristic(state)
        if h <= 0:
            return 0.0
        # Symmetric multiplicative error in [-noise, +noise], deterministic.
        u = stable_unit((domain.name, self.seed, state))
        err = (2.0 * u - 1.0) * self.noise
        return max(0.0, h * (1.0 + err))
