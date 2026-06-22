"""GridWorld: shortest-path navigation around obstacles.

State is the agent cell ``(row, col)``. The agent moves on a 4-connected grid;
walls block movement. Unit step cost makes the Manhattan distance an admissible
heuristic, so A* is provably optimal -- the yardstick every other planner is
measured against. Instances are generated deterministically from a seed and are
guaranteed solvable (verified by an internal BFS before being returned).
"""

from __future__ import annotations

import random
from collections import deque

from pathwai.domains.base import Domain
from pathwai.types import Action, State

_MOVES = (
    ("N", -1, 0),
    ("S", 1, 0),
    ("E", 0, 1),
    ("W", 0, -1),
)


class GridWorld(Domain):
    name = "gridworld"

    def __init__(
        self,
        size: int,
        walls: frozenset[tuple[int, int]],
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> None:
        self.size = size
        self.walls = walls
        self.start = start
        self.goal = goal

    # -- construction -----------------------------------------------------
    @classmethod
    def from_seed(cls, seed: int, size: int = 8, wall_density: float = 0.28) -> GridWorld:
        """Deterministically build a solvable instance for ``seed``."""
        start, goal = (0, 0), (size - 1, size - 1)
        for attempt in range(200):
            rng = random.Random((seed << 8) ^ attempt)
            walls = {
                (r, c)
                for r in range(size)
                for c in range(size)
                if (r, c) not in (start, goal) and rng.random() < wall_density
            }
            inst = cls(size, frozenset(walls), start, goal)
            if inst._reachable():
                return inst
        # Fallback: empty grid is always solvable.
        return cls(size, frozenset(), start, goal)

    def _reachable(self) -> bool:
        seen = {self.start}
        q = deque([self.start])
        while q:
            s = q.popleft()
            if s == self.goal:
                return True
            for nxt in self._neighbours(s):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        return False

    def _neighbours(self, s: tuple[int, int]) -> list[tuple[int, int]]:
        out = []
        r, c = s
        for _, dr, dc in _MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                out.append((nr, nc))
        return out

    # -- Domain contract --------------------------------------------------
    def initial_state(self) -> State:
        return self.start

    def goal_test(self, state: State) -> bool:
        return state == self.goal

    def actions(self, state: State) -> list[Action]:
        r, c = state
        out = []
        for name, dr, dc in _MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in self.walls:
                out.append(Action("move", (name,), label=f"move {name}"))
        return out

    def result(self, state: State, action: Action) -> State:
        r, c = state
        for name, dr, dc in _MOVES:
            if name == action.args[0]:
                return (r + dr, c + dc)
        raise ValueError(f"illegal action {action} in {state}")

    def heuristic(self, state: State) -> float:
        return abs(state[0] - self.goal[0]) + abs(state[1] - self.goal[1])

    def render(self, state: State) -> str:
        rows = []
        for r in range(self.size):
            row = []
            for c in range(self.size):
                cell = (r, c)
                if cell == state:
                    row.append("A")
                elif cell == self.goal:
                    row.append("G")
                elif cell in self.walls:
                    row.append("#")
                else:
                    row.append(".")
            rows.append("".join(row))
        return "\n".join(rows)
