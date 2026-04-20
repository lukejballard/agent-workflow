"""Tests for agent_runtime.routes — task lifecycle state-machine-backed endpoints."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_runtime.routes import RuntimeStore, CreateTaskRequest, get_store, router
from agent_runtime.schemas import TaskState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """Fresh FastAPI app with DI overridden to an isolated store per test."""
    app = FastAPI()
    app.include_router(router)
    store = RuntimeStore()
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


def _create_task(client: TestClient, objective: str = "test objective") -> dict:
    resp = client.post("/api/tasks", json={"objective": objective})
    assert resp.status_code == 201
    return resp.json()


def _step_payload(step_id: str = "s1", depends_on: list[str] | None = None) -> dict:
    return {
        "step_id": step_id,
        "title": f"Step {step_id}",
        "depends_on": depends_on or [],
        "input_contract": "none",
        "output_contract": "none",
        "done_condition": "always",
    }


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------


def test_create_task_returns_201(client: TestClient) -> None:
    resp = client.post("/api/tasks", json={"objective": "do something"})
    assert resp.status_code == 201


def test_create_task_body_has_task_id(client: TestClient) -> None:
    data = _create_task(client)
    assert "task_id" in data
    assert len(data["task_id"]) > 0


def test_create_task_state_is_pending(client: TestClient) -> None:
    data = _create_task(client)
    assert data["state"] == TaskState.PENDING


def test_create_task_preserves_objective(client: TestClient) -> None:
    data = _create_task(client, objective="specific objective text")
    assert data["objective"] == "specific objective text"


def test_create_task_accepts_explicit_trace_id(client: TestClient) -> None:
    resp = client.post(
        "/api/tasks", json={"objective": "t", "trace_id": "my-trace-42"}
    )
    assert resp.json()["trace_id"] == "my-trace-42"


def test_create_task_generates_trace_id_when_absent(client: TestClient) -> None:
    data = _create_task(client)
    assert data["trace_id"] != ""


def test_create_task_includes_timestamps(client: TestClient) -> None:
    data = _create_task(client)
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------


def test_list_tasks_empty_initially(client: TestClient) -> None:
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_returns_created_task(client: TestClient) -> None:
    _create_task(client)
    resp = client.get("/api/tasks")
    assert len(resp.json()) == 1


def test_list_tasks_returns_multiple_tasks(client: TestClient) -> None:
    _create_task(client, "task A")
    _create_task(client, "task B")
    _create_task(client, "task C")
    assert len(client.get("/api/tasks").json()) == 3


# ---------------------------------------------------------------------------
# GET /api/tasks/{task_id}
# ---------------------------------------------------------------------------


def test_get_task_returns_200_for_existing(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.get(f"/api/tasks/{task_id}")
    assert resp.status_code == 200


def test_get_task_returns_correct_task(client: TestClient) -> None:
    task_id = _create_task(client, "unique-obj")["task_id"]
    data = client.get(f"/api/tasks/{task_id}").json()
    assert data["task_id"] == task_id
    assert data["objective"] == "unique-obj"


def test_get_task_returns_404_for_missing(client: TestClient) -> None:
    resp = client.get("/api/tasks/nonexistent-id")
    assert resp.status_code == 404


def test_get_task_404_body_has_detail(client: TestClient) -> None:
    resp = client.get("/api/tasks/ghost")
    assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# POST /api/tasks/{task_id}/transitions
# ---------------------------------------------------------------------------


def test_transition_pending_to_planning_succeeds(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/transitions", json={"target_state": "PLANNING"}
    )
    assert resp.status_code == 200


def test_transition_updates_task_state(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    data = client.post(
        f"/api/tasks/{task_id}/transitions", json={"target_state": "PLANNING"}
    ).json()
    assert data["state"] == TaskState.PLANNING


def test_transition_state_persists_on_subsequent_get(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    client.post(f"/api/tasks/{task_id}/transitions", json={"target_state": "PLANNING"})
    data = client.get(f"/api/tasks/{task_id}").json()
    assert data["state"] == TaskState.PLANNING


def test_transition_invalid_state_returns_422(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    # PENDING → DONE is not an allowed transition
    resp = client.post(
        f"/api/tasks/{task_id}/transitions", json={"target_state": "DONE"}
    )
    assert resp.status_code == 422


def test_transition_invalid_state_body_has_detail(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/transitions", json={"target_state": "DONE"}
    )
    assert "detail" in resp.json()


def test_transition_missing_task_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/api/tasks/no-such-task/transitions", json={"target_state": "PLANNING"}
    )
    assert resp.status_code == 404


def test_transition_unknown_target_state_returns_422(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/transitions", json={"target_state": "NOT_A_STATE"}
    )
    assert resp.status_code == 422


def test_transition_sequence_pending_planning_executing(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    client.post(f"/api/tasks/{task_id}/transitions", json={"target_state": "PLANNING"})
    resp = client.post(
        f"/api/tasks/{task_id}/transitions", json={"target_state": "EXECUTING"}
    )
    assert resp.status_code == 200
    assert resp.json()["state"] == TaskState.EXECUTING


# ---------------------------------------------------------------------------
# POST /api/tasks/{task_id}/plan
# ---------------------------------------------------------------------------


def test_create_plan_returns_201(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/plan", json={"steps": [_step_payload()]}
    )
    assert resp.status_code == 201


def test_create_plan_body_has_plan_id(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/plan", json={"steps": [_step_payload()]}
    )
    assert "plan_id" in resp.json()


def test_create_plan_task_id_matches(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/plan", json={"steps": [_step_payload()]}
    )
    assert resp.json()["task_id"] == task_id


def test_create_plan_for_missing_task_returns_404(client: TestClient) -> None:
    resp = client.post(
        "/api/tasks/ghost-task/plan", json={"steps": [_step_payload()]}
    )
    assert resp.status_code == 404


def test_create_plan_with_cycle_returns_422(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    cyclic_steps = [
        _step_payload("A", ["B"]),
        _step_payload("B", ["A"]),
    ]
    resp = client.post(f"/api/tasks/{task_id}/plan", json={"steps": cyclic_steps})
    assert resp.status_code == 422


def test_create_plan_with_duplicate_step_id_returns_422(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(
        f"/api/tasks/{task_id}/plan",
        json={"steps": [_step_payload("s1"), _step_payload("s1")]},
    )
    assert resp.status_code == 422


def test_create_plan_empty_steps_is_valid(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.post(f"/api/tasks/{task_id}/plan", json={"steps": []})
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/tasks/{task_id}/plan
# ---------------------------------------------------------------------------


def test_get_plan_returns_200_after_creation(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    client.post(f"/api/tasks/{task_id}/plan", json={"steps": [_step_payload()]})
    resp = client.get(f"/api/tasks/{task_id}/plan")
    assert resp.status_code == 200


def test_get_plan_returns_correct_plan_id(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    plan_id = client.post(
        f"/api/tasks/{task_id}/plan", json={"steps": [_step_payload()]}
    ).json()["plan_id"]
    assert client.get(f"/api/tasks/{task_id}/plan").json()["plan_id"] == plan_id


def test_get_plan_returns_404_when_no_plan(client: TestClient) -> None:
    task_id = _create_task(client)["task_id"]
    resp = client.get(f"/api/tasks/{task_id}/plan")
    assert resp.status_code == 404


def test_get_plan_returns_404_when_task_missing(client: TestClient) -> None:
    resp = client.get("/api/tasks/ghost-task/plan")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# get_store singleton
# ---------------------------------------------------------------------------


def test_get_store_returns_runtime_store_instance() -> None:
    from agent_runtime.routes import RuntimeStore, get_store

    store = get_store()
    assert isinstance(store, RuntimeStore)


# ---------------------------------------------------------------------------
# get_store singleton
# ---------------------------------------------------------------------------


def test_get_store_returns_runtime_store_instance() -> None:
    from agent_runtime.routes import RuntimeStore, get_store

    store = get_store()
    assert isinstance(store, RuntimeStore)
