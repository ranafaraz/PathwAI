"""Environment-driven configuration.

Every heavy component has a deterministic *offline* default so tests and CI run
green with no API keys and no model downloads. The LLM proposer defaults to the
``stub`` backend (a deterministic, deliberately *noisy* heuristic oracle); real
backends (Ollama, OpenAI) are opt-in via env vars and pip extras and degrade
gracefully back to the stub if unavailable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get(name: str, default: str) -> str:
    val = os.environ.get(name)
    return default if val is None or val == "" else val


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.environ[name])
    except (KeyError, ValueError):
        return default


@dataclass
class Settings:
    """Resolved runtime settings.

    Backends
    --------
    proposer_backend : ``stub`` (offline default, noisy heuristic oracle) |
        ``random`` (uninformative ablation) | ``ollama`` (``[ollama]``) |
        ``openai`` (``[openai]``)
    """

    proposer_backend: str = "stub"
    domain: str = "gridworld"
    planner: str = "llm_search"
    seed: int = 7

    # Search / agent budget.
    max_expansions: int = 5000

    # Stub proposer: how noisy the heuristic oracle is. 0 == perfect heuristic,
    # higher == a worse guide. Tuned so open-loop greedy stumbles but the
    # search+verifier agent recovers.
    stub_noise: float = 0.55

    # Optional real-LLM backend knobs.
    ollama_model: str = "llama3.1:8b"
    openai_model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            proposer_backend=_get("PATHWAI_PROPOSER_BACKEND", cls.proposer_backend),
            domain=_get("PATHWAI_DOMAIN", cls.domain),
            planner=_get("PATHWAI_PLANNER", cls.planner),
            seed=_get_int("PATHWAI_SEED", cls.seed),
            max_expansions=_get_int("PATHWAI_MAX_EXPANSIONS", cls.max_expansions),
            stub_noise=_get_float("PATHWAI_STUB_NOISE", cls.stub_noise),
            ollama_model=_get("PATHWAI_OLLAMA_MODEL", cls.ollama_model),
            openai_model=_get("PATHWAI_OPENAI_MODEL", cls.openai_model),
        )
