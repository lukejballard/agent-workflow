/**
 * ApprovalPanel — allows operators to approve or deny pending task actions.
 *
 * Accessibility:
 * - Approve/Deny buttons have descriptive aria-labels including the task
 *   objective so screen-reader users have full context.
 * - Status updates use an aria-live region.
 * - Disabled states are properly conveyed via `aria-disabled`.
 */

import type { AgentTask, TaskState } from "../../types/agentRuntime";

interface ApprovalPanelProps {
  task: AgentTask;
  /** Called when the operator approves by advancing to `targetState`. */
  onApprove: (taskId: string, targetState: TaskState) => void;
  /** Called when the operator denies (transitions to CANCELLED). */
  onDeny: (taskId: string) => void;
  /** Whether a command is in-flight. */
  loading?: boolean;
  /** Error from a previous command, if any. */
  error?: Error | null;
}

/** States that can be approved to the next natural step. */
const APPROVABLE_TRANSITIONS: Partial<Record<TaskState, TaskState>> = {
  PENDING: "PLANNING",
  PLANNING: "EXECUTING",
  EXECUTING: "VALIDATING",
  VALIDATING: "LEARNING",
  LEARNING: "DONE",
};

const TERMINAL_STATES: Set<TaskState> = new Set(["DONE", "FAILED", "CANCELLED"]);

export function ApprovalPanel({
  task,
  onApprove,
  onDeny,
  loading = false,
  error = null,
}: ApprovalPanelProps) {
  const isTerminal = TERMINAL_STATES.has(task.state);
  const nextState = APPROVABLE_TRANSITIONS[task.state];
  const canApprove = !isTerminal && nextState !== undefined;

  if (isTerminal) {
    return (
      <section aria-label="Approval panel" className="approval-panel">
        <p className="approval-panel__terminal-msg">
          Task is in terminal state:{" "}
          <strong>{task.state}</strong>. No approval actions available.
        </p>
      </section>
    );
  }

  return (
    <section aria-label="Approval panel" className="approval-panel">
      <h2 className="approval-panel__title">Operator Action Required</h2>

      <p className="approval-panel__context">
        Task <strong>{task.objective}</strong> is currently{" "}
        <strong>{task.state}</strong>.
        {canApprove && nextState !== undefined && (
          <> Approve to advance to <strong>{nextState}</strong>.</>
        )}
      </p>

      {/* Live region for command feedback */}
      <div role="status" aria-live="polite" className="approval-panel__status">
        {loading && <span>Processing…</span>}
        {error !== null && !loading && (
          <span className="approval-panel__error" aria-live="assertive">
            Error: {error.message}
          </span>
        )}
      </div>

      <div className="approval-panel__actions">
        {canApprove && nextState !== undefined && (
          <button
            type="button"
            className="btn btn--approve"
            onClick={() => onApprove(task.task_id, nextState)}
            disabled={loading}
            aria-disabled={loading}
            aria-label={`Approve task "${task.objective}" — advance to ${nextState}`}
          >
            Approve
          </button>
        )}

        <button
          type="button"
          className="btn btn--deny"
          onClick={() => onDeny(task.task_id)}
          disabled={loading}
          aria-disabled={loading}
          aria-label={`Deny and cancel task "${task.objective}"`}
        >
          Cancel task
        </button>
      </div>
    </section>
  );
}
