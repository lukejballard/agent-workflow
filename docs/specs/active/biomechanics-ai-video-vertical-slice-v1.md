# Feature: Biomechanics AI Video Vertical Slice V1

**Status:** In Progress
**Created:** 2026-04-15
**Author:** GitHub Copilot
**Estimate:** XL
**Supersedes:** docs/specs/active/practitioner-runtime-bootstrap-v1.md (extends runtime bootstrap with 2D video analysis)

---

## Problem
The repository has a practitioner workflow bootstrap, but it does not yet run an end-to-end
video biomechanics analysis pipeline. Coaches still need a transparent flow that starts from
smartphone clip intake and ends with conservative, inspectable metrics and recommendations.

Without this slice:
- video quality issues are not screened early
- pose extraction and mechanics metrics are missing
- trend tracking for objective progress is unavailable
- report outputs can drift into overconfident language

## Product and safety constraints
- This product is coaching and screening support, not a medical device.
- Outputs must avoid diagnosis claims and certainty language.
- Risk outputs are conservative attention cues.
- Metrics must be code-derived; no LLM-generated measurements.
- Confidence must degrade when visibility or quality is weak.
- Core pipeline remains free and open-source.
- Pipeline remains 2D smartphone-first for this phase.

---

## Current repo architecture summary

### Backend
- FastAPI app in `src/biomechanics_ai/collector/server.py`
- Thin routes in `src/biomechanics_ai/collector/workflow_routes.py`
- Business logic in `src/biomechanics_ai/services/workflow_service.py`
- Local JSON persistence and audit trail in `src/biomechanics_ai/storage/repository.py`
- Strict request/response models in `src/biomechanics_ai/models/workflow.py`
- Metrics middleware in `src/biomechanics_ai/observability/metrics.py`

### Frontend
- React + TypeScript + Vite SPA
- API transport in `frontend/src/api/`
- Shared API schemas in `frontend/src/types/workflow.ts`
- Workflow orchestration hook in `frontend/src/hooks/usePractitionerWorkflow.ts`
- Panel-driven page in `frontend/src/pages/PractitionerWorkspacePage.tsx`

### Existing insertion points
- Session registration already captures clip references (`asset_refs`)
- JSON persistence already stores sessions and audit events
- Workspace already renders session, assessment, comparison, and prescription panels

---

## Assumptions
1. Local-file persistence remains acceptable for this vertical slice.
2. Clip upload stores files under a local application data directory.
3. MediaPipe Pose is an optional backend dependency with graceful fallback when unavailable.
4. First slice supports one visible athlete per clip and warns on multi-athlete detections.
5. A compact metric set is enough for initial pitching and hitting analysis.
6. Trend visualization can be table-first before chart-level polish.
7. No new auth model is required beyond existing role/scope checks.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Overconfident injury-like language in reports | Medium | High | Enforce deterministic conservative wording templates |
| False precision from single-camera 2D input | High | High | Mark inferred metrics and valid camera angles per metric |
| Weak or unstable keypoint tracking | High | High | Confidence gating and missing-keypoint handling |
| Left/right handedness mistakes | Medium | Medium | Normalize lead/trail side using athlete handedness |
| Low quality clips produce noisy outputs | High | High | Hard quality gate with retake guidance |
| Template metrics that are not coach-actionable | Medium | High | Keep metric set intentionally small and drill-linked |
| LLM hallucination changes findings | Low | High | No LLM in first pass; deterministic interpretation only |
| Poor body-size/age generalization | Medium | Medium | Use normalized proxies and explicit limitations |
| Regression in existing practitioner workflow APIs | Medium | High | Add regression tests and preserve existing contracts |

---

## First vertical slice plan

### Slice boundary
Upload clip -> run quality gate -> extract pose -> compute minimal metrics -> generate conservative report -> save report and metrics -> list history and trends.

