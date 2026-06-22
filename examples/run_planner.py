"""Minimal end-to-end example: solve one instance and inspect the plan.

Run: ``python examples/run_planner.py``  (fully offline, no keys/downloads).
"""

from __future__ import annotations

from pathwai.config import Settings
from pathwai.domains import make_domain
from pathwai.pipeline import solve_instance


def main() -> None:
    cfg = Settings.from_env()
    cfg.proposer_backend = "stub"

    for domain_name in ("gridworld", "blocksworld", "delivery"):
        domain = make_domain(domain_name, seed=3)
        # The hero planner: LLM proposer + best-first search + verifier.
        res = solve_instance(domain, cfg, "llm_search")
        ratio = res.optimality_ratio
        print(f"[{domain_name}] solved={res.solved} steps={res.steps} "
              f"optimal={res.optimal_cost} ratio={'n/a' if ratio is None else round(ratio, 3)} "
              f"expansions={res.expansions}")


if __name__ == "__main__":
    main()
