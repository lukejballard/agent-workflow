/**
 * TaskCard — summarises one agent task with its current state.
 *
 * Follows semantic HTML + WCAG 2.1 AA accessibility requirements:
 * - role="article" for the card boundary
 * - state badge is annotated with aria-label for screen readers
 */

import type { AgentTask, TaskState } from "../../types/agentRuntime";

interface TaskCardProps {
  task: AgentTask;
  /** Called when the operator clicks "View detail". */
  onSelect?: (taskId: string) => void;
}

const STATE_LABELS: Record<TaskState, string> = {
  PENDING: "Pending",
  PLANNING: "Planning",
  EXECUTING: "Executing",
  VALIDATING: "Validating",
  LEARNING: "Learning",
  DONE: "Done",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};

const TERMINAL_STATES: Set<TaskState> = new Set(["DONE", "FAILED", "CANCELLED"]);

function stateBadgeStyle(state: TaskState): string {
  if (state === "DONE") return "badge badge--success";
  if (state === "FAILED") return "badge badge--error";
  if (state === "CANCELLED") return "badge badge--muted";
  return "badge badge--active";
}

export function TaskCard({ task, onSelect }: TaskCardProps) {
  const isTerminal = TERMINAL_STATES.has(task.state);
  const created = new Date(task.created_at).toLocaleString();

  return (
    <article aria-label={`Task: ${task.objective}`} className="task-card">
      <header className="task-card__header">
        <h2 className="task-card__title">{task.objective}</h2>
        <span
          className={stateBadgeStyle(task.state)}
          aria-label={`State: ${STATE_LABELS[task.state]}`}
        >
          {STATE_LABELS[task.state]}
        </span>
      </header>

      <dl className="task-card__meta">
        <dt>Task ID</dt>
        <dd>
          <code>{task.task_id}</code>
        </dd>

        <dt>Trace ID</dt>
        <dd>
          <code>{task.trace_id}</code>
        </dd>

        <dt>Created</dt>
        <dd>
          <time dateTime={task.created_at}>{created}</time>
        </dd>
      </dl>

      {!isTerminal && onSelect !== undefined && (
        <footer className="task-card__footer">
          <button
            type="button"
            onClick={() => onSelect(task.task_id)}
            aria-label={`View details for task: ${task.objective}`}
          >
            View detail
          </button>
        </footer>
      )}
    </article>
  );
}
