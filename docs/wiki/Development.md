# Development

## Prerequisites

- Python 3.10, 3.11, or 3.12
- Git
- (Optional) Docker for the one-command run
- (Optional) Ollama for local LLM proposer backend

---

## Setup

```bash
git clone https://github.com/ranafaraz/PathwAI.git
cd PathwAI

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

The `[dev]` extra includes pytest, ruff, and all test dependencies. No LLM extras are needed for development — the stub proposer is built-in.

---

## Running tests

```bash
pytest -q                        # 77 tests, all offline
pytest tests/test_search.py      # search engine tests
pytest tests/test_domains.py     # domain + heuristic admissibility
pytest tests/test_verifier.py    # verifier tests
pytest tests/ -k "gridworld"     # filter by keyword
```

Key invariants enforced by the test suite:

- **One search engine:** all planners use `search.best_first`; tests verify no planner bypasses it
- **Heuristic admissibility:** for each domain, `heuristic(state) <= actual_cost_to_goal(state)` checked along every optimal path
- **Stub is imperfect:** the open-loop llm planner's solve rate is verified to be < 0.8 across 50 seeds (the gate enforces the shape, not inflated numbers)
- **Verifier rejects revisits and illegal moves:** tested explicitly with constructed bad proposals

---

## Linting

```bash
ruff check .
ruff format .
```

---

## Full evaluation

```bash
python -m evals.harness          # full benchmark across 150 instances, writes evals/RESULTS.md
python -m evals.gate             # quality gate; exits non-zero on failure
```

CI runs both on every push. Do not manually edit `evals/RESULTS.md` — it is generated.

---

## Code layout

```
pathwai/
    __init__.py
    types.py            State, Action, Plan, PlanResult, BenchmarkRow
    config.py           env-var loading, defaults
    pipeline.py         run_benchmark(), run_instance()
    cli.py              Click commands (solve, compare, render, eval)

    domains/
        base.py         Domain ABC
        gridworld.py    GridWorld domain
        blocksworld.py  Blocksworld domain
        delivery.py     Delivery domain

    search.py           best_first(domain, proposer, verifier, priority_fn) -> Plan
    verify.py           Verifier: check_legal(), check_not_visited()

    proposers/
        base.py         Proposer ABC: estimate(state, domain) -> float
        stub.py         StubProposer: heuristic + noise
        random_.py      RandomProposer: uniform random estimate
        ollama.py       OllamaProposer (lazy import)
        openai.py       OpenAIProposer (lazy import)

    planners/
        classical.py    optimal(), uniform(), greedy() — priority_fn wrappers
        llm.py          LLMPlanner: open-loop, no search
        llm_search.py   LLMSearchPlanner: search + verifier

evals/
    harness.py
    gate.py
    RESULTS.md          (generated)

tests/
    test_domains.py     domain correctness + heuristic admissibility
    test_search.py      best_first engine
    test_verifier.py    Verifier
    test_proposers.py   stub, random
    test_planners.py    all five planners, small instances
    test_pipeline.py    end-to-end
    test_cli.py         CLI commands
    ... (77 total)

docs/
    ARCHITECTURE.md
    DECISIONS.md
    demo.gif
```

---

## Adding a new domain

1. Create `pathwai/domains/mydomain.py` subclassing `Domain`:

```python
from pathwai.domains.base import Domain
from pathwai.types import State, Action

class MyDomain(Domain):
    def initial_state(self, seed: int) -> State: ...
    def applicable_actions(self, state: State) -> list[Action]: ...
    def apply(self, state: State, action: Action) -> State: ...
    def is_goal(self, state: State) -> bool: ...
    def heuristic(self, state: State) -> float: ...  # must be admissible
    def render(self, state: State) -> str: ...
    def optimal_cost(self, seed: int) -> float: ...
```

2. Register in `pathwai/domains/__init__.py` under the `PATHWAI_DOMAIN` key.

3. Add admissibility tests: for every step of an optimal path, assert `heuristic(state) <= remaining_cost`.

4. Add domain to the benchmark loop in `evals/harness.py`.

---

## Adding a new proposer backend

1. Create `pathwai/proposers/myproposer.py`:

```python
from pathwai.proposers.base import Proposer
from pathwai.types import State
from pathwai.domains.base import Domain

class MyProposer(Proposer):
    def estimate(self, state: State, domain: Domain) -> float:
        """Return estimated cost-to-go (lower = better)."""
        ...
```

2. Register in `pathwai/proposers/__init__.py`:

```python
def get_proposer(backend: str) -> Proposer:
    if backend == "myproposer":
        from .myproposer import MyProposer
        return MyProposer()
    ...
```

3. Add a lazy-import guard: if the required dependency is missing, log a warning and fall back to `stub`.

4. Add tests in `tests/test_proposers.py` verifying the output range and offline/fallback behavior.
