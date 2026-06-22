"""Planners and an env-driven factory.

The LLM-guided planners need a proposer; the classical ones do not. ``get_planner``
wires the configured proposer into the former and leaves the latter untouched, so
the same factory serves every backend.
"""

from __future__ import annotations

from pathwai.config import Settings
from pathwai.planners.base import Planner
from pathwai.planners.classical import (
    GreedyPlanner,
    OptimalPlanner,
    UniformCostPlanner,
)
from pathwai.planners.llm import OpenLoopLLMPlanner
from pathwai.planners.llm_search import LLMSearchPlanner
from pathwai.proposers import get_proposer

PLANNERS = ("optimal", "uniform", "greedy", "llm", "llm_search")


def get_planner(cfg: Settings, name: str | None = None) -> Planner:
    """Build the planner named ``name`` (default: ``cfg.planner``)."""
    name = name or cfg.planner
    if name == "optimal":
        return OptimalPlanner(max_expansions=cfg.max_expansions)
    if name == "uniform":
        return UniformCostPlanner(max_expansions=cfg.max_expansions)
    if name == "greedy":
        return GreedyPlanner(max_expansions=cfg.max_expansions)
    if name == "llm":
        return OpenLoopLLMPlanner(get_proposer(cfg))
    if name == "llm_search":
        return LLMSearchPlanner(get_proposer(cfg), max_expansions=cfg.max_expansions)
    raise ValueError(f"unknown planner {name!r}; choose from {', '.join(PLANNERS)}")


__all__ = [
    "Planner",
    "OptimalPlanner",
    "UniformCostPlanner",
    "GreedyPlanner",
    "OpenLoopLLMPlanner",
    "LLMSearchPlanner",
    "get_planner",
    "PLANNERS",
]
