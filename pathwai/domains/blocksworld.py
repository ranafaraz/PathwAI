"""Blocksworld: the canonical AI-planning benchmark.

A set of labelled blocks sit in stacks on a table; the agent moves one *clear*
block at a time onto another clear block or the table, aiming to reach a goal
configuration. The state is a normalised tuple of stacks so equivalent
arrangements hash equal. The admissible heuristic counts blocks that are not yet
correctly placed (each needs at least one move), giving A* a provable optimum on
the small instances used here.
"""

from __future__ import annotations

import random

from pathwai.domains.base import Domain
from pathwai.types import Action, State

Config = tuple  # tuple[tuple[str, ...], ...] -- sorted stacks, bottom->top


def _normalise(stacks: list[tuple[str, ...]]) -> Config:
    return tuple(sorted(s for s in stacks if s))


def _below_map(config: Config) -> dict[str, str]:
    """Map each block to what it rests on (another block or ``'table'``)."""
    below: dict[str, str] = {}
    for stack in config:
        prev = "table"
        for block in stack:
            below[block] = prev
            prev = block
    return below


class Blocksworld(Domain):
    name = "blocksworld"

    def __init__(self, start: Config, goal: Config) -> None:
        self.start = _normalise(list(start))
        self.goal = _normalise(list(goal))
        self._goal_below = _below_map(self.goal)
        self.blocks = sorted(b for stack in self.goal for b in stack)

    # -- construction -----------------------------------------------------
    @classmethod
    def from_seed(cls, seed: int, n_blocks: int = 4) -> Blocksworld:
        labels = [chr(ord("A") + i) for i in range(n_blocks)]
        rng = random.Random((seed << 8) ^ 0x5)
        start = cls._random_config(rng, labels)
        for _ in range(50):
            goal = cls._random_config(rng, labels)
            if _normalise(list(goal)) != _normalise(list(start)):
                return cls(start, goal)
        return cls(start, goal)

    @staticmethod
    def _random_config(rng: random.Random, labels: list[str]) -> Config:
        blocks = labels[:]
        rng.shuffle(blocks)
        stacks: list[tuple[str, ...]] = []
        i = 0
        while i < len(blocks):
            # Random stack height 1..3.
            h = rng.randint(1, min(3, len(blocks) - i))
            stacks.append(tuple(blocks[i : i + h]))
            i += h
        return _normalise(stacks)

    # -- Domain contract --------------------------------------------------
    def initial_state(self) -> State:
        return self.start

    def goal_test(self, state: State) -> bool:
        return state == self.goal

    def actions(self, state: State) -> list[Action]:
        config: Config = state
        tops = [stack[-1] for stack in config]
        out: list[Action] = []
        for block in tops:
            below = self._support(config, block)
            # Move onto the table (skip if already a clear singleton on table).
            if below != "table":
                out.append(Action("move", (block, "table"), label=f"move {block} -> table"))
            # Move onto another clear block.
            for dest in tops:
                if dest != block and dest != below:
                    out.append(Action("move", (block, dest), label=f"move {block} -> {dest}"))
        return out

    def result(self, state: State, action: Action) -> State:
        block, dest = action.args
        stacks = [list(s) for s in state]
        # Remove block (it is a clear top).
        for stack in stacks:
            if stack and stack[-1] == block:
                stack.pop()
                break
        if dest == "table":
            stacks.append([block])
        else:
            for stack in stacks:
                if stack and stack[-1] == dest:
                    stack.append(block)
                    break
        return _normalise([tuple(s) for s in stacks])

    def heuristic(self, state: State) -> float:
        below = _below_map(state)
        misplaced = 0
        for block in self.blocks:
            if not self._well_placed(block, below):
                misplaced += 1
        return float(misplaced)

    def render(self, state: State) -> str:
        parts = [" / ".join("".join(stack) for stack in state)]
        parts.append("goal: " + " / ".join("".join(stack) for stack in self.goal))
        return "\n".join(parts)

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _support(config: Config, block: str) -> str:
        for stack in config:
            if block in stack:
                idx = stack.index(block)
                return "table" if idx == 0 else stack[idx - 1]
        return "table"

    def _well_placed(self, block: str, below: dict[str, str]) -> bool:
        """A block is well-placed iff its whole support chain matches the goal."""
        cur = below.get(block, "table")
        target = self._goal_below.get(block, "table")
        if cur != target:
            return False
        if target == "table":
            return True
        return self._well_placed(target, below)
