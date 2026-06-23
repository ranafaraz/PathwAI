# Configuration

## Environment variables

All configuration is via environment variables. Defaults select the offline stub proposer on gridworld; no `.env` file is needed to run the pipeline, CLI, or tests.

| Variable | Default | Options | Description |
|---|---|---|---|
| `PATHWAI_PROPOSER_BACKEND` | `stub` | `stub`, `random`, `ollama`, `openai` | Proposer backend. `ollama`/`openai` require pip extras and a running service/key |
| `PATHWAI_PLANNER` | `llm_search` | `optimal`, `uniform`, `greedy`, `llm`, `llm_search` | Which planner to use for `pathwai solve` |
| `PATHWAI_DOMAIN` | `gridworld` | `gridworld`, `blocksworld`, `delivery` | Planning domain |
| `PATHWAI_SEED` | `42` | integer | Random seed for domain instance generation |
| `PATHWAI_BEAM_WIDTH` | `1` | integer | Beam width for search (1 = greedy/best-first, >1 = beam) |
| `PATHWAI_MAX_EXPANSIONS` | `500` | integer | Node expansion budget per instance |
| `PATHWAI_STUB_NOISE` | `0.55` | float | Noise std multiplier for stub proposer (do not reduce: intentionally imperfect) |
| `OPENAI_API_KEY` | — | string | Required only for `openai` proposer backend |
| `PATHWAI_OLLAMA_URL` | `http://localhost:11434` | URL | Required only for `ollama` proposer backend |
| `PATHWAI_OLLAMA_MODEL` | `llama3` | string | Ollama model name |

---

## Backend matrix

| Component | Offline default | Optional real backend | Install |
|---|---|---|---|
| Proposer | `stub` (noisy heuristic, deterministic) | `ollama` (local LLM via Ollama) | `pip install "pathwai[ollama]"` |
| Proposer | `stub` | `openai` (GPT via API) | `pip install "pathwai[openai]"` |
| Proposer | — | `random` (ablation, no install needed) | built-in |
| Domain | `gridworld` | `blocksworld`, `delivery` | built-in |
| Planner | `llm_search` | all five built-in | built-in |

Optional backends degrade gracefully: if Ollama is not running, PathwAI warns and falls back to `stub`. If the OpenAI key is missing, same fallback.

---

## .env.example

```bash
# Copy to .env and fill in for real LLM backends.
# Everything works offline without this file.

# Proposer backend (default: stub)
# PATHWAI_PROPOSER_BACKEND=ollama
# PATHWAI_PROPOSER_BACKEND=openai

# Ollama settings (only if using ollama backend)
# PATHWAI_OLLAMA_URL=http://localhost:11434
# PATHWAI_OLLAMA_MODEL=llama3

# OpenAI settings (only if using openai backend)
# OPENAI_API_KEY=sk-...

# Domain and planner
PATHWAI_DOMAIN=gridworld
PATHWAI_PLANNER=llm_search
PATHWAI_SEED=42
PATHWAI_MAX_EXPANSIONS=500
```

---

## Docker

```bash
# Offline run (stub proposer, gridworld)
docker build -t pathwai .
docker run --rm pathwai

# With Ollama backend (requires Ollama running on host)
docker run --rm \
  -e PATHWAI_PROPOSER_BACKEND=ollama \
  -e PATHWAI_OLLAMA_URL=http://host.docker.internal:11434 \
  pathwai

# With OpenAI backend
docker run --rm \
  -e PATHWAI_PROPOSER_BACKEND=openai \
  -e OPENAI_API_KEY=sk-... \
  pathwai
```
