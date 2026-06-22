"""CI quality gate: fail the build if the planning story regresses.

The gate does not just check that numbers are "good" -- it enforces the *shape*
of the result that makes PathwAI worth showing: A* is optimal, the LLM+search
agent is near-optimal and complete, search beats open-loop, guidance beats blind
search, and removing the guidance collapses the open-loop agent. Floors sit well
below the observed offline numbers so ordinary variation never flakes CI, while a
genuine regression (broken verifier, dead heuristic, leaky optimum) trips it.
"""

from __future__ import annotations

import sys

from evals.harness import run_eval


def _checks(res: dict) -> list[tuple[str, bool, str]]:
    o = res["overall"]
    ab = res["ablation"]
    # Derived comparisons.
    search_gap = o["llm_search"]["solve_rate"] - o["llm"]["solve_rate"]
    guidance_speedup = (
        o["uniform"]["expansions"] / o["llm_search"]["expansions"]
        if o["llm_search"]["expansions"]
        else 0.0
    )
    ablation_blowup = (
        ab["llm_search"]["expansions"] / o["llm_search"]["expansions"]
        if o["llm_search"]["expansions"]
        else 0.0
    )
    return [
        (
            "A* baseline is optimal and complete",
            o["optimal"]["solve_rate"] >= 1.0 and o["optimal"]["optimality_ratio"] <= 1.0001,
            f"solve={o['optimal']['solve_rate']}, ratio={o['optimal']['optimality_ratio']}",
        ),
        (
            "llm+search solves everything",
            o["llm_search"]["solve_rate"] >= 0.99,
            f"solve_rate={o['llm_search']['solve_rate']} >= 0.99",
        ),
        (
            "llm+search is near-optimal",
            o["llm_search"]["optimality_ratio"] <= 1.10,
            f"optimality_ratio={o['llm_search']['optimality_ratio']} <= 1.10",
        ),
        (
            "search beats open-loop (correctness)",
            search_gap >= 0.20,
            f"solve gap={search_gap:.3f} >= 0.20 "
            f"(llm_search {o['llm_search']['solve_rate']} vs llm {o['llm']['solve_rate']})",
        ),
        (
            "guidance beats blind search (efficiency)",
            guidance_speedup >= 1.8,
            f"uniform/llm_search expansions={guidance_speedup:.2f}x >= 1.8x "
            f"({o['uniform']['expansions']} vs {o['llm_search']['expansions']})",
        ),
        (
            "ablation: open-loop collapses without guidance",
            ab["llm"]["solve_rate"] <= 0.40,
            f"random-guidance llm solve_rate={ab['llm']['solve_rate']} <= 0.40",
        ),
        (
            "ablation: guidance buys efficiency",
            ablation_blowup >= 1.5,
            f"random/stub llm_search expansions={ablation_blowup:.2f}x >= 1.5x "
            f"({ab['llm_search']['expansions']} vs {o['llm_search']['expansions']})",
        ),
    ]


def main() -> int:
    res = run_eval()
    checks = _checks(res)
    print("PathwAI eval gate")
    failures = []
    for desc, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}: {detail}")
        if not ok:
            failures.append(desc)
    if failures:
        print("\nGATE FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nGATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
