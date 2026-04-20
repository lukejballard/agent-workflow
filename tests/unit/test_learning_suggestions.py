"""Tests for agent_runtime.learning — evidence thresholds and pattern extraction."""

from __future__ import annotations

import uuid

import pytest

from agent_runtime.learning import LearningAnalyzer
from agent_runtime.schemas import RunArtifact, RunArtifactStatus, TaskClass, VerificationEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _artifact(
    run_id: str | None = None,
    residual_risks: list[str] | None = None,
    verification: list[VerificationEntry] | None = None,
) -> RunArtifact:
    return RunArtifact(
        run_id=run_id or str(uuid.uuid4()),
        task_class=TaskClass.TRIVIAL,
        objective="test objective",
        status=RunArtifactStatus.DONE,
        summary="done",
        residual_risks=residual_risks or [],
        verification=verification or [],
    )


def _failed_verification(kind: str) -> VerificationEntry:
    return VerificationEntry(kind=kind, status="failed", details="")


def _passed_verification(kind: str) -> VerificationEntry:
    return VerificationEntry(kind=kind, status="passed", details="")


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------


def test_minimum_evidence_count_zero_raises() -> None:
    with pytest.raises(ValueError):
        LearningAnalyzer(minimum_evidence_count=0)


def test_minimum_evidence_count_negative_raises() -> None:
    with pytest.raises(ValueError):
        LearningAnalyzer(minimum_evidence_count=-1)


def test_minimum_evidence_count_one_is_valid() -> None:
    analyzer = LearningAnalyzer(minimum_evidence_count=1)
    assert analyzer.minimum_evidence_count == 1


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


def test_analyze_empty_artifacts_returns_empty() -> None:
    assert LearningAnalyzer().analyze([]) == []


# ---------------------------------------------------------------------------
# Recurring risk threshold
# ---------------------------------------------------------------------------


def test_analyze_single_artifact_risk_below_threshold_returns_no_suggestion() -> None:
    artifacts = [_artifact(residual_risks=["unmitigated danger"])]
    assert LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts) == []


def test_analyze_risk_at_threshold_returns_suggestion() -> None:
    risk = "missing retry logic"
    artifacts = [
        _artifact(run_id="r1", residual_risks=[risk]),
        _artifact(run_id="r2", residual_risks=[risk]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    assert len(suggestions) == 1
    assert suggestions[0].category == "recurring_risk"


def test_analyze_risk_above_threshold_returns_suggestion() -> None:
    risk = "timeout not handled"
    artifacts = [
        _artifact(run_id="r1", residual_risks=[risk]),
        _artifact(run_id="r2", residual_risks=[risk]),
        _artifact(run_id="r3", residual_risks=[risk]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    assert any(s.category == "recurring_risk" for s in suggestions)


def test_analyze_risk_threshold_one_matches_single_occurrence() -> None:
    artifacts = [_artifact(residual_risks=["edge case risk"])]
    suggestions = LearningAnalyzer(minimum_evidence_count=1).analyze(artifacts)
    assert len(suggestions) == 1


def test_analyze_different_risks_are_independent() -> None:
    artifacts = [
        _artifact(run_id="r1", residual_risks=["risk-A", "risk-B"]),
        _artifact(run_id="r2", residual_risks=["risk-A"]),  # risk-B only appears once
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    categories = [s.description for s in suggestions]
    assert any("risk-A" in d for d in categories)
    assert all("risk-B" not in d for d in categories)


# ---------------------------------------------------------------------------
# Recurring verification failure threshold
# ---------------------------------------------------------------------------


def test_analyze_verification_failure_below_threshold_returns_no_suggestion() -> None:
    artifacts = [_artifact(verification=[_failed_verification("pytest")])]
    assert LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts) == []


def test_analyze_verification_failure_at_threshold_returns_suggestion() -> None:
    artifacts = [
        _artifact(run_id="r1", verification=[_failed_verification("pytest")]),
        _artifact(run_id="r2", verification=[_failed_verification("pytest")]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    assert any(s.category == "recurring_verification_failure" for s in suggestions)


def test_analyze_verification_passed_does_not_generate_suggestion() -> None:
    artifacts = [
        _artifact(run_id="r1", verification=[_passed_verification("pytest")]),
        _artifact(run_id="r2", verification=[_passed_verification("pytest")]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    assert all(s.category != "recurring_verification_failure" for s in suggestions)


def test_analyze_verification_failure_suggestion_contains_kind() -> None:
    artifacts = [
        _artifact(run_id="r1", verification=[_failed_verification("mypy")]),
        _artifact(run_id="r2", verification=[_failed_verification("mypy")]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    vf = next(s for s in suggestions if s.category == "recurring_verification_failure")
    assert "mypy" in vf.description


# ---------------------------------------------------------------------------
# Suggestion attributes
# ---------------------------------------------------------------------------


def test_analyze_suggestion_confidence_is_in_range() -> None:
    risk = "stale memory"
    artifacts = [
        _artifact(run_id="r1", residual_risks=[risk]),
        _artifact(run_id="r2", residual_risks=[risk]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    assert all(0.0 <= s.confidence <= 1.0 for s in suggestions)


def test_analyze_suggestion_evidence_count_matches_occurrences() -> None:
    risk = "missing auth check"
    artifacts = [
        _artifact(run_id="r1", residual_risks=[risk]),
        _artifact(run_id="r2", residual_risks=[risk]),
        _artifact(run_id="r3", residual_risks=[risk]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    assert suggestions[0].evidence_count == 3


def test_analyze_suggestion_source_run_ids_lists_contributing_runs() -> None:
    risk = "race condition"
    artifacts = [
        _artifact(run_id="run-alpha", residual_risks=[risk]),
        _artifact(run_id="run-beta", residual_risks=[risk]),
        _artifact(run_id="run-gamma", residual_risks=[]),
    ]
    suggestions = LearningAnalyzer(minimum_evidence_count=2).analyze(artifacts)
    run_ids = suggestions[0].source_run_ids
    assert "run-alpha" in run_ids
    assert "run-beta" in run_ids
    assert "run-gamma" not in run_ids
