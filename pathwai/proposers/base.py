"""The proposer abstraction: the LLM's role in the planner, reduced to one call.

Every backend -- the offline stub, the random ablation, or a real LLM -- answers
the same question: *given this state, estimate the remaining cost to the goal.*
That single number is what the search engine turns into guidance (``g + estimate``)
and what the open-loop agent greedily follows. Reducing the LLM to a scalar
cost-to-go keeps backends swappable and the comparison apples-to-apples.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from pathwai.domains.base import Domain
from pathwai.types import State


def stable_unit(key: object) -> float:
    """Deterministic pseudo-random float in ``[0, 1)`` from ``key``.

    Uses a content hash (not Python's salted ``hash``) so the stub's "noise" is
    identical across processes and CI runs -- reproducibility is the whole point
    of the offline backend.
    """
    digest = hashlib.md5(repr(key).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(1 << 64)


class Proposer(ABC):
    name: str = "proposer"

    @abstractmethod
    def cost_to_go(self, domain: Domain, state: State) -> float:
        """Estimated remaining cost from ``state`` to a goal (0 at the goal)."""