### Initial supported metrics
- Pitching: trunk_tilt_proxy_deg, stride_length_proxy_ratio, head_stability_proxy
- Hitting: stance_width_proxy_ratio, pelvis_torso_separation_proxy_deg, head_stability_proxy

Every metric includes:
- measured_or_inferred
- confidence
- valid_camera_angles
- limitation text

### Out of scope for this slice
- 3D reconstruction
- diagnosis or injury prediction claims
- advanced bat or ball tracking
- paid external APIs

---

## Task breakdown with dependencies

### Task T1: Checkpoint A architecture and scaffolding
- Objective: Define implementation contract before code.
- Files likely to change: `docs/specs/active/biomechanics-ai-video-vertical-slice-v1.md`
- Approach: Capture architecture summary, assumptions, risks, phased plan, and validation map.
- Verification: Spec reviewed against user request and repo instructions.
- Risk of failure: Low
- Done condition: Active spec exists and maps checkpoints A-H.
- Depends on: none

### Task T2: Extend domain models and storage for video entities
- Objective: Add Clip, PoseFrame, Metric, Observation, Drill, Recommendation, Report persistence shapes.
- Files likely to change: `src/biomechanics_ai/models/workflow.py`, `src/biomechanics_ai/storage/repository.py`, `src/biomechanics_ai/services/workflow_service.py`
- Approach: Add strict Pydantic models and repository collections with audit hooks.
- Verification: Unit tests for model validation and repository round trips.
- Risk of failure: Medium
- Done condition: New entities can be created and retrieved without breaking existing endpoints.
- Depends on: T1

### Task T3: Add upload and session-linked clip creation API
- Objective: Enable clip upload and clip records under sessions.
- Files likely to change: `src/biomechanics_ai/collector/workflow_routes.py`, `src/biomechanics_ai/services/workflow_service.py`, `src/biomechanics_ai/config/settings.py`
- Approach: Add multipart upload endpoint, local storage path handling, validation, and clean errors.
- Verification: API tests for upload success/failure and session linkage.
- Risk of failure: Medium
- Done condition: Clip upload creates persisted clip record and audit event.
- Depends on: T2

### Task T4: Implement quality gating engine
- Objective: Detect low light, blur, shake, bad angle, occlusion, subject size, missing body, multiple athletes.
- Files likely to change: `src/biomechanics_ai/analysis/quality.py` (new), service and route wiring files.
- Approach: OpenCV-based frame sampling and conservative threshold rules with actionable retake guidance.
- Verification: Unit tests with synthetic fixtures for each gating condition.
- Risk of failure: Medium
- Done condition: Unusable clips are rejected with specific reasons and confidence.
- Depends on: T3

### Task T5: Add pose extraction and pose frame storage
- Objective: Extract and persist keypoints with timestamps and per-frame confidence.
- Files likely to change: `src/biomechanics_ai/analysis/pose.py` (new), models/service/storage/route files.
- Approach: MediaPipe adapter with graceful fallback; store frame-level metadata.
- Verification: Unit tests for parsing and missing-keypoint handling.
- Risk of failure: Medium-High
- Done condition: Pose frame records exist for analyzable clips and are inspectable.
- Depends on: T4

### Task T6: Implement minimal mechanics engine
- Objective: Compute compact pitching/hitting metric sets with confidence and camera-angle validity.
- Files likely to change: `src/biomechanics_ai/analysis/mechanics.py` (new), service/models/tests.
- Approach: Deterministic proxy formulas from pose sequences and phase proxies.
- Verification: Unit tests for metric calculations and normalization logic.
- Risk of failure: Medium
- Done condition: Metrics computed for supported movement types with transparent metadata.
- Depends on: T5

### Task T7: Deterministic interpretation, drill mapping, and report generation
- Objective: Produce conservative, coach-facing report items and recommendations.
- Files likely to change: `src/biomechanics_ai/analysis/reporting.py` (new), `src/biomechanics_ai/analysis/drills.py` (new), service/models/tests.
- Approach: Rule-based finding interpretation and flaw-to-drill mapping.
- Verification: Unit tests for report rendering and recommendation mapping.
- Risk of failure: Medium
- Done condition: Report output includes what/why/try/confidence and limitations.
- Depends on: T6

