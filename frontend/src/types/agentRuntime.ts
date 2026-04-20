/**
 * Domain types for the agent-runtime API.
 *
 * These interfaces mirror the Pydantic schemas defined in
 * `src/agent_runtime/schemas.py`.  Keep them aligned when the backend models
 * change.
 */

// ---------------------------------------------------------------------------
// Enumerations
// ---------------------------------------------------------------------------

export type TaskState =
  | "PENDING"
  | "PLANNING"
  | "EXECUTING"
  | "VALIDATING"
  | "LEARNING"
  | "DONE"
  | "FAILED"
  | "CANCELLED";

export type StepExecutionStatus =
  | "pending"
  | "in_progress"
  | "done"
  | "failed"
  | "blocked";

export type ToolCallStatus = "success" | "error" | "timeout" | "denied";

export type MemoryScope =
  | "working"
  | "episodic"
  | "semantic"
  | "long_term";

export type EvaluationStatus = "pass" | "fail" | "needs_review";

export type RunArtifactStatus =
  | "in-progress"
  | "blocked"
  | "review-needed"
  | "done";

// ---------------------------------------------------------------------------
// Plan
// ---------------------------------------------------------------------------

export interface PlanStep {
  step_id: string;
  title: string;
  depends_on: string[];
  input_contract: string;
  output_contract: string;
  done_condition: string;
}

export interface AgentPlan {
  plan_id: string;
  task_id: string;
  revision: number;
  steps: PlanStep[];
}

// ---------------------------------------------------------------------------
// Task
// ---------------------------------------------------------------------------

export interface AgentTask {
  task_id: string;
  objective: string;
  state: TaskState;
  plan: AgentPlan | null;
  trace_id: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

export interface AgentEvent {
  event_id: string;
  event_type: string;
  trace_id: string;
  run_id: string | null;
  task_id: string;
  step_id: string | null;
  occurred_at: string;
  sequence: number;
  payload: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Tool calls
// ---------------------------------------------------------------------------

export interface ToolCall {
  call_id: string;
  task_id: string;
  step_id: string;
  tool_name: string;
  status: ToolCallStatus;
  started_at: string;
  ended_at: string | null;
  retry_count: number;
  trace_id: string;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Memory
// ---------------------------------------------------------------------------

export interface MemoryEntry {
  memory_id: string;
  scope: MemoryScope;
  summary: string;
  source: string;
  confidence: number;
  evidence_refs: string[];
  created_at: string;
  expires_at: string | null;
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------

export interface EvaluationFinding {
  severity: "low" | "medium" | "high" | "critical";
  summary: string;
  evidence: string[];
  remediation: string | null;
}

export interface EvaluationResult {
  task_id: string;
  status: EvaluationStatus;
  confidence: number;
  findings: EvaluationFinding[];
  evaluated_at: string;
}

// ---------------------------------------------------------------------------
// Run artifact
// ---------------------------------------------------------------------------

export interface VerificationEntry {
  kind: string;
  status: "passed" | "failed" | "not-run" | "advisory";
  details: string;
}

export interface RunArtifact {
  schema_version: number;
  run_id: string;
  task_class: string;
  objective: string;
  status: RunArtifactStatus;
  summary: string;
  touched_paths: string[];
  verification: VerificationEntry[];
  residual_risks: string[];
}

// ---------------------------------------------------------------------------
// Request payloads
// ---------------------------------------------------------------------------

export interface CreateTaskPayload {
  objective: string;
  trace_id?: string;
}

export interface TransitionPayload {
  target_state: TaskState;
}

export interface CreatePlanPayload {
  steps: PlanStep[];
}
