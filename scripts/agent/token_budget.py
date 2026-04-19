"""
Token budget utilities for the agent approval policy and tooling.

Provides real token counting (via tiktoken) and cost estimation so that
the pretool approval hook and CI scripts can enforce actual budget limits
rather than relying on self-reported LLM token counts.

Usage (as a library):
    from scripts.agent.token_budget import count_tokens, estimate_cost, BudgetTracker

Usage (as a CLI):
    python scripts/agent/token_budget.py count "some text" --model gpt-4o
    python scripts/agent/token_budget.py cost 1000 200 --model gpt-4o
    python scripts/agent/token_budget.py session --session-file /tmp/budget.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pricing table (USD per 1 000 tokens, [input, output])
# Updated manually when provider prices change.
# ---------------------------------------------------------------------------
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o":               (0.0025,  0.010),
    "gpt-4o-mini":          (0.00015, 0.0006),
    "gpt-4.1":              (0.002,   0.008),
    "gpt-4.1-mini":         (0.0004,  0.0016),
    "o4-mini":              (0.0011,  0.0044),
    "claude-opus-4":        (0.015,   0.075),
    "claude-sonnet-4":      (0.003,   0.015),
    "claude-haiku-4":       (0.0008,  0.004),
    "gemini-2.5-pro":       (0.00125, 0.010),
    "gemini-2.5-flash":     (0.00015, 0.0006),
}

# Default budget ceiling per task (USD). Can be overridden via
# AGENT_TASK_BUDGET_USD env var or --budget flag.
DEFAULT_TASK_BUDGET_USD = float(os.environ.get("AGENT_TASK_BUDGET_USD", "2.00"))

# Default token ceiling per task. Triggers an escalation warning before the
# cost ceiling is reached. Can be overridden via AGENT_TASK_TOKEN_CEILING env var.
DEFAULT_TOKEN_CEILING = int(os.environ.get("AGENT_TASK_TOKEN_CEILING", "200000"))


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Return the real token count of *text* for *model*.

    Falls back to a conservative character-based estimate (÷3.5) when
    tiktoken is not installed, emitting a warning to stderr.
    """
    try:
        import tiktoken  # type: ignore[import-untyped]
    except ImportError:
        _warn(
            "tiktoken is not installed. Using character-based estimate (÷3.5). "
            "Install with: pip install tiktoken"
        )
        return max(1, int(len(text) / 3.5))

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        # Unknown model → fall back to cl100k_base
        enc = tiktoken.get_encoding("cl100k_base")

    return len(enc.encode(text))


def estimate_cost(tokens_in: int, tokens_out: int, model: str = "gpt-4o") -> float:
    """Return estimated USD cost for *tokens_in* input and *tokens_out* output.

    Uses the MODEL_PRICES table. Unknown models use a conservative default.
    """
    in_price, out_price = MODEL_PRICES.get(model, (0.005, 0.020))
    return (tokens_in / 1000 * in_price) + (tokens_out / 1000 * out_price)


def check_budget(
    tokens_in: int,
    tokens_out: int,
    model: str = "gpt-4o",
    budget_usd: float = DEFAULT_TASK_BUDGET_USD,
    token_ceiling: int = DEFAULT_TOKEN_CEILING,
) -> dict[str, Any]:
    """Check whether a usage report is within budget.

    Returns a dict with keys:
      - within_budget: bool
      - within_token_ceiling: bool
      - estimated_cost_usd: float
      - total_tokens: int
      - budget_usd: float
      - token_ceiling: int
      - action: "continue" | "warn" | "escalate" | "abort"
    """
    cost = estimate_cost(tokens_in, tokens_out, model)
    total_tokens = tokens_in + tokens_out

    if cost >= budget_usd or total_tokens >= token_ceiling:
        action = "abort"
    elif cost >= budget_usd * 0.8 or total_tokens >= int(token_ceiling * 0.8):
        action = "escalate"
    elif cost >= budget_usd * 0.5 or total_tokens >= int(token_ceiling * 0.5):
        action = "warn"
    else:
        action = "continue"

    return {
        "within_budget": cost < budget_usd,
        "within_token_ceiling": total_tokens < token_ceiling,
        "estimated_cost_usd": round(cost, 6),
        "total_tokens": total_tokens,
        "budget_usd": budget_usd,
        "token_ceiling": token_ceiling,
        "action": action,
    }


