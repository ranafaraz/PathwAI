"""Delivery: a courier picking up and dropping off packages on a grid.

The agent moves on an open grid and must ``pickup`` each package at its origin
then ``deliver`` it at its destination. State is ``(pos, pending, carried)`` where
``pending``/``carried`` are frozensets of package indices. The heuristic sums two
disjoint admissible lower bounds -- the exact count of remaining pickup/deliver
actions, plus the longest single remaining travel chain -- so A* stays optimal
while the task interleaves navigation with ordering decisions (a mini-TSP).
"""

from __future__ import annotations

import random

from pathwai.domains.base import Domain
from pathwai.types import Action, State

_MOVES = (
    ("N", -1, 0),
    ("S", 1, 0),
    ("E", 0, 1),
    ("W", 0, -1),
)


def _dist(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Delivery(Domain):
    name = "delivery"

    def __init__(
        self,
        size: int,
        start: tuple[int, int],
        pickups: tuple[tuple[int, int], ...],
        dropoffs: tuple[tuple[int, int], ...],
    ) -> None:
        self.size = size
        self.start = start
        self.pickups = pickups
        self.dropoffs = dropoffs
        self.n = len(pickups)

    @classmethod
    def from_seed(cls, seed: int, size: int = 5, n_packages: int = 2) -> Delivery:
        rng = random.Random((seed << 8) ^ 0xD)
        cells = [(r, c) for r in range(size) for c in range(size)]
        start = (size // 2, size // 2)
        picks: list[tuple[int, int]] = []
        drops: list[tuple[int, int]] = []
        used = {start}
        for _ in range(n_packages):
            p = rng.choice([c for c in cells if c not in used])
            used.add(p)
            d = rng.choice([c for c in cells if c not in used])
            used.add(d)
            picks.append(p)
            drops.append(d)
        return cls(size, start, tuple(picks), tuple(drops))

    # -- Domain contract --------------------------------------------------
    def initial_state(self) -> State:
        return (self.start, frozenset(range(self.n)), frozenset())

    def goal_test(self, state: State) -> bool:
        _, pending, carried = state
        return not pending and not carried

    def actions(self, state: State) -> list[Action]:
        pos, pending, carried = state
        out: list[Action] = []
        r, c = pos
        for name, dr, dc in _MOVES:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                out.append(Action("move", (name,), label=f"move {name}"))
        for i in pending:
            if pos == self.pickups[i]:
                out.append(Action("pickup", (i,), label=f"pickup #{i}"))
        for i in carried:
            if pos == self.dropoffs[i]:
                out.append(Action("deliver", (i,), label=f"deliver #{i}"))
        return out

    def result(self, state: State, action: Action) -> State:
        pos, pending, carried = state
        if action.name == "move":
            r, c = pos
            for name, dr, dc in _MOVES:
                if name == action.args[0]:
                    return ((r + dr, c + dc), pending, carried)
        elif action.name == "pickup":
            i = action.args[0]
            return (pos, pending - {i}, carried | {i})
        elif action.name == "deliver":
            i = action.args[0]
            return (pos, pending, carried - {i})
        raise ValueError(f"illegal action {action} in {state}")

    def heuristic(self, state: State) -> float:
        pos, pending, carried = state
        action_lb = 2 * len(pending) + len(carried)
        move_lb = 0
        for i in pending:
            chain = _dist(pos, self.pickups[i]) + _dist(self.pickups[i], self.dropoffs[i])
            move_lb = max(move_lb, chain)
        for i in carried:
            move_lb = max(move_lb, _dist(pos, self.dropoffs[i]))
        return float(action_lb + move_lb)

    def render(self, state: State) -> str:
        pos, pending, carried = state
        grid = [["." for _ in range(self.size)] for _ in range(self.size)]
        for i in pending:
            pr, pc = self.pickups[i]
            grid[pr][pc] = str(i)
        for i in pending | carried:
            dr, dc = self.dropoffs[i]
            if grid[dr][dc] == ".":
                grid[dr][dc] = chr(ord("a") + i)
        grid[pos[0]][pos[1]] = "C"
        body = "\n".join("".join(row) for row in grid)
        legend = f"carrying={sorted(carried)} pending={sorted(pending)}"
        return f"{body}\n{legend}"
