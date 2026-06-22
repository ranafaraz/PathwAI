# Architecture

PathwAI is a small, dependency-free planning library built around one idea: a
**planner is a search with a priority function**, and the LLM's only job is to
supply that priority. Keeping that boundary sharp is what makes the five planners
directly comparable and the LLM's contribution measurable.

## Layers

```
pathwai/
  types.py          State, Action, PlanResult (+ optimality_ratio)
  config.py         env-driven Settings (offline defaults)
  domains/          the search problems
    base.py         Domain ABC: initial_state, actions, result, goal_test,
                    heuristic (admissible), render (NL view for the LLM)
    gridworld.py    navigation; heuristic = Manhattan distance
    blocksworld.py  block stacking; heuristic = # misplaced blocks
    delivery.py     courier pickup/deliver; heuristic = actions + travel chain
  search.py         best_first(domain, priority, budget) -- the one engine
  proposers/        the LLM's role, reduced to cost_to_go(state)
    stub.py         offline: true heuristic + reproducible noise
    random_proposer.py  uninformative ablation
    ollama.py / openai_proposer.py  optional, lazy, graceful fallback
  verify.py         Verifier: legality + no-revisit guardrails
  planners/         turn a domain into a PlanResult
    classical.py    optimal (A*), uniform-cost (Dijkstra), greedy best-first
    llm.py          open-loop: greedily follow the proposer, no backtracking
    llm_search.py   proposer-as-heuristic + search + verifier (the hero)
  pipeline.py       compute the A* optimum, then score a planner against it
  cli.py            solve | compare | render | eval
evals/              metrics, harness (-> RESULTS.md), gate (CI floors)
```

## The one search engine

`search.best_first` expands frontier nodes in ascending priority with a closed
set keyed on state (`best_g`) and an expansion budget. Every planner is this loop
with a different `priority(state, g)`:

| Planner | `priority(state, g)` | Property |
|---|---|---|
| optimal | `g + domain.heuristic(state)` | A\* — optimal (admissible h) |
| uniform | `g` | Dijkstra — optimal, heuristic-blind |
| greedy | `domain.heuristic(state)` | fast, suboptimal |
| llm_search | `g + proposer.cost_to_go(state)` | near-optimal; guided by the LLM |

Because the engine is shared, any difference in the results table comes from the
guidance, not from four hand-written search loops drifting apart.

## The proposer boundary

A proposer answers exactly one question — *estimated remaining cost from this
state* — so backends are interchangeable. The offline `stub` returns the domain's
true cost-to-go scaled by a deterministic, state-seeded error (`stub_noise`),
modelling an informative-but-imperfect LLM. The `random` proposer returns an
uncorrelated value (the ablation). The optional `ollama`/`openai` proposers prompt
a real model for an integer estimate and fall back to the stub on any failure.

## The verifier

The verifier is the guardrail that turns a fallible suggestion into a safe step:
it confirms an action is actually applicable and refuses to revisit an explored
state. In `llm_search` this role is played by the search's closed set (it can
abandon a misleading branch and explore another); in the open-loop `llm` planner
it is the *only* safety net — and without backtracking, a single bad suggestion
that strands the agent in a dead-end ends the episode. That asymmetry is the
experiment.

## Scoring

`pipeline.solve_instance` first runs A\* to get the **ground-truth optimal cost**,
then runs the chosen planner and attaches that cost to the `PlanResult`. The
`optimality_ratio` (plan cost ÷ optimum) is therefore anchored to a provable
baseline. The harness pools 50 seeds × 3 domains and the gate enforces the
*shape* of the result, not just nice numbers.