# ---------------------------------------------------------------------------
# Session-level budget tracker (persists to a JSON file)
# ---------------------------------------------------------------------------

class BudgetTracker:
    """Lightweight file-backed cumulative token / cost tracker for a session.

    Typical usage inside the pretool hook or CI scripts:

        tracker = BudgetTracker("/tmp/agent-budget.json")
        result = tracker.record(tokens_in=500, tokens_out=200, model="gpt-4o")
        if result["action"] in ("escalate", "abort"):
            # emit an ask or deny decision

    The file is created on first write and updated atomically (write-then-rename).
    """

    def __init__(
        self,
        path: str | Path = "/tmp/agent-budget.json",
        budget_usd: float = DEFAULT_TASK_BUDGET_USD,
        token_ceiling: int = DEFAULT_TOKEN_CEILING,
    ) -> None:
        self.path = Path(path)
        self.budget_usd = budget_usd
        self.token_ceiling = token_ceiling
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "created_at": time.time(),
                "entries": [],
                "cumulative_tokens_in": 0,
                "cumulative_tokens_out": 0,
                "cumulative_cost_usd": 0.0,
                "tool_call_count": 0,
            }

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2))
        tmp.replace(self.path)

    def record(
        self,
        tokens_in: int = 0,
        tokens_out: int = 0,
        model: str = "gpt-4o",
        label: str = "",
    ) -> dict[str, Any]:
        """Record a usage event and return the current budget status."""
        cost = estimate_cost(tokens_in, tokens_out, model)
        self._data["cumulative_tokens_in"] += tokens_in
        self._data["cumulative_tokens_out"] += tokens_out
        self._data["cumulative_cost_usd"] = round(
            self._data["cumulative_cost_usd"] + cost, 6
        )
        self._data["entries"].append(
            {
                "ts": time.time(),
                "label": label,
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost, 6),
            }
        )
        self._save()
        return check_budget(
            self._data["cumulative_tokens_in"],
            self._data["cumulative_tokens_out"],
            model=model,
            budget_usd=self.budget_usd,
            token_ceiling=self.token_ceiling,
        )

    def increment_tool_call(self) -> int:
        """Increment and return the tool call count."""
        self._data["tool_call_count"] = self._data.get("tool_call_count", 0) + 1
        self._save()
        return self._data["tool_call_count"]

    @property
    def tool_call_count(self) -> int:
        return int(self._data.get("tool_call_count", 0))

    @property
    def cumulative_cost_usd(self) -> float:
        return float(self._data.get("cumulative_cost_usd", 0.0))

    def summary(self) -> dict[str, Any]:
        return {
            "cumulative_tokens_in":  self._data["cumulative_tokens_in"],
            "cumulative_tokens_out": self._data["cumulative_tokens_out"],
            "cumulative_cost_usd":   self._data["cumulative_cost_usd"],
            "tool_call_count":       self._data.get("tool_call_count", 0),
            "entry_count":           len(self._data["entries"]),
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _warn(msg: str) -> None:
    print(f"WARNING: {msg}", file=sys.stderr)


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent token budget utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # count
    p_count = sub.add_parser("count", help="Count tokens in text")
    p_count.add_argument("text", help="Text to count tokens in")
    p_count.add_argument("--model", default="gpt-4o", help="Model name")

    # cost
    p_cost = sub.add_parser("cost", help="Estimate cost for token counts")
    p_cost.add_argument("tokens_in", type=int)
    p_cost.add_argument("tokens_out", type=int)
    p_cost.add_argument("--model", default="gpt-4o")
    p_cost.add_argument(
        "--budget", type=float, default=DEFAULT_TASK_BUDGET_USD,
        help="Task budget ceiling in USD"
    )

    # session summary
    p_session = sub.add_parser("session", help="Print session budget summary")
    p_session.add_argument(
        "--session-file",
        default="/tmp/agent-budget.json",
        help="Path to the session budget file",
    )

    return parser


def main() -> int:
    parser = _build_cli()
    args = parser.parse_args()

    if args.cmd == "count":
        n = count_tokens(args.text, model=args.model)
        print(n)

    elif args.cmd == "cost":
        result = check_budget(
            args.tokens_in,
            args.tokens_out,
            model=args.model,
            budget_usd=args.budget,
        )
        print(json.dumps(result, indent=2))

    elif args.cmd == "session":
        tracker = BudgetTracker(path=args.session_file)
        print(json.dumps(tracker.summary(), indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
