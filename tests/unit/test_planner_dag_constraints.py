"""Tests for agent_runtime.planner — DAG constraints."""

from __future__ import annotations

import uuid

import pytest

from agent_runtime.planner import BasicPlanner, PlannerError, detect_cycle, validate_plan
from agent_runtime.schemas import Plan, PlanStep


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _step(step_id: str, depends_on: list[str] | None = None) -> PlanStep:
    return PlanStep(
        step_id=step_id,
        title=f"Step {step_id}",
        depends_on=depends_on or [],
        input_contract="input",
        output_contract="output",
        done_condition="done",
    )


def _plan(steps: list[PlanStep]) -> Plan:
    return Plan(plan_id=str(uuid.uuid4()), task_id="task-1", steps=steps)


# ---------------------------------------------------------------------------
# detect_cycle
# ---------------------------------------------------------------------------


def test_detect_cycle_empty_steps_returns_false() -> None:
    assert detect_cycle([]) is False


def test_detect_cycle_single_step_no_deps_returns_false() -> None:
    assert detect_cycle([_step("A")]) is False


def test_detect_cycle_linear_chain_returns_false() -> None:
    # A ← B ← C  (C depends on B, B depends on A)
    steps = [_step("A"), _step("B", ["A"]), _step("C", ["B"])]
    assert detect_cycle(steps) is False


def test_detect_cycle_diamond_returns_false() -> None:
    # A ← B, A ← C, B ← D, C ← D
    steps = [_step("A"), _step("B", ["A"]), _step("C", ["A"]), _step("D", ["B", "C"])]
    assert detect_cycle(steps) is False


def test_detect_cycle_direct_two_node_cycle_returns_true() -> None:
    # A depends on B, B depends on A
    steps = [_step("A", ["B"]), _step("B", ["A"])]
    assert detect_cycle(steps) is True


def test_detect_cycle_self_reference_returns_true() -> None:
    steps = [_step("A", ["A"])]
    assert detect_cycle(steps) is True


def test_detect_cycle_three_node_cycle_returns_true() -> None:
    # A→B→C→A
    steps = [_step("A", ["C"]), _step("B", ["A"]), _step("C", ["B"])]
    assert detect_cycle(steps) is True


def test_detect_cycle_reference_to_unknown_step_is_not_a_cycle() -> None:
    # Step references a dep that doesn't exist — no cycle, just a dangling ref.
    steps = [_step("A", ["MISSING"])]
    assert detect_cycle(steps) is False


# ---------------------------------------------------------------------------
# validate_plan
# ---------------------------------------------------------------------------


def test_validate_plan_valid_linear_chain_returns_no_errors() -> None:
    plan = _plan([_step("A"), _step("B", ["A"]), _step("C", ["B"])])
    assert validate_plan(plan) == []


def test_validate_plan_empty_steps_returns_no_errors() -> None:
    assert validate_plan(_plan([])) == []


def test_validate_plan_duplicate_step_id_returns_error() -> None:
    plan = _plan([_step("A"), _step("A")])
    errors = validate_plan(plan)
    assert any("Duplicate" in e for e in errors)


def test_validate_plan_unknown_dependency_returns_error() -> None:
    plan = _plan([_step("A", ["NONEXISTENT"])])
    errors = validate_plan(plan)
    assert any("NONEXISTENT" in e for e in errors)


def test_validate_plan_cycle_returns_error() -> None:
    plan = _plan([_step("A", ["B"]), _step("B", ["A"])])
    errors = validate_plan(plan)
    assert any("cycle" in e.lower() for e in errors)


def test_validate_plan_multiple_errors_all_returned() -> None:
    # duplicate + unknown dep
    plan = _plan([_step("A"), _step("A"), _step("B", ["UNKNOWN"])])
    errors = validate_plan(plan)
    assert len(errors) >= 2


# ---------------------------------------------------------------------------
# BasicPlanner.create_plan
# ---------------------------------------------------------------------------


def test_basic_planner_returns_plan_for_valid_steps() -> None:
    planner = BasicPlanner()
    steps = [_step("A"), _step("B", ["A"])]
    plan = planner.create_plan(task_id="task-1", trace_id="trace-1", steps=steps)
    assert isinstance(plan, Plan)
    assert plan.task_id == "task-1"
    assert plan.steps == steps


def test_basic_planner_generates_unique_plan_ids() -> None:
    planner = BasicPlanner()
    steps = [_step("A")]
    p1 = planner.create_plan(task_id="t", trace_id="tr", steps=steps)
    p2 = planner.create_plan(task_id="t", trace_id="tr", steps=steps)
    assert p1.plan_id != p2.plan_id


def test_basic_planner_plan_id_is_valid_uuid() -> None:
    planner = BasicPlanner()
    plan = planner.create_plan(task_id="t", trace_id="tr", steps=[_step("A")])
    uuid.UUID(plan.plan_id)  # raises ValueError if not a valid UUID


def test_basic_planner_raises_planner_error_on_cycle() -> None:
    planner = BasicPlanner()
    with pytest.raises(PlannerError):
        planner.create_plan(
            task_id="t",
            trace_id="tr",
            steps=[_step("A", ["B"]), _step("B", ["A"])],
        )


def test_basic_planner_planner_error_contains_error_messages() -> None:
    planner = BasicPlanner()
    with pytest.raises(PlannerError) as exc_info:
        planner.create_plan(
            task_id="t",
            trace_id="tr",
            steps=[_step("A"), _step("A")],  # duplicate
        )
    assert len(exc_info.value.errors) >= 1


def test_basic_planner_raises_on_unknown_dependency() -> None:
    planner = BasicPlanner()
    with pytest.raises(PlannerError) as exc_info:
        planner.create_plan(
            task_id="t",
            trace_id="tr",
            steps=[_step("A", ["GHOST"])],
        )
    assert any("GHOST" in e for e in exc_info.value.errors)


def test_basic_planner_empty_steps_is_valid() -> None:
    planner = BasicPlanner()
    plan = planner.create_plan(task_id="t", trace_id="tr", steps=[])
    assert plan.steps == []
