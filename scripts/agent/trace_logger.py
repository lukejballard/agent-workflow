"""Execution trace logger — per-run structured event log (P4.3).

Produces an append-only JSON event log compatible with the OpenTelemetry span
format (simplified) and readable by Phoenix (Arize AI) / LangSmith.

Storage: ``docs/runs/{run_id}/trace.json``

Each trace file contains:
  {
    "run_id": "...",
    "trace_id": "...",
    "started_at": 1234567890.123,
    "finished_at": null | float,
    "status": "running" | "done" | "failed" | "aborted",
    "events": [
      {
        "event_id": "...",
        "event_type": "phase_transition" | "tool_call" | "decision" | "verification" | "error",
        "timestamp": float,
        "phase": "...",
        "context_snapshot_id": null | str,
        "inputs": {...},
        "outputs": {...},
        "model_used": null | str,
        "token_usage": {"tokens_in": int, "tokens_out": int},
        "decision_rationale": null | str
      },
      ...
    ]
  }

CLI:
  python scripts/agent/trace_logger.py start [--run-id <id>]
  python scripts/agent/trace_logger.py event  --run-id <id> --type <type> [--phase <p>]
      [--inputs '{"key":"val"}'] [--outputs '{"key":"val"}']
      [--model <model>] [--tokens-in <n>] [--tokens-out <n>]
      [--rationale "..."] [--snapshot-id <id>]
  python scripts/agent/trace_logger.py finish --run-id <id> [--status done|failed|aborted]
  python scripts/agent/trace_logger.py show   --run-id <id>
  python scripts/agent/trace_logger.py list   [--n 20]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_RUNS_DIR = "docs/runs"

VALID_EVENT_TYPES = frozenset({
    "phase_transition",
    "tool_call",
    "decision",
    "verification",
    "error",
    "info",
})

VALID_STATUSES = frozenset({"running", "done", "failed", "aborted"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _runs_root() -> Path:
    base = os.environ.get("AGENT_RUNS_DIR", _DEFAULT_RUNS_DIR)
    p = Path(base)
    return p if p.is_absolute() else _REPO_ROOT / p


def _trace_path(run_id: str) -> Path:
    return _runs_root() / run_id / "trace.json"


def _read_trace(run_id: str) -> dict[str, Any] | None:
    p = _trace_path(run_id)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _write_trace(trace: dict[str, Any]) -> None:
    p = _trace_path(trace["run_id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


# ---------------------------------------------------------------------------
# TraceLogger
# ---------------------------------------------------------------------------


class TraceLogger:
    """Append-only structured event logger for one agent run."""

    def __init__(self, run_id: str | None = None, *, runs_dir: Path | None = None) -> None:
        self._run_id = run_id or str(uuid.uuid4())
        if runs_dir is not None:
            global _runs_root  # allow injection for tests
            self._runs_root_override: Path | None = runs_dir
        else:
            self._runs_root_override = None

    @property
    def run_id(self) -> str:
        return self._run_id

    def _get_root(self) -> Path:
        if self._runs_root_override is not None:
            return self._runs_root_override
        return _runs_root()

    def _trace_path_local(self) -> Path:
        return self._get_root() / self._run_id / "trace.json"

    def _read(self) -> dict[str, Any] | None:
        p = self._trace_path_local()
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _write(self, trace: dict[str, Any]) -> None:
        p = self._trace_path_local()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> dict[str, Any]:
        """Create a new trace file. Idempotent — returns existing if already started."""
        existing = self._read()
        if existing:
            return existing
        trace: dict[str, Any] = {
            "run_id": self._run_id,
            "trace_id": str(uuid.uuid4()),
            "started_at": time.time(),
            "finished_at": None,
            "status": "running",
            "events": [],
        }
        self._write(trace)
        return trace

    def log(
        self,
        event_type: str,
        *,
        phase: str | None = None,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        model_used: str | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        decision_rationale: str | None = None,
        context_snapshot_id: str | None = None,
    ) -> dict[str, Any]:
        """Append one event to the trace. Starts the trace if not yet started."""
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Unknown event_type '{event_type}'; valid: {sorted(VALID_EVENT_TYPES)}")
        trace = self._read() or self.start()
        event: dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": time.time(),
            "phase": phase,
            "context_snapshot_id": context_snapshot_id,
            "inputs": inputs or {},
            "outputs": outputs or {},
            "model_used": model_used,
            "token_usage": {"tokens_in": tokens_in, "tokens_out": tokens_out},
            "decision_rationale": decision_rationale,
        }
        trace["events"].append(event)
        self._write(trace)
        return event

    def finish(self, status: str = "done") -> dict[str, Any]:
        """Mark the trace as finished. Returns the final trace dict."""
        if status not in VALID_STATUSES:
            raise ValueError(f"Unknown status '{status}'; valid: {sorted(VALID_STATUSES)}")
        trace = self._read() or self.start()
        trace["finished_at"] = time.time()
        trace["status"] = status
        self._write(trace)
        return trace

    def summary(self) -> dict[str, Any]:
        """Return a concise summary of the trace (no event bodies)."""
        trace = self._read()
        if trace is None:
            return {"error": f"Trace not found for run_id={self._run_id}"}
        events = trace.get("events", [])
        phase_transitions = [e for e in events if e["event_type"] == "phase_transition"]
        tool_calls = [e for e in events if e["event_type"] == "tool_call"]
        tokens_in = sum(e.get("token_usage", {}).get("tokens_in", 0) for e in events)
        tokens_out = sum(e.get("token_usage", {}).get("tokens_out", 0) for e in events)
        return {
            "run_id": trace["run_id"],
            "trace_id": trace["trace_id"],
            "status": trace["status"],
            "started_at": trace.get("started_at"),
            "finished_at": trace.get("finished_at"),
            "event_count": len(events),
            "phase_transition_count": len(phase_transitions),
            "tool_call_count": len(tool_calls),
            "total_tokens_in": tokens_in,
            "total_tokens_out": tokens_out,
            "phases_seen": [e["inputs"].get("to") for e in phase_transitions if e.get("inputs")],
        }


# ---------------------------------------------------------------------------
# Module-level convenience functions (for hook integration)
# ---------------------------------------------------------------------------


def log_phase_transition(
    run_id: str,
    from_phase: str,
    to_phase: str,
    *,
    runs_dir: Path | None = None,
) -> dict[str, Any]:
    """Log a workflow phase transition. Creates the trace if needed."""
    logger = TraceLogger(run_id=run_id, runs_dir=runs_dir)
    return logger.log(
        "phase_transition",
        phase=to_phase,
        inputs={"from": from_phase, "to": to_phase},
    )


def log_tool_call(
    run_id: str,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    phase: str | None = None,
    tokens_in: int = 0,
    tokens_out: int = 0,
    runs_dir: Path | None = None,
) -> dict[str, Any]:
    """Log a tool invocation event."""
    logger = TraceLogger(run_id=run_id, runs_dir=runs_dir)
    return logger.log(
        "tool_call",
        phase=phase,
        inputs={"tool_name": tool_name, "tool_input": tool_input},
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent execution trace logger")
    sub = parser.add_subparsers(dest="command", required=True)

    # start
    p_start = sub.add_parser("start", help="Start a new trace")
    p_start.add_argument("--run-id", dest="run_id", default=None,
                         help="Run ID (default: new UUID)")

    # event
    p_event = sub.add_parser("event", help="Append an event to a trace")
    p_event.add_argument("--run-id", dest="run_id", required=True)
    p_event.add_argument("--type", dest="event_type", required=True,
                         choices=sorted(VALID_EVENT_TYPES))
    p_event.add_argument("--phase", default=None)
    p_event.add_argument("--inputs", default="{}", metavar="JSON")
    p_event.add_argument("--outputs", default="{}", metavar="JSON")
    p_event.add_argument("--model", default=None, dest="model_used")
    p_event.add_argument("--tokens-in", type=int, default=0, dest="tokens_in")
    p_event.add_argument("--tokens-out", type=int, default=0, dest="tokens_out")
    p_event.add_argument("--rationale", default=None, dest="decision_rationale")
    p_event.add_argument("--snapshot-id", default=None, dest="context_snapshot_id")

    # finish
    p_finish = sub.add_parser("finish", help="Mark a trace as finished")
    p_finish.add_argument("--run-id", dest="run_id", required=True)
    p_finish.add_argument("--status", default="done", choices=sorted(VALID_STATUSES - {"running"}))

    # show
    p_show = sub.add_parser("show", help="Print a trace")
    p_show.add_argument("--run-id", dest="run_id", required=True)
    p_show.add_argument("--summary", action="store_true", help="Print summary only")

    # list
    p_list = sub.add_parser("list", help="List recent traces")
    p_list.add_argument("--n", type=int, default=20)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "start":
        run_id = args.run_id or str(uuid.uuid4())
        logger = TraceLogger(run_id=run_id)
        trace = logger.start()
        print(json.dumps({"run_id": trace["run_id"], "trace_id": trace["trace_id"]}))

    elif args.command == "event":
        try:
            inputs = json.loads(args.inputs)
            outputs = json.loads(args.outputs)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON in --inputs or --outputs: {exc}", file=sys.stderr)
            return 1
        logger = TraceLogger(run_id=args.run_id)
        event = logger.log(
            args.event_type,
            phase=args.phase,
            inputs=inputs,
            outputs=outputs,
            model_used=args.model_used,
            tokens_in=args.tokens_in,
            tokens_out=args.tokens_out,
            decision_rationale=args.decision_rationale,
            context_snapshot_id=args.context_snapshot_id,
        )
        print(json.dumps({"event_id": event["event_id"]}))

    elif args.command == "finish":
        logger = TraceLogger(run_id=args.run_id)
        trace = logger.finish(args.status)
        print(json.dumps({"run_id": trace["run_id"], "status": trace["status"]}))

    elif args.command == "show":
        logger = TraceLogger(run_id=args.run_id)
        if args.summary:
            print(json.dumps(logger.summary(), indent=2))
        else:
            trace = logger._read()
            if trace is None:
                print(f"Trace not found: {args.run_id}", file=sys.stderr)
                return 1
            print(json.dumps(trace, indent=2))

    elif args.command == "list":
        root = _runs_root()
        if not root.exists():
            print("[]")
            return 0
        traces: list[dict[str, Any]] = []
        for run_dir in sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            tp = run_dir / "trace.json"
            if tp.exists():
                try:
                    t = json.loads(tp.read_text(encoding="utf-8"))
                    traces.append({
                        "run_id": t.get("run_id"),
                        "status": t.get("status"),
                        "started_at": t.get("started_at"),
                        "finished_at": t.get("finished_at"),
                        "event_count": len(t.get("events", [])),
                    })
                except (json.JSONDecodeError, OSError):
                    pass
            if len(traces) >= args.n:
                break
        print(json.dumps(traces, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
