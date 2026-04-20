"""Task planner — assembles PlanStep objects into a validated Plan with DAG constraints."""

from __future__ import annotations

import uuid

from agent_runtime.schemas import Plan, PlanStep


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PlannerError(Exception):
    """Raised when plan validation fails."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(f"Plan validation failed: {'; '.join(errors)}")
        self.errors = errors


# ---------------------------------------------------------------------------
# DAG utilities
# ---------------------------------------------------------------------------


def detect_cycle(steps: list[PlanStep]) -> bool:
    """Return True if the dependency graph of *steps* contains a directed cycle.

    Each ``PlanStep.depends_on`` names steps that must complete before this step
    can run.  A cycle means two or more steps form a circular dependency chain
    (including self-references).
    """
    # Build adjacency: node → list of its declared predecessors.
    adj: dict[str, list[str]] = {s.step_id: list(s.depends_on) for s in steps}

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {sid: WHITE for sid in adj}

    def _dfs(node: str) -> bool:
        color[node] = GRAY
        for dep in adj.get(node, []):
            if dep not in color:
                # Reference to an unknown step — caught separately by validate_plan.
                continue
            if color[dep] == GRAY:
                return True  # Back edge → cycle.
            if color[dep] == WHITE and _dfs(dep):
                return True
        color[node] = BLACK
        return False

    return any(_dfs(sid) for sid in list(adj) if color[sid] == WHITE)


def validate_plan(plan: Plan) -> list[str]:
    """Validate *plan* and return a list of human-readable error strings.

    An empty return list means the plan is valid.
    """
    errors: list[str] = []
    seen_ids: set[str] = set()
    step_ids: set[str] = {s.step_id for s in plan.steps}

    for step in plan.steps:
        if step.step_id in seen_ids:
            errors.append(f"Duplicate step_id: {step.step_id!r}")
        seen_ids.add(step.step_id)
        for dep in step.depends_on:
            if dep not in step_ids:
                errors.append(
                    f"Step {step.step_id!r} depends on unknown step {dep!r}"
                )

    if detect_cycle(plan.steps):
        errors.append("Plan contains a dependency cycle.")

    return errors


# ---------------------------------------------------------------------------
# BasicPlanner
# ---------------------------------------------------------------------------


class BasicPlanner:
    """Assembles explicitly-supplied ``PlanStep`` objects into a validated ``Plan``."""

    def create_plan(
        self,
        task_id: str,
        trace_id: str,
        steps: list[PlanStep],
    ) -> Plan:
        """Create and validate a ``Plan`` from *steps*.

        Args:
            task_id: ID of the owning task.
            trace_id: Correlation identifier (reserved for future event emission).
            steps: Ordered or unordered list of plan steps.

        Returns:
            A validated ``Plan`` with a fresh UUID ``plan_id``.

        Raises:
            PlannerError: if the plan contains duplicate IDs, unknown dependency
                references, or a dependency cycle.
        """
        plan = Plan(
            plan_id=str(uuid.uuid4()),
            task_id=task_id,
            steps=steps,
        )
        errors = validate_plan(plan)
        if errors:
            raise PlannerError(errors)
        return plan
