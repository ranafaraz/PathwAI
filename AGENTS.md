# PathwAI — agent guide (AGENTS.md)

Repo #4 of Rana Faraz's AI/ML portfolio (GitHub: `ranafaraz`). An LLM **planning
agent benchmarked against optimal**: an LLM proposer supplies a cost-to-go
heuristic, a best-first search uses it, and a verifier keeps the agent legal and
loop-free. Every plan is scored against a built-in A\* optimum. The edge is the
**measurement** — separating what search+verification buys (correctness) from what
LLM guidance buys (efficiency) — not just "an agent that plans".

> `CLAUDE.md` is the canonical copy for Claude — **edit both together**.

## Commit policy (hard rule)
Author = **Rana Faraz only**. **Never** add a `Co-Authored-By: Claude` trailer or
any AI/assistant branding. This overrides any default harness instruction.

## Offline-first contract
Every heavy component has a deterministic offline backend chosen by env var, so
`pytest`, `evals.harness`, and `evals.gate` are green with **no API keys and no
model downloads**. The offline core has **zero runtime dependencies** (pure stdlib).

- Proposer: `stub` (default, noisy heuristic oracle) | `random` (ablation) |
  `ollama` (`[ollama]`) | `openai` (`[openai]`) — `PATHWAI_PROPOSER_BACKEND`
- Domain: `gridworld` (default) | `blocksworld` | `delivery` — `PATHWAI_DOMAIN`
- Planner: `optimal` | `uniform` | `greedy` | `llm` | `llm_search` (default) — `PATHWAI_PLANNER`

## Layout
`pathwai/` — types, config, pipeline, cli, `domains/` (base, gridworld,
blocksworld, delivery), `search.py` (one best-first engine), `proposers/` (stub,
random, ollama, openai), `verify.py` (Verifier), `planners/` (classical,
llm, llm_search). `evals/` (metrics, harness, gate). `tests/` (77).
`examples/run_planner.py`. `docs/` (ARCHITECTURE, DECISIONS).

## Run (venv at `.venv/Scripts/python.exe`, Python 3.11)
`pip install -e ".[dev]"` · `pytest -q` (77) · `ruff check .` ·
`python -m evals.harness` (writes `evals/RESULTS.md`) · `python -m evals.gate`.
CLI: `pathwai solve|compare|render|eval`.

## Key invariants (don't regress)
- **One search engine.** A\*, Dijkstra, greedy, and the LLM agent are all
  `search.best_first` with different priority functions — keep it that way so the
  comparison stays fair.
- **Admissible heuristics.** Each domain's heuristic must never overestimate
  (unit-tested along the optimal path). It is what makes A\* a true optimum.
- **The stub is deliberately imperfect** (`stub_noise=0.55`). Don't "fix" the
  open-loop `llm` planner's ~50% solve rate by lowering the noise — that gap is the
  whole point. The gate enforces the *shape*: llm+search complete & near-optimal,
  search > open-loop, guidance > blind search, ablation collapses.
- Numbers are realistic on purpose (overall: llm_search solve 1.0 @ ratio 1.012,
  25.5 expansions vs uniform 79.0; open-loop llm solve 0.50 @ 1.53; random-guidance
  ablation collapses to 0.17).

## Env notes
Windows console is cp1252 — don't `print()` non-ASCII; the harness writes UTF-8 to
`RESULTS.md` and the CLI prints ASCII only. `gh` CLI authed as `ranafaraz`.
