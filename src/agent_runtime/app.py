"""ASGI entry point for the agent-runtime FastAPI application.

Usage::

    uvicorn src.agent_runtime.app:app --reload

Factory pattern allows tests to create isolated instances::

    from agent_runtime.app import create_app
    app = create_app()
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_runtime.routes import router


def _cors_origins() -> list[str]:
    """Return allowed CORS origins from the environment.

    Reads ``CORS_ORIGINS`` as a comma-separated list.
    Defaults to ``["*"]`` for local development.
    """
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan — wires persistent storage and optional Temporal worker.

    **DATABASE_URL** (optional): when present the SQLAlchemy Core backing store
    is initialised and replaces the default in-memory store in ``routes``.

    **TEMPORAL_HOST** (optional): when present an in-process Temporal worker is
    started that polls the configured task queue.  The ``TemporalPlanRunner`` is
    stored on ``app.state.temporal_runner`` for use by route handlers.  The
    worker is shut down cleanly when the application exits.
    """
    # --- persistent backing store -------------------------------------------
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url:
        from agent_runtime.storage.db import create_engine_from_url
        from agent_runtime.storage.store import SQLRuntimeStore
        from agent_runtime.storage.tables import metadata
        from agent_runtime.routes import configure_store

        engine = create_engine_from_url(db_url)
        metadata.create_all(engine)
        configure_store(SQLRuntimeStore(engine))

    # --- Temporal worker wiring ---------------------------------------------
    _temporal_worker = None
    temporal_host = os.environ.get("TEMPORAL_HOST", "").strip()
    if temporal_host:
        from temporalio.client import Client
        from temporalio.worker import Worker as _TemporalWorker

        from agent_runtime.temporal_runner import (
            PlanWorkflow,
            TemporalPlanRunner,
            execute_step_activity,
        )

        namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
        task_queue = os.environ.get("TEMPORAL_TASK_QUEUE", "agent-runtime")

        temporal_client = await Client.connect(temporal_host, namespace=namespace)
        _temporal_worker = _TemporalWorker(
            temporal_client,
            task_queue=task_queue,
            workflows=[PlanWorkflow],
            activities=[execute_step_activity],
        )
        await _temporal_worker.__aenter__()
        app.state.temporal_runner = TemporalPlanRunner(temporal_client, task_queue)

    try:
        yield
    finally:
        if _temporal_worker is not None:
            await _temporal_worker.__aexit__(None, None, None)


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns a fully configured instance with CORS middleware and all
    agent-runtime routes registered.
    """
    app = FastAPI(
        title="Agent Runtime API",
        version="0.1.0",
        description="Task lifecycle and event-stream API for the agent runtime.",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app


#: Module-level singleton consumed by uvicorn.
app: FastAPI = create_app()
