"""Learning loop analyzer — extracts recurring patterns from run artifact corpora."""

from __future__ import annotations

from agent_runtime.schemas import LearningSuggestion, RunArtifact


class LearningAnalyzer:
    """Analyzes a corpus of ``RunArtifact`` objects for recurring patterns.

    Patterns that appear in fewer than *minimum_evidence_count* artifacts are
    below the evidence threshold and are suppressed.

    Two suggestion categories are generated:
    - ``"recurring_risk"`` — same residual risk text recurs across runs.
    - ``"recurring_verification_failure"`` — same verification kind fails repeatedly.
    """

    def __init__(self, minimum_evidence_count: int = 2) -> None:
        if minimum_evidence_count < 1:
            raise ValueError("minimum_evidence_count must be at least 1.")
        self.minimum_evidence_count = minimum_evidence_count

    def analyze(self, artifacts: list[RunArtifact]) -> list[LearningSuggestion]:
        """Return learning suggestions derived from *artifacts*.

        Returns an empty list when *artifacts* is empty or when no pattern
        meets the ``minimum_evidence_count`` threshold.
        """
        if not artifacts:
            return []

        total = len(artifacts)
        suggestions: list[LearningSuggestion] = []

        # --- Recurring residual risks ---
        risk_runs: dict[str, list[str]] = {}
        for artifact in artifacts:
            for risk in artifact.residual_risks:
                risk_runs.setdefault(risk, []).append(artifact.run_id)

        for risk_text, run_ids in risk_runs.items():
            if len(run_ids) >= self.minimum_evidence_count:
                suggestions.append(
                    LearningSuggestion(
                        category="recurring_risk",
                        description=(
                            f"Residual risk appeared in {len(run_ids)} of {total} runs: "
                            f"{risk_text}"
                        ),
                        confidence=min(len(run_ids) / total, 1.0),
                        evidence_count=len(run_ids),
                        source_run_ids=run_ids,
                    )
                )

        # --- Recurring verification failures ---
        failure_runs: dict[str, list[str]] = {}
        for artifact in artifacts:
            for entry in artifact.verification:
                if entry.status == "failed":
                    failure_runs.setdefault(entry.kind, []).append(artifact.run_id)

        for kind, run_ids in failure_runs.items():
            if len(run_ids) >= self.minimum_evidence_count:
                suggestions.append(
                    LearningSuggestion(
                        category="recurring_verification_failure",
                        description=(
                            f"Verification {kind!r} failed in {len(run_ids)} of {total} runs."
                        ),
                        confidence=min(len(run_ids) / total, 1.0),
                        evidence_count=len(run_ids),
                        source_run_ids=run_ids,
                    )
                )

        return suggestions
