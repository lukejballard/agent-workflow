"""Worker entry point for the Temporal execution backend.

Usage::

    TEMPORAL_HOST=localhost:7233 python -m agent_runtime.temporal_worker

Environment variables
---------------------
TEMPORAL_HOST
    ``host:port`` of the Temporal frontend service (default: ``localhost:7233``).
TEMPORAL_NAMESPACE
    Temporal namespace (default: ``default``).
TEMPORAL_TASK_QUEUE
    Task queue name the worker polls (default: ``agent-runtime``).
"""

from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from agent_runtime.temporal_runner import PlanWorkflow, execute_step_activity


async def _run() -> None:
    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    task_queue = os.environ.get("TEMPORAL_TASK_QUEUE", "agent-runtime")

    client = await Client.connect(host, namespace=namespace)

    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[PlanWorkflow],
        activities=[execute_step_activity],
    ):
        print(f"Worker running on {host!r}, queue={task_queue!r}")
        # Block until interrupted (Ctrl-C / SIGTERM).
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(_run())