### Task T8: Persistence-backed trends and report retrieval API
- Objective: Save results and expose history/trends.
- Files likely to change: route/service/storage/model files.
- Approach: Add list/get report endpoints and athlete trend aggregation endpoint.
- Verification: API tests for persistence round-trip and trend responses.
- Risk of failure: Medium
- Done condition: Historical session report data and trends retrievable per athlete.
- Depends on: T7

### Task T9: Frontend upload-analysis-report-trend UI
- Objective: Provide practical coach-facing vertical slice in existing workspace page.
- Files likely to change: `frontend/src/types/workflow.ts`, `frontend/src/api/workflow.ts`, `frontend/src/hooks/usePractitionerWorkflow.ts`, new/updated panels, tests.
- Approach: Add analysis panel with upload, quality status, report rendering, and trend list.
- Verification: Vitest coverage for shell + key states + workflow actions.
- Risk of failure: Medium
- Done condition: User can run end-to-end flow from selected session.
- Depends on: T8

### Task T10: Cross-checkpoint adversarial review and regression pass
- Objective: Challenge design after each checkpoint and close blockers.
- Files likely to change: tests, docs/spec checkboxes.
- Approach: Explicit PASS/WARN/FAIL checkpoint notes and targeted fixes.
- Verification: backend and frontend tests, residual-risk log.
- Risk of failure: Medium
- Done condition: Checkpoints A-H verified with open risks documented.
- Depends on: T2-T9

---

## Validation plan

### Automated tests
- Upload/session creation: API integration test
- Pose parsing: unit tests with synthetic pose fixture
- Metric calculation: unit tests for pitching and hitting proxies
- Phase proxy segmentation: unit tests for time-index selection helpers
- Quality gating: unit tests per failure mode
- Report rendering: unit tests for deterministic text generation
- Drill mapping: unit tests for flaw-to-drill mapping
- Persistence round trips: repository/service tests for clips/reports/trends
- Normalization logic: unit tests for handedness and frame normalization

### Manual verification path
1. Start backend and frontend.
2. Create athlete and session.
3. Upload smartphone clip.
4. Confirm quality gate decision and retake guidance behavior.
5. Run analysis.
6. Confirm report displays transparent metrics and uncertainty.
7. Create second session and repeat.
8. Confirm trend output surfaces improvement/regression/instability.

### Checkpoint verification gates
- A: architecture map and plan doc completed.
- B: upload and session clip creation with clean failures.
- C: pose extraction persisted and previewable.
- D: quality gating rejection and confidence surfaced.
- E: minimal metrics computed and unit tested.
- F: readable report with explainable recommendations and uncertainty.
- G: persistence + trend retrieval working.
- H: end-to-end workflow tested and stable enough for next iteration.

---

## Adversarial review prompts per checkpoint
At each checkpoint, challenge:
- What breaks with worse camera angle?
- What breaks with occlusion?
- What breaks with youth athletes or different body sizes?
- What assumptions are hidden?
- What metrics are not actionable?
- What outputs could mislead a coach?
- Where are we pretending to know more than the data supports?

Any FAIL finding must be addressed before moving to the next checkpoint.

---

## Acceptance criteria for this pass
- [ ] User can upload a pitching or hitting clip linked to a session.
- [ ] Quality gate rejects unusable clips with specific retake guidance.
- [ ] Pose extraction runs and stores frame-level keypoints/confidence metadata.
- [ ] Small transparent metric set is computed with confidence and camera-angle validity.
- [ ] Deterministic conservative report is generated from structured findings.
- [ ] Report, metrics, and recommendations persist and can be retrieved later.
- [ ] Basic trends are visible across sessions for an athlete.
- [ ] Backend and frontend tests pass for added surfaces.
- [ ] No diagnosis language or overconfident injury claims appear in outputs.
