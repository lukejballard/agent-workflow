"""Token budget estimator for the agent hook system.

Uses a character-count heuristic (chars / 4) as an approximation.
This is intentionally simple because the hook environment has no external
dependencies. For a production system, replace this with tiktoken.
"""
from __future__ import annotations

import argparse
import json
import os

from session_schema import SessionState

CHARS_PER_TOKEN = 4


def get_budget() -> int:
    return int(os.environ.get("AGENT_TOKEN_BUDGET", "150000"))


DEFAULT_BUDGET = get_budget()


def estimate_tokens(text: str) -> int:
    """Estimate token count from character count. Approximation only."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def get_session_token_usage(state: SessionState) -> int:
    """Return cumulative estimated token usage for this session."""
    return state.estimated_tokens_used


def record_token_usage(
    state: SessionState, tool_name: str, tool_input: dict[str, object]
) -> int:
    """Add estimated tokens from tool_input to the session total."""
    try:
        payload_text = json.dumps(tool_input, sort_keys=True)
    except (TypeError, ValueError):
        payload_text = str(tool_input)
    new_tokens = estimate_tokens(payload_text)
    state.estimated_tokens_used = get_session_token_usage(state) + new_tokens
    phase = getattr(state, "current_phase", "unknown") or "unknown"
    costs = dict(state.phase_token_costs)
    costs[phase] = costs.get(phase, 0) + new_tokens
    state.phase_token_costs = costs
    del tool_name
    return state.estimated_tokens_used


def check_budget(
    state: SessionState, budget: int | None = None
) -> tuple[bool, float, int]:
    """Check whether session usage is within the estimated budget."""
    limit = get_budget() if budget is None else budget
    used = get_session_token_usage(state)
    utilization = (used / limit) * 100 if limit > 0 else 0.0
    return used < limit, utilization, used


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="token_budget.py")
    parser.add_argument("--estimate", help="Estimate tokens for a string")
    args = parser.parse_args(argv)
    if args.estimate is None:
        parser.print_usage()
        return 0
    print(estimate_tokens(args.estimate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
