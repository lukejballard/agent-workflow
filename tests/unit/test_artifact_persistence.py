"""Tests for agent_runtime.artifacts — run artifact persistence."""

from __future__ import annotations

import uuid

from agent_runtime.artifacts import InMemoryArtifactStore
from agent_runtime.schemas import (
    RunArtifact,
    RunArtifactStatus,
    TaskClass,
    VerificationEntry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _artifact(
    run_id: str | None = None,
    task_class: TaskClass = TaskClass.TRIVIAL,
    status: RunArtifactStatus = RunArtifactStatus.DONE,
    summary: str = "completed",
    residual_risks: list[str] | None = None,
    touched_paths: list[str] | None = None,
    verification: list[VerificationEntry] | None = None,
) -> RunArtifact:
    return RunArtifact(
        run_id=run_id or str(uuid.uuid4()),
        task_class=task_class,
        objective="test run",
        status=status,
        summary=summary,
        residual_risks=residual_risks or [],
        touched_paths=touched_paths or [],
        verification=verification or [],
    )


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------


def test_save_and_load_roundtrip() -> None:
    store = InMemoryArtifactStore()
    artifact = _artifact(run_id="run-1")
    store.save(artifact)
    loaded = store.load("run-1")
    assert loaded is not None
    assert loaded.run_id == "run-1"


def test_load_nonexistent_run_id_returns_none() -> None:
    store = InMemoryArtifactStore()
    assert store.load("does-not-exist") is None


def test_save_overwrites_on_duplicate_run_id() -> None:
    store = InMemoryArtifactStore()
    original = _artifact(run_id="run-x", summary="first")
    updated = _artifact(run_id="run-x", summary="second")
    store.save(original)
    store.save(updated)
    assert store.load("run-x").summary == "second"  # type: ignore[union-attr]


def test_save_preserves_schema_version() -> None:
    store = InMemoryArtifactStore()
    artifact = _artifact(run_id="run-sv")
    store.save(artifact)
    assert store.load("run-sv").schema_version == 1  # type: ignore[union-attr]


def test_save_preserves_touched_paths() -> None:
    store = InMemoryArtifactStore()
    paths = ["src/agent_runtime/schemas.py", "tests/unit/test_schemas.py"]
    artifact = _artifact(run_id="run-paths", touched_paths=paths)
    store.save(artifact)
    assert store.load("run-paths").touched_paths == paths  # type: ignore[union-attr]


def test_save_preserves_residual_risks() -> None:
    store = InMemoryArtifactStore()
    risks = ["missing retry", "no circuit breaker"]
    artifact = _artifact(run_id="run-risks", residual_risks=risks)
    store.save(artifact)
    assert store.load("run-risks").residual_risks == risks  # type: ignore[union-attr]


def test_save_preserves_typed_verification_entries() -> None:
    store = InMemoryArtifactStore()
    verification = [
        VerificationEntry(kind="pytest", status="passed", details="all green"),
        VerificationEntry(kind="mypy", status="failed", details="type error"),
    ]
    artifact = _artifact(run_id="run-ver", verification=verification)
    store.save(artifact)
    loaded = store.load("run-ver")
    assert loaded is not None
    assert loaded.verification[0].kind == "pytest"
    assert loaded.verification[1].status == "failed"


def test_save_preserves_task_class() -> None:
    store = InMemoryArtifactStore()
    artifact = _artifact(run_id="run-tc", task_class=TaskClass.GREENFIELD_FEATURE)
    store.save(artifact)
    assert store.load("run-tc").task_class == TaskClass.GREENFIELD_FEATURE  # type: ignore[union-attr]


def test_save_preserves_status() -> None:
    store = InMemoryArtifactStore()
    artifact = _artifact(run_id="run-st", status=RunArtifactStatus.BLOCKED)
    store.save(artifact)
    assert store.load("run-st").status == RunArtifactStatus.BLOCKED  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


def test_list_all_empty_store_returns_empty() -> None:
    assert InMemoryArtifactStore().list_all() == []


def test_list_all_returns_all_saved_artifacts() -> None:
    store = InMemoryArtifactStore()
    for i in range(4):
        store.save(_artifact(run_id=f"run-{i}"))
    listed = store.list_all()
    assert len(listed) == 4


def test_list_all_run_ids_match_saved() -> None:
    store = InMemoryArtifactStore()
    run_ids = [f"r-{i}" for i in range(3)]
    for rid in run_ids:
        store.save(_artifact(run_id=rid))
    listed_ids = {a.run_id for a in store.list_all()}
    assert listed_ids == set(run_ids)


def test_list_all_returns_copy_not_reference() -> None:
    store = InMemoryArtifactStore()
    store.save(_artifact(run_id="run-ref"))
    first = store.list_all()
    store.save(_artifact(run_id="run-new"))
    second = store.list_all()
    # First list should not change after a new save.
    assert len(first) == 1
    assert len(second) == 2


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_existing_artifact_returns_true() -> None:
    store = InMemoryArtifactStore()
    store.save(_artifact(run_id="del-1"))
    assert store.delete("del-1") is True


def test_delete_existing_artifact_removes_it() -> None:
    store = InMemoryArtifactStore()
    store.save(_artifact(run_id="del-2"))
    store.delete("del-2")
    assert store.load("del-2") is None


def test_delete_nonexistent_run_id_returns_false() -> None:
    assert InMemoryArtifactStore().delete("ghost") is False


# ---------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------


def test_count_empty_store_returns_zero() -> None:
    assert InMemoryArtifactStore().count() == 0


def test_count_returns_number_of_saved_artifacts() -> None:
    store = InMemoryArtifactStore()
    store.save(_artifact(run_id="c-1"))
    store.save(_artifact(run_id="c-2"))
    store.save(_artifact(run_id="c-3"))
    assert store.count() == 3


def test_count_decrements_after_delete() -> None:
    store = InMemoryArtifactStore()
    store.save(_artifact(run_id="cd-1"))
    store.save(_artifact(run_id="cd-2"))
    store.delete("cd-1")
    assert store.count() == 1
