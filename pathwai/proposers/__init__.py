"""LLM proposer backends and an env-driven factory."""

from __future__ import annotations

from pathwai.config import Settings
from pathwai.proposers.base import Proposer
from pathwai.proposers.random_proposer import RandomProposer
from pathwai.proposers.stub import StubProposer

BACKENDS = ("stub", "random", "ollama", "openai")


def get_proposer(cfg: Settings) -> Proposer:
    """Resolve the configured proposer backend.

    Offline backends are constructed directly; the optional real backends are
    imported lazily so their dependencies are only needed when selected.
    """
    backend = cfg.proposer_backend
    if backend == "stub":
        return StubProposer(noise=cfg.stub_noise, seed=cfg.seed)
    if backend == "random":
        return RandomProposer(seed=cfg.seed)
    if backend == "ollama":
        from pathwai.proposers.ollama import OllamaProposer

        return OllamaProposer(model=cfg.ollama_model)
    if backend == "openai":
        from pathwai.proposers.openai_proposer import OpenAIProposer

        return OpenAIProposer(model=cfg.openai_model)
    raise ValueError(f"unknown proposer backend {backend!r}; choose from {', '.join(BACKENDS)}")


__all__ = ["Proposer", "StubProposer", "RandomProposer", "get_proposer", "BACKENDS"]
