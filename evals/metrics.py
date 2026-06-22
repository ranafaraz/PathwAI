"""Aggregation helpers for the offline eval.

The eval runs one planner over many seeded instances and reduces the per-instance
:class:`~pathwai.types.PlanResult` objects to three portfolio metrics: solve rate,
mean optimality ratio (over solved instances only -- an unsolved instance has no
ratio), and mean node expansions (over all instances, since search effort is
spent whether or not the goal is reached).
"""

from __future__ import annotations

from collections.abc import Iterable

from pathwai.types import PlanResult


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def aggregate(results: Iterable[PlanResult]) -> dict:
    results = list(results)
    n = len(results)
    solved = [r for r in results if r.solved]
    ratios = [r.optimality_ratio for r in solved if r.optimality_ratio is not None]
    return {
        "n": n,
        "solve_rate": round(len(solved) / n, 3) if n else 0.0,
        "optimality_ratio": round(_mean(ratios), 3),
        "expansions": round(_mean([float(r.expansions) for r in results]), 1),
        "invalid_proposals": round(_mean([float(r.invalid_proposals) for r in results]), 2),
    }
