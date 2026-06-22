"""Verifier guardrails, PlanResult arithmetic, and the CLI entry points."""

from __future__ import annotations

from pathwai.cli import main as cli_main
from pathwai.domains import make_domain
from pathwai.types import Action, PlanResult
from pathwai.verify import Verifier


def test_verifier_rejects_illegal_and_revisited():
    domain = make_domain("gridworld", 0)
    v = Verifier()
    state = domain.initial_state()
    legal = domain.actions(state)[0]
    assert v.is_legal(domain, state, legal)
    assert not v.is_legal(domain, state, Action("move", ("nowhere",)))
    v.visit(state)
    assert not v.is_progress(state)  # revisiting an explored state
    assert v.rejections == 2


def test_plan_result_optimality_ratio():
    solved = PlanResult("d", "p", solved=True, plan=[Action("a")], cost=6.0, optimal_cost=4.0)
    assert solved.optimality_ratio == 1.5
    assert solved.steps == 1
    unsolved = PlanResult("d", "p", solved=False, optimal_cost=4.0)
    assert unsolved.optimality_ratio is None


def test_cli_solve_runs(capsys):
    assert cli_main(["solve", "--domain", "blocksworld", "--seed", "1"]) == 0
    out = capsys.readouterr().out
    assert "PathwAI" in out and "solved" in out


def test_cli_compare_runs(capsys):
    assert cli_main(["compare", "--domain", "gridworld", "--seed", "2"]) == 0
    out = capsys.readouterr().out
    assert "llm_search" in out and "optimal" in out


def test_cli_render_runs(capsys):
    assert cli_main(["render", "--domain", "delivery", "--seed", "0"]) == 0
    assert "PathwAI" in capsys.readouterr().out
