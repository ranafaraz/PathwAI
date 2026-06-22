"""PathwAI: deliberate LLM planning, benchmarked against optimal.

A plan-and-solve agent that decomposes goals into action sequences over
deterministic planning domains. A built-in A* solver provides *ground-truth
optimal* plans, so every planner -- including the LLM-guided ones -- is scored
against the optimum on both plan quality and search effort.

Offline-first: a deterministic stub proposer stands in for an LLM so the whole
pipeline, tests, and CI run green with no API keys and no model downloads.
"""

from __future__ import annotations

from pathwai.types import Action, PlanResult

__all__ = ["Action", "PlanResult", "__version__"]
__version__ = "0.1.0"
