"""Token budget estimator for the agent hook system.

Prefers ``tiktoken`` (cl100k_base) when installed for accurate counts; falls
back to a character-count heuristic (``chars // 4``) when tiktoken is missing
or raises. The fallback path is intentionally dependency-free so the hook
environment continues to work in stripped-down installs.
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


def _tiktoken_available() -> bool:
    """Return True if tiktoken can be imported. Used by tests."""
    try:
        import tiktoken  # noqa: F401
    except ImportError:
        return False
    return True


def estimate_tokens(text: str) -> int:
    """Estimate token count for ``text``.

    Uses ``tiktoken.get_encoding("cl100k_base")`` when available. Any
    failure (missing dependency, encoding error, etc.) falls through to the
    char/4 heuristic so the caller never raises.
    """
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return max(1, len(enc.encode(text)))
    except (ImportError, Exception):  # noqa: BLE001 - intentional broad fallback
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
    backend = "tiktoken (cl100k_base)" if _tiktoken_available() else "fallback (chars/4)"
    if args.estimate is None:
        print(f"backend: {backend}")
        parser.print_usage()
        return 0
    print(f"backend: {backend}")
    print(estimate_tokens(args.estimate))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
