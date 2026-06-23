# Evaluation

## Benchmark setup

All results use the offline stub proposer — no API keys or model downloads required. Results are deterministic at a given seed.

**Domains:** GridWorld, Blocksworld, Delivery (3 domains)
**Seeds:** 0–49 (50 instances per domain)
**Total instances:** 150
**Scoring:** every plan measured against its A\* optimum (optimality ratio = agent cost / A\* cost)

**Proposer:**
- Stub: true domain heuristic + Gaussian noise (std=0.55 x heuristic value)
- Random (ablation): uniform random cost-to-go estimate

---

## Main results

Pooled across all 150 instances (50 seeds x 3 domains):

| Planner | Solve rate | Optimality ratio | Avg expansions |
|---|---:|---:|---:|
| optimal (A\*) — ground truth | 1.00 | 1.000 | 28.1 |
| uniform-cost (no heuristic) | 1.00 | 1.000 | 79.0 |
| greedy best-first | 1.00 | 1.045 | 15.0 |
| llm (open-loop, no backtrack) | 0.50 | 1.533 | 12.1 |
| **llm + search + verifier** | **1.00** | **1.012** | **25.5** |

Two effects, cleanly separated:

- **Search + verifier buys correctness.** The noisy stub that the open-loop agent solves 50% of at 1.53x optimal solves 100% at 1.01x optimal once it can search and backtrack.
- **LLM guidance buys efficiency.** The heuristic focuses the frontier: 25.5 expansions vs. uninformed search's 79.0 — a 3.1x reduction.

---

## Per-domain breakdown

| Domain | Planner | Solve rate | Opt. ratio | Avg expansions |
|---|---|---:|---:|---:|
| GridWorld | llm_search | 1.00 | 1.008 | 22.3 |
| GridWorld | llm (open-loop) | 0.54 | 1.481 | 11.0 |
| Blocksworld | llm_search | 1.00 | 1.015 | 27.8 |
| Blocksworld | llm (open-loop) | 0.44 | 1.602 | 13.1 |
| Delivery | llm_search | 1.00 | 1.013 | 26.4 |
| Delivery | llm (open-loop) | 0.52 | 1.516 | 12.2 |

The pattern holds across all three domains: search+verifier recovers full correctness regardless of domain structure.

---

## Null ablation (random proposer)

Replacing the stub with a completely random proposer isolates the contribution of search+verifier from the contribution of guidance:

| Planner (random guidance) | Solve rate | Opt. ratio | Avg expansions |
|---|---:|---:|---:|
| llm open-loop | 0.17 | 1.921 | 11.6 |
| **llm + search + verifier** | **1.00** | **1.000** | **65.0** |

Interpretation:
- The verifier still guarantees 100% correctness with random guidance.
- Expansions balloon from 25.5 (stub guidance) to 65.0 (random guidance), confirming that the efficiency gain comes from the informative heuristic, not the search structure.
- The open-loop agent with random guidance collapses to 0.17 solve rate — worse than greedy or uninformed, because it follows random paths to dead ends with no backtracking.

---

## Reproduce

```bash
# Activate venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Full benchmark across all 150 instances (writes evals/RESULTS.md)
python -m evals.harness

# CI quality gate (checks shape: llm_search complete, llm collapses, etc.)
python -m evals.gate

# Run the null ablation explicitly
PATHWAI_PROPOSER_BACKEND=random python -m evals.harness

# Single domain / seed
pathwai compare --domain gridworld --seed 3
pathwai compare --domain blocksworld --seed 7
pathwai compare --domain delivery --seed 0

# Render a specific instance
pathwai render --domain gridworld --seed 5
```

CI runs `evals.gate` on every push. The gate enforces: llm_search solve rate = 1.0, optimality ratio < 1.05, open-loop llm solve rate < 0.7, random-guidance ablation collapses (expansions > 50).
