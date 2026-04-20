"""Tests for the SSE streaming endpoint GET /api/tasks/{task_id}/events.

Uses FastAPI TestClient with ``stream=True`` to consume the event-stream
body without keeping a long-lived connection open.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_runtime.routes import RuntimeStore, get_store, router


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_client() -> TestClient:
    """Return a TestClient with a fresh isolated RuntimeStore."""
    app = FastAPI()
    app.include_router(router)
    store = RuntimeStore()
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app, raise_server_exceptions=True)


def _create_task(client: TestClient, objective: str = "test objective") -> str:
    resp = client.post("/api/tasks", json={"objective": objective})
    assert resp.status_code == 201
    return resp.json()["task_id"]


# ---------------------------------------------------------------------------
# 404 for unknown task
# ---------------------------------------------------------------------------


def test_sse_returns_404_for_unknown_task() -> None:
    client = _make_client()
    resp = client.get("/api/tasks/no-such-task/events")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Content-type header
# ---------------------------------------------------------------------------


def test_sse_returns_event_stream_content_type() -> None:
    client = _make_client()
    task_id = _create_task(client)
    with client.stream("GET", f"/api/tasks/{task_id}/events") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# Heartbeat data
# ---------------------------------------------------------------------------


def test_sse_first_chunk_is_ping_heartbeat() -> None:
    client = _make_client()
    task_id = _create_task(client)
    with client.stream("GET", f"/api/tasks/{task_id}/events") as resp:
        assert resp.status_code == 200
        body = resp.read().decode()
    assert "data: ping" in body


# ---------------------------------------------------------------------------
# Cache control headers
# ---------------------------------------------------------------------------


def test_sse_has_no_cache_header() -> None:
    client = _make_client()
    task_id = _create_task(client)
    with client.stream("GET", f"/api/tasks/{task_id}/events") as resp:
        assert resp.headers.get("cache-control") == "no-cache"


# ---------------------------------------------------------------------------
# Empty event store — only ping returned
# ---------------------------------------------------------------------------


def test_sse_empty_store_returns_only_ping() -> None:
    client = _make_client()
    task_id = _create_task(client)
    with client.stream("GET", f"/api/tasks/{task_id}/events") as resp:
        body = resp.read().decode()
    lines = [ln for ln in body.splitlines() if ln.startswith("data:")]
    assert lines == ["data: ping"]


# ---------------------------------------------------------------------------
# Events are replayed when present
# ---------------------------------------------------------------------------


def test_sse_replays_buffered_events() -> None:
    """Events injected directly into the store are yielded by the stream."""
    import uuid
    from datetime import datetime, timezone

    from agent_runtime.events import AgentEvent, EventType

    app = FastAPI()
    app.include_router(router)
    store = RuntimeStore()
    task_id = str(uuid.uuid4())

    # Manually insert a task and an event for it.
    from agent_runtime.schemas import Task, TaskState

    store.tasks[task_id] = Task(
        task_id=task_id,
        objective="replay test",
        state=TaskState.PENDING,
        trace_id="trace-replay",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    event = AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.TASK_STATE_TRANSITION,
        trace_id="trace-replay",
        task_id=task_id,
        occurred_at=datetime.now(tz=timezone.utc),
        sequence=0,
        payload={"from_state": "PENDING", "to_state": "PLANNING"},
    )
    store.events[task_id] = [event]

    app.dependency_overrides[get_store] = lambda: store
    client = TestClient(app)

    with client.stream("GET", f"/api/tasks/{task_id}/events") as resp:
        body = resp.read().decode()

    data_lines = [ln for ln in body.splitlines() if ln.startswith("data:")]
    assert len(data_lines) == 2  # ping + event
    assert "task.state_transition" in data_lines[1]
