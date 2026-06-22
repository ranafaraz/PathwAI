"""Proposer backends: determinism, the ablation, and graceful fallback."""

from __future__ import annotations

from pathwai.config import Settings
from pathwai.domains import make_domain
from pathwai.proposers import get_proposer
from pathwai.proposers.base import stable_unit
from pathwai.proposers.stub import StubProposer


def test_stable_unit_is_deterministic_and_bounded():
    a = stable_unit(("gridworld", 7, (1, 2)))
    b = stable_unit(("gridworld", 7, (1, 2)))
    assert a == b
    assert 0.0 <= a < 1.0
    assert stable_unit(("x",)) != stable_unit(("y",))


def test_stub_is_zero_at_goal_and_deterministic():
    domain = make_domain("gridworld", 2)
    stub = StubProposer(noise=0.5, seed=2)
    goal = domain.goal  # gridworld exposes its goal cell
    assert stub.cost_to_go(domain, goal) == 0.0
    state = domain.initial_state()
    assert stub.cost_to_go(domain, state) == stub.cost_to_go(domain, state)


def test_stub_tracks_heuristic_within_noise_band():
    domain = make_domain("delivery", 3)
    noise = 0.5
    stub = StubProposer(noise=noise, seed=3)
    state = domain.initial_state()
    h = domain.heuristic(state)
    est = stub.cost_to_go(domain, state)
    assert (1 - noise) * h - 1e-9 <= est <= (1 + noise) * h + 1e-9


def test_factory_resolves_offline_backends():
    cfg = Settings.from_env()
    cfg.proposer_backend = "stub"
    assert get_proposer(cfg).name == "stub"
    cfg.proposer_backend = "random"
    assert get_proposer(cfg).name == "random"


def test_optional_backends_fall_back_to_stub_offline(recwarn):
    # With no server/key/deps, real backends must degrade, not crash.
    from pathwai.proposers.ollama import OllamaProposer

    domain = make_domain("gridworld", 1)
    val = OllamaProposer().cost_to_go(domain, domain.initial_state())
    assert val >= 0.0
