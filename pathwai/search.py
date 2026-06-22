"""A single best-first search engine that every planner reuses.

The only thing that changes between A*, uniform-cost (Dijkstra), greedy
best-first, and the LLM-guided agent is the **priority function** -- the number
that decides which frontier node to expand next. Sharing one well-tested engine
keeps the planner comparison honest: differences in the results come from the
guidance, not from four subtly different search loops.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable

from pathwai.domains.base import Domain
from pathwai.types import Action, State

# priority(state, g_cost) -> float. Lower is expanded first.
Priority = Callable[[State, float], float]


class SearchOutcome:
    """Result of one search: the plan, its cost, effort, and whether it solved."""

    __slots__ = ("plan", "cost", "expansions", "solved")

    def __init__(
        self, plan: list[Action], cost: float, expansions: int, solved: bool
    ) -> None:
        self.plan = plan
        self.cost = cost
        self.expansions = expansions
        self.solved = solved


def _reconstruct(came_from: dict, goal: State) -> list[Action]:
    plan: list[Action] = []
    s = goal
    while True:
        prev, action = came_from[s]
        if prev is None:
            break
        plan.append(action)
        s = prev
    plan.reverse()
    return plan


def best_first(domain: Domain, priority: Priority, max_expansions: int) -> SearchOutcome:
    """Expand nodes in ascending ``priority`` until the goal is reached or budget
    runs out. With an admissible+consistent priority (``g + h``) this is A* and is
    optimal; with ``g`` alone it is Dijkstra; with ``h`` alone it is greedy."""
    start = domain.initial_state()
    best_g: dict[State, float] = {start: 0.0}
    came_from: dict[State, tuple] = {start: (None, None)}
    counter = 0
    frontier: list[tuple[float, int, float, State]] = [(priority(start, 0.0), 0, 0.0, start)]
    expansions = 0

    while frontier:
        _, _, g, state = heapq.heappop(frontier)
        if g > best_g.get(state, float("inf")):
            continue  # stale entry superseded by a cheaper path
        if domain.goal_test(state):
            return SearchOutcome(_reconstruct(came_from, state), g, expansions, True)
        if expansions >= max_expansions:
            break
        expansions += 1
        for action in domain.actions(state):
            nxt = domain.result(state, action)
            ng = g + domain.step_cost(state, action)
            if ng < best_g.get(nxt, float("inf")):
                best_g[nxt] = ng
                came_from[nxt] = (state, action)
                counter += 1
                heapq.heappush(frontier, (priority(nxt, ng), counter, ng, nxt))

    return SearchOutcome([], float("inf"), expansions, False)


def astar(domain: Domain, max_expansions: int) -> SearchOutcome:
    """Optimal search with the domain's admissible heuristic."""
    return best_first(domain, lambda s, g: g + domain.heuristic(s), max_expansions)
