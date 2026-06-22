"""Optional Ollama proposer (local LLM). Opt-in via ``pip install "pathwai[ollama]"``.

It asks a locally-served model to estimate the number of actions remaining to the
goal from the rendered state. Any failure -- server down, dependency missing,
unparseable answer -- degrades gracefully to the offline stub, so importing or
selecting this backend can never crash the pipeline.
"""

from __future__ import annotations

import re

from pathwai.domains.base import Domain
from pathwai.proposers.base import Proposer
from pathwai.proposers.stub import StubProposer
from pathwai.types import State

_PROMPT = (
    "You are a planning heuristic. Given this state of a {domain} problem, reply "
    "with ONLY an integer: your best estimate of the minimum number of actions "
    "still required to reach the goal.\n\nSTATE:\n{state}\n\nInteger:"
)


class OllamaProposer(Proposer):
    name = "ollama"

    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434") -> None:
        self.model = model
        self.host = host
        self._fallback = StubProposer()
        self._warned = False

    def cost_to_go(self, domain: Domain, state: State) -> float:
        try:
            import requests  # lazy; only needed for the real backend
        except ImportError:
            return self._degrade(domain, state)
        try:
            prompt = _PROMPT.format(domain=domain.name, state=domain.render(state))
            resp = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=30,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "")
            match = re.search(r"-?\d+", text)
            if match:
                return max(0.0, float(int(match.group())))
        except Exception:
            pass
        return self._degrade(domain, state)

    def _degrade(self, domain: Domain, state: State) -> float:
        if not self._warned:
            import warnings

            warnings.warn(
                "Ollama backend unavailable; falling back to the offline stub proposer.",
                RuntimeWarning,
                stacklevel=2,
            )
            self._warned = True
        return self._fallback.cost_to_go(domain, state)
