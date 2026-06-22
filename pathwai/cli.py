"""``pathwai`` command-line interface.

Console output is ASCII-only on purpose (the Windows console is cp1252). The
eval harness writes its richer, Unicode-friendly tables to a file instead.
"""

from __future__ import annotations

import argparse
import sys

from pathwai.config import Settings
from pathwai.domains import DOMAINS, make_domain
from pathwai.pipeline import optimal_cost_of, solve_instance
from pathwai.planners import PLANNERS


def _cfg(args: argparse.Namespace) -> Settings:
    cfg = Settings.from_env()
    if getattr(args, "domain", None):
        cfg.domain = args.domain
    if getattr(args, "seed", None) is not None:
        cfg.seed = args.seed
    if getattr(args, "backend", None):
        cfg.proposer_backend = args.backend
    return cfg


def _cmd_solve(args: argparse.Namespace) -> int:
    cfg = _cfg(args)
    planner = args.planner or cfg.planner
    domain = make_domain(cfg.domain, cfg.seed)
    res = solve_instance(domain, cfg, planner)

    print(f"PathwAI :: {domain.name} (seed {cfg.seed}) :: planner={planner}")
    print("-" * 56)
    print(domain.render(domain.initial_state()))
    print("-" * 56)
    if res.solved:
        for i, action in enumerate(res.plan, 1):
            print(f"  {i:2d}. {action}")
        ratio = res.optimality_ratio
        print("-" * 56)
        print(f"  solved      : yes ({res.steps} steps, cost {res.cost:g})")
        print(f"  optimal cost: {res.optimal_cost}")
        print(f"  optimality  : {'n/a' if ratio is None else format(ratio, '.3f')}")
        print(f"  expansions  : {res.expansions}")
    else:
        print("  solved      : NO (budget exhausted or dead-end)")
        print(f"  expansions  : {res.expansions}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    cfg = _cfg(args)
    domain = make_domain(cfg.domain, cfg.seed)
    opt = optimal_cost_of(domain, cfg.max_expansions)
    print(f"PathwAI :: {domain.name} (seed {cfg.seed}) :: backend={cfg.proposer_backend}")
    print(f"optimal cost = {opt}")
    print(f"{'planner':<12} {'solved':>6} {'steps':>6} {'opt.ratio':>10} {'expansions':>11}")
    for name in PLANNERS:
        res = solve_instance(domain, cfg, name)
        ratio = res.optimality_ratio
        ratio_s = "-" if ratio is None else f"{ratio:.3f}"
        solved_s = "yes" if res.solved else "no"
        print(f"{name:<12} {solved_s:>6} {res.steps:>6} {ratio_s:>10} {res.expansions:>11}")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    cfg = _cfg(args)
    domain = make_domain(cfg.domain, cfg.seed)
    print(f"PathwAI :: {domain.name} (seed {cfg.seed})")
    print(domain.render(domain.initial_state()))
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    from evals.harness import main as eval_main

    return eval_main()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pathwai",
        description="Deliberate LLM planning, benchmarked against optimal.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--domain", choices=DOMAINS, help="planning domain")
    common.add_argument("--seed", type=int, help="instance seed")
    common.add_argument("--backend", help="proposer backend (stub|random|ollama|openai)")

    s = sub.add_parser("solve", parents=[common], help="solve one instance with one planner")
    s.add_argument("--planner", choices=PLANNERS, help="planner to run")
    s.set_defaults(func=_cmd_solve)

    c = sub.add_parser("compare", parents=[common], help="compare all planners on one instance")
    c.set_defaults(func=_cmd_compare)

    r = sub.add_parser("render", parents=[common], help="print an instance")
    r.set_defaults(func=_cmd_render)

    e = sub.add_parser("eval", help="run the full offline eval harness")
    e.set_defaults(func=_cmd_eval)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
