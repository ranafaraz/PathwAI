"""Optional OpenAI proposer. Opt-in via ``pip install "pathwai[openai]"`` + a key.

Mirrors the Ollama backend: ask a hosted model for an integer cost-to-go estimate
from the rendered state, and fall back to the offline stub on any error (missing
dependency, missing ``OPENAI_API_KEY``, rate limit, unparseable reply). The search
machinery treats every proposer identically, so this is a drop-in upgrade.
"""

from __future__ import annotations

import os
import re

from pathwai.domains.base import Domain
from pathwai.proposers.base import Proposer
from pathwai.proposers.stub import StubProposer
from pathwai.types import State

_PROMPT = (
    "You are a planning heuristic for a {domain} problem. Reply with ONLY an "
    "integer: the minimum number of actions still needed to reach the goal.\n\n"
    "STATE:\n{state}\n\nInteger:"
)


class OpenAIProposer(Proposer):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._fallback = StubProposer()
        self._warned = False

    def cost_to_go(self, domain: Domain, state: State) -> float:
        if not os.environ.get("OPENAI_API_KEY"):
            return self._degrade(domain, state)
        try:
            from openai import OpenAI  # lazy

            client = OpenAI()
            prompt = _PROMPT.format(domain=domain.name, state=domain.render(state))
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = resp.choices[0].message.content or ""
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
                "OpenAI backend unavailable; falling back to the offline stub proposer.",
                RuntimeWarning,
                stacklevel=2,
            )
            self._warned = True
        return self._fallback.cost_to_go(domain, state)
