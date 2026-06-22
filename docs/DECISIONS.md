# Design decisions

What I chose, and why — the trade-offs behind PathwAI.

## 1. Reduce the LLM to a scalar `cost_to_go`
An LLM agent can be modelled many ways (next-action policy, full-plan generator,
critic). I chose **heuristic estimator**: given a state, estimate remaining cost.
- *Why:* it slots a language model into classical search as a drop-in heuristic,
  which makes the LLM's contribution measurable on the same axes as A\* and
  Dijkstra. A free-form "generate a plan" interface would conflate proposing,
  searching, and verifying into one opaque call you can't ablate.
- *Cost:* it underuses a real LLM's structured-reasoning ability. The interface is
  deliberately minimal; richer proposers (action rankings, subgoal decomposition)
  are a natural extension.

## 2. One search engine, four priority functions
A\*, uniform-cost, greedy, and the LLM agent are the *same* `best_first` loop.
- *Why:* the comparison has to be fair. If each planner had its own loop, a
  difference in expansions could be an implementation artefact. Sharing the engine
  means the only independent variable is the priority function.

## 3. A deliberately *noisy* offline stub
The stub returns the true heuristic times a reproducible per-state error
(`stub_noise = 0.55`). It would have been easier to return the exact heuristic.
- *Why:* a perfect stub makes the open-loop agent succeed every time and erases
  the whole thesis. Real LLMs are informative but wrong sometimes; the noise
  reproduces that, so the open-loop agent honestly fails ~half the time and the
  search+verifier agent visibly rescues it. The gap *is* the product.
- *Honesty:* the noise is calibrated once and left fixed; it is not tuned per
  domain to flatter a metric. The same value drives all three domains.

## 4. Admissible heuristics, unit-tested
Every domain's heuristic is an admissible lower bound, checked along each optimal
path (`h(s) ≤ remaining optimal cost`).
- *Why:* admissibility is what makes A\* a *true* optimum, and the optimum is the
  denominator of every reported ratio. A non-admissible heuristic would silently
  turn "optimality ratio" into "ratio vs. some heuristic's guess."

## 5. The random-proposer ablation as the "null test"
Mirroring a good empirical paper, PathwAI ships a null: replace the stub with
uninformative guidance and re-run.
- *Why:* it dissociates the two effects. Open-loop collapses (guidance was doing
  the work); search+verifier still solves everything but expands far more nodes
  (guidance bought efficiency, search bought correctness). Without the null, a
  reader can't tell which component earns its keep.

## 6. Zero runtime dependencies for the offline core
The core is pure standard library; `numpy`/`requests`/`openai` are not required.
- *Why:* fast, reproducible CI with nothing to download, and the planning logic
  stays legible. Real backends are opt-in extras, lazily imported.

## 7. Small instances on purpose
Grids are 8×8, Blocksworld uses 4 blocks, Delivery uses 2 packages on a 5×5 grid.
- *Why:* the point is the *comparison against optimal*, which requires actually
  computing the optimum. Small, exhaustively-solvable instances keep A\* exact and
  the whole 150-instance benchmark sub-second. Scaling the domains is orthogonal to
  the thesis and would trade exact optima for approximate ones.

## 8. CI gate enforces the *shape*, not just thresholds
The gate checks A\* is optimal, llm+search is complete and near-optimal, search
beats open-loop, guidance beats blind search, and the ablation collapses.
- *Why:* a plain "Sharpe ≥ X" style floor can pass while the story silently breaks
  (e.g. the verifier regresses but absolute numbers stay high). Gating the
  *relationships* between planners catches regressions a single threshold misses.
