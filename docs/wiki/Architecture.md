# Architecture

## Overview

PathwAI is structured as a single unified search engine driven by pluggable proposers, operating over pluggable planning domains. Every planner in the benchmark — A*, Dijkstra, greedy, open-loop LLM, and LLM+search+verifier — is the same `search.best_first` function with a different priority function. This eliminates the risk of the comparison being rigged by subtly different implementations.

```
pathwai/
    types.py            State, Action, Plan, PlanResult dataclasses
    config.py           env-var loading
    pipeline.py         orchestrates benchmark runs
    cli.py              Click commands (solve, compare, render, eval)

    domains/
        base.py         Domain ABC: state, actions, apply, render, heuristic, is_goal
        gridworld.py    GridWorld: agent on a grid
        blocksworld.py  Blocksworld: stack manipulation
        delivery.py     Delivery: multi-package routing

    search.py           best_first(domain, proposer, verifier, priority_fn)
    verify.py           Verifier: legal-move and loop checks

    proposers/
        stub.py         StubProposer: true heuristic + calibrated noise
        random_.py      RandomProposer: ablation baseline
        ollama.py       OllamaProposer (lazy import, optional)
        openai.py       OpenAIProposer (lazy import, optional)

    planners/
        classical.py    optimal, uniform, greedy (priority function wrappers)
        llm.py          open-loop LLM (no search, no backtrack)
        llm_search.py   LLM + search + verifier (the full agent)

evals/
    harness.py          benchmark orchestration
    gate.py             quality gate
    RESULTS.md          (generated)
```

---

## Domain representation

Each domain implements the `Domain` ABC:

- `initial_state(seed) -> State` — deterministic starting configuration
- `applicable_actions(state) -> list[Action]` — legal moves from this state
- `apply(state, action) -> State` — transition function
- `is_goal(state) -> bool` — terminal check
- `heuristic(state) -> float` — admissible lower bound on cost-to-go
- `render(state) -> str` — text description for LLM prompts and CLI output
- `optimal_cost(seed) -> float` — A* optimum (used for scoring)

**GridWorld:** Agent moves on an N x N grid with obstacles. Heuristic = Manhattan distance to goal. State = `(row, col)`.

**Blocksworld:** Blocks are arranged in stacks; the goal is a target stack configuration. Heuristic = number of misplaced blocks. State = normalised tuple of stack tuples.

**Delivery:** Agent must pick up and deliver packages to specific locations. State = `(position, frozenset(pending_deliveries), frozenset(carried))`. Heuristic = remaining pickups + deliveries + estimated travel.

All three heuristics are **admissible** (never overestimate) — unit-tested by verifying `heuristic(state) <= actual_cost_to_goal(state)` along every step of every optimal path in the test suite.

---

## LLM Proposer

The proposer takes a state description (rendered by the domain) and returns a scalar cost-to-go estimate: how many more steps does the proposer think it will take to reach the goal?

This estimate is used as the heuristic `h` in the priority function `f = g + h`, where `g` is the cost of the path so far. A perfect heuristic makes the search behave like A*. A poor heuristic degrades toward uninformed search.

**Prompt design (real LLM backends):** The render includes the current state, the goal, and the set of applicable actions. The LLM is asked to estimate the remaining cost as a number. The response is parsed; non-numeric responses fall back to the domain heuristic.

**Stub offline:** The stub computes the true domain heuristic value, then adds calibrated Gaussian noise (`stub_noise=0.55`). This means the stub is informative — it guides the search in the right direction — but imperfect enough that the open-loop agent without backtracking fails ~50% of the time. That failure rate is the demonstration that guidance alone is not enough; search and verification are required.

---

## Verifier

The verifier enforces two invariants before a proposed action is accepted:

1. **Legality:** The action must be in `domain.applicable_actions(current_state)`.
2. **No revisits:** The resulting state must not already be in the visited set.

In the open-loop LLM planner, there is no verifier — bad proposals are executed and there is no backtracking. In the LLM+search+verifier agent, illegal or revisiting proposals are rejected and the search backtracks to the next-best frontier node. This is why correctness improves dramatically with the wrapper even with the same (noisy) proposer.

---

## Search component: priority functions

`search.best_first(domain, proposer, verifier, priority_fn)` is a standard priority-queue search. The priority function determines what gets expanded next:

| Planner | Priority function | Equivalent to |
|---|---|---|
| `optimal` | `g` (path cost only) | Dijkstra / UCS |
| `uniform` | `g` | (same, different label) |
| `greedy` | `h` (domain heuristic only) | Greedy best-first |
| `llm` | open-loop, no queue | No search, just follow proposals |
| `llm_search` | `g + proposer.estimate(state)` | A*-style with LLM heuristic |

Because all five planners share the same engine, any difference in solve rate or expansion count is attributable to the priority function alone.

---

## A* oracle

The A* oracle uses the domain's admissible heuristic directly (no noise). Because the heuristic is admissible, A* is guaranteed to find an optimal path — the returned cost is the true minimum. Every result in the benchmark is reported as an optimality ratio: `agent_cost / a_star_cost`. A ratio of 1.000 means the agent matched the optimum exactly; a ratio of 1.012 means it was within 1.2% of the lower bound.

---

## Ablation design

The ablation replaces the stub proposer with a completely random one that assigns uniform random cost estimates. This isolates the contribution of guidance:

- **llm+search+verifier with random guidance:** search and verification still guarantee correctness (100% solve rate), but expansions balloon from 25.5 to 65.0 because the heuristic is no longer informative.
- **llm open-loop with random guidance:** no guidance + no search = 0.17 solve rate. The agent wanders randomly and gets stuck.

This 2x2 structure (search present/absent x guidance informative/random) cleanly attributes each contribution.
