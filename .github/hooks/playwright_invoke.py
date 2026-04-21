"""playwright_invoke.py — thin orchestrator bridge for the Playwright probe.

Lets any Python hook or the orchestrator spawn the Playwright probe
by calling ``probe_url(url)`` without knowing the Node/skill layout.

Usage from a hook or script:
    from playwright_invoke import probe_url
    results = probe_url("https://example.com")
    # results is a list of dicts, one per emitted JSON-line event.

CLI usage (for manual testing):
    python playwright_invoke.py https://example.com
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).parent.parent.parent.parent / ".agents" / "skills" / "playwright"
# Fallback: environment variable overrides the computed path.
_SKILL_DIR = Path(os.environ.get("PLAYWRIGHT_SKILL_DIR", str(_SKILL_DIR)))

_RUN_JS = _SKILL_DIR / "run.js"
_PROBE_JS = _SKILL_DIR / "probe.js"


def _resolve_node() -> str:
    """Return the node executable, preferring the one on PATH."""
    import shutil
    node = shutil.which("node")
    if not node:
        raise FileNotFoundError(
            "node not found on PATH. Install Node ≥ 18 to use the Playwright probe."
        )
    return node


def probe_url(url: str, timeout: int = 60) -> list[dict]:
    """Run the Playwright probe against *url*.

    Args:
        url: The target URL (must include scheme, e.g. ``https://``).
        timeout: Seconds before the subprocess is killed (default 60).

    Returns:
        A list of event dicts emitted by probe.js (one per stdout JSON-line).

    Raises:
        FileNotFoundError: If skill files or node are missing.
        RuntimeError: If the probe exits with a non-zero status and no
            ``done`` event was emitted.
    """
    if not _RUN_JS.exists():
        raise FileNotFoundError(
            f"Playwright run.js not found at {_RUN_JS}. "
            "Ensure the playwright skill is installed."
        )
    if not _PROBE_JS.exists():
        raise FileNotFoundError(
            f"probe.js not found at {_PROBE_JS}. "
            "Run the skill setup step first."
        )

    node = _resolve_node()
    cmd = [node, str(_RUN_JS), str(_PROBE_JS), url]

    try:
        env = {**os.environ, "TARGET_URL": url}
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(_SKILL_DIR),
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Playwright probe timed out after {timeout}s") from exc

    events: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # Non-JSON progress lines from run.js (e.g. "📄 Executing file:")
            pass

    has_done = any(e.get("event") == "done" for e in events)
    if proc.returncode != 0 and not has_done:
        stderr_snippet = proc.stderr[-500:] if proc.stderr else ""
        raise RuntimeError(
            f"Playwright probe failed (exit {proc.returncode}). "
            f"stderr tail: {stderr_snippet}"
        )

    return events


def _format_report(events: list[dict]) -> str:
    lines: list[str] = []
    for ev in events:
        kind = ev.get("event", "?")
        if kind == "navigate":
            lines.append(f"Navigating to {ev.get('url')}")
        elif kind == "title":
            lines.append(f"Title: {ev.get('title')}")
        elif kind == "screenshot":
            lines.append(f"Screenshot saved: {ev.get('path')}")
        elif kind == "links_found":
            lines.append(f"Links found: {ev.get('count')}")
        elif kind == "link":
            status = ev.get("status", ev.get("error", "?"))
            ok = ev.get("ok")
            tag = "OK" if ok else ("ERR" if "error" in ev else str(status))
            lines.append(f"  [{tag}] {ev.get('url')}")
        elif kind == "done":
            lines.append(
                f"Done — checked {ev.get('checked')} / {ev.get('total_found')} links."
            )
        elif kind == "error":
            lines.append(f"ERROR: {ev.get('message')}")
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <URL>", file=sys.stderr)
        sys.exit(2)

    target = sys.argv[1]
    try:
        results = probe_url(target)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(_format_report(results))
