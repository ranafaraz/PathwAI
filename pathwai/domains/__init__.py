"""Deterministic planning domains and a seed-driven factory."""

from __future__ import annotations

from pathwai.domains.base import Domain
from pathwai.domains.blocksworld import Blocksworld
from pathwai.domains.delivery import Delivery
from pathwai.domains.gridworld import GridWorld

_BUILDERS = {
    "gridworld": GridWorld.from_seed,
    "blocksworld": Blocksworld.from_seed,
    "delivery": Delivery.from_seed,
}

DOMAINS = tuple(_BUILDERS)


def make_domain(name: str, seed: int) -> Domain:
    """Build a deterministic instance of ``name`` for ``seed``."""
    try:
        return _BUILDERS[name](seed)
    except KeyError:
        raise ValueError(
            f"unknown domain {name!r}; choose from {', '.join(DOMAINS)}"
        ) from None


__all__ = ["Domain", "GridWorld", "Blocksworld", "Delivery", "make_domain", "DOMAINS"]
